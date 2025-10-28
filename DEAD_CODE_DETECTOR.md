# Dead Code Detector

## Overview

The Dead Code Detector is a static analysis tool that identifies unused code in Python projects. It helps reduce code clutter, improve maintainability, and make codebases cleaner by finding:

- **Unused Functions**: Functions that are defined but never called
- **Unused Classes**: Classes that are defined but never instantiated
- **Unused Imports**: Imported modules that are never used
- **Unused Variables**: Module-level variables that are never referenced

## Features

### Static Analysis
- **AST-based detection**: Uses Python's Abstract Syntax Tree for accurate analysis
- **Cross-file tracking**: Detects usage across multiple files in a project
- **Confidence scoring**: Each dead code item has a confidence level (0-1)
- **Low false positives**: Smart filtering reduces incorrect flagging

### Smart Detection
- **Special method handling**: Automatically excludes `__init__`, `__str__`, etc.
- **Entry point awareness**: Lower confidence for `main()`, `setup()`, test fixtures
- **Attribute tracking**: Detects module.function() usage patterns
- **Private method handling**: Includes private methods but flags carefully

### Flexible Filtering
- **By type**: Filter by functions, classes, imports, or variables
- **By confidence**: Set minimum confidence threshold
- **Multiple output formats**: Text, JSON, CSV

## Installation

The Dead Code Detector is part of qontinui-devtools:

```bash
pip install qontinui-devtools
```

## Usage

### Command Line Interface

#### Basic Usage

```bash
# Detect all types of dead code
qontinui-devtools quality dead-code ./src

# Find only unused imports
qontinui-devtools quality dead-code ./src --type imports

# Find only unused functions
qontinui-devtools quality dead-code ./src --type functions

# High confidence items only
qontinui-devtools quality dead-code ./src --min-confidence 0.8
```

#### Output Formats

```bash
# Save to text file
qontinui-devtools quality dead-code ./src --output report.txt

# Save as JSON
qontinui-devtools quality dead-code ./src --output report.json --format json

# Save as CSV
qontinui-devtools quality dead-code ./src --output report.csv --format csv
```

### Python API

```python
from qontinui_devtools.code_quality import DeadCodeDetector

# Create detector
detector = DeadCodeDetector("./src")

# Find all dead code
all_dead_code = detector.analyze()

# Find specific types
unused_functions = detector.find_unused_functions()
unused_classes = detector.find_unused_classes()
unused_imports = detector.find_unused_imports()
unused_variables = detector.find_unused_variables()

# Get statistics
stats = detector.get_stats()
print(f"Total dead code items: {stats['total']}")
print(f"Functions: {stats['functions']}")
print(f"Classes: {stats['classes']}")
print(f"Imports: {stats['imports']}")
print(f"Variables: {stats['variables']}")

# Filter by confidence
high_confidence = [dc for dc in all_dead_code if dc.confidence > 0.8]
```

### DeadCode Object

Each dead code item is represented by a `DeadCode` dataclass:

```python
@dataclass
class DeadCode:
    type: str           # "function", "class", "import", "variable"
    name: str           # Name of the unused element
    file_path: str      # Path to file containing the dead code
    line_number: int    # Line number where it's defined
    reason: str         # Explanation of why it's dead
    confidence: float   # Confidence level (0-1)
```

## Examples

### Example 1: Basic Detection

```python
from qontinui_devtools.code_quality import DeadCodeDetector

detector = DeadCodeDetector("./my_project")
dead_code = detector.analyze()

for dc in dead_code:
    print(f"{dc.type}: {dc.name} at {dc.file_path}:{dc.line_number}")
    print(f"  Confidence: {dc.confidence:.2f}")
    print(f"  Reason: {dc.reason}")
    print()
```

### Example 2: Finding Unused Imports Only

```python
from qontinui_devtools.code_quality import DeadCodeDetector

detector = DeadCodeDetector("./my_project")
unused_imports = detector.find_unused_imports()

print(f"Found {len(unused_imports)} unused imports:")
for imp in unused_imports:
    print(f"  - {imp.name} in {imp.file_path}:{imp.line_number}")
```

