"""Tests for dead code detector."""

from pathlib import Path

import pytest
from qontinui_devtools.code_quality.dead_code_detector import (
    DeadCodeDetector, DefinitionCollector, UsageCollector)


class TestDefinitionCollector:
    """Test DefinitionCollector."""

    def test_collect_function_definitions(self, tmp_path: Path) -> None:
        """Test collecting function definitions."""
        code = """
def public_function() -> None:
    pass

def _private_function() -> None:
    pass

def __special_method__() -> None:
    pass
"""
        file_path = tmp_path / "test.py"
        file_path.write_text(code)

        import ast

        tree = ast.parse(code)
        collector = DefinitionCollector(str(file_path))
        collector.visit(tree)

        assert "public_function" in collector.functions
        assert "_private_function" in collector.functions
        # Special methods like __special_method__ are skipped (they're used implicitly)
        assert "__special_method__" not in collector.functions

    def test_collect_class_definitions(self, tmp_path: Path) -> None:
        """Test collecting class definitions."""
        code = """
class PublicClass:
    pass

class _PrivateClass:
    pass
"""
        file_path = tmp_path / "test.py"
        file_path.write_text(code)

        import ast

        tree = ast.parse(code)
        collector = DefinitionCollector(str(file_path))
        collector.visit(tree)

        assert "PublicClass" in collector.classes
        assert "_PrivateClass" not in collector.classes  # Private classes skipped

    def test_collect_imports(self, tmp_path: Path) -> None:
        """Test collecting import statements."""
        code = """
import os
import sys as system
from pathlib import Path
from typing import List as ListType, Any
"""
        file_path = tmp_path / "test.py"
        file_path.write_text(code)

        import ast

        tree = ast.parse(code)
        collector = DefinitionCollector(str(file_path))
        collector.visit(tree)

        assert "os" in collector.imports
        assert "system" in collector.imports  # Aliased import
        assert "Path" in collector.imports
        assert "ListType" in collector.imports  # Aliased from import

    def test_collect_variables(self, tmp_path: Path) -> None:
        """Test collecting module-level variables."""
        code = """
PUBLIC_VAR = 42
_private_var = "private"

class MyClass:
    class_var = "not collected"

def func() -> None:
    local_var = "not collected"
"""
        file_path = tmp_path / "test.py"
        file_path.write_text(code)

        import ast

        tree = ast.parse(code)
        collector = DefinitionCollector(str(file_path))
        collector.visit(tree)

        assert "PUBLIC_VAR" in collector.variables
        assert "_private_var" not in collector.variables  # Private vars skipped
        assert "class_var" not in collector.variables  # Class vars not collected
        assert "local_var" not in collector.variables  # Local vars not collected

    def test_annotated_assignment(self, tmp_path: Path) -> None:
        """Test collecting annotated assignments."""
        code = """
public_var: int = 42
another_var: str
"""
        file_path = tmp_path / "test.py"
        file_path.write_text(code)

        import ast

        tree = ast.parse(code)
        collector = DefinitionCollector(str(file_path))
        collector.visit(tree)

        assert "public_var" in collector.variables
        assert "another_var" in collector.variables

    def test_nested_functions(self, tmp_path: Path) -> None:
        """Test that nested functions are handled correctly."""
        code = """
def outer() -> Any:
    def inner() -> None:
        pass
    return inner
"""
        file_path = tmp_path / "test.py"
        file_path.write_text(code)

        import ast

        tree = ast.parse(code)
        collector = DefinitionCollector(str(file_path))
        collector.visit(tree)

        assert "outer" in collector.functions
        # Nested functions are not tracked at module level
        assert "inner" not in collector.functions


