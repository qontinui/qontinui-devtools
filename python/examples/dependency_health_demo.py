"""Demonstration of the Dependency Health Checker with sample output.

This script creates a sample project and demonstrates the dependency health checker
with realistic output.
"""

import tempfile
from datetime import timedelta
from pathlib import Path
from typing import Any
from unittest.mock import Mock

from qontinui_devtools.dependencies import DependencyHealthChecker, HealthStatus, UpdateType
from qontinui_devtools.dependencies.pypi_client import PackageInfo, PyPIClient
from qontinui_schemas.common import utc_now


def create_sample_project() -> Path:
    """Create a sample project with various dependency scenarios."""
    tmpdir = tempfile.mkdtemp()
    project_path = Path(tmpdir)

    # Create pyproject.toml with various dependency scenarios
    pyproject_content = """[project]
name = "sample-web-app"
version = "1.0.0"
description = "A sample web application"

dependencies = [
    "flask>=2.0.0",
    "requests>=2.25.0",  # Outdated
    "django>=3.2.0",
    "sqlalchemy>=1.4.0",
    "celery>=5.0.0",
    "numpy>=1.21.0",
    "pandas>=1.3.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "black>=23.0.0",
    "mypy>=1.0.0",
    "flake8>=5.0.0",
]
"""

    (project_path / "pyproject.toml").write_text(pyproject_content)

    return project_path


