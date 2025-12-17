"""Tests for event tracer functionality."""

from pathlib import Path
from typing import Any

import json
import threading
import time

import pytest
from qontinui_devtools.runtime import (
    EventTrace,
    EventTracer,
    analyze_latencies,
    detect_anomalies,
    export_chrome_trace,
    find_bottleneck,
)


class TestEventTrace:
    """Tests for EventTrace class."""

    def test_create_trace(self) -> None:
        """Test creating an event trace."""
        trace = EventTrace(event_id="evt_001", event_type="click", created_at=time.time())

        assert trace.event_id == "evt_001"
        assert trace.event_type == "click"
        assert not trace.completed
        assert trace.total_latency == 0.0
        assert len(trace.checkpoints) == 0

    def test_add_checkpoint(self) -> None:
        """Test adding checkpoints to a trace."""
        trace = EventTrace(event_id="evt_001", event_type="click", created_at=time.time())

        # Add checkpoints
        trace.add_checkpoint("frontend_emit")
        time.sleep(0.01)
        trace.add_checkpoint("tauri_receive")
        time.sleep(0.01)
        trace.add_checkpoint("python_receive")

        assert len(trace.checkpoints) == 3
        assert trace.checkpoints[0].name == "frontend_emit"
        assert trace.checkpoints[1].name == "tauri_receive"
        assert trace.checkpoints[2].name == "python_receive"
        assert trace.total_latency >= 0.02

    def test_add_checkpoint_with_metadata(self) -> None:
        """Test adding checkpoints with metadata."""
        trace = EventTrace(event_id="evt_001", event_type="click", created_at=time.time())

        metadata = {"button": "submit", "x": 100, "y": 200}
        trace.add_checkpoint("frontend_emit", metadata=metadata)

        assert trace.checkpoints[0].metadata == metadata

    def test_get_latency(self) -> None:
        """Test calculating latency between checkpoints."""
        trace = EventTrace(event_id="evt_001", event_type="click", created_at=time.time())

        trace.add_checkpoint("frontend_emit")
        time.sleep(0.01)
        trace.add_checkpoint("tauri_receive")
        time.sleep(0.02)
        trace.add_checkpoint("python_receive")

        # Get latency between checkpoints
        latency = trace.get_latency("frontend_emit", "python_receive")
        assert latency >= 0.03

        latency = trace.get_latency("tauri_receive", "python_receive")
        assert latency >= 0.02

    def test_get_latency_invalid_checkpoint(self) -> None:
        """Test error handling for invalid checkpoints."""
        trace = EventTrace(event_id="evt_001", event_type="click", created_at=time.time())

        trace.add_checkpoint("frontend_emit")
        trace.add_checkpoint("tauri_receive")

        with pytest.raises(ValueError, match="Checkpoint not found"):
            trace.get_latency("frontend_emit", "nonexistent")

        with pytest.raises(ValueError, match="Checkpoint not found"):
            trace.get_latency("nonexistent", "tauri_receive")

    def test_get_latency_invalid_order(self) -> None:
        """Test error handling for invalid checkpoint order."""
        trace = EventTrace(event_id="evt_001", event_type="click", created_at=time.time())

        trace.add_checkpoint("frontend_emit")
        trace.add_checkpoint("tauri_receive")

        with pytest.raises(ValueError, match="must come after"):
            trace.get_latency("tauri_receive", "frontend_emit")

    def test_get_stage_latencies(self) -> None:
        """Test getting all stage latencies."""
        trace = EventTrace(event_id="evt_001", event_type="click", created_at=time.time())

        trace.add_checkpoint("frontend_emit")
        time.sleep(0.01)
        trace.add_checkpoint("tauri_receive")
        time.sleep(0.02)
        trace.add_checkpoint("python_receive")

        latencies = trace.get_stage_latencies()

        assert "frontend_emit -> tauri_receive" in latencies
        assert "tauri_receive -> python_receive" in latencies
        assert latencies["frontend_emit -> tauri_receive"] >= 0.01
        assert latencies["tauri_receive -> python_receive"] >= 0.02


