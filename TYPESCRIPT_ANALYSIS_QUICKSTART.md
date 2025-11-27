# TypeScript/JavaScript Analysis Quick Start Guide

## Overview

The qontinui-devtools package now includes comprehensive TypeScript/JavaScript analysis tools that provide the same powerful analysis capabilities as the Python tools.

## Installation

```bash
cd /mnt/c/qontinui/qontinui-devtools
poetry install
```

## Quick Commands

### 1. Check for Circular Dependencies

```bash
# Basic check
poetry run qontinui-devtools ts check /path/to/src

# With strict mode (fails CI/CD if issues found)
poetry run qontinui-devtools ts check /path/to/src --strict

# Save report
poetry run qontinui-devtools ts check /path/to/src --output circular-deps.txt
```

**What it does:**
- Scans all `.ts`, `.tsx`, `.js`, `.jsx` files
- Builds import dependency graph
- Detects circular import chains
- Shows severity (high/medium/low)
- Displays complete import chain for each cycle

### 2. Find Dead Code

```bash
# Basic check
poetry run qontinui-devtools ts dead-code /path/to/src

# High-confidence results only
poetry run qontinui-devtools ts dead-code /path/to/src --min-confidence 0.8

# Save report
poetry run qontinui-devtools ts dead-code /path/to/src --output dead-code.txt
```

**What it does:**
- Finds unused exports
- Identifies code only used locally
- Confidence scoring (0-1)
- Distinguishes between truly unused and potentially dynamic usage

### 3. Analyze Type Coverage

```bash
# Basic check
poetry run qontinui-devtools ts types /path/to/src

# Require minimum coverage
poetry run qontinui-devtools ts types /path/to/src --threshold 80 --strict

# Save report
poetry run qontinui-devtools ts types /path/to/src --output coverage.txt
```

**What it does:**
- Calculates overall type coverage percentage
- Finds `any` type usage (anti-pattern)
- Identifies missing parameter types
- Finds missing return types
- Tracks `unknown` type usage

### 4. Check Code Complexity

```bash
# Basic check
poetry run qontinui-devtools ts complexity /path/to/src

# Custom thresholds
poetry run qontinui-devtools ts complexity /path/to/src \
  --max-file-lines 300 \
  --max-function-lines 40 \
  --max-complexity 12 \
  --strict

# Save report
poetry run qontinui-devtools ts complexity /path/to/src --output complexity.txt
```

**What it does:**
- Measures cyclomatic complexity
- Finds large files (>500 lines default)
- Identifies long functions (>50 lines default)
- Detects god components (large React components)
- Calculates average complexity

### 5. Comprehensive Analysis

```bash
# Run all analyses
poetry run qontinui-devtools ts analyze /path/to/src

# Skip specific checks
poetry run qontinui-devtools ts analyze /path/to/src \
  --skip-dead-code \
  --skip-complexity

# Save comprehensive report
poetry run qontinui-devtools ts analyze /path/to/src --output full-analysis.txt
```

**What it does:**
- Runs all 4 analyses in sequence
- Generates comprehensive report
- Combines all findings
- Perfect for code reviews

## Example: Analyze qontinui-web Frontend

```bash
cd /mnt/c/qontinui/qontinui-devtools

# Check circular dependencies
poetry run qontinui-devtools ts check /mnt/c/qontinui/qontinui-web/frontend/src

# Find dead code with high confidence
poetry run qontinui-devtools ts dead-code /mnt/c/qontinui/qontinui-web/frontend/src --min-confidence 0.8

# Check type coverage
poetry run qontinui-devtools ts types /mnt/c/qontinui/qontinui-web/frontend/src

# Analyze complexity
poetry run qontinui-devtools ts complexity /mnt/c/qontinui/qontinui-web/frontend/src

# Full analysis with report
poetry run qontinui-devtools ts analyze /mnt/c/qontinui/qontinui-web/frontend/src \
  --output frontend-analysis.txt
```

## Real Results from qontinui-web

When run on `/mnt/c/qontinui/qontinui-web/frontend/src/app`:

### Circular Dependencies
```
✅ No circular dependencies found!
Files scanned: 92
Total imports: 720
```

### Type Coverage
```
Overall Coverage: 33.7%
Files analyzed: 92
Functions typed: 35/586 (6.0%)
Parameters typed: 303/417 (72.7%)
'any' usage: 34 occurrences

Issues: 503 total
- Missing return types: 356
- Missing param types: 113
- 'any' usage: 34
```

