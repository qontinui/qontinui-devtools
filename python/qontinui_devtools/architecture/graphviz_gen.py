"""Graphviz DOT format generator for dependency graphs."""

from typing import Any

from .graph_visualizer import GraphEdge, GraphNode


def generate_dot(
    nodes: list[GraphNode],
    edges: list[GraphEdge],
    title: str = "Dependency Graph",
    rankdir: str = "TB",
    cycles: list[list[str]] | None = None,
) -> str:
    """Generate Graphviz DOT format string.

    Args:
        nodes: List of graph nodes
        edges: List of graph edges
        title: Graph title
        rankdir: Graph direction - "TB" (top-bottom), "LR" (left-right)
        cycles: List of cycles to highlight in red

    Returns:
        DOT format string
    """
    dot_lines = [
        "digraph DependencyGraph {",
        f'    label="{title}";',
        "    labelloc=t;",
        "    fontsize=20;",
        "    fontname=Helvetica;",
        f"    rankdir={rankdir};",
        "    node [fontname=Helvetica];",
        "    edge [fontname=Helvetica];",
        "",
    ]

    # Build set of edges in cycles
    cycle_edges: set[tuple[str, str]] = set()
    if cycles:
        for cycle in cycles:
            for i in range(len(cycle)):
                source = cycle[i]
                target = cycle[(i + 1) % len(cycle)]
                cycle_edges.add((source, target))

    # Add nodes with styling
    for node in nodes:
        # Ensure node has metrics dictionary
        if not node.metrics:
            node.metrics = {}

        style = apply_styling(node)
        attrs = [
            f'label="{node.label}"',
            f'shape={style["shape"]}',
            f'style={style["style"]}',
            f'fillcolor="{style["fillcolor"]}"',
            f'color="{style["color"]}"',
            f'penwidth={style["penwidth"]}',
        ]

        if node.size:
            # Scale size to reasonable values
            width = node.size / 50
            height = node.size / 50
            attrs.append(f"width={width:.2f}")
            attrs.append(f"height={height:.2f}")

        attrs_str = ", ".join(attrs)
        dot_lines.append(f'    "{node.id}" [{attrs_str}];')

    dot_lines.append("")

    # Add edges
    edge_type_colors = {
        "imports": "#555555",
        "inherits": "#0066cc",
        "calls": "#009900",
    }

    for edge in edges:
        # Check if this edge is part of a cycle
        is_cycle_edge = (edge.source, edge.target) in cycle_edges

        color = "#ff0000" if is_cycle_edge else edge_type_colors.get(edge.edge_type, "#555555")
        penwidth = 2.0 if is_cycle_edge else 1.0
        style = "bold" if is_cycle_edge else "solid"

        attrs = [
            f'color="{color}"',
            f"penwidth={penwidth}",
            f"style={style}",
        ]

        if edge.weight > 1:
            attrs.append(f'label="{edge.weight}"')

        attrs_str = ", ".join(attrs)
        dot_lines.append(f'    "{edge.source}" -> "{edge.target}" [{attrs_str}];')

    dot_lines.append("")

    # Add legend
    legend = create_legend(cycles is not None and len(cycles) > 0)
    dot_lines.append(legend)

    dot_lines.append("}")

    return "\n".join(dot_lines)


