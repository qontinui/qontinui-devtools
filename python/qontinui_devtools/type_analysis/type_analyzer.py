"""Type hint coverage analyzer for Python code.

This module analyzes Python codebases to measure type hint coverage,
identify missing type hints, and suggest improvements for type safety.
"""

import ast
import subprocess
import time
from pathlib import Path

from .models import AnyUsage, MypyError, TypeAnalysisReport, TypeCoverage, UntypedItem
from .type_inference import TypeInferenceEngine


class TypeHintVisitor(ast.NodeVisitor):
    """AST visitor to analyze type hints in Python code."""

    def __init__(self, file_path: str, inference_engine: TypeInferenceEngine) -> None:
        """Initialize the visitor.

        Args:
            file_path: Path to the file being analyzed
            inference_engine: Type inference engine
        """
        self.file_path = file_path
        self.inference_engine = inference_engine

        # Coverage metrics
        self.total_functions = 0
        self.typed_functions = 0
        self.fully_typed_functions = 0
        self.total_parameters = 0
        self.typed_parameters = 0
        self.total_returns = 0
        self.typed_returns = 0

        # Tracking
        self.untyped_items: list[UntypedItem] = []
        self.any_usages: list[AnyUsage] = []
        self.current_class: str | None = None

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition."""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition."""
        self._analyze_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition."""
        self._analyze_function(node)
        self.generic_visit(node)

    def _analyze_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Analyze a function for type hints.

        Args:
            node: Function AST node
        """
        # Skip special methods
        if node.name.startswith("__") and node.name.endswith("__"):
            return

        self.total_functions += 1

        # Count parameters and check type hints
        args = node.args
        all_params = (
            args.posonlyargs
            + args.args
            + args.kwonlyargs
            + ([args.vararg] if args.vararg else [])
            + ([args.kwarg] if args.kwarg else [])
        )

        # Filter out 'self' and 'cls'
        params = [p for p in all_params if p.arg not in ("self", "cls")]

        typed_param_count = 0
        for param in params:
            self.total_parameters += 1

            if param.annotation:
                self.typed_parameters += 1
                typed_param_count += 1

                # Check for Any usage
                if self._contains_any(param.annotation):
                    self.any_usages.append(
                        AnyUsage(
                            file_path=self.file_path,
                            line_number=param.lineno,
                            context=f"Parameter '{param.arg}' in {node.name}",
                            suggestion=None,
                        )
                    )
            else:
                # Missing type hint - try to infer
                suggested_type, confidence, reason = self.inference_engine.infer_parameter_type(
                    param, node
                )

                self.untyped_items.append(
                    UntypedItem(
                        item_type="parameter",
                        name=param.arg,
                        file_path=self.file_path,
                        line_number=param.lineno,
                        function_name=node.name,
                        class_name=self.current_class,
                        suggested_type=suggested_type,
                        confidence=confidence,
                        reason=reason,
                    )
                )

        # Check return type
        self.total_returns += 1
        has_return_hint = node.returns is not None

        if has_return_hint and node.returns is not None:
            self.typed_returns += 1

            # Check for Any usage
            if self._contains_any(node.returns):
                self.any_usages.append(
                    AnyUsage(
                        file_path=self.file_path,
                        line_number=node.lineno,
                        context=f"Return type of {node.name}",
                        suggestion=None,
                    )
                )
        else:
            # Missing return type hint - try to infer
            suggested_type, confidence, reason = self.inference_engine.infer_return_type(node)

            self.untyped_items.append(
                UntypedItem(
                    item_type="return",
                    name=f"{node.name} return",
                    file_path=self.file_path,
                    line_number=node.lineno,
                    function_name=node.name,
                    class_name=self.current_class,
                    suggested_type=suggested_type,
                    confidence=confidence,
                    reason=reason,
                )
            )

        # Determine if function is fully typed, partially typed, or untyped
        if has_return_hint and typed_param_count == len(params):
            self.fully_typed_functions += 1
            self.typed_functions += 1
        elif has_return_hint or typed_param_count > 0:
            self.typed_functions += 1

    def _contains_any(self, annotation: ast.expr) -> bool:
        """Check if annotation contains 'Any' type.

        Args:
            annotation: Type annotation AST node

        Returns:
            True if annotation contains Any
        """
        if isinstance(annotation, ast.Name):
            return annotation.id == "Any"
        elif isinstance(annotation, ast.Subscript):
            # Check container type and type parameters
            if self._contains_any(annotation.value):
                return True
            if isinstance(annotation.slice, ast.Tuple):
                return any(self._contains_any(elt) for elt in annotation.slice.elts)
            return self._contains_any(annotation.slice)
        elif isinstance(annotation, ast.BinOp):
            # Union types (T | U)
            return self._contains_any(annotation.left) or self._contains_any(annotation.right)

        return False

    def get_coverage(self) -> TypeCoverage:
        """Get coverage metrics from this visitor.

        Returns:
            TypeCoverage object
        """
        coverage = TypeCoverage(
            total_functions=self.total_functions,
            typed_functions=self.typed_functions,
            fully_typed_functions=self.fully_typed_functions,
            total_parameters=self.total_parameters,
            typed_parameters=self.typed_parameters,
            total_returns=self.total_returns,
            typed_returns=self.typed_returns,
            any_usage_count=len(self.any_usages),
        )
        coverage.calculate_percentages()
        return coverage