### Complexity
```
Total files: 92
Total lines: 31,122
Total functions: 192
Average complexity: 9.63

Issues: 160 total
- Large files: 13 (largest: 1,852 lines)
- Large functions: 96 (largest: 1,349 lines)
- High complexity: 51
```

## Command Reference

| Command | Purpose | Key Options |
|---------|---------|-------------|
| `ts check` | Circular dependencies | `--strict`, `--output`, `--format` |
| `ts dead-code` | Unused code | `--strict`, `--min-confidence`, `--output` |
| `ts types` | Type coverage | `--strict`, `--threshold`, `--output` |
| `ts complexity` | Code complexity | `--strict`, `--max-file-lines`, `--max-function-lines`, `--max-complexity`, `--output` |
| `ts analyze` | All analyses | `--skip-*`, `--output` |

## Thresholds & Defaults

### Type Coverage
- Default threshold: 80%
- Custom: `--threshold <percent>`

### Complexity
- Max file lines: 500 (custom: `--max-file-lines <num>`)
- Max function lines: 50 (custom: `--max-function-lines <num>`)
- Max cyclomatic complexity: 10 (custom: `--max-complexity <num>`)

### Dead Code Confidence
- Default minimum: 0.7 (70%)
- Custom: `--min-confidence <0-1>`

## CI/CD Integration

Add to your CI pipeline:

```bash
# Fail build on circular dependencies
qontinui-devtools ts check ./src --strict

# Require 80% type coverage
qontinui-devtools ts types ./src --threshold 80 --strict

# Enforce complexity limits
qontinui-devtools ts complexity ./src --strict
```

Exit codes:
- `0` - Success (no issues or issues found but not strict mode)
- `1` - Failure (issues found in strict mode or error occurred)

## Help Commands

```bash
# Main help
poetry run qontinui-devtools ts --help

# Command-specific help
poetry run qontinui-devtools ts check --help
poetry run qontinui-devtools ts dead-code --help
poetry run qontinui-devtools ts types --help
poetry run qontinui-devtools ts complexity --help
poetry run qontinui-devtools ts analyze --help
```

## File Locations

**Source code:**
```
/mnt/c/qontinui/qontinui-devtools/python/qontinui_devtools/typescript_analysis/
├── __init__.py
├── ts_utils.py
├── circular_detector.py
├── dead_code_detector.py
├── type_coverage_analyzer.py
├── complexity_analyzer.py
└── README.md
```

**CLI integration:**
```
/mnt/c/qontinui/qontinui-devtools/python/qontinui_devtools/cli.py
  (lines 2670-3034)
```

## Supported File Types

- `.ts` - TypeScript
- `.tsx` - TypeScript + JSX (React)
- `.js` - JavaScript
- `.jsx` - JavaScript + JSX (React)

## Auto-excluded Directories

- `node_modules/`
- `dist/`
- `build/`
- `.next/`
- `out/`
- `__tests__/`

## Tips

1. **Start with comprehensive analysis** to get an overview:
   ```bash
   qontinui-devtools ts analyze ./src --output analysis.txt
   ```

2. **Focus on high-priority issues** first:
   - Circular dependencies (can cause runtime errors)
   - High-confidence dead code (safe to remove)
   - 'any' type usage (reduces type safety)
   - High complexity functions (hard to maintain)

3. **Use in development** to catch issues early:
   ```bash
   # Quick check during development
   qontinui-devtools ts check ./src
   ```

4. **Integrate with CI/CD** to enforce standards:
   ```bash
   # In your CI pipeline
   qontinui-devtools ts analyze ./src --strict
   ```

5. **Generate reports for code reviews**:
   ```bash
   qontinui-devtools ts analyze ./src --output review-$(date +%Y%m%d).txt
   ```

## Getting Started

1. Analyze your codebase:
   ```bash
   cd /mnt/c/qontinui/qontinui-devtools
   poetry run qontinui-devtools ts analyze /path/to/your/src
   ```

2. Review the findings in the console output

3. Save a detailed report:
   ```bash
   poetry run qontinui-devtools ts analyze /path/to/your/src --output analysis.txt
   ```

4. Focus on specific issues with individual commands

5. Integrate into your workflow with `--strict` mode

## Documentation

For more details, see:
- `/mnt/c/qontinui/qontinui-devtools/python/qontinui_devtools/typescript_analysis/README.md`
- `/tmp/typescript-analysis-summary.md` (comprehensive implementation summary)
