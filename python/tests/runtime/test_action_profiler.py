"""Tests for action profiler."""

import json
import time
from pathlib import Path

import pytest
from qontinui_devtools.runtime import (ActionProfile, ActionProfiler,
                                       ProfilingSession,
                                       calculate_action_type_metrics,
                                       calculate_metrics, calculate_percentile,
                                       calculate_phase_metrics,
                                       format_duration, format_memory)


class TestActionProfile:
    """Tests for ActionProfile dataclass."""

    def test_action_profile_creation(self) -> None:
        """Test creating an ActionProfile."""
        profile = ActionProfile(
            action_type="click",
            action_id="btn_submit",
            start_time=1.0,
            end_time=2.0,
            duration=1.0,
            cpu_time=0.5,
            memory_before=1000,
            memory_after=1500,
            memory_delta=500,
            peak_memory=1600,
        )

        assert profile.action_type == "click"
        assert profile.action_id == "btn_submit"
        assert profile.duration == 1.0
        assert profile.success is True
        assert profile.error is None

    def test_action_profile_with_phases(self) -> None:
        """Test ActionProfile with phase timing."""
        profile = ActionProfile(
            action_type="click",
            action_id="btn_test",
            start_time=1.0,
            end_time=2.0,
            duration=1.0,
            cpu_time=0.5,
            memory_before=1000,
            memory_after=1500,
            memory_delta=500,
            peak_memory=1600,
            phases={"find": 0.3, "move": 0.4, "click": 0.3},
        )

        assert len(profile.phases) == 3
        assert profile.phases["find"] == 0.3
        assert sum(profile.phases.values()) == pytest.approx(1.0)

    def test_action_profile_negative_duration_raises(self) -> None:
        """Test that negative duration raises ValueError."""
        with pytest.raises(ValueError, match="Duration cannot be negative"):
            ActionProfile(
                action_type="click",
                action_id="test",
                start_time=2.0,
                end_time=1.0,
                duration=-1.0,  # Invalid
                cpu_time=0.0,
                memory_before=1000,
                memory_after=1000,
                memory_delta=0,
                peak_memory=1000,
            )


class TestProfilingSession:
    """Tests for ProfilingSession."""

    def test_session_creation(self) -> None:
        """Test creating a ProfilingSession."""
        profiles = [
            ActionProfile(
                action_type="click",
                action_id="btn1",
                start_time=1.0,
                end_time=2.0,
                duration=1.0,
                cpu_time=0.5,
                memory_before=1000,
                memory_after=1500,
                memory_delta=500,
                peak_memory=1600,
            )
        ]

        session = ProfilingSession(
            session_id="test-session",
            start_time=1.0,
            end_time=3.0,
            profiles=profiles,
        )

        assert session.session_id == "test-session"
        assert session.get_total_duration() == 2.0
        assert session.get_action_count() == 1


