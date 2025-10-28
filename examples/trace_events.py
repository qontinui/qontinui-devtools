"""Example: Event tracing through the qontinui system.

This example demonstrates how to use the EventTracer to track events
from frontend through Tauri, Python, ActionExecutor, and HAL layers.
"""

import time
import random
from qontinui_devtools.runtime import (
    EventTracer,
    export_chrome_trace,
    export_timeline_html,
    analyze_latencies,
    find_bottleneck,
    detect_anomalies,
    generate_latency_report,
)


def simulate_event_flow(tracer: EventTracer, event_id: str, event_type: str) -> None:
    """Simulate an event flowing through the system."""
    # Start trace
    tracer.start_trace(event_id, event_type)

    # Frontend emits event
    tracer.checkpoint(event_id, "frontend_emit", metadata={
        "component": "Button",
        "action": "click"
    })

    # Small delay for IPC
    time.sleep(random.uniform(0.001, 0.003))

    # Tauri receives event
    tracer.checkpoint(event_id, "tauri_receive", metadata={
        "process": "main",
        "thread": "ipc_handler"
    })

    # Small delay for Python bridge
    time.sleep(random.uniform(0.002, 0.005))

    # Python receives event
    tracer.checkpoint(event_id, "python_receive", metadata={
        "handler": "event_dispatcher"
    })

    # Processing delay
    time.sleep(random.uniform(0.005, 0.015))

    # ActionExecutor starts processing
    tracer.checkpoint(event_id, "executor_start", metadata={
        "action_type": event_type,
        "queue_depth": random.randint(0, 5)
    })

    # HAL call delay (typically the slowest part)
    time.sleep(random.uniform(0.020, 0.100))

    # HAL operation
    tracer.checkpoint(event_id, "hal_call", metadata={
        "operation": "move_mouse" if event_type == "click" else "key_press",
        "target": f"x={random.randint(0, 1920)}, y={random.randint(0, 1080)}"
    })

    time.sleep(random.uniform(0.001, 0.005))

    tracer.checkpoint(event_id, "hal_complete", metadata={
        "status": "success"
    })

    # Executor completes
    time.sleep(random.uniform(0.002, 0.008))
    tracer.checkpoint(event_id, "executor_complete")

    # Response travels back
    time.sleep(random.uniform(0.001, 0.003))
    tracer.checkpoint(event_id, "python_send")

    time.sleep(random.uniform(0.001, 0.003))
    tracer.checkpoint(event_id, "tauri_send")

    time.sleep(random.uniform(0.001, 0.002))
    tracer.checkpoint(event_id, "frontend_receive")

    # Complete the trace
    tracer.complete_trace(event_id)


