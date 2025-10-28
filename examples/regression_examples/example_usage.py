"""Example usage of the Regression Detector."""

from pathlib import Path
from qontinui_devtools.regression import RegressionDetector, ChangeType

def main() -> None:
    """Demonstrate regression detection capabilities."""

    # Initialize detector
    detector = RegressionDetector()

    # Example 1: Create a baseline snapshot
    print("Creating baseline snapshot...")
    baseline_snapshot = detector.create_snapshot(
        Path("./my_project/src"),
        version="v1.0",
        save=True
    )
    print(f"Baseline: {len(baseline_snapshot.functions)} functions, "
          f"{len(baseline_snapshot.classes)} classes")

    # Example 2: Compare current code to baseline
    print("\nDetecting regressions...")
    report = detector.detect_regressions(
        source_path=Path("./my_project/src"),
        baseline="v1.0",  # Load from saved snapshot
        current_version="v2.0"
    )

    # Example 3: Analyze results
    print(f"\n=== Regression Report ===")
    print(f"Baseline: {report.baseline_version}")
    print(f"Current: {report.current_version}")
    print(f"Total Issues: {len(report.issues)}")
    print(f"  - Breaking Changes: {report.breaking_count}")
    print(f"  - Behavioral Changes: {report.behavioral_count}")
    print(f"  - Performance Regressions: {report.performance_count}")
    print(f"  - Dependency Changes: {report.dependency_count}")

    # Example 4: Show critical issues
    critical_issues = report.get_critical_issues()
    if critical_issues:
        print(f"\n=== Critical Issues ({len(critical_issues)}) ===")
        for issue in critical_issues[:3]:  # Show first 3
            print(f"\n{issue.description}")
            print(f"Impact: {issue.impact_description}")
            print(f"Migration Guide:\n{issue.migration_guide}")

    # Example 5: Check breaking changes
    if report.has_breaking_changes():
        print("\n⚠️  WARNING: Breaking changes detected!")
        breaking = report.get_breaking_changes()
        for issue in breaking:
            print(f"  - {issue.description}")

    # Example 6: Calculate risk score
    risk_score = detector.calculate_risk_score(report)
    print(f"\nRisk Score: {risk_score:.1f}/100")

    # Example 7: Save report for CI/CD
    detector.save_report(report, Path("regression_report.json"))
    print("\nReport saved to regression_report.json")

    # Example 8: Performance regression detection
    print("\n=== Performance Regression Example ===")
    from qontinui_devtools.regression import PerformanceMetric

    baseline_metrics = {
        "my_module.slow_function": PerformanceMetric(
            function_name="slow_function",
            module_path="my_module",
            execution_time_ms=100.0,
            memory_usage_mb=10.0
        )
    }

    current_metrics = {
        "my_module.slow_function": PerformanceMetric(
            function_name="slow_function",
            module_path="my_module",
            execution_time_ms=150.0,  # 50% slower!
            memory_usage_mb=15.0
        )
    }

    perf_issues = detector.detect_performance_regressions(
        baseline_metrics, current_metrics
    )

    if perf_issues:
        print(f"\nFound {len(perf_issues)} performance regressions:")
        for issue in perf_issues:
            print(f"  - {issue.description}")
            print(f"    {issue.impact_description}")

    # Example 9: Dependency change detection
    print("\n=== Dependency Change Example ===")

    baseline_deps = {
        "requests": "2.28.0",
        "numpy": "1.24.0",
        "pandas": "1.5.0"
    }

    current_deps = {
        "requests": "2.31.0",  # Minor version bump
        "numpy": "2.0.0",      # Major version bump!
        # pandas removed
    }

    dep_issues = detector.detect_dependency_changes(baseline_deps, current_deps)

    if dep_issues:
        print(f"\nFound {len(dep_issues)} dependency changes:")
        for issue in dep_issues:
            print(f"  - {issue.description} [{issue.risk_level.value}]")


if __name__ == "__main__":
    main()