class TestEventTracer:
    """Tests for EventTracer class."""

    def test_create_tracer(self) -> None:
        """Test creating an event tracer."""
        tracer = EventTracer()

        stats = tracer.get_statistics()
        assert stats["total_traces"] == 0
        assert stats["max_traces"] == 10000
        assert stats["enable_metadata"] is True

    def test_start_trace(self) -> None:
        """Test starting a trace."""
        tracer = EventTracer()

        trace = tracer.start_trace("evt_001", "click")

        assert trace.event_id == "evt_001"
        assert trace.event_type == "click"
        assert not trace.completed

        retrieved = tracer.get_trace("evt_001")
        assert retrieved is not None
        assert retrieved.event_id == "evt_001"

    def test_start_trace_with_metadata(self) -> None:
        """Test starting a trace with metadata."""
        tracer = EventTracer()

        metadata = {"source": "button", "user_id": "123"}
        trace = tracer.start_trace("evt_001", "click", metadata=metadata)

        # Should have trace_start checkpoint with metadata
        assert len(trace.checkpoints) == 1
        assert trace.checkpoints[0].name == "trace_start"
        assert trace.checkpoints[0].metadata == metadata

    def test_checkpoint(self) -> None:
        """Test recording checkpoints."""
        tracer = EventTracer()

        tracer.start_trace("evt_001", "click")
        tracer.checkpoint("evt_001", "frontend_emit")
        time.sleep(0.01)
        tracer.checkpoint("evt_001", "tauri_receive")

        trace = tracer.get_trace("evt_001")
        assert trace is not None
        assert len(trace.checkpoints) >= 2  # May include trace_start

        # Find our checkpoints
        checkpoint_names = [cp.name for cp in trace.checkpoints]
        assert "frontend_emit" in checkpoint_names
        assert "tauri_receive" in checkpoint_names

    def test_checkpoint_auto_create(self) -> None:
        """Test auto-creating trace on checkpoint."""
        tracer = EventTracer()

        # Checkpoint without starting trace
        tracer.checkpoint("evt_001", "frontend_emit")

        trace = tracer.get_trace("evt_001")
        assert trace is not None
        assert trace.event_type == "unknown"

    def test_complete_trace(self) -> None:
        """Test completing a trace."""
        tracer = EventTracer()

        tracer.start_trace("evt_001", "click")
        tracer.checkpoint("evt_001", "frontend_emit")
        time.sleep(0.01)
        tracer.checkpoint("evt_001", "executor_complete")

        completed = tracer.complete_trace("evt_001")

        assert completed.completed
        assert completed.total_latency >= 0.01

    def test_complete_trace_not_found(self) -> None:
        """Test error handling for completing non-existent trace."""
        tracer = EventTracer()

        with pytest.raises(KeyError, match="Trace not found"):
            tracer.complete_trace("nonexistent")

    def test_concurrent_tracing(self) -> None:
        """Test thread-safe concurrent tracing."""
        tracer = EventTracer()
        errors = []

        def trace_event(event_id: str) -> None:
            try:
                tracer.start_trace(event_id, "click")
                tracer.checkpoint(event_id, "frontend_emit")
                time.sleep(0.001)
                tracer.checkpoint(event_id, "tauri_receive")
                time.sleep(0.001)
                tracer.checkpoint(event_id, "python_receive")
                tracer.complete_trace(event_id)
            except Exception as e:
                errors.append(e)

        # Start multiple threads
        threads: list[Any] = []
        for i in range(10):
            thread = threading.Thread(target=trace_event, args=(f"evt_{i}",))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Check no errors
        assert len(errors) == 0

        # Check all traces created
        assert len(tracer.get_all_traces()) == 10

        # Check all completed
        for i in range(10):
            trace = tracer.get_trace(f"evt_{i}")
            assert trace is not None
            assert trace.completed

    def test_max_traces_eviction(self) -> None:
        """Test eviction of oldest traces when max is reached."""
        tracer = EventTracer(max_traces=5)

        # Create 10 traces
        for i in range(10):
            tracer.start_trace(f"evt_{i}", "click")
            time.sleep(0.001)  # Ensure different timestamps

        # Should only keep 5 most recent
        stats = tracer.get_statistics()
        assert stats["total_traces"] == 5

        # Oldest traces should be evicted
        assert tracer.get_trace("evt_0") is None
        assert tracer.get_trace("evt_1") is None
        assert tracer.get_trace("evt_5") is not None
        assert tracer.get_trace("evt_9") is not None

    def test_analyze_flow(self) -> None:
        """Test flow analysis."""
        tracer = EventTracer()

        # Create some traces
        for i in range(5):
            tracer.start_trace(f"evt_{i}", "click")
            tracer.checkpoint(f"evt_{i}", "frontend_emit")
            time.sleep(0.01)
            tracer.checkpoint(f"evt_{i}", "tauri_receive")
            time.sleep(0.02)
            tracer.checkpoint(f"evt_{i}", "python_receive")
            tracer.complete_trace(f"evt_{i}")

        # Create one incomplete trace
        tracer.start_trace("evt_lost", "click")
        tracer.checkpoint("evt_lost", "frontend_emit")

        flow = tracer.analyze_flow()

        assert flow.total_events == 6
        assert flow.completed_events == 5
        assert flow.lost_events == 1
        assert flow.avg_latency >= 0.03
        assert flow.bottleneck_stage != "N/A"

    def test_find_lost_events(self) -> None:
        """Test finding lost events."""
        tracer = EventTracer()

        # Create completed trace
        tracer.start_trace("evt_complete", "click")
        tracer.checkpoint("evt_complete", "frontend_emit")
        tracer.complete_trace("evt_complete")

        # Create lost trace
        tracer.start_trace("evt_lost", "click")
        tracer.checkpoint("evt_lost", "frontend_emit")

        # Wait for timeout
        time.sleep(0.1)

        lost = tracer.find_lost_events(timeout=0.05)

        assert len(lost) == 1
        assert lost[0].event_id == "evt_lost"
        assert not lost[0].completed

    def test_clear(self) -> None:
        """Test clearing all traces."""
        tracer = EventTracer()

        tracer.start_trace("evt_001", "click")
        tracer.start_trace("evt_002", "click")

        assert len(tracer.get_all_traces()) == 2

        tracer.clear()

        assert len(tracer.get_all_traces()) == 0

    def test_export_trace_timeline(self, tmp_path: Path) -> None:
        """Test exporting trace timeline."""
        tracer = EventTracer()

        # Create some traces
        for i in range(3):
            tracer.start_trace(f"evt_{i}", "click")
            tracer.checkpoint(f"evt_{i}", "frontend_emit")
            time.sleep(0.01)
            tracer.checkpoint(f"evt_{i}", "tauri_receive")
            tracer.complete_trace(f"evt_{i}")

        output_path = tmp_path / "timeline.json"
        tracer.export_trace_timeline(str(output_path))

        assert output_path.exists()

        # Verify it's valid JSON
        with open(output_path) as f:
            data = json.load(f)
            assert "traceEvents" in data
            assert len(data["traceEvents"]) > 0


