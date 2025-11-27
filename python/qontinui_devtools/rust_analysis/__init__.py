"""Rust code analysis tools.

This module provides static analysis tools for Rust codebases:
- CircularDependencyDetector: Detect circular module dependencies
- DeadCodeDetector: Find unused code
- UnsafeAnalyzer: Analyze unsafe code usage
- ComplexityAnalyzer: Measure code complexity

These analyzers use regex-based parsing and don't require rustc or cargo.
"""

from .circular_detector import CircularDependencyDetector, RustCircularDependency
from .complexity_analyzer import ComplexityAnalyzer, ComplexityMetrics
from .dead_code_detector import DeadCodeDetector, RustDeadCode
from .unsafe_analyzer import UnsafeAnalyzer, UnsafeBlock

__all__ = [
    "CircularDependencyDetector",
    "RustCircularDependency",
    "DeadCodeDetector",
    "RustDeadCode",
    "UnsafeAnalyzer",
    "UnsafeBlock",
    "ComplexityAnalyzer",
    "ComplexityMetrics",
]