### Example 3: High Confidence Cleanup

```python
from qontinui_devtools.code_quality import DeadCodeDetector

detector = DeadCodeDetector("./my_project")
dead_code = detector.analyze()

# Focus on high confidence items
high_confidence = [dc for dc in dead_code if dc.confidence > 0.9]

print(f"High confidence dead code ({len(high_confidence)} items):")
for dc in high_confidence:
    print(f"  {dc.name} ({dc.type}) - {dc.file_path}:{dc.line_number}")
```

## How It Works

### Detection Process

1. **File Discovery**: Finds all Python files in the project
   - Skips common directories: `__pycache__`, `.git`, `venv`, etc.

2. **Definition Collection**: For each file, collects:
   - Function definitions (module and class level)
   - Class definitions
   - Import statements
   - Module-level variable assignments

3. **Usage Collection**: For each file, tracks:
   - Name references (`Load` and `Del` contexts)
   - Function calls (direct and method calls)
   - Attribute access (e.g., `module.function()`)

4. **Analysis**: Compares definitions to usages
   - Cross-references all files in the project
   - Calculates confidence based on patterns
   - Generates dead code reports

### Confidence Calculation

The detector assigns confidence levels based on various factors:

| Pattern | Confidence | Reason |
|---------|-----------|---------|
| Regular unused code | 0.85 | Standard case |
| Unused imports | 0.95 | Very reliable |
| Entry points (`main`, `setup`) | 0.3 | Might be called externally |
| Test fixtures (`test_*`, `fixture_*`) | 0.4 | Might be discovered dynamically |
| CLI commands (`*_command`, `*_cli`) | 0.5 | Might be registered via decorators |

### Limitations

1. **Dynamic code execution**: Cannot detect usage via:
   - `getattr()`, `setattr()`
   - `eval()`, `exec()`
   - String-based imports
   - Decorators that register functions

2. **Public APIs**: Code might be:
   - Part of a library's public interface
   - Called by external code
   - Used via plugin systems

3. **Special patterns**:
   - Test fixtures discovered by pytest
   - CLI commands registered via decorators
   - Callback functions stored in data structures

## Best Practices

### 1. Review Before Deleting

Always review flagged code before removing it:

```bash
# Generate a report first
qontinui-devtools quality dead-code ./src --output review.txt

# Review the report
cat review.txt

# Then carefully remove confirmed dead code
```

### 2. Start with High Confidence

Begin with items you're most confident about:

```bash
# Start with unused imports (confidence: 0.95)
qontinui-devtools quality dead-code ./src --type imports

# Then high confidence code
qontinui-devtools quality dead-code ./src --min-confidence 0.8
```

### 3. Check for Public APIs

Before removing code, consider:
- Is this part of a public API?
- Could external code be using this?
- Is this documented in user-facing docs?

### 4. Test After Removal

Always run tests after removing dead code:

```bash
# Remove dead code
# ... make changes ...

# Run tests
pytest

# Run type checking
mypy src/

# Verify the app still works
```

### 5. Gradual Cleanup

Clean up dead code gradually:

```bash
# Week 1: Remove unused imports
qontinui-devtools quality dead-code ./src --type imports --output imports.txt

# Week 2: Remove unused variables
qontinui-devtools quality dead-code ./src --type variables --output vars.txt

# Week 3: Review functions/classes more carefully
qontinui-devtools quality dead-code ./src --type functions --output funcs.txt
```

## Integration with CI/CD

### Pre-commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: dead-code-check
        name: Check for dead code
        entry: python -m qontinui_devtools.cli quality dead-code
        language: system
        args: ['--min-confidence', '0.9', '--type', 'imports']
        pass_filenames: false
```

### GitHub Actions

```yaml
name: Code Quality

on: [push, pull_request]

jobs:
  dead-code:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install qontinui-devtools
      - name: Check for dead code
        run: |
          qontinui-devtools quality dead-code ./src \
            --output dead_code.json \
            --format json
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: dead-code-report
          path: dead_code.json
