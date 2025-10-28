# GitHub Actions Integration Guide

Complete guide for integrating qontinui-devtools with GitHub Actions.

## Quick Start

The repository includes a complete workflow at `.github/workflows/code-quality.yml`. Copy it to your repository and customize as needed.

## Basic Workflow

```yaml
name: Code Quality

on:
  pull_request:
  push:
    branches: [main]

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
        run: qontinui-devtools analyze . --output report.html

      - name: Upload report
        uses: actions/upload-artifact@v4
        with:
          name: code-quality-report
          path: report.html
```

## Advanced Features

### Matrix Strategy

Test with multiple Python versions:

```yaml
jobs:
  analyze:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.8', '3.9', '3.10', '3.11']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install qontinui-devtools
      - run: qontinui-devtools analyze .
```

### Parallel Jobs

```yaml
jobs:
  circular-deps:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install qontinui-devtools
      - run: qontinui-devtools import-cmd check . --output circular-deps.json --format json
      - uses: actions/upload-artifact@v4
        with:
          name: circular-deps
          path: circular-deps.json

  god-classes:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install qontinui-devtools
      - run: qontinui-devtools architecture god-classes . --output god-classes.json --format json
      - uses: actions/upload-artifact@v4
        with:
          name: god-classes
          path: god-classes.json

  quality-gates:
    needs: [circular-deps, god-classes]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with:
          name: circular-deps
      - uses: actions/download-artifact@v4
        with:
          name: god-classes
      - run: pip install qontinui-devtools
      - run: |
          python -m qontinui_devtools.ci.quality_gates \
            --circular-deps circular-deps.json \
            --god-classes god-classes.json \
            --max-circular 0
```

### PR Comments

Automatically post analysis results to PRs:

```yaml
- name: Generate PR comment
  if: github.event_name == 'pull_request'
  run: |
    python -m qontinui_devtools.ci.pr_comment \
      --circular-deps circular-deps.json \
      --pr-number ${{ github.event.pull_request.number }} \
      --output pr-comment.md

- name: Post comment
  if: github.event_name == 'pull_request'
  uses: actions/github-script@v7
  with:
    script: |
      const fs = require('fs');
      const comment = fs.readFileSync('pr-comment.md', 'utf8');

      const { data: comments } = await github.rest.issues.listComments({
        owner: context.repo.owner,
        repo: context.repo.repo,
        issue_number: context.issue.number,
      });

      const botComment = comments.find(c =>
        c.user.type === 'Bot' && c.body.includes('Code Quality Analysis')
      );

      if (botComment) {
        await github.rest.issues.updateComment({
          owner: context.repo.owner,
          repo: context.repo.repo,
          comment_id: botComment.id,
          body: comment
        });
      } else {
        await github.rest.issues.createComment({
          owner: context.repo.owner,
          repo: context.repo.repo,
          issue_number: context.issue.number,
          body: comment
        });
      }
```

### Workflow Summary

Add results to workflow summary:

```yaml
- name: Add summary
  run: |
    echo "## Code Quality Results" >> $GITHUB_STEP_SUMMARY
    echo "" >> $GITHUB_STEP_SUMMARY
    echo "| Metric | Count |" >> $GITHUB_STEP_SUMMARY
    echo "|--------|-------|" >> $GITHUB_STEP_SUMMARY
    echo "| Circular Dependencies | 0 |" >> $GITHUB_STEP_SUMMARY
```

### Scheduled Runs

Run analysis weekly for trend tracking:

```yaml
on:
  schedule:
    - cron: '0 0 * * 0'  # Sunday at midnight

jobs:
  weekly-analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install qontinui-devtools
      - run: qontinui-devtools analyze . --output weekly-report.html
      - uses: actions/upload-artifact@v4
        with:
          name: weekly-report-${{ github.run_number }}
          path: weekly-report.html
```

## Caching

Speed up builds with caching:

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

## Permissions

Set appropriate permissions:

```yaml
permissions:
  contents: read
  pull-requests: write
  checks: write
```

## Conditional Execution

### Run only on specific paths

```yaml
on:
  push:
    paths:
      - '**/*.py'
      - 'pyproject.toml'
```

### Run only on PRs to specific branches

```yaml
on:
  pull_request:
    branches:
      - main
      - develop
```

## Reusable Workflows

Create reusable workflows for consistency:

**.github/workflows/reusable-quality-check.yml**:

```yaml
name: Reusable Quality Check

on:
  workflow_call:
    inputs:
      max-circular:
        required: false
        type: number
        default: 0
      max-god-classes:
        required: false
        type: number
        default: 5

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install qontinui-devtools
      - run: qontinui-devtools analyze .
      - run: |
          python -m qontinui_devtools.ci.quality_gates \
            --max-circular ${{ inputs.max-circular }} \
            --max-god-classes ${{ inputs.max-god-classes }}
```

**Use reusable workflow**:

```yaml
jobs:
  quality-check:
    uses: ./.github/workflows/reusable-quality-check.yml
    with:
      max-circular: 0
      max-god-classes: 10
```

## Composite Actions

Create custom actions:

**.github/actions/setup-qontinui/action.yml**:

```yaml
name: 'Setup qontinui-devtools'
description: 'Install and configure qontinui-devtools'

runs:
  using: 'composite'
  steps:
    - uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - shell: bash
      run: |
        pip install qontinui-devtools
        qontinui-devtools --version
```

**Use composite action**:

```yaml
steps:
  - uses: ./.github/actions/setup-qontinui
  - run: qontinui-devtools analyze .
```

## Notifications

### Slack

```yaml
- name: Notify Slack
  if: failure()
  uses: slackapi/slack-github-action@v1
  with:
    payload: |
      {
        "text": "Quality gates failed for ${{ github.repository }}"
      }
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

### Discord

```yaml
- name: Notify Discord
  if: failure()
  uses: sarisia/actions-status-discord@v1
  with:
    webhook: ${{ secrets.DISCORD_WEBHOOK }}
    title: "Code Quality Check Failed"
```

## Best Practices

1. **Use caching** for faster builds
2. **Run parallel jobs** when possible
3. **Add workflow summaries** for visibility
4. **Post PR comments** for context
5. **Set up notifications** for failures
6. **Use reusable workflows** for consistency
7. **Enable branch protection** based on checks

## Troubleshooting

### Issue: Permission denied

Add permissions to workflow:

```yaml
permissions:
  contents: read
  pull-requests: write
```

### Issue: Artifact upload fails

Check artifact size and retention:

```yaml
- uses: actions/upload-artifact@v4
  with:
    name: reports
    path: analysis-results/
    retention-days: 30
    if-no-files-found: warn
```

### Issue: Workflow doesn't trigger

Check event triggers and branch filters:

```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened]
```

## Complete Example

See `.github/workflows/code-quality.yml` in the repository for a complete, production-ready workflow.