class TestLatencyAnalyzer:
    """Tests for latency analysis functions."""

    def test_analyze_latencies(self) -> None:
        """Test latency analysis."""
        tracer = EventTracer()

        # Create traces with consistent pattern
        for i in range(10):
            tracer.start_trace(f"evt_{i}", "click")
            tracer.checkpoint(f"evt_{i}", "frontend_emit")
            time.sleep(0.01)
            tracer.checkpoint(f"evt_{i}", "tauri_receive")
            time.sleep(0.02)
            tracer.checkpoint(f"evt_{i}", "python_receive")
            tracer.complete_trace(f"evt_{i}")

        traces = tracer.get_all_traces()
        latencies = analyze_latencies(traces)

        # Remove trace_start if present
        latencies = {k: v for k, v in latencies.items() if "trace_start" not in k}

        assert len(latencies) >= 2

        # Check statistics structure
        for _stage, stats in latencies.items():
            assert "mean" in stats
            assert "p50" in stats
            assert "p95" in stats
            assert "p99" in stats
            assert "min" in stats
            assert "max" in stats
            assert "count" in stats
            assert stats["count"] == 10

    def test_find_bottleneck(self) -> None:
        """Test bottleneck detection."""
        tracer = EventTracer()

        # Create traces with slow stage
        for i in range(5):
            tracer.start_trace(f"evt_{i}", "click")
            tracer.checkpoint(f"evt_{i}", "frontend_emit")
            time.sleep(0.001)
            tracer.checkpoint(f"evt_{i}", "tauri_receive")
            time.sleep(0.05)  # Slow stage
            tracer.checkpoint(f"evt_{i}", "python_receive")
            time.sleep(0.001)
            tracer.checkpoint(f"evt_{i}", "executor_complete")
            tracer.complete_trace(f"evt_{i}")

        traces = tracer.get_all_traces()
        bottleneck = find_bottleneck(traces)

        assert "tauri_receive -> python_receive" in bottleneck

    def test_detect_anomalies(self) -> None:
        """Test anomaly detection."""
        tracer = EventTracer()

        # Create normal traces
        for i in range(5):
            tracer.start_trace(f"evt_{i}", "click")
            tracer.checkpoint(f"evt_{i}", "frontend_emit")
            time.sleep(0.01)
            tracer.checkpoint(f"evt_{i}", "tauri_receive")
            tracer.complete_trace(f"evt_{i}")

        # Create anomalous trace
        tracer.start_trace("evt_slow", "click")
        tracer.checkpoint("evt_slow", "frontend_emit")
        time.sleep(0.1)  # 10x slower
        tracer.checkpoint("evt_slow", "tauri_receive")
        tracer.complete_trace("evt_slow")

        traces = tracer.get_all_traces()
        anomalies = detect_anomalies(traces, threshold=2.0)

        # Should detect the slow trace
        assert len(anomalies) >= 1
        anomaly_ids = [event_id for event_id, _, _ in anomalies]
        assert "evt_slow" in anomaly_ids