```

### GitLab CI

```yaml
dead-code-check:
  stage: quality
  script:
    - pip install qontinui-devtools
    - qontinui-devtools quality dead-code ./src --min-confidence 0.8
  artifacts:
    paths:
      - dead_code_report.txt
    when: always
```

## Output Examples

### Text Output

```
Found 8 pieces of dead code:

          Dead Code Summary
┏━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Type      ┃ Count ┃ Avg Confidence ┃
┡━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ Imports   │     4 │           0.95 │
│ Variables │     1 │           0.85 │
│ Functions │     2 │           0.85 │
│ Classes   │     1 │           0.85 │
└───────────┴───────┴────────────────┘

Imports (4):
  • os (confidence: 0.95)
    /path/to/file.py:2
    Import 'os' is never used

Functions (2):
  • unused_function (confidence: 0.85)
    /path/to/file.py:40
    Function 'unused_function' is defined but never called
```

### JSON Output

```json
[
  {
    "type": "function",
    "name": "unused_function",
    "file_path": "/path/to/file.py",
    "line_number": 40,
    "reason": "Function 'unused_function' is defined but never called",
    "confidence": 0.85
  },
  {
    "type": "import",
    "name": "os",
    "file_path": "/path/to/file.py",
    "line_number": 2,
    "reason": "Import 'os' is never used",
    "confidence": 0.95
  }
]
```

### CSV Output

```csv
Type,Name,File,Line,Confidence,Reason
function,unused_function,/path/to/file.py,40,0.85,Function 'unused_function' is defined but never called
import,os,/path/to/file.py,2,0.95,Import 'os' is never used
```

## Troubleshooting

### False Positives

If you see false positives:

1. **Check for dynamic usage**:
   ```python
   # This won't be detected
   func_name = "my_function"
   getattr(module, func_name)()
   ```

2. **Check for decorator registration**:
   ```python
   @app.route("/endpoint")  # Registered via decorator
   def handler():
       pass
   ```

3. **Check for plugin systems**:
   ```python
   # Discovered via entry points
   def plugin_function():
       pass
   ```

### Performance Issues

For large codebases:

1. **Exclude test directories**: Tests often have lower quality standards
2. **Run incrementally**: Analyze one module at a time
3. **Use caching**: The detector doesn't cache yet, but you can run periodically

### Unexpected Results

If results seem wrong:

1. **Check file discovery**: Ensure all Python files are found
2. **Check syntax errors**: Files with syntax errors are skipped
3. **Check import paths**: Relative imports might not be tracked correctly

## API Reference

### DeadCodeDetector

```python
class DeadCodeDetector:
    def __init__(self, root_path: str) -> None:
        """Initialize detector with project root path."""

    def analyze(self) -> list[DeadCode]:
        """Find all dead code in the project."""

    def find_unused_functions(self) -> list[DeadCode]:
        """Find unused functions only."""

    def find_unused_classes(self) -> list[DeadCode]:
        """Find unused classes only."""

    def find_unused_imports(self) -> list[DeadCode]:
        """Find unused imports only."""

    def find_unused_variables(self) -> list[DeadCode]:
        """Find unused module-level variables only."""

    def get_stats(self) -> dict[str, int]:
        """Get statistics about dead code."""
```

### DeadCode

```python
@dataclass
class DeadCode:
    type: str           # "function", "class", "import", "variable"
    name: str           # Name of the unused element
    file_path: str      # Path to the file
    line_number: int    # Line number in file
    reason: str         # Explanation
    confidence: float   # Confidence level (0-1)
```

## Contributing

Contributions are welcome! Areas for improvement:

1. **Better dynamic detection**: Handle `getattr()`, decorators, etc.
2. **Configuration files**: Support for `.deadcoderc` config
3. **Incremental analysis**: Cache results for faster re-analysis
4. **IDE integration**: VS Code extension, PyCharm plugin
5. **Auto-fix**: Automatically remove safe dead code

## License

MIT License - see LICENSE file for details.

## See Also

- [Import Analysis](./docs/import_analysis.md) - Circular dependency detection
- [Architecture Analysis](./docs/architecture.md) - God class detection
- [Code Quality Tools](./docs/code_quality.md) - Other quality checks
