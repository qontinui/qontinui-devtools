"""Command-line interface for Qontinui DevTools."""

import sys
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.tree import Tree

console = Console()


@click.group()
@click.version_option(version="1.1.0")
def main() -> None:
    """Qontinui DevTools - Analysis and debugging tools for Qontinui.

    A comprehensive suite of tools for analyzing imports, detecting race conditions,
    profiling performance, and testing Qontinui applications.

    Examples:

        # Check for circular dependencies
        qontinui-devtools import check ./src

        # Analyze race conditions
        qontinui-devtools concurrency check ./src

        # Run comprehensive analysis
        qontinui-devtools analyze ./src --report report.html
    """
    pass


@main.group()
def import_cmd() -> None:
    """Import analysis commands.

    Tools for analyzing Python imports, detecting circular dependencies,
    and visualizing import graphs.
    """
    pass


@import_cmd.command("check")
@click.argument("path", type=click.Path(exists=True))
@click.option("--strict", is_flag=True, help="Exit with error code if issues found")
@click.option("--output", type=click.Path(), help="Save report to file")
@click.option("--format",
              type=click.Choice(["text", "json", "html"], case_sensitive=False),
              default="text",
              help="Output format")
def check_imports(path: str, strict: bool, output: str | None, format: str) -> None:
    """Check for circular dependencies in Python code.

    Analyzes Python files to detect circular import dependencies that can
    cause import errors and make code harder to maintain.

    Examples:

        # Basic check
        qontinui-devtools import check ./src

        # Strict mode (exit with error if issues found)
        qontinui-devtools import check ./src --strict

        # Save report to file
        qontinui-devtools import check ./src --output report.json --format json
    """
    try:
        from .import_analysis import CircularDependencyDetector
    except ImportError:
        console.print("[red]Error: Import analysis module not available[/red]")
        sys.exit(1)

    try:
        detector = CircularDependencyDetector(path, verbose=True)
        cycles = detector.analyze()

        # Use the rich report from detector
        detector.generate_rich_report(cycles)

        # Save report if requested
        if output:
            if format == "text":
                report_text = detector.generate_report(cycles)
                Path(output).write_text(report_text)
            else:
                save_report(cycles, output, format, detector)
            console.print(f"[green]Report saved to:[/green] {output}")

        # Print statistics
        stats = detector.get_statistics()
        console.print("\n[bold]Statistics:[/bold]")
        console.print(f"  Files scanned: {stats['total_files']}")
        console.print(f"  Total imports: {stats['total_imports']}")
        console.print(f"  Dependencies: {stats['total_dependencies']}")
        console.print(f"  Cycles found: {stats['cycles_found']}")

        if cycles and strict:
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error during analysis:[/red] {e}")
        if strict:
            sys.exit(1)


@import_cmd.command("trace")
@click.argument("module")
@click.option("--visualize", is_flag=True, help="Generate visual graph")
@click.option("--output", default="import_graph.png", help="Output file for graph")
@click.option("--depth", type=int, default=None, help="Maximum depth to trace")
@click.option("--exclude", multiple=True, help="Patterns to exclude from trace")
def trace_imports(
    module: str,
    visualize: bool,
    output: str,
    depth: int | None,
    exclude: tuple[str, ...]
) -> None:
    """Trace imports from a module at runtime.

    Uses import hooks to trace all imports when a module is loaded,
    useful for understanding complex import chains and detecting issues.

    Examples:

        # Trace imports
        qontinui-devtools import trace mypackage.mymodule

        # Trace and visualize
        qontinui-devtools import trace mypackage.mymodule --visualize

        # Limit depth and exclude patterns
        qontinui-devtools import trace mypackage --depth 3 --exclude "test_*"
    """
    try:
        from .import_analysis import ImportTracer
    except ImportError:
        console.print("[red]Error: Import analysis module not available[/red]")
        sys.exit(1)

    console.print(f"[bold cyan]Tracing imports from:[/bold cyan] {module}\n")

    try:
        with ImportTracer() as tracer:
            __import__(module)

        events = tracer.get_events()
        cycles = tracer.find_circular_dependencies()

        console.print(f"[green]✅ Imported {len(events)} modules[/green]\n")

        if cycles:
            console.print(f"[red]❌ Circular dependencies detected:[/red]")
            for cycle in cycles:
                console.print(f"  {' → '.join(cycle)}")
        else:
            console.print("[green]✅ No circular dependencies[/green]")

        if visualize:
            tracer.visualize(output)
            console.print(f"\n[blue]📊 Graph saved to:[/blue] {output}")

    except ImportError as e:
        console.print(f"[red]Failed to import module:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error during trace:[/red] {e}")
        sys.exit(1)


@import_cmd.command("graph")
@click.argument("path", type=click.Path(exists=True))
@click.option("--output", default="dependency_graph.png", help="Output file")
@click.option("--format",
              type=click.Choice(["png", "svg", "pdf"], case_sensitive=False),
              default="png",
              help="Output format")
@click.option("--clusters/--no-clusters", default=True, help="Group by package")
def graph_imports(path: str, output: str, format: str, clusters: bool) -> None:
    """Generate visual dependency graph.

    Creates a visual representation of import dependencies in your codebase,
    making it easier to understand architecture and identify problem areas.

    Examples:

        # Generate PNG graph
        qontinui-devtools import graph ./src

        # Generate SVG with custom output
        qontinui-devtools import graph ./src --output deps.svg --format svg
    """
    console.print(f"[bold cyan]Generating dependency graph for:[/bold cyan] {path}")
    console.print("[yellow]This feature is coming soon![/yellow]")


@main.group()
def concurrency() -> None:
    """Concurrency analysis commands.

    Tools for detecting race conditions, deadlocks, and other concurrency issues
    in multi-threaded code.
    """
    pass


@concurrency.command("check")
@click.argument("path", type=click.Path(exists=True))
@click.option("--severity",
              type=click.Choice(["low", "medium", "high", "critical"], case_sensitive=False),
              default="medium",
              help="Minimum severity to report")
@click.option("--output", type=click.Path(), help="Save report to file")
@click.option("--detailed", is_flag=True, help="Show detailed analysis")
def check_concurrency(
    path: str,
    severity: str,
    output: str | None,
    detailed: bool
) -> None:
    """Check for race conditions and concurrency issues.

    Performs static analysis to detect potential race conditions, missing locks,
    and other thread-safety issues in your code.

    Examples:

        # Basic check
        qontinui-devtools concurrency check ./src

        # Only show critical issues
        qontinui-devtools concurrency check ./src --severity critical

        # Detailed output
        qontinui-devtools concurrency check ./src --detailed
    """
    try:
        from .concurrency import RaceConditionDetector
    except ImportError:
        console.print("[red]Error: Concurrency analysis module not available[/red]")
        sys.exit(1)

    console.print(f"[bold cyan]Analyzing concurrency in:[/bold cyan] {path}\n")

    try:
        detector = RaceConditionDetector(path)
        races = detector.analyze()

        # Filter by severity
        severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        min_level = severity_order.get(severity.lower(), 1)
        races = [r for r in races if severity_order[r.severity] >= min_level]

        if races:
            console.print(f"[red]⚠️  Found {len(races)} potential race conditions:[/red]\n")

            severity_colors = {
                "critical": "red",
                "high": "yellow",
                "medium": "blue",
                "low": "dim"
            }

            for race in races:
                color = severity_colors[race.severity]
                panel_content = [
                    f"[{color}]Severity:[/{color}] {race.severity.upper()}",
                    f"[cyan]Description:[/cyan] {race.description}",
                    f"[cyan]State:[/cyan] {race.shared_state.name}",
                    f"[cyan]Location:[/cyan] {race.shared_state.file_path}:{race.shared_state.line_number}",
                ]

                if detailed:
                    panel_content.extend([
                        f"\n[green]Suggestion:[/green]",
                        race.suggestion
                    ])

                console.print(Panel(
                    "\n".join(panel_content),
                    border_style=color,
                    title=f"Race Condition in {race.shared_state.name}"
                ))
                console.print()
        else:
            console.print("[green]✅ No race conditions detected[/green]")

    except Exception as e:
        console.print(f"[red]Error during analysis:[/red] {e}")
        sys.exit(1)


@concurrency.command("deadlock")
@click.argument("path", type=click.Path(exists=True))
@click.option("--visualize", is_flag=True, help="Generate lock dependency graph")
def check_deadlock(path: str, visualize: bool) -> None:
    """Detect potential deadlocks.

    Analyzes lock acquisition patterns to find potential deadlock scenarios
    where threads might wait for each other indefinitely.

    Examples:

        # Check for deadlocks
        qontinui-devtools concurrency deadlock ./src

        # Visualize lock dependencies
        qontinui-devtools concurrency deadlock ./src --visualize
    """
    console.print(f"[bold cyan]Analyzing deadlock potential in:[/bold cyan] {path}")
    console.print("[yellow]This feature is coming soon![/yellow]")


@main.group()
def test() -> None:
    """Testing commands.

    Tools for stress testing, race condition testing, and other
    dynamic analysis techniques.
    """
    pass


@test.command("race")
@click.option("--threads", default=10, help="Number of concurrent threads")
@click.option("--iterations", default=100, help="Iterations per thread")
@click.option("--target", required=True, help="Target function (module:function)")
@click.option("--timeout", default=30, help="Timeout in seconds")
def test_race(threads: int, iterations: int, target: str, timeout: int) -> None:
    """Run race condition stress test.

    Executes a function concurrently from multiple threads to detect
    race conditions that might not appear in normal testing.

    Examples:

        # Test a function
        qontinui-devtools test race --target mymodule:my_function

        # Heavy stress test
        qontinui-devtools test race --target mymodule:my_function --threads 50 --iterations 1000
    """
    try:
        from .concurrency import RaceConditionTester
    except ImportError:
        console.print("[red]Error: Concurrency testing module not available[/red]")
        sys.exit(1)

    console.print(Panel(
        f"[cyan]Threads:[/cyan] {threads}\n"
        f"[cyan]Iterations:[/cyan] {iterations}\n"
        f"[cyan]Target:[/cyan] {target}\n"
        f"[cyan]Timeout:[/cyan] {timeout}s",
        title="Race Condition Test Configuration",
        border_style="blue"
    ))
    console.print()

    try:
        # Parse target
        if ":" not in target:
            console.print("[red]Error: Target must be in format 'module:function'[/red]")
            sys.exit(1)

        module_name, func_name = target.rsplit(":", 1)
        module = __import__(module_name, fromlist=[func_name])
        func = getattr(module, func_name)

        # Run test
        tester = RaceConditionTester(threads=threads, iterations=iterations)

        with console.status("[bold green]Running tests..."):
            result = tester.test_function(func)

        # Display results
        table = Table(title="Test Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right", style="green")

        table.add_row("Total Iterations", str(result.total_iterations))
        table.add_row("Successful", str(result.successful))
        table.add_row("Failed", str(result.failed))
        table.add_row("Success Rate", f"{result.successful/result.total_iterations*100:.1f}%")

        console.print(table)
        console.print()

        if result.race_detected:
            console.print(Panel(
                "[red]❌ Race condition detected![/red]\n\n" +
                "\n".join(f"• {detail}" for detail in result.failure_details),
                border_style="red",
                title="Race Condition"
            ))
            sys.exit(1)
        else:
            console.print("[green]✅ No race conditions detected[/green]")

    except (ImportError, AttributeError) as e:
        console.print(f"[red]Failed to load target function:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error during test:[/red] {e}")
        sys.exit(1)


