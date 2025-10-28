# Development Guide

Welcome to qontinui-devtools development! This guide will help you set up your development environment and contribute to the project.

## Prerequisites

- Python 3.11 or higher
- Poetry 1.5 or higher
- Git
- (Optional) Graphviz for graph visualizations

### Installing Prerequisites

**Python 3.11+**
```bash
# Check version
python --version

# Install via pyenv (recommended)
pyenv install 3.11.0
pyenv local 3.11.0
```

**Poetry**
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Or via pipx
pipx install poetry

# Verify installation
poetry --version
```

**Graphviz** (Optional, for graph visualization)
```bash
# macOS
brew install graphviz

# Ubuntu/Debian
sudo apt-get install graphviz

# Windows (via chocolatey)
choco install graphviz
```

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/qontinui/qontinui-devtools.git
cd qontinui-devtools
```

### 2. Install Dependencies

```bash
# Install all dependencies including dev dependencies
poetry install

# Install with optional dependencies (e.g., memray for memory profiling)
poetry install --extras all
```

### 3. Activate Virtual Environment

```bash
# Activate Poetry shell
poetry shell

# Or prefix commands with `poetry run`
poetry run pytest
```

### 4. Verify Installation

```bash
# Run verification script
poetry run python scripts/verify_installation.py

# Run tests
poetry run pytest

# Check CLI
poetry run qontinui-devtools --version
```

## Development Workflow

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov

# Run specific test file
poetry run pytest python/tests/import_analysis/test_import_tracer.py

# Run specific test
poetry run pytest python/tests/import_analysis/test_import_tracer.py::test_basic_import_detection

# Run tests in parallel (faster)
poetry run pytest -n auto

# Run only unit tests
poetry run pytest -m unit

# Run only integration tests
poetry run pytest -m integration

# Skip slow tests
poetry run pytest -m "not slow"

# Generate HTML coverage report
poetry run pytest --cov --cov-report=html
# Open htmlcov/index.html in browser
```

### Code Quality

#### Formatting with Black

```bash
# Format all Python files
poetry run black python/

# Check formatting without modifying
poetry run black --check python/

# Format specific file
poetry run black python/qontinui_devtools/import_analysis/import_tracer.py
```

#### Linting with Ruff

```bash
# Lint all files
poetry run ruff check python/

# Auto-fix issues
poetry run ruff check --fix python/

# Lint specific file
poetry run ruff check python/qontinui_devtools/import_analysis/import_tracer.py
```

#### Type Checking with MyPy

```bash
# Type check all files
poetry run mypy python/

# Type check specific module
poetry run mypy python/qontinui_devtools/import_analysis

# Generate HTML report
poetry run mypy python/ --html-report mypy-report
```

#### Run All Quality Checks

```bash
# Run all checks in sequence
poetry run black python/ && \
poetry run ruff check python/ && \
poetry run mypy python/ && \
poetry run pytest

# Or create an alias
alias qa="poetry run black python/ && poetry run ruff check python/ && poetry run mypy python/ && poetry run pytest"
```

### Pre-commit Hooks (Optional)

```bash
# Install pre-commit
poetry run pip install pre-commit

# Install hooks
poetry run pre-commit install

# Run manually
poetry run pre-commit run --all-files
```

## Project Structure

```
qontinui-devtools/
├── python/
│   ├── qontinui_devtools/         # Main package
│   │   ├── __init__.py            # Package exports
│   │   ├── cli.py                 # CLI entry point
│   │   ├── import_analysis/       # Import analysis tools
│   │   ├── concurrency/           # Concurrency analysis
│   │   ├── testing/               # Mock HAL and testing utilities
│   │   ├── architecture/          # Architecture analysis
│   │   ├── reporting/             # HTML reporting
│   │   └── ci/                    # CI/CD integration
│   └── tests/                     # Test suite
│       ├── import_analysis/
│       ├── concurrency/
│       ├── testing/
│       ├── architecture/
│       ├── reporting/
│       └── fixtures/              # Test fixtures
├── docs/                          # Documentation
├── examples/                      # Example scripts
├── scripts/                       # Utility scripts
├── pyproject.toml                 # Poetry configuration
├── README.md                      # Main README
├── CHANGELOG.md                   # Change log
├── CONTRIBUTING.md                # Contribution guidelines
├── QUICKSTART.md                  # Quick start guide
└── DEVELOPMENT.md                 # This file
```

## Adding New Features

### 1. Create a New Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Implement Your Feature

Follow these guidelines:
- Write type hints for all functions
- Add docstrings (Google style)
- Follow existing code patterns
- Keep functions focused and small
- Use meaningful variable names

Example:
```python
from typing import List, Optional

def analyze_module(
    module_path: str,
    max_depth: int = 10,
    exclude_patterns: Optional[List[str]] = None
) -> AnalysisResult:
    """Analyze a Python module for issues.

    Args:
        module_path: Path to the module to analyze
        max_depth: Maximum depth to traverse (default: 10)
        exclude_patterns: Patterns to exclude from analysis

    Returns:
        AnalysisResult containing findings

    Raises:
        FileNotFoundError: If module_path doesn't exist
        ValueError: If max_depth is negative
    """
    # Implementation here
    pass
```

### 3. Write Tests

Add tests in `python/tests/`:

```python
import pytest
from qontinui_devtools.your_module import YourClass


