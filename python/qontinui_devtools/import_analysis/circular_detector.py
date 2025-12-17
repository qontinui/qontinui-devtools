"""Circular dependency detector for Python code.

This module provides static analysis of Python import statements to detect
circular dependencies without executing the code.
"""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import networkx as nx
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .ast_utils import ImportStatement, extract_imports, find_python_files, module_path_from_file
from .fix_suggester import FixSuggestion, analyze_cycle, suggest_best_break_point


@dataclass
class CircularDependency:
    """A detected circular dependency.

    Attributes:
        cycle: List of module names forming the cycle (e.g., ['a', 'b', 'c', 'a'])
        import_chain: List of ImportStatements showing the actual imports
        suggestion: FixSuggestion with recommended fix
        severity: 'high', 'medium', or 'low' based on cycle length
    """

    cycle: list[str]
    import_chain: list[ImportStatement]
    suggestion: FixSuggestion
    severity: str

    def __str__(self) -> str:
        """Human-readable representation."""
        cycle_str = " -> ".join(self.cycle)
        return f"Circular dependency: {cycle_str}"


class CircularDependencyDetector:
    """Static analyzer for detecting circular dependencies in Python code.

    This analyzer:
    1. Scans a directory tree for Python files
    2. Parses each file to extract import statements (no code execution)
    3. Builds a dependency graph
    4. Detects cycles using graph algorithms
    5. Suggests fixes based on usage patterns

    Example:
        >>> detector = CircularDependencyDetector('/path/to/project')
        >>> cycles = detector.analyze()
        >>> for cycle in cycles:
        ...     print(cycle)
        ...     print(cycle.suggestion.description)
    """

    def __init__(self, root_path: str, verbose: bool = False) -> None:
        """Initialize the detector.

        Args:
            root_path: Root directory of the Python project to analyze
            verbose: If True, print progress information
        """
        self.root_path = Path(root_path).resolve()
        self.verbose = verbose
        self.console = Console()

        # State populated during analysis
        self.file_map: dict[str, str] = {}  # module -> file path
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
            self.console.print(f"\n[bold]Analyzing project:[/bold] {self.root_path}")

        # Step 1: Scan directory for Python files
        self._scan_directory()

        # Step 2: Build dependency graph
        self._build_dependency_graph()

        # Step 3: Find cycles
        self._find_cycles()

        # Step 4: Analyze cycles and generate suggestions
        circular_deps = self._analyze_cycles()

        elapsed = time.time() - start_time

        if self.verbose:
            self.console.print(f"\n[bold green]Analysis complete[/bold green] in {elapsed:.2f}s")
            self.console.print(f"Files scanned: {len(self.file_map)}")
            self.console.print(f"Dependencies: {len(self.graph.edges())}")
            self.console.print(f"Cycles found: {len(circular_deps)}")

        return circular_deps

    def _scan_directory(self) -> None:
        """Scan directory tree and extract imports from all Python files."""
        python_files = find_python_files(str(self.root_path))

        if self.verbose:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task(
                    f"Scanning {len(python_files)} Python files...", total=len(python_files)
                )

                for file_path in python_files:
                    self._process_file(file_path)
                    progress.advance(task)
        else:
            for file_path in python_files:
                self._process_file(file_path)

    def _process_file(self, file_path: str) -> None:
        """Process a single Python file to extract imports.

        Args:
            file_path: Path to the Python file
        """
        try:
            # Get module path
            module_name = module_path_from_file(file_path, str(self.root_path))

            if not module_name:
                return

            # Store file mapping
            self.file_map[module_name] = file_path

            # Extract imports
            imports = extract_imports(file_path)
            self.import_map[module_name] = imports

        except (SyntaxError, ValueError) as e:
            if self.verbose:
                self.console.print(f"[yellow]Warning: Could not parse {file_path}: {e}[/yellow]")

    def _build_dependency_graph(self) -> None:
        """Build directed graph of module dependencies."""
        # Add all modules as nodes
        for module in self.file_map.keys():
            self.graph.add_node(module)

        # Add edges for imports
        for module, imports in self.import_map.items():
            for import_stmt in imports:
                imported_module = self._resolve_import(import_stmt.module, module)

                # Only add edge if the imported module is in our project
                if imported_module and imported_module in self.file_map:
                    self.graph.add_edge(module, imported_module, import_stmt=import_stmt)

    def _resolve_import(self, import_module: str, current_module: str) -> str | None:
        """Resolve an import to a module in our project.

        Args:
            import_module: The imported module name
            current_module: The module doing the importing

        Returns:
            Resolved module name if it's in our project, None otherwise
        """
        # Check for exact match
        if import_module in self.file_map:
            return import_module

        # Check if it's a submodule import (e.g., 'foo.bar' importing 'foo')
        parts = import_module.split(".")
        for i in range(len(parts), 0, -1):
            partial = ".".join(parts[:i])
            if partial in self.file_map:
                return partial

        return None

    def _find_cycles(self) -> None:
        """Find all cycles in the dependency graph."""
        try:
            # NetworkX's simple_cycles finds all elementary cycles
            self.cycles = list(nx.simple_cycles(self.graph))
        except Exception as e:
            if self.verbose:
                self.console.print(f"[red]Error finding cycles: {e}[/red]")
            self.cycles: list[Any] = []

    def _analyze_cycles(self) -> list[CircularDependency]:
        """Analyze detected cycles and generate fix suggestions.

        Returns:
            List of CircularDependency objects with suggestions
        """
        circular_deps: list[CircularDependency] = []

        for cycle in self.cycles:
            # Close the cycle for display (add first element at end)
            closed_cycle = cycle + [cycle[0]]

            # Extract import statements in the cycle
            import_chain = self._extract_import_chain(closed_cycle)

            # Analyze and get fix suggestion
            suggestion = analyze_cycle(closed_cycle, self.import_map)

            # Determine severity based on cycle length
            severity = self._determine_severity(len(cycle))

            circular_dep = CircularDependency(
                cycle=closed_cycle,
                import_chain=import_chain,
                suggestion=suggestion,
                severity=severity,
            )

            circular_deps.append(circular_dep)

        # Sort by severity (high first) then by cycle length (shorter first)
        severity_order = {"high": 0, "medium": 1, "low": 2}
        circular_deps.sort(key=lambda x: (severity_order[x.severity], len(x.cycle)))

        return circular_deps

    def _extract_import_chain(self, cycle: list[str]) -> list[ImportStatement]:
        """Extract the import statements forming a cycle.

        Args:
            cycle: List of modules in the cycle

        Returns:
            List of ImportStatement objects
        """
        import_chain: list[ImportStatement] = []

        for i in range(len(cycle) - 1):
            current = cycle[i]
            next_module = cycle[i + 1]

            # Find import from current to next
            if current in self.import_map:
                for import_stmt in self.import_map[current]:
                    resolved = self._resolve_import(import_stmt.module, current)
                    if resolved == next_module:
                        import_chain.append(import_stmt)
                        break

        return import_chain

    def _determine_severity(self, cycle_length: int) -> str:
        """Determine severity based on cycle length.

        Args:
            cycle_length: Number of modules in the cycle

        Returns:
            'high', 'medium', or 'low'
        """
        if cycle_length == 2:
            return "high"  # Direct circular dependency
        elif cycle_length <= 4:
            return "medium"  # Medium complexity
        else:
            return "low"  # Complex, indirect cycle

    def generate_report(self, cycles: list[CircularDependency]) -> str:
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
        lines.append("CIRCULAR DEPENDENCY REPORT")
        lines.append("=" * 80)
        lines.append(f"\nProject: {self.root_path}")
        lines.append(f"Total cycles found: {len(cycles)}")
        lines.append("")

        for idx, cycle in enumerate(cycles, 1):
            lines.append("-" * 80)
            lines.append(f"\nCycle #{idx} [{cycle.severity.upper()} SEVERITY]")
            lines.append(f"Path: {' -> '.join(cycle.cycle)}")
            lines.append("")

            # Show import details
            lines.append("Import chain:")
            for imp in cycle.import_chain:
                file_rel = Path(imp.file_path).relative_to(self.root_path)
                lines.append(f"  {file_rel}:{imp.line_number}: {imp}")

            lines.append("")
            lines.append(f"Fix type: {cycle.suggestion.fix_type}")
            lines.append(f"Description: {cycle.suggestion.description}")

            if cycle.suggestion.code_example:
                lines.append("\nExample fix:")
                lines.append(cycle.suggestion.code_example)

            # Add break point suggestion
            break_point = suggest_best_break_point(cycle.cycle, self.import_map)
            lines.append(f"\n{break_point}")
            lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)

    def generate_rich_report(self, cycles: list[CircularDependency]) -> None:
        """Generate a rich console report with colors and formatting.

        Args:
            cycles: List of detected circular dependencies
        """
        if not cycles:
            self.console.print("\n[bold green]✓ No circular dependencies found[/bold green]\n")
            return

        self.console.print(f"\n[bold red]✗ Found {len(cycles)} circular dependencies[/bold red]\n")

        for idx, cycle in enumerate(cycles, 1):
            # Severity color
            severity_color = {"high": "red", "medium": "yellow", "low": "blue"}[cycle.severity]

            self.console.print(
                f"[bold {severity_color}]Cycle #{idx} "
                f"[{cycle.severity.upper()} SEVERITY][/bold {severity_color}]"
            )

            # Cycle path
            cycle_display = " → ".join(cycle.cycle)
            self.console.print(f"  [cyan]{cycle_display}[/cyan]")

            # Import details
            self.console.print("\n  [bold]Import chain:[/bold]")
            for imp in cycle.import_chain:
                file_rel = Path(imp.file_path).relative_to(self.root_path)
                self.console.print(f"    {file_rel}:{imp.line_number}: [dim]{imp}[/dim]")

            # Suggestion
            self.console.print(f"\n  [bold]Fix type:[/bold] {cycle.suggestion.fix_type}")
            self.console.print(f"  [bold]Description:[/bold] {cycle.suggestion.description}")

            if cycle.suggestion.code_example:
                self.console.print("\n  [bold]Example fix:[/bold]")
                # Indent the example
                for line in cycle.suggestion.code_example.split("\n"):
                    self.console.print(f"    [dim]{line}[/dim]")

            # Break point suggestion
            break_point = suggest_best_break_point(cycle.cycle, self.import_map)
            self.console.print(f"\n  [yellow]{break_point}[/yellow]")
            self.console.print("")

    def get_statistics(self) -> dict[str, Any]:
        """Get analysis statistics.

        Returns:
            Dictionary with analysis statistics
        """
        return {
            "total_files": len(self.file_map),
            "total_imports": sum(len(imports) for imports in self.import_map.values()),
            "total_modules": len(self.graph.nodes()),
            "total_dependencies": len(self.graph.edges()),
            "cycles_found": len(self.cycles),
            "severity_breakdown": self._get_severity_breakdown(),
        }

    def _get_severity_breakdown(self) -> dict[str, int]:
        """Get count of cycles by severity."""
        breakdown = {"high": 0, "medium": 0, "low": 0}

        for cycle in self.cycles:
            severity = self._determine_severity(len(cycle))
            breakdown[severity] += 1

        return breakdown

    def export_graph(self, output_path: str) -> None:
        """Export dependency graph to a file.

        Args:
            output_path: Path to save the graph (supports .gml, .graphml, .json)
        """
        path = Path(output_path)
        suffix = path.suffix.lower()

        try:
            if suffix == ".gml":
                nx.write_gml(self.graph, str(path))
            elif suffix == ".graphml":
                nx.write_graphml(self.graph, str(path))
            elif suffix == ".json":
                import json

                from networkx.readwrite import json_graph

                data = json_graph.node_link_data(self.graph)
                path.write_text(json.dumps(data, indent=2))
            else:
                raise ValueError(f"Unsupported format: {suffix}")

            if self.verbose:
                self.console.print(f"[green]Graph exported to {output_path}[/green]")

        except Exception as e:
            if self.verbose:
                self.console.print(f"[red]Error exporting graph: {e}[/red]")