class TestChromeTraceExport:
    """Tests for Chrome trace export."""

    def test_export_chrome_trace(self, tmp_path: Path) -> None:
        """Test exporting to Chrome trace format."""
        tracer = EventTracer()

        # Create some traces
        for i in range(3):
            tracer.start_trace(f"evt_{i}", "click")
            tracer.checkpoint(f"evt_{i}", "frontend_emit")
            time.sleep(0.01)
            tracer.checkpoint(f"evt_{i}", "tauri_receive")
            time.sleep(0.01)
            tracer.checkpoint(f"evt_{i}", "python_receive")
            tracer.complete_trace(f"evt_{i}")

        output_path = tmp_path / "chrome_trace.json"
        export_chrome_trace(tracer.get_all_traces(), str(output_path))

        assert output_path.exists()

        # Verify format
        with open(output_path) as f:
            data = json.load(f)
            assert "traceEvents" in data
            assert "displayTimeUnit" in data
            assert len(data["traceEvents"]) > 0

            # Check event structure
            event = data["traceEvents"][0]
            assert "name" in event
            assert "ph" in event  # Phase
            assert "ts" in event  # Timestamp
            assert "pid" in event
            assert "tid" in event


class TestPerformance:
    """Performance tests for event tracer."""

    def test_tracer_overhead(self) -> None:
        """Test that tracer has minimal overhead."""
        tracer = EventTracer()

        # Measure without tracing
        start = time.time()
        for _i in range(1000):
            pass  # Do nothing
        baseline = time.time() - start

        # Measure with tracing
        start = time.time()
        for i in range(1000):
            tracer.start_trace(f"evt_{i}", "test")
            tracer.checkpoint(f"evt_{i}", "checkpoint1")
            tracer.checkpoint(f"evt_{i}", "checkpoint2")
            tracer.complete_trace(f"evt_{i}")
        traced = time.time() - start

        # Overhead should be small (allow 100x for safety)
        overhead_pct = (traced - baseline) / traced * 100 if traced > 0 else 0
        print(f"Baseline: {baseline:.4f}s, Traced: {traced:.4f}s, Overhead: {overhead_pct:.1f}%")

        # Should be reasonably fast
        assert traced < 1.0  # Less than 1 second for 1000 traces

    def test_concurrent_performance(self) -> None:
        """Test concurrent tracing performance."""
        tracer = EventTracer()
        num_threads = 10
        traces_per_thread = 100

        def worker() -> None:
            for i in range(traces_per_thread):
                event_id = f"evt_{threading.get_ident()}_{i}"
                tracer.start_trace(event_id, "test")
                tracer.checkpoint(event_id, "checkpoint1")
                tracer.checkpoint(event_id, "checkpoint2")
                tracer.complete_trace(event_id)

        start = time.time()

        threads: list[Any] = []
        for _ in range(num_threads):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        elapsed = time.time() - start

        # Should complete in reasonable time
        assert elapsed < 5.0
        print(f"Concurrent tracing: {num_threads * traces_per_thread} traces in {elapsed:.2f}s")
