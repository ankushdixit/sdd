"""Unit tests for security.py SecurityChecker.

Tests for the SecurityChecker class which runs security scans using Bandit,
Safety (Python), or npm audit (JavaScript/TypeScript).
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from solokit.core.command_runner import CommandResult, CommandRunner
from solokit.quality.checkers.security import SecurityChecker


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project directory."""
    return tmp_path


@pytest.fixture
def mock_runner():
    """Create a mock CommandRunner."""
    return Mock(spec=CommandRunner)


@pytest.fixture
def python_config():
    """Standard Python security config."""
    return {
        "enabled": True,
        "fail_on": "high",
    }


@pytest.fixture
def js_config():
    """Standard JavaScript security config."""
    return {
        "enabled": True,
        "fail_on": "medium",
    }


class TestSecurityCheckerInit:
    """Tests for SecurityChecker initialization."""

    def test_init_with_defaults(self, python_config, temp_project_dir):
        """Test initialization with default parameters."""
        checker = SecurityChecker(python_config, temp_project_dir)

        assert checker.config == python_config
        assert checker.project_root == temp_project_dir
        assert checker.runner is not None
        assert isinstance(checker.runner, CommandRunner)

    def test_init_with_custom_runner(self, python_config, temp_project_dir, mock_runner):
        """Test initialization with custom runner."""
        checker = SecurityChecker(python_config, temp_project_dir, runner=mock_runner)

        assert checker.runner is mock_runner

    def test_init_with_explicit_language(self, python_config, temp_project_dir):
        """Test initialization with explicit language."""
        checker = SecurityChecker(python_config, temp_project_dir, language="javascript")

        assert checker.language == "javascript"

    def test_init_detects_python_from_pyproject(self, python_config, temp_project_dir):
        """Test language detection for Python via pyproject.toml."""
        (temp_project_dir / "pyproject.toml").touch()

        checker = SecurityChecker(python_config, temp_project_dir)

        assert checker.language == "python"

    def test_init_detects_python_from_setup_py(self, python_config, temp_project_dir):
        """Test language detection for Python via setup.py."""
        (temp_project_dir / "setup.py").touch()

        checker = SecurityChecker(python_config, temp_project_dir)

        assert checker.language == "python"

    def test_init_detects_javascript_from_package_json(self, python_config, temp_project_dir):
        """Test language detection for JavaScript via package.json."""
        (temp_project_dir / "package.json").touch()

        checker = SecurityChecker(python_config, temp_project_dir)

        assert checker.language == "javascript"

    def test_init_detects_typescript_from_tsconfig(self, python_config, temp_project_dir):
        """Test language detection for TypeScript."""
        (temp_project_dir / "package.json").touch()
        (temp_project_dir / "tsconfig.json").touch()

        checker = SecurityChecker(python_config, temp_project_dir)

        assert checker.language == "typescript"

    def test_init_defaults_to_python(self, python_config, temp_project_dir):
        """Test default language is Python."""
        checker = SecurityChecker(python_config, temp_project_dir)

        assert checker.language == "python"


class TestSecurityCheckerInterface:
    """Tests for SecurityChecker interface methods."""

    def test_name_returns_security(self, python_config, temp_project_dir):
        """Test name() returns 'security'."""
        checker = SecurityChecker(python_config, temp_project_dir)

        assert checker.name() == "security"

    def test_is_enabled_returns_true_by_default(self, temp_project_dir):
        """Test is_enabled() returns True by default."""
        config = {}
        checker = SecurityChecker(config, temp_project_dir)

        assert checker.is_enabled() is True

    def test_is_enabled_returns_config_value(self, temp_project_dir):
        """Test is_enabled() returns config value."""
        config = {"enabled": False}
        checker = SecurityChecker(config, temp_project_dir)

        assert checker.is_enabled() is False


