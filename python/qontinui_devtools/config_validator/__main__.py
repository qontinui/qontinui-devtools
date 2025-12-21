"""CLI entry point for config validator.

from typing import Any, Any

Usage:
    python -m qontinui_devtools.config_validator [OPTIONS] <config_file.json> [<config_file2.json> ...]

Examples:
    # Validate a single config file
    python -m qontinui_devtools.config_validator config.json

    # Validate with verbose output
    python -m qontinui_devtools.config_validator --verbose config.json

    # Validate multiple files
    python -m qontinui_devtools.config_validator config1.json config2.json

    # Use custom qontinui library path
    python -m qontinui_devtools.config_validator --qontinui-path ../qontinui/src config.json
"""

import argparse
import sys
from pathlib import Path
from typing import Any

from .validator import ConfigValidator


def main() -> int:
    """Validate config files passed as arguments."""
    parser = argparse.ArgumentParser(
        description="Validate Qontinui config files against Pydantic schemas.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m qontinui_devtools.config_validator config.json
  python -m qontinui_devtools.config_validator --verbose config.json
  python -m qontinui_devtools.config_validator config1.json config2.json
  python -m qontinui_devtools.config_validator --qontinui-path ../qontinui/src config.json

Exit codes:
  0    All config files are valid
  1    One or more config files have validation errors
        """,
    )

    parser.add_argument(
        "config_files",
        nargs="+",
        metavar="CONFIG_FILE",
        help="One or more JSON config files to validate",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed error information including expected types and locations",
    )

    parser.add_argument(
        "--qontinui-path",
        type=Path,
        metavar="PATH",
        help="Path to qontinui library (default: auto-detect)",
    )

    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()

    all_valid = True
    results: list[Any] = []

    for config_file in args.config_files:
        config_path = Path(config_file)

        try:
            validator = ConfigValidator(qontinui_path=args.qontinui_path)
            report = validator.validate_file(config_path)

            if args.json:
                # Collect results for JSON output
                results.append(
                    {
                        "config_path": str(config_path),
                        "is_valid": report.is_valid,
                        "total_workflows": report.total_workflows,
                        "valid_workflows": report.valid_workflows,
                        "invalid_workflows": report.invalid_workflows,
                        "total_inline_workflows": report.total_inline_workflows,
                        "valid_inline_workflows": report.valid_inline_workflows,
                        "invalid_inline_workflows": report.invalid_inline_workflows,
                        "error_count": len(report.errors)
                        + len(report.inline_workflow_errors or []),
                        "warning_count": len(report.warnings),
                    }
                )
            else:
                # Print human-readable report
                report.print_report(verbose=args.verbose)

            if not report.is_valid:
                all_valid = False

        except Exception as e:
            if args.json:
                results.append(
                    {
                        "config_path": str(config_path),
                        "is_valid": False,
                        "error": str(e),
                    }
                )
            else:
                print(f"\n❌ Error validating {config_file}: {e}\n")
            all_valid = False

    if args.json:
        import json

        print(
            json.dumps(
                {
                    "all_valid": all_valid,
                    "total_files": len(args.config_files),
                    "valid_files": sum(1 for r in results if r.get("is_valid", False)),
                    "invalid_files": sum(1 for r in results if not r.get("is_valid", False)),
                    "results": results,
                },
                indent=2,
            )
        )

    return 0 if all_valid else 1


if __name__ == "__main__":
    sys.exit(main())
