"""God Class Detector for identifying classes that violate Single Responsibility Principle."""

import ast
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .ast_metrics import (
    analyze_method_calls,
    calculate_complexity,
    count_attributes,
    count_lines,
    count_methods,
    extract_method_names,
    find_shared_attributes,
    get_method_by_name,
)


@dataclass
class ClassMetrics:
    """Metrics for a single class."""

    name: str
    file_path: str
    line_start: int
    line_end: int
    line_count: int
    method_count: int
    attribute_count: int
    cyclomatic_complexity: int
    lcom: float  # Lack of Cohesion of Methods (0-1, higher is worse)
    responsibilities: list[str] = field(default_factory=list)
    is_god_class: bool = False
    severity: str = "medium"  # "critical", "high", "medium"

    def __post_init__(self) -> None:
        """Calculate severity based on metrics."""
        if self.is_god_class:
            # Critical: Very large with high LCOM
            if self.line_count > 1500 or (self.method_count > 80 and self.lcom > 0.7):
                self.severity = "critical"
            # High: Large with moderate LCOM
            elif self.line_count > 1000 or (self.method_count > 50 and self.lcom > 0.6):
                self.severity = "high"
            else:
                self.severity = "medium"


@dataclass
class ExtractionSuggestion:
    """Suggestion for extracting methods into new class."""

    new_class_name: str
    methods_to_extract: list[str]
    responsibility: str
    estimated_lines: int


