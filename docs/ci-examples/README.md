# CI/CD Integration Examples

This directory contains comprehensive examples for integrating qontinui-devtools into various CI/CD platforms.

## Quick Links

- **[Quick Start Guide](QUICK_START.md)** - Get started in under 5 minutes!
- **[Main CI/CD Documentation](../ci-integration.md)** - Complete integration guide

## Platform-Specific Guides

### Popular Platforms

| Platform | Guide | Difficulty | Setup Time |
|----------|-------|------------|------------|
| GitHub Actions | [github-actions.md](github-actions.md) | Easy | 2 min |
| GitLab CI | [gitlab-ci.md](gitlab-ci.md) | Easy | 3 min |
| Jenkins | [jenkins.md](jenkins.md) | Medium | 5 min |
| CircleCI | [circleci.md](circleci.md) | Easy | 3 min |
| Azure Pipelines | [azure-pipelines.md](azure-pipelines.md) | Medium | 4 min |
| Travis CI | [travis-ci.md](travis-ci.md) | Easy | 3 min |

### Examples

- **[Example PR Comment](example-pr-comment.md)** - See what PR comments look like
- **[Example GitHub Actions Output](example-github-actions-output.md)** - Full workflow output

## What's Included

Each platform guide includes:

1. ✅ **Quick Start** - Get running fast
2. ⚙️ **Advanced Configuration** - Parallel jobs, caching, etc.
3. 🔧 **Customization** - Adjust to your needs
4. 💡 **Best Practices** - Pro tips and recommendations
5. 🐛 **Troubleshooting** - Common issues and solutions
6. 📝 **Complete Examples** - Copy-paste ready configs

## Features

### Core Functionality

All platform integrations support:

- **Automated Analysis**
  - Circular dependency detection
  - God class identification
  - Race condition detection
  - Complexity analysis

- **Quality Gates**
  - Configurable thresholds
  - Build failure on violation
  - Clear error reporting

- **Reporting**
  - HTML reports
  - JSON output
  - Artifact storage

### Platform-Specific Features

| Feature | GitHub | GitLab | Jenkins | CircleCI | Azure | Travis |
|---------|--------|--------|---------|----------|-------|--------|
| PR Comments | ✅ | ✅ | ⚠️ | ❌ | ⚠️ | ❌ |
| Code Quality Widget | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Workflow Summaries | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Parallel Jobs | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Scheduled Runs | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Artifact Storage | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ |

Legend: ✅ Full Support | ⚠️ Partial Support | ❌ Not Available

## Configuration Templates

### Minimal Configuration

For simple projects, use the basic template:

```yaml
# Install
- pip install qontinui-devtools

# Analyze
- qontinui-devtools analyze . --output report.html

# Quality Gates
- python -m qontinui_devtools.ci.quality_gates --strict
```

### Standard Configuration

For most projects:

```yaml
# Install
- pip install qontinui-devtools

# Run analyses
- qontinui-devtools import-cmd check . --output circular-deps.json --format json
- qontinui-devtools architecture god-classes . --output god-classes.json --format json
- qontinui-devtools concurrency check . --output race-conditions.json --format json

# Quality gates with custom thresholds
- python -m qontinui_devtools.ci.quality_gates \
    --circular-deps circular-deps.json \
    --god-classes god-classes.json \
    --race-conditions race-conditions.json \
    --max-circular 0 \
    --max-god-classes 5 \
    --max-race-critical 0
```

### Advanced Configuration

For enterprise projects with trend tracking:

```yaml
# Install
- pip install qontinui-devtools

# Parallel analysis
- parallel-job: circular-deps
- parallel-job: god-classes
- parallel-job: race-conditions

# Generate report with trend comparison
- python -m qontinui_devtools.ci.pr_comment \
    --circular-deps circular-deps.json \
    --previous-results baseline.json \
    --output pr-comment.md

# Strict quality gates
- python -m qontinui_devtools.ci.quality_gates --strict
```

## Quality Gate Presets

Choose a preset that matches your needs:

### Strict (New Projects)

```bash
--max-circular 0 \
--max-god-classes 0 \
--max-race-critical 0 \
--max-race-high 0 \
--min-coverage 90 \
--max-avg-complexity 5
```

### Balanced (Most Projects)

```bash
--max-circular 0 \
--max-god-classes 5 \
--max-race-critical 0 \
--max-race-high 10 \
--min-coverage 80 \
--max-avg-complexity 10
```

### Relaxed (Legacy Code)

```bash
--max-circular 10 \
--max-god-classes 20 \
--max-race-critical 5 \
--max-race-high 50 \
--min-coverage 60 \
--max-avg-complexity 15
```

## Common Patterns

### Pattern 1: Parallel Analysis

Run multiple checks in parallel for faster CI:

```yaml
jobs:
  - circular-deps (parallel)
  - god-classes (parallel)
  - race-conditions (parallel)
  - quality-gates (depends on above)
```

### Pattern 2: PR-Only Checks

Run expensive checks only on PRs:

```yaml
if: pull_request
  - run: qontinui-devtools analyze .
  - post: pr-comment
```

### Pattern 3: Scheduled Trend Tracking

Weekly analysis for trend monitoring:

```yaml
schedule: weekly
  - run: qontinui-devtools analyze .
  - save: historical-data
```

### Pattern 4: Branch-Specific Thresholds

Stricter rules for main branch:

```yaml
if: branch == main
  thresholds: strict
else:
  thresholds: balanced
```

## Integration Strategies

### Strategy 1: Gradual Adoption

Start with warnings, then enforce:

1. **Week 1-2**: Run analyses, don't fail build
2. **Week 3-4**: Fail on critical issues only
3. **Week 5+**: Enforce all quality gates

### Strategy 2: Legacy Code

For existing codebases with issues:

1. **Baseline**: Document current state
2. **No Regression**: Prevent new issues
3. **Incremental**: Improve over time

### Strategy 3: New Projects

Start strict from day one:

1. **Zero Tolerance**: All metrics at zero
2. **Strict Gates**: Fail on any violation
3. **Maintain**: Keep quality high

## Getting Help

- 📚 [Main Documentation](../ci-integration.md)
- 🚀 [Quick Start](QUICK_START.md)
- 💬 [GitHub Discussions](https://github.com/qontinui/qontinui-devtools/discussions)
- 🐛 [Report Issues](https://github.com/qontinui/qontinui-devtools/issues)

## Contributing

Found a better way to integrate? Have an example for a new platform?

1. Fork the repository
2. Add your example to this directory
3. Update this README
4. Submit a pull request

We welcome contributions for:
- New CI platforms
- Integration patterns
- Best practices
- Troubleshooting tips

## License

All examples in this directory are provided under the MIT License.
Feel free to copy, modify, and use them in your projects!

---

**Ready to get started?** Check out the [Quick Start Guide](QUICK_START.md)!
