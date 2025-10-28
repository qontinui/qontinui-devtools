"""Type hint analysis tools for Python code.

This module provides tools to analyze type hint coverage, detect missing
type hints, infer types, and improve type safety in Python codebases.
"""

from .models import (
    AnyUsage,
    ItemType,
    MypyError,
    TypeAnalysisReport,
    TypeCoverage,
    TypeHintStatus,
    UntypedItem,
)
from .type_analyzer import TypeAnalyzer, TypeHintVisitor
from .type_inference import TypeInferenceEngine

__all__ = [
    # Main analyzer
    "TypeAnalyzer",
    "TypeHintVisitor",
    # Inference
    "TypeInferenceEngine",
    # Models
    "TypeAnalysisReport",
    "TypeCoverage",
    "UntypedItem",
    "AnyUsage",
    "MypyError",
    "TypeHintStatus",
    "ItemType",
]
