"""
Integration tests for ConfigValidator.

Tests the config validator's ability to validate Qontinui config files
against Pydantic schemas, catching schema mismatches before execution.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from qontinui_devtools.config_validator import ConfigValidator, ValidationError, ValidationReport


@pytest.fixture
def fixtures_dir() -> Path:
    """Return path to test fixtures directory."""
    return Path(__file__).parent.parent / "fixtures" / "config_validator"


@pytest.fixture
def valid_config_file(tmp_path: Path) -> Path:
    """Create a valid config file for testing."""
    config = {
        "name": "Test Valid Config",
        "default_workflow": "test_workflow",
        "workflows": [
            {
                "id": "test_workflow",
                "name": "Test Workflow",
                "actions": {
                    "action1": {
                        "type": "Click",
                        "name": "Click Button",
                        "searches": [{"type": "Match", "image": "button.png", "threshold": 0.8}],
                        "coordinates": {"x": 100, "y": 200},
                    },
                    "action2": {"type": "Wait", "name": "Wait for Element", "duration": 1.5},
                },
                "connections": {
                    "action1": {"false": [[{"action": "action2", "type": "false", "index": 0}]]}
                },
                "initial_action": "action1",
            }
        ],
    }

    config_file = tmp_path / "valid_config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    return config_file


@pytest.fixture
def invalid_connections_file(tmp_path: Path) -> Path:
    """Create a config with invalid connections format (old format)."""
    config = {
        "name": "Invalid Connections Format",
        "default_workflow": "test_workflow",
        "workflows": [
            {
                "id": "test_workflow",
                "name": "Test Workflow with Old Format",
                "actions": {
                    "action1": {
                        "type": "Click",
                        "name": "Click Button",
                        "searches": [{"type": "Match", "image": "button.png", "threshold": 0.8}],
                    },
                    "action2": {"type": "Wait", "name": "Wait for Element", "duration": 1.5},
                },
                "connections": {"action1": ["action2:false"]},
                "initial_action": "action1",
            }
        ],
    }

    config_file = tmp_path / "invalid_connections.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    return config_file


@pytest.fixture
def missing_required_fields_file(tmp_path: Path) -> Path:
    """Create a config with missing required fields."""
    config = {
        "name": "Missing Required Fields",
        "default_workflow": "test_workflow",
        "workflows": [
            {
                "id": "test_workflow",
                "name": "Incomplete Workflow",
                "actions": {
                    "action1": {
                        "name": "Click Button",
                        "searches": [{"type": "Match", "image": "button.png"}],
                    }
                },
                "connections": {},
                "initial_action": "action1",
            }
        ],
    }

    config_file = tmp_path / "missing_fields.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    return config_file


@pytest.fixture
def invalid_json_file(tmp_path: Path) -> Path:
    """Create a file with invalid JSON syntax."""
    config_file = tmp_path / "invalid_json.json"
    with open(config_file, "w", encoding="utf-8") as f:
        f.write('{"name": "Invalid", "workflows": [}')

    return config_file


@pytest.fixture
def multiple_workflows_file(tmp_path: Path) -> Path:
    """Create a config with multiple workflows (some valid, some invalid)."""
    config = {
        "name": "Multiple Workflows Config",
        "default_workflow": "workflow1",
        "workflows": [
            {
                "id": "workflow1",
                "name": "Valid Workflow",
                "actions": {
                    "action1": {
                        "type": "Click",
                        "name": "Click Button",
                        "searches": [{"type": "Match", "image": "button.png", "threshold": 0.8}],
                    }
                },
                "connections": {},
                "initial_action": "action1",
            },
            {
                "id": "workflow2",
                "name": "Invalid Workflow",
                "actions": {"action2": {"name": "Missing Type", "searches": []}},
                "connections": {},
                "initial_action": "action2",
            },
        ],
    }

    config_file = tmp_path / "multiple_workflows.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    return config_file


@pytest.fixture
def mock_validator():
    """Create a mock validator that doesn't require qontinui library."""
    with (
        patch.object(ConfigValidator, "_find_qontinui_path") as mock_find,
        patch.object(ConfigValidator, "_setup_imports") as mock_setup,
    ):

        mock_find.return_value = Path("/mock/qontinui/path")

        validator = ConfigValidator()

        # Mock the Workflow class and its validation
        mock_workflow = MagicMock()
        validator.Workflow = mock_workflow

        # Mock _find_inline_workflows to return empty list
        validator._find_inline_workflows = MagicMock(return_value=[])

        yield validator


