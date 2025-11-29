"""Comprehensive tests for dependency health checker.

This module tests all aspects of the dependency health checker including:
- Parsing various dependency file formats
- Version comparison and update detection
- Vulnerability checking
- Deprecation detection
- License compatibility
- Circular dependency detection
"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock

import pytest
from qontinui_devtools.dependencies import (
    CircularDependency,
    DependencyHealthChecker,
    DependencyHealthReport,
    DependencyInfo,
    HealthStatus,
    LicenseCategory,
    LicenseConflict,
    UpdateType,
    VulnerabilityInfo,
)
from qontinui_devtools.dependencies.pypi_client import PackageInfo, PyPIClient


class TestPyPIClient:
    """Test PyPI client functionality."""

    def test_client_initialization(self):
        """Test client initializes with correct defaults."""
        client = PyPIClient()

        assert client.cache_dir.exists()
        assert client.cache_ttl == timedelta(hours=24)
        assert client.rate_limit == 1.0
        assert not client.offline_mode
        assert client.timeout == 10

    def test_client_offline_mode(self):
        """Test client respects offline mode."""
        client = PyPIClient(offline_mode=True)

        assert client.offline_mode
        result = client.get_package_info("requests")
        # Should return None in offline mode without cache
        assert result is None

    def test_normalize_package_name(self):
        """Test package name normalization."""
        client = PyPIClient()

        assert client._normalize_package_name("Django") == "django"
        assert client._normalize_package_name("django-rest-framework") == "django-rest-framework"
        assert client._normalize_package_name("Flask_SQLAlchemy") == "flask-sqlalchemy"

    def test_cache_file_generation(self):
        """Test cache file path generation."""
        client = PyPIClient()

        cache_file = client._get_cache_file("requests")

        assert cache_file.parent == client.cache_dir
        assert "requests" in cache_file.name
        assert cache_file.suffix == ".json"

    def test_parse_package_data(self):
        """Test parsing PyPI API response."""
        client = PyPIClient()

        mock_data = {
            "info": {
                "name": "requests",
                "version": "2.31.0",
                "license": "Apache-2.0",
                "home_page": "https://requests.readthedocs.io",
                "summary": "Python HTTP for Humans.",
                "author": "Kenneth Reitz",
                "requires_python": ">=3.7",
                "requires_dist": [
                    "charset-normalizer (<4,>=2)",
                    "idna (<4,>=2.5)",
                    "urllib3 (<3,>=1.21.1)",
                ],
            },
            "releases": {
                "2.31.0": [
                    {
                        "upload_time_iso_8601": "2023-05-22T13:00:00Z",
                    }
                ],
                "2.30.0": [
                    {
                        "upload_time_iso_8601": "2023-05-01T10:00:00Z",
                    }
                ],
            },
        }

        package_info = client._parse_package_data(mock_data)

        assert package_info.name == "requests"
        assert package_info.latest_version == "2.31.0"
        assert "2.31.0" in package_info.versions
        assert "2.30.0" in package_info.versions
        assert package_info.license == "Apache-2.0"
        assert package_info.homepage == "https://requests.readthedocs.io"
        assert "Kenneth Reitz" in package_info.maintainers
        assert len(package_info.dependencies) == 3
        assert "charset-normalizer" in package_info.dependencies

    def test_get_latest_version_cached(self):
        """Test getting latest version from cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            client = PyPIClient(cache_dir=cache_dir)

            # Create cached data
            mock_data = {
                "info": {"name": "requests", "version": "2.31.0"},
                "releases": {},
            }

            cache_file = client._get_cache_file("requests")
            with open(cache_file, "w") as f:
                json.dump(mock_data, f)

            version = client.get_latest_version("requests")
            assert version == "2.31.0"

    def test_clear_cache_specific_package(self):
        """Test clearing cache for specific package."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            client = PyPIClient(cache_dir=cache_dir)

            # Create cached files
            cache_file1 = client._get_cache_file("requests")
            cache_file2 = client._get_cache_file("flask")

            cache_file1.touch()
            cache_file2.touch()

            assert cache_file1.exists()
            assert cache_file2.exists()

            client.clear_cache("requests")

            assert not cache_file1.exists()
            assert cache_file2.exists()

    def test_clear_cache_all(self):
        """Test clearing all cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            client = PyPIClient(cache_dir=cache_dir)

            # Create cached files
            cache_file1 = client._get_cache_file("requests")
            cache_file2 = client._get_cache_file("flask")

            cache_file1.touch()
            cache_file2.touch()

            client.clear_cache()

            assert not cache_file1.exists()
            assert not cache_file2.exists()

    def test_get_statistics(self):
        """Test getting client statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            client = PyPIClient(cache_dir=cache_dir)

            stats = client.get_statistics()

            assert "requests_made" in stats
            assert "cache_entries" in stats
            assert "cache_dir" in stats
            assert "offline_mode" in stats


class TestDependencyModels:
    """Test dependency data models."""

    def test_health_status_enum(self):
        """Test HealthStatus enum."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.OUTDATED.value == "outdated"
        assert HealthStatus.VULNERABLE.value == "vulnerable"
        assert HealthStatus.DEPRECATED.value == "deprecated"

    def test_health_status_severity(self):
        """Test health status severity scores."""
        assert HealthStatus.VULNERABLE.severity == 4
        assert HealthStatus.DEPRECATED.severity == 3
        assert HealthStatus.OUTDATED.severity == 2
        assert HealthStatus.HEALTHY.severity == 0

    def test_update_type_enum(self):
        """Test UpdateType enum."""
        assert UpdateType.MAJOR.value == "major"
        assert UpdateType.MINOR.value == "minor"
        assert UpdateType.PATCH.value == "patch"

    def test_update_type_risk_level(self):
        """Test update type risk levels."""
        assert UpdateType.MAJOR.risk_level == "high"
        assert UpdateType.MINOR.risk_level == "medium"
        assert UpdateType.PATCH.risk_level == "low"

    def test_vulnerability_info_creation(self):
        """Test VulnerabilityInfo creation."""
        vuln = VulnerabilityInfo(
            id="CVE-2023-12345",
            severity="high",
            description="Test vulnerability",
            affected_versions="<1.0.0",
            fixed_version="1.0.0",
        )

        assert vuln.id == "CVE-2023-12345"
        assert vuln.severity == "high"
        assert vuln.severity_score == 3
        assert "CVE-2023-12345" in str(vuln)

    def test_vulnerability_severity_score(self):
        """Test vulnerability severity scoring."""
        critical = VulnerabilityInfo(
            id="CVE-1", severity="critical", description="Test", affected_versions="*"
        )
        high = VulnerabilityInfo(
            id="CVE-2", severity="high", description="Test", affected_versions="*"
        )
        medium = VulnerabilityInfo(
            id="CVE-3", severity="medium", description="Test", affected_versions="*"
        )
        low = VulnerabilityInfo(
            id="CVE-4", severity="low", description="Test", affected_versions="*"
        )

        assert critical.severity_score == 4
        assert high.severity_score == 3
        assert medium.severity_score == 2
        assert low.severity_score == 1

    def test_dependency_info_creation(self):
        """Test DependencyInfo creation."""
        dep = DependencyInfo(
            name="requests",
            current_version="2.28.0",
            latest_version="2.31.0",
            update_type=UpdateType.MINOR,
            health_status=HealthStatus.OUTDATED,
        )

        assert dep.name == "requests"
        assert dep.current_version == "2.28.0"
        assert dep.latest_version == "2.31.0"
        assert dep.is_outdated
        assert not dep.has_vulnerabilities
        assert not dep.is_deprecated

    def test_dependency_info_health_score_healthy(self):
        """Test health score for healthy dependency."""
        dep = DependencyInfo(
            name="requests",
            current_version="2.31.0",
            latest_version="2.31.0",
            health_status=HealthStatus.HEALTHY,
        )

        assert dep.health_score == 100.0

    def test_dependency_info_health_score_outdated(self):
        """Test health score for outdated dependency."""
        dep = DependencyInfo(
            name="requests",
            current_version="2.28.0",
            latest_version="2.31.0",
            update_type=UpdateType.MAJOR,
            health_status=HealthStatus.OUTDATED,
        )

        assert dep.health_score == 85.0  # 100 - 15 for major update

    def test_dependency_info_health_score_vulnerable(self):
        """Test health score for vulnerable dependency."""
        vuln = VulnerabilityInfo(
            id="CVE-2023-12345",
            severity="critical",
            description="Critical vulnerability",
            affected_versions="<2.31.0",
        )

        dep = DependencyInfo(
            name="requests",
            current_version="2.28.0",
            health_status=HealthStatus.VULNERABLE,
            vulnerabilities=[vuln],
        )

        assert dep.health_score == 70.0  # 100 - 30 for critical vuln

    def test_dependency_info_health_score_deprecated(self):
        """Test health score for deprecated dependency."""
        dep = DependencyInfo(
            name="nose",
            current_version="1.3.7",
            health_status=HealthStatus.DEPRECATED,
            deprecation_notice="Use pytest instead",
        )

        assert dep.health_score == 75.0  # 100 - 25 for deprecation

    def test_circular_dependency(self):
        """Test CircularDependency model."""
        circular = CircularDependency(
            chain=["package-a", "package-b", "package-c"],
            severity="high",
        )

        assert "package-a" in str(circular)
        assert "package-b" in str(circular)
        assert "package-c" in str(circular)

    def test_license_conflict(self):
        """Test LicenseConflict model."""
        conflict = LicenseConflict(
            package1="package-a",
            license1="GPL-3.0",
            package2="package-b",
            license2="MIT",
            conflict_reason="GPL incompatible with MIT",
        )

        assert "package-a" in str(conflict)
        assert "GPL-3.0" in str(conflict)

    def test_dependency_health_report(self):
        """Test DependencyHealthReport creation."""
        report = DependencyHealthReport(
            total_dependencies=10,
            healthy_count=7,
            outdated_count=2,
            vulnerable_count=1,
            deprecated_count=0,
            overall_health_score=85.5,
        )

        assert report.total_dependencies == 10
        assert report.healthy_count == 7
        assert not report.has_critical_issues
        assert report.needs_updates

    def test_dependency_health_report_str(self):
        """Test report string representation."""
        report = DependencyHealthReport(
            total_dependencies=5,
            healthy_count=3,
            outdated_count=2,
            vulnerable_count=0,
            deprecated_count=0,
            overall_health_score=90.0,
        )

        report_str = str(report)

        assert "Total Dependencies: 5" in report_str
        assert "Overall Health Score: 90.0/100" in report_str
        assert "Healthy:     3" in report_str


