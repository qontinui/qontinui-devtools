"""Generate PR comments with analysis results.

This module generates markdown-formatted comments for pull requests
that summarize code quality analysis results.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import click
from rich.console import Console

console = Console()


def format_trend(current: int, previous: int) -> str:
    """Format trend indicator for metrics.

    Args:
        current: Current value
        previous: Previous value

    Returns:
        Formatted trend string with emoji
    """
    if current < previous:
        diff = previous - current
        return f"📉 -{diff} (improved)"
    elif current > previous:
        diff = current - previous
        return f"📈 +{diff} (worse)"
    else:
        return "➡️ (no change)"


def get_status_emoji(count: int, thresholds: dict[str, int]) -> str:
    """Get status emoji based on count and thresholds.

    Args:
        count: Current count
        thresholds: Dictionary with 'error' and 'warning' thresholds

    Returns:
        Status emoji
    """
    if count <= thresholds.get("error", 0):
        return "✅"
    elif count <= thresholds.get("warning", 5):
        return "⚠️"
    else:
        return "❌"


def generate_circular_deps_section(
    data: dict[str, Any], previous: dict[str, Any] | None = None
) -> list[str]:
    """Generate circular dependencies section.

    Args:
        data: Circular dependency analysis results
        previous: Previous results for comparison

    Returns:
        List of markdown lines
    """
    lines: list[Any] = []
    cycles = data.get("cycles", [])
    count = len(cycles)

    thresholds = {"error": 0, "warning": 3}
    status = get_status_emoji(count, thresholds)

    lines.append(f"{status} **Circular Dependencies**: {count}")

    if previous:
        prev_count = len(previous.get("cycles", []))
        trend = format_trend(count, prev_count)
        lines.append(f"  - Trend: {trend}")

    if count > 0:
        lines.append("")
        lines.append("**Circular dependency cycles found:**")
        lines.append("")

        # Show first 5 cycles
        for i, cycle in enumerate(cycles[:5], 1):
            cycle_path = " → ".join(cycle)
            lines.append(f"{i}. `{cycle_path}`")

        if len(cycles) > 5:
            lines.append(f"  - ... and {len(cycles) - 5} more")

    return lines


def generate_god_classes_section(
    data: dict[str, Any], previous: dict[str, Any] | None = None
) -> list[str]:
    """Generate god classes section.

    Args:
        data: God class detection results
        previous: Previous results for comparison

    Returns:
        List of markdown lines
    """
    lines: list[Any] = []
    god_classes = data.get("god_classes", [])
    count = len(god_classes)

    thresholds = {"error": 5, "warning": 10}
    status = get_status_emoji(count, thresholds)

    lines.append(f"{status} **God Classes**: {count}")

    if previous:
        prev_count = len(previous.get("god_classes", []))
        trend = format_trend(count, prev_count)
        lines.append(f"  - Trend: {trend}")

    if count > 0:
        lines.append("")
        lines.append("**Large classes that should be refactored:**")
        lines.append("")

        # Show first 5 god classes
        for i, god_class in enumerate(god_classes[:5], 1):
            name = god_class.get("name", "Unknown")
            line_count = god_class.get("line_count", 0)
            method_count = god_class.get("method_count", 0)
            lines.append(f"{i}. `{name}` ({line_count} lines, {method_count} methods)")

        if len(god_classes) > 5:
            lines.append(f"  - ... and {len(god_classes) - 5} more")

    return lines


def generate_race_conditions_section(
    data: dict[str, Any], previous: dict[str, Any] | None = None
) -> list[str]:
    """Generate race conditions section.

    Args:
        data: Race condition detection results
        previous: Previous results for comparison

    Returns:
        List of markdown lines
    """
    lines: list[Any] = []
    races = data.get("races", [])

    critical = [r for r in races if r.get("severity") == "critical"]
    high = [r for r in races if r.get("severity") == "high"]
    medium = [r for r in races if r.get("severity") == "medium"]

    # Critical race conditions
    critical_count = len(critical)
    thresholds = {"error": 0, "warning": 2}
    status = get_status_emoji(critical_count, thresholds)
    lines.append(f"{status} **Critical Race Conditions**: {critical_count}")

    if previous:
        prev_critical = len(
            [r for r in previous.get("races", []) if r.get("severity") == "critical"]
        )
        trend = format_trend(critical_count, prev_critical)
        lines.append(f"  - Trend: {trend}")

    # High severity race conditions
    high_count = len(high)
    thresholds = {"error": 5, "warning": 10}
    status = get_status_emoji(high_count, thresholds)
    lines.append(f"{status} **High Severity Race Conditions**: {high_count}")

    # Medium severity race conditions
    lines.append(f"ℹ️ **Medium Severity Race Conditions**: {len(medium)}")

    if critical_count > 0:
        lines.append("")
        lines.append("**Critical race conditions (must fix):**")
        lines.append("")

        for i, race in enumerate(critical[:3], 1):
            location = race.get("location", "Unknown")
            description = race.get("description", "No description")
            lines.append(f"{i}. `{location}`: {description}")

        if len(critical) > 3:
            lines.append(f"  - ... and {len(critical) - 3} more")

    return lines


def generate_coverage_section(
    data: dict[str, Any], previous: dict[str, Any] | None = None
) -> list[str]:
    """Generate code coverage section.

    Args:
        data: Coverage analysis results
        previous: Previous results for comparison

    Returns:
        List of markdown lines
    """
    lines: list[Any] = []
    coverage = data.get("totals", {}).get("percent_covered", 0.0)

    if coverage >= 80:
        status = "✅"
    elif coverage >= 60:
        status = "⚠️"
    else:
        status = "❌"

    lines.append(f"{status} **Code Coverage**: {coverage:.1f}%")

    if previous:
        prev_coverage = previous.get("totals", {}).get("percent_covered", 0.0)
        diff = coverage - prev_coverage
        if diff > 0:
            lines.append(f"  - Trend: 📈 +{diff:.1f}% (improved)")
        elif diff < 0:
            lines.append(f"  - Trend: 📉 {diff:.1f}% (decreased)")
        else:
            lines.append("  - Trend: ➡️ (no change)")

    return lines


def generate_complexity_section(
    data: dict[str, Any], previous: dict[str, Any] | None = None
) -> list[str]:
    """Generate complexity section.

    Args:
        data: Complexity analysis results
        previous: Previous results for comparison

    Returns:
        List of markdown lines
    """
    lines: list[Any] = []
    avg_complexity = data.get("average_complexity", 0)

    if avg_complexity <= 5:
        status = "✅"
    elif avg_complexity <= 10:
        status = "⚠️"
    else:
        status = "❌"

    lines.append(f"{status} **Average Complexity**: {avg_complexity:.1f}")

    # High complexity functions
    functions = data.get("functions", [])
    high_complexity = [f for f in functions if f.get("complexity", 0) > 15]

    if high_complexity:
        lines.append(f"  - Functions over complexity 15: {len(high_complexity)}")

    return lines


def generate_pr_comment(
    circular_deps: dict[str, Any] | None = None,
    god_classes: dict[str, Any] | None = None,
    race_conditions: dict[str, Any] | None = None,
    coverage: dict[str, Any] | None = None,
    complexity: dict[str, Any] | None = None,
    previous_results: dict[str, Any] | None = None,
    pr_number: int | None = None,
    pr_title: str | None = None,
    base_branch: str = "main",
) -> str:
    """Generate markdown comment for PR.

    Args:
        circular_deps: Circular dependency results
        god_classes: God class detection results
        race_conditions: Race condition results
        coverage: Code coverage results
        complexity: Complexity analysis results
        previous_results: Results from base branch for comparison
        pr_number: Pull request number
        pr_title: Pull request title
        base_branch: Base branch name

    Returns:
        Markdown formatted comment
    """
    lines = [
        "## 📊 Code Quality Analysis",
        "",
    ]

    if pr_number and pr_title:
        lines.append(f"**PR #{pr_number}**: {pr_title}")
        lines.append("")

    lines.append("### Summary")
    lines.append("")

    # Get previous data if available
    prev_circular = previous_results.get("circular_deps") if previous_results else None
    prev_god = previous_results.get("god_classes") if previous_results else None
    prev_race = previous_results.get("race_conditions") if previous_results else None
    prev_coverage = previous_results.get("coverage") if previous_results else None
    prev_complexity = previous_results.get("complexity") if previous_results else None

    # Add sections
    if circular_deps:
        lines.extend(generate_circular_deps_section(circular_deps, prev_circular))

    if god_classes:
        lines.extend(generate_god_classes_section(god_classes, prev_god))

    if race_conditions:
        lines.extend(generate_race_conditions_section(race_conditions, prev_race))

    if coverage:
        lines.extend(generate_coverage_section(coverage, prev_coverage))

    if complexity:
        lines.extend(generate_complexity_section(complexity, prev_complexity))

    # Add recommendations
    lines.extend(
        [
            "",
            "### Recommendations",
            "",
        ]
    )

    recommendations: list[Any] = []

    if circular_deps and len(circular_deps.get("cycles", [])) > 0:
        recommendations.append("- 🔄 **Refactor circular dependencies** to improve modularity")

    if god_classes and len(god_classes.get("god_classes", [])) > 5:
        recommendations.append("- 🏗️ **Split god classes** into smaller, focused components")

    if race_conditions:
        critical = len(
            [r for r in race_conditions.get("races", []) if r.get("severity") == "critical"]
        )
        if critical > 0:
            recommendations.append("- 🚨 **Fix critical race conditions** before merging")

    if coverage and coverage.get("totals", {}).get("percent_covered", 100) < 80:
        recommendations.append("- 🧪 **Increase test coverage** to at least 80%")

    if recommendations:
        lines.extend(recommendations)
    else:
        lines.append("✅ No critical issues found!")

    # Footer
    lines.extend(
        [
            "",
            "---",
            f"*Generated by [qontinui-devtools](https://github.com/qontinui/qontinui-devtools) at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        ]
    )

    return "\n".join(lines)


@click.command()
@click.option(
    "--circular-deps", type=click.Path(exists=True), help="Path to circular dependencies JSON"
)
@click.option("--god-classes", type=click.Path(exists=True), help="Path to god classes JSON")
@click.option(
    "--race-conditions", type=click.Path(exists=True), help="Path to race conditions JSON"
)
@click.option("--coverage", type=click.Path(exists=True), help="Path to coverage JSON")
@click.option("--complexity", type=click.Path(exists=True), help="Path to complexity JSON")
@click.option(
    "--previous-results",
    type=click.Path(exists=True),
    help="Path to previous results JSON for trend comparison",
)
@click.option(
    "--output",
    type=click.Path(),
    default="pr-comment.md",
    help="Output file for PR comment (default: pr-comment.md)",
)
@click.option("--pr-number", type=int, help="Pull request number")
@click.option("--pr-title", type=str, help="Pull request title")
@click.option("--base-branch", type=str, default="main", help="Base branch name (default: main)")
def generate_comment(
    circular_deps: str | None,
    god_classes: str | None,
    race_conditions: str | None,
    coverage: str | None,
    complexity: str | None,
    previous_results: str | None,
    output: str,
    pr_number: int | None,
    pr_title: str | None,
    base_branch: str,
) -> None:
    """Generate a markdown comment for pull requests.

    This command generates a comprehensive markdown comment summarizing
    code quality analysis results for posting to pull requests.

    Example:
        qontinui-devtools pr-comment \\
            --circular-deps circular-deps.json \\
            --god-classes god-classes.json \\
            --output comment.md
    """
    console.print("[cyan]Generating PR comment...[/cyan]")

    # Load data files
    circular_data = None
    if circular_deps:
        circular_data = json.loads(Path(circular_deps).read_text())

    god_data = None
    if god_classes:
        god_data = json.loads(Path(god_classes).read_text())

    race_data = None
    if race_conditions:
        race_data = json.loads(Path(race_conditions).read_text())

    coverage_data = None
    if coverage:
        coverage_data = json.loads(Path(coverage).read_text())

    complexity_data = None
    if complexity:
        complexity_data = json.loads(Path(complexity).read_text())

    previous_data = None
    if previous_results:
        previous_data = json.loads(Path(previous_results).read_text())

    # Generate comment
    comment = generate_pr_comment(
        circular_deps=circular_data,
        god_classes=god_data,
        race_conditions=race_data,
        coverage=coverage_data,
        complexity=complexity_data,
        previous_results=previous_data,
        pr_number=pr_number,
        pr_title=pr_title,
        base_branch=base_branch,
    )

    # Write to file
    Path(output).write_text(comment)

    console.print(f"[green]✅ PR comment generated: {output}[/green]")

    # Print preview
    console.print("\n[cyan]Preview:[/cyan]")
    console.print(comment)


if __name__ == "__main__":
    generate_comment()
