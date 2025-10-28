# CI/CD Integration Guide

Complete guide for integrating qontinui-devtools into your CI/CD pipeline with quality gates, PR comments, and trend tracking.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Platform-Specific Guides](#platform-specific-guides)
3. [Quality Gates](#quality-gates)
4. [PR Comments](#pr-comments)
5. [Pre-commit Hooks](#pre-commit-hooks)
6. [Trend Tracking](#trend-tracking)
7. [Advanced Configuration](#advanced-configuration)

## Quick Start

### Installation in CI

The easiest way to install qontinui-devtools in CI is using our installation script:

```bash
curl -sSL https://raw.githubusercontent.com/qontinui/qontinui-devtools/main/scripts/install-ci.sh | bash
```

Or manually:

```bash
pip install qontinui-devtools
qontinui-devtools --version
```

### Basic Usage

Run all analyses:

```bash
# Check circular dependencies
qontinui-devtools import-cmd check src/ --output circular-deps.json --format json

# Detect god classes
qontinui-devtools architecture god-classes src/ --min-lines 500 --output god-classes.json --format json

# Check race conditions
qontinui-devtools concurrency check src/ --output race-conditions.json --format json

# Generate comprehensive report
qontinui-devtools analyze src/ --output report.html --format html
```

## Platform-Specific Guides

### GitHub Actions

**File**: `.github/workflows/code-quality.yml`

The project includes a complete GitHub Actions workflow. Copy it to your repository:

```yaml
name: Code Quality Analysis

on:
  pull_request:
  push:
    branches: [main, develop]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install qontinui-devtools
        run: pip install qontinui-devtools

      - name: Run analysis
        run: |
          qontinui-devtools analyze src/ --output report.html

      - name: Check quality gates
        run: |
          python -m qontinui_devtools.ci.quality_gates \
            --circular-deps circular-deps.json \
            --max-circular 0
```

**Features**:
- Automatic PR comments
- Quality gate enforcement
- Artifact upload
- Workflow summaries

**Setup**:
1. Copy `.github/workflows/code-quality.yml` to your repo
2. Adjust source directory paths
3. Configure quality gate thresholds
4. Commit and push

### GitLab CI

**File**: `.gitlab-ci.yml`

Copy from `.gitlab-ci-example.yml`:

```yaml
stages:
  - analyze
  - report

code-quality:
  stage: analyze
  image: python:3.11
  script:
    - pip install qontinui-devtools
    - qontinui-devtools analyze . --output report.html
  artifacts:
    paths:
      - report.html
    reports:
      codequality: codequality.json
```

**Features**:
- Code Quality widget integration
- Merge request comments
- Artifact storage
- Scheduled analysis

**Setup**:
1. Copy `.gitlab-ci-example.yml` to `.gitlab-ci.yml`
2. Set `GITLAB_TOKEN` variable in CI/CD settings
3. Configure stages and jobs
4. Push to trigger pipeline

### Jenkins

**File**: `Jenkinsfile`

```groovy
pipeline {
    agent any

    stages {
        stage('Setup') {
            steps {
                sh 'pip install qontinui-devtools'
            }
        }

        stage('Analyze') {
            steps {
                sh '''
                    qontinui-devtools import-cmd check . \
                        --output circular-deps.json \
                        --format json

                    qontinui-devtools architecture god-classes . \
                        --output god-classes.json \
                        --format json
                '''
            }
        }

        stage('Quality Gates') {
            steps {
                sh '''
                    python -m qontinui_devtools.ci.quality_gates \
                        --circular-deps circular-deps.json \
                        --god-classes god-classes.json \
                        --max-circular 0 \
                        --max-god-classes 5
                '''
            }
        }

        stage('Report') {
            steps {
                publishHTML([
                    reportDir: '.',
                    reportFiles: 'report.html',
                    reportName: 'Code Quality Report'
                ])
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: '*.json,*.html', allowEmptyArchive: true
        }
    }
}
```

See [docs/ci-examples/jenkins.md](ci-examples/jenkins.md) for more details.

### CircleCI

**File**: `.circleci/config.yml`

```yaml
version: 2.1

jobs:
  analyze:
    docker:
      - image: python:3.11
    steps:
      - checkout
      - run:
          name: Install qontinui-devtools
          command: pip install qontinui-devtools
      - run:
          name: Run analysis
          command: |
            qontinui-devtools analyze . --output report.html
      - store_artifacts:
          path: report.html
      - run:
          name: Check quality gates
          command: |
            python -m qontinui_devtools.ci.quality_gates \
              --circular-deps circular-deps.json \
              --max-circular 0

workflows:
  version: 2
  analyze:
    jobs:
      - analyze
```

See [docs/ci-examples/circleci.md](ci-examples/circleci.md) for more details.

### Azure Pipelines

**File**: `azure-pipelines.yml`

```yaml
trigger:
  - main
  - develop

pool:
  vmImage: 'ubuntu-latest'

steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: '3.11'

  - script: pip install qontinui-devtools
    displayName: 'Install qontinui-devtools'

  - script: |
      qontinui-devtools analyze . --output report.html
    displayName: 'Run analysis'

  - task: PublishBuildArtifacts@1
    inputs:
      pathToPublish: 'report.html'
      artifactName: 'code-quality-report'

  - script: |
      python -m qontinui_devtools.ci.quality_gates \
        --circular-deps circular-deps.json \
        --max-circular 0
    displayName: 'Check quality gates'
```

See [docs/ci-examples/azure-pipelines.md](ci-examples/azure-pipelines.md) for more details.

## Quality Gates

Quality gates enforce code quality standards by failing the build if thresholds are exceeded.

### Basic Usage

```bash
python -m qontinui_devtools.ci.quality_gates \
  --circular-deps circular-deps.json \
  --god-classes god-classes.json \
  --race-conditions race-conditions.json \
  --max-circular 0 \
  --max-god-classes 5 \
  --max-race-critical 0
```

### Available Options

| Option | Description | Default |
|--------|-------------|---------|
| `--max-circular` | Maximum circular dependencies | 0 |
| `--max-god-classes` | Maximum god classes | 5 |
| `--max-race-critical` | Maximum critical race conditions | 0 |
| `--max-race-high` | Maximum high severity races | 10 |
| `--min-coverage` | Minimum code coverage (%) | 80 |
| `--max-avg-complexity` | Maximum average complexity | 10 |
| `--max-complex-functions` | Max functions over complexity 15 | 5 |
| `--strict` | Enable strict mode (all thresholds = 0) | false |

### Strict Mode

Enable strict mode for zero-tolerance on all metrics:

```bash
python -m qontinui_devtools.ci.quality_gates \
  --circular-deps circular-deps.json \
  --strict
```

### Exit Codes

- `0`: All quality gates passed
- `1`: One or more quality gates failed

## PR Comments

Automatically generate and post comprehensive PR comments with analysis results.

### Generate Comment

```bash
python -m qontinui_devtools.ci.pr_comment \
  --circular-deps circular-deps.json \
  --god-classes god-classes.json \
  --race-conditions race-conditions.json \
  --pr-number 123 \
  --pr-title "Add new feature" \
  --output pr-comment.md
```

### With Trend Comparison

Compare against main branch:

```bash
# Save current results
python -m qontinui_devtools.ci.pr_comment \
  --circular-deps circular-deps.json \
  --god-classes god-classes.json \
  --previous-results main-branch-results.json \
  --output pr-comment.md
```

### Example Output

```markdown
## 📊 Code Quality Analysis

**PR #123**: Add new feature

### Summary

✅ **Circular Dependencies**: 0
⚠️ **God Classes**: 7
✅ **Critical Race Conditions**: 0

### Circular Dependencies

No circular dependencies found!

### God Classes

**Large classes that should be refactored:**

1. `UserManager` (650 lines, 45 methods)
2. `DataProcessor` (580 lines, 38 methods)

### Recommendations

- 🏗️ **Split god classes** into smaller, focused components

---
*Generated by [qontinui-devtools](https://github.com/qontinui/qontinui-devtools)*
```

### GitHub Actions Integration

```yaml
- name: Generate PR comment
  if: github.event_name == 'pull_request'
  run: |
    python -m qontinui_devtools.ci.pr_comment \
      --circular-deps circular-deps.json \
      --pr-number ${{ github.event.pull_request.number }} \
      --output pr-comment.md

- name: Post comment
  uses: actions/github-script@v7
  with:
    script: |
      const fs = require('fs');
      const comment = fs.readFileSync('pr-comment.md', 'utf8');
      github.rest.issues.createComment({
        owner: context.repo.owner,
        repo: context.repo.repo,
        issue_number: context.issue.number,
        body: comment
      });
```

## Pre-commit Hooks

Catch issues before they're committed with local pre-commit hooks.

### Installation

1. Install pre-commit:

```bash
pip install pre-commit
```

2. Copy `.pre-commit-config.yaml` to your repository.

3. Install hooks:

```bash
pre-commit install
```

### Available Hooks

- `check-circular-imports`: Detect circular dependencies
- `check-god-classes`: Flag oversized classes
- `check-race-conditions`: Find concurrency issues
- `check-complexity`: Enforce complexity limits

### Configuration

Customize thresholds in `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: check-god-classes
        name: Check for god classes
        entry: python -m qontinui_devtools.ci.pre_commit_hooks check-new-god-classes
        language: system
        types: [python]
        args: ["--min-lines=500", "--min-methods=30"]
```

### Usage

Hooks run automatically on `git commit`. To run manually:

```bash
# Run all hooks
pre-commit run --all-files

# Run specific hook
pre-commit run check-circular-imports --all-files
```

### Skip Hooks

Skip hooks when needed (use sparingly):

```bash
git commit --no-verify
```

## Trend Tracking

Track code quality metrics over time to identify trends.

### Setup Baseline

Run analysis on main branch and save results:

```bash
# On main branch
qontinui-devtools analyze . --output baseline.json --format json

# Store for comparison
git add baseline.json
git commit -m "Add code quality baseline"
```

### Compare in CI

```bash
# In PR branch
qontinui-devtools analyze . --output current.json --format json

# Compare
python -m qontinui_devtools.ci.pr_comment \
  --circular-deps current.json \
  --previous-results baseline.json \
  --output comparison.md
```

### Scheduled Analysis

Run analysis on a schedule to track trends:

**GitHub Actions**:

```yaml
on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
```

**GitLab CI**:

```yaml
schedule:quality-analysis:
  only:
    - schedules
  script:
    - qontinui-devtools analyze . --output weekly-report.html
```

### Trend Visualization

Store historical data and visualize trends:

```python
import json
from datetime import datetime

# Save results with timestamp
results = {
    "timestamp": datetime.now().isoformat(),
    "circular_deps": circular_count,
    "god_classes": god_count,
    "race_conditions": race_count
}

with open(f"history/{datetime.now().date()}.json", "w") as f:
    json.dump(results, f)
```

## Advanced Configuration

### Custom Quality Profiles

Create custom profiles for different project types:

```bash
# Strict profile for critical systems
python -m qontinui_devtools.ci.quality_gates \
  --strict \
  --max-race-critical 0

# Relaxed profile for legacy code
python -m qontinui_devtools.ci.quality_gates \
  --max-circular 10 \
  --max-god-classes 20 \
  --max-race-high 50
```

### Ignore Patterns

Exclude files from analysis:

```bash
qontinui-devtools analyze src/ \
  --exclude "tests/*,migrations/*" \
  --output report.html
```

### Parallel Execution

Run checks in parallel for faster CI:

```yaml
jobs:
  circular-deps:
    runs-on: ubuntu-latest
    steps:
      - run: qontinui-devtools import-cmd check .

  god-classes:
    runs-on: ubuntu-latest
    steps:
      - run: qontinui-devtools architecture god-classes .

  race-conditions:
    runs-on: ubuntu-latest
    steps:
      - run: qontinui-devtools concurrency check .
```

### Caching

Cache dependencies for faster builds:

**GitHub Actions**:

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
```

**GitLab CI**:

```yaml
cache:
  paths:
    - .cache/pip
```

### Notifications

Send notifications on quality gate failures:

```bash
# Slack
if ! python -m qontinui_devtools.ci.quality_gates ...; then
  curl -X POST -H 'Content-type: application/json' \
    --data '{"text":"Quality gates failed!"}' \
    $SLACK_WEBHOOK_URL
fi
```

## Troubleshooting

### Common Issues

**Issue**: `qontinui-devtools: command not found`

**Solution**: Ensure installation completed successfully:
```bash
pip install --upgrade qontinui-devtools
which qontinui-devtools
```

**Issue**: Quality gates always pass/fail

**Solution**: Verify JSON files exist and have correct format:
```bash
cat circular-deps.json | python -m json.tool
```

**Issue**: Pre-commit hooks not running

**Solution**: Reinstall hooks:
```bash
pre-commit uninstall
pre-commit install
```

### Debug Mode

Enable debug logging:

```bash
export QONTINUI_DEBUG=1
qontinui-devtools analyze .
```

### Support

- Documentation: https://qontinui-devtools.readthedocs.io
- Issues: https://github.com/qontinui/qontinui-devtools/issues
- Discussions: https://github.com/qontinui/qontinui-devtools/discussions

## Examples

See [docs/ci-examples/](ci-examples/) for platform-specific examples:

- [GitHub Actions](ci-examples/github-actions.md)
- [GitLab CI](ci-examples/gitlab-ci.md)
- [Jenkins](ci-examples/jenkins.md)
- [CircleCI](ci-examples/circleci.md)
- [Azure Pipelines](ci-examples/azure-pipelines.md)
- [Travis CI](ci-examples/travis-ci.md)

## Best Practices

1. **Start with relaxed thresholds** and gradually tighten them
2. **Run locally** with pre-commit hooks before pushing
3. **Track trends** over time to identify degradation
4. **Fix issues incrementally** rather than all at once
5. **Customize thresholds** based on project needs
6. **Review PR comments** before merging
7. **Schedule regular analysis** for trend tracking

## Migration Guide

### From Manual Checks

Before:
```bash
find . -name "*.py" -exec pylint {} \;
```

After:
```bash
qontinui-devtools analyze . --output report.html
```

### From Other Tools

qontinui-devtools complements existing tools:

- **pylint/flake8**: Static analysis
- **pytest**: Unit testing
- **qontinui-devtools**: Architecture & concurrency analysis

Use them together for comprehensive coverage.

## Next Steps

1. Choose your CI platform from the guides above
2. Copy the relevant configuration file
3. Adjust thresholds and paths
4. Set up pre-commit hooks locally
5. Configure PR comments
6. Enable trend tracking

Happy coding! 🚀
