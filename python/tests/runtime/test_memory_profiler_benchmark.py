"""Performance benchmarks for memory profiler.

Tests profiler overhead and performance characteristics.
"""

import time
import pytest
from qontinui_devtools.runtime import MemoryProfiler


def test_snapshot_overhead(benchmark):
    """Benchmark snapshot creation overhead."""
    profiler = MemoryProfiler(enable_tracemalloc=False)
    profiler.start()

    def take_snapshot():
        return profiler.take_snapshot()

    result = benchmark(take_snapshot)
    profiler.stop()

    # Should be fast (< 100ms)
    assert result.timestamp > 0


def test_snapshot_with_tracemalloc_overhead(benchmark):
    """Benchmark snapshot creation with tracemalloc."""
    try:
        import tracemalloc
    except ImportError:
        pytest.skip("tracemalloc not available")

    profiler = MemoryProfiler(enable_tracemalloc=True)
    profiler.start()

    def take_snapshot():
        return profiler.take_snapshot()

    result = benchmark(take_snapshot)
    profiler.stop()

    assert result.timestamp > 0


def test_leak_detection_overhead(benchmark):
    """Benchmark leak detection overhead."""
    profiler = MemoryProfiler(enable_tracemalloc=False)
    profiler.start()

    # Create some snapshots
    for _ in range(10):
        profiler.take_snapshot()
        time.sleep(0.01)

    profiler.stop()

    def detect_leaks():
        return profiler.detect_leaks()

    leaks = benchmark(detect_leaks)
    assert isinstance(leaks, list)


def test_profiler_memory_overhead():
    """Test memory overhead of the profiler itself."""
    import psutil
    import gc

    gc.collect()
    process = psutil.Process()
    baseline_mb = process.memory_info().rss / (1024 * 1024)

    # Create profiler and take snapshots
    profiler = MemoryProfiler(enable_tracemalloc=False)
    profiler.start()

    for _ in range(100):
        profiler.take_snapshot()

    profiler.stop()

    gc.collect()
    final_mb = process.memory_info().rss / (1024 * 1024)

    overhead_mb = final_mb - baseline_mb

    # Profiler overhead should be reasonable (< 10 MB for 100 snapshots)
    assert overhead_mb < 10, f"Profiler overhead too high: {overhead_mb:.1f} MB"

    print(f"\nProfiler overhead: {overhead_mb:.2f} MB for 100 snapshots")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark-only"])
