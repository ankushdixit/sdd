"""
Tests for session validation with quality gate configuration.

Tests that the session validator properly respects quality gate
configuration settings, particularly the 'required' flag.
"""

import json
from unittest.mock import patch

from scripts.session_validate import SessionValidator


def test_validation_respects_required_false_for_tests(tmp_path):
    """Test that validation passes when test_execution.required is false."""
    # Setup test project structure
    session_dir = tmp_path / ".session"
    session_dir.mkdir()

    # Create config with test_execution.required = false
    config = {
        "quality_gates": {
            "test_execution": {
                "enabled": True,
                "required": False,  # Key: tests not required
                "coverage_threshold": 80,
                "commands": {
                    "python": "pytest --cov --cov-report=json",
                },
            },
            "linting": {"enabled": True, "required": False},
            "formatting": {"enabled": True, "required": False},
        }
    }

    config_file = session_dir / "config.json"
    with open(config_file, "w") as f:
        json.dump(config, f)

    # Initialize validator
    validator = SessionValidator(tmp_path)

    # Mock the quality gate methods to avoid actually running tests
    with (
        patch.object(
            validator.quality_gates, "run_tests", return_value=(False, {"status": "failed"})
        ),
        patch.object(
            validator.quality_gates, "run_linting", return_value=(True, {"status": "skipped"})
        ),
        patch.object(
            validator.quality_gates, "run_formatting", return_value=(True, {"status": "skipped"})
        ),
    ):
        # Run quality gate preview
        result = validator.preview_quality_gates()

        # Should pass even when tests fail, because tests are not required
        assert result["passed"], "Quality gates should pass when tests are not required"
        assert "tests" in result["gates"]
        assert result["gates"]["tests"]["passed"], "Test gate should pass when not required"


def test_validation_respects_required_true_for_tests(tmp_path):
    """Test that validation fails when test_execution.required is true and tests fail."""
    # Setup test project structure
    session_dir = tmp_path / ".session"
    session_dir.mkdir()

    # Create config with test_execution.required = true
    config = {
        "quality_gates": {
            "test_execution": {
                "enabled": True,
                "required": True,  # Key: tests are required
                "coverage_threshold": 80,
                "commands": {
                    "python": "pytest --cov --cov-report=json",
                },
            },
            "linting": {"enabled": False, "required": False},
            "formatting": {"enabled": False, "required": False},
        }
    }

    config_file = session_dir / "config.json"
    with open(config_file, "w") as f:
        json.dump(config, f)

    # Initialize validator
    validator = SessionValidator(tmp_path)

    # Mock the test to fail
    with patch.object(
        validator.quality_gates, "run_tests", return_value=(False, {"status": "failed"})
    ):
        # Run quality gate preview
        result = validator.preview_quality_gates()

        # Should fail because tests are required and they failed
        assert not result["passed"], "Quality gates should fail when required tests fail"
        assert "tests" in result["gates"]
        assert not result["gates"]["tests"][
            "passed"
        ], "Test gate should fail when required and tests fail"


def test_validation_with_disabled_test_gate(tmp_path):
    """Test that validation skips disabled quality gates."""
    # Setup test project structure
    session_dir = tmp_path / ".session"
    session_dir.mkdir()

    # Create config with test_execution disabled
    config = {
        "quality_gates": {
            "test_execution": {
                "enabled": False,  # Disabled
                "required": True,
                "coverage_threshold": 80,
            },
            "linting": {"enabled": False},
            "formatting": {"enabled": False},
        }
    }

    config_file = session_dir / "config.json"
    with open(config_file, "w") as f:
        json.dump(config, f)

    # Initialize validator
    validator = SessionValidator(tmp_path)

    # Run quality gate preview
    result = validator.preview_quality_gates()

    # Should pass and not include disabled gates
    assert result["passed"], "Quality gates should pass when all gates are disabled"
    assert "tests" not in result["gates"], "Disabled gates should not be in results"


def test_validation_with_mixed_required_gates(tmp_path):
    """Test validation with some required and some optional gates."""
    # Setup test project structure
    session_dir = tmp_path / ".session"
    session_dir.mkdir()

    # Create config with mixed requirements
    config = {
        "quality_gates": {
            "test_execution": {
                "enabled": True,
                "required": False,  # Optional
                "coverage_threshold": 80,
            },
            "linting": {
                "enabled": True,
                "required": True,  # Required
                "commands": {"python": "ruff check ."},
            },
            "formatting": {
                "enabled": True,
                "required": False,  # Optional
            },
        }
    }

    config_file = session_dir / "config.json"
    with open(config_file, "w") as f:
        json.dump(config, f)

    # Initialize validator
    validator = SessionValidator(tmp_path)

    # Mock the quality gate methods
    with (
        patch.object(
            validator.quality_gates, "run_tests", return_value=(False, {"status": "failed"})
        ),
        patch.object(
            validator.quality_gates, "run_linting", return_value=(False, {"status": "failed"})
        ),
        patch.object(
            validator.quality_gates, "run_formatting", return_value=(False, {"status": "failed"})
        ),
    ):
        # Run quality gate preview
        result = validator.preview_quality_gates()

        # Tests and formatting should pass (not required) even though they "failed"
        if "tests" in result["gates"]:
            assert result["gates"]["tests"]["passed"], "Optional test gate should pass"
        if "formatting" in result["gates"]:
            assert result["gates"]["formatting"]["passed"], "Optional formatting gate should pass"

        # Linting should fail (required)
        assert "linting" in result["gates"]
        assert not result["gates"]["linting"][
            "passed"
        ], "Required linting gate should fail when linting fails"

        # Overall should fail because linting (required) failed
        assert not result["passed"], "Overall validation should fail when required gates fail"
