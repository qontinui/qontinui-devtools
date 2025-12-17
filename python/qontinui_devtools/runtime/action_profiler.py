"""Action profiler for analyzing performance of qontinui automation actions.

This module provides comprehensive performance profiling capabilities for
analyzing action execution, including timing, CPU usage, memory tracking,
and flame graph generation.
"""

import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

import psutil


@dataclass
class ActionProfile:
    """Profile data for a single action execution."""

    action_type: str
    action_id: str
    start_time: float
    end_time: float
    duration: float
    cpu_time: float
    memory_before: int  # bytes
    memory_after: int
    memory_delta: int
    peak_memory: int
    phases: dict[str, float] = field(default_factory=dict)  # Phase name → duration
    stack_samples: list[tuple[float, list[str]]] = field(default_factory=list)  # For flame graph
    success: bool = True
    error: str | None = None

    def __post_init__(self) -> None:
        """Validate profile data."""
        if self.duration < 0:
            raise ValueError("Duration cannot be negative")
        if self.cpu_time < 0:
            raise ValueError("CPU time cannot be negative")


@dataclass
class ProfilingSession:
    """A complete profiling session."""

    session_id: str
    start_time: float
    end_time: float
    profiles: list[ActionProfile]
    summary: dict[str, Any] = field(default_factory=dict)

    def get_total_duration(self) -> float:
        """Get total session duration."""
        return self.end_time - self.start_time

    def get_action_count(self) -> int:
        """Get number of actions profiled."""
        return len(self.profiles)


