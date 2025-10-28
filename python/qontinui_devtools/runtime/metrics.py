"""Performance metrics calculation for action profiling.

This module provides utilities for calculating aggregate performance metrics
from action profiles, including percentiles, averages, and statistics.
"""

from dataclasses import dataclass

from .action_profiler import ActionProfile


@dataclass
class PerformanceMetrics:
    """Aggregated performance metrics from multiple action profiles."""

    total_actions: int
    total_duration: float
    avg_duration: float
    min_duration: float
    max_duration: float
    p50_duration: float  # Median
    p95_duration: float
    p99_duration: float
    total_cpu_time: float
    avg_cpu_time: float
    cpu_utilization: float  # CPU time / wall time
    total_memory_delta: int
    avg_memory_delta: int
    peak_memory: int
    actions_per_second: float
    slowest_actions: list[tuple[str, float]]  # (action_id, duration)
    fastest_actions: list[tuple[str, float]]  # (action_id, duration)
    failed_actions: int
    success_rate: float


def calculate_percentile(values: list[float], percentile: float) -> float:
    """Calculate percentile value from a list of numbers.

    Args:
        values: List of numeric values
        percentile: Percentile to calculate (0-100)

    Returns:
        Percentile value

    Raises:
        ValueError: If values is empty or percentile is out of range
    """
    if not values:
        raise ValueError("Cannot calculate percentile of empty list")

    if not 0 <= percentile <= 100:
        raise ValueError("Percentile must be between 0 and 100")

    sorted_values = sorted(values)
    n = len(sorted_values)

    if percentile == 0:
        return sorted_values[0]
    if percentile == 100:
        return sorted_values[-1]

    # Use linear interpolation between closest ranks
    rank = (percentile / 100) * (n - 1)
    lower_index = int(rank)
    upper_index = min(lower_index + 1, n - 1)
    fraction = rank - lower_index

    lower_value = sorted_values[lower_index]
    upper_value = sorted_values[upper_index]

    return lower_value + fraction * (upper_value - lower_value)


def calculate_metrics(profiles: list[ActionProfile]) -> PerformanceMetrics:
    """Calculate aggregate metrics from a list of action profiles.

    Args:
        profiles: List of ActionProfile objects to analyze

    Returns:
        PerformanceMetrics with calculated statistics

    Raises:
        ValueError: If profiles list is empty
    """
    if not profiles:
        raise ValueError("Cannot calculate metrics from empty profile list")

    # Basic counts
    total_actions = len(profiles)
    failed_actions = sum(1 for p in profiles if not p.success)
    success_rate = (total_actions - failed_actions) / total_actions

    # Duration metrics
    durations = [p.duration for p in profiles]
    total_duration = sum(durations)
    avg_duration = total_duration / total_actions
    min_duration = min(durations)
    max_duration = max(durations)

    # Percentiles
    p50_duration = calculate_percentile(durations, 50)
    p95_duration = calculate_percentile(durations, 95)
    p99_duration = calculate_percentile(durations, 99)

    # CPU metrics
    cpu_times = [p.cpu_time for p in profiles]
    total_cpu_time = sum(cpu_times)
    avg_cpu_time = total_cpu_time / total_actions
    cpu_utilization = (total_cpu_time / total_duration) if total_duration > 0 else 0.0

    # Memory metrics
    memory_deltas = [p.memory_delta for p in profiles]
    total_memory_delta = sum(memory_deltas)
    avg_memory_delta = total_memory_delta // total_actions
    peak_memory = max(p.peak_memory for p in profiles)

    # Throughput
    actions_per_second = total_actions / total_duration if total_duration > 0 else 0.0

    # Slowest/fastest actions
    sorted_by_duration = sorted(profiles, key=lambda p: p.duration, reverse=True)
    slowest_actions = [
        (p.action_id, p.duration) for p in sorted_by_duration[:10]
    ]  # Top 10

    sorted_by_duration_asc = sorted(profiles, key=lambda p: p.duration)
    fastest_actions = [
        (p.action_id, p.duration) for p in sorted_by_duration_asc[:10]
    ]  # Bottom 10

    return PerformanceMetrics(
        total_actions=total_actions,
        total_duration=total_duration,
        avg_duration=avg_duration,
        min_duration=min_duration,
        max_duration=max_duration,
        p50_duration=p50_duration,
        p95_duration=p95_duration,
        p99_duration=p99_duration,
        total_cpu_time=total_cpu_time,
        avg_cpu_time=avg_cpu_time,
        cpu_utilization=cpu_utilization,
        total_memory_delta=total_memory_delta,
        avg_memory_delta=avg_memory_delta,
        peak_memory=peak_memory,
        actions_per_second=actions_per_second,
        slowest_actions=slowest_actions,
        fastest_actions=fastest_actions,
        failed_actions=failed_actions,
        success_rate=success_rate,
    )


def calculate_phase_metrics(profiles: list[ActionProfile]) -> dict[str, dict[str, float]]:
    """Calculate metrics for each phase across all actions.

    Args:
        profiles: List of ActionProfile objects

    Returns:
        Dictionary mapping phase names to their metrics (avg, min, max, total)
    """
    phase_data: dict[str, list[float]] = {}

    # Collect all phase timings
    for profile in profiles:
        for phase_name, phase_duration in profile.phases.items():
            if phase_name not in phase_data:
                phase_data[phase_name] = []
            phase_data[phase_name].append(phase_duration)

    # Calculate metrics for each phase
    phase_metrics: dict[str, dict[str, float]] = {}
    for phase_name, durations in phase_data.items():
        if durations:
            phase_metrics[phase_name] = {
                "count": len(durations),
                "total": sum(durations),
                "avg": sum(durations) / len(durations),
                "min": min(durations),
                "max": max(durations),
                "p50": calculate_percentile(durations, 50),
                "p95": calculate_percentile(durations, 95),
            }

    return phase_metrics


def calculate_action_type_metrics(
    profiles: list[ActionProfile],
) -> dict[str, PerformanceMetrics]:
    """Calculate separate metrics for each action type.

    Args:
        profiles: List of ActionProfile objects

    Returns:
        Dictionary mapping action types to their metrics
    """
    # Group profiles by action type
    by_type: dict[str, list[ActionProfile]] = {}
    for profile in profiles:
        if profile.action_type not in by_type:
            by_type[profile.action_type] = []
        by_type[profile.action_type].append(profile)

    # Calculate metrics for each type
    type_metrics: dict[str, PerformanceMetrics] = {}
    for action_type, type_profiles in by_type.items():
        type_metrics[action_type] = calculate_metrics(type_profiles)

    return type_metrics


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "1.234s", "123.4ms", "12.34μs")
    """
    if seconds >= 1.0:
        return f"{seconds:.3f}s"
    elif seconds >= 0.001:
        return f"{seconds * 1000:.1f}ms"
    elif seconds >= 0.000001:
        return f"{seconds * 1000000:.1f}μs"
    else:
        return f"{seconds * 1000000000:.0f}ns"


def format_memory(bytes_value: int) -> str:
    """Format memory size in human-readable format.

    Args:
        bytes_value: Memory size in bytes

    Returns:
        Formatted string (e.g., "1.23 GB", "456 MB", "789 KB")
    """
    if bytes_value >= 1024**3:
        return f"{bytes_value / (1024**3):.2f} GB"
    elif bytes_value >= 1024**2:
        return f"{bytes_value / (1024**2):.2f} MB"
    elif bytes_value >= 1024:
        return f"{bytes_value / 1024:.2f} KB"
    else:
        return f"{bytes_value} B"
