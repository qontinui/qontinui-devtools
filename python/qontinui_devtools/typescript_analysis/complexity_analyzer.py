"""Code complexity analyzer for TypeScript/JavaScript.

This module analyzes code complexity including:
- Cyclomatic complexity
- File size metrics
- Function length
- God classes/components (large React components)
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from .ts_utils import count_lines_of_code, find_ts_js_files


@dataclass
class ComplexityIssue:
    """A complexity-related issue.

    Attributes:
        type: Type of issue ("high_complexity", "large_file", "large_function", "god_component")
        name: Name of the entity (function name, class name, etc.)
        file_path: Path to the file
        line_number: Line number where the issue starts
        metric: The metric value (complexity score, line count, etc.)
        threshold: The threshold that was exceeded
        severity: "high", "medium", or "low"
    """

    type: str
    name: str
    file_path: Path
    line_number: int
    metric: int
    threshold: int
    severity: str


class ComplexityAnalyzer:
    """Analyzer for code complexity in TypeScript/JavaScript projects.

    This analyzer:
    1. Measures cyclomatic complexity
    2. Identifies large files
    3. Finds long functions
    4. Detects god classes/components

    Example:
        >>> analyzer = ComplexityAnalyzer('/path/to/project')
        >>> results = analyzer.analyze()
        >>> for issue in results['issues']:
        ...     print(f"{issue.name}: {issue.metric}")
    """

    def __init__(
        self,
        root_path: str,
        verbose: bool = False,
        max_file_lines: int = 500,
        max_function_lines: int = 50,
        max_complexity: int = 10,
    ) -> None:
        """Initialize the analyzer.

        Args:
            root_path: Root directory of the project to analyze
            verbose: If True, print progress information
            max_file_lines: Maximum lines per file before flagging
            max_function_lines: Maximum lines per function before flagging
            max_complexity: Maximum cyclomatic complexity before flagging
        """
        self.root_path = Path(root_path).resolve()
        self.verbose = verbose
        self.console = Console()

        # Thresholds
        self.max_file_lines = max_file_lines
        self.max_function_lines = max_function_lines
        self.max_complexity = max_complexity

        # State
        self.files: list[Path] = []
        self.issues: list[ComplexityIssue] = []
        self.metrics: dict[str, Any] = {
            "total_files": 0,
            "total_lines": 0,
            "total_functions": 0,
            "avg_complexity": 0.0,
        }

    def analyze(self) -> dict[str, Any]:
        """Perform complexity analysis.

        Returns:
            Dictionary with metrics and issues
        """
        if self.verbose:
            self.console.print(
                f"\n[bold]Analyzing TypeScript/JavaScript complexity:[/bold] {self.root_path}"
            )

        # Find all files
        self.files = find_ts_js_files(self.root_path)

        if self.verbose:
            self.console.print(f"Found {len(self.files)} files")

        # Analyze each file
        total_complexity = 0
        function_count = 0

        for file_path in self.files:
            file_complexity, file_functions = self._analyze_file(file_path)
            total_complexity += file_complexity
            function_count += file_functions

        # Calculate average complexity
        if function_count > 0:
            self.metrics["avg_complexity"] = total_complexity / function_count

        self.metrics["total_files"] = len(self.files)
        self.metrics["total_functions"] = function_count

        if self.verbose:
            self.console.print("\n[green]Analysis complete[/green]")
            self.console.print(f"Found {len(self.issues)} complexity issues")

        return {
            "metrics": self.metrics,
            "issues": self.issues,
        }

    def _analyze_file(self, file_path: Path) -> tuple[int, int]:
        """Analyze a single file.

        Args:
            file_path: Path to the file

        Returns:
            Tuple of (total_complexity, function_count)
        """
        # Check file size
        line_counts = count_lines_of_code(file_path)
        code_lines = line_counts["code"]

        self.metrics["total_lines"] += line_counts["total"]

        if code_lines > self.max_file_lines:
            severity = "high" if code_lines > self.max_file_lines * 2 else "medium"
            self.issues.append(
                ComplexityIssue(
                    type="large_file",
                    name=file_path.name,
                    file_path=file_path,
                    line_number=1,
                    metric=code_lines,
                    threshold=self.max_file_lines,
                    severity=severity,
                )
            )

        # Read file content
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            return 0, 0

        # Analyze functions and components
        total_complexity = 0
        function_count = 0

        # Find functions
        functions = self._extract_functions(content)

        for func_name, func_start, func_end in functions:
            function_count += 1

            # Calculate function length
            func_lines = func_end - func_start + 1

            if func_lines > self.max_function_lines:
                severity = "high" if func_lines > self.max_function_lines * 2 else "medium"
                self.issues.append(
                    ComplexityIssue(
                        type="large_function",
                        name=func_name,
                        file_path=file_path,
                        line_number=func_start,
                        metric=func_lines,
                        threshold=self.max_function_lines,
                        severity=severity,
                    )
                )

            # Calculate cyclomatic complexity
            func_content = "\n".join(content.split("\n")[func_start - 1 : func_end])
            complexity = self._calculate_complexity(func_content)
            total_complexity += complexity

            if complexity > self.max_complexity:
                severity = "high" if complexity > self.max_complexity * 2 else "medium"
                self.issues.append(
                    ComplexityIssue(
                        type="high_complexity",
                        name=func_name,
                        file_path=file_path,
                        line_number=func_start,
                        metric=complexity,
                        threshold=self.max_complexity,
                        severity=severity,
                    )
                )

        # Check for React components
        if file_path.suffix == ".tsx":
            self._check_react_components(file_path, content)

        return total_complexity, function_count

    def _extract_functions(self, content: str) -> list[tuple[str, int, int]]:
        """Extract functions from file content.

        Args:
            content: File content

        Returns:
            List of tuples (function_name, start_line, end_line)
        """
        functions = []
        lines = content.split("\n")

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Match function declarations
            func_match = re.search(
                r"(?:export\s+)?(?:async\s+)?(?:function|const|let|var)\s+(\w+)\s*[=:]?\s*(?:async\s*)?\(",
                line,
            )

            if func_match:
                func_name = func_match.group(1)
                start_line = i + 1

                # Find the end of the function by counting braces
                brace_count = 0
                in_function = False
                end_line = start_line

                for j in range(i, len(lines)):
                    current_line = lines[j]

                    # Count braces
                    for char in current_line:
                        if char == "{":
                            brace_count += 1
                            in_function = True
                        elif char == "}":
                            brace_count -= 1

                    if in_function and brace_count == 0:
                        end_line = j + 1
                        break

                functions.append((func_name, start_line, end_line))
                i = end_line
            else:
                i += 1

        return functions

    def _calculate_complexity(self, code: str) -> int:
        """Calculate cyclomatic complexity of code.

        This is a simplified calculation based on counting decision points.

        Args:
            code: Code to analyze

        Returns:
            Cyclomatic complexity score
        """
        # Start with base complexity of 1
        complexity = 1

        # Count decision points
        decision_keywords = [
            r"\bif\b",
            r"\belse\s+if\b",
            r"\bwhile\b",
            r"\bfor\b",
            r"\bcase\b",
            r"\bcatch\b",
            r"\b\?\b",  # Ternary operator
            r"\&\&",  # Logical AND
            r"\|\|",  # Logical OR
        ]

        for keyword in decision_keywords:
            complexity += len(re.findall(keyword, code))

        return complexity

    def _check_react_components(self, file_path: Path, content: str) -> None:
        """Check for god components (large React components).

        Args:
            file_path: Path to the file
            content: File content
        """
        # Find React components
        component_pattern = r"(?:export\s+)?(?:default\s+)?(?:function|const)\s+(\w+)\s*[=:]?\s*(?:\([^)]*\))?\s*(?::\s*\w+)?\s*(?:=>)?\s*\{"

        for match in re.finditer(component_pattern, content):
            component_name = match.group(1)

            # Check if it starts with uppercase (React component convention)
            if component_name[0].isupper():
                # Estimate component size by finding JSX return statement
                start_pos = match.start()
                lines_before = content[:start_pos].count("\n")

                # Look for return statement with JSX
                return_match = re.search(r"return\s*\(", content[start_pos:])
                if return_match:
                    # Count JSX lines (very rough estimate)
                    jsx_content = content[start_pos:]
                    jsx_lines = jsx_content[:1000].count("\n")  # Sample first 1000 chars

                    # If component appears to be very large
                    if jsx_lines > 100:
                        self.issues.append(
                            ComplexityIssue(
                                type="god_component",
                                name=component_name,
                                file_path=file_path,
                                line_number=lines_before + 1,
                                metric=jsx_lines,
                                threshold=100,
                                severity="high",
                            )
                        )

    def generate_rich_report(self, results: dict[str, Any]) -> None:
        """Generate a rich console report of complexity issues.

        Args:
            results: Results from analyze()
        """
        metrics = results["metrics"]
        issues = results["issues"]

        self.console.print("\n[bold]Code Complexity Report[/bold]\n")

        # Summary
        self.console.print("[bold cyan]Metrics:[/bold cyan]")
        self.console.print(f"  Total files: {metrics['total_files']}")
        self.console.print(f"  Total lines: {metrics['total_lines']}")
        self.console.print(f"  Total functions: {metrics['total_functions']}")
        self.console.print(f"  Average complexity: {metrics['avg_complexity']:.2f}")

        # Issues
        if issues:
            self.console.print(
                f"\n[bold yellow]Found {len(issues)} complexity issues[/bold yellow]\n"
            )

            # Group by type
            by_type: dict[str, list[ComplexityIssue]] = {}
            for issue in issues:
                if issue.type not in by_type:
                    by_type[issue.type] = []
                by_type[issue.type].append(issue)

            for issue_type, type_issues in by_type.items():
                self.console.print(f"[bold]{issue_type}:[/bold] {len(type_issues)}")

            # Top issues table
            self.console.print("\n[bold red]Top Issues:[/bold red]")

            table = Table()
            table.add_column("Type", style="yellow")
            table.add_column("Name", style="cyan")
            table.add_column("File", style="white")
            table.add_column("Line", style="green")
            table.add_column("Metric", style="red")
            table.add_column("Threshold", style="magenta")

            # Sort by severity and metric
            sorted_issues = sorted(
                issues,
                key=lambda x: (
                    0 if x.severity == "high" else 1 if x.severity == "medium" else 2,
                    -x.metric,
                ),
            )

            for issue in sorted_issues[:20]:
                rel_path = (
                    issue.file_path.relative_to(self.root_path)
                    if issue.file_path.is_relative_to(self.root_path)
                    else issue.file_path
                )
                table.add_row(
                    issue.type,
                    issue.name,
                    str(rel_path),
                    str(issue.line_number),
                    str(issue.metric),
                    str(issue.threshold),
                )

            self.console.print(table)

            if len(issues) > 20:
                self.console.print(f"\n... and {len(issues) - 20} more issues")

        else:
            self.console.print("\n[green]No complexity issues found![/green]")

    def generate_report(self, results: dict[str, Any]) -> str:
        """Generate a text report of complexity issues.

        Args:
            results: Results from analyze()

        Returns:
            Text report as a string
        """
        metrics = results["metrics"]
        issues = results["issues"]

        lines = [
            "=" * 80,
            "CODE COMPLEXITY REPORT",
            "=" * 80,
            "\nMetrics:",
            f"  Total files: {metrics['total_files']}",
            f"  Total lines: {metrics['total_lines']}",
            f"  Total functions: {metrics['total_functions']}",
            f"  Average complexity: {metrics['avg_complexity']:.2f}",
        ]

        if issues:
            lines.append(f"\nFound {len(issues)} complexity issues\n")

            # Group by type
            by_type: dict[str, list[ComplexityIssue]] = {}
            for issue in issues:
                if issue.type not in by_type:
                    by_type[issue.type] = []
                by_type[issue.type].append(issue)

            for issue_type, type_issues in by_type.items():
                lines.append(f"{issue_type}: {len(type_issues)}")

            lines.append("\nTop Issues:")

            # Sort by severity and metric
            sorted_issues = sorted(
                issues,
                key=lambda x: (
                    0 if x.severity == "high" else 1 if x.severity == "medium" else 2,
                    -x.metric,
                ),
            )

            for issue in sorted_issues[:20]:
                rel_path = (
                    issue.file_path.relative_to(self.root_path)
                    if issue.file_path.is_relative_to(self.root_path)
                    else issue.file_path
                )
                lines.append(
                    f"  {rel_path}:{issue.line_number} - {issue.type} '{issue.name}' "
                    f"(metric={issue.metric}, threshold={issue.threshold})"
                )

            if len(issues) > 20:
                lines.append(f"\n... and {len(issues) - 20} more issues")

        lines.append("=" * 80)

        return "\n".join(lines)
