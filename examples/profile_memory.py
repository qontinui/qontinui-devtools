"""Example: Memory profiling and leak detection.

This example demonstrates how to use the MemoryProfiler to:
- Track memory usage over time
- Detect memory leaks
- Analyze object allocation patterns
- Generate detailed reports
"""

import time

from qontinui_devtools.runtime import (
    MemoryProfiler,
    classify_leak_severity,
    detect_common_leak_patterns,
    suggest_fixes,
)


def simulate_memory_leak():
    """Simulate a memory leak for demonstration."""
    # This is an intentional leak for testing
    cache = []
    for i in range(10):
        # Leak some memory
        cache.extend([{"data": f"item_{i}_{j}" * 100} for j in range(500)])
        time.sleep(0.5)
    return cache


def simulate_stable_usage():
    """Simulate stable memory usage."""
    # Allocate fixed amount
    data = [{"key": f"value{i}"} for i in range(1000)]
    time.sleep(2)
    return data


def main():
    """Run memory profiling examples."""
    print("=" * 80)
    print("Memory Profiling Example")
    print("=" * 80)
    print()

    # Example 1: Basic memory profiling
    print("Example 1: Basic Memory Profiling")
    print("-" * 80)

    profiler = MemoryProfiler(
        enable_tracemalloc=True,
        snapshot_interval=1.0,
    )

    profiler.start()
    baseline = profiler.baseline
    print(f"Baseline: {baseline.total_mb:.1f} MB")
    print(f"Objects: {sum(baseline.objects_by_type.values()):,}")
    print()

    # Take some snapshots
    print("Taking snapshots...")
    for i in range(5):
        time.sleep(1)
        snapshot = profiler.take_snapshot()
        mem_change = snapshot.total_mb - baseline.total_mb
        print(f"  Snapshot {i+1}: {snapshot.total_mb:.1f} MB ({mem_change:+.1f} MB)")

    profiler.stop()
    print()

    # Example 2: Detect memory leak
    print("Example 2: Detecting Memory Leaks")
    print("-" * 80)

    profiler = MemoryProfiler(enable_tracemalloc=True)
    profiler.start()

    baseline = profiler.baseline
    print("Starting leak simulation...")
    print(f"Baseline memory: {baseline.total_mb:.1f} MB")
    print()

    # Simulate leak
    leaky_cache = []
    for iteration in range(10):
        snapshot = profiler.take_snapshot()
        mem_change = snapshot.total_mb - baseline.total_mb

        print(f"Iteration {iteration + 1}: {snapshot.total_mb:.1f} MB ({mem_change:+.1f} MB)")

        # Create leak
        leaky_cache.extend([{"iteration": iteration, "data": "x" * 1000} for _ in range(300)])
        time.sleep(0.3)

    profiler.stop()
    print()

    # Detect leaks
    print("Analyzing for leaks...")
    leaks = profiler.detect_leaks(min_samples=3, growth_threshold=5.0)

    if leaks:
        print(f"Detected {len(leaks)} potential memory leaks:")
        print()

        for i, leak in enumerate(leaks[:5], 1):
            severity = classify_leak_severity(
                leak.count_increase,
                leak.size_increase_mb,
                leak.growth_rate,
            )

            print(f"{i}. {leak.object_type} ({severity})")
            print(f"   Count increase: {leak.count_increase:,} objects")
            print(f"   Size increase: {leak.size_increase_mb:.2f} MB")
            print(f"   Growth rate: {leak.growth_rate:.1f} obj/s")
            print(f"   Confidence: {leak.confidence:.1%}")

            # Get suggestions
            fixes = suggest_fixes(leak.object_type)
            if fixes:
                print("   Suggestions:")
                for fix in fixes[:2]:
                    print(f"     - {fix}")
            print()
    else:
        print("No leaks detected")
        print()

    # Example 3: Snapshot comparison
    print("Example 3: Snapshot Comparison")
    print("-" * 80)

    profiler = MemoryProfiler(enable_tracemalloc=False)
    profiler.start()

    snapshot1 = profiler.take_snapshot()
    print(f"Snapshot 1: {snapshot1.total_mb:.1f} MB")

    # Allocate memory
    [{"key": f"value{i}" * 10} for i in range(5000)]
    time.sleep(0.5)

    snapshot2 = profiler.take_snapshot()
    print(f"Snapshot 2: {snapshot2.total_mb:.1f} MB")
    print()

    # Compare
    comparison = profiler.compare_snapshots(snapshot1, snapshot2)

    print("Comparison:")
    print(f"  Time difference: {comparison['time_diff']:.2f}s")
    print(f"  Memory difference: {comparison['memory_diff_mb']:+.2f} MB")
    print(f"  Rate: {comparison['memory_rate_mb_per_sec']:.2f} MB/s")
    print()

    print("Top object count changes:")
    for obj_type, diff in list(comparison["type_diffs"].items())[:10]:
        print(f"  {obj_type:30s} {diff:+10,d}")
    print()

    profiler.stop()

    # Example 4: Pattern detection
    print("Example 4: Detecting Common Patterns")
    print("-" * 80)

    profiler = MemoryProfiler(enable_tracemalloc=False)
    profiler.start()

    # Simulate various allocations
    [[i] * 100 for i in range(5000)]
    [{f"key{i}": i} for i in range(3000)]

    snapshot = profiler.take_snapshot()
    patterns = detect_common_leak_patterns(snapshot.objects_by_type)

    if patterns:
        print("Detected patterns:")
        for pattern in patterns:
            print(f"  - {pattern}")
    else:
        print("No concerning patterns detected")

    profiler.stop()
    print()

    # Example 5: Generate report
    print("Example 5: Generating Report")
    print("-" * 80)

    profiler = MemoryProfiler(enable_tracemalloc=False)
    profiler.start()

    # Take several snapshots
    for _ in range(5):
        profiler.take_snapshot()
        time.sleep(0.5)

    # Generate text report
    report = profiler.generate_report()
    print(report)

    profiler.stop()
    print()

    # Example 6: HTML report generation
    print("Example 6: HTML Report")
    print("-" * 80)

    try:
        from qontinui_devtools.runtime import generate_html_report

        profiler = MemoryProfiler(enable_tracemalloc=True)
        profiler.start()

        # Simulate some work
        cache = []
        for i in range(8):
            profiler.take_snapshot()
            cache.extend([{"iter": i, "data": "x" * 500} for _ in range(200)])
            time.sleep(0.3)

        leaks = profiler.detect_leaks()
        profiler.stop()

        # Generate HTML report
        output_file = "memory_profile_example.html"
        generate_html_report(
            profiler.snapshots,
            leaks,
            output_file,
            plot_dir="memory_plots",
        )

        print(f"HTML report generated: {output_file}")
        print("Plots directory: memory_plots/")

    except ImportError as e:
        print(f"Note: HTML report generation requires matplotlib: {e}")
    except Exception as e:
        print(f"Warning: Could not generate HTML report: {e}")

    print()
    print("=" * 80)
    print("Examples complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
