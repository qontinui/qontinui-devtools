"""Dependency health checker for Python projects.

This module provides comprehensive dependency health checking including:
- Parsing pyproject.toml, requirements.txt, setup.py, poetry.lock
- Checking for outdated packages
- Security vulnerability detection
- Deprecated package detection
- License compatibility analysis
- Dependency tree analysis
- Circular dependency detection
"""

import json
import re
import tomllib
from pathlib import Path
from typing import Any

from .models import (
    CircularDependency,
    DependencyHealthReport,
    DependencyInfo,
    HealthStatus,
    LicenseCategory,
    LicenseConflict,
    UpdateType,
    VulnerabilityInfo,
)
from .pypi_client import PyPIClient


class DependencyHealthChecker:
    """Comprehensive dependency health checker for Python projects."""

    # Known deprecated packages
    DEPRECATED_PACKAGES = {
        "pkg-resources": "Use importlib.metadata instead",
        "nose": "Use pytest instead",
        "optparse": "Use argparse instead",
        "imp": "Use importlib instead",
    }

    # License compatibility matrix
    LICENSE_CATEGORIES = {
        "MIT": LicenseCategory.PERMISSIVE,
        "BSD": LicenseCategory.PERMISSIVE,
        "Apache": LicenseCategory.PERMISSIVE,
        "Apache-2.0": LicenseCategory.PERMISSIVE,
        "ISC": LicenseCategory.PERMISSIVE,
        "PSF": LicenseCategory.PERMISSIVE,
        "GPL": LicenseCategory.COPYLEFT,
        "GPLv2": LicenseCategory.COPYLEFT,
        "GPLv3": LicenseCategory.COPYLEFT,
        "LGPL": LicenseCategory.COPYLEFT,
        "AGPL": LicenseCategory.COPYLEFT,
    }

    def __init__(
        self,
        pypi_client: PyPIClient | None = None,
        offline_mode: bool = False,
        check_vulnerabilities: bool = True,
        cache_dir: Path | None = None,
    ):
        """Initialize dependency health checker.

        Args:
            pypi_client: PyPI client instance
            offline_mode: Use only cached data
            check_vulnerabilities: Enable vulnerability checking
            cache_dir: Cache directory for vulnerability data
        """
        self.pypi_client = pypi_client or PyPIClient(offline_mode=offline_mode)
        self.offline_mode = offline_mode
        self.check_vulnerabilities = check_vulnerabilities
        self.cache_dir = cache_dir or Path.home() / ".cache" / "qontinui-devtools"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Load vulnerability database
        self._vuln_db = self._load_vulnerability_db()

    def check_health(
        self,
        project_path: str | Path,
        fail_on_vulnerable: bool = False,
        include_dev: bool = True,
    ) -> DependencyHealthReport:
        """Check dependency health for a project.

        Args:
            project_path: Path to the project directory
            fail_on_vulnerable: Raise exception on vulnerabilities
            include_dev: Include dev dependencies

        Returns:
            DependencyHealthReport with comprehensive analysis

        Raises:
            ValueError: If fail_on_vulnerable and vulnerabilities found
        """
        project_path = Path(project_path)

        if not project_path.exists():
            raise FileNotFoundError(f"Project path not found: {project_path}")

        # Parse dependencies from all sources
        dependencies = self._parse_dependencies(project_path, include_dev)

        # Analyze each dependency
        analyzed_deps: list[DependencyInfo] = []
        for dep_name, dep_version in dependencies.items():
            info = self._analyze_dependency(
                dep_name,
                dep_version,
                is_dev=dependencies.get(f"_dev_{dep_name}", False),
            )
            analyzed_deps.append(info)

        # Detect circular dependencies
        circular_deps = self._detect_circular_dependencies(analyzed_deps)

        # Check license conflicts
        license_conflicts = self._check_license_conflicts(analyzed_deps)

        # Calculate tree depth
        max_depth = max((dep.tree_depth for dep in analyzed_deps), default=0)

        # Generate statistics
        healthy = sum(1 for dep in analyzed_deps if dep.health_status == HealthStatus.HEALTHY)
        outdated = sum(1 for dep in analyzed_deps if dep.is_outdated)
        vulnerable = sum(1 for dep in analyzed_deps if dep.has_vulnerabilities)
        deprecated = sum(1 for dep in analyzed_deps if dep.is_deprecated)

        total_vulns = sum(len(dep.vulnerabilities) for dep in analyzed_deps)
        critical_vulns = sum(
            1
            for dep in analyzed_deps
            for vuln in dep.vulnerabilities
            if vuln.severity == "critical"
        )

        # Calculate overall health score
        health_score = self._calculate_health_score(analyzed_deps)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            analyzed_deps, circular_deps, license_conflicts
        )

        report = DependencyHealthReport(
            total_dependencies=len(analyzed_deps),
            healthy_count=healthy,
            outdated_count=outdated,
            vulnerable_count=vulnerable,
            deprecated_count=deprecated,
            dependencies=analyzed_deps,
            overall_health_score=health_score,
            recommendations=recommendations,
            circular_dependencies=circular_deps,
            license_conflicts=license_conflicts,
            max_tree_depth=max_depth,
            total_vulnerabilities=total_vulns,
            critical_vulnerabilities=critical_vulns,
            metadata={"project_path": str(project_path)},
        )

        if fail_on_vulnerable and critical_vulns > 0:
            raise ValueError(
                f"Critical vulnerabilities found: {critical_vulns}. "
                "Run without fail_on_vulnerable to see details."
            )

        return report

    def _parse_dependencies(self, project_path: Path, include_dev: bool) -> dict[str, str]:
        """Parse dependencies from all available sources.

        Args:
            project_path: Path to project directory
            include_dev: Include dev dependencies

        Returns:
            Dictionary mapping package names to versions
        """
        dependencies: dict[str, str] = {}

        # Try pyproject.toml
        pyproject_file = project_path / "pyproject.toml"
        if pyproject_file.exists():
            deps = self._parse_pyproject_toml(pyproject_file, include_dev)
            dependencies.update(deps)

        # Try requirements.txt
        requirements_file = project_path / "requirements.txt"
        if requirements_file.exists():
            deps = self._parse_requirements_txt(requirements_file)
            dependencies.update(deps)

        # Try poetry.lock
        poetry_lock = project_path / "poetry.lock"
        if poetry_lock.exists():
            deps = self._parse_poetry_lock(poetry_lock, include_dev)
            dependencies.update(deps)

        # Try setup.py (basic parsing)
        setup_py = project_path / "setup.py"
        if setup_py.exists():
            deps = self._parse_setup_py(setup_py)
            dependencies.update(deps)

        return dependencies

    def _parse_pyproject_toml(self, file_path: Path, include_dev: bool) -> dict[str, str]:
        """Parse dependencies from pyproject.toml.

        Args:
            file_path: Path to pyproject.toml
            include_dev: Include dev dependencies

        Returns:
            Dictionary of dependencies
        """
        dependencies: dict[str, str] = {}

        with open(file_path, "rb") as f:
            data = tomllib.load(f)

        # Poetry format
        if "tool" in data and "poetry" in data["tool"]:
            poetry = data["tool"]["poetry"]

            # Main dependencies
            if "dependencies" in poetry:
                for name, spec in poetry["dependencies"].items():
                    if name == "python":
                        continue
                    version = self._extract_version(spec)
                    dependencies[name] = version

            # Dev dependencies
            if include_dev and "dev-dependencies" in poetry:
                for name, spec in poetry["dev-dependencies"].items():
                    version = self._extract_version(spec)
                    dependencies[name] = version
                    dependencies[f"_dev_{name}"] = True

        # PEP 621 format
        if "project" in data:
            project = data["project"]

            # Main dependencies
            if "dependencies" in project:
                for spec in project["dependencies"]:
                    name, version = self._parse_requirement_spec(spec)
                    dependencies[name] = version

            # Optional dependencies
            if include_dev and "optional-dependencies" in project:
                for _group, deps in project["optional-dependencies"].items():
                    for spec in deps:
                        name, version = self._parse_requirement_spec(spec)
                        dependencies[name] = version
                        dependencies[f"_dev_{name}"] = True

        return dependencies

    def _parse_requirements_txt(self, file_path: Path) -> dict[str, str]:
        """Parse dependencies from requirements.txt.

        Args:
            file_path: Path to requirements.txt

        Returns:
            Dictionary of dependencies
        """
        dependencies: dict[str, str] = {}

        with open(file_path) as f:
            for line in f:
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue

                # Skip -e and -r flags
                if line.startswith("-"):
                    continue

                name, version = self._parse_requirement_spec(line)
                if name:
                    dependencies[name] = version

        return dependencies

    def _parse_poetry_lock(self, file_path: Path, include_dev: bool) -> dict[str, str]:
        """Parse dependencies from poetry.lock.

        Args:
            file_path: Path to poetry.lock
            include_dev: Include dev dependencies

        Returns:
            Dictionary of dependencies
        """
        dependencies: dict[str, str] = {}

        with open(file_path, "rb") as f:
            data = tomllib.load(f)

        if "package" in data:
            for package in data["package"]:
                name = package.get("name", "")
                version = package.get("version", "")
                is_dev = package.get("category") == "dev"

                if not include_dev and is_dev:
                    continue

                dependencies[name] = version
                if is_dev:
                    dependencies[f"_dev_{name}"] = True

        return dependencies

    def _parse_setup_py(self, file_path: Path) -> dict[str, str]:
        """Parse dependencies from setup.py (basic regex-based).

        Args:
            file_path: Path to setup.py

        Returns:
            Dictionary of dependencies
        """
        dependencies: dict[str, str] = {}

        with open(file_path) as f:
            content = f.read()

        # Look for install_requires
        install_requires_match = re.search(r"install_requires\s*=\s*\[(.*?)\]", content, re.DOTALL)

        if install_requires_match:
            requires_str = install_requires_match.group(1)
            # Extract strings
            for match in re.finditer(r'["\']([^"\']+)["\']', requires_str):
                spec = match.group(1)
                name, version = self._parse_requirement_spec(spec)
                if name:
                    dependencies[name] = version

        return dependencies

    def _parse_requirement_spec(self, spec: str) -> tuple[str, str]:
        """Parse a requirement specification.

        Args:
            spec: Requirement string (e.g., "requests>=2.28.0")

        Returns:
            Tuple of (name, version)
        """
        # Remove extras [extra1,extra2]
        spec = re.sub(r"\[.*?\]", "", spec)

        # Match name and version
        match = re.match(r"^([a-zA-Z0-9\-_\.]+)\s*([><=!~]+)?\s*(.*)$", spec.strip())

        if match:
            name = match.group(1)
            match.group(2) or ""
            version = match.group(3).strip() or "*"

            # Clean up version
            version = version.strip("\"' ")

            return name, version

        return "", ""

    def _extract_version(self, spec: str | dict[str, Any]) -> str:
        """Extract version from various specification formats.

        Args:
            spec: Version specification

        Returns:
            Version string
        """
        if isinstance(spec, str):
            # Remove operators
            version = re.sub(r"^[><=!~^]+", "", spec).strip()
            return version or "*"

        if isinstance(spec, dict):
            if "version" in spec:
                return self._extract_version(spec["version"])

        return "*"

    def _analyze_dependency(
        self, name: str, current_version: str, is_dev: bool = False
    ) -> DependencyInfo:
        """Analyze a single dependency.

        Args:
            name: Package name
            current_version: Current version
            is_dev: Is dev dependency

        Returns:
            DependencyInfo with analysis results
        """
        # Fetch package info from PyPI
        pypi_info = self.pypi_client.get_package_info(name)

        if not pypi_info:
            return DependencyInfo(
                name=name,
                current_version=current_version,
                health_status=HealthStatus.UNKNOWN,
                is_dev_dependency=is_dev,
            )

        # Determine update type and latest version
        latest_version = pypi_info.latest_version
        update_type = self._compare_versions(current_version, latest_version)

        # Check for vulnerabilities
        vulnerabilities: list[Any] = []
        if self.check_vulnerabilities:
            vulnerabilities = self._check_vulnerabilities(name, current_version)

        # Check for deprecation
        deprecation_notice = self.DEPRECATED_PACKAGES.get(name.lower())

        # Determine health status
        health_status = self._determine_health_status(
            current_version, latest_version, vulnerabilities, deprecation_notice
        )

        # Categorize license
        license_category = self._categorize_license(pypi_info.license)

        # Get release date
        release_date = pypi_info.get_release_date(current_version)

        return DependencyInfo(
            name=name,
            current_version=current_version,
            latest_version=latest_version,
            update_type=update_type,
            health_status=health_status,
            vulnerabilities=vulnerabilities,
            last_release_date=release_date,
            license=pypi_info.license,
            license_category=license_category,
            deprecation_notice=deprecation_notice,
            homepage=pypi_info.homepage,
            repository=pypi_info.repository,
            maintainers=pypi_info.maintainers,
            dependencies=pypi_info.dependencies,
            download_count=pypi_info.download_count,
            is_dev_dependency=is_dev,
        )

    def _compare_versions(self, current: str, latest: str) -> UpdateType | None:
        """Compare versions and determine update type.

        Args:
            current: Current version
            latest: Latest version

        Returns:
            UpdateType or None if same
        """
        if current == "*" or current == latest:
            return None

        # Remove version operators
        current_clean = re.sub(r"^[><=!~^]+", "", current).strip()
        latest_clean = latest.strip()

        # Parse semantic versions
        current_parts = self._parse_semver(current_clean)
        latest_parts = self._parse_semver(latest_clean)

        if not current_parts or not latest_parts:
            return UpdateType.UNKNOWN

        # Compare versions
        if latest_parts[0] > current_parts[0]:
            return UpdateType.MAJOR
        elif latest_parts[1] > current_parts[1]:
            return UpdateType.MINOR
        elif latest_parts[2] > current_parts[2]:
            return UpdateType.PATCH

        # Check for prerelease
        if len(latest_parts) > 3 and latest_parts[3]:
            return UpdateType.PRERELEASE

        return None

    def _parse_semver(self, version: str) -> tuple[int, int, int, str] | None:
        """Parse semantic version string.

        Args:
            version: Version string

        Returns:
            Tuple of (major, minor, patch, prerelease) or None
        """
        # Match X.Y.Z or X.Y.Z-prerelease
        match = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:-(.+))?", version)

        if match:
            major = int(match.group(1))
            minor = int(match.group(2))
            patch = int(match.group(3))
            prerelease = match.group(4) or ""

            return (major, minor, patch, prerelease)

        return None

    def _check_vulnerabilities(self, package_name: str, version: str) -> list[VulnerabilityInfo]:
        """Check for security vulnerabilities.

        Args:
            package_name: Package name
            version: Package version

        Returns:
            List of vulnerabilities
        """
        vulnerabilities: list[VulnerabilityInfo] = []

        # Check local vulnerability database
        if package_name in self._vuln_db:
            for vuln_data in self._vuln_db[package_name]:
                if self._is_version_affected(version, vuln_data.get("affected", "")):
                    vulnerabilities.append(
                        VulnerabilityInfo(
                            id=vuln_data.get("id", "UNKNOWN"),
                            severity=vuln_data.get("severity", "unknown"),
                            description=vuln_data.get("description", ""),
                            affected_versions=vuln_data.get("affected", ""),
                            fixed_version=vuln_data.get("fixed", None),
                            cvss_score=vuln_data.get("cvss_score"),
                        )
                    )

        return vulnerabilities

    def _is_version_affected(self, version: str, affected_spec: str) -> bool:
        """Check if version is affected by vulnerability.

        Args:
            version: Package version
            affected_spec: Affected version specification

        Returns:
            True if affected
        """
        # Simplified check - in production, use packaging library
        version_clean = re.sub(r"^[><=!~^]+", "", version).strip()

        if "<" in affected_spec:
            max_version = re.search(r"<([0-9.]+)", affected_spec)
            if max_version:
                return version_clean < max_version.group(1)

        return True  # Conservative default

    def _determine_health_status(
        self,
        current: str,
        latest: str | None,
        vulnerabilities: list[VulnerabilityInfo],
        deprecation: str | None,
    ) -> HealthStatus:
        """Determine overall health status.

        Args:
            current: Current version
            latest: Latest version
            vulnerabilities: List of vulnerabilities
            deprecation: Deprecation notice

        Returns:
            HealthStatus
        """
        if vulnerabilities:
            return HealthStatus.VULNERABLE

        if deprecation:
            return HealthStatus.DEPRECATED

        if latest and current != latest and current != "*":
            return HealthStatus.OUTDATED

        if latest:
            return HealthStatus.HEALTHY

        return HealthStatus.UNKNOWN

    def _categorize_license(self, license_str: str | None) -> LicenseCategory:
        """Categorize license into compatibility category.

        Args:
            license_str: License string

        Returns:
            LicenseCategory
        """
        if not license_str:
            return LicenseCategory.UNKNOWN

        license_upper = license_str.upper()

        for license_key, category in self.LICENSE_CATEGORIES.items():
            if license_key.upper() in license_upper:
                return category

        return LicenseCategory.UNKNOWN

    def _detect_circular_dependencies(
        self, dependencies: list[DependencyInfo]
    ) -> list[CircularDependency]:
        """Detect circular dependencies.

        Args:
            dependencies: List of dependencies

        Returns:
            List of circular dependency chains
        """
        # Build dependency graph
        graph: dict[str, list[str]] = {}
        for dep in dependencies:
            graph[dep.name] = dep.dependencies

        # Find cycles using DFS
        cycles: list[CircularDependency] = []
        visited = set()
        path: list[str] = []

        def dfs(node: str) -> None:
            if node in path:
                # Found cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:]
                if len(cycle) > 1:
                    cycles.append(CircularDependency(chain=cycle))
                return

            if node in visited:
                return

            visited.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                dfs(neighbor)

            path.pop()

        for node in graph:
            if node not in visited:
                dfs(node)

        return cycles

    def _check_license_conflicts(self, dependencies: list[DependencyInfo]) -> list[LicenseConflict]:
        """Check for license compatibility conflicts.

        Args:
            dependencies: List of dependencies

        Returns:
            List of license conflicts
        """
        conflicts: list[LicenseConflict] = []

        # Check for GPL + proprietary/permissive conflicts
        copyleft_deps = [
            dep for dep in dependencies if dep.license_category == LicenseCategory.COPYLEFT
        ]
        permissive_deps = [
            dep for dep in dependencies if dep.license_category == LicenseCategory.PERMISSIVE
        ]

        # GPL requires all linked code to be GPL
        for copyleft in copyleft_deps:
            if (
                "GPL" in (copyleft.license or "").upper()
                and "LGPL" not in (copyleft.license or "").upper()
            ):
                for permissive in permissive_deps:
                    conflicts.append(
                        LicenseConflict(
                            package1=copyleft.name,
                            license1=copyleft.license or "Unknown",
                            package2=permissive.name,
                            license2=permissive.license or "Unknown",
                            conflict_reason="GPL requires all linked code to be GPL-compatible",
                        )
                    )

        return conflicts

    def _calculate_health_score(self, dependencies: list[DependencyInfo]) -> float:
        """Calculate overall health score.

        Args:
            dependencies: List of dependencies

        Returns:
            Health score (0-100)
        """
        if not dependencies:
            return 100.0

        # Average individual scores
        total_score = sum(dep.health_score for dep in dependencies)
        avg_score = total_score / len(dependencies)

        return round(avg_score, 2)

    def _generate_recommendations(
        self,
        dependencies: list[DependencyInfo],
        circular_deps: list[CircularDependency],
        license_conflicts: list[LicenseConflict],
    ) -> list[str]:
        """Generate actionable recommendations.

        Args:
            dependencies: List of dependencies
            circular_deps: Circular dependencies
            license_conflicts: License conflicts

        Returns:
            List of recommendation strings
        """
        recommendations: list[str] = []

        # Critical vulnerabilities
        critical = [
            dep
            for dep in dependencies
            for vuln in dep.vulnerabilities
            if vuln.severity == "critical"
        ]
        if critical:
            recommendations.append(
                f"URGENT: Fix {len(critical)} package(s) with critical vulnerabilities"
            )

        # Deprecated packages
        deprecated = [dep for dep in dependencies if dep.is_deprecated]
        if deprecated:
            recommendations.append(
                f"Replace {len(deprecated)} deprecated package(s): "
                f"{', '.join(dep.name for dep in deprecated[:3])}"
            )

        # Outdated packages
        major_updates = [dep for dep in dependencies if dep.update_type == UpdateType.MAJOR]
        if major_updates:
            recommendations.append(
                f"Consider upgrading {len(major_updates)} package(s) with major updates available"
            )

        # Circular dependencies
        if circular_deps:
            recommendations.append(f"Resolve {len(circular_deps)} circular dependency chain(s)")

        # License conflicts
        if license_conflicts:
            recommendations.append(
                f"Review {len(license_conflicts)} license compatibility conflict(s)"
            )

        # General health
        if not recommendations:
            recommendations.append("All dependencies are healthy!")

        return recommendations

    def _load_vulnerability_db(self) -> dict[str, list[dict[str, Any]]]:
        """Load vulnerability database from cache.

        Returns:
            Vulnerability database
        """
        vuln_db_file = self.cache_dir / "vulnerabilities.json"

        if vuln_db_file.exists():
            try:
                with open(vuln_db_file) as f:
                    return json.load(f)
            except (OSError, json.JSONDecodeError):
                pass

        # Return minimal example database
        return {
            "requests": [
                {
                    "id": "CVE-2023-32681",
                    "severity": "medium",
                    "description": "Unintended leak of Proxy-Authorization header",
                    "affected": "<2.31.0",
                    "fixed": "2.31.0",
                }
            ],
        }
