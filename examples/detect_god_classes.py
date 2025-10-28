"""Example script for detecting god classes in a codebase."""

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from qontinui_devtools.architecture import GodClassDetector

console = Console()


def main() -> None:
    """Analyze a codebase for god classes."""
    # Configure detector with custom thresholds
    detector = GodClassDetector(
        min_lines=500,      # Flag classes with 500+ lines
        min_methods=20,     # Flag classes with 20+ methods
        max_lcom=0.8,       # Flag classes with LCOM > 0.8
        verbose=True
    )

    # Analyze directory (replace with your path)
    # Example: "../qontinui/src"
    target_path = input("Enter path to analyze: ")

    console.print(Panel(
        f"[cyan]Analyzing:[/cyan] {target_path}\n"
        f"[cyan]Min Lines:[/cyan] {detector.min_lines}\n"
        f"[cyan]Min Methods:[/cyan] {detector.min_methods}\n"
        f"[cyan]Max LCOM:[/cyan] {detector.max_lcom}",
        title="God Class Detection",
        border_style="blue"
    ))

    with console.status("[bold green]Scanning files..."):
        god_classes = detector.analyze_directory(target_path)

    if not god_classes:
        console.print("\n[green]✅ No god classes detected! Your codebase is well-structured.[/green]")
        return

    console.print(f"\n[red]❌ Found {len(god_classes)} god classes:[/red]\n")

    # Create summary table
    table = Table(title="God Classes Summary", show_header=True, header_style="bold magenta")
    table.add_column("Class", style="cyan", no_wrap=True)
    table.add_column("Lines", justify="right", style="yellow")
    table.add_column("Methods", justify="right", style="yellow")
    table.add_column("LCOM", justify="right", style="red")
    table.add_column("Severity", style="bold")

    for cls in god_classes:
        severity_color = {
            "critical": "[red]CRITICAL[/red]",
            "high": "[yellow]HIGH[/yellow]",
            "medium": "[blue]MEDIUM[/blue]"
        }[cls.severity]

        table.add_row(
            cls.name,
            str(cls.line_count),
            str(cls.method_count),
            f"{cls.lcom:.2f}",
            severity_color
        )

    console.print(table)
    console.print()

    # Show detailed analysis for each god class
    for i, cls in enumerate(god_classes, 1):
        color = {"critical": "red", "high": "yellow", "medium": "blue"}[cls.severity]

        console.print(f"\n[bold {color}]{i}. {cls.name}[/bold {color}]")
        console.print(f"[dim]File: {cls.file_path}:{cls.line_start}[/dim]\n")

        # Metrics
        console.print("[bold]Metrics:[/bold]")
        console.print(f"  Lines of Code: {cls.line_count}")
        console.print(f"  Method Count: {cls.method_count}")
        console.print(f"  Attribute Count: {cls.attribute_count}")
        console.print(f"  Cyclomatic Complexity: {cls.cyclomatic_complexity}")
        console.print(f"  LCOM (Lack of Cohesion): {cls.lcom:.3f}")

        # Responsibilities
        if cls.responsibilities:
            console.print("\n[bold]Detected Responsibilities:[/bold]")
            for resp in cls.responsibilities:
                console.print(f"  • {resp}")

        # Extraction suggestions
        suggestions = detector.suggest_extractions(cls)
        if suggestions:
            console.print("\n[bold green]Refactoring Suggestions:[/bold green]")
            for j, sug in enumerate(suggestions[:5], 1):
                console.print(f"\n  {j}. Extract → [cyan]{sug.new_class_name}[/cyan]")
                console.print(f"     Responsibility: {sug.responsibility}")
                console.print(f"     Methods: {len(sug.methods_to_extract)}")
                console.print(f"     Estimated Lines: {sug.estimated_lines}")
                console.print(f"     Example methods: {', '.join(sug.methods_to_extract[:5])}")

        console.print("\n" + "─" * 80)

    # Generate markdown report
    console.print("\n[bold]Generating Report...[/bold]")
    report = detector.generate_report(god_classes)

    report_path = Path("god_class_report.md")
    report_path.write_text(report)

    console.print(f"[green]✅ Report saved to:[/green] {report_path.absolute()}")


if __name__ == "__main__":
    main()
