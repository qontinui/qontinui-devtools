# Setup Instructions for CI/CD Integration

Complete step-by-step instructions for setting up qontinui-devtools in your CI/CD pipeline.

## Prerequisites

- Python 3.8 or higher
- Git repository with Python code
- CI/CD platform account (GitHub, GitLab, Jenkins, etc.)

## Installation Methods

### Method 1: Using Installation Script (Recommended)

```bash
# Download and run installation script
curl -sSL https://raw.githubusercontent.com/qontinui/qontinui-devtools/main/scripts/install-ci.sh | bash

# Or if you have the repo cloned
chmod +x scripts/install-ci.sh
./scripts/install-ci.sh
```

### Method 2: Manual Installation

```bash
# Install via pip
pip install qontinui-devtools

# Verify installation
qontinui-devtools --version
```

### Method 3: From Source (Development)

```bash
# Clone repository
git clone https://github.com/qontinui/qontinui-devtools.git
cd qontinui-devtools

# Install in development mode
pip install -e .
```

## Platform Setup

### GitHub Actions

1. **Copy workflow file**
   ```bash
   mkdir -p .github/workflows
   cp .github/workflows/code-quality.yml .github/workflows/
   ```

2. **Customize configuration** (optional)
   ```bash
   # Edit .github/workflows/code-quality.yml
   # Adjust source paths, thresholds, etc.
   ```

3. **Commit and push**
   ```bash
   git add .github/workflows/code-quality.yml
   git commit -m "Add code quality workflow"
   git push
   ```

4. **Verify**
   - Create a pull request
   - Check the "Checks" tab
   - Review the analysis results

### GitLab CI

1. **Copy CI configuration**
   ```bash
   cp .gitlab-ci-example.yml .gitlab-ci.yml
   ```

2. **Set up GitLab token** (for MR comments)
   - Go to Settings → Access Tokens
   - Create token with `api` scope
   - Add as `GITLAB_TOKEN` in CI/CD variables (Settings → CI/CD → Variables)

3. **Customize configuration** (optional)
   ```bash
   # Edit .gitlab-ci.yml
   # Adjust stages, jobs, thresholds
   ```

4. **Commit and push**
   ```bash
   git add .gitlab-ci.yml
   git commit -m "Add code quality pipeline"
   git push
   ```

5. **Verify**
   - Go to CI/CD → Pipelines
   - Check the latest pipeline run
   - Review job outputs

### Jenkins

1. **Create Jenkinsfile**
   ```bash
   # Copy example Jenkinsfile from docs/ci-examples/jenkins.md
   # Or create your own
   ```

2. **Configure Jenkins job**
   - Create new Pipeline job
   - Point to your repository
   - Set Script Path to `Jenkinsfile`

3. **Install required plugins** (if needed)
   - Pipeline
   - Git
   - HTML Publisher (for reports)

4. **Run build**
   - Click "Build Now"
   - Review console output
   - Check published reports

### CircleCI

1. **Create CircleCI config**
   ```bash
   mkdir -p .circleci
   # Copy config from docs/ci-examples/circleci.md
   ```

2. **Enable CircleCI**
   - Go to app.circleci.com
   - Add project
   - Follow setup wizard

3. **Commit and push**
   ```bash
   git add .circleci/config.yml
   git commit -m "Add CircleCI configuration"
   git push
   ```

4. **Verify**
   - Check CircleCI dashboard
   - Review workflow run
   - Download artifacts

### Azure Pipelines

1. **Create Azure Pipelines config**
   ```bash
   # Copy config from docs/ci-examples/azure-pipelines.md
   ```

2. **Create pipeline in Azure DevOps**
   - Go to Pipelines → New Pipeline
   - Select your repository
   - Choose "Existing Azure Pipelines YAML file"
   - Select `/azure-pipelines.yml`

3. **Run pipeline**
   - Click "Run"
   - Monitor progress
   - Review results

### Travis CI

1. **Create Travis config**
   ```bash
   # Copy config from docs/ci-examples/travis-ci.md
   ```

2. **Enable Travis**
   - Go to travis-ci.com
   - Sign in with GitHub
   - Enable Travis for your repository

3. **Commit and push**
   ```bash
   git add .travis.yml
   git commit -m "Add Travis CI configuration"
   git push
   ```

## Local Setup (Pre-commit Hooks)

### Step 1: Install Pre-commit

```bash
pip install pre-commit
```

### Step 2: Copy Configuration

```bash
# Copy .pre-commit-config.yaml from qontinui-devtools
cp .pre-commit-config.yaml .
```

### Step 3: Install Hooks

```bash
pre-commit install
```

### Step 4: Test Hooks

```bash
# Run on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run
```

### Step 5: Customize (Optional)

Edit `.pre-commit-config.yaml` to adjust:
- Hook thresholds
- Enabled/disabled hooks
- Additional checks

## Configuration

### Quality Gate Thresholds

Edit your CI configuration to adjust thresholds:

```yaml
# Example for GitHub Actions
- name: Check quality gates
  run: |
    python -m qontinui_devtools.ci.quality_gates \
      --circular-deps circular-deps.json \
      --god-classes god-classes.json \
      --race-conditions race-conditions.json \
      --max-circular 0 \
      --max-god-classes 5 \
      --max-race-critical 0 \
      --max-race-high 10 \
      --min-coverage 80
```

### Source Paths

Update source paths in analysis commands:

```yaml
# Before (analyzes everything)
qontinui-devtools analyze .

# After (analyzes specific directory)
qontinui-devtools analyze src/

# Multiple directories
qontinui-devtools analyze src/ lib/ app/
```

### Output Directories

Customize where results are saved:

```yaml
# Set environment variable
export QONTINUI_OUTPUT_DIR=analysis-results

# Or use --output flag
qontinui-devtools analyze . --output reports/quality.html
```

