"""Circular dependency detector for Rust code.

This module provides static analysis of Rust mod and use statements to detect
circular dependencies without requiring rustc or cargo.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import networkx as nx

    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

from rich.console import Console
from rich.table import Table


@dataclass
class RustCircularDependency:
    """A detected circular dependency in Rust code.

    Attributes:
        cycle: List of module names forming the cycle
        severity: 'high', 'medium', or 'low' based on cycle length
        files: List of file paths involved in the cycle
    """

    cycle: list[str]
    severity: str
    files: list[str]

    def __str__(self) -> str:
        """Human-readable representation."""
        cycle_str = " -> ".join(self.cycle)
        return f"Circular dependency: {cycle_str}"


class CircularDependencyDetector:
    """Static analyzer for detecting circular dependencies in Rust code.

    This analyzer:
    1. Scans a directory tree for Rust files
    2. Parses each file to extract mod and use statements
    3. Builds a dependency graph
    4. Detects cycles using graph algorithms

    Example:
        >>> detector = CircularDependencyDetector('/path/to/rust/project')
        >>> cycles = detector.analyze()
        >>> for cycle in cycles:
        ...     print(cycle)
    """

    def __init__(self, root_path: str, verbose: bool = False) -> None:
        """Initialize the detector.

        Args:
            root_path: Root directory of the Rust project to analyze
            verbose: If True, print progress information
        """
        self.root_path = Path(root_path).resolve()
        self.verbose = verbose
        self.console = Console()

        # State populated during analysis
        self.file_map: dict[str, str] = {}  # module -> file path
        self.mod_map: dict[str, list[str]] = {}  # module -> child modules
        self.use_map: dict[str, list[str]] = {}  # module -> used modules
        self.graph: dict[str, set[str]] = {}  # Simple adjacency list
        self.cycles: list[list[str]] = []

    def analyze(self) -> list[RustCircularDependency]:
        """Perform full analysis and return detected circular dependencies.

        Returns:
            List of RustCircularDependency objects, one per detected cycle
        """
        if self.verbose:
            self.console.print(f"\n[bold]Analyzing Rust project:[/bold] {self.root_path}")

        # Step 1: Scan directory for Rust files
        self._scan_directory()

        # Step 2: Build dependency graph
        self._build_dependency_graph()

        # Step 3: Find cycles
        self._find_cycles()

        # Step 4: Convert to circular dependencies
        circular_deps = self._create_circular_dependencies()

        if self.verbose:
            self.console.print(f"Files scanned: {len(self.file_map)}")
            self.console.print(f"Dependencies: {len(self.graph.edges())}")
            self.console.print(f"Cycles found: {len(circular_deps)}")

        return circular_deps

    def _scan_directory(self) -> None:
        """Scan directory tree and extract modules from all Rust files."""
        rust_files = list(self.root_path.rglob("*.rs"))

        for file_path in rust_files:
            self._process_file(file_path)

    def _process_file(self, file_path: Path) -> None:
        """Process a single Rust file to extract module information.

        Args:
            file_path: Path to the Rust file
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Get module name from file path
            module_name = self._get_module_name(file_path)
            if not module_name:
                return

            # Store file mapping
            self.file_map[module_name] = str(file_path)

            # Extract mod declarations
            mods = self._extract_mods(content)
            self.mod_map[module_name] = mods

            # Extract use statements
            uses = self._extract_uses(content)
            self.use_map[module_name] = uses

        except (UnicodeDecodeError, PermissionError) as e:
            if self.verbose:
                self.console.print(f"[yellow]Warning: Could not read {file_path}: {e}[/yellow]")

    def _get_module_name(self, file_path: Path) -> str | None:
        """Get module name from file path.

        Args:
            file_path: Path to the Rust file

        Returns:
            Module name or None if not part of project
        """
        try:
            rel_path = file_path.relative_to(self.root_path)
        except ValueError:
            return None

        # Convert path to module name
        # src/main.rs -> main
        # src/lib.rs -> lib
        # src/foo/bar.rs -> foo::bar
        # src/foo/mod.rs -> foo

        parts = list(rel_path.parts)

        # Remove 'src' if present
        if parts and parts[0] == "src":
            parts = parts[1:]

        if not parts:
            return None

        # Handle lib.rs and main.rs
        if parts[-1] in ("lib.rs", "main.rs"):
            return parts[-1].replace(".rs", "")

        # Handle mod.rs
        if parts[-1] == "mod.rs":
            parts = parts[:-1]
            if not parts:
                return None
            return "::".join(parts)

        # Handle regular files
        parts[-1] = parts[-1].replace(".rs", "")
        return "::".join(parts)

    def _extract_mods(self, content: str) -> list[str]:
        """Extract mod declarations from Rust code.

        Args:
            content: Rust source code

        Returns:
            List of module names declared with 'mod'
        """
        # Match: mod foo;
        # Match: pub mod foo;
        # Match: pub(crate) mod foo;
        pattern = r"(?:pub(?:\([^)]*\))?\s+)?mod\s+(\w+)\s*;"

        mods = re.findall(pattern, content)
        return mods

    def _extract_uses(self, content: str) -> list[str]:
        """Extract use statements from Rust code.

        Args:
            content: Rust source code

        Returns:
            List of module paths from use statements
        """
        # Match: use foo::bar;
        # Match: use crate::foo::bar;
        # Match: use super::foo;
        # Match: use self::foo;
        pattern = r"use\s+(?:crate::)?(?:super::)?(?:self::)?([a-zA-Z_][\w:]*)"

        uses = re.findall(pattern, content)

        # Extract just the first module component
        first_components = []
        for use in uses:
            # Split by :: and take first component
            parts = use.split("::")
            if parts:
                first_components.append(parts[0])

        return first_components

    def _build_dependency_graph(self) -> None:
        """Build directed graph of module dependencies."""
        # Initialize graph nodes
        for module in self.file_map.keys():
            if module not in self.graph:
                self.graph[module] = set()

        # Add edges for mod declarations (parent -> child)
        for parent, children in self.mod_map.items():
            if parent not in self.graph:
                self.graph[parent] = set()

            for child in children:
                # Construct full child module name
                child_full = f"{parent}::{child}" if parent not in ("main", "lib") else child

                # Check if child exists as a module
                if child_full in self.file_map or child in self.file_map:
                    target = child_full if child_full in self.file_map else child
                    self.graph[parent].add(target)

        # Add edges for use statements (user -> used)
        for user, used_modules in self.use_map.items():
            if user not in self.graph:
                self.graph[user] = set()

            for used in used_modules:
                # Try to resolve the used module
                resolved = self._resolve_module(used, user)
                if resolved and resolved in self.file_map:
                    self.graph[user].add(resolved)

    def _resolve_module(self, module_name: str, current_module: str) -> str | None:
        """Resolve a module reference to a full module path.

        Args:
            module_name: The module name from a use statement
            current_module: The module doing the use

        Returns:
            Resolved module name if it's in our project, None otherwise
        """
        # Check for exact match
        if module_name in self.file_map:
            return module_name

        # Check for submodule
        parts = current_module.split("::")
        if len(parts) > 1:
            parent = "::".join(parts[:-1])
            candidate = f"{parent}::{module_name}"
            if candidate in self.file_map:
                return candidate

        # Check as child of current module
        candidate = f"{current_module}::{module_name}"
        if candidate in self.file_map:
            return candidate

        return None

    def _find_cycles(self) -> None:
        """Find all cycles in the dependency graph using DFS."""
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node: str) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            if node in self.graph:
                for neighbor in self.graph[node]:
                    if neighbor not in visited:
                        dfs(neighbor)
                    elif neighbor in rec_stack:
                        # Found a cycle
                        cycle_start = path.index(neighbor)
                        cycle = path[cycle_start:]
                        if cycle and cycle not in self.cycles:
                            self.cycles.append(cycle)

            path.pop()
            rec_stack.remove(node)

        try:
            for node in self.graph:
                if node not in visited:
                    dfs(node)
        except Exception as e:
            if self.verbose:
                self.console.print(f"[red]Error finding cycles: {e}[/red]")
            self.cycles = []

    def _create_circular_dependencies(self) -> list[RustCircularDependency]:
        """Create RustCircularDependency objects from cycles.

        Returns:
            List of RustCircularDependency objects
        """
        circular_deps: list[RustCircularDependency] = []

        for cycle in self.cycles:
            # Close the cycle
            closed_cycle = cycle + [cycle[0]]

            # Get files involved
            files = [self.file_map[mod] for mod in cycle if mod in self.file_map]

            # Determine severity
            severity = self._determine_severity(len(cycle))

            circular_dep = RustCircularDependency(
                cycle=closed_cycle, severity=severity, files=files
            )

            circular_deps.append(circular_dep)

        # Sort by severity then by cycle length
        severity_order = {"high": 0, "medium": 1, "low": 2}
        circular_deps.sort(key=lambda x: (severity_order[x.severity], len(x.cycle)))

        return circular_deps

    def _determine_severity(self, cycle_length: int) -> str:
        """Determine severity based on cycle length.

        Args:
            cycle_length: Number of modules in the cycle

        Returns:
            'high', 'medium', or 'low'
        """
        if cycle_length == 2:
            return "high"
        elif cycle_length <= 4:
            return "medium"
        else:
            return "low"

    def generate_report(self, cycles: list[RustCircularDependency]) -> str:
        """Generate a detailed text report of circular dependencies.

        Args:
            cycles: List of detected circular dependencies

        Returns:
            Formatted report as a string
        """
        if not cycles:
            return "No circular dependencies found."

        lines: list[str] = []
        lines.append("=" * 80)
        lines.append("RUST CIRCULAR DEPENDENCY REPORT")
        lines.append("=" * 80)
        lines.append(f"\nProject: {self.root_path}")
        lines.append(f"Total cycles found: {len(cycles)}")
        lines.append("")

        for idx, cycle in enumerate(cycles, 1):
            lines.append("-" * 80)
            lines.append(f"\nCycle #{idx} [{cycle.severity.upper()} SEVERITY]")
            lines.append(f"Path: {' -> '.join(cycle.cycle)}")
            lines.append("")
            lines.append("Files involved:")
            for file in cycle.files:
                rel_path = Path(file).relative_to(self.root_path)
                lines.append(f"  {rel_path}")
            lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)

    def generate_rich_report(self, cycles: list[RustCircularDependency]) -> None:
        """Generate a rich console report with colors and formatting.

        Args:
            cycles: List of detected circular dependencies
        """
        if not cycles:
            self.console.print("\n[bold green]No circular dependencies found[/bold green]\n")
            return

        self.console.print(f"\n[bold red]Found {len(cycles)} circular dependencies[/bold red]\n")

        for idx, cycle in enumerate(cycles, 1):
            severity_color = {"high": "red", "medium": "yellow", "low": "blue"}[cycle.severity]

            self.console.print(
                f"[bold {severity_color}]Cycle #{idx} "
                f"[{cycle.severity.upper()} SEVERITY][/bold {severity_color}]"
            )

            cycle_display = " -> ".join(cycle.cycle)
            self.console.print(f"  [cyan]{cycle_display}[/cyan]")

            self.console.print("\n  [bold]Files involved:[/bold]")
            for file in cycle.files:
                rel_path = Path(file).relative_to(self.root_path)
                self.console.print(f"    {rel_path}")
            self.console.print("")

    def get_statistics(self) -> dict[str, Any]:
        """Get analysis statistics.

        Returns:
            Dictionary with analysis statistics
        """
        severity_breakdown = {"high": 0, "medium": 0, "low": 0}
        for cycle in self.cycles:
            severity = self._determine_severity(len(cycle))
            severity_breakdown[severity] += 1

        total_edges = sum(len(neighbors) for neighbors in self.graph.values())
        return {
            "total_files": len(self.file_map),
            "total_modules": len(self.graph),
            "total_dependencies": total_edges,
            "cycles_found": len(self.cycles),
            "severity_breakdown": severity_breakdown,
        }
