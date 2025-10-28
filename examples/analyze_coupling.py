"""Example: Analyze coupling and cohesion metrics in a codebase.

This example demonstrates how to use the CouplingCohesionAnalyzer to measure
module dependencies and internal class cohesion.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

from qontinui_devtools.architecture import CouplingCohesionAnalyzer


def main():
    """Analyze coupling and cohesion in a codebase."""
    # Change this to point to your codebase
    target_path = "../qontinui/src"

    # You can also analyze a specific module
    # target_path = "../qontinui/src/qontinui/core"

    print(f"Analyzing: {target_path}\n")

    # Create analyzer
    analyzer = CouplingCohesionAnalyzer(verbose=True)

    # Analyze the directory
    coupling, cohesion = analyzer.analyze_directory(target_path)

    # Print coupling results
    print("\n" + "=" * 80)
    print("HIGH COUPLING MODULES (Ce > 10)")
    print("=" * 80 + "\n")

    high_coupling = [c for c in coupling if c.efferent_coupling > 10]

    if high_coupling:
        for c in sorted(high_coupling, key=lambda x: x.efferent_coupling, reverse=True):
            print(f"Module: {c.name}")
            print(f"  Efferent Coupling (Ce): {c.efferent_coupling}")
            print(f"  Afferent Coupling (Ca): {c.afferent_coupling}")
            print(f"  Instability: {c.instability:.3f}")
            print(f"  Distance from Main: {c.distance_from_main:.3f}")
            print(f"  Score: {c.coupling_score.upper()}")
            print()
    else:
        print("No modules with high coupling (Ce > 10)")

    # Print cohesion results
    print("\n" + "=" * 80)
    print("LOW COHESION CLASSES (LCOM > 0.7)")
    print("=" * 80 + "\n")

    low_cohesion = [c for c in cohesion if c.lcom > 0.7]

    if low_cohesion:
        for c in sorted(low_cohesion, key=lambda x: x.lcom, reverse=True)[:10]:
            print(f"Class: {c.name}")
            print(f"  File: {c.file_path}")
            print(f"  LCOM: {c.lcom:.3f} (higher is worse)")
            print(f"  LCOM4: {c.lcom4:.1f} (1 is ideal)")
            print(f"  TCC: {c.tcc:.3f} (higher is better)")
            print(f"  LCC: {c.lcc:.3f} (higher is better)")
            print(f"  Score: {c.cohesion_score.upper()}")
            print()
    else:
        print("No classes with low cohesion (LCOM > 0.7)")

    # Generate and save report
    print("\n" + "=" * 80)
    print("GENERATING REPORT")
    print("=" * 80 + "\n")

    report = analyzer.generate_report(coupling, cohesion)

    report_path = Path(__file__).parent / "coupling_report.txt"
    report_path.write_text(report)

    print(f"Full report saved to: {report_path}")

    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80 + "\n")

    if coupling:
        avg_ce = sum(c.efferent_coupling for c in coupling) / len(coupling)
        avg_instability = sum(c.instability for c in coupling) / len(coupling)
        poor_coupling = len([c for c in coupling if c.coupling_score == "poor"])

        print(f"Modules analyzed: {len(coupling)}")
        print(f"Average Ce: {avg_ce:.2f}")
        print(f"Average Instability: {avg_instability:.3f}")
        print(f"Poor coupling: {poor_coupling} modules")

    if cohesion:
        avg_lcom = sum(c.lcom for c in cohesion) / len(cohesion)
        poor_cohesion = len([c for c in cohesion if c.cohesion_score == "poor"])

        print(f"\nClasses analyzed: {len(cohesion)}")
        print(f"Average LCOM: {avg_lcom:.3f}")
        print(f"Poor cohesion: {poor_cohesion} classes")


if __name__ == "__main__":
    main()
