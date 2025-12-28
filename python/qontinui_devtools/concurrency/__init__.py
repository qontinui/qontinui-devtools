"""Concurrency testing and analysis tools for qontinui-devtools.

This package provides tools for detecting and testing race conditions:
- Static analysis with RaceConditionDetector
- Runtime stress testing with RaceConditionTester
- State instrumentation with SharedStateTracker
- Pre-built test scenarios
"""

from .decorators import concurrent_test, stress_test, tracked_test
from .instrumentation import (Access, InstrumentedObject, RaceConflict,
                              SharedStateTracker)
from .race_detector import RaceCondition, RaceConditionDetector, SharedState
from .race_tester import RaceConditionTester, RaceTestResult, compare_results

__all__ = [
    # Core testing
    "RaceConditionTester",
    "RaceTestResult",
    "compare_results",
    # Static analysis
    "RaceConditionDetector",
    "RaceCondition",
    "SharedState",
    # Decorators
    "concurrent_test",
    "stress_test",
    "tracked_test",
    # Instrumentation
    "SharedStateTracker",
    "InstrumentedObject",
    "Access",
    "RaceConflict",
]
