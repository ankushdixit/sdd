"""Unit tests for linting.py LintingChecker.

Tests for the LintingChecker class which runs linters like ruff, flake8, eslint.
"""

from unittest.mock import Mock

import pytest
from solokit.core.command_runner import CommandResult, CommandRunner
from solokit.quality.checkers.linting import LintingChecker


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project directory."""
    return tmp_path


@pytest.fixture
def mock_runner():
    """Create a mock CommandRunner."""
    return Mock(spec=CommandRunner)


@pytest.fixture
def linting_config():
    """Standard linting config."""
    return {
        "enabled": True,
        "required": False,
        "auto_fix": False,
        "commands": {
            "python": "ruff check src",
            "javascript": "eslint .",
            "typescript": "eslint .",
        },
    }


class TestLintingCheckerInit:
    """Tests for LintingChecker initialization."""

    def test_init_with_defaults(self, linting_config, temp_project_dir):
        """Test initialization with default parameters."""
        checker = LintingChecker(linting_config, temp_project_dir)

        assert checker.config == linting_config
        assert checker.project_root == temp_project_dir
        assert checker.runner is not None
        assert isinstance(checker.runner, CommandRunner)
        assert checker.auto_fix is False

    def test_init_with_custom_runner(self, linting_config, temp_project_dir, mock_runner):
        """Test initialization with custom runner."""
        checker = LintingChecker(linting_config, temp_project_dir, runner=mock_runner)

        assert checker.runner is mock_runner

    def test_init_with_explicit_language(self, linting_config, temp_project_dir):
        """Test initialization with explicit language."""
        checker = LintingChecker(linting_config, temp_project_dir, language="javascript")

        assert checker.language == "javascript"

    def test_init_with_auto_fix_from_config(self, temp_project_dir):
        """Test initialization with auto_fix from config."""
        config = {
            "enabled": True,
            "auto_fix": True,
            "commands": {"python": "ruff check"},
        }
        checker = LintingChecker(config, temp_project_dir)

        assert checker.auto_fix is True

    def test_init_with_auto_fix_override(self, temp_project_dir):
        """Test initialization with auto_fix override."""
        config = {
            "enabled": True,
            "auto_fix": False,
            "commands": {"python": "ruff check"},
        }
        checker = LintingChecker(config, temp_project_dir, auto_fix=True)

        assert checker.auto_fix is True

    def test_init_detects_python_from_pyproject(self, linting_config, temp_project_dir):
        """Test language detection for Python via pyproject.toml."""
        (temp_project_dir / "pyproject.toml").touch()

        checker = LintingChecker(linting_config, temp_project_dir)

        assert checker.language == "python"

    def test_init_detects_javascript_from_package_json(self, linting_config, temp_project_dir):
        """Test language detection for JavaScript via package.json."""
        (temp_project_dir / "package.json").touch()

        checker = LintingChecker(linting_config, temp_project_dir)

        assert checker.language == "javascript"

    def test_init_defaults_to_python(self, linting_config, temp_project_dir):
        """Test default language is Python."""
        checker = LintingChecker(linting_config, temp_project_dir)

        assert checker.language == "python"


class TestLintingCheckerInterface:
    """Tests for LintingChecker interface methods."""

    def test_name_returns_linting(self, linting_config, temp_project_dir):
        """Test name() returns 'linting'."""
        checker = LintingChecker(linting_config, temp_project_dir)

        assert checker.name() == "linting"

    def test_is_enabled_returns_true_by_default(self, temp_project_dir):
        """Test is_enabled() returns True by default."""
        config = {}
        checker = LintingChecker(config, temp_project_dir)

        assert checker.is_enabled() is True

    def test_is_enabled_returns_config_value(self, temp_project_dir):
        """Test is_enabled() returns config value."""
        config = {"enabled": False}
        checker = LintingChecker(config, temp_project_dir)

        assert checker.is_enabled() is False


class TestLintingCheckerRun:
    """Tests for LintingChecker.run() method."""

    def test_run_returns_skipped_when_disabled(self, temp_project_dir):
        """Test run() returns skipped result when disabled."""
        config = {"enabled": False}
        checker = LintingChecker(config, temp_project_dir)

        result = checker.run()

        assert result.checker_name == "linting"
        assert result.passed is True
        assert result.status == "skipped"

    def test_run_returns_skipped_when_no_command_for_language(self, temp_project_dir, mock_runner):
        """Test run() returns skipped when no command configured."""
        config = {"enabled": True, "commands": {}}
        checker = LintingChecker(config, temp_project_dir, language="python", runner=mock_runner)

        result = checker.run()

        assert result.status == "skipped"
        assert result.info["reason"] == "no command for python"

    def test_run_executes_linting_command(self, linting_config, temp_project_dir, mock_runner):
        """Test run() executes linting command."""
        checker = LintingChecker(
            linting_config, temp_project_dir, language="python", runner=mock_runner
        )

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="No issues found",
            stderr="",
            command=["ruff"],
            duration_seconds=0.5,
        )

        _ = checker.run()

        mock_runner.run.assert_called_once()
        call_args = mock_runner.run.call_args[0][0]
        assert "ruff" in call_args
        assert "check" in call_args

    def test_run_passes_when_no_issues(self, linting_config, temp_project_dir, mock_runner):
        """Test run() passes when no linting issues found."""
        checker = LintingChecker(
            linting_config, temp_project_dir, language="python", runner=mock_runner
        )

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="No issues found",
            stderr="",
            command=["ruff"],
            duration_seconds=0.5,
        )

        result = checker.run()

        assert result.passed is True
        assert result.status == "passed"

    def test_run_fails_when_issues_found(self, linting_config, temp_project_dir, mock_runner):
        """Test run() fails when linting issues found."""
        checker = LintingChecker(
            linting_config, temp_project_dir, language="python", runner=mock_runner
        )

        mock_runner.run.return_value = CommandResult(
            returncode=5,
            stdout="Found 5 issues",
            stderr="",
            command=["ruff"],
            duration_seconds=0.5,
        )

        result = checker.run()

        assert result.passed is False
        assert result.status == "failed"
        assert len(result.errors) > 0

    def test_run_adds_fix_flag_for_python_when_auto_fix(
        self, linting_config, temp_project_dir, mock_runner
    ):
        """Test run() adds --fix flag for Python when auto_fix enabled."""
        checker = LintingChecker(
            linting_config,
            temp_project_dir,
            language="python",
            auto_fix=True,
            runner=mock_runner,
        )

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="Fixed",
            stderr="",
            command=["ruff"],
            duration_seconds=0.5,
        )

        _ = checker.run()

        call_args = mock_runner.run.call_args[0][0]
        assert "--fix" in " ".join(call_args)

    def test_run_adds_fix_flag_for_javascript_when_auto_fix(
        self, linting_config, temp_project_dir, mock_runner
    ):
        """Test run() adds --fix flag for JavaScript when auto_fix enabled."""
        checker = LintingChecker(
            linting_config,
            temp_project_dir,
            language="javascript",
            auto_fix=True,
            runner=mock_runner,
        )

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="Fixed",
            stderr="",
            command=["eslint"],
            duration_seconds=0.5,
        )

        _ = checker.run()

        call_args = mock_runner.run.call_args[0][0]
        assert "--fix" in " ".join(call_args)

    def test_run_includes_execution_time(self, linting_config, temp_project_dir, mock_runner):
        """Test run() includes execution time in result."""
        checker = LintingChecker(
            linting_config, temp_project_dir, language="python", runner=mock_runner
        )

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="No issues",
            stderr="",
            command=["ruff"],
            duration_seconds=0.5,
        )

        result = checker.run()

        assert result.execution_time > 0

    def test_run_includes_auto_fixed_info(self, linting_config, temp_project_dir, mock_runner):
        """Test run() includes auto_fixed info in result."""
        checker = LintingChecker(
            linting_config,
            temp_project_dir,
            language="python",
            auto_fix=True,
            runner=mock_runner,
        )

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="Fixed issues",
            stderr="",
            command=["ruff"],
            duration_seconds=0.5,
        )

        result = checker.run()

        assert result.info["auto_fixed"] is True


class TestLintingCheckerTimeout:
    """Tests for timeout handling."""

    def test_run_handles_timeout_not_required(self, temp_project_dir, mock_runner):
        """Test run() handles timeout when linting not required."""
        config = {
            "enabled": True,
            "required": False,
            "commands": {"python": "ruff check"},
        }
        checker = LintingChecker(config, temp_project_dir, language="python", runner=mock_runner)

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="",
            stderr="",
            command=["ruff"],
            duration_seconds=120.0,
            timed_out=True,
        )

        result = checker.run()

        assert result.status == "skipped"
        assert result.info["reason"] == "timeout"
        assert result.passed is True

    def test_run_handles_timeout_required(self, temp_project_dir, mock_runner):
        """Test run() handles timeout when linting required."""
        config = {
            "enabled": True,
            "required": True,
            "commands": {"python": "ruff check"},
        }
        checker = LintingChecker(config, temp_project_dir, language="python", runner=mock_runner)

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="",
            stderr="",
            command=["ruff"],
            duration_seconds=120.0,
            timed_out=True,
        )

        result = checker.run()

        assert result.status == "failed"
        assert result.passed is False
        assert "timeout" in result.info["reason"]


class TestLintingCheckerToolNotFound:
    """Tests for missing tool handling."""

    def test_run_handles_tool_not_found_not_required(self, temp_project_dir, mock_runner):
        """Test run() handles tool not found when linting not required."""
        config = {
            "enabled": True,
            "required": False,
            "commands": {"python": "ruff check"},
        }
        checker = LintingChecker(config, temp_project_dir, language="python", runner=mock_runner)

        mock_runner.run.return_value = CommandResult(
            returncode=-1, stdout="", stderr="", command=["ruff"], duration_seconds=0.1
        )

        result = checker.run()

        assert result.status == "skipped"
        assert result.info["reason"] == "linting tool not available"

    def test_run_handles_tool_not_found_required(self, temp_project_dir, mock_runner):
        """Test run() handles tool not found when linting required."""
        config = {
            "enabled": True,
            "required": True,
            "commands": {"python": "ruff check"},
        }
        checker = LintingChecker(config, temp_project_dir, language="python", runner=mock_runner)

        mock_runner.run.return_value = CommandResult(
            returncode=-1, stdout="", stderr="", command=["ruff"], duration_seconds=0.1
        )

        result = checker.run()

        assert result.status == "failed"
        assert result.passed is False
        assert "not found" in str(result.errors[0])


class TestLintingCheckerErrorOutput:
    """Tests for error output handling."""

    def test_run_includes_error_output(self, linting_config, temp_project_dir, mock_runner):
        """Test run() includes error output in result."""
        checker = LintingChecker(
            linting_config, temp_project_dir, language="python", runner=mock_runner
        )

        mock_runner.run.return_value = CommandResult(
            returncode=3,
            stdout="file1.py:10: E501 line too long",
            stderr="",
            command=["ruff"],
            duration_seconds=0.5,
        )

        result = checker.run()

        assert result.errors[0]["message"] == "Linting found 3 issue(s)"
        assert "line too long" in result.errors[0]["output"]

    def test_run_limits_output_length(self, linting_config, temp_project_dir, mock_runner):
        """Test run() limits output length."""
        checker = LintingChecker(
            linting_config, temp_project_dir, language="python", runner=mock_runner
        )

        long_output = "x" * 1000

        mock_runner.run.return_value = CommandResult(
            returncode=5,
            stdout=long_output,
            stderr="",
            command=["ruff"],
            duration_seconds=0.5,
        )

        result = checker.run()

        assert len(result.errors[0]["output"]) <= 500
        assert len(result.info["output"]) <= 1000


class TestLintingCheckerDifferentLanguages:
    """Tests for different language support."""

    def test_run_javascript_linting(self, linting_config, temp_project_dir, mock_runner):
        """Test run() for JavaScript linting."""
        checker = LintingChecker(
            linting_config, temp_project_dir, language="javascript", runner=mock_runner
        )

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="No errors",
            stderr="",
            command=["eslint"],
            duration_seconds=0.5,
        )

        result = checker.run()

        assert result.passed is True
        call_args = mock_runner.run.call_args[0][0]
        assert "eslint" in call_args

    def test_run_typescript_linting(self, linting_config, temp_project_dir, mock_runner):
        """Test run() for TypeScript linting."""
        checker = LintingChecker(
            linting_config, temp_project_dir, language="typescript", runner=mock_runner
        )

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="No errors",
            stderr="",
            command=["eslint"],
            duration_seconds=0.5,
        )

        result = checker.run()

        assert result.passed is True
        call_args = mock_runner.run.call_args[0][0]
        assert "eslint" in call_args
