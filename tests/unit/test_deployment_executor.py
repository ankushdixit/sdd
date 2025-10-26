"""Unit tests for DeploymentExecutor class.

This module tests the deployment execution framework including:
- Class initialization and configuration
- Pre-deployment validation
- Deployment execution
- Smoke test execution
- Rollback procedures
- Deployment logging
"""

import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from sdd.deployment.executor import DeploymentExecutor


@pytest.fixture
def sample_work_item():
    """Create a sample deployment work item."""
    return {
        "id": "DEPLOY-001",
        "type": "deployment",
        "title": "Production Deployment",
        "specification": """
## Deployment Procedure
### Deployment Steps
1. Pull code
2. Build
""",
    }


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory with config file."""
    temp_dir = tempfile.mkdtemp()
    config_dir = Path(temp_dir) / ".session"
    config_dir.mkdir(parents=True)

    # Create a basic config file
    config_path = config_dir / "config.json"
    config = {
        "deployment": {
            "pre_deployment_checks": {
                "integration_tests": True,
                "security_scans": True,
                "environment_validation": True,
            },
            "smoke_tests": {"enabled": True, "timeout": 300, "retry_count": 3},
            "rollback": {"automatic": True, "on_smoke_test_failure": True},
            "environments": {
                "staging": {"auto_deploy": True},
                "production": {"auto_deploy": False},
            },
        }
    }
    config_path.write_text(json.dumps(config))

    original_cwd = Path.cwd()
    import os

    os.chdir(temp_dir)

    yield temp_dir

    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)


class TestDeploymentExecutorInit:
    """Tests for DeploymentExecutor initialization."""

    def test_init_with_work_item(self, sample_work_item):
        """Test that DeploymentExecutor initializes with a work item."""
        # Arrange & Act
        executor = DeploymentExecutor(sample_work_item)

        # Assert
        assert executor.work_item == sample_work_item
        assert executor.config is not None
        assert isinstance(executor.deployment_log, list)

    def test_init_loads_default_config_when_no_file(self, sample_work_item):
        """Test that DeploymentExecutor loads default config when config file doesn't exist."""
        # Arrange & Act
        executor = DeploymentExecutor(sample_work_item)

        # Assert
        assert "pre_deployment_checks" in executor.config
        assert "smoke_tests" in executor.config
        assert "rollback" in executor.config
        assert "environments" in executor.config

    def test_init_loads_config_from_file(self, sample_work_item, temp_config_dir):
        """Test that DeploymentExecutor loads config from file when it exists."""
        # Arrange
        config_path = Path(".session/config.json")

        # Act
        executor = DeploymentExecutor(sample_work_item, config_path=config_path)

        # Assert
        assert executor.config is not None
        assert executor.config["pre_deployment_checks"]["integration_tests"] is True


class TestDeploymentExecutorMethods:
    """Tests for DeploymentExecutor method existence."""

    def test_has_pre_deployment_validation_method(self, sample_work_item):
        """Test that DeploymentExecutor has pre_deployment_validation method."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)

        # Act & Assert
        assert hasattr(executor, "pre_deployment_validation")
        assert callable(executor.pre_deployment_validation)

    def test_has_execute_deployment_method(self, sample_work_item):
        """Test that DeploymentExecutor has execute_deployment method."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)

        # Act & Assert
        assert hasattr(executor, "execute_deployment")
        assert callable(executor.execute_deployment)

    def test_has_run_smoke_tests_method(self, sample_work_item):
        """Test that DeploymentExecutor has run_smoke_tests method."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)

        # Act & Assert
        assert hasattr(executor, "run_smoke_tests")
        assert callable(executor.run_smoke_tests)

    def test_has_rollback_method(self, sample_work_item):
        """Test that DeploymentExecutor has rollback method."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)

        # Act & Assert
        assert hasattr(executor, "rollback")
        assert callable(executor.rollback)

    def test_has_private_check_methods(self, sample_work_item):
        """Test that DeploymentExecutor has all required private check methods."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)

        required_methods = [
            "_check_integration_tests",
            "_check_security_scans",
            "_check_environment_readiness",
            "_parse_deployment_steps",
            "_execute_deployment_step",
            "_parse_smoke_tests",
            "_execute_smoke_test",
            "_parse_rollback_steps",
            "_execute_rollback_step",
        ]

        # Act & Assert
        for method in required_methods:
            assert hasattr(executor, method), f"Method {method} should exist"
            assert callable(getattr(executor, method)), f"Method {method} should be callable"

    def test_has_get_deployment_log_method(self, sample_work_item):
        """Test that DeploymentExecutor has get_deployment_log method."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)

        # Act & Assert
        assert hasattr(executor, "get_deployment_log")
        assert callable(executor.get_deployment_log)