def main():
    """Run event tracing example."""
    print("=" * 60)
    print("Event Tracer Example")
    print("=" * 60)
    print()

    # Create tracer
    tracer = EventTracer(max_traces=100)

    # Simulate various events
    event_types = ["click", "keypress", "scroll", "drag"]
    num_events = 20

    print(f"Simulating {num_events} events...")
    for i in range(num_events):
        event_id = f"evt_{i:03d}"
        event_type = random.choice(event_types)

        simulate_event_flow(tracer, event_id, event_type)

        # Small delay between events
        time.sleep(0.01)

        # Progress indicator
        if (i + 1) % 5 == 0:
            print(f"  Traced {i + 1}/{num_events} events")

    print(f"✓ Completed tracing {num_events} events")
    print()

    # Analyze flow
    print("=" * 60)
    print("Event Flow Analysis")
    print("=" * 60)
    print()

    flow = tracer.analyze_flow()

    print(f"Total Events:      {flow.total_events}")
    print(f"Completed Events:  {flow.completed_events}")
    print(f"Lost Events:       {flow.lost_events}")
    print(f"Avg Latency:       {flow.avg_latency * 1000:.2f}ms")
    print(f"P95 Latency:       {flow.p95_latency * 1000:.2f}ms")
    print(f"P99 Latency:       {flow.p99_latency * 1000:.2f}ms")
    print(f"Bottleneck Stage:  {flow.bottleneck_stage}")
    print()

    # Stage latencies
    print("=" * 60)
    print("Stage Latencies")
    print("=" * 60)
    print()

    latencies = analyze_latencies(tracer.get_all_traces())

    # Sort by mean latency (descending)
    sorted_stages = sorted(
        latencies.items(),
        key=lambda x: x[1]["mean"],
        reverse=True
    )

    for stage, stats in sorted_stages:
        if "trace_start" in stage:
            continue  # Skip internal checkpoint

        print(f"{stage}")
        print(f"  Mean:  {stats['mean'] * 1000:6.2f}ms")
        print(f"  P50:   {stats['p50'] * 1000:6.2f}ms")
        print(f"  P95:   {stats['p95'] * 1000:6.2f}ms")
        print(f"  P99:   {stats['p99'] * 1000:6.2f}ms")
        print(f"  Min:   {stats['min'] * 1000:6.2f}ms")
        print(f"  Max:   {stats['max'] * 1000:6.2f}ms")
        print(f"  Count: {stats['count']}")
        print()

    # Bottleneck analysis
    print("=" * 60)
    print("Bottleneck Analysis")
    print("=" * 60)
    print()

    bottleneck = find_bottleneck(tracer.get_all_traces())
    print(f"Primary Bottleneck: {bottleneck}")

    if bottleneck in latencies:
        stats = latencies[bottleneck]
        print(f"  This stage accounts for {stats['mean'] * 1000:.2f}ms on average")
        print(f"  P95: {stats['p95'] * 1000:.2f}ms")
        print(f"  Recommendation: Optimize this stage to improve overall latency")
    print()

    # Detect anomalies
    print("=" * 60)
    print("Anomaly Detection")
    print("=" * 60)
    print()

    anomalies = detect_anomalies(tracer.get_all_traces(), threshold=1.5)

    if anomalies:
        print(f"Found {len(anomalies)} anomalous events:")
        print()

        for event_id, trace, stage in anomalies[:5]:  # Show first 5
            stage_latency = trace.get_stage_latencies().get(stage, 0.0)
            avg_latency = latencies[stage]["mean"]
            factor = stage_latency / avg_latency if avg_latency > 0 else 0

            print(f"  {event_id} ({trace.event_type})")
            print(f"    Slow stage: {stage}")
            print(f"    Latency: {stage_latency * 1000:.2f}ms ({factor:.1f}x average)")
            print()

        if len(anomalies) > 5:
            print(f"  ... and {len(anomalies) - 5} more anomalies")
    else:
        print("No anomalies detected (all events within normal range)")
    print()

    # Lost events
    print("=" * 60)
    print("Lost Events")
    print("=" * 60)
    print()

    lost = tracer.find_lost_events(timeout=0.5)

    if lost:
        print(f"Found {len(lost)} lost events:")
        for trace in lost:
            print(f"  {trace.event_id} ({trace.event_type})")
            print(f"    Last checkpoint: {trace.checkpoints[-1].name if trace.checkpoints else 'N/A'}")
            print(f"    Age: {time.time() - trace.created_at:.2f}s")
    else:
        print("No lost events detected")
    print()

    # Export timeline
    print("=" * 60)
    print("Exporting Timelines")
    print("=" * 60)
    print()

    # Chrome trace format
    chrome_trace_path = "event_timeline.json"
    export_chrome_trace(tracer.get_all_traces(), chrome_trace_path)
    print(f"✓ Chrome trace saved to: {chrome_trace_path}")
    print(f"  Open in chrome://tracing or https://ui.perfetto.dev/")
    print()

    # HTML timeline
    html_timeline_path = "event_timeline.html"
    export_timeline_html(tracer.get_all_traces(), html_timeline_path)
    print(f"✓ HTML timeline saved to: {html_timeline_path}")
    print(f"  Open in your browser to view interactive timeline")
    print()

    # Generate detailed report
    print("=" * 60)
    print("Generating Detailed Report")
    print("=" * 60)
    print()

    report = generate_latency_report(tracer.get_all_traces())
    print(report)

    # Save report to file
    report_path = "latency_report.txt"
    with open(report_path, 'w') as f:
        f.write(report)
    print()
    print(f"✓ Report saved to: {report_path}")
    print()

    # Example: Comparing two specific traces
    print("=" * 60)
    print("Trace Comparison Example")
    print("=" * 60)
    print()

    if len(tracer.get_all_traces()) >= 2:
        from qontinui_devtools.runtime import compare_traces

        trace1 = tracer.get_trace("evt_000")
        trace2 = tracer.get_trace("evt_001")

        if trace1 and trace2:
            comparison = compare_traces(trace1, trace2)

            print(f"Comparing {trace1.event_id} vs {trace2.event_id}:")
            print()

            for stage, stats in comparison.items():
                if "trace_start" in stage:
                    continue

                print(f"{stage}")
                print(f"  Trace 1: {stats['trace1'] * 1000:.2f}ms")
                print(f"  Trace 2: {stats['trace2'] * 1000:.2f}ms")
                print(f"  Diff:    {stats['diff'] * 1000:+.2f}ms ({stats['diff_pct']:+.1f}%)")
                print()

    print("=" * 60)
    print("Example Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
