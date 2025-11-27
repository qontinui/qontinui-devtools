# TypeScript/JavaScript Analysis Tools

This package provides comprehensive static analysis tools for TypeScript and JavaScript codebases.

## Features

### 1. Circular Dependency Detection

Detects circular import dependencies that can cause runtime issues and make code harder to maintain.

```bash
# Basic check
qontinui-devtools ts check ./src

# Strict mode (exit with error if issues found)
qontinui-devtools ts check ./src --strict

# Save report
qontinui-devtools ts check ./src --output report.txt
```

**Features:**
- Analyzes all `.ts`, `.tsx`, `.js`, `.jsx` files
- Builds dependency graph from import statements
- Detects cycles using graph algorithms
- Categorizes severity (high/medium/low based on cycle length)
- Shows import chain for each cycle

### 2. Dead Code Detection

Identifies potentially unused exports, functions, and code.

```bash
# Basic check
qontinui-devtools ts dead-code ./src

# Only high-confidence results
qontinui-devtools ts dead-code ./src --min-confidence 0.8

# Save report
qontinui-devtools ts dead-code ./src --output dead-code.txt
```

**Features:**
- Tracks all exports across files
- Identifies exports not imported elsewhere
- Confidence scoring based on usage patterns
- Distinguishes between truly unused and potentially dynamic usage

### 3. Type Coverage Analysis

Measures TypeScript type coverage and identifies type-related issues.

```bash
# Basic check
qontinui-devtools ts types ./src

# Require minimum coverage
qontinui-devtools ts types ./src --threshold 90 --strict

# Save report
qontinui-devtools ts types ./src --output coverage.txt
```

**Features:**
- Calculates overall type coverage percentage
- Counts typed vs untyped function parameters
- Identifies `any` type usage (anti-pattern)
- Finds missing return type annotations
- Tracks `unknown` type usage (better than `any`)

### 4. Complexity Analysis

Measures code complexity and identifies potential code smells.

```bash
# Basic check
qontinui-devtools ts complexity ./src

# Custom thresholds
qontinui-devtools ts complexity ./src --max-file-lines 300 --max-complexity 15

# Save report
qontinui-devtools ts complexity ./src --output complexity.txt
```

**Features:**
- Calculates cyclomatic complexity
- Identifies large files (> 500 lines by default)
- Finds long functions (> 50 lines by default)
- Detects god components (large React components in `.tsx` files)
- Average complexity across codebase

**Thresholds (configurable):**
- Max file lines: 500
- Max function lines: 50
- Max cyclomatic complexity: 10

### 5. Comprehensive Analysis

Runs all analyses in one command.

```bash
# Full analysis
qontinui-devtools ts analyze ./src

# Skip specific checks
qontinui-devtools ts analyze ./src --skip-dead-code --skip-complexity

# Save comprehensive report
qontinui-devtools ts analyze ./src --output full-report.txt
```

## Implementation Details

### Import Resolution

The tools resolve import paths using the following strategies:

1. **Relative imports**: `./foo`, `../bar`
2. **Path aliases**: `@/components`, `~/utils`
3. **File extensions**: Tries `.ts`, `.tsx`, `.js`, `.jsx`
4. **Index files**: Resolves to `index.ts`, `index.tsx`, etc.

### Exclusions

The following directories are automatically excluded from analysis:
- `node_modules`
- `dist`
- `build`
- `.next`
- `out`
- `__tests__`

### Type Coverage Calculation

```
coverage = (typed_items / total_items) * 100

where:
  typed_items = typed_parameters + typed_functions
  total_items = total_parameters + total_functions
```

### Cyclomatic Complexity

Simplified McCabe complexity calculation based on decision points:

```
complexity = 1 + count(if, else if, while, for, case, catch, ?, &&, ||)
```

## Example Output

### Circular Dependencies

```
Found 1 circular dependencies:

1. Cycle (severity: high):
   moduleA
      -> imports from './moduleB' (line 5)
   moduleB
      -> imports from './moduleA' (line 10)

Statistics:
  Files scanned: 150
  Total imports: 450
  Total cycles: 1
```

### Dead Code

```
Dead Code Report
┏━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━┳━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┓
┃ File        ┃ Name     ┃ Type  ┃ Line ┃ Confidence ┃ Reason            ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━╇━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━┩
│ utils.ts    │ oldFunc  │ func  │ 42   │ 90%        │ Not used anywhere │
└─────────────┴──────────┴───────┴──────┴────────────┴───────────────────┘
```

### Type Coverage

```
TypeScript Type Coverage Report

Overall Coverage: 75.3%
  Files analyzed: 150
  Functions: 120/200 typed
  Parameters: 450/500 typed
  'any' usage: 25 occurrences
  'unknown' usage: 3 occurrences
```

### Complexity

```
Code Complexity Report

Metrics:
  Total files: 150
  Total lines: 45000
  Total functions: 800
  Average complexity: 8.5

Found 45 complexity issues

Top Issues:
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━┳━━━━━━━━━━━┓
┃ Type           ┃ Name         ┃ File        ┃ Line ┃ Metric ┃ Threshold ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━╇━━━━━━━━━━━┩
│ large_file     │ Dashboard.ts │ components/ │ 1    │ 1200   │ 500       │
│ large_function │ processData  │ utils.ts    │ 150  │ 180    │ 50        │
└────────────────┴──────────────┴─────────────┴──────┴────────┴───────────┘
```

## Limitations

- **Regex-based parsing**: Uses regex patterns instead of full AST parsing (no Node.js required)
- **Dynamic imports**: Cannot analyze dynamic `import()` statements
- **Type inference**: Cannot detect inferred types, only explicit annotations
- **Runtime behavior**: Cannot detect code used via reflection or dynamic property access
- **JSX complexity**: Simplified estimation for React component complexity

## Integration

### CI/CD

Use `--strict` flag to fail builds on issues:

```bash
# Fail on circular dependencies
qontinui-devtools ts check ./src --strict

# Fail on low type coverage
qontinui-devtools ts types ./src --threshold 80 --strict

# Fail on complexity issues
qontinui-devtools ts complexity ./src --strict
```

### Pre-commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: ts-check
      name: TypeScript Circular Dependency Check
      entry: qontinui-devtools ts check
      language: system
      types: [typescript, javascript]
      pass_filenames: false
      args: [./src, --strict]
```

## Architecture

```
typescript_analysis/
├── __init__.py              # Package exports
├── ts_utils.py             # Parsing utilities
├── circular_detector.py    # Circular dependency detection
├── dead_code_detector.py   # Dead code detection
├── type_coverage_analyzer.py  # Type coverage analysis
├── complexity_analyzer.py  # Complexity analysis
└── README.md              # This file
```

Each analyzer follows the same pattern:
1. Scan directory for TS/JS files
2. Parse files to extract relevant information
3. Analyze and build reports
4. Generate rich console output and text reports