class TestDefaultConfiguration:
    """Tests for default configuration structure."""

    def test_default_config_has_required_keys(self, sample_work_item):
        """Test that default configuration has all required keys."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)

        required_keys = ["pre_deployment_checks", "smoke_tests", "rollback", "environments"]

        # Act & Assert
        for key in required_keys:
            assert key in executor.config, f"Config should have key: {key}"

    def test_pre_deployment_checks_structure(self, sample_work_item):
        """Test that pre_deployment_checks has correct structure."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)

        # Act
        checks = executor.config["pre_deployment_checks"]

        # Assert
        assert "integration_tests" in checks
        assert "security_scans" in checks
        assert "environment_validation" in checks

    def test_smoke_tests_config_structure(self, sample_work_item):
        """Test that smoke_tests config has correct structure."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)

        # Act
        smoke_config = executor.config["smoke_tests"]

        # Assert
        assert "enabled" in smoke_config
        assert "timeout" in smoke_config
        assert "retry_count" in smoke_config

    def test_rollback_config_structure(self, sample_work_item):
        """Test that rollback config has correct structure."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)

        # Act
        rollback_config = executor.config["rollback"]

        # Assert
        assert "automatic" in rollback_config
        assert "on_smoke_test_failure" in rollback_config

    def test_environments_config_structure(self, sample_work_item):
        """Test that environments config has correct structure."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)

        # Act
        env_config = executor.config["environments"]

        # Assert
        assert "staging" in env_config
        assert "production" in env_config


class TestPreDeploymentValidation:
    """Tests for pre-deployment validation."""

    def test_pre_deployment_validation_returns_results(self, sample_work_item):
        """Test that pre_deployment_validation returns results with correct structure."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)

        # Act
        passed, results = executor.pre_deployment_validation()

        # Assert
        assert "checks" in results
        assert "passed" in results
        assert isinstance(results["checks"], list)
        assert isinstance(passed, bool)

    def test_pre_deployment_validation_includes_integration_tests(self, sample_work_item):
        """Test that pre_deployment_validation includes integration tests check."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)
        executor.config["pre_deployment_checks"]["integration_tests"] = True

        # Act
        passed, results = executor.pre_deployment_validation()

        # Assert
        check_names = [check["name"] for check in results["checks"]]
        assert "Integration Tests" in check_names

    def test_pre_deployment_validation_includes_security_scans(self, sample_work_item):
        """Test that pre_deployment_validation includes security scans check."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)
        executor.config["pre_deployment_checks"]["security_scans"] = True

        # Act
        passed, results = executor.pre_deployment_validation()

        # Assert
        check_names = [check["name"] for check in results["checks"]]
        assert "Security Scans" in check_names

    def test_pre_deployment_validation_includes_environment_readiness(self, sample_work_item):
        """Test that pre_deployment_validation includes environment readiness check."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)
        executor.config["pre_deployment_checks"]["environment_validation"] = True

        # Act
        passed, results = executor.pre_deployment_validation()

        # Assert
        check_names = [check["name"] for check in results["checks"]]
        assert "Environment Readiness" in check_names


class TestDeploymentExecution:
    """Tests for deployment execution."""

    def test_execute_deployment_returns_timestamped_results(self, sample_work_item):
        """Test that execute_deployment returns results with timestamps."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)

        # Act
        success, results = executor.execute_deployment(dry_run=True)

        # Assert
        assert "started_at" in results
        assert "completed_at" in results
        assert "steps" in results
        assert "success" in results

    def test_execute_deployment_dry_run_succeeds(self, sample_work_item):
        """Test that execute_deployment succeeds in dry-run mode."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)

        # Act
        success, results = executor.execute_deployment(dry_run=True)

        # Assert
        assert success is True
        assert results["success"] is True

    def test_execute_deployment_logs_to_deployment_log(self, sample_work_item):
        """Test that execute_deployment adds entries to deployment log."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)

        # Act
        executor.execute_deployment(dry_run=True)
        log = executor.get_deployment_log()

        # Assert
        assert len(log) > 0
        assert any("Deployment started" in entry["event"] for entry in log)


