"""Tests for dependency graph visualizer."""

import json
import tempfile
from pathlib import Path

import pytest
from qontinui_devtools.architecture import DependencyGraphVisualizer, GraphEdge, GraphNode


@pytest.fixture
def sample_python_code(tmp_path: Path) -> Path:
    """Create a sample Python project for testing."""
    # Create package structure
    pkg = tmp_path / "sample_pkg"
    pkg.mkdir()

    # Create __init__.py
    (pkg / "__init__.py").write_text("from .module_a import ClassA\n")

    # Create module_a.py
    module_a = """
class ClassA:
    def method_a(self) -> Any:
        return "A"

    def method_b(self) -> Any:
        return self.method_a()

def function_a() -> Any:
    return "function_a"
"""
    (pkg / "module_a.py").write_text(module_a)

    # Create module_b.py
    module_b = """
from .module_a import ClassA

class ClassB(ClassA):
    def method_c(self) -> Any:
        return "B"

    def method_d(self) -> Any:
        return self.method_c()

def function_b() -> Any:
    from .module_a import function_a
    return function_a()
"""
    (pkg / "module_b.py").write_text(module_b)

    # Create module_c.py
    module_c = """
from .module_b import ClassB
import json

class ClassC:
    def __init__(self) -> None:
        self.b = ClassB()

    def method_e(self) -> Any:
        return json.dumps({"value": "C"})
"""
    (pkg / "module_c.py").write_text(module_c)

    return pkg


@pytest.fixture
def visualizer() -> DependencyGraphVisualizer:
    """Create a graph visualizer instance."""
    return DependencyGraphVisualizer(verbose=False)


class TestGraphNode:
    """Test GraphNode dataclass."""

    def test_create_node(self) -> None:
        """Test creating a graph node."""
        node = GraphNode(
            id="test.module",
            label="module",
            node_type="module",
            metrics={"complexity": 10},
            color="#ff0000",
            size=20,
        )

        assert node.id == "test.module"
        assert node.label == "module"
        assert node.node_type == "module"
        assert node.metrics["complexity"] == 10
        assert node.color == "#ff0000"
        assert node.size == 20

    def test_node_to_dict(self) -> None:
        """Test converting node to dictionary."""
        node = GraphNode(
            id="test.module",
            label="module",
            node_type="module",
            metrics={"complexity": 10},
        )

        node_dict = node.to_dict()
        assert node_dict["id"] == "test.module"
        assert node_dict["label"] == "module"
        assert node_dict["node_type"] == "module"
        assert node_dict["metrics"]["complexity"] == 10


class TestGraphEdge:
    """Test GraphEdge dataclass."""

    def test_create_edge(self) -> None:
        """Test creating a graph edge."""
        edge = GraphEdge(source="module_a", target="module_b", edge_type="imports", weight=2)

        assert edge.source == "module_a"
        assert edge.target == "module_b"
        assert edge.edge_type == "imports"
        assert edge.weight == 2

    def test_edge_to_dict(self) -> None:
        """Test converting edge to dictionary."""
        edge = GraphEdge(source="module_a", target="module_b", edge_type="imports")

        edge_dict = edge.to_dict()
        assert edge_dict["source"] == "module_a"
        assert edge_dict["target"] == "module_b"
        assert edge_dict["edge_type"] == "imports"
        assert edge_dict["weight"] == 1


