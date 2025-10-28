# Travis CI Integration Guide

Complete guide for integrating qontinui-devtools with Travis CI.

## Quick Start

Create `.travis.yml` in your repository root:

```yaml
language: python

python:
  - "3.11"

cache:
  directories:
    - $HOME/.cache/pip

install:
  - pip install --upgrade pip
  - pip install qontinui-devtools
  - qontinui-devtools --version

before_script:
  - mkdir -p analysis-results

script:
  # Run analyses
  - qontinui-devtools import-cmd check . --output analysis-results/circular-deps.json --format json || true
  - qontinui-devtools architecture god-classes . --min-lines 500 --output analysis-results/god-classes.json --format json || true
  - qontinui-devtools concurrency check . --output analysis-results/race-conditions.json --format json || true

  # Generate report
  - qontinui-devtools analyze . --output analysis-results/report.html --format html || true

  # Check quality gates
  - python -m qontinui_devtools.ci.quality_gates --circular-deps analysis-results/circular-deps.json --god-classes analysis-results/god-classes.json --race-conditions analysis-results/race-conditions.json --max-circular 0 --max-god-classes 5 --max-race-critical 0

after_script:
  - ls -la analysis-results/

# Deploy reports to GitHub Pages (optional)
deploy:
  provider: pages
  skip_cleanup: true
  github_token: $GITHUB_TOKEN
  keep_history: true
  local_dir: analysis-results
  on:
    branch: main
```

## Advanced Configuration

### Build Matrix

Test with multiple Python versions:

```yaml
language: python

python:
  - "3.8"
  - "3.9"
  - "3.10"
  - "3.11"

jobs:
  include:
    - python: "3.11"
      env: QUALITY_GATES=true

script:
  - qontinui-devtools analyze .
  - if [ "$QUALITY_GATES" = "true" ]; then python -m qontinui_devtools.ci.quality_gates --strict; fi
```

### Parallel Jobs

```yaml
jobs:
  include:
    - stage: analyze
      name: "Circular Dependencies"
      script: qontinui-devtools import-cmd check . --output circular-deps.json --format json

    - stage: analyze
      name: "God Classes"
      script: qontinui-devtools architecture god-classes . --output god-classes.json --format json

    - stage: analyze
      name: "Race Conditions"
      script: qontinui-devtools concurrency check . --output race-conditions.json --format json

    - stage: quality-gates
      script: python -m qontinui_devtools.ci.quality_gates --circular-deps circular-deps.json --max-circular 0

stages:
  - analyze
  - quality-gates
```

### PR-only Checks

```yaml
if: type = pull_request

script:
  - qontinui-devtools analyze .
  - python -m qontinui_devtools.ci.pr_comment --circular-deps circular-deps.json --pr-number $TRAVIS_PULL_REQUEST --output pr-comment.md
```

### Scheduled Builds

```yaml
if: type = cron

script:
  - qontinui-devtools analyze . --output weekly-report-$(date +%Y-%m-%d).html
  - # Upload to storage
```

## Docker Integration

```yaml
language: minimal

services:
  - docker

script:
  - docker run -v $(pwd):/workspace -w /workspace python:3.11 bash -c "pip install qontinui-devtools && qontinui-devtools analyze ."
```

## Notifications

### Slack

```yaml
notifications:
  slack:
    rooms:
      - secure: "encrypted-token"
    on_success: change
    on_failure: always
    template:
      - "Build <%{build_url}|#%{build_number}> %{result} for %{repository_slug}"
      - "Quality gates: %{result}"
```

### Email

```yaml
notifications:
  email:
    recipients:
      - dev-team@example.com
    on_success: change
    on_failure: always
```

## Artifacts

Travis doesn't support artifacts directly, but you can upload to external services:

### Upload to S3

```yaml
addons:
  artifacts:
    paths:
      - analysis-results/
    target_paths: builds/$TRAVIS_BUILD_NUMBER
```

### Upload to GitHub Releases

```yaml
deploy:
  provider: releases
  api_key: $GITHUB_TOKEN
  file: analysis-results/report.html
  skip_cleanup: true
  on:
    tags: true
```

## Environment Variables

```yaml
env:
  global:
    - QONTINUI_OUTPUT_DIR=analysis-results
    - QONTINUI_MAX_CIRCULAR=0
    - QONTINUI_MAX_GOD_CLASSES=5

script:
  - python -m qontinui_devtools.ci.quality_gates --max-circular $QONTINUI_MAX_CIRCULAR
```

## Caching

```yaml
cache:
  directories:
    - $HOME/.cache/pip
    - node_modules

before_cache:
  - rm -f $HOME/.cache/pip/log/debug.log
```

## Best Practices

1. **Use caching** for faster builds
2. **Fail fast** with quality gates
3. **Run parallel jobs** when possible
4. **Set up notifications** for failures
5. **Deploy reports** to GitHub Pages

## Troubleshooting

### Issue: Build timeout

```yaml
install:
  - travis_wait 30 pip install qontinui-devtools
```

### Issue: Memory limit

```yaml
sudo: required

before_install:
  - sudo sysctl -w vm.max_map_count=262144
```

### Issue: Python version

```yaml
python:
  - "3.11"

before_install:
  - python --version
  - pip --version
```

## Complete Example

See the Quick Start section for a complete, production-ready configuration.
