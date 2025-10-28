# Dependency Health Checker

A comprehensive dependency health checker for Python projects that monitors package health, security vulnerabilities, outdated versions, and license compatibility.

## Features

- **Multiple Dependency File Formats**: Supports `pyproject.toml`, `requirements.txt`, `setup.py`, and `poetry.lock`
- **Version Analysis**: Detects outdated packages with semantic version awareness (major/minor/patch)
- **Security Scanning**: Checks for known vulnerabilities using local vulnerability database
- **Deprecation Detection**: Identifies deprecated packages with migration suggestions
- **License Compatibility**: Analyzes license conflicts (GPL, MIT, BSD, etc.)
- **Circular Dependencies**: Detects circular dependency chains
- **Health Scoring**: Calculates individual and overall health scores (0-100)
- **PyPI Integration**: Fetches latest package information from PyPI with caching and rate limiting
- **Offline Mode**: Works with cached data when internet is unavailable
- **CI/CD Integration**: Can fail builds on critical vulnerabilities

## Installation

```python
from qontinui_devtools.dependencies import DependencyHealthChecker
```

## Quick Start

```python
from qontinui_devtools.dependencies import DependencyHealthChecker

# Initialize checker
checker = DependencyHealthChecker()

# Check project health
report = checker.check_health("/path/to/project")

# Display results
print(f"Health Score: {report.overall_health_score:.1f}/100")
print(f"Vulnerable packages: {report.vulnerable_count}")
print(f"Outdated packages: {report.outdated_count}")

# Get specific issues
for dep in report.get_vulnerable_dependencies():
    print(f"VULNERABILITY: {dep.name}")
    for vuln in dep.vulnerabilities:
        print(f"  - {vuln}")
```

## Advanced Usage

### Offline Mode

```python
checker = DependencyHealthChecker(offline_mode=True)
report = checker.check_health("/path/to/project")
```

### Fail on Vulnerabilities (CI/CD)

```python
try:
    report = checker.check_health(
        "/path/to/project",
        fail_on_vulnerable=True
    )
except ValueError as e:
    print(f"Build failed: {e}")
    sys.exit(1)
```

### Custom Cache Directory

```python
from pathlib import Path

checker = DependencyHealthChecker(
    cache_dir=Path("/custom/cache/dir")
)
```

### Exclude Dev Dependencies

```python
report = checker.check_health(
    "/path/to/project",
    include_dev=False
)
```

## Report Structure

### DependencyHealthReport

- `total_dependencies`: Total number of dependencies analyzed
- `healthy_count`: Number of healthy dependencies
- `outdated_count`: Number of outdated dependencies
- `vulnerable_count`: Number of vulnerable dependencies
- `deprecated_count`: Number of deprecated dependencies
- `overall_health_score`: Overall health score (0-100)
- `recommendations`: List of actionable recommendations
- `circular_dependencies`: List of circular dependency chains
- `license_conflicts`: List of license compatibility conflicts
- `total_vulnerabilities`: Total vulnerability count
- `critical_vulnerabilities`: Critical vulnerability count

### DependencyInfo

Each dependency includes:

- `name`: Package name
- `current_version`: Currently installed version
- `latest_version`: Latest available version
- `update_type`: Update type (major/minor/patch)
- `health_status`: Health status (healthy/outdated/vulnerable/deprecated)
- `vulnerabilities`: List of security vulnerabilities
- `license`: Package license
- `license_category`: License category (permissive/copyleft)
- `deprecation_notice`: Deprecation message if applicable
- `health_score`: Individual health score (0-100)

## Health Scoring

The health score is calculated based on:

- **Vulnerabilities**: -30 for critical, -20 for high, -10 for medium, -5 for low
- **Deprecation**: -25 points
- **Outdated Packages**: -15 for major, -8 for minor, -3 for patch updates
- **Package Age**: -10 for 2+ years, -5 for 1+ year without updates

## PyPI Integration

### Caching

- Default cache location: `~/.cache/qontinui-devtools/pypi/`
- Default TTL: 24 hours
- Automatic cache invalidation

### Rate Limiting

- Default: 1 second between requests
- Respects PyPI's rate limits
- Configurable via `rate_limit` parameter

### Cache Management

```python
from qontinui_devtools.dependencies import PyPIClient

client = PyPIClient()

# Clear specific package cache
client.clear_cache("requests")

# Clear all cache
client.clear_cache()

# Get statistics
stats = client.get_statistics()
print(f"Requests made: {stats['requests_made']}")
print(f"Cache entries: {stats['cache_entries']}")
```

## Supported File Formats

### pyproject.toml (Poetry)

