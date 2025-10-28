"""
Tests for report aggregator.
"""

import tempfile
from pathlib import Path

import pytest

from qontinui_devtools.reporting import ReportAggregator


class TestReportAggregator:
    """Tests for ReportAggregator."""

    def test_initialization(self):
        """Test aggregator initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            aggregator = ReportAggregator(tmpdir, verbose=False)
            assert aggregator.project_path == Path(tmpdir)
            assert aggregator.verbose is False
            assert aggregator.results == {}

    def test_initialization_invalid_path(self):
        """Test initialization with invalid path."""
        with pytest.raises(ValueError, match="does not exist"):
            ReportAggregator("/nonexistent/path")

    def test_run_all_analyses_empty_project(self):
        """Test running analyses on an empty project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            aggregator = ReportAggregator(tmpdir, verbose=False)
            report_data = aggregator.run_all_analyses()

            assert report_data.project_name == Path(tmpdir).name
            assert len(report_data.sections) > 0
            assert "files_analyzed" in report_data.summary_metrics

    def test_run_all_analyses_with_python_files(self):
        """Test running analyses on a project with Python files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some Python files (NOT test files, as those are excluded)
            file1 = Path(tmpdir) / "module1.py"
            file1.write_text(
                """
def hello():
    pass

class MyClass:
    def method1(self):
        pass
"""
            )

            file2 = Path(tmpdir) / "module2.py"
            file2.write_text(
                """
import os

def world():
    pass
