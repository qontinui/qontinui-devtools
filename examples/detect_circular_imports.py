#!/usr/bin/env python3
"""
from typing import Any, Any

Example script demonstrating how to use the ImportTracer to detect
circular dependencies in real-time.

This example shows how the ImportTracer would have caught the circular
dependency issue that caused the freeze with pynput_controller:
    pynput_controller → wrappers → keyboard → factory → pynput_controller

Usage:
    python examples/detect_circular_imports.py
"""

import sys
from pathlib import Path
from typing import Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

from qontinui_devtools.import_analysis import (ImportTracer,
                                               generate_html_report,
                                               visualize_import_graph)


def example_trace_imports() -> Any:
    """Example 1: Trace imports and detect circular dependencies."""
    print("=" * 80)
    print("Example 1: Trace imports from test module")
    print("=" * 80)
    print()

    # Add tests to path
    test_path = Path(__file__).parent.parent / "python" / "tests"
    if str(test_path) not in sys.path:
        sys.path.insert(0, str(test_path))

    with ImportTracer() as tracer:
        try:
            # This will create a circular dependency
            import fixtures.circular_a  # noqa: F401
        except ImportError as e:
            print(f"Note: Circular import may cause ImportError: {e}")

    # Check for circular dependencies
    circular = tracer.find_circular_dependencies()

    if circular:
        print(f"❌ Circular dependencies found: {len(circular)}")
        print()
        for i, cycle in enumerate(circular, 1):
            cycle_str = " → ".join(cycle)
            print(f"  {i}. {cycle_str}")
        print()
    else:
        print("✅ No circular dependencies detected")
        print()

    # Generate report
    print("-" * 80)
    print("Full Report:")
    print("-" * 80)
    report = tracer.generate_report()
    print(report)

    return tracer


def example_visualize_graph(tracer) -> None:
    """Example 2: Generate visualization of import graph."""
    print("=" * 80)
    print("Example 2: Generate import graph visualization")
    print("=" * 80)
    print()

    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)

    # Generate PNG visualization (requires graphviz)
    png_path = output_dir / "import_graph.png"
    try:
        visualize_import_graph(
            tracer.get_graph(),
            str(png_path),
            highlight_cycles=True,
            layout="dot",
            title="Import Dependency Graph",
        )
        print(f"✓ PNG visualization saved to: {png_path}")
    except ImportError:
        print("⚠ Skipping PNG visualization (graphviz Python package not installed)")
        print("  Install with: pip install graphviz")
    except Exception as e:
        if "Graphviz" in str(e) or "dot" in str(e):
            print("⚠ Skipping PNG visualization (graphviz executable not installed)")
            print("  Install graphviz: sudo apt-get install graphviz")
        else:
            print(f"✗ Error generating PNG: {e}")

    # Generate DOT file (always works)
    dot_path = output_dir / "import_graph.dot"
    try:
        visualize_import_graph(
            tracer.get_graph(),
            str(dot_path),
            highlight_cycles=True,
        )
        print(f"✓ DOT file saved to: {dot_path}")
    except Exception as e:
        print(f"✗ Error generating DOT file: {e}")

    # Generate HTML interactive report
    html_path = output_dir / "import_report.html"
    try:
        circular = tracer.find_circular_dependencies()
        generate_html_report(
            tracer.get_graph(),
            str(html_path),
            circular,
            title="Import Analysis Report",
        )
        print(f"✓ HTML report saved to: {html_path}")
        print(f"  Open in browser: file://{html_path.absolute()}")
    except Exception as e:
        print(f"✗ Error generating HTML report: {e}")

    print()


def example_export_data(tracer) -> None:
    """Example 3: Export import data to JSON."""
    print("=" * 80)
    print("Example 3: Export import data")
    print("=" * 80)
    print()

    import json

    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)

    json_path = output_dir / "import_data.json"
    data = tracer.to_dict()

    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✓ Import data exported to: {json_path}")
    print(f"  Total events: {len(data['events'])}")
    print(f"  Circular dependencies: {len(data['circular_dependencies'])}")
    print()


def example_simulated_qontinui_issue() -> None:
    """Example 4: Simulate the pynput_controller circular dependency issue."""
    print("=" * 80)
    print("Example 4: How ImportTracer would catch the pynput_controller issue")
    print("=" * 80)
    print()

    print("The actual circular dependency that caused the freeze was:")
    print("  pynput_controller → wrappers → keyboard → factory → pynput_controller")
    print()

    # Simulate with our test modules
    print("Simulating with test modules (circular_c → circular_d → circular_e → circular_c):")
    print()

    # Remove modules if cached
    for mod in ["fixtures.circular_c", "fixtures.circular_d", "fixtures.circular_e"]:
        if mod in sys.modules:
            del sys.modules[mod]

    with ImportTracer() as tracer:
        try:
            import fixtures.circular_c  # noqa: F401
        except ImportError as e:
            print(f"Note: Circular import detected and prevented: {e}")
            print()

    circular = tracer.find_circular_dependencies()

    if circular:
        print(f"✓ ImportTracer successfully detected {len(circular)} circular dependency!")
        print()
        for cycle in circular:
            if any("circular" in node for node in cycle):
                print("  Detected cycle:")
                for i, node in enumerate(cycle):
                    if i > 0:
                        print("    ↓")
                    print(f"    {node}")
        print()
        print("With this tool, you would have seen this warning BEFORE the freeze!")
    else:
        print("No circular dependencies detected in this run.")

    print()


def example_practical_usage() -> None:
    """Example 5: Practical usage - checking if a module is safe to import."""
    print("=" * 80)
    print("Example 5: Check if a module is safe to import")
    print("=" * 80)
    print()

    print("Use case: Before importing a new module, check for circular dependencies")
    print()

    # Test with a safe module
    print("Checking safe module (simple_module)...")
    for mod in ["fixtures.simple_module"]:
        if mod in sys.modules:
            del sys.modules[mod]

    with ImportTracer() as tracer:
        import fixtures.simple_module  # noqa: F401

    circular = tracer.find_circular_dependencies()
    simple_cycles = [c for c in circular if any("simple_module" in n for n in c)]

    if not simple_cycles:
        print("  ✓ Safe to import - no circular dependencies")
    else:
        print(f"  ⚠ Warning - found {len(simple_cycles)} circular dependencies")

    print()


def main() -> None:
    """Run all examples."""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "IMPORT TRACER EXAMPLES" + " " * 36 + "║")
    print("╚" + "═" * 78 + "╝")
    print()

    # Run examples
    tracer = example_trace_imports()
    example_visualize_graph(tracer)
    example_export_data(tracer)
    example_simulated_qontinui_issue()
    example_practical_usage()

    print("=" * 80)
    print("All examples completed!")
    print("=" * 80)
    print()


if __name__ == "__main__":
    main()
