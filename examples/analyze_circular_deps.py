#!/usr/bin/env python3
"""Example script demonstrating the Circular Dependency Detector.

This script shows how to use the CircularDependencyDetector to analyze
Python projects for circular import dependencies.
"""

import sys
from pathlib import Path

from qontinui_devtools.import_analysis import CircularDependencyDetector


def analyze_project(project_path: str) -> None:
    """Analyze a project for circular dependencies.

    Args:
        project_path: Path to the Python project to analyze
    """
    print(f"Analyzing project: {project_path}\n")
    print("=" * 80)

    # Create detector with verbose output
    detector = CircularDependencyDetector(project_path, verbose=True)

    # Run analysis
    circular_deps = detector.analyze()

    print("\n" + "=" * 80)
    print("\nAnalysis Results:")
    print("=" * 80)

    if circular_deps:
        print(f"\n❌ Found {len(circular_deps)} circular dependencies:\n")

        for i, dep in enumerate(circular_deps, 1):
            print(f"\nCircular Dependency #{i}")
            print(f"Severity: {dep.severity.upper()}")
            print(f"Cycle: {' → '.join(dep.cycle)}")
            print(f"\nFix Type: {dep.suggestion.fix_type}")
            print(f"Description: {dep.suggestion.description}")

            if dep.suggestion.code_example:
                print("\nExample Fix:")
                print("-" * 40)
                print(dep.suggestion.code_example)
                print("-" * 40)

            print("\nAffected Files:")
            for file_path in dep.suggestion.affected_files:
                try:
                    rel_path = Path(file_path).relative_to(Path(project_path).resolve())
                    print(f"  - {rel_path}")
                except ValueError:
                    print(f"  - {file_path}")

            print("\nImport Chain:")
            for imp in dep.import_chain:
                try:
                    rel_path = Path(imp.file_path).relative_to(Path(project_path).resolve())
                    print(f"  {rel_path}:{imp.line_number} - {imp}")
                except ValueError:
                    print(f"  {imp.file_path}:{imp.line_number} - {imp}")

            print("\n" + "-" * 80)

    else:
        print("\n✅ No circular dependencies found!")

    # Display statistics
    stats = detector.get_statistics()
    print("\nStatistics:")
    print(f"  Files scanned: {stats['total_files']}")
    print(f"  Total modules: {stats['total_modules']}")
    print(f"  Total imports: {stats['total_imports']}")
    print(f"  Total dependencies: {stats['total_dependencies']}")
    print(f"  Circular dependencies: {stats['cycles_found']}")

    if stats['severity_breakdown']:
        print("\n  Severity Breakdown:")
        for severity, count in stats['severity_breakdown'].items():
            if count > 0:
                print(f"    {severity.capitalize()}: {count}")


def save_report_to_file(project_path: str, output_file: str) -> None:
    """Analyze project and save report to file.

    Args:
        project_path: Path to the Python project to analyze
        output_file: Path to save the report
    """
    print(f"Analyzing project: {project_path}")
    print(f"Output file: {output_file}\n")

    # Create detector
    detector = CircularDependencyDetector(project_path, verbose=True)

    # Run analysis
    circular_deps = detector.analyze()

    # Generate and save report
    report = detector.generate_report(circular_deps)

    Path(output_file).write_text(report)
    print(f"\n✅ Report saved to: {output_file}")


def analyze_with_graph_export(project_path: str, graph_file: str) -> None:
    """Analyze project and export dependency graph.

    Args:
        project_path: Path to the Python project to analyze
        graph_file: Path to save the graph (e.g., 'deps.json', 'deps.gml')
    """
    print(f"Analyzing project: {project_path}")
    print(f"Graph output: {graph_file}\n")

    # Create detector
    detector = CircularDependencyDetector(project_path, verbose=True)

    # Run analysis
    circular_deps = detector.analyze()

    # Export graph
    detector.export_graph(graph_file)
    print(f"\n✅ Dependency graph exported to: {graph_file}")

    # Show results
    if circular_deps:
        print(f"\n❌ Found {len(circular_deps)} circular dependencies")
    else:
        print("\n✅ No circular dependencies found")


def main() -> None:
    """Main entry point for the example script."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python analyze_circular_deps.py <project_path>")
        print("  python analyze_circular_deps.py <project_path> --output report.txt")
        print("  python analyze_circular_deps.py <project_path> --graph deps.json")
        print("\nExamples:")
        print("  # Analyze qontinui source code")
        print("  python analyze_circular_deps.py /path/to/qontinui/src")
        print()
        print("  # Save report to file")
        print("  python analyze_circular_deps.py /path/to/qontinui/src --output report.txt")
        print()
        print("  # Export dependency graph")
        print("  python analyze_circular_deps.py /path/to/qontinui/src --graph deps.json")
        sys.exit(1)

    project_path = sys.argv[1]

    if not Path(project_path).exists():
        print(f"Error: Path does not exist: {project_path}")
        sys.exit(1)

    # Check for options
    if len(sys.argv) >= 4 and sys.argv[2] == "--output":
        save_report_to_file(project_path, sys.argv[3])
    elif len(sys.argv) >= 4 and sys.argv[2] == "--graph":
        analyze_with_graph_export(project_path, sys.argv[3])
    else:
        analyze_project(project_path)


if __name__ == "__main__":
    main()
