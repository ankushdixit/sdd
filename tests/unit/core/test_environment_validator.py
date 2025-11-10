"""Unit tests for EnvironmentValidator class.

This module tests environment validation functionality including:
- Connectivity validation
- Configuration validation (environment variables)
- Dependency validation
- Health check validation
- Monitoring validation
- Infrastructure validation
- Capacity validation
"""

import os

import pytest

from solokit.core.exceptions import ValidationError
from solokit.quality.env_validator import EnvironmentValidator


class TestEnvironmentValidatorInit:
    """Tests for EnvironmentValidator initialization."""

    def test_init_with_environment_name(self):
        """Test that EnvironmentValidator initializes with an environment name."""
        # Arrange & Act
        validator = EnvironmentValidator("staging")

        # Assert
        assert validator.environment == "staging"
        assert hasattr(validator, "validation_results")
        assert isinstance(validator.validation_results, list)

    @pytest.mark.parametrize("environment", ["staging", "production", "development"])
    def test_init_with_various_environments(self, environment):
        """Test that EnvironmentValidator works with different environment names."""
        # Arrange & Act
        validator = EnvironmentValidator(environment)

        # Assert
        assert validator.environment == environment


class TestConnectivityValidation:
    """Tests for connectivity validation."""

    def test_validate_connectivity_returns_correct_structure(self):
        """Test that validate_connectivity returns tuple with correct structure."""
        # Arrange
        validator = EnvironmentValidator("staging")

        # Act
        passed, results = validator.validate_connectivity()

        # Assert
        assert isinstance(passed, bool)
        assert isinstance(results, dict)
        assert "checks" in results
        assert "passed" in results

    def test_validate_connectivity_default_passes(self):
        """Test that validate_connectivity passes by default (framework stub)."""
        # Arrange
        validator = EnvironmentValidator("staging")

        # Act
        passed, results = validator.validate_connectivity()

        # Assert
        assert passed is True
        assert results["passed"] is True


class TestConfigurationValidation:
    """Tests for configuration validation."""

    def test_validate_configuration_with_existing_var(self):
        """Test that validate_configuration detects existing environment variables."""
        # Arrange
        os.environ["TEST_VAR"] = "test_value"
        validator = EnvironmentValidator("staging")

        # Act
        results = validator.validate_configuration(["TEST_VAR"])

        # Assert
        assert results["passed"] is True
        assert len(results["checks"]) == 1
        assert results["checks"][0]["passed"] is True

        # Cleanup
        del os.environ["TEST_VAR"]

    def test_validate_configuration_detects_missing_var(self):
        """Test that validate_configuration raises ValidationError for missing environment variables."""
        # Arrange
        validator = EnvironmentValidator("staging")

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_configuration(["NONEXISTENT_VAR"])

        # Verify error details
        assert "NONEXISTENT_VAR" in exc_info.value.message
        assert "NONEXISTENT_VAR" in exc_info.value.context["missing_variables"]
        assert exc_info.value.context["environment"] == "staging"
        assert exc_info.value.remediation is not None

    def test_validate_configuration_with_multiple_vars(self):
        """Test that validate_configuration checks multiple environment variables."""
        # Arrange
        os.environ["VAR1"] = "value1"
        os.environ["VAR2"] = "value2"
        validator = EnvironmentValidator("staging")

        # Act
        results = validator.validate_configuration(["VAR1", "VAR2"])

        # Assert
        assert results["passed"] is True
        assert len(results["checks"]) == 2

        # Cleanup
        del os.environ["VAR1"]
        del os.environ["VAR2"]

    def test_validate_configuration_fails_with_empty_var(self):
        """Test that validate_configuration raises ValidationError when variable is set but empty."""
        # Arrange
        os.environ["EMPTY_VAR"] = ""
        validator = EnvironmentValidator("staging")

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_configuration(["EMPTY_VAR"])

        # Verify error details
        assert "EMPTY_VAR" in exc_info.value.message
        assert "EMPTY_VAR" in exc_info.value.context["missing_variables"]

        # Cleanup
        del os.environ["EMPTY_VAR"]


class TestDependencyValidation:
    """Tests for dependency validation."""

    def test_validate_dependencies_returns_correct_structure(self):
        """Test that validate_dependencies returns tuple with correct structure."""
        # Arrange
        validator = EnvironmentValidator("staging")

        # Act
        passed, results = validator.validate_dependencies()

        # Assert
        assert isinstance(passed, bool)
        assert isinstance(results, dict)
        assert "checks" in results
        assert "passed" in results

    def test_validate_dependencies_default_passes(self):
        """Test that validate_dependencies passes by default (framework stub)."""
        # Arrange
        validator = EnvironmentValidator("staging")

        # Act
        passed, results = validator.validate_dependencies()

        # Assert
        assert passed is True


class TestHealthCheckValidation:
    """Tests for health check validation."""

    def test_validate_health_checks_returns_correct_structure(self):
        """Test that validate_health_checks returns tuple with correct structure."""
        # Arrange
        validator = EnvironmentValidator("staging")

        # Act
        passed, results = validator.validate_health_checks()

        # Assert
        assert isinstance(passed, bool)
        assert isinstance(results, dict)
        assert "checks" in results
        assert "passed" in results

    def test_validate_health_checks_default_passes(self):
        """Test that validate_health_checks passes by default (framework stub)."""
        # Arrange
        validator = EnvironmentValidator("staging")

        # Act
        passed, results = validator.validate_health_checks()

        # Assert
        assert passed is True