### Branch Filters

Configure which branches trigger analysis:

```yaml
# GitHub Actions
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

# GitLab CI
only:
  - main
  - merge_requests
```

## Testing Your Setup

### 1. Dry Run (No Build)

Test locally before committing:

```bash
# Install qontinui-devtools
pip install qontinui-devtools

# Run analysis
qontinui-devtools analyze . --output test-report.html

# Check quality gates
python -m qontinui_devtools.ci.quality_gates \
  --circular-deps circular-deps.json \
  --max-circular 0
```

### 2. Test with Pre-commit

```bash
# Test pre-commit hooks
pre-commit run --all-files

# Should see checks running:
# - Check for circular imports
# - Check for god classes
# - Check for race conditions
# - Check cyclomatic complexity
```

### 3. Create Test PR

1. Create a new branch
2. Make a small change
3. Push and create PR
4. Verify CI runs
5. Check PR comment (if configured)

### 4. Verify Outputs

Check that you get:
- ✅ Analysis results in CI logs
- ✅ Quality gate pass/fail status
- ✅ Artifacts uploaded (reports, JSON files)
- ✅ PR comment (GitHub/GitLab)
- ✅ Workflow summary (GitHub)

## Troubleshooting

### Common Issues

#### Issue: "qontinui-devtools: command not found"

**Solution:**
```bash
# Verify Python and pip are available
python --version
pip --version

# Install qontinui-devtools
pip install qontinui-devtools

# Verify installation
which qontinui-devtools
qontinui-devtools --version
```

#### Issue: "Permission denied" on install script

**Solution:**
```bash
# Make script executable
chmod +x scripts/install-ci.sh

# Run script
./scripts/install-ci.sh
```

#### Issue: Quality gates always fail/pass

**Solution:**
```bash
# Check JSON files exist
ls -la *.json

# Verify JSON format
cat circular-deps.json | python -m json.tool

# Check thresholds are correct
python -m qontinui_devtools.ci.quality_gates --help
```

#### Issue: Pre-commit hooks not running

**Solution:**
```bash
# Uninstall and reinstall
pre-commit uninstall
pre-commit install

# Check .git/hooks/pre-commit exists
ls -la .git/hooks/

# Test manually
pre-commit run --all-files
```

#### Issue: PR comments not posting

**Solution:**

For GitHub:
```yaml
# Verify permissions in workflow
permissions:
  contents: read
  pull-requests: write
```

For GitLab:
```bash
# Check GITLAB_TOKEN is set
# Go to Settings → CI/CD → Variables
# Verify token has 'api' scope
```

#### Issue: Slow CI runs

**Solutions:**
```yaml
# 1. Enable caching
cache:
  paths:
    - ~/.cache/pip

# 2. Run jobs in parallel
jobs:
  - circular-deps (parallel)
  - god-classes (parallel)
  - race-conditions (parallel)

# 3. Skip on draft PRs
rules:
  - if: '$CI_MERGE_REQUEST_TITLE =~ /^Draft:/'
    when: never
```

## Advanced Setup

### Trend Tracking

Track metrics over time:

```bash
# 1. Save baseline on main branch
git checkout main
qontinui-devtools analyze . --output baseline.json --format json
git add baseline.json
git commit -m "Add quality baseline"

# 2. Compare in PRs
python -m qontinui_devtools.ci.pr_comment \
  --circular-deps current.json \
  --previous-results baseline.json \
  --output comparison.md
```

### Multiple Environments

Run analysis for different environments:

```yaml
matrix:
  include:
    - python: "3.8"
      env: PYTHON_38
    - python: "3.11"
      env: PYTHON_311
```

### Custom Reports

Generate custom reports:

```bash
# HTML report
qontinui-devtools analyze . --output report.html --format html

# JSON for processing
qontinui-devtools analyze . --output data.json --format json

# Text for logs
qontinui-devtools analyze . --output summary.txt --format text
```

### Notifications

Set up notifications on failures:

```yaml
# Slack
on_failure:
  - curl -X POST $SLACK_WEBHOOK -d "Quality gates failed"

# Email
on_failure:
  - mail -s "CI Failed" team@example.com
```

## Best Practices

1. **Start with relaxed thresholds** and tighten over time
2. **Run locally first** with pre-commit hooks
3. **Review results regularly** to identify trends
4. **Adjust thresholds** based on project needs
5. **Document exceptions** when bypassing quality gates
6. **Keep CI fast** with caching and parallel jobs
7. **Monitor CI time** and optimize if needed

## Next Steps

1. ✅ Complete initial setup
2. 📊 Review first analysis results
3. 🎯 Adjust quality gate thresholds
4. 🔧 Set up pre-commit hooks locally
5. 📈 Enable trend tracking
6. 👥 Train team on CI workflow
7. 📝 Document project-specific conventions

## Getting Help

- 📚 [Full Documentation](../ci-integration.md)
- 🚀 [Quick Start Guide](QUICK_START.md)
- 💬 [GitHub Discussions](https://github.com/qontinui/qontinui-devtools/discussions)
- 🐛 [Report Issues](https://github.com/qontinui/qontinui-devtools/issues)
- 📧 Email: support@qontinui.com

## Success Checklist

Use this checklist to verify your setup:

- [ ] qontinui-devtools installed in CI
- [ ] Analysis runs on PR/push
- [ ] Quality gates enforce thresholds
- [ ] Reports/artifacts uploaded
- [ ] PR comments working (if applicable)
- [ ] Pre-commit hooks installed locally
- [ ] Team trained on workflow
- [ ] Documentation updated
- [ ] Thresholds adjusted for project
- [ ] Notifications configured

**All checked?** Congratulations! Your CI/CD integration is complete! 🎉
