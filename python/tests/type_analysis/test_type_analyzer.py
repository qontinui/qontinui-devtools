"""Tests for type hint analyzer.

This module contains comprehensive tests for the type hint analysis tools.
"""

import ast
from pathlib import Path

from qontinui_devtools.type_analysis import (TypeAnalysisReport, TypeAnalyzer,
                                             TypeCoverage, TypeHintVisitor,
                                             TypeInferenceEngine, UntypedItem)


class TestTypeInferenceEngine:
    """Tests for type inference engine."""

    def test_infer_from_default_none(self) -> None:
        """Test inference from None default."""
        engine = TypeInferenceEngine()
        node = ast.Constant(value=None)
        inferred, confidence = engine.infer_from_default(node)
        assert inferred == "None"
        assert confidence == 0.9

    def test_infer_from_default_bool(self) -> None:
        """Test inference from bool default."""
        engine = TypeInferenceEngine()
        node = ast.Constant(value=True)
        inferred, confidence = engine.infer_from_default(node)
        assert inferred == "bool"
        assert confidence == 1.0

    def test_infer_from_default_int(self) -> None:
        """Test inference from int default."""
        engine = TypeInferenceEngine()
        node = ast.Constant(value=42)
        inferred, confidence = engine.infer_from_default(node)
        assert inferred == "int"
        assert confidence == 1.0

    def test_infer_from_default_float(self) -> None:
        """Test inference from float default."""
        engine = TypeInferenceEngine()
        node = ast.Constant(value=3.14)
        inferred, confidence = engine.infer_from_default(node)
        assert inferred == "float"
        assert confidence == 1.0

    def test_infer_from_default_str(self) -> None:
        """Test inference from str default."""
        engine = TypeInferenceEngine()
        node = ast.Constant(value="hello")
        inferred, confidence = engine.infer_from_default(node)
        assert inferred == "str"
        assert confidence == 1.0

    def test_infer_from_default_empty_list(self) -> None:
        """Test inference from empty list default."""
        engine = TypeInferenceEngine()
        node = ast.List(elts=[])
        inferred, confidence = engine.infer_from_default(node)
        assert inferred == "list[Any]"
        assert confidence == 0.8

    def test_infer_from_default_list_with_elements(self) -> None:
        """Test inference from list with elements."""
        engine = TypeInferenceEngine()
        node = ast.List(elts=[ast.Constant(value=1), ast.Constant(value=2)])
        inferred, confidence = engine.infer_from_default(node)
        assert inferred == "list[int]"
        assert confidence == 0.8

    def test_infer_from_default_empty_dict(self) -> None:
        """Test inference from empty dict default."""
        engine = TypeInferenceEngine()
        node = ast.Dict(keys=[], values=[])
        inferred, confidence = engine.infer_from_default(node)
        assert inferred == "dict[str, Any]"
        assert confidence == 0.8

    def test_infer_from_default_empty_tuple(self) -> None:
        """Test inference from empty tuple default."""
        engine = TypeInferenceEngine()
        node = ast.Tuple(elts=[])
        inferred, confidence = engine.infer_from_default(node)
        assert inferred == "tuple[()]"
        assert confidence == 0.9

    def test_infer_from_default_tuple_with_elements(self) -> None:
        """Test inference from tuple with elements."""
        engine = TypeInferenceEngine()
        node = ast.Tuple(elts=[ast.Constant(value=1), ast.Constant(value="a")])
        inferred, confidence = engine.infer_from_default(node)
        assert inferred == "tuple[int, str]"
        assert confidence == 0.7

    def test_infer_from_name_with_suffix(self) -> None:
        """Test inference from parameter name with suffix."""
        engine = TypeInferenceEngine()
        inferred, confidence = engine.infer_from_name("user_id")
        assert inferred == "int"
        assert confidence == 0.5

    def test_infer_from_name_with_prefix(self) -> None:
        """Test inference from parameter name with prefix."""
        engine = TypeInferenceEngine()
        inferred, confidence = engine.infer_from_name("is_active")
        assert inferred == "bool"
        assert confidence == 0.5

    def test_infer_from_name_count(self) -> None:
        """Test inference from count parameter."""
        engine = TypeInferenceEngine()
        inferred, confidence = engine.infer_from_name("count")
        # Won't match without suffix
        assert inferred is None

    def test_infer_return_type_no_returns(self) -> None:
        """Test inference when function has no return statements."""
        engine = TypeInferenceEngine()
        code = """
def func() -> None:
    x = 1
    """
        tree = ast.parse(code)
        func_node = tree.body[0]
        assert isinstance(func_node, (ast.FunctionDef, ast.AsyncFunctionDef))
        inferred, confidence, reason = engine.infer_return_type(func_node)
        assert inferred == "None"
        assert confidence == 0.9
        assert "No return statements" in reason

    def test_infer_return_type_none_returns(self) -> None:
        """Test inference when function returns None."""
        engine = TypeInferenceEngine()
        code = """
def func() -> None:
    return None
    """
        tree = ast.parse(code)
        func_node = tree.body[0]
        assert isinstance(func_node, (ast.FunctionDef, ast.AsyncFunctionDef))
        inferred, confidence, reason = engine.infer_return_type(func_node)
        assert inferred == "None"
        assert confidence == 0.9

    def test_infer_return_type_constant(self) -> None:
        """Test inference when function returns a constant."""
        engine = TypeInferenceEngine()
        code = """
def func() -> Any:
    return 42
    """
        tree = ast.parse(code)
        func_node = tree.body[0]
        assert isinstance(func_node, (ast.FunctionDef, ast.AsyncFunctionDef))
        inferred, confidence, reason = engine.infer_return_type(func_node)
        assert inferred == "int"
        assert confidence == 0.7

    def test_infer_return_type_multiple_types(self) -> None:
        """Test inference when function returns multiple types."""
        engine = TypeInferenceEngine()
        code = """
def func(x) -> Any:
    if x:
        return 42
    return "hello"
    """
        tree = ast.parse(code)
        func_node = tree.body[0]
        assert isinstance(func_node, (ast.FunctionDef, ast.AsyncFunctionDef))
        inferred, confidence, reason = engine.infer_return_type(func_node)
        assert inferred is not None and "int" in inferred and "str" in inferred
        assert inferred is not None and "|" in inferred

    def test_infer_return_type_with_none(self) -> None:
        """Test inference when function returns value or None."""
        engine = TypeInferenceEngine()
        code = """
def func(x) -> Any:
    if x:
        return 42
    return None
    """
        tree = ast.parse(code)
        func_node = tree.body[0]
        assert isinstance(func_node, (ast.FunctionDef, ast.AsyncFunctionDef))
        inferred, confidence, reason = engine.infer_return_type(func_node)
        assert inferred is not None and "int" in inferred
        assert inferred is not None and "None" in inferred
        assert inferred is not None and "|" in inferred

    def test_infer_expr_type_list(self) -> None:
        """Test expression type inference for list."""
        engine = TypeInferenceEngine()
        node = ast.List(elts=[])
        result = engine._infer_expr_type(node)
        assert result == "list[Any]"

    def test_infer_expr_type_dict(self) -> None:
        """Test expression type inference for dict."""
        engine = TypeInferenceEngine()
        node = ast.Dict(keys=[], values=[])
        result = engine._infer_expr_type(node)
        assert result == "dict[str, Any]"

    def test_infer_expr_type_comparison(self) -> None:
        """Test expression type inference for comparison."""
        engine = TypeInferenceEngine()
        node = ast.Compare(
            left=ast.Constant(value=1), ops=[ast.Lt()], comparators=[ast.Constant(value=2)]
        )
        result = engine._infer_expr_type(node)
        assert result == "bool"

    def test_suggest_type_improvements_any(self) -> None:
        """Test suggestions for Any type."""
        engine = TypeInferenceEngine()
        suggestions = engine.suggest_type_improvements("Any")
        assert len(suggestions) > 0
        assert any("more specific" in s for s in suggestions)

    def test_suggest_type_improvements_bare_list(self) -> None:
        """Test suggestions for bare list."""
        engine = TypeInferenceEngine()
        suggestions = engine.suggest_type_improvements("list")
        assert len(suggestions) > 0
        assert any("list[T]" in s for s in suggestions)

    def test_suggest_type_improvements_optional(self) -> None:
        """Test suggestions for Optional."""
        engine = TypeInferenceEngine()
        suggestions = engine.suggest_type_improvements("Optional[int]")
        assert len(suggestions) > 0
        assert any("T | None" in s for s in suggestions)


