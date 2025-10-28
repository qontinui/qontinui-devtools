# GitLab CI Integration Guide

Complete guide for integrating qontinui-devtools with GitLab CI/CD.

## Quick Start

Copy `.gitlab-ci-example.yml` to `.gitlab-ci.yml` and customize:

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
    expire_in: 1 week
```

## Advanced Configuration

### Parallel Jobs

```yaml
stages:
  - analyze
  - report

circular-dependencies:
  stage: analyze
  image: python:3.11
  script:
    - pip install qontinui-devtools
    - qontinui-devtools import-cmd check . --output circular-deps.json --format json
  artifacts:
    paths:
      - circular-deps.json
    expire_in: 1 week

god-classes:
  stage: analyze
  image: python:3.11
  script:
    - pip install qontinui-devtools
    - qontinui-devtools architecture god-classes . --output god-classes.json --format json
  artifacts:
    paths:
      - god-classes.json
    expire_in: 1 week

race-conditions:
  stage: analyze
  image: python:3.11
  script:
    - pip install qontinui-devtools
    - qontinui-devtools concurrency check . --output race-conditions.json --format json
  artifacts:
    paths:
      - race-conditions.json
    expire_in: 1 week

quality-gates:
  stage: report
  image: python:3.11
  dependencies:
    - circular-dependencies
    - god-classes
    - race-conditions
  script:
    - pip install qontinui-devtools
    - |
      python -m qontinui_devtools.ci.quality_gates \
        --circular-deps circular-deps.json \
        --god-classes god-classes.json \
        --race-conditions race-conditions.json \
        --max-circular 0
```

### Code Quality Widget

Integrate with GitLab's Code Quality widget:

```yaml
code-quality:
  stage: analyze
  image: python:3.11
  script:
    - pip install qontinui-devtools
    - qontinui-devtools analyze . --output report.json --format json
    - python scripts/convert-to-gitlab-format.py report.json codequality.json
  artifacts:
    reports:
      codequality: codequality.json
```

**scripts/convert-to-gitlab-format.py**:

```python
import json
import sys

# Convert qontinui-devtools output to GitLab Code Quality format
input_file = sys.argv[1]
output_file = sys.argv[2]

with open(input_file) as f:
    data = json.load(f)

issues = []
for cycle in data.get('cycles', []):
    issues.append({
        'description': f"Circular dependency: {' -> '.join(cycle)}",
        'severity': 'major',
        'fingerprint': hash(' -> '.join(cycle)),
        'location': {
            'path': cycle[0],
            'lines': {'begin': 1}
        }
    })

with open(output_file, 'w') as f:
    json.dump(issues, f)
```

### Merge Request Comments

```yaml
mr-comment:
  stage: report
  image: python:3.11
  only:
    - merge_requests
  script:
    - pip install qontinui-devtools
    - |
      python -m qontinui_devtools.ci.pr_comment \
        --circular-deps circular-deps.json \
        --pr-number $CI_MERGE_REQUEST_IID \
        --output mr-comment.md
    - |
      # Post comment using GitLab API
      apt-get update && apt-get install -y curl
      COMMENT=$(cat mr-comment.md | jq -Rs .)
      curl --request POST \
        --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
        --header "Content-Type: application/json" \
        --data "{\"body\": $COMMENT}" \
        "$CI_API_V4_URL/projects/$CI_PROJECT_ID/merge_requests/$CI_MERGE_REQUEST_IID/notes"
```

### Scheduled Pipelines

```yaml
weekly-analysis:
  stage: analyze
  image: python:3.11
  only:
    - schedules
  script:
    - pip install qontinui-devtools
    - qontinui-devtools analyze . --output weekly-report-$(date +%Y-%m-%d).html
  artifacts:
    paths:
      - weekly-report-*.html
    expire_in: 90 days
```

## Job Templates

Create reusable templates:

```yaml
.qontinui-setup:
  image: python:3.11
  before_script:
    - pip install --upgrade pip
    - pip install qontinui-devtools
    - qontinui-devtools --version
    - mkdir -p $QONTINUI_OUTPUT_DIR
  cache:
    paths:
      - .cache/pip

