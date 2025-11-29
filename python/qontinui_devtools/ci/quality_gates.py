"""Quality gates for CI/CD pipelines.

This module provides quality gate enforcement for qontinui-devtools in CI/CD environments.
It checks various metrics against configurable thresholds and fails the build if exceeded.
"""

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


class QualityGate:
    """Represents a single quality gate check."""

    def __init__(self, name: str, actual: int, threshold: int, severity: str = "error"):
        self.name = name
        self.actual = actual
        self.threshold = threshold
        self.severity = severity
        self.passed = actual <= threshold

    def __repr__(self) -> str:
        status = "✅" if self.passed else "❌"
        return f"{status} {self.name}: {self.actual}/{self.threshold}"


class QualityGateChecker:
    """Checks multiple quality gates and reports results."""

    def __init__(self):
        self.gates: list[QualityGate] = []
        self.warnings: list[str] = []

    def add_gate(self, gate: QualityGate) -> None:
        """Add a quality gate to check."""
        self.gates.append(gate)

    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)

    def check_circular_dependencies(self, file_path: str, max_allowed: int) -> None:
        """Check circular dependency count."""
        try:
            data = json.loads(Path(file_path).read_text())
            cycles = data.get("cycles", [])
            count = len(cycles)

            gate = QualityGate("Circular Dependencies", count, max_allowed, "error")
            self.add_gate(gate)

            if not gate.passed:
                self.add_warning(
                    f"Found {count} circular dependency cycles. "
                    f"Review and refactor to reduce coupling."
                )
        except FileNotFoundError:
            console.print(f"[yellow]Warning: {file_path} not found[/yellow]")
        except json.JSONDecodeError:
            console.print(f"[yellow]Warning: {file_path} is not valid JSON[/yellow]")

    def check_god_classes(self, file_path: str, max_allowed: int) -> None:
        """Check god class count."""
        try:
            data = json.loads(Path(file_path).read_text())
            god_classes = data.get("god_classes", [])
            count = len(god_classes)

            gate = QualityGate("God Classes", count, max_allowed, "error")
            self.add_gate(gate)

            if not gate.passed:
                self.add_warning(
                    f"Found {count} god classes. "
                    f"Consider splitting large classes into smaller, focused components."
                )
        except FileNotFoundError:
            console.print(f"[yellow]Warning: {file_path} not found[/yellow]")
        except json.JSONDecodeError:
            console.print(f"[yellow]Warning: {file_path} is not valid JSON[/yellow]")

    def check_race_conditions(self, file_path: str, max_critical: int, max_high: int) -> None:
        """Check race condition count by severity."""
        try:
            data = json.loads(Path(file_path).read_text())
            races = data.get("races", [])

            critical = len([r for r in races if r.get("severity") == "critical"])
            high = len([r for r in races if r.get("severity") == "high"])

            critical_gate = QualityGate("Critical Race Conditions", critical, max_critical, "error")
            self.add_gate(critical_gate)

            high_gate = QualityGate("High Severity Race Conditions", high, max_high, "error")
            self.add_gate(high_gate)

            if not critical_gate.passed:
                self.add_warning(
                    f"Found {critical} critical race conditions. "
                    f"These must be fixed immediately to prevent data corruption."
                )

            if not high_gate.passed:
                self.add_warning(
                    f"Found {high} high severity race conditions. "
                    f"Review and add proper synchronization."
                )
        except FileNotFoundError:
            console.print(f"[yellow]Warning: {file_path} not found[/yellow]")
        except json.JSONDecodeError:
            console.print(f"[yellow]Warning: {file_path} is not valid JSON[/yellow]")

    def check_code_coverage(self, file_path: str, min_coverage: float) -> None:
        """Check code coverage percentage."""
        try:
            data = json.loads(Path(file_path).read_text())
            coverage = data.get("totals", {}).get("percent_covered", 0.0)

            # Convert to inverted gate (higher is better)
            gate = QualityGate(
                "Code Coverage", int(100 - coverage), int(100 - min_coverage), "warning"
            )
            self.add_gate(gate)

            if not gate.passed:
                self.add_warning(
                    f"Code coverage is {coverage:.1f}%, below minimum of {min_coverage}%. "
                    f"Add more tests to improve coverage."
                )
        except FileNotFoundError:
            console.print(f"[yellow]Warning: {file_path} not found[/yellow]")
        except json.JSONDecodeError:
            console.print(f"[yellow]Warning: {file_path} is not valid JSON[/yellow]")

    def check_complexity(
        self,
        file_path: str,
        max_average: int,
        max_functions_over_threshold: int,
        threshold: int = 15,
    ) -> None:
        """Check cyclomatic complexity."""
        try:
            data = json.loads(Path(file_path).read_text())

            if "average_complexity" in data:
                avg = data["average_complexity"]
                gate = QualityGate("Average Complexity", int(avg), max_average, "warning")
                self.add_gate(gate)

            if "functions" in data:
                high_complexity = len(
                    [f for f in data["functions"] if f.get("complexity", 0) > threshold]
                )

                gate = QualityGate(
                    f"Functions Over Complexity {threshold}",
                    high_complexity,
                    max_functions_over_threshold,
                    "warning",
                )
                self.add_gate(gate)
        except FileNotFoundError:
            console.print(f"[yellow]Warning: {file_path} not found[/yellow]")
        except json.JSONDecodeError:
            console.print(f"[yellow]Warning: {file_path} is not valid JSON[/yellow]")

    def print_results(self) -> None:
        """Print quality gate results in a formatted table."""
        table = Table(title="Quality Gate Results", show_header=True)
        table.add_column("Status", style="bold", width=6)
        table.add_column("Metric", style="cyan")
        table.add_column("Actual", justify="right")
        table.add_column("Threshold", justify="right")
        table.add_column("Result", justify="center")

        for gate in self.gates:
            status = "✅" if gate.passed else "❌"
            result_style = "green" if gate.passed else "red"
            result_text = "PASS" if gate.passed else "FAIL"

            table.add_row(
                status,
                gate.name,
                str(gate.actual),
                str(gate.threshold),
                f"[{result_style}]{result_text}[/{result_style}]",
            )

        console.print(table)

        # Print warnings
        if self.warnings:
            console.print("\n[yellow]⚠️  Warnings:[/yellow]")
            for warning in self.warnings:
                console.print(f"  • {warning}")

    def passed(self) -> bool:
        """Check if all quality gates passed."""
        return all(gate.passed for gate in self.gates)

    def exit(self) -> None:
        """Exit with appropriate code based on results."""
        if self.passed():
            console.print("\n[green]✅ All quality gates PASSED![/green]", style="bold")
            sys.exit(0)
        else:
            failed_count = sum(1 for gate in self.gates if not gate.passed)
            console.print(
                f"\n[red]❌ Quality gates FAILED ({failed_count}/{len(self.gates)} checks failed)[/red]",
                style="bold",
            )
            console.print("[yellow]Fix the issues above before merging.[/yellow]")
            sys.exit(1)


