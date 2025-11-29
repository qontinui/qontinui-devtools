"""WebSocket server for real-time performance dashboard.

This module provides a web server with WebSocket support for streaming
real-time metrics to connected clients.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

import aiohttp
from aiohttp import web

from .metrics_collector import MetricsCollector

logger = logging.getLogger(__name__)


class DashboardServer:
    """WebSocket server for real-time metrics streaming.

    This server provides:
    - HTTP endpoint serving the dashboard HTML
    - WebSocket endpoint for real-time metrics streaming
    - Support for multiple concurrent clients
    - Automatic client management and cleanup

    Example:
        >>> collector = MetricsCollector(sample_interval=1.0)
        >>> server = DashboardServer(
        ...     host="localhost",
        ...     port=8765,
        ...     metrics_collector=collector
        ... )
        >>> server.start()

    Args:
        host: Server host address (default: "localhost")
        port: Server port number (default: 8765)
        metrics_collector: Optional MetricsCollector instance
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8765,
        metrics_collector: MetricsCollector | None = None,
    ) -> None:
        """Initialize the dashboard server.

        Args:
            host: Server host address
            port: Server port number
            metrics_collector: Optional MetricsCollector instance
        """
        self.host = host
        self.port = port
        self.collector = metrics_collector or MetricsCollector()
        self.clients: set[web.WebSocketResponse] = set()
        self.app = web.Application()
        self._setup_routes()
        self._broadcast_task: asyncio.Task[None] | None = None
        self._runner: web.AppRunner | None = None

    def _setup_routes(self) -> None:
        """Setup HTTP and WebSocket routes."""
        self.app.router.add_get("/ws", self.websocket_handler)
        self.app.router.add_get("/", self.index_handler)

    async def websocket_handler(self, request: web.Request) -> web.WebSocketResponse:
        """Handle WebSocket connections for metrics streaming.

        Args:
            request: Incoming HTTP request

        Returns:
            WebSocket response
        """
        ws = web.WebSocketResponse(heartbeat=30.0)
        await ws.prepare(request)

        # Add client to set
        self.clients.add(ws)
        logger.info(f"Client connected. Total clients: {len(self.clients)}")

        try:
            # Send initial metrics immediately
            try:
                metrics = self.collector.get_latest_metrics()
                await ws.send_json(metrics)
            except Exception as e:
                logger.error(f"Error sending initial metrics: {e}")

            # Handle incoming messages
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    # Handle client messages if needed
                    try:
                        data = json.loads(msg.data)
                        await self._handle_client_message(ws, data)
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON from client: {msg.data}")
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {ws.exception()}")
        except asyncio.CancelledError:
            logger.info("WebSocket handler cancelled")
        except Exception as e:
            logger.error(f"WebSocket handler error: {e}")
        finally:
            self.clients.discard(ws)
            logger.info(f"Client disconnected. Total clients: {len(self.clients)}")

        return ws

    async def _handle_client_message(self, ws: web.WebSocketResponse, data: dict[str, Any]) -> None:
        """Handle messages from clients.

        Args:
            ws: WebSocket connection
            data: Message data
        """
        msg_type = data.get("type")

        if msg_type == "ping":
            await ws.send_json({"type": "pong", "timestamp": data.get("timestamp")})
        elif msg_type == "request_metrics":
            metrics = self.collector.get_latest_metrics()
            await ws.send_json(metrics)

    async def index_handler(self, request: web.Request) -> web.Response:
        """Serve dashboard HTML.

        Args:
            request: Incoming HTTP request

        Returns:
            HTTP response with dashboard HTML
        """
        html = self._generate_dashboard_html()
        return web.Response(text=html, content_type="text/html")

    def _generate_dashboard_html(self) -> str:
        """Generate the dashboard HTML content.

        Returns:
            Complete HTML document as string
        """
        # Check if template file exists
        template_path = Path(__file__).parent / "templates" / "dashboard.html"
        if template_path.exists():
            return template_path.read_text()

        # Return embedded HTML if template not found
        return self._get_embedded_dashboard_html()

    def _get_embedded_dashboard_html(self) -> str:
        """Get embedded dashboard HTML.

        Returns:
            Embedded HTML content
        """
        return """<!DOCTYPE html>
<html>
<head>
    <title>Qontinui Performance Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            background: #1a1a2e;
            color: #eee;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        .card {
            background: #16213e;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
        }
        .status-good { color: #4ade80; }
        .status-warn { color: #fbbf24; }
        .status-error { color: #f87171; }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-indicator.connected { background: #4ade80; }
        .status-indicator.disconnected { background: #f87171; }
    </style>
</head>
<body class="p-8">
    <div class="flex justify-between items-center mb-8">
        <h1 class="text-3xl font-bold">Qontinui Performance Dashboard</h1>
        <div class="flex items-center">
            <span class="status-indicator connected" id="connection-status"></span>
            <span id="connection-text">Connected</span>
        </div>
    </div>

    <!-- Metric Cards -->
    <div class="grid grid-cols-4 gap-6 mb-8">
        <div class="card">
            <div class="text-sm text-gray-400">CPU Usage</div>
            <div id="cpu-value" class="metric-value">0%</div>
        </div>
        <div class="card">
            <div class="text-sm text-gray-400">Memory</div>
            <div id="memory-value" class="metric-value">0 MB</div>
        </div>
        <div class="card">
            <div class="text-sm text-gray-400">Actions/min</div>
            <div id="actions-value" class="metric-value">0</div>
        </div>
        <div class="card">
            <div class="text-sm text-gray-400">Success Rate</div>
            <div id="success-rate" class="metric-value status-good">100%</div>
        </div>
    </div>

    <!-- Secondary Metrics -->
    <div class="grid grid-cols-4 gap-6 mb-8">
        <div class="card">
            <div class="text-sm text-gray-400">Threads</div>
            <div id="thread-count" class="metric-value">0</div>
        </div>
        <div class="card">
            <div class="text-sm text-gray-400">Action Queue</div>
            <div id="action-queue" class="metric-value">0</div>
        </div>
        <div class="card">
            <div class="text-sm text-gray-400">Event Queue</div>
            <div id="event-queue" class="metric-value">0</div>
        </div>
        <div class="card">
            <div class="text-sm text-gray-400">Error Count</div>
            <div id="error-count" class="metric-value">0</div>
        </div>
    </div>

    <!-- Charts -->
    <div class="grid grid-cols-2 gap-6">
        <div class="card">
            <h3 class="text-lg font-bold mb-4">CPU & Memory</h3>
            <canvas id="systemChart"></canvas>
        </div>
        <div class="card">
            <h3 class="text-lg font-bold mb-4">Action Performance</h3>
            <canvas id="actionChart"></canvas>
        </div>
        <div class="card">
            <h3 class="text-lg font-bold mb-4">Event Queue Depth</h3>
            <canvas id="queueChart"></canvas>
        </div>
        <div class="card">
            <h3 class="text-lg font-bold mb-4">Error Rate</h3>
            <canvas id="errorChart"></canvas>
        </div>
    </div>

    <script>
        // WebSocket connection
        let ws = null;
        let reconnectAttempts = 0;
        const maxReconnectAttempts = 10;

        function connect() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

            ws.onopen = () => {
                console.log('Connected to dashboard server');
                reconnectAttempts = 0;
                updateConnectionStatus(true);
            };

            ws.onclose = () => {
                console.log('Disconnected from dashboard server');
                updateConnectionStatus(false);

                // Attempt reconnection
                if (reconnectAttempts < maxReconnectAttempts) {
                    reconnectAttempts++;
                    setTimeout(connect, 2000 * reconnectAttempts);
                }
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

            ws.onmessage = (event) => {
                try {
                    const metrics = JSON.parse(event.data);
                    updateDashboard(metrics);
                } catch (e) {
                    console.error('Error parsing metrics:', e);
                }
            };
        }

        function updateConnectionStatus(connected) {
            const indicator = document.getElementById('connection-status');
            const text = document.getElementById('connection-text');

            if (connected) {
                indicator.className = 'status-indicator connected';
                text.textContent = 'Connected';
            } else {
                indicator.className = 'status-indicator disconnected';
                text.textContent = 'Disconnected';
            }
        }

        // Chart configurations
        const chartConfig = {
            responsive: true,
            maintainAspectRatio: true,
            animation: false,
            plugins: {
                legend: {
                    labels: { color: '#eee' }
                }
            },
            scales: {
                y: {
                    ticks: { color: '#999' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                },
                x: {
                    ticks: { color: '#999' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                }
            }
        };

        const systemChart = new Chart(document.getElementById('systemChart'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'CPU %',
                        data: [],
                        borderColor: '#4ade80',
                        backgroundColor: 'rgba(74, 222, 128, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: 'Memory %',
                        data: [],
                        borderColor: '#60a5fa',
                        backgroundColor: 'rgba(96, 165, 250, 0.1)',
                        tension: 0.4
                    }
                ]
            },
            options: { ...chartConfig, scales: { ...chartConfig.scales, y: { ...chartConfig.scales.y, min: 0, max: 100 } } }
        });

        const actionChart = new Chart(document.getElementById('actionChart'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Actions/min',
                        data: [],
                        borderColor: '#a78bfa',
                        backgroundColor: 'rgba(167, 139, 250, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: 'Avg Duration (ms)',
                        data: [],
                        borderColor: '#fbbf24',
                        backgroundColor: 'rgba(251, 191, 36, 0.1)',
                        tension: 0.4,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                ...chartConfig,
                scales: {
                    ...chartConfig.scales,
                    y: { ...chartConfig.scales.y, position: 'left' },
                    y1: { ...chartConfig.scales.y, position: 'right', grid: { display: false } }
                }
            }
        });

        const queueChart = new Chart(document.getElementById('queueChart'), {
            type: 'bar',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Action Queue',
                        data: [],
                        backgroundColor: 'rgba(167, 139, 250, 0.7)',
                        borderColor: '#a78bfa',
                        borderWidth: 1
                    },
                    {
                        label: 'Event Queue',
                        data: [],
                        backgroundColor: 'rgba(96, 165, 250, 0.7)',
                        borderColor: '#60a5fa',
                        borderWidth: 1
                    }
                ]
            },
            options: chartConfig
        });

        const errorChart = new Chart(document.getElementById('errorChart'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Error Count',
                        data: [],
                        borderColor: '#f87171',
                        backgroundColor: 'rgba(248, 113, 113, 0.1)',
                        tension: 0.4,
                        fill: true
                    }
                ]
            },
            options: { ...chartConfig, scales: { ...chartConfig.scales, y: { ...chartConfig.scales.y, min: 0 } } }
        });

        // Update dashboard with new metrics
        function updateDashboard(metrics) {
            if (!metrics) return;

            // Update metric cards
            if (metrics.system) {
                document.getElementById('cpu-value').textContent =
                    `${metrics.system.cpu_percent.toFixed(1)}%`;
                document.getElementById('memory-value').textContent =
                    `${metrics.system.memory_mb} MB`;
                document.getElementById('thread-count').textContent =
                    `${metrics.system.thread_count}`;
            }

            if (metrics.actions) {
                document.getElementById('actions-value').textContent =
                    `${metrics.actions.actions_per_minute.toFixed(1)}`;

                const successRate = metrics.actions.success_rate;
                const successElem = document.getElementById('success-rate');
                successElem.textContent = `${successRate.toFixed(1)}%`;

                // Color code success rate
                if (successRate >= 95) {
                    successElem.className = 'metric-value status-good';
                } else if (successRate >= 80) {
                    successElem.className = 'metric-value status-warn';
                } else {
                    successElem.className = 'metric-value status-error';
                }

                document.getElementById('action-queue').textContent =
                    `${metrics.actions.queue_depth}`;
                document.getElementById('error-count').textContent =
                    `${metrics.actions.error_count}`;
            }

            if (metrics.events) {
                document.getElementById('event-queue').textContent =
                    `${metrics.events.queue_depth}`;
            }

            // Update charts
            const now = new Date().toLocaleTimeString();
            const maxPoints = 60; // Keep 60 data points (1 minute at 1s intervals)

            // System chart
            systemChart.data.labels.push(now);
            systemChart.data.datasets[0].data.push(metrics.system?.cpu_percent || 0);
            systemChart.data.datasets[1].data.push(metrics.system?.memory_percent || 0);

            if (systemChart.data.labels.length > maxPoints) {
                systemChart.data.labels.shift();
                systemChart.data.datasets.forEach(d => d.data.shift());
            }
            systemChart.update('none');

            // Action chart
            actionChart.data.labels.push(now);
            actionChart.data.datasets[0].data.push(metrics.actions?.actions_per_minute || 0);
            actionChart.data.datasets[1].data.push((metrics.actions?.avg_duration || 0) * 1000); // Convert to ms

            if (actionChart.data.labels.length > maxPoints) {
                actionChart.data.labels.shift();
                actionChart.data.datasets.forEach(d => d.data.shift());
            }
            actionChart.update('none');

            // Queue chart
            queueChart.data.labels.push(now);
            queueChart.data.datasets[0].data.push(metrics.actions?.queue_depth || 0);
            queueChart.data.datasets[1].data.push(metrics.events?.queue_depth || 0);

            if (queueChart.data.labels.length > maxPoints) {
                queueChart.data.labels.shift();
                queueChart.data.datasets.forEach(d => d.data.shift());
            }
            queueChart.update('none');

            // Error chart
            errorChart.data.labels.push(now);
            errorChart.data.datasets[0].data.push(metrics.actions?.error_count || 0);

            if (errorChart.data.labels.length > maxPoints) {
                errorChart.data.labels.shift();
                errorChart.data.datasets.forEach(d => d.data.shift());
            }
            errorChart.update('none');
        }

        // Connect on page load
        connect();
    </script>
</body>
</html>"""

    async def broadcast_metrics(self) -> None:
        """Broadcast metrics to all connected clients continuously."""
        while True:
            try:
                if self.clients:
                    metrics = self.collector.get_latest_metrics()

                    # Send to all clients
                    disconnected_clients = set()
                    for ws in self.clients.copy():
                        try:
                            await ws.send_json(metrics)
                        except ConnectionResetError:
                            disconnected_clients.add(ws)
                        except Exception as e:
                            logger.error(f"Error sending to client: {e}")
                            disconnected_clients.add(ws)

                    # Remove disconnected clients
                    self.clients -= disconnected_clients

                await asyncio.sleep(1.0)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in broadcast loop: {e}")
                await asyncio.sleep(1.0)

    async def start_async(self) -> None:
        """Start the dashboard server asynchronously."""
        # Start metrics collector
        self.collector.start()

        # Start broadcast task
        self._broadcast_task = asyncio.create_task(self.broadcast_metrics())

        # Setup and start web server
        self._runner = web.AppRunner(self.app)
        await self._runner.setup()

        site = web.TCPSite(self._runner, self.host, self.port)
        await site.start()

        logger.info(f"Dashboard server started at http://{self.host}:{self.port}")

    async def stop_async(self) -> None:
        """Stop the dashboard server asynchronously."""
        # Cancel broadcast task
        if self._broadcast_task:
            self._broadcast_task.cancel()
            try:
                await self._broadcast_task
            except asyncio.CancelledError:
                pass

        # Close all client connections
        for ws in list(self.clients):
            await ws.close()
        self.clients.clear()

        # Stop web server
        if self._runner:
            await self._runner.cleanup()

        # Stop metrics collector
        self.collector.stop()

        logger.info("Dashboard server stopped")

    def start(self) -> None:
        """Start the dashboard server (blocking).

        This is the main entry point for running the server.
        It will block until interrupted.
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Start server
            loop.run_until_complete(self.start_async())

            # Run forever
            loop.run_forever()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            # Cleanup
            loop.run_until_complete(self.stop_async())
            loop.close()

    def stop(self) -> None:
        """Stop the dashboard server.

        This can be called from another thread to stop the server.
        """
        if asyncio.get_event_loop().is_running():
            asyncio.create_task(self.stop_async())
