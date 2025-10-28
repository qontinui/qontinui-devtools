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
from .import_analysis import CircularDependencyDetector, ImportTracer
from .concurrency import RaceConditionDetector, RaceConditionTester
from .testing import MockHAL

# Phase 2: Architecture Analysis
from .architecture import (
    GodClassDetector,
    SRPAnalyzer,
    CouplingCohesionAnalyzer,
    DependencyGraphVisualizer,
)

# Phase 3: Runtime Monitoring
from .runtime import (
    ActionProfiler,
    EventTracer,
    MemoryProfiler,
    DashboardServer,
    MetricsCollector,
)

# Phase 4: Advanced Analysis
from .security import SecurityAnalyzer
from .documentation import DocumentationGenerator
from .regression import RegressionDetector
from .type_analysis import TypeAnalyzer
from .dependencies import DependencyHealthChecker

# Code Quality
from .code_quality import DeadCodeDetector

# Reporting
from .reporting import HTMLReportGenerator, ReportAggregator

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
