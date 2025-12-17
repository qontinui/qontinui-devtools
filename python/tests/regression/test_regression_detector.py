"""Comprehensive tests for regression detection functionality."""

import json
from pathlib import Path

import pytest
from qontinui_devtools.regression import (
    APISnapshot,
    ChangeType,
    ClassSignature,
    FunctionSignature,
    PerformanceMetric,
    RegressionDetector,
    RegressionIssue,
    RegressionReport,
    RiskLevel,
    SeverityLevel,
)


class TestFunctionSignature:
    """Test FunctionSignature model."""

    def test_function_signature_equality(self) -> None:
        """Test function signature equality comparison."""
        sig1 = FunctionSignature(
            name="test_func",
            parameters=["x: int", "y: str"],
            return_type="bool",
            module_path="test.module",
        )
        sig2 = FunctionSignature(
            name="test_func",
            parameters=["x: int", "y: str"],
            return_type="bool",
            module_path="test.module",
        )
        assert sig1 == sig2

    def test_function_signature_inequality(self) -> None:
        """Test function signature inequality."""
        sig1 = FunctionSignature(
            name="test_func",
            parameters=["x: int"],
            return_type="bool",
            module_path="test.module",
        )
        sig2 = FunctionSignature(
            name="test_func",
            parameters=["x: int", "y: str"],
            return_type="bool",
            module_path="test.module",
        )
        assert sig1 != sig2

    def test_function_signature_hash(self) -> None:
        """Test function signature hashing."""
        sig1 = FunctionSignature(
            name="test_func",
            parameters=["x: int"],
            return_type="bool",
            module_path="test.module",
        )
        sig2 = FunctionSignature(
            name="test_func",
            parameters=["x: int"],
            return_type="bool",
            module_path="test.module",
        )
        assert hash(sig1) == hash(sig2)

    def test_function_signature_to_dict(self) -> None:
        """Test function signature serialization."""
        sig = FunctionSignature(
            name="test_func",
            parameters=["x: int"],
            return_type="bool",
            module_path="test.module",
            is_async=True,
            decorators=["@property"],
        )
        data = sig.to_dict()
        assert data["name"] == "test_func"
        assert data["is_async"] is True
        assert "@property" in data["decorators"]

    def test_function_signature_from_dict(self) -> None:
        """Test function signature deserialization."""
        data = {
            "name": "test_func",
            "parameters": ["x: int"],
            "return_type": "bool",
            "module_path": "test.module",
            "is_async": True,
        }
        sig = FunctionSignature.from_dict(data)
        assert sig.name == "test_func"
        assert sig.is_async is True


class TestClassSignature:
    """Test ClassSignature model."""

    def test_class_signature_to_dict(self) -> None:
        """Test class signature serialization."""
        method = FunctionSignature(
            name="method1", parameters=[], return_type=None, module_path="test.module"
        )
        cls_sig = ClassSignature(
            name="TestClass",
            module_path="test.module",
            methods=[method],
            base_classes=["BaseClass"],
        )
        data = cls_sig.to_dict()
        assert data["name"] == "TestClass"
        assert len(data["methods"]) == 1
        assert "BaseClass" in data["base_classes"]

    def test_class_signature_from_dict(self) -> None:
        """Test class signature deserialization."""
        data = {
            "name": "TestClass",
            "module_path": "test.module",
            "methods": [
                {
                    "name": "method1",
                    "parameters": [],
                    "return_type": None,
                    "module_path": "test.module",
                }
            ],
            "base_classes": ["BaseClass"],
        }
        cls_sig = ClassSignature.from_dict(data)
        assert cls_sig.name == "TestClass"
        assert len(cls_sig.methods) == 1


