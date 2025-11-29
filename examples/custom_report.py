#!/usr/bin/env python3
"""
Example: Create a custom HTML report with specific sections.

This demonstrates how to manually create report sections and customize
the report content.

Usage:
    python custom_report.py
"""

import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import qontinui_devtools
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

from qontinui_devtools.reporting import (
    HTMLReportGenerator,
    ReportData,
    ReportSection,
    create_bar_chart,
    create_line_chart,
    create_pie_chart,
)


def create_custom_report():
    """Create a custom report with manually defined sections."""

    # Create report data
    report_data = ReportData(
        project_name="Example Project",
        analysis_date=datetime.now(),
        project_path="/example/project",
        version="1.0.0",
    )

    # Set summary metrics
    report_data.summary_metrics = {
        "files_analyzed": 150,
        "total_lines": 15000,
        "circular_dependencies": 1,
        "god_classes": 2,
        "race_conditions": 0,
        "critical_issues": 1,
    }

    # Add Import Analysis section
    import_section = ReportSection(
        id="imports",
        title="Import Analysis",
        content="""
        <h3>Circular Dependencies</h3>
        <p>Found 1 circular dependency that needs attention:</p>
        <ul>
            <li><code>module_a → module_b → module_a</code></li>
        </ul>
        <h3>Recommendations</h3>
        <ul>
            <li>Extract common code to a new module</li>
            <li>Use dependency injection to break the cycle</li>
        </ul>
        """,
        severity="warning",
        metrics={"circular_dependencies": 1, "total_imports": 450},
        chart_data=create_bar_chart(
            labels=["Module A", "Module B", "Module C", "Module D"],
            data=[45, 38, 52, 31],
            title="Imports per Module",
            color="blue",
        ),
    )
    report_data.add_section(import_section)

    # Add Architecture section
    arch_section = ReportSection(
        id="architecture",
        title="Architecture Quality",
        content="""
        <h3>God Classes Detected</h3>
        <p>Found 2 god classes that violate the Single Responsibility Principle:</p>
        <ul>
            <li><strong>UserManager</strong> - 45 methods, 850 lines
                <br>Responsibilities: user auth, profile management, notifications, logging
            </li>
            <li><strong>DataProcessor</strong> - 32 methods, 650 lines
                <br>Responsibilities: data validation, transformation, export, caching
            </li>
        </ul>
        <h3>Refactoring Suggestions</h3>
        <ul>
            <li>Extract NotificationService from UserManager</li>
            <li>Extract CacheManager from DataProcessor</li>
        </ul>
        """,
        severity="warning",
        metrics={"god_classes": 2, "srp_violations": 5, "average_class_size": 185},
        chart_data=create_pie_chart(
            labels=["Small Classes", "Medium Classes", "Large Classes", "God Classes"],
            data=[85, 42, 21, 2],
            title="Class Size Distribution",
        ),
    )
    report_data.add_section(arch_section)

    # Add Code Quality section
    quality_section = ReportSection(
        id="quality",
        title="Code Quality",
        content="""
        <h3>Code Quality Metrics</h3>
        <p>Overall code quality is good with minor issues:</p>
        <ul>
            <li>Average cyclomatic complexity: 3.2 (good)</li>
            <li>Code duplication: 2.5% (acceptable)</li>
            <li>Documentation coverage: 78% (good)</li>
            <li>Type hints coverage: 85% (very good)</li>
        </ul>
        <h3>Issues Found</h3>
        <ul>
            <li>5 TODO comments requiring attention</li>
            <li>3 wildcard imports should be made explicit</li>
            <li>12 functions missing docstrings</li>
        </ul>
        """,
        severity="success",
        metrics={
            "total_files": 150,
            "total_lines": 15000,
            "complexity_avg": 3.2,
            "duplication": 2.5,
        },
        chart_data=create_line_chart(
            labels=["Week 1", "Week 2", "Week 3", "Week 4"],
            datasets=[
                {"label": "Code Quality Score", "data": [72, 75, 78, 82], "color": "green"},
                {"label": "Test Coverage", "data": [65, 68, 72, 75], "color": "blue"},
            ],
            title="Quality Trends",
            y_label="Score (%)",
        ),
    )
    report_data.add_section(quality_section)

    # Add Concurrency section
    concurrency_section = ReportSection(
        id="concurrency",
        title="Concurrency Analysis",
        content="""
        <h3>Race Conditions</h3>
        <p>✅ No race conditions detected!</p>
        <p>All shared state access is properly synchronized:</p>
        <ul>
            <li>All shared dictionaries use locks</li>
            <li>Thread-safe data structures used appropriately</li>
            <li>No unsynchronized counter updates</li>
        </ul>
        <h3>Best Practices Followed</h3>
        <ul>
            <li>Using threading.Lock for critical sections</li>
            <li>Leveraging queue.Queue for thread communication</li>
            <li>Proper use of threading.Event for signaling</li>
        </ul>
        """,
        severity="success",
        metrics={"race_conditions": 0, "shared_state_accesses": 45, "locks_used": 8},
    )
    report_data.add_section(concurrency_section)

    # Add Recommendations section
    recommendations_section = ReportSection(
        id="recommendations",
        title="Recommendations",
        content="""
        <h3>Priority Actions</h3>
        <ol>
            <li><strong>Break circular dependency</strong>
                <br>Refactor module_a and module_b to eliminate circular import
                <br>Priority: High | Estimated effort: 2-4 hours
            </li>
            <li><strong>Refactor UserManager god class</strong>
                <br>Extract NotificationService and improve separation of concerns
                <br>Priority: Medium | Estimated effort: 1 day
            </li>
            <li><strong>Refactor DataProcessor god class</strong>
                <br>Extract CacheManager and DataValidator
                <br>Priority: Medium | Estimated effort: 1 day
            </li>
            <li><strong>Address TODO comments</strong>
                <br>Review and resolve 5 TODO items
                <br>Priority: Low | Estimated effort: 2-3 hours
            </li>
        </ol>
        <h3>Long-term Improvements</h3>
        <ul>
            <li>Increase test coverage to 85%+</li>
            <li>Add docstrings to remaining functions</li>
            <li>Set up automated code quality checks in CI/CD</li>
        </ul>
        """,
        severity="info",
        metrics={"total_recommendations": 4, "high_priority": 1, "medium_priority": 2},
    )
    report_data.add_section(recommendations_section)

    # Generate HTML report
    print("Generating custom HTML report...")
    generator = HTMLReportGenerator(verbose=True)
    output_path = "custom_analysis_report.html"
    generator.generate(report_data, output_path)

    print(f"\n✅ Custom report generated: {output_path}")
    print(f"📊 Report contains {len(report_data.sections)} sections")
    print(f"📁 File size: {Path(output_path).stat().st_size:,} bytes")
    print("\n💡 Open in browser to view the report.")


if __name__ == "__main__":
    create_custom_report()
