"""
Tests for environment_validator module.

Validates runtime environment (Node.js, Python) version checking and auto-installation.

Run tests:
    pytest tests/unit/init/test_environment_validator.py -v

Run with coverage:
    pytest tests/unit/init/test_environment_validator.py --cov=sdd.init.environment_validator --cov-report=term-missing

Target: 90%+ coverage
"""
import pytest
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from sdd.init.environment_validator import (
    parse_version,
    check_node_version,
    check_python_version,
    attempt_node_install_with_nvm,
    attempt_python_install_with_pyenv,
    validate_environment,
    MIN_NODE_VERSION,
    MIN_PYTHON_VERSION,
)
from sdd.core.exceptions import ValidationError, ErrorCode


class TestParseVersion:
    """Tests for parse_version()."""

    def test_parse_standard_version(self):
        """Test parsing standard version string."""
        assert parse_version("18.0.0") == (18, 0, 0)
        assert parse_version("3.11.7") == (3, 11, 7)

    def test_parse_version_with_v_prefix(self):
        """Test parsing version with 'v' prefix."""
        assert parse_version("v18.0.0") == (18, 0, 0)
        assert parse_version("v3.11.0") == (3, 11, 0)

    def test_parse_version_with_whitespace(self):
        """Test parsing version with leading/trailing whitespace."""
        assert parse_version("  18.0.0  ") == (18, 0, 0)
        assert parse_version("\n3.11.7\n") == (3, 11, 7)

    def test_parse_version_missing_patch(self):
        """Test parsing version with missing patch number."""
        assert parse_version("18.0") == (18, 0, 0)

    def test_parse_invalid_version_too_few_parts(self):
        """Test parsing invalid version with too few parts."""
        with pytest.raises(ValueError, match="Invalid version format"):
            parse_version("18")

    def test_parse_invalid_version_non_numeric(self):
        """Test parsing invalid version with non-numeric parts."""
        with pytest.raises(ValueError, match="Invalid version format"):
            parse_version("18.x.0")

    def test_parse_empty_string(self):
        """Test parsing empty string."""
        with pytest.raises(ValueError):
            parse_version("")


class TestCheckNodeVersion:
    """Tests for check_node_version()."""

    def test_node_not_installed(self):
        """Test when Node.js is not installed."""
        with patch("sdd.init.environment_validator.shutil.which", return_value=None):
            meets_req, version = check_node_version()

            assert meets_req is False
            assert version is None

    def test_node_meets_requirement(self):
        """Test when Node.js meets version requirement."""
        with patch("sdd.init.environment_validator.shutil.which", return_value="/usr/bin/node"):
            with patch("sdd.init.environment_validator.CommandRunner") as mock_runner_class:
                mock_runner = Mock()
                mock_runner_class.return_value = mock_runner
                mock_runner.run.return_value = Mock(success=True, stdout="v20.0.0")

                meets_req, version = check_node_version()

                assert meets_req is True
                assert version == "v20.0.0"

    def test_node_below_requirement(self):
        """Test when Node.js is below version requirement."""
        with patch("sdd.init.environment_validator.shutil.which", return_value="/usr/bin/node"):
            with patch("sdd.init.environment_validator.CommandRunner") as mock_runner_class:
                mock_runner = Mock()
                mock_runner_class.return_value = mock_runner
                mock_runner.run.return_value = Mock(success=True, stdout="v16.0.0")

                meets_req, version = check_node_version()

                assert meets_req is False
                assert version == "v16.0.0"

    def test_node_command_fails(self):
        """Test when node --version command fails."""
        with patch("sdd.init.environment_validator.shutil.which", return_value="/usr/bin/node"):
            with patch("sdd.init.environment_validator.CommandRunner") as mock_runner_class:
                mock_runner = Mock()
                mock_runner_class.return_value = mock_runner
                mock_runner.run.return_value = Mock(success=False, stdout="")

                meets_req, version = check_node_version()

                assert meets_req is False
                assert version is None

    def test_node_version_parse_error(self):
        """Test when version string cannot be parsed."""
        with patch("sdd.init.environment_validator.shutil.which", return_value="/usr/bin/node"):
            with patch("sdd.init.environment_validator.CommandRunner") as mock_runner_class:
                mock_runner = Mock()
                mock_runner_class.return_value = mock_runner
                mock_runner.run.return_value = Mock(success=True, stdout="invalid")

                meets_req, version = check_node_version()

                assert meets_req is False
                assert version == "invalid"


