"""TypeScript/JavaScript analysis tools.

This package provides static analysis tools for TypeScript and JavaScript codebases:
- CircularDependencyDetector: Detect circular imports in TS/JS files
- DeadCodeDetector: Find unused exports, functions, and classes
- TypeCoverageAnalyzer: Analyze TypeScript type coverage
- ComplexityAnalyzer: Measure code complexity and identify code smells
"""

from .circular_detector import CircularDependencyDetector
from .dead_code_detector import DeadCodeDetector
from .type_coverage_analyzer import TypeCoverageAnalyzer
from .complexity_analyzer import ComplexityAnalyzer

__all__ = [
    "CircularDependencyDetector",
    "DeadCodeDetector",
    "TypeCoverageAnalyzer",
    "ComplexityAnalyzer",
]
