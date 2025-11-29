"""Tests for the real-time performance dashboard.

This module tests:
- Metrics collection functionality
- WebSocket server operation
- Client connection and disconnection
- Metrics broadcasting
- Concurrent client support
"""

import asyncio
import json
import time

import pytest
from aiohttp import WSMsgType
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from qontinui_devtools.runtime import (
    ActionMetrics,
    DashboardServer,
    EventMetrics,
    MetricsCollector,
    SystemMetrics,
)


class TestMetricsCollector:
    """Test suite for MetricsCollector."""

    def test_initialization(self) -> None:
        """Test MetricsCollector initialization."""
        collector = MetricsCollector(sample_interval=1.0, history_size=100)

        assert collector._interval == 1.0
        assert collector._history_size == 100
        assert not collector._running
        assert collector._thread is None

    def test_system_metrics_collection(self) -> None:
        """Test collection of system metrics."""
        collector = MetricsCollector()
        metrics = collector.collect_system_metrics()

        assert isinstance(metrics, SystemMetrics)
        assert metrics.cpu_percent >= 0
        assert metrics.memory_mb >= 0
        assert metrics.memory_percent >= 0
        assert metrics.thread_count > 0
        assert metrics.process_count >= 1
        assert metrics.timestamp > 0

    def test_action_metrics_collection(self) -> None:
        """Test collection of action metrics."""
        collector = MetricsCollector()

        # Record some actions
        collector.record_action("test_action_1", 0.1, success=True)
        collector.record_action("test_action_2", 0.2, success=True)
        collector.record_action("test_action_3", 0.15, success=False)

        time.sleep(0.1)  # Let metrics settle

        metrics = collector.collect_action_metrics()

        assert isinstance(metrics, ActionMetrics)
        assert metrics.total_actions == 3
        assert metrics.error_count == 1
        assert metrics.success_rate < 100.0  # Should be ~66.7%
        assert metrics.avg_duration > 0

    def test_event_metrics_collection(self) -> None:
        """Test collection of event metrics."""
        collector = MetricsCollector()

        # Record some events
        collector.record_event(0.05, success=True)
        collector.record_event(0.03, success=True)
        collector.record_event(0.04, success=False)

        metrics = collector.collect_event_metrics()

        assert isinstance(metrics, EventMetrics)
        assert metrics.events_queued == 3
        assert metrics.events_processed == 2
        assert metrics.events_failed == 1
        assert metrics.avg_processing_time > 0

    def test_get_latest_metrics(self) -> None:
        """Test getting latest metrics of all types."""
        collector = MetricsCollector()

        metrics = collector.get_latest_metrics()

        assert "system" in metrics
        assert "actions" in metrics
        assert "events" in metrics

        # Check system metrics structure
        assert "cpu_percent" in metrics["system"]
        assert "memory_mb" in metrics["system"]
        assert "thread_count" in metrics["system"]

        # Check action metrics structure
        assert "total_actions" in metrics["actions"]
        assert "actions_per_minute" in metrics["actions"]
        assert "success_rate" in metrics["actions"]

        # Check event metrics structure
        assert "events_queued" in metrics["events"]
        assert "events_processed" in metrics["events"]

    def test_action_queue_depth(self) -> None:
        """Test setting and tracking action queue depth."""
        collector = MetricsCollector()

        collector.set_action_queue_depth(5)
        metrics = collector.collect_action_metrics()

        assert metrics.queue_depth == 5

    def test_event_queue_depth(self) -> None:
        """Test setting and tracking event queue depth."""
        collector = MetricsCollector()

        collector.set_event_queue_depth(10)
        metrics = collector.collect_event_metrics()

        assert metrics.queue_depth == 10

    def test_current_action_tracking(self) -> None:
        """Test tracking current action."""
        collector = MetricsCollector()

        collector.set_current_action("current_test_action")
        metrics = collector.collect_action_metrics()

        assert metrics.current_action == "current_test_action"

        collector.set_current_action(None)
        metrics = collector.collect_action_metrics()

        assert metrics.current_action is None

    def test_start_stop_collector(self) -> None:
        """Test starting and stopping the collector."""
        collector = MetricsCollector(sample_interval=0.1)

        # Start collector
        collector.start()
        assert collector._running
        assert collector._thread is not None
        assert collector._thread.is_alive()

        time.sleep(0.3)  # Let it collect a few samples

        # Stop collector
        collector.stop()
        assert not collector._running

    def test_metrics_queue(self) -> None:
        """Test metrics queue functionality."""
        collector = MetricsCollector(sample_interval=0.1)

        collector.start()
        time.sleep(0.3)  # Let it collect samples

        # Should have metrics in queue
        metrics = collector.get_metrics_from_queue(timeout=1.0)
        assert metrics is not None
        assert "system" in metrics

        collector.stop()

    def test_action_history_limit(self) -> None:
        """Test that action history respects size limit."""
        collector = MetricsCollector(history_size=5)

        # Record more actions than history size
        for i in range(10):
            collector.record_action(f"action_{i}", 0.1, success=True)

        # Should only keep last 5
        assert len(collector._action_history) == 5

    def test_actions_per_minute_calculation(self) -> None:
        """Test actions per minute calculation."""
        collector = MetricsCollector()

        # Record actions
        for _ in range(5):
            collector.record_action("test", 0.1, success=True)

        metrics = collector.collect_action_metrics()

        # Should show 5 actions in the last minute
        assert metrics.actions_per_minute == 5.0

    def test_success_rate_calculation(self) -> None:
        """Test success rate calculation."""
        collector = MetricsCollector()

        # 3 successes, 1 failure
        collector.record_action("test1", 0.1, success=True)
        collector.record_action("test2", 0.1, success=True)
        collector.record_action("test3", 0.1, success=True)
        collector.record_action("test4", 0.1, success=False)

        metrics = collector.collect_action_metrics()

        assert metrics.success_rate == 75.0

    def test_empty_metrics(self) -> None:
        """Test metrics with no recorded data."""
        collector = MetricsCollector()

        action_metrics = collector.collect_action_metrics()
        assert action_metrics.total_actions == 0
        assert action_metrics.success_rate == 100.0  # Default
        assert action_metrics.avg_duration == 0.0

        event_metrics = collector.collect_event_metrics()
        assert event_metrics.events_queued == 0
        assert event_metrics.avg_processing_time == 0.0