class TestSecurityCheckerRun:
    """Tests for SecurityChecker.run() method."""

    def test_run_returns_skipped_when_disabled(self, temp_project_dir):
        """Test run() returns skipped result when disabled."""
        config = {"enabled": False}
        checker = SecurityChecker(config, temp_project_dir)

        result = checker.run()

        assert result.checker_name == "security"
        assert result.passed is True
        assert result.status == "skipped"

    def test_run_python_calls_scan_python(self, python_config, temp_project_dir, mock_runner):
        """Test run() calls _scan_python for Python projects."""
        (temp_project_dir / "pyproject.toml").touch()
        checker = SecurityChecker(python_config, temp_project_dir, runner=mock_runner)

        with patch.object(
            checker,
            "_scan_python",
            return_value={"vulnerabilities": [], "by_severity": {}},
        ):
            result = checker.run()

            checker._scan_python.assert_called_once()
            assert result.checker_name == "security"

    def test_run_javascript_calls_scan_javascript(self, js_config, temp_project_dir, mock_runner):
        """Test run() calls _scan_javascript for JS projects."""
        (temp_project_dir / "package.json").touch()
        checker = SecurityChecker(js_config, temp_project_dir, runner=mock_runner)

        with patch.object(
            checker,
            "_scan_javascript",
            return_value={"vulnerabilities": [], "by_severity": {}},
        ):
            result = checker.run()

            checker._scan_javascript.assert_called_once()
            assert result.checker_name == "security"

    def test_run_passes_with_no_vulnerabilities(self, python_config, temp_project_dir, mock_runner):
        """Test run() passes when no vulnerabilities found."""
        checker = SecurityChecker(
            python_config, temp_project_dir, language="python", runner=mock_runner
        )

        with patch.object(
            checker,
            "_scan_python",
            return_value={"vulnerabilities": [], "by_severity": {}},
        ):
            result = checker.run()

            assert result.passed is True
            assert result.status == "passed"

    def test_run_fails_with_high_severity_vulnerabilities(
        self, python_config, temp_project_dir, mock_runner
    ):
        """Test run() fails with high severity vulnerabilities."""
        checker = SecurityChecker(
            python_config, temp_project_dir, language="python", runner=mock_runner
        )

        scan_results = {
            "vulnerabilities": [{"severity": "HIGH", "issue": "SQL injection"}],
            "by_severity": {"HIGH": 1},
        }

        with patch.object(checker, "_scan_python", return_value=scan_results):
            result = checker.run()

            assert result.passed is False
            assert result.status == "failed"

    def test_run_passes_with_low_severity_when_threshold_high(
        self, python_config, temp_project_dir, mock_runner
    ):
        """Test run() passes with low severity when threshold is high."""
        checker = SecurityChecker(
            python_config, temp_project_dir, language="python", runner=mock_runner
        )

        scan_results = {
            "vulnerabilities": [{"severity": "LOW", "issue": "Weak cipher"}],
            "by_severity": {"LOW": 1},
        }

        with patch.object(checker, "_scan_python", return_value=scan_results):
            result = checker.run()

            assert result.passed is True
            assert result.status == "passed"

    def test_run_fails_with_medium_severity_when_threshold_medium(
        self, temp_project_dir, mock_runner
    ):
        """Test run() fails with medium severity when threshold is medium."""
        config = {"enabled": True, "fail_on": "medium"}
        checker = SecurityChecker(config, temp_project_dir, language="python", runner=mock_runner)

        scan_results = {
            "vulnerabilities": [{"severity": "MEDIUM", "issue": "Weak hash"}],
            "by_severity": {"MEDIUM": 1},
        }

        with patch.object(checker, "_scan_python", return_value=scan_results):
            result = checker.run()

            assert result.passed is False
            assert result.status == "failed"

    def test_run_includes_execution_time(self, python_config, temp_project_dir, mock_runner):
        """Test run() includes execution time in result."""
        checker = SecurityChecker(
            python_config, temp_project_dir, language="python", runner=mock_runner
        )

        with patch.object(
            checker,
            "_scan_python",
            return_value={"vulnerabilities": [], "by_severity": {}},
        ):
            result = checker.run()

            assert result.execution_time > 0

    def test_run_skips_unsupported_language(self, python_config, temp_project_dir, mock_runner):
        """Test run() skips unsupported language."""
        checker = SecurityChecker(
            python_config, temp_project_dir, language="ruby", runner=mock_runner
        )

        result = checker.run()

        assert result.status == "skipped"
        assert result.info["reason"] == "unsupported language: ruby"


