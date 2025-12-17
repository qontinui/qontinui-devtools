"""Tests for coupling and cohesion analyzer."""

from typing import Any

from typing import Any

from typing import Any

from typing import Any

import ast
import os
import tempfile
from pathlib import Path

import pytest
from qontinui_devtools.architecture import (
    CouplingCohesionAnalyzer,
    DependencyGraphBuilder,
    calculate_lcc,
    calculate_lcom,
    calculate_lcom4,
    calculate_tcc,
    count_abstract_classes,
)


class TestCohesionMetrics:
    """Test cohesion metric calculations."""

    def test_calculate_lcom_low_cohesion(self) -> None:
        """Test LCOM calculation for low cohesion class."""
        code = """
class LowCohesion:
    def method_a(self) -> None:
        self.attr_a = 1

    def method_b(self) -> None:
        self.attr_b = 2

    def method_c(self) -> None:
        self.attr_c = 3
"""
        tree = ast.parse(code)
        class_node = tree.body[0]
        assert isinstance(class_node, ast.ClassDef)

        lcom = calculate_lcom(class_node)

        # All methods are disconnected, LCOM should be high
        assert lcom > 0.5

    def test_calculate_lcom_high_cohesion(self) -> None:
        """Test LCOM calculation for high cohesion class."""
        code = """
class HighCohesion:
    def __init__(self) -> None:
        self.data: list[Any] = []
        self.count = 0

    def add(self, item) -> None:
        self.data.append(item)
        self.count += 1

    def remove(self, item) -> None:
        self.data.remove(item)
        self.count -= 1

    def size(self) -> Any:
        return self.count
"""
        tree = ast.parse(code)
        class_node = tree.body[0]
        assert isinstance(class_node, ast.ClassDef)

        lcom = calculate_lcom(class_node)

        # All methods share attributes, LCOM should be low
        assert lcom < 0.3

    def test_calculate_lcom4_perfect_cohesion(self) -> None:
        """Test LCOM4 for perfect cohesion (all methods connected)."""
        code = """
class PerfectCohesion:
    def method_a(self) -> None:
        self.shared = 1

    def method_b(self) -> Any:
        return self.shared * 2

    def method_c(self) -> None:
        self.shared += 3
"""
        tree = ast.parse(code)
        class_node = tree.body[0]
        assert isinstance(class_node, ast.ClassDef)

        lcom4 = calculate_lcom4(class_node)

        # All methods connected = 1 component
        assert lcom4 == 1.0

    def test_calculate_lcom4_disconnected(self) -> None:
        """Test LCOM4 for completely disconnected methods."""
        code = """
class Disconnected:
    def method_a(self) -> None:
        self.attr_a = 1

    def method_b(self) -> None:
        self.attr_b = 2

    def method_c(self) -> None:
        self.attr_c = 3
"""
        tree = ast.parse(code)
        class_node = tree.body[0]
        assert isinstance(class_node, ast.ClassDef)

        lcom4 = calculate_lcom4(class_node)

        # Each method is a separate component
        assert lcom4 == 3.0

    def test_calculate_tcc_perfect(self) -> None:
        """Test TCC for perfect tight cohesion."""
        code = """
class TightlyCoupled:
    def method_a(self) -> None:
        self.x = 1
        self.y = 2

    def method_b(self) -> Any:
        return self.x + self.y

    def method_c(self) -> Any:
        return self.x * self.y
"""
        tree = ast.parse(code)
        class_node = tree.body[0]
        assert isinstance(class_node, ast.ClassDef)

        tcc = calculate_tcc(class_node)

        # All pairs directly connected
        assert tcc == 1.0

    def test_calculate_tcc_no_connections(self) -> None:
        """Test TCC for no connections."""
        code = """
class NoConnections:
    def method_a(self) -> None:
        self.a = 1

    def method_b(self) -> None:
        self.b = 2
"""
        tree = ast.parse(code)
        class_node = tree.body[0]
        assert isinstance(class_node, ast.ClassDef)

        tcc = calculate_tcc(class_node)

        # No shared attributes
        assert tcc == 0.0

    def test_calculate_lcc_with_indirect(self) -> None:
        """Test LCC includes indirect connections."""
        code = """
class IndirectConnections:
    def method_a(self) -> None:
        self.x = 1

    def method_b(self) -> None:
        self.x = 2
        self.y = 3

    def method_c(self) -> None:
        self.y = 4
"""
        tree = ast.parse(code)
        class_node = tree.body[0]
        assert isinstance(class_node, ast.ClassDef)

        lcc = calculate_lcc(class_node)

        # a-b direct, b-c direct, a-c indirect -> all connected
        assert lcc == 1.0

    def test_single_method_class(self) -> None:
        """Test metrics for class with single method."""
        code = """
class SingleMethod:
    def method(self) -> None:
        self.x = 1
"""
        tree = ast.parse(code)
        class_node = tree.body[0]
        assert isinstance(class_node, ast.ClassDef)

        # All metrics should return ideal values for single method
        assert calculate_lcom(class_node) == 0.0
        assert calculate_lcom4(class_node) == 1.0
        assert calculate_tcc(class_node) == 1.0
        assert calculate_lcc(class_node) == 1.0