class TestDashboardServer(AioHTTPTestCase):
    """Test suite for DashboardServer using aiohttp test utilities."""

    async def get_application(self):  # type: ignore
        """Create application for testing."""
        self.collector = MetricsCollector(sample_interval=0.1)
        self.server = DashboardServer(host="localhost", port=8765, metrics_collector=self.collector)
        return self.server.app

    @unittest_run_loop
    async def test_index_handler(self) -> None:
        """Test serving dashboard HTML."""
        resp = await self.client.request("GET", "/")
        assert resp.status == 200

        text = await resp.text()
        assert "Qontinui Performance Dashboard" in text
        assert "Chart.js" in text

    @unittest_run_loop
    async def test_websocket_connection(self) -> None:
        """Test WebSocket connection establishment."""
        async with self.client.ws_connect("/ws") as ws:
            # Should receive initial metrics
            msg = await ws.receive()
            assert msg.type == WSMsgType.TEXT

            data = json.loads(msg.data)
            assert "system" in data
            assert "actions" in data
            assert "events" in data

    @unittest_run_loop
    async def test_websocket_ping_pong(self) -> None:
        """Test WebSocket ping/pong functionality."""
        async with self.client.ws_connect("/ws") as ws:
            # Skip initial metrics
            await ws.receive()

            # Send ping
            await ws.send_json({"type": "ping", "timestamp": 123456})

            # Should receive pong
            msg = await ws.receive()
            data = json.loads(msg.data)

            assert data["type"] == "pong"
            assert data["timestamp"] == 123456

    @unittest_run_loop
    async def test_websocket_request_metrics(self) -> None:
        """Test requesting metrics via WebSocket."""
        async with self.client.ws_connect("/ws") as ws:
            # Skip initial metrics
            await ws.receive()

            # Request metrics
            await ws.send_json({"type": "request_metrics"})

            # Should receive metrics
            msg = await ws.receive()
            data = json.loads(msg.data)

            assert "system" in data
            assert "actions" in data

    @unittest_run_loop
    async def test_multiple_websocket_clients(self) -> None:
        """Test multiple concurrent WebSocket clients."""
        # Connect multiple clients
        ws1 = await self.client.ws_connect("/ws")
        ws2 = await self.client.ws_connect("/ws")
        ws3 = await self.client.ws_connect("/ws")

        try:
            # All should receive initial metrics
            msg1 = await ws1.receive()
            msg2 = await ws2.receive()
            msg3 = await ws3.receive()

            assert msg1.type == WSMsgType.TEXT
            assert msg2.type == WSMsgType.TEXT
            assert msg3.type == WSMsgType.TEXT

            # All should have valid data
            data1 = json.loads(msg1.data)
            data2 = json.loads(msg2.data)
            data3 = json.loads(msg3.data)

            assert "system" in data1
            assert "system" in data2
            assert "system" in data3

        finally:
            await ws1.close()
            await ws2.close()
            await ws3.close()

    @unittest_run_loop
    async def test_client_tracking(self) -> None:
        """Test that server tracks connected clients."""
        initial_count = len(self.server.clients)

        # Connect client
        ws = await self.client.ws_connect("/ws")
        await ws.receive()  # Wait for initial metrics

        # Should have one more client
        assert len(self.server.clients) == initial_count + 1

        # Disconnect
        await ws.close()
        await asyncio.sleep(0.1)  # Give time for cleanup

        # Should be back to initial count
        assert len(self.server.clients) == initial_count

    @unittest_run_loop
    async def test_metrics_with_data(self) -> None:
        """Test that metrics contain real data."""
        # Record some data
        self.collector.record_action("test_action", 0.1, success=True)
        self.collector.set_action_queue_depth(5)
        self.collector.record_event(0.05, success=True)

        async with self.client.ws_connect("/ws") as ws:
            msg = await ws.receive()
            data = json.loads(msg.data)

            # Check system metrics
            assert data["system"]["cpu_percent"] >= 0
            assert data["system"]["memory_mb"] > 0

            # Check action metrics
            assert data["actions"]["total_actions"] >= 1
            assert data["actions"]["queue_depth"] == 5

            # Check event metrics
            assert data["events"]["events_queued"] >= 1

    def test_dashboard_server_initialization(self) -> None:
        """Test DashboardServer initialization."""
        collector = MetricsCollector()
        server = DashboardServer(host="0.0.0.0", port=9000, metrics_collector=collector)

        assert server.host == "0.0.0.0"
        assert server.port == 9000
        assert server.collector is collector
        assert len(server.clients) == 0

    def test_embedded_html_generation(self) -> None:
        """Test embedded HTML generation."""
        server = DashboardServer()
        html = server._get_embedded_dashboard_html()

        assert "<!DOCTYPE html>" in html
        assert "Qontinui Performance Dashboard" in html
        assert "Chart.js" in html
        assert "WebSocket" in html


