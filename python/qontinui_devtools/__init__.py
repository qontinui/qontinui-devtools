"""Qontinui DevTools - Analysis, debugging, and diagnostic tools for Qontinui.

This package provides comprehensive tooling for:
- Import analysis and circular dependency detection
- Architecture quality analysis (god classes, SRP violations, coupling/cohesion)
- Code quality checking
- Concurrency and race condition analysis
- Runtime performance monitoring
- Testing utilities (Mock HAL components)
- Interactive visualizations
- HTML reporting
- CI/CD integration
- Security analysis
- Documentation generation
- Regression detection
- Type hint analysis
- Dependency health checking
"""

__version__ = "1.1.0"

# Phase 1: Critical Tools
# Phase 2: Architecture Analysis
from .architecture import (
    CouplingCohesionAnalyzer,
    DependencyGraphVisualizer,
    GodClassDetector,
    SRPAnalyzer,
)

# Code Quality
from .code_quality import DeadCodeDetector
from .concurrency import RaceConditionDetector, RaceConditionTester
from .dependencies import DependencyHealthChecker
from .documentation import DocumentationGenerator
from .import_analysis import CircularDependencyDetector, ImportTracer
from .regression import RegressionDetector

# Reporting
from .reporting import HTMLReportGenerator, ReportAggregator

# Phase 3: Runtime Monitoring
from .runtime import ActionProfiler, DashboardServer, EventTracer, MemoryProfiler, MetricsCollector

# Phase 4: Advanced Analysis
from .security import SecurityAnalyzer
from .testing import MockHAL
from .type_analysis import TypeAnalyzer

__all__ = [
    # Version
    "__version__",
    # Import Analysis
    "CircularDependencyDetector",
    "ImportTracer",
    # Concurrency
    "RaceConditionDetector",
    "RaceConditionTester",
    # Testing
    "MockHAL",
    # Architecture
    "GodClassDetector",
    "SRPAnalyzer",
    "CouplingCohesionAnalyzer",
    "DependencyGraphVisualizer",
    # Runtime Monitoring
    "ActionProfiler",
    "EventTracer",
    "MemoryProfiler",
    "DashboardServer",
    "MetricsCollector",
    # Advanced Analysis (Phase 4)
    "SecurityAnalyzer",
    "DocumentationGenerator",
    "RegressionDetector",
    "TypeAnalyzer",
    "DependencyHealthChecker",
    # Code Quality
    "DeadCodeDetector",
    # Reporting
    "HTMLReportGenerator",
    "ReportAggregator",
]
