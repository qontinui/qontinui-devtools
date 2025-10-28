#!/usr/bin/env python3
"""Example: Visualize dependency graphs for Python code.

This example demonstrates how to use the DependencyGraphVisualizer to create
beautiful, interactive visualizations of module, class, and function dependencies.
"""

from pathlib import Path
from qontinui_devtools.architecture import DependencyGraphVisualizer


def main():
    """Generate various dependency visualizations."""
    visualizer = DependencyGraphVisualizer(verbose=True)

    # Get path to qontinui-devtools source
    devtools_path = Path(__file__).parent.parent / "python" / "qontinui_devtools"

    print("\n" + "=" * 80)
    print("Dependency Graph Visualizer Demo")
    print("=" * 80)

    # 1. Module-level graph (interactive HTML)
    print("\n1. Building module-level dependency graph...")
    print("-" * 80)
    nodes, edges = visualizer.build_graph(str(devtools_path), level="module")
    print(f"   Found {len(nodes)} modules with {len(edges)} dependencies")

    # Detect cycles
    cycles = visualizer.detect_cycles(nodes, edges)
    if cycles:
        print(f"   ⚠️  Found {len(cycles)} circular dependencies:")
        for i, cycle in enumerate(cycles[:3], 1):  # Show first 3
            print(f"      {i}. {' → '.join(cycle)} → {cycle[0]}")
    else:
        print("   ✅ No circular dependencies detected")

    # Generate interactive HTML
    output_html = Path(__file__).parent / "qontinui_devtools_modules.html"
    visualizer.generate_html_interactive(nodes, edges, str(output_html))
    print(f"   📊 Interactive HTML saved to: {output_html}")

    # 2. Export to JSON for further analysis
    print("\n2. Exporting graph to JSON...")
    print("-" * 80)
    output_json = Path(__file__).parent / "qontinui_devtools_graph.json"
    visualizer.export_json(nodes, edges, str(output_json))
    print(f"   💾 JSON data saved to: {output_json}")

    # 3. Class-level graph
    print("\n3. Building class-level dependency graph...")
    print("-" * 80)
    class_nodes, class_edges = visualizer.build_graph(str(devtools_path), level="class")
    print(f"   Found {len(class_nodes)} classes with {len(class_edges)} relationships")

    # Generate class graph
    output_class_html = Path(__file__).parent / "qontinui_devtools_classes.html"
    visualizer.generate_html_interactive(class_nodes, class_edges, str(output_class_html))
    print(f"   📊 Class graph saved to: {output_class_html}")

    # 4. Function-level graph (might be large)
    print("\n4. Building function-level call graph...")
    print("-" * 80)
    func_nodes, func_edges = visualizer.build_graph(str(devtools_path), level="function")
    print(f"   Found {len(func_nodes)} functions with {len(func_edges)} calls")

    if len(func_nodes) < 200:  # Only generate if not too large
        output_func_html = Path(__file__).parent / "qontinui_devtools_functions.html"
        visualizer.generate_html_interactive(func_nodes, func_edges, str(output_func_html))
        print(f"   📊 Function graph saved to: {output_func_html}")
    else:
        print(f"   ⚠️  Function graph too large ({len(func_nodes)} nodes), skipping HTML generation")

    # 5. Apply different layouts
    print("\n5. Testing layout algorithms...")
    print("-" * 80)

    layouts_to_test = ["force", "hierarchical", "circular"]
    for layout in layouts_to_test:
        positions = visualizer.apply_layout(nodes, edges, layout)
        print(f"   ✓ {layout.capitalize()} layout: positioned {len(positions)} nodes")

    # 6. Generate static visualization (if graphviz is available)
    print("\n6. Attempting static visualization (requires graphviz)...")
    print("-" * 80)
    try:
        import graphviz

        output_png = Path(__file__).parent / "qontinui_devtools_modules.png"
        visualizer.visualize(
            nodes,
            edges,
            str(output_png),
            format="png",
            layout="dot",
            highlight_cycles=True,
        )
        print(f"   📊 PNG visualization saved to: {output_png}")

        output_svg = Path(__file__).parent / "qontinui_devtools_modules.svg"
        visualizer.visualize(
            nodes,
            edges,
            str(output_svg),
            format="svg",
            layout="neato",
            highlight_cycles=True,
        )
        print(f"   📊 SVG visualization saved to: {output_svg}")
    except ImportError:
        print("   ⚠️  Graphviz Python package not installed, skipping static visualizations")
        print("   💡 Install with: pip install graphviz")
    except Exception as e:
        print(f"   ⚠️  Graphviz binaries not found on system PATH, skipping static visualizations")
        print("   💡 Install graphviz system package (apt install graphviz / brew install graphviz)")
        print(f"   Error: {e}")

    # Summary
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Generated visualizations in: {Path(__file__).parent}")
    print("\nInteractive HTML files:")
    print(f"  - {output_html.name} (module dependencies)")
    print(f"  - {output_class_html.name} (class relationships)")
    if len(func_nodes) < 200:
        print(f"  - {output_func_html.name} (function calls)")
    print(f"\nJSON export:")
    print(f"  - {output_json.name}")
    print("\n💡 Open the HTML files in your browser to:")
    print("   - Zoom and pan around the graph")
    print("   - Click nodes to see details and metrics")
    print("   - Search for specific modules/classes")
    print("   - Filter by type or edge relationships")
    print("   - Export as SVG")
    print()


if __name__ == "__main__":
    main()
