"""Example usage of the Dependency Health Checker.

This script demonstrates how to use the dependency health checker
to analyze a Python project's dependencies.
"""

from pathlib import Path

from qontinui_devtools.dependencies import (DependencyHealthChecker,
                                            HealthStatus, UpdateType)


def main() -> None:
    """Run dependency health check example."""
    # Initialize the checker
    print("Initializing Dependency Health Checker...")
    checker = DependencyHealthChecker(
        offline_mode=False,  # Use online PyPI data
        check_vulnerabilities=True,  # Check for security issues
    )

    # Check the current project
    project_path = Path.cwd().parent.parent  # Go up to project root
    print(f"\nAnalyzing dependencies in: {project_path}")
    print("=" * 70)

    # Run the health check
    report = checker.check_health(
        project_path=project_path,
        fail_on_vulnerable=False,  # Don't raise exception on vulnerabilities
        include_dev=True,  # Include dev dependencies
    )

    # Display overall statistics
    print(f"\n{report}")
    print("\n" + "=" * 70)

    # Display vulnerable packages
    if report.vulnerable_count > 0:
        print("\n🔴 VULNERABLE PACKAGES:")
        print("-" * 70)
        for dep in report.get_vulnerable_dependencies():
            print(f"\n{dep.name} {dep.current_version}")
            for vuln in dep.vulnerabilities:
                print(f"  {vuln}")

    # Display deprecated packages
    if report.deprecated_count > 0:
        print("\n⚠️  DEPRECATED PACKAGES:")
        print("-" * 70)
        for dep in report.get_deprecated_dependencies():
            print(f"{dep.name}: {dep.deprecation_notice}")

    # Display outdated packages
    if report.outdated_count > 0:
        print("\n📦 OUTDATED PACKAGES:")
        print("-" * 70)
        for dep in report.get_outdated_dependencies():
            update_emoji = {
                UpdateType.MAJOR: "🔴",
                UpdateType.MINOR: "🟡",
                UpdateType.PATCH: "🟢",
            }
            emoji = update_emoji.get(dep.update_type, "⚪") if dep.update_type else "⚪"

            if dep.update_type:
                print(
                    f"{emoji} {dep.name}: {dep.current_version} → {dep.latest_version} "
                    f"({dep.update_type.value} update, risk: {dep.update_type.risk_level})"
                )
            else:
                print(
                    f"{emoji} {dep.name}: {dep.current_version} → {dep.latest_version} "
                    "(unknown update type)"
                )

    # Display circular dependencies
    if report.circular_dependencies:
        print("\n🔄 CIRCULAR DEPENDENCIES:")
        print("-" * 70)
        for circular in report.circular_dependencies:
            print(f"{circular}")

    # Display license conflicts
    if report.license_conflicts:
        print("\n⚖️  LICENSE CONFLICTS:")
        print("-" * 70)
        for conflict in report.license_conflicts:
            print(f"{conflict}")

    # Display recommendations
    print("\n💡 RECOMMENDATIONS:")
    print("-" * 70)
    for i, recommendation in enumerate(report.recommendations, 1):
        print(f"{i}. {recommendation}")

    # Display detailed dependency information
    print("\n📊 DETAILED DEPENDENCY INFORMATION:")
    print("-" * 70)
    for dep in sorted(report.dependencies, key=lambda d: d.health_score):
        status_emoji = {
            HealthStatus.HEALTHY: "✅",
            HealthStatus.OUTDATED: "📦",
            HealthStatus.VULNERABLE: "🔴",
            HealthStatus.DEPRECATED: "⚠️",
            HealthStatus.UNKNOWN: "❓",
        }
        emoji = status_emoji.get(dep.health_status, "❓")

        print(
            f"{emoji} {dep.name:30} "
            f"v{dep.current_version:15} "
            f"Health: {dep.health_score:5.1f}/100"
        )

        if dep.latest_version and dep.latest_version != dep.current_version:
            print(f"   Latest: {dep.latest_version}")

        if dep.license:
            print(f"   License: {dep.license} ({dep.license_category.value})")

        if dep.last_release_date:
            age = (Path(__file__).stat().st_mtime - dep.last_release_date.timestamp()) / 86400
            print(f"   Last release: {int(age)} days ago")

    print("\n" + "=" * 70)
    print(f"Overall Health Score: {report.overall_health_score:.1f}/100")
    print("=" * 70)


if __name__ == "__main__":
    main()