@pytest.mark.integration
class TestDashboardIntegration:
    """Integration tests for dashboard system."""

    def test_end_to_end_metrics_flow(self) -> None:
        """Test complete metrics collection and retrieval flow."""
        collector = MetricsCollector(sample_interval=0.1)

        # Start collector
        collector.start()

        # Generate some activity
        for i in range(5):
            collector.record_action(f"action_{i}", 0.05, success=True)
            collector.record_event(0.02, success=True)

        time.sleep(0.3)  # Let metrics collect

        # Get metrics
        metrics = collector.get_latest_metrics()

        # Verify all data is present
        assert metrics["system"]["cpu_percent"] >= 0
        assert metrics["actions"]["total_actions"] == 5
        assert metrics["events"]["events_processed"] == 5

        collector.stop()

    def test_metrics_under_load(self) -> None:
        """Test metrics collection under load."""
        collector = MetricsCollector(sample_interval=0.05)
        collector.start()

        # Generate load
        for i in range(100):
            collector.record_action(f"action_{i}", 0.001, success=(i % 10 != 0))

        time.sleep(0.2)

        metrics = collector.collect_action_metrics()

        assert metrics.total_actions == 100
        assert 80 <= metrics.success_rate <= 95  # ~90% success rate

        collector.stop()

    def test_collector_restart(self) -> None:
        """Test stopping and restarting the collector."""
        collector = MetricsCollector(sample_interval=0.1)

        # Start
        collector.start()
        assert collector._running

        # Stop
        collector.stop()
        assert not collector._running

        # Restart
        collector.start()
        assert collector._running

        collector.stop()

    def test_metrics_accuracy(self) -> None:
        """Test accuracy of metrics calculations."""
        collector = MetricsCollector()

        # Record exact data
        collector.record_action("action1", 0.1, success=True)
        collector.record_action("action2", 0.2, success=True)
        collector.record_action("action3", 0.3, success=True)

        metrics = collector.collect_action_metrics()

        # Average should be 0.2
        expected_avg = 0.2
        assert abs(metrics.avg_duration - expected_avg) < 0.01

        # Success rate should be 100%
        assert metrics.success_rate == 100.0

    def test_concurrent_metric_recording(self) -> None:
        """Test thread-safe concurrent metric recording."""
        import threading

        collector = MetricsCollector()

        def record_actions():
            for i in range(50):
                collector.record_action(f"action_{i}", 0.01, success=True)

        def record_events():
            for _i in range(50):
                collector.record_event(0.01, success=True)

        # Run concurrently
        t1 = threading.Thread(target=record_actions)
        t2 = threading.Thread(target=record_events)

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        # Verify all recorded
        action_metrics = collector.collect_action_metrics()
        event_metrics = collector.collect_event_metrics()

        assert action_metrics.total_actions == 50
        assert event_metrics.events_processed == 50