class TestCouplingMetrics:
    """Test coupling metric calculations."""

    def test_calculate_instability_maximally_stable(self) -> None:
        """Test instability calculation for maximally stable module."""
        analyzer = CouplingCohesionAnalyzer()

        # Ca = 10, Ce = 0 -> I = 0
        instability = analyzer.calculate_instability(ca=10, ce=0)
        assert instability == 0.0

    def test_calculate_instability_maximally_unstable(self) -> None:
        """Test instability calculation for maximally unstable module."""
        analyzer = CouplingCohesionAnalyzer()

        # Ca = 0, Ce = 10 -> I = 1
        instability = analyzer.calculate_instability(ca=0, ce=10)
        assert instability == 1.0

    def test_calculate_instability_balanced(self) -> None:
        """Test instability calculation for balanced module."""
        analyzer = CouplingCohesionAnalyzer()

        # Ca = 5, Ce = 5 -> I = 0.5
        instability = analyzer.calculate_instability(ca=5, ce=5)
        assert instability == 0.5

    def test_calculate_instability_isolated(self) -> None:
        """Test instability calculation for isolated module."""
        analyzer = CouplingCohesionAnalyzer()

        # Ca = 0, Ce = 0 -> I = 0
        instability = analyzer.calculate_instability(ca=0, ce=0)
        assert instability == 0.0

    def test_calculate_distance_from_main_perfect(self) -> None:
        """Test distance from main sequence for perfect balance."""
        analyzer = CouplingCohesionAnalyzer()

        # I = 0.5, A = 0.5 -> D = |0.5 + 0.5 - 1| = 0
        distance = analyzer.calculate_distance_from_main(instability=0.5, abstractness=0.5)
        assert distance == 0.0

    def test_calculate_distance_from_main_zone_of_pain(self) -> None:
        """Test distance for zone of pain (concrete and stable)."""
        analyzer = CouplingCohesionAnalyzer()

        # I = 0.0, A = 0.0 -> D = |0 + 0 - 1| = 1
        distance = analyzer.calculate_distance_from_main(instability=0.0, abstractness=0.0)
        assert distance == 1.0

    def test_calculate_distance_from_main_zone_of_uselessness(self) -> None:
        """Test distance for zone of uselessness (abstract and unstable)."""
        analyzer = CouplingCohesionAnalyzer()

        # I = 1.0, A = 1.0 -> D = |1 + 1 - 1| = 1
        distance = analyzer.calculate_distance_from_main(instability=1.0, abstractness=1.0)
        assert distance == 1.0