class TestDependencyHealthChecker:
    """Test dependency health checker."""

    @pytest.fixture
    def mock_pypi_client(self):
        """Create mock PyPI client."""
        client = Mock(spec=PyPIClient)
        return client

    @pytest.fixture
    def checker(self, mock_pypi_client):
        """Create checker with mock client."""
        return DependencyHealthChecker(
            pypi_client=mock_pypi_client,
            offline_mode=True,
            check_vulnerabilities=False,
        )

    @pytest.fixture
    def temp_project(self):
        """Create temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_checker_initialization(self):
        """Test checker initializes correctly."""
        checker = DependencyHealthChecker()

        assert checker.pypi_client is not None
        assert not checker.offline_mode
        assert checker.check_vulnerabilities

    def test_parse_requirement_spec_simple(self, checker):
        """Test parsing simple requirement spec."""
        name, version = checker._parse_requirement_spec("requests==2.31.0")

        assert name == "requests"
        assert version == "2.31.0"

    def test_parse_requirement_spec_operator(self, checker):
        """Test parsing requirement with operator."""
        name, version = checker._parse_requirement_spec("requests>=2.28.0")

        assert name == "requests"
        assert version == "2.28.0"

    def test_parse_requirement_spec_extras(self, checker):
        """Test parsing requirement with extras."""
        name, version = checker._parse_requirement_spec("requests[security]>=2.28.0")

        assert name == "requests"
        assert version == "2.28.0"

    def test_parse_requirement_spec_complex(self, checker):
        """Test parsing complex requirement."""
        name, version = checker._parse_requirement_spec("Django>=3.2,<4.0")

        assert name == "Django"
        assert "3.2" in version

    def test_extract_version_string(self, checker):
        """Test extracting version from string."""
        version = checker._extract_version(">=2.28.0")
        assert version == "2.28.0"

        version = checker._extract_version("^1.0.0")
        assert version == "1.0.0"

        version = checker._extract_version("*")
        assert version == "*"

    def test_extract_version_dict(self, checker):
        """Test extracting version from dict."""
        version = checker._extract_version({"version": "2.28.0"})
        assert version == "2.28.0"

    def test_parse_requirements_txt(self, checker, temp_project):
        """Test parsing requirements.txt."""
        requirements_file = temp_project / "requirements.txt"
        requirements_file.write_text(
            """# Dependencies
