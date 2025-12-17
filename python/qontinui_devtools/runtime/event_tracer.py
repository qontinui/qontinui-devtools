"""Event tracer for tracking event flow through the qontinui system.

This module provides comprehensive event tracing capabilities to track events
from frontend through Tauri, Python, ActionExecutor, and HAL layers.
"""

import threading
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Checkpoint:
    """A checkpoint in event processing."""

    name: str
    timestamp: float
    metadata: dict[str, Any]
    thread_id: int


@dataclass
class EventTrace:
    """Trace of a single event through the system."""

    event_id: str
    event_type: str
    created_at: float
    checkpoints: list[Checkpoint] = field(default_factory=list)
    completed: bool = False
    total_latency: float = 0.0

    def add_checkpoint(
        self, name: str, timestamp: float | None = None, metadata: dict[str, Any] | None = None
    ) -> None:
        """Add a checkpoint to the trace.

        Args:
            name: Checkpoint name (e.g., "frontend_emit", "tauri_receive")
            timestamp: Optional timestamp (defaults to current time)
            metadata: Optional metadata dictionary
        """
        if timestamp is None:
            timestamp = time.time()

        checkpoint = Checkpoint(
            name=name, timestamp=timestamp, metadata=metadata or {}, thread_id=threading.get_ident()
        )

        self.checkpoints.append(checkpoint)

        # Update total latency
        if len(self.checkpoints) > 1:
            self.total_latency = timestamp - self.checkpoints[0].timestamp

    def get_latency(self, from_checkpoint: str, to_checkpoint: str) -> float:
        """Get latency between two checkpoints.

        Args:
            from_checkpoint: Starting checkpoint name
            to_checkpoint: Ending checkpoint name

        Returns:
            Latency in seconds

        Raises:
            ValueError: If checkpoints not found
        """
        from_idx = None
        to_idx = None

        for i, checkpoint in enumerate(self.checkpoints):
            if checkpoint.name == from_checkpoint:
                from_idx = i
            if checkpoint.name == to_checkpoint:
                to_idx = i

        if from_idx is None:
            raise ValueError(f"Checkpoint not found: {from_checkpoint}")
        if to_idx is None:
            raise ValueError(f"Checkpoint not found: {to_checkpoint}")
        if to_idx <= from_idx:
            raise ValueError("to_checkpoint must come after from_checkpoint")

        return self.checkpoints[to_idx].timestamp - self.checkpoints[from_idx].timestamp

    def get_stage_latencies(self) -> dict[str, float]:
        """Get latencies between consecutive checkpoints.

        Returns:
            Dictionary mapping stage names to latencies
        """
        latencies: dict[Any, Any] = {}

        for i in range(len(self.checkpoints) - 1):
            stage_name = f"{self.checkpoints[i].name} -> {self.checkpoints[i + 1].name}"
            latency = self.checkpoints[i + 1].timestamp - self.checkpoints[i].timestamp
            latencies[stage_name] = latency

        return latencies


@dataclass
class EventFlow:
    """Analysis of event flow patterns."""

    total_events: int
    completed_events: int
    lost_events: int
    avg_latency: float
    p95_latency: float
    p99_latency: float
    bottleneck_stage: str
    stage_latencies: dict[str, float]


