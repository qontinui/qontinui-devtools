# Contributing to Qontinui DevTools

Thank you for your interest in contributing to Qontinui DevTools! This document provides guidelines and instructions for contributing.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Development Workflow](#development-workflow)
5. [Code Style](#code-style)
6. [Testing](#testing)
7. [Documentation](#documentation)
8. [Pull Request Process](#pull-request-process)
9. [Reporting Bugs](#reporting-bugs)
10. [Suggesting Features](#suggesting-features)

---

## Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

**Positive behaviors:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behaviors:**
- Trolling, insulting/derogatory comments, and personal attacks
- Public or private harassment
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

---

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- Poetry (for dependency management)
- (Optional) Graphviz for visualization features

### Quick Start

```bash
# Clone the repository
git clone https://github.com/qontinui/qontinui-devtools.git
cd qontinui-devtools

# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install --with dev

# Activate virtual environment
poetry shell

# Verify installation
qontinui-devtools --version

# Run tests
pytest
```

---

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/qontinui-devtools.git
cd qontinui-devtools

# Add upstream remote
git remote add upstream https://github.com/qontinui/qontinui-devtools.git
```

### 2. Install Development Dependencies

```bash
# Install all dependencies including dev tools
poetry install --with dev --all-extras

# Install pre-commit hooks
pre-commit install
```

### 3. Verify Setup

```bash
# Run tests
poetry run pytest

# Check code style
poetry run black --check python/
poetry run ruff python/

# Type checking
poetry run mypy python/

# All checks at once
poetry run pytest && \
poetry run black --check python/ && \
poetry run ruff python/ && \
poetry run mypy python/
```

### 4. IDE Setup

#### VS Code

Install recommended extensions:
- Python (Microsoft)
- Pylance
- Black Formatter
- Ruff

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.formatting.provider": "black",
  "python.linting.ruffEnabled": true,
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

#### PyCharm

1. Go to: Settings → Project → Python Interpreter
2. Select: Poetry Environment
3. Enable: Settings → Tools → Python Integrated Tools → Pytest
4. Configure: Settings → Editor → Code Style → Python
   - Scheme: Black
   - Line length: 100

---

## Development Workflow

### 1. Create a Branch

```bash
# Update main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/bug-description
```

**Branch Naming:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions/fixes

### 2. Make Changes

```bash
# Make your changes
vim python/qontinui_devtools/your_module.py

# Run tests frequently
pytest python/tests/test_your_module.py

# Check code style
black python/qontinui_devtools/your_module.py
ruff python/qontinui_devtools/your_module.py

# Type check
mypy python/qontinui_devtools/your_module.py
```

### 3. Commit Changes

```bash
# Stage changes
git add python/qontinui_devtools/your_module.py

# Commit with descriptive message
git commit -m "Add feature X to improve Y

- Implement feature X
- Add tests for X
- Update documentation

Fixes #123"
```

**Commit Message Format:**

```
Short summary (50 chars or less)

Detailed explanation of the changes:
- What was changed
- Why it was changed
- Any important details

References: #issue_number
```

### 4. Push and Create PR

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create Pull Request on GitHub
# Fill in the PR template
```

---

## Code Style

### Python Style Guide

We follow PEP 8 with some modifications:

- **Line length:** 100 characters (not 80)
- **Formatter:** Black (automatic)
- **Import sorting:** isort (automatic)
- **Linter:** Ruff

### Code Formatting

```bash
# Format code
black python/

# Sort imports
isort python/

# Lint
ruff python/

# Or use pre-commit
pre-commit run --all-files
```

### Type Hints

**All functions must have type hints:**

```python
# Good
def analyze_file(file_path: str, exclude: list[str] | None = None) -> list[Issue]:
    """Analyze a Python file for issues."""
    pass

# Bad
def analyze_file(file_path, exclude=None):
    pass
```

### Docstrings

**Use Google-style docstrings:**

```python
def function_name(param1: str, param2: int) -> bool:
    """Short description of function.

    Longer description with more details about what the function
    does and how it works.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param1 is empty
        IOError: When file cannot be read

    Example:
        >>> function_name("test", 42)
        True
    """
    pass
```

### Error Handling

**Always handle errors appropriately:**

```python
# Good
try:
    result = risky_operation()
except SpecificError as e:
    logger.error("Operation failed", error=str(e))
    raise AnalysisError(f"Failed to analyze: {e}") from e

# Bad
try:
    result = risky_operation()
except:
    pass
```

### Logging

**Use structured logging:**

```python
from qontinui_devtools.utils import get_logger

logger = get_logger(__name__)

# Good
logger.info("Analysis started", path=path, files=len(files))
logger.error("Analysis failed", path=path, error=str(e))

# Bad
print(f"Analyzing {path}")
```

---

## Testing

### Test Structure

```
python/tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
└── fixtures/       # Test fixtures and data
```

### Writing Tests

**Use pytest:**

```python
import pytest
from qontinui_devtools import CircularDependencyDetector

def test_detect_circular_dependency():
    """Test circular dependency detection."""
    # Arrange
    detector = CircularDependencyDetector("tests/fixtures/circular")

    # Act
    cycles = detector.analyze()

    # Assert
    assert len(cycles) == 1
    assert "module_a" in cycles[0].cycle
    assert "module_b" in cycles[0].cycle

def test_no_circular_dependency():
    """Test when no circular dependencies exist."""
    detector = CircularDependencyDetector("tests/fixtures/clean")
    cycles = detector.analyze()
    assert len(cycles) == 0

@pytest.mark.parametrize("path,expected", [
    ("tests/fixtures/simple", 0),
    ("tests/fixtures/circular", 1),
    ("tests/fixtures/complex", 3),
])
def test_multiple_scenarios(path: str, expected: int):
    """Test multiple scenarios."""
    detector = CircularDependencyDetector(path)
    cycles = detector.analyze()
    assert len(cycles) == expected
```

### Test Coverage

**Maintain >90% test coverage:**

```bash
# Run tests with coverage
pytest --cov=qontinui_devtools --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Test Markers

```python
# Unit test (fast)
@pytest.mark.unit
def test_unit():
    pass

# Integration test (slower)
@pytest.mark.integration
def test_integration():
    pass

# Slow test
@pytest.mark.slow
def test_slow():
    pass
```

**Run specific tests:**

```bash
# Only unit tests
pytest -m unit

# Skip slow tests
pytest -m "not slow"

# Only integration tests
pytest -m integration
```

---

## Documentation

### Documentation Standards

1. **All public APIs must be documented**
2. **Use clear, concise language**
3. **Include examples**
4. **Keep documentation up-to-date with code**

### Writing Documentation

```markdown
# Feature Name

Brief description of the feature.

## Usage

Basic usage example:

\`\`\`python
from qontinui_devtools import Feature

feature = Feature()
result = feature.do_something()
\`\`\`

## Parameters

- `param1` (str): Description of param1
- `param2` (int, optional): Description of param2. Default: 42

## Returns

Description of what is returned.

## Examples

### Example 1: Basic Usage

\`\`\`python
result = feature.do_something()
print(result)
\`\`\`

### Example 2: Advanced Usage

\`\`\`python
result = feature.do_something(param1="custom")
\`\`\`
```

### Building Documentation

```bash
# Install documentation dependencies
poetry install --with docs

# Build docs
cd docs
make html

# View docs
open _build/html/index.html
```

---

## Pull Request Process

### Before Submitting

**Checklist:**
- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New tests added for new functionality
- [ ] Documentation updated
- [ ] Type hints added
- [ ] Commit messages are clear
- [ ] No merge conflicts with main

### PR Template

```markdown
## Description

Brief description of changes.

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update

## How Has This Been Tested?

Describe the tests you ran.

## Checklist

- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published
```

### Review Process

1. **Automated Checks:** Must pass all CI checks
2. **Code Review:** Requires approval from maintainer
3. **Testing:** Reviewer may request additional tests
4. **Documentation:** Ensure docs are updated
5. **Merge:** Maintainer will merge when ready

### After Merge

```bash
# Update your main branch
git checkout main
git pull upstream main

# Delete feature branch
git branch -d feature/your-feature-name
git push origin --delete feature/your-feature-name
```

---

## Reporting Bugs

### Before Reporting

1. **Search existing issues** to avoid duplicates
2. **Try the latest version** to see if it's fixed
3. **Gather information** about the bug

### Bug Report Template

```markdown
## Bug Description

Clear and concise description of the bug.

## Steps to Reproduce

1. Go to '...'
2. Run command '....'
3. See error

## Expected Behavior

What you expected to happen.

## Actual Behavior

What actually happened.

## Environment

- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.11.2]
- DevTools version: [e.g., 0.1.0]
- Installation method: [pip/poetry/source]

## Additional Context

Any other context, screenshots, or logs.

## Possible Solution

Optional: Your ideas on how to fix it.
```

---

## Suggesting Features

### Feature Request Template

```markdown
## Feature Description

Clear and concise description of the feature.

## Problem Statement

What problem does this feature solve?

## Proposed Solution

How should this feature work?

## Alternatives Considered

What other solutions did you consider?

## Use Cases

Examples of how this feature would be used:

1. Use case 1...
2. Use case 2...

## Implementation Notes

Optional: Ideas on how to implement this.
```

---

## Development Tips

### Running Specific Tests

```bash
# Run single test
pytest python/tests/test_import_analysis.py::test_circular_dependency

# Run tests matching pattern
pytest -k "test_circular"

# Run with verbose output
pytest -v

# Run with print output
pytest -s
```

### Debugging

```python
# Use pytest with pdb
pytest --pdb

# Or add breakpoint in code
def function():
    import pdb; pdb.set_trace()
    # or
    breakpoint()
```

### Performance Testing

```bash
# Profile tests
pytest --profile

# Benchmark specific test
pytest --benchmark-only
```

### Local CLI Testing

```bash
# Install in development mode
pip install -e .

# Run CLI
qontinui-devtools --help

# Or use poetry
poetry run qontinui-devtools --help
```

---

## Release Process

(For Maintainers)

### Version Bumping

```bash
# Update version in pyproject.toml
poetry version patch  # 0.1.0 -> 0.1.1
poetry version minor  # 0.1.0 -> 0.2.0
poetry version major  # 0.1.0 -> 1.0.0
```

### Release Checklist

- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped
- [ ] Git tag created
- [ ] PyPI package published
- [ ] GitHub release created

---

## Getting Help

### Resources

- **Documentation:** https://qontinui-devtools.readthedocs.io
- **Issues:** https://github.com/qontinui/qontinui-devtools/issues
- **Discussions:** https://github.com/qontinui/qontinui-devtools/discussions

### Contact

- **GitHub Issues:** For bugs and feature requests
- **Discussions:** For questions and general discussion
- **Email:** dev@qontinui.com

---

## Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- GitHub contributors page
- Release notes

Thank you for contributing to Qontinui DevTools!

---

**Version:** 0.1.0
**Last Updated:** 2025-10-28
**License:** MIT