class ActionProfiler:
    """Profile action execution performance.

    This profiler measures:
    - High-resolution timing (microsecond precision)
    - CPU time and utilization
    - Memory usage (before/after/delta/peak)
    - Optional stack sampling for flame graphs

    Example:
        profiler = ActionProfiler()
        profiler.start_session()

        with profiler.profile_action("click", "btn_submit") as profile:
            # Execute action
            do_something()
            # Track phase
            profile.phases["find"] = 0.01

        session = profiler.end_session()
    """

    def __init__(
        self,
        sample_interval: float = 0.001,  # 1ms
        enable_memory: bool = True,
        enable_cpu: bool = True,
        enable_stack_sampling: bool = False,
    ) -> None:
        """Initialize the profiler.

        Args:
            sample_interval: Interval for stack sampling in seconds (if enabled)
            enable_memory: Track memory usage
            enable_cpu: Track CPU time
            enable_stack_sampling: Sample call stacks for flame graphs (expensive)
        """
        self.sample_interval = sample_interval
        self.enable_memory = enable_memory
        self.enable_cpu = enable_cpu
        self.enable_stack_sampling = enable_stack_sampling

        self._session_id: str | None = None
        self._session_start: float | None = None
        self._profiles: list[ActionProfile] = []
        self._process = psutil.Process()

    def start_session(self) -> str:
        """Start a new profiling session.

        Returns:
            Session ID
        """
        if self._session_id is not None:
            raise RuntimeError("Session already started. End current session first.")

        self._session_id = str(uuid.uuid4())
        self._session_start = time.perf_counter()
        self._profiles: list[Any] = []
        return self._session_id

    @contextmanager
    def profile_action(
        self, action_type: str, action_id: str | None = None
    ) -> Iterator[ActionProfile]:
        """Profile a single action execution.

        Usage:
            with profiler.profile_action("click", "btn_submit") as profile:
                # Execute action
                element.click()
                # Optionally add phase timing
                profile.phases["find"] = 0.01
                profile.phases["move"] = 0.02

        Args:
            action_type: Type of action (e.g., "click", "type", "scroll")
            action_id: Optional identifier for the specific action

        Yields:
            ActionProfile that can be updated during execution
        """
        if self._session_id is None:
            raise RuntimeError("No active session. Call start_session() first.")

        # Generate ID if not provided
        if action_id is None:
            action_id = f"{action_type}_{len(self._profiles)}"

        # Initial measurements
        start_time = time.perf_counter()
        start_cpu = time.process_time() if self.enable_cpu else 0.0

        memory_before = 0
        memory_after = 0
        peak_memory = 0

        if self.enable_memory:
            mem_info = self._process.memory_info()
            memory_before = mem_info.rss
            peak_memory = memory_before

        # Create profile object
        profile = ActionProfile(
            action_type=action_type,
            action_id=action_id,
            start_time=start_time,
            end_time=0.0,  # Will be set later
            duration=0.0,  # Will be calculated
            cpu_time=0.0,  # Will be calculated
            memory_before=memory_before,
            memory_after=0,  # Will be set later
            memory_delta=0,  # Will be calculated
            peak_memory=peak_memory,
            phases={},
            stack_samples = []
        )

        # Stack sampling setup (if enabled)
        if self.enable_stack_sampling:
            pass
            # Note: Actual stack sampling would require threading or signal-based approach
            # For now, we'll just mark it as available
            # A production implementation would use a background thread or py-spy

        try:
            # Track peak memory during execution
            if self.enable_memory:
                # Sample once at start
                peak_memory = memory_before

            # Yield profile for user code
            yield profile

            # Track final memory
            if self.enable_memory:
                mem_info = self._process.memory_info()
                memory_after = mem_info.rss
                profile.memory_after = memory_after
                profile.memory_delta = memory_after - memory_before
                profile.peak_memory = max(peak_memory, memory_after)

            profile.success = True

        except Exception as e:
            profile.success = False
            profile.error = str(e)
            raise

        finally:
            # Final measurements
            end_time = time.perf_counter()
            end_cpu = time.process_time() if self.enable_cpu else 0.0

            profile.end_time = end_time
            profile.duration = end_time - start_time
            profile.cpu_time = end_cpu - start_cpu if self.enable_cpu else 0.0

            # Store profile
            self._profiles.append(profile)

    def end_session(self) -> ProfilingSession:
        """End the current session and get results.

        Returns:
            ProfilingSession with all collected profiles and summary
        """
        if self._session_id is None:
            raise RuntimeError("No active session to end.")

        if self._session_start is None:
            raise RuntimeError("Session start time not recorded.")

        session_end = time.perf_counter()

        # Calculate summary statistics
        summary = self.get_summary()

        session = ProfilingSession(
            session_id=self._session_id,
            start_time=self._session_start,
            end_time=session_end,
            profiles=self._profiles.copy(),
            summary=summary,
        )

        # Reset state
        self._session_id = None
        self._session_start = None
        self._profiles: list[Any] = []

        return session

    def get_summary(self) -> dict[str, Any]:
        """Get summary statistics for current session.

        Returns:
            Dictionary with summary metrics
        """
        if not self._profiles:
            return {
                "total_actions": 0,
                "total_duration": 0.0,
                "total_cpu_time": 0.0,
                "total_memory_delta": 0,
                "successful_actions": 0,
                "failed_actions": 0,
            }

        total_duration = sum(p.duration for p in self._profiles)
        total_cpu_time = sum(p.cpu_time for p in self._profiles)
        total_memory_delta = sum(p.memory_delta for p in self._profiles)
        successful = sum(1 for p in self._profiles if p.success)
        failed = sum(1 for p in self._profiles if not p.success)

        durations = [p.duration for p in self._profiles]
        avg_duration = total_duration / len(self._profiles)
        min_duration = min(durations)
        max_duration = max(durations)

        return {
            "total_actions": len(self._profiles),
            "total_duration": total_duration,
            "total_cpu_time": total_cpu_time,
            "total_memory_delta": total_memory_delta,
            "avg_duration": avg_duration,
            "min_duration": min_duration,
            "max_duration": max_duration,
            "successful_actions": successful,
            "failed_actions": failed,
        }

    def generate_flame_graph(self, output_path: str, format: str = "svg") -> None:
        """Generate flame graph visualization.

        Args:
            output_path: Path to save the flame graph
            format: Output format ("svg" or "json" for speedscope)

        Raises:
            ValueError: If no stack samples available
            ImportError: If flame graph generation dependencies not available
        """
        # Collect all stack samples from profiles
        all_samples: list[tuple[float, list[str]]] = []
        for profile in self._profiles:
            all_samples.extend(profile.stack_samples)

        if not all_samples:
            raise ValueError(
                "No stack samples available. Enable stack sampling when creating profiler."
            )

        # Import flame graph generator
        from .flame_graph import generate_flame_graph

        generate_flame_graph(all_samples, output_path, format=format)

    def export_to_json(self, output_path: str) -> None:
        """Export current profiles to JSON.

        Args:
            output_path: Path to save JSON file
        """
        import json

        data = {
            "session_id": self._session_id,
            "session_start": self._session_start,
            "profiles": [
                {
                    "action_type": p.action_type,
                    "action_id": p.action_id,
                    "start_time": p.start_time,
                    "end_time": p.end_time,
                    "duration": p.duration,
                    "cpu_time": p.cpu_time,
                    "memory_before": p.memory_before,
                    "memory_after": p.memory_after,
                    "memory_delta": p.memory_delta,
                    "peak_memory": p.peak_memory,
                    "phases": p.phases,
                    "success": p.success,
                    "error": p.error,
                }
                for p in self._profiles
            ],
            "summary": self.get_summary(),
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
