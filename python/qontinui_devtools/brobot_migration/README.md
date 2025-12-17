# Brobot Migration Tool

## Overview

This module provides a comprehensive suite of tools for migrating Java unit and integration tests from the Brobot library to equivalent Python tests in the Qontinui project.

## Migration from qontinui Core Library

**Status:** Migrated from `qontinui.test_migration` to `qontinui_devtools.brobot_migration` (Phase 2: Core Library Cleanup)

This migration tool was originally part of the qontinui core library but has been moved to qontinui-devtools since it's a one-time migration utility for users transitioning from Brobot, not core automation functionality.

## Features

- **Test Discovery**: Scan Java test files and classify them by type
- **Code Translation**: Convert Java test code to Python using hybrid LLM + rule-based approach
- **Mock Generation**: Automatically generate Qontinui mocks for Brobot APIs
- **Validation**: Verify translated tests match original behavior
- **Coverage Analysis**: Track migration progress and test coverage
- **Reporting**: Generate detailed migration reports

## Usage

### Command Line Interface

```bash
# Discover tests
python -m qontinui_devtools.brobot_migration.cli discover /path/to/brobot/tests

# Migrate tests
python -m qontinui_devtools.brobot_migration.cli migrate /path/to/brobot/tests --output /path/to/qontinui/tests

# Validate migration
python -m qontinui_devtools.brobot_migration.cli validate /path/to/qontinui/tests

# Generate report
python -m qontinui_devtools.brobot_migration.cli report /path/to/qontinui/tests --output migration-report.html
```

### Programmatic API

```python
from qontinui_devtools.brobot_migration import TestMigrationCLI

cli = TestMigrationCLI()
cli.run_migration(
    source_dir="/path/to/brobot/tests",
    output_dir="/path/to/qontinui/tests"
)
```

## Architecture

```
brobot_migration/
├── cli.py                    # Command-line interface
├── orchestrator.py           # Main migration orchestrator
├── discovery/                # Test discovery and classification
│   ├── scanner.py
│   └── classifier.py
├── translation/              # Code translation engines
│   ├── llm_test_translator.py
│   ├── hybrid_test_translator.py
│   └── assertion_converter.py
├── mocks/                    # Mock generation
│   ├── brobot_mock_analyzer.py
│   └── qontinui_mock_generator.py
├── validation/               # Test validation
│   ├── behavior_comparator.py
│   └── coverage_tracker.py
└── reporting/                # Report generation
    └── dashboard.py
```

## Configuration

Create a `migration_config.json`:

```json
{
  "source_directory": "/path/to/brobot/tests",
  "output_directory": "/path/to/qontinui/tests",
  "llm_provider": "openai",
  "parallel_workers": 4,
  "validation_enabled": true
}
```

## Dependencies

- qontinui (core library)
- transformers (for LLM-based translation)
- pytest (for running migrated tests)

## Known Limitations

- Complex Java generics may require manual review
- Some Brobot-specific patterns may not have direct Qontinui equivalents
- Integration tests with external dependencies need manual configuration

## Support

This is a one-time migration tool. For issues, please refer to:
- Qontinui documentation: https://qontinui.github.io
- GitHub issues: https://github.com/qontinui/qontinui-devtools/issues
