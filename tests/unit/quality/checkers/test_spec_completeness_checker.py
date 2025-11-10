"""Unit tests for spec_completeness.py SpecCompletenessChecker.

Tests for the SpecCompletenessChecker class which validates specification files.
"""

from unittest.mock import patch

import pytest

from solokit.core.exceptions import FileNotFoundError as SolokitFileNotFoundError
from solokit.core.exceptions import SpecValidationError
from solokit.quality.checkers.spec_completeness import SpecCompletenessChecker


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project directory."""
    return tmp_path


@pytest.fixture
def spec_config():
    """Standard spec completeness config."""
    return {"enabled": True}


class TestSpecCompletenessCheckerInit:
    """Tests for SpecCompletenessChecker initialization."""

    def test_init_with_defaults(self, spec_config, temp_project_dir):
        """Test initialization with default parameters."""
        checker = SpecCompletenessChecker(spec_config, temp_project_dir)

        assert checker.config == spec_config
        assert checker.project_root == temp_project_dir
        assert checker.work_item == {}

    def test_init_with_work_item(self, spec_config, temp_project_dir):
        """Test initialization with work item."""
        work_item = {"id": "WI-001", "type": "feature"}
        checker = SpecCompletenessChecker(spec_config, temp_project_dir, work_item=work_item)

        assert checker.work_item == work_item


class TestSpecCompletenessCheckerInterface:
    """Tests for SpecCompletenessChecker interface methods."""

    def test_name_returns_spec_completeness(self, spec_config, temp_project_dir):
        """Test name() returns 'spec_completeness'."""
        checker = SpecCompletenessChecker(spec_config, temp_project_dir)

        assert checker.name() == "spec_completeness"

    def test_is_enabled_returns_true_by_default(self, temp_project_dir):
        """Test is_enabled() returns True by default."""
        config = {}
        checker = SpecCompletenessChecker(config, temp_project_dir)

        assert checker.is_enabled() is True

    def test_is_enabled_returns_config_value(self, temp_project_dir):
        """Test is_enabled() returns config value."""
        config = {"enabled": False}
        checker = SpecCompletenessChecker(config, temp_project_dir)

        assert checker.is_enabled() is False


class TestSpecCompletenessCheckerRun:
    """Tests for SpecCompletenessChecker.run() method."""

    def test_run_returns_skipped_when_disabled(self, temp_project_dir):
        """Test run() returns skipped result when disabled."""
        config = {"enabled": False}
        checker = SpecCompletenessChecker(config, temp_project_dir)

        result = checker.run()

        assert result.checker_name == "spec_completeness"
        assert result.passed is True
        assert result.status == "skipped"

    def test_run_fails_when_work_item_missing_id(self, spec_config, temp_project_dir):
        """Test run() fails when work item missing id."""
        work_item = {"type": "feature"}
        checker = SpecCompletenessChecker(spec_config, temp_project_dir, work_item=work_item)

        result = checker.run()

        assert result.passed is False
        assert result.status == "failed"
        assert "missing 'id'" in str(result.errors[0])

    def test_run_fails_when_work_item_missing_type(self, spec_config, temp_project_dir):
        """Test run() fails when work item missing type."""
        work_item = {"id": "WI-001"}
        checker = SpecCompletenessChecker(spec_config, temp_project_dir, work_item=work_item)

        result = checker.run()

        assert result.passed is False
        assert result.status == "failed"
        assert "missing" in str(result.errors[0])

    def test_run_passes_when_spec_valid(self, spec_config, temp_project_dir):
        """Test run() passes when spec file is valid."""
        work_item = {"id": "WI-001", "type": "feature"}
        checker = SpecCompletenessChecker(spec_config, temp_project_dir, work_item=work_item)

        with patch("solokit.quality.checkers.spec_completeness.validate_spec_file"):
            result = checker.run()

        assert result.passed is True
        assert result.status == "passed"
        assert "complete" in result.info["message"]

    def test_run_fails_with_validation_errors(self, spec_config, temp_project_dir):
        """Test run() fails when spec validation fails."""
        work_item = {"id": "WI-001", "type": "feature"}
        checker = SpecCompletenessChecker(spec_config, temp_project_dir, work_item=work_item)

        validation_error = SpecValidationError(
            work_item_id="WI-001",
            errors=["Missing Overview section", "Missing Acceptance Criteria"],
            remediation="Add missing sections",
        )

        with patch(
            "solokit.quality.checkers.spec_completeness.validate_spec_file",
            side_effect=validation_error,
        ):
            result = checker.run()

        assert result.passed is False
        assert result.status == "failed"
        assert len(result.errors) == 2
        assert "suggestion" in result.info

    def test_run_fails_when_spec_file_not_found(self, spec_config, temp_project_dir):
        """Test run() fails when spec file not found."""
        work_item = {"id": "WI-001", "type": "feature"}
        checker = SpecCompletenessChecker(spec_config, temp_project_dir, work_item=work_item)

        file_error = SolokitFileNotFoundError(
            file_path=".session/specs/WI-001.md", file_type="spec"
        )

        with patch(
            "solokit.quality.checkers.spec_completeness.validate_spec_file",
            side_effect=file_error,
        ):
            result = checker.run()

        assert result.passed is False
        assert result.status == "failed"
        assert len(result.errors) == 1
        assert "suggestion" in result.info

    def test_run_handles_generic_errors(self, spec_config, temp_project_dir):
        """Test run() handles generic errors."""
        work_item = {"id": "WI-001", "type": "feature"}
        checker = SpecCompletenessChecker(spec_config, temp_project_dir, work_item=work_item)

        with patch(
            "solokit.quality.checkers.spec_completeness.validate_spec_file",
            side_effect=ValueError("Parse error"),
        ):
            result = checker.run()

        assert result.passed is False
        assert result.status == "failed"
        assert "Parse error" in str(result.errors[0])

    def test_run_includes_execution_time(self, spec_config, temp_project_dir):
        """Test run() includes execution time in result."""
        work_item = {"id": "WI-001", "type": "feature"}
        checker = SpecCompletenessChecker(spec_config, temp_project_dir, work_item=work_item)

        with patch("solokit.quality.checkers.spec_completeness.validate_spec_file"):
            result = checker.run()

        assert result.execution_time > 0

    def test_run_includes_work_item_id_in_messages(self, spec_config, temp_project_dir):
        """Test run() includes work item ID in messages."""
        work_item = {"id": "WI-001", "type": "feature"}
        checker = SpecCompletenessChecker(spec_config, temp_project_dir, work_item=work_item)

        with patch("solokit.quality.checkers.spec_completeness.validate_spec_file"):
            result = checker.run()

        assert "WI-001" in result.info["message"]