class TestSmokeTests:
    """Tests for smoke test execution."""

    def test_run_smoke_tests_returns_results(self, sample_work_item):
        """Test that run_smoke_tests returns results with correct structure."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)

        # Act
        passed, results = executor.run_smoke_tests()

        # Assert
        assert isinstance(passed, bool)
        assert isinstance(results, dict)
        assert "tests" in results or "status" in results

    def test_run_smoke_tests_uses_configuration(self, sample_work_item):
        """Test that run_smoke_tests uses smoke test configuration."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)

        # Act
        passed, results = executor.run_smoke_tests()

        # Assert
        assert executor.config["smoke_tests"]["enabled"] is not None

    def test_run_smoke_tests_skips_when_disabled(self, sample_work_item):
        """Test that run_smoke_tests skips when disabled in config."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)
        executor.config["smoke_tests"]["enabled"] = False

        # Act
        passed, results = executor.run_smoke_tests()

        # Assert
        assert passed is True
        assert results.get("status") == "skipped"


class TestRollback:
    """Tests for rollback functionality."""

    def test_rollback_returns_timestamped_results(self, sample_work_item):
        """Test that rollback returns results with timestamps."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)

        # Act
        success, results = executor.rollback()

        # Assert
        assert "started_at" in results
        assert "completed_at" in results
        assert isinstance(success, bool)

    def test_rollback_tracks_steps(self, sample_work_item):
        """Test that rollback tracks executed steps."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)

        # Act
        success, results = executor.rollback()

        # Assert
        assert "steps" in results
        assert isinstance(results["steps"], list)

    def test_rollback_logs_to_deployment_log(self, sample_work_item):
        """Test that rollback adds entries to deployment log."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)

        # Act
        executor.rollback()
        log = executor.get_deployment_log()

        # Assert
        assert len(log) > 0
        assert any("Rollback" in entry["event"] for entry in log)


class TestDeploymentLogging:
    """Tests for deployment logging."""

    def test_get_deployment_log_returns_list(self, sample_work_item):
        """Test that get_deployment_log returns a list."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)

        # Act
        log = executor.get_deployment_log()

        # Assert
        assert isinstance(log, list)

    def test_deployment_log_captures_events(self, sample_work_item):
        """Test that deployment log captures events during operations."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)

        # Act
        executor.pre_deployment_validation()
        executor.execute_deployment(dry_run=True)
        log = executor.get_deployment_log()

        # Assert
        assert len(log) > 0
        assert all("timestamp" in entry for entry in log)
        assert all("event" in entry for entry in log)
        assert all("data" in entry for entry in log)


class TestConfigurationLoading:
    """Tests for configuration loading edge cases."""

    def test_load_config_with_missing_deployment_key(self, sample_work_item, temp_config_dir):
        """Test that _load_config returns default config when deployment key missing."""
        # Arrange
        config_path = Path(".session/config.json")
        config_path.write_text(json.dumps({"other_key": "value"}))

        # Act
        executor = DeploymentExecutor(sample_work_item, config_path=config_path)

        # Assert
        assert "pre_deployment_checks" in executor.config
        assert "smoke_tests" in executor.config


