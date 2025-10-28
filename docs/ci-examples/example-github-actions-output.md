# Example GitHub Actions Workflow Output

This document shows what a typical GitHub Actions workflow run looks like with qontinui-devtools.

## Workflow Summary

```
Code Quality Analysis
Run #42 • Triggered by pull request #123 • Duration: 2m 34s
```

## Job: analyze

### Set up Python
```
✓ Set up Python 3.11.0
  Python version: 3.11.0
  Added to PATH: /opt/hostedtoolcache/Python/3.11.0/x64
```

### Install qontinui-devtools
```
✓ Install qontinui-devtools
  Collecting qontinui-devtools
    Downloading qontinui_devtools-1.0.0-py3-none-any.whl (125 kB)
  Collecting click>=8.0.0
    Using cached click-8.1.7-py3-none-any.whl (97 kB)
  Collecting rich>=13.0.0
    Using cached rich-13.7.0-py3-none-any.whl (240 kB)
  Installing collected packages: click, rich, qontinui-devtools
  Successfully installed click-8.1.7 rich-13.7.0 qontinui-devtools-1.0.0

  qontinui-devtools version 1.0.0
```

### Check for circular dependencies
```
✓ Check for circular dependencies
  Analyzing imports in src/...
  Found 150 Python files

  No circular dependencies detected!

  Saved results to analysis-results/circular-deps.json
```

### Detect god classes
```
⚠ Detect god classes
  Scanning for large classes (min 500 lines)...

  Found 7 god classes:
  • UserManager (src/services/user_manager.py)
    - Lines: 650
    - Methods: 45
  • AuthenticationService (src/auth/service.py)
    - Lines: 580
    - Methods: 38
  • DatabaseHandler (src/db/handler.py)
    - Lines: 520
    - Methods: 32

  Consider refactoring large classes into smaller components.

  Saved results to analysis-results/god-classes.json
```

### Check for race conditions
```
⚠ Check for race conditions
  Analyzing concurrency patterns...

  Found 11 potential race conditions:
  • 0 critical
  • 3 high severity
  • 8 medium severity

  High severity issues:
  1. src/auth/session_manager.py:45
     Shared session dictionary accessed without lock

  2. src/db/connection_pool.py:120
     Connection counter modified without synchronization

  3. src/cache/memory_cache.py:78
     Cache dictionary modified during iteration

  Saved results to analysis-results/race-conditions.json
```

### Generate comprehensive report
```
✓ Generate comprehensive report
  Generating HTML report...

  Including:
  • Circular dependency analysis
  • God class detection
  • Race condition analysis
  • Code metrics and statistics

  Report saved to analysis-results/analysis-report.html
```

### Upload analysis artifacts
```
✓ Upload analysis artifacts
  With the provided path, there will be 5 files uploaded

  Artifact name: code-quality-report
  Root directory: /home/runner/work/project/project
  Artifact size: 2.4 MB

  Artifact uploaded successfully!
  Artifact ID: 1234567890
  Artifact URL: https://github.com/owner/repo/actions/runs/1234567890
```

### Check quality gates
```
✓ Check quality gates

  Code Quality Gates Check
  ┌────────────────────────────────────────────────┐
  │  Enforcing quality standards                   │
  └────────────────────────────────────────────────┘

  Quality Gate Results
  ┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━┓
  ┃ Status ┃ Metric                        ┃ Actual ┃ Threshold ┃ Result ┃
  ┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━┩
  │ ✅     │ Circular Dependencies         │ 0      │ 0         │ PASS   │
  │ ⚠️      │ God Classes                   │ 7      │ 5         │ FAIL   │
  │ ✅     │ Critical Race Conditions      │ 0      │ 0         │ PASS   │
  │ ✅     │ High Severity Race Conditions │ 3      │ 10        │ PASS   │
  └────────┴───────────────────────────────┴────────┴───────────┴────────┘

  ⚠️  Warnings:
    • Found 7 god classes. Consider splitting large classes into smaller, focused components.

  ❌ Quality gates FAILED (1/4 checks failed)
  Fix the issues above before merging.

Error: Process completed with exit code 1.
```

