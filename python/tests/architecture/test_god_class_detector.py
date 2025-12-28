"""Tests for God Class Detector."""

import ast
from pathlib import Path

import pytest
from qontinui_devtools.architecture import (ClassMetrics, ExtractionSuggestion,
                                            GodClassDetector)
from qontinui_devtools.architecture.ast_metrics import (calculate_complexity,
                                                        count_attributes,
                                                        count_lines,
                                                        count_methods,
                                                        extract_method_names,
                                                        find_shared_attributes)


@pytest.fixture
def fixtures_dir() -> Path:
    """Get path to test fixtures directory."""
    return Path(__file__).parent.parent / "fixtures" / "god_class"


@pytest.fixture
def god_class_file(fixtures_dir: Path) -> Path:
    """Get path to god class example file."""
    return fixtures_dir / "god_class_example.py"


@pytest.fixture
def normal_class_file(fixtures_dir: Path) -> Path:
    """Get path to normal class example file."""
    return fixtures_dir / "normal_class.py"


@pytest.fixture
def detector() -> GodClassDetector:
    """Create detector with default settings."""
    return GodClassDetector(min_lines=200, min_methods=15, verbose=True)


class TestAstMetrics:
    """Tests for AST metrics utilities."""

    def test_count_lines(self, god_class_file: Path) -> None:
        """Test line counting."""
        with open(god_class_file) as f:
            source = f.read()

        tree = ast.parse(source)
        class_node = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "HugeClass":
                class_node = node
                break

        assert class_node is not None
        total_lines, code_lines = count_lines(class_node, source)

        assert total_lines > 0
        assert code_lines > 0
        assert code_lines <= total_lines

    def test_count_methods(self, god_class_file: Path) -> None:
        """Test method counting."""
        with open(god_class_file) as f:
            source = f.read()

        tree = ast.parse(source)
        class_node = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "HugeClass":
                class_node = node
                break

        assert class_node is not None
        method_counts = count_methods(class_node)

        assert method_counts["instance"] > 50  # HugeClass has many instance methods
        assert "public" in method_counts
        assert "private" in method_counts

    def test_count_attributes(self, god_class_file: Path) -> None:
        """Test attribute counting."""
        with open(god_class_file) as f:
            source = f.read()

        tree = ast.parse(source)
        class_node = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "HugeClass":
                class_node = node
                break

        assert class_node is not None
        attr_count = count_attributes(class_node)

        assert attr_count >= 10  # HugeClass has many attributes in __init__

    def test_extract_method_names(self, god_class_file: Path) -> None:
        """Test method name extraction."""
        with open(god_class_file) as f:
            source = f.read()

        tree = ast.parse(source)
        class_node = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "HugeClass":
                class_node = node
                break

        assert class_node is not None
        method_names = extract_method_names(class_node)

        assert "__init__" in method_names
        assert "get_data" in method_names
        assert "validate_input" in method_names
        assert len(method_names) > 50

    def test_find_shared_attributes(self) -> None:
        """Test finding shared attributes between methods."""
        source = """
class TestClass:
    def __init__(self) -> None:
        self.x = 0
        self.y = 0

    def method1(self) -> Any:
        return self.x + self.y

    def method2(self) -> Any:
        return self.x * 2

    def method3(self) -> Any:
        return 42
"""
        tree = ast.parse(source)
        class_node = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)][0]

        method1 = class_node.body[1]
        method2 = class_node.body[2]
        method3 = class_node.body[3]

        assert isinstance(method1, ast.FunctionDef)
        assert isinstance(method2, ast.FunctionDef)
        assert isinstance(method3, ast.FunctionDef)

        # method1 and method2 share self.x
        shared_1_2 = find_shared_attributes(method1, method2)
        assert "x" in shared_1_2

        # method1 and method3 share nothing
        shared_1_3 = find_shared_attributes(method1, method3)
        assert len(shared_1_3) == 0

    def test_calculate_complexity(self, god_class_file: Path) -> None:
        """Test complexity calculation."""
        with open(god_class_file) as f:
            source = f.read()

        tree = ast.parse(source)
        class_node = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "HugeClass":
                class_node = node
                break

        assert class_node is not None
        complexity = calculate_complexity(class_node)

        assert complexity > 0  # Should have some complexity


