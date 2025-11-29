"""Tests for memory profiler."""

import gc
import time

import pytest
from qontinui_devtools.runtime import (
    MemoryLeak,
    MemoryProfiler,
    MemorySnapshot,
)


class TestMemorySnapshot:
    """Test MemorySnapshot dataclass."""

    def test_snapshot_creation(self):
        """Test creating a snapshot."""
        snapshot = MemorySnapshot(
            timestamp=time.time(),
            total_mb=100.0,
            rss_mb=95.0,
            vms_mb=120.0,
            objects_by_type={"dict": 100, "list": 50},
            top_objects=[("dict", 1000), ("list", 500)],
            tracemalloc_snapshot=None,
            gc_stats={"collections": (100, 10, 1)},
        )

        assert snapshot.total_mb == 100.0
        assert snapshot.objects_by_type["dict"] == 100
        assert len(snapshot.top_objects) == 2

    def test_snapshot_string_representation(self):
        """Test snapshot string representation."""
        snapshot = MemorySnapshot(
            timestamp=1234567.89,
            total_mb=100.5,
            rss_mb=95.0,
            vms_mb=120.0,
            objects_by_type={"dict": 100, "list": 50},
            top_objects=[],
        )

        str_repr = str(snapshot)
        assert "1234567.89" in str_repr
        assert "100.5" in str_repr
        assert "objects=150" in str_repr


class TestMemoryLeak:
    """Test MemoryLeak dataclass."""

    def test_leak_creation(self):
        """Test creating a leak report."""
        leak = MemoryLeak(
            object_type="dict",
            count_increase=1000,
            size_increase_mb=2.5,
            growth_rate=100.0,
            samples=[(0.0, 100), (1.0, 200), (2.0, 300)],
            confidence=0.95,
        )

        assert leak.object_type == "dict"
        assert leak.count_increase == 1000
        assert leak.confidence == 0.95

    def test_leak_string_representation(self):
        """Test leak string representation."""
        leak = MemoryLeak(
            object_type="list",
            count_increase=500,
            size_increase_mb=1.2,
            growth_rate=50.0,
            samples=[],
            confidence=0.85,
        )

        str_repr = str(leak)
        assert "list" in str_repr
        assert "+500" in str_repr
        assert "1.2" in str_repr
        assert "85.00%" in str_repr


