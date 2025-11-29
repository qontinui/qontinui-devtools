"""Interactive dependency graph visualizer for code architecture."""

import ast
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import networkx as nx


@dataclass
class GraphNode:
    """A node in the dependency graph."""

    id: str
    label: str
    node_type: str  # "module", "class", "function"
    metrics: dict[str, Any]  # Coupling, complexity, etc.
    color: str | None = None
    size: int | None = None
    package: str = ""  # For filtering by package

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class GraphEdge:
    """An edge in the dependency graph."""

    source: str
    target: str
    edge_type: str  # "imports", "inherits", "calls"
    weight: int = 1

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class DependencyGraphVisualizer:
    """Create visualizations of dependency graphs."""

    def __init__(self, verbose: bool = False) -> None:
        """Initialize the visualizer.

        Args:
            verbose: Whether to print progress messages
        """
        self.verbose = verbose
        self.graph = nx.DiGraph()

    def _log(self, message: str) -> None:
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            print(f"[GraphVisualizer] {message}")

    def build_graph(
        self, path: str, level: str = "module"
    ) -> tuple[list[GraphNode], list[GraphEdge]]:
        """Build a dependency graph from a Python codebase.

        Args:
            path: Path to the codebase
            level: Level of detail - "module", "class", or "function"

        Returns:
            Tuple of (nodes, edges)
        """
        self._log(f"Building {level}-level graph from {path}")

        path_obj = Path(path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Path not found: {path}")

        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []

        if level == "module":
            nodes, edges = self._build_module_graph(path_obj)
        elif level == "class":
            nodes, edges = self._build_class_graph(path_obj)
        elif level == "function":
            nodes, edges = self._build_function_graph(path_obj)
        else:
            raise ValueError(f"Invalid level: {level}. Choose 'module', 'class', or 'function'")

        self._log(f"Built graph with {len(nodes)} nodes and {len(edges)} edges")
        return nodes, edges

    def _build_module_graph(self, path: Path) -> tuple[list[GraphNode], list[GraphEdge]]:
        """Build a module-level dependency graph."""
        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []
        module_imports: dict[str, set[str]] = {}

        # Find all Python files
        if path.is_file():
            python_files = [path]
        else:
            python_files = list(path.rglob("*.py"))

        self._log(f"Found {len(python_files)} Python files")

        # Parse each file to extract imports
        for file_path in python_files:
            if file_path.name == "__pycache__":
                continue

            module_name = self._get_module_name(file_path, path)
            if not module_name:
                continue

            try:
                with open(file_path, encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=str(file_path))

                imports = self._extract_imports(tree, path)
                module_imports[module_name] = imports

            except (SyntaxError, UnicodeDecodeError) as e:
                self._log(f"Error parsing {file_path}: {e}")
                continue

        # Create nodes
        for module_name in module_imports:
            package = module_name.rsplit(".", 1)[0] if "." in module_name else ""
            nodes.append(
                GraphNode(
                    id=module_name,
                    label=module_name.split(".")[-1],
                    node_type="module",
                    metrics={"imports": len(module_imports[module_name])},
                    package=package,
                )
            )

        # Create edges
        for source_module, imported_modules in module_imports.items():
            for target_module in imported_modules:
                # Only include edges between modules in the graph
                if target_module in module_imports:
                    edges.append(
                        GraphEdge(
                            source=source_module,
                            target=target_module,
                            edge_type="imports",
                            weight=1,
                        )
                    )

        # Calculate metrics
        self._calculate_node_metrics(nodes, edges)

        return nodes, edges

    def _build_class_graph(self, path: Path) -> tuple[list[GraphNode], list[GraphEdge]]:
        """Build a class-level dependency graph."""
        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []
        class_info: dict[str, dict[str, Any]] = {}

        # Find all Python files
        if path.is_file():
            python_files = [path]
        else:
            python_files = list(path.rglob("*.py"))

        # Parse each file to extract classes
        for file_path in python_files:
            if file_path.name == "__pycache__":
                continue

            module_name = self._get_module_name(file_path, path)
            if not module_name:
                continue

            try:
                with open(file_path, encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=str(file_path))

                classes = self._extract_classes(tree, module_name)
                class_info.update(classes)

            except (SyntaxError, UnicodeDecodeError) as e:
                self._log(f"Error parsing {file_path}: {e}")
                continue

        # Create nodes
        for class_id, info in class_info.items():
            nodes.append(
                GraphNode(
                    id=class_id,
                    label=info["name"],
                    node_type="class",
                    metrics={"methods": info["methods"]},
                    package=info["module"],
                )
            )

        # Create edges for inheritance
        for class_id, info in class_info.items():
            for base in info["bases"]:
                # Check if base class is in our graph
                base_id = f"{info['module']}.{base}"
                if base_id in class_info:
                    edges.append(
                        GraphEdge(source=class_id, target=base_id, edge_type="inherits", weight=1)
                    )

        self._calculate_node_metrics(nodes, edges)

        return nodes, edges

    def _build_function_graph(self, path: Path) -> tuple[list[GraphNode], list[GraphEdge]]:
        """Build a function-level dependency graph."""
        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []
        function_info: dict[str, dict[str, Any]] = {}

        # Find all Python files
        if path.is_file():
            python_files = [path]
        else:
            python_files = list(path.rglob("*.py"))

        # Parse each file to extract functions
        for file_path in python_files:
            if file_path.name == "__pycache__":
                continue

            module_name = self._get_module_name(file_path, path)
            if not module_name:
                continue

            try:
                with open(file_path, encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=str(file_path))

                functions = self._extract_functions(tree, module_name)
                function_info.update(functions)

            except (SyntaxError, UnicodeDecodeError) as e:
                self._log(f"Error parsing {file_path}: {e}")
                continue

        # Create nodes
        for func_id, info in function_info.items():
            nodes.append(
                GraphNode(
                    id=func_id,
                    label=info["name"],
                    node_type="function",
                    metrics={"lines": info["lines"], "calls": len(info["calls"])},
                    package=info["module"],
                )
            )

        # Create edges for function calls
        for func_id, info in function_info.items():
            for called_func in info["calls"]:
                # Check if called function is in our graph
                if called_func in function_info:
                    edges.append(
                        GraphEdge(source=func_id, target=called_func, edge_type="calls", weight=1)
                    )

        self._calculate_node_metrics(nodes, edges)

        return nodes, edges

    def _get_module_name(self, file_path: Path, root_path: Path) -> str:
        """Get the module name from a file path."""
        try:
            relative = file_path.relative_to(root_path)
            parts = list(relative.parts[:-1]) + [relative.stem]
            if parts[-1] == "__init__":
                parts = parts[:-1]
            return ".".join(parts) if parts else ""
        except ValueError:
            return ""

    def _extract_imports(self, tree: ast.AST, root_path: Path) -> set[str]:
        """Extract import statements from an AST."""
        imports: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split(".")[0])

        return imports

    def _extract_classes(self, tree: ast.AST, module_name: str) -> dict[str, dict[str, Any]]:
        """Extract class information from an AST."""
        classes: dict[str, dict[str, Any]] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_id = f"{module_name}.{node.name}"
                bases = [
                    base.id if isinstance(base, ast.Name) else ast.unparse(base)
                    for base in node.bases
                ]
                methods = sum(
                    1
                    for item in node.body
                    if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef)
                )

                classes[class_id] = {
                    "name": node.name,
                    "module": module_name,
                    "bases": bases,
                    "methods": methods,
                }

        return classes

    def _extract_functions(self, tree: ast.AST, module_name: str) -> dict[str, dict[str, Any]]:
        """Extract function information from an AST."""
        functions: dict[str, dict[str, Any]] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                func_id = f"{module_name}.{node.name}"

                # Count lines
                lines = node.end_lineno - node.lineno + 1 if node.end_lineno else 0

                # Extract function calls
                calls: set[str] = set()
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name):
                            calls.add(child.func.id)
                        elif isinstance(child.func, ast.Attribute):
                            calls.add(child.func.attr)

                functions[func_id] = {
                    "name": node.name,
                    "module": module_name,
                    "lines": lines,
                    "calls": list(calls),
                }

        return functions

    def _calculate_node_metrics(self, nodes: list[GraphNode], edges: list[GraphEdge]) -> None:
        """Calculate metrics for nodes based on the graph structure."""
        # Build a networkx graph for analysis
        G = nx.DiGraph()
        for node in nodes:
            G.add_node(node.id)
        for edge in edges:
            G.add_edge(edge.source, edge.target)

        # Calculate metrics
        in_degrees = dict(G.in_degree())
        out_degrees = dict(G.out_degree())

        for node in nodes:
            node.metrics["in_degree"] = in_degrees.get(node.id, 0)
            node.metrics["out_degree"] = out_degrees.get(node.id, 0)
            node.metrics["total_degree"] = node.metrics["in_degree"] + node.metrics["out_degree"]

            # Set size based on importance (total degree)
            node.size = max(10, min(50, node.metrics["total_degree"] * 5))

    def detect_cycles(self, nodes: list[GraphNode], edges: list[GraphEdge]) -> list[list[str]]:
        """Detect circular dependencies in the graph.

        Args:
            nodes: List of graph nodes
            edges: List of graph edges

        Returns:
            List of cycles, where each cycle is a list of node IDs
        """
        G = nx.DiGraph()
        for node in nodes:
            G.add_node(node.id)
        for edge in edges:
            G.add_edge(edge.source, edge.target)

        try:
            cycles = list(nx.simple_cycles(G))
            return cycles
        except Exception as e:
            self._log(f"Error detecting cycles: {e}")
            return []

    def visualize(
        self,
        nodes: list[GraphNode],
        edges: list[GraphEdge],
        output_path: str,
        format: str = "png",
        layout: str = "dot",
        highlight_cycles: bool = True,
    ) -> None:
        """Create a visualization of the dependency graph.

        Args:
            nodes: List of graph nodes
            edges: List of graph edges
            output_path: Path to save the visualization
            format: Output format - "png", "svg", "pdf", or "html"
            layout: Layout algorithm - "dot", "neato", "fdp", "circo"
            highlight_cycles: Whether to highlight circular dependencies
        """
        if format == "html":
            self.generate_html_interactive(nodes, edges, output_path)
        else:
            self._generate_static(nodes, edges, output_path, format, layout, highlight_cycles)

    def _generate_static(
        self,
        nodes: list[GraphNode],
        edges: list[GraphEdge],
        output_path: str,
        format: str,
        layout: str,
        highlight_cycles: bool,
    ) -> None:
        """Generate a static visualization using graphviz."""
        try:
            import graphviz
        except ImportError:
            raise ImportError(
                "graphviz is required for static visualizations. "
                "Install it with: pip install graphviz"
            )

        from .graphviz_gen import generate_dot

        # Detect cycles if requested
        cycles: list[list[str]] = []
        if highlight_cycles:
            cycles = self.detect_cycles(nodes, edges)
            if cycles:
                self._log(f"Found {len(cycles)} circular dependencies")

        # Generate DOT format
        dot_string = generate_dot(
            nodes, edges, title="Dependency Graph", rankdir="TB", cycles=cycles
        )

        # Render using graphviz
        dot = graphviz.Source(dot_string, engine=layout)
        output_file = Path(output_path).stem
        dot.render(output_file, format=format, cleanup=True)

        self._log(f"Saved {format} visualization to {output_path}")

    def generate_html_interactive(
        self, nodes: list[GraphNode], edges: list[GraphEdge], output_path: str
    ) -> None:
        """Generate an interactive HTML visualization.

        Args:
            nodes: List of graph nodes
            edges: List of graph edges
            output_path: Path to save the HTML file
        """
        from .html_graph import generate_html_graph

        html_content = generate_html_graph(nodes, edges, title="Interactive Dependency Graph")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        self._log(f"Saved interactive HTML to {output_path}")

    def apply_layout(
        self, nodes: list[GraphNode], edges: list[GraphEdge], layout: str
    ) -> dict[str, tuple[float, float]]:
        """Apply a layout algorithm to position nodes.

        Args:
            nodes: List of graph nodes
            edges: List of graph edges
            layout: Layout algorithm - "force", "hierarchical", "circular"

        Returns:
            Dictionary mapping node IDs to (x, y) positions
        """
        from .layouts import circular_layout, force_directed_layout, hierarchical_layout

        if layout == "force":
            return force_directed_layout(nodes, edges)
        elif layout == "hierarchical":
            return hierarchical_layout(nodes, edges)
        elif layout == "circular":
            return circular_layout(nodes, edges)
        else:
            raise ValueError(f"Unknown layout: {layout}")

    def export_json(self, nodes: list[GraphNode], edges: list[GraphEdge], output_path: str) -> None:
        """Export the graph to JSON format.

        Args:
            nodes: List of graph nodes
            edges: List of graph edges
            output_path: Path to save the JSON file
        """
        data = {
            "nodes": [node.to_dict() for node in nodes],
            "edges": [edge.to_dict() for edge in edges],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        self._log(f"Exported graph to {output_path}")