"""
            )

            aggregator = ReportAggregator(tmpdir, verbose=False)
            report_data = aggregator.run_all_analyses()

            # Should have analyzed files (quality checks exclude files with "test" in name)
            assert report_data.summary_metrics.get("files_analyzed", 0) >= 2

            # Should have sections
            assert len(report_data.sections) > 0

            # Check for specific sections
            section_ids = [s.id for s in report_data.sections]
            assert "imports" in section_ids
            assert "architecture" in section_ids
            assert "quality" in section_ids
            assert "concurrency" in section_ids
            assert "recommendations" in section_ids

    def test_count_critical_issues(self):
        """Test counting critical issues."""
        with tempfile.TemporaryDirectory() as tmpdir:
            aggregator = ReportAggregator(tmpdir, verbose=False)

            # Set up test results
            aggregator.results = {
                "imports": {"circular_dependencies": 2},
                "concurrency": {"race_conditions": 1},
                "architecture": {"god_classes": 5},
            }

            critical_count = aggregator._count_critical_issues()

            # Should count circular deps (2) + race conditions (1) + excess god classes (2)
            assert critical_count >= 3

    def test_create_import_section_no_issues(self):
        """Test creating import section with no issues."""
        with tempfile.TemporaryDirectory() as tmpdir:
            aggregator = ReportAggregator(tmpdir, verbose=False)
            aggregator.results = {"imports": {"circular_dependencies": 0, "cycles": []}}

            section = aggregator._create_import_section()

            assert section.id == "imports"
            assert section.severity == "success"
            assert "No circular dependencies" in section.content

    def test_create_import_section_with_issues(self):
        """Test creating import section with circular dependencies."""
        with tempfile.TemporaryDirectory() as tmpdir:
            aggregator = ReportAggregator(tmpdir, verbose=False)
            aggregator.results = {
                "imports": {
                    "circular_dependencies": 3,
                    "cycles": [
                        ["module_a", "module_b", "module_a"],
                        ["module_c", "module_d", "module_c"],
                        ["module_e", "module_f", "module_e"],
                    ],
                }
            }

            section = aggregator._create_import_section()

            assert section.id == "imports"
            assert section.severity == "error"
            assert "3" in section.content

    def test_create_architecture_section_clean(self):
        """Test creating architecture section with no issues."""
        with tempfile.TemporaryDirectory() as tmpdir:
            aggregator = ReportAggregator(tmpdir, verbose=False)
            aggregator.results = {
                "architecture": {
                    "god_classes": 0,
                    "srp_violations": 0,
                    "god_class_details": [],
                }
            }

            section = aggregator._create_architecture_section()

            assert section.id == "architecture"
            assert section.severity == "success"
            assert "clean" in section.content.lower()

    def test_create_architecture_section_with_issues(self):
        """Test creating architecture section with god classes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            aggregator = ReportAggregator(tmpdir, verbose=False)

            # Mock god class details
            class MockGodClass:
                def __init__(self, name: str, method_count: int):
                    self.class_name = name
                    self.method_count = method_count

            aggregator.results = {
                "architecture": {
                    "god_classes": 2,
                    "srp_violations": 5,
                    "god_class_details": [
                        MockGodClass("BigClass", 30),
                        MockGodClass("HugeClass", 50),
                    ],
                }
            }

            section = aggregator._create_architecture_section()

            assert section.id == "architecture"
            assert section.severity == "warning"
            assert "2" in section.content

    def test_create_quality_section(self):
        """Test creating code quality section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            aggregator = ReportAggregator(tmpdir, verbose=False)
            aggregator.results = {
                "quality": {
                    "total_files": 50,
                    "total_lines": 5000,
                    "issues": [
                        {
                            "file": "/test/file1.py",
                            "issue": "Wildcard import",
                            "severity": "warning",
                        },
                        {
                            "file": "/test/file2.py",
                            "issue": "TODO comment",
                            "severity": "info",
                        },
                    ],
                }
            }

            section = aggregator._create_quality_section()

            assert section.id == "quality"
            assert "50" in section.content
            assert "5,000" in section.content or "5000" in section.content
            assert section.metrics["total_files"] == 50

    def test_create_concurrency_section_no_issues(self):
        """Test creating concurrency section with no race conditions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            aggregator = ReportAggregator(tmpdir, verbose=False)
            aggregator.results = {
                "concurrency": {"race_conditions": 0, "race_details": []}
            }

            section = aggregator._create_concurrency_section()

            assert section.id == "concurrency"
            assert section.severity == "success"
            assert "No race conditions" in section.content

    def test_create_concurrency_section_with_issues(self):
        """Test creating concurrency section with race conditions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            aggregator = ReportAggregator(tmpdir, verbose=False)

            # Mock race condition
            class MockRace:
                def __init__(self, desc: str):
                    self.description = desc

            aggregator.results = {
                "concurrency": {
                    "race_conditions": 3,
                    "race_details": [
                        MockRace("Shared variable access without lock"),
                        MockRace("Unsynchronized dictionary access"),
                        MockRace("Race condition in counter"),
                    ],
                }
            }

            section = aggregator._create_concurrency_section()

            assert section.id == "concurrency"
            assert section.severity == "error"
            assert "3" in section.content

    def test_create_recommendations_section_no_issues(self):
        """Test recommendations with no issues."""
        with tempfile.TemporaryDirectory() as tmpdir:
            aggregator = ReportAggregator(tmpdir, verbose=False)
            aggregator.results = {
                "imports": {"circular_dependencies": 0},
                "architecture": {"god_classes": 0, "srp_violations": 0},
                "concurrency": {"race_conditions": 0},
            }

            section = aggregator._create_recommendations_section()

            assert section.id == "recommendations"
            assert section.severity == "success"
            assert "Excellent" in section.content or "good work" in section.content.lower()

    def test_create_recommendations_section_with_issues(self):
        """Test recommendations with issues."""
        with tempfile.TemporaryDirectory() as tmpdir:
            aggregator = ReportAggregator(tmpdir, verbose=False)
            aggregator.results = {
                "imports": {"circular_dependencies": 2},
                "architecture": {"god_classes": 3, "srp_violations": 5},
                "concurrency": {"race_conditions": 1},
            }

            section = aggregator._create_recommendations_section()

            assert section.id == "recommendations"
            assert section.severity in ["warning", "error"]
            assert "circular dependencies" in section.content.lower()
            assert "god class" in section.content.lower()
            assert "synchronization" in section.content.lower()


class TestReportAggregatorIntegration:
    """Integration tests for report aggregator."""

    def test_full_analysis_workflow(self):
        """Test complete analysis workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a realistic project structure
            src_dir = Path(tmpdir) / "src"
            src_dir.mkdir()

            # Create main module
            (src_dir / "main.py").write_text(
                """
import helper

def main():
    helper.do_something()

if __name__ == "__main__":
    main()
"""
            )

            # Create helper module
            (src_dir / "helper.py").write_text(
                """
import threading

counter = 0
lock = threading.Lock()

def do_something():
    global counter
    with lock:
        counter += 1
"""
            )

            # Create a large class
            (src_dir / "big_class.py").write_text(
                """
class BigClass:
    def method1(self): pass
    def method2(self): pass
    def method3(self): pass
    def method4(self): pass
    def method5(self): pass
    def method6(self): pass
    def method7(self): pass
    def method8(self): pass
    def method9(self): pass
    def method10(self): pass
"""
            )

            # Run aggregator
            aggregator = ReportAggregator(str(src_dir), verbose=False)
            report_data = aggregator.run_all_analyses()

            # Verify report data
            assert report_data.project_name == "src"
            assert len(report_data.sections) >= 5

            # Verify summary metrics
            metrics = report_data.summary_metrics
            assert metrics["files_analyzed"] >= 3
            assert metrics["total_lines"] > 0

            # Verify sections exist
            section_ids = [s.id for s in report_data.sections]
            assert "imports" in section_ids
            assert "architecture" in section_ids
            assert "quality" in section_ids
            assert "concurrency" in section_ids
            assert "recommendations" in section_ids

            # Verify each section has valid content
            for section in report_data.sections:
                assert len(section.content) > 0
                assert section.severity in ["success", "warning", "error", "info"]
                assert isinstance(section.metrics, dict)
