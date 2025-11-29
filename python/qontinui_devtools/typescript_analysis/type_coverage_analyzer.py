"""Type coverage analyzer for TypeScript codebases.

This module analyzes TypeScript type coverage including:
- Percentage of typed parameters vs untyped
- Usage of 'any' type
- Missing return type annotations
- Implicit vs explicit typing
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .ts_utils import find_ts_js_files


@dataclass
class TypeIssue:
    """A type-related issue.

    Attributes:
        type: Type of issue ("any_usage", "missing_param_type", "missing_return_type", "implicit_any")
        file_path: Path to the file
        line_number: Line number
        context: Code context showing the issue
        severity: "high", "medium", or "low"
    """

    type: str
    file_path: Path
    line_number: int
    context: str
    severity: str


class TypeCoverageAnalyzer:
    """Analyzer for TypeScript type coverage.

    This analyzer:
    1. Scans TypeScript files
    2. Identifies type annotations
    3. Finds 'any' usage
    4. Calculates coverage metrics

    Example:
        >>> analyzer = TypeCoverageAnalyzer('/path/to/project')
        >>> coverage = analyzer.analyze()
        >>> print(f"Type coverage: {coverage['percentage']:.1f}%")
    """

    def __init__(self, root_path: str, verbose: bool = False) -> None:
        """Initialize the analyzer.

        Args:
            root_path: Root directory of the project to analyze
            verbose: If True, print progress information
        """
        self.root_path = Path(root_path).resolve()
        self.verbose = verbose
        self.console = Console()

        # State
        self.files: list[Path] = []
        self.issues: list[TypeIssue] = []
        self.metrics: dict[str, int] = {
            "total_functions": 0,
            "typed_functions": 0,
            "total_parameters": 0,
            "typed_parameters": 0,
            "any_count": 0,
            "unknown_count": 0,
        }

    def analyze(self) -> dict[str, Any]:
        """Perform type coverage analysis.

        Returns:
            Dictionary with coverage metrics and issues
        """
        if self.verbose:
            self.console.print(
                f"\n[bold]Analyzing TypeScript type coverage:[/bold] {self.root_path}"
            )

        # Find TypeScript files (not JavaScript)
        all_files = find_ts_js_files(self.root_path)
        self.files = [f for f in all_files if f.suffix in [".ts", ".tsx"]]

        if self.verbose:
            self.console.print(f"Found {len(self.files)} TypeScript files")

        # Analyze each file
        if self.verbose:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task("Analyzing type coverage...", total=len(self.files))

                for file_path in self.files:
                    self._analyze_file(file_path)
                    progress.advance(task)
        else:
            for file_path in self.files:
                self._analyze_file(file_path)

        # Calculate coverage
        coverage = self._calculate_coverage()

        if self.verbose:
            self.console.print("\n[green]Analysis complete[/green]")
            self.console.print(f"Type coverage: {coverage['percentage']:.1f}%")

        return coverage

    def _analyze_file(self, file_path: Path) -> None:
        """Analyze a single TypeScript file.

        Args:
            file_path: Path to the TypeScript file
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            return

        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()

            # Skip comments
            if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
                continue

            # Check for 'any' usage
            if re.search(r"\bany\b", stripped):
                # Make sure it's actually the 'any' type, not part of a word
                if re.search(r":\s*any\b|<any>|\bany\[\]", stripped):
                    self.metrics["any_count"] += 1
                    self.issues.append(
                        TypeIssue(
                            type="any_usage",
                            file_path=file_path,
                            line_number=line_num,
                            context=stripped,
                            severity="high",
                        )
                    )

            # Check for 'unknown' type (better than 'any')
            if re.search(r":\s*unknown\b", stripped):
                self.metrics["unknown_count"] += 1

            # Check for function definitions
            func_match = re.search(
                r"(?:function|const|let|var)\s+(\w+)\s*[=:]?\s*(?:async\s*)?\(([^)]*)\)(?:\s*:\s*([^{;=]+))?",
                stripped,
            )
            if func_match:
                params_str = func_match.group(2)
                return_type = func_match.group(3)

                self.metrics["total_functions"] += 1

                # Check if return type is specified
                if return_type and return_type.strip():
                    self.metrics["typed_functions"] += 1
                else:
                    # Missing return type
                    if not stripped.startswith("//"):  # Not in comment
                        self.issues.append(
                            TypeIssue(
                                type="missing_return_type",
                                file_path=file_path,
                                line_number=line_num,
                                context=stripped,
                                severity="medium",
                            )
                        )

                # Check parameters
                if params_str:
                    params = [p.strip() for p in params_str.split(",") if p.strip()]
                    for param in params:
                        self.metrics["total_parameters"] += 1

                        # Check if parameter has type annotation
                        if ":" in param:
                            self.metrics["typed_parameters"] += 1
                        else:
                            # Missing parameter type
                            self.issues.append(
                                TypeIssue(
                                    type="missing_param_type",
                                    file_path=file_path,
                                    line_number=line_num,
                                    context=f"Parameter '{param}' in: {stripped}",
                                    severity="medium",
                                )
                            )

            # Check for arrow functions
            arrow_match = re.search(
                r"(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(([^)]*)\)(?:\s*:\s*([^=]+))?\s*=>",
                stripped,
            )
            if arrow_match:
                params_str = arrow_match.group(2)
                return_type = arrow_match.group(3)

                self.metrics["total_functions"] += 1

                # Check if return type is specified
                if return_type and return_type.strip():
                    self.metrics["typed_functions"] += 1

                # Check parameters
                if params_str:
                    params = [p.strip() for p in params_str.split(",") if p.strip()]
                    for param in params:
                        self.metrics["total_parameters"] += 1

                        # Check if parameter has type annotation
                        if ":" in param:
                            self.metrics["typed_parameters"] += 1

    def _calculate_coverage(self) -> dict[str, Any]:
        """Calculate type coverage metrics.

        Returns:
            Dictionary with coverage metrics
        """
        # Calculate overall coverage
        total_items = self.metrics["total_parameters"] + self.metrics["total_functions"]
        typed_items = self.metrics["typed_parameters"] + self.metrics["typed_functions"]

        if total_items > 0:
            percentage = (typed_items / total_items) * 100
        else:
            percentage = 0.0

        # Group issues by type
        issues_by_type = {}
        for issue in self.issues:
            if issue.type not in issues_by_type:
                issues_by_type[issue.type] = []
            issues_by_type[issue.type].append(issue)

        return {
            "percentage": percentage,
            "total_files": len(self.files),
            "total_functions": self.metrics["total_functions"],
            "typed_functions": self.metrics["typed_functions"],
            "total_parameters": self.metrics["total_parameters"],
            "typed_parameters": self.metrics["typed_parameters"],
            "any_count": self.metrics["any_count"],
            "unknown_count": self.metrics["unknown_count"],
            "issues": self.issues,
            "issues_by_type": issues_by_type,
        }

    def generate_rich_report(self, coverage: dict[str, Any]) -> None:
        """Generate a rich console report of type coverage.

        Args:
            coverage: Coverage metrics from analyze()
        """
        self.console.print("\n[bold]TypeScript Type Coverage Report[/bold]\n")

        # Summary
        self.console.print(
            f"[bold cyan]Overall Coverage: {coverage['percentage']:.1f}%[/bold cyan]"
        )
        self.console.print(f"  Files analyzed: {coverage['total_files']}")
        self.console.print(
            f"  Functions: {coverage['typed_functions']}/{coverage['total_functions']} typed"
        )
        self.console.print(
            f"  Parameters: {coverage['typed_parameters']}/{coverage['total_parameters']} typed"
        )
        self.console.print(f"  'any' usage: {coverage['any_count']} occurrences")
        self.console.print(f"  'unknown' usage: {coverage['unknown_count']} occurrences")

        # Issues breakdown
        issues_by_type = coverage["issues_by_type"]

        if issues_by_type:
            self.console.print("\n[bold yellow]Issues by Type:[/bold yellow]")
            for issue_type, issues in issues_by_type.items():
                self.console.print(f"  {issue_type}: {len(issues)}")

            # Show top issues
            self.console.print("\n[bold red]Top Issues:[/bold red]")

            # Limit to 20 issues
            top_issues = self.issues[:20]

            table = Table()
            table.add_column("Type", style="yellow")
            table.add_column("File", style="cyan")
            table.add_column("Line", style="green")
            table.add_column("Severity", style="red")

            for issue in top_issues:
                rel_path = (
                    issue.file_path.relative_to(self.root_path)
                    if issue.file_path.is_relative_to(self.root_path)
                    else issue.file_path
                )
                table.add_row(
                    issue.type,
                    str(rel_path),
                    str(issue.line_number),
                    issue.severity,
                )

            self.console.print(table)

            if len(self.issues) > 20:
                self.console.print(f"\n... and {len(self.issues) - 20} more issues")

        else:
            self.console.print("\n[green]No type issues found![/green]")

    def generate_report(self, coverage: dict[str, Any]) -> str:
        """Generate a text report of type coverage.

        Args:
            coverage: Coverage metrics from analyze()

        Returns:
            Text report as a string
        """
        lines = [
            "=" * 80,
            "TYPESCRIPT TYPE COVERAGE REPORT",
            "=" * 80,
            f"\nOverall Coverage: {coverage['percentage']:.1f}%\n",
            f"Files analyzed: {coverage['total_files']}",
            f"Functions: {coverage['typed_functions']}/{coverage['total_functions']} typed",
            f"Parameters: {coverage['typed_parameters']}/{coverage['total_parameters']} typed",
            f"'any' usage: {coverage['any_count']} occurrences",
            f"'unknown' usage: {coverage['unknown_count']} occurrences",
        ]

        issues_by_type = coverage["issues_by_type"]

        if issues_by_type:
            lines.append("\nIssues by Type:")
            for issue_type, issues in issues_by_type.items():
                lines.append(f"  {issue_type}: {len(issues)}")

            lines.append("\nTop Issues:")
            for issue in self.issues[:20]:
                rel_path = (
                    issue.file_path.relative_to(self.root_path)
                    if issue.file_path.is_relative_to(self.root_path)
                    else issue.file_path
                )
                lines.append(f"  {rel_path}:{issue.line_number} - {issue.type} ({issue.severity})")

            if len(self.issues) > 20:
                lines.append(f"\n... and {len(self.issues) - 20} more issues")

        lines.append("=" * 80)

        return "\n".join(lines)
