"""Real-time metrics collection for performance monitoring.

This module provides classes for collecting system, action, and event metrics
in real-time with minimal overhead (<1%).
"""

import queue
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any

import psutil


@dataclass
class SystemMetrics:
    """Current system metrics snapshot."""

    timestamp: float
    cpu_percent: float
    memory_mb: int
    memory_percent: float
    thread_count: int
    process_count: int


@dataclass
class ActionMetrics:
    """Action execution metrics."""

    timestamp: float
    total_actions: int
    actions_per_minute: float
    avg_duration: float
    current_action: str | None
    queue_depth: int
    success_rate: float
    error_count: int


@dataclass
class EventMetrics:
    """Event processing metrics."""

    timestamp: float
    events_queued: int
    events_processed: int
    events_failed: int
    avg_processing_time: float
    queue_depth: int


@dataclass
class ActionRecord:
    """Record of a single action execution."""

    timestamp: float
    name: str
    duration: float
    success: bool


class MetricsCollector:
    """Collect real-time system and application metrics.

    This collector runs in a background thread and samples metrics at regular
    intervals. It maintains a rolling window of recent data for calculating
    rates and averages.

    Example:
        >>> collector = MetricsCollector(sample_interval=1.0)
        >>> collector.start()
        >>> # ... application runs ...
        >>> metrics = collector.get_latest_metrics()
        >>> collector.stop()

    Args:
        sample_interval: Time between metric samples in seconds (default: 1.0)
        history_size: Number of historical samples to keep (default: 300)
    """

    def __init__(
        self, sample_interval: float = 1.0, history_size: int = 300
    ) -> None:
        """Initialize the metrics collector.

        Args:
            sample_interval: Time between samples in seconds
            history_size: Number of historical samples to retain
        """
        self._interval = sample_interval
        self._history_size = history_size
        self._running = False
        self._thread: threading.Thread | None = None
        self._metrics_queue: queue.Queue[dict[str, Any]] = queue.Queue(maxsize=1000)

        # Process handle for system metrics
        self._process = psutil.Process()

        # Action tracking
        self._action_history: deque[ActionRecord] = deque(maxlen=history_size)
        self._current_action: str | None = None
        self._action_queue_depth = 0
        self._action_lock = threading.Lock()

        # Event tracking
        self._events_queued = 0
        self._events_processed = 0
        self._events_failed = 0
        self._event_durations: deque[float] = deque(maxlen=history_size)
        self._event_queue_depth = 0
        self._event_lock = threading.Lock()

        # System metrics cache
        self._last_cpu_percent = 0.0

    def start(self) -> None:
        """Start collecting metrics in a background thread."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._collection_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop collecting metrics and wait for thread to finish."""
        if not self._running:
            return

        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None

    def _collection_loop(self) -> None:
        """Main collection loop running in background thread."""
        while self._running:
            try:
                metrics = self.get_latest_metrics()

                # Add to queue for consumers
                try:
                    self._metrics_queue.put_nowait(metrics)
                except queue.Full:
                    # Drop oldest metric if queue is full
                    try:
                        self._metrics_queue.get_nowait()
                        self._metrics_queue.put_nowait(metrics)
                    except queue.Empty:
                        pass

                time.sleep(self._interval)
            except Exception:
                # Continue even if collection fails
                pass

    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system resource metrics.

        Returns:
            SystemMetrics with current CPU, memory, thread, and process counts
        """
        # Get CPU percent (non-blocking)
        try:
            cpu_percent = self._process.cpu_percent()
            if cpu_percent > 0:
                self._last_cpu_percent = cpu_percent
        except Exception:
            cpu_percent = self._last_cpu_percent

        # Get memory info
        try:
            mem_info = self._process.memory_info()
            memory_mb = mem_info.rss // (1024 * 1024)
            memory_percent = self._process.memory_percent()
        except Exception:
            memory_mb = 0
            memory_percent = 0.0

        # Get thread count
        try:
            thread_count = self._process.num_threads()
        except Exception:
            thread_count = 0

        # Get process count (children)
        try:
            process_count = len(self._process.children(recursive=True)) + 1
        except Exception:
            process_count = 1

        return SystemMetrics(
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            memory_mb=memory_mb,
            memory_percent=memory_percent,
            thread_count=thread_count,
            process_count=process_count,
        )

    def collect_action_metrics(self) -> ActionMetrics:
        """Collect action execution metrics.

        Returns:
            ActionMetrics with current action statistics
        """
        with self._action_lock:
            now = time.time()
            window_start = now - 60.0  # 1 minute window

            # Filter recent actions
            recent_actions = [
                action
                for action in self._action_history
                if action.timestamp >= window_start
            ]

            # Calculate metrics
            total_actions = len(self._action_history)
            actions_per_minute = float(len(recent_actions))

            # Calculate average duration
            if recent_actions:
                avg_duration = sum(a.duration for a in recent_actions) / len(
                    recent_actions
                )
            else:
                avg_duration = 0.0

            # Calculate success rate
            if recent_actions:
                successes = sum(1 for a in recent_actions if a.success)
                success_rate = (successes / len(recent_actions)) * 100.0
            else:
                success_rate = 100.0

            # Count errors
            error_count = sum(
                1 for a in self._action_history if not a.success
            )

            return ActionMetrics(
                timestamp=now,
                total_actions=total_actions,
                actions_per_minute=actions_per_minute,
                avg_duration=avg_duration,
                current_action=self._current_action,
                queue_depth=self._action_queue_depth,
                success_rate=success_rate,
                error_count=error_count,
            )

    def collect_event_metrics(self) -> EventMetrics:
        """Collect event processing metrics.

        Returns:
            EventMetrics with current event statistics
        """
        with self._event_lock:
            # Calculate average processing time
            if self._event_durations:
                avg_time = sum(self._event_durations) / len(self._event_durations)
            else:
                avg_time = 0.0

            return EventMetrics(
                timestamp=time.time(),
                events_queued=self._events_queued,
                events_processed=self._events_processed,
                events_failed=self._events_failed,
                avg_processing_time=avg_time,
                queue_depth=self._event_queue_depth,
            )

    def get_latest_metrics(self) -> dict[str, Any]:
        """Get latest metrics of all types.

        Returns:
            Dictionary containing system, action, and event metrics
        """
        system = self.collect_system_metrics()
        actions = self.collect_action_metrics()
        events = self.collect_event_metrics()

        return {
            "system": {
                "timestamp": system.timestamp,
                "cpu_percent": system.cpu_percent,
                "memory_mb": system.memory_mb,
                "memory_percent": system.memory_percent,
                "thread_count": system.thread_count,
                "process_count": system.process_count,
            },
            "actions": {
                "timestamp": actions.timestamp,
                "total_actions": actions.total_actions,
                "actions_per_minute": actions.actions_per_minute,
                "avg_duration": actions.avg_duration,
                "current_action": actions.current_action,
                "queue_depth": actions.queue_depth,
                "success_rate": actions.success_rate,
                "error_count": actions.error_count,
            },
            "events": {
                "timestamp": events.timestamp,
                "events_queued": events.events_queued,
                "events_processed": events.events_processed,
                "events_failed": events.events_failed,
                "avg_processing_time": events.avg_processing_time,
                "queue_depth": events.queue_depth,
            },
        }

    def record_action(
        self, name: str, duration: float, success: bool = True
    ) -> None:
        """Record an action execution.

        Args:
            name: Name of the action
            duration: Execution duration in seconds
            success: Whether the action succeeded
        """
        with self._action_lock:
            self._action_history.append(
                ActionRecord(
                    timestamp=time.time(),
                    name=name,
                    duration=duration,
                    success=success,
                )
            )

    def set_current_action(self, name: str | None) -> None:
        """Set the currently executing action.

        Args:
            name: Name of the action, or None if no action is running
        """
        with self._action_lock:
            self._current_action = name

    def set_action_queue_depth(self, depth: int) -> None:
        """Set the current action queue depth.

        Args:
            depth: Number of actions in queue
        """
        with self._action_lock:
            self._action_queue_depth = depth

    def record_event(self, processing_time: float, success: bool = True) -> None:
        """Record an event processing.

        Args:
            processing_time: Time taken to process event in seconds
            success: Whether processing succeeded
        """
        with self._event_lock:
            self._events_queued += 1
            if success:
                self._events_processed += 1
                self._event_durations.append(processing_time)
            else:
                self._events_failed += 1

    def set_event_queue_depth(self, depth: int) -> None:
        """Set the current event queue depth.

        Args:
            depth: Number of events in queue
        """
        with self._event_lock:
            self._event_queue_depth = depth

    def get_metrics_from_queue(self, timeout: float = 0.1) -> dict[str, Any] | None:
        """Get next metrics from queue.

        Args:
            timeout: Maximum time to wait for metrics

        Returns:
            Metrics dictionary or None if queue is empty
        """
        try:
            return self._metrics_queue.get(timeout=timeout)
        except queue.Empty:
            return None
