"""Unit tests for formatting.py FormattingChecker.

Tests for the FormattingChecker class which runs formatters like black, prettier.
"""

from unittest.mock import Mock

import pytest
from solokit.core.command_runner import CommandResult, CommandRunner
from solokit.quality.checkers.formatting import FormattingChecker


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project directory."""
    return tmp_path


@pytest.fixture
def mock_runner():
    """Create a mock CommandRunner."""
    return Mock(spec=CommandRunner)


@pytest.fixture
def formatting_config():
    """Standard formatting config."""
    return {
        "enabled": True,
        "required": False,
        "auto_fix": False,
        "commands": {
            "python": "black src",
            "javascript": "prettier .",
            "typescript": "prettier .",
        },
    }


class TestFormattingCheckerInit:
    """Tests for FormattingChecker initialization."""

    def test_init_with_defaults(self, formatting_config, temp_project_dir):
        """Test initialization with default parameters."""
        checker = FormattingChecker(formatting_config, temp_project_dir)

        assert checker.config == formatting_config
        assert checker.project_root == temp_project_dir
        assert checker.runner is not None
        assert isinstance(checker.runner, CommandRunner)
        assert checker.auto_fix is False

    def test_init_with_custom_runner(self, formatting_config, temp_project_dir, mock_runner):
        """Test initialization with custom runner."""
        checker = FormattingChecker(formatting_config, temp_project_dir, runner=mock_runner)

        assert checker.runner is mock_runner

    def test_init_with_explicit_language(self, formatting_config, temp_project_dir):
        """Test initialization with explicit language."""
        checker = FormattingChecker(formatting_config, temp_project_dir, language="javascript")

        assert checker.language == "javascript"

    def test_init_with_auto_fix_from_config(self, temp_project_dir):
        """Test initialization with auto_fix from config."""
        config = {"enabled": True, "auto_fix": True, "commands": {"python": "black"}}
        checker = FormattingChecker(config, temp_project_dir)

        assert checker.auto_fix is True

    def test_init_with_auto_fix_override(self, temp_project_dir):
        """Test initialization with auto_fix override."""
        config = {"enabled": True, "auto_fix": False, "commands": {"python": "black"}}
        checker = FormattingChecker(config, temp_project_dir, auto_fix=True)

        assert checker.auto_fix is True

    def test_init_detects_python_from_pyproject(self, formatting_config, temp_project_dir):
        """Test language detection for Python via pyproject.toml."""
        (temp_project_dir / "pyproject.toml").touch()

        checker = FormattingChecker(formatting_config, temp_project_dir)

        assert checker.language == "python"

    def test_init_detects_javascript_from_package_json(self, formatting_config, temp_project_dir):
        """Test language detection for JavaScript via package.json."""
        (temp_project_dir / "package.json").touch()

        checker = FormattingChecker(formatting_config, temp_project_dir)

        assert checker.language == "javascript"

    def test_init_defaults_to_python(self, formatting_config, temp_project_dir):
        """Test default language is Python."""
        checker = FormattingChecker(formatting_config, temp_project_dir)

        assert checker.language == "python"


class TestFormattingCheckerInterface:
    """Tests for FormattingChecker interface methods."""

    def test_name_returns_formatting(self, formatting_config, temp_project_dir):
        """Test name() returns 'formatting'."""
        checker = FormattingChecker(formatting_config, temp_project_dir)

        assert checker.name() == "formatting"

    def test_is_enabled_returns_true_by_default(self, temp_project_dir):
        """Test is_enabled() returns True by default."""
        config = {}
        checker = FormattingChecker(config, temp_project_dir)

        assert checker.is_enabled() is True

    def test_is_enabled_returns_config_value(self, temp_project_dir):
        """Test is_enabled() returns config value."""
        config = {"enabled": False}
        checker = FormattingChecker(config, temp_project_dir)

        assert checker.is_enabled() is False


class TestFormattingCheckerRun:
    """Tests for FormattingChecker.run() method."""

    def test_run_returns_skipped_when_disabled(self, temp_project_dir):
        """Test run() returns skipped result when disabled."""
        config = {"enabled": False}
        checker = FormattingChecker(config, temp_project_dir)

        result = checker.run()

        assert result.checker_name == "formatting"
        assert result.passed is True
        assert result.status == "skipped"

    def test_run_returns_skipped_when_no_command_for_language(self, temp_project_dir, mock_runner):
        """Test run() returns skipped when no command configured."""
        config = {"enabled": True, "commands": {}}
        checker = FormattingChecker(config, temp_project_dir, language="python", runner=mock_runner)

        result = checker.run()

        assert result.status == "skipped"
        assert result.info["reason"] == "no command for python"

    def test_run_executes_formatting_command(
        self, formatting_config, temp_project_dir, mock_runner
    ):
        """Test run() executes formatting command."""
        checker = FormattingChecker(
            formatting_config, temp_project_dir, language="python", runner=mock_runner
        )

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="All done!",
            stderr="",
            command=["black"],
            duration_seconds=0.5,
        )

        _ = checker.run()

        mock_runner.run.assert_called_once()
        call_args = mock_runner.run.call_args[0][0]
        assert "black" in call_args

    def test_run_passes_when_formatting_correct(
        self, formatting_config, temp_project_dir, mock_runner
    ):
        """Test run() passes when formatting is correct."""
        checker = FormattingChecker(
            formatting_config, temp_project_dir, language="python", runner=mock_runner
        )

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="All done!",
            stderr="",
            command=["black"],
            duration_seconds=0.5,
        )

        result = checker.run()

        assert result.passed is True
        assert result.status == "passed"

    def test_run_fails_when_formatting_issues_found(
        self, formatting_config, temp_project_dir, mock_runner
    ):
        """Test run() fails when formatting issues found."""
        checker = FormattingChecker(
            formatting_config, temp_project_dir, language="python", runner=mock_runner
        )

        mock_runner.run.return_value = CommandResult(
            returncode=1,
            stdout="Would reformat 5 files",
            stderr="",
            command=["black"],
            duration_seconds=0.5,
        )

        result = checker.run()

        assert result.passed is False
        assert result.status == "failed"
        assert len(result.errors) > 0

    def test_run_adds_check_flag_for_python_when_not_auto_fix(
        self, formatting_config, temp_project_dir, mock_runner
    ):
        """Test run() adds --check flag for Python when auto_fix disabled."""
        checker = FormattingChecker(
            formatting_config,
            temp_project_dir,
            language="python",
            auto_fix=False,
            runner=mock_runner,
        )

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="All done!",
            stderr="",
            command=["black"],
            duration_seconds=0.5,
        )

        _ = checker.run()

        call_args = mock_runner.run.call_args[0][0]
        assert "--check" in " ".join(call_args)

    def test_run_no_check_flag_for_python_when_auto_fix(
        self, formatting_config, temp_project_dir, mock_runner
    ):
        """Test run() does not add --check flag for Python when auto_fix enabled."""
        checker = FormattingChecker(
            formatting_config,
            temp_project_dir,
            language="python",
            auto_fix=True,
            runner=mock_runner,
        )

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="Reformatted",
            stderr="",
            command=["black"],
            duration_seconds=0.5,
        )

        _ = checker.run()

        call_args = mock_runner.run.call_args[0][0]
        assert "--check" not in " ".join(call_args)

    def test_run_adds_write_flag_for_javascript_when_auto_fix(
        self, formatting_config, temp_project_dir, mock_runner
    ):
        """Test run() adds --write flag for JavaScript when auto_fix enabled."""
        checker = FormattingChecker(
            formatting_config,
            temp_project_dir,
            language="javascript",
            auto_fix=True,
            runner=mock_runner,
        )

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="Formatted",
            stderr="",
            command=["prettier"],
            duration_seconds=0.5,
        )

        _ = checker.run()

        call_args = mock_runner.run.call_args[0][0]
        assert "--write" in " ".join(call_args)

    def test_run_adds_check_flag_for_javascript_when_not_auto_fix(
        self, formatting_config, temp_project_dir, mock_runner
    ):
        """Test run() adds --check flag for JavaScript when auto_fix disabled."""
        checker = FormattingChecker(
            formatting_config,
            temp_project_dir,
            language="javascript",
            auto_fix=False,
            runner=mock_runner,
        )

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="All matched files use Prettier code style!",
            stderr="",
            command=["prettier"],
            duration_seconds=0.5,
        )

        _ = checker.run()

        call_args = mock_runner.run.call_args[0][0]
        assert "--check" in " ".join(call_args)

    def test_run_includes_execution_time(self, formatting_config, temp_project_dir, mock_runner):
        """Test run() includes execution time in result."""
        checker = FormattingChecker(
            formatting_config, temp_project_dir, language="python", runner=mock_runner
        )

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="All done!",
            stderr="",
            command=["black"],
            duration_seconds=0.5,
        )

        result = checker.run()

        assert result.execution_time > 0

    def test_run_includes_formatted_info(self, formatting_config, temp_project_dir, mock_runner):
        """Test run() includes formatted info in result."""
        checker = FormattingChecker(
            formatting_config,
            temp_project_dir,
            language="python",
            auto_fix=True,
            runner=mock_runner,
        )

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="Reformatted",
            stderr="",
            command=["black"],
            duration_seconds=0.5,
        )

        result = checker.run()

        assert result.info["formatted"] is True


class TestFormattingCheckerTimeout:
    """Tests for timeout handling."""

    def test_run_handles_timeout_not_required(self, temp_project_dir, mock_runner):
        """Test run() handles timeout when formatting not required."""
        config = {"enabled": True, "required": False, "commands": {"python": "black"}}
        checker = FormattingChecker(config, temp_project_dir, language="python", runner=mock_runner)

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="",
            stderr="",
            command=["black"],
            duration_seconds=120.0,
            timed_out=True,
        )

        result = checker.run()

        assert result.status == "skipped"
        assert result.info["reason"] == "timeout"
        assert result.passed is True

    def test_run_handles_timeout_required(self, temp_project_dir, mock_runner):
        """Test run() handles timeout when formatting required."""
        config = {"enabled": True, "required": True, "commands": {"python": "black"}}
        checker = FormattingChecker(config, temp_project_dir, language="python", runner=mock_runner)

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="",
            stderr="",
            command=["black"],
            duration_seconds=120.0,
            timed_out=True,
        )

        result = checker.run()

        assert result.status == "failed"
        assert result.passed is False
        assert "timeout" in result.info["reason"]


class TestFormattingCheckerToolNotFound:
    """Tests for missing tool handling."""

    def test_run_handles_tool_not_found_not_required(self, temp_project_dir, mock_runner):
        """Test run() handles tool not found when formatting not required."""
        config = {"enabled": True, "required": False, "commands": {"python": "black"}}
        checker = FormattingChecker(config, temp_project_dir, language="python", runner=mock_runner)

        mock_runner.run.return_value = CommandResult(
            returncode=-1, stdout="", stderr="", command=["black"], duration_seconds=0.1
        )

        result = checker.run()

        assert result.status == "skipped"
        assert result.info["reason"] == "formatting tool not available"

    def test_run_handles_tool_not_found_required(self, temp_project_dir, mock_runner):
        """Test run() handles tool not found when formatting required."""
        config = {"enabled": True, "required": True, "commands": {"python": "black"}}
        checker = FormattingChecker(config, temp_project_dir, language="python", runner=mock_runner)

        mock_runner.run.return_value = CommandResult(
            returncode=-1, stdout="", stderr="", command=["black"], duration_seconds=0.1
        )

        result = checker.run()

        assert result.status == "failed"
        assert result.passed is False
        assert "not found" in str(result.errors[0])


class TestFormattingCheckerErrorOutput:
    """Tests for error output handling."""

    def test_run_includes_error_output(self, formatting_config, temp_project_dir, mock_runner):
        """Test run() includes error output in result."""
        checker = FormattingChecker(
            formatting_config, temp_project_dir, language="python", runner=mock_runner
        )

        mock_runner.run.return_value = CommandResult(
            returncode=1,
            stdout="Would reformat file1.py\nWould reformat file2.py",
            stderr="",
            command=["black"],
            duration_seconds=0.5,
        )

        result = checker.run()

        assert result.errors[0]["message"] == "Code formatting issues found"
        assert "reformat" in result.errors[0]["output"]

    def test_run_limits_output_length(self, formatting_config, temp_project_dir, mock_runner):
        """Test run() limits output length."""
        checker = FormattingChecker(
            formatting_config, temp_project_dir, language="python", runner=mock_runner
        )

        long_output = "x" * 1000

        mock_runner.run.return_value = CommandResult(
            returncode=1,
            stdout=long_output,
            stderr="",
            command=["black"],
            duration_seconds=0.5,
        )

        result = checker.run()

        assert len(result.errors[0]["output"]) <= 500
        assert len(result.info["output"]) <= 1000


class TestFormattingCheckerDifferentLanguages:
    """Tests for different language support."""

    def test_run_javascript_formatting(self, formatting_config, temp_project_dir, mock_runner):
        """Test run() for JavaScript formatting."""
        checker = FormattingChecker(
            formatting_config,
            temp_project_dir,
            language="javascript",
            runner=mock_runner,
        )

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="All matched files use Prettier code style!",
            stderr="",
            command=["prettier"],
            duration_seconds=0.5,
        )

        result = checker.run()

        assert result.passed is True
        call_args = mock_runner.run.call_args[0][0]
        assert "prettier" in call_args

    def test_run_typescript_formatting(self, formatting_config, temp_project_dir, mock_runner):
        """Test run() for TypeScript formatting."""
        checker = FormattingChecker(
            formatting_config,
            temp_project_dir,
            language="typescript",
            runner=mock_runner,
        )

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="All matched files use Prettier code style!",
            stderr="",
            command=["prettier"],
            duration_seconds=0.5,
        )

        result = checker.run()

        assert result.passed is True
        call_args = mock_runner.run.call_args[0][0]
        assert "prettier" in call_args
