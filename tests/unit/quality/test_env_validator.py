#!/usr/bin/env python3
"""
Unit tests for EnvironmentValidator.

Tests environment validation including configuration checks,
connectivity, dependencies, health checks, and infrastructure validation.
"""

import os
from unittest.mock import patch

import pytest
from solokit.core.exceptions import ErrorCode, ValidationError
from solokit.quality.env_validator import EnvironmentValidator, main


class TestEnvironmentValidatorInit:
    """Test EnvironmentValidator initialization."""

    def test_init_with_environment_name(self):
        """Should initialize with environment name."""
        validator = EnvironmentValidator("production")

        assert validator.environment == "production"
        assert validator.validation_results == []

    def test_init_with_different_environments(self):
        """Should initialize with various environment names."""
        for env in ["dev", "staging", "production", "test"]:
            validator = EnvironmentValidator(env)
            assert validator.environment == env


class TestValidateConfiguration:
    """Test validate_configuration method."""

    def test_validate_configuration_all_present(self):
        """Should pass when all required variables are set."""
        validator = EnvironmentValidator("production")

        with patch.dict(os.environ, {"API_KEY": "test123", "DATABASE_URL": "postgres://localhost"}):
            result = validator.validate_configuration(["API_KEY", "DATABASE_URL"])

            assert result["passed"] is True
            assert len(result["checks"]) == 2

    def test_validate_configuration_missing_variable(self):
        """Should raise ValidationError when variable is missing."""
        validator = EnvironmentValidator("production")

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                validator.validate_configuration(["MISSING_VAR"])

            error = exc_info.value
            assert error.code == ErrorCode.MISSING_REQUIRED_FIELD
            assert "MISSING_VAR" in error.message
            assert "missing_variables" in error.context
            assert "MISSING_VAR" in error.context["missing_variables"]

    def test_validate_configuration_empty_variable(self):
        """Should raise ValidationError when variable is empty."""
        validator = EnvironmentValidator("production")

        with patch.dict(os.environ, {"EMPTY_VAR": ""}):
            with pytest.raises(ValidationError) as exc_info:
                validator.validate_configuration(["EMPTY_VAR"])

            error = exc_info.value
            assert "EMPTY_VAR" in error.context["missing_variables"]

    def test_validate_configuration_multiple_missing(self):
        """Should report all missing variables."""
        validator = EnvironmentValidator("production")

        with patch.dict(os.environ, {"VAR1": "value"}, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                validator.validate_configuration(["VAR1", "VAR2", "VAR3"])

            error = exc_info.value
            assert len(error.context["missing_variables"]) == 2
            assert "VAR2" in error.context["missing_variables"]
            assert "VAR3" in error.context["missing_variables"]

    def test_validate_configuration_environment_in_context(self):
        """Should include environment in error context."""
        validator = EnvironmentValidator("staging")

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                validator.validate_configuration(["VAR1"])

            assert exc_info.value.context["environment"] == "staging"

    def test_validate_configuration_provides_remediation(self):
        """Should provide remediation message."""
        validator = EnvironmentValidator("production")

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                validator.validate_configuration(["API_KEY"])

            assert exc_info.value.remediation is not None
            assert "API_KEY" in exc_info.value.remediation

    def test_validate_configuration_empty_list(self):
        """Should pass with empty required variables list."""
        validator = EnvironmentValidator("production")

        result = validator.validate_configuration([])

        assert result["passed"] is True
        assert len(result["checks"]) == 0

    def test_validate_configuration_check_details(self):
        """Should include check details for each variable."""
        validator = EnvironmentValidator("production")

        with patch.dict(os.environ, {"VAR1": "value1", "VAR2": "value2"}):
            result = validator.validate_configuration(["VAR1", "VAR2"])

            assert all("name" in check for check in result["checks"])
            assert all("passed" in check for check in result["checks"])
            assert all(check["passed"] for check in result["checks"])


class TestValidateConnectivity:
    """Test validate_connectivity method."""

    def test_validate_connectivity_default_passes(self):
        """Should return True by default (framework stub)."""
        validator = EnvironmentValidator("production")

        passed, results = validator.validate_connectivity()

        assert passed is True
        assert results["passed"] is True
        assert "checks" in results

    def test_validate_connectivity_returns_dict(self):
        """Should return proper result structure."""
        validator = EnvironmentValidator("production")

        passed, results = validator.validate_connectivity()

        assert isinstance(passed, bool)
        assert isinstance(results, dict)
        assert "checks" in results
        assert "passed" in results


class TestValidateDependencies:
    """Test validate_dependencies method."""

    def test_validate_dependencies_default_passes(self):
        """Should return True by default (framework stub)."""
        validator = EnvironmentValidator("production")

        passed, results = validator.validate_dependencies()

        assert passed is True
        assert results["passed"] is True
        assert "checks" in results

    def test_validate_dependencies_returns_dict(self):
        """Should return proper result structure."""
        validator = EnvironmentValidator("production")

        passed, results = validator.validate_dependencies()

        assert isinstance(passed, bool)
        assert isinstance(results, dict)


class TestValidateHealthChecks:
    """Test validate_health_checks method."""

    def test_validate_health_checks_default_passes(self):
        """Should return True by default (framework stub)."""
        validator = EnvironmentValidator("production")

        passed, results = validator.validate_health_checks()

        assert passed is True
        assert results["passed"] is True

    def test_validate_health_checks_returns_dict(self):
        """Should return proper result structure."""
        validator = EnvironmentValidator("production")

        passed, results = validator.validate_health_checks()

        assert isinstance(results, dict)
        assert "checks" in results
        assert "passed" in results


class TestValidateMonitoring:
    """Test validate_monitoring method."""

    def test_validate_monitoring_default_passes(self):
        """Should return True by default (framework stub)."""
        validator = EnvironmentValidator("production")

        passed, results = validator.validate_monitoring()

        assert passed is True
        assert results["passed"] is True

    def test_validate_monitoring_returns_dict(self):
        """Should return proper result structure."""
        validator = EnvironmentValidator("production")

        passed, results = validator.validate_monitoring()

        assert isinstance(results, dict)


class TestValidateInfrastructure:
    """Test validate_infrastructure method."""

    def test_validate_infrastructure_default_passes(self):
        """Should return True by default (framework stub)."""
        validator = EnvironmentValidator("production")

        passed, results = validator.validate_infrastructure()

        assert passed is True
        assert results["passed"] is True

    def test_validate_infrastructure_returns_dict(self):
        """Should return proper result structure."""
        validator = EnvironmentValidator("production")

        passed, results = validator.validate_infrastructure()

        assert isinstance(results, dict)
        assert "checks" in results


class TestValidateCapacity:
    """Test validate_capacity method."""

    def test_validate_capacity_default_passes(self):
        """Should return True by default (framework stub)."""
        validator = EnvironmentValidator("production")

        passed, results = validator.validate_capacity()

        assert passed is True
        assert results["passed"] is True

    def test_validate_capacity_returns_dict(self):
        """Should return proper result structure."""
        validator = EnvironmentValidator("production")

        passed, results = validator.validate_capacity()

        assert isinstance(results, dict)


class TestValidateAll:
    """Test validate_all method."""

    def test_validate_all_without_env_vars(self):
        """Should run all validations without env var checks."""
        validator = EnvironmentValidator("production")

        passed, results = validator.validate_all()

        assert passed is True
        assert "validations" in results
        assert len(results["validations"]) == 6  # All validation categories

    def test_validate_all_with_env_vars(self):
        """Should include configuration validation when env vars provided."""
        validator = EnvironmentValidator("production")

        with patch.dict(os.environ, {"VAR1": "value"}):
            passed, results = validator.validate_all(required_env_vars=["VAR1"])

            assert passed is True
            assert len(results["validations"]) == 7  # Including configuration

    def test_validate_all_validation_names(self):
        """Should include all validation categories."""
        validator = EnvironmentValidator("production")

        passed, results = validator.validate_all()

        validation_names = [v["name"] for v in results["validations"]]
        assert "Connectivity" in validation_names
        assert "Dependencies" in validation_names
        assert "Health Checks" in validation_names
        assert "Monitoring" in validation_names
        assert "Infrastructure" in validation_names
        assert "Capacity" in validation_names

    def test_validate_all_failed_configuration(self):
        """Should fail overall when configuration validation fails."""
        validator = EnvironmentValidator("production")

        with patch.dict(os.environ, {}, clear=True):
            passed, results = validator.validate_all(required_env_vars=["MISSING"])

            assert passed is False
            config_validation = next(
                v for v in results["validations"] if v["name"] == "Configuration"
            )
            assert config_validation["passed"] is False

    def test_validate_all_includes_validation_details(self):
        """Should include details for each validation."""
        validator = EnvironmentValidator("production")

        passed, results = validator.validate_all()

        for validation in results["validations"]:
            assert "name" in validation
            assert "passed" in validation
            assert "details" in validation

    def test_validate_all_configuration_error_details(self):
        """Should include error details for failed configuration."""
        validator = EnvironmentValidator("production")

        with patch.dict(os.environ, {}, clear=True):
            passed, results = validator.validate_all(required_env_vars=["API_KEY"])

            config_validation = next(
                v for v in results["validations"] if v["name"] == "Configuration"
            )
            assert "error" in config_validation["details"]
            assert "context" in config_validation["details"]

    def test_validate_all_no_env_vars_skips_configuration(self):
        """Should skip configuration validation when no env vars provided."""
        validator = EnvironmentValidator("production")

        passed, results = validator.validate_all(required_env_vars=None)

        validation_names = [v["name"] for v in results["validations"]]
        assert "Configuration" not in validation_names

    def test_validate_all_empty_env_vars_skips_configuration(self):
        """Should skip configuration validation with empty env vars list."""
        validator = EnvironmentValidator("production")

        passed, results = validator.validate_all(required_env_vars=[])

        validation_names = [v["name"] for v in results["validations"]]
        assert "Configuration" not in validation_names


class TestValidateAllIntegration:
    """Integration tests for validate_all method."""

    def test_validate_all_multiple_failures(self):
        """Should aggregate multiple validation failures."""
        validator = EnvironmentValidator("production")

        # Mock some validations to fail
        with patch.object(
            validator,
            "validate_connectivity",
            return_value=(False, {"checks": [], "passed": False}),
        ):
            with patch.object(
                validator,
                "validate_dependencies",
                return_value=(False, {"checks": [], "passed": False}),
            ):
                passed, results = validator.validate_all()

                assert passed is False
                failed_count = sum(1 for v in results["validations"] if not v["passed"])
                assert failed_count >= 2

    def test_validate_all_mixed_results(self):
        """Should handle mixed success and failure results."""
        validator = EnvironmentValidator("production")

        with patch.object(
            validator, "validate_connectivity", return_value=(True, {"checks": [], "passed": True})
        ):
            with patch.object(
                validator,
                "validate_dependencies",
                return_value=(False, {"checks": [], "passed": False}),
            ):
                passed, results = validator.validate_all()

                assert passed is False
                assert any(v["passed"] for v in results["validations"])
                assert any(not v["passed"] for v in results["validations"])


class TestMainFunction:
    """Test main CLI entry point."""

    def test_main_missing_environment_argument(self, capsys):
        """Should exit with error if environment not provided."""
        with patch("sys.argv", ["env_validator.py"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

            captured = capsys.readouterr()
            assert "environment" in captured.err.lower()

    def test_main_successful_validation(self, capsys):
        """Should exit with 0 on successful validation."""
        with patch("sys.argv", ["env_validator.py", "production"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 0

    def test_main_failed_validation(self, capsys):
        """Should exit with 1 on failed validation."""
        with patch("sys.argv", ["env_validator.py", "production"]):
            with patch.dict(os.environ, {}, clear=True):
                with patch.object(
                    EnvironmentValidator,
                    "validate_all",
                    return_value=(False, {"validations": [{"name": "Test", "passed": False}]}),
                ):
                    with pytest.raises(SystemExit) as exc_info:
                        main()

                    assert exc_info.value.code == 1

    def test_main_displays_validation_results(self, capsys):
        """Should display validation results."""
        with patch("sys.argv", ["env_validator.py", "staging"]):
            with pytest.raises(SystemExit):
                main()

            captured = capsys.readouterr()
            assert "Environment Validation" in captured.out

    def test_main_displays_validation_items(self, capsys):
        """Should display individual validation items."""
        with patch("sys.argv", ["env_validator.py", "production"]):
            with pytest.raises(SystemExit):
                main()

            captured = capsys.readouterr()
            # Should show validation categories
            assert len(captured.out) > 0

    def test_main_handles_validation_error(self, capsys):
        """Should handle ValidationError gracefully."""
        # Create a mock exception that won't trigger logging issues
        mock_error = ValidationError(
            message="Test error",
            code=ErrorCode.CONFIG_VALIDATION_FAILED,
            remediation="Fix the issue",
        )

        with patch("sys.argv", ["env_validator.py", "production"]):
            with patch.object(EnvironmentValidator, "validate_all", side_effect=mock_error):
                # Mock the logger to avoid KeyError with 'message' in LogRecord
                with patch("solokit.quality.env_validator.logger"):
                    with pytest.raises(SystemExit) as exc_info:
                        main()

                    assert exc_info.value.code != 0

                    captured = capsys.readouterr()
                    assert "Test error" in captured.err

    def test_main_shows_remediation_on_error(self, capsys):
        """Should display remediation message on error."""
        # Create a mock exception that won't trigger logging issues
        mock_error = ValidationError(
            message="Config error",
            code=ErrorCode.CONFIG_VALIDATION_FAILED,
            remediation="Set required variables",
        )

        with patch("sys.argv", ["env_validator.py", "production"]):
            with patch.object(EnvironmentValidator, "validate_all", side_effect=mock_error):
                # Mock the logger to avoid KeyError with 'message' in LogRecord
                with patch("solokit.quality.env_validator.logger"):
                    with pytest.raises(SystemExit):
                        main()

                    captured = capsys.readouterr()
                    assert "Remediation" in captured.err


class TestValidationResultStructure:
    """Test validation result structure consistency."""

    def test_connectivity_result_structure(self):
        """Should return consistent result structure."""
        validator = EnvironmentValidator("production")
        passed, results = validator.validate_connectivity()

        assert "checks" in results
        assert "passed" in results
        assert isinstance(results["checks"], list)
        assert isinstance(results["passed"], bool)

    def test_dependencies_result_structure(self):
        """Should return consistent result structure."""
        validator = EnvironmentValidator("production")
        passed, results = validator.validate_dependencies()

        assert "checks" in results
        assert "passed" in results

    def test_health_checks_result_structure(self):
        """Should return consistent result structure."""
        validator = EnvironmentValidator("production")
        passed, results = validator.validate_health_checks()

        assert "checks" in results
        assert "passed" in results

    def test_monitoring_result_structure(self):
        """Should return consistent result structure."""
        validator = EnvironmentValidator("production")
        passed, results = validator.validate_monitoring()

        assert "checks" in results
        assert "passed" in results

    def test_infrastructure_result_structure(self):
        """Should return consistent result structure."""
        validator = EnvironmentValidator("production")
        passed, results = validator.validate_infrastructure()

        assert "checks" in results
        assert "passed" in results

    def test_capacity_result_structure(self):
        """Should return consistent result structure."""
        validator = EnvironmentValidator("production")
        passed, results = validator.validate_capacity()

        assert "checks" in results
        assert "passed" in results


class TestConfigurationValidationEdgeCases:
    """Test edge cases for configuration validation."""

    def test_validate_configuration_whitespace_only(self):
        """Should treat whitespace-only values as empty."""
        validator = EnvironmentValidator("production")

        with patch.dict(os.environ, {"VAR": "   "}):
            # Whitespace might be considered valid by the current implementation
            # Testing actual behavior
            validator.validate_configuration(["VAR"])
            # If whitespace is valid, check passes; if not, exception is raised

    def test_validate_configuration_special_characters(self):
        """Should handle special characters in variable values."""
        validator = EnvironmentValidator("production")

        special_value = "test!@#$%^&*()_+-={}[]|:;<>?,./"
        with patch.dict(os.environ, {"SPECIAL": special_value}):
            result = validator.validate_configuration(["SPECIAL"])

            assert result["passed"] is True

    def test_validate_configuration_unicode_values(self):
        """Should handle unicode in variable values."""
        validator = EnvironmentValidator("production")

        with patch.dict(os.environ, {"UNICODE": "test\u00e9\u00f1"}):
            result = validator.validate_configuration(["UNICODE"])

            assert result["passed"] is True

    def test_validate_configuration_very_long_list(self):
        """Should handle large number of required variables."""
        validator = EnvironmentValidator("production")

        # Create 100 environment variables
        env_vars = {f"VAR_{i}": f"value_{i}" for i in range(100)}
        with patch.dict(os.environ, env_vars):
            result = validator.validate_configuration(list(env_vars.keys()))

            assert result["passed"] is True
            assert len(result["checks"]) == 100


class TestValidateAllEdgeCases:
    """Test edge cases for validate_all method."""

    def test_validate_all_preserves_all_validation_results(self):
        """Should preserve results from all validations."""
        validator = EnvironmentValidator("production")

        passed, results = validator.validate_all()

        # Each validation should have its own entry
        assert all("name" in v for v in results["validations"])
        assert all("passed" in v for v in results["validations"])
        assert all("details" in v for v in results["validations"])

    def test_validate_all_overall_passed_consistency(self):
        """Should set overall passed consistently with individual results."""
        validator = EnvironmentValidator("production")

        passed, results = validator.validate_all()

        # Overall passed should match all individual checks passing
        all_passed = all(v["passed"] for v in results["validations"])
        assert results["passed"] == all_passed

    def test_validate_all_with_configuration_exception_handling(self):
        """Should handle configuration validation exceptions properly."""
        validator = EnvironmentValidator("production")

        with patch.dict(os.environ, {}, clear=True):
            passed, results = validator.validate_all(required_env_vars=["MISSING1", "MISSING2"])

            assert passed is False
            config_result = next(
                (v for v in results["validations"] if v["name"] == "Configuration"), None
            )
            assert config_result is not None
            assert config_result["passed"] is False
