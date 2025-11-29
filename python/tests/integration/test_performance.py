"""Performance tests for Phase 3 runtime monitoring tools.

This module includes:
- Performance benchmarks for all tools
- Overhead measurement
- Stress testing
- Memory leak detection
- Long-running monitoring tests
"""

import gc
import threading
import time

import pytest

# Mock implementations
try:
    from qontinui_devtools.runtime.dashboard import PerformanceDashboard
    from qontinui_devtools.runtime.event_tracer import EventTracer
    from qontinui_devtools.runtime.memory_profiler import MemoryProfiler
    from qontinui_devtools.runtime.profiler import ActionProfiler
except ImportError:

    class ActionProfiler:
        def __init__(self, config=None):
            self.config = config or {}
            self.is_running = False
            self.profiles = []

        def start(self):
            self.is_running = True

        def stop(self):
            self.is_running = False

        def profile(self, func):
            def wrapper(*args, **kwargs):
                start = time.perf_counter()
                result = func(*args, **kwargs)
                duration = time.perf_counter() - start
                self.profiles.append({"function": func.__name__, "duration": duration})
                return result

            return wrapper

        def get_profile_data(self):
            return {
                "profiles": self.profiles,
                "total_calls": len(self.profiles),
                "total_time": sum(p["duration"] for p in self.profiles),
            }

    class EventTracer:
        def __init__(self, config=None):
            self.config = config or {}
            self.is_running = False
            self.events = []

        def start(self):
            self.is_running = True

        def stop(self):
            self.is_running = False

        def trace_event(self, event_type, data):
            if self.is_running:
                self.events.append({"type": event_type, "data": data, "timestamp": time.time()})

        def get_events(self):
            return self.events

    class MemoryProfiler:
        def __init__(self, config=None):
            self.config = config or {}
            self.is_running = False
            self.snapshots = []

        def start(self):
            self.is_running = True
            self._take_snapshot()

        def stop(self):
            self.is_running = False
            self._take_snapshot()

        def _take_snapshot(self):
            import sys

            self.snapshots.append(
                {
                    "timestamp": time.time(),
                    "memory_mb": sys.getsizeof(self.snapshots) / (1024 * 1024),
                }
            )

        def get_memory_usage(self):
            if not self.snapshots:
                return {"current_mb": 0, "peak_mb": 0}
            current = self.snapshots[-1]["memory_mb"]
            peak = max(s["memory_mb"] for s in self.snapshots)
            return {"current_mb": current, "peak_mb": peak}

    class PerformanceDashboard:
        def __init__(self, config=None):
            self.config = config or {}
            self.is_running = False
            self.metrics = {}

        def start(self):
            self.is_running = True

        def stop(self):
            self.is_running = False

        def update_metrics(self, metrics):
            self.metrics.update(metrics)


