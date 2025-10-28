"""Data models for regression detection and reporting."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ChangeType(Enum):
    """Type of change detected in code comparison."""

    BREAKING = "breaking"
    BEHAVIORAL = "behavioral"
    PERFORMANCE = "performance"
    COMPATIBLE = "compatible"
    DEPENDENCY = "dependency"


class RiskLevel(Enum):
    """Risk level associated with a detected change."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SeverityLevel(Enum):
    """Severity level for impact assessment."""

    SEVERE = "severe"
    MODERATE = "moderate"
    MINOR = "minor"
    NEGLIGIBLE = "negligible"


@dataclass
class FunctionSignature:
    """Represents a function signature for comparison."""

    name: str
    parameters: list[str]
    return_type: str | None
    module_path: str
    decorators: list[str] = field(default_factory=list)
    docstring: str | None = None
    is_async: bool = False
    is_public: bool = True
    line_number: int = 0

    def __eq__(self, other: object) -> bool:
        """Check if two signatures are equal."""
        if not isinstance(other, FunctionSignature):
            return False
        return (
            self.name == other.name
            and self.parameters == other.parameters
            and self.return_type == other.return_type
            and self.module_path == other.module_path
            and self.is_async == other.is_async
        )

    def __hash__(self) -> int:
        """Generate hash for signature."""
        return hash((self.name, tuple(self.parameters), self.return_type, self.module_path, self.is_async))

    def to_dict(self) -> dict[str, Any]:
        """Convert signature to dictionary."""
        return {
            "name": self.name,
            "parameters": self.parameters,
            "return_type": self.return_type,
            "module_path": self.module_path,
            "decorators": self.decorators,
            "docstring": self.docstring,
            "is_async": self.is_async,
            "is_public": self.is_public,
            "line_number": self.line_number,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FunctionSignature":
        """Create signature from dictionary."""
        return cls(
            name=data["name"],
            parameters=data["parameters"],
            return_type=data.get("return_type"),
            module_path=data["module_path"],
            decorators=data.get("decorators", []),
            docstring=data.get("docstring"),
            is_async=data.get("is_async", False),
            is_public=data.get("is_public", True),
            line_number=data.get("line_number", 0),
        )


@dataclass
class ClassSignature:
    """Represents a class signature for comparison."""

    name: str
    module_path: str
    methods: list[FunctionSignature] = field(default_factory=list)
    base_classes: list[str] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    docstring: str | None = None
    is_public: bool = True
    line_number: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert class signature to dictionary."""
        return {
            "name": self.name,
            "module_path": self.module_path,
            "methods": [m.to_dict() for m in self.methods],
            "base_classes": self.base_classes,
            "decorators": self.decorators,
            "docstring": self.docstring,
            "is_public": self.is_public,
            "line_number": self.line_number,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ClassSignature":
        """Create class signature from dictionary."""
        return cls(
            name=data["name"],
            module_path=data["module_path"],
            methods=[FunctionSignature.from_dict(m) for m in data.get("methods", [])],
            base_classes=data.get("base_classes", []),
            decorators=data.get("decorators", []),
            docstring=data.get("docstring"),
            is_public=data.get("is_public", True),
            line_number=data.get("line_number", 0),
        )


@dataclass
class PerformanceMetric:
    """Performance metric for comparison."""

    function_name: str
    module_path: str
    execution_time_ms: float
    memory_usage_mb: float = 0.0
    call_count: int = 1

    def to_dict(self) -> dict[str, Any]:
        """Convert metric to dictionary."""
        return {
            "function_name": self.function_name,
            "module_path": self.module_path,
            "execution_time_ms": self.execution_time_ms,
            "memory_usage_mb": self.memory_usage_mb,
            "call_count": self.call_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PerformanceMetric":
        """Create metric from dictionary."""
        return cls(
            function_name=data["function_name"],
            module_path=data["module_path"],
            execution_time_ms=data["execution_time_ms"],
            memory_usage_mb=data.get("memory_usage_mb", 0.0),
            call_count=data.get("call_count", 1),
        )


@dataclass
class RegressionIssue:
    """Represents a detected regression issue."""

    change_type: ChangeType
    risk_level: RiskLevel
    description: str
    old_signature: FunctionSignature | None
    new_signature: FunctionSignature | None
    impact_description: str
    migration_guide: str
    severity: SeverityLevel = SeverityLevel.MODERATE
    affected_modules: list[str] = field(default_factory=list)
    performance_delta: float | None = None
    old_performance: PerformanceMetric | None = None
    new_performance: PerformanceMetric | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert issue to dictionary."""
        return {
            "change_type": self.change_type.value,
            "risk_level": self.risk_level.value,
            "description": self.description,
            "old_signature": self.old_signature.to_dict() if self.old_signature else None,
            "new_signature": self.new_signature.to_dict() if self.new_signature else None,
            "impact_description": self.impact_description,
            "migration_guide": self.migration_guide,
            "severity": self.severity.value,
            "affected_modules": self.affected_modules,
            "performance_delta": self.performance_delta,
            "old_performance": (
                self.old_performance.to_dict() if self.old_performance else None
            ),
            "new_performance": (
                self.new_performance.to_dict() if self.new_performance else None
            ),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RegressionIssue":
        """Create issue from dictionary."""
        return cls(
            change_type=ChangeType(data["change_type"]),
            risk_level=RiskLevel(data["risk_level"]),
            description=data["description"],
            old_signature=(
                FunctionSignature.from_dict(data["old_signature"])
                if data.get("old_signature")
                else None
            ),
            new_signature=(
                FunctionSignature.from_dict(data["new_signature"])
                if data.get("new_signature")
                else None
            ),
            impact_description=data["impact_description"],
            migration_guide=data["migration_guide"],
            severity=SeverityLevel(data.get("severity", "moderate")),
            affected_modules=data.get("affected_modules", []),
            performance_delta=data.get("performance_delta"),
            old_performance=(
                PerformanceMetric.from_dict(data["old_performance"])
                if data.get("old_performance")
                else None
            ),
            new_performance=(
                PerformanceMetric.from_dict(data["new_performance"])
                if data.get("new_performance")
                else None
            ),
        )


@dataclass
class RegressionReport:
    """Complete regression analysis report."""

    baseline_version: str
    current_version: str
    issues: list[RegressionIssue]
    breaking_count: int
    behavioral_count: int
    performance_count: int
    dependency_count: int
    total_functions_compared: int
    total_classes_compared: int
    timestamp: str = ""
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "baseline_version": self.baseline_version,
            "current_version": self.current_version,
            "issues": [issue.to_dict() for issue in self.issues],
            "breaking_count": self.breaking_count,
            "behavioral_count": self.behavioral_count,
            "performance_count": self.performance_count,
            "dependency_count": self.dependency_count,
            "total_functions_compared": self.total_functions_compared,
            "total_classes_compared": self.total_classes_compared,
            "timestamp": self.timestamp,
            "summary": self.summary,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RegressionReport":
        """Create report from dictionary."""
        return cls(
            baseline_version=data["baseline_version"],
            current_version=data["current_version"],
            issues=[RegressionIssue.from_dict(i) for i in data["issues"]],
            breaking_count=data["breaking_count"],
            behavioral_count=data["behavioral_count"],
            performance_count=data["performance_count"],
            dependency_count=data.get("dependency_count", 0),
            total_functions_compared=data["total_functions_compared"],
            total_classes_compared=data.get("total_classes_compared", 0),
            timestamp=data.get("timestamp", ""),
            summary=data.get("summary", ""),
        )

    def get_critical_issues(self) -> list[RegressionIssue]:
        """Get all critical risk issues."""
        return [i for i in self.issues if i.risk_level == RiskLevel.CRITICAL]

    def get_breaking_changes(self) -> list[RegressionIssue]:
        """Get all breaking changes."""
        return [i for i in self.issues if i.change_type == ChangeType.BREAKING]

    def get_performance_regressions(self) -> list[RegressionIssue]:
        """Get all performance regressions."""
        return [i for i in self.issues if i.change_type == ChangeType.PERFORMANCE]

    def has_breaking_changes(self) -> bool:
        """Check if report contains breaking changes."""
        return self.breaking_count > 0

    def get_severity_distribution(self) -> dict[str, int]:
        """Get distribution of issues by severity."""
        distribution: dict[str, int] = {
            "severe": 0,
            "moderate": 0,
            "minor": 0,
            "negligible": 0,
        }
        for issue in self.issues:
            distribution[issue.severity.value] += 1
        return distribution