class TestPreDeploymentValidationFailures:
    """Tests for pre-deployment validation failure scenarios."""

    def test_pre_deployment_validation_fails_when_integration_tests_fail(self, sample_work_item):
        """Test that pre_deployment_validation fails when integration tests fail."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)
        executor.config["pre_deployment_checks"]["integration_tests"] = True

        with patch.object(executor, "_check_integration_tests", return_value=False):
            # Act
            passed, results = executor.pre_deployment_validation()

        # Assert
        assert passed is False
        assert results["passed"] is False

    def test_pre_deployment_validation_fails_when_security_scans_fail(self, sample_work_item):
        """Test that pre_deployment_validation fails when security scans fail."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)
        executor.config["pre_deployment_checks"]["security_scans"] = True

        with patch.object(executor, "_check_security_scans", return_value=False):
            # Act
            passed, results = executor.pre_deployment_validation()

        # Assert
        assert passed is False
        assert results["passed"] is False

    def test_pre_deployment_validation_fails_when_environment_not_ready(self, sample_work_item):
        """Test that pre_deployment_validation fails when environment not ready."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)
        executor.config["pre_deployment_checks"]["environment_validation"] = True

        with patch.object(executor, "_check_environment_readiness", return_value=False):
            # Act
            passed, results = executor.pre_deployment_validation()

        # Assert
        assert passed is False
        assert results["passed"] is False


class TestDeploymentExecutionFailures:
    """Tests for deployment execution failure scenarios."""

    def test_execute_deployment_fails_when_step_fails(self, sample_work_item):
        """Test that execute_deployment fails when a step fails."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)

        with patch.object(
            executor, "_parse_deployment_steps", return_value=["step1", "step2", "step3"]
        ):
            with patch.object(
                executor, "_execute_deployment_step", side_effect=[True, False, True]
            ):
                # Act
                success, results = executor.execute_deployment()

        # Assert
        assert success is False
        assert results["success"] is False
        assert results["failed_at_step"] == 2
        assert len(results["steps"]) == 2  # Should stop after failed step

    def test_execute_deployment_stops_on_first_failure(self, sample_work_item):
        """Test that execute_deployment stops executing steps after first failure."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)
        steps_executed = []

        def track_step(step):
            steps_executed.append(step)
            return len(steps_executed) != 2  # Fail on second step

        with patch.object(
            executor, "_parse_deployment_steps", return_value=["step1", "step2", "step3"]
        ):
            with patch.object(executor, "_execute_deployment_step", side_effect=track_step):
                # Act
                success, results = executor.execute_deployment()

        # Assert
        assert len(steps_executed) == 2  # Should have executed only 2 steps
        assert success is False


class TestSmokeTestsExecution:
    """Tests for smoke test execution when enabled."""

    def test_run_smoke_tests_executes_when_enabled(self, sample_work_item):
        """Test that run_smoke_tests executes tests when enabled."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)
        executor.config["smoke_tests"]["enabled"] = True

        test_list = [{"name": "test1"}, {"name": "test2"}]
        with patch.object(executor, "_parse_smoke_tests", return_value=test_list):
            with patch.object(executor, "_execute_smoke_test", return_value=True):
                # Act
                passed, results = executor.run_smoke_tests()

        # Assert
        assert passed is True
        assert len(results["tests"]) == 2

    def test_run_smoke_tests_fails_when_test_fails(self, sample_work_item):
        """Test that run_smoke_tests fails when a test fails."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)
        executor.config["smoke_tests"]["enabled"] = True

        test_list = [{"name": "test1"}, {"name": "test2"}]
        with patch.object(executor, "_parse_smoke_tests", return_value=test_list):
            with patch.object(executor, "_execute_smoke_test", side_effect=[True, False]):
                # Act
                passed, results = executor.run_smoke_tests()

        # Assert
        assert passed is False
        assert results["passed"] is False

    def test_run_smoke_tests_passes_config_to_executor(self, sample_work_item):
        """Test that run_smoke_tests passes timeout and retry config to test executor."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)
        executor.config["smoke_tests"]["enabled"] = True
        executor.config["smoke_tests"]["timeout"] = 600
        executor.config["smoke_tests"]["retry_count"] = 5

        test_list = [{"name": "test1"}]
        with patch.object(executor, "_parse_smoke_tests", return_value=test_list):
            with patch.object(executor, "_execute_smoke_test", return_value=True) as mock_execute:
                # Act
                executor.run_smoke_tests()

        # Assert
        mock_execute.assert_called_with(test_list[0], timeout=600, retry_count=5)


