"""Pre-commit hooks for qontinui-devtools.

from typing import Any, Any

This module provides pre-commit hooks for local development to catch
code quality issues before they are committed.
"""

import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import click
from rich.console import Console

console = Console()


def get_staged_python_files() -> list[str]:
    """Get list of staged Python files.

    Returns:
        List of staged Python file paths
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            text=True,
            check=True,
        )

        files = result.stdout.strip().split("\n")
        python_files = [f for f in files if f.endswith(".py") and Path(f).exists()]

        return python_files
    except subprocess.CalledProcessError:
        console.print("[red]Error: Failed to get staged files[/red]")
        return []


def get_git_root() -> Path | None:
    """Get the git repository root directory.

    Returns:
        Path to git root or None if not in a git repo
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        return None


@click.command()
@click.argument("filenames", nargs=-1)
def check_circular_imports(filenames: Sequence[str]) -> None:
    """Check for circular imports in staged files.

    Args:
        filenames: Optional list of filenames to check
    """
    console.print("[cyan]Checking for circular imports...[/cyan]")

    # Get files to check
    if filenames:
        files_to_check = [f for f in filenames if f.endswith(".py")]
    else:
        files_to_check = get_staged_python_files()

    if not files_to_check:
        console.print("[yellow]No Python files to check[/yellow]")
        sys.exit(0)

    # Get git root for context
    git_root = get_git_root()
    if not git_root:
        console.print("[red]Error: Not in a git repository[/red]")
        sys.exit(1)

    # Try to import and run the circular dependency detector
    try:
        from qontinui_devtools.import_analysis import \
            CircularDependencyDetector

        detector = CircularDependencyDetector(str(git_root))
        cycles = detector.analyze()

        if cycles:
            console.print(f"[red]❌ Found {len(cycles)} circular dependencies:[/red]")
            for i, cycle in enumerate(cycles, 1):
                cycle_path = " → ".join(cycle.cycle)
                console.print(f"  {i}. {cycle_path}")
            sys.exit(1)
        else:
            console.print("[green]✅ No circular imports found[/green]")
            sys.exit(0)

    except ImportError:
        console.print("[yellow]Warning: qontinui-devtools not installed, skipping check[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Error checking circular imports: {e}[/red]")
        sys.exit(1)


@click.command()
@click.argument("filenames", nargs=-1)
@click.option(
    "--min-lines",
    type=int,
    default=500,
    help="Minimum lines to consider a god class (default: 500)",
)
@click.option(
    "--min-methods",
    type=int,
    default=30,
    help="Minimum methods to consider a god class (default: 30)",
)
def check_new_god_classes(filenames: Sequence[str], min_lines: int, min_methods: int) -> None:
    """Check if any staged files contain god classes.

    Args:
        filenames: Optional list of filenames to check
        min_lines: Minimum lines to flag as god class
        min_methods: Minimum methods to flag as god class
    """
    console.print("[cyan]Checking for god classes...[/cyan]")

    # Get files to check
    if filenames:
        files_to_check = [f for f in filenames if f.endswith(".py")]
    else:
        files_to_check = get_staged_python_files()

    if not files_to_check:
        console.print("[yellow]No Python files to check[/yellow]")
        sys.exit(0)

    # Try to import and run the god class detector
    try:
        from qontinui_devtools.architecture.god_class_detector import \
            GodClassDetector

        detector = GodClassDetector(min_lines=min_lines, min_methods=min_methods)

        found_god_classes: list[Any] = []

        for file in files_to_check:
            file_path = Path(file)
            if not file_path.exists():
                continue

            god_classes = detector.analyze_file(str(file_path))
            if god_classes:
                found_god_classes.extend(god_classes)

        if found_god_classes:
            console.print(f"[red]❌ Found {len(found_god_classes)} god classes:[/red]")
            for god_class in found_god_classes:
                console.print(f"  • {god_class.name} in {god_class.file_path}")
                console.print(
                    f"    ({god_class.line_count} lines, " f"{god_class.method_count} methods)"
                )
            console.print(
                "\n[yellow]Consider refactoring large classes into "
                "smaller, focused components[/yellow]"
            )
            sys.exit(1)
        else:
            console.print("[green]✅ No god classes found[/green]")
            sys.exit(0)

    except ImportError:
        console.print("[yellow]Warning: qontinui-devtools not installed, skipping check[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Error checking god classes: {e}[/red]")
        sys.exit(1)


