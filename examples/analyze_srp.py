#!/usr/bin/env python3
"""Example script demonstrating SRP Analyzer usage.

from typing import Any, Any

This script shows how to use the SRP Analyzer programmatically
to detect Single Responsibility Principle violations in Python code.
"""

import sys
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

from qontinui_devtools.architecture import SRPAnalyzer


def main() -> Any:
    """Run SRP analysis on example code."""

    # Path to analyze (can be a file or directory)
    # For this example, analyze the test fixtures
    fixtures_path = Path(__file__).parent.parent / "python" / "tests" / "fixtures" / "srp"

    if not fixtures_path.exists():
        print(f"Error: Fixtures path not found: {fixtures_path}")
        return 1

    print("=" * 80)
    print("SRP ANALYZER EXAMPLE")
    print("=" * 80)
    print()
    print(f"Analyzing: {fixtures_path}")
    print()

    # Create analyzer instance
    analyzer = SRPAnalyzer(verbose=True)

    # Run analysis
    print("Running analysis...")
    violations, execution_time = analyzer.analyze_with_timing(str(fixtures_path), min_methods=5)

    print(f"\nAnalysis completed in {execution_time:.2f} seconds")
    print()

    # Display results
    if not violations:
        print("✅ No SRP violations detected!")
        return 0

    print(f"Found {len(violations)} SRP violations:\n")

    for i, violation in enumerate(violations, 1):
        print(f"{i}. {violation.class_name} ({violation.severity}):")
        print(f"   File: {violation.file_path}:{violation.line_number}")
        print(f"   Responsibilities: {len(violation.clusters)}")
        print()

        for cluster in violation.clusters:
            print(f"   - {cluster.name}:")

            # Show first 5 methods
            methods_to_show = cluster.methods[:5]
            for method in methods_to_show:
                print(f"       • {method}")

            if len(cluster.methods) > 5:
                print(f"       ... and {len(cluster.methods) - 5} more")

            print(f"     Confidence: {cluster.confidence:.2f}")
            print()

        print(f"   Recommendation: {violation.recommendation}")
        print()

        print("   Suggested Refactorings:")
        for suggestion in violation.suggested_refactorings:
            print(f"     → {suggestion}")

        print()
        print("-" * 80)
        print()

    # Generate and save full report
    report = analyzer.generate_report(violations)

    report_path = Path(__file__).parent / "srp_analysis_report.txt"
    report_path.write_text(report)

    print(f"Full report saved to: {report_path}")
    print()

    # Display statistics
    print("Statistics:")
    print(f"  Files analyzed:   {analyzer.stats['files_analyzed']}")
    print(f"  Classes analyzed: {analyzer.stats['classes_analyzed']}")
    print(f"  Violations found: {analyzer.stats['violations_found']}")
    print(f"  Execution time:   {execution_time:.2f}s")
    print()

    return 0


def analyze_custom_path(path: str) -> None:
    """Analyze a custom path.

    Args:
        path: Path to Python file or directory to analyze
    """
    analyzer = SRPAnalyzer(verbose=True)

    violations = analyzer.analyze_directory(path, min_methods=5)

    if violations:
        print(f"\nFound {len(violations)} violations in {path}")

        for violation in violations:
            print(f"\n{violation.class_name}:")
            for cluster in violation.clusters:
                print(f"  - {cluster.name} ({len(cluster.methods)} methods)")
    else:
        print(f"\n✅ No violations found in {path}")


def demonstrate_clustering() -> None:
    """Demonstrate the clustering algorithm."""
    from qontinui_devtools.architecture.clustering import \
        cluster_methods_by_keywords

    print("\n" + "=" * 80)
    print("CLUSTERING DEMONSTRATION")
    print("=" * 80)
    print()

    # Example methods with multiple responsibilities
    methods = [
        # Data access
        "get_user",
        "fetch_data",
        "retrieve_records",
        "find_items",
        # Validation
        "validate_email",
        "check_password",
        "verify_credentials",
        # Business logic
        "calculate_total",
        "process_order",
        "compute_score",
        # Persistence
        "save_to_database",
        "load_from_cache",
        "persist_changes",
    ]

    print("Methods to cluster:")
    for method in methods:
        print(f"  - {method}")
    print()

    # Cluster the methods
    clusters = cluster_methods_by_keywords(methods, min_cluster_size=2)

    print(f"Detected {len(clusters)} responsibility clusters:")
    print()

    for i, cluster in enumerate(clusters, 1):
        print(f"{i}. {cluster.name} (confidence: {cluster.confidence:.2f})")
        for method in cluster.methods:
            print(f"     • {method}")
        print(f"   Keywords: {', '.join(sorted(cluster.keywords))}")
        print()


if __name__ == "__main__":
    # Run main analysis
    exit_code = main()

    # Demonstrate clustering algorithm
    demonstrate_clustering()

    # Example of analyzing a custom path
    # Uncomment and modify path as needed:
    # analyze_custom_path("/path/to/your/code")

    sys.exit(exit_code)