class TestMonitoringValidation:
    """Tests for monitoring validation."""

    def test_validate_monitoring_returns_correct_structure(self):
        """Test that validate_monitoring returns tuple with correct structure."""
        # Arrange
        validator = EnvironmentValidator("staging")

        # Act
        passed, results = validator.validate_monitoring()

        # Assert
        assert isinstance(passed, bool)
        assert isinstance(results, dict)
        assert "checks" in results
        assert "passed" in results

    def test_validate_monitoring_default_passes(self):
        """Test that validate_monitoring passes by default (framework stub)."""
        # Arrange
        validator = EnvironmentValidator("staging")

        # Act
        passed, results = validator.validate_monitoring()

        # Assert
        assert passed is True


class TestInfrastructureValidation:
    """Tests for infrastructure validation."""

    def test_validate_infrastructure_returns_correct_structure(self):
        """Test that validate_infrastructure returns tuple with correct structure."""
        # Arrange
        validator = EnvironmentValidator("staging")

        # Act
        passed, results = validator.validate_infrastructure()

        # Assert
        assert isinstance(passed, bool)
        assert isinstance(results, dict)
        assert "checks" in results
        assert "passed" in results

    def test_validate_infrastructure_default_passes(self):
        """Test that validate_infrastructure passes by default (framework stub)."""
        # Arrange
        validator = EnvironmentValidator("staging")

        # Act
        passed, results = validator.validate_infrastructure()

        # Assert
        assert passed is True


class TestCapacityValidation:
    """Tests for capacity validation."""

    def test_validate_capacity_returns_correct_structure(self):
        """Test that validate_capacity returns tuple with correct structure."""
        # Arrange
        validator = EnvironmentValidator("staging")

        # Act
        passed, results = validator.validate_capacity()

        # Assert
        assert isinstance(passed, bool)
        assert isinstance(results, dict)
        assert "checks" in results
        assert "passed" in results

    def test_validate_capacity_default_passes(self):
        """Test that validate_capacity passes by default (framework stub)."""
        # Arrange
        validator = EnvironmentValidator("staging")

        # Act
        passed, results = validator.validate_capacity()

        # Assert
        assert passed is True


class TestValidateAll:
    """Tests for validate_all comprehensive validation."""

    def test_validate_all_runs_all_validation_types(self):
        """Test that validate_all runs all 7 validation types."""
        # Arrange
        os.environ["TEST_VAR"] = "test_value"
        validator = EnvironmentValidator("staging")

        expected_validations = [
            "Connectivity",
            "Configuration",
            "Dependencies",
            "Health Checks",
            "Monitoring",
            "Infrastructure",
            "Capacity",
        ]

        # Act
        passed, results = validator.validate_all(required_env_vars=["TEST_VAR"])

        # Assert
        assert "validations" in results
        validation_names = [v["name"] for v in results["validations"]]

        for expected in expected_validations:
            assert expected in validation_names, f"Missing validation: {expected}"

        # Cleanup
        del os.environ["TEST_VAR"]

    def test_validate_all_returns_correct_structure(self):
        """Test that validate_all returns correct result structure."""
        # Arrange
        validator = EnvironmentValidator("staging")

        # Act
        passed, results = validator.validate_all()

        # Assert
        assert isinstance(passed, bool)
        assert isinstance(results, dict)
        assert "validations" in results
        assert "passed" in results
        assert isinstance(results["validations"], list)

    def test_validate_all_without_env_vars_skips_config(self):
        """Test that validate_all runs without required_env_vars parameter."""
        # Arrange
        validator = EnvironmentValidator("staging")

        # Act
        passed, results = validator.validate_all(required_env_vars=None)

        # Assert
        _validation_names = [v["name"] for v in results["validations"]]
        # Configuration should not be in the list when required_env_vars is None
        assert passed is True

    def test_validate_all_passes_when_all_checks_pass(self):
        """Test that validate_all returns True when all checks pass."""
        # Arrange
        os.environ["TEST_VAR"] = "test_value"
        validator = EnvironmentValidator("staging")

        # Act
        passed, results = validator.validate_all(required_env_vars=["TEST_VAR"])

        # Assert
        assert passed is True
        assert results["passed"] is True

        # Cleanup
        del os.environ["TEST_VAR"]

    def test_validate_all_fails_when_config_check_fails(self):
        """Test that validate_all returns False when configuration check fails."""
        # Arrange
        validator = EnvironmentValidator("staging")

        # Act
        passed, results = validator.validate_all(required_env_vars=["MISSING_VAR"])

        # Assert
        assert passed is False
        assert results["passed"] is False

    def test_validate_all_includes_details_for_each_validation(self):
        """Test that validate_all includes details for each validation."""
        # Arrange
        validator = EnvironmentValidator("staging")

        # Act
        passed, results = validator.validate_all()

        # Assert
        for validation in results["validations"]:
            assert "name" in validation
            assert "passed" in validation
            assert "details" in validation

    def test_validate_all_includes_error_context_when_config_fails(self):
        """Test that validate_all includes error context when configuration validation fails."""
        # Arrange
        validator = EnvironmentValidator("staging")

        # Act
        passed, results = validator.validate_all(
            required_env_vars=["MISSING_VAR_1", "MISSING_VAR_2"]
        )

        # Assert
        assert passed is False
        assert results["passed"] is False

        # Find the Configuration validation
        config_validation = next(v for v in results["validations"] if v["name"] == "Configuration")
        assert config_validation["passed"] is False
        assert "error" in config_validation["details"]
        assert "context" in config_validation["details"]
        assert "missing_variables" in config_validation["details"]["context"]
        assert "MISSING_VAR_1" in config_validation["details"]["context"]["missing_variables"]
        assert "MISSING_VAR_2" in config_validation["details"]["context"]["missing_variables"]