@test.command("stress")
@click.argument("path", type=click.Path(exists=True))
@click.option("--duration", default=60, help="Test duration in seconds")
@click.option("--workers", default=4, help="Number of worker processes")
def stress_test(path: str, duration: int, workers: int) -> None:
    """Run stress test on code.

    Performs sustained load testing to identify performance degradation,
    memory leaks, and stability issues under stress.

    Examples:

        # 1-minute stress test
        qontinui-devtools test stress ./tests/test_suite.py

        # 10-minute test with 8 workers
        qontinui-devtools test stress ./tests --duration 600 --workers 8
    """
    console.print(f"[bold cyan]Running stress test:[/bold cyan] {path}")
    console.print("[yellow]This feature is coming soon![/yellow]")


@main.command("analyze")
@click.argument("path", type=click.Path(exists=True))
@click.option("--report", type=click.Path(), help="Generate HTML report")
@click.option("--format",
              type=click.Choice(["text", "json", "html"], case_sensitive=False),
              default="text",
              help="Output format")
@click.option("--checks",
              multiple=True,
              type=click.Choice(["imports", "concurrency", "complexity", "all"]),
              default=["all"],
              help="Checks to run")
def analyze(
    path: str,
    report: str | None,
    format: str,
    checks: tuple[str, ...]
) -> None:
    """Run comprehensive analysis on codebase.

    Performs multiple static analysis checks including import analysis,
    concurrency checks, and code complexity metrics.

    Examples:

        # Full analysis
        qontinui-devtools analyze ./src

        # Generate HTML report
        qontinui-devtools analyze ./src --report report.html --format html

        # Run specific checks
        qontinui-devtools analyze ./src --checks imports --checks concurrency
    """
    console.print(Panel(
        f"[bold cyan]Path:[/bold cyan] {path}\n"
        f"[bold cyan]Checks:[/bold cyan] {', '.join(checks)}\n"
        f"[bold cyan]Format:[/bold cyan] {format}",
        title="Comprehensive Analysis",
        border_style="cyan"
    ))
    console.print()

    # Determine which checks to run
    run_all = "all" in checks
    run_imports = run_all or "imports" in checks
    run_concurrency = run_all or "concurrency" in checks
    run_complexity = run_all or "complexity" in checks

    results: dict[str, Any] = {}

    # Import analysis
    if run_imports:
        try:
            from .import_analysis import CircularDependencyDetector

            with console.status("[bold green]Analyzing imports..."):
                import_detector = CircularDependencyDetector(path, verbose=False)
                import_cycles = import_detector.analyze()

            results["imports"] = {
                "cycles": len(import_cycles),
                "status": "FAIL" if import_cycles else "PASS"
            }
        except Exception as e:
            console.print(f"[yellow]Warning: Import analysis failed:[/yellow] {e}")
            results["imports"] = {"status": "ERROR", "error": str(e)}

    # Concurrency analysis
    if run_concurrency:
        try:
            from .concurrency import RaceConditionDetector

            with console.status("[bold green]Analyzing concurrency..."):
                race_detector = RaceConditionDetector(path)
                races = race_detector.analyze()

            results["concurrency"] = {
                "races": len(races),
                "status": "FAIL" if races else "PASS"
            }
        except Exception as e:
            console.print(f"[yellow]Warning: Concurrency analysis failed:[/yellow] {e}")
            results["concurrency"] = {"status": "ERROR", "error": str(e)}

    # Display summary
    table = Table(title="Analysis Summary", show_header=True, header_style="bold magenta")
    table.add_column("Check", style="cyan", width=20)
    table.add_column("Status", style="bold", width=10)
    table.add_column("Issues", justify="right", width=10)
    table.add_column("Details", width=40)

    if "imports" in results:
        status = results["imports"]["status"]
        status_color = "[green]✓" if status == "PASS" else "[red]✗" if status == "FAIL" else "[yellow]⚠"
        issues = results["imports"].get("cycles", "N/A")
        details = f"Found {issues} circular dependencies" if status == "FAIL" else "No issues"
        table.add_row("Circular Dependencies", f"{status_color} {status}", str(issues), details)

    if "concurrency" in results:
        status = results["concurrency"]["status"]
        status_color = "[green]✓" if status == "PASS" else "[red]✗" if status == "FAIL" else "[yellow]⚠"
        issues = results["concurrency"].get("races", "N/A")
        details = f"Found {issues} potential races" if status == "FAIL" else "No issues"
        table.add_row("Race Conditions", f"{status_color} {status}", str(issues), details)

    console.print(table)
    console.print()

    # Generate report if requested
    if report:
        console.print(f"[blue]📄 Generating report:[/blue] {report}")
        try:
            generate_report(results, report, format)
            console.print(f"[green]✅ Report saved successfully[/green]")
        except Exception as e:
            console.print(f"[red]Failed to generate report:[/red] {e}")


@main.group()
def profile() -> None:
    """Performance profiling commands.

    Tools for profiling CPU usage, memory consumption, and identifying
    performance bottlenecks.
    """
    pass


@profile.command("cpu")
@click.argument("target")
@click.option("--duration", default=10, help="Profile duration in seconds")
@click.option("--output", default="profile.svg", help="Output file")
def profile_cpu(target: str, duration: int, output: str) -> None:
    """Profile CPU usage of a running process or script.

    Examples:

        # Profile a Python script
        qontinui-devtools profile cpu script.py --duration 30

        # Profile running process
        qontinui-devtools profile cpu --target pid:1234
    """
    console.print(f"[bold cyan]Profiling CPU usage:[/bold cyan] {target}")
    console.print("[yellow]This feature is coming soon![/yellow]")


@profile.command("memory")
@click.option("--duration", default=60, help="Profile duration in seconds")
@click.option("--interval", default=5.0, help="Snapshot interval in seconds")
@click.option("--output", default="memory_profile.html", help="Output HTML file")
@click.option("--plot-dir", default=None, help="Directory for plot files")
@click.option("--tracemalloc/--no-tracemalloc", default=True, help="Enable tracemalloc")
@click.option("--min-samples", default=3, help="Minimum samples for leak detection")
@click.option("--growth-threshold", default=10.0, help="Growth rate threshold (obj/s)")
def profile_memory(
    duration: int,
    interval: float,
    output: str,
    plot_dir: str | None,
    tracemalloc: bool,
    min_samples: int,
    growth_threshold: float,
) -> None:
    """Profile memory usage and detect leaks.

    This command runs memory profiling for a specified duration, taking
    periodic snapshots and detecting memory leaks through growth analysis.

    Examples:

        # Profile for 60 seconds with default settings
        qontinui-devtools profile memory

        # Profile for 2 minutes with 10-second intervals
        qontinui-devtools profile memory --duration 120 --interval 10

        # Profile with custom output location
        qontinui-devtools profile memory --output reports/memory.html
    """
    try:
        from .runtime import MemoryProfiler, generate_html_report
        from pathlib import Path
        import time
    except ImportError as e:
        console.print(f"[red]Error importing memory profiler: {e}[/red]")
        sys.exit(1)

    console.print("[bold cyan]Memory Profiling[/bold cyan]")
    console.print(f"Duration: {duration}s, Interval: {interval}s")
    console.print(f"Output: {output}")
    console.print()

    # Create profiler
    profiler = MemoryProfiler(
        enable_tracemalloc=tracemalloc,
        snapshot_interval=interval,
    )

    # Start profiling
    console.print("[green]Starting memory profiler...[/green]")
    profiler.start()

    baseline = profiler.baseline
    console.print(f"Baseline: {baseline.total_mb:.1f} MB, {sum(baseline.objects_by_type.values()):,} objects")
    console.print()

    # Take snapshots
    num_snapshots = int(duration / interval)
    with console.status("[bold green]Profiling memory...") as status:
        for i in range(num_snapshots):
            time.sleep(interval)
            snapshot = profiler.take_snapshot()

            mem_change = snapshot.total_mb - baseline.total_mb
            obj_count = sum(snapshot.objects_by_type.values())

            status.update(
                f"[bold green]Snapshot {i+1}/{num_snapshots}: "
                f"{snapshot.total_mb:.1f} MB ({mem_change:+.1f} MB), "
                f"{obj_count:,} objects"
            )

    profiler.stop()
    console.print()

    # Get final snapshot
    final = profiler.snapshots[-1]
    console.print("[bold]Profiling Summary[/bold]")
    console.print(f"Total snapshots: {len(profiler.snapshots)}")
    console.print(f"Memory change: {final.total_mb - baseline.total_mb:+.1f} MB")
    console.print()

    # Detect leaks
    console.print("[bold]Detecting memory leaks...[/bold]")
    leaks = profiler.detect_leaks(
        min_samples=min_samples,
        growth_threshold=growth_threshold,
    )

    if leaks:
        console.print(f"[red]⚠️  Detected {len(leaks)} potential memory leaks:[/red]")
        console.print()

        # Display top leaks
        for i, leak in enumerate(leaks[:10], 1):
            from .runtime import classify_leak_severity

            severity = classify_leak_severity(
                leak.count_increase, leak.size_increase_mb, leak.growth_rate
            )

            severity_color = {
                "critical": "red",
                "high": "orange1",
                "medium": "yellow",
                "low": "blue",
            }.get(severity, "white")

            console.print(
                f"  [{severity_color}]{i}. {leak.object_type}[/{severity_color}] "
                f"({severity})"
            )
            console.print(f"     Growth: +{leak.count_increase:,} objects")
            console.print(f"     Size: +{leak.size_increase_mb:.2f} MB")
            console.print(f"     Rate: {leak.growth_rate:.1f} obj/s")
            console.print(f"     Confidence: {leak.confidence:.1%}")

            # Suggest fixes
            from .runtime import suggest_fixes

            fixes = suggest_fixes(leak.object_type)
            if fixes:
                console.print(f"     [dim]Suggestions:[/dim]")
                for fix in fixes[:2]:
                    console.print(f"       • {fix}")
            console.print()

    else:
        console.print("[green]✅ No memory leaks detected[/green]")
        console.print()

    # Generate HTML report
    console.print("[bold]Generating report...[/bold]")
    try:
        generate_html_report(
            profiler.snapshots,
            leaks,
            output,
            plot_dir=plot_dir,
        )
        console.print(f"[green]✓ Report saved to:[/green] {output}")

        # Show plot directory if created
        if plot_dir:
            console.print(f"[green]✓ Plots saved to:[/green] {plot_dir}")
    except Exception as e:
        console.print(f"[yellow]Warning: Could not generate full report: {e}[/yellow]")
        # Fall back to text report
        text_report = profiler.generate_report()
        output_txt = str(Path(output).with_suffix(".txt"))
        Path(output_txt).write_text(text_report)
        console.print(f"[green]✓ Text report saved to:[/green] {output_txt}")

    console.print()
    console.print("[bold green]Memory profiling complete![/bold green]")


