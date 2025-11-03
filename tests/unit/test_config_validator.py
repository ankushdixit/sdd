"""Unit tests for config_validator module.

This module tests configuration validation functionality including:
- JSON schema validation
- Config file loading and validation
- Error handling for invalid configs
- SDD-specific configuration validation
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from sdd.core.config_validator import (
    _format_validation_error,
    load_and_validate_config,
    validate_config,
)


@pytest.fixture
def minimal_schema(tmp_path):
    """Create minimal JSON schema for testing basic validation.

    Returns:
        Path: Path to minimal schema file with single required string field.
    """
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {"test_field": {"type": "string"}},
        "required": ["test_field"],
    }
    path = tmp_path / "schema.json"
    path.write_text(json.dumps(schema))
    return path


@pytest.fixture
def full_sdd_schema(tmp_path):
    """Create full SDD config schema for comprehensive testing.

    Returns:
        Path: Path to full SDD schema, or skips test if schema not found.
    """
    repo_schema = Path("src/sdd/templates/config.schema.json")
    if repo_schema.exists():
        schema_content = repo_schema.read_text()
        path = tmp_path / "config.schema.json"
        path.write_text(schema_content)
        return path
    else:
        pytest.skip("config.schema.json not found in repository")


class TestImportHandling:
    """Test suite for jsonschema import handling."""

    def test_validate_config_handles_missing_jsonschema_library(self, tmp_path):
        """Test that validate_config warns when jsonschema is not installed."""
        # Arrange
        config = {"test_field": "value"}
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config))
        schema_path = tmp_path / "schema.json"
        schema_path.write_text(json.dumps({"type": "object"}))

        # Act
        with patch.dict("sys.modules", {"jsonschema": None}):
            # Force reload to trigger ImportError path
            import importlib

            import sdd.core.config_validator as cv

            importlib.reload(cv)
            is_valid, errors = cv.validate_config(config_path, schema_path)

        # Assert
        assert is_valid  # Should be valid (validation skipped)
        assert len(errors) == 1
        assert "jsonschema not installed" in errors[0].lower()


class TestValidateConfig:
    """Test suite for validate_config function with basic schemas."""

    def test_validate_config_accepts_valid_configuration(self, tmp_path, minimal_schema):
        """Test that validate_config returns True for a valid configuration."""
        # Arrange
        config = {"test_field": "value"}
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config))

        # Act
        is_valid, errors = validate_config(config_path, minimal_schema)

        # Assert
        assert is_valid
        assert len(errors) == 0

    def test_validate_config_rejects_wrong_type(self, tmp_path, minimal_schema):
        """Test that validate_config rejects config with wrong field type."""
        # Arrange
        config = {"test_field": 123}  # Should be string, not int
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config))

        # Act
        is_valid, errors = validate_config(config_path, minimal_schema)

        # Assert
        assert not is_valid
        assert len(errors) > 0
        assert "test_field" in errors[0]

    def test_validate_config_rejects_missing_required_field(self, tmp_path, minimal_schema):
        """Test that validate_config rejects config missing required field."""
        # Arrange
        config = {}  # Missing required test_field
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config))

        # Act
        is_valid, errors = validate_config(config_path, minimal_schema)

        # Assert
        assert not is_valid
        assert len(errors) > 0

    def test_validate_config_handles_missing_config_file(self, tmp_path, minimal_schema):
        """Test that validate_config reports error when config file doesn't exist."""
        # Arrange
        config_path = tmp_path / "nonexistent.json"

        # Act
        is_valid, errors = validate_config(config_path, minimal_schema)

        # Assert
        assert not is_valid
        assert any("not found" in error.lower() for error in errors)

    def test_validate_config_warns_on_missing_schema_file(self, tmp_path):
        """Test that validate_config warns when schema file doesn't exist but allows config."""
        # Arrange
        config = {"test_field": "value"}
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config))
        schema_path = tmp_path / "nonexistent_schema.json"

        # Act
        is_valid, errors = validate_config(config_path, schema_path)

        # Assert
        assert is_valid  # Should be valid (no validation performed)
        assert len(errors) > 0  # But should have warning
        assert any("warning" in error.lower() for error in errors)

    def test_validate_config_handles_invalid_json_in_config(self, tmp_path, minimal_schema):
        """Test that validate_config reports error when config has invalid JSON."""
        # Arrange
        config_path = tmp_path / "config.json"
        config_path.write_text("{invalid json")

        # Act
        is_valid, errors = validate_config(config_path, minimal_schema)

        # Assert
        assert not is_valid
        assert any("invalid json" in error.lower() for error in errors)

    def test_validate_config_handles_invalid_json_in_schema(self, tmp_path):
        """Test that validate_config reports error when schema has invalid JSON."""
        # Arrange
        config = {"test_field": "value"}
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config))
        schema_path = tmp_path / "schema.json"
        schema_path.write_text("{invalid json")

        # Act
        is_valid, errors = validate_config(config_path, schema_path)

        # Assert
        assert not is_valid
        assert any("invalid json" in error.lower() for error in errors)

    def test_validate_config_handles_invalid_schema_structure(self, tmp_path):
        """Test that validate_config reports error when schema structure is invalid."""
        # Arrange
        config = {"test_field": "value"}
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config))

        # Create schema with invalid structure (e.g., circular reference or invalid type)
        schema = {"type": "invalid_type"}  # 'invalid_type' is not a valid JSON schema type
        schema_path = tmp_path / "schema.json"
        schema_path.write_text(json.dumps(schema))

        # Act
        is_valid, errors = validate_config(config_path, schema_path)

        # Assert
        assert not is_valid
        assert any("invalid schema" in error.lower() for error in errors)


