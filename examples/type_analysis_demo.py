#!/usr/bin/env python3
"""Demonstration of the Type Hint Analyzer.

This script demonstrates how to use the type hint analyzer to measure
type coverage and get suggestions for improving type safety.
"""

import tempfile
from pathlib import Path

from qontinui_devtools.type_analysis import TypeAnalyzer


def create_sample_code(tmp_dir: Path) -> None:
    """Create sample Python files with varying type coverage."""

    # Fully typed module
    (tmp_dir / "fully_typed.py").write_text(
        """
def add(x: int, y: int) -> int:
    '''Add two numbers.'''
    return x + y

def greet(name: str, greeting: str = "Hello") -> str:
    '''Greet someone.'''
    return f"{greeting}, {name}!"

class Calculator:
    '''A simple calculator.'''

    def multiply(self, x: int, y: int) -> int:
        '''Multiply two numbers.'''
        return x * y

    def divide(self, x: float, y: float) -> float:
        '''Divide two numbers.'''
        if y == 0:
            raise ValueError("Cannot divide by zero")
        return x / y
"""
    )

    # Partially typed module
    (tmp_dir / "partially_typed.py").write_text(
        """
def process_data(data, format="json"):
    '''Process data in various formats.'''
    if format == "json":
        return {"data": data}
    return str(data)

def calculate(x: int, y):
    '''Calculate something.'''
    return x * y + 10

class DataProcessor:
    '''Process data.'''

    def __init__(self, config):
        self.config = config

    def process(self, items: list) -> dict:
        '''Process items.'''
        return {"count": len(items), "items": items}
"""
    )

    # Untyped module
    (tmp_dir / "untyped.py").write_text(
        """
def fetch_data(url, timeout=30):
    '''Fetch data from URL.'''
    return {"status": "ok", "data": []}

def transform(data, mapper=None):
    '''Transform data using mapper.'''
    if mapper:
        return [mapper(item) for item in data]
    return data

class Cache:
    '''Simple cache.'''

    def __init__(self):
        self.data = {}

    def get(self, key, default=None):
        '''Get value from cache.'''
        return self.data.get(key, default)

    def set(self, key, value):
        '''Set value in cache.'''
        self.data[key] = value
"""
    )

    # Module with Any usage
    (tmp_dir / "uses_any.py").write_text(
        """
from typing import Any

def process(data: Any) -> Any:
    '''Process arbitrary data.'''
    return data

def handle_request(request: dict[str, Any]) -> dict[str, Any]:
    '''Handle a request.'''
    return {"status": "ok", "data": request.get("data")}
"""
    )


def main() -> None:
    """Run the type hint analysis demonstration."""
    print("=" * 80)
    print("TYPE HINT ANALYZER DEMONSTRATION")
    print("=" * 80)
    print()

    # Create temporary directory with sample code
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        print(f"Creating sample code in: {tmp_path}")
        create_sample_code(tmp_path)
        print()

        # Run analysis
        print("Running type hint analysis...")
        analyzer = TypeAnalyzer(run_mypy=False, strict_mode=False)
        report = analyzer.analyze_directory(tmp_path)
        print()

        # Display summary
        print("=" * 80)
        print("ANALYSIS SUMMARY")
        print("=" * 80)
        summary = report.get_summary()
        print(f"Files analyzed: {summary['files_analyzed']}")
        print(f"Analysis time: {summary['analysis_time']:.3f}s")
        print()

        # Coverage metrics
        print("COVERAGE METRICS:")
        print(f"  Overall coverage: {summary['coverage_percentage']:.1f}%")
        print(f"  Parameter coverage: {summary['parameter_coverage']:.1f}%")
        print(f"  Return coverage: {summary['return_coverage']:.1f}%")
        print()
        print(f"  Total functions: {summary['total_functions']}")
        print(
            f"  Fully typed: {summary['fully_typed_functions']} ({summary['fully_typed_functions']/summary['total_functions']*100:.1f}%)"
        )
        print(f"  Partially typed: {summary['typed_functions'] - summary['fully_typed_functions']}")
        print(f"  Untyped: {summary['total_functions'] - summary['typed_functions']}")
        print()

        # Module breakdown
        print("=" * 80)
        print("MODULE BREAKDOWN")
        print("=" * 80)
        for module_name, module_cov in sorted(report.module_coverage.items()):
            module_cov.calculate_percentages()
            print(f"\n{module_name}:")
            print(f"  Coverage: {module_cov.coverage_percentage:.1f}%")
            print(f"  Functions: {module_cov.total_functions}")
            print(f"  Fully typed: {module_cov.fully_typed_functions}")
            print(f"  Parameters: {module_cov.typed_parameters}/{module_cov.total_parameters}")
            print(f"  Returns: {module_cov.typed_returns}/{module_cov.total_returns}")
        print()

        # Top untyped items with suggestions
        print("=" * 80)
        print("TOP UNTYPED ITEMS (with suggestions)")
        print("=" * 80)
        sorted_items = report.get_sorted_untyped_items(limit=15)
        for i, item in enumerate(sorted_items, 1):
            print(f"\n{i}. {item.get_full_name()}")
            print(f"   Type: {item.item_type}")
            print(f"   Location: {Path(item.file_path).name}:{item.line_number}")
            if item.suggested_type:
                print(f"   Suggestion: {item.suggested_type}")
                print(f"   Confidence: {item.confidence:.2f}")
                if item.reason:
                    print(f"   Reason: {item.reason}")
        print()

        # Any usage warnings
        if report.any_usages:
            print("=" * 80)
            print("ANY TYPE USAGE WARNINGS")
            print("=" * 80)
            print(f"Found {len(report.any_usages)} uses of 'Any' type")
            for usage in report.any_usages[:10]:
                print(f"\n  {Path(usage.file_path).name}:{usage.line_number}")
                print(f"  Context: {usage.context}")
            print()

        # Recommendations
        print("=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80)
        cov_pct = summary["coverage_percentage"]
        if cov_pct >= 90:
            print("✓ Excellent type coverage! Your code is well-typed.")
        elif cov_pct >= 70:
            print("○ Good type coverage, but there's room for improvement.")
        elif cov_pct >= 50:
            print("△ Moderate type coverage. Consider adding more type hints.")
        else:
            print("✗ Low type coverage. Adding type hints will improve code quality.")

        print()
        print("Next steps:")
        print("  1. Start with functions marked as high-confidence suggestions")
        print("  2. Add type hints to public APIs first")
        print("  3. Replace 'Any' types with more specific types")
        print("  4. Run mypy to validate your type hints")
        print("=" * 80)


if __name__ == "__main__":
    main()
