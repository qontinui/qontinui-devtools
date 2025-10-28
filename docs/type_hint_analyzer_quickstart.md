# Type Hint Analyzer - Quick Start Guide

## Installation

The Type Hint Analyzer is included in qontinui-devtools. No additional installation required.

```bash
pip install qontinui-devtools
```

## Basic Usage

### Analyze a Directory

```python
from qontinui_devtools.type_analysis import TypeAnalyzer

analyzer = TypeAnalyzer()
report = analyzer.analyze_directory("path/to/your/code")

# Print summary
summary = report.get_summary()
print(f"Coverage: {summary['coverage_percentage']:.1f}%")
print(f"Fully typed functions: {summary['fully_typed_functions']}/{summary['total_functions']}")
```

### Analyze a Single File

```python
coverage, untyped_items, any_usages = analyzer.analyze_file("path/to/file.py")

print(f"Coverage: {coverage.coverage_percentage:.1f}%")
print(f"Functions: {coverage.total_functions}")
```

### Get Suggestions for Missing Type Hints

```python
# Get top 10 items that need type hints
for item in report.get_sorted_untyped_items(limit=10):
    print(f"\n{item.get_full_name()}")
    print(f"  Location: {item.file_path}:{item.line_number}")

    if item.suggested_type:
        print(f"  Suggested type: {item.suggested_type}")
        print(f"  Confidence: {item.confidence:.1%}")
        print(f"  Reason: {item.reason}")
```

### Generate a Report

```python
# Generate and save a text report
report_text = analyzer.generate_report_text(report)

with open("type_coverage_report.txt", "w") as f:
    f.write(report_text)
```

## Advanced Usage

### With Mypy Integration

```python
analyzer = TypeAnalyzer(
    run_mypy=True,           # Run mypy for additional checks
    strict_mode=True,        # Use mypy strict mode
    mypy_config="mypy.ini"   # Path to mypy config
)

report = analyzer.analyze_directory("path/to/code")

# Check mypy errors
for error in report.mypy_errors:
    print(f"{error.severity}: {error.message}")
    print(f"  at {error.file_path}:{error.line_number}")
```

### With Exclusions

```python
report = analyzer.analyze_directory(
    "path/to/code",
    exclude_patterns=[
        "**/test_*.py",      # Exclude test files
        "**/tests/**",       # Exclude test directories
        "**/*_pb2.py",       # Exclude generated files
        "**/venv/**",        # Exclude virtual environments
    ]
)
```

### Module-Level Analysis

```python
# Check coverage for specific modules
for module_name, module_cov in report.module_coverage.items():
    print(f"{module_name}: {module_cov.coverage_percentage:.1f}%")

    if module_cov.coverage_percentage < 80:
        print(f"  ⚠️  Needs improvement")
```

### Check for 'Any' Usage

```python
# Find all uses of the Any type
for usage in report.any_usages:
    print(f"{usage.file_path}:{usage.line_number}")
    print(f"  {usage.context}")

    if usage.suggestion:
        print(f"  Suggestion: {usage.suggestion}")
```

## Common Patterns

### CI/CD Integration

```python
#!/usr/bin/env python3
"""Type coverage check for CI/CD."""

from qontinui_devtools.type_analysis import TypeAnalyzer
import sys

analyzer = TypeAnalyzer(run_mypy=True)
report = analyzer.analyze_directory("src")

coverage = report.overall_coverage.coverage_percentage
min_coverage = 80.0

print(f"Type coverage: {coverage:.1f}%")

if coverage < min_coverage:
    print(f"❌ Coverage below minimum ({min_coverage}%)")
    sys.exit(1)
else:
    print(f"✓ Coverage meets minimum requirement")
    sys.exit(0)
```

### Pre-commit Hook

```python
#!/usr/bin/env python3
"""Check type hints before commit."""

from qontinui_devtools.type_analysis import TypeAnalyzer
import subprocess
import sys

# Get changed Python files
result = subprocess.run(
    ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
    capture_output=True,
    text=True
)

python_files = [
    f for f in result.stdout.split("\n")
    if f.endswith(".py")
]

if not python_files:
    sys.exit(0)

# Check type coverage of changed files
analyzer = TypeAnalyzer(run_mypy=False)
issues = []

for file_path in python_files:
    coverage, untyped_items, _ = analyzer.analyze_file(file_path)

    if coverage.coverage_percentage < 100:
        issues.append((file_path, coverage, untyped_items))

if issues:
    print("⚠️  Type hint issues found:")
    for file_path, coverage, untyped_items in issues:
        print(f"\n{file_path}: {coverage.coverage_percentage:.1f}% coverage")
        for item in untyped_items[:3]:
            print(f"  - {item.name} (line {item.line_number})")

    print("\nRun 'git commit --no-verify' to bypass this check")
    sys.exit(1)

sys.exit(0)
```