class TestUsageCollector:
    """Test UsageCollector."""

    def test_collect_name_usage(self) -> None:
        """Test collecting name references."""
        code = """
x = 42
y = x + 1
"""
        import ast

        tree = ast.parse(code)
        collector = UsageCollector()
        collector.visit(tree)

        assert "x" in collector.used_names

    def test_collect_function_calls(self) -> None:
        """Test collecting function calls."""
        code = """
result = some_function(arg1, arg2)
obj.method_call()
"""
        import ast

        tree = ast.parse(code)
        collector = UsageCollector()
        collector.visit(tree)

        assert "some_function" in collector.used_names
        assert "method_call" in collector.used_names

    def test_collect_attribute_access(self) -> None:
        """Test collecting attribute access."""
        code = """
value = obj.attribute
result = module.function()
"""
        import ast

        tree = ast.parse(code)
        collector = UsageCollector()
        collector.visit(tree)

        assert "attribute" in collector.used_names
        assert "function" in collector.used_names


class TestDeadCodeDetector:
    """Test DeadCodeDetector."""

    @pytest.fixture
    def temp_project(self, tmp_path: Path) -> Path:
        """Create a temporary project structure."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        return project_dir

    def test_find_unused_function(self, temp_project: Path) -> None:
        """Test finding an unused function."""
        code = """
def used_function() -> Any:
    return 42

def unused_function() -> Any:
    return 0

result = used_function()
"""
        (temp_project / "module.py").write_text(code)

        detector = DeadCodeDetector(str(temp_project))
        dead_code = detector.find_unused_functions()

        assert len(dead_code) == 1
        assert dead_code[0].name == "unused_function"
        assert dead_code[0].type == "function"
        assert dead_code[0].confidence > 0.5

    def test_find_unused_class(self, temp_project: Path) -> None:
        """Test finding an unused class."""
        code = """
class UsedClass:
    pass

class UnusedClass:
    pass

obj = UsedClass()
"""
        (temp_project / "module.py").write_text(code)

        detector = DeadCodeDetector(str(temp_project))
        dead_code = detector.find_unused_classes()

        assert len(dead_code) == 1
        assert dead_code[0].name == "UnusedClass"
        assert dead_code[0].type == "class"

    def test_find_unused_import(self, temp_project: Path) -> None:
        """Test finding an unused import."""
        code = """
import os
import sys
from pathlib import Path

# Only use os
print(os.getcwd())
"""
        (temp_project / "module.py").write_text(code)

        detector = DeadCodeDetector(str(temp_project))
        dead_code = detector.find_unused_imports()

        unused_names = {dc.name for dc in dead_code}
        assert "sys" in unused_names
        assert "Path" in unused_names
        assert "os" not in unused_names  # os is used

    def test_find_unused_variable(self, temp_project: Path) -> None:
        """Test finding an unused module-level variable."""
        code = """
USED_CONSTANT = 42
UNUSED_CONSTANT = 0

def function() -> Any:
    return USED_CONSTANT
"""
        (temp_project / "module.py").write_text(code)

        detector = DeadCodeDetector(str(temp_project))
        dead_code = detector.find_unused_variables()

        assert len(dead_code) == 1
        assert dead_code[0].name == "UNUSED_CONSTANT"
        assert dead_code[0].type == "variable"

    def test_cross_file_usage(self, temp_project: Path) -> None:
        """Test that cross-file usage is detected."""
        # Module A defines a function
        module_a = """
def shared_function() -> Any:
    return 42

def unused_function() -> Any:
    return 0
"""
        (temp_project / "module_a.py").write_text(module_a)

        # Module B uses the function
        module_b = """
from module_a import shared_function

result = shared_function()
"""
        (temp_project / "module_b.py").write_text(module_b)

        detector = DeadCodeDetector(str(temp_project))
        dead_code = detector.find_unused_functions()

        # shared_function should not be marked as dead
        dead_names = {dc.name for dc in dead_code}
        assert "shared_function" not in dead_names
        assert "unused_function" in dead_names

    def test_analyze_all_types(self, temp_project: Path) -> None:
        """Test analyzing all types of dead code."""
        code = """
