"""Unit tests for scripts/quality_gates.py.

This module provides comprehensive unit tests for the QualityGates class,
which orchestrates all quality validation including tests, linting, formatting,
security scanning, documentation validation, and custom checks.
"""

import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

from sdd.quality.gates import QualityGates


class TestQualityGatesInit:
    """Tests for QualityGates initialization and configuration loading."""

    def test_init_with_default_config_path(self):
        """Test initialization uses default config path when none provided."""
        # Arrange & Act
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Assert
        assert gates._config_path == Path(".session/config.json")
        assert gates.config is not None

    def test_init_with_custom_config_path(self):
        """Test initialization with custom config path."""
        # Arrange
        custom_path = Path("/custom/config.json")

        # Act
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates(config_path=custom_path)

        # Assert
        assert gates._config_path == custom_path

    def test_load_config_file_not_found_uses_defaults(self, temp_dir):
        """Test loading config when file doesn't exist returns defaults."""
        # Arrange
        config_path = temp_dir / "nonexistent.json"

        # Act
        gates = QualityGates(config_path=config_path)

        # Assert
        assert gates.config["test_execution"]["enabled"] is True
        assert gates.config["test_execution"]["coverage_threshold"] == 80
        assert gates.config["linting"]["enabled"] is True

    def test_load_config_with_valid_json(self, temp_dir):
        """Test loading config from valid JSON file."""
        # Arrange
        config_path = temp_dir / "config.json"
        config_data = {
            "quality_gates": {
                "test_execution": {"enabled": True, "coverage_threshold": 90},
                "linting": {"enabled": False},
            }
        }
        config_path.write_text(json.dumps(config_data))

        # Act
        with patch("sdd.quality.gates.load_and_validate_config", None):
            gates = QualityGates(config_path=config_path)

        # Assert
        assert gates.config["test_execution"]["coverage_threshold"] == 90
        assert gates.config["linting"]["enabled"] is False

    def test_load_config_with_validation_success(self, temp_dir):
        """Test loading config with successful schema validation."""
        # Arrange
        config_path = temp_dir / "config.json"
        schema_path = temp_dir / "config.schema.json"
        config_data = {
            "quality_gates": {"test_execution": {"enabled": True, "coverage_threshold": 85}}
        }
        config_path.write_text(json.dumps(config_data))
        schema_path.write_text("{}")

        mock_validator = Mock(return_value=config_data)

        # Act
        with patch("sdd.quality.gates.load_and_validate_config", mock_validator):
            gates = QualityGates(config_path=config_path)

        # Assert
        mock_validator.assert_called_once()
        assert gates.config["test_execution"]["coverage_threshold"] == 85

    def test_load_config_with_validation_failure_uses_defaults(self, temp_dir):
        """Test loading config falls back to defaults when validation fails."""
        # Arrange
        config_path = temp_dir / "config.json"
        schema_path = temp_dir / "config.schema.json"
        config_path.write_text('{"quality_gates": {}}')
        schema_path.write_text("{}")

        mock_validator = Mock(side_effect=ValueError("Invalid config"))

        # Act
        with patch("sdd.quality.gates.load_and_validate_config", mock_validator):
            gates = QualityGates(config_path=config_path)

        # Assert
        assert gates.config["test_execution"]["coverage_threshold"] == 80

    def test_default_config_structure(self):
        """Test default configuration has all required sections."""
        # Arrange & Act
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Assert
        assert "test_execution" in gates.config
        assert "linting" in gates.config
        assert "formatting" in gates.config
        assert "security" in gates.config
        assert "documentation" in gates.config
        assert "spec_completeness" in gates.config

    def test_default_config_test_execution_settings(self):
        """Test default test execution configuration."""
        # Arrange & Act
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Assert
        test_config = gates.config["test_execution"]
        assert test_config["enabled"] is True
        assert test_config["required"] is True
        assert test_config["coverage_threshold"] == 80
        assert "python" in test_config["commands"]
        assert "javascript" in test_config["commands"]


class TestQualityGatesLanguageDetection:
    """Tests for language detection logic."""

    def test_detect_language_python_pyproject(self):
        """Test detecting Python project via pyproject.toml."""

        # Arrange & Act
        def mock_exists(self):
            return "pyproject.toml" in str(self)

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        with patch.object(Path, "exists", mock_exists):
            language = gates._detect_language()

        # Assert
        assert language == "python"

    def test_detect_language_python_setup_py(self):
        """Test detecting Python project via setup.py."""

        # Arrange & Act
        def mock_exists(self):
            return "setup.py" in str(self)

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        with patch.object(Path, "exists", mock_exists):
            language = gates._detect_language()

        # Assert
        assert language == "python"

    def test_detect_language_typescript(self):
        """Test detecting TypeScript project."""

        # Arrange & Act
        def mock_exists(self):
            path_str = str(self)
            return "package.json" in path_str or "tsconfig.json" in path_str

        with patch.object(Path, "exists", mock_exists):
            gates = QualityGates()
            language = gates._detect_language()

        # Assert
        assert language == "typescript"

    def test_detect_language_javascript(self):
        """Test detecting JavaScript project (has package.json, no tsconfig.json)."""

        # Arrange & Act
        def mock_exists(self):
            return "package.json" in str(self) and "tsconfig.json" not in str(self)

        with patch.object(Path, "exists", mock_exists):
            gates = QualityGates()
            language = gates._detect_language()

        # Assert
        assert language == "javascript"

    def test_detect_language_defaults_to_python(self):
        """Test language detection defaults to Python when no markers found."""
        # Arrange & Act
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()
            language = gates._detect_language()

        # Assert
        assert language == "python"


