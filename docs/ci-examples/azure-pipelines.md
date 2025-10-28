# Azure Pipelines Integration Guide

Complete guide for integrating qontinui-devtools with Azure Pipelines.

## Quick Start

Create `azure-pipelines.yml` in your repository root:

```yaml
trigger:
  branches:
    include:
      - main
      - develop
  paths:
    include:
      - '**/*.py'

pr:
  branches:
    include:
      - main
      - develop

pool:
  vmImage: 'ubuntu-latest'

variables:
  pythonVersion: '3.11'
  outputDir: 'analysis-results'

stages:
  - stage: CodeQuality
    displayName: 'Code Quality Analysis'
    jobs:
      - job: Analyze
        displayName: 'Run Quality Checks'
        steps:
          - task: UsePythonVersion@0
            displayName: 'Set up Python'
            inputs:
              versionSpec: '$(pythonVersion)'
              addToPath: true

          - script: |
              python -m pip install --upgrade pip
              pip install qontinui-devtools
              qontinui-devtools --version
            displayName: 'Install qontinui-devtools'

          - script: |
              mkdir -p $(outputDir)
            displayName: 'Create output directory'

          - script: |
              qontinui-devtools import-cmd check . \
                --output $(outputDir)/circular-deps.json \
                --format json
            displayName: 'Check circular dependencies'
            continueOnError: true

          - script: |
              qontinui-devtools architecture god-classes . \
                --min-lines 500 \
                --output $(outputDir)/god-classes.json \
                --format json
            displayName: 'Detect god classes'
            continueOnError: true

          - script: |
              qontinui-devtools concurrency check . \
                --output $(outputDir)/race-conditions.json \
                --format json
            displayName: 'Check race conditions'
            continueOnError: true

          - script: |
              qontinui-devtools analyze . \
                --output $(outputDir)/analysis-report.html \
                --format html
            displayName: 'Generate comprehensive report'
            continueOnError: true

          - script: |
              python -m qontinui_devtools.ci.quality_gates \
                --circular-deps $(outputDir)/circular-deps.json \
                --god-classes $(outputDir)/god-classes.json \
                --race-conditions $(outputDir)/race-conditions.json \
                --max-circular 0 \
                --max-god-classes 5 \
                --max-race-critical 0
            displayName: 'Check quality gates'

          - task: PublishBuildArtifacts@1
            displayName: 'Publish analysis artifacts'
            condition: always()
            inputs:
              pathToPublish: '$(outputDir)'
              artifactName: 'code-quality-report'
              publishLocation: 'Container'

          - task: PublishTestResults@2
            displayName: 'Publish test results'
            condition: always()
            inputs:
              testResultsFormat: 'JUnit'
              testResultsFiles: '$(outputDir)/*.xml'
              failTaskOnFailedTests: false
```

## Advanced Configuration

### Parallel Jobs

```yaml
stages:
  - stage: Analyze
    displayName: 'Code Analysis'
    jobs:
      - job: CircularDeps
        displayName: 'Circular Dependencies'
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '3.11'
          - script: pip install qontinui-devtools
          - script: qontinui-devtools import-cmd check . --output circular-deps.json --format json
          - publish: circular-deps.json
            artifact: circular-deps

      - job: GodClasses
        displayName: 'God Classes'
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '3.11'
          - script: pip install qontinui-devtools
          - script: qontinui-devtools architecture god-classes . --output god-classes.json --format json
          - publish: god-classes.json
            artifact: god-classes

      - job: RaceConditions
        displayName: 'Race Conditions'
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '3.11'
          - script: pip install qontinui-devtools
          - script: qontinui-devtools concurrency check . --output race-conditions.json --format json
          - publish: race-conditions.json
            artifact: race-conditions

  - stage: QualityGates
    displayName: 'Quality Gates'
    dependsOn: Analyze
    jobs:
      - job: CheckGates
        displayName: 'Check Quality Gates'
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '3.11'
          - script: pip install qontinui-devtools
          - download: current
            artifact: circular-deps
          - download: current
            artifact: god-classes
          - download: current
            artifact: race-conditions
          - script: |
              python -m qontinui_devtools.ci.quality_gates \
                --circular-deps $(Pipeline.Workspace)/circular-deps/circular-deps.json \
                --god-classes $(Pipeline.Workspace)/god-classes/god-classes.json \
                --race-conditions $(Pipeline.Workspace)/race-conditions/race-conditions.json \
                --max-circular 0
```

