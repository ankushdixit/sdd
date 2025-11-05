"""Unit tests for custom.py CustomValidationChecker.

Tests for the CustomValidationChecker class which runs user-defined validation rules.
"""

from unittest.mock import Mock

import pytest

from sdd.core.command_runner import CommandResult, CommandRunner
from sdd.quality.checkers.custom import CustomValidationChecker


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project directory."""
    return tmp_path


@pytest.fixture
def mock_runner():
    """Create a mock CommandRunner."""
    return Mock(spec=CommandRunner)


@pytest.fixture
def custom_config():
    """Standard custom validation config."""
    return {
        "rules": [
            {
                "type": "command",
                "name": "Check version",
                "command": "python --version",
                "required": True,
            },
            {
                "type": "file_exists",
                "name": "Config exists",
                "path": "config.yaml",
                "required": False,
            },
        ]
    }


class TestCustomValidationCheckerInit:
    """Tests for CustomValidationChecker initialization."""

    def test_init_with_defaults(self, custom_config, temp_project_dir):
        """Test initialization with default parameters."""
        checker = CustomValidationChecker(custom_config, temp_project_dir)

        assert checker.config == custom_config
        assert checker.project_root == temp_project_dir
        assert checker.runner is not None
        assert isinstance(checker.runner, CommandRunner)
        assert checker.work_item == {}

    def test_init_with_custom_runner(
        self, custom_config, temp_project_dir, mock_runner
    ):
        """Test initialization with custom runner."""
        checker = CustomValidationChecker(
            custom_config, temp_project_dir, runner=mock_runner
        )

        assert checker.runner is mock_runner

    def test_init_with_work_item(self, custom_config, temp_project_dir):
        """Test initialization with work item."""
        work_item = {"id": "WI-001", "validation_rules": []}
        checker = CustomValidationChecker(
            custom_config, temp_project_dir, work_item=work_item
        )

        assert checker.work_item == work_item


class TestCustomValidationCheckerInterface:
    """Tests for CustomValidationChecker interface methods."""

    def test_name_returns_custom_validations(self, custom_config, temp_project_dir):
        """Test name() returns 'custom_validations'."""
        checker = CustomValidationChecker(custom_config, temp_project_dir)

        assert checker.name() == "custom_validations"

    def test_is_enabled_returns_true_when_rules_exist(
        self, custom_config, temp_project_dir
    ):
        """Test is_enabled() returns True when rules exist."""
        checker = CustomValidationChecker(custom_config, temp_project_dir)

        assert checker.is_enabled() is True

    def test_is_enabled_returns_false_when_no_rules(self, temp_project_dir):
        """Test is_enabled() returns False when no rules."""
        config = {"rules": []}
        work_item = {}
        checker = CustomValidationChecker(config, temp_project_dir, work_item=work_item)

        assert checker.is_enabled() is False

    def test_is_enabled_returns_true_when_work_item_has_rules(self, temp_project_dir):
        """Test is_enabled() returns True when work item has rules."""
        config = {"rules": []}
        work_item = {
            "validation_rules": [
                {"type": "command", "name": "Test", "command": "echo test"}
            ]
        }
        checker = CustomValidationChecker(config, temp_project_dir, work_item=work_item)

        assert checker.is_enabled() is True


class TestCustomValidationCheckerRun:
    """Tests for CustomValidationChecker.run() method."""

    def test_run_returns_skipped_when_no_rules(self, temp_project_dir, mock_runner):
        """Test run() returns skipped result when no rules defined."""
        config = {"rules": []}
        work_item = {}
        checker = CustomValidationChecker(
            config, temp_project_dir, work_item=work_item, runner=mock_runner
        )

        result = checker.run()

        assert result.checker_name == "custom_validations"
        assert result.passed is True
        assert result.status == "skipped"
        assert result.info["reason"] == "no custom rules defined"

    def test_run_passes_when_all_rules_pass(
        self, custom_config, temp_project_dir, mock_runner
    ):
        """Test run() passes when all rules pass."""
        checker = CustomValidationChecker(
            custom_config, temp_project_dir, runner=mock_runner
        )

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="Python 3.9",
            stderr="",
            command=["python"],
            duration_seconds=0.1,
        )

        with open(temp_project_dir / "config.yaml", "w") as f:
            f.write("test: true")

        result = checker.run()

        assert result.passed is True
        assert result.status == "passed"

    def test_run_fails_when_required_rule_fails(
        self, custom_config, temp_project_dir, mock_runner
    ):
        """Test run() fails when required rule fails."""
        checker = CustomValidationChecker(
            custom_config, temp_project_dir, runner=mock_runner
        )

        mock_runner.run.return_value = CommandResult(
            returncode=1,
            stdout="",
            stderr="Error",
            command=["python"],
            duration_seconds=0.1,
        )

        result = checker.run()

        assert result.passed is False
        assert result.status == "failed"
        assert len(result.errors) > 0

    def test_run_passes_when_optional_rule_fails(self, temp_project_dir, mock_runner):
        """Test run() passes when optional rule fails."""
        config = {
            "rules": [
                {
                    "type": "command",
                    "name": "Optional check",
                    "command": "false",
                    "required": False,
                },
            ]
        }
        checker = CustomValidationChecker(config, temp_project_dir, runner=mock_runner)

        mock_runner.run.return_value = CommandResult(
            returncode=1, stdout="", stderr="", command=["false"], duration_seconds=0.1
        )

        result = checker.run()

        assert result.passed is True
        assert result.status == "passed"
        assert len(result.warnings) > 0

    def test_run_includes_execution_time(
        self, custom_config, temp_project_dir, mock_runner
    ):
        """Test run() includes execution time in result."""
        checker = CustomValidationChecker(
            custom_config, temp_project_dir, runner=mock_runner
        )

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="Python 3.9",
            stderr="",
            command=["python"],
            duration_seconds=0.1,
        )

        with open(temp_project_dir / "config.yaml", "w") as f:
            f.write("test: true")

        result = checker.run()

        assert result.execution_time > 0

    def test_run_combines_project_and_work_item_rules(
        self, temp_project_dir, mock_runner
    ):
        """Test run() combines rules from config and work item."""
        config = {
            "rules": [
                {
                    "type": "command",
                    "name": "Project rule",
                    "command": "echo project",
                    "required": True,
                }
            ]
        }
        work_item = {
            "validation_rules": [
                {
                    "type": "command",
                    "name": "Work item rule",
                    "command": "echo work",
                    "required": True,
                }
            ]
        }
        checker = CustomValidationChecker(
            config, temp_project_dir, work_item=work_item, runner=mock_runner
        )

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="output",
            stderr="",
            command=["echo"],
            duration_seconds=0.1,
        )

        result = checker.run()

        assert len(result.info["validations"]) == 2


class TestCustomValidationCheckerCommandValidation:
    """Tests for command validation rules."""

    def test_run_command_validation_succeeds(
        self, custom_config, temp_project_dir, mock_runner
    ):
        """Test _run_command_validation succeeds when command succeeds."""
        checker = CustomValidationChecker(
            custom_config, temp_project_dir, runner=mock_runner
        )

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="Success",
            stderr="",
            command=["test"],
            duration_seconds=0.1,
        )

        rule = {"type": "command", "command": "test", "name": "Test"}
        result = checker._run_command_validation(rule)

        assert result is True

    def test_run_command_validation_fails(
        self, custom_config, temp_project_dir, mock_runner
    ):
        """Test _run_command_validation fails when command fails."""
        checker = CustomValidationChecker(
            custom_config, temp_project_dir, runner=mock_runner
        )

        mock_runner.run.return_value = CommandResult(
            returncode=1,
            stdout="",
            stderr="Error",
            command=["test"],
            duration_seconds=0.1,
        )

        rule = {"type": "command", "command": "test", "name": "Test"}
        result = checker._run_command_validation(rule)

        assert result is False

    def test_run_command_validation_handles_missing_command(
        self, custom_config, temp_project_dir, mock_runner
    ):
        """Test _run_command_validation handles missing command field."""
        checker = CustomValidationChecker(
            custom_config, temp_project_dir, runner=mock_runner
        )

        rule = {"type": "command", "name": "Test"}
        result = checker._run_command_validation(rule)

        assert result is True


class TestCustomValidationCheckerFileExistsValidation:
    """Tests for file_exists validation rules."""

    def test_check_file_exists_succeeds(self, custom_config, temp_project_dir):
        """Test _check_file_exists succeeds when file exists."""
        checker = CustomValidationChecker(custom_config, temp_project_dir)

        test_file = temp_project_dir / "test.txt"
        test_file.touch()

        rule = {"type": "file_exists", "path": "test.txt", "name": "Test"}
        result = checker._check_file_exists(rule)

        assert result is True

    def test_check_file_exists_fails(self, custom_config, temp_project_dir):
        """Test _check_file_exists fails when file doesn't exist."""
        checker = CustomValidationChecker(custom_config, temp_project_dir)

        rule = {"type": "file_exists", "path": "nonexistent.txt", "name": "Test"}
        result = checker._check_file_exists(rule)

        assert result is False

    def test_check_file_exists_handles_missing_path(
        self, custom_config, temp_project_dir
    ):
        """Test _check_file_exists handles missing path field."""
        checker = CustomValidationChecker(custom_config, temp_project_dir)

        rule = {"type": "file_exists", "name": "Test"}
        result = checker._check_file_exists(rule)

        assert result is True


