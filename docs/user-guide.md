# Qontinui DevTools User Guide

A comprehensive guide to using Qontinui DevTools for analyzing, debugging, and testing your Qontinui applications.

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Import Analysis](#import-analysis)
4. [Concurrency Analysis](#concurrency-analysis)
5. [Testing Tools](#testing-tools)
6. [Performance Profiling](#performance-profiling)
7. [Mock HAL](#mock-hal)
8. [Comprehensive Analysis](#comprehensive-analysis)
9. [Configuration](#configuration)
10. [Common Workflows](#common-workflows)
11. [Troubleshooting](#troubleshooting)

---

## Installation

### Prerequisites

- Python 3.11 or higher
- pip or Poetry package manager
- (Optional) Graphviz for visualization features

### Install from PyPI

```bash
pip install qontinui-devtools
```

### Install from Source

```bash
git clone https://github.com/qontinui/qontinui-devtools.git
cd qontinui-devtools
poetry install
```

### Install with Optional Features

```bash
# Install with memory profiling support
pip install qontinui-devtools[memory]

# Install all optional features
pip install qontinui-devtools[all]
```

### Verify Installation

```bash
qontinui-devtools --version
qontinui-devtools --help
```

---

## Quick Start

### Basic Usage

```bash
# Check for circular dependencies
qontinui-devtools import check ./src

# Analyze race conditions
qontinui-devtools concurrency check ./src

# Run comprehensive analysis
qontinui-devtools analyze ./src
```

### Common Options

All commands support these common options:

- `--help` - Show detailed help for the command
- `--output PATH` - Save results to a file
- `--format FORMAT` - Choose output format (text/json/html)

### Example Session

```bash
# Navigate to your project
cd /path/to/your/qontinui/project

# Run a quick health check
qontinui-devtools analyze ./src --format text

# If issues are found, investigate further
qontinui-devtools import check ./src --detailed
qontinui-devtools concurrency check ./src --severity high

# Generate a comprehensive report
qontinui-devtools analyze ./src --report analysis_report.html --format html
```

---

## Import Analysis

The import analysis tools help you detect and resolve circular dependencies, understand import chains, and visualize your project's module structure.

### Check for Circular Dependencies

The most common use case - detect circular imports that can cause import errors:

```bash
# Basic check
qontinui-devtools import check ./src

# Strict mode (exit with error code 1 if issues found)
qontinui-devtools import check ./src --strict

# Save results to file
qontinui-devtools import check ./src --output report.json --format json
```

**Example Output:**

```
Analyzing imports in: ./src

❌ Found 2 circular dependencies:

╭─────────────────── Cycle 1 ───────────────────╮
│ Cycle Path:                                   │
│ module_a → module_b → module_c → module_a     │
│                                               │
│ Suggestion:                                   │
│ Consider moving shared dependencies to a      │
│ separate module or using lazy imports         │
╰───────────────────────────────────────────────╯
```

### Trace Runtime Imports

Trace all imports that occur when loading a module:

```bash
# Basic trace
qontinui-devtools import trace mypackage.mymodule

# Trace and generate visual graph
qontinui-devtools import trace mypackage.mymodule --visualize

# Limit depth to avoid system modules
qontinui-devtools import trace mypackage --depth 3

# Exclude test modules
qontinui-devtools import trace mypackage --exclude "test_*" --exclude "*_test"
```

**Use Cases:**
- Understanding complex import chains
- Debugging import errors
- Optimizing import times
- Documenting module dependencies

### Generate Dependency Graphs

Create visual representations of your project's import structure:

```bash
# Generate PNG graph
qontinui-devtools import graph ./src

# Generate SVG with custom output path
qontinui-devtools import graph ./src --output deps.svg --format svg

# Generate PDF without package clustering
qontinui-devtools import graph ./src --output deps.pdf --format pdf --no-clusters
```

**Graph Features:**
- Color-coded by package
- Shows import direction with arrows
- Highlights circular dependencies in red
- Optional package clustering for better organization

---

## Concurrency Analysis

Detect race conditions, deadlocks, and other thread-safety issues in your multi-threaded code.

### Check for Race Conditions

Static analysis to detect potential race conditions:

```bash
# Basic check (shows medium+ severity)
qontinui-devtools concurrency check ./src

# Only show critical issues
qontinui-devtools concurrency check ./src --severity critical

# Show all severity levels
qontinui-devtools concurrency check ./src --severity low

# Detailed output with fix suggestions
qontinui-devtools concurrency check ./src --detailed

# Save report
qontinui-devtools concurrency check ./src --output races.json --format json
```

**Severity Levels:**
- **Critical**: Definite race condition that will cause errors
- **High**: Very likely race condition
- **Medium**: Potential race condition (default threshold)
- **Low**: Unlikely but theoretically possible

**Example Output:**

```
Analyzing concurrency in: ./src

⚠️  Found 3 potential race conditions:

╭──────── Race Condition in shared_counter ────────╮
│ Severity: HIGH                                   │
│ Description: Shared state modified without lock  │
│ State: shared_counter                            │
│ Location: src/worker.py:42                       │
│                                                  │
│ Suggestion:                                      │
│ Add threading.Lock() to protect shared state:   │
│                                                  │
│   self.lock = threading.Lock()                   │
│   with self.lock:                                │
│       self.counter += 1                          │
╰──────────────────────────────────────────────────╯
```

### Detect Deadlocks

Analyze lock acquisition patterns to find potential deadlock scenarios:

```bash
# Check for deadlock potential
qontinui-devtools concurrency deadlock ./src

# Visualize lock dependency graph
qontinui-devtools concurrency deadlock ./src --visualize
```

**Deadlock Detection:**
- Identifies lock acquisition order violations
- Detects cyclic lock dependencies
- Suggests lock ordering strategies
- Visualizes lock wait-for graphs

---

## Testing Tools

Dynamic testing tools to stress test your code and detect runtime issues.

### Race Condition Stress Testing

Execute functions concurrently to detect race conditions:

```bash
# Test a specific function
qontinui-devtools test race --target mymodule:my_function

# Heavy stress test with many threads
qontinui-devtools test race \
  --target mymodule:my_function \
  --threads 50 \
  --iterations 1000

# Quick smoke test
qontinui-devtools test race \
  --target mymodule:my_function \
  --threads 5 \
  --iterations 10 \
  --timeout 10
```

**Parameters:**
- `--threads`: Number of concurrent threads (default: 10)
- `--iterations`: Iterations per thread (default: 100)
- `--timeout`: Maximum test duration in seconds (default: 30)
- `--target`: Function to test in format `module:function`

**Example Output:**

```
╭─────── Race Condition Test Configuration ────────╮
│ Threads: 50                                      │
│ Iterations: 1000                                 │
│ Target: mymodule:increment_counter               │
│ Timeout: 30s                                     │
╰──────────────────────────────────────────────────╯

Running tests... ━━━━━━━━━━━━━━━━━━━━━━ 100%

┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ Metric           ┃   Value ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━┩
│ Total Iterations │   50000 │
│ Successful       │   49987 │
│ Failed           │      13 │
│ Success Rate     │   99.97% │
└──────────────────┴─────────┘

╭──────────── Race Condition ───────────────╮
│ ❌ Race condition detected!               │
│                                           │
│ • Counter value mismatch                  │
│ • Expected: 50000, Got: 49987            │
│ • Lost updates indicate race condition    │
╰───────────────────────────────────────────╯
```

### Stress Testing

Sustained load testing to identify performance degradation and stability issues:

```bash
# Run 1-minute stress test
qontinui-devtools test stress ./tests/test_suite.py

# Extended stress test with multiple workers
qontinui-devtools test stress ./tests \
  --duration 600 \
  --workers 8
```

**Use Cases:**
- Finding memory leaks under sustained load
- Identifying performance degradation over time
- Testing system stability
- Validating resource cleanup

---

## Performance Profiling

Profile CPU and memory usage to identify bottlenecks.

### CPU Profiling

Profile CPU usage and generate flame graphs:

```bash
# Profile a Python script
qontinui-devtools profile cpu script.py --duration 30

# Profile a running process
qontinui-devtools profile cpu --target pid:1234

# Custom output format
qontinui-devtools profile cpu script.py \
  --duration 60 \
  --output profile.svg
```

**Output Formats:**
- SVG flame graphs (interactive in browsers)
- Text call trees
- JSON profiling data

### Memory Profiling

Profile memory usage and detect leaks:

```bash
# Profile memory usage
qontinui-devtools profile memory script.py

# Generate detailed HTML report
qontinui-devtools profile memory script.py \
  --output memory_report.html

# Profile with memory tracking
qontinui-devtools profile memory script.py \
  --track-allocations
```

**Memory Profiling Features:**
- Heap snapshots over time
- Allocation timeline
- Leak detection
- Memory usage by module

---

## Mock HAL

The Mock Hardware Abstraction Layer allows testing without physical hardware.

### Initialize Mock HAL

Set up the mock HAL environment:

```bash
# Initialize with default configuration
qontinui-devtools hal init

# Initialize with custom config
qontinui-devtools hal init --config my_hal_config.yaml
```

**Configuration Options:**
- Screen size and resolution
- Input device mappings
- Simulated latency
- Error injection settings

### Record HAL Interactions

Record real or simulated HAL interactions for replay:

```bash
# Record 60 seconds of interactions
qontinui-devtools hal record session.hal

# Record for specific duration
qontinui-devtools hal record session.hal --duration 300

# Record with annotations
qontinui-devtools hal record session.hal \
  --annotate \
  --description "User login flow"
```

**Recording Features:**
- Captures all HAL calls with timestamps
- Records input events (mouse, keyboard, touch)
- Saves screen state changes
- Includes timing information

### Replay HAL Interactions

Replay recorded sessions for testing:

```bash
# Replay at normal speed
qontinui-devtools hal replay session.hal

# Replay at 2x speed
qontinui-devtools hal replay session.hal --speed 2.0

# Replay in slow motion for debugging
qontinui-devtools hal replay session.hal --speed 0.5

# Replay with validation
qontinui-devtools hal replay session.hal \
  --verify \
  --report replay_results.html
```

**Replay Options:**
- Variable playback speed
- Pause/resume control
- Step-through mode for debugging
- Automatic verification of expected outcomes

---

## Comprehensive Analysis

Run multiple checks in a single command.

### Basic Analysis

```bash
# Analyze entire codebase
qontinui-devtools analyze ./src

# Generate HTML report
qontinui-devtools analyze ./src \
  --report analysis_report.html \
  --format html

# Generate JSON for CI integration
qontinui-devtools analyze ./src \
  --report analysis.json \
  --format json
```

### Selective Analysis

Run only specific checks:

```bash
# Only check imports
qontinui-devtools analyze ./src --checks imports

# Check imports and concurrency
qontinui-devtools analyze ./src \
  --checks imports \
  --checks concurrency

# Run all checks (default)
qontinui-devtools analyze ./src --checks all
```

**Available Checks:**
- `imports` - Circular dependency detection
- `concurrency` - Race condition analysis
- `complexity` - Code complexity metrics
- `all` - Run all available checks

**Example Output:**

```
╭────────── Comprehensive Analysis ──────────╮
│ Path: ./src                                │
│ Checks: imports, concurrency, complexity   │
│ Format: text                               │
╰────────────────────────────────────────────╯

Analyzing imports... ✓
Analyzing concurrency... ✓
Analyzing complexity... ✓

┏━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Check                  ┃ Status ┃ Issues ┃ Details                 ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Circular Dependencies  │ ✓ PASS │      0 │ No issues               │
│ Race Conditions        │ ✗ FAIL │      3 │ Found 3 potential races │
│ Code Complexity        │ ⚠ WARN │      5 │ 5 high-complexity funcs │
└────────────────────────┴────────┴────────┴─────────────────────────┘

📄 Report saved: analysis_report.html
```

---

## Configuration

Customize DevTools behavior with configuration files.

### Configuration File

Create `.qontinui-devtools.yaml` in your project root:

```yaml
# Import analysis settings
imports:
  exclude_patterns:
    - "test_*"
    - "*_test.py"
    - "conftest.py"
  max_depth: 10
  ignore_stdlib: true

# Concurrency analysis settings
concurrency:
  min_severity: "medium"
  check_asyncio: true
  check_threading: true
  check_multiprocessing: true

# Testing settings
testing:
  race_test_threads: 20
  race_test_iterations: 200
  timeout: 60

# Profiling settings
profiling:
  sample_rate: 100  # Hz
  track_allocations: true
  max_frames: 50

# Mock HAL settings
hal:
  screen_size: [1920, 1080]
  simulate_latency: true
  latency_ms: 10
  error_rate: 0.0

# Output settings
output:
  color: true
  verbose: false
  format: "text"
```

### Environment Variables

Override settings with environment variables:

```bash
# Set minimum severity for concurrency checks
export QONTINUI_CONCURRENCY_SEVERITY=high

# Disable colored output
export QONTINUI_NO_COLOR=1

# Set default output format
export QONTINUI_OUTPUT_FORMAT=json

# Enable verbose mode
export QONTINUI_VERBOSE=1
```

### Per-Command Configuration

Override configuration per command:

```bash
# Use custom config file
qontinui-devtools analyze ./src --config my_config.yaml

# Override specific settings
qontinui-devtools concurrency check ./src \
  --severity high \
  --exclude "test_*"
```

---

## Common Workflows

### Pre-Commit Workflow

Check code before committing:

```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running Qontinui DevTools checks..."

# Check for circular dependencies
qontinui-devtools import check ./src --strict
if [ $? -ne 0 ]; then
    echo "❌ Import check failed"
    exit 1
fi

# Check for race conditions
qontinui-devtools concurrency check ./src --severity high
if [ $? -ne 0 ]; then
    echo "❌ Concurrency check failed"
    exit 1
fi

echo "✅ All checks passed"
```

### CI/CD Integration

Add to your CI pipeline:

```yaml
# .github/workflows/analysis.yml
name: Static Analysis

on: [push, pull_request]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install qontinui-devtools

      - name: Run analysis
        run: |
          qontinui-devtools analyze ./src \
            --report analysis.json \
            --format json

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: analysis-results
          path: analysis.json
```

### Development Workflow

Daily development routine:

```bash
# Morning: Quick health check
qontinui-devtools analyze ./src

# During development: Monitor specific files
qontinui-devtools import check ./src/mymodule.py

# Before lunch: Comprehensive check
qontinui-devtools analyze ./src --detailed

# Before going home: Generate report
qontinui-devtools analyze ./src \
  --report daily_report_$(date +%Y%m%d).html \
  --format html
```

### Debugging Workflow

When investigating issues:

```bash
# Step 1: Get overview
qontinui-devtools analyze ./src

# Step 2: Trace specific module
qontinui-devtools import trace problematic.module --visualize

# Step 3: Check concurrency in detail
qontinui-devtools concurrency check ./src/problematic --detailed

# Step 4: Stress test suspicious function
qontinui-devtools test race \
  --target problematic.module:suspicious_function \
  --threads 50 \
  --iterations 1000

# Step 5: Profile if needed
qontinui-devtools profile cpu problematic/script.py --duration 60
```

---

## Troubleshooting

### Common Issues

#### "Module not found" error

```bash
# Ensure your package is installed or PYTHONPATH is set
export PYTHONPATH=/path/to/your/project:$PYTHONPATH
qontinui-devtools import trace mymodule
```

#### Analysis running slowly

```bash
# Use exclude patterns to skip test files
qontinui-devtools analyze ./src --exclude "test_*" --exclude "conftest.py"

# Limit analysis depth
qontinui-devtools import check ./src --max-depth 5
```

#### No output or silent failure

```bash
# Enable verbose mode
qontinui-devtools analyze ./src --verbose

# Check logs
qontinui-devtools analyze ./src 2>&1 | tee analysis.log
```

#### Visualization not working

```bash
# Install Graphviz
sudo apt-get install graphviz  # Ubuntu/Debian
brew install graphviz          # macOS

# Verify installation
dot -V
```

### Getting Help

```bash
# General help
qontinui-devtools --help

# Command-specific help
qontinui-devtools import --help
qontinui-devtools import check --help

# Show version
qontinui-devtools --version
```

### Reporting Bugs

When reporting bugs, include:

1. **Version information:**
   ```bash
   qontinui-devtools --version
   python --version
   ```

2. **Full command:**
   ```bash
   qontinui-devtools analyze ./src --verbose
   ```

3. **Error output:**
   ```bash
   qontinui-devtools analyze ./src 2>&1 | tee error.log
   ```

4. **System information:**
   ```bash
   uname -a  # Linux/macOS
   ver       # Windows
   ```

---

## Advanced Topics

### Custom Analyzers

Extend DevTools with custom analyzers:

```python
from qontinui_devtools import BaseAnalyzer

class CustomAnalyzer(BaseAnalyzer):
    def analyze(self, path: str) -> list[Issue]:
        # Your analysis logic here
        pass
```

### Integration with IDEs

Configure your IDE to run DevTools:

**VS Code:**
```json
{
    "tasks": [
        {
            "label": "Analyze Code",
            "type": "shell",
            "command": "qontinui-devtools analyze ${workspaceFolder}/src"
        }
    ]
}
```

**PyCharm:**
- External Tools > Add
- Program: `qontinui-devtools`
- Arguments: `analyze $ProjectFileDir$/src`

### API Usage

Use DevTools programmatically:

```python
from qontinui_devtools import CircularDependencyDetector

detector = CircularDependencyDetector("./src")
cycles = detector.analyze()

for cycle in cycles:
    print(f"Found cycle: {' → '.join(cycle.cycle)}")
```

---

## Additional Resources

- **API Reference:** See [api-reference.md](api-reference.md)
- **Integration Guide:** See [integration.md](integration.md)
- **Architecture:** See [architecture.md](architecture.md)
- **Contributing:** See [../CONTRIBUTING.md](../CONTRIBUTING.md)
- **GitHub:** https://github.com/qontinui/qontinui-devtools
- **Documentation:** https://qontinui-devtools.readthedocs.io

---

**Version:** 0.1.0
**Last Updated:** 2025-10-28
**License:** MIT
