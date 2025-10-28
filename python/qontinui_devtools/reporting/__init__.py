"""
Reporting tools for qontinui-devtools.

This package provides comprehensive HTML report generation that aggregates
results from all analysis tools into a single interactive document.

Example:
    >>> from qontinui_devtools.reporting import ReportAggregator, HTMLReportGenerator
    >>> aggregator = ReportAggregator("../qontinui/src")
    >>> report_data = aggregator.run_all_analyses()
    >>> generator = HTMLReportGenerator()
    >>> generator.generate(report_data, "analysis_report.html")
"""

from .aggregator import ReportAggregator
from .html_reporter import HTMLReportGenerator, ReportData, ReportSection
from .charts import (
    create_bar_chart,
    create_pie_chart,
    create_doughnut_chart,
    create_line_chart,
    create_scatter_chart,
    create_stacked_bar_chart,
    create_radar_chart,
    create_multi_axis_chart,
)

__all__ = [
    # Core reporting
    "HTMLReportGenerator",
    "ReportData",
    "ReportSection",
    "ReportAggregator",
    # Chart functions
    "create_bar_chart",
    "create_pie_chart",
    "create_doughnut_chart",
    "create_line_chart",
    "create_scatter_chart",
    "create_stacked_bar_chart",
    "create_radar_chart",
    "create_multi_axis_chart",
]

__version__ = "1.0.0"
