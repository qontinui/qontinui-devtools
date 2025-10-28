# Dead Code Detector - Quick Start Guide

## Installation

```bash
pip install qontinui-devtools
```

## 5-Minute Quick Start

### 1. Basic Usage

```bash
# Detect all dead code in your project
qontinui-devtools quality dead-code ./src
```

### 2. Find Unused Imports (Safest to Remove)

```bash
# High confidence, easy wins
qontinui-devtools quality dead-code ./src --type imports
```

### 3. Generate Report

```bash
# Save results for review
qontinui-devtools quality dead-code ./src --output dead_code.txt
```

### 4. High Confidence Only

```bash
# Focus on items you can confidently remove
qontinui-devtools quality dead-code ./src --min-confidence 0.8
```

### 5. Python API

```python
from qontinui_devtools.code_quality import DeadCodeDetector

# Analyze project
detector = DeadCodeDetector("./src")
dead_code = detector.analyze()

# Print results
for dc in dead_code:
    print(f"{dc.name} ({dc.type}) - {dc.file_path}:{dc.line_number}")
```

## Common Commands

| Task | Command |
|------|---------|
| Find all dead code | `qontinui-devtools quality dead-code ./src` |
| Find unused imports | `qontinui-devtools quality dead-code ./src --type imports` |
| Find unused functions | `qontinui-devtools quality dead-code ./src --type functions` |
| Find unused classes | `qontinui-devtools quality dead-code ./src --type classes` |
| High confidence only | `qontinui-devtools quality dead-code ./src --min-confidence 0.8` |
| Save to JSON | `qontinui-devtools quality dead-code ./src --output report.json --format json` |
| Save to CSV | `qontinui-devtools quality dead-code ./src --output report.csv --format csv` |

## Workflow

### Step 1: Generate Report
```bash
qontinui-devtools quality dead-code ./src --output review.txt
```

### Step 2: Review Report
```bash
cat review.txt
# Or open in your editor
```

### Step 3: Start with Safe Removals
```bash
# Start with unused imports (safest)
qontinui-devtools quality dead-code ./src --type imports
```

### Step 4: Remove Dead Code
- Remove flagged imports
- Delete unused functions/classes
- Remove unused variables

### Step 5: Test
```bash
# Run your tests
pytest

# Run type checking
mypy src/

# Verify the app works
python -m your_app
```

### Step 6: Repeat
```bash
# Check for more dead code
qontinui-devtools quality dead-code ./src
```

## Understanding Results

### Output Example
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
```

### Confidence Levels

- **0.95** - Very high (unused imports)
- **0.85** - High (most unused code)
- **0.5** - Medium (CLI commands, might be registered)
- **0.3-0.4** - Low (entry points, test fixtures)

### What to Remove First

1. **Imports (0.95 confidence)** - Safest to remove
2. **Variables (0.85 confidence)** - Usually safe
3. **Functions/Classes (0.85 confidence)** - Review before removing
4. **Low confidence items** - Investigate carefully

## Best Practices

### ✅ DO
- Review results before deleting code
- Start with high confidence items (>0.8)
- Run tests after removing code
- Remove unused imports first (safest)
- Use version control (git)

### ❌ DON'T
- Blindly delete all flagged code
- Remove public API methods
- Remove code without understanding it
- Skip testing after removal
- Remove entry points (main, setup, etc.)

## Common False Positives

### 1. Decorator-Registered Functions
```python
@app.route("/api")  # Registered via decorator
def handler():      # May show as unused
    pass
```

### 2. Dynamic Calls
```python
func_name = "my_function"
getattr(module, func_name)()  # Usage not detected
```

### 3. Public APIs
```python
# Part of library's public interface
def public_api_function():
    pass  # Used by external code
```

### 4. Plugin Systems
```python
# Discovered via entry points
def plugin_function():
    pass  # Found dynamically
```

## Integration

### Pre-commit Hook
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: dead-code
        name: Check for dead code
        entry: qontinui-devtools quality dead-code
        language: system
        args: ['--min-confidence', '0.9', '--type', 'imports']
```

### GitHub Actions
```yaml
- name: Check dead code
  run: qontinui-devtools quality dead-code ./src --min-confidence 0.8
```

## Python API Quick Reference

```python
from qontinui_devtools.code_quality import DeadCodeDetector

# Initialize
detector = DeadCodeDetector("./src")

# Find all dead code
all_dead = detector.analyze()

# Find specific types
imports = detector.find_unused_imports()
functions = detector.find_unused_functions()
classes = detector.find_unused_classes()
variables = detector.find_unused_variables()

# Get statistics
stats = detector.get_stats()
print(f"Total: {stats['total']}")
print(f"Functions: {stats['functions']}")
print(f"Classes: {stats['classes']}")
print(f"Imports: {stats['imports']}")
print(f"Variables: {stats['variables']}")

# Filter by confidence
high_conf = [dc for dc in all_dead if dc.confidence > 0.8]

# Access dead code properties
for dc in imports:
    print(f"Type: {dc.type}")              # "import"
    print(f"Name: {dc.name}")              # "os"
    print(f"File: {dc.file_path}")         # "/path/to/file.py"
    print(f"Line: {dc.line_number}")       # 42
    print(f"Reason: {dc.reason}")          # "Import 'os' is never used"
    print(f"Confidence: {dc.confidence}")  # 0.95
```

## Help

```bash
# Get help on any command
qontinui-devtools quality --help
qontinui-devtools quality dead-code --help
```

## Full Documentation

See [DEAD_CODE_DETECTOR.md](./DEAD_CODE_DETECTOR.md) for complete documentation.

## Examples

See [examples/detect_dead_code.py](./examples/detect_dead_code.py) for a working example.

## Support

- Report issues on GitHub
- Check documentation for troubleshooting
- Review tests for usage examples