### Generate PR comment
```
✓ Generate PR comment
  Generating PR comment...
  Loading analysis results...
  • circular-deps.json: 0 cycles
  • god-classes.json: 7 classes
  • race-conditions.json: 11 issues

  PR comment generated: analysis-results/pr-comment.md

  Preview:
  ─────────────────────────────────────────────────
  ## 📊 Code Quality Analysis

  **PR #123**: Add user authentication system

  ### Summary

  ✅ **Circular Dependencies**: 0
  ⚠️ **God Classes**: 7
  ✅ **Critical Race Conditions**: 0
  ⚠️ **High Severity Race Conditions**: 3
  ...
```

### Post PR comment
```
✓ Post PR comment
  Finding existing comments...
  Found existing bot comment (#98765432)
  Updating comment...
  Comment updated successfully!

  Comment URL: https://github.com/owner/repo/pull/123#issuecomment-98765432
```

### Add workflow summary
```
✓ Add workflow summary

  ## 📊 Code Quality Analysis Summary

  | Metric | Count | Status |
  |--------|-------|--------|
  | Circular Dependencies | 0 | ✅ |
  | God Classes | 7 | ⚠️ |
  | Critical Race Conditions | 0 | ✅ |

  📁 [View detailed report](https://github.com/owner/repo/actions/runs/1234567890)
```

### Fail if quality gates failed
```
✗ Fail if quality gates failed
  ❌ Quality gates failed. Please review the analysis results.
  Error: Process completed with exit code 1.
```

## Workflow Annotations

The workflow also creates annotations on the PR:

### Error Annotations
```
⚠️ God Classes (7 found)
src/services/user_manager.py:1
Consider splitting UserManager (650 lines, 45 methods) into smaller components

⚠️ Race Condition (High Severity)
src/auth/session_manager.py:45
Shared session dictionary accessed without lock
```

## Pull Request Checks

```
✅ Circular Dependencies (0 found)
⚠️ God Classes (7 found - exceeds threshold of 5)
✅ Critical Race Conditions (0 found)
✅ High Severity Race Conditions (3 found - below threshold of 10)

Overall: Some checks were not successful
```

## Example: Successful Run

```
Code Quality Analysis
Run #43 • Triggered by pull request #124 • Duration: 1m 52s

✓ Set up Python
✓ Install qontinui-devtools
✓ Check for circular dependencies (0 found)
✓ Detect god classes (3 found)
✓ Check for race conditions (2 medium found)
✓ Generate comprehensive report
✓ Upload analysis artifacts
✓ Check quality gates (All passed!)
✓ Generate PR comment
✓ Post PR comment
✓ Add workflow summary

Quality Gate Results
┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━┓
┃ Status ┃ Metric                        ┃ Actual ┃ Threshold ┃ Result ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━┩
│ ✅     │ Circular Dependencies         │ 0      │ 0         │ PASS   │
│ ✅     │ God Classes                   │ 3      │ 5         │ PASS   │
│ ✅     │ Critical Race Conditions      │ 0      │ 0         │ PASS   │
│ ✅     │ High Severity Race Conditions │ 0      │ 10        │ PASS   │
└────────┴───────────────────────────────┴────────┴───────────┴────────┘

✅ All quality gates PASSED!
```

## Artifacts

After the workflow completes, the following artifacts are available:

```
code-quality-report
├── circular-deps.json (1.2 KB)
├── god-classes.json (3.4 KB)
├── race-conditions.json (5.6 KB)
├── analysis-report.html (245 KB)
└── pr-comment.md (2.8 KB)

Download artifact (2.4 MB)
```

## Workflow Summary (in PR)

When you open the PR, you'll see a summary at the bottom:

```
📊 Code Quality Analysis Summary

| Metric | Count | Status |
|--------|-------|--------|
| Circular Dependencies | 0 | ✅ |
| God Classes | 7 | ⚠️ |
| Critical Race Conditions | 0 | ✅ |

📁 View detailed report
```
