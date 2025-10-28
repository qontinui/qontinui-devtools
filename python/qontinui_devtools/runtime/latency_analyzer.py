"""Latency analysis utilities for event traces.

This module provides advanced latency analysis including percentile calculations,
bottleneck detection, and anomaly detection.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .event_tracer import EventTrace


def analyze_latencies(
    traces: list["EventTrace"]
) -> dict[str, dict[str, float]]:
    """Analyze latencies between all checkpoint pairs.

    Args:
        traces: List of EventTrace instances

    Returns:
        Dictionary mapping stage names to latency statistics:
        {
            "frontend_emit -> tauri_receive": {
                "mean": 2.5,
                "p50": 2.1,
                "p95": 5.0,
                "p99": 8.3,
                "min": 1.2,
                "max": 10.5,
                "count": 100
            },
            ...
        }

    Example:
        >>> tracer = EventTracer()
        >>> # ... trace some events ...
        >>> latencies = analyze_latencies(tracer.get_all_traces())
        >>> print(f"P95: {latencies['frontend_emit -> tauri_receive']['p95']:.3f}s")
    """
    # Collect latencies for each stage
    stage_latencies: dict[str, list[float]] = {}

    for trace in traces:
        for stage, latency in trace.get_stage_latencies().items():
            if stage not in stage_latencies:
                stage_latencies[stage] = []
            stage_latencies[stage].append(latency)

    # Calculate statistics for each stage
    result = {}

    for stage, latencies in stage_latencies.items():
        if not latencies:
            continue

        sorted_latencies = sorted(latencies)
        n = len(sorted_latencies)

        result[stage] = {
            "mean": sum(latencies) / n,
            "p50": sorted_latencies[int(n * 0.50)],
            "p95": sorted_latencies[int(n * 0.95)] if n > 1 else sorted_latencies[0],
            "p99": sorted_latencies[int(n * 0.99)] if n > 1 else sorted_latencies[0],
            "min": sorted_latencies[0],
            "max": sorted_latencies[-1],
            "count": n
        }

    return result


def find_bottleneck(traces: list["EventTrace"]) -> str:
    """Identify the slowest stage in event processing.

    Args:
        traces: List of EventTrace instances

    Returns:
        Name of the bottleneck stage

    Example:
        >>> tracer = EventTracer()
        >>> # ... trace some events ...
        >>> bottleneck = find_bottleneck(tracer.get_all_traces())
        >>> print(f"Bottleneck: {bottleneck}")
    """
    latencies = analyze_latencies(traces)

    if not latencies:
        return "N/A"

    # Find stage with highest mean latency
    bottleneck = max(latencies.items(), key=lambda x: x[1]["mean"])
    return bottleneck[0]


def detect_anomalies(
    traces: list["EventTrace"],
    threshold: float = 2.0  # 2x average
) -> list[tuple[str, "EventTrace", str]]:
    """Detect anomalously slow events.

    An event is considered anomalous if any of its stages take longer
    than threshold * average for that stage.

    Args:
        traces: List of EventTrace instances
        threshold: Multiplier threshold (default: 2.0 = 2x average)

    Returns:
        List of tuples: [(event_id, trace, slow_stage), ...]

    Example:
        >>> tracer = EventTracer()
        >>> # ... trace some events ...
        >>> anomalies = detect_anomalies(tracer.get_all_traces(), threshold=3.0)
        >>> for event_id, trace, stage in anomalies:
        ...     print(f"Slow event {event_id} at {stage}")
    """
    latencies = analyze_latencies(traces)

    if not latencies:
        return []

    anomalies = []

    for trace in traces:
        for stage, latency in trace.get_stage_latencies().items():
            if stage in latencies:
                avg_latency = latencies[stage]["mean"]

                if latency > avg_latency * threshold:
                    anomalies.append((trace.event_id, trace, stage))
                    break  # Only report once per trace

    return anomalies


def calculate_throughput(
    traces: list["EventTrace"],
    window_seconds: float = 1.0
) -> dict[str, float]:
    """Calculate event throughput over time windows.

    Args:
        traces: List of EventTrace instances
        window_seconds: Window size in seconds

    Returns:
        Dictionary mapping timestamps to events per second:
        {
            "1698765432.0": 10.5,
            "1698765433.0": 12.3,
            ...
        }

    Example:
        >>> tracer = EventTracer()
        >>> # ... trace some events ...
        >>> throughput = calculate_throughput(tracer.get_all_traces())
        >>> avg_tps = sum(throughput.values()) / len(throughput)
        >>> print(f"Average throughput: {avg_tps:.2f} events/sec")
    """
    if not traces:
        return {}

    # Find time range
    min_time = min(t.created_at for t in traces)
    max_time = max(t.created_at for t in traces)

    # Create time windows
    windows = {}
    current_time = min_time

    while current_time <= max_time:
        window_key = f"{current_time:.1f}"
        window_end = current_time + window_seconds

        # Count events in this window
        count = sum(
            1 for t in traces
            if current_time <= t.created_at < window_end
        )

        windows[window_key] = count / window_seconds
        current_time = window_end

    return windows


def compare_traces(
    trace1: "EventTrace",
    trace2: "EventTrace"
) -> dict[str, dict[str, float]]:
    """Compare two traces and show latency differences.

    Args:
        trace1: First EventTrace
        trace2: Second EventTrace

    Returns:
        Dictionary showing latency comparison:
        {
            "frontend_emit -> tauri_receive": {
                "trace1": 2.5,
                "trace2": 3.1,
                "diff": 0.6,
                "diff_pct": 24.0
            },
            ...
        }

    Example:
        >>> tracer = EventTracer()
        >>> trace1 = tracer.get_trace("evt_001")
        >>> trace2 = tracer.get_trace("evt_002")
        >>> comparison = compare_traces(trace1, trace2)
    """
    latencies1 = trace1.get_stage_latencies()
    latencies2 = trace2.get_stage_latencies()

    # Find common stages
    common_stages = set(latencies1.keys()) & set(latencies2.keys())

    result = {}

    for stage in common_stages:
        lat1 = latencies1[stage]
        lat2 = latencies2[stage]
        diff = lat2 - lat1
        diff_pct = (diff / lat1 * 100) if lat1 > 0 else 0.0

        result[stage] = {
            "trace1": lat1,
            "trace2": lat2,
            "diff": diff,
            "diff_pct": diff_pct
        }

    return result


def generate_latency_report(traces: list["EventTrace"]) -> str:
    """Generate a human-readable latency report.

    Args:
        traces: List of EventTrace instances

    Returns:
        Multi-line string report

    Example:
        >>> tracer = EventTracer()
        >>> # ... trace some events ...
        >>> report = generate_latency_report(tracer.get_all_traces())
        >>> print(report)
    """
    if not traces:
        return "No traces to analyze."

    latencies = analyze_latencies(traces)
    bottleneck = find_bottleneck(traces)
    anomalies = detect_anomalies(traces)

    lines = [
        "=" * 60,
        "LATENCY ANALYSIS REPORT",
        "=" * 60,
        "",
        f"Total Events: {len(traces)}",
        f"Completed Events: {sum(1 for t in traces if t.completed)}",
        f"Bottleneck Stage: {bottleneck}",
        f"Anomalies Detected: {len(anomalies)}",
        "",
        "=" * 60,
        "STAGE LATENCIES",
        "=" * 60,
        ""
    ]

    # Sort stages by mean latency (descending)
    sorted_stages = sorted(
        latencies.items(),
        key=lambda x: x[1]["mean"],
        reverse=True
    )

    for stage, stats in sorted_stages:
        lines.append(f"\n{stage}")
        lines.append("-" * 60)
        lines.append(f"  Count:  {stats['count']}")
        lines.append(f"  Mean:   {stats['mean'] * 1000:.2f}ms")
        lines.append(f"  P50:    {stats['p50'] * 1000:.2f}ms")
        lines.append(f"  P95:    {stats['p95'] * 1000:.2f}ms")
        lines.append(f"  P99:    {stats['p99'] * 1000:.2f}ms")
        lines.append(f"  Min:    {stats['min'] * 1000:.2f}ms")
        lines.append(f"  Max:    {stats['max'] * 1000:.2f}ms")

    if anomalies:
        lines.append("")
        lines.append("=" * 60)
        lines.append("ANOMALIES")
        lines.append("=" * 60)
        lines.append("")

        for event_id, trace, stage in anomalies[:10]:  # Show first 10
            stage_latency = trace.get_stage_latencies().get(stage, 0.0)
            avg_latency = latencies[stage]["mean"]
            factor = stage_latency / avg_latency if avg_latency > 0 else 0

            lines.append(f"  {event_id}: {stage}")
            lines.append(f"    Latency: {stage_latency * 1000:.2f}ms ({factor:.1f}x average)")

        if len(anomalies) > 10:
            lines.append(f"  ... and {len(anomalies) - 10} more")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)
