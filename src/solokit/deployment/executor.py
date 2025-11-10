#!/usr/bin/env python3
"""
Deployment execution framework.

Provides automated deployment execution with:
- Pre-deployment validation
- Deployment execution with comprehensive logging
- Smoke test execution
- Rollback automation on failure
- Deployment state tracking
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from solokit.core.error_handlers import convert_file_errors, log_errors
from solokit.core.exceptions import (
    DeploymentStepError,
    ErrorCode,
    FileOperationError,
    PreDeploymentCheckError,
    RollbackError,
    SmokeTestError,
)
from solokit.core.output import get_output

output = get_output()


class DeploymentExecutor:
    """Deployment execution and validation."""

    def __init__(self, work_item: dict[str, Any], config_path: Path | None = None) -> None:
        """Initialize deployment executor."""
        if config_path is None:
            config_path = Path(".session/config.json")
        self.work_item = work_item
        self.config = self._load_config(config_path)
        self.deployment_log: list[dict[str, Any]] = []

    @convert_file_errors
    def _load_config(self, config_path: Path) -> dict[str, Any]:
        """
        Load deployment configuration.

        Args:
            config_path: Path to configuration file

        Returns:
            dict: Deployment configuration

        Raises:
            FileOperationError: If config file cannot be read or parsed
        """
        if not config_path.exists():
            return self._default_config()

        try:
            with open(config_path) as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            raise FileOperationError(
                operation="parse", file_path=str(config_path), details=f"Invalid JSON: {e}", cause=e
            ) from e

        deployment_config = config.get("deployment", self._default_config())
        return deployment_config  # type: ignore[no-any-return]

    def _default_config(self) -> dict[str, Any]:
        """Default deployment configuration."""
        return {
            "pre_deployment_checks": {
                "integration_tests": True,
                "security_scans": True,
                "environment_validation": True,
            },
            "smoke_tests": {"enabled": True, "timeout": 300, "retry_count": 3},
            "rollback": {
                "automatic": True,
                "on_smoke_test_failure": True,
                "on_error_threshold": True,
                "error_threshold_percent": 5,
            },
            "environments": {
                "staging": {"auto_deploy": True, "require_approval": False},
                "production": {"auto_deploy": False, "require_approval": True},
            },
        }

    @log_errors()
    def pre_deployment_validation(self) -> dict[str, Any]:
        """
        Run pre-deployment validation checks.

        Returns:
            dict: Validation results with checks and status

        Raises:
            PreDeploymentCheckError: If any validation check fails
        """
        results: dict[str, Any] = {"checks": [], "passed": True}
        failed_checks: list[str] = []

        # Check integration tests
        if self.config["pre_deployment_checks"].get("integration_tests"):
            tests_passed = self._check_integration_tests()
            results["checks"].append({"name": "Integration Tests", "passed": tests_passed})
            if not tests_passed:
                results["passed"] = False
                failed_checks.append("Integration Tests")

        # Check security scans
        if self.config["pre_deployment_checks"].get("security_scans"):
            scans_passed = self._check_security_scans()
            results["checks"].append({"name": "Security Scans", "passed": scans_passed})
            if not scans_passed:
                results["passed"] = False
                failed_checks.append("Security Scans")

        # Check environment readiness
        if self.config["pre_deployment_checks"].get("environment_validation"):
            env_ready = self._check_environment_readiness()
            results["checks"].append({"name": "Environment Readiness", "passed": env_ready})
            if not env_ready:
                results["passed"] = False
                failed_checks.append("Environment Readiness")

        self._log("Pre-deployment validation", results)

        # Raise exception if any checks failed
        if not results["passed"]:
            raise PreDeploymentCheckError(
                check_name=", ".join(failed_checks),
                details=f"{len(failed_checks)} check(s) failed",
                context={"results": results, "failed_checks": failed_checks},
            )

        return results

    @log_errors()
    def execute_deployment(self, dry_run: bool = False) -> dict[str, Any]:
        """
        Execute deployment procedure.

        Args:
            dry_run: If True, simulate deployment without actual execution

        Returns:
            dict: Deployment results with steps and timestamps

        Raises:
            DeploymentStepError: If any deployment step fails
        """
        results: dict[str, Any] = {
            "started_at": datetime.now().isoformat(),
            "steps": [],
            "success": True,
        }

        self._log("Deployment started", {"dry_run": dry_run})

        # Parse deployment steps from work item
        deployment_steps = self._parse_deployment_steps()

        for i, step in enumerate(deployment_steps, 1):
            self._log(f"Executing step {i}", {"step": step})

            if not dry_run:
                step_success = self._execute_deployment_step(step)
            else:
                step_success = True  # Simulate success in dry run

            results["steps"].append({"number": i, "description": step, "success": step_success})

            if not step_success:
                results["success"] = False
                results["failed_at_step"] = i
                self._log("Deployment failed", {"step": i, "description": step})
                raise DeploymentStepError(
                    step_number=i, step_description=step, context={"results": results}
                )

        results["completed_at"] = datetime.now().isoformat()
        return results

    @log_errors()
    def run_smoke_tests(self) -> dict[str, Any]:
        """
        Run smoke tests to verify deployment.

        Returns:
            dict: Test results with status

        Raises:
            SmokeTestError: If any smoke test fails
        """
        config = self.config["smoke_tests"]
        results: dict[str, Any] = {"tests": [], "passed": True}

        if not config.get("enabled"):
            return {"status": "skipped"}

        self._log("Running smoke tests", config)

        # Parse smoke tests from work item
        smoke_tests = self._parse_smoke_tests()
        failed_tests = []

        for test in smoke_tests:
            test_passed = self._execute_smoke_test(
                test,
                timeout=config.get("timeout", 300),
                retry_count=config.get("retry_count", 3),
            )

            test_name = test.get("name", "unknown")
            results["tests"].append({"name": test_name, "passed": test_passed})

            if not test_passed:
                results["passed"] = False
                failed_tests.append(test_name)

        self._log("Smoke tests completed", results)

        # Raise exception if any tests failed
        if not results["passed"]:
            raise SmokeTestError(
                test_name=", ".join(failed_tests),
                details=f"{len(failed_tests)} test(s) failed",
                context={"results": results, "failed_tests": failed_tests},
            )

        return results

    @log_errors()
    def rollback(self) -> dict[str, Any]:
        """
        Execute rollback procedure.

        Returns:
            dict: Rollback results with steps and timestamps

        Raises:
            RollbackError: If any rollback step fails
        """
        results: dict[str, Any] = {
            "started_at": datetime.now().isoformat(),
            "steps": [],
            "success": True,
        }

        self._log("Rollback started", {})

        # Parse rollback steps from work item
        rollback_steps = self._parse_rollback_steps()

        for i, step in enumerate(rollback_steps, 1):
            self._log(f"Executing rollback step {i}", {"step": step})

            step_success = self._execute_rollback_step(step)

            results["steps"].append({"number": i, "description": step, "success": step_success})

            if not step_success:
                results["success"] = False
                results["failed_at_step"] = i
                raise RollbackError(
                    step=step,
                    details=f"Rollback failed at step {i}",
                    context={"results": results, "step_number": i},
                )

        results["completed_at"] = datetime.now().isoformat()
        self._log("Rollback completed", results)

        return results

    def _check_integration_tests(self) -> bool:
        """Check if integration tests passed."""
        # NOTE: Framework stub - Integrate with quality_gates.py for actual test execution
        # In production, this should call QualityGates.run_tests() and check results
        return True

    def _check_security_scans(self) -> bool:
        """Check if security scans passed."""
        # NOTE: Framework stub - Integrate with quality_gates.py for actual security scanning
        # In production, this should call QualityGates.run_security_gate() and check results
        return True

    def _check_environment_readiness(self) -> bool:
        """Check if environment is ready."""
        # NOTE: Framework stub - Integrate with environment_validator.py for actual validation
        # In production, this should instantiate EnvironmentValidator and call validate_all()
        return True

    def _parse_deployment_steps(self) -> list[str]:
        """Parse deployment steps from work item specification."""
        # NOTE: Framework stub - Parse deployment steps from spec file
        # Use spec_parser.py to extract "## Deployment Steps" section
        # and convert to structured list of commands/actions
        return []

    def _execute_deployment_step(self, step: str) -> bool:
        """Execute a single deployment step."""
        # NOTE: Framework stub - Implement project-specific deployment step execution
        # Step types might include: shell commands, API calls, file operations, etc.
        # Should handle errors, logging, and timeouts appropriately
        return True

    def _parse_smoke_tests(self) -> list[dict]:
        """Parse smoke tests from work item specification."""
        # NOTE: Framework stub - Parse smoke test definitions from spec file
        # Use spec_parser.py to extract "## Smoke Tests" section
        # and convert to list of {name, command, expected_result} dicts
        return []

    def _execute_smoke_test(self, test: dict, timeout: int, retry_count: int) -> bool:
        """Execute a single smoke test with retries."""
        # NOTE: Framework stub - Implement project-specific smoke test execution
        # Should execute test command, check result, handle retries and timeouts
        # Common tests: HTTP endpoint checks, database queries, cache reads
        return True

    def _parse_rollback_steps(self) -> list[str]:
        """Parse rollback steps from work item specification."""
        # NOTE: Framework stub - Parse rollback procedure from spec file
        # Use spec_parser.py to extract "## Rollback Procedure" section
        # and convert to ordered list of rollback commands/actions
        return []

    def _execute_rollback_step(self, step: str) -> bool:
        """Execute a single rollback step."""
        # NOTE: Framework stub - Implement project-specific rollback step execution
        # Must be highly reliable since this runs during failure scenarios
        # Should handle partial rollbacks and verification of rollback success
        return True

    def _log(self, event: str, data: dict[str, Any]) -> None:
        """Log deployment event."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "data": data,
        }
        self.deployment_log.append(log_entry)

    def get_deployment_log(self) -> list[dict[str, Any]]:
        """Get deployment log."""
        return self.deployment_log


