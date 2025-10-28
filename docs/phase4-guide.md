# Phase 4 Advanced Analysis Tools - Comprehensive Guide

> Complete guide for using Phase 4 advanced analysis tools in qontinui-devtools v1.1.0

## Table of Contents

- [Overview](#overview)
- [Security Analyzer](#security-analyzer)
- [Documentation Generator](#documentation-generator)
- [Regression Detector](#regression-detector)
- [Type Hint Analyzer](#type-hint-analyzer)
- [Dependency Health Checker](#dependency-health-checker)
- [Best Practices](#best-practices)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

---

## Overview

Phase 4 introduces five powerful advanced analysis tools designed to enhance code quality, security, and maintainability:

1. **Security Analyzer** - Detect security vulnerabilities
2. **Documentation Generator** - Auto-generate comprehensive documentation
3. **Regression Detector** - Track and prevent regressions
4. **Type Hint Analyzer** - Improve type safety
5. **Dependency Health Checker** - Monitor dependency health

All tools feature:
- CLI and Python API access
- Multiple output formats
- CI/CD integration
- Detailed reporting
- Configurable thresholds

---

## Security Analyzer

The Security Analyzer scans Python code for common security vulnerabilities and provides remediation guidance.

### Features

- **Hardcoded Credentials Detection**
  - API keys, passwords, tokens
  - Connection strings
  - Secret keys

- **SQL Injection Scanning**
  - String concatenation in queries
  - Unsafe parameterization
  - ORM misuse

- **Command Injection Detection**
  - Unsafe os.system() calls
  - subprocess with shell=True
  - User input in commands

- **Path Traversal Issues**
  - Unsafe file operations
  - Directory traversal vulnerabilities
  - Unsafe path joins

- **Insecure Deserialization**
  - Unsafe pickle usage
  - YAML load vulnerabilities
  - JSON parsing issues

- **Weak Cryptography**
  - Deprecated algorithms
  - Weak random number generation
  - Insufficient key sizes

### CLI Usage

```bash
# Basic security scan
qontinui-devtools security scan ./src

# Only critical and high severity issues
qontinui-devtools security scan ./src --severity high

# Generate HTML report
qontinui-devtools security scan ./src \
    --output security_report.html \
    --format html

# JSON output for CI/CD
qontinui-devtools security scan ./src \
    --output security.json \
    --format json \
    --severity medium
```

### Python API

```python
from qontinui_devtools.security import SecurityAnalyzer

# Create analyzer
analyzer = SecurityAnalyzer("/path/to/project")

# Run analysis
vulnerabilities = analyzer.analyze()

# Filter by severity
critical_vulns = [v for v in vulnerabilities if v.severity == "critical"]

# Generate report
analyzer.generate_report(vulnerabilities, "report.html", format="html")

# Get statistics
stats = analyzer.get_statistics()
print(f"Total vulnerabilities: {stats['total']}")
print(f"Critical: {stats['critical']}")
```

### Example Output

```
Found 3 security issues:

• SQL Injection Risk
  src/database.py:45
  Unsafe string concatenation in SQL query

• Hardcoded Credentials
  src/config.py:12
  API key hardcoded in source file

• Command Injection
  src/utils.py:78
  User input passed to os.system() without sanitization
```

### Configuration

Create `.qontinui-security.yaml`:

```yaml
severity:
  minimum: medium
  fail_on: critical

ignore:
  - pattern: "TEST_.*"  # Ignore test credentials
  - file: "tests/*"     # Skip test files

checks:
  sql_injection: true
  command_injection: true
  hardcoded_secrets: true
  path_traversal: true
  deserialization: true
  weak_crypto: true

custom_patterns:
  - name: "Internal API Key"
    pattern: "INTERNAL_KEY_.*"
    severity: high
```

---

## Documentation Generator

Automatically generates comprehensive documentation from Python source code.

### Features

- **API Reference Generation**
  - Module documentation
  - Class documentation
  - Function/method documentation
  - Type hint integration

- **Multiple Output Formats**
  - HTML (interactive, styled)
  - Markdown (GitHub-friendly)
  - JSON (machine-readable)

- **Smart Extraction**
  - Docstring parsing
  - Type hint extraction
  - Example code detection
  - Cross-reference generation

### CLI Usage

```bash
# Generate HTML documentation
qontinui-devtools docs generate ./src --output docs/

# Generate Markdown
qontinui-devtools docs generate ./src \
    --output docs/ \
    --format markdown

# Generate JSON API reference
qontinui-devtools docs generate ./src \
    --output api.json \
    --format json
```

### Python API

```python
from qontinui_devtools.documentation import DocumentationGenerator

# Create generator
generator = DocumentationGenerator("/path/to/project")

# Generate documentation
generator.generate("docs/", format="html")

# Generate specific module docs
module_docs = generator.generate_module_docs("mypackage.mymodule")

# Get API reference
api_ref = generator.get_api_reference()
```

### Example Output Structure

```
docs/
├── index.html
├── modules/
│   ├── mypackage.html
│   ├── mypackage.module1.html
│   └── mypackage.module2.html
├── classes/
│   ├── MyClass.html
│   └── AnotherClass.html
├── functions/
│   └── utilities.html
└── search.html
```

### Configuration

Create `.qontinui-docs.yaml`:

```yaml
output:
  format: html
  theme: default
  logo: docs/logo.png

include:
  - "src/**/*.py"

exclude:
  - "tests/**"
  - "**/test_*.py"
  - "**/__pycache__/**"

sections:
  - name: "Getting Started"
    file: "docs/getting-started.md"
  - name: "API Reference"
    auto: true
  - name: "Examples"
    file: "docs/examples.md"

docstring_style: google  # google, numpy, or sphinx

cross_references: true
syntax_highlighting: true
search_enabled: true
```

---

## Regression Detector

Detects performance and behavioral regressions by comparing against baseline snapshots.

### Features

- **Performance Regression Detection**
  - Execution time tracking
  - Memory usage monitoring
  - Throughput comparison

- **API Change Detection**
  - Signature changes
  - Breaking changes
  - Deprecation tracking

- **Behavioral Analysis**
  - Test coverage changes
  - Output validation
  - State change detection

- **Baseline Management**
  - Create snapshots
  - Compare versions
  - Historical tracking

### CLI Usage

```bash
# Create baseline snapshot
qontinui-devtools regression baseline ./src --name v1.0.0

# Check for regressions
qontinui-devtools regression check ./src

# Compare against specific baseline
qontinui-devtools regression check ./src --baseline v1.0.0

# Generate regression report
qontinui-devtools regression check ./src \
    --baseline v1.0.0 \
    --output regression_report.html
```

### Python API

```python
from qontinui_devtools.regression import RegressionDetector

# Create detector
detector = RegressionDetector("/path/to/project")

# Create baseline
detector.create_baseline("v1.0.0")

# Check for regressions
regressions = detector.check(baseline="v1.0.0")

# Analyze specific metrics
perf_regressions = detector.check_performance(baseline="v1.0.0")
api_changes = detector.check_api_changes(baseline="v1.0.0")

# Get regression report
report = detector.generate_report(regressions)
```

### Example Output

```
Found 2 regressions:

• Performance Regression
  Function: process_data
  Baseline: 0.5s → Current: 1.2s (140% slower)

• API Change
  Module: mypackage.utils
  Function signature changed:
    Old: def calculate(x: int) -> int
    New: def calculate(x: int, y: int = 0) -> int
```

### Configuration

Create `.qontinui-regression.yaml`:

```yaml
baselines:
  directory: ".regression-baselines"
  auto_create: true
  retention: 10  # Keep last 10 baselines

thresholds:
  performance:
    max_slowdown: 1.2  # 20% slower
    max_memory_increase: 1.3  # 30% more memory

  api:
    fail_on_breaking: true
    warn_on_signature: true

metrics:
  - execution_time
  - memory_usage
  - test_coverage
  - api_surface

notifications:
  enabled: true
  channels:
    - slack
    - email
```

---

## Type Hint Analyzer

Analyzes type hint coverage and suggests improvements for better type safety.

### Features

- **Coverage Calculation**
  - Function coverage
  - Parameter coverage
  - Return type coverage
  - Attribute coverage

- **Type Suggestions**
  - Inferred types from usage
  - Common patterns
  - Standard library types
  - Custom type hints

- **Incremental Improvement**
  - Track coverage over time
  - Set coverage goals
  - Prioritize suggestions

### CLI Usage

```bash
# Check type coverage
qontinui-devtools types coverage ./src

# Get type hint suggestions
qontinui-devtools types coverage ./src --suggest

# Generate detailed report
qontinui-devtools types coverage ./src \
    --suggest \
    --output type_report.html \
    --format html
```

### Python API

```python
from qontinui_devtools.type_analysis import TypeAnalyzer

# Create analyzer
analyzer = TypeAnalyzer("/path/to/project")

# Analyze coverage
coverage = analyzer.analyze_coverage()
print(f"Type coverage: {coverage.percentage:.1f}%")

# Get suggestions
suggestions = analyzer.suggest_types()
for suggestion in suggestions:
    print(f"{suggestion.location}: {suggestion.suggestion}")

# Check specific file
file_coverage = analyzer.analyze_file("src/mymodule.py")
```

### Example Output

```
Type coverage: 67.5%
Typed functions: 27/40
Typed parameters: 81/120

Suggestions (10):

  src/utils.py:15: def process(data) -> List[Dict[str, Any]]
  src/models.py:23: def __init__(self, value: int) -> None
  src/api.py:45: def fetch(url: str, timeout: float = 30.0) -> Response
```

### Configuration

Create `.qontinui-types.yaml`:

```yaml
coverage:
  target: 80.0  # Target 80% coverage
  strict: false

checks:
  function_returns: true
  function_parameters: true
  class_attributes: true
  variable_annotations: true

suggestions:
  enabled: true
  confidence_threshold: 0.7
  max_suggestions: 50

ignore:
  - "tests/**"
  - "**/migrations/**"
  - "**/__pycache__/**"

mypy_integration: true
```

---

## Dependency Health Checker

Monitors and analyzes project dependencies for security, freshness, and compatibility.

### Features

- **Outdated Package Detection**
  - Version comparison
  - Available updates
  - Breaking changes

- **Security Vulnerability Scanning**
  - CVE database integration
  - Severity assessment
  - Patch recommendations

- **License Compatibility**
  - License detection
  - Compatibility checking
  - Compliance reporting

- **Dependency Analysis**
  - Dependency tree
  - Unused dependencies
  - Circular dependencies

### CLI Usage

```bash
# Check dependency health
qontinui-devtools deps check ./

# Show update commands
qontinui-devtools deps check ./ --update

# Generate detailed report
qontinui-devtools deps check ./ \
    --output deps_report.html \
    --format html

# Check specific dependency file
qontinui-devtools deps check requirements.txt
```

### Python API

```python
from qontinui_devtools.dependencies import DependencyHealthChecker

# Create checker
checker = DependencyHealthChecker("/path/to/project")

# Check health
health = checker.check()
print(f"Outdated: {health.outdated}")
print(f"Vulnerabilities: {health.vulnerabilities}")

# Get update commands
updates = checker.get_update_commands()
for cmd in updates:
    print(cmd)

# Check specific package
pkg_info = checker.check_package("requests")
print(f"Current: {pkg_info.current_version}")
print(f"Latest: {pkg_info.latest_version}")
```

### Example Output

```
Total dependencies: 45
Outdated: 8
Vulnerabilities: 2

Vulnerabilities:
  • Pillow 9.0.0 → 10.0.0 (CVE-2023-XXXX) [HIGH]
  • requests 2.25.0 → 2.31.0 (CVE-2023-YYYY) [MEDIUM]

Outdated packages:
  • click 8.0.0 → 8.1.7
  • pytest 7.0.0 → 7.4.4
  • black 23.0.0 → 24.1.1

Update commands:
  pip install --upgrade pillow requests
  pip install --upgrade click pytest black
```

### Configuration

Create `.qontinui-deps.yaml`:

```yaml
sources:
  - requirements.txt
  - pyproject.toml
  - setup.py

security:
  check_vulnerabilities: true
  severity_threshold: medium
  auto_update: false

updates:
  check_outdated: true
  suggest_commands: true
  include_dev: true

licenses:
  allowed:
    - MIT
    - Apache-2.0
    - BSD-3-Clause
  disallowed:
    - GPL-3.0
  warn_on_unknown: true

ignore:
  packages:
    - internal-package  # Internal packages
  vulnerabilities:
    - CVE-2020-XXXXX   # False positive
```

---

## Best Practices

### Security Analysis

1. **Run regularly** - Include in CI/CD pipeline
2. **Fix critical issues first** - Prioritize by severity
3. **Don't hardcode secrets** - Use environment variables
4. **Validate user input** - Always sanitize
5. **Use parameterized queries** - Prevent SQL injection
6. **Keep dependencies updated** - Reduce vulnerabilities

### Documentation

1. **Write good docstrings** - Clear, concise, complete
2. **Use type hints** - Improves generated docs
3. **Include examples** - Show usage patterns
4. **Keep docs updated** - Regenerate on changes
5. **Organize logically** - Group related items
6. **Cross-reference** - Link related components

### Regression Detection

1. **Create baselines regularly** - After each release
2. **Monitor key metrics** - Performance, coverage, API
3. **Set reasonable thresholds** - Balance strictness and flexibility
4. **Investigate all regressions** - Even small ones
5. **Document changes** - Explain intentional regressions

### Type Hints

1. **Start with interfaces** - Public APIs first
2. **Be specific** - Use precise types
3. **Gradual improvement** - Don't try to do everything at once
4. **Run mypy** - Catch type errors early
5. **Document complex types** - Explain Union, Optional, etc.

### Dependency Management

1. **Regular updates** - Stay current
2. **Security first** - Fix vulnerabilities immediately
3. **Test after updates** - Ensure compatibility
4. **Pin versions** - For reproducibility
5. **Review licenses** - Ensure compliance
6. **Minimize dependencies** - Reduce attack surface

---

## CI/CD Integration

### GitHub Actions

```yaml
name: Phase 4 Analysis

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install qontinui-devtools
        run: pip install qontinui-devtools

      - name: Security Scan
        run: |
          qontinui-devtools security scan ./src \
            --severity critical \
            --output security.json \
            --format json

      - name: Upload Security Report
        uses: actions/upload-artifact@v3
        with:
          name: security-report
          path: security.json

  type-coverage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4

      - name: Check Type Coverage
        run: |
          qontinui-devtools types coverage ./src --suggest

      - name: Fail if coverage < 80%
        run: |
          coverage=$(qontinui-devtools types coverage ./src | grep -oP '\d+\.\d+')
          if (( $(echo "$coverage < 80.0" | bc -l) )); then
            echo "Type coverage $coverage% is below 80%"
            exit 1
          fi

  dependencies:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4

      - name: Check Dependencies
        run: |
          qontinui-devtools deps check ./ \
            --output deps.json \
            --format json

      - name: Check for vulnerabilities
        run: |
          qontinui-devtools deps check ./ | grep -q "Vulnerabilities: 0" || exit 1

  regression:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0  # Get full history

      - uses: actions/setup-python@v4

      - name: Check Regressions
        run: |
          qontinui-devtools regression check ./src --baseline main
```

### GitLab CI

```yaml
stages:
  - analyze
  - report

security_scan:
  stage: analyze
  script:
    - pip install qontinui-devtools
    - qontinui-devtools security scan ./src --output security.html --format html
  artifacts:
    paths:
      - security.html
    expire_in: 1 week

type_coverage:
  stage: analyze
  script:
    - qontinui-devtools types coverage ./src --suggest
  allow_failure: false

dependency_check:
  stage: analyze
  script:
    - qontinui-devtools deps check ./
  only:
    - schedules

documentation:
  stage: report
  script:
    - qontinui-devtools docs generate ./src --output docs/
  artifacts:
    paths:
      - docs/
  only:
    - main
```

### Pre-commit Hook

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: security-scan
        name: Security Scan
        entry: qontinui-devtools security scan
        args: ['--severity', 'critical']
        language: system
        pass_filenames: false

      - id: type-coverage
        name: Type Coverage
        entry: qontinui-devtools types coverage
        language: system
        pass_filenames: false
```

---

## Troubleshooting

### Security Analyzer

**Problem**: Too many false positives

**Solution**:
```yaml
# .qontinui-security.yaml
ignore:
  - pattern: "TEST_.*"
  - file: "tests/*"
```

**Problem**: Missing vulnerabilities

**Solution**: Lower severity threshold
```bash
qontinui-devtools security scan ./src --severity low
```

### Documentation Generator

**Problem**: Missing documentation

**Solution**: Ensure proper docstrings
```python
def my_function(param: str) -> int:
    """Short description.

    Longer description here.

    Args:
        param: Description

    Returns:
        Description of return value
    """
    pass
```

**Problem**: Broken links in generated docs

**Solution**: Use relative imports and proper cross-references

### Regression Detector

**Problem**: No baseline exists

**Solution**: Create one first
```bash
qontinui-devtools regression baseline ./src --name v1.0.0
```

**Problem**: False performance regressions

**Solution**: Adjust thresholds in configuration
```yaml
thresholds:
  performance:
    max_slowdown: 1.5  # Allow 50% slowdown
```

### Type Analyzer

**Problem**: Inaccurate suggestions

**Solution**: Run mypy first and fix type errors

**Problem**: Coverage percentage seems wrong

**Solution**: Check excluded files in configuration

### Dependency Checker

**Problem**: Cannot find vulnerabilities

**Solution**: Update vulnerability database
```bash
pip install --upgrade qontinui-devtools
```

**Problem**: False vulnerability reports

**Solution**: Add to ignore list
```yaml
ignore:
  vulnerabilities:
    - CVE-2023-XXXXX
```

---

## Advanced Usage

### Combining Multiple Tools

```bash
# Run all Phase 4 analyses
qontinui-devtools security scan ./src --output reports/security.html --format html
qontinui-devtools docs generate ./src --output docs/
qontinui-devtools types coverage ./src --suggest > reports/types.txt
qontinui-devtools deps check ./ --output reports/deps.json --format json
qontinui-devtools regression check ./src --baseline main
```

### Custom Scripts

```python
from qontinui_devtools import (
    SecurityAnalyzer,
    DocumentationGenerator,
    RegressionDetector,
    TypeAnalyzer,
    DependencyHealthChecker
)

def full_analysis(project_path):
    """Run complete Phase 4 analysis."""

    # Security
    security = SecurityAnalyzer(project_path)
    vulns = security.analyze()

    # Types
    types = TypeAnalyzer(project_path)
    coverage = types.analyze_coverage()

    # Dependencies
    deps = DependencyHealthChecker(project_path)
    health = deps.check()

    # Generate unified report
    report = {
        'security': {'vulnerabilities': len(vulns)},
        'types': {'coverage': coverage.percentage},
        'dependencies': {
            'outdated': health.outdated,
            'vulnerabilities': health.vulnerabilities
        }
    }

    return report
```

---

## Getting Help

- [GitHub Issues](https://github.com/qontinui/qontinui-devtools/issues)
- [Documentation](https://qontinui-devtools.readthedocs.io)
- [Discussions](https://github.com/qontinui/qontinui-devtools/discussions)

---

*Last updated: October 28, 2025*
*Version: 1.1.0*
