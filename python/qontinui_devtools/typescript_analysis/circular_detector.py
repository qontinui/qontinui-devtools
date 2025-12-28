"""Circular dependency detector for TypeScript/JavaScript code.

This module provides static analysis of TS/JS import statements to detect
circular dependencies without executing the code.
"""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import networkx as nx
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .ts_utils import (ImportStatement, extract_imports, find_ts_js_files,
                       module_path_from_file, resolve_import_path)


@dataclass
class CircularDependency:
    """A detected circular dependency.

    Attributes:
        cycle: List of module names forming the cycle
        import_chain: List of ImportStatements showing the actual imports
        severity: 'high', 'medium', or 'low' based on cycle length
    """

    cycle: list[str]
    import_chain: list[ImportStatement]
    severity: str

    def __str__(self) -> str:
        """Human-readable representation."""
        cycle_str = " -> ".join(self.cycle)
        return f"Circular dependency: {cycle_str}"


class CircularDependencyDetector:
    """Static analyzer for detecting circular dependencies in TypeScript/JavaScript code.

    This analyzer:
    1. Scans a directory tree for TS/JS files
    2. Parses each file to extract import statements
    3. Builds a dependency graph
    4. Detects cycles using graph algorithms

    Example:
        >>> detector = CircularDependencyDetector('/path/to/project')
        >>> cycles = detector.analyze()
        >>> for cycle in cycles:
        ...     print(cycle)
    """

    def __init__(self, root_path: str, verbose: bool = False) -> None:
        """Initialize the detector.

        Args:
            root_path: Root directory of the project to analyze
            verbose: If True, print progress information
        """
        self.root_path = Path(root_path).resolve()
        self.verbose = verbose
        self.console = Console()

        # State populated during analysis
        self.file_map: dict[str, Path] = {}  # module -> file path
        self.import_map: dict[str, list[ImportStatement]] = {}  # module -> imports
        self.graph: nx.DiGraph = nx.DiGraph()
        self.cycles: list[list[str]] = []

    def analyze(self) -> list[CircularDependency]:
        """Perform full analysis and return detected circular dependencies.

        Returns:
            List of CircularDependency objects, one per detected cycle
        """
        start_time = time.time()

        if self.verbose:
            self.console.print(
                f"\n[bold]Analyzing TypeScript/JavaScript project:[/bold] {self.root_path}"
            )

        # Step 1: Scan directory for TS/JS files
        self._scan_directory()

        # Step 2: Build dependency graph
        self._build_dependency_graph()

        # Step 3: Find cycles
        self._find_cycles()

        # Step 4: Analyze cycles
        circular_deps = self._analyze_cycles()

        elapsed = time.time() - start_time
        if self.verbose:
            self.console.print(f"\n[green]Analysis complete in {elapsed:.2f}s[/green]")

        return circular_deps

    def _scan_directory(self) -> None:
        """Scan directory for TS/JS files and build file map."""
        files = find_ts_js_files(self.root_path)

        if self.verbose:
            self.console.print(f"Found {len(files)} TypeScript/JavaScript files")

        for file_path in files:
            module_name = module_path_from_file(file_path, self.root_path)
            self.file_map[module_name] = file_path

    def _build_dependency_graph(self) -> None:
        """Build dependency graph from import statements."""
        if self.verbose:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task("Building dependency graph...", total=None)

                for module_name, file_path in self.file_map.items():
                    self._process_file(module_name, file_path)

                progress.update(task, completed=True)
        else:
            for module_name, file_path in self.file_map.items():
                self._process_file(module_name, file_path)

    def _process_file(self, module_name: str, file_path: Path) -> None:
        """Process a single file and extract its dependencies."""
        imports = extract_imports(file_path)
        self.import_map[module_name] = imports

        # Add node to graph
        self.graph.add_node(module_name)

        # Add edges for each import
        for imp in imports:
            # Resolve the import to a file path
            resolved_path = resolve_import_path(imp.source, file_path, self.root_path)

            if resolved_path:
                # Convert back to module name
                target_module = module_path_from_file(resolved_path, self.root_path)

                if target_module in self.file_map:
                    self.graph.add_edge(module_name, target_module)

    def _find_cycles(self) -> None:
        """Find all cycles in the dependency graph using NetworkX."""
        try:
            # Find all simple cycles
            self.cycles = list(nx.simple_cycles(self.graph))

            if self.verbose:
                self.console.print(f"Found {len(self.cycles)} circular dependencies")

        except Exception as e:
            if self.verbose:
                self.console.print(f"[red]Error finding cycles: {e}[/red]")
            self.cycles = []

    def _analyze_cycles(self) -> list[CircularDependency]:
        """Analyze detected cycles and create CircularDependency objects."""
        circular_deps: list[Any] = []

        for cycle in self.cycles:
            # Make cycle complete (add first node at end)
            complete_cycle = cycle + [cycle[0]]

            # Collect import statements for the cycle
            import_chain: list[Any] = []
            for i in range(len(cycle)):
                from_module = complete_cycle[i]
                to_module = complete_cycle[i + 1]

                # Find the import statement
                if from_module in self.import_map:
                    for imp in self.import_map[from_module]:
                        # Check if this import leads to the target module
                        file_path = self.file_map[from_module]
                        resolved = resolve_import_path(imp.source, file_path, self.root_path)
                        if resolved:
                            target = module_path_from_file(resolved, self.root_path)
                            if target == to_module:
                                import_chain.append(imp)
                                break

            # Determine severity based on cycle length
            if len(cycle) == 2:
                severity = "high"  # Direct circular dependency
            elif len(cycle) <= 4:
                severity = "medium"
            else:
                severity = "low"  # Long cycle, less likely to cause issues

            circular_deps.append(
                CircularDependency(
                    cycle=complete_cycle,
                    import_chain=import_chain,
                    severity=severity,
                )
            )

        # Sort by severity
        severity_order = {"high": 0, "medium": 1, "low": 2}
        circular_deps.sort(key=lambda x: (severity_order[x.severity], len(x.cycle)))

        return circular_deps

    def generate_rich_report(self, cycles: list[CircularDependency]) -> None:
        """Generate a rich console report of circular dependencies.

        Args:
            cycles: List of detected circular dependencies
        """
        if not cycles:
            self.console.print("\n[green]No circular dependencies found![/green]")
            return

        self.console.print(f"\n[bold red]Found {len(cycles)} circular dependencies:[/bold red]\n")

        for i, cycle in enumerate(cycles, 1):
            # Determine color based on severity
            if cycle.severity == "high":
                color = "red"
            elif cycle.severity == "medium":
                color = "yellow"
            else:
                color = "blue"

            self.console.print(
                f"[bold {color}]{i}. Cycle (severity: {cycle.severity}):[/bold {color}]"
            )

            # Print the cycle
            for j, module in enumerate(cycle.cycle[:-1]):
                self.console.print(f"   {module}")
                if j < len(cycle.import_chain):
                    imp = cycle.import_chain[j]
                    self.console.print(
                        f"      -> imports from '{imp.source}' (line {imp.line_number})"
                    )

            self.console.print()

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about the analyzed codebase.

        Returns:
            Dictionary with statistics
        """
        total_imports = sum(len(imports) for imports in self.import_map.values())

        return {
            "total_files": len(self.file_map),
            "total_imports": total_imports,
            "total_cycles": len(self.cycles),
            "high_severity": sum(1 for c in self.cycles if len(c) == 2),
            "medium_severity": sum(1 for c in self.cycles if 3 <= len(c) <= 4),
            "low_severity": sum(1 for c in self.cycles if len(c) > 4),
        }

    def generate_report(self, cycles: list[CircularDependency]) -> str:
        """Generate a text report of circular dependencies.

        Args:
            cycles: List of detected circular dependencies

        Returns:
            Text report as a string
        """
        if not cycles:
            return "No circular dependencies found!"

        lines = [
            "=" * 80,
            "CIRCULAR DEPENDENCY REPORT",
            "=" * 80,
            f"\nFound {len(cycles)} circular dependencies\n",
        ]

        for i, cycle in enumerate(cycles, 1):
            lines.append(f"\n{i}. Cycle (severity: {cycle.severity}):")
            lines.append("-" * 40)

            for j, module in enumerate(cycle.cycle[:-1]):
                lines.append(f"  {module}")
                if j < len(cycle.import_chain):
                    imp = cycle.import_chain[j]
                    lines.append(f"    -> imports from '{imp.source}' (line {imp.line_number})")

        lines.append("\n" + "=" * 80)
        stats = self.get_statistics()
        lines.append("STATISTICS:")
        lines.append(f"  Total files analyzed: {stats['total_files']}")
        lines.append(f"  Total imports: {stats['total_imports']}")
        lines.append(f"  High severity cycles: {stats['high_severity']}")
        lines.append(f"  Medium severity cycles: {stats['medium_severity']}")
        lines.append(f"  Low severity cycles: {stats['low_severity']}")
        lines.append("=" * 80)

        return "\n".join(lines)