class TestConfigValidatorInitialization:
    """Tests for ConfigValidator initialization and setup."""

    def test_init_with_explicit_path(self) -> None:
        """Test initialization with explicit qontinui path."""
        test_path = Path("/test/qontinui/path")

        with patch.object(ConfigValidator, "_setup_imports"):
            validator = ConfigValidator(qontinui_path=test_path)
            assert validator.qontinui_path == test_path

    def test_init_auto_detect_path(self) -> None:
        """Test initialization with auto-detection of qontinui path."""
        with (
            patch.object(ConfigValidator, "_find_qontinui_path") as mock_find,
            patch.object(ConfigValidator, "_setup_imports"),
        ):

            mock_find.return_value = Path("/auto/detected/path")
            validator = ConfigValidator()

            assert validator.qontinui_path == Path("/auto/detected/path")
            mock_find.assert_called_once()

    def test_auto_detect_qontinui_path_success(self) -> None:
        """Test successful auto-detection of qontinui path."""
        with (
            patch.object(ConfigValidator, "_setup_imports"),
            patch("pathlib.Path.exists") as mock_exists,
        ):

            # Mock that the second candidate path exists
            mock_exists.side_effect = [False, True]

            validator = ConfigValidator()

            # Should find a valid path
            assert validator.qontinui_path is not None

    def test_auto_detect_qontinui_path_failure(self) -> None:
        """Test auto-detection failure when qontinui not found."""
        with (
            patch.object(ConfigValidator, "_setup_imports"),
            patch("pathlib.Path.exists", return_value=False),
        ):

            with pytest.raises(FileNotFoundError, match="Could not find qontinui library"):
                ConfigValidator()

    def test_setup_imports_adds_to_sys_path(self) -> None:
        """Test that _setup_imports adds qontinui path to sys.path."""
        import sys

        test_path = Path("/test/qontinui/src")
        original_path = sys.path.copy()

        try:
            with patch.object(ConfigValidator, "_find_qontinui_path", return_value=test_path):
                # Mock the actual imports to avoid ImportError
                with patch("builtins.__import__"):
                    validator = ConfigValidator()

                    # Should have added test_path to sys.path
                    assert str(test_path) in sys.path
        finally:
            # Restore original sys.path
            sys.path = original_path


class TestValidateValidConfig:
    """Tests for validating valid configuration files."""

    def test_validate_valid_config(
        self, valid_config_file: Path, mock_validator: ConfigValidator
    ) -> None:
        """Test validation of a completely valid config file."""
        # Mock successful validation
        mock_validator.Workflow.model_validate.return_value = MagicMock()

        report = mock_validator.validate_file(valid_config_file)

        assert isinstance(report, ValidationReport)
        assert report.is_valid is True
        assert report.total_workflows == 1
        assert report.valid_workflows == 1
        assert report.invalid_workflows == 0
        assert len(report.errors) == 0
        assert report.config_path == valid_config_file

    def test_validate_multiple_valid_workflows(
        self, tmp_path: Path, mock_validator: ConfigValidator
    ) -> None:
        """Test validation of config with multiple valid workflows."""
        config = {
            "name": "Multi Workflow",
            "default_workflow": "workflow1",
            "workflows": [
                {
                    "id": f"workflow{i}",
                    "name": f"Workflow {i}",
                    "actions": {},
                    "connections": {},
                    "initial_action": "action1",
                }
                for i in range(5)
            ],
        }

        config_file = tmp_path / "multi_valid.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f)

        # Mock successful validation for all workflows
        mock_validator.Workflow.model_validate.return_value = MagicMock()

        report = mock_validator.validate_file(config_file)

        assert report.is_valid is True
        assert report.total_workflows == 5
        assert report.valid_workflows == 5
        assert report.invalid_workflows == 0