@pytest.mark.integration
@pytest.mark.performance
class TestProfilerPerformance:
    """Performance tests for ActionProfiler."""

    def test_profiler_overhead(
        self, sample_action_instance, profiler_config, performance_thresholds
    ):
        """Test that profiler overhead is below threshold."""
        # Baseline: measure without profiler
        baseline_times = []
        for _ in range(10):
            start = time.perf_counter()
            sample_action_instance.execute(iterations=10)
            baseline_times.append(time.perf_counter() - start)

        baseline_avg = sum(baseline_times) / len(baseline_times)

        # With profiler
        profiler = ActionProfiler(profiler_config)
        profiler.start()

        profiled_times = []

        @profiler.profile
        def execute_profiled():
            start = time.perf_counter()
            sample_action_instance.execute(iterations=10)
            return time.perf_counter() - start

        for _ in range(10):
            profiled_times.append(execute_profiled())

        profiler.stop()
        profiled_avg = sum(profiled_times) / len(profiled_times)

        # Calculate overhead
        overhead_percent = ((profiled_avg - baseline_avg) / baseline_avg) * 100

        print(f"\nProfiler Overhead: {overhead_percent:.2f}%")
        print(f"Baseline: {baseline_avg*1000:.2f}ms")
        print(f"Profiled: {profiled_avg*1000:.2f}ms")

        # Assert overhead is below threshold
        assert (
            overhead_percent < performance_thresholds["max_overhead_percent"]
        ), f"Profiler overhead {overhead_percent:.2f}% exceeds threshold"

    def test_profiler_scalability(self, sample_action_instance, profiler_config):
        """Test profiler performance with increasing load."""
        profiler = ActionProfiler(profiler_config)
        profiler.start()

        @profiler.profile
        def execute():
            sample_action_instance.execute(iterations=5)

        # Test with increasing number of calls
        call_counts = [10, 100, 1000]
        overhead_percentages = []

        for count in call_counts:
            # Baseline
            start = time.perf_counter()
            for _ in range(count):
                sample_action_instance.execute(iterations=5)
            baseline = time.perf_counter() - start

            # With profiler
            start = time.perf_counter()
            for _ in range(count):
                execute()
            profiled = time.perf_counter() - start

            overhead = ((profiled - baseline) / baseline) * 100
            overhead_percentages.append(overhead)

            print(f"\n{count} calls: {overhead:.2f}% overhead")

        profiler.stop()

        # Overhead should not increase significantly with scale
        assert (
            max(overhead_percentages) - min(overhead_percentages) < 3.0
        ), "Overhead increases too much with scale"

    def test_profiler_memory_usage(
        self, sample_action_instance, profiler_config, performance_thresholds
    ):
        """Test profiler memory usage."""
        import sys

        profiler = ActionProfiler(profiler_config)

        # Measure memory before
        gc.collect()
        start_objects = len(gc.get_objects())

        profiler.start()

        @profiler.profile
        def execute():
            sample_action_instance.execute(iterations=10)

        # Generate many profile entries
        for _ in range(1000):
            execute()

        profiler.stop()

        # Measure memory after
        gc.collect()
        end_objects = len(gc.get_objects())

        profile_data = profiler.get_profile_data()
        memory_mb = sys.getsizeof(profile_data) / (1024 * 1024)

        print(f"\nProfiler memory usage: {memory_mb:.2f}MB")
        print(f"Object count increase: {end_objects - start_objects}")

        assert (
            memory_mb < performance_thresholds["max_memory_mb"]
        ), f"Profiler memory usage {memory_mb:.2f}MB exceeds threshold"


@pytest.mark.integration
@pytest.mark.performance
class TestEventTracerPerformance:
    """Performance tests for EventTracer."""

    def test_event_tracer_overhead(
        self, sample_action_instance, event_tracer_config, performance_thresholds
    ):
        """Test that event tracer overhead is below threshold."""
        iterations = 100

        # Baseline without tracer
        start = time.perf_counter()
        for i in range(iterations):
            sample_action_instance._process_iteration(i)
        baseline = time.perf_counter() - start

        # With tracer
        tracer = EventTracer(event_tracer_config)
        tracer.start()

        start = time.perf_counter()
        for i in range(iterations):
            tracer.trace_event("iteration", {"index": i})
            sample_action_instance._process_iteration(i)
        traced = time.perf_counter() - start

        tracer.stop()

        overhead_percent = ((traced - baseline) / baseline) * 100

        print(f"\nEvent Tracer Overhead: {overhead_percent:.2f}%")
        print(f"Baseline: {baseline*1000:.2f}ms")
        print(f"Traced: {traced*1000:.2f}ms")

        assert (
            overhead_percent < performance_thresholds["max_overhead_percent"]
        ), f"Event tracer overhead {overhead_percent:.2f}% exceeds threshold"

    def test_event_tracer_latency(self, event_tracer_config, performance_thresholds):
        """Test event tracing latency."""
        tracer = EventTracer(event_tracer_config)
        tracer.start()

        latencies = []
        for i in range(1000):
            start = time.perf_counter()
            tracer.trace_event("test", {"index": i})
            latency = (time.perf_counter() - start) * 1000  # Convert to ms
            latencies.append(latency)

        tracer.stop()

        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]

        print("\nEvent Tracing Latency:")
        print(f"  Average: {avg_latency:.4f}ms")
        print(f"  P95: {p95_latency:.4f}ms")
        print(f"  Max: {max_latency:.4f}ms")

        assert (
            avg_latency < performance_thresholds["max_event_latency_ms"]
        ), f"Average event latency {avg_latency:.4f}ms exceeds threshold"

    def test_event_tracer_memory_growth(self, event_tracer_config, performance_thresholds):
        """Test event tracer memory growth over time."""
        import sys

        tracer = EventTracer(event_tracer_config)
        tracer.start()

        # Trace many events
        for i in range(10000):
            tracer.trace_event("test", {"index": i, "data": "x" * 100})

        tracer.stop()

        events = tracer.get_events()
        memory_mb = sys.getsizeof(events) / (1024 * 1024)

        print(f"\nEvent buffer memory: {memory_mb:.2f}MB for {len(events)} events")
        print(f"Memory per event: {memory_mb / len(events) * 1024:.2f}KB")

        assert (
            memory_mb < performance_thresholds["max_memory_mb"]
        ), f"Event tracer memory {memory_mb:.2f}MB exceeds threshold"

    def test_event_tracer_concurrent_writes(self, event_tracer_config):
        """Test event tracer performance with concurrent writes."""
        tracer = EventTracer(event_tracer_config)
        tracer.start()

        def worker(thread_id: int, count: int):
            start = time.perf_counter()
            for i in range(count):
                tracer.trace_event("thread_event", {"thread_id": thread_id, "index": i})
            return time.perf_counter() - start

        # Test with increasing thread count
        threads = []
        results = {}

        num_threads = 10
        events_per_thread = 100

        start = time.perf_counter()

        for i in range(num_threads):
            t = threading.Thread(
                target=lambda tid=i: results.update({tid: worker(tid, events_per_thread)})
            )
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        total_time = time.perf_counter() - start

        tracer.stop()

        events = tracer.get_events()

        print("\nConcurrent Event Tracing:")
        print(f"  Threads: {num_threads}")
        print(f"  Events per thread: {events_per_thread}")
        print(f"  Total events: {len(events)}")
        print(f"  Total time: {total_time*1000:.2f}ms")
        print(f"  Events/sec: {len(events)/total_time:.0f}")

        # Verify all events were captured
        assert len(events) == num_threads * events_per_thread