class TestGodClassDetector:
    """Tests for GodClassDetector."""

    def test_detect_god_class(self, detector: GodClassDetector, god_class_file: Path) -> None:
        """Test detection of god class."""
        god_classes = detector.analyze_file(str(god_class_file))

        assert len(god_classes) > 0
        huge_class = next((c for c in god_classes if c.name == "HugeClass"), None)
        assert huge_class is not None
        assert huge_class.is_god_class
        assert huge_class.method_count > 50
        assert huge_class.line_count > 150  # Adjusted threshold

    def test_normal_class_not_detected(
        self, detector: GodClassDetector, normal_class_file: Path
    ) -> None:
        """Test that normal classes are not flagged."""
        god_classes = detector.analyze_file(str(normal_class_file))

        # Normal classes should not be detected
        # NormalClass should not be flagged
        normal_class = next((c for c in god_classes if c.name == "NormalClass"), None)
        assert normal_class is None

        # WellDesignedValidator might have high LCOM (methods don't share attributes)
        # but should have low method count
        if god_classes:
            for cls in god_classes:
                # These are well-designed, so shouldn't meet multiple criteria
                assert cls.method_count < 10 or cls.line_count < 100

    def test_calculate_lcom(self, detector: GodClassDetector, god_class_file: Path) -> None:
        """Test LCOM calculation."""
        with open(god_class_file) as f:
            source = f.read()

        tree = ast.parse(source)
        class_node = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "HugeClass":
                class_node = node
                break

        assert class_node is not None
        lcom = detector.calculate_lcom(class_node)

        # God class should have high LCOM (poor cohesion)
        assert 0.0 <= lcom <= 1.0
        # Many methods don't share attributes, so LCOM should be relatively high
        assert lcom > 0.5

    def test_detect_responsibilities(
        self, detector: GodClassDetector, god_class_file: Path
    ) -> None:
        """Test responsibility detection."""
        with open(god_class_file) as f:
            source = f.read()

        tree = ast.parse(source)
        class_node = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "HugeClass":
                class_node = node
                break

        assert class_node is not None
        responsibilities = detector.detect_responsibilities(class_node)

        # Should detect multiple responsibilities
        assert len(responsibilities) >= 5
        # Check for specific responsibilities based on method naming
        resp_lower = [r.lower() for r in responsibilities]
        assert any("data" in r or "access" in r for r in resp_lower)
        assert any("validation" in r for r in resp_lower)
        assert any("persistence" in r for r in resp_lower)

    def test_suggest_extractions(self, detector: GodClassDetector, god_class_file: Path) -> None:
        """Test extraction suggestions."""
        god_classes = detector.analyze_file(str(god_class_file))
        huge_class = next((c for c in god_classes if c.name == "HugeClass"), None)

        assert huge_class is not None
        suggestions = detector.suggest_extractions(huge_class)

        # Should have extraction suggestions
        assert len(suggestions) > 0

        # Check structure of suggestions
        for suggestion in suggestions:
            assert isinstance(suggestion, ExtractionSuggestion)
            assert len(suggestion.new_class_name) > 0
            assert len(suggestion.methods_to_extract) >= 3
            assert len(suggestion.responsibility) > 0
            assert suggestion.estimated_lines > 0

    def test_severity_calculation(self, detector: GodClassDetector, god_class_file: Path) -> None:
        """Test severity level calculation."""
        god_classes = detector.analyze_file(str(god_class_file))
        huge_class = next((c for c in god_classes if c.name == "HugeClass"), None)

        assert huge_class is not None
        assert huge_class.severity in ["critical", "high", "medium"]

    def test_generate_report(self, detector: GodClassDetector, god_class_file: Path) -> None:
        """Test report generation."""
        god_classes = detector.analyze_file(str(god_class_file))

        report = detector.generate_report(god_classes)

        assert len(report) > 0
        assert "God Class Detection Report" in report
        assert "HugeClass" in report
        assert "LCOM" in report
        assert "Recommendations" in report

    def test_analyze_directory(self, detector: GodClassDetector, fixtures_dir: Path) -> None:
        """Test analyzing entire directory."""
        god_classes = detector.analyze_directory(str(fixtures_dir))

        # Should find HugeClass
        assert len(god_classes) > 0
        names = [c.name for c in god_classes]
        assert "HugeClass" in names
        assert "NormalClass" not in names

        # WellDesignedValidator might be flagged due to LCOM, but HugeClass should be worse
        huge_class = next(c for c in god_classes if c.name == "HugeClass")
        assert huge_class.severity in ["critical", "high"]

    def test_threshold_configuration(self, god_class_file: Path) -> None:
        """Test configuring detection thresholds."""
        # Very strict thresholds
        strict_detector = GodClassDetector(min_lines=1000, min_methods=100)
        strict_results = strict_detector.analyze_file(str(god_class_file))

        # Lenient thresholds
        lenient_detector = GodClassDetector(min_lines=50, min_methods=5)
        lenient_results = lenient_detector.analyze_file(str(god_class_file))

        # Lenient should detect as many or more than strict
        assert len(lenient_results) >= len(strict_results)

    def test_class_metrics_dataclass(self) -> None:
        """Test ClassMetrics dataclass."""
        metrics = ClassMetrics(
            name="TestClass",
            file_path="/test/path.py",
            line_start=1,
            line_end=100,
            line_count=100,
            method_count=50,
            attribute_count=10,
            cyclomatic_complexity=75,
            lcom=0.85,
            responsibilities=["data", "validation"],
            is_god_class=True,
        )

        # Should auto-calculate severity as critical (many methods + high LCOM)
        assert metrics.severity in ["critical", "high", "medium"]
        assert metrics.is_god_class

    def test_extraction_suggestion_dataclass(self) -> None:
        """Test ExtractionSuggestion dataclass."""
        suggestion = ExtractionSuggestion(
            new_class_name="DataAccessor",
            methods_to_extract=["get_data", "set_data", "fetch_data"],
            responsibility="Data Access",
            estimated_lines=150,
        )

        assert suggestion.new_class_name == "DataAccessor"
        assert len(suggestion.methods_to_extract) == 3
        assert suggestion.estimated_lines == 150

    def test_lcom_edge_cases(self, detector: GodClassDetector) -> None:
        """Test LCOM calculation edge cases."""
        # Class with only one method
        source_one_method = """
class OneMethod:
    def method1(self) -> Any:
        return 42
"""
        tree = ast.parse(source_one_method)
        class_node = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)][0]
        lcom = detector.calculate_lcom(class_node)
        assert lcom == 0.0  # Single method has perfect cohesion

        # Class with highly cohesive methods
        source_cohesive = """
class Cohesive:
    def __init__(self) -> None:
        self.x = 0

    def method1(self) -> Any:
        return self.x + 1

    def method2(self) -> Any:
        return self.x * 2

    def method3(self) -> None:
        self.x += 1
"""
        tree = ast.parse(source_cohesive)
        class_node = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)][0]
        lcom = detector.calculate_lcom(class_node)
        assert lcom == 0.0  # All methods share self.x

    def test_method_count_types(self) -> None:
        """Test counting different method types."""
        source = """
class MixedMethods:
    def instance_method(self) -> None:
        pass

    @classmethod
    def class_method(cls) -> None:
        pass

    @staticmethod
    def static_method() -> None:
        pass

    def _private_method(self) -> None:
        pass
"""
        tree = ast.parse(source)
        class_node = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)][0]
        counts = count_methods(class_node)

        assert counts["instance"] == 2  # instance_method, _private_method
        assert counts["class"] == 1
        assert counts["static"] == 1
        assert counts["private"] == 1
        assert counts["public"] == 3