class TestMemoryProfiler:
    """Test MemoryProfiler class."""

    def test_profiler_creation(self):
        """Test creating a profiler."""
        profiler = MemoryProfiler(
            enable_tracemalloc=False,
            snapshot_interval=1.0,
        )

        assert profiler._interval == 1.0
        assert not profiler._running
        assert len(profiler._snapshots) == 0

    def test_start_stop(self):
        """Test starting and stopping profiler."""
        profiler = MemoryProfiler(enable_tracemalloc=False)

        profiler.start()
        assert profiler._running
        assert profiler._baseline is not None

        profiler.stop()
        assert not profiler._running

    def test_cannot_start_twice(self):
        """Test that starting twice raises error."""
        profiler = MemoryProfiler(enable_tracemalloc=False)
        profiler.start()

        with pytest.raises(RuntimeError, match="already running"):
            profiler.start()

        profiler.stop()

    def test_take_snapshot(self):
        """Test taking a snapshot."""
        profiler = MemoryProfiler(enable_tracemalloc=False)
        profiler.start()

        snapshot = profiler.take_snapshot()

        assert isinstance(snapshot, MemorySnapshot)
        assert snapshot.total_mb > 0
        assert snapshot.rss_mb > 0
        assert len(snapshot.objects_by_type) > 0
        assert "dict" in snapshot.objects_by_type
        assert "list" in snapshot.objects_by_type

        profiler.stop()

    def test_multiple_snapshots(self):
        """Test taking multiple snapshots."""
        profiler = MemoryProfiler(enable_tracemalloc=False)
        profiler.start()

        # Take 3 snapshots
        for _ in range(3):
            profiler.take_snapshot()
            time.sleep(0.1)

        assert len(profiler.snapshots) == 4  # baseline + 3

        profiler.stop()

    def test_detect_leak_insufficient_samples(self):
        """Test leak detection with insufficient samples."""
        profiler = MemoryProfiler(enable_tracemalloc=False)
        profiler.start()

        profiler.take_snapshot()

        leaks = profiler.detect_leaks(min_samples=3)
        assert len(leaks) == 0

        profiler.stop()

    def test_detect_leak_with_intentional_leak(self):
        """Test detecting an intentional memory leak."""
        profiler = MemoryProfiler(enable_tracemalloc=False, snapshot_interval=0.2)
        profiler.start()

        # Create intentional leak
        leaky_list = []
        for i in range(5):
            # Take snapshot
            profiler.take_snapshot()

            # Leak memory by creating many dicts
            leaky_list.extend([{"data": f"x{j}" * 100} for j in range(500)])
            time.sleep(0.2)

        # Detect leaks
        leaks = profiler.detect_leaks(min_samples=3, growth_threshold=1.0, min_increase=100)

        profiler.stop()

        # Should detect dict leak
        assert len(leaks) > 0
        dict_leaks = [leak for leak in leaks if leak.object_type == "dict"]
        assert len(dict_leaks) > 0

        # Check leak properties
        dict_leak = dict_leaks[0]
        assert dict_leak.count_increase > 0
        assert dict_leak.growth_rate > 0
        assert dict_leak.confidence > 0

    def test_compare_snapshots(self):
        """Test comparing two snapshots."""
        profiler = MemoryProfiler(enable_tracemalloc=False)
        profiler.start()

        snapshot1 = profiler.take_snapshot()

        # Allocate some memory
        data = [{"key": f"value{i}"} for i in range(1000)]

        time.sleep(0.1)
        snapshot2 = profiler.take_snapshot()

        comparison = profiler.compare_snapshots(snapshot1, snapshot2)

        assert "time_diff" in comparison
        assert "memory_diff_mb" in comparison
        assert "memory_rate_mb_per_sec" in comparison
        assert "type_diffs" in comparison
        assert comparison["time_diff"] > 0

        # Should see increase in dicts
        assert "dict" in comparison["type_diffs"]

        profiler.stop()

        # Clean up
        del data
        gc.collect()

    def test_generate_report(self):
        """Test generating a report."""
        profiler = MemoryProfiler(enable_tracemalloc=False)
        profiler.start()

        # Take some snapshots
        for _ in range(3):
            profiler.take_snapshot()
            time.sleep(0.1)

        report = profiler.generate_report()

        assert isinstance(report, str)
        assert "MEMORY PROFILING REPORT" in report
        assert "SUMMARY" in report
        assert "Duration" in report
        assert "Snapshots" in report

        profiler.stop()

    def test_baseline_property(self):
        """Test baseline property."""
        profiler = MemoryProfiler(enable_tracemalloc=False)

        assert profiler.baseline is None

        profiler.start()
        assert profiler.baseline is not None
        assert isinstance(profiler.baseline, MemorySnapshot)

        profiler.stop()

    def test_snapshots_property(self):
        """Test snapshots property."""
        profiler = MemoryProfiler(enable_tracemalloc=False)
        profiler.start()

        profiler.take_snapshot()
        profiler.take_snapshot()

        snapshots = profiler.snapshots
        assert len(snapshots) == 3  # baseline + 2
        assert all(isinstance(s, MemorySnapshot) for s in snapshots)

        # Should be a copy
        snapshots.clear()
        assert len(profiler.snapshots) == 3

        profiler.stop()

    def test_clear_snapshots(self):
        """Test clearing snapshots."""
        profiler = MemoryProfiler(enable_tracemalloc=False)
        profiler.start()

        profiler.take_snapshot()
        profiler.take_snapshot()

        assert len(profiler.snapshots) > 0
        assert profiler.baseline is not None

        profiler.clear()

        assert len(profiler.snapshots) == 0
        assert profiler.baseline is None

        profiler.stop()

    def test_gc_stats_collection(self):
        """Test GC statistics collection."""
        profiler = MemoryProfiler(enable_tracemalloc=False)
        profiler.start()

        snapshot = profiler.take_snapshot()

        assert "collections" in snapshot.gc_stats
        assert "objects" in snapshot.gc_stats
        assert "garbage" in snapshot.gc_stats
        assert isinstance(snapshot.gc_stats["collections"], tuple)
        assert len(snapshot.gc_stats["collections"]) == 3  # gen0, gen1, gen2

        profiler.stop()

    def test_analyze_growth_linear(self):
        """Test growth analysis with linear growth."""
        profiler = MemoryProfiler(enable_tracemalloc=False)

        # Simulate linear growth
        samples = [(float(i), i * 10) for i in range(10)]

        is_growing, rate, confidence = profiler._analyze_growth(samples, threshold=5.0)

        assert is_growing
        assert rate > 5.0
        assert confidence > 0.9  # Should be very confident about linear growth

    def test_analyze_growth_no_growth(self):
        """Test growth analysis with no growth."""
        profiler = MemoryProfiler(enable_tracemalloc=False)

        # Simulate no growth
        samples = [(float(i), 100) for i in range(10)]

        is_growing, rate, confidence = profiler._analyze_growth(samples, threshold=1.0)

        assert not is_growing
        assert abs(rate) < 1.0

    def test_analyze_growth_noisy_data(self):
        """Test growth analysis with noisy data."""
        profiler = MemoryProfiler(enable_tracemalloc=False)

        # Simulate noisy data (random fluctuation)
        import random

        samples = [(float(i), 100 + random.randint(-10, 10)) for i in range(10)]

        is_growing, rate, confidence = profiler._analyze_growth(samples, threshold=5.0)

        # Should not detect growth with random noise
        assert not is_growing or confidence < 0.7

    def test_estimate_size_increase(self):
        """Test size increase estimation."""
        profiler = MemoryProfiler(enable_tracemalloc=False)

        # Test various types
        dict_size = profiler._estimate_size_increase("dict", 1000)
        assert dict_size > 0

        list_size = profiler._estimate_size_increase("list", 1000)
        assert list_size > 0

        # Dict should be larger than list
        assert dict_size > list_size

    def test_profiler_with_tracemalloc(self):
        """Test profiler with tracemalloc enabled."""
        try:
            import tracemalloc

            tracemalloc_available = True
        except ImportError:
            tracemalloc_available = False

        if not tracemalloc_available:
            pytest.skip("tracemalloc not available")

        profiler = MemoryProfiler(enable_tracemalloc=True)
        profiler.start()

        snapshot = profiler.take_snapshot()

        assert snapshot.tracemalloc_snapshot is not None

        profiler.stop()

    def test_empty_snapshots_report(self):
        """Test generating report with no snapshots."""
        profiler = MemoryProfiler(enable_tracemalloc=False)

        report = profiler.generate_report()

        assert "No snapshots collected" in report