import unused_import
from pathlib import Path

UNUSED_VAR = 42

class UnusedClass:
    pass

def unused_function() -> None:
    pass

# Use Path to avoid marking it as dead
p = Path(".")
"""
        (temp_project / "module.py").write_text(code)

        detector = DeadCodeDetector(str(temp_project))
        dead_code = detector.analyze()

        types = {dc.type for dc in dead_code}
        assert "function" in types
        assert "class" in types
        assert "import" in types
        assert "variable" in types

    def test_get_stats(self, temp_project: Path) -> None:
        """Test getting dead code statistics."""
        code = """
import unused_import

UNUSED_VAR = 42

class UnusedClass:
    pass

def unused_function() -> None:
    pass
"""
        (temp_project / "module.py").write_text(code)

        detector = DeadCodeDetector(str(temp_project))
        stats = detector.get_stats()

        assert stats["total"] == 4
        assert stats["functions"] == 1
        assert stats["classes"] == 1
        assert stats["imports"] == 1
        assert stats["variables"] == 1

    def test_skip_special_methods(self, temp_project: Path) -> None:
        """Test that special methods are handled correctly."""
        code = """
class MyClass:
    def __init__(self) -> None:
        pass

    def __str__(self) -> Any:
        return "MyClass"

    def public_method(self) -> None:
        pass
"""
        (temp_project / "module.py").write_text(code)

        detector = DeadCodeDetector(str(temp_project))
        dead_code = detector.find_unused_functions()

        # __init__ and __str__ should not be marked as dead
        # (they might be used via instantiation or str())
        dead_names = {dc.name for dc in dead_code}
        assert "__init__" not in dead_names
        assert "__str__" not in dead_names

    def test_confidence_levels(self, temp_project: Path) -> None:
        """Test confidence level calculation."""
        code = """
def main() -> None:
    pass

def test_something() -> None:
    pass

def regular_function() -> None:
    pass
"""
        (temp_project / "module.py").write_text(code)

        detector = DeadCodeDetector(str(temp_project))
        dead_code = detector.find_unused_functions()

        # Find each function
        main_dead = next((dc for dc in dead_code if dc.name == "main"), None)
        test_dead = next((dc for dc in dead_code if dc.name == "test_something"), None)
        regular_dead = next((dc for dc in dead_code if dc.name == "regular_function"), None)

        # main should have lower confidence (common entry point)
        if main_dead:
            assert main_dead.confidence < 0.5

        # test_ functions should have lower confidence
        if test_dead:
            assert test_dead.confidence < 0.5

        # Regular functions should have higher confidence
        if regular_dead:
            assert regular_dead.confidence > 0.5

    def test_skip_pycache(self, temp_project: Path) -> None:
        """Test that __pycache__ directories are skipped."""
        # Create a __pycache__ directory with a .py file (shouldn't happen, but test it)
        pycache = temp_project / "__pycache__"
        pycache.mkdir()
        (pycache / "cached.py").write_text("def cached(): pass")

        # Create a normal file
        (temp_project / "normal.py").write_text("def normal(): pass")

        detector = DeadCodeDetector(str(temp_project))
        python_files = detector._find_python_files()

        # Should only find normal.py
        assert len(python_files) == 1
        assert python_files[0].name == "normal.py"

    def test_handle_syntax_errors(self, temp_project: Path) -> None:
        """Test that syntax errors are handled gracefully."""
        invalid_code = """
def broken function():
    this is not valid python
"""
        (temp_project / "broken.py").write_text(invalid_code)

        valid_code = """
def unused_function() -> None:
    pass
"""
        (temp_project / "valid.py").write_text(valid_code)

        detector = DeadCodeDetector(str(temp_project))
        dead_code = detector.analyze()

        # Should still find dead code in valid files
        assert len(dead_code) > 0

    def test_multiple_files(self, temp_project: Path) -> None:
        """Test analysis across multiple files."""
        # File 1
        (temp_project / "file1.py").write_text(
            """
