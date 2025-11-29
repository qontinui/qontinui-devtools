"""
Example demonstrating inline workflow validation.

This script shows how the ConfigValidator detects and validates inline workflows
embedded within action configurations.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

from qontinui_devtools.config_validator import ConfigValidator


def create_test_config_with_inline_workflow():
    """Create a test config with an inline workflow that has schema errors."""
    return {
        "workflows": [
            {
                "id": "main_workflow",
                "name": "Main Workflow",
                "version": "1.0.0",
                "format": "graph",
                "actions": [
                    {
                        "id": "if_action_1",
                        "type": "IF",
                        "config": {
                            "condition": {
                                "type": "variable",
                                "variableName": "test_var",
                                "operator": "==",
                                "expectedValue": True,
                            },
                            "thenActions": ["action_2"],
                            "elseActions": ["action_3"],
                            # Inline workflow with schema error (missing required fields)
                            "thenWorkflow": {
                                "id": "inline_then",
                                "name": "Inline Then Workflow",
                                "version": "1.0.0",
                                # Missing "format" field (required)
                                "actions": [
                                    {
                                        "id": "inline_action_1",
                                        "type": "CLICK",
                                        "config": {
                                            "target": {"type": "coordinates", "x": 100, "y": 200}
                                        },
                                    }
                                ],
                                # Missing "connections" field (required)
                            },
                        },
                    }
                ],
                "connections": {
                    "if_action_1": {
                        "true": [[{"action": "action_2", "type": "true", "index": 0}]],
                        "false": [[{"action": "action_3", "type": "false", "index": 0}]],
                    }
                },
            }
        ]
    }


def main():
    """Test inline workflow validation."""
    print("=" * 80)
    print("Testing Inline Workflow Validation")
    print("=" * 80)
    print()

    # Create test config
    config = create_test_config_with_inline_workflow()

    # Write to temporary file
    test_file = Path("/tmp/test_inline_workflow_config.json")
    with open(test_file, "w") as f:
        json.dump(config, f, indent=2)

    print(f"Created test config: {test_file}")
    print()

    # Validate
    try:
        validator = ConfigValidator()
        report = validator.validate_file(test_file)

        # Print report
        report.print_report(verbose=True)

        # Summary
        print("\n" + "=" * 80)
        print("Summary:")
        print("=" * 80)
        print(f"Main workflows: {report.total_workflows}")
        print(f"Inline workflows detected: {report.total_inline_workflows}")
        print(f"Valid inline workflows: {report.valid_inline_workflows}")
        print(f"Invalid inline workflows: {report.invalid_inline_workflows}")
        print(f"Total errors: {len(report.errors) + len(report.inline_workflow_errors)}")
        print()

        if report.is_valid:
            print("✅ All workflows (including inline) are valid!")
        else:
            print("❌ Validation failed - errors detected in workflows")
            if report.inline_workflow_errors:
                print(f"   - {len(report.inline_workflow_errors)} errors in inline workflows")

    except Exception as e:
        print(f"❌ Error during validation: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