class TestRegressionIssue:
    """Test RegressionIssue model."""

    def test_regression_issue_creation(self) -> None:
        """Test creating regression issue."""
        issue = RegressionIssue(
            change_type=ChangeType.BREAKING,
            risk_level=RiskLevel.CRITICAL,
            description="Function removed",
            old_signature=None,
            new_signature=None,
            impact_description="Calls will fail",
            migration_guide="Replace with alternative",
        )
        assert issue.change_type == ChangeType.BREAKING
        assert issue.risk_level == RiskLevel.CRITICAL

    def test_regression_issue_serialization(self) -> None:
        """Test regression issue serialization."""
        old_sig = FunctionSignature(
            name="old_func", parameters=[], return_type=None, module_path="test"
        )
        issue = RegressionIssue(
            change_type=ChangeType.BEHAVIORAL,
            risk_level=RiskLevel.MEDIUM,
            description="Signature changed",
            old_signature=old_sig,
            new_signature=None,
            impact_description="May break",
            migration_guide="Update calls",
            severity=SeverityLevel.MODERATE,
        )
        data = issue.to_dict()
        assert data["change_type"] == "behavioral"
        assert data["severity"] == "moderate"

    def test_regression_issue_deserialization(self) -> None:
        """Test regression issue deserialization."""
        data = {
            "change_type": "breaking",
            "risk_level": "critical",
            "description": "Test",
            "old_signature": None,
            "new_signature": None,
            "impact_description": "Impact",
            "migration_guide": "Guide",
            "severity": "severe",
        }
        issue = RegressionIssue.from_dict(data)
        assert issue.change_type == ChangeType.BREAKING
        assert issue.severity == SeverityLevel.SEVERE


class TestRegressionReport:
    """Test RegressionReport model."""

    def test_regression_report_creation(self) -> None:
        """Test creating regression report."""
        report = RegressionReport(
            baseline_version="v1.0",
            current_version="v2.0",
            issues=[],
            breaking_count=0,
            behavioral_count=0,
            performance_count=0,
            dependency_count=0,
            total_functions_compared=10,
            total_classes_compared=5,
        )
        assert report.baseline_version == "v1.0"
        assert report.total_functions_compared == 10

    def test_regression_report_has_breaking_changes(self) -> None:
        """Test checking for breaking changes."""
        report = RegressionReport(
            baseline_version="v1.0",
            current_version="v2.0",
            issues=[],
            breaking_count=2,
            behavioral_count=0,
            performance_count=0,
            dependency_count=0,
            total_functions_compared=10,
            total_classes_compared=0,
        )
        assert report.has_breaking_changes()

    def test_regression_report_get_critical_issues(self) -> None:
        """Test filtering critical issues."""
        issue1 = RegressionIssue(
            change_type=ChangeType.BREAKING,
            risk_level=RiskLevel.CRITICAL,
            description="Critical issue",
            old_signature=None,
            new_signature=None,
            impact_description="High impact",
            migration_guide="Fix it",
        )
        issue2 = RegressionIssue(
            change_type=ChangeType.BEHAVIORAL,
            risk_level=RiskLevel.LOW,
            description="Minor issue",
            old_signature=None,
            new_signature=None,
            impact_description="Low impact",
            migration_guide="Optional",
        )
        report = RegressionReport(
            baseline_version="v1.0",
            current_version="v2.0",
            issues=[issue1, issue2],
            breaking_count=1,
            behavioral_count=1,
            performance_count=0,
            dependency_count=0,
            total_functions_compared=10,
            total_classes_compared=0,
        )
        critical = report.get_critical_issues()
        assert len(critical) == 1
        assert critical[0].risk_level == RiskLevel.CRITICAL

    def test_regression_report_severity_distribution(self) -> None:
        """Test severity distribution calculation."""
        issues = [
            RegressionIssue(
                change_type=ChangeType.BREAKING,
                risk_level=RiskLevel.CRITICAL,
                description="Issue 1",
                old_signature=None,
                new_signature=None,
                impact_description="Impact",
                migration_guide="Guide",
                severity=SeverityLevel.SEVERE,
            ),
            RegressionIssue(
                change_type=ChangeType.BEHAVIORAL,
                risk_level=RiskLevel.LOW,
                description="Issue 2",
                old_signature=None,
                new_signature=None,
                impact_description="Impact",
                migration_guide="Guide",
                severity=SeverityLevel.MINOR,
            ),
        ]
        report = RegressionReport(
            baseline_version="v1.0",
            current_version="v2.0",
            issues=issues,
            breaking_count=1,
            behavioral_count=1,
            performance_count=0,
            dependency_count=0,
            total_functions_compared=10,
            total_classes_compared=0,
        )
        distribution = report.get_severity_distribution()
        assert distribution["severe"] == 1
        assert distribution["minor"] == 1


