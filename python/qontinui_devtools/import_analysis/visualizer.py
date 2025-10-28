"""
Visualization tools for import graphs.

This module provides utilities to generate visual representations of import
graphs using Graphviz, with support for highlighting circular dependencies.
"""

import os
from typing import Optional, Literal
from pathlib import Path

from .import_tracer import ImportGraph


LayoutType = Literal["dot", "neato", "fdp", "sfdp", "circo", "twopi"]


def visualize_import_graph(
    graph: ImportGraph,
    output_path: str,
    highlight_cycles: bool = True,
    layout: LayoutType = "dot",
    title: Optional[str] = None,
    max_nodes: Optional[int] = None,
    exclude_stdlib: bool = True,
) -> None:
    """Generate a visual representation of an import graph.

    This function creates a DOT file and optionally renders it to an image
    using Graphviz. Circular dependencies can be highlighted in red.

    Args:
        graph: ImportGraph instance to visualize
        output_path: Path where the output file should be saved
            (extension determines format: .png, .svg, .pdf, .dot)
        highlight_cycles: If True, highlight circular dependencies in red
        layout: Graphviz layout algorithm to use:
            - "dot": Hierarchical (default, best for most cases)
            - "neato": Spring model
            - "fdp": Force-directed
            - "sfdp": Scalable force-directed (good for large graphs)
            - "circo": Circular layout
            - "twopi": Radial layout
        title: Optional title for the graph
        max_nodes: Maximum number of nodes to include (None for unlimited)
        exclude_stdlib: If True, exclude standard library modules

    Raises:
        ImportError: If graphviz is not installed
        ValueError: If output format is not supported
    """
    try:
        import graphviz
    except ImportError as e:
        raise ImportError(
            "graphviz package is required for visualization. "
            "Install with: pip install graphviz"
        ) from e

    output_path_obj = Path(output_path)
    extension = output_path_obj.suffix.lower()

    # Determine format and whether to render
    if extension == ".dot":
        # Just save DOT file
        format_type = None
        render = False
    elif extension in {".png", ".svg", ".pdf", ".jpg", ".jpeg"}:
        format_type = extension[1:]  # Remove leading dot
        render = True
    else:
        raise ValueError(
            f"Unsupported output format: {extension}. "
            "Supported formats: .dot, .png, .svg, .pdf, .jpg"
        )

    # Create Graphviz digraph
    dot = graphviz.Digraph(
        comment=title or "Import Graph",
        engine=layout,
        format=format_type,
    )

    # Set graph attributes
    dot.attr(rankdir="LR", concentrate="true")
    dot.attr("node", shape="box", style="rounded,filled", fillcolor="lightblue")
    dot.attr("edge", color="gray")

    if title:
        dot.attr(label=title, fontsize="20", labelloc="t")

    # Get all modules
    all_modules = graph.get_all_modules()

    # Filter modules if needed
    modules_to_include = all_modules.copy()

    if exclude_stdlib:
        # Common patterns for stdlib modules
        stdlib_patterns = {
            "sys", "os", "re", "time", "json", "collections", "typing",
            "dataclasses", "pathlib", "threading", "multiprocessing",
            "unittest", "logging", "argparse", "subprocess", "shutil",
            "tempfile", "io", "contextlib", "functools", "itertools",
            "operator", "copy", "pickle", "urllib", "http", "email",
            "html", "xml", "csv", "sqlite3", "hashlib", "hmac", "secrets",
            "uuid", "datetime", "calendar", "abc", "enum", "traceback",
            "warnings", "inspect", "importlib", "pkgutil", "ast",
        }
        modules_to_include = {
            m for m in modules_to_include
            if not any(m.startswith(s) for s in stdlib_patterns)
        }

    # Limit number of nodes if specified
    if max_nodes and len(modules_to_include) > max_nodes:
        # Keep most connected nodes
        node_degrees = {
            node: len(graph.get_dependencies(node))
            for node in modules_to_include
        }
        sorted_nodes = sorted(node_degrees.items(), key=lambda x: x[1], reverse=True)
        modules_to_include = {node for node, _ in sorted_nodes[:max_nodes]}

    # Find cycles if highlighting
    cycles_set = set()
    cycles_edges = set()
    if highlight_cycles:
        cycles = graph.find_circular_paths()
        for cycle in cycles:
            # Add all nodes in cycle
            cycles_set.update(cycle)
            # Add all edges in cycle
            for i in range(len(cycle) - 1):
                cycles_edges.add((cycle[i], cycle[i + 1]))

    # Add nodes
    for module in modules_to_include:
        if module in cycles_set:
            dot.node(module, module, fillcolor="salmon", color="red", penwidth="2")
        else:
            dot.node(module, module)

    # Add edges
    for source in modules_to_include:
        targets = graph.get_dependencies(source)
        for target in targets:
            if target in modules_to_include:
                edge_tuple = (source, target)
                if edge_tuple in cycles_edges:
                    dot.edge(source, target, color="red", penwidth="2")
                else:
                    dot.edge(source, target)

    # Render or save
    if render:
        # Render to image file
        output_without_ext = str(output_path_obj.with_suffix(""))
        dot.render(output_without_ext, cleanup=True)
    else:
        # Save DOT file
        with open(output_path, "w") as f:
            f.write(dot.source)