### PR Comments

```yaml
- task: PowerShell@2
  displayName: 'Generate PR comment'
  condition: eq(variables['Build.Reason'], 'PullRequest')
  inputs:
    targetType: 'inline'
    script: |
      python -m qontinui_devtools.ci.pr_comment `
        --circular-deps $(outputDir)/circular-deps.json `
        --god-classes $(outputDir)/god-classes.json `
        --pr-number $(System.PullRequest.PullRequestNumber) `
        --pr-title "$(System.PullRequest.SourceBranch)" `
        --output pr-comment.md

- task: GitHubComment@0
  displayName: 'Post PR comment'
  condition: eq(variables['Build.Reason'], 'PullRequest')
  inputs:
    gitHubConnection: 'GitHub'
    repositoryName: '$(Build.Repository.Name)'
    id: $(System.PullRequest.PullRequestNumber)
    comment: |
      $(cat pr-comment.md)
```

### Scheduled Runs

```yaml
schedules:
  - cron: '0 0 * * 0'
    displayName: 'Weekly analysis'
    branches:
      include:
        - main
    always: true
```

### Multi-platform

```yaml
strategy:
  matrix:
    Linux:
      vmImage: 'ubuntu-latest'
    macOS:
      vmImage: 'macOS-latest'
    Windows:
      vmImage: 'windows-latest'
  maxParallel: 3

pool:
  vmImage: '$(vmImage)'
```

## Templates

Create reusable templates for common tasks.

**templates/install-qontinui.yml**:

```yaml
steps:
  - task: UsePythonVersion@0
    displayName: 'Set up Python'
    inputs:
      versionSpec: '3.11'

  - script: |
      python -m pip install --upgrade pip
      pip install qontinui-devtools
    displayName: 'Install qontinui-devtools'
```

**Use template**:

```yaml
jobs:
  - job: Analyze
    steps:
      - template: templates/install-qontinui.yml
      - script: qontinui-devtools analyze .
```

## Variable Groups

Store configuration in variable groups:

```yaml
variables:
  - group: code-quality-config

jobs:
  - job: QualityGates
    steps:
      - script: |
          python -m qontinui_devtools.ci.quality_gates \
            --max-circular $(maxCircular) \
            --max-god-classes $(maxGodClasses)
```

## Notifications

### Email

```yaml
- task: SendEmail@1
  displayName: 'Send failure notification'
  condition: failed()
  inputs:
    to: 'team@example.com'
    subject: 'Code quality check failed'
    body: 'Build $(Build.BuildNumber) failed quality gates'
```

### Slack

```yaml
- task: SlackNotification@1
  displayName: 'Notify Slack'
  condition: failed()
  inputs:
    SlackApiToken: '$(SlackToken)'
    MessageAuthor: 'Azure Pipelines'
    Channel: '#dev-team'
    Message: 'Quality gates failed for $(Build.Repository.Name)'
```

## Caching

```yaml
- task: Cache@2
  displayName: 'Cache pip packages'
  inputs:
    key: 'pip | "$(Agent.OS)" | requirements.txt'
    path: $(Pipeline.Workspace)/.pip
    restoreKeys: |
      pip | "$(Agent.OS)"
      pip

- script: |
    pip install --cache-dir $(Pipeline.Workspace)/.pip qontinui-devtools
  displayName: 'Install with cache'
```

## Best Practices

1. **Use templates** for reusability
2. **Cache dependencies** for faster builds
3. **Run parallel jobs** when possible
4. **Store artifacts** for historical tracking
5. **Set up notifications** for failures
6. **Use variable groups** for configuration

## Troubleshooting

### Issue: Python not found

```yaml
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.11'
    addToPath: true
    architecture: 'x64'
```

### Issue: Permission denied

```yaml
- script: |
    sudo pip install qontinui-devtools
  displayName: 'Install with sudo'
```

### Issue: Artifacts not published

```yaml
- task: PublishBuildArtifacts@1
  condition: always()
  inputs:
    pathToPublish: '$(outputDir)'
    artifactName: 'reports'
```

## Complete Example

See the Quick Start section for a complete, production-ready configuration.
