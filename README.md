# Qontinui DevTools

> Sophisticated analysis, debugging, and diagnostic tools for the Qontinui automation ecosystem

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests](https://img.shields.io/badge/tests-162%20passed-brightgreen.svg)](python/tests/)

## Overview

Qontinui DevTools is a comprehensive suite of analysis and debugging tools designed to detect, diagnose, and prevent common issues in the Qontinui automation framework. Built from real-world debugging experiences, it provides powerful static analysis, runtime monitoring, and testing utilities.

### Key Features

- **Import Tracer & Circular Dependency Detector** - Detect and prevent import deadlocks
- **Race Condition Detector & Tester** - Find and test threading issues
- **Mock HAL Components** - Complete hardware-free testing suite
- **God Class Detector** - Identify classes violating Single Responsibility Principle
- **SRP Analyzer** - Semantic analysis of class responsibilities
- **Coupling & Cohesion Analyzer** - Measure code quality metrics (Ca, Ce, LCOM, TCC, LCC)
- **Dependency Graph Visualizer** - Interactive module dependency visualization
- **HTML Report Generator** - Beautiful, comprehensive reports with Chart.js visualizations
- **CI/CD Integration** - GitHub Actions, GitLab CI, and more

## Why a Separate Repository?

DevTools is maintained separately from the main Qontinui repositories to:
- Keep production code lean (no heavy dev dependencies)
- Allow independent versioning and release cycles
- Enable reuse across multiple Qontinui projects
- Support experimental features without production impact

## Quick Start

### Installation

```bash
# Install from PyPI (when published)
pip install qontinui-devtools

# Or install with Poetry
poetry add qontinui-devtools --group dev

# Or install from source
git clone https://github.com/qontinui/qontinui-devtools.git
cd qontinui-devtools
poetry install
```

### Basic Usage

```bash
# Check for circular dependencies
qontinui-devtools import check /path/to/qontinui

# Detect god classes
qontinui-devtools architecture god-classes /path/to/qontinui

# Analyze SRP violations
qontinui-devtools architecture srp /path/to/qontinui

# Run coupling/cohesion analysis
qontinui-devtools architecture coupling /path/to/qontinui

# Generate interactive dependency graph
qontinui-devtools architecture graph /path/to/qontinui --output graph.html

# Generate comprehensive HTML report
qontinui-devtools report /path/to/qontinui --output report.html

# Run race condition tests
qontinui-devtools test race --threads 10 --iterations 100
```

### Python API

```python
from qontinui_devtools import (
    CircularDependencyDetector,
    GodClassDetector,
    SRPAnalyzer,
    CouplingCohesionAnalyzer,
    DependencyGraphVisualizer,
    HTMLReportGenerator,
    ReportAggregator,
)

# Detect circular imports
detector = CircularDependencyDetector("/path/to/qontinui/src")
cycles = detector.find_cycles()
for cycle in cycles:
    print(f"Found cycle: {' -> '.join(cycle)}")

# Find god classes
god_detector = GodClassDetector()
results = god_detector.analyze_directory("/path/to/qontinui/src")
for result in results.god_classes:
    print(f"{result.class_name}: {result.metrics.num_methods} methods, "
          f"LCOM={result.metrics.lcom:.2f}")

# Generate comprehensive report
aggregator = ReportAggregator("/path/to/qontinui/src")
report_data = aggregator.run_all_analyses()
generator = HTMLReportGenerator()
generator.generate(report_data, "analysis_report.html")
```

## Features in Detail

### Phase 1: Critical Debugging Tools

#### Import Analysis

**Import Tracer**
- Real-time import chain tracing with deadlock detection
- Thread-safe import monitoring
- Detailed timeline visualization
- Export to JSON/HTML

**Circular Dependency Detector**
- Static analysis to find import cycles
- Tarjan's algorithm for cycle detection
- Dependency graph visualization
- Suggested refactoring strategies

```bash
# Detect circular dependencies
qontinui-devtools import check /path/to/project

# Trace imports in real-time
qontinui-devtools import trace /path/to/project
```

#### Concurrency Analysis

**Race Condition Detector**
- Static analysis for threading issues
- Detects unprotected shared state
- Identifies missing locks
- Reports potential race conditions

**Race Condition Tester**
- Stress testing with configurable thread counts
- Automatic failure detection
- Timing analysis and statistics
- Reproducible test scenarios

```bash
# Detect potential race conditions
qontinui-devtools concurrency detect /path/to/project

# Stress test for race conditions
qontinui-devtools test race --threads 10 --iterations 1000
```

#### Testing Utilities

**Mock HAL Components**
- Complete mock implementations of all HAL interfaces
- Configurable behavior patterns
- Action recording and verification
- Test image fixtures included

```python
from qontinui_devtools.testing import MockHAL

# Create mock HAL
hal = MockHAL.create()

# Configure behavior
hal.pattern_matcher.configure(
    pattern="submit_button.png",
    should_match=True,
    match_location=(100, 200),
    confidence=0.95
)

# Use in tests
hal.input_controller.type_text("hello")
assert hal.input_controller.get_typed_text() == ["hello"]
```

### Phase 2: Architecture Analysis

#### God Class Detector

Identifies classes that violate the Single Responsibility Principle by:
- Calculating LCOM (Lack of Cohesion of Methods)
- Counting methods and attributes
- Analyzing method complexity
- Suggesting class extractions

```bash
qontinui-devtools architecture god-classes /path/to/project --threshold 0.8
```

#### SRP Analyzer

Performs semantic analysis to detect responsibility violations:
- Clusters methods by semantic similarity
- Identifies distinct responsibilities
- Suggests refactoring strategies
- Uses NLP techniques for analysis

```bash
qontinui-devtools architecture srp /path/to/project
```

#### Coupling & Cohesion Analyzer

Measures comprehensive code quality metrics:
- **Ca** (Afferent Coupling) - incoming dependencies
- **Ce** (Efferent Coupling) - outgoing dependencies
- **I** (Instability) - Ce / (Ca + Ce)
- **LCOM** (Lack of Cohesion of Methods)
- **TCC** (Tight Class Cohesion)
- **LCC** (Loose Class Cohesion)

```bash
qontinui-devtools architecture coupling /path/to/project --format json
```

#### Dependency Graph Visualizer

Creates interactive visualizations of module dependencies:
- Force-directed graph layout
- Cycle highlighting
- Zoom and pan support
- Export to PNG, SVG, PDF, or interactive HTML

```bash
qontinui-devtools architecture graph /path/to/project --output graph.html
```

### Reporting

#### HTML Report Generator

Generates comprehensive, interactive HTML reports with:
- Executive summary with key metrics
- Chart.js visualizations (bar, pie, line, scatter, radar)
- Detailed findings for each analysis tool
- Actionable recommendations
- Responsive design
- Dark mode support

```bash
qontinui-devtools report /path/to/project --output report.html
```

### CI/CD Integration

Pre-configured workflows for popular CI platforms:
- GitHub Actions
- GitLab CI
- Jenkins
- CircleCI
- Travis CI
- Azure Pipelines

Features:
- Quality gates with configurable thresholds
- PR comment generation
- Artifact upload (reports, graphs)
- Pre-commit hooks

```bash
# Setup pre-commit hooks
qontinui-devtools ci setup-hooks

# Run full CI analysis
qontinui-devtools ci analyze /path/to/project --fail-on-threshold
```

## Documentation

Comprehensive documentation is available in the `docs/` directory:

- [User Guide](docs/user-guide.md) - Complete usage guide
- [API Reference](docs/api-reference.md) - Python API documentation
- [CI/CD Integration](docs/ci-integration.md) - CI/CD setup guide
- [Architecture](docs/architecture.md) - Design and architecture
- [Table of Contents](docs/TABLE_OF_CONTENTS.md) - Complete documentation index

## Examples

The `examples/` directory contains practical examples:

```bash
# Run example scripts
poetry run python examples/detect_circular_imports.py
poetry run python examples/analyze_architecture.py
poetry run python examples/generate_report.py
poetry run python examples/test_mock_hal.py
```

Available examples:
- `detect_circular_imports.py` - Import analysis
- `analyze_architecture.py` - Architecture quality analysis
- `test_race_conditions.py` - Concurrency testing
- `generate_report.py` - Report generation
- `test_mock_hal.py` - Mock HAL usage
- `visualize_dependencies.py` - Graph visualization

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/qontinui/qontinui-devtools.git
cd qontinui-devtools

# Install dependencies
poetry install

# Install pre-commit hooks (optional)
poetry run pre-commit install
```

### Running Tests

```bash
# All tests (162 tests)
poetry run pytest

# With coverage
poetry run pytest --cov

# Specific test file
poetry run pytest python/tests/import_analysis/test_import_tracer.py

# Run in parallel
poetry run pytest -n auto
```

### Code Quality

```bash
# Format code
poetry run black python/

# Lint
poetry run ruff python/

# Type check
poetry run mypy python/

# Run all checks
poetry run black python/ && poetry run ruff python/ && poetry run mypy python/
```

### Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Test Coverage

Phases 1-4 include **200+ comprehensive tests**:

- Import Analysis: 42 tests
- Concurrency: 38 tests
- Mock HAL: 48 tests
- Architecture Analysis: 34 tests
- Runtime Monitoring: 24 tests
- Code Quality: 12 tests
- Reporting: 15 tests
- CI Integration: 12 tests
- Phase 4 Integration: 45+ tests

```bash
# Run with coverage report
poetry run pytest --cov --cov-report=html
# Open htmlcov/index.html
```

## Project Statistics

- **8,500+ lines** of documentation
- **200+ tests** with high coverage (including Phase 4 integration tests)
- **20+ CLI commands** (5 new Phase 4 command groups)
- **60+ Python modules**
- **Multiple export formats** (HTML, JSON, PNG, SVG, PDF)
- **Full type hints** throughout
- **5 Phase 4 tools** (Security, Docs, Regression, Types, Dependencies)

## Compatibility

| qontinui-devtools | qontinui | qontinui-runner | qontinui-api | qontinui-web |
|-------------------|----------|-----------------|--------------|--------------|
| v1.1.x (Phase 4)  | v1.x     | v1.x            | v1.x         | v1.x         |
| v1.0.x            | v1.x     | v1.x            | v1.x         | v1.x         |

DevTools supports the current and previous major version of Qontinui.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- [Issue Tracker](https://github.com/qontinui/qontinui-devtools/issues)
- [Discussions](https://github.com/qontinui/qontinui-devtools/discussions)
- [Documentation](https://qontinui-devtools.readthedocs.io)
- Email: support@qontinui.dev

### Phase 3: Runtime Monitoring

**Action Profiler**
- Execution performance measurement
- CPU and memory tracking
- Flame graph generation
- Performance bottleneck identification

**Event Tracer**
- System-wide event tracking
- Latency analysis across layers
- Timeline visualization
- Chrome trace format export

**Memory Profiler**
- Detailed allocation tracking
- Memory leak detection
- Growth analysis
- Interactive HTML reports

**Performance Dashboard**
- Real-time metrics monitoring
- WebSocket-based streaming
- Interactive web interface
- System health monitoring

```bash
# Profile action execution
qontinui-devtools profile action script.py --flame-graph profile.svg

# Trace events
qontinui-devtools trace events --duration 60 --html timeline.html

# Profile memory usage
qontinui-devtools profile memory --duration 120

# Start performance dashboard
qontinui-devtools dashboard --port 8765
```

### Phase 4: Advanced Analysis

**Security Analyzer**
- Hardcoded credential detection
- SQL injection vulnerability scanning
- Command injection detection
- Path traversal issue identification
- Insecure deserialization checks
- Weak cryptography detection
- Configurable severity levels
- Multiple output formats (text, JSON, HTML)

**Documentation Generator**
- Automatic API reference generation
- Module documentation extraction
- Class and function documentation
- Type hint integration
- Multiple format support (HTML, Markdown, JSON)
- Examples and usage extraction

**Regression Detector**
- Performance regression detection
- API change tracking
- Behavioral regression analysis
- Baseline snapshot management
- Test coverage comparison
- Change impact analysis

**Type Hint Analyzer**
- Type coverage calculation
- Missing type hint detection
- Type hint suggestions
- Function and parameter analysis
- Return type annotation checking
- Incremental improvement tracking

**Dependency Health Checker**
- Outdated package detection
- Security vulnerability scanning
- Deprecated package identification
- License compatibility checking
- Update command generation
- Dependency tree analysis

```bash
# Security analysis
qontinui-devtools security scan ./src --severity critical --output security.html

# Generate documentation
qontinui-devtools docs generate ./src --output docs/ --format html

# Check for regressions
qontinui-devtools regression check ./src --baseline v1.0.0

# Analyze type coverage
qontinui-devtools types coverage ./src --suggest

# Check dependency health
qontinui-devtools deps check ./ --update
```

## Roadmap

### Phase 5: ML-Enhanced Analysis (Planned)
- ML-based anomaly detection
- Intelligent code review
- Pattern learning from codebases
- Predictive issue detection

## Acknowledgments

Built with care to solve real debugging challenges encountered in the Qontinui project. Special thanks to all contributors and early adopters.

---

**Ready to improve your code quality?** [Get started now!](QUICKSTART.md)