class EventTracer:
    """Trace events through the system.

    This class provides thread-safe event tracing with checkpoint recording,
    latency measurement, and flow analysis.

    Common checkpoint names:
        - "frontend_emit": Event emitted from frontend
        - "tauri_receive": Received by Tauri
        - "python_receive": Received by Python process
        - "executor_start": ActionExecutor starts processing
        - "hal_call": HAL operation called
        - "hal_complete": HAL operation completed
        - "executor_complete": ActionExecutor finished
        - "python_send": Python sends response
        - "tauri_send": Tauri sends to frontend
        - "frontend_receive": Frontend receives response

    Example:
        >>> tracer = EventTracer()
        >>> tracer.start_trace("evt_001", "click")
        >>> tracer.checkpoint("evt_001", "frontend_emit")
        >>> tracer.checkpoint("evt_001", "tauri_receive")
        >>> tracer.checkpoint("evt_001", "python_receive")
        >>> tracer.complete_trace("evt_001")
        >>> flow = tracer.analyze_flow()
        >>> print(f"Avg latency: {flow.avg_latency:.3f}s")
    """

    def __init__(self, max_traces: int = 10000, enable_metadata: bool = True) -> None:
        """Initialize event tracer.

        Args:
            max_traces: Maximum number of traces to keep in memory
            enable_metadata: Whether to collect metadata
        """
        self._traces: dict[str, EventTrace] = {}
        self._lock = threading.Lock()
        self._max_traces = max_traces
        self._enable_metadata = enable_metadata

    def start_trace(
        self, event_id: str, event_type: str, metadata: dict[str, Any] | None = None
    ) -> EventTrace:
        """Start tracing an event.

        Args:
            event_id: Unique event identifier
            event_type: Type of event (e.g., "click", "keypress")
            metadata: Optional metadata dictionary

        Returns:
            EventTrace instance
        """
        with self._lock:
            # Evict oldest trace if at capacity
            if len(self._traces) >= self._max_traces:
                oldest_id = min(self._traces.keys(), key=lambda k: self._traces[k].created_at)
                del self._traces[oldest_id]

            trace = EventTrace(event_id=event_id, event_type=event_type, created_at=time.time())

            self._traces[event_id] = trace

            # Add initial checkpoint with metadata
            if self._enable_metadata:
                trace.add_checkpoint("trace_start", metadata=metadata)

            return trace

    def checkpoint(
        self, event_id: str, checkpoint_name: str, metadata: dict[str, Any] | None = None
    ) -> None:
        """Record a checkpoint for an event.

        Args:
            event_id: Event identifier
            checkpoint_name: Name of the checkpoint
            metadata: Optional metadata dictionary
        """
        with self._lock:
            trace = self._traces.get(event_id)
            if trace is None:
                # Auto-create trace if not found
                trace = self.start_trace(event_id, "unknown")

            trace.add_checkpoint(
                checkpoint_name, metadata=metadata if self._enable_metadata else None
            )

    def complete_trace(self, event_id: str) -> EventTrace:
        """Mark event as completed.

        Args:
            event_id: Event identifier

        Returns:
            Completed EventTrace

        Raises:
            KeyError: If event not found
        """
        with self._lock:
            trace = self._traces.get(event_id)
            if trace is None:
                raise KeyError(f"Trace not found: {event_id}")

            trace.completed = True

            # Update total latency
            if trace.checkpoints:
                trace.total_latency = time.time() - trace.checkpoints[0].timestamp

            return trace

    def get_trace(self, event_id: str) -> EventTrace | None:
        """Get trace by ID.

        Args:
            event_id: Event identifier

        Returns:
            EventTrace or None if not found
        """
        with self._lock:
            return self._traces.get(event_id)

    def get_all_traces(self) -> list[EventTrace]:
        """Get all traces.

        Returns:
            List of all EventTrace instances
        """
        with self._lock:
            return list(self._traces.values())

    def analyze_flow(self) -> EventFlow:
        """Analyze event flow patterns.

        Returns:
            EventFlow analysis
        """
        with self._lock:
            traces = list(self._traces.values())

        if not traces:
            return EventFlow(
                total_events=0,
                completed_events=0,
                lost_events=0,
                avg_latency=0.0,
                p95_latency=0.0,
                p99_latency=0.0,
                bottleneck_stage="N/A",
                stage_latencies={},
            )

        total_events = len(traces)
        completed_events = sum(1 for t in traces if t.completed)
        lost_events = total_events - completed_events

        # Calculate latencies
        latencies = [t.total_latency for t in traces if t.total_latency > 0]

        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            sorted_latencies = sorted(latencies)
            p95_idx = int(len(sorted_latencies) * 0.95)
            p99_idx = int(len(sorted_latencies) * 0.99)
            p95_latency = sorted_latencies[p95_idx] if p95_idx < len(sorted_latencies) else 0.0
            p99_latency = sorted_latencies[p99_idx] if p99_idx < len(sorted_latencies) else 0.0
        else:
            avg_latency = 0.0
            p95_latency = 0.0
            p99_latency = 0.0

        # Aggregate stage latencies
        stage_latencies: dict[str, list[float]] = {}

        for trace in traces:
            for stage, latency in trace.get_stage_latencies().items():
                if stage not in stage_latencies:
                    stage_latencies[stage] = []
                stage_latencies[stage].append(latency)

        # Calculate average stage latencies
        avg_stage_latencies = {
            stage: sum(lats) / len(lats) for stage, lats in stage_latencies.items()
        }

        # Find bottleneck
        bottleneck_stage = "N/A"
        if avg_stage_latencies:
            bottleneck_stage = max(avg_stage_latencies.items(), key=lambda x: x[1])[0]

        return EventFlow(
            total_events=total_events,
            completed_events=completed_events,
            lost_events=lost_events,
            avg_latency=avg_latency,
            p95_latency=p95_latency,
            p99_latency=p99_latency,
            bottleneck_stage=bottleneck_stage,
            stage_latencies=avg_stage_latencies,
        )

    def find_lost_events(self, timeout: float = 5.0) -> list[EventTrace]:
        """Find events that didn't complete within timeout.

        Args:
            timeout: Timeout in seconds

        Returns:
            List of lost EventTrace instances
        """
        with self._lock:
            current_time = time.time()
            lost_traces: list[Any] = []

            for trace in self._traces.values():
                if not trace.completed:
                    age = current_time - trace.created_at
                    if age > timeout:
                        lost_traces.append(trace)

            return lost_traces

    def export_trace_timeline(self, output_path: str) -> None:
        """Export timeline visualization (Chrome trace format).

        Args:
            output_path: Output file path
        """
        from .timeline import export_chrome_trace

        with self._lock:
            traces = list(self._traces.values())

        export_chrome_trace(traces, output_path)

    def clear(self) -> None:
        """Clear all traces."""
        with self._lock:
            self._traces.clear()

    def start(self) -> None:
        """Start the tracer (for compatibility with tests).
        
        This is a no-op as the tracer is always active once instantiated.
        """
        pass

    def stop(self) -> None:
        """Stop the tracer (for compatibility with tests).
        
        This is a no-op as the tracer doesn't need explicit stopping.
        """
        pass

    def trace_event(self, event_name: str, metadata: dict[str, Any] | None = None) -> None:
        """Trace an event (for compatibility with tests).
        
        Args:
            event_name: Name of the event
            metadata: Optional metadata dictionary
        """
        event_id = f"event_{time.time()}_{threading.get_ident()}"
        self.start_trace(event_id, event_name, metadata)

    def get_events(self) -> list[EventTrace]:
        """Get all events (for compatibility with tests).
        
        Returns:
            List of all EventTrace instances
        """
        return self.get_all_traces()

    def export(self, output_path: str) -> None:
        """Export trace data (for compatibility with tests).
        
        Args:
            output_path: Output file path
        """
        self.export_trace_timeline(output_path)

    def get_statistics(self) -> dict[str, Any]:
        """Get tracer statistics.

        Returns:
            Dictionary with statistics
        """
        with self._lock:
            return {
                "total_traces": len(self._traces),
                "max_traces": self._max_traces,
                "enable_metadata": self._enable_metadata,
                "memory_usage_bytes": sum(
                    len(trace.checkpoints) * 100  # Rough estimate
                    for trace in self._traces.values()
                ),
            }