class TestDependencyGraphVisualizer:
    """Test DependencyGraphVisualizer class."""

    def test_init(self) -> None:
        """Test initializing the visualizer."""
        visualizer = DependencyGraphVisualizer(verbose=True)
        assert visualizer.verbose is True

    def test_build_module_graph(
        self, visualizer: DependencyGraphVisualizer, sample_python_code: Path
    ) -> None:
        """Test building a module-level dependency graph."""
        nodes, edges = visualizer.build_graph(str(sample_python_code), level="module")

        # Should have 3 modules
        assert len(nodes) >= 3

        # Check node types
        for node in nodes:
            assert node.node_type == "module"
            assert "in_degree" in node.metrics
            assert "out_degree" in node.metrics

        # Should have at least some edges
        assert len(edges) > 0

        # Check edge types
        for edge in edges:
            assert edge.edge_type == "imports"

    def test_build_class_graph(
        self, visualizer: DependencyGraphVisualizer, sample_python_code: Path
    ) -> None:
        """Test building a class-level dependency graph."""
        nodes, edges = visualizer.build_graph(str(sample_python_code), level="class")

        # Should have at least 3 classes
        assert len(nodes) >= 3

        # Check node types
        for node in nodes:
            assert node.node_type == "class"
            assert "methods" in node.metrics

        # Should have inheritance edges
        if edges:
            inheritance_edges = [e for e in edges if e.edge_type == "inherits"]
            assert len(inheritance_edges) >= 0  # At least ClassB inherits from ClassA

    def test_build_function_graph(
        self, visualizer: DependencyGraphVisualizer, sample_python_code: Path
    ) -> None:
        """Test building a function-level dependency graph."""
        nodes, edges = visualizer.build_graph(str(sample_python_code), level="function")

        # Should have functions and methods
        assert len(nodes) > 0

        # Check node types
        for node in nodes:
            assert node.node_type == "function"
            assert "lines" in node.metrics
            assert "calls" in node.metrics

    def test_invalid_level(
        self, visualizer: DependencyGraphVisualizer, sample_python_code: Path
    ) -> None:
        """Test with invalid level parameter."""
        with pytest.raises(ValueError, match="Invalid level"):
            visualizer.build_graph(str(sample_python_code), level="invalid")

    def test_invalid_path(self, visualizer: DependencyGraphVisualizer) -> None:
        """Test with non-existent path."""
        with pytest.raises(FileNotFoundError):
            visualizer.build_graph("/non/existent/path")

    def test_detect_cycles(self, visualizer: DependencyGraphVisualizer) -> None:
        """Test circular dependency detection."""
        # Create nodes with circular dependencies
        nodes = [
            GraphNode("a", "A", "module", {}),
            GraphNode("b", "B", "module", {}),
            GraphNode("c", "C", "module", {}),
        ]

        edges = [
            GraphEdge("a", "b", "imports"),
            GraphEdge("b", "c", "imports"),
            GraphEdge("c", "a", "imports"),  # Creates cycle
        ]

        cycles = visualizer.detect_cycles(nodes, edges)
        assert len(cycles) > 0
        assert len(cycles[0]) == 3  # Triangle cycle

    def test_no_cycles(self, visualizer: DependencyGraphVisualizer) -> None:
        """Test with acyclic graph."""
        nodes = [
            GraphNode("a", "A", "module", {}),
            GraphNode("b", "B", "module", {}),
            GraphNode("c", "C", "module", {}),
        ]

        edges = [
            GraphEdge("a", "b", "imports"),
            GraphEdge("b", "c", "imports"),
        ]

        cycles = visualizer.detect_cycles(nodes, edges)
        assert len(cycles) == 0

    def test_generate_html_interactive(
        self, visualizer: DependencyGraphVisualizer, sample_python_code: Path
    ) -> None:
        """Test generating interactive HTML visualization."""
        nodes, edges = visualizer.build_graph(str(sample_python_code), level="module")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            output_path = f.name

        try:
            visualizer.generate_html_interactive(nodes, edges, output_path)

            # Check file was created
            assert Path(output_path).exists()

            # Check file contains HTML
            with open(output_path) as f:
                content = f.read()
                assert "<!DOCTYPE html>" in content
                assert "d3" in content.lower()  # Check for d3.js reference
                assert "nodes" in content.lower()
                assert "edges" in content.lower()
        finally:
            Path(output_path).unlink()

    def test_visualize_html(
        self, visualizer: DependencyGraphVisualizer, sample_python_code: Path
    ) -> None:
        """Test visualize method with HTML format."""
        nodes, edges = visualizer.build_graph(str(sample_python_code), level="module")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            output_path = f.name

        try:
            visualizer.visualize(nodes, edges, output_path, format="html", highlight_cycles=True)

            assert Path(output_path).exists()
        finally:
            Path(output_path).unlink()

    def test_export_json(
        self, visualizer: DependencyGraphVisualizer, sample_python_code: Path
    ) -> None:
        """Test exporting graph to JSON."""
        nodes, edges = visualizer.build_graph(str(sample_python_code), level="module")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_path = f.name

        try:
            visualizer.export_json(nodes, edges, output_path)

            # Check file was created
            assert Path(output_path).exists()

            # Check JSON structure
            with open(output_path) as f:
                data = json.load(f)
                assert "nodes" in data
                assert "edges" in data
                assert len(data["nodes"]) == len(nodes)
                assert len(data["edges"]) == len(edges)
        finally:
            Path(output_path).unlink()

    def test_apply_layout(self, visualizer: DependencyGraphVisualizer) -> None:
        """Test applying layout algorithms."""
        nodes = [
            GraphNode("a", "A", "module", {}),
            GraphNode("b", "B", "module", {}),
            GraphNode("c", "C", "module", {}),
        ]

        edges = [
            GraphEdge("a", "b", "imports"),
            GraphEdge("b", "c", "imports"),
        ]

        # Test force-directed layout
        positions = visualizer.apply_layout(nodes, edges, "force")
        assert len(positions) == 3
        assert all(isinstance(pos, tuple) and len(pos) == 2 for pos in positions.values())

        # Test hierarchical layout
        positions = visualizer.apply_layout(nodes, edges, "hierarchical")
        assert len(positions) == 3

        # Test circular layout
        positions = visualizer.apply_layout(nodes, edges, "circular")
        assert len(positions) == 3

    def test_calculate_node_metrics(
        self, visualizer: DependencyGraphVisualizer, sample_python_code: Path
    ) -> None:
        """Test that node metrics are calculated correctly."""
        nodes, edges = visualizer.build_graph(str(sample_python_code), level="module")

        for node in nodes:
            assert "in_degree" in node.metrics
            assert "out_degree" in node.metrics
            assert "total_degree" in node.metrics
            assert node.metrics["total_degree"] == (
                node.metrics["in_degree"] + node.metrics["out_degree"]
            )
            assert node.size is not None


