"""Command-line interface for dependency health checker.

This module provides a CLI for running dependency health checks on Python projects.
"""

import argparse
import sys

from .health_checker import DependencyHealthChecker
from .models import UpdateType


def main():
    """Run dependency health checker CLI."""
    parser = argparse.ArgumentParser(
        description="Check dependency health for Python projects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check current directory
  python -m qontinui_devtools.dependencies.cli

  # Check specific project
  python -m qontinui_devtools.dependencies.cli /path/to/project

  # Fail on vulnerabilities (CI/CD)
  python -m qontinui_devtools.dependencies.cli --fail-on-vulnerable

  # Offline mode
  python -m qontinui_devtools.dependencies.cli --offline

  # Exclude dev dependencies
  python -m qontinui_devtools.dependencies.cli --no-dev
        """,
    )

    parser.add_argument(
        "project_path",
        nargs="?",
        default=".",
        help="Path to project directory (default: current directory)",
    )

    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use offline mode (cached data only)",
    )

    parser.add_argument(
        "--no-vulnerabilities",
        action="store_true",
        help="Skip vulnerability checking",
    )

    parser.add_argument(
        "--fail-on-vulnerable",
        action="store_true",
        help="Exit with error code if vulnerabilities found",
    )

    parser.add_argument(
        "--no-dev",
        action="store_true",
        help="Exclude dev dependencies",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    # Initialize checker
    checker = DependencyHealthChecker(
        offline_mode=args.offline,
        check_vulnerabilities=not args.no_vulnerabilities,
    )

    try:
        # Run health check
        report = checker.check_health(
            project_path=args.project_path,
            fail_on_vulnerable=args.fail_on_vulnerable,
            include_dev=not args.no_dev,
        )

        if args.json:
            # Output JSON format
            import json

            output = {
                "health_score": report.overall_health_score,
                "total_dependencies": report.total_dependencies,
                "healthy_count": report.healthy_count,
                "outdated_count": report.outdated_count,
                "vulnerable_count": report.vulnerable_count,
                "deprecated_count": report.deprecated_count,
                "total_vulnerabilities": report.total_vulnerabilities,
                "critical_vulnerabilities": report.critical_vulnerabilities,
                "recommendations": report.recommendations,
                "dependencies": [
                    {
                        "name": dep.name,
                        "current_version": dep.current_version,
                        "latest_version": dep.latest_version,
                        "health_status": dep.health_status.value,
                        "health_score": dep.health_score,
                        "update_type": dep.update_type.value if dep.update_type else None,
                        "vulnerabilities": len(dep.vulnerabilities),
                    }
                    for dep in report.dependencies
                ],
            }
            print(json.dumps(output, indent=2))
        else:
            # Human-readable output
            print("=" * 80)
            print(report)
            print("=" * 80)
            print()

            # Vulnerable packages
            if report.vulnerable_count > 0:
                print("🔴 VULNERABLE PACKAGES:")
                print("-" * 80)
                for dep in report.get_vulnerable_dependencies():
                    print(f"\n{dep.name} {dep.current_version}")
                    for vuln in dep.vulnerabilities:
                        print(f"  {vuln}")
                print()

            # Deprecated packages
            if report.deprecated_count > 0:
                print("⚠️  DEPRECATED PACKAGES:")
                print("-" * 80)
                for dep in report.get_deprecated_dependencies():
                    print(f"{dep.name}: {dep.deprecation_notice}")
                print()

            # Outdated packages
            if report.outdated_count > 0 and args.verbose:
                print("📦 OUTDATED PACKAGES:")
                print("-" * 80)
                update_emoji = {
                    UpdateType.MAJOR: "🔴",
                    UpdateType.MINOR: "🟡",
                    UpdateType.PATCH: "🟢",
                }
                for dep in report.get_outdated_dependencies():
                    emoji = update_emoji.get(dep.update_type, "⚪")
                    print(
                        f"{emoji} {dep.name:25} {dep.current_version:12} → "
                        f"{dep.latest_version:12} ({dep.update_type.value})"
                    )
                print()

            # Circular dependencies
            if report.circular_dependencies:
                print("🔄 CIRCULAR DEPENDENCIES:")
                print("-" * 80)
                for circular in report.circular_dependencies:
                    print(f"{circular}")
                print()

            # License conflicts
            if report.license_conflicts:
                print("⚖️  LICENSE CONFLICTS:")
                print("-" * 80)
                for conflict in report.license_conflicts:
                    print(f"{conflict}")
                print()

            # Recommendations
            print("💡 RECOMMENDATIONS:")
            print("-" * 80)
            for i, recommendation in enumerate(report.recommendations, 1):
                print(f"{i}. {recommendation}")
            print()

            # Summary
            print("=" * 80)
            print(f"OVERALL HEALTH SCORE: {report.overall_health_score:.1f}/100")
            print("=" * 80)

        # Exit with appropriate code
        if report.has_critical_issues and args.fail_on_vulnerable:
            sys.exit(1)
        elif report.overall_health_score < 50:
            sys.exit(2)  # Very poor health
        else:
            sys.exit(0)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