class TestCustomValidationCheckerGrepValidation:
    """Tests for grep validation rules."""

    def test_run_grep_validation_succeeds(
        self, custom_config, temp_project_dir, mock_runner
    ):
        """Test _run_grep_validation succeeds when pattern found."""
        checker = CustomValidationChecker(
            custom_config, temp_project_dir, runner=mock_runner
        )

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="match found",
            stderr="",
            command=["grep"],
            duration_seconds=0.1,
        )

        rule = {"type": "grep", "pattern": "test", "files": ".", "name": "Test"}
        result = checker._run_grep_validation(rule)

        assert result is True

    def test_run_grep_validation_fails(
        self, custom_config, temp_project_dir, mock_runner
    ):
        """Test _run_grep_validation fails when pattern not found."""
        checker = CustomValidationChecker(
            custom_config, temp_project_dir, runner=mock_runner
        )

        mock_runner.run.return_value = CommandResult(
            returncode=1, stdout="", stderr="", command=["grep"], duration_seconds=0.1
        )

        rule = {"type": "grep", "pattern": "test", "files": ".", "name": "Test"}
        result = checker._run_grep_validation(rule)

        assert result is False

    def test_run_grep_validation_handles_missing_pattern(
        self, custom_config, temp_project_dir, mock_runner
    ):
        """Test _run_grep_validation handles missing pattern field."""
        checker = CustomValidationChecker(
            custom_config, temp_project_dir, runner=mock_runner
        )

        rule = {"type": "grep", "files": ".", "name": "Test"}
        result = checker._run_grep_validation(rule)

        assert result is True

    def test_run_grep_validation_uses_default_files(
        self, custom_config, temp_project_dir, mock_runner
    ):
        """Test _run_grep_validation uses default files when not specified."""
        checker = CustomValidationChecker(
            custom_config, temp_project_dir, runner=mock_runner
        )

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="match",
            stderr="",
            command=["grep"],
            duration_seconds=0.1,
        )

        rule = {"type": "grep", "pattern": "test", "name": "Test"}
        result = checker._run_grep_validation(rule)

        assert result is True
        call_args = mock_runner.run.call_args[0][0]
        assert "." in call_args


