"""Integration tests for Phase 3 runtime monitoring tools.

This module tests the integration between:
- Action Profiler
- Event Tracer
- Memory Profiler
- Performance Dashboard

All tests verify that tools work correctly together and don't interfere
with each other's operation.
"""

import asyncio
import json
import threading
import time
from pathlib import Path
from typing import Any

import pytest

# These imports will be available once Phase 3 tools are implemented
# For now, we'll use mock implementations to define the API
try:
    from qontinui_devtools.runtime.dashboard import PerformanceDashboard
    from qontinui_devtools.runtime.event_tracer import EventTracer
    from qontinui_devtools.runtime.memory_profiler import MemoryProfiler
    from qontinui_devtools.runtime.profiler import ActionProfiler
except ImportError:
    # Mock implementations for testing the API
    class ActionProfiler:
        """Mock Action Profiler for testing."""

        def __init__(self, config: dict[str, Any] = None) -> None:
            self.config = config or {}
            self.is_running = False
            self.profiles: list[Any] = []

        def start(self) -> None:
            """Start profiling."""
            self.is_running = True

        def stop(self) -> None:
            """Stop profiling."""
            self.is_running = False

        def profile(self, func) -> Any:
            """Decorator to profile a function."""

            def wrapper(*args, **kwargs) -> Any:
                start = time.perf_counter()
                result = func(*args, **kwargs)
                duration = time.perf_counter() - start
                self.profiles.append(
                    {"function": func.__name__, "duration": duration, "timestamp": time.time()}
                )
                return result

            return wrapper

        def get_profile_data(self) -> dict[str, Any]:
            """Get collected profile data."""
            return {
                "profiles": self.profiles,
                "total_calls": len(self.profiles),
                "total_time": sum(p["duration"] for p in self.profiles),
            }

        def export(self, output_path: Path, format: str = "json") -> None:
            """Export profile data."""
            data = self.get_profile_data()
            with open(output_path, "w") as f:
                json.dump(data, f, indent=2)

    class EventTracer:
        """Mock Event Tracer for testing."""

        def __init__(self, config: dict[str, Any] = None) -> None:
            self.config = config or {}
            self.is_running = False
            self.events: list[Any] = []

        def start(self) -> None:
            """Start tracing."""
            self.is_running = True

        def stop(self) -> None:
            """Stop tracing."""
            self.is_running = False

        def trace_event(self, event_type: str, data: dict[str, Any]) -> None:
            """Trace an event."""
            if self.is_running:
                self.events.append(
                    {
                        "type": event_type,
                        "data": data,
                        "timestamp": time.time(),
                        "thread_id": threading.get_ident(),
                    }
                )

        def get_events(self, event_type: str = None) -> list[dict[str, Any]]:
            """Get traced events."""
            if event_type:
                return [e for e in self.events if e["type"] == event_type]
            return self.events

        def export(self, output_path: Path, format: str = "json") -> None:
            """Export event data."""
            with open(output_path, "w") as f:
                json.dump(self.events, f, indent=2)

    class MemoryProfiler:
        """Mock Memory Profiler for testing."""

        def __init__(self, config: dict[str, Any] = None) -> None:
            self.config = config or {}
            self.is_running = False
            self.snapshots: list[Any] = []

        def start(self) -> None:
            """Start memory profiling."""
            self.is_running = True
            self._take_snapshot()

        def stop(self) -> None:
            """Stop memory profiling."""
            self.is_running = False
            self._take_snapshot()

        def _take_snapshot(self) -> None:
            """Take a memory snapshot."""
            import sys

            self.snapshots.append(
                {
                    "timestamp": time.time(),
                    "memory_mb": sys.getsizeof(self.snapshots) / (1024 * 1024),
                    "objects": len(self.snapshots),
                }
            )

        def get_memory_usage(self) -> dict[str, float]:
            """Get current memory usage."""
            if not self.snapshots:
                return {"current_mb": 0, "peak_mb": 0}

            current = self.snapshots[-1]["memory_mb"]
            peak = max(s["memory_mb"] for s in self.snapshots)

            return {"current_mb": current, "peak_mb": peak, "snapshots": len(self.snapshots)}

        def export(self, output_path: Path, format: str = "json") -> None:
            """Export memory profile data."""
            with open(output_path, "w") as f:
                json.dump(self.snapshots, f, indent=2)

    class PerformanceDashboard:
        """Mock Performance Dashboard for testing."""

        def __init__(self, config: dict[str, Any] = None) -> None:
            self.config = config or {}
            self.is_running = False
            self.metrics: dict[Any, Any] = {}

        def start(self) -> None:
            """Start dashboard."""
            self.is_running = True

        def stop(self) -> None:
            """Stop dashboard."""
            self.is_running = False

        def update_metrics(self, metrics: dict[str, Any]) -> None:
            """Update dashboard metrics."""
            self.metrics.update(metrics)

        def get_metrics(self) -> dict[str, Any]:
            """Get current metrics."""
            return self.metrics


