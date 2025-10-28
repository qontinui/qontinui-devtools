"""Example: Real-time Performance Dashboard

This example demonstrates how to use the MetricsCollector and DashboardServer
to create a real-time performance monitoring dashboard for your application.

The dashboard displays:
- System resources (CPU, memory, threads)
- Action execution metrics
- Event processing statistics
- Queue depths and error rates

Run this example:
    python examples/performance_dashboard.py

Then open http://localhost:8765 in your browser to view the dashboard.
"""

import time
import random
from threading import Thread

from qontinui_devtools.runtime import DashboardServer, MetricsCollector


def simulate_application_activity(collector: MetricsCollector, duration: int = 300) -> None:
    """Simulate application activity for demo purposes.

    This generates realistic metrics by simulating:
    - Action executions with varying durations
    - Event processing
    - Queue depth changes
    - Occasional errors

    Args:
        collector: MetricsCollector instance to record metrics
        duration: How long to run simulation in seconds
    """
    print("Starting application activity simulation...")

    action_types = [
        "click_button",
        "navigate_page",
        "scroll_viewport",
        "wait_for_element",
        "extract_text",
        "take_screenshot",
    ]

    start_time = time.time()
    action_count = 0

    while time.time() - start_time < duration:
        # Simulate action execution
        action_name = random.choice(action_types)
        action_duration = random.uniform(0.05, 0.5)  # 50-500ms
        success = random.random() > 0.05  # 95% success rate

        # Set current action
        collector.set_current_action(action_name)

        # Simulate work
        time.sleep(action_duration)

        # Record the action
        collector.record_action(action_name, action_duration, success)
        collector.set_current_action(None)

        action_count += 1

        # Simulate action queue depth (varies between 0-10)
        queue_depth = max(0, int(random.gauss(3, 2)))
        collector.set_action_queue_depth(queue_depth)

        # Simulate event processing
        num_events = random.randint(1, 5)
        for _ in range(num_events):
            event_time = random.uniform(0.01, 0.1)
            event_success = random.random() > 0.02  # 98% success rate
            collector.record_event(event_time, event_success)

        # Simulate event queue depth
        event_queue_depth = max(0, int(random.gauss(5, 3)))
        collector.set_event_queue_depth(event_queue_depth)

        # Vary activity rate (faster during bursts)
        if random.random() < 0.1:
            # Burst mode - faster actions
            time.sleep(random.uniform(0.01, 0.1))
        else:
            # Normal mode
            time.sleep(random.uniform(0.2, 1.0))

        # Print progress every 50 actions
        if action_count % 50 == 0:
            elapsed = time.time() - start_time
            rate = action_count / elapsed
            print(f"Simulated {action_count} actions ({rate:.1f}/sec)")

    print(f"Simulation complete: {action_count} actions in {duration}s")


def main() -> None:
    """Run the dashboard server with simulated activity."""
    print("=" * 60)
    print("Qontinui DevTools - Performance Dashboard Example")
    print("=" * 60)
    print()
    print("This example demonstrates the real-time performance dashboard.")
    print("It will:")
    print("  1. Start a metrics collector")
    print("  2. Launch the dashboard web server")
    print("  3. Simulate application activity")
    print()
    print("Dashboard URL: http://localhost:8765")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()

    # Create metrics collector (sample every 1 second)
    collector = MetricsCollector(sample_interval=1.0)

    # Start background thread to simulate activity
    simulator = Thread(
        target=simulate_application_activity,
        args=(collector, 300),  # Run for 5 minutes
        daemon=True
    )
    simulator.start()

    # Create and start dashboard server
    server = DashboardServer(
        host="localhost",
        port=8765,
        metrics_collector=collector
    )

    print("Starting dashboard server...")
    print("Open http://localhost:8765 in your browser")
    print()

    try:
        server.start()
    except KeyboardInterrupt:
        print("\nStopping dashboard...")
        collector.stop()
        print("Dashboard stopped")


if __name__ == "__main__":
    main()
