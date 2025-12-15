"""
Config validator for Qontinui configuration files.

This tool validates config files against Pydantic schemas BEFORE execution,
catching schema mismatches early in development.
"""

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError as PydanticValidationError


@dataclass
class ValidationError:
    """Single validation error."""

    workflow_id: str
    workflow_name: str
    field: str
    error_type: str
    message: str
    current_value: Any
    expected_type: str
    location: list[str]
    is_inline: bool = False
    parent_action_id: str | None = None
    inline_workflow_context: str | None = None


@dataclass
class ValidationReport:
    """Complete validation report."""

    config_path: Path
    is_valid: bool
    total_workflows: int
    valid_workflows: int
    invalid_workflows: int
    errors: list[ValidationError]
    warnings: list[str]
    total_inline_workflows: int = 0
    valid_inline_workflows: int = 0
    invalid_inline_workflows: int = 0
    inline_workflow_errors: list[ValidationError] = None

    def __post_init__(self):
        """Initialize inline workflow errors list if None."""
        if self.inline_workflow_errors is None:
            self.inline_workflow_errors = []

    def print_report(self, verbose: bool = False) -> None:
        """Print formatted validation report."""
        print(f"\n{'=' * 80}")
        print(f"Config Validation Report: {self.config_path.name}")
        print(f"{'=' * 80}\n")

        if self.is_valid:
            summary_parts = [f"All {self.total_workflows} workflows are valid"]
            if self.total_inline_workflows > 0:
                summary_parts.append(f"{self.total_inline_workflows} inline workflows are valid")
            print(f"✅ PASSED - {', '.join(summary_parts)}\n")
            return

        print(f"❌ FAILED - {self.invalid_workflows}/{self.total_workflows} workflows have errors")
        if self.total_inline_workflows > 0:
            print(
                f"           {self.invalid_inline_workflows}/{self.total_inline_workflows} inline workflows have errors"
            )
        print()

        # Group errors by workflow
        errors_by_workflow: dict[str, list[ValidationError]] = {}
        for error in self.errors:
            if error.workflow_id not in errors_by_workflow:
                errors_by_workflow[error.workflow_id] = []
            errors_by_workflow[error.workflow_id].append(error)

        # Print each workflow's errors
        for workflow_id, workflow_errors in errors_by_workflow.items():
            workflow_name = workflow_errors[0].workflow_name
            print(f"📝 Workflow: {workflow_name}")
            print(f"   ID: {workflow_id}")
            print(f"   Errors: {len(workflow_errors)}\n")

            for error in workflow_errors:
                print(f"   ❌ {error.field}")
                print(f"      Type: {error.error_type}")
                print(f"      Message: {error.message}")
                if verbose:
                    print(f"      Expected: {error.expected_type}")
                    print(f"      Got: {type(error.current_value).__name__}")
                    print(f"      Location: {' -> '.join(error.location)}")
                print()

        # Print migration hints
        print(f"{'=' * 80}")
        print("💡 How to Fix:")
        print(f"{'=' * 80}\n")

        if any("connections" in e.field for e in self.errors):
            print("Schema Mismatch Detected:")
            print("  The 'connections' field format has changed.")
            print()
            print("  Old format (from qontinui-web v1.x):")
            print('    "connections": {')
            print('      "action1": ["action2:false"]')
            print("    }")
            print()
            print("  New format (qontinui library v2.0):")
            print('    "connections": {')
            print('      "action1": {')
            print('        "false": [[{"action": "action2", "type": "false", "index": 0}]]')
            print("      }")
            print("    }")
            print()
            print("  Solutions:")
            print("  1. Re-export config from updated qontinui-web (RECOMMENDED)")
            print("  2. Update qontinui-web to export in new format")
            print("  3. Wait for auto-migration support (if added)")
            print()

        # Print inline workflow errors
        if self.inline_workflow_errors:
            print(f"{'=' * 80}")
            print("📦 Inline Workflow Errors:")
            print(f"{'=' * 80}\n")

            # Group inline workflow errors by parent context
            inline_errors_by_context: dict[str, list[ValidationError]] = {}
            for error in self.inline_workflow_errors:
                context = error.inline_workflow_context or "unknown"
                if context not in inline_errors_by_context:
                    inline_errors_by_context[context] = []
                inline_errors_by_context[context].append(error)

            # Print each inline workflow's errors
            for context, context_errors in inline_errors_by_context.items():
                workflow_name = context_errors[0].workflow_name
                parent_action = context_errors[0].parent_action_id
                print(f"📝 Inline Workflow in: {workflow_name}")
                print(f"   Parent Action: {parent_action}")
                print(f"   Context: {context}")
                print(f"   Errors: {len(context_errors)}\n")

                for error in context_errors:
                    print(f"   ❌ {error.field}")
                    print(f"      Type: {error.error_type}")
                    print(f"      Message: {error.message}")
                    if verbose:
                        print(f"      Expected: {error.expected_type}")
                        print(f"      Got: {type(error.current_value).__name__}")
                        print(f"      Location: {' -> '.join(error.location)}")
                    print()

        # Print warnings
        if self.warnings:
            print(f"{'=' * 80}")
            print(f"⚠️  Warnings ({len(self.warnings)}):")
            print(f"{'=' * 80}\n")
            for warning in self.warnings:
                print(f"  • {warning}")
            print()


