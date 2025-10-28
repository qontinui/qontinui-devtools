# CI/CD Quick Start Guide

Get qontinui-devtools running in your CI/CD pipeline in under 5 minutes!

## Choose Your Platform

Click your CI platform to jump to the quick setup:

1. [GitHub Actions](#github-actions) (Recommended)
2. [GitLab CI](#gitlab-ci)
3. [Jenkins](#jenkins)
4. [CircleCI](#circleci)
5. [Azure Pipelines](#azure-pipelines)
6. [Travis CI](#travis-ci)

## GitHub Actions

### Step 1: Copy Workflow File

Copy `.github/workflows/code-quality.yml` from qontinui-devtools repository to your repo.

### Step 2: Customize (Optional)

Edit the workflow file to adjust:
- Source directory (replace `.` with your source path like `src/`)
- Quality gate thresholds
- Branch filters

### Step 3: Commit and Push

```bash
git add .github/workflows/code-quality.yml
git commit -m "Add code quality checks"
git push
```

### Step 4: Create a PR

The workflow will automatically run on your next PR!

**That's it!** 🎉

[Full GitHub Actions guide →](github-actions.md)

---

## GitLab CI

### Step 1: Copy CI Configuration

```bash
# In your repository root
cp .gitlab-ci-example.yml .gitlab-ci.yml
```

### Step 2: Set Up Token (for MR comments)

1. Go to Settings → Access Tokens
2. Create token with `api` scope
3. Add as `GITLAB_TOKEN` in CI/CD variables

### Step 3: Customize (Optional)

Edit `.gitlab-ci.yml` to adjust thresholds and paths.

### Step 4: Commit and Push

```bash
git add .gitlab-ci.yml
git commit -m "Add code quality checks"
git push
```

**That's it!** 🎉

[Full GitLab CI guide →](gitlab-ci.md)

---

## Jenkins

### Step 1: Create Jenkinsfile

Create `Jenkinsfile` in your repository root:

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
                sh 'qontinui-devtools analyze . --output report.html'
            }
        }
        stage('Quality Gates') {
            steps {
                sh 'python -m qontinui_devtools.ci.quality_gates --strict'
            }
        }
    }
    post {
        always {
            publishHTML([
                reportDir: '.',
                reportFiles: 'report.html',
                reportName: 'Code Quality Report'
            ])
        }
    }
}
```

### Step 2: Configure Job

1. Create new Pipeline job
2. Point to your repository
3. Set Script Path to `Jenkinsfile`

### Step 3: Run

Click "Build Now" to test!

**That's it!** 🎉

[Full Jenkins guide →](jenkins.md)

---

## CircleCI

### Step 1: Create Config File

Create `.circleci/config.yml`:

```yaml
version: 2.1

jobs:
  code-quality:
    docker:
      - image: cimg/python:3.11
    steps:
      - checkout
      - run: pip install qontinui-devtools
      - run: qontinui-devtools analyze . --output report.html
      - store_artifacts:
          path: report.html

workflows:
  quality-check:
    jobs:
      - code-quality
```

### Step 2: Commit and Push

```bash
git add .circleci/config.yml
git commit -m "Add code quality checks"
git push
```

**That's it!** 🎉

[Full CircleCI guide →](circleci.md)

---

## Azure Pipelines

### Step 1: Create Pipeline File

Create `azure-pipelines.yml`:

```yaml
trigger:
  - main

pool:
  vmImage: 'ubuntu-latest'

steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: '3.11'

  - script: pip install qontinui-devtools
    displayName: 'Install qontinui-devtools'

  - script: qontinui-devtools analyze . --output report.html
    displayName: 'Run analysis'

  - task: PublishBuildArtifacts@1
    inputs:
      pathToPublish: 'report.html'
      artifactName: 'code-quality-report'
```

### Step 2: Create Pipeline

1. Go to Azure DevOps
2. Create new pipeline
3. Select your repository
4. Choose "Existing Azure Pipelines YAML file"
5. Select `/azure-pipelines.yml`

**That's it!** 🎉

[Full Azure Pipelines guide →](azure-pipelines.md)

---

## Travis CI

### Step 1: Create Travis Config

Create `.travis.yml`:

```yaml
language: python
python: "3.11"

install:
  - pip install qontinui-devtools

script:
  - qontinui-devtools analyze . --output report.html
  - python -m qontinui_devtools.ci.quality_gates --strict
```

### Step 2: Enable Travis

1. Go to travis-ci.com
2. Enable Travis for your repository
3. Push to trigger build

**That's it!** 🎉

[Full Travis CI guide →](travis-ci.md)

---

## Local Setup (Pre-commit Hooks)

Want to catch issues before committing? Set up pre-commit hooks!

### Step 1: Install Pre-commit

```bash
pip install pre-commit
```

### Step 2: Copy Config

```bash
# Copy .pre-commit-config.yaml from qontinui-devtools
cp .pre-commit-config.yaml .
```

### Step 3: Install Hooks

```bash
pre-commit install
```

### Step 4: Test

```bash
# Test on all files
pre-commit run --all-files
```

Now hooks run automatically on every commit!

---

## Customizing Quality Gates

All platforms support customizable thresholds. Here's how:

### Strict Mode (Zero Tolerance)

```bash
python -m qontinui_devtools.ci.quality_gates \
  --strict
```

### Custom Thresholds

```bash
python -m qontinui_devtools.ci.quality_gates \
  --max-circular 0 \
  --max-god-classes 5 \
  --max-race-critical 0 \
  --max-race-high 10 \
  --min-coverage 80
```

### Relaxed Mode (Legacy Code)

```bash
python -m qontinui_devtools.ci.quality_gates \
  --max-circular 10 \
  --max-god-classes 20 \
  --max-race-critical 5 \
  --max-race-high 50 \
  --min-coverage 60
```

---

## What You Get

Once set up, you automatically get:

✅ **Automated Analysis**
- Circular dependency detection
- God class identification
- Race condition analysis
- Code complexity metrics

✅ **Quality Gates**
- Build fails if thresholds exceeded
- Configurable for your needs
- Clear error messages

✅ **PR Comments** (GitHub/GitLab)
- Automatic summary on PRs
- Trend comparison with main branch
- Actionable recommendations

✅ **Reports & Artifacts**
- HTML reports for easy viewing
- JSON data for custom processing
- Historical tracking

✅ **Pre-commit Hooks** (Local)
- Catch issues before committing
- Fast feedback loop
- Customizable checks

---

## Need Help?

- 📚 [Full Documentation](../ci-integration.md)
- 💬 [GitHub Discussions](https://github.com/qontinui/qontinui-devtools/discussions)
- 🐛 [Report Issues](https://github.com/qontinui/qontinui-devtools/issues)
- 📧 Email: support@qontinui.com

---

## Next Steps

1. ✅ Set up CI pipeline (you just did this!)
2. 📝 Review first analysis results
3. 🎯 Adjust quality gate thresholds
4. 🔧 Set up pre-commit hooks locally
5. 📊 Enable trend tracking
6. 🚀 Integrate into code review process

Happy coding! 🎉