class TestMetricsDataClasses:
    """Test the metrics dataclasses."""

    def test_system_metrics_creation(self) -> None:
        """Test SystemMetrics dataclass creation."""
        metrics = SystemMetrics(
            timestamp=123.456,
            cpu_percent=45.5,
            memory_mb=512,
            memory_percent=25.0,
            thread_count=10,
            process_count=2,
        )

        assert metrics.timestamp == 123.456
        assert metrics.cpu_percent == 45.5
        assert metrics.memory_mb == 512
        assert metrics.thread_count == 10

    def test_action_metrics_creation(self) -> None:
        """Test ActionMetrics dataclass creation."""
        metrics = ActionMetrics(
            timestamp=123.456,
            total_actions=100,
            actions_per_minute=30.0,
            avg_duration=0.15,
            current_action="test_action",
            queue_depth=5,
            success_rate=95.0,
            error_count=5,
        )

        assert metrics.total_actions == 100
        assert metrics.actions_per_minute == 30.0
        assert metrics.current_action == "test_action"
        assert metrics.success_rate == 95.0

    def test_event_metrics_creation(self) -> None:
        """Test EventMetrics dataclass creation."""
        metrics = EventMetrics(
            timestamp=123.456,
            events_queued=150,
            events_processed=145,
            events_failed=5,
            avg_processing_time=0.05,
            queue_depth=10,
        )

        assert metrics.events_queued == 150
        assert metrics.events_processed == 145
        assert metrics.events_failed == 5
        assert metrics.queue_depth == 10