def generate_html_report(
    graph: ImportGraph,
    output_path: str,
    circular_deps: list[list[str]],
    title: str = "Import Analysis Report",
) -> None:
    """Generate an interactive HTML report of the import graph.

    Args:
        graph: ImportGraph instance to visualize
        output_path: Path where HTML file should be saved
        circular_deps: List of circular dependency paths
        title: Title for the report
    """
    try:
        import json
    except ImportError:
        # json is stdlib, should never fail
        raise

    # Convert graph to JSON
    graph_data = graph.to_dict()

    # Create HTML with embedded D3.js visualization
    html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
        }}
        h1 {{
            color: #333;
        }}
        .circular-deps {{
            background-color: #ffe6e6;
            border: 2px solid #ff4444;
            border-radius: 5px;
            padding: 15px;
            margin: 20px 0;
        }}
        .circular-deps h2 {{
            color: #cc0000;
            margin-top: 0;
        }}
        .cycle {{
            font-family: monospace;
            margin: 10px 0;
            padding: 5px;
            background-color: white;
            border-radius: 3px;
        }}
        #graph {{
            border: 1px solid #ccc;
            margin: 20px 0;
        }}
        .node {{
            cursor: pointer;
        }}
        .node circle {{
            fill: #69b3a2;
            stroke: #333;
            stroke-width: 2px;
        }}
        .node.cycle-node circle {{
            fill: #ff4444;
            stroke: #cc0000;
        }}
        .node text {{
            font-size: 12px;
            font-family: monospace;
        }}
        .link {{
            stroke: #999;
            stroke-opacity: 0.6;
            stroke-width: 2px;
            fill: none;
        }}
        .link.cycle-link {{
            stroke: #ff4444;
            stroke-width: 3px;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>

    {circular_section}

    <h2>Import Graph</h2>
    <svg id="graph" width="1200" height="800"></svg>

    <script>
        const graphData = {graph_json};
        const cycles = {cycles_json};

        // Create set of nodes and edges in cycles
        const cycleNodes = new Set();
        const cycleEdges = new Set();
        cycles.forEach(cycle => {{
            cycle.forEach(node => cycleNodes.add(node));
            for (let i = 0; i < cycle.length - 1; i++) {{
                cycleEdges.add(`${{cycle[i]}}->${{cycle[i+1]}}`);
            }}
        }});

        // Prepare data for D3
        const nodes = graphData.nodes.map(name => ({{
            id: name,
            name: name,
            inCycle: cycleNodes.has(name)
        }}));

        const links = graphData.edges.map(edge => ({{
            source: edge.source,
            target: edge.target,
            inCycle: cycleEdges.has(`${{edge.source}}->${{edge.target}}`)
        }}));

        // Set up SVG
        const svg = d3.select("#graph");
        const width = 1200;
        const height = 800;

        // Create force simulation
        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(50));

        // Create arrow markers
        svg.append("defs").selectAll("marker")
            .data(["arrow", "arrow-cycle"])
            .enter().append("marker")
            .attr("id", d => d)
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 25)
            .attr("refY", 0)
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .attr("orient", "auto")
            .append("path")
            .attr("d", "M0,-5L10,0L0,5")
            .attr("fill", d => d === "arrow-cycle" ? "#ff4444" : "#999");

        // Create links
        const link = svg.append("g")
            .selectAll("path")
            .data(links)
            .enter().append("path")
            .attr("class", d => d.inCycle ? "link cycle-link" : "link")
            .attr("marker-end", d => d.inCycle ? "url(#arrow-cycle)" : "url(#arrow)");

        // Create nodes
        const node = svg.append("g")
            .selectAll("g")
            .data(nodes)
            .enter().append("g")
            .attr("class", d => d.inCycle ? "node cycle-node" : "node")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

        node.append("circle")
            .attr("r", 8);

        node.append("text")
            .attr("dx", 12)
            .attr("dy", 4)
            .text(d => d.name);

        // Update positions on simulation tick
        simulation.on("tick", () => {{
            link.attr("d", d => {{
                const dx = d.target.x - d.source.x;
                const dy = d.target.y - d.source.y;
                const dr = Math.sqrt(dx * dx + dy * dy);
                return `M${{d.source.x}},${{d.source.y}}A${{dr}},${{dr}} 0 0,1 ${{d.target.x}},${{d.target.y}}`;
            }});

            node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
        }});

        function dragstarted(event, d) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }}

        function dragged(event, d) {{
            d.fx = event.x;
            d.fy = event.y;
        }}

        function dragended(event, d) {{
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }}
    </script>
</body>
</html>
"""

    # Generate circular dependencies section
    if circular_deps:
        circular_html = '<div class="circular-deps">\n'
        circular_html += '<h2>⚠️ Circular Dependencies Detected</h2>\n'
        for i, cycle in enumerate(circular_deps, 1):
            cycle_str = " → ".join(cycle)
            circular_html += f'<div class="cycle">{i}. {cycle_str}</div>\n'
        circular_html += '</div>\n'
    else:
        circular_html = '<div style="background-color: #e6ffe6; padding: 15px; border-radius: 5px;">\n'
        circular_html += '<h2 style="color: #006600;">✓ No Circular Dependencies</h2>\n'
        circular_html += '</div>\n'

    # Fill in template
    html_content = html_template.format(
        title=title,
        circular_section=circular_html,
        graph_json=json.dumps(graph_data),
        cycles_json=json.dumps(circular_deps),
    )

    # Write to file
    with open(output_path, "w") as f:
        f.write(html_content)
