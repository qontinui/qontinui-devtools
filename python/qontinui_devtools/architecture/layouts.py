"""Custom layout algorithms for dependency graphs."""

import math
from typing import Any
import networkx as nx
from .graph_visualizer import GraphNode, GraphEdge


def force_directed_layout(
    nodes: list[GraphNode],
    edges: list[GraphEdge],
    iterations: int = 100,
    width: float = 1000.0,
    height: float = 1000.0,
) -> dict[str, tuple[float, float]]:
    """Simple force-directed layout algorithm using Fruchterman-Reingold.

    Args:
        nodes: List of graph nodes
        edges: List of graph edges
        iterations: Number of iterations to run
        width: Canvas width
        height: Canvas height

    Returns:
        Dictionary mapping node IDs to (x, y) positions
    """
    # Build networkx graph
    G = nx.DiGraph()
    for node in nodes:
        G.add_node(node.id)
    for edge in edges:
        G.add_edge(edge.source, edge.target)

    # Use networkx's spring layout (Fruchterman-Reingold)
    pos = nx.spring_layout(G, k=2 / math.sqrt(len(nodes)), iterations=iterations, scale=min(width, height) / 2)

    # Scale to canvas size and center
    result: dict[str, tuple[float, float]] = {}
    for node_id, (x, y) in pos.items():
        result[node_id] = (
            x * width / 2 + width / 2,
            y * height / 2 + height / 2,
        )

    return result


def hierarchical_layout(
    nodes: list[GraphNode],
    edges: list[GraphEdge],
    width: float = 1000.0,
    height: float = 1000.0,
) -> dict[str, tuple[float, float]]:
    """Hierarchical layout (top-down) using topological sort.

    Args:
        nodes: List of graph nodes
        edges: List of graph edges
        width: Canvas width
        height: Canvas height

    Returns:
        Dictionary mapping node IDs to (x, y) positions
    """
    # Build networkx graph
    G = nx.DiGraph()
    for node in nodes:
        G.add_node(node.id)
    for edge in edges:
        G.add_edge(edge.source, edge.target)

    # Try to use topological sort for DAGs
    try:
        # For DAGs, use topological generations
        layers = list(nx.topological_generations(G))
    except nx.NetworkXError:
        # For cyclic graphs, use longest path heuristic
        layers = _assign_layers_cyclic(G)

    result: dict[str, tuple[float, float]] = {}

    # Position nodes layer by layer
    layer_height = height / (len(layers) + 1)

    for i, layer in enumerate(layers):
        y = (i + 1) * layer_height
        layer_width = width / (len(layer) + 1)

        for j, node_id in enumerate(sorted(layer)):
            x = (j + 1) * layer_width
            result[node_id] = (x, y)

    return result


def _assign_layers_cyclic(G: nx.DiGraph) -> list[list[str]]:
    """Assign layers to nodes in a cyclic graph using heuristic.

    Args:
        G: NetworkX directed graph

    Returns:
        List of layers, where each layer is a list of node IDs
    """
    # Start with nodes that have no incoming edges
    layers: list[list[str]] = []
    remaining = set(G.nodes())
    in_degree = dict(G.in_degree())

    while remaining:
        # Find nodes with minimum in-degree from remaining nodes
        current_layer = [
            node for node in remaining if in_degree[node] == min(in_degree[n] for n in remaining)
        ]

        if not current_layer:
            # Fallback: just take any remaining nodes
            current_layer = list(remaining)

        layers.append(current_layer)

        # Remove current layer from remaining
        remaining -= set(current_layer)

        # Update in-degrees (remove edges from current layer)
        for node in current_layer:
            for successor in G.successors(node):
                if successor in remaining:
                    in_degree[successor] -= 1

    return layers


def circular_layout(
    nodes: list[GraphNode],
    edges: list[GraphEdge],
    width: float = 1000.0,
    height: float = 1000.0,
) -> dict[str, tuple[float, float]]:
    """Circular layout placing nodes evenly on a circle.

    Args:
        nodes: List of graph nodes
        edges: List of graph edges
        width: Canvas width
        height: Canvas height

    Returns:
        Dictionary mapping node IDs to (x, y) positions
    """
    result: dict[str, tuple[float, float]] = {}

    n = len(nodes)
    if n == 0:
        return result

    # Calculate radius to fit in canvas
    radius = min(width, height) * 0.4
    center_x = width / 2
    center_y = height / 2

    # Place nodes evenly on circle
    for i, node in enumerate(nodes):
        angle = 2 * math.pi * i / n
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        result[node.id] = (x, y)

    return result


