# CircleCI Integration Guide

Complete guide for integrating qontinui-devtools with CircleCI.

## Quick Start

Create `.circleci/config.yml` in your repository:

```yaml
version: 2.1

orbs:
  python: circleci/python@2.1.1

jobs:
  code-quality:
    docker:
      - image: cimg/python:3.11
    resource_class: medium

    steps:
      - checkout

      - restore_cache:
          keys:
            - deps-{{ checksum "requirements.txt" }}
            - deps-

      - run:
          name: Install qontinui-devtools
          command: |
            pip install qontinui-devtools
            qontinui-devtools --version

      - save_cache:
          key: deps-{{ checksum "requirements.txt" }}
          paths:
            - ~/.cache/pip

      - run:
          name: Create output directory
          command: mkdir -p analysis-results

      - run:
          name: Check circular dependencies
          command: |
            qontinui-devtools import-cmd check . \
              --output analysis-results/circular-deps.json \
              --format json

      - run:
          name: Detect god classes
          command: |
            qontinui-devtools architecture god-classes . \
              --min-lines 500 \
              --output analysis-results/god-classes.json \
              --format json

      - run:
          name: Check race conditions
          command: |
            qontinui-devtools concurrency check . \
              --output analysis-results/race-conditions.json \
              --format json

      - run:
          name: Generate report
          command: |
            qontinui-devtools analyze . \
              --output analysis-results/report.html \
              --format html

      - run:
          name: Check quality gates
          command: |
            python -m qontinui_devtools.ci.quality_gates \
              --circular-deps analysis-results/circular-deps.json \
              --god-classes analysis-results/god-classes.json \
              --race-conditions analysis-results/race-conditions.json \
              --max-circular 0 \
              --max-god-classes 5 \
              --max-race-critical 0

      - store_artifacts:
          path: analysis-results
          destination: code-quality-reports

      - store_test_results:
          path: analysis-results

workflows:
  version: 2
  quality-check:
    jobs:
      - code-quality
```

## Advanced Configuration

### Parallel Execution

```yaml
version: 2.1

jobs:
  circular-deps:
    docker:
      - image: cimg/python:3.11
    steps:
      - checkout
      - run: pip install qontinui-devtools
      - run: qontinui-devtools import-cmd check . --output circular-deps.json --format json
      - persist_to_workspace:
          root: .
          paths:
            - circular-deps.json

  god-classes:
    docker:
      - image: cimg/python:3.11
    steps:
      - checkout
      - run: pip install qontinui-devtools
      - run: qontinui-devtools architecture god-classes . --output god-classes.json --format json
      - persist_to_workspace:
          root: .
          paths:
            - god-classes.json

  race-conditions:
    docker:
      - image: cimg/python:3.11
    steps:
      - checkout
      - run: pip install qontinui-devtools
      - run: qontinui-devtools concurrency check . --output race-conditions.json --format json
      - persist_to_workspace:
          root: .
          paths:
            - race-conditions.json

  quality-gates:
    docker:
      - image: cimg/python:3.11
    steps:
      - checkout
      - attach_workspace:
          at: .
      - run: pip install qontinui-devtools
      - run: |
          python -m qontinui_devtools.ci.quality_gates \
            --circular-deps circular-deps.json \
            --god-classes god-classes.json \
            --race-conditions race-conditions.json \
            --max-circular 0 \
            --max-god-classes 5

workflows:
  version: 2
  parallel-analysis:
    jobs:
      - circular-deps
      - god-classes
      - race-conditions
      - quality-gates:
          requires:
            - circular-deps
            - god-classes
            - race-conditions
```

### PR-only Checks

```yaml
workflows:
  version: 2
  quality-check:
    jobs:
      - code-quality:
          filters:
            branches:
              ignore:
                - main
                - develop
```

### Scheduled Analysis

```yaml
workflows:
  version: 2
  quality-check:
    jobs:
      - code-quality

  weekly-analysis:
    triggers:
      - schedule:
          cron: "0 0 * * 0"
          filters:
            branches:
              only:
                - main
    jobs:
      - code-quality
```

### With Orbs

```yaml
version: 2.1

orbs:
  python: circleci/python@2.1.1
  slack: circleci/slack@4.12.1

jobs:
  code-quality:
    executor: python/default
    steps:
      - checkout
      - python/install-packages:
          pkg-manager: pip
          pip-dependency-file: requirements.txt
      - run:
          name: Run analysis
          command: qontinui-devtools analyze . --output report.html
      - slack/notify:
          event: fail
          template: basic_fail_1

workflows:
  quality-check:
    jobs:
      - code-quality
```

## Environment Variables

```yaml
jobs:
  code-quality:
    docker:
      - image: cimg/python:3.11
    environment:
      QONTINUI_OUTPUT_DIR: analysis-results
      QONTINUI_MAX_CIRCULAR: 0
      QONTINUI_MAX_GOD_CLASSES: 5
```

## Optimization

### Caching

```yaml
- restore_cache:
    keys:
      - v1-deps-{{ checksum "requirements.txt" }}
      - v1-deps-

- run: pip install qontinui-devtools

- save_cache:
    key: v1-deps-{{ checksum "requirements.txt" }}
    paths:
      - ~/.cache/pip
```

### Resource Classes

```yaml
jobs:
  code-quality:
    docker:
      - image: cimg/python:3.11
    resource_class: large  # Faster execution
```

## Best Practices

1. **Use caching** for faster builds
2. **Run parallel jobs** when possible
3. **Store artifacts** for easy access
4. **Set up notifications** for failures
5. **Use scheduled workflows** for trend tracking

## Troubleshooting

### Issue: Out of memory

```yaml
jobs:
  code-quality:
    resource_class: large
    docker:
      - image: cimg/python:3.11
```

### Issue: Build timeout

```yaml
jobs:
  code-quality:
    docker:
      - image: cimg/python:3.11
    steps:
      - run:
          name: Run analysis
          command: qontinui-devtools analyze .
          no_output_timeout: 30m
```

## Complete Example

See the Quick Start section for a complete, production-ready configuration.