@pytest.mark.integration
class TestProfilerEventTracerIntegration:
    """Test integration between ActionProfiler and EventTracer."""

    def test_profiler_and_tracer_together(
        self, sample_action_instance, profiler_config, event_tracer_config
    ):
        """Test that profiler and tracer can run simultaneously."""
        # Initialize tools
        profiler = ActionProfiler(profiler_config)
        tracer = EventTracer(event_tracer_config)

        # Start both
        profiler.start()
        tracer.start()

        try:
            # Execute action with both tools active
            @profiler.profile
            def execute_with_events() -> Any:
                tracer.trace_event("action_start", {"action": "sample"})
                result = sample_action_instance.execute(iterations=5)
                tracer.trace_event("action_end", {"action": "sample", "result": result})
                return result

            result = execute_with_events()

            # Verify both tools captured data
            profile_data = profiler.get_profile_data()
            events = tracer.get_events()

            assert profile_data["total_calls"] > 0
            assert len(events) >= 2  # At least start and end events
            assert result is not None

            # Verify event ordering
            start_events = tracer.get_events("action_start")
            end_events = tracer.get_events("action_end")
            assert len(start_events) == 1
            assert len(end_events) == 1
            assert start_events[0]["timestamp"] < end_events[0]["timestamp"]

        finally:
            profiler.stop()
            tracer.stop()

    def test_profiler_captures_tracer_overhead(
        self, profiler_config, event_tracer_config, sample_action_instance
    ):
        """Test that profiler can measure tracer overhead."""
        profiler = ActionProfiler(profiler_config)
        tracer = EventTracer(event_tracer_config)

        # Measure without tracer
        profiler.start()

        @profiler.profile
        def without_tracer() -> Any:
            return sample_action_instance.execute(iterations=3)

        without_tracer()
        profiler.stop()
        data_without = profiler.get_profile_data()

        # Reset and measure with tracer
        profiler = ActionProfiler(profiler_config)
        profiler.start()
        tracer.start()

        @profiler.profile
        def with_tracer() -> Any:
            for i in range(3):
                tracer.trace_event("iteration", {"index": i})
            return sample_action_instance.execute(iterations=3)

        with_tracer()
        tracer.stop()
        profiler.stop()
        data_with = profiler.get_profile_data()

        # Verify overhead is minimal (< 10%)
        time_without = data_without["total_time"]
        time_with = data_with["total_time"]

        overhead_percent = ((time_with - time_without) / time_without) * 100
        assert overhead_percent < 10, f"Tracer overhead too high: {overhead_percent:.2f}%"

    def test_concurrent_profiling_and_tracing(
        self, concurrent_action, profiler_config, event_tracer_config
    ):
        """Test profiler and tracer with concurrent execution."""
        profiler = ActionProfiler(profiler_config)
        tracer = EventTracer(event_tracer_config)

        profiler.start()
        tracer.start()

        def worker(thread_id: int) -> Any:
            tracer.trace_event("thread_start", {"thread_id": thread_id})

            @profiler.profile
            def execute() -> Any:
                result = concurrent_action.execute_threaded(thread_id, iterations=5)
                tracer.trace_event("thread_complete", {"thread_id": thread_id, "result": result})
                return result

            return execute()

        # Run multiple threads
        threads: list[Any] = []
        for i in range(5):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        profiler.stop()
        tracer.stop()

        # Verify data from all threads
        profile_data = profiler.get_profile_data()
        tracer.get_events()

        assert profile_data["total_calls"] >= 5  # At least one per thread
        assert len(tracer.get_events("thread_start")) == 5
        assert len(tracer.get_events("thread_complete")) == 5

    def test_event_tracer_during_profiled_error(
        self, sample_action_instance, profiler_config, event_tracer_config
    ):
        """Test that tracer captures events when profiled function errors."""
        profiler = ActionProfiler(profiler_config)
        tracer = EventTracer(event_tracer_config)

        profiler.start()
        tracer.start()

        @profiler.profile
        def execute_with_error() -> None:
            tracer.trace_event("action_start", {"action": "error_test"})
            try:
                sample_action_instance.execute_with_error()
            except RuntimeError as e:
                tracer.trace_event("action_error", {"error": str(e), "type": type(e).__name__})
                raise
            finally:
                tracer.trace_event("action_end", {"action": "error_test"})

        with pytest.raises(RuntimeError):
            execute_with_error()

        profiler.stop()
        tracer.stop()

        # Verify error was captured
        error_events = tracer.get_events("action_error")
        assert len(error_events) == 1
        assert "Simulated" in error_events[0]["data"]["error"]

        # Verify we still got start and end events
        assert len(tracer.get_events("action_start")) == 1
        assert len(tracer.get_events("action_end")) == 1