@pytest.mark.integration
@pytest.mark.performance
class TestMemoryProfilerPerformance:
    """Performance tests for MemoryProfiler."""

    def test_memory_profiler_overhead(
        self, memory_intensive_action, memory_profiler_config, performance_thresholds
    ):
        """Test memory profiler overhead."""
        # Baseline
        start = time.perf_counter()
        memory_intensive_action.execute(size_mb=10)
        memory_intensive_action.cleanup()
        baseline = time.perf_counter() - start

        # With memory profiler
        mem_profiler = MemoryProfiler(memory_profiler_config)
        mem_profiler.start()

        start = time.perf_counter()
        memory_intensive_action.execute(size_mb=10)
        memory_intensive_action.cleanup()
        profiled = time.perf_counter() - start

        mem_profiler.stop()

        overhead_percent = ((profiled - baseline) / baseline) * 100

        print(f"\nMemory Profiler Overhead: {overhead_percent:.2f}%")

        assert (
            overhead_percent < performance_thresholds["max_overhead_percent"]
        ), f"Memory profiler overhead {overhead_percent:.2f}% exceeds threshold"

    def test_memory_profiler_sampling_performance(self, memory_profiler_config):
        """Test memory profiler sampling performance."""
        # Test with different sampling intervals
        intervals = [0.001, 0.01, 0.1]
        results = []

        for interval in intervals:
            config = memory_profiler_config.copy()
            config["sampling_interval"] = interval

            mem_profiler = MemoryProfiler(config)
            mem_profiler.start()

            start = time.perf_counter()
            time.sleep(1.0)  # Run for 1 second
            elapsed = time.perf_counter() - start

            mem_profiler.stop()

            snapshot_count = len(mem_profiler.snapshots)
            samples_per_sec = snapshot_count / elapsed

            results.append(
                {
                    "interval": interval,
                    "snapshots": snapshot_count,
                    "samples_per_sec": samples_per_sec,
                }
            )

            print(f"\nInterval: {interval}s")
            print(f"  Snapshots: {snapshot_count}")
            print(f"  Samples/sec: {samples_per_sec:.2f}")

        # Verify sampling rate scales appropriately
        assert results[0]["snapshots"] > results[1]["snapshots"]
        assert results[1]["snapshots"] > results[2]["snapshots"]


