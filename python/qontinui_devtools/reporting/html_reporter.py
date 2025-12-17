"""
HTML Report Generator for qontinui-devtools.

Generates comprehensive, interactive HTML reports aggregating results from all analysis tools.
"""

import html
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, PackageLoader, TemplateNotFound, select_autoescape


@dataclass
class ReportSection:
    """A section in the HTML report."""

    id: str
    title: str
    content: str  # HTML content
    severity: str  # "success", "warning", "error", "info"
    metrics: dict[str, Any] = field(default_factory=dict)
    chart_data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate severity level."""
        valid_severities = {"success", "warning", "error", "info"}
        if self.severity not in valid_severities:
            raise ValueError(
                f"Invalid severity '{self.severity}'. Must be one of: {valid_severities}"
            )


@dataclass
class ReportData:
    """Aggregated data for report generation."""

    project_name: str
    analysis_date: datetime
    sections: list[ReportSection] = field(default_factory=list)
    summary_metrics: dict[str, Any] = field(default_factory=dict)
    charts_data: dict[str, Any] = field(default_factory=dict)
    project_path: str = ""
    version: str = "1.0.0"

    def add_section(self, section: ReportSection) -> None:
        """Add a section to the report."""
        self.sections.append(section)

    def get_section(self, section_id: str) -> ReportSection | None:
        """Get a section by ID."""
        for section in self.sections:
            if section.id == section_id:
                return section
        return None

    def get_overall_status(self) -> tuple[str, str, str]:
        """
        Get overall status of the report.

        Returns:
            Tuple of (status_color, status_icon, status_message)
        """
        error_count = sum(1 for s in self.sections if s.severity == "error")
        warning_count = sum(1 for s in self.sections if s.severity == "warning")

        if error_count > 0:
            return (
                "red",
                "❌",
                f"Critical Issues Found ({error_count} errors, {warning_count} warnings)",
            )
        elif warning_count > 5:
            return (
                "yellow",
                "⚠️",
                f"Warnings Detected ({warning_count} warnings need attention)",
            )
        elif warning_count > 0:
            return (
                "green",
                "✅",
                f"Good with Minor Issues ({warning_count} warnings)",
            )
        else:
            return ("green", "✅", "All Checks Passed - Excellent Code Quality!")


class HTMLReportGenerator:
    """Generate comprehensive HTML reports."""

    def __init__(self, verbose: bool = False) -> None:
        """
        Initialize the HTML report generator.

        Args:
            verbose: Enable verbose logging
        """
        self.verbose = verbose
        self.env = self._setup_jinja_env()
        self.report_data: ReportData | None = None

    def _setup_jinja_env(self) -> Environment:
        """Set up Jinja2 environment."""
        try:
            # Try to load from package
            env = Environment(
                loader=PackageLoader("qontinui_devtools.reporting", "templates"),
                autoescape=select_autoescape(["html", "xml"]),
            )
        except (ImportError, ModuleNotFoundError):
            # Fallback to file system loader
            from jinja2 import FileSystemLoader

            templates_dir = Path(__file__).parent / "templates"
            templates_dir.mkdir(exist_ok=True)
            env = Environment(
                loader=FileSystemLoader(str(templates_dir)),
                autoescape=select_autoescape(["html", "xml"]),
            )

        # Add custom filters
        env.filters["tojson_safe"] = self._tojson_safe
        env.filters["format_datetime"] = self._format_datetime
        env.filters["format_number"] = self._format_number

        return env

    @staticmethod
    def _tojson_safe(obj: Any) -> str:
        """Convert object to JSON safely for use in JavaScript."""
        return json.dumps(obj)

    @staticmethod
    def _format_datetime(dt: datetime) -> str:
        """Format datetime for display."""
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _format_number(num: int | float) -> str:
        """Format number with thousands separator."""
        return f"{num:,}"

    def generate(
        self, report_data: ReportData, output_path: str, template: str = "default"
    ) -> None:
        """
        Generate HTML report.

        Args:
            report_data: The report data to generate from
            output_path: Path to save the HTML report
            template: Template name to use (default: "default")
        """
        self.report_data = report_data

        if self.verbose:
            print(f"Generating HTML report: {output_path}")
            print(f"Project: {report_data.project_name}")
            print(f"Sections: {len(report_data.sections)}")

        # Generate HTML content
        html_content = self._generate_html(template)

        # Write to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(html_content, encoding="utf-8")

        if self.verbose:
            print(f"Report generated: {output_file.absolute()}")
            print(f"File size: {output_file.stat().st_size:,} bytes")

    def _generate_html(self, template: str) -> str:
        """
        Generate HTML content from template.

        Args:
            template: Template name

        Returns:
            HTML content as string
        """
        if not self.report_data:
            raise ValueError("No report data set")

        # Prepare context
        context = self._prepare_context()

        # Try to load custom template, fallback to inline template
        try:
            tmpl = self.env.get_template(f"{template}.html")
            return tmpl.render(**context)
        except TemplateNotFound:
            # Use inline template
            return self._generate_inline_html(context)

    def _prepare_context(self) -> dict[str, Any]:
        """Prepare template context."""
        if not self.report_data:
            raise ValueError("No report data set")

        status_color, status_icon, status_message = self.report_data.get_overall_status()

        return {
            "project_name": self.report_data.project_name,
            "project_path": self.report_data.project_path,
            "analysis_date": self.report_data.analysis_date,
            "version": self.report_data.version,
            "sections": self.report_data.sections,
            "summary_metrics": self.report_data.summary_metrics,
            "charts_data": self.report_data.charts_data,
            "overall_status_color": status_color,
            "overall_status_icon": status_icon,
            "overall_status_message": status_message,
            "key_metrics": self._prepare_key_metrics(),
        }

    def _prepare_key_metrics(self) -> list[dict[str, Any]]:
        """Prepare key metrics for summary cards."""
        metrics: list[Any] = []

        data = self.report_data
        if not data:
            return metrics

        # Total issues
        error_count = sum(1 for s in data.sections if s.severity == "error")
        warning_count = sum(1 for s in data.sections if s.severity == "warning")
        total_issues = error_count + warning_count

        metrics.append(
            {
                "name": "Total Issues",
                "value": total_issues,
                "color": "red" if error_count > 0 else ("yellow" if warning_count > 0 else "green"),
                "description": f"{error_count} errors, {warning_count} warnings",
            }
        )

        # Files analyzed
        files_analyzed = data.summary_metrics.get("files_analyzed", 0)
        metrics.append(
            {
                "name": "Files Analyzed",
                "value": files_analyzed,
                "color": "blue",
                "description": "Source files scanned",
            }
        )

        # Code quality score (0-100)
        quality_score = self._calculate_quality_score()
        metrics.append(
            {
                "name": "Quality Score",
                "value": f"{quality_score:.1f}/100",
                "color": (
                    "green" if quality_score >= 80 else ("yellow" if quality_score >= 60 else "red")
                ),
                "description": "Overall code quality rating",
            }
        )

        # Critical findings
        critical_count = data.summary_metrics.get("critical_issues", error_count)
        metrics.append(
            {
                "name": "Critical Issues",
                "value": critical_count,
                "color": "red" if critical_count > 0 else "green",
                "description": "Issues requiring immediate attention",
            }
        )

        return metrics

    def _calculate_quality_score(self) -> float:
        """
        Calculate overall quality score (0-100).

        Based on various factors weighted by importance.
        """
        if not self.report_data:
            return 0.0

        score = 100.0

        # Deduct for errors (10 points each, max -50)
        error_count = sum(1 for s in self.report_data.sections if s.severity == "error")
        score -= min(error_count * 10, 50)

        # Deduct for warnings (2 points each, max -20)
        warning_count = sum(1 for s in self.report_data.sections if s.severity == "warning")
        score -= min(warning_count * 2, 20)

        # Deduct for specific issues
        metrics = self.report_data.summary_metrics

        # Circular dependencies (5 points each, max -15)
        circular_deps = metrics.get("circular_dependencies", 0)
        score -= min(circular_deps * 5, 15)

        # God classes (8 points each, max -15)
        god_classes = metrics.get("god_classes", 0)
        score -= min(god_classes * 8, 15)

        # Race conditions (10 points each, max -20)
        race_conditions = metrics.get("race_conditions", 0)
        score -= min(race_conditions * 10, 20)

        return max(score, 0.0)

    def _generate_inline_html(self, context: dict[str, Any]) -> str:
        """Generate HTML using inline template (fallback)."""
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(context['project_name'])} - Code Quality Report</title>

    <!-- Chart.js for visualizations -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>

    <!-- Tailwind CSS for styling -->
    <script src="https://cdn.tailwindcss.com"></script>

    <style>
        .metric-card {{
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .metric-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
        }}
        .severity-error {{
            background-color: #fee2e2;
            border-left-color: #dc2626;
        }}
        .severity-warning {{
            background-color: #fef3c7;
            border-left-color: #f59e0b;
        }}
        .severity-success {{
            background-color: #d1fae5;
            border-left-color: #10b981;
        }}
        .severity-info {{
            background-color: #dbeafe;
            border-left-color: #3b82f6;
        }}
        .nav-link {{
            padding: 1rem 1.5rem;
            text-decoration: none;
            color: #4b5563;
            font-weight: 500;
            transition: color 0.2s, background-color 0.2s;
            display: block;
        }}
        .nav-link:hover {{
            color: #2563eb;
            background-color: #f3f4f6;
        }}
        .nav-link.active {{
            color: #2563eb;
            border-bottom: 2px solid #2563eb;
        }}
        .section-content {{
            line-height: 1.8;
        }}
        .section-content h3 {{
            margin-top: 1.5rem;
            margin-bottom: 1rem;
            font-size: 1.25rem;
            font-weight: 600;
        }}
        .section-content ul {{
            margin-left: 1.5rem;
            margin-bottom: 1rem;
        }}
        .section-content li {{
            margin-bottom: 0.5rem;
        }}
        .section-content code {{
            background-color: #f3f4f6;
            padding: 0.125rem 0.375rem;
            border-radius: 0.25rem;
            font-family: 'Courier New', monospace;
            font-size: 0.875rem;
        }}
        .chart-container {{
            position: relative;
            height: 300px;
        }}
    </style>
</head>
<body class="bg-gray-100">
    <!-- Header -->
    <header class="bg-gradient-to-r from-blue-600 to-blue-800 text-white p-6 shadow-lg">
        <div class="container mx-auto">
            <h1 class="text-4xl font-bold mb-2">{html.escape(context['project_name'])}</h1>
            <p class="text-blue-100">Code Quality Report - {self._format_datetime(context['analysis_date'])}</p>
            <p class="text-sm text-blue-200 mt-1">Project: {html.escape(context['project_path'])}</p>
        </div>
    </header>

    <!-- Navigation -->
    <nav class="bg-white shadow-md sticky top-0 z-10">
        <div class="container mx-auto">
            <ul class="flex flex-wrap">
                <li><a href="#summary" class="nav-link">Summary</a></li>
                <li><a href="#imports" class="nav-link">Imports</a></li>
                <li><a href="#architecture" class="nav-link">Architecture</a></li>
                <li><a href="#quality" class="nav-link">Code Quality</a></li>
                <li><a href="#concurrency" class="nav-link">Concurrency</a></li>
                <li><a href="#recommendations" class="nav-link">Recommendations</a></li>
            </ul>
        </div>
    </nav>

    <!-- Main Content -->
    <main class="container mx-auto px-4 py-8">

        <!-- Executive Summary -->
        <section id="summary" class="mb-12">
            <h2 class="text-3xl font-bold mb-6">Executive Summary</h2>

            <!-- Overall Status -->
            <div class="bg-{context['overall_status_color']}-100 border-l-4 border-{context['overall_status_color']}-500 p-6 mb-8 rounded-r-lg shadow">
                <p class="font-bold text-{context['overall_status_color']}-700 text-xl">
                    {context['overall_status_icon']} {html.escape(context['overall_status_message'])}
                </p>
            </div>

            <!-- Key Metrics Grid -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
"""

        # Add key metrics
        for metric in context["key_metrics"]:
            html_content += f"""
                <div class="metric-card bg-white rounded-lg shadow-lg p-6">
                    <h3 class="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-2">{html.escape(metric['name'])}</h3>
                    <p class="text-4xl font-bold text-{metric['color']}-600 mb-2">{html.escape(str(metric['value']))}</p>
                    <p class="text-sm text-gray-500">{html.escape(metric['description'])}</p>
                </div>
"""

        html_content += """
            </div>

            <!-- Charts -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                <div class="bg-white rounded-lg shadow-lg p-6">
                    <h3 class="text-lg font-bold mb-4 text-gray-800">Issue Distribution</h3>
                    <div class="chart-container">
                        <canvas id="issueChart"></canvas>
                    </div>
                </div>
                <div class="bg-white rounded-lg shadow-lg p-6">
                    <h3 class="text-lg font-bold mb-4 text-gray-800">Severity Breakdown</h3>
                    <div class="chart-container">
                        <canvas id="severityChart"></canvas>
                    </div>
                </div>
            </div>
        </section>
"""

        # Add sections
        for section in context["sections"]:
            severity_class = f"severity-{section.severity}"
            html_content += f"""
        <section id="{section.id}" class="mb-12">
            <h2 class="text-3xl font-bold mb-6 text-gray-800">{html.escape(section.title)}</h2>

            <div class="{severity_class} border-l-4 rounded-r-lg shadow-lg p-6 bg-white">
                <div class="section-content">
                    {section.content}
                </div>
            </div>

            <!-- Section Metrics -->
"""
            if section.metrics:
                html_content += """
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
"""
                for key, value in section.metrics.items():
                    html_content += f"""
                <div class="bg-white rounded-lg shadow p-4">
                    <p class="text-sm text-gray-600 font-medium">{html.escape(key.replace('_', ' ').title())}</p>
                    <p class="text-2xl font-bold text-gray-800">{html.escape(str(value))}</p>
                </div>
"""
                html_content += """
            </div>
"""

            # Add chart if present
            if section.chart_data:
                chart_id = f"{section.id}Chart"
                html_content += f"""
            <div class="bg-white rounded-lg shadow-lg p-6 mt-6">
                <h3 class="text-lg font-bold mb-4 text-gray-800">{html.escape(section.title)} Analysis</h3>
                <div class="chart-container">
                    <canvas id="{chart_id}"></canvas>
                </div>
            </div>
"""

            html_content += """
        </section>
"""

        # Footer and scripts
        html_content += f"""
    </main>

    <!-- Footer -->
    <footer class="bg-gray-800 text-white p-6 mt-12">
        <div class="container mx-auto text-center">
            <p class="text-lg font-semibold mb-2">Generated by qontinui-devtools v{html.escape(context['version'])}</p>
            <p class="text-sm text-gray-400">
                Report generated on {self._format_datetime(context['analysis_date'])}
            </p>
            <p class="text-xs text-gray-500 mt-4">
                This report is for informational purposes. Always review code manually.
            </p>
        </div>
    </footer>

    <script>
        // Initialize charts
        {self._generate_chart_scripts(context)}

        // Smooth scrolling for navigation
        document.querySelectorAll('.nav-link').forEach(link => {{
            link.addEventListener('click', function(e) {{
                e.preventDefault();
                const targetId = this.getAttribute('href');
                const targetSection = document.querySelector(targetId);
                if (targetSection) {{
                    targetSection.scrollIntoView({{ behavior: 'smooth', block: 'start' }});

                    // Update active link
                    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
                    this.classList.add('active');
                }}
            }});
        }});

        // Highlight active section on scroll
        const sections = document.querySelectorAll('section[id]');
        const navLinks = document.querySelectorAll('.nav-link');

        window.addEventListener('scroll', () => {{
            let current = '';
            sections.forEach(section => {{
                const sectionTop = section.offsetTop;
                const sectionHeight = section.clientHeight;
                if (pageYOffset >= sectionTop - 200) {{
                    current = section.getAttribute('id');
                }}
            }});

            navLinks.forEach(link => {{
                link.classList.remove('active');
                if (link.getAttribute('href') === '#' + current) {{
                    link.classList.add('active');
                }}
            }});
        }});
    </script>
</body>
</html>
"""
        return html_content

    def _generate_chart_scripts(self, context: dict[str, Any]) -> str:
        """Generate Chart.js initialization scripts."""
        scripts: list[Any] = []

        # Issue distribution chart
        sections = context["sections"]
        section_labels = [s.title for s in sections]
        section_counts = [len(s.metrics) if s.metrics else 1 for s in sections]

        if section_labels:
            scripts.append(
                f"""
        const issueCtx = document.getElementById('issueChart');
        if (issueCtx) {{
            new Chart(issueCtx, {{
                type: 'bar',
                data: {{
                    labels: {json.dumps(section_labels)},
                    datasets: [{{
                        label: 'Issues by Category',
                        data: {json.dumps(section_counts)},
                        backgroundColor: [
                            'rgba(59, 130, 246, 0.7)',
                            'rgba(16, 185, 129, 0.7)',
                            'rgba(245, 158, 11, 0.7)',
                            'rgba(239, 68, 68, 0.7)',
                            'rgba(139, 92, 246, 0.7)',
                            'rgba(236, 72, 153, 0.7)'
                        ],
                        borderColor: [
                            'rgba(59, 130, 246, 1)',
                            'rgba(16, 185, 129, 1)',
                            'rgba(245, 158, 11, 1)',
                            'rgba(239, 68, 68, 1)',
                            'rgba(139, 92, 246, 1)',
                            'rgba(236, 72, 153, 1)'
                        ],
                        borderWidth: 2
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            display: false
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            ticks: {{
                                precision: 0
                            }}
                        }}
                    }}
                }}
            }});
        }}
"""
            )

        # Severity breakdown chart
        severity_counts = {
            "Error": sum(1 for s in sections if s.severity == "error"),
            "Warning": sum(1 for s in sections if s.severity == "warning"),
            "Info": sum(1 for s in sections if s.severity == "info"),
            "Success": sum(1 for s in sections if s.severity == "success"),
        }

        scripts.append(
            f"""
        const severityCtx = document.getElementById('severityChart');
        if (severityCtx) {{
            new Chart(severityCtx, {{
                type: 'doughnut',
                data: {{
                    labels: ['Error', 'Warning', 'Info', 'Success'],
                    datasets: [{{
                        label: 'Severity Distribution',
                        data: [{severity_counts['Error']}, {severity_counts['Warning']}, {severity_counts['Info']}, {severity_counts['Success']}],
                        backgroundColor: [
                            'rgba(239, 68, 68, 0.8)',
                            'rgba(245, 158, 11, 0.8)',
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)'
                        ],
                        borderColor: [
                            'rgba(239, 68, 68, 1)',
                            'rgba(245, 158, 11, 1)',
                            'rgba(59, 130, 246, 1)',
                            'rgba(16, 185, 129, 1)'
                        ],
                        borderWidth: 2
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            position: 'bottom'
                        }}
                    }}
                }}
            }});
        }}
"""
        )

        # Add section-specific charts
        for section in sections:
            if section.chart_data:
                chart_id = f"{section.id}Chart"
                scripts.append(
                    f"""
        const {section.id}Ctx = document.getElementById('{chart_id}');
        if ({section.id}Ctx) {{
            new Chart({section.id}Ctx, {json.dumps(section.chart_data)});
        }}
"""
                )

        return "\n".join(scripts)

    def add_section(self, section: ReportSection) -> None:
        """
        Add a section to the current report.

        Args:
            section: Section to add
        """
        if not self.report_data:
            raise ValueError("No report data set. Call generate() first.")

        self.report_data.add_section(section)

    def create_summary_section(self, metrics: dict[str, Any]) -> ReportSection:
        """
        Create a summary section from metrics.

        Args:
            metrics: Dictionary of metrics

        Returns:
            ReportSection for summary
        """
        content = "<h3>Summary Metrics</h3><ul>"
        for key, value in metrics.items():
            content += f"<li><strong>{html.escape(key.replace('_', ' ').title())}:</strong> {html.escape(str(value))}</li>"
        content += "</ul>"

        return ReportSection(
            id="summary",
            title="Summary",
            content=content,
            severity="info",
            metrics=metrics,
        )

    def create_charts(self, data: dict[str, Any]) -> str:
        """
        Create Chart.js configuration from data.

        Args:
            data: Chart data

        Returns:
            HTML with Chart.js configuration
        """
        chart_type = data.get("type", "bar")
        chart_id = data.get("id", "chart")
        labels = data.get("labels", [])
        datasets = data.get("datasets", [])

        chart_config = {
            "type": chart_type,
            "data": {"labels": labels, "datasets": datasets},
            "options": {
                "responsive": True,
                "maintainAspectRatio": False,
                "plugins": {"legend": {"display": True, "position": "bottom"}},
            },
        }

        return f"""
        <div class="chart-container">
            <canvas id="{chart_id}"></canvas>
        </div>
        <script>
            const {chart_id}Ctx = document.getElementById('{chart_id}');
            if ({chart_id}Ctx) {{
                new Chart({chart_id}Ctx, {json.dumps(chart_config)});
            }}
        </script>
        """
