"""Tests for concurrent usage of Phase 3 runtime monitoring tools.

This module tests:
- Thread-safety of all tools
- Concurrent tool initialization and shutdown
- Race conditions in tool interactions
- Data consistency during concurrent operations
"""

from typing import Any
import asyncio
import threading
import time
from collections import defaultdict

import pytest

# Mock implementations
try:
    from qontinui_devtools.runtime.dashboard import PerformanceDashboard
    from qontinui_devtools.runtime.event_tracer import EventTracer
    from qontinui_devtools.runtime.memory_profiler import MemoryProfiler
    from qontinui_devtools.runtime.profiler import ActionProfiler
except ImportError:

    class ActionProfiler:
        def __init__(self, config=None) -> None:
            self.config = config or {}
            self.is_running = False
            self.profiles: list[Any] = []
            self._lock = threading.Lock()

        def start(self) -> None:
            self.is_running = True

        def stop(self) -> None:
            self.is_running = False

        def profile(self, func) -> Any:
            def wrapper(*args, **kwargs) -> Any:
                start = time.perf_counter()
                result = func(*args, **kwargs)
                duration = time.perf_counter() - start
                with self._lock:
                    self.profiles.append(
                        {
                            "function": func.__name__,
                            "duration": duration,
                            "thread_id": threading.get_ident(),
                        }
                    )
                return result

            return wrapper

        def get_profile_data(self) -> Any:
            with self._lock:
                return {
                    "profiles": self.profiles.copy(),
                    "total_calls": len(self.profiles),
                    "total_time": sum(p["duration"] for p in self.profiles),
                }

    class EventTracer:
        def __init__(self, config=None) -> None:
            self.config = config or {}
            self.is_running = False
            self.events: list[Any] = []
            self._lock = threading.Lock()

        def start(self) -> None:
            self.is_running = True

        def stop(self) -> None:
            self.is_running = False

        def trace_event(self, event_type, data) -> None:
            if self.is_running:
                with self._lock:
                    self.events.append(
                        {
                            "type": event_type,
                            "data": data,
                            "timestamp": time.time(),
                            "thread_id": threading.get_ident(),
                        }
                    )

        def get_events(self, event_type=None) -> Any:
            with self._lock:
                events = self.events.copy()

            if event_type:
                return [e for e in events if e["type"] == event_type]
            return events

    class MemoryProfiler:
        def __init__(self, config=None) -> None:
            self.config = config or {}
            self.is_running = False
            self.snapshots: list[Any] = []
            self._lock = threading.Lock()

        def start(self) -> None:
            self.is_running = True
            self._take_snapshot()

        def stop(self) -> None:
            self.is_running = False
            self._take_snapshot()

        def _take_snapshot(self) -> None:
            import sys

            with self._lock:
                self.snapshots.append(
                    {
                        "timestamp": time.time(),
                        "memory_mb": sys.getsizeof(self.snapshots) / (1024 * 1024),
                        "thread_id": threading.get_ident(),
                    }
                )

        def get_memory_usage(self) -> Any:
            with self._lock:
                if not self.snapshots:
                    return {"current_mb": 0, "peak_mb": 0}
                current = self.snapshots[-1]["memory_mb"]
                peak = max(s["memory_mb"] for s in self.snapshots)
                return {"current_mb": current, "peak_mb": peak}

    class PerformanceDashboard:
        def __init__(self, config=None) -> None:
            self.config = config or {}
            self.is_running = False
            self.metrics: dict[Any, Any] = {}
            self._lock = threading.Lock()

        def start(self) -> None:
            self.is_running = True

        def stop(self) -> None:
            self.is_running = False

        def update_metrics(self, metrics) -> None:
            with self._lock:
                self.metrics.update(metrics)

        def get_metrics(self) -> Any:
            with self._lock:
                return self.metrics.copy()