class TypeAnalyzer:
    """Analyzes type hint coverage in Python code."""

    def __init__(
        self, run_mypy: bool = True, strict_mode: bool = False, mypy_config: str | None = None
    ) -> None:
        """Initialize the type analyzer.

        Args:
            run_mypy: Whether to run mypy for additional checking
            strict_mode: Whether to use strict type checking
            mypy_config: Path to mypy configuration file
        """
        self.run_mypy = run_mypy
        self.strict_mode = strict_mode
        self.mypy_config = mypy_config
        self.inference_engine = TypeInferenceEngine()

    def analyze_file(
        self, file_path: str | Path
    ) -> tuple[TypeCoverage, list[UntypedItem], list[AnyUsage]]:
        """Analyze a single Python file.

        Args:
            file_path: Path to Python file

        Returns:
            Tuple of (coverage, untyped_items, any_usages)
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Read and parse file
        source = file_path.read_text(encoding="utf-8")

        try:
            tree = ast.parse(source, filename=str(file_path))
        except SyntaxError:
            # Return empty results for files with syntax errors
            return (TypeCoverage(), [], [])

        # Visit AST
        visitor = TypeHintVisitor(str(file_path), self.inference_engine)
        visitor.visit(tree)

        return (visitor.get_coverage(), visitor.untyped_items, visitor.any_usages)

    def analyze_directory(
        self, directory: str | Path, exclude_patterns: list[str] | None = None
    ) -> TypeAnalysisReport:
        """Analyze all Python files in a directory.

        Args:
            directory: Directory to analyze
            exclude_patterns: Patterns to exclude (e.g., ["**/test_*.py", "**/venv/**"])

        Returns:
            TypeAnalysisReport with complete analysis
        """
        start_time = time.time()
        directory = Path(directory)

        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        # Find all Python files
        python_files = list(directory.rglob("*.py"))

        # Apply exclusions
        if exclude_patterns:
            filtered_files = []
            for file in python_files:
                should_exclude = False
                for pattern in exclude_patterns:
                    if file.match(pattern):
                        should_exclude = True
                        break
                if not should_exclude:
                    filtered_files.append(file)
            python_files = filtered_files

        # Initialize overall metrics
        overall_coverage = TypeCoverage()
        module_coverage: dict[str, TypeCoverage] = {}
        class_coverage: dict[str, TypeCoverage] = {}
        all_untyped_items: list[UntypedItem] = []
        all_any_usages: list[AnyUsage] = []

        # Analyze each file
        for file_path in python_files:
            coverage, untyped_items, any_usages = self.analyze_file(file_path)

            # Accumulate overall metrics
            overall_coverage.total_functions += coverage.total_functions
            overall_coverage.typed_functions += coverage.typed_functions
            overall_coverage.fully_typed_functions += coverage.fully_typed_functions
            overall_coverage.total_parameters += coverage.total_parameters
            overall_coverage.typed_parameters += coverage.typed_parameters
            overall_coverage.total_returns += coverage.total_returns
            overall_coverage.typed_returns += coverage.typed_returns
            overall_coverage.any_usage_count += coverage.any_usage_count

            # Store module-level coverage
            module_name = self._get_module_name(file_path, directory)
            module_coverage[module_name] = coverage

            # Collect untyped items and any usages
            all_untyped_items.extend(untyped_items)
            all_any_usages.extend(any_usages)

            # Group by class
            for item in untyped_items:
                if item.class_name:
                    class_key = f"{module_name}.{item.class_name}"
                    if class_key not in class_coverage:
                        class_coverage[class_key] = TypeCoverage()

        # Calculate overall percentages
        overall_coverage.calculate_percentages()

        # Run mypy if requested
        mypy_errors: list[MypyError] = []
        if self.run_mypy:
            mypy_errors = self._run_mypy(directory)

        # Create report
        analysis_time = time.time() - start_time
        report = TypeAnalysisReport(
            overall_coverage=overall_coverage,
            module_coverage=module_coverage,
            class_coverage=class_coverage,
            untyped_items=all_untyped_items,
            any_usages=all_any_usages,
            mypy_errors=mypy_errors,
            analysis_time=analysis_time,
            files_analyzed=len(python_files),
            strict_mode=self.strict_mode,
        )

        return report

    def _get_module_name(self, file_path: Path, base_dir: Path) -> str:
        """Get module name from file path.

        Args:
            file_path: Path to Python file
            base_dir: Base directory

        Returns:
            Module name (e.g., "package.module")
        """
        try:
            relative = file_path.relative_to(base_dir)
            parts = list(relative.parts[:-1]) + [relative.stem]
            return ".".join(parts)
        except ValueError:
            return file_path.stem

    def _run_mypy(self, directory: Path) -> list[MypyError]:
        """Run mypy on the directory.

        Args:
            directory: Directory to check

        Returns:
            List of mypy errors
        """
        mypy_errors: list[MypyError] = []

        try:
            # Build mypy command
            cmd = ["mypy", str(directory)]

            if self.strict_mode:
                cmd.append("--strict")

            if self.mypy_config:
                cmd.extend(["--config-file", self.mypy_config])

            # Run mypy
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )

            # Parse mypy output
            for line in result.stdout.split("\n"):
                if not line.strip():
                    continue

                # Parse line format: file:line:col: severity: message [error-code]
                parts = line.split(":", 4)
                if len(parts) >= 4:
                    file_path = parts[0].strip()
                    try:
                        line_num = int(parts[1].strip())
                        col = int(parts[2].strip()) if parts[2].strip().isdigit() else 0
                        rest = parts[3] if len(parts) == 4 else parts[4]

                        # Extract severity and message
                        if "error:" in rest:
                            severity = "error"
                            message = rest.split("error:", 1)[1].strip()
                        elif "warning:" in rest:
                            severity = "warning"
                            message = rest.split("warning:", 1)[1].strip()
                        elif "note:" in rest:
                            severity = "note"
                            message = rest.split("note:", 1)[1].strip()
                        else:
                            severity = "info"
                            message = rest.strip()

                        # Extract error code
                        error_code = None
                        if "[" in message and "]" in message:
                            error_code = message[message.rfind("[") + 1 : message.rfind("]")]

                        mypy_errors.append(
                            MypyError(
                                file_path=file_path,
                                line_number=line_num,
                                column=col,
                                severity=severity,
                                message=message,
                                error_code=error_code,
                            )
                        )
                    except (ValueError, IndexError):
                        continue

        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Mypy not available or timed out
            pass

        return mypy_errors

    def generate_report_text(self, report: TypeAnalysisReport) -> str:
        """Generate a text report from analysis.

        Args:
            report: Analysis report

        Returns:
            Formatted text report
        """
        lines = []

        # Header
        lines.append("=" * 80)
        lines.append("TYPE HINT COVERAGE ANALYSIS")
        lines.append("=" * 80)
        lines.append("")

        # Summary
        lines.append("SUMMARY")
        lines.append("-" * 80)
        lines.append(f"Files analyzed: {report.files_analyzed}")
        lines.append(f"Analysis time: {report.analysis_time:.2f}s")
        lines.append(f"Strict mode: {'Yes' if report.strict_mode else 'No'}")
        lines.append("")

        # Coverage metrics
        cov = report.overall_coverage
        lines.append("COVERAGE METRICS")
        lines.append("-" * 80)
        lines.append(f"Overall coverage: {cov.coverage_percentage:.1f}%")
        lines.append(f"Parameter coverage: {cov.parameter_coverage:.1f}%")
        lines.append(f"Return coverage: {cov.return_coverage:.1f}%")
        lines.append("")
        lines.append(f"Total functions: {cov.total_functions}")
        lines.append(
            f"Fully typed: {cov.fully_typed_functions} ({cov.fully_typed_functions/cov.total_functions*100 if cov.total_functions > 0 else 0:.1f}%)"
        )
        lines.append(f"Partially typed: {cov.typed_functions - cov.fully_typed_functions}")
        lines.append(f"Untyped: {cov.total_functions - cov.typed_functions}")
        lines.append("")
        lines.append(f"Total parameters: {cov.total_parameters}")
        lines.append(f"Typed parameters: {cov.typed_parameters}")
        lines.append(f"Total returns: {cov.total_returns}")
        lines.append(f"Typed returns: {cov.typed_returns}")
        lines.append(f"Any usage count: {cov.any_usage_count}")
        lines.append("")

        # Top untyped items
        if report.untyped_items:
            lines.append("TOP UNTYPED ITEMS")
            lines.append("-" * 80)
            sorted_items = report.get_sorted_untyped_items(limit=20)
            for item in sorted_items:
                lines.append(f"{item.file_path}:{item.line_number}")
                lines.append(f"  Type: {item.item_type}")
                lines.append(f"  Name: {item.get_full_name()}")
                if item.suggested_type:
                    lines.append(
                        f"  Suggestion: {item.suggested_type} (confidence: {item.confidence:.2f})"
                    )
                    if item.reason:
                        lines.append(f"  Reason: {item.reason}")
                lines.append("")

        # Mypy errors
        if report.mypy_errors:
            lines.append("MYPY ERRORS")
            lines.append("-" * 80)
            for error in report.mypy_errors[:20]:
                lines.append(f"{error.file_path}:{error.line_number}:{error.column}")
                lines.append(f"  [{error.severity.upper()}] {error.message}")
                if error.error_code:
                    lines.append(f"  Code: {error.error_code}")
                lines.append("")

        # Module coverage
        if report.module_coverage:
            lines.append("MODULE COVERAGE")
            lines.append("-" * 80)
            sorted_modules = sorted(
                report.module_coverage.items(), key=lambda x: x[1].coverage_percentage
            )
            for module_name, module_cov in sorted_modules[:10]:
                lines.append(f"{module_name}: {module_cov.coverage_percentage:.1f}%")
            lines.append("")

        lines.append("=" * 80)

        return "\n".join(lines)