circular-dependencies:
  extends: .qontinui-setup
  script:
    - qontinui-devtools import-cmd check . --output circular-deps.json --format json
```

## Rules and Conditions

### Run only on specific branches

```yaml
code-quality:
  script:
    - qontinui-devtools analyze .
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
    - if: '$CI_MERGE_REQUEST_IID'
```

### Run only when Python files change

```yaml
code-quality:
  script:
    - qontinui-devtools analyze .
  rules:
    - changes:
        - "**/*.py"
```

### Skip on draft MRs

```yaml
code-quality:
  script:
    - qontinui-devtools analyze .
  rules:
    - if: '$CI_MERGE_REQUEST_TITLE =~ /^Draft:/'
      when: never
    - if: '$CI_MERGE_REQUEST_IID'
```

## Environment Variables

```yaml
variables:
  QONTINUI_OUTPUT_DIR: "analysis-results"
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

code-quality:
  script:
    - qontinui-devtools analyze . --output $QONTINUI_OUTPUT_DIR/report.html
```

## Caching

```yaml
cache:
  key: ${CI_COMMIT_REF_SLUG}
  paths:
    - .cache/pip
    - venv/

before_script:
  - python -m venv venv
  - source venv/bin/activate
  - pip install qontinui-devtools
```

## Artifacts

### Upload reports

```yaml
code-quality:
  artifacts:
    paths:
      - analysis-results/
    reports:
      codequality: codequality.json
    expire_in: 30 days
    when: always
```

### Download from previous job

```yaml
quality-gates:
  dependencies:
    - circular-dependencies
    - god-classes
  script:
    - python -m qontinui_devtools.ci.quality_gates \
        --circular-deps circular-deps.json \
        --god-classes god-classes.json
```

## Pages Deployment

Deploy reports to GitLab Pages:

```yaml
pages:
  stage: deploy
  dependencies:
    - code-quality
  script:
    - mkdir public
    - cp analysis-results/report.html public/index.html
  artifacts:
    paths:
      - public
  only:
    - main
```

## Notifications

### Slack

```yaml
.notify-slack:
  script:
    - |
      curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"Quality gates failed for $CI_PROJECT_NAME\"}" \
        $SLACK_WEBHOOK_URL

quality-gates:
  script:
    - python -m qontinui_devtools.ci.quality_gates || !reference [.notify-slack, script]
```

### Email

```yaml
code-quality:
  script:
    - qontinui-devtools analyze .
  after_script:
    - |
      if [ $CI_JOB_STATUS == 'failed' ]; then
        echo "Quality gates failed" | mail -s "CI Failure" team@example.com
      fi
```

## Docker Services

Run with additional services:

```yaml
code-quality:
  services:
    - postgres:latest
  variables:
    POSTGRES_DB: test_db
  script:
    - qontinui-devtools analyze .
```

## Include External Configs

```yaml
include:
  - local: '.gitlab/ci/quality-checks.yml'
  - remote: 'https://example.com/shared-ci-config.yml'
```

## Best Practices

1. **Use templates** for DRY configuration
2. **Cache dependencies** for faster pipelines
3. **Run parallel jobs** when possible
4. **Set appropriate expiration** for artifacts
5. **Use rules** for conditional execution
6. **Integrate with Code Quality widget**
7. **Post MR comments** for visibility

## Troubleshooting

### Issue: Job timeout

```yaml
code-quality:
  timeout: 30m
  script:
    - qontinui-devtools analyze .
```

### Issue: Out of memory

```yaml
code-quality:
  tags:
    - high-memory
  script:
    - qontinui-devtools analyze .
```

### Issue: Cache not working

```yaml
cache:
  key:
    files:
      - requirements.txt
  paths:
    - .cache/pip
```

## Complete Example

See `.gitlab-ci-example.yml` in the repository for a complete, production-ready configuration.