class TestCustomValidationCheckerUnknownRuleType:
    """Tests for unknown rule type handling."""

    def test_run_handles_unknown_rule_type(self, temp_project_dir, mock_runner):
        """Test run() handles unknown rule type gracefully."""
        config = {
            "rules": [{"type": "unknown_type", "name": "Unknown", "required": True}]
        }
        checker = CustomValidationChecker(config, temp_project_dir, runner=mock_runner)

        result = checker.run()

        # Unknown rule type should be treated as passed
        assert result.passed is True
        assert result.status == "passed"


class TestCustomValidationCheckerValidationDetails:
    """Tests for validation result details."""

    def test_run_includes_validation_details(
        self, custom_config, temp_project_dir, mock_runner
    ):
        """Test run() includes detailed validation information."""
        checker = CustomValidationChecker(
            custom_config, temp_project_dir, runner=mock_runner
        )

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="output",
            stderr="",
            command=["python"],
            duration_seconds=0.1,
        )

        with open(temp_project_dir / "config.yaml", "w") as f:
            f.write("test: true")

        result = checker.run()

        validations = result.info["validations"]
        assert len(validations) == 2
        assert all("name" in v for v in validations)
        assert all("passed" in v for v in validations)
        assert all("required" in v for v in validations)
        assert all("type" in v for v in validations)