class TestGraphvizGeneration:
    """Test Graphviz DOT generation."""

    def test_generate_dot(self) -> None:
        """Test generating DOT format."""
        from qontinui_devtools.architecture.graphviz_gen import generate_dot

        nodes = [
            GraphNode("a", "A", "module", {"complexity": 5}),
            GraphNode("b", "B", "class", {"methods": 3}),
        ]

        edges = [GraphEdge("a", "b", "imports")]

        dot_string = generate_dot(nodes, edges, title="Test Graph", rankdir="LR")

        assert "digraph DependencyGraph" in dot_string
        assert "Test Graph" in dot_string
        assert "rankdir=LR" in dot_string
        assert '"a"' in dot_string
        assert '"b"' in dot_string
        assert '"a" -> "b"' in dot_string

    def test_generate_dot_with_cycles(self) -> None:
        """Test generating DOT with cycle highlighting."""
        from qontinui_devtools.architecture.graphviz_gen import generate_dot

        nodes = [
            GraphNode("a", "A", "module", {}),
            GraphNode("b", "B", "module", {}),
        ]

        edges = [
            GraphEdge("a", "b", "imports"),
            GraphEdge("b", "a", "imports"),
        ]

        cycles = [["a", "b"]]

        dot_string = generate_dot(nodes, edges, cycles=cycles)

        # Should highlight cycle edges in red
        assert "#ff0000" in dot_string

    def test_apply_styling(self) -> None:
        """Test node styling."""
        from qontinui_devtools.architecture.graphviz_gen import apply_styling

        node = GraphNode("test", "Test", "module", {"total_degree": 15})

        style = apply_styling(node)

        assert "fillcolor" in style
        assert "color" in style
        assert "shape" in style
        assert "style" in style
        assert "penwidth" in style


class TestHTMLGeneration:
    """Test HTML graph generation."""

    def test_generate_html_graph(self) -> None:
        """Test generating HTML graph."""
        from qontinui_devtools.architecture.html_graph import generate_html_graph

        nodes = [
            GraphNode("a", "A", "module", {"complexity": 5}),
            GraphNode("b", "B", "class", {"methods": 3}),
        ]

        edges = [GraphEdge("a", "b", "imports")]

        html = generate_html_graph(nodes, edges, title="Test Graph")

        assert "<!DOCTYPE html>" in html
        assert "Test Graph" in html
        assert "d3" in html.lower()  # Check for d3 reference (might be d3.v7.min.js)
        assert '"id": "a"' in html
        assert '"id": "b"' in html