def func1() -> None:
    pass

def func2() -> None:
    pass
"""
        )

        # File 2
        (temp_project / "file2.py").write_text(
            """
from file1 import func1

result = func1()
"""
        )

        detector = DeadCodeDetector(str(temp_project))
        dead_code = detector.find_unused_functions()

        # func1 is used in file2, func2 is not used
        dead_names = {dc.name for dc in dead_code}
        assert "func2" in dead_names
        assert "func1" not in dead_names

    def test_method_usage_via_class(self, temp_project: Path) -> None:
        """Test that methods called via instances are detected."""
        code = """
class MyClass:
    def used_method(self) -> None:
        pass

    def unused_method(self) -> None:
        pass

obj = MyClass()
obj.used_method()
"""
        (temp_project / "module.py").write_text(code)

        detector = DeadCodeDetector(str(temp_project))
        dead_code = detector.find_unused_functions()

        dead_names = {dc.name for dc in dead_code}
        assert "used_method" not in dead_names
        assert "unused_method" in dead_names


@pytest.fixture
def sample_project(tmp_path: Path) -> Path:
    """Create a sample project with various dead code patterns."""
    project = tmp_path / "sample_project"
    project.mkdir()

    # Module with unused code
    (project / "main.py").write_text(
        """
import os
import sys
import json
from typing import List, Dict, Any

USED_CONSTANT = 42
UNUSED_CONSTANT = "dead"

class UsedClass:
    def __init__(self) -> None:
        self.value = USED_CONSTANT

    def used_method(self) -> Any:
        return self.value

    def unused_method(self) -> Any:
        return "never called"

class UnusedClass:
    pass

def used_function() -> Any:
    obj = UsedClass()
    return obj.used_method()

def unused_function() -> Any:
    return "never called"

def main() -> None:
    result = used_function()
    data = json.dumps({"result": result})
    print(data)

if __name__ == "__main__":
    main()
"""
    )

    # Helper module
    (project / "helpers.py").write_text(
        """
def used_helper() -> Any:
    return "helper"

def unused_helper() -> Any:
    return "dead"
"""
    )

    # Module that uses helpers
    (project / "user.py").write_text(
        """
from helpers import used_helper

result = used_helper()
"""
    )

    return project


def test_sample_project_analysis(sample_project: Path) -> None:
    """Test analyzing a realistic project."""
    detector = DeadCodeDetector(str(sample_project))
    dead_code = detector.analyze()

    # Check that we found dead code
    assert len(dead_code) > 0

    # Get dead code by type
    dead_imports = [dc for dc in dead_code if dc.type == "import"]
    dead_functions = [dc for dc in dead_code if dc.type == "function"]
    dead_classes = [dc for dc in dead_code if dc.type == "class"]
    dead_variables = [dc for dc in dead_code if dc.type == "variable"]

    # Verify specific dead code items
    dead_import_names = {dc.name for dc in dead_imports}
    assert "sys" in dead_import_names  # Imported but never used
    assert "List" in dead_import_names or "Dict" in dead_import_names

    dead_function_names = {dc.name for dc in dead_functions}
    assert "unused_function" in dead_function_names
    assert "unused_helper" in dead_function_names
    assert "unused_method" in dead_function_names

    dead_class_names = {dc.name for dc in dead_classes}
    assert "UnusedClass" in dead_class_names

    dead_variable_names = {dc.name for dc in dead_variables}
    assert "UNUSED_CONSTANT" in dead_variable_names

    # Verify that used code is NOT marked as dead
    assert "json" not in dead_import_names  # Used for json.dumps
    assert "used_function" not in dead_function_names
    assert "UsedClass" not in dead_class_names
    assert "USED_CONSTANT" not in dead_variable_names

    # os is actually imported but never used, so it SHOULD be in dead imports
    assert "os" in dead_import_names  # Imported but never used