def apply_styling(node: GraphNode, metrics: dict[str, Any] | None = None) -> dict[str, str]:
    """Apply visual styling based on node metrics.

    Args:
        node: Graph node to style
        metrics: Optional additional metrics

    Returns:
        Dictionary with styling attributes:
        - color: border color
        - fillcolor: fill color
        - style: node style
        - shape: node shape
        - penwidth: border width
    """
    # Default styles by node type
    type_styles = {
        "module": {
            "shape": "box",
            "style": "filled,rounded",
            "color": "#333333",
            "base_fill": "#e3f2fd",
        },
        "class": {
            "shape": "box",
            "style": "filled",
            "color": "#333333",
            "base_fill": "#fff3e0",
        },
        "function": {
            "shape": "ellipse",
            "style": "filled",
            "color": "#333333",
            "base_fill": "#f1f8e9",
        },
    }

    style = type_styles.get(node.node_type, type_styles["module"]).copy()

    # Set default fillcolor if not present
    if "fillcolor" not in style:
        style["fillcolor"] = style.get("base_fill", "#e3f2fd")
    else:
        style["fillcolor"] = style.get("base_fill", "#e3f2fd")

    # Set default penwidth
    if "penwidth" not in style:
        style["penwidth"] = "1.0"

    # Color based on metrics
    if node.metrics and node.metrics.get("total_degree") is not None:
        total_degree = node.metrics.get("total_degree", 0)

        # High coupling = red tint, low coupling = green tint
        if total_degree > 10:
            style["fillcolor"] = "#ffcdd2"  # Red
            style["penwidth"] = "2.0"
        elif total_degree > 5:
            style["fillcolor"] = "#fff9c4"  # Yellow
            style["penwidth"] = "1.5"
        else:
            style["fillcolor"] = style.get("base_fill", "#e3f2fd")  # Default color
            style["penwidth"] = "1.0"

        # Highlight nodes with high complexity
        if node.metrics.get("methods", 0) > 10 or node.metrics.get("lines", 0) > 100:
            style["color"] = "#d32f2f"
            style["penwidth"] = "2.0"

    # Override with node's custom color if set
    if node.color:
        style["fillcolor"] = node.color

    # Remove base_fill from returned style
    if "base_fill" in style:
        del style["base_fill"]

    return style


def create_legend(show_cycles: bool = False) -> str:
    """Create DOT string for graph legend.

    Args:
        show_cycles: Whether to include cycle highlighting in legend

    Returns:
        DOT string for legend subgraph
    """
    legend_lines = [
        "    subgraph cluster_legend {",
        '        label="Legend";',
        "        fontsize=12;",
        "        style=filled;",
        "        fillcolor=white;",
        "        color=black;",
        "",
        "        // Node types",
        '        legend_module [label="Module", shape=box, style="filled,rounded", fillcolor="#e3f2fd"];',
        '        legend_class [label="Class", shape=box, style=filled, fillcolor="#fff3e0"];',
        '        legend_function [label="Function", shape=ellipse, style=filled, fillcolor="#f1f8e9"];',
        "",
        "        // Edge types",
        '        legend_edge1 [label="", shape=point, width=0];',
        '        legend_edge2 [label="", shape=point, width=0];',
        '        legend_edge1 -> legend_edge2 [label="imports", color="#555555"];',
        "",
        '        legend_edge3 [label="", shape=point, width=0];',
        '        legend_edge4 [label="", shape=point, width=0];',
        '        legend_edge3 -> legend_edge4 [label="inherits", color="#0066cc"];',
        "",
        '        legend_edge5 [label="", shape=point, width=0];',
        '        legend_edge6 [label="", shape=point, width=0];',
        '        legend_edge5 -> legend_edge6 [label="calls", color="#009900"];',
    ]

    if show_cycles:
        legend_lines.extend(
            [
                "",
                "        // Cycles",
                '        legend_edge7 [label="", shape=point, width=0];',
                '        legend_edge8 [label="", shape=point, width=0];',
                '        legend_edge7 -> legend_edge8 [label="cycle", color="#ff0000", penwidth=2.0, style=bold];',
            ]
        )

    legend_lines.extend(
        [
            "",
            "        // Coupling levels",
            '        legend_low [label="Low coupling", shape=box, style=filled, fillcolor="#f1f8e9"];',
            '        legend_med [label="Medium coupling", shape=box, style=filled, fillcolor="#fff9c4"];',
            '        legend_high [label="High coupling", shape=box, style=filled, fillcolor="#ffcdd2"];',
            "",
            "    }",
        ]
    )

    return "\n".join(legend_lines)