@click.command()
@click.argument("filenames", nargs=-1)
@click.option(
    "--severity",
    type=click.Choice(["critical", "high", "medium", "low"]),
    default="high",
    help="Minimum severity to fail on (default: high)",
)
def check_race_conditions(filenames: Sequence[str], severity: str) -> None:
    """Check for race conditions in staged files.

    Args:
        filenames: Optional list of filenames to check
        severity: Minimum severity to fail on
    """
    console.print("[cyan]Checking for race conditions...[/cyan]")

    # Get files to check
    if filenames:
        files_to_check = [f for f in filenames if f.endswith(".py")]
    else:
        files_to_check = get_staged_python_files()

    if not files_to_check:
        console.print("[yellow]No Python files to check[/yellow]")
        sys.exit(0)

    # Severity levels
    severity_levels = {
        "critical": 3,
        "high": 2,
        "medium": 1,
        "low": 0,
    }
    min_severity_level = severity_levels.get(severity, 2)

    # Try to import and run the race condition detector
    try:
        from qontinui_devtools.concurrency.race_detector import \
            RaceConditionDetector

        detector = RaceConditionDetector()

        found_issues: list[Any] = []

        for file in files_to_check:
            file_path = Path(file)
            if not file_path.exists():
                continue

            races = detector.analyze_file(str(file_path))

            for race in races:
                race_severity_level = severity_levels.get(race.severity.lower(), 0)
                if race_severity_level >= min_severity_level:
                    found_issues.append((file, race))

        if found_issues:
            console.print(
                f"[red]❌ Found {len(found_issues)} race condition(s) "
                f"with severity >= {severity}:[/red]"
            )
            for file, race in found_issues:
                console.print(f"  • [{race.severity.upper()}] in {file}")
                console.print(f"    {race.description}")
                if race.location:
                    console.print(f"    Location: {race.location}")

            console.print(
                "\n[yellow]Add proper synchronization to prevent race conditions[/yellow]"
            )
            sys.exit(1)
        else:
            console.print(f"[green]✅ No race conditions found (severity >= {severity})[/green]")
            sys.exit(0)

    except ImportError:
        console.print("[yellow]Warning: qontinui-devtools not installed, skipping check[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Error checking race conditions: {e}[/red]")
        sys.exit(1)


@click.command()
@click.argument("filenames", nargs=-1)
@click.option(
    "--max-complexity",
    type=int,
    default=15,
    help="Maximum cyclomatic complexity allowed (default: 15)",
)
def check_complexity(filenames: Sequence[str], max_complexity: int) -> None:
    """Check cyclomatic complexity of staged files.

    Args:
        filenames: Optional list of filenames to check
        max_complexity: Maximum allowed complexity
    """
    console.print("[cyan]Checking code complexity...[/cyan]")

    # Get files to check
    if filenames:
        files_to_check = [f for f in filenames if f.endswith(".py")]
    else:
        files_to_check = get_staged_python_files()

    if not files_to_check:
        console.print("[yellow]No Python files to check[/yellow]")
        sys.exit(0)

    # Use radon or similar tool to check complexity
    try:
        import radon.complexity as radon_complexity

        high_complexity_functions: list[Any] = []

        for file in files_to_check:
            file_path = Path(file)
            if not file_path.exists():
                continue

            with open(file_path) as f:
                code = f.read()

            results = radon_complexity.cc_visit(code)

            for result in results:
                if result.complexity > max_complexity:
                    high_complexity_functions.append((file, result))

        if high_complexity_functions:
            console.print(
                f"[red]❌ Found {len(high_complexity_functions)} functions "
                f"with complexity > {max_complexity}:[/red]"
            )
            for file, result in high_complexity_functions:
                console.print(f"  • {result.name} in {file} " f"(complexity: {result.complexity})")

            console.print(
                "\n[yellow]Consider refactoring complex functions into "
                "smaller, simpler ones[/yellow]"
            )
            sys.exit(1)
        else:
            console.print(f"[green]✅ All functions have complexity <= {max_complexity}[/green]")
            sys.exit(0)

    except ImportError:
        console.print("[yellow]Warning: radon not installed, skipping complexity check[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Error checking complexity: {e}[/red]")
        sys.exit(1)


@click.group()
def main() -> None:
    """Pre-commit hooks for qontinui-devtools."""
    pass


# Register commands
main.add_command(check_circular_imports)
main.add_command(check_new_god_classes)
main.add_command(check_race_conditions)
main.add_command(check_complexity)


if __name__ == "__main__":
    main()