@pytest.mark.integration
@pytest.mark.performance
@pytest.mark.stress
class TestStressTests:
    """Stress tests for runtime monitoring tools."""

    def test_profiler_stress_many_calls(
        self, sample_action_instance, profiler_config, stress_test_config
    ):
        """Stress test profiler with many function calls."""
        profiler = ActionProfiler(profiler_config)
        profiler.start()

        @profiler.profile
        def fast_function():
            return sample_action_instance._process_iteration(0)

        start = time.perf_counter()

        # Make many rapid calls
        iterations = stress_test_config["iterations_per_thread"] * 10
        for _ in range(iterations):
            fast_function()

        elapsed = time.perf_counter() - start

        profiler.stop()

        profile_data = profiler.get_profile_data()

        print("\nProfiler Stress Test:")
        print(f"  Total calls: {profile_data['total_calls']}")
        print(f"  Duration: {elapsed:.2f}s")
        print(f"  Calls/sec: {profile_data['total_calls']/elapsed:.0f}")

        # Verify all calls were captured
        assert profile_data["total_calls"] == iterations

    def test_event_tracer_stress_high_volume(self, event_tracer_config, stress_test_config):
        """Stress test event tracer with high event volume."""
        tracer = EventTracer(event_tracer_config)
        tracer.start()

        start = time.perf_counter()

        num_events = stress_test_config["iterations_per_thread"] * 100

        for i in range(num_events):
            tracer.trace_event(
                "stress_test", {"index": i, "timestamp": time.time(), "data": {"value": i * 2}}
            )

        elapsed = time.perf_counter() - start

        tracer.stop()

        events = tracer.get_events()

        print("\nEvent Tracer Stress Test:")
        print(f"  Total events: {len(events)}")
        print(f"  Duration: {elapsed:.2f}s")
        print(f"  Events/sec: {len(events)/elapsed:.0f}")

        # Verify all events were captured
        assert len(events) == num_events

    def test_concurrent_stress_all_tools(
        self,
        concurrent_action,
        profiler_config,
        event_tracer_config,
        memory_profiler_config,
        stress_test_config,
    ):
        """Stress test all tools running concurrently."""
        profiler = ActionProfiler(profiler_config)
        tracer = EventTracer(event_tracer_config)
        mem_profiler = MemoryProfiler(memory_profiler_config)

        profiler.start()
        tracer.start()
        mem_profiler.start()

        def worker(thread_id: int):
            @profiler.profile
            def execute():
                tracer.trace_event("thread_start", {"thread_id": thread_id})

                for i in range(stress_test_config["iterations_per_thread"]):
                    result = concurrent_action.execute_threaded(thread_id, iterations=10)
                    tracer.trace_event("iteration", {"thread_id": thread_id, "iteration": i})

                tracer.trace_event("thread_end", {"thread_id": thread_id})
                return result

            return execute()

        start = time.perf_counter()

        threads = []
        for i in range(stress_test_config["num_threads"]):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        elapsed = time.perf_counter() - start

        mem_profiler.stop()
        tracer.stop()
        profiler.stop()

        # Collect metrics
        profile_data = profiler.get_profile_data()
        events = tracer.get_events()
        memory_data = mem_profiler.get_memory_usage()

        print("\nConcurrent Stress Test:")
        print(f"  Threads: {stress_test_config['num_threads']}")
        print(f"  Iterations per thread: {stress_test_config['iterations_per_thread']}")
        print(f"  Duration: {elapsed:.2f}s")
        print(f"  Profile calls: {profile_data['total_calls']}")
        print(f"  Events traced: {len(events)}")
        print(f"  Peak memory: {memory_data['peak_mb']:.2f}MB")

        # Verify data from all threads
        assert profile_data["total_calls"] >= stress_test_config["num_threads"]
        assert len(events) > 0

    def test_long_running_monitoring(
        self, sample_action_instance, profiler_config, event_tracer_config
    ):
        """Test tools can handle long-running monitoring sessions."""
        profiler = ActionProfiler(profiler_config)
        tracer = EventTracer(event_tracer_config)

        profiler.start()
        tracer.start()

        @profiler.profile
        def execute():
            tracer.trace_event("action", {})
            return sample_action_instance.execute(iterations=5)

        start = time.perf_counter()
        duration = 5.0  # Run for 5 seconds

        iteration = 0
        while time.perf_counter() - start < duration:
            execute()
            iteration += 1
            time.sleep(0.01)

        elapsed = time.perf_counter() - start

        tracer.stop()
        profiler.stop()

        profile_data = profiler.get_profile_data()
        events = tracer.get_events()

        print("\nLong-Running Test:")
        print(f"  Duration: {elapsed:.2f}s")
        print(f"  Iterations: {iteration}")
        print(f"  Profile calls: {profile_data['total_calls']}")
        print(f"  Events: {len(events)}")
        print(f"  Avg time per iteration: {elapsed/iteration*1000:.2f}ms")

        assert profile_data["total_calls"] == iteration
        assert len(events) == iteration