class ConfigValidator:
    """
    Validates Qontinui config files against Pydantic schemas.

    This tool loads config files and validates them using the same Pydantic
    models that the qontinui library uses at runtime. It catches schema
    mismatches BEFORE execution, saving debugging time.

    Example:
        >>> validator = ConfigValidator()
        >>> report = validator.validate_file("config.json")
        >>> if not report.is_valid:
        ...     report.print_report(verbose=True)
        ...     sys.exit(1)
    """

    def __init__(self, qontinui_path: Path | None = None):
        """
        Initialize validator.

        Args:
            qontinui_path: Path to qontinui library (default: auto-detect)
        """
        self.qontinui_path = qontinui_path or self._find_qontinui_path()
        self._setup_imports()

    def _find_qontinui_path(self) -> Path:
        """Auto-detect qontinui library path."""
        # Try common locations
        candidates = [
            Path.cwd() / "qontinui" / "src",
            Path.cwd().parent / "qontinui" / "src",
            Path.cwd().parent.parent / "qontinui" / "src",
        ]

        for path in candidates:
            if (path / "qontinui" / "config" / "schema.py").exists():
                return path

        raise FileNotFoundError(
            "Could not find qontinui library. " "Please specify qontinui_path parameter."
        )

    def _setup_imports(self) -> None:
        """Setup Python path and import Pydantic models."""
        if str(self.qontinui_path) not in sys.path:
            sys.path.insert(0, str(self.qontinui_path))

        # Import Pydantic models
        try:
            from qontinui.config.schema import Workflow
            from qontinui.json_executor.config_parser import ConfigParser

            self.Workflow = Workflow
            self.ConfigParser = ConfigParser
        except ImportError as e:
            raise ImportError(f"Failed to import qontinui models from {self.qontinui_path}: {e}") from e

    def validate_file(self, config_path: str | Path) -> ValidationReport:
        """
        Validate a config file.

        Args:
            config_path: Path to config JSON file

        Returns:
            ValidationReport with detailed errors

        Example:
            >>> report = validator.validate_file("bdo_config.json")
            >>> print(f"Valid: {report.is_valid}")
            >>> print(f"Errors: {len(report.errors)}")
        """
        config_path = Path(config_path)

        if not config_path.exists():
            return ValidationReport(
                config_path=config_path,
                is_valid=False,
                total_workflows=0,
                valid_workflows=0,
                invalid_workflows=0,
                errors=[],
                warnings=[f"Config file not found: {config_path}"],
            )

        # Load JSON
        try:
            with open(config_path, encoding="utf-8") as f:
                config_data = json.load(f)
        except json.JSONDecodeError as e:
            return ValidationReport(
                config_path=config_path,
                is_valid=False,
                total_workflows=0,
                valid_workflows=0,
                invalid_workflows=0,
                errors=[],
                warnings=[f"Invalid JSON: {e}"],
            )

        # Validate workflows
        workflows = config_data.get("workflows", [])
        errors: list[ValidationError] = []
        warnings: list[str] = []
        valid_count = 0

        for workflow in workflows:
            workflow_id = workflow.get("id", "unknown")
            workflow_name = workflow.get("name", "unknown")

            try:
                # Attempt to parse workflow with Pydantic
                self.Workflow.model_validate(workflow)
                valid_count += 1
            except PydanticValidationError as e:
                # Parse Pydantic errors
                for error in e.errors():
                    field_location = [str(loc) for loc in error["loc"]]
                    field_name = ".".join(field_location)

                    # Get current value at error location
                    current_value = self._get_nested_value(workflow, error["loc"])

                    errors.append(
                        ValidationError(
                            workflow_id=workflow_id,
                            workflow_name=workflow_name,
                            field=field_name,
                            error_type=error["type"],
                            message=error["msg"],
                            current_value=current_value,
                            expected_type=error.get("expected", "unknown"),
                            location=field_location,
                        )
                    )

        # Validate inline workflows (from action configs and transitions)
        inline_workflows = self._find_inline_workflows(workflows)

        # Also check transitions for inline workflows
        transitions = config_data.get("transitions", [])
        for transition in transitions:
            transition_id = transition.get("id", "unknown")
            inline_wfs = transition.get("inlineWorkflows", [])
            for inline_wf in inline_wfs:
                if isinstance(inline_wf, dict) and "actions" in inline_wf:
                    inline_workflows.append(
                        (
                            transition_id,  # parent ID (transition)
                            f"Transition: {transition_id}",  # parent name
                            transition_id,  # action ID (same as transition for transitions)
                            inline_wf,
                        )
                    )

        inline_errors: list[ValidationError] = []
        inline_valid_count = 0

        for (
            parent_workflow_id,
            parent_workflow_name,
            action_id,
            inline_workflow,
        ) in inline_workflows:
            try:
                # Attempt to parse inline workflow with Pydantic
                self.Workflow.model_validate(inline_workflow)
                inline_valid_count += 1
            except PydanticValidationError as e:
                # Parse Pydantic errors for inline workflow
                for error in e.errors():
                    field_location = [str(loc) for loc in error["loc"]]
                    field_name = ".".join(field_location)

                    # Get current value at error location
                    current_value = self._get_nested_value(inline_workflow, error["loc"])

                    inline_errors.append(
                        ValidationError(
                            workflow_id=parent_workflow_id,
                            workflow_name=parent_workflow_name,
                            field=field_name,
                            error_type=error["type"],
                            message=error["msg"],
                            current_value=current_value,
                            expected_type=error.get("expected", "unknown"),
                            location=field_location,
                            is_inline=True,
                            parent_action_id=action_id,
                            inline_workflow_context=f"Inline workflow in action '{action_id}'",
                        )
                    )

        is_valid = len(errors) == 0 and len(inline_errors) == 0

        return ValidationReport(
            config_path=config_path,
            is_valid=is_valid,
            total_workflows=len(workflows),
            valid_workflows=valid_count,
            invalid_workflows=len(workflows) - valid_count,
            errors=errors,
            warnings=warnings,
            total_inline_workflows=len(inline_workflows),
            valid_inline_workflows=inline_valid_count,
            invalid_inline_workflows=len(inline_workflows) - inline_valid_count,
            inline_workflow_errors=inline_errors,
        )

    def _get_nested_value(self, data: dict[str, Any], location: tuple[Any, ...]) -> Any:
        """Get value at nested location in dict."""
        current = data
        for key in location:
            if isinstance(current, dict):
                current = current.get(key, None)
            elif isinstance(current, list) and isinstance(key, int):
                current = current[key] if key < len(current) else None
            else:
                return None
        return current

    def _find_inline_workflows(self, workflows: list[dict]) -> list[tuple[str, str, str, dict]]:
        """Find inline workflows embedded in action configs.

        Args:
            workflows: List of workflow dictionaries

        Returns:
            List of (parent_workflow_id, parent_workflow_name, action_id, inline_workflow_dict)
        """
        inline_workflows = []

        for workflow in workflows:
            workflow_id = workflow.get("id", "unknown")
            workflow_name = workflow.get("name", "unknown")

            for action in workflow.get("actions", []):
                # Skip if action is not a dict (malformed config)
                if not isinstance(action, dict):
                    continue

                action_id = action.get("id", "unknown")
                config = action.get("config", {})

                # Check for inline workflows in various action types
                # Pattern 1: RunWorkflow with inline workflow definition
                if "workflow" in config and isinstance(config["workflow"], dict):
                    # If workflow is a dict with workflow structure (not just a workflow_id reference)
                    if "actions" in config["workflow"]:
                        inline_workflows.append(
                            (workflow_id, workflow_name, action_id, config["workflow"])
                        )

                # Pattern 2: IF action with inline workflow in then/else branches
                if action.get("type") == "IF":
                    if "thenWorkflow" in config and isinstance(config["thenWorkflow"], dict):
                        if "actions" in config["thenWorkflow"]:
                            inline_workflows.append(
                                (
                                    workflow_id,
                                    workflow_name,
                                    f"{action_id}.then",
                                    config["thenWorkflow"],
                                )
                            )
                    if "elseWorkflow" in config and isinstance(config["elseWorkflow"], dict):
                        if "actions" in config["elseWorkflow"]:
                            inline_workflows.append(
                                (
                                    workflow_id,
                                    workflow_name,
                                    f"{action_id}.else",
                                    config["elseWorkflow"],
                                )
                            )

                # Pattern 3: LOOP action with inline workflow
                if action.get("type") == "LOOP":
                    if "workflow" in config and isinstance(config["workflow"], dict):
                        if "actions" in config["workflow"]:
                            inline_workflows.append(
                                (
                                    workflow_id,
                                    workflow_name,
                                    f"{action_id}.loop",
                                    config["workflow"],
                                )
                            )

                # Pattern 4: TRY_CATCH action with inline workflows
                if action.get("type") == "TRY_CATCH":
                    if "tryWorkflow" in config and isinstance(config["tryWorkflow"], dict):
                        if "actions" in config["tryWorkflow"]:
                            inline_workflows.append(
                                (
                                    workflow_id,
                                    workflow_name,
                                    f"{action_id}.try",
                                    config["tryWorkflow"],
                                )
                            )
                    if "catchWorkflow" in config and isinstance(config["catchWorkflow"], dict):
                        if "actions" in config["catchWorkflow"]:
                            inline_workflows.append(
                                (
                                    workflow_id,
                                    workflow_name,
                                    f"{action_id}.catch",
                                    config["catchWorkflow"],
                                )
                            )
                    if "finallyWorkflow" in config and isinstance(config["finallyWorkflow"], dict):
                        if "actions" in config["finallyWorkflow"]:
                            inline_workflows.append(
                                (
                                    workflow_id,
                                    workflow_name,
                                    f"{action_id}.finally",
                                    config["finallyWorkflow"],
                                )
                            )

                # Pattern 5: SWITCH action with inline workflows in cases
                if action.get("type") == "SWITCH":
                    cases = config.get("cases", [])
                    for idx, case in enumerate(cases):
                        if "workflow" in case and isinstance(case["workflow"], dict):
                            if "actions" in case["workflow"]:
                                inline_workflows.append(
                                    (
                                        workflow_id,
                                        workflow_name,
                                        f"{action_id}.case[{idx}]",
                                        case["workflow"],
                                    )
                                )
                    if "defaultWorkflow" in config and isinstance(config["defaultWorkflow"], dict):
                        if "actions" in config["defaultWorkflow"]:
                            inline_workflows.append(
                                (
                                    workflow_id,
                                    workflow_name,
                                    f"{action_id}.default",
                                    config["defaultWorkflow"],
                                )
                            )

        return inline_workflows