class TestRollbackFailures:
    """Tests for rollback failure scenarios."""

    def test_rollback_fails_when_step_fails(self, sample_work_item):
        """Test that rollback fails when a rollback step fails."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)

        with patch.object(
            executor, "_parse_rollback_steps", return_value=["rollback1", "rollback2"]
        ):
            with patch.object(executor, "_execute_rollback_step", side_effect=[True, False]):
                # Act
                success, results = executor.rollback()

        # Assert
        assert success is False
        assert results["success"] is False
        assert results["failed_at_step"] == 2

    def test_rollback_stops_on_first_failure(self, sample_work_item):
        """Test that rollback stops executing steps after first failure."""
        # Arrange
        executor = DeploymentExecutor(sample_work_item)
        steps_executed = []

        def track_step(step):
            steps_executed.append(step)
            return len(steps_executed) != 1  # Fail on first step

        with patch.object(executor, "_parse_rollback_steps", return_value=["rb1", "rb2", "rb3"]):
            with patch.object(executor, "_execute_rollback_step", side_effect=track_step):
                # Act
                success, results = executor.rollback()

        # Assert
        assert len(steps_executed) == 1  # Should have executed only 1 step before failing
        assert success is False


class TestMainCLI:
    """Tests for main CLI function."""

    @patch("sdd.deployment.executor.DeploymentExecutor")
    def test_main_executes_full_workflow(self, mock_executor_class):
        """Test that main executes the full deployment workflow."""
        # Arrange
        mock_executor = Mock()
        mock_executor.pre_deployment_validation.return_value = (True, {})
        mock_executor.execute_deployment.return_value = (True, {})
        mock_executor.run_smoke_tests.return_value = (True, {})
        mock_executor_class.return_value = mock_executor

        with patch("sys.argv", ["deployment_executor.py", "WORK-001"]):
            # Act
            from sdd.deployment.executor import main

            result = main()

        # Assert
        assert result is None  # main() prints but doesn't return a value
        mock_executor.pre_deployment_validation.assert_called_once()
        mock_executor.execute_deployment.assert_called_once()
        mock_executor.run_smoke_tests.assert_called_once()

    @patch("sdd.deployment.executor.DeploymentExecutor")
    def test_main_exits_when_pre_deployment_fails(self, mock_executor_class):
        """Test that main exits when pre-deployment validation fails."""
        # Arrange
        mock_executor = Mock()
        mock_executor.pre_deployment_validation.return_value = (False, {})
        mock_executor_class.return_value = mock_executor

        with patch("sys.argv", ["deployment_executor.py", "WORK-001"]):
            # Act
            from sdd.deployment.executor import main

            with pytest.raises(SystemExit) as exc_info:
                main()

        # Assert
        assert exc_info.value.code == 1

    @patch("sdd.deployment.executor.DeploymentExecutor")
    def test_main_rolls_back_when_deployment_fails(self, mock_executor_class):
        """Test that main initiates rollback when deployment fails."""
        # Arrange
        mock_executor = Mock()
        mock_executor.pre_deployment_validation.return_value = (True, {})
        mock_executor.execute_deployment.return_value = (False, {})
        mock_executor_class.return_value = mock_executor

        with patch("sys.argv", ["deployment_executor.py", "WORK-001"]):
            # Act
            from sdd.deployment.executor import main

            with pytest.raises(SystemExit) as exc_info:
                main()

        # Assert
        assert exc_info.value.code == 1
        mock_executor.rollback.assert_called_once()

    @patch("sdd.deployment.executor.DeploymentExecutor")
    def test_main_rolls_back_when_smoke_tests_fail(self, mock_executor_class):
        """Test that main initiates rollback when smoke tests fail."""
        # Arrange
        mock_executor = Mock()
        mock_executor.pre_deployment_validation.return_value = (True, {})
        mock_executor.execute_deployment.return_value = (True, {})
        mock_executor.run_smoke_tests.return_value = (False, {})
        mock_executor_class.return_value = mock_executor

        with patch("sys.argv", ["deployment_executor.py", "WORK-001"]):
            # Act
            from sdd.deployment.executor import main

            with pytest.raises(SystemExit) as exc_info:
                main()

        # Assert
        assert exc_info.value.code == 1
        mock_executor.rollback.assert_called_once()

    def test_main_requires_work_item_argument(self):
        """Test that main exits with error when no work item ID provided."""
        # Arrange & Act
        with patch("sys.argv", ["deployment_executor.py"]):
            from sdd.deployment.executor import main

            with pytest.raises(SystemExit) as exc_info:
                main()

        # Assert
        assert exc_info.value.code == 1