class TestSecurityCheckerBandit:
    """Tests for Bandit scanner."""

    def test_run_bandit_returns_none_when_no_src_dir(
        self, python_config, temp_project_dir, mock_runner
    ):
        """Test _run_bandit returns None when no src/ directory."""
        checker = SecurityChecker(python_config, temp_project_dir, runner=mock_runner)

        result = checker._run_bandit()

        assert result is None

    def test_run_bandit_executes_command(self, python_config, temp_project_dir, mock_runner):
        """Test _run_bandit executes bandit command."""
        (temp_project_dir / "src").mkdir()
        checker = SecurityChecker(python_config, temp_project_dir, runner=mock_runner)

        mock_runner.run.return_value = CommandResult(
            returncode=0, stdout="", stderr="", command=["bandit"], duration_seconds=0.5
        )

        with patch("tempfile.mkstemp", return_value=(1, "/tmp/bandit_report.json")):
            with patch("os.close"):
                with patch("builtins.open", create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = (
                        '{"results": []}'
                    )
                    with patch.object(Path, "exists", return_value=True):
                        with patch.object(Path, "unlink"):
                            _ = checker._run_bandit()

        mock_runner.run.assert_called_once()
        call_args = mock_runner.run.call_args[0][0]
        assert call_args[0] == "bandit"
        assert "-r" in call_args
        assert "-f" in call_args
        assert "json" in call_args

    def test_run_bandit_parses_json_report(self, python_config, temp_project_dir, mock_runner):
        """Test _run_bandit parses JSON report correctly."""
        (temp_project_dir / "src").mkdir()
        checker = SecurityChecker(python_config, temp_project_dir, runner=mock_runner)

        bandit_output = {
            "results": [
                {
                    "filename": "test.py",
                    "line_number": 10,
                    "issue_text": "Use of eval",
                    "issue_severity": "HIGH",
                    "issue_confidence": "HIGH",
                }
            ]
        }

        mock_runner.run.return_value = CommandResult(
            returncode=0, stdout="", stderr="", command=["bandit"], duration_seconds=0.5
        )

        with patch("tempfile.mkstemp", return_value=(1, "/tmp/bandit_report.json")):
            with patch("os.close"):
                with patch("builtins.open", create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(
                        bandit_output
                    )
                    with patch.object(Path, "exists", return_value=True):
                        with patch.object(Path, "unlink"):
                            result = checker._run_bandit()

        assert result == bandit_output

    def test_run_bandit_handles_json_decode_error(
        self, python_config, temp_project_dir, mock_runner
    ):
        """Test _run_bandit handles JSON decode errors gracefully."""
        (temp_project_dir / "src").mkdir()
        checker = SecurityChecker(python_config, temp_project_dir, runner=mock_runner)

        mock_runner.run.return_value = CommandResult(
            returncode=0, stdout="", stderr="", command=["bandit"], duration_seconds=0.5
        )

        with patch("tempfile.mkstemp", return_value=(1, "/tmp/bandit_report.json")):
            with patch("os.close"):
                with patch("builtins.open", create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = "invalid json"
                    with patch.object(Path, "exists", return_value=True):
                        with patch.object(Path, "unlink"):
                            result = checker._run_bandit()

        assert result is None

    def test_run_bandit_cleans_up_temp_file(self, python_config, temp_project_dir, mock_runner):
        """Test _run_bandit cleans up temporary file."""
        (temp_project_dir / "src").mkdir()
        checker = SecurityChecker(python_config, temp_project_dir, runner=mock_runner)

        mock_runner.run.return_value = CommandResult(
            returncode=0, stdout="", stderr="", command=["bandit"], duration_seconds=0.5
        )

        mock_unlink = Mock()

        with patch("tempfile.mkstemp", return_value=(1, "/tmp/bandit_report.json")):
            with patch("os.close"):
                with patch("builtins.open", create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = (
                        '{"results": []}'
                    )
                    with patch.object(Path, "exists", return_value=True):
                        with patch.object(Path, "unlink", mock_unlink):
                            _ = checker._run_bandit()

        mock_unlink.assert_called_once()


class TestSecurityCheckerSafety:
    """Tests for Safety scanner."""

    def test_run_safety_returns_empty_when_no_requirements(
        self, python_config, temp_project_dir, mock_runner
    ):
        """Test _run_safety returns empty list when no requirements.txt."""
        checker = SecurityChecker(python_config, temp_project_dir, runner=mock_runner)

        result = checker._run_safety()

        assert result == []

    def test_run_safety_executes_command(self, python_config, temp_project_dir, mock_runner):
        """Test _run_safety executes safety command."""
        (temp_project_dir / "requirements.txt").touch()
        checker = SecurityChecker(python_config, temp_project_dir, runner=mock_runner)

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="[]",
            stderr="",
            command=["safety"],
            duration_seconds=0.5,
        )

        _ = checker._run_safety()

        mock_runner.run.assert_called_once()
        call_args = mock_runner.run.call_args[0][0]
        assert call_args[0] == "safety"
        assert "check" in call_args
        assert "--json" in call_args

    def test_run_safety_parses_json_output(self, python_config, temp_project_dir, mock_runner):
        """Test _run_safety parses JSON output correctly."""
        (temp_project_dir / "requirements.txt").touch()
        checker = SecurityChecker(python_config, temp_project_dir, runner=mock_runner)

        safety_output = [
            {
                "package": "django",
                "version": "1.0",
                "vulnerability": "XSS",
                "severity": "high",
            }
        ]

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout=json.dumps(safety_output),
            stderr="",
            command=["safety"],
            duration_seconds=0.5,
        )

        result = checker._run_safety()

        assert result == safety_output

    def test_run_safety_handles_json_decode_error(
        self, python_config, temp_project_dir, mock_runner
    ):
        """Test _run_safety handles JSON decode errors gracefully."""
        (temp_project_dir / "requirements.txt").touch()
        checker = SecurityChecker(python_config, temp_project_dir, runner=mock_runner)

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="invalid json",
            stderr="",
            command=["safety"],
            duration_seconds=0.5,
        )

        result = checker._run_safety()

        assert result == []


class TestSecurityCheckerNpmAudit:
    """Tests for npm audit scanner."""

    def test_scan_javascript_returns_empty_when_no_package_json(
        self, js_config, temp_project_dir, mock_runner
    ):
        """Test _scan_javascript returns empty when no package.json."""
        checker = SecurityChecker(js_config, temp_project_dir, runner=mock_runner)

        result = checker._scan_javascript()

        assert result["vulnerabilities"] == []
        assert result["by_severity"] == {}

    def test_scan_javascript_executes_npm_audit(self, js_config, temp_project_dir, mock_runner):
        """Test _scan_javascript executes npm audit command."""
        (temp_project_dir / "package.json").touch()
        checker = SecurityChecker(js_config, temp_project_dir, runner=mock_runner)

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout='{"vulnerabilities": {}}',
            stderr="",
            command=["npm"],
            duration_seconds=0.5,
        )

        _ = checker._scan_javascript()

        mock_runner.run.assert_called_once()
        call_args = mock_runner.run.call_args[0][0]
        assert call_args[0] == "npm"
        assert "audit" in call_args
        assert "--json" in call_args

    def test_scan_javascript_parses_audit_output(self, js_config, temp_project_dir, mock_runner):
        """Test _scan_javascript parses npm audit output."""
        (temp_project_dir / "package.json").touch()
        checker = SecurityChecker(js_config, temp_project_dir, runner=mock_runner)

        audit_output = {
            "vulnerabilities": {
                "package1": {"severity": "high", "title": "XSS vulnerability"},
                "package2": {"severity": "low", "title": "Minor issue"},
            }
        }

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout=json.dumps(audit_output),
            stderr="",
            command=["npm"],
            duration_seconds=0.5,
        )

        result = checker._scan_javascript()

        assert result["npm_audit"] == audit_output
        assert result["by_severity"]["HIGH"] == 1
        assert result["by_severity"]["LOW"] == 1

    def test_scan_javascript_handles_json_decode_error(
        self, js_config, temp_project_dir, mock_runner
    ):
        """Test _scan_javascript handles JSON decode errors gracefully."""
        (temp_project_dir / "package.json").touch()
        checker = SecurityChecker(js_config, temp_project_dir, runner=mock_runner)

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="invalid json",
            stderr="",
            command=["npm"],
            duration_seconds=0.5,
        )

        result = checker._scan_javascript()

        assert result["vulnerabilities"] == []
        assert result["by_severity"] == {}


