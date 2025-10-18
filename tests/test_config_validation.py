"""Tests for configuration validation."""

import json
import sys
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.config_validator import (  # noqa: E402
    load_and_validate_config,
    validate_config,
)


@pytest.fixture
def schema_path(tmp_path):
    """Create minimal schema for testing."""
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
def full_schema_path(tmp_path):
    """Create full SDD config schema for testing."""
    # Load the actual schema from the repository
    repo_schema = Path(".session/config.schema.json")
    if repo_schema.exists():
        schema_content = repo_schema.read_text()
        path = tmp_path / "config.schema.json"
        path.write_text(schema_content)
        return path
    else:
        pytest.skip("config.schema.json not found in repository")


def test_valid_config(tmp_path, schema_path):
    """Test validation of valid configuration."""
    config = {"test_field": "value"}
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))

    is_valid, errors = validate_config(config_path, schema_path)

    assert is_valid
    assert len(errors) == 0


def test_invalid_config_wrong_type(tmp_path, schema_path):
    """Test validation fails with wrong type."""
    config = {"test_field": 123}  # Should be string
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))

    is_valid, errors = validate_config(config_path, schema_path)

    assert not is_valid
    assert len(errors) > 0
    assert "test_field" in errors[0]


def test_invalid_config_missing_required(tmp_path, schema_path):
    """Test validation fails with missing required field."""
    config = {}  # Missing test_field
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))

    is_valid, errors = validate_config(config_path, schema_path)

    assert not is_valid
    assert len(errors) > 0


def test_load_and_validate_raises_on_invalid(tmp_path, schema_path):
    """Test load_and_validate_config raises ValueError on invalid config."""
    config = {"test_field": 123}
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))

    with pytest.raises(ValueError, match="Configuration validation failed"):
        load_and_validate_config(config_path, schema_path)


def test_load_and_validate_returns_config_on_valid(tmp_path, schema_path):
    """Test load_and_validate_config returns config on valid input."""
    config = {"test_field": "value", "extra_field": 42}
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))

    result = load_and_validate_config(config_path, schema_path)

    assert result == config


def test_config_file_not_found(tmp_path, schema_path):
    """Test error when config file doesn't exist."""
    config_path = tmp_path / "nonexistent.json"

    is_valid, errors = validate_config(config_path, schema_path)

    assert not is_valid
    assert any("not found" in error.lower() for error in errors)


def test_schema_file_not_found(tmp_path):
    """Test warning when schema file doesn't exist."""
    config = {"test_field": "value"}
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))
    schema_path = tmp_path / "nonexistent_schema.json"

    is_valid, errors = validate_config(config_path, schema_path)

    # Should be valid (no validation performed)
    assert is_valid
    # But should have warning
    assert len(errors) > 0
    assert any("warning" in error.lower() for error in errors)


def test_invalid_json_in_config(tmp_path, schema_path):
    """Test error when config file has invalid JSON."""
    config_path = tmp_path / "config.json"
    config_path.write_text("{invalid json")

    is_valid, errors = validate_config(config_path, schema_path)

    assert not is_valid
    assert any("invalid json" in error.lower() for error in errors)


def test_invalid_json_in_schema(tmp_path):
    """Test error when schema file has invalid JSON."""
    config = {"test_field": "value"}
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))

    schema_path = tmp_path / "schema.json"
    schema_path.write_text("{invalid json")

    is_valid, errors = validate_config(config_path, schema_path)

    assert not is_valid
    assert any("invalid json" in error.lower() for error in errors)


def test_full_sdd_config_valid(tmp_path, full_schema_path):
    """Test validation of complete SDD configuration."""
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

    is_valid, errors = validate_config(config_path, full_schema_path)

    assert is_valid, f"Validation failed: {errors}"
    assert len(errors) == 0


def test_full_sdd_config_invalid_severity(tmp_path, full_schema_path):
    """Test validation fails with invalid severity value."""
    config = {
        "quality_gates": {"security": {"required": True, "severity": "invalid", "timeout": 120}}
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))

    is_valid, errors = validate_config(config_path, full_schema_path)

    assert not is_valid
    assert any("severity" in error for error in errors)


def test_full_sdd_config_invalid_threshold(tmp_path, full_schema_path):
    """Test validation fails with out-of-range similarity threshold."""
    config = {
        "learning": {
            "auto_curate_frequency": 5,
            "similarity_threshold": 1.5,  # Out of range (max 1.0)
        }
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))

    is_valid, errors = validate_config(config_path, full_schema_path)

    assert not is_valid
    assert any("similarity_threshold" in error or "maximum" in error for error in errors)


def test_full_sdd_config_invalid_timeout(tmp_path, full_schema_path):
    """Test validation fails with invalid timeout (less than minimum)."""
    config = {"quality_gates": {"test": {"required": True, "timeout": 0}}}  # Min is 1
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))

    is_valid, errors = validate_config(config_path, full_schema_path)

    assert not is_valid
    assert any("timeout" in error or "minimum" in error for error in errors)


def test_full_sdd_config_missing_required_field(tmp_path, full_schema_path):
    """Test validation fails when required field is missing."""
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

    is_valid, errors = validate_config(config_path, full_schema_path)

    assert not is_valid
    assert any("required" in error for error in errors)


def test_additional_properties_allowed(tmp_path, full_schema_path):
    """Test that additional properties are allowed in config."""
    config = {
        "quality_gates": {"test": {"required": True}},
        "custom_section": {"custom_field": "value"},  # Additional property
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))

    is_valid, errors = validate_config(config_path, full_schema_path)

    # Should be valid (additionalProperties: true in schema)
    assert is_valid