class TestAbstractnessCalculation:
    """Test abstractness metric calculation."""

    def test_count_abstract_classes_abc(self) -> None:
        """Test counting abstract classes using ABC."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
from abc import ABC, abstractmethod

class AbstractBase(ABC):
    @abstractmethod
    def abstract_method(self) -> None:
        pass

class ConcreteClass:
    def method(self) -> None:
        pass
"""
            )
            f.flush()

            try:
                abstract, total = count_abstract_classes(f.name)
                assert abstract == 1
                assert total == 2
            finally:
                os.unlink(f.name)

    def test_count_abstract_classes_decorator_only(self) -> None:
        """Test counting abstract classes using only decorator."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
from abc import abstractmethod

class SemiAbstract:
    @abstractmethod
    def abstract_method(self) -> None:
        pass

    def concrete_method(self) -> None:
        pass
"""
            )
            f.flush()

            try:
                abstract, total = count_abstract_classes(f.name)
                assert abstract == 1
                assert total == 1
            finally:
                os.unlink(f.name)

    def test_count_abstract_classes_no_abstract(self) -> None:
        """Test counting when there are no abstract classes."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
class ConcreteA:
    def method(self) -> None:
        pass

class ConcreteB:
    def method(self) -> None:
        pass
"""
            )
            f.flush()

            try:
                abstract, total = count_abstract_classes(f.name)
                assert abstract == 0
                assert total == 2
            finally:
                os.unlink(f.name)


class TestDependencyGraphBuilder:
    """Test dependency graph construction."""

    def test_build_simple_graph(self) -> None:
        """Test building graph for simple module structure."""
        # Create temporary module structure
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create main.py that imports helper.py
            main_path = Path(tmpdir) / "main.py"
            helper_path = Path(tmpdir) / "helper.py"

            main_path.write_text("from helper import help_function\n")
            helper_path.write_text("def help_function():\n    pass\n")

            builder = DependencyGraphBuilder()
            graph = builder.build(tmpdir)

            # main.py should depend on helper.py
            assert str(main_path) in graph
            assert str(helper_path) in graph[str(main_path)]

    def test_calculate_afferent_coupling(self) -> None:
        """Test afferent coupling calculation."""
        graph = {
            "/a.py": {"/c.py"},
            "/b.py": {"/c.py"},
            "/c.py": set(),
        }

        builder = DependencyGraphBuilder()

        # c.py is depended on by a.py and b.py
        ca = builder.calculate_afferent_coupling("/c.py", graph)
        assert ca == 2

    def test_calculate_efferent_coupling(self) -> None:
        """Test efferent coupling calculation."""
        graph = {
            "/a.py": {"/b.py", "/c.py", "/d.py"},
            "/b.py": set(),
            "/c.py": set(),
            "/d.py": set(),
        }

        builder = DependencyGraphBuilder()

        # a.py depends on 3 modules
        ce = builder.calculate_efferent_coupling("/a.py", graph)
        assert ce == 3

    def test_find_cycles(self) -> None:
        """Test cycle detection in dependency graph."""
        graph = {
            "/a.py": {"/b.py"},
            "/b.py": {"/c.py"},
            "/c.py": {"/a.py"},  # Cycle!
        }

        builder = DependencyGraphBuilder()
        cycles = builder.find_cycles(graph)

        assert len(cycles) >= 1
        # Verify it found the cycle (order may vary)
        cycle_modules = set()
        for cycle in cycles:
            cycle_modules.update(cycle)
        assert "/a.py" in cycle_modules
        assert "/b.py" in cycle_modules
        assert "/c.py" in cycle_modules