class TestValidateInvalidConfigs:
    """Tests for detecting invalid configuration files."""

    def test_validate_invalid_connections_format(
        self, invalid_connections_file: Path, mock_validator: ConfigValidator
    ) -> None:
        """Test detection of invalid connections format (schema mismatch)."""
        from pydantic import ValidationError as PydanticValidationError

        # Mock validation error for connections field
        error_dict = {
            "type": "dict_type",
            "loc": ("connections", "action1"),
            "msg": "Input should be a valid dictionary",
            "input": ["action2:false"],
        }

        mock_validator.Workflow.model_validate.side_effect = (
            PydanticValidationError.from_exception_data("ValidationError", [error_dict])
        )

        report = mock_validator.validate_file(invalid_connections_file)

        assert report.is_valid is False
        assert report.invalid_workflows == 1
        assert len(report.errors) > 0

        # Check that error is related to connections
        assert any("connections" in error.field for error in report.errors)

    def test_validate_missing_required_fields(
        self, missing_required_fields_file: Path, mock_validator: ConfigValidator
    ) -> None:
        """Test detection of missing required fields."""
        from pydantic import ValidationError as PydanticValidationError

        # Mock validation error for missing field
        error_dict = {
            "type": "missing",
            "loc": ("actions", "action1", "type"),
            "msg": "Field required",
            "input": {},
        }

        mock_validator.Workflow.model_validate.side_effect = (
            PydanticValidationError.from_exception_data("ValidationError", [error_dict])
        )

        report = mock_validator.validate_file(missing_required_fields_file)

        assert report.is_valid is False
        assert len(report.errors) > 0

        # Check for missing field error
        assert any(error.error_type == "missing" for error in report.errors)

    def test_validate_multiple_workflows_mixed_validity(
        self, multiple_workflows_file: Path, mock_validator: ConfigValidator
    ) -> None:
        """Test validation with some valid and some invalid workflows."""
        from pydantic import ValidationError as PydanticValidationError

        # First workflow valid, second invalid
        call_count = [0]

        def mock_validate(workflow):
            call_count[0] += 1
            if call_count[0] == 1:
                return MagicMock()  # Valid
            else:
                error_dict = {
                    "type": "missing",
                    "loc": ("actions", "action2", "type"),
                    "msg": "Field required",
                    "input": {},
                }
                raise PydanticValidationError.from_exception_data("ValidationError", [error_dict])

        mock_validator.Workflow.model_validate.side_effect = mock_validate

        report = mock_validator.validate_file(multiple_workflows_file)

        assert report.is_valid is False
        assert report.total_workflows == 2
        assert report.valid_workflows == 1
        assert report.invalid_workflows == 1
        assert len(report.errors) > 0


class TestValidateNonexistentFile:
    """Tests for handling nonexistent or inaccessible files."""

    def test_validate_nonexistent_file(self, mock_validator: ConfigValidator) -> None:
        """Test handling of nonexistent config file."""
        nonexistent_path = Path("/nonexistent/config.json")

        report = mock_validator.validate_file(nonexistent_path)

        assert isinstance(report, ValidationReport)
        assert report.is_valid is False
        assert report.total_workflows == 0
        assert len(report.warnings) > 0
        assert "not found" in report.warnings[0].lower()

    def test_validate_invalid_json(
        self, invalid_json_file: Path, mock_validator: ConfigValidator
    ) -> None:
        """Test handling of invalid JSON syntax."""
        report = mock_validator.validate_file(invalid_json_file)

        assert report.is_valid is False
        assert report.total_workflows == 0
        assert len(report.warnings) > 0
        assert "json" in report.warnings[0].lower()

    def test_validate_empty_workflows(
        self, tmp_path: Path, mock_validator: ConfigValidator
    ) -> None:
        """Test handling of config with no workflows."""
        config = {"name": "Empty Config", "default_workflow": "none", "workflows": []}

        config_file = tmp_path / "empty.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f)

        report = mock_validator.validate_file(config_file)

        assert report.is_valid is True
        assert report.total_workflows == 0
        assert report.valid_workflows == 0