class TestTypeCoverage:
    """Tests for TypeCoverage model."""

    def test_calculate_percentages_all_typed(self) -> None:
        """Test percentage calculation when everything is typed."""
        coverage = TypeCoverage(
            total_functions=10,
            typed_functions=10,
            total_parameters=20,
            typed_parameters=20,
            total_returns=10,
            typed_returns=10,
        )
        coverage.calculate_percentages()
        assert coverage.coverage_percentage == 100.0
        assert coverage.parameter_coverage == 100.0
        assert coverage.return_coverage == 100.0

    def test_calculate_percentages_half_typed(self) -> None:
        """Test percentage calculation when half is typed."""
        coverage = TypeCoverage(
            total_functions=10,
            typed_functions=5,
            total_parameters=20,
            typed_parameters=10,
            total_returns=10,
            typed_returns=5,
        )
        coverage.calculate_percentages()
        assert coverage.coverage_percentage == 50.0
        assert coverage.parameter_coverage == 50.0
        assert coverage.return_coverage == 50.0

    def test_calculate_percentages_no_items(self) -> None:
        """Test percentage calculation with no items."""
        coverage = TypeCoverage()
        coverage.calculate_percentages()
        assert coverage.coverage_percentage == 100.0
        assert coverage.parameter_coverage == 100.0
        assert coverage.return_coverage == 100.0