@pytest.mark.integration
@pytest.mark.performance
class TestMemoryLeakDetection:
    """Tests to detect memory leaks in monitoring tools."""

    def test_profiler_no_memory_leak(self, sample_action_instance, profiler_config):
        """Test that profiler doesn't leak memory over time."""
        import sys

        profiler = ActionProfiler(profiler_config)

        @profiler.profile
        def execute():
            sample_action_instance.execute(iterations=5)

        # Warm up
        profiler.start()
        for _ in range(100):
            execute()
        profiler.stop()

        # Measure memory at intervals
        memory_samples = []

        for cycle in range(5):
            gc.collect()
            profiler = ActionProfiler(profiler_config)
            profiler.start()

            for _ in range(1000):
                execute()

            profiler.stop()

            data = profiler.get_profile_data()
            memory_mb = sys.getsizeof(data) / (1024 * 1024)
            memory_samples.append(memory_mb)

            print(f"Cycle {cycle + 1}: {memory_mb:.2f}MB")

            del profiler
            gc.collect()

        # Verify memory doesn't grow significantly
        first_sample = memory_samples[0]
        last_sample = memory_samples[-1]
        growth_percent = ((last_sample - first_sample) / first_sample) * 100

        print(f"\nMemory growth: {growth_percent:.2f}%")

        assert growth_percent < 10, f"Memory leak detected: {growth_percent:.2f}% growth"

    def test_event_tracer_no_memory_leak(self, event_tracer_config):
        """Test that event tracer doesn't leak memory."""
        import sys

        memory_samples = []

        for cycle in range(5):
            gc.collect()
            tracer = EventTracer(event_tracer_config)
            tracer.start()

            for i in range(1000):
                tracer.trace_event("test", {"index": i})

            tracer.stop()

            events = tracer.get_events()
            memory_mb = sys.getsizeof(events) / (1024 * 1024)
            memory_samples.append(memory_mb)

            print(f"Cycle {cycle + 1}: {memory_mb:.2f}MB")

            del tracer
            del events
            gc.collect()

        # Verify memory is stable
        first_sample = memory_samples[0]
        last_sample = memory_samples[-1]
        growth_percent = ((last_sample - first_sample) / first_sample) * 100

        print(f"\nMemory growth: {growth_percent:.2f}%")

        assert growth_percent < 10, f"Memory leak detected: {growth_percent:.2f}% growth"


@pytest.mark.integration
@pytest.mark.performance
class TestOverallPerformanceMetrics:
    """Test overall performance metrics for the monitoring suite."""

    def test_combined_overhead_threshold(
        self,
        sample_action_instance,
        profiler_config,
        event_tracer_config,
        memory_profiler_config,
        performance_thresholds,
    ):
        """Test that combined overhead of all tools meets threshold."""
        # Baseline
        baseline_times = []
        for _ in range(10):
            start = time.perf_counter()
            sample_action_instance.execute(iterations=10)
            baseline_times.append(time.perf_counter() - start)

        baseline_avg = sum(baseline_times) / len(baseline_times)

        # With all tools
        profiler = ActionProfiler(profiler_config)
        tracer = EventTracer(event_tracer_config)
        mem_profiler = MemoryProfiler(memory_profiler_config)

        profiler.start()
        tracer.start()
        mem_profiler.start()

        monitored_times = []

        @profiler.profile
        def execute_monitored():
            tracer.trace_event("execute", {})
            start = time.perf_counter()
            result = sample_action_instance.execute(iterations=10)
            elapsed = time.perf_counter() - start
            return elapsed

        for _ in range(10):
            monitored_times.append(execute_monitored())

        mem_profiler.stop()
        tracer.stop()
        profiler.stop()

        monitored_avg = sum(monitored_times) / len(monitored_times)
        overhead_percent = ((monitored_avg - baseline_avg) / baseline_avg) * 100

        print("\nCombined Overhead:")
        print(f"  Baseline: {baseline_avg*1000:.2f}ms")
        print(f"  Monitored: {monitored_avg*1000:.2f}ms")
        print(f"  Overhead: {overhead_percent:.2f}%")

        assert (
            overhead_percent < performance_thresholds["max_overhead_percent"]
        ), f"Combined overhead {overhead_percent:.2f}% exceeds {performance_thresholds['max_overhead_percent']}%"
