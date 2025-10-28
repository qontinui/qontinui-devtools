# Quick Start Guide

Get started with qontinui-devtools in 5 minutes!

## Installation

### Option 1: Using pip (when published)

```bash
pip install qontinui-devtools
```

### Option 2: Using Poetry (Recommended)

```bash
# Add to your project
poetry add qontinui-devtools --group dev

# Or clone and install from source
git clone https://github.com/qontinui/qontinui-devtools.git
cd qontinui-devtools
poetry install
```

### Option 3: From Source

```bash
git clone https://github.com/qontinui/qontinui-devtools.git
cd qontinui-devtools
pip install -e .
```

## Verify Installation

```bash
# Run verification script
python scripts/verify_installation.py

# Or check version
qontinui-devtools --version
```

## Your First Analysis

### 1. Check for Circular Dependencies

```bash
# Analyze your project
qontinui-devtools import check /path/to/your/project

# Example output:
# Found 2 circular dependencies:
#   module_a -> module_b -> module_c -> module_a
#   service_x -> service_y -> service_x
```

### 2. Detect God Classes

```bash
# Find classes that do too much
qontinui-devtools architecture god-classes /path/to/your/project

# Example output:
# Found 3 god classes:
#   UserManager: 45 methods, LCOM=0.89 (HIGH SEVERITY)
#   DataProcessor: 38 methods, LCOM=0.82 (HIGH SEVERITY)
```

### 3. Generate HTML Report

```bash
# Create comprehensive analysis report
qontinui-devtools report /path/to/your/project --output report.html

# Open in browser
# The report includes:
# - Executive summary
# - Interactive charts
# - Detailed findings
# - Actionable recommendations
```

### 4. Test for Race Conditions

```bash
# Stress test your code
qontinui-devtools test race --threads 10 --iterations 1000

# Example output:
# Running 1000 iterations with 10 threads...
# SUCCESS: No race conditions detected
# Average execution time: 0.045s
```

## Common Commands

### Import Analysis

```bash
# Check for circular dependencies
qontinui-devtools import check /path/to/project

# Trace imports in real-time (advanced)
qontinui-devtools import trace /path/to/project
```

### Architecture Analysis

```bash
# Find god classes
qontinui-devtools architecture god-classes /path/to/project --threshold 0.8

# Analyze SRP violations
qontinui-devtools architecture srp /path/to/project

# Calculate coupling metrics
qontinui-devtools architecture coupling /path/to/project

# Generate dependency graph
qontinui-devtools architecture graph /path/to/project --output graph.html
```

### Concurrency Testing

```bash
# Detect potential race conditions (static)
qontinui-devtools concurrency detect /path/to/project

# Stress test (dynamic)
qontinui-devtools test race --threads 20 --iterations 5000
```

### Reporting

```bash
# Generate comprehensive HTML report
qontinui-devtools report /path/to/project --output report.html

# Generate JSON report for CI/CD
qontinui-devtools report /path/to/project --format json --output report.json
```

### CI/CD Integration

```bash
# Setup pre-commit hooks
qontinui-devtools ci setup-hooks

# Run full analysis with quality gates
qontinui-devtools ci analyze /path/to/project --fail-on-threshold
```

## Python API Examples

### Example 1: Detect Circular Imports

```python
from qontinui_devtools import CircularDependencyDetector

# Create detector
detector = CircularDependencyDetector("/path/to/project/src")

# Find cycles
cycles = detector.find_cycles()

# Print results
for cycle in cycles:
    print(f"Found cycle: {' -> '.join(cycle)}")
```

### Example 2: Analyze God Classes

```python
from qontinui_devtools import GodClassDetector

# Create detector
detector = GodClassDetector()

# Analyze directory
results = detector.analyze_directory("/path/to/project/src")

# Print god classes
for result in results.god_classes:
    print(f"{result.class_name}:")
    print(f"  Methods: {result.metrics.num_methods}")
    print(f"  LCOM: {result.metrics.lcom:.2f}")
    print(f"  Severity: {result.severity}")
```

### Example 3: Generate HTML Report