class TestYourClass:
    """Tests for YourClass."""

    def test_basic_functionality(self) -> None:
        """Test basic functionality works."""
        instance = YourClass()
        result = instance.do_something()
        assert result == expected_value

    def test_error_handling(self) -> None:
        """Test error handling."""
        instance = YourClass()
        with pytest.raises(ValueError):
            instance.do_something_invalid()

    @pytest.mark.parametrize("input_val,expected", [
        (1, 2),
        (2, 4),
        (3, 6),
    ])
    def test_multiple_inputs(self, input_val: int, expected: int) -> None:
        """Test with multiple inputs."""
        instance = YourClass()
        result = instance.double(input_val)
        assert result == expected
```

### 4. Update Documentation

- Add docstrings to all public functions/classes
- Update relevant documentation in `docs/`
- Add examples to `examples/` if applicable
- Update README.md if adding major features

### 5. Run Quality Checks

```bash
# Format code
poetry run black python/

# Lint
poetry run ruff check --fix python/

# Type check
poetry run mypy python/

# Run tests
poetry run pytest --cov
```

### 6. Commit Your Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "Add feature: description of what you added"

# Push to GitHub
git push origin feature/your-feature-name
```

### 7. Create Pull Request

1. Go to GitHub repository
2. Click "New Pull Request"
3. Select your branch
4. Fill in PR template
5. Request review

## Debugging

### Debug with IPython

```python
# Add breakpoint in your code
import IPython; IPython.embed()

# Run your code
poetry run python your_script.py
```

### Debug Tests with pytest

```bash
# Run with verbose output
poetry run pytest -vv

# Show print statements
poetry run pytest -s

# Drop into debugger on failure
poetry run pytest --pdb

# Drop into debugger at start of test
poetry run pytest --trace
```

### Debug CLI Commands

```bash
# Use --verbose flag
poetry run qontinui-devtools --verbose import check /path/to/project

# Use --debug flag
poetry run qontinui-devtools --debug architecture god-classes /path/to/project
```

## Testing Strategies

### Unit Tests

Test individual functions/methods in isolation:

```python
def test_calculate_lcom() -> None:
    """Test LCOM calculation."""
    methods = [{"attrs": {"a", "b"}}, {"attrs": {"c", "d"}}]
    result = calculate_lcom(methods)
    assert result == 1.0
```

### Integration Tests

Test multiple components together:

```python
@pytest.mark.integration
def test_full_analysis_workflow(tmp_path: Path) -> None:
    """Test complete analysis workflow."""
    # Create test files
    create_test_module(tmp_path / "module.py")

    # Run analysis
    detector = GodClassDetector()
    results = detector.analyze_directory(str(tmp_path))

    # Verify results
    assert len(results.god_classes) > 0
```

### Fixtures

Use fixtures for reusable test data:

```python
@pytest.fixture
def sample_module(tmp_path: Path) -> Path:
    """Create a sample module for testing."""
    module_path = tmp_path / "sample.py"
    module_path.write_text("""
class SampleClass:
    def method1(self): pass
    def method2(self): pass
""")
    return module_path


def test_with_fixture(sample_module: Path) -> None:
    """Test using fixture."""
    detector = GodClassDetector()
    results = detector.analyze_file(str(sample_module))
    assert results is not None
```

## Performance Optimization

### Profiling

```bash
# Profile with cProfile
poetry run python -m cProfile -o profile.stats your_script.py

# Analyze with snakeviz
poetry run pip install snakeviz
poetry run snakeviz profile.stats

# Profile with py-spy
poetry run py-spy record -o profile.svg -- python your_script.py
```

### Benchmarking

```python
import time

def benchmark_function() -> None:
    """Benchmark a function."""
    iterations = 1000
    start = time.time()

    for _ in range(iterations):
        your_function()

    elapsed = time.time() - start
    print(f"Average time: {elapsed/iterations:.6f}s")
```

## Documentation

### Building Documentation

```bash
# Generate API docs (if using Sphinx)
cd docs
poetry run sphinx-build -b html . _build

# Or use mkdocs (if configured)
poetry run mkdocs build
poetry run mkdocs serve  # Local preview
```

### Writing Documentation

- Use Markdown for all documentation
- Follow Google style for docstrings
- Include code examples
- Add type hints to all examples
- Keep it concise and actionable

## Release Process

### 1. Update Version

```bash
# Update version in pyproject.toml
poetry version minor  # or major, patch

# Update __version__ in __init__.py
```

### 2. Update CHANGELOG.md

Add new release section with all changes

### 3. Run Full Test Suite

```bash
poetry run pytest --cov
poetry run black --check python/
poetry run ruff check python/
poetry run mypy python/
```

### 4. Create Git Tag

```bash
git add .
git commit -m "Release v1.0.0"
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin main --tags
```

### 5. Build and Publish

```bash
# Build package
poetry build

# Publish to PyPI (requires credentials)
poetry publish

# Or publish to test PyPI first
poetry publish -r testpypi
```

## Troubleshooting

### Issue: Import Errors

```bash
# Solution: Reinstall in editable mode
poetry install
```

### Issue: Test Failures

```bash
# Solution: Clear pytest cache
poetry run pytest --cache-clear
rm -rf .pytest_cache
```

### Issue: Type Check Errors

```bash
# Solution: Update mypy cache
poetry run mypy --install-types
rm -rf .mypy_cache
```

### Issue: Poetry Lock Errors

```bash
# Solution: Update lock file
poetry lock --no-update
poetry install
```

## Getting Help

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/qontinui/qontinui-devtools/issues)
- **Discussions**: [GitHub Discussions](https://github.com/qontinui/qontinui-devtools/discussions)
- **Contributing Guide**: [CONTRIBUTING.md](CONTRIBUTING.md)

## Code of Conduct

Please be respectful and constructive in all interactions. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for details.

## License

By contributing to qontinui-devtools, you agree that your contributions will be licensed under the MIT License.

---

**Happy coding!** Thanks for contributing to qontinui-devtools!