@pytest.mark.integration
@pytest.mark.concurrent
class TestConcurrentToolAccess:
    """Test concurrent access to monitoring tools."""

    def test_profiler_thread_safety(self, sample_action_instance, profiler_config) -> Any:
        """Test that profiler is thread-safe."""
        profiler = ActionProfiler(profiler_config)
        profiler.start()

        @profiler.profile
        def execute_in_thread(thread_id: int, iterations: int) -> Any:
            results: list[Any] = []
            for i in range(iterations):
                result = sample_action_instance._process_iteration(i)
                results.append(result)
            return results

        # Run multiple threads
        threads: list[Any] = []
        num_threads = 10
        iterations_per_thread = 20

        for i in range(num_threads):
            t = threading.Thread(target=execute_in_thread, args=(i, iterations_per_thread))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        profiler.stop()

        # Verify data integrity
        profile_data = profiler.get_profile_data()
        assert profile_data["total_calls"] == num_threads

        # Verify all threads are represented
        thread_ids = {p["thread_id"] for p in profile_data["profiles"]}
        assert len(thread_ids) == num_threads

    def test_event_tracer_thread_safety(self, event_tracer_config) -> None:
        """Test that event tracer is thread-safe."""
        tracer = EventTracer(event_tracer_config)
        tracer.start()

        def trace_events(thread_id: int, count: int) -> None:
            for i in range(count):
                tracer.trace_event("thread_event", {"thread_id": thread_id, "index": i})
                time.sleep(0.001)

        # Run multiple threads
        threads: list[Any] = []
        num_threads = 10
        events_per_thread = 50

        for i in range(num_threads):
            t = threading.Thread(target=trace_events, args=(i, events_per_thread))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        tracer.stop()

        # Verify all events were captured
        events = tracer.get_events()
        assert len(events) == num_threads * events_per_thread

        # Verify no data corruption
        thread_event_counts = defaultdict(int)
        for event in events:
            thread_id = event["data"]["thread_id"]
            thread_event_counts[thread_id] += 1

        assert len(thread_event_counts) == num_threads
        assert all(count == events_per_thread for count in thread_event_counts.values())

    def test_memory_profiler_thread_safety(self, memory_profiler_config) -> None:
        """Test that memory profiler is thread-safe."""
        mem_profiler = MemoryProfiler(memory_profiler_config)
        mem_profiler.start()

        def take_snapshots(count: int) -> None:
            for _ in range(count):
                mem_profiler._take_snapshot()
                time.sleep(0.001)

        # Run multiple threads taking snapshots
        threads: list[Any] = []
        num_threads = 5
        snapshots_per_thread = 10

        for _ in range(num_threads):
            t = threading.Thread(target=take_snapshots, args=(snapshots_per_thread,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        mem_profiler.stop()

        # Verify snapshots
        mem_profiler.get_memory_usage()
        # Should have start + thread snapshots + stop
        min_snapshots = 1 + (num_threads * snapshots_per_thread) + 1
        assert len(mem_profiler.snapshots) >= min_snapshots

    def test_dashboard_concurrent_updates(self, dashboard_config) -> None:
        """Test dashboard with concurrent metric updates."""
        dashboard = PerformanceDashboard(dashboard_config)
        dashboard.start()

        def update_metrics(thread_id: int, count: int) -> None:
            for i in range(count):
                dashboard.update_metrics(
                    {f"thread_{thread_id}_metric_{i}": {"value": i, "timestamp": time.time()}}
                )
                time.sleep(0.001)

        # Run multiple threads updating metrics
        threads: list[Any] = []
        num_threads = 5
        updates_per_thread = 20

        for i in range(num_threads):
            t = threading.Thread(target=update_metrics, args=(i, updates_per_thread))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        dashboard.stop()

        # Verify all metrics were recorded
        metrics = dashboard.get_metrics()
        expected_metrics = num_threads * updates_per_thread
        assert len(metrics) == expected_metrics


@pytest.mark.integration
@pytest.mark.concurrent
class TestConcurrentToolLifecycle:
    """Test concurrent initialization and shutdown of tools."""

    def test_concurrent_tool_initialization(
        self, profiler_config, event_tracer_config, memory_profiler_config, dashboard_config
    ) -> None:
        """Test initializing all tools concurrently."""
        tools: dict[Any, Any] = {}
        errors=[],

        def init_profiler() -> None:
            try:
                tools["profiler"] = ActionProfiler(profiler_config)
                tools["profiler"].start()
            except Exception as e:
                errors.append(("profiler", e))

        def init_tracer() -> None:
            try:
                tools["tracer"] = EventTracer(event_tracer_config)
                tools["tracer"].start()
            except Exception as e:
                errors.append(("tracer", e))

        def init_memory() -> None:
            try:
                tools["memory"] = MemoryProfiler(memory_profiler_config)
                tools["memory"].start()
            except Exception as e:
                errors.append(("memory", e))

        def init_dashboard() -> None:
            try:
                tools["dashboard"] = PerformanceDashboard(dashboard_config)
                tools["dashboard"].start()
            except Exception as e:
                errors.append(("dashboard", e))

        # Initialize all tools concurrently
        threads = [
            threading.Thread(target=init_profiler),
            threading.Thread(target=init_tracer),
            threading.Thread(target=init_memory),
            threading.Thread(target=init_dashboard),
        ]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Verify no errors
        assert len(errors) == 0, f"Initialization errors: {errors}"

        # Verify all tools initialized
        assert len(tools) == 4
        assert all(tool.is_running for tool in tools.values())

        # Clean up
        for tool in tools.values():
            tool.stop()

    def test_concurrent_tool_shutdown(
        self, profiler_config, event_tracer_config, memory_profiler_config
    ) -> None:
        """Test shutting down all tools concurrently."""
        # Initialize tools
        profiler = ActionProfiler(profiler_config)
        tracer = EventTracer(event_tracer_config)
        mem_profiler = MemoryProfiler(memory_profiler_config)

        profiler.start()
        tracer.start()
        mem_profiler.start()

        # Use tools briefly
        time.sleep(0.1)

        errors=[],

        def stop_profiler() -> None:
            try:
                profiler.stop()
            except Exception as e:
                errors.append(("profiler", e))

        def stop_tracer() -> None:
            try:
                tracer.stop()
            except Exception as e:
                errors.append(("tracer", e))

        def stop_memory() -> None:
            try:
                mem_profiler.stop()
            except Exception as e:
                errors.append(("memory", e))

        # Stop all tools concurrently
        threads = [
            threading.Thread(target=stop_profiler),
            threading.Thread(target=stop_tracer),
            threading.Thread(target=stop_memory),
        ]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Verify no errors
        assert len(errors) == 0, f"Shutdown errors: {errors}"

        # Verify all tools stopped
        assert not profiler.is_running
        assert not tracer.is_running
        assert not mem_profiler.is_running

    def test_rapid_start_stop_cycles(self, profiler_config) -> None:
        """Test rapid start/stop cycles don't cause issues."""
        errors=[],

        def cycle_tool(cycle_id: int) -> None:
            try:
                for _i in range(10):
                    profiler = ActionProfiler(profiler_config)
                    profiler.start()
                    time.sleep(0.001)
                    profiler.stop()
            except Exception as e:
                errors.append((cycle_id, e))

        # Run multiple threads doing rapid cycles
        threads: list[Any] = []
        for i in range(5):
            t = threading.Thread(target=cycle_tool, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Verify no errors
        assert len(errors) == 0, f"Cycle errors: {errors}"


@pytest.mark.integration
@pytest.mark.concurrent
class TestConcurrentDataCollection:
    """Test data collection during concurrent operations."""

    def test_concurrent_profiling_and_tracing(
        self, sample_action_instance, profiler_config, event_tracer_config
    ) -> None:
        """Test profiling and tracing during concurrent execution."""
        profiler = ActionProfiler(profiler_config)
        tracer = EventTracer(event_tracer_config)

        profiler.start()
        tracer.start()

        @profiler.profile
        def worker(thread_id: int, iterations: int) -> None:
            tracer.trace_event("worker_start", {"thread_id": thread_id})

            for i in range(iterations):
                tracer.trace_event("iteration", {"thread_id": thread_id, "index": i})
                sample_action_instance._process_iteration(i)

            tracer.trace_event("worker_end", {"thread_id": thread_id})

        # Run workers concurrently
        threads: list[Any] = []
        num_threads = 8
        iterations = 10

        for i in range(num_threads):
            t = threading.Thread(target=worker, args=(i, iterations))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        tracer.stop()
        profiler.stop()

        # Verify data consistency
        profile_data = profiler.get_profile_data()
        tracer.get_events()

        # Should have profile data from all threads
        assert profile_data["total_calls"] == num_threads

        # Should have events from all threads
        start_events = tracer.get_events("worker_start")
        end_events = tracer.get_events("worker_end")
        iteration_events = tracer.get_events("iteration")

        assert len(start_events) == num_threads
        assert len(end_events) == num_threads
        assert len(iteration_events) == num_threads * iterations

    def test_dashboard_with_concurrent_data_sources(
        self,
        sample_action_instance,
        profiler_config,
        event_tracer_config,
        memory_profiler_config,
        dashboard_config,
    ) -> None:
        """Test dashboard receiving data from multiple concurrent sources."""
        profiler = ActionProfiler(profiler_config)
        tracer = EventTracer(event_tracer_config)
        mem_profiler = MemoryProfiler(memory_profiler_config)
        dashboard = PerformanceDashboard(dashboard_config)

        profiler.start()
        tracer.start()
        mem_profiler.start()
        dashboard.start()

        def data_collector(collector_id: int) -> None:
            @profiler.profile
            def collect() -> None:
                for i in range(20):
                    tracer.trace_event("collection", {"collector_id": collector_id, "index": i})

                    # Update dashboard periodically
                    if i % 5 == 0:
                        dashboard.update_metrics(
                            {
                                f"collector_{collector_id}": {
                                    "profiles": profiler.get_profile_data(),
                                    "events": len(tracer.get_events()),
                                    "memory": mem_profiler.get_memory_usage(),
                                }
                            }
                        )

                    sample_action_instance._process_iteration(i)
                    time.sleep(0.01)

            collect()

        # Run multiple data collectors
        threads: list[Any] = []
        num_collectors = 4

        for i in range(num_collectors):
            t = threading.Thread(target=data_collector, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        dashboard.stop()
        mem_profiler.stop()
        tracer.stop()
        profiler.stop()

        # Verify dashboard received data from all collectors
        metrics = dashboard.get_metrics()
        collector_metrics = [k for k in metrics.keys() if k.startswith("collector_")]
        assert len(collector_metrics) == num_collectors


@pytest.mark.integration
@pytest.mark.concurrent
class TestRaceConditions:
    """Test for race conditions in tool interactions."""

    def test_no_race_in_event_ordering(self, event_tracer_config) -> None:
        """Test that event ordering is preserved despite concurrent writes."""
        tracer = EventTracer(event_tracer_config)
        tracer.start()

        def trace_sequence(thread_id: int, count: int) -> None:
            for i in range(count):
                tracer.trace_event(
                    "sequence", {"thread_id": thread_id, "sequence": i, "timestamp": time.time()}
                )

        # Trace events from multiple threads
        threads: list[Any] = []
        num_threads = 5
        events_per_thread = 20

        for i in range(num_threads):
            t = threading.Thread(target=trace_sequence, args=(i, events_per_thread))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        tracer.stop()

        # Verify sequence within each thread
        events = tracer.get_events("sequence")

        # Group by thread
        thread_events = defaultdict(list)
        for event in events:
            thread_id = event["data"]["thread_id"]
            thread_events[thread_id].append(event["data"]["sequence"])

        # Verify each thread's sequence is in order
        for thread_id, sequences in thread_events.items():
            assert sequences == list(
                range(events_per_thread)
            ), f"Thread {thread_id} events out of order: {sequences}"

    def test_no_race_in_profile_data(self, sample_action_instance, profiler_config) -> Any:
        """Test that profile data remains consistent under concurrent access."""
        profiler = ActionProfiler(profiler_config)
        profiler.start()

        @profiler.profile
        def profiled_function(value: int) -> Any:
            time.sleep(0.001)
            return value * 2

        results: list[Any] = []
        errors=[],

        def worker(thread_id: int) -> None:
            try:
                local_results: list[Any] = []
                for i in range(50):
                    result = profiled_function(i)
                    local_results.append(result)

                    # Periodically read profile data
                    if i % 10 == 0:
                        data = profiler.get_profile_data()
                        assert data["total_calls"] > 0

                results.extend(local_results)
            except Exception as e:
                errors.append((thread_id, e))

        # Run workers
        threads: list[Any] = []
        num_threads = 5

        for i in range(num_threads):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        profiler.stop()

        # Verify no errors
        assert len(errors) == 0, f"Race condition errors: {errors}"

        # Verify profile data consistency
        profile_data = profiler.get_profile_data()
        assert profile_data["total_calls"] == num_threads * 50

    def test_no_deadlock_with_all_tools(
        self,
        sample_action_instance,
        profiler_config,
        event_tracer_config,
        memory_profiler_config,
        dashboard_config,
    ) -> None:
        """Test that no deadlocks occur with all tools running."""
        profiler = ActionProfiler(profiler_config)
        tracer = EventTracer(event_tracer_config)
        mem_profiler = MemoryProfiler(memory_profiler_config)
        dashboard = PerformanceDashboard(dashboard_config)

        profiler.start()
        tracer.start()
        mem_profiler.start()
        dashboard.start()

        completed = threading.Event()

        def intensive_worker(thread_id: int) -> None:
            @profiler.profile
            def work() -> None:
                for i in range(50):
                    tracer.trace_event("work", {"thread_id": thread_id, "i": i})

                    sample_action_instance._process_iteration(i)

                    if i % 10 == 0:
                        # Update dashboard with data from all tools
                        dashboard.update_metrics(
                            {
                                f"worker_{thread_id}": {
                                    "profiles": profiler.get_profile_data(),
                                    "events": len(tracer.get_events()),
                                    "memory": mem_profiler.get_memory_usage(),
                                }
                            }
                        )

            work()

        # Run multiple intensive workers
        threads: list[Any] = []
        for i in range(6):
            t = threading.Thread(target=intensive_worker, args=(i,))
            threads.append(t)
            t.start()

        # Set timeout to detect deadlocks
        def set_completed() -> None:
            for t in threads:
                t.join()
            completed.set()

        completion_thread = threading.Thread(target=set_completed)
        completion_thread.start()

        # Wait with timeout
        success = completed.wait(timeout=30.0)

        dashboard.stop()
        mem_profiler.stop()
        tracer.stop()
        profiler.stop()

        assert success, "Deadlock detected - operations did not complete in time"


@pytest.mark.integration
@pytest.mark.concurrent
class TestAsyncConcurrency:
    """Test tools with async/await patterns."""

    def test_profiler_with_async_await(self, sample_action_instance, profiler_config) -> Any:
        """Test profiler with async functions."""
        profiler = ActionProfiler(profiler_config)
        profiler.start()

        async def async_worker(worker_id: int):
            @profiler.profile
            def sync_work() -> Any:
                return sample_action_instance._process_iteration(worker_id)

            results: list[Any] = []
            for _i in range(10):
                result = sync_work()
                results.append(result)
                await asyncio.sleep(0.01)

            return results

        async def run_async_workers():
            tasks = [async_worker(i) for i in range(5)]
            return await asyncio.gather(*tasks)

        # Run async workers
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_async_workers())
        loop.close()

        profiler.stop()

        # Verify profiling worked
        profile_data = profiler.get_profile_data()
        assert profile_data["total_calls"] == 5 * 10  # 5 workers, 10 iterations each

    def test_event_tracer_with_async_await(self, event_tracer_config) -> None:
        """Test event tracer with async functions."""
        tracer = EventTracer(event_tracer_config)
        tracer.start()

        async def async_tracer(tracer_id: int):
            for i in range(10):
                tracer.trace_event("async_event", {"tracer_id": tracer_id, "index": i})
                await asyncio.sleep(0.01)

        async def run_async_tracers():
            tasks = [async_tracer(i) for i in range(5)]
            await asyncio.gather(*tasks)

        # Run async tracers
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_async_tracers())
        loop.close()

        tracer.stop()

        # Verify all events captured
        events = tracer.get_events("async_event")
        assert len(events) == 5 * 10  # 5 tracers, 10 events each
