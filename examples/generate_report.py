#!/usr/bin/env python3
"""
Example: Generate comprehensive HTML report for code analysis.

This script demonstrates how to use the qontinui-devtools reporting module
to generate a comprehensive HTML report from analysis results.

Usage:
    python generate_report.py <project_path> [output_report.html]

Example:
    python generate_report.py ../qontinui/src qontinui_analysis.html
"""

import sys
from pathlib import Path

# Add parent directory to path to import qontinui_devtools
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

from qontinui_devtools.reporting import HTMLReportGenerator, ReportAggregator


def main() -> None:
    """Generate HTML report for a project."""
    if len(sys.argv) < 2:
        print("Usage: python generate_report.py <project_path> [output_report.html]")
        print("\nExample:")
        print("  python generate_report.py ../qontinui/src qontinui_analysis.html")
        sys.exit(1)

    project_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "analysis_report.html"

    print(f"Analyzing project: {project_path}")
    print("=" * 60)

    # Create aggregator
    aggregator = ReportAggregator(project_path, verbose=True)

    # Run all analyses
    print("\n1. Running all analyses...")
    report_data = aggregator.run_all_analyses()

    # Display summary
    print("\n2. Analysis Summary:")
    print(f"   - Files analyzed: {report_data.summary_metrics.get('files_analyzed', 0)}")
    print(f"   - Total lines: {report_data.summary_metrics.get('total_lines', 0):,}")
    print(
        f"   - Circular dependencies: {report_data.summary_metrics.get('circular_dependencies', 0)}"
    )
    print(f"   - God classes: {report_data.summary_metrics.get('god_classes', 0)}")
    print(f"   - Race conditions: {report_data.summary_metrics.get('race_conditions', 0)}")
    print(f"   - Critical issues: {report_data.summary_metrics.get('critical_issues', 0)}")

    # Generate HTML report
    print(f"\n3. Generating HTML report: {output_path}")
    generator = HTMLReportGenerator(verbose=True)
    generator.generate(report_data, output_path)

    print("\n" + "=" * 60)
    print("✅ Report generated successfully!")
    print(f"📊 Report location: {Path(output_path).absolute()}")
    print(f"📁 File size: {Path(output_path).stat().st_size:,} bytes")
    print("\n💡 Open the HTML file in your browser to view the interactive report.")
    print("   It includes:")
    print("   - Executive summary with overall quality score")
    print("   - Import analysis (circular dependencies)")
    print("   - Architecture quality (god classes, SRP violations)")
    print("   - Code quality metrics")
    print("   - Concurrency issues (race conditions)")
    print("   - Interactive charts and visualizations")
    print("   - Actionable recommendations")


if __name__ == "__main__":
    main()
