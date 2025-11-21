"""Unit tests for tests.py TestRunner.

Tests for the TestRunner class which executes tests using pytest, Jest,
or other test frameworks and validates coverage.
"""

import json
from unittest.mock import Mock, patch

import pytest

from solokit.core.command_runner import CommandResult, CommandRunner
from solokit.quality.checkers.tests import ExecutionChecker


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project directory."""
    return tmp_path


@pytest.fixture
def mock_runner():
    """Create a mock CommandRunner."""
    return Mock(spec=CommandRunner)


@pytest.fixture
def test_config():
    """Standard test execution config."""
    return {
        "enabled": True,
        "coverage_threshold": 80,
        "commands": {
            "python": "pytest --cov=src --cov-report=json",
            "javascript": "npm test",
            "typescript": "npm test",
        },
    }


class TestTestRunnerInit:
    """Tests for TestRunner initialization."""

    def test_init_with_defaults(self, test_config, temp_project_dir):
        """Test initialization with default parameters."""
        runner = ExecutionChecker(test_config, temp_project_dir)

        assert runner.config == test_config
        assert runner.project_root == temp_project_dir
        assert runner.runner is not None
        assert isinstance(runner.runner, CommandRunner)

    def test_init_with_custom_runner(self, test_config, temp_project_dir, mock_runner):
        """Test initialization with custom runner."""
        runner = ExecutionChecker(test_config, temp_project_dir, runner=mock_runner)

        assert runner.runner is mock_runner

    def test_init_with_explicit_language(self, test_config, temp_project_dir):
        """Test initialization with explicit language."""
        runner = ExecutionChecker(test_config, temp_project_dir, language="javascript")

        assert runner.language == "javascript"

    def test_init_detects_python_from_pyproject(self, test_config, temp_project_dir):
        """Test language detection for Python via pyproject.toml."""
        (temp_project_dir / "pyproject.toml").touch()

        runner = ExecutionChecker(test_config, temp_project_dir)

        assert runner.language == "python"

    def test_init_detects_python_from_setup_py(self, test_config, temp_project_dir):
        """Test language detection for Python via setup.py."""
        (temp_project_dir / "setup.py").touch()

        runner = ExecutionChecker(test_config, temp_project_dir)

        assert runner.language == "python"

    def test_init_detects_javascript_from_package_json(self, test_config, temp_project_dir):
        """Test language detection for JavaScript via package.json."""
        (temp_project_dir / "package.json").touch()

        runner = ExecutionChecker(test_config, temp_project_dir)

        assert runner.language == "javascript"

    def test_init_detects_typescript_from_tsconfig(self, test_config, temp_project_dir):
        """Test language detection for TypeScript."""
        (temp_project_dir / "package.json").touch()
        (temp_project_dir / "tsconfig.json").touch()

        runner = ExecutionChecker(test_config, temp_project_dir)

        assert runner.language == "typescript"

    def test_init_defaults_to_python(self, test_config, temp_project_dir):
        """Test default language is Python."""
        runner = ExecutionChecker(test_config, temp_project_dir)

        assert runner.language == "python"


class TestTestRunnerInterface:
    """Tests for TestRunner interface methods."""

    def test_name_returns_tests(self, test_config, temp_project_dir):
        """Test name() returns 'tests'."""
        runner = ExecutionChecker(test_config, temp_project_dir)

        assert runner.name() == "tests"

    def test_is_enabled_returns_true_by_default(self, temp_project_dir):
        """Test is_enabled() returns True by default."""
        config = {}
        runner = ExecutionChecker(config, temp_project_dir)

        assert runner.is_enabled() is True

    def test_is_enabled_returns_config_value(self, temp_project_dir):
        """Test is_enabled() returns config value."""
        config = {"enabled": False}
        runner = ExecutionChecker(config, temp_project_dir)

        assert runner.is_enabled() is False


class TestTestRunnerRun:
    """Tests for TestRunner.run() method."""

    def test_run_returns_skipped_when_disabled(self, temp_project_dir):
        """Test run() returns skipped result when disabled."""
        config = {"enabled": False}
        runner = ExecutionChecker(config, temp_project_dir)

        result = runner.run()

        assert result.checker_name == "tests"
        assert result.passed is True
        assert result.status == "skipped"

    def test_run_returns_skipped_when_no_command_for_language(self, temp_project_dir, mock_runner):
        """Test run() returns skipped when no command configured."""
        config = {"enabled": True, "commands": {}}
        runner = ExecutionChecker(config, temp_project_dir, language="python", runner=mock_runner)

        result = runner.run()

        assert result.status == "skipped"
        assert result.info["reason"] == "no command for python"

    def test_run_executes_test_command(self, test_config, temp_project_dir, mock_runner):
        """Test run() executes test command."""
        runner = ExecutionChecker(
            test_config, temp_project_dir, language="python", runner=mock_runner
        )

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="Tests passed",
            stderr="",
            command=["pytest"],
            duration_seconds=1.5,
        )

        with patch.object(runner, "_parse_coverage", return_value=85.0):
            _ = runner.run()

        mock_runner.run.assert_called_once()
        call_args = mock_runner.run.call_args[0][0]
        assert "pytest" in call_args

    def test_run_passes_when_tests_pass_and_coverage_met(
        self, test_config, temp_project_dir, mock_runner
    ):
        """Test run() passes when tests pass and coverage meets threshold."""
        runner = ExecutionChecker(
            test_config, temp_project_dir, language="python", runner=mock_runner
        )

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="Tests passed",
            stderr="",
            command=["pytest"],
            duration_seconds=1.5,
        )

        with patch.object(runner, "_parse_coverage", return_value=85.0):
            result = runner.run()

        assert result.passed is True
        assert result.status == "passed"
        assert result.info["coverage"] == 85.0

    def test_run_fails_when_tests_fail(self, test_config, temp_project_dir, mock_runner):
        """Test run() fails when tests fail."""
        runner = ExecutionChecker(
            test_config, temp_project_dir, language="python", runner=mock_runner
        )

        mock_runner.run.return_value = CommandResult(
            returncode=1,
            stdout="",
            stderr="Test failed",
            command=["pytest"],
            duration_seconds=1.5,
        )

        with patch.object(runner, "_parse_coverage", return_value=85.0):
            result = runner.run()

        assert result.passed is False
        assert result.status == "failed"
        assert len(result.errors) > 0

    def test_run_fails_when_coverage_below_threshold(
        self, test_config, temp_project_dir, mock_runner
    ):
        """Test run() fails when coverage below threshold."""
        runner = ExecutionChecker(
            test_config, temp_project_dir, language="python", runner=mock_runner
        )

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="Tests passed",
            stderr="",
            command=["pytest"],
            duration_seconds=1.5,
        )

        with patch.object(runner, "_parse_coverage", return_value=75.0):
            result = runner.run()

        assert result.passed is False
        assert result.status == "failed"
        assert any("Coverage" in str(e) for e in result.errors)

    def test_run_handles_timeout(self, test_config, temp_project_dir, mock_runner):
        """Test run() handles test execution timeout."""
        runner = ExecutionChecker(
            test_config, temp_project_dir, language="python", runner=mock_runner
        )

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="",
            stderr="",
            command=["pytest"],
            duration_seconds=1200.0,
            timed_out=True,
        )

        result = runner.run()

        assert result.passed is False
        assert result.status == "failed"
        assert "timeout" in result.info["reason"]

    def test_run_handles_tool_not_found(self, test_config, temp_project_dir, mock_runner):
        """Test run() handles test tool not found."""
        runner = ExecutionChecker(
            test_config, temp_project_dir, language="python", runner=mock_runner
        )

        mock_runner.run.return_value = CommandResult(
            returncode=-1,
            stdout="",
            stderr="pytest: not found",
            command=["pytest"],
            duration_seconds=0.1,
        )

        result = runner.run()

        assert result.status == "skipped"
        assert "not available" in result.info["reason"]

    def test_run_handles_no_tests_collected(self, test_config, temp_project_dir, mock_runner):
        """Test run() handles exit code 5 (no tests collected)."""
        runner = ExecutionChecker(
            test_config, temp_project_dir, language="python", runner=mock_runner
        )

        mock_runner.run.return_value = CommandResult(
            returncode=5, stdout="", stderr="", command=["pytest"], duration_seconds=0.5
        )

        result = runner.run()

        assert result.status == "skipped"
        assert result.info["reason"] == "no tests collected"
        assert result.passed is True

    def test_run_includes_execution_time(self, test_config, temp_project_dir, mock_runner):
        """Test run() includes execution time in result."""
        runner = ExecutionChecker(
            test_config, temp_project_dir, language="python", runner=mock_runner
        )

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="Tests passed",
            stderr="",
            command=["pytest"],
            duration_seconds=1.5,
        )

        with patch.object(runner, "_parse_coverage", return_value=85.0):
            result = runner.run()

        assert result.execution_time > 0

    def test_run_limits_error_output(self, test_config, temp_project_dir, mock_runner):
        """Test run() limits error output length."""
        runner = ExecutionChecker(
            test_config, temp_project_dir, language="python", runner=mock_runner
        )

        long_stderr = "x" * 1000

        mock_runner.run.return_value = CommandResult(
            returncode=1,
            stdout="",
            stderr=long_stderr,
            command=["pytest"],
            duration_seconds=1.5,
        )

        with patch.object(runner, "_parse_coverage", return_value=85.0):
            result = runner.run()

        error_output = result.errors[0]["output"]
        assert len(error_output) <= 500


class TestTestRunnerCoverageParsing:
    """Tests for coverage parsing."""

    def test_parse_coverage_python_reads_coverage_json(self, test_config, temp_project_dir):
        """Test _parse_coverage reads Python coverage.json file."""
        runner = ExecutionChecker(test_config, temp_project_dir, language="python")

        coverage_data = {"totals": {"percent_covered": 87.5}}
        coverage_file = temp_project_dir / "coverage.json"
        coverage_file.write_text(json.dumps(coverage_data))

        result = runner._parse_coverage()

        assert result == 87.5

    def test_parse_coverage_python_returns_none_when_file_missing(
        self, test_config, temp_project_dir
    ):
        """Test _parse_coverage returns None when coverage.json missing."""
        runner = ExecutionChecker(test_config, temp_project_dir, language="python")

        result = runner._parse_coverage()

        assert result is None

    def test_parse_coverage_javascript_reads_coverage_summary(self, test_config, temp_project_dir):
        """Test _parse_coverage reads JavaScript coverage-summary.json."""
        runner = ExecutionChecker(test_config, temp_project_dir, language="javascript")

        coverage_data = {"total": {"lines": {"pct": 92.3}}}
        coverage_dir = temp_project_dir / "coverage"
        coverage_dir.mkdir()
        coverage_file = coverage_dir / "coverage-summary.json"
        coverage_file.write_text(json.dumps(coverage_data))

        result = runner._parse_coverage()

        assert result == 92.3

    def test_parse_coverage_typescript_reads_coverage_summary(self, test_config, temp_project_dir):
        """Test _parse_coverage reads TypeScript coverage-summary.json."""
        runner = ExecutionChecker(test_config, temp_project_dir, language="typescript")

        coverage_data = {"total": {"lines": {"pct": 88.7}}}
        coverage_dir = temp_project_dir / "coverage"
        coverage_dir.mkdir()
        coverage_file = coverage_dir / "coverage-summary.json"
        coverage_file.write_text(json.dumps(coverage_data))

        result = runner._parse_coverage()

        assert result == 88.7

    def test_parse_coverage_handles_json_decode_error(self, test_config, temp_project_dir):
        """Test _parse_coverage handles JSON decode errors gracefully."""
        runner = ExecutionChecker(test_config, temp_project_dir, language="python")

        coverage_file = temp_project_dir / "coverage.json"
        coverage_file.write_text("invalid json")

        result = runner._parse_coverage()

        assert result is None

    def test_parse_coverage_handles_file_read_error(self, test_config, temp_project_dir):
        """Test _parse_coverage handles file read errors gracefully."""
        runner = ExecutionChecker(test_config, temp_project_dir, language="python")

        with patch("builtins.open", side_effect=OSError("Permission denied")):
            result = runner._parse_coverage()

        assert result is None

    def test_parse_coverage_returns_none_for_unsupported_language(
        self, test_config, temp_project_dir
    ):
        """Test _parse_coverage returns None for unsupported language."""
        runner = ExecutionChecker(test_config, temp_project_dir, language="ruby")

        result = runner._parse_coverage()

        assert result is None


class TestTestRunnerExitCodes:
    """Tests for handling pytest exit codes."""

    def test_run_handles_exit_code_0_tests_passed(self, test_config, temp_project_dir, mock_runner):
        """Test run() handles exit code 0 (all tests passed)."""
        runner = ExecutionChecker(
            test_config, temp_project_dir, language="python", runner=mock_runner
        )

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="Tests passed",
            stderr="",
            command=["pytest"],
            duration_seconds=1.0,
        )

        with patch.object(runner, "_parse_coverage", return_value=85.0):
            result = runner.run()

        assert result.passed is True
        assert result.status == "passed"

    def test_run_handles_exit_code_1_tests_failed(self, test_config, temp_project_dir, mock_runner):
        """Test run() handles exit code 1 (some tests failed)."""
        runner = ExecutionChecker(
            test_config, temp_project_dir, language="python", runner=mock_runner
        )

        mock_runner.run.return_value = CommandResult(
            returncode=1,
            stdout="",
            stderr="Tests failed",
            command=["pytest"],
            duration_seconds=1.0,
        )

        with patch.object(runner, "_parse_coverage", return_value=85.0):
            result = runner.run()

        assert result.passed is False
        assert result.status == "failed"

    def test_run_handles_exit_code_2_interrupted(self, test_config, temp_project_dir, mock_runner):
        """Test run() handles exit code 2 (test execution interrupted)."""
        runner = ExecutionChecker(
            test_config, temp_project_dir, language="python", runner=mock_runner
        )

        mock_runner.run.return_value = CommandResult(
            returncode=2,
            stdout="",
            stderr="Interrupted",
            command=["pytest"],
            duration_seconds=0.5,
        )

        with patch.object(runner, "_parse_coverage", return_value=85.0):
            result = runner.run()

        assert result.passed is False
        assert result.status == "failed"

    def test_run_handles_exit_code_5_no_tests_collected(
        self, test_config, temp_project_dir, mock_runner
    ):
        """Test run() handles exit code 5 (no tests collected) as skipped."""
        runner = ExecutionChecker(
            test_config, temp_project_dir, language="python", runner=mock_runner
        )

        mock_runner.run.return_value = CommandResult(
            returncode=5, stdout="", stderr="", command=["pytest"], duration_seconds=0.1
        )

        result = runner.run()

        assert result.status == "skipped"
        assert result.passed is True


class TestTestRunnerCustomThreshold:
    """Tests for custom coverage threshold."""

    def test_run_uses_custom_threshold(self, temp_project_dir, mock_runner):
        """Test run() uses custom coverage threshold."""
        config = {
            "enabled": True,
            "coverage_threshold": 95,
            "commands": {"python": "pytest"},
        }
        runner = ExecutionChecker(config, temp_project_dir, language="python", runner=mock_runner)

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="Tests passed",
            stderr="",
            command=["pytest"],
            duration_seconds=1.0,
        )

        with patch.object(runner, "_parse_coverage", return_value=92.0):
            result = runner.run()

        assert result.passed is False
        assert result.info["threshold"] == 95

    def test_run_passes_with_coverage_above_custom_threshold(self, temp_project_dir, mock_runner):
        """Test run() passes when coverage above custom threshold."""
        config = {
            "enabled": True,
            "coverage_threshold": 70,
            "commands": {"python": "pytest"},
        }
        runner = ExecutionChecker(config, temp_project_dir, language="python", runner=mock_runner)

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="Tests passed",
            stderr="",
            command=["pytest"],
            duration_seconds=1.0,
        )

        with patch.object(runner, "_parse_coverage", return_value=75.0):
            result = runner.run()

        assert result.passed is True
        assert result.info["threshold"] == 70