```python
from qontinui_devtools import ReportAggregator, HTMLReportGenerator

# Run all analyses
aggregator = ReportAggregator("/path/to/project/src")
report_data = aggregator.run_all_analyses()

# Generate HTML report
generator = HTMLReportGenerator()
generator.generate(report_data, "analysis_report.html")

print("Report generated: analysis_report.html")
```

### Example 4: Use Mock HAL for Testing

```python
from qontinui_devtools.testing import MockHAL

# Create mock HAL
hal = MockHAL.create()

# Configure pattern matching
hal.pattern_matcher.configure(
    pattern="button.png",
    should_match=True,
    match_location=(100, 200),
    confidence=0.95
)

# Use in your tests
location = hal.pattern_matcher.find_pattern("button.png")
assert location == (100, 200)

# Simulate input
hal.input_controller.click(100, 200)
hal.input_controller.type_text("Hello, World!")

# Verify actions
actions = hal.input_controller.get_actions()
assert len(actions) == 2
assert actions[0].action_type == "click"
assert actions[1].action_type == "type"
```

## Configuration

### CLI Configuration File

Create `.qontinui-devtools.toml` in your project root:

```toml
[import_analysis]
exclude_patterns = ["**/tests/**", "**/migrations/**"]
max_depth = 10

[architecture]
god_class_threshold = 0.8
srp_min_clusters = 3

[concurrency]
default_threads = 10
default_iterations = 1000

[reporting]
default_output = "report.html"
include_charts = true
dark_mode = true
```

## Next Steps

1. **Read the User Guide**: [docs/user-guide.md](docs/user-guide.md)
2. **Explore Examples**: Check the [examples/](examples/) directory
3. **API Reference**: [docs/api-reference.md](docs/api-reference.md)
4. **CI/CD Integration**: [docs/ci-integration.md](docs/ci-integration.md)

## Common Issues

### Issue: "Module not found"

```bash
# Solution: Reinstall dependencies
poetry install
# or
pip install -e .
```

### Issue: "Command not found: qontinui-devtools"

```bash
# Solution: Use poetry run or activate virtual environment
poetry run qontinui-devtools --help

# Or activate environment
poetry shell
qontinui-devtools --help
```

### Issue: "Import errors in analysis"

```bash
# Solution: Ensure target project is importable
export PYTHONPATH=/path/to/your/project:$PYTHONPATH
qontinui-devtools import check /path/to/your/project
```

## Getting Help

- **CLI Help**: `qontinui-devtools --help`
- **Command Help**: `qontinui-devtools <command> --help`
- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/qontinui/qontinui-devtools/issues)
- **Discussions**: [GitHub Discussions](https://github.com/qontinui/qontinui-devtools/discussions)

## Tips and Tricks

### Tip 1: Run Multiple Analyses

```bash
# Chain commands with &&
qontinui-devtools import check . && \
qontinui-devtools architecture god-classes . && \
qontinui-devtools report . --output report.html
```

### Tip 2: Filter Results

```bash
# Only show high severity issues
qontinui-devtools architecture god-classes . --min-severity high

# Exclude test files
qontinui-devtools import check . --exclude "**/tests/**"
```

### Tip 3: Export in Multiple Formats

```bash
# Generate both HTML and JSON
qontinui-devtools report . --output report.html
qontinui-devtools report . --format json --output report.json
```

### Tip 4: Use in Pre-commit Hooks

```bash
# Install pre-commit hooks
qontinui-devtools ci setup-hooks

# Now runs automatically on git commit
git commit -m "Your changes"
```

## Example Workflow

Here's a typical workflow for analyzing a project:

```bash
# 1. Check for circular dependencies
qontinui-devtools import check /path/to/project

# 2. Analyze architecture quality
qontinui-devtools architecture god-classes /path/to/project
qontinui-devtools architecture srp /path/to/project
qontinui-devtools architecture coupling /path/to/project

# 3. Generate dependency graph
qontinui-devtools architecture graph /path/to/project --output graph.html

# 4. Test for race conditions
qontinui-devtools test race --threads 10 --iterations 1000

# 5. Generate comprehensive report
qontinui-devtools report /path/to/project --output report.html

# 6. Open report in browser
open report.html  # macOS
xdg-open report.html  # Linux
start report.html  # Windows
```

---

**Ready for more?** Check out the [full documentation](docs/TABLE_OF_CONTENTS.md)!