class TestCheckPythonVersion:
    """Tests for check_python_version()."""

    def test_python_not_installed(self):
        """Test when Python is not installed."""
        with patch("sdd.init.environment_validator.shutil.which", return_value=None):
            meets_req, version, binary = check_python_version()

            assert meets_req is False
            assert version is None
            assert binary is None

    def test_python_meets_requirement(self):
        """Test when Python meets version requirement."""
        with patch("sdd.init.environment_validator.shutil.which", return_value="/usr/bin/python3"):
            with patch("sdd.init.environment_validator.CommandRunner") as mock_runner_class:
                mock_runner = Mock()
                mock_runner_class.return_value = mock_runner
                mock_runner.run.return_value = Mock(success=True, stdout="Python 3.11.7")

                meets_req, version, binary = check_python_version()

                assert meets_req is True
                assert version == "3.11.7"
                assert binary == "/usr/bin/python3"

    def test_python_below_requirement(self):
        """Test when Python is below version requirement."""
        with patch("sdd.init.environment_validator.shutil.which", return_value="/usr/bin/python3"):
            with patch("sdd.init.environment_validator.CommandRunner") as mock_runner_class:
                mock_runner = Mock()
                mock_runner_class.return_value = mock_runner
                mock_runner.run.return_value = Mock(success=True, stdout="Python 3.9.0")

                meets_req, version, binary = check_python_version()

                assert meets_req is False
                assert version == "3.9.0"

    def test_python_specific_binary(self):
        """Test checking specific Python binary."""
        with patch("sdd.init.environment_validator.shutil.which", return_value="/usr/bin/python3.11"):
            with patch("sdd.init.environment_validator.CommandRunner") as mock_runner_class:
                mock_runner = Mock()
                mock_runner_class.return_value = mock_runner
                mock_runner.run.return_value = Mock(success=True, stdout="Python 3.11.0")

                meets_req, version, binary = check_python_version("python3.11")

                assert meets_req is True
                assert version == "3.11.0"
                assert binary == "/usr/bin/python3.11"

    def test_python_version_in_stderr(self):
        """Test when Python version is in stderr (Python 2.x behavior)."""
        with patch("sdd.init.environment_validator.shutil.which", return_value="/usr/bin/python"):
            with patch("sdd.init.environment_validator.CommandRunner") as mock_runner_class:
                mock_runner = Mock()
                mock_runner_class.return_value = mock_runner
                mock_runner.run.return_value = Mock(success=True, stdout="", stderr="Python 3.11.0")

                meets_req, version, binary = check_python_version("python")

                assert meets_req is True
                assert version == "3.11.0"


class TestAttemptNodeInstallWithNvm:
    """Tests for attempt_node_install_with_nvm()."""

    def test_nvm_not_installed(self, tmp_path):
        """Test when nvm is not installed."""
        with patch("sdd.init.environment_validator.Path.home", return_value=tmp_path):
            success, message = attempt_node_install_with_nvm()

            assert success is False
            assert "nvm not found" in message
            assert "brew install node" in message

    def test_nvm_install_success(self, tmp_path):
        """Test successful Node.js installation via nvm."""
        nvm_dir = tmp_path / ".nvm"
        nvm_dir.mkdir()

        with patch("sdd.init.environment_validator.Path.home", return_value=tmp_path):
            with patch("sdd.init.environment_validator.CommandRunner") as mock_runner_class:
                mock_runner = Mock()
                mock_runner_class.return_value = mock_runner
                mock_runner.run.return_value = Mock(success=True, stdout="", stderr="")

                success, message = attempt_node_install_with_nvm()

                assert success is True
                assert "installed successfully" in message.lower()

    def test_nvm_install_failure(self, tmp_path):
        """Test failed Node.js installation via nvm."""
        nvm_dir = tmp_path / ".nvm"
        nvm_dir.mkdir()

        with patch("sdd.init.environment_validator.Path.home", return_value=tmp_path):
            with patch("sdd.init.environment_validator.CommandRunner") as mock_runner_class:
                mock_runner = Mock()
                mock_runner_class.return_value = mock_runner
                mock_runner.run.return_value = Mock(success=False, stderr="Install failed")

                success, message = attempt_node_install_with_nvm()

                assert success is False
                assert "nvm installation failed" in message


class TestAttemptPythonInstallWithPyenv:
    """Tests for attempt_python_install_with_pyenv()."""

    def test_pyenv_not_installed(self):
        """Test when pyenv is not installed."""
        with patch("sdd.init.environment_validator.shutil.which", return_value=None):
            success, message = attempt_python_install_with_pyenv()

            assert success is False
            assert "pyenv not found" in message
            assert "brew install python" in message

    def test_pyenv_install_success(self):
        """Test successful Python installation via pyenv."""
        with patch("sdd.init.environment_validator.shutil.which", return_value="/usr/bin/pyenv"):
            with patch("sdd.init.environment_validator.CommandRunner") as mock_runner_class:
                mock_runner = Mock()
                mock_runner_class.return_value = mock_runner
                mock_runner.run.return_value = Mock(success=True, stdout="", stderr="")

                success, message = attempt_python_install_with_pyenv()

                assert success is True
                assert "installed successfully" in message.lower()

    def test_pyenv_install_failure(self):
        """Test failed Python installation via pyenv."""
        with patch("sdd.init.environment_validator.shutil.which", return_value="/usr/bin/pyenv"):
            with patch("sdd.init.environment_validator.CommandRunner") as mock_runner_class:
                mock_runner = Mock()
                mock_runner_class.return_value = mock_runner
                mock_runner.run.return_value = Mock(success=False, stderr="Install failed")

                success, message = attempt_python_install_with_pyenv()

                assert success is False
                assert "pyenv installation failed" in message

    def test_pyenv_custom_version(self):
        """Test installing specific Python version."""
        with patch("sdd.init.environment_validator.shutil.which", return_value="/usr/bin/pyenv"):
            with patch("sdd.init.environment_validator.CommandRunner") as mock_runner_class:
                mock_runner = Mock()
                mock_runner_class.return_value = mock_runner
                mock_runner.run.return_value = Mock(success=True)

                success, message = attempt_python_install_with_pyenv("3.12")

                assert success is True
                # Verify correct version was requested
                call_args = mock_runner.run.call_args[0][0]
                assert "3.12" in call_args