class TestValidationReportFormat:
    """Tests for ValidationReport structure and formatting."""

    def test_validation_report_structure(
        self, valid_config_file: Path, mock_validator: ConfigValidator
    ) -> None:
        """Test that ValidationReport has correct structure."""
        mock_validator.Workflow.model_validate.return_value = MagicMock()

        report = mock_validator.validate_file(valid_config_file)

        # Check all required fields exist
        assert hasattr(report, "config_path")
        assert hasattr(report, "is_valid")
        assert hasattr(report, "total_workflows")
        assert hasattr(report, "valid_workflows")
        assert hasattr(report, "invalid_workflows")
        assert hasattr(report, "errors")
        assert hasattr(report, "warnings")

        # Check types
        assert isinstance(report.config_path, Path)
        assert isinstance(report.is_valid, bool)
        assert isinstance(report.total_workflows, int)
        assert isinstance(report.valid_workflows, int)
        assert isinstance(report.invalid_workflows, int)
        assert isinstance(report.errors, list)
        assert isinstance(report.warnings, list)

    def test_validation_error_structure(
        self, invalid_connections_file: Path, mock_validator: ConfigValidator
    ) -> None:
        """Test that ValidationError has correct structure."""
        from pydantic import ValidationError as PydanticValidationError

        error_dict = {
            "type": "dict_type",
            "loc": ("connections", "action1"),
            "msg": "Invalid type",
            "input": ["wrong"],
        }

        mock_validator.Workflow.model_validate.side_effect = (
            PydanticValidationError.from_exception_data("ValidationError", [error_dict])
        )

        report = mock_validator.validate_file(invalid_connections_file)

        assert len(report.errors) > 0

        error = report.errors[0]
        assert isinstance(error, ValidationError)
        assert hasattr(error, "workflow_id")
        assert hasattr(error, "workflow_name")
        assert hasattr(error, "field")
        assert hasattr(error, "error_type")
        assert hasattr(error, "message")
        assert hasattr(error, "current_value")
        assert hasattr(error, "expected_type")
        assert hasattr(error, "location")
        assert hasattr(error, "is_inline")
        assert hasattr(error, "parent_action_id")
        assert hasattr(error, "inline_workflow_context")

        assert isinstance(error.location, list)
        assert error.workflow_id == "test_workflow"

    def test_print_report_valid_config(
        self, valid_config_file: Path, mock_validator: ConfigValidator, capsys
    ) -> None:
        """Test print_report output for valid config."""
        mock_validator.Workflow.model_validate.return_value = MagicMock()

        report = mock_validator.validate_file(valid_config_file)
        report.print_report()

        captured = capsys.readouterr()
        assert "PASSED" in captured.out
        assert str(report.total_workflows) in captured.out

    def test_print_report_invalid_config(
        self, invalid_connections_file: Path, mock_validator: ConfigValidator, capsys
    ) -> None:
        """Test print_report output for invalid config."""
        from pydantic import ValidationError as PydanticValidationError

        error_dict = {
            "type": "dict_type",
            "loc": ("connections", "action1"),
            "msg": "Invalid connections format",
            "input": ["wrong"],
        }

        mock_validator.Workflow.model_validate.side_effect = (
            PydanticValidationError.from_exception_data("ValidationError", [error_dict])
        )

        report = mock_validator.validate_file(invalid_connections_file)
        report.print_report()

        captured = capsys.readouterr()
        assert "FAILED" in captured.out
        assert "connections" in captured.out.lower()

    def test_print_report_verbose_mode(
        self, invalid_connections_file: Path, mock_validator: ConfigValidator, capsys
    ) -> None:
        """Test print_report verbose output includes detailed info."""
        from pydantic import ValidationError as PydanticValidationError

        error_dict = {
            "type": "dict_type",
            "loc": ("connections", "action1"),
            "msg": "Invalid type",
            "input": ["wrong"],
            "expected": "dict",
        }

        mock_validator.Workflow.model_validate.side_effect = (
            PydanticValidationError.from_exception_data("ValidationError", [error_dict])
        )

        report = mock_validator.validate_file(invalid_connections_file)
        report.print_report(verbose=True)

        captured = capsys.readouterr()
        assert "Expected:" in captured.out
        assert "Got:" in captured.out
        assert "Location:" in captured.out