class TestUntypedItem:
    """Tests for UntypedItem model."""

    def test_get_full_name_simple(self) -> None:
        """Test full name for simple item."""
        item = UntypedItem(
            item_type="parameter",
            name="x",
            file_path="/test.py",
            line_number=1,
        )
        assert item.get_full_name() == "x"

    def test_get_full_name_with_function(self) -> None:
        """Test full name with function."""
        item = UntypedItem(
            item_type="parameter",
            name="x",
            file_path="/test.py",
            line_number=1,
            function_name="foo",
        )
        assert item.get_full_name() == "foo.x"

    def test_get_full_name_with_class_and_function(self) -> None:
        """Test full name with class and function."""
        item = UntypedItem(
            item_type="parameter",
            name="x",
            file_path="/test.py",
            line_number=1,
            class_name="MyClass",
            function_name="method",
        )
        assert item.get_full_name() == "MyClass.method.x"


class TestTypeHintVisitor:
    """Tests for TypeHintVisitor."""

    def test_visit_typed_function(self) -> None:
        """Test visiting a fully typed function."""
        code = """
def add(x: int, y: int) -> int:
    return x + y
"""
        tree = ast.parse(code)
        visitor = TypeHintVisitor("/test.py", TypeInferenceEngine())
        visitor.visit(tree)

        coverage = visitor.get_coverage()
        assert coverage.total_functions == 1
        assert coverage.fully_typed_functions == 1
        assert coverage.typed_parameters == 2
        assert coverage.typed_returns == 1
        assert len(visitor.untyped_items) == 0

    def test_visit_untyped_function(self) -> None:
        """Test visiting an untyped function."""
        code = """
def add(x, y) -> Any:
    return x + y
"""
        tree = ast.parse(code)
        visitor = TypeHintVisitor("/test.py", TypeInferenceEngine())
        visitor.visit(tree)

        coverage = visitor.get_coverage()
        assert coverage.total_functions == 1
        assert coverage.fully_typed_functions == 0
        assert coverage.typed_functions == 0
        assert coverage.typed_parameters == 0
        assert coverage.typed_returns == 0
        assert len(visitor.untyped_items) == 3  # 2 params + 1 return

    def test_visit_partially_typed_function(self) -> None:
        """Test visiting a partially typed function."""
        code = """
def add(x: int, y) -> int:
    return x + y
"""
        tree = ast.parse(code)
        visitor = TypeHintVisitor("/test.py", TypeInferenceEngine())
        visitor.visit(tree)

        coverage = visitor.get_coverage()
        assert coverage.total_functions == 1
        assert coverage.fully_typed_functions == 0
        assert coverage.typed_functions == 1
        assert coverage.typed_parameters == 1
        assert coverage.typed_returns == 1

    def test_visit_function_with_defaults(self) -> None:
        """Test visiting function with default values."""
        code = """
def greet(name: str, greeting="Hello") -> Any:
    return f"{greeting}, {name}"
"""
        tree = ast.parse(code)
        visitor = TypeHintVisitor("/test.py", TypeInferenceEngine())
        visitor.visit(tree)

        # Should suggest str for greeting based on default
        untyped_params = [item for item in visitor.untyped_items if item.item_type == "parameter"]
        assert len(untyped_params) == 1
        assert untyped_params[0].name == "greeting"
        assert untyped_params[0].suggested_type == "str"

    def test_visit_class_method(self) -> None:
        """Test visiting class method."""
        code = """
class Calculator:
    def add(self, x: int, y: int) -> int:
        return x + y
"""
        tree = ast.parse(code)
        visitor = TypeHintVisitor("/test.py", TypeInferenceEngine())
        visitor.visit(tree)

        coverage = visitor.get_coverage()
        assert coverage.total_functions == 1
        assert coverage.fully_typed_functions == 1
        # self is not counted
        assert coverage.total_parameters == 2

    def test_visit_async_function(self) -> None:
        """Test visiting async function."""
        code = """
async def fetch(url: str) -> str:
    return "data"
"""
        tree = ast.parse(code)
        visitor = TypeHintVisitor("/test.py", TypeInferenceEngine())
        visitor.visit(tree)

        coverage = visitor.get_coverage()
        assert coverage.total_functions == 1
        assert coverage.fully_typed_functions == 1

    def test_skip_special_methods(self) -> None:
        """Test that special methods are skipped."""
        code = """
class MyClass:
    def __init__(self, x) -> None:
        self.x = x

    def __str__(self) -> Any:
        return str(self.x)
"""
        tree = ast.parse(code)
        visitor = TypeHintVisitor("/test.py", TypeInferenceEngine())
        visitor.visit(tree)

        coverage = visitor.get_coverage()
        assert coverage.total_functions == 0  # Special methods skipped

    def test_detect_any_usage_parameter(self) -> None:
        """Test detection of Any in parameter."""
        code = """
from typing import Any

def process(data: Any) -> None:
    pass
"""
        tree = ast.parse(code)
        visitor = TypeHintVisitor("/test.py", TypeInferenceEngine())
        visitor.visit(tree)

        assert len(visitor.any_usages) == 1
        assert "data" in visitor.any_usages[0].context

    def test_detect_any_usage_return(self) -> None:
        """Test detection of Any in return type."""
        code = """
from typing import Any

def get_data() -> Any:
    return {}
"""
        tree = ast.parse(code)
        visitor = TypeHintVisitor("/test.py", TypeInferenceEngine())
        visitor.visit(tree)

        assert len(visitor.any_usages) == 1
        assert "get_data" in visitor.any_usages[0].context

    def test_detect_any_in_generic(self) -> None:
        """Test detection of Any in generic types."""
        code = """
from typing import Any

def process(items: list[Any]) -> None:
    pass
"""
        tree = ast.parse(code)
        visitor = TypeHintVisitor("/test.py", TypeInferenceEngine())
        visitor.visit(tree)

        assert len(visitor.any_usages) == 1


