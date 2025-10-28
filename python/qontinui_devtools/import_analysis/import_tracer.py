"""
Import tracer to detect circular dependencies and import deadlocks.

This module provides tools to hook into Python's import system and trace
import chains in real-time, detecting circular dependencies that can cause
freezes or deadlocks.
"""

import sys
import threading
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Optional
from collections import defaultdict
import inspect


@dataclass
class ImportEvent:
    """Record of a single import event.

    Attributes:
        module_name: Name of the module being imported
        importer: Name of the module that triggered the import (None for top-level)
        timestamp: Unix timestamp when import occurred
        thread_id: ID of the thread that performed the import
        stack_trace: List of formatted stack frames
    """
    module_name: str
    importer: Optional[str]
    timestamp: float
    thread_id: int
    stack_trace: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "module_name": self.module_name,
            "importer": self.importer,
            "timestamp": self.timestamp,
            "thread_id": self.thread_id,
            "stack_trace": self.stack_trace,
        }


class ImportGraph:
    """Graph representing module import relationships.

    This class maintains a directed graph where edges represent import
    relationships (A imports B means A -> B edge).
    """

    def __init__(self):
        """Initialize empty import graph."""
        self._graph: dict[str, set[str]] = defaultdict(set)
        self._lock = threading.Lock()

    def add_import(self, importer: str, imported: str) -> None:
        """Add an import relationship to the graph.

        Args:
            importer: Module doing the importing
            imported: Module being imported
        """
        with self._lock:
            self._graph[importer].add(imported)
            # Ensure imported module exists in graph even if it imports nothing
            if imported not in self._graph:
                self._graph[imported] = set()

    def get_dependencies(self, module: str) -> set[str]:
        """Get direct dependencies of a module.

        Args:
            module: Module name to query

        Returns:
            Set of module names that this module imports
        """
        with self._lock:
            return self._graph.get(module, set()).copy()

    def find_circular_paths(self) -> list[list[str]]:
        """Find all circular import paths using depth-first search.

        Returns:
            List of circular paths, where each path is a list of module names
            forming a cycle.
        """
        with self._lock:
            graph_copy = {k: v.copy() for k, v in self._graph.items()}

        cycles = []
        visited = set()
        rec_stack = []

        def dfs(node: str) -> None:
            """Depth-first search to detect cycles."""
            if node in rec_stack:
                # Found a cycle - extract it
                cycle_start = rec_stack.index(node)
                cycle = rec_stack[cycle_start:] + [node]
                cycles.append(cycle)
                return

            if node in visited:
                return

            visited.add(node)
            rec_stack.append(node)

            for neighbor in graph_copy.get(node, []):
                dfs(neighbor)

            rec_stack.pop()

        # Check all nodes as potential cycle starting points
        for node in graph_copy:
            if node not in visited:
                dfs(node)

        return cycles

    def to_dict(self) -> dict[str, Any]:
        """Convert graph to dictionary representation.

        Returns:
            Dictionary with 'nodes' and 'edges' lists
        """
        with self._lock:
            nodes = list(self._graph.keys())
            edges = []
            for source, targets in self._graph.items():
                for target in targets:
                    edges.append({"source": source, "target": target})

        return {
            "nodes": nodes,
            "edges": edges,
        }

    def get_all_modules(self) -> set[str]:
        """Get all modules in the graph.

        Returns:
            Set of all module names
        """
        with self._lock:
            return set(self._graph.keys())


class ImportHook:
    """Meta path finder hook to intercept module imports.

    This hook is installed in sys.meta_path to intercept all import attempts
    and record them for analysis.
    """

    def __init__(self, tracer: 'ImportTracer'):
        """Initialize the import hook.

        Args:
            tracer: The ImportTracer instance to report events to
        """
        self.tracer = tracer

    def find_module(self, fullname: str, path: Optional[list[str]] = None) -> None:
        """Called for every import attempt.

        Args:
            fullname: Fully qualified name of the module
            path: Import path

        Returns:
            None (we don't actually handle the import, just observe it)
        """
        # Get the calling module
        frame = sys._getframe(1)
        importer = None

        # Try to determine which module is doing the import
        while frame:
            frame_globals = frame.f_globals
            if '__name__' in frame_globals:
                potential_importer = frame_globals['__name__']
                if potential_importer != '__main__' and not potential_importer.startswith('importlib'):
                    importer = potential_importer
                    break
            frame = frame.f_back

        # Get stack trace
        stack = traceback.format_stack()
        # Filter out internal import machinery
        filtered_stack = [
            frame for frame in stack
            if 'importlib' not in frame and 'import_tracer.py' not in frame
        ]

        # Record the import event
        event = ImportEvent(
            module_name=fullname,
            importer=importer,
            timestamp=time.time(),
            thread_id=threading.get_ident(),
            stack_trace=filtered_stack[-5:],  # Keep last 5 frames for context
        )

        self.tracer._record_event(event)

        # Return None so other import hooks/finders handle the actual import
        return None

    def find_spec(self, fullname: str, path: Optional[list[str]] = None, target=None):
        """Modern import hook interface (Python 3.4+).

        Args:
            fullname: Fully qualified name of the module
            path: Import path
            target: Target module (for package reloads)

        Returns:
            None (we don't actually handle the import, just observe it)
        """
        # Call find_module for compatibility
        self.find_module(fullname, path)
        return None