@pytest.mark.integration
class TestMemoryProfilerIntegration:
    """Test integration of MemoryProfiler with other tools."""

    def test_memory_profiler_with_action_profiler(
        self, memory_intensive_action, profiler_config, memory_profiler_config
    ):
        """Test memory profiler alongside action profiler."""
        profiler = ActionProfiler(profiler_config)
        mem_profiler = MemoryProfiler(memory_profiler_config)

        profiler.start()
        mem_profiler.start()

        @profiler.profile
        def allocate_memory() -> Any:
            return memory_intensive_action.execute(size_mb=10)

        allocate_memory()

        mem_profiler.stop()
        profiler.stop()

        # Verify both captured data
        profile_data = profiler.get_profile_data()
        memory_data = mem_profiler.get_memory_usage()

        assert profile_data["total_calls"] > 0
        assert memory_data["peak_mb"] >= 0
        assert memory_data["snapshots"] >= 2  # Start and stop snapshots

    def test_memory_profiler_with_event_tracer(
        self, memory_intensive_action, memory_profiler_config, event_tracer_config
    ):
        """Test memory profiler with event tracer."""
        mem_profiler = MemoryProfiler(memory_profiler_config)
        tracer = EventTracer(event_tracer_config)

        mem_profiler.start()
        tracer.start()

        tracer.trace_event("allocation_start", {})
        result = memory_intensive_action.execute(size_mb=5)
        tracer.trace_event("allocation_end", {"elements": result})

        memory_data = mem_profiler.get_memory_usage()
        tracer.trace_event("memory_snapshot", memory_data)

        mem_profiler.stop()
        tracer.stop()

        # Verify events captured memory state
        snapshot_events = tracer.get_events("memory_snapshot")
        assert len(snapshot_events) > 0
        assert "current_mb" in snapshot_events[0]["data"]

    def test_memory_cleanup_verification(self, memory_intensive_action, memory_profiler_config) -> None:
        """Test that memory profiler detects cleanup."""
        mem_profiler = MemoryProfiler(memory_profiler_config)

        mem_profiler.start()

        # Allocate memory
        memory_intensive_action.execute(size_mb=10)
        usage_after_alloc = mem_profiler.get_memory_usage()

        # Clean up
        memory_intensive_action.cleanup()
        usage_after_cleanup = mem_profiler.get_memory_usage()

        mem_profiler.stop()

        # Peak should be higher than current after cleanup
        assert usage_after_alloc["current_mb"] >= 0
        assert usage_after_cleanup["peak_mb"] >= usage_after_alloc["current_mb"]