requests==2.31.0
flask>=2.0.0
django~=4.2.0

# Development
pytest>=7.0.0
"""
        )

        deps = checker._parse_requirements_txt(requirements_file)

        assert "requests" in deps
        assert deps["requests"] == "2.31.0"
        assert "flask" in deps
        assert deps["flask"] == "2.0.0"
        assert "django" in deps
        assert "pytest" in deps

    def test_parse_pyproject_toml_poetry(self, checker, temp_project):
        """Test parsing pyproject.toml with Poetry format."""
        pyproject_file = temp_project / "pyproject.toml"
        pyproject_file.write_text(
            """[tool.poetry]
name = "test-project"
version = "1.0.0"

[tool.poetry.dependencies]
python = "^3.9"
requests = "^2.31.0"
flask = ">=2.0.0"

[tool.poetry.dev-dependencies]
pytest = "^7.0.0"
black = "^23.0.0"
"""
        )

        deps = checker._parse_pyproject_toml(pyproject_file, include_dev=True)

        assert "requests" in deps
        assert deps["requests"] == "2.31.0"
        assert "flask" in deps
        assert "pytest" in deps
        assert "_dev_pytest" in deps

    def test_parse_pyproject_toml_pep621(self, checker, temp_project):
        """Test parsing pyproject.toml with PEP 621 format."""
        pyproject_file = temp_project / "pyproject.toml"
        pyproject_file.write_text(
            """[project]