@profile.command("action")
@click.argument("script_file", type=click.Path(exists=True))
@click.option("--output", default="profile.json", help="Output JSON file")
@click.option("--flame-graph", type=click.Path(), help="Generate flame graph (SVG or JSON)")
@click.option("--format", type=click.Choice(["svg", "json"]), default="svg", help="Flame graph format")
@click.option("--sample-interval", default=0.001, help="Stack sampling interval in seconds")
@click.option("--enable-stack-sampling", is_flag=True, help="Enable stack sampling for flame graphs")
def profile_actions(
    script_file: str,
    output: str,
    flame_graph: str | None,
    format: str,
    sample_interval: float,
    enable_stack_sampling: bool,
) -> None:
    """Profile action execution performance.

    Measures timing, CPU usage, memory consumption, and optionally generates
    flame graphs for visualizing performance bottlenecks.

    Examples:

        # Basic profiling
        qontinui-devtools profile action test_workflow.py

        # With flame graph
        qontinui-devtools profile action test_workflow.py --flame-graph profile.svg

        # Interactive flame graph (speedscope format)
        qontinui-devtools profile action test_workflow.py --flame-graph profile.json --format json

        # Enable stack sampling
        qontinui-devtools profile action test_workflow.py --enable-stack-sampling --flame-graph profile.svg
    """
    try:
        from .runtime import (
            ActionProfiler,
            calculate_action_type_metrics,
            calculate_metrics,
            calculate_phase_metrics,
            format_duration,
            format_memory,
        )
    except ImportError:
        console.print("[red]Error: Runtime profiling module not available[/red]")
        sys.exit(1)

    console.print(Panel(
        f"[bold cyan]Profiling Actions[/bold cyan]\n\n"
        f"Script: {script_file}\n"
        f"Output: {output}\n"
        f"Stack Sampling: {'Enabled' if enable_stack_sampling else 'Disabled'}",
        title="Action Profiler",
        border_style="cyan"
    ))
    console.print()

    # Create profiler
    profiler = ActionProfiler(
        sample_interval=sample_interval,
        enable_memory=True,
        enable_cpu=True,
        enable_stack_sampling=enable_stack_sampling,
    )

    # Start session
    session_id = profiler.start_session()
    console.print(f"[green]Session started:[/green] {session_id}\n")

    # Note: In a real implementation, you would integrate with the actual
    # workflow/action execution. For now, we'll provide a framework.
    console.print("[yellow]Note: Integrate this with your action execution framework[/yellow]")
    console.print("[yellow]Example integration:[/yellow]")
    console.print()

    syntax = Syntax(
        '''# In your action execution code:
with profiler.profile_action("click", "submit_button") as profile:
    # Execute action
    element.click()

    # Track phases
    profile.phases["find"] = 0.01
    profile.phases["move"] = 0.02
    profile.phases["click"] = 0.01
''',
        "python",
        theme="monokai",
        line_numbers=True,
    )
    console.print(syntax)
    console.print()

    # For demonstration, create a simple example profile
    import time

    with console.status("[bold green]Profiling actions..."):
        # Simulate some actions
        for i in range(10):
            with profiler.profile_action("click", f"button_{i}") as profile:
                time.sleep(0.01)  # Simulate action
                profile.phases["find"] = 0.003
                profile.phases["move"] = 0.004
                profile.phases["click"] = 0.003

    # End session
    session = profiler.end_session()
    console.print(f"[green]Session ended:[/green] {len(session.profiles)} actions profiled\n")

    # Calculate metrics
    metrics = calculate_metrics(session.profiles)

    # Display summary table
    table = Table(title="Performance Summary", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan", width=30)
    table.add_column("Value", justify="right", style="green")

    table.add_row("Total Actions", str(metrics.total_actions))
    table.add_row("Total Duration", format_duration(metrics.total_duration))
    table.add_row("Avg Duration", format_duration(metrics.avg_duration))
    table.add_row("Min Duration", format_duration(metrics.min_duration))
    table.add_row("Max Duration", format_duration(metrics.max_duration))
    table.add_row("P50 (Median)", format_duration(metrics.p50_duration))
    table.add_row("P95", format_duration(metrics.p95_duration))
    table.add_row("P99", format_duration(metrics.p99_duration))
    table.add_row("Total CPU Time", format_duration(metrics.total_cpu_time))
    table.add_row("CPU Utilization", f"{metrics.cpu_utilization * 100:.1f}%")
    table.add_row("Total Memory Delta", format_memory(metrics.total_memory_delta))
    table.add_row("Peak Memory", format_memory(metrics.peak_memory))
    table.add_row("Actions/sec", f"{metrics.actions_per_second:.2f}")
    table.add_row("Success Rate", f"{metrics.success_rate * 100:.1f}%")

    console.print(table)
    console.print()

    # Show slowest actions
    if metrics.slowest_actions:
        console.print("[bold]Slowest Actions:[/bold]")
        for action_id, duration in metrics.slowest_actions[:5]:
            console.print(f"  • {action_id}: {format_duration(duration)}")
        console.print()

    # Show phase metrics if available
    phase_metrics = calculate_phase_metrics(session.profiles)
    if phase_metrics:
        phase_table = Table(title="Phase Breakdown", show_header=True)
        phase_table.add_column("Phase", style="cyan")
        phase_table.add_column("Count", justify="right")
        phase_table.add_column("Avg", justify="right")
        phase_table.add_column("Min", justify="right")
        phase_table.add_column("Max", justify="right")
        phase_table.add_column("P95", justify="right")

        for phase_name, phase_data in phase_metrics.items():
            phase_table.add_row(
                phase_name,
                str(int(phase_data["count"])),
                format_duration(phase_data["avg"]),
                format_duration(phase_data["min"]),
                format_duration(phase_data["max"]),
                format_duration(phase_data["p95"]),
            )

        console.print(phase_table)
        console.print()

    # Show action type breakdown
    type_metrics = calculate_action_type_metrics(session.profiles)
    if len(type_metrics) > 1:
        type_table = Table(title="Action Type Breakdown", show_header=True)
        type_table.add_column("Type", style="cyan")
        type_table.add_column("Count", justify="right")
        type_table.add_column("Avg Duration", justify="right")
        type_table.add_column("Total Duration", justify="right")

        for action_type, type_metric in type_metrics.items():
            type_table.add_row(
                action_type,
                str(type_metric.total_actions),
                format_duration(type_metric.avg_duration),
                format_duration(type_metric.total_duration),
            )

        console.print(type_table)
        console.print()

    # Export to JSON
    profiler.export_to_json(output)
    console.print(f"[green]✅ Profile exported to:[/green] {output}")

    # Generate flame graph if requested
    if flame_graph and enable_stack_sampling:
        try:
            profiler.generate_flame_graph(flame_graph, format=format)
            console.print(f"[green]✅ Flame graph generated:[/green] {flame_graph}")
            if format == "json":
                console.print("[blue]💡 Upload to https://www.speedscope.app/ for interactive viewing[/blue]")
        except ValueError as e:
            console.print(f"[yellow]Warning: Could not generate flame graph: {e}[/yellow]")
    elif flame_graph and not enable_stack_sampling:
        console.print("[yellow]Warning: --enable-stack-sampling required for flame graphs[/yellow]")

    console.print()
    console.print("[bold green]Profiling complete![/bold green]")


@main.group()
def architecture() -> None:
    """Architecture analysis commands.

    Tools for detecting architectural anti-patterns and design issues
    like god classes, violations of SOLID principles, and poor cohesion.
    """
    pass


@architecture.command("god-classes")
@click.argument("path", type=click.Path(exists=True))
@click.option("--min-lines", default=500, help="Minimum lines to flag")
@click.option("--min-methods", default=20, help="Minimum methods to flag")
@click.option("--detail", type=click.Choice(["low", "medium", "high"]), default="medium", help="Detail level")
@click.option("--output", type=click.Path(), help="Save report to file")
def detect_god_classes(
    path: str,
    min_lines: int,
    min_methods: int,
    detail: str,
    output: str | None
) -> None:
    """Detect god classes violating Single Responsibility Principle.

    Analyzes classes to find those that are too large, have too many methods,
    or exhibit poor cohesion (high LCOM score). These "god classes" typically
    handle multiple responsibilities and should be refactored.

    Examples:

        # Basic check
        qontinui-devtools architecture god-classes ./src

        # Strict thresholds
        qontinui-devtools architecture god-classes ./src --min-lines 300 --min-methods 15

        # High detail with extraction suggestions
        qontinui-devtools architecture god-classes ./src --detail high

        # Save report to file
        qontinui-devtools architecture god-classes ./src --output report.md
    """
    try:
        from .architecture import GodClassDetector
    except ImportError:
        console.print("[red]Error: Architecture analysis module not available[/red]")
        sys.exit(1)

    detector = GodClassDetector(min_lines=min_lines, min_methods=min_methods, verbose=True)

    with console.status("[bold green]Analyzing classes..."):
        god_classes = detector.analyze_directory(path)

    if not god_classes:
        console.print("[green]✅ No god classes detected![/green]")
        return

    console.print(f"\n[red]❌ Found {len(god_classes)} god classes:[/red]\n")

    for i, cls in enumerate(god_classes, 1):
        color = {"critical": "red", "high": "yellow", "medium": "blue"}[cls.severity]

        console.print(f"[{color}]{i}. {cls.name}[/{color}] ({cls.line_count} lines, {cls.method_count} methods)")
        console.print(f"   File: {cls.file_path}:{cls.line_start}")
        console.print(f"   Cohesion (LCOM): {cls.lcom:.2f} (higher is worse)")

        if detail in ["medium", "high"]:
            if cls.responsibilities:
                console.print(f"   Responsibilities:")
                for resp in cls.responsibilities:
                    console.print(f"     - {resp}")

        if detail == "high":
            suggestions = detector.suggest_extractions(cls)
            if suggestions:
                console.print(f"   Extraction suggestions:")
                for sug in suggestions[:3]:  # Show top 3
                    console.print(
                        f"     → {sug.new_class_name}: {len(sug.methods_to_extract)} methods "
                        f"({sug.estimated_lines} lines)"
                    )

        console.print()

    if output:
        report = detector.generate_report(god_classes)
        Path(output).write_text(report)
        console.print(f"[blue]Report saved to: {output}[/blue]")


@architecture.command("srp")
@click.argument("path", type=click.Path(exists=True))
@click.option("--detail", type=click.Choice(["low", "high"]), default="low", help="Detail level")
@click.option("--min-methods", default=5, help="Minimum methods to analyze")
@click.option("--output", type=click.Path(), help="Save report to file")
def analyze_srp(path: str, detail: str, min_methods: int, output: str | None) -> None:
    """Analyze Single Responsibility Principle violations using semantic analysis.

    Examines classes to detect when they have multiple distinct responsibilities
    by analyzing method names semantically and clustering them into responsibility
    groups. This is more sophisticated than simple size metrics.

    Examples:

        # Basic check
        qontinui-devtools architecture srp ./src

        # Detailed output showing all methods in clusters
        qontinui-devtools architecture srp ./src --detail high

        # Analyze classes with fewer methods
        qontinui-devtools architecture srp ./src --min-methods 3

        # Save report to file
        qontinui-devtools architecture srp ./src --output srp_report.txt
    """
    try:
        from .architecture import SRPAnalyzer
    except ImportError:
        console.print("[red]Error: Architecture analysis module not available[/red]")
        sys.exit(1)

    analyzer = SRPAnalyzer(verbose=True)

    with console.status("[bold green]Analyzing SRP violations..."):
        violations = analyzer.analyze_directory(path, min_methods=min_methods)

    if not violations:
        console.print("[green]✅ No SRP violations detected![/green]")
        return

    console.print(f"\n[red]❌ Found {len(violations)} SRP violations:[/red]\n")

    # Group by severity
    by_severity = {"critical": [], "high": [], "medium": []}
    for v in violations:
        by_severity[v.severity].append(v)

    # Display violations by severity
    for severity in ["critical", "high", "medium"]:
        if not by_severity[severity]:
            continue

        severity_color = {"critical": "red", "high": "yellow", "medium": "blue"}[severity]
        console.print(f"[{severity_color}]## {severity.upper()} SEVERITY ({len(by_severity[severity])})[/{severity_color}]")
        console.print()

        for violation in by_severity[severity]:
            console.print(f"[{severity_color}]{violation.class_name}[/{severity_color}] has {len(violation.clusters)} distinct responsibilities:")
            console.print(f"  File: {violation.file_path}:{violation.line_number}")
            console.print()

            for i, cluster in enumerate(violation.clusters, 1):
                console.print(
                    f"  {i}. [{severity_color}]{cluster.name}[/{severity_color}] "
                    f"({len(cluster.methods)} methods, confidence: {cluster.confidence:.2f})"
                )

                if detail == "high":
                    for method in cluster.methods:
                        console.print(f"      • {method}")
                else:
                    # Show first 3 methods
                    for method in cluster.methods[:3]:
                        console.print(f"      • {method}")
                    if len(cluster.methods) > 3:
                        console.print(f"      ... and {len(cluster.methods) - 3} more")

            console.print()
            console.print(f"  [cyan]Recommendation:[/cyan] {violation.recommendation}")
            console.print()
            console.print(f"  [cyan]Suggested Refactorings:[/cyan]")
            for suggestion in violation.suggested_refactorings:
                console.print(f"    → {suggestion}")
            console.print()
            console.print("-" * 80)
            console.print()

    # Display statistics
    console.print(f"\n[bold]Analysis Statistics:[/bold]")
    console.print(f"  Files analyzed:   {analyzer.stats['files_analyzed']}")
    console.print(f"  Classes analyzed: {analyzer.stats['classes_analyzed']}")
    console.print(f"  Violations found: {analyzer.stats['violations_found']}")

    # Save report if requested
    if output:
        report = analyzer.generate_report(violations)
        Path(output).write_text(report)
        console.print(f"\n[blue]Report saved to: {output}[/blue]")


@architecture.command("graph")
@click.argument("path", type=click.Path(exists=True))
@click.option("--output", default="dependency_graph.html", help="Output file")
@click.option(
    "--format",
    type=click.Choice(["png", "svg", "pdf", "html"]),
    default="html",
    help="Output format",
)
@click.option(
    "--layout",
    type=click.Choice(["dot", "neato", "fdp", "circo"]),
    default="dot",
    help="Graph layout algorithm",
)
@click.option(
    "--level",
    type=click.Choice(["module", "class", "function"]),
    default="module",
    help="Dependency level to analyze",
)
@click.option("--highlight-cycles/--no-highlight-cycles", default=True, help="Highlight circular dependencies")
def visualize_graph(
    path: str,
    output: str,
    format: str,
    layout: str,
    level: str,
    highlight_cycles: bool,
) -> None:
    """Generate interactive dependency graph visualization.

    Creates visual representations of code dependencies to help understand
    architecture at a glance. Supports multiple formats and layouts.

    Examples:

        # Generate interactive HTML graph
        qontinui-devtools architecture graph ./src

        # Module-level dependencies as PNG
        qontinui-devtools architecture graph ./src --format png --output deps.png

        # Class-level graph with circular layout
        qontinui-devtools architecture graph ./src --level class --layout circo

        # Function-level call graph
        qontinui-devtools architecture graph ./src --level function
    """
    try:
        from .architecture import DependencyGraphVisualizer
    except ImportError:
        console.print("[red]Error: Graph visualizer module not available[/red]")
        sys.exit(1)

    visualizer = DependencyGraphVisualizer(verbose=True)

    with console.status(f"[bold green]Building {level}-level dependency graph..."):
        try:
            nodes, edges = visualizer.build_graph(path, level=level)
        except Exception as e:
            console.print(f"[red]Error building graph: {e}[/red]")
            sys.exit(1)

    console.print(f"[green]✅ Graph built:[/green] {len(nodes)} nodes, {len(edges)} edges")

    # Detect cycles if requested
    if highlight_cycles:
        with console.status("[bold green]Detecting circular dependencies..."):
            cycles = visualizer.detect_cycles(nodes, edges)
        if cycles:
            console.print(f"[yellow]⚠️  Found {len(cycles)} circular dependencies[/yellow]")

    # Generate visualization
    with console.status(f"[bold green]Generating {format} visualization..."):
        try:
            visualizer.visualize(
                nodes,
                edges,
                output,
                format=format,
                layout=layout,
                highlight_cycles=highlight_cycles,
            )
        except ImportError as e:
            if format in ["png", "svg", "pdf"]:
                console.print(
                    f"[red]Error: {format.upper()} format requires graphviz to be installed.[/red]"
                )
                console.print("[yellow]Install with: pip install graphviz[/yellow]")
                console.print("[yellow]Or use --format html for a standalone HTML visualization[/yellow]")
            else:
                console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
        except Exception as e:
            console.print(f"[red]Error generating visualization: {e}[/red]")
            sys.exit(1)

    console.print(f"[green]✅ Graph saved to:[/green] {output}")

    if format == "html":
        console.print("[blue]💡 Open in browser to interact with the graph[/blue]")
        console.print("[blue]   - Zoom and pan[/blue]")
        console.print("[blue]   - Click nodes for details[/blue]")
        console.print("[blue]   - Search and filter[/blue]")


@architecture.command("coupling")
@click.argument("path", type=click.Path(exists=True))
@click.option("--threshold", default=10, help="Max efferent coupling threshold")
@click.option("--show-all", is_flag=True, help="Show all modules, not just problematic ones")
@click.option("--output", type=click.Path(), help="Save report to file")
def analyze_coupling(path: str, threshold: int, show_all: bool, output: str | None) -> None:
    """Analyze coupling and cohesion metrics.

    Measures how tightly modules are coupled (dependencies) and how cohesive
    they are internally. Helps identify modules that should be split or
    dependencies that should be reduced.

    Metrics explained:
    - Ca (Afferent Coupling): Number of modules that depend on this module
    - Ce (Efferent Coupling): Number of modules this module depends on
    - Instability (I): Ce / (Ca + Ce), range 0 (stable) to 1 (unstable)
    - Distance from Main: How far from ideal balance (lower is better)
    - LCOM: Lack of Cohesion of Methods (lower is better)
    - TCC: Tight Class Cohesion (higher is better)

    Examples:

        # Analyze coupling
        qontinui-devtools architecture coupling ./src

        # Custom threshold
        qontinui-devtools architecture coupling ./src --threshold 15

        # Show all modules
        qontinui-devtools architecture coupling ./src --show-all

        # Save report
        qontinui-devtools architecture coupling ./src --output coupling_report.txt
    """
    try:
        from .architecture import CouplingCohesionAnalyzer
    except ImportError:
        console.print("[red]Error: Coupling analyzer module not available[/red]")
        sys.exit(1)

    console.print(f"[bold cyan]Analyzing coupling and cohesion in:[/bold cyan] {path}\n")

    analyzer = CouplingCohesionAnalyzer(verbose=True)

    with console.status("[bold green]Analyzing modules and classes..."):
        coupling, cohesion = analyzer.analyze_directory(path)

    # Coupling Analysis
    console.print("\n[bold]Coupling Analysis:[/bold]\n")

    if coupling:
        # Filter by threshold if not showing all
        if not show_all:
            high_coupling = [c for c in coupling if c.efferent_coupling > threshold]
            if high_coupling:
                coupling_to_show = high_coupling
                console.print(f"[yellow]Modules with Ce > {threshold}:[/yellow]\n")
            else:
                coupling_to_show = sorted(coupling, key=lambda x: x.efferent_coupling, reverse=True)[:10]
                console.print(f"[green]No modules exceed threshold of {threshold}. Showing top 10:[/green]\n")
        else:
            coupling_to_show = sorted(coupling, key=lambda x: x.efferent_coupling, reverse=True)

        table = Table(title="Module Coupling Metrics")
        table.add_column("Module", style="cyan")
        table.add_column("Ca", justify="right")
        table.add_column("Ce", justify="right")
        table.add_column("Instability", justify="right")
        table.add_column("Distance", justify="right")
        table.add_column("Score", justify="center")

        for c in coupling_to_show[:20]:  # Top 20
            color = {
                "excellent": "green",
                "good": "blue",
                "fair": "yellow",
                "poor": "red"
            }[c.coupling_score]

            table.add_row(
                c.name,
                str(c.afferent_coupling),
                str(c.efferent_coupling),
                f"{c.instability:.2f}",
                f"{c.distance_from_main:.2f}",
                f"[{color}]{c.coupling_score}[/{color}]"
            )

        console.print(table)
    else:
        console.print("[yellow]No modules found.[/yellow]")

    # Cohesion Analysis
    console.print("\n[bold]Cohesion Analysis:[/bold]\n")

    if cohesion:
        # Find classes with poor cohesion
        poor_cohesion = [c for c in cohesion if c.lcom > 0.7 or c.lcom4 > 2.0]

        if poor_cohesion:
            console.print(f"[yellow]Found {len(poor_cohesion)} classes with poor cohesion:[/yellow]\n")

            for c in sorted(poor_cohesion, key=lambda x: x.lcom, reverse=True)[:10]:
                color = {
                    "excellent": "green",
                    "good": "blue",
                    "fair": "yellow",
                    "poor": "red"
                }[c.cohesion_score]

                console.print(f"[{color}]{c.name}[/{color}]:")
                console.print(f"  File: {c.file_path}")
                console.print(f"  LCOM: {c.lcom:.2f} (lower is better)")
                console.print(f"  LCOM4: {c.lcom4:.1f} (1 is ideal)")
                console.print(f"  TCC: {c.tcc:.2f} (higher is better)")
                console.print(f"  LCC: {c.lcc:.2f} (higher is better)")
                console.print(f"  Score: {c.cohesion_score.upper()}\n")
        else:
            console.print("[green]✅ All classes have good cohesion![/green]")
    else:
        console.print("[yellow]No classes found.[/yellow]")

    # Summary Statistics
    console.print("\n[bold]Summary Statistics:[/bold]\n")

    if coupling:
        avg_ce = sum(c.efferent_coupling for c in coupling) / len(coupling)
        avg_ca = sum(c.afferent_coupling for c in coupling) / len(coupling)
        avg_instability = sum(c.instability for c in coupling) / len(coupling)

        console.print(f"Modules analyzed: {len(coupling)}")
        console.print(f"Average Ce: {avg_ce:.2f}")
        console.print(f"Average Ca: {avg_ca:.2f}")
        console.print(f"Average Instability: {avg_instability:.2f}")

        poor_count = len([c for c in coupling if c.coupling_score == "poor"])
        if poor_count > 0:
            console.print(f"[red]⚠️  {poor_count} modules with poor coupling[/red]")

    if cohesion:
        avg_lcom = sum(c.lcom for c in cohesion) / len(cohesion)
        avg_tcc = sum(c.tcc for c in cohesion) / len(cohesion)

        console.print(f"\nClasses analyzed: {len(cohesion)}")
        console.print(f"Average LCOM: {avg_lcom:.2f}")
        console.print(f"Average TCC: {avg_tcc:.2f}")

        poor_count = len([c for c in cohesion if c.cohesion_score == "poor"])
        if poor_count > 0:
            console.print(f"[red]⚠️  {poor_count} classes with poor cohesion[/red]")

    # Save report if requested
    if output:
        report = analyzer.generate_report(coupling, cohesion)
        Path(output).write_text(report)
        console.print(f"\n[green]✅ Report saved to:[/green] {output}")


@main.group()
def quality() -> None:
    """Code quality analysis commands.

    Tools for detecting code quality issues like dead code, unused imports,
    and other maintainability problems.
    """
    pass


@quality.command("dead-code")
@click.argument("path", type=click.Path(exists=True))
@click.option("--type", "code_type",
              type=click.Choice(["all", "functions", "classes", "imports", "variables"]),
              default="all",
              help="Type of dead code to detect")
@click.option("--min-confidence", default=0.5, type=float,
              help="Minimum confidence level (0-1)")
@click.option("--output", type=click.Path(), help="Save report to file")
@click.option("--format",
              type=click.Choice(["text", "json", "csv"], case_sensitive=False),
              default="text",
              help="Output format")
def detect_dead_code(
    path: str,
    code_type: str,
    min_confidence: float,
    output: str | None,
    format: str
) -> None:
    """Detect unused code in Python projects.

    Analyzes Python files to find unused functions, classes, imports, and
    variables that can be safely removed. This helps reduce code clutter
    and improve maintainability.

    Examples:

        # Find all types of dead code
        qontinui-devtools quality dead-code ./src

        # Find only unused functions
        qontinui-devtools quality dead-code ./src --type functions

        # High confidence items only
        qontinui-devtools quality dead-code ./src --min-confidence 0.8

        # Save report to file
        qontinui-devtools quality dead-code ./src --output dead_code.txt

        # Generate JSON report
        qontinui-devtools quality dead-code ./src --output report.json --format json
    """
    try:
        from .code_quality import DeadCodeDetector
    except ImportError:
        console.print("[red]Error: Code quality module not available[/red]")
        sys.exit(1)

    with console.status("[bold green]Analyzing code for dead code..."):
        detector = DeadCodeDetector(path)

        # Get dead code based on type
        if code_type == "all":
            dead_code = detector.analyze()
        elif code_type == "functions":
            dead_code = detector.find_unused_functions()
        elif code_type == "classes":
            dead_code = detector.find_unused_classes()
        elif code_type == "imports":
            dead_code = detector.find_unused_imports()
        elif code_type == "variables":
            dead_code = detector.find_unused_variables()
        else:
            dead_code = detector.analyze()

        # Filter by confidence
        dead_code = [dc for dc in dead_code if dc.confidence >= min_confidence]

    if not dead_code:
        console.print("[green]✅ No dead code detected![/green]")
        console.print(f"[dim](Minimum confidence: {min_confidence})[/dim]")
        return

    # Group by type
    by_type = {}
    for dc in dead_code:
        by_type.setdefault(dc.type, []).append(dc)

    # Display summary
    console.print(f"\n[red]Found {len(dead_code)} pieces of dead code:[/red]\n")

    # Create summary table
    summary_table = Table(title="Dead Code Summary", show_header=True, header_style="bold magenta")
    summary_table.add_column("Type", style="cyan")
    summary_table.add_column("Count", justify="right", style="bold")
    summary_table.add_column("Avg Confidence", justify="right")

    type_order = ["import", "variable", "function", "class"]
    for dtype in type_order:
        if dtype in by_type:
            items = by_type[dtype]
            avg_conf = sum(dc.confidence for dc in items) / len(items)
            summary_table.add_row(
                dtype.capitalize() + "s",
                str(len(items)),
                f"{avg_conf:.2f}"
            )

    console.print(summary_table)
    console.print()

    # Display detailed results
    for dtype in type_order:
        if dtype not in by_type:
            continue

        items = by_type[dtype]
        console.print(f"[bold cyan]{dtype.capitalize()}s ({len(items)}):[/bold cyan]")

        for dc in sorted(items, key=lambda x: x.confidence, reverse=True)[:10]:
            confidence_color = "red" if dc.confidence > 0.8 else "yellow" if dc.confidence > 0.6 else "blue"
            console.print(f"  [{confidence_color}]• {dc.name}[/{confidence_color}] "
                         f"(confidence: {dc.confidence:.2f})")
            console.print(f"    {dc.file_path}:{dc.line_number}")
            console.print(f"    [dim]{dc.reason}[/dim]")

        if len(items) > 10:
            console.print(f"  [dim]... and {len(items) - 10} more[/dim]")
        console.print()

    # Save report if requested
    if output:
        if format == "json":
            import json
            json_data = [
                {
                    "type": dc.type,
                    "name": dc.name,
                    "file_path": dc.file_path,
                    "line_number": dc.line_number,
                    "reason": dc.reason,
                    "confidence": dc.confidence,
                }
                for dc in dead_code
            ]
            Path(output).write_text(json.dumps(json_data, indent=2))
        elif format == "csv":
            import csv
            with open(output, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Type", "Name", "File", "Line", "Confidence", "Reason"])
                for dc in dead_code:
                    writer.writerow([dc.type, dc.name, dc.file_path, dc.line_number, dc.confidence, dc.reason])
        else:  # text
            lines = ["Dead Code Report", "=" * 80, ""]
            lines.append(f"Total items: {len(dead_code)}")
            lines.append(f"Minimum confidence: {min_confidence}")
            lines.append("")

            for dtype in type_order:
                if dtype not in by_type:
                    continue
                items = by_type[dtype]
                lines.append(f"\n{dtype.capitalize()}s ({len(items)}):")
                lines.append("-" * 40)
                for dc in items:
                    lines.append(f"\n  {dc.name} (confidence: {dc.confidence:.2f})")
                    lines.append(f"  File: {dc.file_path}:{dc.line_number}")
                    lines.append(f"  Reason: {dc.reason}")

            Path(output).write_text("\n".join(lines))

        console.print(f"[green]✅ Report saved to:[/green] {output}")

    # Statistics
    stats = detector.get_stats()
    console.print("[bold]Statistics:[/bold]")
    console.print(f"  Total dead code items: {stats['total']}")
    console.print(f"  Functions: {stats['functions']}")
    console.print(f"  Classes: {stats['classes']}")
    console.print(f"  Imports: {stats['imports']}")
    console.print(f"  Variables: {stats['variables']}")


@main.group()
def security() -> None:
    """Security analysis commands.

    Tools for detecting security vulnerabilities, analyzing code for
    common security issues, and generating security reports.
    """
    pass


@security.command("scan")
@click.argument("path", type=click.Path(exists=True))
@click.option("--output", type=click.Path(), help="Output file path")
@click.option("--format", type=click.Choice(["text", "json", "html"]), default="text", help="Output format")
@click.option("--severity", type=click.Choice(["critical", "high", "medium", "low"]), default="medium", help="Minimum severity to report")
def scan_security(path: str, output: str | None, format: str, severity: str) -> None:
    """Scan for security vulnerabilities.

    Analyzes Python code for common security issues including:
    - Hardcoded credentials
    - SQL injection vulnerabilities
    - Command injection risks
    - Path traversal issues
    - Insecure deserialization
    - Weak cryptography usage

    Examples:

        # Basic scan
        qontinui-devtools security scan ./src

        # Only critical issues
        qontinui-devtools security scan ./src --severity critical

        # Generate HTML report
        qontinui-devtools security scan ./src --output security.html --format html
    """
    try:
        from .security import SecurityAnalyzer
    except ImportError:
        console.print("[red]Error: Security analysis module not available[/red]")
        sys.exit(1)

    console.print(f"[bold cyan]Scanning for security vulnerabilities:[/bold cyan] {path}\n")

    analyzer = SecurityAnalyzer()
    with console.status("[bold green]Analyzing security..."):
        report = analyzer.analyze_directory(path)

    # Filter by severity
    from .security.models import Severity as SevEnum
    severity_map = {
        "low": SevEnum.LOW,
        "medium": SevEnum.MEDIUM,
        "high": SevEnum.HIGH,
        "critical": SevEnum.CRITICAL
    }
    min_severity = severity_map.get(severity.lower(), SevEnum.MEDIUM)

    # Filter vulnerabilities based on severity
    filtered_vulns = [v for v in report.vulnerabilities if v.severity <= min_severity]

    if filtered_vulns:
        console.print(f"[red]Found {len(filtered_vulns)} security issues:[/red]\n")
        for vuln in filtered_vulns:
            color = {"critical": "red", "high": "yellow", "medium": "blue", "low": "dim"}[vuln.severity.value]
            console.print(f"[{color}]• {vuln.type.value.replace('_', ' ').title()}[/{color}]")
            console.print(f"  {vuln.file_path}:{vuln.line_number}")
            console.print(f"  {vuln.description}\n")
    else:
        console.print("[green]No security issues detected![/green]")

    if output:
        _generate_security_report(report, filtered_vulns, output, format)
        console.print(f"[green]Report saved to: {output}[/green]")


def _generate_security_report(report, vulnerabilities, output_path: str, format: str) -> None:
    """Generate security report in specified format."""
    import json
    from pathlib import Path

    if format == 'json':
        # Generate JSON report
        report_data = {
            'summary': {
                'total_files_scanned': report.total_files_scanned,
                'total_vulnerabilities': len(vulnerabilities),
                'critical_count': sum(1 for v in vulnerabilities if v.severity.value == 'critical'),
                'high_count': sum(1 for v in vulnerabilities if v.severity.value == 'high'),
                'medium_count': sum(1 for v in vulnerabilities if v.severity.value == 'medium'),
                'low_count': sum(1 for v in vulnerabilities if v.severity.value == 'low'),
                'scan_duration': report.scan_duration
            },
            'vulnerabilities': [v.to_dict() for v in vulnerabilities]
        }

        with open(output_path, 'w') as f:
            json.dump(report_data, f, indent=2)

    elif format == 'html':
        # Generate HTML report
        html = _generate_html_report(report, vulnerabilities)
        with open(output_path, 'w') as f:
            f.write(html)

    else:
        # Generate text report
        with open(output_path, 'w') as f:
            f.write(str(report))
            f.write("\n\n")
            for vuln in vulnerabilities:
                f.write(str(vuln))
                f.write("\n\n")


def _generate_html_report(report, vulnerabilities) -> str:
    """Generate HTML security report."""
    from datetime import datetime

    severity_colors = {
        'critical': '#dc2626',
        'high': '#f59e0b',
        'medium': '#3b82f6',
        'low': '#6b7280'
    }

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Security Analysis Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            h1 {{ color: #333; border-bottom: 3px solid #3b82f6; padding-bottom: 10px; }}
            h2 {{ color: #555; margin-top: 30px; }}
            .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
            .stat {{ padding: 20px; background: #f8f9fa; border-left: 4px solid #3b82f6; }}
            .stat-label {{ font-size: 14px; color: #666; }}
            .stat-value {{ font-size: 28px; font-weight: bold; color: #333; }}
            .vulnerability {{ margin: 20px 0; padding: 20px; border-left: 4px solid #ccc; background: #f8f9fa; }}
            .severity-critical {{ border-left-color: {severity_colors['critical']}; }}
            .severity-high {{ border-left-color: {severity_colors['high']}; }}
            .severity-medium {{ border-left-color: {severity_colors['medium']}; }}
            .severity-low {{ border-left-color: {severity_colors['low']}; }}
            .vuln-header {{ display: flex; justify-content: space-between; align-items: start; }}
            .vuln-title {{ font-size: 18px; font-weight: bold; color: #333; }}
            .severity-badge {{ padding: 4px 12px; border-radius: 4px; color: white; font-size: 12px; font-weight: bold; }}
            .code {{ background: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 4px; overflow-x: auto; margin: 10px 0; }}
            .meta {{ color: #666; font-size: 14px; margin: 10px 0; }}
            .remediation {{ background: #e7f5ff; padding: 15px; border-radius: 4px; margin: 10px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Security Analysis Report</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

            <div class="summary">
                <div class="stat">
                    <div class="stat-label">Files Scanned</div>
                    <div class="stat-value">{report.total_files_scanned}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Total Issues</div>
                    <div class="stat-value">{len(vulnerabilities)}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Critical</div>
                    <div class="stat-value" style="color: {severity_colors['critical']}">{sum(1 for v in vulnerabilities if v.severity.value == 'critical')}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">High</div>
                    <div class="stat-value" style="color: {severity_colors['high']}">{sum(1 for v in vulnerabilities if v.severity.value == 'high')}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Medium</div>
                    <div class="stat-value" style="color: {severity_colors['medium']}">{sum(1 for v in vulnerabilities if v.severity.value == 'medium')}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Low</div>
                    <div class="stat-value" style="color: {severity_colors['low']}">{sum(1 for v in vulnerabilities if v.severity.value == 'low')}</div>
                </div>
            </div>

            <h2>Detected Vulnerabilities</h2>
    """

    for vuln in sorted(vulnerabilities, key=lambda v: (v.severity.value, v.file_path)):
        severity = vuln.severity.value
        html += f"""
            <div class="vulnerability severity-{severity}">
                <div class="vuln-header">
                    <div class="vuln-title">{vuln.type.value.replace('_', ' ').title()}</div>
                    <span class="severity-badge" style="background: {severity_colors[severity]}">{severity.upper()}</span>
                </div>
                <div class="meta">
                    <strong>File:</strong> {vuln.file_path}:{vuln.line_number}<br>
                    <strong>CWE:</strong> {vuln.cwe_id} | <strong>OWASP:</strong> {vuln.owasp_category}
                </div>
                <p><strong>Description:</strong> {vuln.description}</p>
                <pre class="code">{vuln.code_snippet}</pre>
                <div class="remediation">
                    <strong>Remediation:</strong> {vuln.remediation}
                </div>
            </div>
        """

    html += """
        </div>
    </body>
    </html>
    """

    return html


@main.group()
def docs() -> None:
    """Documentation generation commands.

    Tools for automatically generating API documentation, module
    documentation, and comprehensive project documentation.
    """
    pass


@docs.command("generate")
@click.argument("path", type=click.Path(exists=True))
@click.option("--output", type=click.Path(), help="Output directory")
@click.option("--format", type=click.Choice(["html", "markdown", "json"]), default="html", help="Output format")
def generate_docs(path: str, output: str | None, format: str) -> None:
    """Generate documentation.

    Automatically generates comprehensive documentation from Python
    source code including:
    - API reference
    - Module documentation
    - Class and function documentation
    - Type hints and signatures
    - Examples and usage

    Examples:

        # Generate HTML documentation
        qontinui-devtools docs generate ./src --output docs/

        # Generate markdown
        qontinui-devtools docs generate ./src --output docs/ --format markdown
    """
    try:
        from .documentation import DocumentationGenerator
    except ImportError:
        console.print("[red]Error: Documentation module not available[/red]")
        sys.exit(1)

    output_dir = output or "docs"
    console.print(f"[bold cyan]Generating documentation:[/bold cyan] {path}\n")

    generator = DocumentationGenerator(path)
    with console.status("[bold green]Generating documentation..."):
        generator.generate(output_dir, format)

    console.print(f"[green]Documentation generated in: {output_dir}[/green]")


@main.group()
def regression() -> None:
    """Regression detection commands.

    Tools for detecting performance and behavioral regressions by
    comparing against baseline snapshots.
    """
    pass


@regression.command("check")
@click.argument("path", type=click.Path(exists=True))
@click.option("--baseline", help="Baseline snapshot name")
def check_regression(path: str, baseline: str | None) -> None:
    """Check for regressions.

    Compares current code against a baseline snapshot to detect:
    - Performance regressions
    - API changes
    - Behavioral changes
    - Test coverage changes

    Examples:

        # Check against latest baseline
        qontinui-devtools regression check ./src

        # Check against specific baseline
        qontinui-devtools regression check ./src --baseline v1.0.0
    """
    try:
        from .regression import RegressionDetector
    except ImportError:
        console.print("[red]Error: Regression detection module not available[/red]")
        sys.exit(1)

    console.print(f"[bold cyan]Checking for regressions:[/bold cyan] {path}\n")

    detector = RegressionDetector(path)
    with console.status("[bold green]Analyzing regressions..."):
        regressions = detector.check(baseline)

    if regressions:
        console.print(f"[red]Found {len(regressions)} regressions:[/red]\n")
        for reg in regressions:
            console.print(f"[yellow]• {reg.type}: {reg.description}[/yellow]")
    else:
        console.print("[green]No regressions detected![/green]")


@main.group()
def types() -> None:
    """Type hint analysis commands.

    Tools for analyzing type hint coverage and suggesting
    improvements to type annotations.
    """
    pass


@types.command("coverage")
@click.argument("path", type=click.Path(exists=True))
@click.option("--suggest", is_flag=True, help="Suggest type hints")
def type_coverage(path: str, suggest: bool) -> None:
    """Analyze type hint coverage.

    Analyzes Python code to determine type hint coverage and
    optionally suggests type hints for untyped code.

    Examples:

        # Check type coverage
        qontinui-devtools types coverage ./src

        # Get suggestions
        qontinui-devtools types coverage ./src --suggest
    """
    try:
        from .type_analysis import TypeAnalyzer
    except ImportError:
        console.print("[red]Error: Type analysis module not available[/red]")
        sys.exit(1)

    console.print(f"[bold cyan]Analyzing type coverage:[/bold cyan] {path}\n")

    analyzer = TypeAnalyzer(run_mypy=True)
    with console.status("[bold green]Analyzing types..."):
        report = analyzer.analyze_directory(path)

    # Display coverage metrics
    cov = report.overall_coverage
    console.print(f"\n[bold]Overall Type Coverage:[/bold] {cov.coverage_percentage:.1f}%")
    console.print(f"  Fully typed functions: {cov.fully_typed_functions}/{cov.total_functions} ({cov.fully_typed_functions/cov.total_functions*100 if cov.total_functions > 0 else 0:.1f}%)")
    console.print(f"  Typed parameters: {cov.typed_parameters}/{cov.total_parameters} ({cov.parameter_coverage:.1f}%)")
    console.print(f"  Typed returns: {cov.typed_returns}/{cov.total_returns} ({cov.return_coverage:.1f}%)")
    console.print(f"  Any usage: {cov.any_usage_count} occurrences")
    console.print(f"\nFiles analyzed: {report.files_analyzed}")
    console.print(f"Analysis time: {report.analysis_time:.2f}s")

    if suggest and report.untyped_items:
        console.print(f"\n[yellow]Type Suggestions (showing top 10 of {len(report.untyped_items)}):[/yellow]\n")
        sorted_items = report.get_sorted_untyped_items(limit=10)
        for item in sorted_items:
            console.print(f"  {item.file_path}:{item.line_number}")
            console.print(f"    {item.get_full_name()} - {item.item_type}")
            if item.suggested_type:
                console.print(f"    Suggestion: {item.suggested_type} (confidence: {item.confidence:.2f})")
                if item.reason:
                    console.print(f"    Reason: {item.reason}")
            console.print("")


@main.group()
def deps() -> None:
    """Dependency health commands.

    Tools for analyzing dependency health, checking for outdated
    packages, and identifying security vulnerabilities in dependencies.
    """
    pass


@deps.command("check")
@click.argument("path", type=click.Path(exists=True))
@click.option("--update", is_flag=True, help="Show update commands")
def check_deps(path: str, update: bool) -> None:
    """Check dependency health.

    Analyzes project dependencies to identify:
    - Outdated packages
    - Security vulnerabilities
    - Deprecated packages
    - License issues

    Examples:

        # Check dependencies
        qontinui-devtools deps check ./

        # Show update commands
        qontinui-devtools deps check ./ --update
    """
    try:
        from .dependencies import DependencyHealthChecker
    except ImportError:
        console.print("[red]Error: Dependency checker module not available[/red]")
        sys.exit(1)

    console.print(f"[bold cyan]Checking dependency health:[/bold cyan] {path}\n")

    checker = DependencyHealthChecker(path)
    with console.status("[bold green]Analyzing dependencies..."):
        health = checker.check()

    console.print(f"Total dependencies: {health.total}")
    console.print(f"Outdated: {health.outdated}")
    console.print(f"Vulnerabilities: {health.vulnerabilities}")

    if update and health.outdated > 0:
        console.print(f"\n[yellow]Update commands:[/yellow]\n")
        for cmd in health.update_commands:
            console.print(f"  {cmd}")


@main.group()
def hal() -> None:
    """Mock HAL commands.

    Commands for working with the mock hardware abstraction layer
    for testing without physical hardware.
    """
    pass


@hal.command("init")
@click.option("--config", type=click.Path(), help="Configuration file")
def init_hal(config: str | None) -> None:
    """Initialize mock HAL environment.

    Examples:

        # Initialize with default config
        qontinui-devtools hal init

        # Initialize with custom config
        qontinui-devtools hal init --config hal_config.yaml
    """
    console.print("[bold cyan]Initializing Mock HAL...[/bold cyan]")
    console.print("[yellow]This feature is coming soon![/yellow]")


@hal.command("record")
@click.argument("output")
@click.option("--duration", default=60, help="Recording duration in seconds")
def record_hal(output: str, duration: int) -> None:
    """Record HAL interactions for replay.

    Examples:

        # Record 60 seconds of interactions
        qontinui-devtools hal record session.hal

        # Record for 5 minutes
        qontinui-devtools hal record session.hal --duration 300
    """
    console.print(f"[bold cyan]Recording HAL interactions to:[/bold cyan] {output}")
    console.print("[yellow]This feature is coming soon![/yellow]")


@hal.command("replay")
@click.argument("input", type=click.Path(exists=True))
@click.option("--speed", default=1.0, help="Playback speed multiplier")
def replay_hal(input: str, speed: float) -> None:
    """Replay recorded HAL interactions.

    Examples:

        # Replay at normal speed
        qontinui-devtools hal replay session.hal

        # Replay at 2x speed
        qontinui-devtools hal replay session.hal --speed 2.0
    """
    console.print(f"[bold cyan]Replaying HAL interactions from:[/bold cyan] {input}")
    console.print("[yellow]This feature is coming soon![/yellow]")


@main.group()
def trace() -> None:
    """Event tracing commands.

    Commands for tracing events through the Qontinui system and analyzing
    latencies from frontend through Tauri, Python, ActionExecutor, and HAL.
    """
    pass


@trace.command("events")
@click.option("--duration", default=60, help="Trace duration in seconds")
@click.option("--output", default="events.json", help="Output file")
@click.option("--timeline", type=click.Path(), help="Generate timeline visualization")
@click.option("--html", type=click.Path(), help="Generate HTML timeline")
def trace_events(duration: int, output: str, timeline: str | None, html: str | None) -> None:
    """Trace events for specified duration.

    This command traces events through the Qontinui system and provides
    detailed latency analysis and timeline visualization.

    Examples:

        # Trace events for 60 seconds
        qontinui-devtools trace events

        # Trace and generate Chrome trace
        qontinui-devtools trace events --timeline timeline.json

        # Trace and generate HTML timeline
        qontinui-devtools trace events --html timeline.html

        # Custom duration
        qontinui-devtools trace events --duration 30
    """
    from .runtime import EventTracer, export_chrome_trace, export_timeline_html
    import time

    tracer = EventTracer()

    console.print(f"[bold cyan]Tracing events for {duration} seconds...[/bold cyan]")
    console.print("[yellow]Note: This is a demonstration. Hook into qontinui event system for real tracing.[/yellow]")
    console.print()

    # Simulate some traces for demonstration
    import random
    start_time = time.time()

    with console.status("[bold green]Tracing events...") as status:
        event_count = 0
        while time.time() - start_time < duration:
            # Simulate an event every 100ms
            time.sleep(0.1)

            event_id = f"evt_{event_count}"
            event_type = random.choice(["click", "keypress", "scroll"])

            tracer.start_trace(event_id, event_type)
            tracer.checkpoint(event_id, "frontend_emit")

            time.sleep(random.uniform(0.001, 0.005))
            tracer.checkpoint(event_id, "tauri_receive")

            time.sleep(random.uniform(0.002, 0.010))
            tracer.checkpoint(event_id, "python_receive")

            time.sleep(random.uniform(0.005, 0.020))
            tracer.checkpoint(event_id, "executor_start")

            if random.random() > 0.1:  # 90% complete
                time.sleep(random.uniform(0.010, 0.050))
                tracer.checkpoint(event_id, "executor_complete")
                tracer.complete_trace(event_id)

            event_count += 1
            status.update(f"[bold green]Traced {event_count} events...")

    console.print(f"[green]✓[/green] Traced {event_count} events")
    console.print()

    # Analyze
    flow = tracer.analyze_flow()

    console.print("[bold]Event Flow Analysis:[/bold]")
    console.print(f"  Total events: {flow.total_events}")
    console.print(f"  Completed: {flow.completed_events}")
    console.print(f"  Lost: {flow.lost_events}")
    console.print(f"  Avg latency: {flow.avg_latency * 1000:.2f}ms")
    console.print(f"  P95 latency: {flow.p95_latency * 1000:.2f}ms")
    console.print(f"  P99 latency: {flow.p99_latency * 1000:.2f}ms")
    console.print(f"  Bottleneck: {flow.bottleneck_stage}")
    console.print()

    # Stage latencies
    if flow.stage_latencies:
        console.print("[bold]Stage Latencies:[/bold]")
        sorted_stages = sorted(
            flow.stage_latencies.items(),
            key=lambda x: x[1],
            reverse=True
        )
        for stage, latency in sorted_stages[:5]:  # Top 5
            console.print(f"  {stage}: {latency * 1000:.2f}ms")
        console.print()

    # Export timeline
    if timeline:
        export_chrome_trace(tracer.get_all_traces(), timeline)
        console.print(f"[green]✓[/green] Chrome trace saved to: {timeline}")
        console.print(f"  Open in chrome://tracing or https://ui.perfetto.dev/")

    if html:
        export_timeline_html(tracer.get_all_traces(), html)
        console.print(f"[green]✓[/green] HTML timeline saved to: {html}")
        console.print(f"  Open {html} in your browser")


@trace.command("analyze")
@click.argument("trace_file", type=click.Path(exists=True))
@click.option("--threshold", default=2.0, help="Anomaly detection threshold (multiplier)")
def analyze_trace(trace_file: str, threshold: float) -> None:
    """Analyze saved trace file.

    Examples:

        # Analyze trace
        qontinui-devtools trace analyze events.json

        # With custom anomaly threshold
        qontinui-devtools trace analyze events.json --threshold 3.0
    """
    from .runtime import (
        analyze_latencies,
        detect_anomalies,
        find_bottleneck,
        generate_latency_report
    )
    import json

    console.print(f"[bold cyan]Analyzing trace file:[/bold cyan] {trace_file}")
    console.print("[yellow]Note: This command is a placeholder. Implement trace file loading.[/yellow]")


@trace.command("report")
@click.argument("trace_file", type=click.Path(exists=True))
@click.option("--output", help="Output file (defaults to stdout)")
def trace_report(trace_file: str, output: str | None) -> None:
    """Generate detailed latency report.

    Examples:

        # Print report to stdout
        qontinui-devtools trace report events.json

        # Save to file
        qontinui-devtools trace report events.json --output report.txt
    """
    from .runtime import generate_latency_report

    console.print(f"[bold cyan]Generating latency report:[/bold cyan] {trace_file}")
    console.print("[yellow]Note: This command is a placeholder. Implement trace file loading.[/yellow]")


def save_report(data: Any, output: str, format: str, detector: Any = None) -> None:
    """Save analysis report to file."""
    import json

    if format == "json":
        with open(output, "w") as f:
            json.dump({
                "cycles": [
                    {
                        "cycle": c.cycle,
                        "severity": c.severity,
                        "suggestion": {
                            "type": c.suggestion.fix_type,
                            "description": c.suggestion.description,
                            "code_example": c.suggestion.code_example,
                            "affected_files": c.suggestion.affected_files,
                        },
                        "import_chain": [
                            {
                                "module": imp.module,
                                "file": imp.file_path,
                                "line": imp.line_number,
                                "statement": str(imp),
                            }
                            for imp in c.import_chain
                        ],
                    }
                    for c in data
                ],
                "statistics": detector.get_statistics() if detector else {},
            }, f, indent=2)
    elif format == "html":
        # TODO: Implement HTML report generation
        console.print("[yellow]HTML format not yet implemented[/yellow]")
    else:
        with open(output, "w") as f:
            for i, cycle in enumerate(data, 1):
                f.write(f"Cycle {i}:\n")
                f.write(f"  {' → '.join(cycle.cycle)}\n")
                f.write(f"  Suggestion: {cycle.suggestion}\n\n")


def generate_report(results: dict[str, Any], output: str, format: str) -> None:
    """Generate comprehensive analysis report."""
    import json

    if format == "json":
        with open(output, "w") as f:
            json.dump(results, f, indent=2)
    elif format == "html":
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Qontinui DevTools Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #2c3e50; }}
        .pass {{ color: #27ae60; }}
        .fail {{ color: #e74c3c; }}
        .error {{ color: #f39c12; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #3498db; color: white; }}
    </style>
</head>
<body>
    <h1>Qontinui DevTools Analysis Report</h1>
    <table>
        <tr><th>Check</th><th>Status</th><th>Details</th></tr>
        {"".join(f"<tr><td>{k}</td><td class='{v['status'].lower()}'>{v['status']}</td><td>{v}</td></tr>"
                 for k, v in results.items())}
    </table>
</body>
</html>
"""
        with open(output, "w") as f:
            f.write(html_content)
    else:
        with open(output, "w") as f:
            f.write("QONTINUI DEVTOOLS ANALYSIS REPORT\n")
            f.write("=" * 50 + "\n\n")
            for check, result in results.items():
                f.write(f"{check.upper()}: {result['status']}\n")
                f.write(f"  {result}\n\n")


@main.command("analyze")
@click.argument("path", type=click.Path(exists=True))
@click.option("--report", type=click.Path(), help="Generate HTML report at specified path")
@click.option(
    "--format",
    type=click.Choice(["text", "json", "html"], case_sensitive=False),
    default="text",
    help="Output format (text: console output, json: JSON file, html: interactive report)",
)
@click.option("--output", type=click.Path(), help="Output file path (used with --format)")
@click.option("--verbose", is_flag=True, help="Enable verbose output")
def analyze(
    path: str, report: str | None, format: str, output: str | None, verbose: bool
) -> None:
    """Run comprehensive analysis and generate interactive HTML report.

    This command runs all available analysis tools (imports, architecture, quality,
    concurrency) and aggregates the results into a comprehensive report.

    Examples:

        # Run analysis with console output
        qontinui-devtools analyze ./src

        # Generate interactive HTML report
        qontinui-devtools analyze ./src --report analysis_report.html

        # Generate HTML report with custom name
        qontinui-devtools analyze ./src --format html --output report.html

        # Save JSON results
        qontinui-devtools analyze ./src --format json --output results.json

        # Verbose mode
        qontinui-devtools analyze ./src --report report.html --verbose
    """
    try:
        from .reporting import ReportAggregator, HTMLReportGenerator
    except ImportError:
        console.print("[red]Error: Reporting module not available[/red]")
        sys.exit(1)

    console.print(f"[bold]Running comprehensive analysis on: {path}[/bold]\n")

    # Create aggregator and run all analyses
    aggregator = ReportAggregator(path, verbose=verbose)

    with console.status("[bold green]Running all analyses..."):
        try:
            report_data = aggregator.run_all_analyses()
        except Exception as e:
            console.print(f"[red]Error during analysis: {e}[/red]")
            if verbose:
                import traceback

                traceback.print_exc()
            sys.exit(1)

    # Display summary in console
    console.print("\n[bold cyan]═══ Analysis Summary ═══[/bold cyan]\n")

    # Overall status
    status_color, status_icon, status_message = report_data.get_overall_status()
    panel = Panel(
        f"{status_icon} {status_message}",
        title="Overall Status",
        border_style=status_color,
    )
    console.print(panel)

    # Key metrics table
    table = Table(title="\nKey Metrics", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan", width=30)
    table.add_column("Value", justify="right", style="green")

    metrics = report_data.summary_metrics
    table.add_row("Files Analyzed", str(metrics.get("files_analyzed", 0)))
    table.add_row("Total Lines", f"{metrics.get('total_lines', 0):,}")
    table.add_row("Circular Dependencies", str(metrics.get("circular_dependencies", 0)))
    table.add_row("God Classes", str(metrics.get("god_classes", 0)))
    table.add_row("Race Conditions", str(metrics.get("race_conditions", 0)))
    table.add_row("SRP Violations", str(metrics.get("srp_violations", 0)))
    table.add_row("Critical Issues", str(metrics.get("critical_issues", 0)))

    console.print(table)

    # Section summary
    console.print("\n[bold]Section Results:[/bold]\n")
    for section in report_data.sections:
        severity_icon = {
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "info": "ℹ️",
        }[section.severity]

        severity_color = {
            "success": "green",
            "warning": "yellow",
            "error": "red",
            "info": "blue",
        }[section.severity]

        console.print(
            f"  {severity_icon} [{severity_color}]{section.title}[/{severity_color}]"
        )

    # Generate outputs based on format
    if format == "html" or report:
        output_path = report or output or "analysis_report.html"
        generator = HTMLReportGenerator(verbose=verbose)

        with console.status(f"[bold green]Generating HTML report..."):
            try:
                generator.generate(report_data, output_path)
            except Exception as e:
                console.print(f"[red]Error generating HTML report: {e}[/red]")
                if verbose:
                    import traceback

                    traceback.print_exc()
                sys.exit(1)

        console.print(f"\n[green]✅ HTML report generated: {output_path}[/green]")
        console.print(
            "[blue]💡 Open in browser to view detailed analysis with charts and recommendations[/blue]"
        )

    elif format == "json" and output:
        import json

        # Convert report data to JSON
        json_data = {
            "project_name": report_data.project_name,
            "analysis_date": report_data.analysis_date.isoformat(),
            "project_path": report_data.project_path,
            "summary_metrics": report_data.summary_metrics,
            "sections": [
                {
                    "id": s.id,
                    "title": s.title,
                    "severity": s.severity,
                    "metrics": s.metrics,
                }
                for s in report_data.sections
            ],
        }

        with open(output, "w") as f:
            json.dump(json_data, f, indent=2)

        console.print(f"\n[green]✅ JSON report saved: {output}[/green]")

    # Final recommendations
    console.print("\n[bold]Next Steps:[/bold]")
    if metrics.get("critical_issues", 0) > 0:
        console.print(
            "  [red]1. Address critical issues immediately (circular deps, race conditions)[/red]"
        )
        console.print("  [yellow]2. Review warnings and plan refactoring[/yellow]")
        console.print("  3. Run analysis again to track progress")
    elif metrics.get("circular_dependencies", 0) > 0 or metrics.get("god_classes", 0) > 0:
        console.print("  [yellow]1. Refactor identified issues[/yellow]")
        console.print("  2. Review architecture recommendations")
        console.print("  3. Run analysis again to verify improvements")
    else:
        console.print("  [green]1. Excellent! Maintain code quality[/green]")
        console.print("  2. Continue regular code reviews")
        console.print("  3. Run analysis periodically to catch issues early")

    console.print()


@main.command("dashboard")
@click.option("--host", default="localhost", help="Server host address")
@click.option("--port", default=8765, type=int, help="Server port number")
@click.option("--interval", default=1.0, type=float, help="Metrics collection interval in seconds")
def start_dashboard(host: str, port: int, interval: float) -> None:
    """Start real-time performance dashboard.

    Launches a web-based dashboard that displays real-time system and application
    metrics via WebSocket streaming. The dashboard shows:

    - CPU and memory usage
    - Action execution statistics
    - Event processing metrics
    - Queue depths
    - Error rates

    The dashboard updates automatically every second and supports multiple
    concurrent viewers.

    Examples:

        # Start dashboard on default port
        qontinui-devtools dashboard

        # Start on custom host and port
        qontinui-devtools dashboard --host 0.0.0.0 --port 9000

        # Adjust collection interval
        qontinui-devtools dashboard --interval 0.5
    """
    try:
        from .runtime import DashboardServer, MetricsCollector
    except ImportError as e:
        console.print(f"[red]Error: Dashboard module not available: {e}[/red]")
        sys.exit(1)

    # Check for aiohttp
    try:
        import aiohttp
    except ImportError:
        console.print("[red]Error: aiohttp is required for the dashboard[/red]")
        console.print("[yellow]Install it with: pip install aiohttp[/yellow]")
        sys.exit(1)

    console.print(Panel.fit(
        f"[bold cyan]Qontinui Performance Dashboard[/bold cyan]\n\n"
        f"[green]Starting dashboard server...[/green]\n"
        f"  Host: {host}\n"
        f"  Port: {port}\n"
        f"  Update Interval: {interval}s\n\n"
        f"[blue]Open in browser:[/blue] http://{host}:{port}\n"
        f"[yellow]Press Ctrl+C to stop[/yellow]",
        title="Dashboard",
        border_style="cyan"
    ))

    # Create collector with specified interval
    collector = MetricsCollector(sample_interval=interval)

    # Create and start server
    server = DashboardServer(
        host=host,
        port=port,
        metrics_collector=collector
    )

    try:
        console.print(f"\n[green]✅ Dashboard running at http://{host}:{port}[/green]")
        console.print("[dim]Waiting for connections...[/dim]\n")
        server.start()
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping dashboard...[/yellow]")
        collector.stop()
        console.print("[green]✅ Dashboard stopped[/green]")
    except OSError as e:
        if "Address already in use" in str(e):
            console.print(f"[red]Error: Port {port} is already in use[/red]")
            console.print(f"[yellow]Try a different port with --port <port_number>[/yellow]")
        else:
            console.print(f"[red]Error starting server: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