class TestTypeAnalyzer:
    """Tests for TypeAnalyzer."""

    def test_analyze_file_typed(self, tmp_path: Path) -> None:
        """Test analyzing a well-typed file."""
        code = """
def add(x: int, y: int) -> int:
    return x + y

def greet(name: str) -> str:
    return f"Hello, {name}"
"""
        file_path = tmp_path / "test.py"
        file_path.write_text(code)

        analyzer = TypeAnalyzer(run_mypy=False)
        coverage, untyped_items, any_usages = analyzer.analyze_file(file_path)

        assert coverage.total_functions == 2
        assert coverage.fully_typed_functions == 2
        assert len(untyped_items) == 0

    def test_analyze_file_untyped(self, tmp_path: Path) -> None:
        """Test analyzing an untyped file."""
        code = """
def add(x, y) -> Any:
    return x + y

def greet(name) -> Any:
    return f"Hello, {name}"
"""
        file_path = tmp_path / "test.py"
        file_path.write_text(code)

        analyzer = TypeAnalyzer(run_mypy=False)
        coverage, untyped_items, any_usages = analyzer.analyze_file(file_path)

        assert coverage.total_functions == 2
        assert coverage.fully_typed_functions == 0
        assert len(untyped_items) > 0

    def test_analyze_file_syntax_error(self, tmp_path: Path) -> None:
        """Test analyzing file with syntax error."""
        code = """
def broken(
    # Missing closing paren
"""
        file_path = tmp_path / "test.py"
        file_path.write_text(code)

        analyzer = TypeAnalyzer(run_mypy=False)
        coverage, untyped_items, any_usages = analyzer.analyze_file(file_path)

        # Should return empty results without crashing
        assert coverage.total_functions == 0

    def test_analyze_directory(self, tmp_path: Path) -> None:
        """Test analyzing a directory."""
        # Create multiple files
        file1 = tmp_path / "module1.py"
        file1.write_text(
            """
def typed_func(x: int) -> int:
    return x * 2
"""
        )

        file2 = tmp_path / "module2.py"
        file2.write_text(
            """
def untyped_func(x, y) -> Any:
    return x + y
"""
        )

        analyzer = TypeAnalyzer(run_mypy=False)
        report = analyzer.analyze_directory(tmp_path)

        assert report.files_analyzed == 2
        assert report.overall_coverage.total_functions == 2
        assert len(report.module_coverage) == 2

    def test_analyze_directory_with_exclusions(self, tmp_path: Path) -> None:
        """Test analyzing directory with exclusions."""
        # Create files
        (tmp_path / "main.py").write_text("def foo(): pass")
        (tmp_path / "test_main.py").write_text("def test_foo(): pass")

        analyzer = TypeAnalyzer(run_mypy=False)
        report = analyzer.analyze_directory(tmp_path, exclude_patterns=["**/test_*.py"])

        assert report.files_analyzed == 1

    def test_get_module_name(self, tmp_path: Path) -> None:
        """Test module name extraction."""
        analyzer = TypeAnalyzer(run_mypy=False)

        file_path = tmp_path / "package" / "module.py"
        file_path.parent.mkdir()
        file_path.touch()

        module_name = analyzer._get_module_name(file_path, tmp_path)
        assert module_name == "package.module"

    def test_generate_report_text(self, tmp_path: Path) -> None:
        """Test text report generation."""
        code = """
def add(x: int, y: int) -> int:
    return x + y
"""
        file_path = tmp_path / "test.py"
        file_path.write_text(code)

        analyzer = TypeAnalyzer(run_mypy=False)
        report = analyzer.analyze_directory(tmp_path)
        text = analyzer.generate_report_text(report)

        assert "TYPE HINT COVERAGE ANALYSIS" in text
        assert "COVERAGE METRICS" in text
        assert "100.0%" in text  # Fully typed