class TestFormatValidationError:
    """Test suite for _format_validation_error helper function."""

    def test_format_validation_error_with_path(self):
        """Test that _format_validation_error formats error with path correctly."""
        # Arrange
        try:
            import jsonschema

            # Create a validation error with a path
            schema = {
                "type": "object",
                "properties": {
                    "nested": {"type": "object", "properties": {"field": {"type": "string"}}}
                },
            }
            instance = {"nested": {"field": 123}}
            try:
                jsonschema.validate(instance=instance, schema=schema)
            except jsonschema.ValidationError as e:
                # Act
                result = _format_validation_error(e)

                # Assert
                assert "nested -> field" in result or "nested" in result
                assert "123" in result or "not of type" in result.lower()
        except ImportError:
            pytest.skip("jsonschema not installed")

    def test_format_validation_error_without_path(self):
        """Test that _format_validation_error formats root-level error correctly."""
        # Arrange
        try:
            import jsonschema

            # Create a validation error without path (root level)
            schema = {"type": "string"}
            instance = 123
            try:
                jsonschema.validate(instance=instance, schema=schema)
            except jsonschema.ValidationError as e:
                # Act
                result = _format_validation_error(e)

                # Assert
                assert "root" in result.lower()
                assert "123" in result or "not of type" in result.lower()
        except ImportError:
            pytest.skip("jsonschema not installed")


class TestLoadAndValidateConfig:
    """Test suite for load_and_validate_config function."""

    def test_load_and_validate_raises_on_invalid_config(self, tmp_path, minimal_schema):
        """Test that load_and_validate_config raises ValueError for invalid config."""
        # Arrange
        config = {"test_field": 123}  # Wrong type
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config))

        # Act & Assert
        with pytest.raises(ValueError, match="Configuration validation failed"):
            load_and_validate_config(config_path, minimal_schema)

    def test_load_and_validate_returns_valid_config(self, tmp_path, minimal_schema):
        """Test that load_and_validate_config returns config dict for valid input."""
        # Arrange
        config = {"test_field": "value", "extra_field": 42}
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config))

        # Act
        result = load_and_validate_config(config_path, minimal_schema)

        # Assert
        assert result == config


