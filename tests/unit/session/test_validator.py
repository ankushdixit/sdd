"""Unit tests for session_validate module.

This module tests session validation functionality with quality gate configuration,
particularly testing how the validator respects the 'required' flag for different
quality gates.
"""

import json
from unittest.mock import patch

import pytest

from solokit.session.validate import SessionValidator


@pytest.fixture
def session_project(tmp_path):
    """Create session project structure with .session directory.

    Args:
        tmp_path: Pytest tmp_path fixture.

    Returns:
        Path: Root project directory with .session subdirectory.
    """
    session_dir = tmp_path / ".session"
    session_dir.mkdir()
    return tmp_path


@pytest.fixture
def create_config(session_project):
    """Factory fixture to create config.json with specified quality gates.

    Args:
        session_project: Session project directory fixture.

    Returns:
        callable: Function that creates config file with given config dict.
    """

    def _create_config(config_dict):
        config_file = session_project / ".session" / "config.json"
        with open(config_file, "w") as f:
            json.dump(config_dict, f)
        return config_file

    return _create_config


class TestRequiredFlagHandling:
    """Test suite for quality gate 'required' flag handling."""

    def test_validation_passes_when_tests_not_required_and_fail(
        self, session_project, create_config
    ):
        """Test that validation passes when test_execution.required is false even if tests fail."""
        # Arrange
        config = {
            "quality_gates": {
                "test_execution": {
                    "enabled": True,
                    "required": False,  # Tests not required
                    "coverage_threshold": 80,
                    "commands": {"python": "pytest --cov --cov-report=json"},
                },
                "linting": {"enabled": True, "required": False},
                "formatting": {"enabled": True, "required": False},
            }
        }
        create_config(config)
        validator = SessionValidator(session_project)

        # Act
        with (
            patch.object(
                validator.quality_gates,
                "run_tests",
                return_value=(False, {"status": "failed"}),
            ),
            patch.object(
                validator.quality_gates,
                "run_linting",
                return_value=(True, {"status": "skipped"}),
            ),
            patch.object(
                validator.quality_gates,
                "run_formatting",
                return_value=(True, {"status": "skipped"}),
            ),
        ):
            result = validator.preview_quality_gates()

        # Assert
        assert result["passed"], "Quality gates should pass when tests are not required"
        assert "tests" in result["gates"]
        assert result["gates"]["tests"]["passed"], "Test gate should pass when not required"

    def test_validation_fails_when_tests_required_and_fail(self, session_project, create_config):
        """Test that validation fails when test_execution.required is true and tests fail."""
        # Arrange
        config = {
            "quality_gates": {
                "test_execution": {
                    "enabled": True,
                    "required": True,  # Tests are required
                    "coverage_threshold": 80,
                    "commands": {"python": "pytest --cov --cov-report=json"},
                },
                "linting": {"enabled": False, "required": False},
                "formatting": {"enabled": False, "required": False},
            }
        }
        create_config(config)
        validator = SessionValidator(session_project)

        # Act
        with patch.object(
            validator.quality_gates,
            "run_tests",
            return_value=(False, {"status": "failed"}),
        ):
            result = validator.preview_quality_gates()

        # Assert
        assert not result["passed"], "Quality gates should fail when required tests fail"
        assert "tests" in result["gates"]
        assert not result["gates"]["tests"]["passed"], (
            "Test gate should fail when required and tests fail"
        )


class TestDisabledGateHandling:
    """Test suite for disabled quality gate handling."""

    def test_validation_skips_disabled_gates(self, session_project, create_config):
        """Test that validation skips quality gates that are disabled."""
        # Arrange
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
        create_config(config)
        validator = SessionValidator(session_project)

        # Act
        result = validator.preview_quality_gates()

        # Assert
        assert result["passed"], "Quality gates should pass when all gates are disabled"
        assert "tests" not in result["gates"], "Disabled gates should not appear in results"


class TestMixedRequiredGates:
    """Test suite for mixed required and optional quality gates."""

    def test_validation_with_mixed_required_and_optional_gates(
        self, session_project, create_config
    ):
        """Test validation behavior with some required and some optional gates."""
        # Arrange
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
        create_config(config)
        validator = SessionValidator(session_project)

        # Act
        with (
            patch.object(
                validator.quality_gates,
                "run_tests",
                return_value=(False, {"status": "failed"}),
            ),
            patch.object(
                validator.quality_gates,
                "run_linting",
                return_value=(False, {"status": "failed"}),
            ),
            patch.object(
                validator.quality_gates,
                "run_formatting",
                return_value=(False, {"status": "failed"}),
            ),
        ):
            result = validator.preview_quality_gates()

        # Assert
        # Optional gates (tests, formatting) should pass even when they "fail"
        if "tests" in result["gates"]:
            assert result["gates"]["tests"]["passed"], (
                "Optional test gate should pass even when execution fails"
            )
        if "formatting" in result["gates"]:
            assert result["gates"]["formatting"]["passed"], (
                "Optional formatting gate should pass even when execution fails"
            )

        # Required gate (linting) should fail
        assert "linting" in result["gates"]
        assert not result["gates"]["linting"]["passed"], (
            "Required linting gate should fail when linting fails"
        )

        # Overall validation should fail because a required gate failed
        assert not result["passed"], "Overall validation should fail when any required gate fails"