class TestTypeAnalysisReport:
    """Tests for TypeAnalysisReport."""

    def test_get_summary(self) -> None:
        """Test getting report summary."""
        coverage = TypeCoverage(
            total_functions=10,
            typed_functions=8,
            fully_typed_functions=6,
            total_parameters=20,
            typed_parameters=15,
            total_returns=10,
            typed_returns=8,
        )
        coverage.calculate_percentages()

        report = TypeAnalysisReport(
            overall_coverage=coverage,
            files_analyzed=5,
            analysis_time=1.5,
        )

        summary = report.get_summary()
        assert summary["total_functions"] == 10
        assert summary["typed_functions"] == 8
        assert summary["files_analyzed"] == 5
        assert summary["analysis_time"] == 1.5

    def test_get_sorted_untyped_items(self) -> None:
        """Test sorting untyped items."""
        items = [
            UntypedItem("parameter", "x", "/test.py", 10),
            UntypedItem("function", "foo", "/test.py", 5),
            UntypedItem("return", "bar return", "/test.py", 20),
        ]

        report = TypeAnalysisReport(
            overall_coverage=TypeCoverage(),
            untyped_items=items,
        )

        sorted_items = report.get_sorted_untyped_items()

        # Functions should come first, then returns, then parameters
        assert sorted_items[0].item_type == "function"
        assert sorted_items[1].item_type == "return"
        assert sorted_items[2].item_type == "parameter"

    def test_get_sorted_untyped_items_with_limit(self) -> None:
        """Test sorting with limit."""
        items = [UntypedItem("parameter", f"x{i}", "/test.py", i) for i in range(100)]

        report = TypeAnalysisReport(
            overall_coverage=TypeCoverage(),
            untyped_items=items,
        )

        sorted_items = report.get_sorted_untyped_items(limit=10)
        assert len(sorted_items) == 10


