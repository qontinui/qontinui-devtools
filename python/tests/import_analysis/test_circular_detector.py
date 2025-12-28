"""Tests for the circular dependency detector."""

from pathlib import Path

import pytest
from qontinui_devtools.import_analysis import CircularDependencyDetector
from qontinui_devtools.import_analysis.ast_utils import (extract_imports,
                                                         find_python_files,
                                                         module_path_from_file)


class TestImportExtraction:
    """Tests for import extraction from Python files."""

    def test_extract_imports_from_simple_file(self, tmp_path: Path) -> None:
        """Test extracting imports from a simple Python file."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text(
            """
import os
import sys
from pathlib import Path
from typing import List, Dict
"""
        )

        imports = extract_imports(str(test_file))

        assert len(imports) == 4
        assert any(imp.module == "os" and not imp.is_from_import for imp in imports)
        assert any(imp.module == "sys" and not imp.is_from_import for imp in imports)
        assert any(imp.module == "pathlib" and imp.is_from_import for imp in imports)
        assert any(imp.module == "typing" and imp.is_from_import for imp in imports)

    def test_extract_from_import_with_multiple_names(self, tmp_path: Path) -> None:
        """Test extracting 'from X import Y, Z' statements."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text(
            """
from collections import Counter, defaultdict, OrderedDict
"""
        )

        imports = extract_imports(str(test_file))

        assert len(imports) == 1
        assert imports[0].module == "collections"
        assert imports[0].is_from_import
        assert len(imports[0].imported_names) == 3
        assert "Counter" in imports[0].imported_names
        assert "defaultdict" in imports[0].imported_names
        assert "OrderedDict" in imports[0].imported_names

    def test_extract_wildcard_import(self, tmp_path: Path) -> None:
        """Test extracting 'from X import *' statements."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text(
            """
from os.path import *
"""
        )

        imports = extract_imports(str(test_file))

        assert len(imports) == 1
        assert imports[0].module == "os.path"
        assert imports[0].is_from_import
        assert imports[0].imported_names == ["*"]

    def test_extract_imports_with_line_numbers(self, tmp_path: Path) -> None:
        """Test that line numbers are correctly recorded."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text(
            """import os

def foo() -> None:
    pass

from pathlib import Path
"""
        )

        imports = extract_imports(str(test_file))

        assert len(imports) == 2
        os_import = next(imp for imp in imports if imp.module == "os")
        path_import = next(imp for imp in imports if imp.module == "pathlib")

        assert os_import.line_number == 1
        assert path_import.line_number == 6

    def test_module_path_from_file(self, tmp_path: Path) -> None:
        """Test converting file paths to module paths."""
        root = tmp_path / "myproject"
        root.mkdir()

        # Test simple module
        file_path = root / "mymodule.py"
        module_path = module_path_from_file(str(file_path), str(root))
        assert module_path == "mymodule"

        # Test nested module
        subdir = root / "package" / "subpackage"
        subdir.mkdir(parents=True)
        file_path = subdir / "module.py"
        module_path = module_path_from_file(str(file_path), str(root))
        assert module_path == "package.subpackage.module"

        # Test __init__.py
        file_path = subdir / "__init__.py"
        module_path = module_path_from_file(str(file_path), str(root))
        assert module_path == "package.subpackage"

    def test_find_python_files(self, tmp_path: Path) -> None:
        """Test finding Python files in a directory tree."""
        # Create structure
        (tmp_path / "module1.py").write_text("# Module 1")
        (tmp_path / "module2.py").write_text("# Module 2")

        subdir = tmp_path / "package"
        subdir.mkdir()
        (subdir / "__init__.py").write_text("")
        (subdir / "submodule.py").write_text("# Submodule")

        # Should skip __pycache__
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        (pycache / "module1.pyc").write_text("")

        files = find_python_files(str(tmp_path))

        assert len(files) == 4
        assert any("module1.py" in f for f in files)
        assert any("module2.py" in f for f in files)
        assert any("__init__.py" in f for f in files)
        assert any("submodule.py" in f for f in files)
        assert not any("__pycache__" in f for f in files)


