"""Single Responsibility Principle (SRP) Analyzer.

from typing import Any, Any

This module analyzes Python classes to detect SRP violations by identifying
classes with multiple distinct responsibilities through semantic analysis
of method names and clustering.
"""

import ast
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .clustering import MethodCluster, cluster_methods_by_keywords


@dataclass
class SRPViolation:
    """A detected SRP violation.

    Attributes:
        class_name: Name of the class with violation
        file_path: Path to the file containing the class
        line_number: Line number where class is defined
        clusters: List of identified responsibility clusters
        severity: Severity level ("critical", "high", "medium")
        recommendation: Human-readable recommendation for fixing
        suggested_refactorings: List of suggested refactoring steps
    """

    class_name: str
    file_path: str
    line_number: int
    clusters: list[MethodCluster]
    severity: str
    recommendation: str
    suggested_refactorings: list[str]

    def __post_init__(self) -> None:
        """Validate severity."""
        if self.severity not in ("critical", "high", "medium"):
            raise ValueError(f"Invalid severity: {self.severity}")


class SRPAnalyzer:
    """Analyze classes for SRP violations using semantic analysis.

    This analyzer examines Python classes to detect when they have multiple
    responsibilities by clustering their methods semantically.
    """

    def __init__(self, verbose: bool = False) -> None:
        """Initialize the SRP analyzer.

        Args:
            verbose: Whether to print verbose output during analysis
        """
        self.verbose = verbose
        self.stats: dict[str, int] = {
            "files_analyzed": 0,
            "classes_analyzed": 0,
            "violations_found": 0,
        }

    def analyze_directory(self, path: str, min_methods: int = 5) -> list[SRPViolation]:
        """Analyze all Python files in a directory for SRP violations.

        Args:
            path: Directory path to analyze
            min_methods: Minimum number of methods for a class to be analyzed

        Returns:
            List of detected SRP violations
        """
        path_obj = Path(path)
        if not path_obj.exists():
            raise ValueError(f"Path does not exist: {path}")

        violations: list[Any] = []

        # Find all Python files
        if path_obj.is_file():
            python_files = [path_obj]
        else:
            python_files = list(path_obj.rglob("*.py"))

        if self.verbose:
            print(f"Analyzing {len(python_files)} Python files...")

        for file_path in python_files:
            try:
                file_violations = self.analyze_file(str(file_path), min_methods)
                violations.extend(file_violations)
                self.stats["files_analyzed"] += 1
            except Exception as e:
                if self.verbose:
                    print(f"Error analyzing {file_path}: {e}")

        self.stats["violations_found"] = len(violations)

        return violations

    def analyze_file(self, file_path: str, min_methods: int = 5) -> list[SRPViolation]:
        """Analyze a single Python file for SRP violations.

        Args:
            file_path: Path to Python file
            min_methods: Minimum number of methods to analyze (default: 5)

        Returns:
            List of violations found in this file
        """
        violations: list[Any] = []

        try:
            with open(file_path, encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source, filename=file_path)

            # Find all class definitions
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    violation = self.analyze_class(node, file_path, min_methods)
                    if violation:
                        violations.append(violation)
                    self.stats["classes_analyzed"] += 1

        except SyntaxError as e:
            if self.verbose:
                print(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            if self.verbose:
                print(f"Error parsing {file_path}: {e}")

        return violations

    def analyze_class(
        self,
        class_node: ast.ClassDef,
        file_path: str,
        min_methods: int = 5,
    ) -> SRPViolation | None:
        """Analyze a class for SRP violations.

        Args:
            class_node: AST node representing the class
            file_path: Path to file containing the class
            min_methods: Minimum number of methods to analyze

        Returns:
            SRPViolation if violation detected, None otherwise
        """
        # Extract method names
        methods = self._extract_methods(class_node)

        # Filter out magic methods and private methods for cleaner analysis
        public_methods = [m for m in methods if not m.startswith("__") and not m.startswith("_")]

        # Skip classes with too few methods
        if len(public_methods) < min_methods:
            return None

        # Cluster methods by responsibility
        clusters = self.cluster_methods(public_methods)

        # Detect violation based on number of clusters
        num_clusters = len(clusters)

        if num_clusters < 2:
            # Single responsibility or unclear - no violation
            return None

        # Determine severity
        severity = self._calculate_severity(num_clusters)

        # Generate recommendations
        recommendation = self._generate_recommendation(class_node.name, clusters)
        suggested_refactorings = self._generate_refactoring_suggestions(class_node.name, clusters)

        return SRPViolation(
            class_name=class_node.name,
            file_path=file_path,
            line_number=class_node.lineno,
            clusters=clusters,
            severity=severity,
            recommendation=recommendation,
            suggested_refactorings=suggested_refactorings,
        )

    def _extract_methods(self, class_node: ast.ClassDef) -> list[str]:
        """Extract method names from a class node.

        Args:
            class_node: AST node representing a class

        Returns:
            List of method names
        """
        methods: list[Any] = []

        for node in class_node.body:
            if isinstance(node, ast.FunctionDef):
                methods.append(node.name)

        return methods

    def cluster_methods(self, methods: list[str]) -> list[MethodCluster]:
        """Cluster methods by semantic similarity.

        Args:
            methods: List of method names

        Returns:
            List of method clusters
        """
        return cluster_methods_by_keywords(methods, min_cluster_size=2)

    def _calculate_severity(self, num_clusters: int) -> str:
        """Calculate severity based on number of responsibilities.

        Args:
            num_clusters: Number of responsibility clusters

        Returns:
            Severity level: "critical", "high", or "medium"
        """
        if num_clusters >= 5:
            return "critical"
        elif num_clusters >= 3:
            return "high"
        else:
            return "medium"

    def _generate_recommendation(self, class_name: str, clusters: list[MethodCluster]) -> str:
        """Generate a recommendation for fixing the violation.

        Args:
            class_name: Name of the class
            clusters: List of responsibility clusters

        Returns:
            Human-readable recommendation
        """
        num_responsibilities = len(clusters)

        if num_responsibilities >= 5:
            return (
                f"Critical: {class_name} has {num_responsibilities} distinct "
                f"responsibilities. Consider splitting into multiple classes, "
                f"each with a single, well-defined responsibility."
            )
        elif num_responsibilities >= 3:
            return (
                f"High: {class_name} has {num_responsibilities} responsibilities. "
                f"Extract separate classes for each responsibility to improve "
                f"maintainability."
            )
        else:
            return (
                f"Medium: {class_name} has {num_responsibilities} responsibilities. "
                f"Consider splitting into separate classes for better separation "
                f"of concerns."
            )

    def _generate_refactoring_suggestions(
        self, class_name: str, clusters: list[MethodCluster]
    ) -> list[str]:
        """Generate specific refactoring suggestions.

        Args:
            class_name: Name of the class
            clusters: List of responsibility clusters

        Returns:
            List of refactoring suggestions
        """
        suggestions: list[Any] = []

        for cluster in clusters:
            # Suggest a new class name based on responsibility
            new_class_name = self._suggest_class_name(class_name, cluster.name)

            suggestion = (
                f"Extract {cluster.name} responsibility ({len(cluster.methods)} methods) "
                f"into a new class '{new_class_name}'"
            )
            suggestions.append(suggestion)

        # Add coordination suggestion
        if len(clusters) > 2:
            suggestions.append(
                "Consider using a Facade or Coordinator pattern to manage "
                "interactions between the extracted classes"
            )

        return suggestions

    def _suggest_class_name(self, original_name: str, responsibility: str) -> str:
        """Suggest a class name for extracted responsibility.

        Args:
            original_name: Original class name
            responsibility: Responsibility being extracted

        Returns:
            Suggested class name
        """
        # Remove common suffixes
        base_name = original_name
        for suffix in ["Manager", "Handler", "Service", "Controller", "Helper"]:
            if base_name.endswith(suffix):
                base_name = base_name[: -len(suffix)]

        # Map responsibilities to class name components
        responsibility_map = {
            "Data Access": "Repository",
            "Validation": "Validator",
            "Business Logic": "Service",
            "Persistence": "Persister",
            "Presentation": "Formatter",
            "Event Handling": "EventHandler",
            "Lifecycle": "Lifecycle",
            "Factory": "Factory",
            "Conversion": "Converter",
            "Comparison": "Comparator",
        }

        suffix = responsibility_map.get(responsibility, responsibility.replace(" ", ""))
        return f"{base_name}{suffix}"

    def generate_report(self, violations: list[SRPViolation]) -> str:
        """Generate a human-readable report of violations.

        Args:
            violations: List of SRP violations

        Returns:
            Formatted report string
        """
        if not violations:
            return "No SRP violations detected!"

        lines = ["=" * 80]
        lines.append("SRP VIOLATION REPORT")
        lines.append("=" * 80)
        lines.append("")
        lines.append(f"Total violations: {len(violations)}")
        lines.append("")

        # Group by severity
        by_severity: dict[str, list[SRPViolation]] = {"critical": [], "high": [], "medium": []}
        for violation in violations:
            by_severity[violation.severity].append(violation)

        lines.append(f"Critical: {len(by_severity['critical'])}")
        lines.append(f"High:     {len(by_severity['high'])}")
        lines.append(f"Medium:   {len(by_severity['medium'])}")
        lines.append("")
        lines.append("=" * 80)

        # Report each violation
        for severity in ["critical", "high", "medium"]:
            if not by_severity[severity]:
                continue

            lines.append("")
            lines.append(f"{severity.upper()} SEVERITY VIOLATIONS")
            lines.append("-" * 80)

            for violation in by_severity[severity]:
                lines.append("")
                lines.append(f"Class: {violation.class_name}")
                lines.append(f"File:  {violation.file_path}:{violation.line_number}")
                lines.append(f"Responsibilities: {len(violation.clusters)}")
                lines.append("")

                for i, cluster in enumerate(violation.clusters, 1):
                    lines.append(
                        f"  {i}. {cluster.name} "
                        f"({len(cluster.methods)} methods, "
                        f"confidence: {cluster.confidence:.2f})"
                    )
                    for method in cluster.methods[:5]:  # Show first 5
                        lines.append(f"     - {method}")
                    if len(cluster.methods) > 5:
                        lines.append(f"     ... and {len(cluster.methods) - 5} more")
                    lines.append("")

                lines.append(f"Recommendation: {violation.recommendation}")
                lines.append("")
                lines.append("Suggested Refactorings:")
                for suggestion in violation.suggested_refactorings:
                    lines.append(f"  - {suggestion}")
                lines.append("")
                lines.append("-" * 80)

        lines.append("")
        lines.append("=" * 80)
        lines.append("Analysis Statistics:")
        lines.append(f"  Files analyzed:   {self.stats['files_analyzed']}")
        lines.append(f"  Classes analyzed: {self.stats['classes_analyzed']}")
        lines.append(f"  Violations found: {self.stats['violations_found']}")
        lines.append("=" * 80)

        return "\n".join(lines)

    def analyze_with_timing(
        self, path: str, min_methods: int = 5
    ) -> tuple[list[SRPViolation], float]:
        """Analyze directory and measure execution time.

        Args:
            path: Directory path to analyze
            min_methods: Minimum number of methods for analysis

        Returns:
            Tuple of (violations, execution_time_seconds)
        """
        start_time = time.time()
        violations = self.analyze_directory(path, min_methods)
        execution_time = time.time() - start_time

        return violations, execution_time
