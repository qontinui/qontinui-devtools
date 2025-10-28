"""Data models for type hint analysis.

This module defines the data structures used for tracking type hint coverage,
untyped items, and analysis reports.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TypeHintStatus(Enum):
    """Status of type hints for a function or method."""

    FULLY_TYPED = "fully_typed"
    PARTIALLY_TYPED = "partially_typed"
    UNTYPED = "untyped"
    USES_ANY = "uses_any"


class ItemType(Enum):
    """Type of item being analyzed."""

    FUNCTION = "function"
    METHOD = "method"
    PARAMETER = "parameter"
    RETURN = "return"
    ATTRIBUTE = "attribute"
    VARIABLE = "variable"


@dataclass
class TypeCoverage:
    """Type hint coverage metrics.

    Attributes:
        total_functions: Total number of functions/methods analyzed
        typed_functions: Number of functions with at least partial typing
        fully_typed_functions: Number of fully typed functions
        total_parameters: Total number of parameters
        typed_parameters: Number of parameters with type hints
        total_returns: Total number of return statements/functions
        typed_returns: Number of returns with type hints
        coverage_percentage: Overall coverage percentage (0-100)
        parameter_coverage: Parameter coverage percentage (0-100)
        return_coverage: Return coverage percentage (0-100)
        any_usage_count: Number of times Any type is used
    """

    total_functions: int = 0
    typed_functions: int = 0
    fully_typed_functions: int = 0
    total_parameters: int = 0
    typed_parameters: int = 0
    total_returns: int = 0
    typed_returns: int = 0
    coverage_percentage: float = 0.0
    parameter_coverage: float = 0.0
    return_coverage: float = 0.0
    any_usage_count: int = 0

    def calculate_percentages(self) -> None:
        """Calculate coverage percentages from counts."""
        # Overall coverage (based on typed items)
        total_items = self.total_parameters + self.total_returns
        typed_items = self.typed_parameters + self.typed_returns

        if total_items > 0:
            self.coverage_percentage = (typed_items / total_items) * 100
        else:
            self.coverage_percentage = 100.0

        # Parameter coverage
        if self.total_parameters > 0:
            self.parameter_coverage = (self.typed_parameters / self.total_parameters) * 100
        else:
            self.parameter_coverage = 100.0

        # Return coverage
        if self.total_returns > 0:
            self.return_coverage = (self.typed_returns / self.total_returns) * 100
        else:
            self.return_coverage = 100.0


@dataclass
class UntypedItem:
    """An item missing type hints.

    Attributes:
        item_type: Type of item (function, parameter, return, etc.)
        name: Name of the item
        file_path: Path to file containing the item
        line_number: Line number where item is defined
        function_name: Name of containing function/method
        class_name: Name of containing class (if any)
        suggested_type: Suggested type hint based on inference
        confidence: Confidence in suggestion (0.0-1.0)
        reason: Reason for suggestion
    """

    item_type: str
    name: str
    file_path: str
    line_number: int
    function_name: str | None = None
    class_name: str | None = None
    suggested_type: str | None = None
    confidence: float = 0.0
    reason: str = ""

    def get_full_name(self) -> str:
        """Get fully qualified name of the item."""
        parts = []
        if self.class_name:
            parts.append(self.class_name)
        if self.function_name:
            parts.append(self.function_name)
        parts.append(self.name)
        return ".".join(parts)


@dataclass
class AnyUsage:
    """Usage of the Any type.

    Attributes:
        file_path: Path to file
        line_number: Line number
        context: Context where Any is used
        suggestion: Suggested more specific type
    """

    file_path: str
    line_number: int
    context: str
    suggestion: str | None = None


@dataclass
class MypyError:
    """A mypy error or warning.

    Attributes:
        file_path: Path to file
        line_number: Line number
        column: Column number
        severity: Error severity (error, warning, note)
        message: Error message
        error_code: Mypy error code
    """

    file_path: str
    line_number: int
    column: int
    severity: str
    message: str
    error_code: str | None = None


@dataclass
class TypeAnalysisReport:
    """Complete type analysis report.

    Attributes:
        overall_coverage: Overall coverage metrics
        module_coverage: Coverage metrics per module
        class_coverage: Coverage metrics per class
        untyped_items: List of items missing type hints
        any_usages: List of Any type usages
        mypy_errors: List of mypy errors/warnings
        analysis_time: Time taken for analysis (seconds)
        files_analyzed: Number of files analyzed
        strict_mode: Whether strict mode was used
    """

    overall_coverage: TypeCoverage
    module_coverage: dict[str, TypeCoverage] = field(default_factory=dict)
    class_coverage: dict[str, TypeCoverage] = field(default_factory=dict)
    untyped_items: list[UntypedItem] = field(default_factory=list)
    any_usages: list[AnyUsage] = field(default_factory=list)
    mypy_errors: list[MypyError] = field(default_factory=list)
    analysis_time: float = 0.0
    files_analyzed: int = 0
    strict_mode: bool = False

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of the analysis."""
        return {
            "coverage_percentage": self.overall_coverage.coverage_percentage,
            "parameter_coverage": self.overall_coverage.parameter_coverage,
            "return_coverage": self.overall_coverage.return_coverage,
            "total_functions": self.overall_coverage.total_functions,
            "typed_functions": self.overall_coverage.typed_functions,
            "fully_typed_functions": self.overall_coverage.fully_typed_functions,
            "untyped_items_count": len(self.untyped_items),
            "any_usages_count": len(self.any_usages),
            "mypy_errors_count": len(self.mypy_errors),
            "files_analyzed": self.files_analyzed,
            "analysis_time": self.analysis_time,
        }

    def get_sorted_untyped_items(self, limit: int | None = None) -> list[UntypedItem]:
        """Get untyped items sorted by priority.

        Priority order:
        1. Functions without any type hints
        2. Return values without hints
        3. Parameters without hints

        Args:
            limit: Maximum number of items to return

        Returns:
            Sorted list of untyped items
        """
        # Sort by item type priority, then by file path
        priority_order = {
            "function": 0,
            "method": 0,
            "return": 1,
            "parameter": 2,
            "attribute": 3,
            "variable": 4,
        }

        sorted_items = sorted(
            self.untyped_items,
            key=lambda x: (priority_order.get(x.item_type, 99), x.file_path, x.line_number)
        )

        if limit:
            return sorted_items[:limit]
        return sorted_items