def create_mock_pypi_client() -> Any:
    """Create a mock PyPI client with realistic package data."""
    mock_client = Mock(spec=PyPIClient)

    # Package data mapping
    package_data = {
        "flask": PackageInfo(
            name="flask",
            latest_version="3.0.0",
            versions=["3.0.0", "2.3.0", "2.0.0"],
            release_dates={
                "3.0.0": utc_now() - timedelta(days=30),
                "2.3.0": utc_now() - timedelta(days=120),
            },
            license="BSD-3-Clause",
            homepage="https://flask.palletsprojects.com/",
            repository="https://github.com/pallets/flask",
            maintainers=["Pallets Team"],
            dependencies=["werkzeug", "jinja2", "click"],
            download_count=50000000,
            description="A simple framework for building complex web applications.",
            requires_python=">=3.8",
        ),
        "requests": PackageInfo(
            name="requests",
            latest_version="2.31.0",
            versions=["2.31.0", "2.30.0", "2.25.0"],
            release_dates={
                "2.31.0": utc_now() - timedelta(days=180),
                "2.25.0": utc_now() - timedelta(days=800),
            },
            license="Apache-2.0",
            homepage="https://requests.readthedocs.io",
            repository="https://github.com/psf/requests",
            maintainers=["Kenneth Reitz", "Nate Prewitt"],
            dependencies=["urllib3", "certifi", "charset-normalizer"],
            download_count=100000000,
            description="Python HTTP for Humans.",
            requires_python=">=3.7",
        ),
        "django": PackageInfo(
            name="django",
            latest_version="4.2.7",
            versions=["4.2.7", "4.2.0", "3.2.0"],
            release_dates={
                "4.2.7": utc_now() - timedelta(days=45),
                "3.2.0": utc_now() - timedelta(days=900),
            },
            license="BSD-3-Clause",
            homepage="https://www.djangoproject.com/",
            repository="https://github.com/django/django",
            maintainers=["Django Software Foundation"],
            dependencies=["sqlparse", "asgiref"],
            download_count=80000000,
            description="A high-level Python web framework.",
            requires_python=">=3.8",
        ),
        "sqlalchemy": PackageInfo(
            name="sqlalchemy",
            latest_version="2.0.23",
            versions=["2.0.23", "1.4.0"],
            release_dates={
                "2.0.23": utc_now() - timedelta(days=20),
                "1.4.0": utc_now() - timedelta(days=600),
            },
            license="MIT",
            homepage="https://www.sqlalchemy.org",
            repository="https://github.com/sqlalchemy/sqlalchemy",
            maintainers=["Mike Bayer"],
            dependencies=["greenlet"],
            download_count=60000000,
            description="Database Abstraction Library",
            requires_python=">=3.7",
        ),
        "celery": PackageInfo(
            name="celery",
            latest_version="5.3.4",
            versions=["5.3.4", "5.0.0"],
            release_dates={
                "5.3.4": utc_now() - timedelta(days=60),
                "5.0.0": utc_now() - timedelta(days=800),
            },
            license="BSD-3-Clause",
            homepage="http://celeryproject.org",
            repository="https://github.com/celery/celery",
            maintainers=["Ask Solem"],
            dependencies=["kombu", "billiard", "pytz"],
            download_count=30000000,
            description="Distributed Task Queue.",
            requires_python=">=3.7",
        ),
        "numpy": PackageInfo(
            name="numpy",
            latest_version="1.26.2",
            versions=["1.26.2", "1.21.0"],
            release_dates={
                "1.26.2": utc_now() - timedelta(days=15),
                "1.21.0": utc_now() - timedelta(days=700),
            },
            license="BSD-3-Clause",
            homepage="https://numpy.org",
            repository="https://github.com/numpy/numpy",
            maintainers=["NumPy Developers"],
            dependencies=[],
            download_count=200000000,
            description="Fundamental package for array computing in Python",
            requires_python=">=3.9",
        ),
        "pandas": PackageInfo(
            name="pandas",
            latest_version="2.1.4",
            versions=["2.1.4", "1.3.0"],
            release_dates={
                "2.1.4": utc_now() - timedelta(days=25),
                "1.3.0": utc_now() - timedelta(days=750),
            },
            license="BSD-3-Clause",
            homepage="https://pandas.pydata.org",
            repository="https://github.com/pandas-dev/pandas",
            maintainers=["Pandas Development Team"],
            dependencies=["numpy", "python-dateutil", "pytz"],
            download_count=150000000,
            description="Powerful data structures for data analysis",
            requires_python=">=3.9",
        ),
        "pytest": PackageInfo(
            name="pytest",
            latest_version="7.4.3",
            versions=["7.4.3", "7.0.0"],
            release_dates={
                "7.4.3": utc_now() - timedelta(days=40),
                "7.0.0": utc_now() - timedelta(days=500),
            },
            license="MIT",
            homepage="https://docs.pytest.org/",
            repository="https://github.com/pytest-dev/pytest",
            maintainers=["Pytest Team"],
            dependencies=["pluggy", "packaging"],
            download_count=120000000,
            description="pytest: simple powerful testing with Python",
            requires_python=">=3.7",
        ),
        "black": PackageInfo(
            name="black",
            latest_version="23.12.0",
            versions=["23.12.0", "23.0.0"],
            release_dates={
                "23.12.0": utc_now() - timedelta(days=10),
                "23.0.0": utc_now() - timedelta(days=300),
            },
            license="MIT",
            homepage="https://github.com/psf/black",
            repository="https://github.com/psf/black",
            maintainers=["Łukasz Langa"],
            dependencies=["click", "platformdirs"],
            download_count=40000000,
            description="The uncompromising code formatter.",
            requires_python=">=3.8",
        ),
        "mypy": PackageInfo(
            name="mypy",
            latest_version="1.7.1",
            versions=["1.7.1", "1.0.0"],
            release_dates={
                "1.7.1": utc_now() - timedelta(days=20),
                "1.0.0": utc_now() - timedelta(days=350),
            },
            license="MIT",
            homepage="http://www.mypy-lang.org/",
            repository="https://github.com/python/mypy",
            maintainers=["Jukka Lehtosalo"],
            dependencies=["typing-extensions"],
            download_count=35000000,
            description="Optional static typing for Python",
            requires_python=">=3.8",
        ),
        "flake8": PackageInfo(
            name="flake8",
            latest_version="6.1.0",
            versions=["6.1.0", "5.0.0"],
            release_dates={
                "6.1.0": utc_now() - timedelta(days=50),
                "5.0.0": utc_now() - timedelta(days=400),
            },
            license="MIT",
            homepage="https://github.com/PyCQA/flake8",
            repository="https://github.com/PyCQA/flake8",
            maintainers=["PyCQA Team"],
            dependencies=["mccabe", "pycodestyle", "pyflakes"],
            download_count=45000000,
            description="the modular source code checker",
            requires_python=">=3.8",
        ),
    }

    def get_package_info(name: str) -> Any:
        return package_data.get(name)

    mock_client.get_package_info.side_effect = get_package_info

    return mock_client


