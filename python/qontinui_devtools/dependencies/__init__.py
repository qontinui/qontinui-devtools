"""Dependency health checker for Python projects.

This module provides comprehensive dependency health checking including:
- Package version analysis
- Security vulnerability detection
- Deprecated package detection
- License compatibility checking
- Dependency tree analysis
- Circular dependency detection
"""

from .health_checker import DependencyHealthChecker
from .models import (CircularDependency, DependencyHealthReport,
                     DependencyInfo, HealthStatus, LicenseCategory,
                     LicenseConflict, UpdateType, VulnerabilityInfo)
from .pypi_client import PackageInfo, PyPIClient

__all__ = [
    "DependencyHealthChecker",
    "DependencyHealthReport",
    "DependencyInfo",
    "HealthStatus",
    "UpdateType",
    "VulnerabilityInfo",
    "CircularDependency",
    "LicenseCategory",
    "LicenseConflict",
    "PyPIClient",
    "PackageInfo",
]

__version__ = "1.0.0"