class TestIntegration:
    """Integration tests for type analysis."""

    def test_full_analysis_workflow(self, tmp_path: Path) -> None:
        """Test complete analysis workflow."""
        # Create a realistic Python package
        package = tmp_path / "mypackage"
        package.mkdir()

        (package / "__init__.py").write_text("")

        (package / "math_utils.py").write_text(
            """
def add(x: int, y: int) -> int:
    '''Add two numbers.'''
    return x + y

def multiply(x, y) -> Any:
    '''Multiply two numbers (untyped).'''
    return x * y
"""
        )

        (package / "string_utils.py").write_text(
            """
def upper(s: str) -> str:
    '''Convert to uppercase.'''
    return s.upper()

def reverse(s) -> Any:
    '''Reverse string (untyped).'''
    return s[::-1]
"""
        )

        # Run analysis
        analyzer = TypeAnalyzer(run_mypy=False)
        report = analyzer.analyze_directory(package)

        # Verify results
        assert report.files_analyzed == 3  # __init__, math_utils, string_utils
        assert report.overall_coverage.total_functions == 4
        assert report.overall_coverage.fully_typed_functions == 2
        assert len(report.untyped_items) > 0

        # Check module coverage (module names don't include parent dir)
        module_names = list(report.module_coverage.keys())
        assert any("math_utils" in name for name in module_names)
        assert any("string_utils" in name for name in module_names)

        # Generate report
        text = analyzer.generate_report_text(report)
        assert len(text) > 0

    def test_inference_suggestions(self, tmp_path: Path) -> None:
        """Test that inference provides useful suggestions."""
        code = """
def process(count=10, name="default", items=[], enabled=True) -> Any:
    return count + len(items)
"""
        file_path = tmp_path / "test.py"
        file_path.write_text(code)

        analyzer = TypeAnalyzer(run_mypy=False)
        coverage, untyped_items, any_usages = analyzer.analyze_file(file_path)

        # Check that suggestions were made
        param_items = [item for item in untyped_items if item.item_type == "parameter"]

        # Find specific parameters
        count_item = next((item for item in param_items if item.name == "count"), None)
        name_item = next((item for item in param_items if item.name == "name"), None)
        enabled_item = next((item for item in param_items if item.name == "enabled"), None)

        assert count_item and count_item.suggested_type == "int"
        assert name_item and name_item.suggested_type == "str"
        assert enabled_item and enabled_item.suggested_type == "bool"

    def test_any_detection(self, tmp_path: Path) -> None:
        """Test that Any usage is properly detected."""
        code = """
from typing import Any

def process(data: Any) -> Any:
    return data

def convert(items: list[Any]) -> dict[str, Any]:
    return {str(i): item for i, item in enumerate(items)}
"""
        file_path = tmp_path / "test.py"
        file_path.write_text(code)

        analyzer = TypeAnalyzer(run_mypy=False)
        coverage, untyped_items, any_usages = analyzer.analyze_file(file_path)

        # Should detect multiple Any usages
        assert len(any_usages) >= 4  # data param, return, list[Any], dict[str, Any]

    def test_complex_return_inference(self, tmp_path: Path) -> None:
        """Test inference for complex return types."""
        code = """
def get_value(use_int) -> Any:
    if use_int:
        return 42
    else:
        return "hello"

def maybe_value(exists) -> Any:
    if exists:
        return [1, 2, 3]
    return None
"""
        file_path = tmp_path / "test.py"
        file_path.write_text(code)

        analyzer = TypeAnalyzer(run_mypy=False)
        coverage, untyped_items, any_usages = analyzer.analyze_file(file_path)

        # Find return type suggestions
        return_items = [item for item in untyped_items if item.item_type == "return"]

        get_value_return = next((item for item in return_items if "get_value" in item.name), None)
        maybe_value_return = next(
            (item for item in return_items if "maybe_value" in item.name), None
        )

        # get_value should suggest union of int and str
        assert get_value_return
        assert (
            get_value_return.suggested_type is not None and "|" in get_value_return.suggested_type
        )
        assert (
            get_value_return.suggested_type is not None and "int" in get_value_return.suggested_type
        )
        assert (
            get_value_return.suggested_type is not None and "str" in get_value_return.suggested_type
        )

        # maybe_value should suggest list with None
        assert maybe_value_return
        assert (
            maybe_value_return.suggested_type is not None
            and "None" in maybe_value_return.suggested_type
        )