class GodClassDetector:
    """Detect god classes violating SRP."""

    def __init__(
        self,
        min_lines: int = 500,
        min_methods: int = 20,
        max_lcom: float = 0.8,
        verbose: bool = False,
    ) -> None:
        """Initialize detector with configurable thresholds.

        Args:
            min_lines: Minimum line count to consider as god class
            min_methods: Minimum method count to consider as god class
            max_lcom: Maximum LCOM threshold (higher = worse cohesion)
            verbose: Enable verbose output
        """
        self.min_lines = min_lines
        self.min_methods = min_methods
        self.max_lcom = max_lcom
        self.verbose = verbose

    def analyze_directory(self, path: str) -> list[ClassMetrics]:
        """Analyze all Python files in a directory.

        Args:
            path: Directory path to analyze

        Returns:
            List of god class metrics
        """
        god_classes = []
        path_obj = Path(path)

        # Find all Python files
        python_files = list(path_obj.rglob("*.py"))

        for file_path in python_files:
            try:
                file_god_classes = self.analyze_file(str(file_path))
                god_classes.extend(file_god_classes)
            except Exception as e:
                if self.verbose:
                    print(f"Error analyzing {file_path}: {e}")

        # Sort by severity and line count
        severity_order = {"critical": 0, "high": 1, "medium": 2}
        god_classes.sort(key=lambda x: (severity_order[x.severity], -x.line_count))

        return god_classes

    def analyze_file(self, file_path: str) -> list[ClassMetrics]:
        """Analyze a single Python file.

        Args:
            file_path: Path to Python file

        Returns:
            List of god class metrics found in file
        """
        god_classes = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)

            # Find all classes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    metrics = self.calculate_metrics(node, file_path, source)
                    if metrics.is_god_class:
                        god_classes.append(metrics)

        except Exception as e:
            if self.verbose:
                print(f"Error parsing {file_path}: {e}")

        return god_classes

    def calculate_metrics(
        self,
        node: ast.ClassDef,
        file_path: str,
        source: str | None = None,
    ) -> ClassMetrics:
        """Calculate metrics for a class.

        Args:
            node: Class AST node
            file_path: Path to source file
            source: Full source code (optional, will read from file if not provided)

        Returns:
            ClassMetrics object
        """
        if source is None:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

        # Basic metrics
        total_lines, code_lines = count_lines(node, source)
        method_counts = count_methods(node)
        method_count = sum(method_counts.values())
        attribute_count = count_attributes(node)
        complexity = calculate_complexity(node)

        # LCOM calculation
        lcom = self.calculate_lcom(node)

        # Detect responsibilities
        responsibilities = self.detect_responsibilities(node)

        # Determine if god class
        is_god_class = (
            code_lines >= self.min_lines
            or method_count >= self.min_methods
            or lcom >= self.max_lcom
        ) and method_count >= 10  # Minimum threshold to be meaningful

        metrics = ClassMetrics(
            name=node.name,
            file_path=file_path,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            line_count=code_lines,
            method_count=method_count,
            attribute_count=attribute_count,
            cyclomatic_complexity=complexity,
            lcom=lcom,
            responsibilities=responsibilities,
            is_god_class=is_god_class,
        )

        return metrics

    def calculate_lcom(self, node: ast.ClassDef) -> float:
        """Calculate Lack of Cohesion of Methods (LCOM).

        LCOM measures how related methods are to each other based on
        shared attribute access. Higher values indicate lower cohesion.

        Algorithm:
        - For each pair of methods, check if they share attributes
        - LCOM = (pairs not sharing) / (total pairs)
        - Range: 0 (perfect cohesion) to 1 (no cohesion)

        Args:
            node: Class AST node

        Returns:
            LCOM value (0-1)
        """
        methods = [
            n for n in node.body
            if isinstance(n, ast.FunctionDef) and n.name != "__init__"
        ]

        if len(methods) < 2:
            return 0.0

        # Count pairs that share attributes
        pairs_sharing = 0
        total_pairs = 0

        for i in range(len(methods)):
            for j in range(i + 1, len(methods)):
                total_pairs += 1
                shared_attrs = find_shared_attributes(methods[i], methods[j])
                if shared_attrs:
                    pairs_sharing += 1

        if total_pairs == 0:
            return 0.0

        # LCOM = pairs not sharing / total pairs
        lcom = 1.0 - (pairs_sharing / total_pairs)
        return round(lcom, 3)

    def detect_responsibilities(self, node: ast.ClassDef) -> list[str]:
        """Detect responsibilities based on method naming patterns.

        Args:
            node: Class AST node

        Returns:
            List of detected responsibility names
        """
        method_names = extract_method_names(node)

        # Group methods by common prefixes/patterns
        responsibility_groups: dict[str, list[str]] = defaultdict(list)

        # Common patterns
        patterns = {
            "data_access": ["get_", "set_", "fetch_", "retrieve_", "load_", "find_"],
            "validation": ["validate_", "check_", "verify_", "is_valid_", "ensure_"],
            "persistence": ["save_", "store_", "persist_", "write_", "delete_", "update_"],
            "business_logic": ["calculate_", "compute_", "process_", "execute_", "perform_"],
            "presentation": ["render_", "display_", "show_", "format_", "to_string", "to_dict"],
            "initialization": ["init_", "setup_", "configure_", "initialize_"],
            "error_handling": ["handle_", "on_error_", "catch_", "recover_"],
            "event_handling": ["on_", "handle_event_", "dispatch_", "trigger_"],
            "notification": ["notify_", "alert_", "send_", "publish_"],
            "transformation": ["transform_", "convert_", "map_", "adapt_"],
            "caching": ["cache_", "cached_", "invalidate_", "clear_cache"],
            "logging": ["log_", "trace_", "debug_", "info_", "warn_", "error_"],
        }

        for method_name in method_names:
            # Skip special methods
            if method_name.startswith("__") and method_name.endswith("__"):
                continue

            matched = False
            for responsibility, prefixes in patterns.items():
                for prefix in prefixes:
                    if method_name.lower().startswith(prefix):
                        responsibility_groups[responsibility].append(method_name)
                        matched = True
                        break
                if matched:
                    break

            # Check for domain-specific keywords in method name
            if not matched:
                # Extract keywords from method name
                words = method_name.lower().replace("_", " ").split()
                # Group by first meaningful word
                if len(words) > 1 and words[0] not in ["get", "set", "is", "has", "can"]:
                    key = f"{words[0]}_operations"
                    responsibility_groups[key].append(method_name)

        # Filter out responsibilities with too few methods (< 3)
        responsibilities = [
            resp.replace("_", " ").title()
            for resp, methods in responsibility_groups.items()
            if len(methods) >= 3
        ]

        return sorted(responsibilities)

    def suggest_extractions(self, metrics: ClassMetrics) -> list[ExtractionSuggestion]:
        """Suggest extractions for a god class.

        Args:
            metrics: ClassMetrics for the god class

        Returns:
            List of extraction suggestions
        """
        suggestions = []

        try:
            # Read the source file
            with open(metrics.file_path, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)

            # Find the class node
            class_node = None
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == metrics.name:
                    class_node = node
                    break

            if not class_node:
                return suggestions

            # Group methods by responsibility patterns
            method_names = extract_method_names(class_node)
            patterns = {
                "DataAccessor": ["get_", "set_", "fetch_", "retrieve_", "load_", "find_"],
                "Validator": ["validate_", "check_", "verify_", "is_valid_", "ensure_"],
                "PersistenceManager": ["save_", "store_", "persist_", "write_", "delete_", "update_"],
                "BusinessLogicProcessor": ["calculate_", "compute_", "process_", "execute_", "perform_"],
                "Formatter": ["render_", "display_", "show_", "format_", "to_string", "to_dict"],
                "EventHandler": ["on_", "handle_event_", "dispatch_", "trigger_"],
                "Notifier": ["notify_", "alert_", "send_", "publish_"],
                "Transformer": ["transform_", "convert_", "map_", "adapt_"],
                "CacheManager": ["cache_", "cached_", "invalidate_", "clear_cache"],
                "Logger": ["log_", "trace_", "debug_", "info_", "warn_", "error_"],
            }

            for class_name, prefixes in patterns.items():
                matching_methods = []
                for method_name in method_names:
                    for prefix in prefixes:
                        if method_name.lower().startswith(prefix):
                            matching_methods.append(method_name)
                            break

                if len(matching_methods) >= 3:
                    # Estimate lines
                    estimated_lines = 0
                    for method_name in matching_methods:
                        method_node = get_method_by_name(class_node, method_name)
                        if method_node:
                            _, code_lines = count_lines(method_node, source)
                            estimated_lines += code_lines

                    # Create suggestion
                    responsibility = class_name.replace("Manager", "").replace("Processor", "")
                    suggestions.append(
                        ExtractionSuggestion(
                            new_class_name=class_name,
                            methods_to_extract=matching_methods,
                            responsibility=responsibility,
                            estimated_lines=estimated_lines,
                        )
                    )

            # Sort by estimated lines (largest first)
            suggestions.sort(key=lambda x: x.estimated_lines, reverse=True)

        except Exception as e:
            if self.verbose:
                print(f"Error generating suggestions for {metrics.name}: {e}")

        return suggestions

    def generate_report(self, god_classes: list[ClassMetrics]) -> str:
        """Generate a detailed markdown report.

        Args:
            god_classes: List of god class metrics

        Returns:
            Markdown report string
        """
        report_lines = [
            "# God Class Detection Report",
            "",
            f"Found {len(god_classes)} god classes violating Single Responsibility Principle.",
            "",
            "## Summary",
            "",
            f"- **Total Classes Analyzed**: {len(god_classes)}",
            f"- **Critical Severity**: {sum(1 for c in god_classes if c.severity == 'critical')}",
            f"- **High Severity**: {sum(1 for c in god_classes if c.severity == 'high')}",
            f"- **Medium Severity**: {sum(1 for c in god_classes if c.severity == 'medium')}",
            "",
            "## Thresholds Used",
            "",
            f"- **Minimum Lines**: {self.min_lines}",
            f"- **Minimum Methods**: {self.min_methods}",
            f"- **Maximum LCOM**: {self.max_lcom}",
            "",
            "## Detailed Analysis",
            "",
        ]

        for i, cls in enumerate(god_classes, 1):
            report_lines.extend([
                f"### {i}. {cls.name} [{cls.severity.upper()}]",
                "",
                f"**File**: `{cls.file_path}:{cls.line_start}`",
                "",
                "**Metrics**:",
                f"- Lines of Code: {cls.line_count}",
                f"- Method Count: {cls.method_count}",
                f"- Attribute Count: {cls.attribute_count}",
                f"- Cyclomatic Complexity: {cls.cyclomatic_complexity}",
                f"- LCOM (Lack of Cohesion): {cls.lcom:.3f}",
                "",
            ])

            if cls.responsibilities:
                report_lines.extend([
                    "**Detected Responsibilities**:",
                    "",
                ])
                for resp in cls.responsibilities:
                    report_lines.append(f"- {resp}")
                report_lines.append("")

            # Add extraction suggestions
            suggestions = self.suggest_extractions(cls)
            if suggestions:
                report_lines.extend([
                    "**Extraction Suggestions**:",
                    "",
                ])
                for sug in suggestions[:5]:  # Top 5 suggestions
                    report_lines.extend([
                        f"- **{sug.new_class_name}**",
                        f"  - Responsibility: {sug.responsibility}",
                        f"  - Methods to Extract: {len(sug.methods_to_extract)}",
                        f"  - Estimated Lines: {sug.estimated_lines}",
                        f"  - Methods: `{', '.join(sug.methods_to_extract[:10])}`",
                        "",
                    ])

            report_lines.append("---")
            report_lines.append("")

        # Add recommendations
        report_lines.extend([
            "## Recommendations",
            "",
            "1. **Refactor Critical Classes First**: Focus on classes with 'critical' severity.",
            "2. **Extract Responsibilities**: Use the extraction suggestions to create new, focused classes.",
            "3. **Apply Single Responsibility Principle**: Each class should have one reason to change.",
            "4. **Improve Cohesion**: Methods in a class should work together on related data.",
            "5. **Use Composition**: Break large classes into smaller, composable components.",
            "",
            "## LCOM Interpretation",
            "",
            "- **0.0 - 0.3**: Good cohesion (methods work together)",
            "- **0.3 - 0.6**: Moderate cohesion (some refactoring may help)",
            "- **0.6 - 0.8**: Poor cohesion (strong candidate for refactoring)",
            "- **0.8 - 1.0**: Very poor cohesion (urgent refactoring needed)",
            "",
        ])

        return "\n".join(report_lines)