class TestGetNestedValue:
    """Tests for _get_nested_value helper method."""

    def test_get_nested_value_dict(self, mock_validator: ConfigValidator) -> None:
        """Test getting nested value from dict."""
        data = {"level1": {"level2": {"level3": "value"}}}

        value = mock_validator._get_nested_value(data, ("level1", "level2", "level3"))
        assert value == "value"

    def test_get_nested_value_list(self, mock_validator: ConfigValidator) -> None:
        """Test getting nested value with list index."""
        data = {"items": [{"name": "item1"}, {"name": "item2"}]}

        value = mock_validator._get_nested_value(data, ("items", 1, "name"))
        assert value == "item2"

    def test_get_nested_value_missing_key(self, mock_validator: ConfigValidator) -> None:
        """Test getting nested value with missing key."""
        data = {"level1": {"level2": "value"}}

        value = mock_validator._get_nested_value(data, ("level1", "missing", "key"))
        assert value is None

    def test_get_nested_value_out_of_range(self, mock_validator: ConfigValidator) -> None:
        """Test getting nested value with out-of-range list index."""
        data = {"items": [1, 2, 3]}

        value = mock_validator._get_nested_value(data, ("items", 10))
        assert value is None


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_empty_config_file(self, tmp_path: Path, mock_validator: ConfigValidator) -> None:
        """Test handling of empty config file."""
        config_file = tmp_path / "empty.json"
        with open(config_file, "w", encoding="utf-8") as f:
            f.write("{}")

        report = mock_validator.validate_file(config_file)

        assert report.is_valid is True
        assert report.total_workflows == 0

    def test_config_with_unicode(self, tmp_path: Path, mock_validator: ConfigValidator) -> None:
        """Test handling of config with unicode characters."""
        config = {"name": "Unicode Config 你好", "default_workflow": "test", "workflows": []}

        config_file = tmp_path / "unicode.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False)

        report = mock_validator.validate_file(config_file)

        assert report.config_path == config_file
        assert report.total_workflows == 0

    def test_workflow_without_id(self, tmp_path: Path, mock_validator: ConfigValidator) -> None:
        """Test handling of workflow without ID field."""
        from pydantic import ValidationError as PydanticValidationError

        config = {
            "name": "No ID Config",
            "default_workflow": "test",
            "workflows": [
                {
                    "name": "Workflow without ID",
                    "actions": {},
                    "connections": {},
                    "initial_action": "action1",
                }
            ],
        }

        config_file = tmp_path / "no_id.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f)

        error_dict = {"type": "missing", "loc": ("id",), "msg": "Field required", "input": {}}

        mock_validator.Workflow.model_validate.side_effect = (
            PydanticValidationError.from_exception_data("ValidationError", [error_dict])
        )

        report = mock_validator.validate_file(config_file)

        # Should handle gracefully with "unknown" ID
        assert report.is_valid is False
        assert len(report.errors) > 0
        assert report.errors[0].workflow_id == "unknown"

    def test_large_config_file(self, tmp_path: Path, mock_validator: ConfigValidator) -> None:
        """Test handling of large config file with many workflows."""
        config = {
            "name": "Large Config",
            "default_workflow": "workflow_0",
            "workflows": [
                {
                    "id": f"workflow_{i}",
                    "name": f"Workflow {i}",
                    "actions": {
                        f"action_{j}": {"type": "Click", "name": f"Action {j}"} for j in range(10)
                    },
                    "connections": {},
                    "initial_action": "action_0",
                }
                for i in range(50)
            ],
        }

        config_file = tmp_path / "large.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f)

        # Mock validation success for all workflows
        mock_validator.Workflow.model_validate.return_value = MagicMock()

        report = mock_validator.validate_file(config_file)

        assert report.total_workflows == 50


class TestIntegrationWithFixtures:
    """Integration tests using pre-created fixture files."""

    def test_fixture_valid_config(
        self, fixtures_dir: Path, mock_validator: ConfigValidator
    ) -> None:
        """Test validation using fixture valid config file."""
        fixture_file = fixtures_dir / "valid_config.json"

        if not fixture_file.exists():
            pytest.skip("Fixture file not found")

        mock_validator.Workflow.model_validate.return_value = MagicMock()

        report = mock_validator.validate_file(fixture_file)

        assert isinstance(report, ValidationReport)
        assert report.config_path == fixture_file

    def test_fixture_invalid_connections(
        self, fixtures_dir: Path, mock_validator: ConfigValidator
    ) -> None:
        """Test validation using fixture invalid connections file."""
        from pydantic import ValidationError as PydanticValidationError

        fixture_file = fixtures_dir / "invalid_connections_format.json"

        if not fixture_file.exists():
            pytest.skip("Fixture file not found")

        error_dict = {
            "type": "dict_type",
            "loc": ("connections",),
            "msg": "Invalid connections",
            "input": {},
        }

        mock_validator.Workflow.model_validate.side_effect = (
            PydanticValidationError.from_exception_data("ValidationError", [error_dict])
        )

        report = mock_validator.validate_file(fixture_file)

        assert report.is_valid is False