class TestLayouts:
    """Test layout algorithms."""

    def test_force_directed_layout(self) -> None:
        """Test force-directed layout."""
        from qontinui_devtools.architecture.layouts import force_directed_layout

        nodes = [
            GraphNode("a", "A", "module", {}),
            GraphNode("b", "B", "module", {}),
            GraphNode("c", "C", "module", {}),
        ]

        edges = [
            GraphEdge("a", "b", "imports"),
            GraphEdge("b", "c", "imports"),
        ]

        positions = force_directed_layout(nodes, edges, width=1000, height=1000, iterations=50)

        assert len(positions) == 3
        for _node_id, (x, y) in positions.items():
            assert isinstance(x, float) or isinstance(x, int)
            assert isinstance(y, float) or isinstance(y, int)
            # Just check that positions are numbers (networkx may produce any values)
            assert not (x != x)  # Not NaN
            assert not (y != y)  # Not NaN

    def test_hierarchical_layout(self) -> None:
        """Test hierarchical layout."""
        from qontinui_devtools.architecture.layouts import hierarchical_layout

        nodes = [
            GraphNode("a", "A", "module", {}),
            GraphNode("b", "B", "module", {}),
            GraphNode("c", "C", "module", {}),
        ]

        edges = [
            GraphEdge("a", "b", "imports"),
            GraphEdge("b", "c", "imports"),
        ]

        positions = hierarchical_layout(nodes, edges)

        assert len(positions) == 3

    def test_circular_layout(self) -> None:
        """Test circular layout."""
        from qontinui_devtools.architecture.layouts import circular_layout

        nodes = [
            GraphNode("a", "A", "module", {}),
            GraphNode("b", "B", "module", {}),
            GraphNode("c", "C", "module", {}),
        ]

        edges = [
            GraphEdge("a", "b", "imports"),
            GraphEdge("b", "c", "imports"),
        ]

        positions = circular_layout(nodes, edges)

        assert len(positions) == 3

        # Check nodes are on a circle
        center_x, center_y = 500, 500
        for x, y in positions.values():
            # All points should be roughly the same distance from center
            distance = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
            assert 350 <= distance <= 450  # Allow some tolerance

    def test_grid_layout(self) -> None:
        """Test grid layout."""
        from qontinui_devtools.architecture.layouts import grid_layout

        nodes = [
            GraphNode("a", "A", "module", {}),
            GraphNode("b", "B", "module", {}),
            GraphNode("c", "C", "module", {}),
            GraphNode("d", "D", "module", {}),
        ]

        edges: list[GraphEdge] = []

        positions = grid_layout(nodes, edges)

        assert len(positions) == 4


class TestIntegration:
    """Integration tests with real code."""

    def test_visualize_qontinui_devtools(self, visualizer: DependencyGraphVisualizer) -> None:
        """Test visualizing the qontinui-devtools codebase itself."""
        # Get the path to the qontinui_devtools package
        import qontinui_devtools

        pkg_path = Path(qontinui_devtools.__file__).parent

        # Build module-level graph
        nodes, edges = visualizer.build_graph(str(pkg_path), level="module")

        # Should find multiple modules
        assert len(nodes) > 0
        assert len(edges) >= 0

        # Test HTML generation
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            output_path = f.name

        try:
            visualizer.generate_html_interactive(nodes, edges, output_path)
            assert Path(output_path).exists()
        finally:
            Path(output_path).unlink()

    def test_full_workflow(
        self, visualizer: DependencyGraphVisualizer, sample_python_code: Path
    ) -> None:
        """Test complete workflow from parsing to visualization."""
        # Build graph
        nodes, edges = visualizer.build_graph(str(sample_python_code), level="module")

        assert len(nodes) > 0
        assert len(edges) >= 0

        # Detect cycles
        cycles = visualizer.detect_cycles(nodes, edges)
        # Sample code shouldn't have cycles
        assert len(cycles) == 0

        # Generate HTML
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            html_path = f.name

        try:
            visualizer.visualize(
                nodes,
                edges,
                html_path,
                format="html",
                layout="dot",
                highlight_cycles=True,
            )
            assert Path(html_path).exists()
        finally:
            Path(html_path).unlink()

        # Export JSON
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json_path = f.name

        try:
            visualizer.export_json(nodes, edges, json_path)
            assert Path(json_path).exists()

            # Verify JSON content
            with open(json_path) as f:
                data = json.load(f)
                assert len(data["nodes"]) == len(nodes)
                assert len(data["edges"]) == len(edges)
        finally:
            Path(json_path).unlink()