class TestCouplingCohesionAnalyzer:
    """Test the main analyzer class."""

    def test_analyze_directory_basic(self) -> None:
        """Test analyzing a basic directory."""
        # Use test fixtures
        fixtures_dir = Path(__file__).parent.parent / "fixtures"

        analyzer = CouplingCohesionAnalyzer(verbose=False)
        coupling, cohesion = analyzer.analyze_directory(str(fixtures_dir / "low_cohesion.py"))

        # Should find at least one module and classes
        assert len(coupling) >= 1
        assert len(cohesion) >= 1

    def test_analyze_low_cohesion_class(self) -> None:
        """Test analyzing the low cohesion fixture."""
        fixtures_dir = Path(__file__).parent.parent / "fixtures"
        low_cohesion_file = fixtures_dir / "low_cohesion.py"

        analyzer = CouplingCohesionAnalyzer(verbose=False)
        coupling, cohesion = analyzer.analyze_directory(str(low_cohesion_file))

        # Find the LowCohesionClass
        low_cohesion_class = next((c for c in cohesion if c.name == "LowCohesionClass"), None)

        assert low_cohesion_class is not None
        # Should have poor cohesion
        assert low_cohesion_class.lcom > 0.7
        assert low_cohesion_class.lcom4 > 1.0
        assert low_cohesion_class.cohesion_score in ("poor", "fair")

    def test_analyze_high_cohesion_class(self) -> None:
        """Test analyzing the high cohesion fixture."""
        fixtures_dir = Path(__file__).parent.parent / "fixtures"
        low_cohesion_file = fixtures_dir / "low_cohesion.py"

        analyzer = CouplingCohesionAnalyzer(verbose=False)
        coupling, cohesion = analyzer.analyze_directory(str(low_cohesion_file))

        # Find the HighCohesionClass
        high_cohesion_class = next((c for c in cohesion if c.name == "HighCohesionClass"), None)

        assert high_cohesion_class is not None
        # Should have good cohesion
        assert high_cohesion_class.lcom < 0.3
        assert high_cohesion_class.lcom4 == 1.0
        assert high_cohesion_class.cohesion_score in ("excellent", "good")

    def test_generate_report(self) -> None:
        """Test report generation."""
        fixtures_dir = Path(__file__).parent.parent / "fixtures"

        analyzer = CouplingCohesionAnalyzer(verbose=False)
        coupling, cohesion = analyzer.analyze_directory(str(fixtures_dir / "low_cohesion.py"))

        report = analyzer.generate_report(coupling, cohesion)

        # Report should contain key sections
        assert "COUPLING" in report
        assert "COHESION" in report
        assert "SUMMARY" in report

    def test_coupling_score_classification(self) -> None:
        """Test coupling score classification."""
        analyzer = CouplingCohesionAnalyzer()

        # Excellent: low distance, low dependencies
        score = analyzer._classify_coupling(ca=5, ce=3, instability=0.5, distance=0.05)
        assert score == "excellent"

        # Poor: high distance
        score = analyzer._classify_coupling(ca=1, ce=20, instability=0.95, distance=0.8)
        assert score == "poor"

    def test_cohesion_score_classification(self) -> None:
        """Test cohesion score classification."""
        analyzer = CouplingCohesionAnalyzer()

        # Excellent: 1 component, high TCC
        score = analyzer._classify_cohesion(lcom=0.1, lcom4=1.0, tcc=0.8, lcc=0.9)
        assert score == "excellent"

        # Poor: many components, low TCC
        score = analyzer._classify_cohesion(lcom=0.9, lcom4=5.0, tcc=0.1, lcc=0.2)
        assert score == "poor"


class TestIntegration:
    """Integration tests with real file structures."""

    def test_analyze_module_with_deps(self) -> None:
        """Test analyzing a module with dependencies."""
        fixtures_dir = Path(__file__).parent.parent / "fixtures" / "module_with_deps"

        if not fixtures_dir.exists():
            pytest.skip("Fixture module_with_deps not found")

        analyzer = CouplingCohesionAnalyzer(verbose=False)
        coupling, cohesion = analyzer.analyze_directory(str(fixtures_dir))

        # Should find multiple modules
        assert len(coupling) >= 3

        # main.py should have efferent coupling > 0
        main_module = next((c for c in coupling if "main.py" in c.file_path), None)
        if main_module:
            assert main_module.efferent_coupling >= 2

    def test_high_coupling_fixture(self) -> None:
        """Test analyzing the high coupling fixture."""
        fixtures_dir = Path(__file__).parent.parent / "fixtures"
        high_coupling_file = fixtures_dir / "high_coupling.py"

        if not high_coupling_file.exists():
            pytest.skip("Fixture high_coupling.py not found")

        analyzer = CouplingCohesionAnalyzer(verbose=False)
        coupling, cohesion = analyzer.analyze_directory(str(high_coupling_file))

        # Should find the module
        assert len(coupling) >= 1

        # The HighlyCoupledClass should be in cohesion results
        highly_coupled = next((c for c in cohesion if c.name == "HighlyCoupledClass"), None)
        assert highly_coupled is not None