class TestValidateEnvironment:
    """Tests for validate_environment()."""

    def test_saas_t3_node_ok(self):
        """Test validation for saas_t3 stack with valid Node.js."""
        with patch("sdd.init.environment_validator.check_node_version", return_value=(True, "v20.0.0")):
            result = validate_environment("saas_t3", auto_update=False)

            assert result["node_ok"] is True
            assert result["node_version"] == "v20.0.0"
            assert len(result["errors"]) == 0

    def test_saas_t3_node_missing_no_auto_update(self):
        """Test validation for saas_t3 with missing Node.js, no auto-update."""
        with patch("sdd.init.environment_validator.check_node_version", return_value=(False, None)):
            with pytest.raises(ValidationError) as exc:
                validate_environment("saas_t3", auto_update=False)

            assert exc.value.code == ErrorCode.INVALID_CONFIGURATION
            assert "Node.js 18+ required" in str(exc.value)

    def test_saas_t3_node_auto_update_success(self):
        """Test auto-update successfully installs Node.js."""
        with patch("sdd.init.environment_validator.check_node_version") as mock_check:
            # First call: not installed, second call after install: installed
            mock_check.side_effect = [(False, None), (True, "v20.0.0")]

            with patch(
                "sdd.init.environment_validator.attempt_node_install_with_nvm",
                return_value=(True, "Success"),
            ):
                result = validate_environment("saas_t3", auto_update=True)

                assert result["node_ok"] is True
                assert result["node_version"] == "v20.0.0"

    def test_ml_ai_fastapi_python_ok(self):
        """Test validation for ml_ai_fastapi with valid Python."""
        with patch(
            "sdd.init.environment_validator.check_python_version",
            return_value=(True, "3.11.7", "/usr/bin/python3"),
        ):
            result = validate_environment("ml_ai_fastapi", auto_update=False)

            assert result["python_ok"] is True
            assert result["python_version"] == "3.11.7"
            assert result["python_binary"] == "/usr/bin/python3"

    def test_ml_ai_fastapi_python_missing_no_auto_update(self):
        """Test validation for ml_ai_fastapi with missing Python, no auto-update."""
        with patch("sdd.init.environment_validator.check_python_version", return_value=(False, None, None)):
            # Check for python3.11 specifically also fails
            with patch("sdd.init.environment_validator.check_python_version", return_value=(False, None, None)):
                with pytest.raises(ValidationError) as exc:
                    validate_environment("ml_ai_fastapi", auto_update=False)

                assert "Python 3.11+ required" in str(exc.value)

    def test_ml_ai_fastapi_finds_python311_specifically(self):
        """Test that it checks for python3.11 specifically if default fails."""
        with patch("sdd.init.environment_validator.check_python_version") as mock_check:
            # First call with no args: fails
            # Second call with "python3.11": succeeds
            mock_check.side_effect = [
                (False, "3.9.0", "/usr/bin/python3"),
                (True, "3.11.0", "/usr/bin/python3.11"),
            ]

            result = validate_environment("ml_ai_fastapi", auto_update=False)

            assert result["python_ok"] is True
            assert result["python_version"] == "3.11.0"

    def test_dashboard_refine_requires_node(self):
        """Test validation for dashboard_refine stack."""
        with patch("sdd.init.environment_validator.check_node_version", return_value=(True, "v18.0.0")):
            result = validate_environment("dashboard_refine", auto_update=False)

            assert result["node_ok"] is True

    def test_fullstack_nextjs_requires_node(self):
        """Test validation for fullstack_nextjs stack."""
        with patch("sdd.init.environment_validator.check_node_version", return_value=(True, "v20.0.0")):
            result = validate_environment("fullstack_nextjs", auto_update=False)

            assert result["node_ok"] is True

    def test_error_context_includes_stack_info(self):
        """Test that validation error includes stack context."""
        with patch("sdd.init.environment_validator.check_node_version", return_value=(False, None)):
            with pytest.raises(ValidationError) as exc:
                validate_environment("saas_t3", auto_update=False)

            assert "stack_type" in exc.value.context
            assert exc.value.context["stack_type"] == "saas_t3"