class TestSDDConfigValidation:
    """Test suite for SDD-specific configuration validation."""

    def test_sdd_config_accepts_complete_valid_configuration(self, tmp_path, full_sdd_schema):
        """Test that full SDD configuration with all valid fields passes validation."""
        # Arrange
        config = {
            "quality_gates": {
                "test": {"required": True, "command": "pytest tests/", "timeout": 300},
                "lint": {"required": False, "command": "ruff check .", "timeout": 60},
                "security": {"required": True, "severity": "high", "timeout": 120},
            },
            "learning": {
                "auto_curate_frequency": 5,
                "similarity_threshold": 0.7,
                "containment_threshold": 0.8,
            },
            "session": {"auto_commit": False, "require_work_item": True},
        }
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config))

        # Act
        is_valid, errors = validate_config(config_path, full_sdd_schema)

        # Assert
        assert is_valid, f"Validation failed: {errors}"
        assert len(errors) == 0

    def test_sdd_config_rejects_invalid_severity_value(self, tmp_path, full_sdd_schema):
        """Test that SDD config rejects invalid security severity value."""
        # Arrange
        config = {
            "quality_gates": {"security": {"required": True, "severity": "invalid", "timeout": 120}}
        }
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config))

        # Act
        is_valid, errors = validate_config(config_path, full_sdd_schema)

        # Assert
        assert not is_valid
        assert any("severity" in error for error in errors)

    def test_sdd_config_rejects_out_of_range_threshold(self, tmp_path, full_sdd_schema):
        """Test that SDD config rejects similarity threshold outside valid range."""
        # Arrange
        config = {
            "learning": {
                "auto_curate_frequency": 5,
                "similarity_threshold": 1.5,  # Out of range (max 1.0)
            }
        }
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config))

        # Act
        is_valid, errors = validate_config(config_path, full_sdd_schema)

        # Assert
        assert not is_valid
        assert any("similarity_threshold" in error or "maximum" in error for error in errors)

    def test_sdd_config_rejects_invalid_timeout_value(self, tmp_path, full_sdd_schema):
        """Test that SDD config rejects timeout value less than minimum."""
        # Arrange
        config = {
            "quality_gates": {"test": {"required": True, "timeout": 0}}  # Min is 1
        }
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config))

        # Act
        is_valid, errors = validate_config(config_path, full_sdd_schema)

        # Assert
        assert not is_valid
        assert any("timeout" in error or "minimum" in error for error in errors)

    def test_sdd_config_rejects_missing_required_field(self, tmp_path, full_sdd_schema):
        """Test that SDD config rejects quality gate missing required field."""
        # Arrange
        config = {
            "quality_gates": {
                "test": {
                    # Missing 'required' field which is required
                    "command": "pytest tests/",
                    "timeout": 300,
                }
            }
        }
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config))

        # Act
        is_valid, errors = validate_config(config_path, full_sdd_schema)

        # Assert
        assert not is_valid
        assert any("required" in error for error in errors)

    def test_sdd_config_allows_additional_properties(self, tmp_path, full_sdd_schema):
        """Test that SDD config schema allows additional custom properties."""
        # Arrange
        config = {
            "quality_gates": {"test": {"required": True}},
            "custom_section": {"custom_field": "value"},  # Additional property
        }
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config))

        # Act
        is_valid, errors = validate_config(config_path, full_sdd_schema)

        # Assert
        assert is_valid  # Should be valid (additionalProperties: true in schema)


class TestMain:
    """Test suite for main() CLI entry point."""

    def test_main_with_no_arguments_shows_usage(self, capsys):
        """Test that main() displays usage message when called without arguments."""
        # Arrange
        import sys

        from sdd.core.config_validator import main

        # Act & Assert
        with patch.object(sys, "argv", ["config_validator.py"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Usage:" in captured.out
        assert "config_path" in captured.out

    def test_main_validates_config_successfully(self, tmp_path, minimal_schema, capsys):
        """Test that main() exits with 0 when config is valid."""
        # Arrange
        import sys

        from sdd.core.config_validator import main

        config = {"test_field": "value"}
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config))

        # Act & Assert
        with patch.object(
            sys, "argv", ["config_validator.py", str(config_path), str(minimal_schema)]
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Configuration is valid" in captured.out

    def test_main_reports_validation_errors(self, tmp_path, minimal_schema, capsys):
        """Test that main() exits with 1 and shows errors when config is invalid."""
        # Arrange
        import sys

        from sdd.core.config_validator import main

        config = {"test_field": 123}  # Wrong type
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config))

        # Act & Assert
        with patch.object(
            sys, "argv", ["config_validator.py", str(config_path), str(minimal_schema)]
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "validation failed" in captured.out.lower()
        assert "Errors:" in captured.out

    def test_main_uses_default_schema_path_when_not_provided(self, tmp_path, capsys):
        """Test that main() uses default schema path from config directory."""
        # Arrange
        import sys

        from sdd.core.config_validator import main

        config = {"test_field": "value"}
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config))

        # Create schema at default location
        schema_path = tmp_path / "config.schema.json"
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {"test_field": {"type": "string"}},
            "required": ["test_field"],
        }
        schema_path.write_text(json.dumps(schema))

        # Act & Assert
        with patch.object(sys, "argv", ["config_validator.py", str(config_path)]):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Configuration is valid" in captured.out

    def test_main_shows_warnings_for_valid_config(self, tmp_path, capsys):
        """Test that main() displays warnings even when config is valid."""
        # Arrange
        import sys

        from sdd.core.config_validator import main

        config = {"test_field": "value"}
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config))

        # Schema doesn't exist, so we'll get a warning
        schema_path = tmp_path / "nonexistent.json"

        # Act & Assert
        with patch.object(sys, "argv", ["config_validator.py", str(config_path), str(schema_path)]):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 0  # Valid despite warning
        captured = capsys.readouterr()
        assert "Configuration is valid" in captured.out
        assert "Warnings:" in captured.out