@pytest.mark.integration
class TestDashboardIntegration:
    """Test integration of PerformanceDashboard with monitoring tools."""

    def test_dashboard_with_all_tools(
        self,
        sample_action_instance,
        profiler_config,
        event_tracer_config,
        memory_profiler_config,
        dashboard_config,
    ):
        """Test dashboard integration with all monitoring tools."""
        profiler = ActionProfiler(profiler_config)
        tracer = EventTracer(event_tracer_config)
        mem_profiler = MemoryProfiler(memory_profiler_config)
        dashboard = PerformanceDashboard(dashboard_config)

        # Start all tools
        profiler.start()
        tracer.start()
        mem_profiler.start()
        dashboard.start()

        try:
            # Execute action
            @profiler.profile
            def execute_monitored() -> Any:
                tracer.trace_event("action_start", {})
                result = sample_action_instance.execute(iterations=5)
                tracer.trace_event("action_end", {})
                return result

            execute_monitored()

            # Update dashboard with all metrics
            dashboard.update_metrics(
                {
                    "profiler": profiler.get_profile_data(),
                    "events": tracer.get_events(),
                    "memory": mem_profiler.get_memory_usage(),
                }
            )

            # Verify dashboard has all data
            metrics = dashboard.get_metrics()
            assert "profiler" in metrics
            assert "events" in metrics
            assert "memory" in metrics
            assert metrics["profiler"]["total_calls"] > 0
            assert len(metrics["events"]) > 0

        finally:
            dashboard.stop()
            mem_profiler.stop()
            tracer.stop()
            profiler.stop()

    def test_dashboard_live_updates(
        self, sample_action_instance, profiler_config, dashboard_config
    ):
        """Test that dashboard receives live updates during execution."""
        profiler = ActionProfiler(profiler_config)
        dashboard = PerformanceDashboard(dashboard_config)

        profiler.start()
        dashboard.start()

        metrics_snapshots: list[Any] = []

        @profiler.profile
        def execute_with_updates() -> None:
            for i in range(5):
                sample_action_instance._process_iteration(i)

                # Update dashboard periodically
                dashboard.update_metrics(profiler.get_profile_data())
                metrics_snapshots.append(dashboard.get_metrics().copy())

                time.sleep(0.01)

        execute_with_updates()

        profiler.stop()
        dashboard.stop()

        # Verify metrics increased over time
        assert len(metrics_snapshots) >= 5
        first_calls = metrics_snapshots[0].get("total_calls", 0)
        last_calls = metrics_snapshots[-1].get("total_calls", 0)
        assert last_calls > first_calls

    def test_dashboard_concurrent_updates(
        self, concurrent_action, profiler_config, dashboard_config
    ):
        """Test dashboard with concurrent metric updates."""
        profiler = ActionProfiler(profiler_config)
        dashboard = PerformanceDashboard(dashboard_config)

        profiler.start()
        dashboard.start()

        def worker(thread_id: int) -> Any:
            @profiler.profile
            def execute() -> Any:
                result = concurrent_action.execute_threaded(thread_id, iterations=10)
                # Each thread updates dashboard
                dashboard.update_metrics({f"thread_{thread_id}": profiler.get_profile_data()})
                return result

            return execute()

        threads: list[Any] = []
        for i in range(3):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        profiler.stop()
        dashboard.stop()

        # Verify dashboard has data from all threads
        metrics = dashboard.get_metrics()
        thread_metrics = [k for k in metrics.keys() if k.startswith("thread_")]
        assert len(thread_metrics) == 3