```toml
[tool.poetry.dependencies]
python = "^3.9"
requests = "^2.31.0"

[tool.poetry.dev-dependencies]
pytest = "^7.0.0"
```

### pyproject.toml (PEP 621)

```toml
[project]
dependencies = [
    "requests>=2.31.0",
    "flask>=2.0.0",
]

[project.optional-dependencies]
dev = ["pytest>=7.0.0"]
```

### requirements.txt

```
requests==2.31.0
flask>=2.0.0
django~=4.2.0
```

### poetry.lock

Automatically parsed for locked versions.

### setup.py

```python
setup(
    name='myproject',
    install_requires=[
        'requests>=2.31.0',
        'flask>=2.0.0',
    ],
)
```

## License Compatibility

The checker detects potential license conflicts:

- **Permissive**: MIT, BSD, Apache-2.0
- **Copyleft**: GPL, LGPL, AGPL
- **Conflicts**: GPL packages mixed with permissive/proprietary

## Example Output

```
Dependency Health Report
==================================================
Total Dependencies: 15
Overall Health Score: 85.8/100

Status Breakdown:
  Healthy:     0
  Outdated:    11
  Vulnerable:  2
  Deprecated:  0

Total Vulnerabilities: 2
  Critical: 0

🔴 VULNERABLE PACKAGES:
flask 2.0.0
  [HIGH] GHSA-m2qf-hxjv-5gpq: Flask has possible disclosure...

📦 OUTDATED PACKAGES:
🔴 flask      2.0.0 → 3.0.0 (major update, risk: high)
🟡 requests   2.25.0 → 2.31.0 (minor update, risk: medium)

💡 RECOMMENDATIONS:
1. URGENT: Fix 2 package(s) with critical vulnerabilities
2. Consider upgrading 5 package(s) with major updates available
```

## CI/CD Integration

### GitHub Actions

```yaml
- name: Check Dependency Health
  run: |
    python -c "
    from qontinui_devtools.dependencies import DependencyHealthChecker
    checker = DependencyHealthChecker()
    report = checker.check_health('.', fail_on_vulnerable=True)
    print(f'Health Score: {report.overall_health_score:.1f}/100')
    "
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: dependency-health
      name: Check Dependency Health
      entry: python -m qontinui_devtools.dependencies
      language: system
      pass_filenames: false
```

## API Reference

### DependencyHealthChecker

```python
DependencyHealthChecker(
    pypi_client: PyPIClient | None = None,
    offline_mode: bool = False,
    check_vulnerabilities: bool = True,
    cache_dir: Path | None = None,
)
```

**Methods:**

- `check_health(project_path, fail_on_vulnerable=False, include_dev=True)`: Run health check
- `_parse_dependencies(project_path, include_dev)`: Parse dependency files
- `_analyze_dependency(name, version, is_dev)`: Analyze single dependency
- `_detect_circular_dependencies(dependencies)`: Find circular dependencies
- `_check_license_conflicts(dependencies)`: Check license compatibility

### PyPIClient

```python
PyPIClient(
    cache_dir: Path | None = None,
    cache_ttl: timedelta | None = None,
    rate_limit: float | None = None,
    offline_mode: bool = False,
    timeout: int = 10,
)
```

**Methods:**

- `get_package_info(package_name)`: Fetch package information
- `get_latest_version(package_name)`: Get latest version
- `get_all_versions(package_name)`: Get all versions
- `clear_cache(package_name)`: Clear cache
- `get_statistics()`: Get client statistics

## Testing

```bash
pytest python/tests/dependencies/ -v
```

62 comprehensive tests covering:
- PyPI client functionality
- Dependency parsing (all formats)
- Version comparison
- Vulnerability detection
- Health scoring
- License compatibility
- Circular dependency detection

## Performance

- **Caching**: 24-hour cache reduces API calls
- **Rate Limiting**: Respects PyPI limits (1 req/sec default)
- **Offline Mode**: Works without internet
- **Parallel Processing**: Future enhancement for large projects

## Limitations

- Vulnerability database requires updates (use OSV API in production)
- PyPI API doesn't provide download counts in JSON API
- GPL license detection is conservative
- Circular dependency detection may have false positives

## Future Enhancements

1. Integration with OSV (Open Source Vulnerabilities) API
2. GitHub Security Advisory integration
3. Automated pull request creation for updates
4. Dependency tree visualization
5. Historical health tracking
6. Email/Slack notifications
7. Custom vulnerability rules
8. Package quality metrics (test coverage, CI status)

## Contributing

See main project documentation for contribution guidelines.

## License

MIT License - See main project LICENSE file.