class TestCircularDetector:
    """Tests for the circular dependency detector."""

    def test_detect_no_circular_deps(self) -> None:
        """Test detection when there are no circular dependencies."""
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "no_circular"

        detector = CircularDependencyDetector(str(fixtures_path), verbose=False)
        cycles = detector.analyze()

        assert len(cycles) == 0

    def test_detect_circular_deps(self) -> None:
        """Test detection of circular dependencies."""
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "circular"

        detector = CircularDependencyDetector(str(fixtures_path), verbose=False)
        cycles = detector.analyze()

        # Should detect the a->b->c->a cycle
        assert len(cycles) > 0

        # Verify the cycle contains our modules
        cycle_modules = set()
        for cycle in cycles:
            cycle_modules.update(cycle.cycle)

        # The cycle should involve module_a, module_b, and module_c
        assert any("module_a" in str(m) for m in cycle_modules)
        assert any("module_b" in str(m) for m in cycle_modules)
        assert any("module_c" in str(m) for m in cycle_modules)

    def test_cycle_severity(self) -> None:
        """Test that cycle severity is correctly determined."""
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "circular"

        detector = CircularDependencyDetector(str(fixtures_path), verbose=False)
        cycles = detector.analyze()

        # 3-module cycle should be medium severity
        assert any(cycle.severity == "medium" for cycle in cycles)

    def test_fix_suggestions_generated(self) -> None:
        """Test that fix suggestions are generated for cycles."""
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "circular"

        detector = CircularDependencyDetector(str(fixtures_path), verbose=False)
        cycles = detector.analyze()

        for cycle in cycles:
            assert cycle.suggestion is not None
            assert cycle.suggestion.fix_type in ["lazy_import", "type_checking", "restructure"]
            assert cycle.suggestion.description
            assert len(cycle.suggestion.affected_files) > 0

    def test_import_chain_extracted(self) -> None:
        """Test that import chains are correctly extracted."""
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "circular"

        detector = CircularDependencyDetector(str(fixtures_path), verbose=False)
        cycles = detector.analyze()

        for cycle in cycles:
            # Should have import statements
            assert len(cycle.import_chain) > 0

            # Each import should have valid information
            for imp in cycle.import_chain:
                assert imp.file_path
                assert imp.line_number > 0
                assert imp.module

    def test_statistics(self) -> None:
        """Test that statistics are correctly computed."""
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "circular"

        detector = CircularDependencyDetector(str(fixtures_path), verbose=False)
        detector.analyze()

        stats = detector.get_statistics()

        assert stats["total_files"] > 0
        assert stats["total_imports"] > 0
        assert stats["total_modules"] > 0
        assert stats["total_dependencies"] > 0
        assert stats["cycles_found"] > 0

    def test_generate_text_report(self) -> None:
        """Test generating a text report."""
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "circular"

        detector = CircularDependencyDetector(str(fixtures_path), verbose=False)
        cycles = detector.analyze()

        report = detector.generate_report(cycles)

        assert "CIRCULAR DEPENDENCY REPORT" in report
        assert "module_a" in report or "module_b" in report or "module_c" in report
        assert "Fix type:" in report

    def test_empty_directory(self, tmp_path: Path) -> None:
        """Test analyzing an empty directory."""
        detector = CircularDependencyDetector(str(tmp_path), verbose=False)
        cycles = detector.analyze()

        assert len(cycles) == 0

    def test_invalid_python_syntax(self, tmp_path: Path) -> None:
        """Test handling files with invalid Python syntax."""
        bad_file = tmp_path / "bad.py"
        bad_file.write_text("def broken(\n")  # Invalid syntax

        good_file = tmp_path / "good.py"
        good_file.write_text("import os\n")

        # Should handle the error gracefully and process the good file
        detector = CircularDependencyDetector(str(tmp_path), verbose=False)
        cycles = detector.analyze()

        # Should not crash
        assert isinstance(cycles, list)


class TestFixSuggester:
    """Tests for fix suggestion generation."""

    def test_type_checking_suggestion(self) -> None:
        """Test that TYPE_CHECKING suggestions are generated appropriately."""
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "circular"

        detector = CircularDependencyDetector(str(fixtures_path), verbose=False)
        cycles = detector.analyze()

        # Check that suggestions include code examples
        for cycle in cycles:
            if cycle.suggestion.fix_type == "type_checking":
                code_example = cycle.suggestion.code_example or ""
                assert "TYPE_CHECKING" in code_example
                assert "from typing import TYPE_CHECKING" in code_example

    def test_lazy_import_suggestion(self) -> None:
        """Test that lazy import suggestions include proper examples."""
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "circular"

        detector = CircularDependencyDetector(str(fixtures_path), verbose=False)
        cycles = detector.analyze()

        # Check that suggestions include function-level import examples
        for cycle in cycles:
            if cycle.suggestion.fix_type == "lazy_import":
                assert cycle.suggestion.code_example is not None
                assert (
                    "def " in cycle.suggestion.code_example
                    or "function" in cycle.suggestion.description.lower()
                )

    def test_restructure_suggestion(self) -> None:
        """Test that restructure suggestions provide guidance."""
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "circular"

        detector = CircularDependencyDetector(str(fixtures_path), verbose=False)
        cycles = detector.analyze()

        # Check that restructure suggestions provide actionable advice
        for cycle in cycles:
            if cycle.suggestion.fix_type == "restructure":
                assert cycle.suggestion.description
                assert len(cycle.suggestion.description) > 50  # Should be detailed


class TestIntegration:
    """Integration tests for the full analysis workflow."""

    def test_full_workflow_with_circular_deps(self) -> None:
        """Test the complete workflow from scan to report."""
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "circular"

        # Create detector
        detector = CircularDependencyDetector(str(fixtures_path), verbose=False)

        # Run analysis
        cycles = detector.analyze()

        # Verify results
        assert len(cycles) > 0

        # Generate reports
        text_report = detector.generate_report(cycles)
        assert text_report
        assert len(text_report) > 100

        # Check statistics
        stats = detector.get_statistics()
        assert stats["cycles_found"] == len(cycles)

    def test_full_workflow_without_circular_deps(self) -> None:
        """Test the complete workflow with clean code."""
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "no_circular"

        detector = CircularDependencyDetector(str(fixtures_path), verbose=False)
        cycles = detector.analyze()

        assert len(cycles) == 0

        report = detector.generate_report(cycles)
        assert "No circular dependencies found" in report


@pytest.mark.unit
class TestModulePathConversion:
    """Unit tests for module path conversion utilities."""

    def test_module_path_with_nested_packages(self, tmp_path: Path) -> None:
        """Test module path conversion with deeply nested packages."""
        root = tmp_path / "src"
        root.mkdir()

        file_path = root / "a" / "b" / "c" / "module.py"
        file_path.parent.mkdir(parents=True)

        result = module_path_from_file(str(file_path), str(root))
        assert result == "a.b.c.module"

    def test_module_path_with_special_characters(self, tmp_path: Path) -> None:
        """Test handling of special characters in paths."""
        root = tmp_path
        file_path = root / "my_module.py"

        result = module_path_from_file(str(file_path), str(root))
        assert result == "my_module"
