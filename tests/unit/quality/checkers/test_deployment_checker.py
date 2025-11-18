"""Unit tests for deployment.py DeploymentChecker.

Tests for the DeploymentChecker class which orchestrates deployment quality gates
including integration tests, security scans, environment validation, deployment
documentation, and rollback procedure testing.
"""

from unittest.mock import Mock, patch

import pytest

from solokit.core.command_runner import CommandRunner
from solokit.quality.checkers.base import CheckResult
from solokit.quality.checkers.deployment import DeploymentChecker


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project directory."""
    return tmp_path


@pytest.fixture
def mock_runner():
    """Create a mock CommandRunner."""
    return Mock(spec=CommandRunner)


@pytest.fixture
def deployment_config():
    """Standard deployment configuration."""
    return {
        "enabled": True,
        "integration_tests": {"enabled": True},
        "security_scans": {"enabled": True},
    }


@pytest.fixture
def deployment_work_item():
    """Standard deployment work item with complete documentation."""
    return {
        "id": "WI-DEPLOY-001",
        "type": "deployment",
        "title": "Deploy to Production",
        "specification": """
        # Deployment to Production

        ## Environment: production

        ## Deployment Procedure
        1. Build application
        2. Run migrations
        3. Deploy to staging
        4. Run smoke tests
        5. Deploy to production

        ## Rollback Procedure
        1. Revert deployment
        2. Rollback database migrations
        3. Verify system stability

        ## Smoke Tests
        - Health endpoint returns 200
        - Database connectivity check
        - API response time < 200ms

        ## Monitoring & Alerting
        - Datadog dashboard configured
        - PagerDuty alerts set up
        - Slack notifications enabled
        """,
    }


@pytest.fixture
def incomplete_deployment_work_item():
    """Deployment work item with incomplete documentation."""
    return {
        "id": "WI-DEPLOY-002",
        "type": "deployment",
        "title": "Deploy to Staging",
        "specification": """
        # Deployment to Staging

        ## Deployment Procedure
        1. Build application
        2. Deploy to staging
        """,
    }


class TestDeploymentCheckerInit:
    """Tests for DeploymentChecker initialization."""

    def test_init_with_defaults(self, deployment_config, deployment_work_item):
        """Test initialization with default parameters."""
        checker = DeploymentChecker(deployment_work_item, deployment_config)

        assert checker.config == deployment_config
        assert checker.work_item == deployment_work_item
        assert checker.runner is not None
        assert isinstance(checker.runner, CommandRunner)

    def test_init_with_custom_runner(self, deployment_config, deployment_work_item, mock_runner):
        """Test initialization with custom runner."""
        checker = DeploymentChecker(deployment_work_item, deployment_config, runner=mock_runner)

        assert checker.runner is mock_runner

    def test_init_with_custom_project_root(
        self, deployment_config, deployment_work_item, temp_project_dir
    ):
        """Test initialization with custom project root."""
        checker = DeploymentChecker(
            deployment_work_item,
            deployment_config,
            project_root=temp_project_dir,
        )

        assert checker.project_root == temp_project_dir

    def test_init_stores_work_item(self, deployment_config, deployment_work_item):
        """Test initialization stores work item."""
        checker = DeploymentChecker(deployment_work_item, deployment_config)

        assert checker.work_item == deployment_work_item
        assert checker.work_item["type"] == "deployment"


class TestDeploymentCheckerInterface:
    """Tests for DeploymentChecker interface methods."""

    def test_name_returns_deployment(self, deployment_config, deployment_work_item):
        """Test name() returns 'deployment'."""
        checker = DeploymentChecker(deployment_work_item, deployment_config)

        assert checker.name() == "deployment"

    def test_is_enabled_returns_true_by_default(self, deployment_work_item):
        """Test is_enabled() returns True by default."""
        config = {}
        checker = DeploymentChecker(deployment_work_item, config)

        assert checker.is_enabled() is True

    def test_is_enabled_returns_config_value(self, deployment_work_item):
        """Test is_enabled() returns config value."""
        config = {"enabled": False}
        checker = DeploymentChecker(deployment_work_item, config)

        assert checker.is_enabled() is False


class TestDeploymentCheckerRun:
    """Tests for DeploymentChecker.run() method."""

    def test_run_returns_skipped_when_disabled(self, deployment_work_item):
        """Test run() returns skipped result when disabled."""
        config = {"enabled": False}
        checker = DeploymentChecker(deployment_work_item, config)

        result = checker.run()

        assert result.checker_name == "deployment"
        assert result.passed is True
        assert result.status == "skipped"
        assert result.info.get("reason") == "disabled"

    @patch("solokit.quality.checkers.integration.IntegrationChecker")
    @patch("solokit.quality.checkers.security.SecurityChecker")
    def test_run_passes_when_all_gates_pass(
        self,
        mock_security_checker_class,
        mock_integration_checker_class,
        deployment_config,
        deployment_work_item,
        mock_runner,
    ):
        """Test run() passes when all gates pass."""
        # Mock IntegrationChecker
        mock_integration_instance = Mock()
        mock_integration_checker_class.return_value = mock_integration_instance
        mock_integration_instance.is_enabled.return_value = True
        mock_integration_instance.run.return_value = CheckResult(
            checker_name="integration",
            passed=True,
            status="passed",
            errors=[],
            warnings=[],
            info={"tests_passed": 10},
        )

        # Mock SecurityChecker
        mock_security_instance = Mock()
        mock_security_checker_class.return_value = mock_security_instance
        mock_security_instance.is_enabled.return_value = True
        mock_security_instance.run.return_value = CheckResult(
            checker_name="security",
            passed=True,
            status="passed",
            errors=[],
            warnings=[],
            info={"vulnerabilities": 0},
        )

        checker = DeploymentChecker(deployment_work_item, deployment_config, runner=mock_runner)

        with patch.object(checker, "_validate_deployment_environment", return_value=True):
            with patch.object(checker, "_validate_deployment_documentation", return_value=True):
                with patch.object(checker, "_check_rollback_tested", return_value=True):
                    result = checker.run()

        assert result.checker_name == "deployment"
        assert result.passed is True
        assert result.status == "passed"
        assert len(result.errors) == 0
        assert "gates" in result.info
        assert len(result.info["gates"]) == 5  # 5 gates total

    @patch("solokit.quality.checkers.integration.IntegrationChecker")
    @patch("solokit.quality.checkers.security.SecurityChecker")
    def test_run_fails_when_integration_tests_fail(
        self,
        mock_security_checker_class,
        mock_integration_checker_class,
        deployment_config,
        deployment_work_item,
        mock_runner,
    ):
        """Test run() fails when integration tests fail."""
        # Mock IntegrationChecker - failed
        mock_integration_instance = Mock()
        mock_integration_checker_class.return_value = mock_integration_instance
        mock_integration_instance.is_enabled.return_value = True
        mock_integration_instance.run.return_value = CheckResult(
            checker_name="integration",
            passed=False,
            status="failed",
            errors=[{"message": "Integration test failed"}],
            warnings=[],
            info={},
        )

        # Mock SecurityChecker - passed
        mock_security_instance = Mock()
        mock_security_checker_class.return_value = mock_security_instance
        mock_security_instance.is_enabled.return_value = True
        mock_security_instance.run.return_value = CheckResult(
            checker_name="security",
            passed=True,
            status="passed",
            errors=[],
            warnings=[],
            info={},
        )

        checker = DeploymentChecker(deployment_work_item, deployment_config, runner=mock_runner)

        with patch.object(checker, "_validate_deployment_environment", return_value=True):
            with patch.object(checker, "_validate_deployment_documentation", return_value=True):
                with patch.object(checker, "_check_rollback_tested", return_value=True):
                    result = checker.run()

        assert result.passed is False
        assert result.status == "failed"
        assert len(result.errors) > 0
        assert any("Integration Tests" in str(e.get("gate", "")) for e in result.errors)

    @patch("solokit.quality.checkers.integration.IntegrationChecker")
    @patch("solokit.quality.checkers.security.SecurityChecker")
    def test_run_fails_when_security_scans_fail(
        self,
        mock_security_checker_class,
        mock_integration_checker_class,
        deployment_config,
        deployment_work_item,
        mock_runner,
    ):
        """Test run() fails when security scans fail."""
        # Mock IntegrationChecker - passed
        mock_integration_instance = Mock()
        mock_integration_checker_class.return_value = mock_integration_instance
        mock_integration_instance.is_enabled.return_value = True
        mock_integration_instance.run.return_value = CheckResult(
            checker_name="integration",
            passed=True,
            status="passed",
            errors=[],
            warnings=[],
            info={},
        )

        # Mock SecurityChecker - failed
        mock_security_instance = Mock()
        mock_security_checker_class.return_value = mock_security_instance
        mock_security_instance.is_enabled.return_value = True
        mock_security_instance.run.return_value = CheckResult(
            checker_name="security",
            passed=False,
            status="failed",
            errors=[{"message": "High severity vulnerability found"}],
            warnings=[],
            info={},
        )

        checker = DeploymentChecker(deployment_work_item, deployment_config, runner=mock_runner)

        with patch.object(checker, "_validate_deployment_environment", return_value=True):
            with patch.object(checker, "_validate_deployment_documentation", return_value=True):
                with patch.object(checker, "_check_rollback_tested", return_value=True):
                    result = checker.run()

        assert result.passed is False
        assert result.status == "failed"
        assert len(result.errors) > 0
        assert any("Security Scans" in str(e.get("gate", "")) for e in result.errors)

    @patch("solokit.quality.checkers.integration.IntegrationChecker")
    @patch("solokit.quality.checkers.security.SecurityChecker")
    def test_run_fails_when_environment_validation_fails(
        self,
        mock_security_checker_class,
        mock_integration_checker_class,
        deployment_config,
        deployment_work_item,
        mock_runner,
    ):
        """Test run() fails when environment validation fails."""
        # Mock checkers - all pass
        mock_integration_instance = Mock()
        mock_integration_checker_class.return_value = mock_integration_instance
        mock_integration_instance.is_enabled.return_value = True
        mock_integration_instance.run.return_value = CheckResult(
            checker_name="integration",
            passed=True,
            status="passed",
            errors=[],
            warnings=[],
            info={},
        )

        mock_security_instance = Mock()
        mock_security_checker_class.return_value = mock_security_instance
        mock_security_instance.is_enabled.return_value = True
        mock_security_instance.run.return_value = CheckResult(
            checker_name="security",
            passed=True,
            status="passed",
            errors=[],
            warnings=[],
            info={},
        )

        checker = DeploymentChecker(deployment_work_item, deployment_config, runner=mock_runner)

        # Environment validation fails
        with patch.object(checker, "_validate_deployment_environment", return_value=False):
            with patch.object(checker, "_validate_deployment_documentation", return_value=True):
                with patch.object(checker, "_check_rollback_tested", return_value=True):
                    result = checker.run()

        assert result.passed is False
        assert result.status == "failed"
        assert len(result.errors) > 0
        assert any("Environment Validation" in str(e.get("gate", "")) for e in result.errors)

    @patch("solokit.quality.checkers.integration.IntegrationChecker")
    @patch("solokit.quality.checkers.security.SecurityChecker")
    def test_run_fails_when_documentation_incomplete(
        self,
        mock_security_checker_class,
        mock_integration_checker_class,
        deployment_config,
        deployment_work_item,
        mock_runner,
    ):
        """Test run() fails when documentation is incomplete."""
        # Mock checkers - all pass
        mock_integration_instance = Mock()
        mock_integration_checker_class.return_value = mock_integration_instance
        mock_integration_instance.is_enabled.return_value = True
        mock_integration_instance.run.return_value = CheckResult(
            checker_name="integration",
            passed=True,
            status="passed",
            errors=[],
            warnings=[],
            info={},
        )

        mock_security_instance = Mock()
        mock_security_checker_class.return_value = mock_security_instance
        mock_security_instance.is_enabled.return_value = True
        mock_security_instance.run.return_value = CheckResult(
            checker_name="security",
            passed=True,
            status="passed",
            errors=[],
            warnings=[],
            info={},
        )

        checker = DeploymentChecker(deployment_work_item, deployment_config, runner=mock_runner)

        # Documentation validation fails
        with patch.object(checker, "_validate_deployment_environment", return_value=True):
            with patch.object(checker, "_validate_deployment_documentation", return_value=False):
                with patch.object(checker, "_check_rollback_tested", return_value=True):
                    result = checker.run()

        assert result.passed is False
        assert result.status == "failed"
        assert len(result.errors) > 0
        assert any("Deployment Documentation" in str(e.get("gate", "")) for e in result.errors)

    @patch("solokit.quality.checkers.integration.IntegrationChecker")
    @patch("solokit.quality.checkers.security.SecurityChecker")
    def test_run_handles_integration_checker_not_available(
        self,
        mock_security_checker_class,
        mock_integration_checker_class,
        deployment_config,
        deployment_work_item,
        mock_runner,
    ):
        """Test run() handles IntegrationChecker import error gracefully."""
        # Mock IntegrationChecker to raise ImportError
        mock_integration_checker_class.side_effect = ImportError("Module not found")

        # Mock SecurityChecker - passed
        mock_security_instance = Mock()
        mock_security_checker_class.return_value = mock_security_instance
        mock_security_instance.is_enabled.return_value = True
        mock_security_instance.run.return_value = CheckResult(
            checker_name="security",
            passed=True,
            status="passed",
            errors=[],
            warnings=[],
            info={},
        )

        checker = DeploymentChecker(deployment_work_item, deployment_config, runner=mock_runner)

        with patch.object(checker, "_validate_deployment_environment", return_value=True):
            with patch.object(checker, "_validate_deployment_documentation", return_value=True):
                with patch.object(checker, "_check_rollback_tested", return_value=True):
                    result = checker.run()

        # Should still pass with integration tests skipped
        assert result.passed is True
        assert "gates" in result.info
        integration_gate = next(
            (g for g in result.info["gates"] if g["name"] == "Integration Tests"), None
        )
        assert integration_gate is not None
        assert integration_gate["details"].get("skipped") == "checker not available"


class TestDeploymentEnvironmentValidation:
    """Tests for _validate_deployment_environment method."""

    def test_validate_environment_with_staging(self, deployment_config, mock_runner):
        """Test environment validation with staging environment."""
        work_item = {
            "id": "WI-001",
            "specification": "Deploy to environment: staging",
        }

        checker = DeploymentChecker(work_item, deployment_config, runner=mock_runner)

        with patch("solokit.quality.env_validator.EnvironmentValidator") as mock_validator:
            mock_validator_instance = Mock()
            mock_validator.return_value = mock_validator_instance
            mock_validator_instance.validate_all.return_value = (True, {})

            result = checker._validate_deployment_environment()

            assert result is True
            mock_validator.assert_called_once_with("staging")

    def test_validate_environment_with_production(self, deployment_config, mock_runner):
        """Test environment validation with production environment."""
        work_item = {
            "id": "WI-001",
            "specification": "Deploy to environment: production",
        }

        checker = DeploymentChecker(work_item, deployment_config, runner=mock_runner)

        with patch("solokit.quality.env_validator.EnvironmentValidator") as mock_validator:
            mock_validator_instance = Mock()
            mock_validator.return_value = mock_validator_instance
            mock_validator_instance.validate_all.return_value = (True, {})

            result = checker._validate_deployment_environment()

            assert result is True
            mock_validator.assert_called_once_with("production")

    def test_validate_environment_defaults_to_staging(self, deployment_config, mock_runner):
        """Test environment validation defaults to staging when not specified."""
        work_item = {
            "id": "WI-001",
            "specification": "Deploy the application",
        }

        checker = DeploymentChecker(work_item, deployment_config, runner=mock_runner)

        with patch("solokit.quality.env_validator.EnvironmentValidator") as mock_validator:
            mock_validator_instance = Mock()
            mock_validator.return_value = mock_validator_instance
            mock_validator_instance.validate_all.return_value = (True, {})

            result = checker._validate_deployment_environment()

            assert result is True
            mock_validator.assert_called_once_with("staging")

    def test_validate_environment_returns_false_when_validation_fails(
        self, deployment_config, mock_runner
    ):
        """Test environment validation returns False when validation fails."""
        work_item = {
            "id": "WI-001",
            "specification": "Deploy to environment: production",
        }

        checker = DeploymentChecker(work_item, deployment_config, runner=mock_runner)

        with patch("solokit.quality.env_validator.EnvironmentValidator") as mock_validator:
            mock_validator_instance = Mock()
            mock_validator.return_value = mock_validator_instance
            mock_validator_instance.validate_all.return_value = (
                False,
                {"errors": ["Failed"]},
            )

            result = checker._validate_deployment_environment()

            assert result is False

    def test_validate_environment_handles_import_error(self, deployment_config, mock_runner):
        """Test environment validation handles ImportError gracefully."""
        work_item = {
            "id": "WI-001",
            "specification": "Deploy to environment: staging",
        }

        checker = DeploymentChecker(work_item, deployment_config, runner=mock_runner)

        with patch(
            "solokit.quality.env_validator.EnvironmentValidator",
            side_effect=ImportError("Module not found"),
        ):
            result = checker._validate_deployment_environment()

            # Should return True when validator not available
            assert result is True


class TestDeploymentDocumentationValidation:
    """Tests for _validate_deployment_documentation method."""

    def test_validate_documentation_passes_with_all_sections(
        self, deployment_config, deployment_work_item, mock_runner
    ):
        """Test documentation validation passes with all required sections."""
        checker = DeploymentChecker(deployment_work_item, deployment_config, runner=mock_runner)

        result = checker._validate_deployment_documentation()

        assert result is True

    def test_validate_documentation_fails_with_missing_sections(
        self, deployment_config, incomplete_deployment_work_item, mock_runner
    ):
        """Test documentation validation fails with missing sections."""
        checker = DeploymentChecker(
            incomplete_deployment_work_item, deployment_config, runner=mock_runner
        )

        result = checker._validate_deployment_documentation()

        assert result is False

    def test_validate_documentation_checks_deployment_procedure(
        self, deployment_config, mock_runner
    ):
        """Test documentation validation checks for deployment procedure."""
        work_item = {
            "id": "WI-001",
            "specification": """
            # Deployment
            Missing deployment procedure section
            """,
        }

        checker = DeploymentChecker(work_item, deployment_config, runner=mock_runner)

        result = checker._validate_deployment_documentation()

        assert result is False

    def test_validate_documentation_checks_rollback_procedure(self, deployment_config, mock_runner):
        """Test documentation validation checks for rollback procedure."""
        work_item = {
            "id": "WI-001",
            "specification": """
            # Deployment
            ## Deployment Procedure
            Steps here
            """,
        }

        checker = DeploymentChecker(work_item, deployment_config, runner=mock_runner)

        result = checker._validate_deployment_documentation()

        assert result is False

    def test_validate_documentation_checks_smoke_tests(self, deployment_config, mock_runner):
        """Test documentation validation checks for smoke tests."""
        work_item = {
            "id": "WI-001",
            "specification": """
            # Deployment
            ## Deployment Procedure
            Steps here
            ## Rollback Procedure
            Steps here
            """,
        }

        checker = DeploymentChecker(work_item, deployment_config, runner=mock_runner)

        result = checker._validate_deployment_documentation()

        assert result is False

    def test_validate_documentation_checks_monitoring(self, deployment_config, mock_runner):
        """Test documentation validation checks for monitoring & alerting."""
        work_item = {
            "id": "WI-001",
            "specification": """
            # Deployment
            ## Deployment Procedure
            Steps here
            ## Rollback Procedure
            Steps here
            ## Smoke Tests
            Tests here
            """,
        }

        checker = DeploymentChecker(work_item, deployment_config, runner=mock_runner)

        result = checker._validate_deployment_documentation()

        assert result is False

    def test_validate_documentation_case_insensitive(self, deployment_config, mock_runner):
        """Test documentation validation is case insensitive."""
        work_item = {
            "id": "WI-001",
            "specification": """
            # Deployment
            ## DEPLOYMENT PROCEDURE
            Steps here
            ## ROLLBACK PROCEDURE
            Steps here
            ## SMOKE TESTS
            Tests here
            ## MONITORING & ALERTING
            Config here
            """,
        }

        checker = DeploymentChecker(work_item, deployment_config, runner=mock_runner)

        result = checker._validate_deployment_documentation()

        assert result is True


class TestRollbackTesting:
    """Tests for _check_rollback_tested method."""

    def test_check_rollback_tested_returns_true(
        self, deployment_config, deployment_work_item, mock_runner
    ):
        """Test rollback testing check returns True (framework stub)."""
        checker = DeploymentChecker(deployment_work_item, deployment_config, runner=mock_runner)

        result = checker._check_rollback_tested()

        # Framework stub should return True
        assert result is True


class TestDeploymentCheckerIntegration:
    """Integration tests for full deployment checker workflow."""

    @patch("solokit.quality.checkers.integration.IntegrationChecker")
    @patch("solokit.quality.checkers.security.SecurityChecker")
    def test_full_deployment_workflow_success(
        self,
        mock_security_checker_class,
        mock_integration_checker_class,
        deployment_config,
        deployment_work_item,
        mock_runner,
    ):
        """Test full deployment workflow with all gates passing."""
        # Mock IntegrationChecker
        mock_integration_instance = Mock()
        mock_integration_checker_class.return_value = mock_integration_instance
        mock_integration_instance.is_enabled.return_value = True
        mock_integration_instance.run.return_value = CheckResult(
            checker_name="integration",
            passed=True,
            status="passed",
            errors=[],
            warnings=[],
            info={"tests_passed": 10},
        )

        # Mock SecurityChecker
        mock_security_instance = Mock()
        mock_security_checker_class.return_value = mock_security_instance
        mock_security_instance.is_enabled.return_value = True
        mock_security_instance.run.return_value = CheckResult(
            checker_name="security",
            passed=True,
            status="passed",
            errors=[],
            warnings=[],
            info={"vulnerabilities": 0},
        )

        checker = DeploymentChecker(deployment_work_item, deployment_config, runner=mock_runner)

        with patch("solokit.quality.env_validator.EnvironmentValidator") as mock_validator:
            mock_validator_instance = Mock()
            mock_validator.return_value = mock_validator_instance
            mock_validator_instance.validate_all.return_value = (True, {})

            result = checker.run()

        assert result.passed is True
        assert result.status == "passed"
        assert len(result.errors) == 0
        assert result.execution_time >= 0

        # Verify all gates are present
        gates = result.info["gates"]
        gate_names = [g["name"] for g in gates]
        assert "Integration Tests" in gate_names
        assert "Security Scans" in gate_names
        assert "Environment Validation" in gate_names
        assert "Deployment Documentation" in gate_names
        assert "Rollback Tested" in gate_names

    @patch("solokit.quality.checkers.integration.IntegrationChecker")
    @patch("solokit.quality.checkers.security.SecurityChecker")
    def test_full_deployment_workflow_with_multiple_failures(
        self,
        mock_security_checker_class,
        mock_integration_checker_class,
        deployment_config,
        incomplete_deployment_work_item,
        mock_runner,
    ):
        """Test full deployment workflow with multiple gates failing."""
        # Mock IntegrationChecker - failed
        mock_integration_instance = Mock()
        mock_integration_checker_class.return_value = mock_integration_instance
        mock_integration_instance.is_enabled.return_value = True
        mock_integration_instance.run.return_value = CheckResult(
            checker_name="integration",
            passed=False,
            status="failed",
            errors=[{"message": "Test failed"}],
            warnings=[],
            info={},
        )

        # Mock SecurityChecker - failed
        mock_security_instance = Mock()
        mock_security_checker_class.return_value = mock_security_instance
        mock_security_instance.is_enabled.return_value = True
        mock_security_instance.run.return_value = CheckResult(
            checker_name="security",
            passed=False,
            status="failed",
            errors=[{"message": "Vulnerability found"}],
            warnings=[],
            info={},
        )

        checker = DeploymentChecker(
            incomplete_deployment_work_item, deployment_config, runner=mock_runner
        )

        with patch("solokit.quality.env_validator.EnvironmentValidator") as mock_validator:
            mock_validator_instance = Mock()
            mock_validator.return_value = mock_validator_instance
            mock_validator_instance.validate_all.return_value = (False, {})

            result = checker.run()

        # Should fail overall
        assert result.passed is False
        assert result.status == "failed"

        # Should have multiple errors
        assert len(result.errors) >= 3  # Integration, Security, Environment, Documentation

        # Check that specific gates failed
        error_gates = [e.get("gate", "") for e in result.errors]
        assert "Integration Tests" in error_gates
        assert "Security Scans" in error_gates
        assert "Environment Validation" in error_gates
        assert "Deployment Documentation" in error_gates
