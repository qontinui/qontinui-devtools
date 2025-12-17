"""Complexity analyzer for Rust codebases.

This module measures code complexity in Rust projects:
- Function complexity (cyclomatic complexity approximation)
- File sizes and line counts
- Large functions
- Complex match statements
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table


@dataclass
class ComplexityMetrics:
    """Complexity metrics for a code element.

    Attributes:
        name: Name of the element (function, file, etc.)
        file_path: Path to the file
        line_number: Starting line number
        element_type: Type of element (function, file, match)
        complexity: Complexity score
        lines: Number of lines
        details: Additional details about the complexity
    """

    name: str
    file_path: str
    line_number: int
    element_type: str
    complexity: int
    lines: int
    details: str


class ComplexityAnalyzer:
    """Analyze code complexity in Rust projects.

    This analyzer measures:
    - Function complexity (based on control flow statements)
    - File sizes (large files)
    - Function sizes (large functions)
    - Match statement complexity

    The analyzer uses regex patterns to approximate cyclomatic complexity.
    """

    def __init__(
        self, root_path: str, verbose: bool = False, complexity_threshold: int = 10
    ) -> None:
        """Initialize the analyzer.

        Args:
            root_path: Root directory to analyze
            verbose: If True, print progress information
            complexity_threshold: Threshold for flagging complex functions
        """
        self.root_path = Path(root_path)
        self.verbose = verbose
        self.complexity_threshold = complexity_threshold
        self.console = Console()
        self._metrics: list[ComplexityMetrics] = []

    def _find_rust_files(self) -> list[Path]:
        """Find all Rust files in the project."""
        rust_files: list[Any] = []
        for path in self.root_path.rglob("*.rs"):
            parts = path.parts
            skip_dirs = {"target", ".git", "vendor"}
            if any(skip_dir in parts for skip_dir in skip_dirs):
                continue
            rust_files.append(path)
        return rust_files

    def _calculate_cyclomatic_complexity(self, code: str) -> int:
        """Calculate approximate cyclomatic complexity.

        Counts decision points:
        - if, else if
        - match arms
        - for, while, loop
        - &&, ||
        - ?

        Args:
            code: Code snippet

        Returns:
            Complexity score (starts at 1)
        """
        complexity = 1  # Base complexity

        # Count if/else if
        complexity += len(re.findall(r"\bif\b", code))
        complexity += len(re.findall(r"\belse\s+if\b", code))

        # Count match arms (each => adds a path)
        complexity += len(re.findall(r"=>", code))

        # Count loops
        complexity += len(re.findall(r"\bfor\b", code))
        complexity += len(re.findall(r"\bwhile\b", code))
        complexity += len(re.findall(r"\bloop\b", code))

        # Count logical operators
        complexity += len(re.findall(r"&&", code))
        complexity += len(re.findall(r"\|\|", code))

        # Count ? operators (error propagation)
        complexity += len(re.findall(r"\?", code))

        return complexity

    def _extract_function_body(self, lines: list[str], start_line: int) -> tuple[str, int]:
        """Extract function body from lines.

        Args:
            lines: All lines in the file
            start_line: Line where function starts (0-indexed)

        Returns:
            Tuple of (function body, number of lines)
        """
        # Find the opening brace
        brace_count = 0
        body_lines: list[Any] = []
        in_body = False

        for i in range(start_line, len(lines)):
            line = lines[i]
            body_lines.append(line)

            # Count braces
            for char in line:
                if char == "{":
                    brace_count += 1
                    in_body = True
                elif char == "}":
                    brace_count -= 1

                # If we've closed all braces, we're done
                if in_body and brace_count == 0:
                    return "".join(body_lines), len(body_lines)

        return "".join(body_lines), len(body_lines)

    def _analyze_file(self, file_path: Path) -> None:
        """Analyze a single file for complexity.

        Args:
            file_path: Path to the Rust file
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()
                content = "".join(lines)

            # Check file size
            line_count = len(lines)
            if line_count > 500:
                self._metrics.append(
                    ComplexityMetrics(
                        name=file_path.name,
                        file_path=str(file_path),
                        line_number=1,
                        element_type="file",
                        complexity=0,
                        lines=line_count,
                        details=f"Large file with {line_count} lines",
                    )
                )

            # Find functions and analyze them
            func_pattern = r"(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?(?:unsafe\s+)?fn\s+(\w+)\s*[<(]"
            for match in re.finditer(func_pattern, content):
                func_name = match.group(1)
                line_num = content[: match.start()].count("\n") + 1

                # Extract function body
                body, body_lines = self._extract_function_body(lines, line_num - 1)

                # Calculate complexity
                complexity = self._calculate_cyclomatic_complexity(body)

                # Flag if complex or large
                if complexity >= self.complexity_threshold or body_lines > 100:
                    details_parts: list[Any] = []
                    if complexity >= self.complexity_threshold:
                        details_parts.append(f"complexity {complexity}")
                    if body_lines > 100:
                        details_parts.append(f"{body_lines} lines")

                    self._metrics.append(
                        ComplexityMetrics(
                            name=func_name,
                            file_path=str(file_path),
                            line_number=line_num,
                            element_type="function",
                            complexity=complexity,
                            lines=body_lines,
                            details=f"Complex function: {', '.join(details_parts)}",
                        )
                    )

            # Find complex match statements
            match_pattern = r"match\s+[^{]+\{"
            for match in re.finditer(match_pattern, content):
                line_num = content[: match.start()].count("\n") + 1

                # Extract match body
                match_body, match_lines = self._extract_function_body(lines, line_num - 1)

                # Count match arms
                arm_count = len(re.findall(r"=>", match_body))

                # Flag if many arms or very long
                if arm_count > 10 or match_lines > 50:
                    self._metrics.append(
                        ComplexityMetrics(
                            name=f"match (line {line_num})",
                            file_path=str(file_path),
                            line_number=line_num,
                            element_type="match",
                            complexity=arm_count,
                            lines=match_lines,
                            details=f"Complex match: {arm_count} arms, {match_lines} lines",
                        )
                    )

        except (UnicodeDecodeError, PermissionError) as e:
            if self.verbose:
                self.console.print(f"[yellow]Warning: Could not read {file_path}: {e}[/yellow]")

    def analyze(self) -> list[ComplexityMetrics]:
        """Analyze complexity across the project.

        Returns:
            List of ComplexityMetrics objects
        """
        if self.verbose:
            self.console.print(f"\n[bold]Analyzing complexity:[/bold] {self.root_path}")

        rust_files = self._find_rust_files()

        for file_path in rust_files:
            self._analyze_file(file_path)

        # Sort by complexity (high first)
        self._metrics.sort(key=lambda m: (-m.complexity, -m.lines))

        if self.verbose:
            self.console.print(f"Files scanned: {len(rust_files)}")
            self.console.print(f"Complex elements found: {len(self._metrics)}")

        return self._metrics

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about code complexity.

        Returns:
            Dictionary with statistics
        """
        if not self._metrics:
            self.analyze()

        # Count by type
        by_type: dict[str, int] = {}
        for metric in self._metrics:
            by_type[metric.element_type] = by_type.get(metric.element_type, 0) + 1

        # Calculate averages
        functions = [m for m in self._metrics if m.element_type == "function"]
        avg_complexity = sum(f.complexity for f in functions) / len(functions) if functions else 0
        avg_lines = sum(f.lines for f in functions) / len(functions) if functions else 0

        # Top complex functions
        top_complex = sorted(functions, key=lambda f: f.complexity, reverse=True)[:10]

        return {
            "total_issues": len(self._metrics),
            "by_type": by_type,
            "avg_function_complexity": round(avg_complexity, 2),
            "avg_function_lines": round(avg_lines, 2),
            "most_complex": [
                {"name": m.name, "complexity": m.complexity, "lines": m.lines} for m in top_complex
            ],
        }

    def generate_report(self, metrics: list[ComplexityMetrics] | None = None) -> str:
        """Generate a detailed text report of complexity.

        Args:
            metrics: List of metrics to report (uses all if None)

        Returns:
            Formatted report as a string
        """
        if metrics is None:
            metrics = self._metrics

        if not metrics:
            return "No complexity issues found."

        lines: list[str] = []
        lines.append("=" * 80)
        lines.append("RUST COMPLEXITY REPORT")
        lines.append("=" * 80)
        lines.append(f"\nProject: {self.root_path}")
        lines.append(f"Complexity threshold: {self.complexity_threshold}")
        lines.append(f"Total issues: {len(metrics)}")
        lines.append("")

        # Statistics
        stats = self.get_statistics()
        lines.append("STATISTICS:")
        lines.append(f"  Average function complexity: {stats['avg_function_complexity']}")
        lines.append(f"  Average function lines: {stats['avg_function_lines']}")
        lines.append("")

        lines.append("BY TYPE:")
        for element_type, count in sorted(stats["by_type"].items()):
            lines.append(f"  {element_type}: {count}")

        lines.append("\n" + "-" * 80)
        lines.append("\nDETAILS:")

        # Group by type
        by_type: dict[str, list[ComplexityMetrics]] = {}
        for metric in metrics:
            by_type.setdefault(metric.element_type, []).append(metric)

        for element_type, items in sorted(by_type.items()):
            lines.append(f"\n{element_type.upper()}S ({len(items)}):")

            for item in items[:20]:  # Limit to top 20 per type
                rel_path = Path(item.file_path).relative_to(self.root_path)
                lines.append(
                    f"\n  {item.name} - Complexity: {item.complexity}, Lines: {item.lines}"
                )
                lines.append(f"    {rel_path}:{item.line_number}")
                lines.append(f"    {item.details}")

        lines.append("\n" + "=" * 80)
        return "\n".join(lines)

    def generate_rich_report(self, metrics: list[ComplexityMetrics] | None = None) -> None:
        """Generate a rich console report with colors and formatting.

        Args:
            metrics: List of metrics to report (uses all if None)
        """
        if metrics is None:
            metrics = self._metrics

        if not metrics:
            self.console.print("\n[bold green]No complexity issues found[/bold green]\n")
            return

        self.console.print(f"\n[bold yellow]Found {len(metrics)} complexity issues[/bold yellow]\n")

        # Statistics
        stats = self.get_statistics()

        # Summary table
        summary_table = Table(title="Complexity Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", justify="right", style="green")

        summary_table.add_row("Total Issues", str(stats["total_issues"]))
        summary_table.add_row("Avg Function Complexity", str(stats["avg_function_complexity"]))
        summary_table.add_row("Avg Function Lines", str(stats["avg_function_lines"]))

        self.console.print(summary_table)
        self.console.print()

        # Most complex functions
        if stats["most_complex"]:
            complex_table = Table(title="Most Complex Functions")
            complex_table.add_column("Function", style="cyan")
            complex_table.add_column("Complexity", justify="right", style="red")
            complex_table.add_column("Lines", justify="right", style="yellow")

            for item in stats["most_complex"][:10]:
                complex_table.add_row(item["name"], str(item["complexity"]), str(item["lines"]))

            self.console.print(complex_table)
            self.console.print()
