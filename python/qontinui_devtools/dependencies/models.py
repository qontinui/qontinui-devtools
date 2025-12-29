"""Data models for dependency health checking.

This module defines the core data structures used in dependency health analysis,
including health status enums, update types, and comprehensive dependency reports.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from qontinui_schemas.common import utc_now


class HealthStatus(Enum):
    """Health status of a dependency."""

    HEALTHY = "healthy"
    OUTDATED = "outdated"
    VULNERABLE = "vulnerable"
    DEPRECATED = "deprecated"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        return self.value

    @property
    def severity(self) -> int:
        """Return severity score (higher is worse)."""
        severity_map = {
            HealthStatus.VULNERABLE: 4,
            HealthStatus.DEPRECATED: 3,
            HealthStatus.OUTDATED: 2,
            HealthStatus.UNKNOWN: 1,
            HealthStatus.HEALTHY: 0,
        }
        return severity_map[self]


class UpdateType(Enum):
    """Semantic version update type."""

    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"
    PRERELEASE = "prerelease"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        return self.value

    @property
    def risk_level(self) -> str:
        """Return risk level for this update type."""
        risk_map = {
            UpdateType.MAJOR: "high",
            UpdateType.MINOR: "medium",
            UpdateType.PATCH: "low",
            UpdateType.PRERELEASE: "high",
            UpdateType.UNKNOWN: "medium",
        }
        return risk_map[self]


class LicenseCategory(Enum):
    """License category for compatibility checking."""

    PERMISSIVE = "permissive"  # MIT, BSD, Apache
    COPYLEFT = "copyleft"  # GPL, LGPL, AGPL
    PROPRIETARY = "proprietary"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        return self.value


@dataclass
class VulnerabilityInfo:
    """Information about a security vulnerability."""

    id: str  # CVE or GHSA ID
    severity: str  # low, medium, high, critical
    description: str
    affected_versions: str
    fixed_version: str | None = None
    published_date: datetime | None = None
    cvss_score: float | None = None
    references: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        severity_str = f"[{self.severity.upper()}]"
        fixed_str = f" (fixed in {self.fixed_version})" if self.fixed_version else ""
        return f"{severity_str} {self.id}: {self.description}{fixed_str}"

    @property
    def severity_score(self) -> int:
        """Return numeric severity score."""
        severity_map = {
            "critical": 4,
            "high": 3,
            "medium": 2,
            "low": 1,
            "unknown": 0,
        }
        return severity_map.get(self.severity.lower(), 0)


@dataclass
class DependencyInfo:
    """Comprehensive information about a dependency."""

    name: str
    current_version: str
    latest_version: str | None = None
    update_type: UpdateType | None = None
    health_status: HealthStatus = HealthStatus.UNKNOWN
    vulnerabilities: list[VulnerabilityInfo] = field(default_factory=list)
    last_release_date: datetime | None = None
    license: str | None = None
    license_category: LicenseCategory = LicenseCategory.UNKNOWN
    deprecation_notice: str | None = None
    homepage: str | None = None
    repository: str | None = None
    maintainers: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    download_count: int = 0
    tree_depth: int = 0
    is_dev_dependency: bool = False
    extras: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        status_str = f"[{self.health_status.value.upper()}]"
        version_str = f"{self.current_version}"
        if self.latest_version and self.latest_version != self.current_version:
            version_str += f" -> {self.latest_version}"
        return f"{status_str} {self.name} {version_str}"

    @property
    def is_outdated(self) -> bool:
        """Check if package is outdated."""
        return (
            self.latest_version is not None
            and self.latest_version != self.current_version
            and self.update_type is not None
        )

    @property
    def has_vulnerabilities(self) -> bool:
        """Check if package has vulnerabilities."""
        return len(self.vulnerabilities) > 0

    @property
    def is_deprecated(self) -> bool:
        """Check if package is deprecated."""
        return self.deprecation_notice is not None

    @property
    def health_score(self) -> float:
        """Calculate individual dependency health score (0-100)."""
        score = 100.0

        # Deduct for vulnerabilities
        for vuln in self.vulnerabilities:
            if vuln.severity == "critical":
                score -= 30
            elif vuln.severity == "high":
                score -= 20
            elif vuln.severity == "medium":
                score -= 10
            else:
                score -= 5

        # Deduct for deprecation
        if self.is_deprecated:
            score -= 25

        # Deduct for being outdated
        if self.is_outdated and self.update_type:
            if self.update_type == UpdateType.MAJOR:
                score -= 15
            elif self.update_type == UpdateType.MINOR:
                score -= 8
            elif self.update_type == UpdateType.PATCH:
                score -= 3

        # Deduct for old packages (no release in 2+ years)
        if self.last_release_date:
            # Handle both timezone-aware and naive datetimes
            now = utc_now()
            last_release = self.last_release_date

            # If last_release is timezone-aware, make now timezone-aware too
            if (
                last_release.tzinfo is not None
                and last_release.tzinfo.utcoffset(last_release) is not None
            ):
                # Convert last_release to naive datetime in UTC
                last_release = last_release.replace(tzinfo=None)

            age_days = (now - last_release).days
            if age_days > 730:  # 2 years
                score -= 10
            elif age_days > 365:  # 1 year
                score -= 5

        return max(0.0, min(100.0, score))


@dataclass
class CircularDependency:
    """Information about a circular dependency chain."""

    chain: list[str]
    severity: str = "medium"  # low, medium, high

    def __str__(self) -> str:
        return " -> ".join(self.chain + [self.chain[0]])


@dataclass
class LicenseConflict:
    """Information about a license compatibility conflict."""

    package1: str
    license1: str
    package2: str
    license2: str
    conflict_reason: str

    def __str__(self) -> str:
        return (
            f"{self.package1} ({self.license1}) conflicts with "
            f"{self.package2} ({self.license2}): {self.conflict_reason}"
        )


@dataclass
class DependencyHealthReport:
    """Comprehensive dependency health analysis report."""

    total_dependencies: int
    healthy_count: int
    outdated_count: int
    vulnerable_count: int
    deprecated_count: int
    dependencies: list[DependencyInfo] = field(default_factory=list)
    overall_health_score: float = 100.0
    recommendations: list[str] = field(default_factory=list)
    circular_dependencies: list[CircularDependency] = field(default_factory=list)
    license_conflicts: list[LicenseConflict] = field(default_factory=list)
    max_tree_depth: int = 0
    total_vulnerabilities: int = 0
    critical_vulnerabilities: int = 0
    timestamp: datetime = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        lines = [
            "Dependency Health Report",
            "=" * 50,
            f"Total Dependencies: {self.total_dependencies}",
            f"Overall Health Score: {self.overall_health_score:.1f}/100",
            "",
            "Status Breakdown:",
            f"  Healthy:     {self.healthy_count}",
            f"  Outdated:    {self.outdated_count}",
            f"  Vulnerable:  {self.vulnerable_count}",
            f"  Deprecated:  {self.deprecated_count}",
        ]

        if self.total_vulnerabilities > 0:
            lines.extend(
                [
                    "",
                    f"Total Vulnerabilities: {self.total_vulnerabilities}",
                    f"  Critical: {self.critical_vulnerabilities}",
                ]
            )

        if self.circular_dependencies:
            lines.extend(
                [
                    "",
                    f"Circular Dependencies: {len(self.circular_dependencies)}",
                ]
            )

        if self.license_conflicts:
            lines.extend(
                [
                    "",
                    f"License Conflicts: {len(self.license_conflicts)}",
                ]
            )

        return "\n".join(lines)

    @property
    def has_critical_issues(self) -> bool:
        """Check if there are critical security issues."""
        return self.critical_vulnerabilities > 0

    @property
    def needs_updates(self) -> bool:
        """Check if any packages need updates."""
        return self.outdated_count > 0

    def get_vulnerable_dependencies(self) -> list[DependencyInfo]:
        """Get list of vulnerable dependencies."""
        return [dep for dep in self.dependencies if dep.has_vulnerabilities]

    def get_outdated_dependencies(self) -> list[DependencyInfo]:
        """Get list of outdated dependencies."""
        return [dep for dep in self.dependencies if dep.is_outdated]

    def get_deprecated_dependencies(self) -> list[DependencyInfo]:
        """Get list of deprecated dependencies."""
        return [dep for dep in self.dependencies if dep.is_deprecated]