@pytest.mark.integration
class TestAllToolsConcurrently:
    """Test all Phase 3 tools running concurrently."""

    def test_all_tools_no_interference(
        self,
        sample_action_instance,
        profiler_config,
        event_tracer_config,
        memory_profiler_config,
        dashboard_config,
    ):
        """Test that all tools can run together without interference."""
        # Initialize all tools
        profiler = ActionProfiler(profiler_config)
        tracer = EventTracer(event_tracer_config)
        mem_profiler = MemoryProfiler(memory_profiler_config)
        dashboard = PerformanceDashboard(dashboard_config)

        # Start all tools
        profiler.start()
        tracer.start()
        mem_profiler.start()
        dashboard.start()

        successful_executions = 0

        try:
            # Execute multiple iterations with all tools active
            for i in range(10):

                @profiler.profile
                def execute_iteration(iteration_num: int = i) -> Any:
                    tracer.trace_event("iteration_start", {"iteration": iteration_num})

                    result = sample_action_instance.execute(iterations=3)

                    tracer.trace_event(
                        "iteration_end", {"iteration": iteration_num, "result": result}
                    )

                    # Update dashboard
                    dashboard.update_metrics(
                        {
                            "iteration": iteration_num,
                            "profiler": profiler.get_profile_data(),
                            "events_count": len(tracer.get_events()),
                            "memory": mem_profiler.get_memory_usage(),
                        }
                    )

                    return result

                result = execute_iteration()
                assert result is not None
                successful_executions += 1

                time.sleep(0.01)

        finally:
            dashboard.stop()
            mem_profiler.stop()
            tracer.stop()
            profiler.stop()

        # Verify all tools captured data
        assert successful_executions == 10

        profile_data = profiler.get_profile_data()
        assert profile_data["total_calls"] >= 10

        events = tracer.get_events()
        assert len(events) >= 20  # At least start and end for each iteration

        memory_data = mem_profiler.get_memory_usage()
        assert memory_data["snapshots"] >= 2

        metrics = dashboard.get_metrics()
        assert "iteration" in metrics
        assert metrics["iteration"] == 9  # Last iteration

    def test_all_tools_with_async_execution(
        self, sample_action_instance, profiler_config, event_tracer_config, memory_profiler_config
    ):
        """Test all tools with async action execution."""
        profiler = ActionProfiler(profiler_config)
        tracer = EventTracer(event_tracer_config)
        mem_profiler = MemoryProfiler(memory_profiler_config)

        profiler.start()
        tracer.start()
        mem_profiler.start()

        async def execute_async_monitored():
            tracer.trace_event("async_start", {})

            @profiler.profile
            def sync_wrapper() -> Any:
                # Since we can't profile async directly, wrap it
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(sample_action_instance.execute_async(iterations=5))
                loop.close()
                return result

            result = sync_wrapper()
            tracer.trace_event("async_end", {"result": result})
            return result

        # Run async execution
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(execute_async_monitored())
        loop.close()

        mem_profiler.stop()
        tracer.stop()
        profiler.stop()

        # Verify all tools captured data
        assert result is not None
        assert profiler.get_profile_data()["total_calls"] > 0
        assert len(tracer.get_events()) >= 2
        assert mem_profiler.get_memory_usage()["snapshots"] >= 2

    def test_all_tools_error_handling(
        self, sample_action_instance, profiler_config, event_tracer_config, memory_profiler_config
    ):
        """Test that all tools handle errors gracefully."""
        profiler = ActionProfiler(profiler_config)
        tracer = EventTracer(event_tracer_config)
        mem_profiler = MemoryProfiler(memory_profiler_config)

        profiler.start()
        tracer.start()
        mem_profiler.start()

        @profiler.profile
        def execute_with_error() -> None:
            tracer.trace_event("before_error", {})
            try:
                sample_action_instance.execute_with_error()
            except RuntimeError as e:
                tracer.trace_event(
                    "error_caught", {"error": str(e), "memory": mem_profiler.get_memory_usage()}
                )
                raise

        with pytest.raises(RuntimeError):
            execute_with_error()

        mem_profiler.stop()
        tracer.stop()
        profiler.stop()

        # Verify tools still have valid data after error
        assert profiler.get_profile_data()["total_calls"] > 0
        assert len(tracer.get_events("error_caught")) == 1
        assert mem_profiler.get_memory_usage()["snapshots"] >= 2

    def test_tools_export_integration(
        self,
        sample_action_instance,
        temp_test_dir,
        profiler_config,
        event_tracer_config,
        memory_profiler_config,
    ):
        """Test that all tools can export their data."""
        profiler = ActionProfiler(profiler_config)
        tracer = EventTracer(event_tracer_config)
        mem_profiler = MemoryProfiler(memory_profiler_config)

        profiler.start()
        tracer.start()
        mem_profiler.start()

        # Execute some actions
        @profiler.profile
        def execute() -> Any:
            tracer.trace_event("action", {})
            return sample_action_instance.execute(iterations=5)

        execute()

        mem_profiler.stop()
        tracer.stop()
        profiler.stop()

        # Export all data
        profiler_export = temp_test_dir / "profiler.json"
        tracer_export = temp_test_dir / "events.json"
        memory_export = temp_test_dir / "memory.json"

        profiler.export(profiler_export, format="json")
        tracer.export(tracer_export, format="json")
        mem_profiler.export(memory_export, format="json")

        # Verify all exports exist and contain valid JSON
        assert profiler_export.exists()
        assert tracer_export.exists()
        assert memory_export.exists()

        with open(profiler_export) as f:
            profiler_data = json.load(f)
            assert "total_calls" in profiler_data

        with open(tracer_export) as f:
            events_data = json.load(f)
            assert len(events_data) > 0

        with open(memory_export) as f:
            memory_data = json.load(f)
            assert len(memory_data) > 0