class TestQualityGatesTestExecution:
    """Tests for test execution and coverage validation."""

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_tests_success_with_coverage(self, mock_run):
        """Test running tests successfully with coverage above threshold."""
        # Arrange
        mock_run.return_value = Mock(
            returncode=0, stdout="pytest output\n100% tests passed", stderr=""
        )

        coverage_data = {"totals": {"percent_covered": 85.5}}

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        with patch.object(Path, "exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=json.dumps(coverage_data))):
                passed, results = gates.run_tests(language="python")

        # Assert
        assert passed is True
        assert results["status"] == "passed"
        assert results["coverage"] == 85.5

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_tests_failure(self, mock_run):
        """Test running tests that fail."""
        # Arrange
        mock_run.return_value = Mock(returncode=1, stdout="test failures", stderr="errors")

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        with patch.object(Path, "exists", return_value=False):
            passed, results = gates.run_tests(language="python")

        # Assert
        assert passed is False
        assert results["status"] == "failed"
        assert results["returncode"] == 1

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_tests_coverage_below_threshold(self, mock_run):
        """Test running tests with coverage below threshold."""
        # Arrange
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        coverage_data = {"totals": {"percent_covered": 60.0}}

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        with patch.object(Path, "exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=json.dumps(coverage_data))):
                passed, results = gates.run_tests(language="python")

        # Assert
        assert passed is False
        assert results["status"] == "failed"
        assert "Coverage 60.0% below threshold 80%" in results["reason"]

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_tests_no_tests_collected(self, mock_run):
        """Test running tests when no tests are collected (exit code 5)."""
        # Arrange
        mock_run.return_value = Mock(returncode=5, stdout="", stderr="")

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        passed, results = gates.run_tests(language="python")

        # Assert
        assert passed is True
        assert results["status"] == "skipped"
        assert results["reason"] == "no tests collected"

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_tests_timeout(self, mock_run):
        """Test running tests that timeout."""
        # Arrange
        mock_run.side_effect = subprocess.TimeoutExpired("pytest", 300)

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        passed, results = gates.run_tests(language="python")

        # Assert
        assert passed is False
        assert results["status"] == "failed"
        assert results["reason"] == "timeout"

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_tests_pytest_not_available(self, mock_run):
        """Test running tests when pytest is not available."""
        # Arrange
        mock_run.side_effect = FileNotFoundError("pytest not found")

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        passed, results = gates.run_tests(language="python")

        # Assert
        assert passed is True
        assert results["status"] == "skipped"
        assert results["reason"] == "pytest not available"

    def test_run_tests_disabled(self):
        """Test running tests when test execution is disabled."""
        # Arrange
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()
        gates.config["test_execution"]["enabled"] = False

        # Act
        passed, results = gates.run_tests()

        # Assert
        assert passed is True
        assert results["status"] == "skipped"
        assert results["reason"] == "disabled"

    def test_run_tests_no_command_for_language(self):
        """Test running tests when no command configured for language."""
        # Arrange
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        passed, results = gates.run_tests(language="ruby")

        # Assert
        assert passed is True
        assert results["status"] == "skipped"
        assert "no command for ruby" in results["reason"]

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_tests_auto_detect_language(self, mock_run):
        """Test running tests with auto-detected language."""
        # Arrange
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        with patch.object(gates, "_detect_language", return_value="python"):
            passed, results = gates.run_tests()

        # Assert
        mock_run.assert_called_once()


class TestQualityGatesCoverageParsing:
    """Tests for coverage parsing from different languages."""

    def test_parse_coverage_python_valid_json(self):
        """Test parsing Python coverage from valid JSON file."""
        # Arrange
        coverage_data = {"totals": {"percent_covered": 92.5}}

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        with patch.object(Path, "exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=json.dumps(coverage_data))):
                coverage = gates._parse_coverage("python")

        # Assert
        assert coverage == 92.5

    def test_parse_coverage_python_file_not_found(self):
        """Test parsing Python coverage when file doesn't exist."""
        # Arrange
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        with patch.object(Path, "exists", return_value=False):
            coverage = gates._parse_coverage("python")

        # Assert
        assert coverage is None

    def test_parse_coverage_javascript_valid_json(self):
        """Test parsing JavaScript coverage from valid JSON file."""
        # Arrange
        coverage_data = {"total": {"lines": {"pct": 88.3}}}

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        with patch.object(Path, "exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=json.dumps(coverage_data))):
                coverage = gates._parse_coverage("javascript")

        # Assert
        assert coverage == 88.3

    def test_parse_coverage_typescript(self):
        """Test parsing TypeScript coverage (uses same format as JavaScript)."""
        # Arrange
        coverage_data = {"total": {"lines": {"pct": 95.0}}}

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        with patch.object(Path, "exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=json.dumps(coverage_data))):
                coverage = gates._parse_coverage("typescript")

        # Assert
        assert coverage == 95.0

    def test_parse_coverage_unsupported_language(self):
        """Test parsing coverage for unsupported language returns None."""
        # Arrange
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        coverage = gates._parse_coverage("ruby")

        # Assert
        assert coverage is None


class TestQualityGatesSecurityScan:
    """Tests for security vulnerability scanning."""

    @patch("sdd.quality.gates.subprocess.run")
    @patch("os.close")
    def test_run_security_scan_python_bandit_no_issues(self, mock_close, mock_run, temp_dir):
        """Test running security scan with bandit finding no issues."""
        # Arrange
        temp_file = temp_dir / "bandit.json"
        bandit_data = {"results": []}
        temp_file.write_text(json.dumps(bandit_data))

        with patch("tempfile.mkstemp", return_value=(999, str(temp_file))):
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            with patch.object(Path, "exists", return_value=False):
                gates = QualityGates()

            # Act
            passed, results = gates.run_security_scan(language="python")

        # Assert
        assert passed is True
        assert results["status"] == "passed"
        mock_close.assert_called_once_with(999)

    @patch("sdd.quality.gates.subprocess.run")
    @patch("os.close")
    def test_run_security_scan_python_bandit_high_severity(self, mock_close, mock_run, temp_dir):
        """Test running security scan with high severity issues."""
        # Arrange
        temp_file = temp_dir / "bandit.json"
        bandit_data = {"results": [{"issue_severity": "HIGH", "issue_text": "SQL injection risk"}]}
        temp_file.write_text(json.dumps(bandit_data))

        with patch("tempfile.mkstemp", return_value=(999, str(temp_file))):
            mock_run.return_value = Mock(returncode=1, stdout="", stderr="")

            with patch.object(Path, "exists", return_value=False):
                gates = QualityGates()

            # Act
            passed, results = gates.run_security_scan(language="python")

        # Assert
        assert passed is False
        assert "HIGH" in results["by_severity"]
        assert results["by_severity"]["HIGH"] == 1

    @patch("sdd.quality.gates.subprocess.run")
    @patch("os.close")
    def test_run_security_scan_python_low_severity_passes(self, mock_close, mock_run, temp_dir):
        """Test running security scan with low severity issues passes."""
        # Arrange
        temp_file = temp_dir / "bandit.json"
        bandit_data = {"results": [{"issue_severity": "LOW", "issue_text": "Minor issue"}]}
        temp_file.write_text(json.dumps(bandit_data))

        with patch("tempfile.mkstemp", return_value=(999, str(temp_file))):
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            with patch.object(Path, "exists", return_value=False):
                gates = QualityGates()

            # Act
            passed, results = gates.run_security_scan(language="python")

        # Assert
        assert passed is True
        assert results["status"] == "passed"

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_security_scan_bandit_not_available(self, mock_run):
        """Test running security scan when bandit is not available."""
        # Arrange
        mock_run.side_effect = FileNotFoundError("bandit not found")

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        passed, results = gates.run_security_scan(language="python")

        # Assert
        assert passed is True

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_security_scan_javascript_npm_audit(self, mock_run):
        """Test running security scan for JavaScript with npm audit."""
        # Arrange
        audit_data = {
            "vulnerabilities": {"lodash": {"severity": "high"}, "express": {"severity": "low"}}
        }
        mock_run.return_value = Mock(returncode=1, stdout=json.dumps(audit_data), stderr="")

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        passed, results = gates.run_security_scan(language="javascript")

        # Assert
        assert passed is False
        assert results["by_severity"]["HIGH"] == 1
        assert results["by_severity"]["LOW"] == 1

    def test_run_security_scan_disabled(self):
        """Test running security scan when disabled."""
        # Arrange
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()
        gates.config["security"]["enabled"] = False

        # Act
        passed, results = gates.run_security_scan()

        # Assert
        assert passed is True
        assert results["status"] == "skipped"

    @patch("sdd.quality.gates.subprocess.run")
    @patch("os.close")
    def test_run_security_scan_custom_fail_threshold_medium(self, mock_close, mock_run, temp_dir):
        """Test security scan with custom fail threshold at medium."""
        # Arrange
        temp_file = temp_dir / "bandit.json"
        bandit_data = {"results": [{"issue_severity": "MEDIUM", "issue_text": "Medium issue"}]}
        temp_file.write_text(json.dumps(bandit_data))

        with patch("tempfile.mkstemp", return_value=(999, str(temp_file))):
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            with patch.object(Path, "exists", return_value=False):
                gates = QualityGates()
            gates.config["security"]["fail_on"] = "medium"

            # Act
            passed, results = gates.run_security_scan(language="python")

        # Assert
        assert passed is False
        assert results["by_severity"]["MEDIUM"] == 1


class TestQualityGatesLinting:
    """Tests for code linting validation."""

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_linting_success(self, mock_run):
        """Test running linting successfully with no issues."""
        # Arrange
        mock_run.return_value = Mock(returncode=0, stdout="All checks passed", stderr="")

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        passed, results = gates.run_linting(language="python")

        # Assert
        assert passed is True
        assert results["status"] == "passed"

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_linting_with_issues(self, mock_run):
        """Test running linting with issues found."""
        # Arrange
        mock_run.return_value = Mock(returncode=1, stdout="Found 5 linting issues", stderr="")

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        passed, results = gates.run_linting(language="python")

        # Assert
        assert passed is False
        assert results["status"] == "failed"
        assert results["issues_found"] == 1

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_linting_with_auto_fix(self, mock_run):
        """Test running linting with auto-fix enabled."""
        # Arrange
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        passed, results = gates.run_linting(language="python", auto_fix=True)

        # Assert
        assert passed is True
        assert results["fixed"] is True
        mock_run.assert_called_once()
        assert "--fix" in mock_run.call_args[0][0]

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_linting_javascript_with_auto_fix(self, mock_run):
        """Test running linting for JavaScript with auto-fix."""
        # Arrange
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        passed, results = gates.run_linting(language="javascript", auto_fix=True)

        # Assert
        assert passed is True
        mock_run.assert_called_once()
        assert "--fix" in mock_run.call_args[0][0]

    def test_run_linting_disabled(self):
        """Test running linting when disabled."""
        # Arrange
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()
        gates.config["linting"]["enabled"] = False

        # Act
        passed, results = gates.run_linting()

        # Assert
        assert passed is True
        assert results["status"] == "skipped"

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_linting_tool_not_found_required(self, mock_run):
        """Test running linting when tool not found and gate is required."""
        # Arrange
        mock_run.side_effect = FileNotFoundError("ruff not found")

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()
        gates.config["linting"]["required"] = True

        # Act
        passed, results = gates.run_linting(language="python")

        # Assert
        assert passed is False
        assert results["status"] == "failed"
        assert "Required linting tool not found" in results["reason"]

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_linting_tool_not_found_optional(self, mock_run):
        """Test running linting when tool not found and gate is optional."""
        # Arrange
        mock_run.side_effect = FileNotFoundError("ruff not found")

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()
        gates.config["linting"]["required"] = False

        # Act
        passed, results = gates.run_linting(language="python")

        # Assert
        assert passed is True
        assert results["status"] == "skipped"


class TestQualityGatesFormatting:
    """Tests for code formatting validation."""

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_formatting_success(self, mock_run):
        """Test running formatting check successfully."""
        # Arrange
        mock_run.return_value = Mock(returncode=0, stdout="All files formatted", stderr="")

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        passed, results = gates.run_formatting(language="python", auto_fix=False)

        # Assert
        assert passed is True
        assert results["status"] == "passed"

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_formatting_python_check_mode(self, mock_run):
        """Test running Python formatting in check mode (no auto-fix)."""
        # Arrange
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        passed, results = gates.run_formatting(language="python", auto_fix=False)

        # Assert
        assert passed is True
        mock_run.assert_called_once()
        assert "--check" in mock_run.call_args[0][0]

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_formatting_python_auto_fix(self, mock_run):
        """Test running Python formatting with auto-fix."""
        # Arrange
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        passed, results = gates.run_formatting(language="python", auto_fix=True)

        # Assert
        assert passed is True
        assert results["formatted"] is True
        # Should not have --check flag when auto_fix is True
        assert "--check" not in str(mock_run.call_args)

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_formatting_javascript_auto_fix(self, mock_run):
        """Test running JavaScript formatting with auto-fix."""
        # Arrange
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        passed, results = gates.run_formatting(language="javascript", auto_fix=True)

        # Assert
        assert passed is True
        mock_run.assert_called_once()
        assert "--write" in mock_run.call_args[0][0]

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_formatting_javascript_check_mode(self, mock_run):
        """Test running JavaScript formatting in check mode."""
        # Arrange
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        passed, results = gates.run_formatting(language="javascript", auto_fix=False)

        # Assert
        assert passed is True
        mock_run.assert_called_once()
        assert "--check" in mock_run.call_args[0][0]

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_formatting_unformatted_files(self, mock_run):
        """Test running formatting when files are not formatted."""
        # Arrange
        mock_run.return_value = Mock(returncode=1, stdout="Would reformat 3 files", stderr="")

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        passed, results = gates.run_formatting(language="python", auto_fix=False)

        # Assert
        assert passed is False
        assert results["status"] == "failed"

    def test_run_formatting_disabled(self):
        """Test running formatting when disabled."""
        # Arrange
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()
        gates.config["formatting"]["enabled"] = False

        # Act
        passed, results = gates.run_formatting()

        # Assert
        assert passed is True
        assert results["status"] == "skipped"

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_formatting_tool_not_found_required(self, mock_run):
        """Test running formatting when tool not found and gate is required."""
        # Arrange
        mock_run.side_effect = FileNotFoundError("ruff not found")

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()
        gates.config["formatting"]["required"] = True

        # Act
        passed, results = gates.run_formatting(language="python")

        # Assert
        assert passed is False
        assert results["status"] == "failed"


class TestQualityGatesDocumentation:
    """Tests for documentation validation."""

    @patch("sdd.quality.gates.subprocess.run")
    def test_validate_documentation_all_checks_pass(self, mock_run):
        """Test validating documentation when all checks pass."""
        # Arrange
        mock_run.side_effect = [
            Mock(returncode=0, stdout="feature/my-feature", stderr=""),  # git rev-parse
            Mock(returncode=0, stdout="CHANGELOG.md", stderr=""),  # git log
            Mock(returncode=0, stdout="", stderr=""),  # pydocstyle
        ]

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        passed, results = gates.validate_documentation()

        # Assert
        assert passed is True
        assert results["status"] == "passed"

    def test_validate_documentation_disabled(self):
        """Test validating documentation when disabled."""
        # Arrange
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()
        gates.config["documentation"]["enabled"] = False

        # Act
        passed, results = gates.validate_documentation()

        # Assert
        assert passed is True
        assert results["status"] == "skipped"

    @patch("sdd.quality.gates.subprocess.run")
    def test_check_changelog_updated_on_feature_branch(self, mock_run):
        """Test checking CHANGELOG updated on feature branch."""
        # Arrange
        mock_run.side_effect = [
            Mock(returncode=0, stdout="feature/my-feature", stderr=""),
            Mock(returncode=0, stdout="CHANGELOG.md\nfile.py", stderr=""),
        ]

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        result = gates._check_changelog_updated()

        # Assert
        assert result is True

    @patch("sdd.quality.gates.subprocess.run")
    def test_check_changelog_not_updated_on_feature_branch(self, mock_run):
        """Test checking CHANGELOG not updated on feature branch."""
        # Arrange
        mock_run.side_effect = [
            Mock(returncode=0, stdout="feature/my-feature", stderr=""),
            Mock(returncode=0, stdout="file.py\ntest.py", stderr=""),
        ]

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        result = gates._check_changelog_updated()

        # Assert
        assert result is False

    @patch("sdd.quality.gates.subprocess.run")
    def test_check_changelog_on_main_branch_skipped(self, mock_run):
        """Test checking CHANGELOG on main branch is skipped."""
        # Arrange
        mock_run.return_value = Mock(returncode=0, stdout="main", stderr="")

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        result = gates._check_changelog_updated()

        # Assert
        assert result is True

    @patch("sdd.quality.gates.subprocess.run")
    def test_check_python_docstrings_pass(self, mock_run):
        """Test checking Python docstrings when all present."""
        # Arrange
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        result = gates._check_python_docstrings()

        # Assert
        assert result is True

    @patch("sdd.quality.gates.subprocess.run")
    def test_check_python_docstrings_missing(self, mock_run):
        """Test checking Python docstrings when some are missing."""
        # Arrange
        mock_run.return_value = Mock(returncode=1, stdout="Missing docstrings", stderr="")

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        result = gates._check_python_docstrings()

        # Assert
        assert result is False

    @patch("sdd.quality.gates.subprocess.run")
    def test_check_python_docstrings_tool_not_available(self, mock_run):
        """Test checking Python docstrings when pydocstyle not available."""
        # Arrange
        mock_run.side_effect = FileNotFoundError("pydocstyle not found")

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        result = gates._check_python_docstrings()

        # Assert
        assert result is True  # Skip check if tool not available

    @patch("sdd.quality.gates.subprocess.run")
    def test_check_readme_current_updated(self, mock_run):
        """Test checking README was updated."""
        # Arrange
        mock_run.return_value = Mock(returncode=0, stdout="README.md\nfile.py", stderr="")

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        result = gates._check_readme_current()

        # Assert
        assert result is True

    @patch("sdd.quality.gates.subprocess.run")
    def test_check_readme_current_not_updated(self, mock_run):
        """Test checking README was not updated."""
        # Arrange
        mock_run.return_value = Mock(returncode=0, stdout="file.py\ntest.py", stderr="")

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        result = gates._check_readme_current()

        # Assert
        assert result is False


class TestQualityGatesSpecCompleteness:
    """Tests for spec file completeness validation."""

    def test_validate_spec_completeness_success(self):
        """Test validating spec completeness successfully."""
        # Arrange
        work_item = {"id": "WI-001", "type": "feature"}

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        with patch("sdd.quality.gates.validate_spec_file", return_value=(True, [])):
            passed, results = gates.validate_spec_completeness(work_item)

        # Assert
        assert passed is True
        assert results["status"] == "passed"

    def test_validate_spec_completeness_failure(self):
        """Test validating spec completeness with errors."""
        # Arrange
        work_item = {"id": "WI-001", "type": "feature"}
        errors = ["Missing description", "Missing acceptance criteria"]

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        with patch("sdd.quality.gates.validate_spec_file", return_value=(False, errors)):
            passed, results = gates.validate_spec_completeness(work_item)

        # Assert
        assert passed is False
        assert results["status"] == "failed"
        assert results["errors"] == errors

    def test_validate_spec_completeness_disabled(self):
        """Test validating spec completeness when disabled."""
        # Arrange
        work_item = {"id": "WI-001", "type": "feature"}

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()
        gates.config["spec_completeness"]["enabled"] = False

        # Act
        passed, results = gates.validate_spec_completeness(work_item)

        # Assert
        assert passed is True
        assert results["status"] == "skipped"

    def test_validate_spec_completeness_validator_not_available(self):
        """Test validating spec completeness when validator not available."""
        # Arrange
        work_item = {"id": "WI-001", "type": "feature"}

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        with patch("sdd.quality.gates.validate_spec_file", None):
            passed, results = gates.validate_spec_completeness(work_item)

        # Assert
        assert passed is True
        assert results["status"] == "skipped"

    def test_validate_spec_completeness_missing_work_item_fields(self):
        """Test validating spec completeness with missing work item fields."""
        # Arrange
        work_item = {"id": "WI-001"}  # Missing 'type'

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        passed, results = gates.validate_spec_completeness(work_item)

        # Assert
        assert passed is False
        assert results["status"] == "failed"
        assert "missing" in results["error"].lower()


class TestQualityGatesCustomValidations:
    """Tests for custom validation rules."""

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_custom_validations_command_success(self, mock_run):
        """Test running custom command validation successfully."""
        # Arrange
        mock_run.return_value = Mock(returncode=0)
        work_item = {
            "validation_rules": [
                {"type": "command", "command": "echo test", "name": "Test command"}
            ]
        }

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        passed, results = gates.run_custom_validations(work_item)

        # Assert
        assert passed is True
        assert results["status"] == "passed"

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_custom_validations_command_failure(self, mock_run):
        """Test running custom command validation that fails."""
        # Arrange
        mock_run.return_value = Mock(returncode=1)
        work_item = {
            "validation_rules": [
                {
                    "type": "command",
                    "command": "false",
                    "name": "Test command",
                    "required": True,
                }
            ]
        }

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        passed, results = gates.run_custom_validations(work_item)

        # Assert
        assert passed is False
        assert results["status"] == "failed"

    def test_run_custom_validations_file_exists_pass(self, temp_dir):
        """Test file exists validation when file is present."""
        # Arrange
        test_file = temp_dir / "test.txt"
        test_file.touch()

        work_item = {
            "validation_rules": [
                {"type": "file_exists", "path": str(test_file), "name": "Test file"}
            ]
        }

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        with patch("sdd.quality.gates.Path") as mock_path:
            mock_path.return_value.exists.return_value = True
            passed, results = gates.run_custom_validations(work_item)

        # Assert
        assert passed is True

    def test_run_custom_validations_file_exists_fail(self):
        """Test file exists validation when file is missing."""
        # Arrange
        work_item = {
            "validation_rules": [
                {
                    "type": "file_exists",
                    "path": "/nonexistent/file.txt",
                    "name": "Test file",
                    "required": True,
                }
            ]
        }

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        with patch("sdd.quality.gates.Path") as mock_path:
            mock_path.return_value.exists.return_value = False
            passed, results = gates.run_custom_validations(work_item)

        # Assert
        assert passed is False

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_custom_validations_grep_pattern_found(self, mock_run):
        """Test grep validation when pattern is found."""
        # Arrange
        mock_run.return_value = Mock(returncode=0)
        work_item = {
            "validation_rules": [
                {
                    "type": "grep",
                    "pattern": "TODO",
                    "files": ".",
                    "name": "Check TODOs",
                }
            ]
        }

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        passed, results = gates.run_custom_validations(work_item)

        # Assert
        assert passed is True

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_custom_validations_grep_pattern_not_found(self, mock_run):
        """Test grep validation when pattern is not found."""
        # Arrange
        mock_run.return_value = Mock(returncode=1)
        work_item = {
            "validation_rules": [
                {
                    "type": "grep",
                    "pattern": "REQUIRED_STRING",
                    "files": ".",
                    "name": "Check required string",
                    "required": True,
                }
            ]
        }

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        passed, results = gates.run_custom_validations(work_item)

        # Assert
        assert passed is False

    def test_run_custom_validations_optional_failure(self):
        """Test custom validation with optional rule failing doesn't fail overall."""
        # Arrange
        work_item = {
            "validation_rules": [
                {
                    "type": "file_exists",
                    "path": "/nonexistent/file.txt",
                    "name": "Optional file",
                    "required": False,
                }
            ]
        }

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        with patch("sdd.quality.gates.Path") as mock_path:
            mock_path.return_value.exists.return_value = False
            passed, results = gates.run_custom_validations(work_item)

        # Assert
        assert passed is True  # Optional rule failure doesn't fail overall


class TestQualityGatesRequiredGates:
    """Tests for checking required gates configuration."""

    def test_check_required_gates_all_met(self):
        """Test checking required gates when all are enabled."""
        # Arrange
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        all_met, missing = gates.check_required_gates()

        # Assert
        assert all_met is True
        assert len(missing) == 0

    def test_check_required_gates_some_missing(self):
        """Test checking required gates when some are disabled."""
        # Arrange
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()
        gates.config["test_execution"]["enabled"] = False
        gates.config["test_execution"]["required"] = True

        # Act
        all_met, missing = gates.check_required_gates()

        # Assert
        assert all_met is False
        assert "test_execution" in missing


class TestQualityGatesReporting:
    """Tests for quality gate reporting and remediation guidance."""

    def test_generate_report_all_passed(self):
        """Test generating report when all gates passed."""
        # Arrange
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        all_results = {
            "tests": {"status": "passed", "coverage": 85},
            "security": {"status": "passed", "by_severity": {}},
            "linting": {"status": "passed"},
            "formatting": {"status": "passed"},
        }

        # Act
        report = gates.generate_report(all_results)

        # Assert
        assert "QUALITY GATE RESULTS" in report
        assert "✓ PASSED" in report
        assert "Coverage: 85%" in report

    def test_generate_report_some_failed(self):
        """Test generating report when some gates failed."""
        # Arrange
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        all_results = {
            "tests": {"status": "failed", "coverage": 60},
            "security": {
                "status": "failed",
                "by_severity": {"HIGH": 3, "MEDIUM": 5},
            },
        }

        # Act
        report = gates.generate_report(all_results)

        # Assert
        assert "QUALITY GATE RESULTS" in report
        assert "✗ FAILED" in report
        assert "HIGH: 3" in report
        assert "MEDIUM: 5" in report

    def test_generate_report_with_skipped_gates(self):
        """Test generating report with skipped gates."""
        # Arrange
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        all_results = {
            "linting": {"status": "skipped"},
            "formatting": {"status": "skipped"},
        }

        # Act
        report = gates.generate_report(all_results)

        # Assert
        assert "⊘ SKIPPED" in report

    def test_generate_report_with_documentation_checks(self):
        """Test generating report with documentation check details."""
        # Arrange
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        all_results = {
            "documentation": {
                "status": "passed",
                "checks": [
                    {"name": "CHANGELOG updated", "passed": True},
                    {"name": "Docstrings present", "passed": True},
                ],
            }
        }

        # Act
        report = gates.generate_report(all_results)

        # Assert
        assert "Documentation: ✓ PASSED" in report
        assert "✓ CHANGELOG updated" in report
        assert "✓ Docstrings present" in report

    def test_get_remediation_guidance_tests_failed(self):
        """Test getting remediation guidance for failed tests."""
        # Arrange
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        guidance = gates.get_remediation_guidance(["tests"])

        # Assert
        assert "REMEDIATION GUIDANCE" in guidance
        assert "Tests Failed" in guidance
        assert "Review test output" in guidance

    def test_get_remediation_guidance_security_failed(self):
        """Test getting remediation guidance for security failures."""
        # Arrange
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        guidance = gates.get_remediation_guidance(["security"])

        # Assert
        assert "Security Issues Found" in guidance
        assert "Update vulnerable dependencies" in guidance

    def test_get_remediation_guidance_documentation_failed(self):
        """Test getting remediation guidance for documentation failures."""
        # Arrange
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        guidance = gates.get_remediation_guidance(["documentation"])

        # Assert
        assert "Documentation Issues" in guidance
        assert "CHANGELOG.md" in guidance

    def test_get_remediation_guidance_multiple_failures(self):
        """Test getting remediation guidance for multiple failures."""
        # Arrange
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        guidance = gates.get_remediation_guidance(["tests", "linting", "formatting"])

        # Assert
        assert "Tests Failed" in guidance
        assert "Linting Issues" in guidance
        assert "Formatting Issues" in guidance


class TestQualityGatesContext7:
    """Tests for Context7 library verification."""

    def test_verify_context7_libraries_disabled(self):
        """Test Context7 library verification when disabled."""
        # Arrange
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        passed, results = gates.verify_context7_libraries()

        # Assert
        assert passed is True
        assert results["status"] == "skipped"
        assert results["reason"] == "not enabled"

    def test_verify_context7_libraries_no_stack_file(self):
        """Test Context7 verification when stack.txt doesn't exist."""
        # Arrange
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()
        gates.config["context7"] = {"enabled": True}

        # Act
        with patch.object(Path, "exists", return_value=False):
            passed, results = gates.verify_context7_libraries()

        # Assert
        assert passed is True
        assert results["status"] == "skipped"
        assert results["reason"] == "no stack.txt"

    def test_parse_libraries_from_stack(self, temp_dir):
        """Test parsing libraries from stack.txt file."""
        # Arrange
        stack_file = temp_dir / ".session" / "tracking" / "stack.txt"
        stack_file.parent.mkdir(parents=True, exist_ok=True)
        stack_file.write_text("Python 3.11\npytest 7.4.0\nruff 0.1.0\n")

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        with patch("sdd.quality.gates.Path") as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.__truediv__.return_value = stack_file
            with patch("builtins.open", mock_open(read_data="Python 3.11\npytest 7.4.0\n")):
                libraries = gates._parse_libraries_from_stack()

        # Assert
        assert len(libraries) == 2
        assert libraries[0]["name"] == "Python"
        assert libraries[0]["version"] == "3.11"

    def test_should_verify_library_with_important_list(self):
        """Test checking if library should be verified with important list."""
        # Arrange
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        lib = {"name": "pytest", "version": "7.4.0"}
        config = {"important_libraries": ["pytest", "ruff"]}

        # Act
        should_verify = gates._should_verify_library(lib, config)

        # Assert
        assert should_verify is True

    def test_should_verify_library_not_in_important_list(self):
        """Test library not in important list is not verified."""
        # Arrange
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        lib = {"name": "other-lib", "version": "1.0.0"}
        config = {"important_libraries": ["pytest", "ruff"]}

        # Act
        should_verify = gates._should_verify_library(lib, config)

        # Assert
        assert should_verify is False

    def test_should_verify_library_no_important_list(self):
        """Test all libraries verified when no important list configured."""
        # Arrange
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        lib = {"name": "any-lib", "version": "1.0.0"}
        config = {}

        # Act
        should_verify = gates._should_verify_library(lib, config)

        # Assert
        assert should_verify is True

    def test_query_context7_stub_returns_true(self):
        """Test Context7 query stub returns True."""
        # Arrange
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        lib = {"name": "pytest", "version": "7.4.0"}

        # Act
        result = gates._query_context7(lib)

        # Assert
        assert result is True


class TestQualityGatesIntegration:
    """Tests for integration test validation."""

    def test_run_integration_tests_disabled(self):
        """Test running integration tests when disabled."""
        # Arrange
        work_item = {"id": "test-001", "type": "integration_test"}

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act - Mock Path.exists to return True for config file
        def exists_side_effect(self):
            return str(self) == ".session/config.json"

        with (
            patch.object(Path, "exists", exists_side_effect),
            patch(
                "builtins.open", mock_open(read_data='{"integration_tests": {"enabled": false}}')
            ),
        ):
            passed, results = gates.run_integration_tests(work_item)

        # Assert
        assert passed is True
        assert results["status"] == "skipped"
        assert results["reason"] == "disabled"

    def test_run_integration_tests_not_integration_test_type(self):
        """Test running integration tests on non-integration test work item."""
        # Arrange
        work_item = {"type": "feature"}

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        with patch(
            "builtins.open", mock_open(read_data='{"integration_tests": {"enabled": true}}')
        ):
            passed, results = gates.run_integration_tests(work_item)

        # Assert
        assert passed is True
        assert results["status"] == "skipped"
        assert results["reason"] == "not integration test"

    @patch("sdd.quality.gates.subprocess.run")
    def test_validate_integration_environment_docker_available(self, mock_run):
        """Test validating integration environment with Docker available."""
        # Arrange
        work_item = {
            "type": "integration_test",
            "environment_requirements": {
                "compose_file": "docker-compose.yml",
                "config_files": [],
            },
        }

        mock_run.side_effect = [
            Mock(returncode=0),  # docker --version
            Mock(returncode=0),  # docker-compose --version
        ]

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        with patch.object(Path, "exists", return_value=True):
            passed, results = gates.validate_integration_environment(work_item)

        # Assert
        assert passed is True
        assert results["docker_available"] is True
        assert results["docker_compose_available"] is True

    @patch("sdd.quality.gates.subprocess.run")
    def test_validate_integration_environment_docker_not_available(self, mock_run):
        """Test validating integration environment without Docker."""
        # Arrange
        work_item = {
            "type": "integration_test",
            "environment_requirements": {"config_files": []},
        }

        mock_run.side_effect = FileNotFoundError("docker not found")

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        with patch.object(Path, "exists", return_value=True):
            passed, results = gates.validate_integration_environment(work_item)

        # Assert
        assert passed is False
        assert results["docker_available"] is False

    def test_validate_integration_environment_missing_config_files(self):
        """Test validating integration environment with missing config files."""
        # Arrange
        work_item = {
            "type": "integration_test",
            "environment_requirements": {
                "compose_file": "docker-compose.yml",
                "config_files": ["config.json", "secrets.env"],
            },
        }

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        with patch("sdd.quality.gates.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            with patch.object(Path, "exists", return_value=False):
                passed, results = gates.validate_integration_environment(work_item)

        # Assert
        assert passed is False
        assert len(results["missing_config"]) > 0

    def test_validate_integration_environment_non_integration_test(self):
        """Test validating integration environment for non-integration test."""
        # Arrange
        work_item = {"type": "feature"}

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        passed, results = gates.validate_integration_environment(work_item)

        # Assert
        assert passed is True
        assert results["status"] == "skipped"

    def test_validate_integration_documentation_disabled(self):
        """Test validating integration documentation when disabled."""
        # Arrange
        work_item = {"id": "test-001", "type": "integration_test"}

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act - Mock Path.exists to return True for config file
        def exists_side_effect(self):
            return str(self) == ".session/config.json"

        config_data = '{"integration_tests": {"documentation": {"enabled": false}}}'
        with (
            patch.object(Path, "exists", exists_side_effect),
            patch("builtins.open", mock_open(read_data=config_data)),
        ):
            passed, results = gates.validate_integration_documentation(work_item)

        # Assert
        assert passed is True
        assert results["status"] == "skipped"

    def test_validate_integration_documentation_non_integration_test(self):
        """Test validating integration documentation for non-integration test."""
        # Arrange
        work_item = {"type": "feature"}

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        passed, results = gates.validate_integration_documentation(work_item)

        # Assert
        assert passed is True
        assert results["status"] == "skipped"


class TestQualityGatesDeployment:
    """Tests for deployment-specific quality gates."""

    @patch.object(QualityGates, "run_integration_tests")
    @patch.object(QualityGates, "run_security_scan")
    def test_run_deployment_gates_all_pass(self, mock_security, mock_integration):
        """Test running deployment gates when all pass."""
        # Arrange
        work_item = {"type": "deployment"}
        mock_integration.return_value = (True, {"status": "passed"})
        mock_security.return_value = (True, {"status": "passed"})

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        with patch.object(gates, "_validate_deployment_environment", return_value=True):
            with patch.object(gates, "_validate_deployment_documentation", return_value=True):
                with patch.object(gates, "_check_rollback_tested", return_value=True):
                    passed, results = gates.run_deployment_gates(work_item)

        # Assert
        assert passed is True
        assert len(results["gates"]) == 5

    @patch.object(QualityGates, "run_integration_tests")
    @patch.object(QualityGates, "run_security_scan")
    def test_run_deployment_gates_integration_fails(self, mock_security, mock_integration):
        """Test running deployment gates when integration tests fail."""
        # Arrange
        work_item = {"type": "deployment"}
        mock_integration.return_value = (False, {"status": "failed"})
        mock_security.return_value = (True, {"status": "passed"})

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        with patch.object(gates, "_validate_deployment_environment", return_value=True):
            with patch.object(gates, "_validate_deployment_documentation", return_value=True):
                with patch.object(gates, "_check_rollback_tested", return_value=True):
                    passed, results = gates.run_deployment_gates(work_item)

        # Assert
        assert passed is False

    @patch.object(QualityGates, "run_integration_tests")
    @patch.object(QualityGates, "run_security_scan")
    def test_run_deployment_gates_security_fails(self, mock_security, mock_integration):
        """Test running deployment gates when security scan fails."""
        # Arrange
        work_item = {"type": "deployment"}
        mock_integration.return_value = (True, {"status": "passed"})
        mock_security.return_value = (False, {"status": "failed"})

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        with patch.object(gates, "_validate_deployment_environment", return_value=True):
            with patch.object(gates, "_validate_deployment_documentation", return_value=True):
                with patch.object(gates, "_check_rollback_tested", return_value=True):
                    passed, results = gates.run_deployment_gates(work_item)

        # Assert
        assert passed is False

    def test_validate_deployment_environment_success(self):
        """Test validating deployment environment fallback returns True."""
        # Arrange
        work_item = {"specification": "environment: staging"}

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        # Since environment_validator module doesn't exist, the method will
        # catch the ImportError and return True (fallback behavior)
        result = gates._validate_deployment_environment(work_item)

        # Assert
        assert result is True  # Falls back to True when module not available

    def test_validate_deployment_environment_validator_not_available(self):
        """Test deployment environment validation when validator not available."""
        # Arrange
        work_item = {"specification": "environment: staging"}

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        result = gates._validate_deployment_environment(work_item)

        # Assert
        assert result is True  # Returns True when validator not available

    def test_validate_deployment_documentation_all_sections_present(self):
        """Test deployment documentation validation with all sections."""
        # Arrange
        work_item = {
            "specification": """
            Deployment Procedure:
            - Step 1

            Rollback Procedure:
            - Step 1

            Smoke Tests:
            - Test 1

            Monitoring & Alerting:
            - Alert 1
            """
        }

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        result = gates._validate_deployment_documentation(work_item)

        # Assert
        assert result is True

    def test_validate_deployment_documentation_missing_sections(self):
        """Test deployment documentation validation with missing sections."""
        # Arrange
        work_item = {
            "specification": """
            Deployment Procedure:
            - Step 1
            """
        }

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        result = gates._validate_deployment_documentation(work_item)

        # Assert
        assert result is False

    def test_check_rollback_tested_stub(self):
        """Test rollback tested check (stub implementation)."""
        # Arrange
        work_item = {"type": "deployment"}

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        result = gates._check_rollback_tested(work_item)

        # Assert
        assert result is True  # Stub always returns True


class TestQualityGatesHelperMethods:
    """Tests for helper methods and edge cases."""

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_command_validation_success(self, mock_run):
        """Test running command validation successfully."""
        # Arrange
        mock_run.return_value = Mock(returncode=0)
        rule = {"command": "echo test"}

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        result = gates._run_command_validation(rule)

        # Assert
        assert result is True

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_command_validation_failure(self, mock_run):
        """Test running command validation that fails."""
        # Arrange
        mock_run.return_value = Mock(returncode=1)
        rule = {"command": "false"}

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        result = gates._run_command_validation(rule)

        # Assert
        assert result is False

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_command_validation_exception(self, mock_run):
        """Test running command validation with exception."""
        # Arrange
        mock_run.side_effect = Exception("Command failed")
        rule = {"command": "invalid"}

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        result = gates._run_command_validation(rule)

        # Assert
        assert result is False

    def test_run_command_validation_no_command(self):
        """Test running command validation with no command specified."""
        # Arrange
        rule = {}

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        result = gates._run_command_validation(rule)

        # Assert
        assert result is True

    def test_check_file_exists_file_present(self, temp_dir):
        """Test checking file exists when file is present."""
        # Arrange
        test_file = temp_dir / "test.txt"
        test_file.touch()
        rule = {"path": str(test_file)}

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        with patch("sdd.quality.gates.Path") as mock_path:
            mock_path.return_value.exists.return_value = True
            result = gates._check_file_exists(rule)

        # Assert
        assert result is True

    def test_check_file_exists_file_missing(self):
        """Test checking file exists when file is missing."""
        # Arrange
        rule = {"path": "/nonexistent/file.txt"}

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        with patch("sdd.quality.gates.Path") as mock_path:
            mock_path.return_value.exists.return_value = False
            result = gates._check_file_exists(rule)

        # Assert
        assert result is False

    def test_check_file_exists_no_path(self):
        """Test checking file exists with no path specified."""
        # Arrange
        rule = {}

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        result = gates._check_file_exists(rule)

        # Assert
        assert result is True

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_grep_validation_pattern_found(self, mock_run):
        """Test running grep validation when pattern is found."""
        # Arrange
        mock_run.return_value = Mock(returncode=0)
        rule = {"pattern": "TODO", "files": "."}

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        result = gates._run_grep_validation(rule)

        # Assert
        assert result is True

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_grep_validation_pattern_not_found(self, mock_run):
        """Test running grep validation when pattern is not found."""
        # Arrange
        mock_run.return_value = Mock(returncode=1)
        rule = {"pattern": "NOTFOUND", "files": "."}

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        result = gates._run_grep_validation(rule)

        # Assert
        assert result is False

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_grep_validation_exception(self, mock_run):
        """Test running grep validation with exception."""
        # Arrange
        mock_run.side_effect = Exception("grep failed")
        rule = {"pattern": "test", "files": "."}

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        result = gates._run_grep_validation(rule)

        # Assert
        assert result is False

    def test_run_grep_validation_no_pattern(self):
        """Test running grep validation with no pattern specified."""
        # Arrange
        rule = {"files": "."}

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        result = gates._run_grep_validation(rule)

        # Assert
        assert result is True


class TestQualityGatesAdditionalCoverage:
    """Additional tests to increase coverage for quality_gates.py."""

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_tests_general_exception(self, mock_run):
        """Test running tests with general exception."""
        # Arrange
        mock_run.side_effect = Exception("Unexpected error")

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        passed, results = gates.run_tests(language="python")

        # Assert
        assert passed is False
        assert results["status"] == "failed"
        assert "Unexpected error" in results["reason"]

    @patch("sdd.quality.gates.subprocess.run")
    @patch("os.close")
    def test_run_security_scan_bandit_invalid_json(self, mock_close, mock_run, temp_dir):
        """Test security scan with invalid JSON in bandit output."""
        # Arrange
        temp_file = temp_dir / "bandit.json"
        temp_file.write_text("invalid json content")

        with patch("tempfile.mkstemp", return_value=(999, str(temp_file))):
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            with patch.object(Path, "exists", return_value=False):
                gates = QualityGates()

            # Act
            passed, results = gates.run_security_scan(language="python")

        # Assert
        assert passed is True  # Should pass since invalid JSON is skipped

    @patch("sdd.quality.gates.subprocess.run")
    @patch("os.close")
    def test_run_security_scan_bandit_empty_file(self, mock_close, mock_run, temp_dir):
        """Test security scan with empty bandit output file."""
        # Arrange
        temp_file = temp_dir / "bandit.json"
        temp_file.write_text("")

        with patch("tempfile.mkstemp", return_value=(999, str(temp_file))):
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            with patch.object(Path, "exists", return_value=False):
                gates = QualityGates()

            # Act
            passed, results = gates.run_security_scan(language="python")

        # Assert
        assert passed is True  # Should pass since empty file is skipped

    @patch("sdd.quality.gates.subprocess.run")
    @patch("os.close")
    def test_run_security_scan_with_safety_results(self, mock_close, mock_run, temp_dir):
        """Test security scan with both bandit and safety results."""
        # Arrange
        temp_file = temp_dir / "bandit.json"
        bandit_data = {"results": []}
        temp_file.write_text(json.dumps(bandit_data))

        safety_data = [{"vulnerability": "CVE-2023-1234", "severity": "high"}]

        with patch("tempfile.mkstemp", return_value=(999, str(temp_file))):
            mock_run.side_effect = [
                Mock(returncode=0, stdout="", stderr=""),  # bandit
                Mock(returncode=1, stdout=json.dumps(safety_data), stderr=""),  # safety
            ]

            with patch.object(Path, "exists", return_value=False):
                gates = QualityGates()

            # Act
            passed, results = gates.run_security_scan(language="python")

        # Assert
        assert "safety" in results
        assert len(results["vulnerabilities"]) > 0

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_security_scan_invalid_fail_on_threshold(self, mock_run):
        """Test security scan with invalid fail_on threshold."""
        # Arrange
        mock_run.side_effect = FileNotFoundError()

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()
        gates.config["security"]["fail_on"] = "invalid_level"

        # Act
        passed, results = gates.run_security_scan(language="python")

        # Assert
        # Should default to "HIGH" when invalid threshold specified
        assert passed is True

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_linting_timeout(self, mock_run):
        """Test linting with timeout exception."""
        # Arrange
        mock_run.side_effect = subprocess.TimeoutExpired("ruff", 120)

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()
        gates.config["linting"]["required"] = False

        # Act
        passed, results = gates.run_linting(language="python")

        # Assert
        assert passed is True
        assert results["status"] == "skipped"

    @patch("sdd.quality.gates.subprocess.run")
    def test_run_formatting_timeout(self, mock_run):
        """Test formatting with timeout exception."""
        # Arrange
        mock_run.side_effect = subprocess.TimeoutExpired("ruff", 120)

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()
        gates.config["formatting"]["required"] = False

        # Act
        passed, results = gates.run_formatting(language="python")

        # Assert
        assert passed is True
        assert results["status"] == "skipped"

    @patch("sdd.quality.gates.subprocess.run")
    def test_check_changelog_git_exception(self, mock_run):
        """Test CHANGELOG check with git exception."""
        # Arrange
        mock_run.side_effect = Exception("git error")

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        result = gates._check_changelog_updated()

        # Assert
        assert result is True  # Should skip check on error

    @patch("sdd.quality.gates.subprocess.run")
    def test_check_python_docstrings_timeout(self, mock_run):
        """Test Python docstring check with timeout."""
        # Arrange
        mock_run.side_effect = subprocess.TimeoutExpired("pydocstyle", 30)

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        result = gates._check_python_docstrings()

        # Assert
        assert result is True  # Should skip check on timeout

    @patch("sdd.quality.gates.subprocess.run")
    def test_check_readme_current_exception(self, mock_run):
        """Test README check with exception."""
        # Arrange
        mock_run.side_effect = Exception("git error")

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        result = gates._check_readme_current()

        # Assert
        assert result is True  # Should skip check on error

    def test_validate_documentation_with_work_item(self):
        """Test documentation validation with work item parameter."""
        # Arrange
        work_item = {"id": "WI-001", "type": "feature"}

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()
        gates.config["documentation"]["check_readme"] = True

        # Act
        with patch.object(gates, "_check_changelog_updated", return_value=True):
            with patch.object(gates, "_check_python_docstrings", return_value=True):
                with patch.object(gates, "_check_readme_current", return_value=True):
                    passed, results = gates.validate_documentation(work_item)

        # Assert
        assert passed is True
        assert len(results["checks"]) == 3

    def test_verify_context7_libraries_with_libraries(self):
        """Test Context7 verification with actual libraries."""
        # Arrange
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()
        gates.config["context7"] = {"enabled": True}

        stack_content = "Python 3.11\npytest 7.4.0\nruff 0.1.0\n"

        # Act
        with patch.object(Path, "exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=stack_content)):
                with patch.object(gates, "_should_verify_library", return_value=True):
                    with patch.object(gates, "_query_context7", return_value=True):
                        passed, results = gates.verify_context7_libraries()

        # Assert
        assert passed is True
        assert results["verified"] == 3
        assert results["failed"] == 0

    def test_verify_context7_libraries_with_failures(self):
        """Test Context7 verification with failed verifications."""
        # Arrange
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()
        gates.config["context7"] = {"enabled": True}

        stack_content = "Python 3.11\npytest 7.4.0\n"

        # Act
        with patch.object(Path, "exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=stack_content)):
                with patch.object(gates, "_should_verify_library", return_value=True):
                    with patch.object(gates, "_query_context7", return_value=False):
                        passed, results = gates.verify_context7_libraries()

        # Assert
        assert passed is False
        assert results["verified"] == 0
        assert results["failed"] == 2

    def test_parse_libraries_from_stack_with_comments(self):
        """Test parsing libraries with comments and empty lines."""
        # Arrange
        stack_content = "# Comment line\n\nPython 3.11\n# Another comment\npytest\n"

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        with patch("builtins.open", mock_open(read_data=stack_content)):
            libraries = gates._parse_libraries_from_stack()

        # Assert
        assert len(libraries) == 2
        assert libraries[0]["name"] == "Python"
        assert libraries[1]["name"] == "pytest"

    def test_parse_libraries_from_stack_exception(self):
        """Test parsing libraries with file read exception."""
        # Arrange
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        with patch("builtins.open", side_effect=OSError("File error")):
            libraries = gates._parse_libraries_from_stack()

        # Assert
        assert libraries == []

    def test_run_custom_validations_unknown_rule_type(self):
        """Test custom validations with unknown rule type."""
        # Arrange
        work_item = {"validation_rules": [{"type": "unknown_type", "name": "Unknown rule"}]}

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        passed, results = gates.run_custom_validations(work_item)

        # Assert
        assert passed is True  # Unknown types pass by default

    def test_run_custom_validations_project_level_rules(self):
        """Test custom validations with project-level rules."""
        # Arrange
        work_item = None

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()
        gates.config["custom_validations"] = {
            "rules": [{"type": "file_exists", "path": "/test/file", "name": "Test file"}]
        }

        # Act
        with patch("sdd.quality.gates.Path") as mock_path:
            mock_path.return_value.exists.return_value = True
            passed, results = gates.run_custom_validations(work_item)

        # Assert
        assert passed is True
        assert len(results["validations"]) == 1

    def test_run_command_validation_timeout(self):
        """Test command validation with timeout."""
        # Arrange
        rule = {"command": "sleep 100"}

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        with patch(
            "sdd.quality.gates.subprocess.run",
            side_effect=subprocess.TimeoutExpired("sleep", 60),
        ):
            result = gates._run_command_validation(rule)

        # Assert
        assert result is False

    def test_generate_report_with_context7_results(self):
        """Test report generation with Context7 results."""
        # Arrange
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        all_results = {
            "context7": {
                "status": "passed",
                "verified": 5,
                "failed": 0,
            }
        }

        # Act
        report = gates.generate_report(all_results)

        # Assert
        assert "Context7: ✓ PASSED" in report
        assert "Verified: 5" in report
        assert "Failed: 0" in report

    def test_generate_report_with_custom_validations(self):
        """Test report generation with custom validation results."""
        # Arrange
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        all_results = {
            "custom": {
                "status": "failed",
                "validations": [
                    {"name": "File exists", "passed": True, "required": True},
                    {"name": "Pattern found", "passed": False, "required": True},
                ],
            }
        }

        # Act
        report = gates.generate_report(all_results)

        # Assert
        assert "Custom Validations: ✗ FAILED" in report
        assert "✓ File exists (required)" in report
        assert "✗ Pattern found (required)" in report

    def test_get_remediation_guidance_context7_failed(self):
        """Test remediation guidance for Context7 failures."""
        # Arrange
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        guidance = gates.get_remediation_guidance(["context7"])

        # Assert
        assert "Context7 Library Verification Failed" in guidance
        assert "Review failed library versions" in guidance

    def test_get_remediation_guidance_custom_failed(self):
        """Test remediation guidance for custom validation failures."""
        # Arrange
        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        guidance = gates.get_remediation_guidance(["custom"])

        # Assert
        assert "Custom Validation Failed" in guidance
        assert "Review failed validation rules" in guidance

    @patch.object(QualityGates, "run_integration_tests")
    @patch.object(QualityGates, "run_security_scan")
    def test_run_deployment_gates_environment_fails(self, mock_security, mock_integration):
        """Test deployment gates when environment validation fails."""
        # Arrange
        work_item = {"type": "deployment"}
        mock_integration.return_value = (True, {"status": "passed"})
        mock_security.return_value = (True, {"status": "passed"})

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        with patch.object(gates, "_validate_deployment_environment", return_value=False):
            with patch.object(gates, "_validate_deployment_documentation", return_value=True):
                with patch.object(gates, "_check_rollback_tested", return_value=True):
                    passed, results = gates.run_deployment_gates(work_item)

        # Assert
        assert passed is False
        env_gate = [g for g in results["gates"] if g["name"] == "Environment Validation"][0]
        assert env_gate["passed"] is False

    @patch.object(QualityGates, "run_integration_tests")
    @patch.object(QualityGates, "run_security_scan")
    def test_run_deployment_gates_documentation_fails(self, mock_security, mock_integration):
        """Test deployment gates when documentation validation fails."""
        # Arrange
        work_item = {"type": "deployment"}
        mock_integration.return_value = (True, {"status": "passed"})
        mock_security.return_value = (True, {"status": "passed"})

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        with patch.object(gates, "_validate_deployment_environment", return_value=True):
            with patch.object(gates, "_validate_deployment_documentation", return_value=False):
                with patch.object(gates, "_check_rollback_tested", return_value=True):
                    passed, results = gates.run_deployment_gates(work_item)

        # Assert
        assert passed is False

    @patch.object(QualityGates, "run_integration_tests")
    @patch.object(QualityGates, "run_security_scan")
    def test_run_deployment_gates_rollback_fails(self, mock_security, mock_integration):
        """Test deployment gates when rollback test fails."""
        # Arrange
        work_item = {"type": "deployment"}
        mock_integration.return_value = (True, {"status": "passed"})
        mock_security.return_value = (True, {"status": "passed"})

        with patch.object(Path, "exists", return_value=False):
            gates = QualityGates()

        # Act
        with patch.object(gates, "_validate_deployment_environment", return_value=True):
            with patch.object(gates, "_validate_deployment_documentation", return_value=True):
                with patch.object(gates, "_check_rollback_tested", return_value=False):
                    passed, results = gates.run_deployment_gates(work_item)

        # Assert
        assert passed is False