def main() -> None:
    """Run the demonstration."""
    print("=" * 80)
    print("DEPENDENCY HEALTH CHECKER DEMONSTRATION")
    print("=" * 80)
    print()

    # Create sample project
    print("Creating sample web application project...")
    project_path = create_sample_project()
    print(f"Project created at: {project_path}")
    print()

    # Create mock PyPI client
    mock_client = create_mock_pypi_client()

    # Create checker
    print("Initializing Dependency Health Checker...")
    checker = DependencyHealthChecker(
        pypi_client=mock_client,
        offline_mode=False,
        check_vulnerabilities=True,
    )

    # Add some vulnerabilities for demonstration
    checker._vuln_db = {
        "requests": [
            {
                "id": "CVE-2023-32681",
                "severity": "medium",
                "description": "Unintended leak of Proxy-Authorization header",
                "affected": "<2.31.0",
                "fixed": "2.31.0",
            }
        ],
        "flask": [
            {
                "id": "GHSA-m2qf-hxjv-5gpq",
                "severity": "high",
                "description": "Flask has possible disclosure of permanent session cookie",
                "affected": "<2.3.3",
                "fixed": "2.3.3",
            }
        ],
    }

    print("Running dependency health check...")
    print()

    # Run health check
    report = checker.check_health(project_path, include_dev=True)

    # Display report
    print("=" * 80)
    print(report)
    print("=" * 80)
    print()

    # Display vulnerable packages
    if report.vulnerable_count > 0:
        print("🔴 VULNERABLE PACKAGES:")
        print("-" * 80)
        for dep in report.get_vulnerable_dependencies():
            print(f"\n{dep.name} {dep.current_version}")
            for vuln in dep.vulnerabilities:
                print(f"  {vuln}")
        print()

    # Display outdated packages
    if report.outdated_count > 0:
        print("📦 OUTDATED PACKAGES:")
        print("-" * 80)
        update_emoji = {
            UpdateType.MAJOR: "🔴",
            UpdateType.MINOR: "🟡",
            UpdateType.PATCH: "🟢",
        }

        for dep in sorted(
            report.get_outdated_dependencies(),
            key=lambda d: d.health_score,
        ):
            emoji = update_emoji.get(dep.update_type, "⚪") if dep.update_type else "⚪"
            if dep.update_type:
                print(
                    f"{emoji} {dep.name:20} {dep.current_version:12} → {dep.latest_version:12} "
                    f"({dep.update_type.value:8} update, risk: {dep.update_type.risk_level})"
                )
            else:
                print(
                    f"{emoji} {dep.name:20} {dep.current_version:12} → {dep.latest_version:12} "
                    "(unknown update type)"
                )
        print()

    # Display recommendations
    print("💡 RECOMMENDATIONS:")
    print("-" * 80)
    for i, recommendation in enumerate(report.recommendations, 1):
        print(f"{i}. {recommendation}")
    print()

    # Display health scores
    print("📊 DETAILED HEALTH SCORES:")
    print("-" * 80)
    status_emoji = {
        HealthStatus.HEALTHY: "✅",
        HealthStatus.OUTDATED: "📦",
        HealthStatus.VULNERABLE: "🔴",
        HealthStatus.DEPRECATED: "⚠️",
        HealthStatus.UNKNOWN: "❓",
    }

    for dep in sorted(report.dependencies, key=lambda d: d.health_score):
        emoji = status_emoji.get(dep.health_status, "❓")
        print(
            f"{emoji} {dep.name:20} v{dep.current_version:12} "
            f"Health: {dep.health_score:5.1f}/100  "
            f"License: {dep.license or 'Unknown':15}"
        )
    print()

    print("=" * 80)
    print(f"OVERALL HEALTH SCORE: {report.overall_health_score:.1f}/100")
    print("=" * 80)
    print()

    # PyPI client statistics
    try:
        stats = checker.pypi_client.get_statistics()
        print("📈 PyPI CLIENT STATISTICS:")
        print("-" * 80)
        print(f"Total API requests: {stats['requests_made']}")
        print(f"Cached entries: {stats['cache_entries']}")
        print(f"Cache directory: {stats['cache_dir']}")
        print(f"Offline mode: {stats['offline_mode']}")
        print()
    except Exception:
        # Mock client doesn't support get_statistics
        pass

    print("✨ Demonstration complete!")


if __name__ == "__main__":
    main()