class TestActionProfiler:
    """Tests for ActionProfiler."""

    def test_profiler_initialization(self) -> None:
        """Test profiler initialization."""
        profiler = ActionProfiler(sample_interval=0.001, enable_memory=True, enable_cpu=True)

        assert profiler.sample_interval == 0.001
        assert profiler.enable_memory is True
        assert profiler.enable_cpu is True

    def test_start_session(self) -> None:
        """Test starting a profiling session."""
        profiler = ActionProfiler()
        session_id = profiler.start_session()

        assert session_id is not None
        assert isinstance(session_id, str)

    def test_start_session_twice_raises(self) -> None:
        """Test that starting a session twice raises error."""
        profiler = ActionProfiler()
        profiler.start_session()

        with pytest.raises(RuntimeError, match="Session already started"):
            profiler.start_session()

    def test_profile_action_without_session_raises(self) -> None:
        """Test profiling without starting session raises error."""
        profiler = ActionProfiler()

        with pytest.raises(RuntimeError, match="No active session"):
            with profiler.profile_action("click", "test"):
                pass

    def test_profile_action_basic(self) -> None:
        """Test basic action profiling."""
        profiler = ActionProfiler(enable_stack_sampling=False)
        profiler.start_session()

        with profiler.profile_action("click", "btn_test") as profile:
            # Simulate action
            time.sleep(0.05)  # 50ms

        assert profile.action_type == "click"
        assert profile.action_id == "btn_test"
        assert profile.duration >= 0.05  # At least 50ms
        assert profile.cpu_time >= 0  # Should have some CPU time
        assert profile.success is True
        assert profile.error is None

        session = profiler.end_session()
        assert len(session.profiles) == 1

    def test_profile_action_with_memory_tracking(self) -> None:
        """Test action profiling with memory tracking."""
        profiler = ActionProfiler(enable_memory=True)
        profiler.start_session()

        with profiler.profile_action("click", "btn_test") as profile:
            # Allocate some memory
            time.sleep(0.01)

        # Memory tracking should show some change
        assert profile.memory_before > 0
        assert profile.memory_after > 0
        assert profile.peak_memory >= profile.memory_before

        profiler.end_session()

    def test_profile_action_with_phases(self) -> None:
        """Test action profiling with phase tracking."""
        profiler = ActionProfiler()
        profiler.start_session()

        with profiler.profile_action("click", "btn_test") as profile:
            time.sleep(0.01)
            profile.phases["find"] = 0.003

            time.sleep(0.01)
            profile.phases["move"] = 0.005

            time.sleep(0.01)
            profile.phases["click"] = 0.002

        assert len(profile.phases) == 3
        assert "find" in profile.phases
        assert "move" in profile.phases
        assert "click" in profile.phases

        profiler.end_session()

    def test_profile_action_with_error(self) -> None:
        """Test action profiling when error occurs."""
        profiler = ActionProfiler()
        profiler.start_session()

        with pytest.raises(ValueError):
            with profiler.profile_action("click", "btn_test"):
                raise ValueError("Test error")

        # Profile should still be recorded
        session = profiler.end_session()
        assert len(session.profiles) == 1
        assert session.profiles[0].success is False
        assert session.profiles[0].error == "Test error"

    def test_profile_multiple_actions(self) -> None:
        """Test profiling multiple actions."""
        profiler = ActionProfiler()
        profiler.start_session()

        # Profile 5 actions
        for i in range(5):
            with profiler.profile_action("click", f"btn_{i}") as profile:
                time.sleep(0.01)
                profile.phases["execute"] = 0.01

        session = profiler.end_session()
        assert len(session.profiles) == 5

        # Check all profiles
        for i, profile in enumerate(session.profiles):
            assert profile.action_id == f"btn_{i}"
            assert profile.duration >= 0.01

    def test_profile_action_generates_id_if_not_provided(self) -> None:
        """Test that action ID is auto-generated if not provided."""
        profiler = ActionProfiler()
        profiler.start_session()

        with profiler.profile_action("click") as profile:
            time.sleep(0.01)

        assert profile.action_id.startswith("click_")

        profiler.end_session()

    def test_get_summary(self) -> None:
        """Test getting summary statistics."""
        profiler = ActionProfiler()
        profiler.start_session()

        # Profile some actions
        for i in range(3):
            with profiler.profile_action("click", f"btn_{i}"):
                time.sleep(0.01 * (i + 1))  # Variable duration

        summary = profiler.get_summary()

        assert summary["total_actions"] == 3
        assert summary["total_duration"] > 0
        assert summary["avg_duration"] > 0
        assert summary["min_duration"] > 0
        assert summary["max_duration"] > summary["min_duration"]
        assert summary["successful_actions"] == 3
        assert summary["failed_actions"] == 0

        profiler.end_session()

    def test_end_session_without_start_raises(self) -> None:
        """Test ending session without starting raises error."""
        profiler = ActionProfiler()

        with pytest.raises(RuntimeError, match="No active session"):
            profiler.end_session()

    def test_export_to_json(self, tmp_path: Path) -> None:
        """Test exporting profiles to JSON."""
        profiler = ActionProfiler()
        profiler.start_session()

        with profiler.profile_action("click", "btn_test"):
            time.sleep(0.01)

        # Export to JSON
        output_file = tmp_path / "profile.json"
        profiler.export_to_json(str(output_file))

        # Verify file was created and contains valid JSON
        assert output_file.exists()

        with open(output_file) as f:
            data = json.load(f)

        assert "session_id" in data
        assert "profiles" in data
        assert len(data["profiles"]) == 1
        assert data["profiles"][0]["action_type"] == "click"

        profiler.end_session()

    def test_cpu_time_measurement(self) -> None:
        """Test CPU time measurement."""
        profiler = ActionProfiler(enable_cpu=True)
        profiler.start_session()

        with profiler.profile_action("compute", "test") as profile:
            # Do some CPU work
            sum(i**2 for i in range(100000))

        # CPU time should be measured
        assert profile.cpu_time > 0
        # CPU time should be close to wall time (allow small variance due to timing precision)
        # In multi-tasking environments, CPU time can slightly exceed wall time due to
        # measurement granularity differences between perf_counter and process_time
        assert profile.cpu_time <= profile.duration * 1.01  # Allow 1% variance

        profiler.end_session()

    def test_disabled_cpu_tracking(self) -> None:
        """Test that CPU tracking can be disabled."""
        profiler = ActionProfiler(enable_cpu=False)
        profiler.start_session()

        with profiler.profile_action("click", "test") as profile:
            time.sleep(0.01)

        assert profile.cpu_time == 0.0

        profiler.end_session()

    def test_disabled_memory_tracking(self) -> None:
        """Test that memory tracking can be disabled."""
        profiler = ActionProfiler(enable_memory=False)
        profiler.start_session()

        with profiler.profile_action("click", "test") as profile:
            pass

        assert profile.memory_before == 0
        assert profile.memory_after == 0
        assert profile.memory_delta == 0

        profiler.end_session()