class TestAPISnapshot:
    """Test APISnapshot functionality."""

    def test_create_snapshot(self, tmp_path: Path) -> None:
        """Test creating API snapshot from source."""
        # Create test Python file
        test_file = tmp_path / "test_module.py"
        test_file.write_text(
            """
def public_function(x: int, y: str) -> bool:
    '''Public function.'''
    return True

def _private_function():
    pass

class PublicClass:
    '''Public class.'''
    def method1(self) -> None:
        pass
"""
        )

        snapshot = APISnapshot()
        snapshot.create_snapshot(tmp_path, "v1.0")

        assert len(snapshot.functions) > 0
        assert len(snapshot.classes) > 0
        assert any("public_function" in key for key in snapshot.functions)
        assert any("PublicClass" in key for key in snapshot.classes)

    def test_snapshot_save_and_load(self, tmp_path: Path) -> None:
        """Test saving and loading snapshots."""
        # Create snapshot
        snapshot1 = APISnapshot()
        snapshot1.functions["test.func1"] = FunctionSignature(
            name="func1", parameters=[], return_type=None, module_path="test"
        )
        snapshot1.metadata = {"version": "v1.0"}

        # Save
        snapshot_file = tmp_path / "snapshot.json"
        snapshot1.save_snapshot(snapshot_file)
        assert snapshot_file.exists()

        # Load
        snapshot2 = APISnapshot()
        snapshot2.load_snapshot(snapshot_file)

        assert "test.func1" in snapshot2.functions
        assert snapshot2.metadata["version"] == "v1.0"

    def test_snapshot_comparison(self) -> None:
        """Test comparing two snapshots."""
        # Create baseline snapshot
        baseline = APISnapshot()
        baseline.functions["test.func1"] = FunctionSignature(
            name="func1", parameters=["x: int"], return_type=None, module_path="test"
        )
        baseline.functions["test.func2"] = FunctionSignature(
            name="func2", parameters=[], return_type=None, module_path="test"
        )

        # Create current snapshot
        current = APISnapshot()
        current.functions["test.func1"] = FunctionSignature(
            name="func1", parameters=["x: int", "y: str"], return_type=None, module_path="test"
        )
        current.functions["test.func3"] = FunctionSignature(
            name="func3", parameters=[], return_type=None, module_path="test"
        )

        added, removed, modified, unchanged = current.compare_snapshots(baseline)

        assert "test.func3" in added
        assert "test.func2" in removed
        assert "test.func1" in modified

    def test_snapshot_filter_by_module(self) -> None:
        """Test filtering snapshot by module prefix."""
        snapshot = APISnapshot()
        snapshot.functions["module1.func1"] = FunctionSignature(
            name="func1", parameters=[], return_type=None, module_path="module1"
        )
        snapshot.functions["module2.func2"] = FunctionSignature(
            name="func2", parameters=[], return_type=None, module_path="module2"
        )

        filtered = snapshot.filter_by_module("module1")
        assert len(filtered.functions) == 1
        assert "module1.func1" in filtered.functions


