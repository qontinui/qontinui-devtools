#!/usr/bin/env python3
"""
Example script demonstrating the Race Condition Detector.

This script shows how to use the RaceConditionDetector to analyze Python code
for potential threading issues.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

from qontinui_devtools.concurrency import RaceConditionDetector


def analyze_directory(path: str, verbose: bool = True) -> None:
    """
    Analyze a directory for race conditions.

    Args:
        path: Path to directory or file to analyze
        verbose: Print detailed output
    """
    print(f"Analyzing: {path}")
    print("=" * 80)
    print()

    # Create detector
    detector = RaceConditionDetector(
        root_path=path,
        exclude_patterns=["test_", "__pycache__", ".git", "venv", ".venv", "build", "dist"],
    )

    # Run analysis
    print("Running analysis...")
    races = detector.analyze()

    # Get statistics
    stats = detector.get_statistics()

    # Print summary
    print("\n" + "=" * 80)
    print("ANALYSIS SUMMARY")
    print("=" * 80)
    print(f"Files analyzed:        {stats['files_analyzed']}")
    print(f"Shared states found:   {stats['shared_states_found']}")
    print(f"  - Protected:         {stats['protected_states']}")
    print(f"  - Unprotected:       {stats['unprotected_states']}")
    print(f"Locks found:           {stats['locks_found']}")
    print()
    print(f"Race conditions:       {stats['race_conditions_found']}")
    print(f"  - Critical:          {stats['critical_issues']}")
    print(f"  - High:              {stats['high_issues']}")
    print(f"  - Medium:            {stats['medium_issues']}")
    print(f"  - Low:               {stats['low_issues']}")
    print()

    if not races:
        print("No race conditions detected. Great job!")
        return

    # Print detailed findings
    if verbose:
        print("\n" + "=" * 80)
        print("DETAILED FINDINGS")
        print("=" * 80)
        print()

        for i, race in enumerate(races, 1):
            # Skip low severity in summary view
            if race.severity == "low" and not verbose:
                continue

            # Severity badge
            severity_emoji = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢",
            }
            emoji = severity_emoji.get(race.severity, "⚪")

            print(f"{i}. {emoji} [{race.severity.upper()}] {race.shared_state.name}")
            print(f"   Type: {race.shared_state.inferred_type}")
            if race.shared_state.class_name:
                print(f"   Class: {race.shared_state.class_name}")
            print(f"   Location: {race.shared_state.file_path}:{race.shared_state.line_number}")
            print()

            # Description
            print(f"   Description:")
            print(f"     {race.description}")
            print()

            # Patterns
            if race.patterns_detected:
                print(f"   Patterns:")
                for pattern in race.patterns_detected:
                    print(f"     - {pattern}")
                print()

            # Suggestion
            print(f"   Suggestion:")
            # Wrap suggestion text
            suggestion_lines = race.suggestion.split(". ")
            for line in suggestion_lines:
                if line:
                    print(f"     {line}.")
            print()

            # Access locations (limited)
            if len(race.access_locations) <= 5:
                print(f"   Access locations:")
                for file_path, line_num, access_type in race.access_locations:
                    print(f"     - Line {line_num}: {access_type}")
            else:
                print(f"   Access locations: {len(race.access_locations)} (showing first 5)")
                for file_path, line_num, access_type in race.access_locations[:5]:
                    print(f"     - Line {line_num}: {access_type}")

            print()
            print("-" * 80)
            print()

    # Print report to file
    report_file = Path("race_condition_report.txt")
    report = detector.generate_report(include_low=True)
    report_file.write_text(report)
    print(f"\nFull report saved to: {report_file.absolute()}")


def analyze_example_code() -> None:
    """Analyze some example code with known race conditions."""
    import tempfile

    print("Analyzing example code with known race conditions...")
    print("=" * 80)
    print()

    # Create temporary directory with example code
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Example 1: Unprotected class variable
        (tmppath / "bad_cache.py").write_text('''
class Cache:
    """Cache with race condition."""
    _data = {}

    def get(self, key):
        return self._data.get(key)

    def set(self, key, value):
        self._data[key] = value  # RACE CONDITION!

    def clear(self):
        self._data.clear()
''')

        # Example 2: Check-then-act pattern
        (tmppath / "singleton.py").write_text('''
class Singleton:
    """Singleton with race condition."""
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:  # Check
            cls._instance = Singleton()  # Act - RACE CONDITION!
        return cls._instance
''')

        # Example 3: Properly protected (should not flag)
        (tmppath / "safe_cache.py").write_text('''
import threading

class SafeCache:
    """Cache with proper locking."""
    def __init__(self):
        self._data = {}
        self._lock = threading.Lock()

    def set(self, key, value):
        with self._lock:
            self._data[key] = value  # Properly protected

    def get(self, key):
        with self._lock:
            return self._data.get(key)
''')

        # Analyze
        analyze_directory(str(tmppath), verbose=True)


def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Detect race conditions in Python code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a directory
  python detect_race_conditions.py /path/to/project

  # Analyze a single file
  python detect_race_conditions.py mymodule.py

  # Run example analysis
  python detect_race_conditions.py --example

  # Quick summary only
  python detect_race_conditions.py /path/to/project --quiet
""",
    )

    parser.add_argument(
        "path",
        nargs="?",
        help="Path to directory or file to analyze",
    )
    parser.add_argument(
        "--example",
        action="store_true",
        help="Run analysis on example code",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Show summary only, not detailed findings",
    )

    args = parser.parse_args()

    if args.example:
        analyze_example_code()
    elif args.path:
        analyze_directory(args.path, verbose=not args.quiet)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