def main() -> None:
    """
    CLI entry point.

    Raises:
        ValidationError: If no work item ID provided
        PreDeploymentCheckError: If pre-deployment checks fail
        DeploymentStepError: If deployment fails
        SmokeTestError: If smoke tests fail
        RollbackError: If rollback fails
    """
    import sys

    from solokit.core.exceptions import ValidationError

    if len(sys.argv) < 2:
        raise ValidationError(
            message="Missing required argument: work_item_id",
            code=ErrorCode.INVALID_COMMAND,
            remediation="Usage: deployment_executor.py <work_item_id>",
        )

    # Load work item
    # NOTE: Framework stub - Should load work item by ID from work_items.json
    # Use work_item_manager.WorkItemManager to load actual work item data

    executor = DeploymentExecutor(work_item={})

    try:
        # Pre-deployment validation
        executor.pre_deployment_validation()

        # Execute deployment
        executor.execute_deployment()

        # Run smoke tests
        executor.run_smoke_tests()

        output.info("Deployment successful!")

    except (DeploymentStepError, SmokeTestError) as e:
        # Attempt rollback on deployment or smoke test failure
        output.info(f"Error: {e.message}")
        output.info("Initiating rollback...")
        try:
            executor.rollback()
            output.info("Rollback completed successfully")
        except RollbackError as rollback_err:
            output.info(f"Rollback failed: {rollback_err.message}")
            raise
        # Re-raise original error after successful rollback
        raise


if __name__ == "__main__":
    main()