class TestMetrics:
    """Tests for metrics calculations."""

    def test_calculate_percentile(self) -> None:
        """Test percentile calculation."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]

        assert calculate_percentile(values, 0) == 1.0
        assert calculate_percentile(values, 50) == 5.5
        assert calculate_percentile(values, 100) == 10.0
        assert calculate_percentile(values, 95) == pytest.approx(9.55)

    def test_calculate_percentile_single_value(self) -> None:
        """Test percentile with single value."""
        values = [5.0]

        assert calculate_percentile(values, 0) == 5.0
        assert calculate_percentile(values, 50) == 5.0
        assert calculate_percentile(values, 100) == 5.0

    def test_calculate_percentile_empty_raises(self) -> None:
        """Test that empty list raises error."""
        with pytest.raises(ValueError, match="Cannot calculate percentile of empty list"):
            calculate_percentile([], 50)

    def test_calculate_percentile_invalid_range_raises(self) -> None:
        """Test that invalid percentile raises error."""
        values = [1.0, 2.0, 3.0]

        with pytest.raises(ValueError, match="Percentile must be between 0 and 100"):
            calculate_percentile(values, -1)

        with pytest.raises(ValueError, match="Percentile must be between 0 and 100"):
            calculate_percentile(values, 101)

    def test_calculate_metrics(self) -> None:
        """Test calculating aggregate metrics."""
        profiles = [
            ActionProfile(
                action_type="click",
                action_id=f"btn_{i}",
                start_time=float(i),
                end_time=float(i + 1),
                duration=1.0 + i * 0.1,
                cpu_time=0.5,
                memory_before=1000,
                memory_after=1500,
                memory_delta=500,
                peak_memory=1600,
            )
            for i in range(10)
        ]

        metrics = calculate_metrics(profiles)

        assert metrics.total_actions == 10
        assert metrics.total_duration > 0
        assert metrics.avg_duration > 0
        assert metrics.min_duration == 1.0
        assert metrics.max_duration == 1.9
        assert metrics.p50_duration > metrics.min_duration
        assert metrics.p95_duration > metrics.p50_duration
        assert metrics.p99_duration > metrics.p95_duration
        assert metrics.failed_actions == 0
        assert metrics.success_rate == 1.0

    def test_calculate_metrics_empty_raises(self) -> None:
        """Test that empty profiles list raises error."""
        with pytest.raises(ValueError, match="Cannot calculate metrics from empty"):
            calculate_metrics([])

    def test_calculate_metrics_with_failures(self) -> None:
        """Test metrics calculation with failed actions."""
        profiles = [
            ActionProfile(
                action_type="click",
                action_id=f"btn_{i}",
                start_time=float(i),
                end_time=float(i + 1),
                duration=1.0,
                cpu_time=0.5,
                memory_before=1000,
                memory_after=1500,
                memory_delta=500,
                peak_memory=1600,
                success=(i % 2 == 0),  # Half succeed, half fail
            )
            for i in range(10)
        ]

        metrics = calculate_metrics(profiles)

        assert metrics.total_actions == 10
        assert metrics.failed_actions == 5
        assert metrics.success_rate == 0.5

    def test_calculate_phase_metrics(self) -> None:
        """Test calculating phase-level metrics."""
        profiles = [
            ActionProfile(
                action_type="click",
                action_id=f"btn_{i}",
                start_time=float(i),
                end_time=float(i + 1),
                duration=1.0,
                cpu_time=0.5,
                memory_before=1000,
                memory_after=1500,
                memory_delta=500,
                peak_memory=1600,
                phases={"find": 0.3, "move": 0.4, "click": 0.3},
            )
            for i in range(5)
        ]

        phase_metrics = calculate_phase_metrics(profiles)

        assert "find" in phase_metrics
        assert "move" in phase_metrics
        assert "click" in phase_metrics

        assert phase_metrics["find"]["count"] == 5
        assert phase_metrics["find"]["avg"] == pytest.approx(0.3)
        assert phase_metrics["move"]["total"] == pytest.approx(2.0)

    def test_calculate_action_type_metrics(self) -> None:
        """Test calculating metrics by action type."""
        profiles = [
            ActionProfile(
                action_type="click" if i < 5 else "type",
                action_id=f"action_{i}",
                start_time=float(i),
                end_time=float(i + 1),
                duration=1.0,
                cpu_time=0.5,
                memory_before=1000,
                memory_after=1500,
                memory_delta=500,
                peak_memory=1600,
            )
            for i in range(10)
        ]

        type_metrics = calculate_action_type_metrics(profiles)

        assert "click" in type_metrics
        assert "type" in type_metrics

        assert type_metrics["click"].total_actions == 5
        assert type_metrics["type"].total_actions == 5

    def test_format_duration(self) -> None:
        """Test duration formatting."""
        assert format_duration(1.5) == "1.500s"
        assert format_duration(0.123) == "123.0ms"
        assert format_duration(0.000123) == "123.0μs"
        assert format_duration(0.000000123) == "123ns"

    def test_format_memory(self) -> None:
        """Test memory formatting."""
        assert format_memory(1024**3 + 512 * 1024**2) == "1.50 GB"
        assert format_memory(512 * 1024**2) == "512.00 MB"
        assert format_memory(512 * 1024) == "512.00 KB"
        assert format_memory(512) == "512 B"


class TestPerformanceOverhead:
    """Tests to measure profiler overhead."""

    def test_profiler_overhead(self) -> None:
        """Test that profiler overhead is minimal."""
        # Baseline: measure time without profiler
        start = time.perf_counter()
        for _ in range(100):
            time.sleep(0.001)  # 1ms per iteration
        baseline_duration = time.perf_counter() - start

        # With profiler
        profiler = ActionProfiler()
        profiler.start_session()

        start = time.perf_counter()
        for i in range(100):
            with profiler.profile_action("test", f"action_{i}"):
                time.sleep(0.001)
        profiled_duration = time.perf_counter() - start

        profiler.end_session()

        # Calculate overhead percentage
        overhead = ((profiled_duration - baseline_duration) / baseline_duration) * 100

        # Overhead should be less than 15% (accounts for context manager overhead,
        # memory tracking, and CPU time measurement in various environments)
        assert overhead < 15, f"Overhead was {overhead:.1f}%, expected < 15%"
