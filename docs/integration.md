# Integration Guide

Guide for integrating Qontinui DevTools into your CI/CD pipelines, pre-commit hooks, and development workflows.

## Table of Contents

1. [GitHub Actions](#github-actions)
2. [GitLab CI](#gitlab-ci)
3. [Pre-commit Hooks](#pre-commit-hooks)
4. [Jenkins](#jenkins)
5. [CircleCI](#circleci)
6. [Azure Pipelines](#azure-pipelines)
7. [Quality Gates](#quality-gates)
8. [IDE Integration](#ide-integration)
9. [Docker Integration](#docker-integration)
10. [Custom Integrations](#custom-integrations)

---

## GitHub Actions

### Basic Analysis Workflow

Create `.github/workflows/analysis.yml`:

```yaml
name: Static Analysis

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  analyze:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install qontinui-devtools

      - name: Run analysis
        run: |
          qontinui-devtools analyze ./src \
            --report analysis.json \
            --format json

      - name: Upload results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: analysis-results
          path: analysis.json
```

### Comprehensive Testing Workflow

```yaml
name: Comprehensive Testing

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight

jobs:
  import-analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install DevTools
        run: pip install qontinui-devtools

      - name: Check circular dependencies
        run: |
          qontinui-devtools import check ./src \
            --strict \
            --output import_report.json \
            --format json

      - name: Upload import analysis
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: import-report
          path: import_report.json

  concurrency-analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install DevTools
        run: pip install qontinui-devtools

      - name: Check race conditions
        run: |
          qontinui-devtools concurrency check ./src \
            --severity medium \
            --output race_report.json \
            --format json

      - name: Upload concurrency analysis
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: race-report
          path: race_report.json

  race-testing:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install qontinui-devtools
          pip install -e .

      - name: Test critical functions
        run: |
          # Test each critical function
          qontinui-devtools test race \
            --target mypackage.worker:process_data \
            --threads 50 \
            --iterations 1000

  generate-report:
    runs-on: ubuntu-latest
    needs: [import-analysis, concurrency-analysis, race-testing]
    if: always()

    steps:
      - uses: actions/checkout@v3

      - name: Download all artifacts
        uses: actions/download-artifact@v3

      - name: Generate HTML report
        run: |
          pip install qontinui-devtools
          qontinui-devtools analyze ./src \
            --report report.html \
            --format html

      - name: Upload HTML report
        uses: actions/upload-artifact@v3
        with:
          name: comprehensive-report
          path: report.html

      - name: Comment on PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('analysis.json', 'utf8');
            const data = JSON.parse(report);

            const comment = `## Analysis Results

            - **Circular Dependencies:** ${data.imports.cycles}
            - **Race Conditions:** ${data.concurrency.races}

            [View full report](https://github.com/${{ github.repository }}/actions/runs/${{ github.run_id }})
            `;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });
```

### Quality Gate Workflow

```yaml
name: Quality Gate

on:
  pull_request:
    branches: [ main ]

jobs:
  quality-gate:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install DevTools
        run: pip install qontinui-devtools

      - name: Run quality checks
        id: checks
        run: |
          # Run checks and capture exit codes
          qontinui-devtools import check ./src --strict || echo "import_failed=true" >> $GITHUB_OUTPUT
          qontinui-devtools concurrency check ./src --severity high || echo "concurrency_failed=true" >> $GITHUB_OUTPUT

      - name: Fail if quality gate not met
        if: steps.checks.outputs.import_failed == 'true' || steps.checks.outputs.concurrency_failed == 'true'
        run: |
          echo "::error::Quality gate failed"
          exit 1

      - name: Success notification
        if: success()
        run: echo "✅ All quality checks passed"
```

---

## GitLab CI

### `.gitlab-ci.yml` Configuration

```yaml
stages:
  - analyze
  - test
  - report

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip

before_script:
  - python -m pip install --upgrade pip
  - pip install qontinui-devtools

import-analysis:
  stage: analyze
  script:
    - qontinui-devtools import check ./src --output import_report.json --format json
  artifacts:
    reports:
      junit: import_report.json
    paths:
      - import_report.json
    expire_in: 1 week
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

concurrency-analysis:
  stage: analyze
  script:
    - qontinui-devtools concurrency check ./src --severity medium --output race_report.json --format json
  artifacts:
    paths:
      - race_report.json
    expire_in: 1 week
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

race-testing:
  stage: test
  script:
    - pip install -e .
    - |
      # Test critical functions
      qontinui-devtools test race \
        --target mypackage.worker:process_data \
        --threads 50 \
        --iterations 1000
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

comprehensive-report:
  stage: report
  dependencies:
    - import-analysis
    - concurrency-analysis
  script:
    - qontinui-devtools analyze ./src --report report.html --format html
  artifacts:
    paths:
      - report.html
    expire_in: 1 month
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

quality-gate:
  stage: analyze
  script:
    - qontinui-devtools import check ./src --strict
    - qontinui-devtools concurrency check ./src --severity high
  allow_failure: false
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

---

## Pre-commit Hooks

### Using pre-commit Framework

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: qontinui-import-check
        name: Check circular dependencies
        entry: qontinui-devtools import check
        language: system
        pass_filenames: false
        args: ['./src', '--strict']

      - id: qontinui-concurrency-check
        name: Check race conditions
        entry: qontinui-devtools concurrency check
        language: system
        pass_filenames: false
        args: ['./src', '--severity', 'high']
```

Install the hooks:

```bash
pip install pre-commit
pre-commit install
```

### Manual Git Hook

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash

echo "Running Qontinui DevTools checks..."

# Check for circular dependencies
echo "Checking for circular dependencies..."
qontinui-devtools import check ./src --strict
if [ $? -ne 0 ]; then
    echo "❌ Circular dependency check failed"
    exit 1
fi

# Check for high-severity race conditions
echo "Checking for race conditions..."
qontinui-devtools concurrency check ./src --severity high
if [ $? -ne 0 ]; then
    echo "❌ Race condition check failed"
    exit 1
fi

echo "✅ All checks passed"
exit 0
```

Make it executable:

```bash
chmod +x .git/hooks/pre-commit
```

### Pre-push Hook

Create `.git/hooks/pre-push`:

```bash
#!/bin/bash

echo "Running comprehensive analysis before push..."

# Run full analysis
qontinui-devtools analyze ./src --format json --output /tmp/analysis.json

# Check results
python3 << EOF
import json
import sys

with open('/tmp/analysis.json') as f:
    results = json.load(f)

failed = False

if results.get('imports', {}).get('status') == 'FAIL':
    print("❌ Import analysis failed")
    failed = True

if results.get('concurrency', {}).get('status') == 'FAIL':
    print("❌ Concurrency analysis failed")
    failed = True

if failed:
    print("\nRun 'qontinui-devtools analyze ./src' for details")
    sys.exit(1)

print("✅ All checks passed")
EOF

exit $?
```

---

## Jenkins

### Jenkinsfile

```groovy
pipeline {
    agent any

    stages {
        stage('Setup') {
            steps {
                sh 'python -m pip install --upgrade pip'
                sh 'pip install qontinui-devtools'
            }
        }

        stage('Import Analysis') {
            steps {
                sh 'qontinui-devtools import check ./src --output import_report.json --format json'
            }
            post {
                always {
                    archiveArtifacts artifacts: 'import_report.json', allowEmptyArchive: true
                }
            }
        }

        stage('Concurrency Analysis') {
            steps {
                sh 'qontinui-devtools concurrency check ./src --output race_report.json --format json'
            }
            post {
                always {
                    archiveArtifacts artifacts: 'race_report.json', allowEmptyArchive: true
                }
            }
        }

        stage('Race Testing') {
            steps {
                sh 'pip install -e .'
                sh '''
                    qontinui-devtools test race \
                        --target mypackage.worker:process_data \
                        --threads 50 \
                        --iterations 1000
                '''
            }
        }

        stage('Generate Report') {
            steps {
                sh 'qontinui-devtools analyze ./src --report report.html --format html'
            }
            post {
                always {
                    publishHTML([
                        reportDir: '.',
                        reportFiles: 'report.html',
                        reportName: 'DevTools Analysis Report'
                    ])
                }
            }
        }

        stage('Quality Gate') {
            steps {
                script {
                    def importCheck = sh(
                        script: 'qontinui-devtools import check ./src --strict',
                        returnStatus: true
                    )
                    def raceCheck = sh(
                        script: 'qontinui-devtools concurrency check ./src --severity high',
                        returnStatus: true
                    )

                    if (importCheck != 0 || raceCheck != 0) {
                        error("Quality gate failed")
                    }
                }
            }
        }
    }

    post {
        always {
            cleanWs()
        }
    }
}
```

---

## CircleCI

### `.circleci/config.yml`

```yaml
version: 2.1

orbs:
  python: circleci/python@2.1.1

jobs:
  analyze:
    docker:
      - image: cimg/python:3.11
    steps:
      - checkout

      - restore_cache:
          keys:
            - v1-dependencies-{{ checksum "requirements.txt" }}
            - v1-dependencies-

      - run:
          name: Install dependencies
          command: |
            python -m pip install --upgrade pip
            pip install qontinui-devtools

      - save_cache:
          paths:
            - ~/.cache/pip
          key: v1-dependencies-{{ checksum "requirements.txt" }}

      - run:
          name: Run import analysis
          command: |
            qontinui-devtools import check ./src \
              --output import_report.json \
              --format json

      - run:
          name: Run concurrency analysis
          command: |
            qontinui-devtools concurrency check ./src \
              --output race_report.json \
              --format json

      - run:
          name: Generate comprehensive report
          command: |
            qontinui-devtools analyze ./src \
              --report report.html \
              --format html

      - store_artifacts:
          path: import_report.json
          destination: reports/import_report.json

      - store_artifacts:
          path: race_report.json
          destination: reports/race_report.json

      - store_artifacts:
          path: report.html
          destination: reports/report.html

      - store_test_results:
          path: reports

workflows:
  version: 2
  analyze-workflow:
    jobs:
      - analyze:
          filters:
            branches:
              only:
                - main
                - develop
```

---

## Azure Pipelines

### `azure-pipelines.yml`

```yaml
trigger:
  branches:
    include:
      - main
      - develop

pr:
  branches:
    include:
      - main
      - develop

pool:
  vmImage: 'ubuntu-latest'

variables:
  python.version: '3.11'

stages:
  - stage: Analysis
    displayName: 'Static Analysis'
    jobs:
      - job: ImportAnalysis
        displayName: 'Import Analysis'
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '$(python.version)'

          - script: |
              python -m pip install --upgrade pip
              pip install qontinui-devtools
            displayName: 'Install dependencies'

          - script: |
              qontinui-devtools import check ./src \
                --output $(Build.ArtifactStagingDirectory)/import_report.json \
                --format json
            displayName: 'Check circular dependencies'

          - task: PublishBuildArtifacts@1
            inputs:
              pathToPublish: '$(Build.ArtifactStagingDirectory)'
              artifactName: 'import-analysis'

      - job: ConcurrencyAnalysis
        displayName: 'Concurrency Analysis'
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '$(python.version)'

          - script: |
              pip install qontinui-devtools
            displayName: 'Install DevTools'

          - script: |
              qontinui-devtools concurrency check ./src \
                --output $(Build.ArtifactStagingDirectory)/race_report.json \
                --format json
            displayName: 'Check race conditions'

          - task: PublishBuildArtifacts@1
            inputs:
              pathToPublish: '$(Build.ArtifactStagingDirectory)'
              artifactName: 'concurrency-analysis'

  - stage: Report
    displayName: 'Generate Report'
    dependsOn: Analysis
    jobs:
      - job: ComprehensiveReport
        displayName: 'Generate Comprehensive Report'
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '$(python.version)'

          - script: |
              pip install qontinui-devtools
            displayName: 'Install DevTools'

          - script: |
              qontinui-devtools analyze ./src \
                --report $(Build.ArtifactStagingDirectory)/report.html \
                --format html
            displayName: 'Generate report'

          - task: PublishBuildArtifacts@1
            inputs:
              pathToPublish: '$(Build.ArtifactStagingDirectory)'
              artifactName: 'comprehensive-report'
```

---

## Quality Gates

### SonarQube Integration

```bash
# Run analysis and convert to SonarQube format
qontinui-devtools analyze ./src --format json --output analysis.json

# Convert to SonarQube generic format
python scripts/convert_to_sonarqube.py analysis.json sonarqube.json

# Run SonarQube scanner
sonar-scanner \
  -Dsonar.externalIssuesReportPaths=sonarqube.json
```

### Custom Quality Gate Script

```python
#!/usr/bin/env python3
"""Quality gate script for CI/CD."""

import json
import sys
from pathlib import Path

def check_quality_gate(report_path: str) -> bool:
    """Check if quality gate criteria are met."""
    with open(report_path) as f:
        results = json.load(f)

    # Define quality criteria
    max_import_cycles = 0
    max_high_severity_races = 0
    max_critical_races = 0

    # Check imports
    import_cycles = results.get('imports', {}).get('cycles', 0)
    if import_cycles > max_import_cycles:
        print(f"❌ Too many circular dependencies: {import_cycles}")
        return False

    # Check concurrency
    races = results.get('concurrency', {}).get('races', [])
    high_severity = sum(1 for r in races if r.get('severity') == 'high')
    critical = sum(1 for r in races if r.get('severity') == 'critical')

    if high_severity > max_high_severity_races:
        print(f"❌ Too many high-severity race conditions: {high_severity}")
        return False

    if critical > max_critical_races:
        print(f"❌ Critical race conditions found: {critical}")
        return False

    print("✅ Quality gate passed")
    return True

if __name__ == '__main__':
    report_path = sys.argv[1] if len(sys.argv) > 1 else 'analysis.json'

    if not Path(report_path).exists():
        print(f"❌ Report not found: {report_path}")
        sys.exit(1)

    if not check_quality_gate(report_path):
        sys.exit(1)
```

---

## IDE Integration

### VS Code

Create `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Analyze Code",
      "type": "shell",
      "command": "qontinui-devtools",
      "args": ["analyze", "${workspaceFolder}/src"],
      "group": {
        "kind": "build",
        "isDefault": false
      },
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    },
    {
      "label": "Check Imports",
      "type": "shell",
      "command": "qontinui-devtools",
      "args": ["import", "check", "${workspaceFolder}/src"],
      "problemMatcher": []
    },
    {
      "label": "Check Concurrency",
      "type": "shell",
      "command": "qontinui-devtools",
      "args": ["concurrency", "check", "${workspaceFolder}/src"],
      "problemMatcher": []
    }
  ]
}
```

Create `.vscode/launch.json` for debugging:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "DevTools: Analyze",
      "type": "python",
      "request": "launch",
      "module": "qontinui_devtools.cli",
      "args": ["analyze", "${workspaceFolder}/src"],
      "console": "integratedTerminal"
    }
  ]
}
```

### PyCharm

1. **External Tools Configuration:**
   - Go to: Settings → Tools → External Tools
   - Click '+' to add new tool
   - Name: "Qontinui DevTools Analyze"
   - Program: `qontinui-devtools`
   - Arguments: `analyze $ProjectFileDir$/src`
   - Working directory: `$ProjectFileDir$`

2. **File Watcher:**
   - Go to: Settings → Tools → File Watchers
   - Click '+' to add new watcher
   - File type: Python
   - Scope: Project Files
   - Program: `qontinui-devtools`
   - Arguments: `import check $FilePath$`

---

## Docker Integration

### Dockerfile for CI

```dockerfile
FROM python:3.11-slim

# Install DevTools
RUN pip install --no-cache-dir qontinui-devtools

# Set working directory
WORKDIR /workspace

# Copy source code
COPY . .

# Run analysis
CMD ["qontinui-devtools", "analyze", "./src", "--report", "report.html", "--format", "html"]
```

### Docker Compose for Analysis

```yaml
version: '3.8'

services:
  analyze:
    build: .
    volumes:
      - ./src:/workspace/src
      - ./reports:/workspace/reports
    command: >
      qontinui-devtools analyze /workspace/src
        --report /workspace/reports/report.html
        --format html

  import-check:
    image: python:3.11-slim
    volumes:
      - ./src:/workspace/src
    command: >
      sh -c "pip install qontinui-devtools &&
             qontinui-devtools import check /workspace/src --strict"

  concurrency-check:
    image: python:3.11-slim
    volumes:
      - ./src:/workspace/src
    command: >
      sh -c "pip install qontinui-devtools &&
             qontinui-devtools concurrency check /workspace/src"
```

Run analysis:

```bash
docker-compose run analyze
```

---

## Custom Integrations

### Python API Integration

```python
from qontinui_devtools import (
    CircularDependencyDetector,
    RaceConditionDetector
)

def run_custom_analysis(path: str) -> dict:
    """Custom analysis integration."""
    results = {
        'passed': True,
        'issues': []
    }

    # Import analysis
    import_detector = CircularDependencyDetector(path)
    cycles = import_detector.analyze()

    if cycles:
        results['passed'] = False
        results['issues'].extend([
            {
                'type': 'circular_dependency',
                'cycle': cycle.cycle,
                'severity': cycle.severity
            }
            for cycle in cycles
        ])

    # Concurrency analysis
    race_detector = RaceConditionDetector(path)
    races = race_detector.analyze()

    if races:
        results['passed'] = False
        results['issues'].extend([
            {
                'type': 'race_condition',
                'state': race.shared_state.name,
                'severity': race.severity
            }
            for race in races
        ])

    return results
```

### Webhook Integration

```python
import requests
from qontinui_devtools import CircularDependencyDetector

def send_webhook(url: str, results: dict) -> None:
    """Send analysis results to webhook."""
    response = requests.post(url, json=results)
    response.raise_for_status()

# Run analysis
detector = CircularDependencyDetector('./src')
cycles = detector.analyze()

# Send results
webhook_url = 'https://example.com/webhook'
send_webhook(webhook_url, {
    'cycles_found': len(cycles),
    'status': 'failed' if cycles else 'passed'
})
```

---

## Best Practices

### 1. Fail Fast

Configure CI to fail early on critical issues:

```yaml
- name: Critical Checks
  run: |
    qontinui-devtools concurrency check ./src --severity critical
    if [ $? -ne 0 ]; then
      echo "Critical issues found - stopping pipeline"
      exit 1
    fi
```

### 2. Progressive Analysis

Run quick checks first, comprehensive analysis later:

```yaml
stages:
  - quick-check    # Fast: 30s
  - full-analysis  # Slow: 5min
  - stress-test    # Very slow: 30min (scheduled only)
```

### 3. Caching

Cache analysis results to speed up CI:

```yaml
- uses: actions/cache@v3
  with:
    path: ~/.qontinui-cache
    key: analysis-${{ hashFiles('**/*.py') }}
```

### 4. Notifications

Send notifications for analysis results:

```yaml
- name: Notify on failure
  if: failure()
  uses: slackapi/slack-github-action@v1
  with:
    payload: |
      {
        "text": "DevTools analysis failed in ${{ github.repository }}"
      }
```

---

**Version:** 0.1.0
**Last Updated:** 2025-10-28
**License:** MIT