class TestMemoryProfilerIntegration:
    """Integration tests for memory profiler."""

    def test_full_profiling_session(self):
        """Test a complete profiling session."""
        profiler = MemoryProfiler(enable_tracemalloc=False, snapshot_interval=0.2)
        profiler.start()

        baseline = profiler.baseline
        assert baseline is not None

        # Simulate work with memory allocation
        cache = []
        for iteration in range(5):
            # Take snapshot
            snapshot = profiler.take_snapshot()
            assert snapshot.timestamp > baseline.timestamp

            # Do some work
            cache.extend([{"iteration": iteration, "data": "x" * 1000} for _ in range(200)])
            time.sleep(0.2)

        # Final snapshot
        final = profiler.take_snapshot()

        # Detect leaks
        leaks = profiler.detect_leaks(min_samples=3)

        # Generate report
        report = profiler.generate_report()

        profiler.stop()

        # Assertions
        assert len(profiler.snapshots) >= 6  # baseline + 5 + final
        assert final.total_mb > baseline.total_mb
        assert len(leaks) > 0
        assert "MEMORY PROFILING REPORT" in report

        # Clean up
        del cache
        gc.collect()

    def test_memory_growth_detection(self):
        """Test detecting memory growth over time."""
        profiler = MemoryProfiler(enable_tracemalloc=False)
        profiler.start()

        # Create growing cache
        cache = []
        snapshots = []

        for i in range(10):
            snapshot = profiler.take_snapshot()
            snapshots.append(snapshot)

            # Add more items each iteration
            cache.extend([f"item{i}_{j}" * 10 for j in range(100)])
            time.sleep(0.1)

        # Check memory growth
        memory_values = [s.total_mb for s in snapshots]
        assert memory_values[-1] > memory_values[0]

        # Detect leaks
        leaks = profiler.detect_leaks(min_samples=3)
        assert len(leaks) > 0

        profiler.stop()

        # Clean up
        del cache
        gc.collect()

    def test_stable_memory_no_leaks(self):
        """Test that stable memory usage doesn't trigger leak detection."""
        profiler = MemoryProfiler(enable_tracemalloc=False)
        profiler.start()

        # Allocate fixed amount of memory
        fixed_data = [{"key": f"value{i}"} for i in range(1000)]

        # Take multiple snapshots
        for _ in range(5):
            profiler.take_snapshot()
            time.sleep(0.1)

        # Detect leaks
        leaks = profiler.detect_leaks(min_samples=3, growth_threshold=10.0)

        profiler.stop()

        # Should not detect significant leaks with stable memory
        # (or very few with low confidence)
        major_leaks = [l for l in leaks if l.confidence > 0.8]
        assert len(major_leaks) == 0

        # Clean up
        del fixed_data
        gc.collect()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