def tree_layout(
    nodes: list[GraphNode],
    edges: list[GraphEdge],
    width: float = 1000.0,
    height: float = 1000.0,
    root: str | None = None,
) -> dict[str, tuple[float, float]]:
    """Tree layout for hierarchical structures.

    Args:
        nodes: List of graph nodes
        edges: List of graph edges
        width: Canvas width
        height: Canvas height
        root: Root node ID (if None, will find a suitable root)

    Returns:
        Dictionary mapping node IDs to (x, y) positions
    """
    # Build networkx graph
    G = nx.DiGraph()
    for node in nodes:
        G.add_node(node.id)
    for edge in edges:
        G.add_edge(edge.source, edge.target)

    # Find root if not specified
    if root is None:
        # Find node with no incoming edges
        candidates = [n for n in G.nodes() if G.in_degree(n) == 0]
        if candidates:
            root = candidates[0]
        else:
            # Just pick the first node
            root = list(G.nodes())[0] if G.nodes() else None

    if root is None:
        return {}

    # Use networkx's tree layout
    try:
        # Try to create a tree from the graph
        tree = nx.bfs_tree(G, root)
        pos = nx.drawing.nx_agraph.graphviz_layout(tree, prog="dot")
    except Exception:
        # Fallback to hierarchical layout
        return hierarchical_layout(nodes, edges, width, height)

    # Scale positions to canvas
    if not pos:
        return {}

    # Find bounds
    xs = [x for x, y in pos.values()]
    ys = [y for x, y in pos.values()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    # Avoid division by zero
    x_range = max_x - min_x if max_x != min_x else 1
    y_range = max_y - min_y if max_y != min_y else 1

    # Scale and center
    result: dict[str, tuple[float, float]] = {}
    margin = 50
    for node_id, (x, y) in pos.items():
        scaled_x = ((x - min_x) / x_range) * (width - 2 * margin) + margin
        scaled_y = ((y - min_y) / y_range) * (height - 2 * margin) + margin
        result[node_id] = (scaled_x, scaled_y)

    return result


def radial_layout(
    nodes: list[GraphNode],
    edges: list[GraphEdge],
    width: float = 1000.0,
    height: float = 1000.0,
    root: str | None = None,
) -> dict[str, tuple[float, float]]:
    """Radial layout placing nodes in concentric circles by distance from root.

    Args:
        nodes: List of graph nodes
        edges: List of graph edges
        width: Canvas width
        height: Canvas height
        root: Root node ID (if None, will find a suitable root)

    Returns:
        Dictionary mapping node IDs to (x, y) positions
    """
    # Build networkx graph
    G = nx.DiGraph()
    for node in nodes:
        G.add_node(node.id)
    for edge in edges:
        G.add_edge(edge.source, edge.target)

    # Find root if not specified
    if root is None:
        candidates = [n for n in G.nodes() if G.in_degree(n) == 0]
        if candidates:
            root = candidates[0]
        else:
            root = list(G.nodes())[0] if G.nodes() else None

    if root is None:
        return {}

    # Calculate distances from root using BFS
    try:
        distances = nx.single_source_shortest_path_length(G.to_undirected(), root)
    except nx.NetworkXError:
        # Fallback to circular layout
        return circular_layout(nodes, edges, width, height)

    # Group nodes by distance
    max_distance = max(distances.values()) if distances else 0
    layers: dict[int, list[str]] = {i: [] for i in range(max_distance + 1)}
    for node_id, dist in distances.items():
        layers[dist].append(node_id)

    # Place nodes
    result: dict[str, tuple[float, float]] = {}
    center_x = width / 2
    center_y = height / 2
    max_radius = min(width, height) * 0.4

    for dist, layer_nodes in layers.items():
        if dist == 0:
            # Place root at center
            result[layer_nodes[0]] = (center_x, center_y)
        else:
            # Place nodes on a circle
            radius = (dist / max_distance) * max_radius
            n = len(layer_nodes)
            for i, node_id in enumerate(layer_nodes):
                angle = 2 * math.pi * i / n
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                result[node_id] = (x, y)

    return result


def grid_layout(
    nodes: list[GraphNode],
    edges: list[GraphEdge],
    width: float = 1000.0,
    height: float = 1000.0,
) -> dict[str, tuple[float, float]]:
    """Grid layout placing nodes in a regular grid.

    Args:
        nodes: List of graph nodes
        edges: List of graph edges
        width: Canvas width
        height: Canvas height

    Returns:
        Dictionary mapping node IDs to (x, y) positions
    """
    n = len(nodes)
    if n == 0:
        return {}

    # Calculate grid dimensions
    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)

    result: dict[str, tuple[float, float]] = {}

    cell_width = width / (cols + 1)
    cell_height = height / (rows + 1)

    for i, node in enumerate(nodes):
        row = i // cols
        col = i % cols
        x = (col + 1) * cell_width
        y = (row + 1) * cell_height
        result[node.id] = (x, y)

    return result