class TestRegressionDetector:
    """Test RegressionDetector functionality."""

    def test_detector_initialization(self, tmp_path: Path) -> None:
        """Test detector initialization."""
        detector = RegressionDetector(snapshot_dir=tmp_path)
        assert detector.snapshot_dir == tmp_path
        assert detector.snapshot_dir.exists()

    def test_create_snapshot(self, tmp_path: Path) -> None:
        """Test creating snapshot with detector."""
        # Create test source
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "test.py").write_text("def test_func(): pass")

        detector = RegressionDetector(snapshot_dir=tmp_path / "snapshots")
        snapshot = detector.create_snapshot(source_dir, "v1.0", save=True)

        assert len(snapshot.functions) > 0
        assert (tmp_path / "snapshots" / "snapshot_v1.0.json").exists()

    def test_detect_breaking_changes_removed_function(self, tmp_path: Path) -> None:
        """Test detecting removed function as breaking change."""
        # Create baseline
        baseline_dir = tmp_path / "baseline"
        baseline_dir.mkdir()
        (baseline_dir / "test.py").write_text(
            """
def function_to_remove():
    pass

def function_to_keep():
    pass
"""
        )

        # Create current version
        current_dir = tmp_path / "current"
        current_dir.mkdir()
        (current_dir / "test.py").write_text(
            """
def function_to_keep():
    pass
"""
        )

        detector = RegressionDetector(snapshot_dir=tmp_path / "snapshots")
        baseline_snapshot = detector.create_snapshot(baseline_dir, "v1.0", save=False)
        report = detector.detect_regressions(current_dir, baseline_snapshot, "v2.0")

        assert report.breaking_count > 0
        breaking_issues = [i for i in report.issues if i.change_type == ChangeType.BREAKING]
        assert len(breaking_issues) > 0
        assert any("removed" in i.description.lower() for i in breaking_issues)

    def test_detect_parameter_change(self, tmp_path: Path) -> None:
        """Test detecting parameter changes."""
        # Create baseline
        baseline_dir = tmp_path / "baseline"
        baseline_dir.mkdir()
        (baseline_dir / "test.py").write_text(
            """
def test_func(x: int):
    pass
"""
        )

        # Create current version with changed parameters
        current_dir = tmp_path / "current"
        current_dir.mkdir()
        (current_dir / "test.py").write_text(
            """
def test_func(x: int, y: str):
    pass
"""
        )

        detector = RegressionDetector(snapshot_dir=tmp_path / "snapshots")
        baseline_snapshot = detector.create_snapshot(baseline_dir, "v1.0", save=False)
        report = detector.detect_regressions(current_dir, baseline_snapshot, "v2.0")

        assert len(report.issues) > 0
        param_issues = [i for i in report.issues if "signature changed" in i.description]
        assert len(param_issues) > 0

    def test_detect_return_type_change(self, tmp_path: Path) -> None:
        """Test detecting return type changes."""
        # Create baseline
        baseline_dir = tmp_path / "baseline"
        baseline_dir.mkdir()
        (baseline_dir / "test.py").write_text(
            """
def test_func() -> int:
    return 1
"""
        )

        # Create current version with changed return type
        current_dir = tmp_path / "current"
        current_dir.mkdir()
        (current_dir / "test.py").write_text(
            """
def test_func() -> str:
    return "1"
"""
        )

        detector = RegressionDetector(snapshot_dir=tmp_path / "snapshots")
        baseline_snapshot = detector.create_snapshot(baseline_dir, "v1.0", save=False)
        report = detector.detect_regressions(current_dir, baseline_snapshot, "v2.0")

        assert len(report.issues) > 0
        return_issues = [i for i in report.issues if "return type" in i.description.lower()]
        assert len(return_issues) > 0

    def test_detect_async_change(self, tmp_path: Path) -> None:
        """Test detecting async/sync function changes."""
        # Create baseline
        baseline_dir = tmp_path / "baseline"
        baseline_dir.mkdir()
        (baseline_dir / "test.py").write_text(
            """
def test_func():
    pass
"""
        )

        # Create current version as async
        current_dir = tmp_path / "current"
        current_dir.mkdir()
        (current_dir / "test.py").write_text(
            """
async def test_func():
    pass
"""
        )

        detector = RegressionDetector(snapshot_dir=tmp_path / "snapshots")
        baseline_snapshot = detector.create_snapshot(baseline_dir, "v1.0", save=False)
        report = detector.detect_regressions(current_dir, baseline_snapshot, "v2.0")

        # Async/sync change is a breaking change that shows as removed function
        # (technically it's a different signature)
        assert report.breaking_count > 0
        # The function should be reported as removed since changing async/sync
        # fundamentally changes the signature
        removed_issues = [i for i in report.issues if "removed" in i.description.lower()]
        assert len(removed_issues) > 0

    def test_detect_performance_regression(self) -> None:
        """Test detecting performance regressions."""
        baseline_metrics = {
            "test.slow_func": PerformanceMetric(
                function_name="slow_func",
                module_path="test",
                execution_time_ms=100.0,
            )
        }

        current_metrics = {
            "test.slow_func": PerformanceMetric(
                function_name="slow_func",
                module_path="test",
                execution_time_ms=150.0,  # 50% slower
            )
        }

        detector = RegressionDetector(performance_threshold=0.10)
        issues = detector.detect_performance_regressions(baseline_metrics, current_metrics)

        assert len(issues) > 0
        perf_issue = issues[0]
        assert perf_issue.change_type == ChangeType.PERFORMANCE
        assert perf_issue.performance_delta is not None
        assert perf_issue.performance_delta > 0.10

    def test_performance_risk_assessment(self) -> None:
        """Test performance risk level assessment."""
        detector = RegressionDetector()

        # Test different performance degradation levels
        assert detector._assess_performance_risk(0.60) == RiskLevel.CRITICAL
        assert detector._assess_performance_risk(0.30) == RiskLevel.HIGH
        assert detector._assess_performance_risk(0.15) == RiskLevel.MEDIUM
        assert detector._assess_performance_risk(0.05) == RiskLevel.LOW

    def test_detect_dependency_changes(self) -> None:
        """Test detecting dependency version changes."""
        baseline_deps = {"requests": "2.28.0", "numpy": "1.24.0", "pandas": "1.5.0"}
        current_deps = {"requests": "2.31.0", "numpy": "1.24.0"}

        detector = RegressionDetector()
        issues = detector.detect_dependency_changes(baseline_deps, current_deps)

        # Should detect removed pandas and upgraded requests
        assert len(issues) >= 2
        removed_issues = [i for i in issues if "removed" in i.description.lower()]
        version_issues = [i for i in issues if "version changed" in i.description.lower()]
        assert len(removed_issues) > 0
        assert len(version_issues) > 0

    def test_version_change_risk_assessment(self) -> None:
        """Test dependency version change risk assessment."""
        detector = RegressionDetector()

        # Major version change
        assert detector._assess_version_change_risk("1.0.0", "2.0.0") == RiskLevel.HIGH

        # Minor version change
        assert detector._assess_version_change_risk("1.0.0", "1.1.0") == RiskLevel.MEDIUM

        # Patch version change
        assert detector._assess_version_change_risk("1.0.0", "1.0.1") == RiskLevel.LOW

    def test_calculate_risk_score(self) -> None:
        """Test risk score calculation."""
        issues = [
            RegressionIssue(
                change_type=ChangeType.BREAKING,
                risk_level=RiskLevel.CRITICAL,
                description="Critical issue",
                old_signature=None,
                new_signature=None,
                impact_description="High impact",
                migration_guide="Fix",
            ),
            RegressionIssue(
                change_type=ChangeType.BEHAVIORAL,
                risk_level=RiskLevel.MEDIUM,
                description="Medium issue",
                old_signature=None,
                new_signature=None,
                impact_description="Medium impact",
                migration_guide="Update",
            ),
        ]

        report = RegressionReport(
            baseline_version="v1.0",
            current_version="v2.0",
            issues=issues,
            breaking_count=1,
            behavioral_count=1,
            performance_count=0,
            dependency_count=0,
            total_functions_compared=10,
            total_classes_compared=0,
        )

        detector = RegressionDetector()
        risk_score = detector.calculate_risk_score(report)

        assert risk_score > 0
        assert risk_score <= 100

    def test_save_and_load_report(self, tmp_path: Path) -> None:
        """Test saving and loading regression reports."""
        report = RegressionReport(
            baseline_version="v1.0",
            current_version="v2.0",
            issues=[],
            breaking_count=0,
            behavioral_count=0,
            performance_count=0,
            dependency_count=0,
            total_functions_compared=10,
            total_classes_compared=5,
            summary="Test summary",
        )

        detector = RegressionDetector()
        report_file = tmp_path / "report.json"
        detector.save_report(report, report_file)

        assert report_file.exists()

        loaded_report = detector.load_report(report_file)
        assert loaded_report.baseline_version == "v1.0"
        assert loaded_report.current_version == "v2.0"
        assert loaded_report.total_functions_compared == 10

    def test_migration_guide_generation(self, tmp_path: Path) -> None:
        """Test migration guide generation for parameter changes."""
        # Create test case with parameter changes
        baseline_dir = tmp_path / "baseline"
        baseline_dir.mkdir()
        (baseline_dir / "test.py").write_text(
            """
def test_func(x: int):
    pass
"""
        )

        current_dir = tmp_path / "current"
        current_dir.mkdir()
        (current_dir / "test.py").write_text(
            """
def test_func(x: int, y: str = "default"):
    pass
"""
        )

        detector = RegressionDetector(snapshot_dir=tmp_path / "snapshots")
        baseline_snapshot = detector.create_snapshot(baseline_dir, "v1.0", save=False)
        report = detector.detect_regressions(current_dir, baseline_snapshot, "v2.0")

        # Check that migration guides are generated
        for issue in report.issues:
            assert issue.migration_guide
            assert len(issue.migration_guide) > 0

    def test_false_positive_handling_compatible_changes(self, tmp_path: Path) -> None:
        """Test that compatible changes don't trigger false positives."""
        # Create baseline
        baseline_dir = tmp_path / "baseline"
        baseline_dir.mkdir()
        (baseline_dir / "test.py").write_text(
            """
def test_func(x: int, y: str = "default"):
    '''Docstring.'''
    pass
"""
        )

        # Create current with only docstring change
        current_dir = tmp_path / "current"
        current_dir.mkdir()
        (current_dir / "test.py").write_text(
            """
def test_func(x: int, y: str = "default"):
    '''Updated docstring.'''
    pass
"""
        )

        detector = RegressionDetector(snapshot_dir=tmp_path / "snapshots")
        baseline_snapshot = detector.create_snapshot(baseline_dir, "v1.0", save=False)
        report = detector.detect_regressions(current_dir, baseline_snapshot, "v2.0")

        # Docstring changes shouldn't trigger regressions
        assert len(report.issues) == 0

    def test_class_removal_detection(self, tmp_path: Path) -> None:
        """Test detection of removed classes."""
        # Create baseline with class
        baseline_dir = tmp_path / "baseline"
        baseline_dir.mkdir()
        (baseline_dir / "test.py").write_text(
            """
class MyClass:
    def method1(self) -> None:
        pass
"""
        )

        # Create current without class
        current_dir = tmp_path / "current"
        current_dir.mkdir()
        (current_dir / "test.py").write_text("# Class removed")

        detector = RegressionDetector(snapshot_dir=tmp_path / "snapshots")
        baseline_snapshot = detector.create_snapshot(baseline_dir, "v1.0", save=False)
        report = detector.detect_regressions(current_dir, baseline_snapshot, "v2.0")

        assert report.breaking_count > 0
        class_issues = [i for i in report.issues if "Class" in i.description]
        assert len(class_issues) > 0

    def test_parameter_order_change_detection(self, tmp_path: Path) -> None:
        """Test detection of parameter order changes."""
        # Create baseline
        baseline_dir = tmp_path / "baseline"
        baseline_dir.mkdir()
        (baseline_dir / "test.py").write_text(
            """
def test_func(x: int, y: str):
    pass
"""
        )

        # Create current with reordered parameters
        current_dir = tmp_path / "current"
        current_dir.mkdir()
        (current_dir / "test.py").write_text(
            """
def test_func(y: str, x: int):
    pass
"""
        )

        detector = RegressionDetector(snapshot_dir=tmp_path / "snapshots")
        baseline_snapshot = detector.create_snapshot(baseline_dir, "v1.0", save=False)
        report = detector.detect_regressions(current_dir, baseline_snapshot, "v2.0")

        # Parameter order change should be detected
        assert len(report.issues) > 0

    def test_report_summary_generation(self, tmp_path: Path) -> None:
        """Test regression report summary generation."""
        issues = [
            RegressionIssue(
                change_type=ChangeType.BREAKING,
                risk_level=RiskLevel.CRITICAL,
                description="Breaking change",
                old_signature=None,
                new_signature=None,
                impact_description="Impact",
                migration_guide="Guide",
            )
        ]

        report = RegressionReport(
            baseline_version="v1.0",
            current_version="v2.0",
            issues=issues,
            breaking_count=1,
            behavioral_count=0,
            performance_count=0,
            dependency_count=0,
            total_functions_compared=10,
            total_classes_compared=0,
        )

        detector = RegressionDetector()
        summary = detector._generate_summary(report)

        assert "v1.0" in summary
        assert "v2.0" in summary
        assert "Breaking Changes: 1" in summary
        assert "WARNING" in summary  # Should warn about breaking changes

    def test_multiple_issue_types_in_report(self, tmp_path: Path) -> None:
        """Test report with multiple types of issues."""
        # Create complex scenario with multiple issue types
        baseline_dir = tmp_path / "baseline"
        baseline_dir.mkdir()
        (baseline_dir / "test.py").write_text(
            """
def removed_func():
    pass

def changed_func(x: int) -> str:
    return str(x)

def kept_func():
    pass
"""
        )

        current_dir = tmp_path / "current"
        current_dir.mkdir()
        (current_dir / "test.py").write_text(
            """
def changed_func(x: int, y: int) -> int:
    return x + y

def kept_func():
    pass

def new_func():
    pass
"""
        )

        detector = RegressionDetector(snapshot_dir=tmp_path / "snapshots")
        baseline_snapshot = detector.create_snapshot(baseline_dir, "v1.0", save=False)
        report = detector.detect_regressions(current_dir, baseline_snapshot, "v2.0")

        # Should have breaking changes (removed_func) and behavioral changes (changed_func)
        assert report.breaking_count > 0 or report.behavioral_count > 0
        assert len(report.issues) > 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_source_directory(self, tmp_path: Path) -> None:
        """Test handling of empty source directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        snapshot = APISnapshot()
        snapshot.create_snapshot(empty_dir, "v1.0")

        assert len(snapshot.functions) == 0
        assert len(snapshot.classes) == 0

    def test_syntax_error_in_source(self, tmp_path: Path) -> None:
        """Test handling of syntax errors in source files."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "bad.py").write_text("def bad_syntax( invalid python")

        snapshot = APISnapshot()
        # Should not raise, just log warning
        snapshot.create_snapshot(source_dir, "v1.0")

    def test_nonexistent_snapshot_load(self, tmp_path: Path) -> None:
        """Test loading nonexistent snapshot."""
        snapshot = APISnapshot()
        with pytest.raises(FileNotFoundError):
            snapshot.load_snapshot(tmp_path / "nonexistent.json")

    def test_invalid_snapshot_json(self, tmp_path: Path) -> None:
        """Test loading invalid JSON snapshot."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not valid json {{{")

        snapshot = APISnapshot()
        with pytest.raises(json.JSONDecodeError):
            snapshot.load_snapshot(bad_file)

    def test_performance_regression_with_missing_baseline(self) -> None:
        """Test performance regression when function not in baseline."""
        baseline_metrics = {
            "test.func1": PerformanceMetric(
                function_name="func1", module_path="test", execution_time_ms=100.0
            )
        }

        current_metrics = {
            "test.func1": PerformanceMetric(
                function_name="func1", module_path="test", execution_time_ms=100.0
            ),
            "test.func2": PerformanceMetric(
                function_name="func2", module_path="test", execution_time_ms=200.0
            ),
        }

        detector = RegressionDetector()
        issues = detector.detect_performance_regressions(baseline_metrics, current_metrics)

        # Should not crash, func2 should be ignored
        assert all(i.description != "func2" for i in issues)
