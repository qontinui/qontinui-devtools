"""Example: Detect dead code in a Python project.

This example demonstrates how to use the DeadCodeDetector to find
unused functions, classes, imports, and variables in a codebase.
"""

from pathlib import Path

from qontinui_devtools.code_quality import DeadCodeDetector


def main() -> None:
    """Run dead code detection example."""
    # Analyze the qontinui_devtools package itself
    project_path = Path(__file__).parent.parent / "python" / "qontinui_devtools"

    print("=" * 80)
    print("Dead Code Detection Example")
    print("=" * 80)
    print(f"\nAnalyzing: {project_path}")
    print("\nThis may take a moment...\n")

    # Create detector
    detector = DeadCodeDetector(str(project_path))

    # Get all dead code
    dead_code = detector.analyze()

    if not dead_code:
        print("No dead code found! Your codebase is clean.")
        return

    # Group by type
    by_type = {}
    for dc in dead_code:
        by_type.setdefault(dc.type, []).append(dc)

    # Display results
    print(f"Found {len(dead_code)} potential dead code items:\n")

    # Display by type
    for code_type in ["import", "variable", "function", "class"]:
        if code_type not in by_type:
            continue

        items = by_type[code_type]
        print(f"\n{code_type.upper()}S ({len(items)}):")
        print("-" * 60)

        # Show top 5 for each type
        for dc in sorted(items, key=lambda x: x.confidence, reverse=True)[:5]:
            print(f"  • {dc.name}")
            print(f"    File: {dc.file_path}:{dc.line_number}")
            print(f"    Confidence: {dc.confidence:.2f}")
            print(f"    Reason: {dc.reason}")
            print()

        if len(items) > 5:
            print(f"  ... and {len(items) - 5} more")

    # Statistics
    print("\n" + "=" * 80)
    print("STATISTICS")
    print("=" * 80)
    stats = detector.get_stats()
    print(f"Total dead code items: {stats['total']}")
    print(f"  Functions: {stats['functions']}")
    print(f"  Classes: {stats['classes']}")
    print(f"  Imports: {stats['imports']}")
    print(f"  Variables: {stats['variables']}")

    # Filter by high confidence
    high_confidence = [dc for dc in dead_code if dc.confidence > 0.8]
    print(f"\nHigh confidence items (>0.8): {len(high_confidence)}")

    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print("1. Review high confidence items first")
    print("2. Unused imports are usually safe to remove")
    print("3. Be cautious with functions that might be called dynamically")
    print("4. Consider if code is part of a public API before removing")
    print("=" * 80)


if __name__ == "__main__":
    main()