class TestSecurityCheckerPythonIntegration:
    """Integration tests for Python security scanning."""

    def test_scan_python_combines_bandit_and_safety(
        self, python_config, temp_project_dir, mock_runner
    ):
        """Test _scan_python combines Bandit and Safety results."""
        (temp_project_dir / "src").mkdir()
        (temp_project_dir / "requirements.txt").touch()
        checker = SecurityChecker(python_config, temp_project_dir, runner=mock_runner)

        bandit_output = {
            "results": [
                {
                    "filename": "test.py",
                    "line_number": 10,
                    "issue_text": "Use of eval",
                    "issue_severity": "HIGH",
                    "issue_confidence": "HIGH",
                }
            ]
        }

        safety_output = [{"package": "django", "version": "1.0"}]

        mock_runner.run.side_effect = [
            CommandResult(
                returncode=0,
                stdout="",
                stderr="",
                command=["bandit"],
                duration_seconds=0.5,
            ),
            CommandResult(
                returncode=0,
                stdout=json.dumps(safety_output),
                stderr="",
                command=["safety"],
                duration_seconds=0.5,
            ),
        ]

        with patch("tempfile.mkstemp", return_value=(1, "/tmp/bandit_report.json")):
            with patch("os.close"):
                with patch("builtins.open", create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(
                        bandit_output
                    )
                    with patch.object(Path, "exists", return_value=True):
                        with patch.object(Path, "unlink"):
                            result = checker._scan_python()

        assert "bandit" in result
        assert "safety" in result
        assert result["by_severity"]["HIGH"] == 1
        assert len(result["vulnerabilities"]) == 2
