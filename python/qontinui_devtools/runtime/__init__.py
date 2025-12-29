"""Runtime analysis and tracing tools for Qontinui.

This module provides event tracing, latency analysis, timeline visualization,
action profiling, real-time performance monitoring, and memory profiling for
tracking events through the Qontinui system.
"""

from .action_profiler import ActionProfile, ActionProfiler, ProfilingSession
from .dashboard_server import DashboardServer
from .event_tracer import Checkpoint, EventFlow, EventTrace, EventTracer
from .latency_analyzer import (
                               analyze_latencies,
                               calculate_throughput,
                               compare_traces,
                               detect_anomalies,
                               find_bottleneck,
                               generate_latency_report,
)
from .leak_detector import (
                               analyze_growth_trend,
                               analyze_object_retention,
                               classify_leak_severity,
                               detect_common_leak_patterns,
                               find_cycles_containing,
                               find_leaked_objects,
                               find_reference_chains,
                               get_object_size_deep,
                               suggest_fixes,
)

# Memory profiling
from .memory_profiler import MemoryLeak, MemoryProfiler, MemorySnapshot
from .memory_viz import (
                               generate_html_report,
                               plot_comparison,
                               plot_leak_heatmap,
                               plot_memory_timeline,
                               plot_object_growth,
                               plot_top_objects,
)
from .metrics import (
                               PerformanceMetrics,
                               calculate_action_type_metrics,
                               calculate_metrics,
                               calculate_percentile,
                               calculate_phase_metrics,
                               format_duration,
                               format_memory,
)
from .metrics_collector import ActionMetrics, EventMetrics, MetricsCollector, SystemMetrics
from .timeline import export_chrome_trace, export_timeline_html

__all__ = [
    # Event tracing
    "EventTracer",
    "EventTrace",
    "EventFlow",
    "Checkpoint",
    # Latency analysis
    "analyze_latencies",
    "find_bottleneck",
    "detect_anomalies",
    "calculate_throughput",
    "compare_traces",
    "generate_latency_report",
    # Timeline export
    "export_chrome_trace",
    "export_timeline_html",
    # Action profiling
    "ActionProfiler",
    "ActionProfile",
    "ProfilingSession",
    "PerformanceMetrics",
    "calculate_metrics",
    "calculate_percentile",
    "calculate_phase_metrics",
    "calculate_action_type_metrics",
    "format_duration",
    "format_memory",
    # Real-time monitoring
    "MetricsCollector",
    "DashboardServer",
    "SystemMetrics",
    "ActionMetrics",
    "EventMetrics",
    # Memory profiling
    "MemoryProfiler",
    "MemorySnapshot",
    "MemoryLeak",
    "analyze_growth_trend",
    "find_reference_chains",
    "find_leaked_objects",
    "classify_leak_severity",
    "analyze_object_retention",
    "find_cycles_containing",
    "get_object_size_deep",
    "detect_common_leak_patterns",
    "suggest_fixes",
    "plot_memory_timeline",
    "plot_object_growth",
    "plot_top_objects",
    "plot_leak_heatmap",
    "plot_comparison",
    "generate_html_report",
]