### Incremental Improvement Tracking

```python
#!/usr/bin/env python3
"""Track type coverage improvements over time."""

import json
from datetime import datetime
from pathlib import Path
from qontinui_devtools.type_analysis import TypeAnalyzer

analyzer = TypeAnalyzer()
report = analyzer.analyze_directory("src")

# Load historical data
history_file = Path("type_coverage_history.json")
history = []

if history_file.exists():
    history = json.loads(history_file.read_text())

# Add current measurement
history.append({
    "date": datetime.now().isoformat(),
    "coverage": report.overall_coverage.coverage_percentage,
    "fully_typed": report.overall_coverage.fully_typed_functions,
    "total_functions": report.overall_coverage.total_functions,
})

# Save updated history
history_file.write_text(json.dumps(history, indent=2))

# Show progress
if len(history) > 1:
    prev = history[-2]
    curr = history[-1]
    delta = curr["coverage"] - prev["coverage"]

    print(f"Current coverage: {curr['coverage']:.1f}%")
    print(f"Change: {delta:+.1f}%")
```

## Tips for Best Results

### 1. Start with Public APIs
Focus on adding type hints to public functions first:
```python
# Prioritize by visibility
sorted_items = sorted(
    report.untyped_items,
    key=lambda x: (
        not x.name.startswith("_"),  # Public items first
        x.item_type == "function",    # Functions before params
        -x.confidence,                # High confidence first
    )
)
```

### 2. Trust High-Confidence Suggestions
Use suggestions with confidence > 0.8:
```python
for item in report.untyped_items:
    if item.confidence > 0.8:
        print(f"Safe to apply: {item.name} -> {item.suggested_type}")
```

### 3. Replace 'Any' Types
Identify and replace `Any` types:
```python
for usage in report.any_usages:
    if "list[Any]" in str(usage.context):
        print(f"Consider list[T] at {usage.file_path}:{usage.line_number}")
```

### 4. Run Incrementally
Check coverage after each batch of changes:
```bash
# Before changes
python -c "from qontinui_devtools.type_analysis import TypeAnalyzer; \
           print(TypeAnalyzer().analyze_directory('src').overall_coverage.coverage_percentage)"

# After changes
# Re-run to see improvement
```

## Interpreting Results

### Coverage Levels
- **90-100%**: Excellent - Well-typed codebase
- **70-89%**: Good - Some improvements possible
- **50-69%**: Moderate - Significant gaps
- **Below 50%**: Needs improvement

### Confidence Scores
- **0.9-1.0**: Very high - Safe to apply automatically
- **0.7-0.9**: High - Review and apply
- **0.5-0.7**: Medium - Verify before applying
- **Below 0.5**: Low - Manual inspection needed

## Common Issues

### Issue: Coverage shows 0% but code has type hints

**Cause**: Using old-style typing (Python 3.9-)

**Solution**: Update to PEP 604 syntax:
```python
# Old style (not detected well)
from typing import Optional, Union
def foo(x: Optional[int]) -> Union[str, int]: ...

# New style (properly detected)
def foo(x: int | None) -> str | int: ...
```

### Issue: Mypy errors not showing

**Cause**: Mypy not installed or not in PATH

**Solution**: Install mypy:
```bash
pip install mypy
```

### Issue: Too many false positives

**Cause**: Analyzing generated or third-party code

**Solution**: Add exclusions:
```python
report = analyzer.analyze_directory(
    "src",
    exclude_patterns=["**/generated/**", "**/vendor/**"]
)
```

## Next Steps

1. **Measure baseline**: Run analyzer on your codebase
2. **Set targets**: Decide on minimum coverage goals
3. **Prioritize**: Use suggestions to identify quick wins
4. **Improve incrementally**: Add type hints in small batches
5. **Track progress**: Monitor coverage improvements
6. **Integrate CI/CD**: Prevent regressions

For more information, see the [full documentation](../TYPE_HINT_ANALYZER_SUMMARY.md).
