#!/usr/bin/env python3
"""Example: Profile action execution performance using ActionProfiler.

This example demonstrates how to use the ActionProfiler to measure timing,
CPU usage, and memory consumption of automation actions.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

from qontinui_devtools.runtime import (ActionProfiler, calculate_metrics,
                                       format_duration, format_memory)
from rich.console import Console
from rich.table import Table

console = Console()


def simulate_click_action() -> None:
    """Simulate a click action with multiple phases."""
    # Simulate finding element
    time.sleep(0.01)

    # Simulate moving to element
    time.sleep(0.02)

    # Simulate click
    time.sleep(0.01)


def simulate_type_action(text: str) -> None:
    """Simulate typing text."""
    # Simulate finding input field
    time.sleep(0.01)

    # Simulate typing (proportional to text length)
    time.sleep(0.005 * len(text))


def simulate_scroll_action() -> None:
    """Simulate scrolling."""
    time.sleep(0.015)


def main() -> None:
    """Run profiling example."""
    console.print("[bold cyan]Action Profiler Example[/bold cyan]\n")

    # Create profiler
    profiler = ActionProfiler(
        enable_memory=True,
        enable_cpu=True,
        enable_stack_sampling=False,  # Disable for this example
    )

    # Start profiling session
    session_id = profiler.start_session()
    console.print(f"[green]Started session:[/green] {session_id}\n")

    # Profile multiple actions
    console.print("[yellow]Profiling actions...[/yellow]\n")

    # Profile 10 click actions
    for i in range(10):
        with profiler.profile_action("click", f"button_{i}") as profile:
            # Simulate action execution
            simulate_click_action()

            # Track individual phases
            profile.phases["find"] = 0.01
            profile.phases["move"] = 0.02
            profile.phases["click"] = 0.01

    # Profile 5 type actions
    for i in range(5):
        with profiler.profile_action("type", f"input_{i}") as profile:
            text = f"Test text {i}"
            simulate_type_action(text)

            profile.phases["find"] = 0.01
            profile.phases["type"] = 0.005 * len(text)

    # Profile 3 scroll actions
    for i in range(3):
        with profiler.profile_action("scroll", f"scroll_{i}") as profile:
            simulate_scroll_action()

            profile.phases["scroll"] = 0.015

    # End session and get results
    session = profiler.end_session()
    console.print(f"[green]Session ended:[/green] {len(session.profiles)} actions profiled\n")

    # Calculate metrics
    metrics = calculate_metrics(session.profiles)

    # Display summary
    console.print("[bold]Performance Summary[/bold]\n")

    summary_table = Table(show_header=False, box=None)
    summary_table.add_column("Metric", style="cyan", width=25)
    summary_table.add_column("Value", style="green")

    summary_table.add_row("Total Actions", str(metrics.total_actions))
    summary_table.add_row("Total Duration", format_duration(metrics.total_duration))
    summary_table.add_row("Avg Duration", format_duration(metrics.avg_duration))
    summary_table.add_row("Min Duration", format_duration(metrics.min_duration))
    summary_table.add_row("Max Duration", format_duration(metrics.max_duration))
    summary_table.add_row("P50 (Median)", format_duration(metrics.p50_duration))
    summary_table.add_row("P95", format_duration(metrics.p95_duration))
    summary_table.add_row("P99", format_duration(metrics.p99_duration))
    summary_table.add_row("CPU Utilization", f"{metrics.cpu_utilization * 100:.1f}%")
    summary_table.add_row("Memory Delta", format_memory(metrics.total_memory_delta))
    summary_table.add_row("Actions/sec", f"{metrics.actions_per_second:.2f}")

    console.print(summary_table)
    console.print()

    # Show slowest actions
    console.print("[bold]Slowest Actions:[/bold]")
    for action_id, duration in metrics.slowest_actions[:5]:
        console.print(f"  • {action_id}: {format_duration(duration)}")
    console.print()

    # Export to JSON
    output_file = "profile_results.json"
    profiler.export_to_json(output_file)
    console.print(f"[blue]Results exported to:[/blue] {output_file}\n")

    console.print("[bold green]Profiling complete![/bold green]")


if __name__ == "__main__":
    main()