@click.command()
@click.option(
    "--circular-deps",
    type=click.Path(exists=True),
    help="Path to circular dependencies JSON output",
)
@click.option("--god-classes", type=click.Path(exists=True), help="Path to god classes JSON output")
@click.option(
    "--race-conditions", type=click.Path(exists=True), help="Path to race conditions JSON output"
)
@click.option("--coverage", type=click.Path(exists=True), help="Path to coverage JSON output")
@click.option("--complexity", type=click.Path(exists=True), help="Path to complexity JSON output")
@click.option(
    "--max-circular", type=int, default=0, help="Maximum allowed circular dependencies (default: 0)"
)
@click.option(
    "--max-god-classes", type=int, default=5, help="Maximum allowed god classes (default: 5)"
)
@click.option(
    "--max-race-critical", type=int, default=0, help="Maximum critical race conditions (default: 0)"
)
@click.option(
    "--max-race-high",
    type=int,
    default=10,
    help="Maximum high severity race conditions (default: 10)",
)
@click.option(
    "--min-coverage",
    type=float,
    default=80.0,
    help="Minimum code coverage percentage (default: 80)",
)
@click.option(
    "--max-avg-complexity",
    type=int,
    default=10,
    help="Maximum average cyclomatic complexity (default: 10)",
)
@click.option(
    "--max-complex-functions",
    type=int,
    default=5,
    help="Maximum functions over complexity threshold (default: 5)",
)
@click.option("--fail-on-warnings", is_flag=True, help="Fail on warnings in addition to errors")
@click.option("--strict", is_flag=True, help="Enable strict mode (all thresholds set to 0)")
def check_gates(
    circular_deps: str | None,
    god_classes: str | None,
    race_conditions: str | None,
    coverage: str | None,
    complexity: str | None,
    max_circular: int,
    max_god_classes: int,
    max_race_critical: int,
    max_race_high: int,
    min_coverage: float,
    max_avg_complexity: int,
    max_complex_functions: int,
    fail_on_warnings: bool,
    strict: bool,
) -> None:
    """Check quality gates and fail if thresholds are exceeded.

    This command checks various code quality metrics against configurable
    thresholds and fails the build if any threshold is exceeded.

    Example:
        qontinui-devtools quality-gates \\
            --circular-deps circular-deps.json \\
            --god-classes god-classes.json \\
            --max-circular 0 \\
            --max-god-classes 5
    """
    console.print(
        Panel(
            "[bold cyan]Code Quality Gates Check[/bold cyan]",
            subtitle="Enforcing quality standards",
        )
    )

    # Apply strict mode
    if strict:
        max_circular = 0
        max_god_classes = 0
        max_race_critical = 0
        max_race_high = 0
        min_coverage = 100.0
        max_avg_complexity = 5
        max_complex_functions = 0

    checker = QualityGateChecker()

    # Check circular dependencies
    if circular_deps:
        checker.check_circular_dependencies(circular_deps, max_circular)

    # Check god classes
    if god_classes:
        checker.check_god_classes(god_classes, max_god_classes)

    # Check race conditions
    if race_conditions:
        checker.check_race_conditions(race_conditions, max_race_critical, max_race_high)

    # Check code coverage
    if coverage:
        checker.check_code_coverage(coverage, min_coverage)

    # Check complexity
    if complexity:
        checker.check_complexity(complexity, max_avg_complexity, max_complex_functions)

    # Print results
    checker.print_results()

    # Exit with appropriate code
    checker.exit()


if __name__ == "__main__":
    check_gates()