class ImportTracer:
    """Context manager to trace Python imports in real-time.

    This class installs a hook into Python's import system to record every
    module import, build an import graph, and detect circular dependencies.

    Example:
        >>> with ImportTracer() as tracer:
        ...     import some_module
        >>> cycles = tracer.find_circular_dependencies()
        >>> if cycles:
        ...     print(f"Found {len(cycles)} circular dependencies!")
    """

    def __init__(self):
        """Initialize the import tracer."""
        self._events: list[ImportEvent] = []
        self._graph = ImportGraph()
        self._lock = threading.Lock()
        self._hook: Optional[ImportHook] = None
        self._start_time: Optional[float] = None
        self._installed = False

    def __enter__(self) -> 'ImportTracer':
        """Install the import hook when entering context.

        Returns:
            Self for use in with statement
        """
        self._start_time = time.time()
        self._hook = ImportHook(self)
        sys.meta_path.insert(0, self._hook)
        self._installed = True
        return self

    def __exit__(self, *args) -> None:
        """Remove the import hook when exiting context.

        Args:
            *args: Exception information (ignored)
        """
        if self._hook and self._installed:
            try:
                sys.meta_path.remove(self._hook)
            except ValueError:
                # Already removed
                pass
            self._installed = False

    def _record_event(self, event: ImportEvent) -> None:
        """Record an import event (called by ImportHook).

        Args:
            event: The import event to record
        """
        with self._lock:
            self._events.append(event)

            # Update graph if we know the importer
            if event.importer:
                self._graph.add_import(event.importer, event.module_name)

    def get_events(self) -> list[ImportEvent]:
        """Get all recorded import events.

        Returns:
            List of ImportEvent objects in chronological order
        """
        with self._lock:
            return self._events.copy()

    def get_graph(self) -> ImportGraph:
        """Get the import graph.

        Returns:
            ImportGraph instance
        """
        return self._graph

    def find_circular_dependencies(self) -> list[list[str]]:
        """Find all circular import dependencies.

        Returns:
            List of circular paths, where each path is a list of module names
            forming a cycle (e.g., ['A', 'B', 'C', 'A'])
        """
        return self._graph.find_circular_paths()

    def generate_report(self) -> str:
        """Generate a human-readable report of import activity.

        Returns:
            Formatted string report
        """
        lines = []
        lines.append("=" * 80)
        lines.append("IMPORT TRACER REPORT")
        lines.append("=" * 80)

        if self._start_time:
            duration = time.time() - self._start_time
            lines.append(f"Duration: {duration:.2f}s")

        events = self.get_events()
        lines.append(f"Total imports tracked: {len(events)}")
        lines.append("")

        # Group by thread
        thread_groups = defaultdict(list)
        for event in events:
            thread_groups[event.thread_id].append(event)

        lines.append(f"Threads involved: {len(thread_groups)}")
        lines.append("")

        # Find circular dependencies
        cycles = self.find_circular_dependencies()
        if cycles:
            lines.append("CIRCULAR DEPENDENCIES DETECTED!")
            lines.append("-" * 80)
            for i, cycle in enumerate(cycles, 1):
                cycle_str = " -> ".join(cycle)
                lines.append(f"{i}. {cycle_str}")
            lines.append("")
        else:
            lines.append("No circular dependencies detected.")
            lines.append("")

        # Top imported modules
        import_counts = defaultdict(int)
        for event in events:
            import_counts[event.module_name] += 1

        if import_counts:
            lines.append("Most imported modules:")
            lines.append("-" * 80)
            top_imports = sorted(import_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            for module, count in top_imports:
                lines.append(f"  {module}: {count} time(s)")
            lines.append("")

        # Import timeline (first 20 events)
        if events:
            lines.append("Import timeline (first 20):")
            lines.append("-" * 80)
            for event in events[:20]:
                importer_str = event.importer or "<top-level>"
                lines.append(f"  {importer_str} -> {event.module_name}")
            if len(events) > 20:
                lines.append(f"  ... and {len(events) - 20} more")
            lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Export all data to dictionary format.

        Returns:
            Dictionary containing events, graph, and metadata
        """
        return {
            "start_time": self._start_time,
            "duration": time.time() - self._start_time if self._start_time else None,
            "events": [event.to_dict() for event in self.get_events()],
            "graph": self._graph.to_dict(),
            "circular_dependencies": self.find_circular_dependencies(),
        }
