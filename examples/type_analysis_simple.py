#!/usr/bin/env python3
"""Simple example of using the Type Hint Analyzer."""

from qontinui_devtools.type_analysis import TypeAnalyzer

# Create analyzer
analyzer = TypeAnalyzer(run_mypy=False)

# Analyze a directory
report = analyzer.analyze_directory("python/qontinui_devtools/type_analysis")

# Print results
print(f"Coverage: {report.overall_coverage.coverage_percentage:.1f}%")
print(f"Functions: {report.overall_coverage.total_functions}")
print(f"Fully typed: {report.overall_coverage.fully_typed_functions}")
print()

# Show top untyped items
print("Top untyped items:")
for item in report.get_sorted_untyped_items(limit=5):
    print(f"  {item.name} ({item.file_path}:{item.line_number})")
    if item.suggested_type:
        print(f"    Suggestion: {item.suggested_type}")

# Generate full text report
text_report = analyzer.generate_report_text(report)
print("\n" + text_report)