name = "test-project"
version = "1.0.0"
dependencies = [
    "requests>=2.31.0",
    "flask>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "black>=23.0.0",
]
"""
        )

        deps = checker._parse_pyproject_toml(pyproject_file, include_dev=True)

        assert "requests" in deps
        assert "flask" in deps
        assert "pytest" in deps
        assert "_dev_pytest" in deps

    def test_parse_poetry_lock(self, checker, temp_project):
        """Test parsing poetry.lock."""
        poetry_lock = temp_project / "poetry.lock"
        poetry_lock.write_text(
            """[[package]]
name = "requests"
version = "2.31.0"
category = "main"

[[package]]
name = "pytest"
version = "7.4.0"
category = "dev"
"""
        )

        deps = checker._parse_poetry_lock(poetry_lock, include_dev=True)

        assert "requests" in deps
        assert deps["requests"] == "2.31.0"
        assert "pytest" in deps
        assert deps["pytest"] == "7.4.0"
        assert "_dev_pytest" in deps

    def test_parse_setup_py(self, checker, temp_project):
        """Test parsing setup.py."""
        setup_py = temp_project / "setup.py"
        setup_py.write_text(
            """from setuptools import setup

setup(
    name='test-project',
    version='1.0.0',
    install_requires=[
        'requests>=2.31.0',
        'flask>=2.0.0',
        'django~=4.2.0',
    ],
)
"""
        )

        deps = checker._parse_setup_py(setup_py)

        assert "requests" in deps
        assert "flask" in deps
        assert "django" in deps

    def test_parse_semver_valid(self, checker):
        """Test parsing valid semantic versions."""
        version = checker._parse_semver("2.31.0")
        assert version == (2, 31, 0, "")

        version = checker._parse_semver("1.0.0-alpha.1")
        assert version == (1, 0, 0, "alpha.1")

    def test_parse_semver_invalid(self, checker):
        """Test parsing invalid versions."""
        version = checker._parse_semver("invalid")
        assert version is None

    def test_compare_versions_major(self, checker):
        """Test major version comparison."""
        update_type = checker._compare_versions("1.0.0", "2.0.0")
        assert update_type == UpdateType.MAJOR

    def test_compare_versions_minor(self, checker):
        """Test minor version comparison."""
        update_type = checker._compare_versions("2.28.0", "2.31.0")
        assert update_type == UpdateType.MINOR

    def test_compare_versions_patch(self, checker):
        """Test patch version comparison."""
        update_type = checker._compare_versions("2.31.0", "2.31.5")
        assert update_type == UpdateType.PATCH

    def test_compare_versions_same(self, checker):
        """Test comparing same versions."""
        update_type = checker._compare_versions("2.31.0", "2.31.0")
        assert update_type is None

    def test_compare_versions_with_operators(self, checker):
        """Test comparing versions with operators."""
        update_type = checker._compare_versions(">=2.28.0", "2.31.0")
        assert update_type == UpdateType.MINOR

    def test_categorize_license_permissive(self, checker):
        """Test categorizing permissive licenses."""
        assert checker._categorize_license("MIT") == LicenseCategory.PERMISSIVE
        assert checker._categorize_license("BSD-3-Clause") == LicenseCategory.PERMISSIVE
        assert checker._categorize_license("Apache-2.0") == LicenseCategory.PERMISSIVE

    def test_categorize_license_copyleft(self, checker):
        """Test categorizing copyleft licenses."""
        assert checker._categorize_license("GPL-3.0") == LicenseCategory.COPYLEFT
        assert checker._categorize_license("LGPL-2.1") == LicenseCategory.COPYLEFT

    def test_categorize_license_unknown(self, checker):
        """Test categorizing unknown licenses."""
        assert checker._categorize_license(None) == LicenseCategory.UNKNOWN
        assert checker._categorize_license("Custom License") == LicenseCategory.UNKNOWN

    def test_determine_health_status_vulnerable(self, checker):
        """Test determining health status with vulnerabilities."""
        vulns = [
            VulnerabilityInfo(
                id="CVE-123",
                severity="high",
                description="Test",
                affected_versions="*",
            )
        ]

        status = checker._determine_health_status("2.28.0", "2.31.0", vulns, None)
        assert status == HealthStatus.VULNERABLE

    def test_determine_health_status_deprecated(self, checker):
        """Test determining health status for deprecated package."""
        status = checker._determine_health_status("1.0.0", "1.0.0", [], "Use pytest instead")
        assert status == HealthStatus.DEPRECATED

    def test_determine_health_status_outdated(self, checker):
        """Test determining health status for outdated package."""
        status = checker._determine_health_status("2.28.0", "2.31.0", [], None)
        assert status == HealthStatus.OUTDATED

    def test_determine_health_status_healthy(self, checker):
        """Test determining health status for healthy package."""
        status = checker._determine_health_status("2.31.0", "2.31.0", [], None)
        assert status == HealthStatus.HEALTHY

    def test_detect_circular_dependencies_simple(self, checker):
        """Test detecting simple circular dependency."""
        deps = [
            DependencyInfo(
                name="package-a",
                current_version="1.0.0",
                dependencies=["package-b"],
            ),
            DependencyInfo(
                name="package-b",
                current_version="1.0.0",
                dependencies=["package-a"],
            ),
        ]

        circular = checker._detect_circular_dependencies(deps)

        assert len(circular) > 0

    def test_detect_circular_dependencies_complex(self, checker):
        """Test detecting complex circular dependency chain."""
        deps = [
            DependencyInfo(
                name="package-a",
                current_version="1.0.0",
                dependencies=["package-b"],
            ),
            DependencyInfo(
                name="package-b",
                current_version="1.0.0",
                dependencies=["package-c"],
            ),
            DependencyInfo(
                name="package-c",
                current_version="1.0.0",
                dependencies=["package-a"],
            ),
        ]

        circular = checker._detect_circular_dependencies(deps)

        assert len(circular) > 0

    def test_detect_circular_dependencies_none(self, checker):
        """Test detecting no circular dependencies."""
        deps = [
            DependencyInfo(
                name="package-a",
                current_version="1.0.0",
                dependencies=["package-b"],
            ),
            DependencyInfo(
                name="package-b",
                current_version="1.0.0",
                dependencies=[],
            ),
        ]

        circular = checker._detect_circular_dependencies(deps)

        assert len(circular) == 0

    def test_check_license_conflicts(self, checker):
        """Test checking license conflicts."""
        deps = [
            DependencyInfo(
                name="package-gpl",
                current_version="1.0.0",
                license="GPL-3.0",
                license_category=LicenseCategory.COPYLEFT,
            ),
            DependencyInfo(
                name="package-mit",
                current_version="1.0.0",
                license="MIT",
                license_category=LicenseCategory.PERMISSIVE,
            ),
        ]

        conflicts = checker._check_license_conflicts(deps)

        assert len(conflicts) > 0
        assert any("GPL" in str(c) for c in conflicts)

    def test_calculate_health_score_perfect(self, checker):
        """Test calculating health score for perfect dependencies."""
        deps = [
            DependencyInfo(
                name=f"package-{i}",
                current_version="1.0.0",
                latest_version="1.0.0",
                health_status=HealthStatus.HEALTHY,
            )
            for i in range(5)
        ]

        score = checker._calculate_health_score(deps)
        assert score == 100.0

    def test_calculate_health_score_mixed(self, checker):
        """Test calculating health score for mixed dependencies."""
        deps = [
            DependencyInfo(
                name="healthy",
                current_version="1.0.0",
                latest_version="1.0.0",
                health_status=HealthStatus.HEALTHY,
            ),
            DependencyInfo(
                name="outdated",
                current_version="1.0.0",
                latest_version="2.0.0",
                update_type=UpdateType.MAJOR,
                health_status=HealthStatus.OUTDATED,
            ),
        ]

        score = checker._calculate_health_score(deps)
        assert 80 < score < 100

    def test_generate_recommendations_critical_vuln(self, checker):
        """Test recommendations for critical vulnerabilities."""
        deps = [
            DependencyInfo(
                name="vulnerable",
                current_version="1.0.0",
                health_status=HealthStatus.VULNERABLE,
                vulnerabilities=[
                    VulnerabilityInfo(
                        id="CVE-123",
                        severity="critical",
                        description="Critical vuln",
                        affected_versions="*",
                    )
                ],
            )
        ]

        recommendations = checker._generate_recommendations(deps, [], [])

        assert any("URGENT" in rec for rec in recommendations)
        assert any("critical" in rec.lower() for rec in recommendations)

    def test_generate_recommendations_deprecated(self, checker):
        """Test recommendations for deprecated packages."""
        deps = [
            DependencyInfo(
                name="nose",
                current_version="1.3.7",
                health_status=HealthStatus.DEPRECATED,
                deprecation_notice="Use pytest",
            )
        ]

        recommendations = checker._generate_recommendations(deps, [], [])

        assert any("deprecated" in rec.lower() for rec in recommendations)

    def test_generate_recommendations_healthy(self, checker):
        """Test recommendations for healthy dependencies."""
        deps = [
            DependencyInfo(
                name="requests",
                current_version="2.31.0",
                latest_version="2.31.0",
                health_status=HealthStatus.HEALTHY,
            )
        ]

        recommendations = checker._generate_recommendations(deps, [], [])

        assert any("healthy" in rec.lower() for rec in recommendations)

    def test_check_health_integration(self, temp_project):
        """Test full health check integration."""
        # Create a test project with requirements
        requirements_file = temp_project / "requirements.txt"
        requirements_file.write_text("requests==2.31.0\nflask>=2.0.0")

        # Create checker with mocked PyPI client
        mock_client = Mock(spec=PyPIClient)
        mock_client.get_package_info.return_value = PackageInfo(
            name="requests",
            latest_version="2.31.0",
            versions=["2.31.0", "2.30.0"],
            release_dates={"2.31.0": datetime.now()},
            license="Apache-2.0",
            homepage="https://requests.readthedocs.io",
            repository=None,
            maintainers=["Kenneth Reitz"],
            dependencies=["urllib3", "certifi"],
            download_count=1000000,
            description="HTTP library",
            requires_python=">=3.7",
        )

        checker = DependencyHealthChecker(
            pypi_client=mock_client,
            check_vulnerabilities=False,
        )

        report = checker.check_health(temp_project)

        assert report.total_dependencies > 0
        assert report.overall_health_score > 0
        assert len(report.recommendations) > 0

    def test_check_health_nonexistent_project(self, checker):
        """Test health check on nonexistent project."""
        with pytest.raises(FileNotFoundError):
            checker.check_health("/nonexistent/path")

    def test_analyze_dependency_with_mock_data(self, checker):
        """Test analyzing dependency with mocked PyPI data."""
        mock_info = PackageInfo(
            name="requests",
            latest_version="2.31.0",
            versions=["2.31.0", "2.30.0"],
            release_dates={"2.31.0": datetime.now()},
            license="Apache-2.0",
            homepage="https://requests.readthedocs.io",
            repository=None,
            maintainers=["Kenneth Reitz"],
            dependencies=["urllib3", "certifi"],
            download_count=1000000,
            description="HTTP library",
            requires_python=">=3.7",
        )

        checker.pypi_client.get_package_info.return_value = mock_info

        dep_info = checker._analyze_dependency("requests", "2.28.0")

        assert dep_info.name == "requests"
        assert dep_info.current_version == "2.28.0"
        assert dep_info.latest_version == "2.31.0"
        assert dep_info.update_type == UpdateType.MINOR
        assert dep_info.license == "Apache-2.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
