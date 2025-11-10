#!/usr/bin/env python3
"""
Integration test execution framework.

Supports:
- Multi-service orchestration
- Test environment setup/teardown
- Test data management
- Parallel test execution
- Result aggregation

Updated in Phase 5.7.3 to use spec_parser for reading test specifications.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from solokit.core.command_runner import CommandRunner
from solokit.core.constants import (
    CLEANUP_TIMEOUT,
    DOCKER_COMMAND_TIMEOUT,
    DOCKER_COMPOSE_TIMEOUT,
    FIXTURE_SETUP_TIMEOUT,
    INTEGRATION_TEST_TIMEOUT,
)
from solokit.core.exceptions import (
    EnvironmentSetupError,
    FileNotFoundError,
    IntegrationExecutionError,
    TimeoutError,
    ValidationError,
)
from solokit.core.output import get_output
from solokit.work_items import spec_parser

output = get_output()
logger = logging.getLogger(__name__)


class IntegrationTestRunner:
    """Execute integration tests with multi-service orchestration."""

    def __init__(self, work_item: dict):
        """
        Initialize integration test runner.

        Args:
            work_item: Integration test work item (must have 'id' field)

        Raises:
            ValidationError: If work item missing 'id' field or spec parsing fails
            FileNotFoundError: If spec file not found
        """
        self.work_item = work_item
        work_id = work_item.get("id")

        if not work_id:
            raise ValidationError(
                message="Work item must have 'id' field",
                context={"work_item": work_item},
                remediation="Ensure work item dict contains 'id' key",
            )

        # Parse spec file to get test scenarios and environment requirements
        # Pass full work_item dict to support custom spec filenames
        try:
            parsed_spec = spec_parser.parse_spec_file(work_item)
        except FileNotFoundError:
            # Re-raise as-is (already correct exception type)
            raise
        except Exception as e:
            raise ValidationError(
                message=f"Failed to parse spec file for {work_id}",
                context={"work_item_id": work_id, "error": str(e)},
                remediation=f"Check .session/specs/{work_id}.md for valid format",
                cause=e,
            )

        # Extract test scenarios from parsed spec
        self.test_scenarios = parsed_spec.get("test_scenarios", [])

        # Parse environment requirements from spec content
        # The environment_requirements section contains service names and configuration
        env_req_text = parsed_spec.get("environment_requirements", "")
        self.env_requirements = self._parse_environment_requirements(env_req_text)

        self.results: dict[str, Any] = {
            "scenarios": [],
            "start_time": None,
            "end_time": None,
            "total_duration": 0.0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
        }

        # Initialize CommandRunner
        self.runner = CommandRunner(default_timeout=INTEGRATION_TEST_TIMEOUT)

    def _parse_environment_requirements(self, env_text: str) -> dict:
        """
        Parse environment requirements from spec text.

        Args:
            env_text: Environment requirements section content

        Returns:
            Dict with 'services_required' and 'compose_file' keys
        """
        if not env_text:
            return {
                "services_required": [],
                "compose_file": "docker-compose.integration.yml",
            }

        # Extract service names (look for lines with service names)
        services = []
        compose_file = "docker-compose.integration.yml"

        for line in env_text.split("\n"):
            line = line.strip()
            # Look for service names (simple heuristic: lines with common service names)
            if any(
                s in line.lower()
                for s in [
                    "postgresql",
                    "postgres",
                    "redis",
                    "mongodb",
                    "mysql",
                    "nginx",
                    "kafka",
                ]
            ):
                # Extract service name and version if present
                parts = line.split()
                if parts:
                    services.append(parts[0].strip("-*•"))
            # Look for compose file reference
            if "docker-compose" in line.lower() or "compose" in line.lower():
                # Try to extract filename
                words = line.split()
                for word in words:
                    if "docker-compose" in word or word.endswith(".yml") or word.endswith(".yaml"):
                        compose_file = word.strip("`\"':")

        return {"services_required": services, "compose_file": compose_file}

    def setup_environment(self) -> None:
        """
        Set up integration test environment.

        Raises:
            FileNotFoundError: If Docker Compose file not found
            EnvironmentSetupError: If service startup or health check fails
            TimeoutError: If service startup times out
        """
        logger.info("Setting up integration test environment...")

        # Check if Docker Compose file exists
        compose_file = self.env_requirements.get("compose_file", "docker-compose.integration.yml")
        if not Path(compose_file).exists():
            raise FileNotFoundError(file_path=compose_file, file_type="Docker Compose")

        # Start services
        result = self.runner.run(
            ["docker-compose", "-f", compose_file, "up", "-d"],
            timeout=DOCKER_COMPOSE_TIMEOUT,
        )

        if not result.success:
            if result.timed_out:
                raise TimeoutError(
                    operation="docker-compose startup",
                    timeout_seconds=180,
                    context={"compose_file": compose_file},
                )
            raise EnvironmentSetupError(
                component="docker-compose",
                details=result.stderr or "Failed to start services",
                context={"compose_file": compose_file, "stderr": result.stderr},
            )

        logger.info(f"✓ Services started from {compose_file}")

        # Wait for services to be healthy
        services = self.env_requirements.get("services_required", [])
        for service in services:
            self._wait_for_service(service)

        logger.info(f"✓ All {len(services)} services are healthy")

        # Load test data
        self._load_test_data()

        logger.info("✓ Integration test environment ready")

    def _wait_for_service(self, service: str, timeout: int = 60) -> None:
        """
        Wait for service to be healthy.

        Args:
            service: Service name
            timeout: Maximum wait time in seconds

        Raises:
            TimeoutError: If service doesn't become healthy within timeout
            EnvironmentSetupError: If service health check fails
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            result = self.runner.run(
                ["docker-compose", "ps", "-q", service], timeout=DOCKER_COMMAND_TIMEOUT
            )

            if result.success and result.stdout.strip():
                # Check health status
                health_result = self.runner.run(
                    [
                        "docker",
                        "inspect",
                        "--format='{{.State.Health.Status}}'",
                        result.stdout.strip(),
                    ],
                    timeout=DOCKER_COMMAND_TIMEOUT,
                )

                if health_result.success and "healthy" in health_result.stdout:
                    return

            time.sleep(2)

        # Timeout - service didn't become healthy
        raise TimeoutError(
            operation=f"waiting for service '{service}' to become healthy",
            timeout_seconds=timeout,
            context={"service": service},
        )

    def _load_test_data(self) -> None:
        """
        Load test data fixtures.

        Raises:
            FileNotFoundError: If fixture file not found
            EnvironmentSetupError: If fixture loading fails
        """
        fixtures = self.env_requirements.get("test_data_fixtures", [])

        for fixture in fixtures:
            fixture_path = Path(fixture)
            if not fixture_path.exists():
                logger.warning(f"Fixture not found: {fixture}")
                continue

            # Execute fixture loading script using the same Python interpreter
            result = self.runner.run(
                [sys.executable, str(fixture_path)], timeout=FIXTURE_SETUP_TIMEOUT, check=True
            )
            if result.success:
                logger.info(f"✓ Loaded fixture: {fixture}")
            else:
                raise EnvironmentSetupError(
                    component="test data fixture",
                    details=f"Failed to load fixture: {fixture}",
                    context={"fixture": fixture, "stderr": result.stderr},
                )

    def run_tests(self, language: str | None = None) -> dict[str, Any]:
        """
        Execute all integration test scenarios.

        Args:
            language: Project language (python, javascript, typescript)

        Returns:
            dict: Test results with passed/failed counts and duration

        Raises:
            ValidationError: If unsupported language
            IntegrationExecutionError: If tests fail to execute
        """
        self.results["start_time"] = datetime.now().isoformat()

        logger.info(f"\nRunning {len(self.test_scenarios)} integration test scenarios...\n")

        # Detect language if not provided
        if language is None:
            language = self._detect_language()

        # Run scenarios based on language
        if language == "python":
            self._run_pytest()
        elif language in ["javascript", "typescript"]:
            self._run_jest()
        else:
            raise ValidationError(
                message=f"Unsupported language: {language}",
                context={"language": language},
                remediation="Supported languages: python, javascript, typescript",
            )

        self.results["end_time"] = datetime.now().isoformat()

        # Calculate duration
        start = datetime.fromisoformat(self.results["start_time"])
        end = datetime.fromisoformat(self.results["end_time"])
        self.results["total_duration"] = (end - start).total_seconds()

        return self.results

    def _run_pytest(self) -> None:
        """
        Run integration tests using pytest.

        Raises:
            TimeoutError: If tests timeout
            IntegrationExecutionError: If tests fail
        """
        test_dir = self.work_item.get("test_directory", "tests/integration")

        result = self.runner.run(
            [
                "pytest",
                test_dir,
                "-v",
                "--tb=short",
                "--json-report",
                "--json-report-file=integration-test-results.json",
            ],
            timeout=INTEGRATION_TEST_TIMEOUT,
        )

        # Parse results
        results_file = Path("integration-test-results.json")
        if results_file.exists():
            with open(results_file) as f:
                test_data = json.load(f)

            self.results["passed"] = test_data.get("summary", {}).get("passed", 0)
            self.results["failed"] = test_data.get("summary", {}).get("failed", 0)
            self.results["skipped"] = test_data.get("summary", {}).get("skipped", 0)
            self.results["tests"] = test_data.get("tests", [])

        if result.timed_out:
            raise TimeoutError(
                operation="pytest execution",
                timeout_seconds=600,
                context={"test_directory": test_dir},
            )

        if not result.success:
            raise IntegrationExecutionError(
                test_framework="pytest",
                details=f"{self.results.get('failed', 0)} tests failed",
                context={
                    "test_directory": test_dir,
                    "passed": self.results.get("passed", 0),
                    "failed": self.results.get("failed", 0),
                    "skipped": self.results.get("skipped", 0),
                    "stderr": result.stderr,
                },
            )

    def _run_jest(self) -> None:
        """
        Run integration tests using Jest.

        Raises:
            TimeoutError: If tests timeout
            IntegrationExecutionError: If tests fail
        """
        result = self.runner.run(
            [
                "npm",
                "test",
                "--",
                "--testPathPattern=integration",
                "--json",
                "--outputFile=integration-test-results.json",
            ],
            timeout=INTEGRATION_TEST_TIMEOUT,
        )

        # Parse results
        results_file = Path("integration-test-results.json")
        if results_file.exists():
            with open(results_file) as f:
                test_data = json.load(f)

            self.results["passed"] = test_data.get("numPassedTests", 0)
            self.results["failed"] = test_data.get("numFailedTests", 0)
            self.results["skipped"] = test_data.get("numPendingTests", 0)

        if result.timed_out:
            raise TimeoutError(
                operation="jest execution",
                timeout_seconds=600,
                context={"test_pattern": "integration"},
            )

        if not result.success:
            raise IntegrationExecutionError(
                test_framework="jest",
                details=f"{self.results.get('failed', 0)} tests failed",
                context={
                    "passed": self.results.get("passed", 0),
                    "failed": self.results.get("failed", 0),
                    "skipped": self.results.get("skipped", 0),
                    "stderr": result.stderr,
                },
            )

    def _detect_language(self) -> str:
        """Detect project language."""
        if Path("pyproject.toml").exists() or Path("setup.py").exists():
            return "python"
        elif Path("package.json").exists():
            if Path("tsconfig.json").exists():
                return "typescript"
            return "javascript"
        return "python"

    def teardown_environment(self) -> None:
        """
        Tear down integration test environment.

        Raises:
            EnvironmentSetupError: If teardown fails
            TimeoutError: If teardown times out
        """
        logger.info("\nTearing down integration test environment...")

        compose_file = self.env_requirements.get("compose_file", "docker-compose.integration.yml")

        # Stop and remove services
        result = self.runner.run(
            ["docker-compose", "-f", compose_file, "down", "-v"],
            timeout=CLEANUP_TIMEOUT,
        )

        if not result.success:
            if result.timed_out:
                raise TimeoutError(
                    operation="docker-compose teardown",
                    timeout_seconds=60,
                    context={"compose_file": compose_file},
                )
            raise EnvironmentSetupError(
                component="docker-compose teardown",
                details=result.stderr or "Failed to tear down services",
                context={"compose_file": compose_file, "stderr": result.stderr},
            )

        logger.info("✓ Services stopped and removed")
        logger.info("✓ Volumes cleaned up")

    def generate_report(self) -> str:
        """Generate integration test report."""
        report = f"""
Integration Test Report
{"=" * 80}

Work Item: {self.work_item.get("id", "N/A")}
Test Name: {self.work_item.get("title", "N/A")}

Duration: {self.results["total_duration"]:.2f} seconds

Results:
  ✓ Passed:  {self.results["passed"]}
  ✗ Failed:  {self.results["failed"]}
  ○ Skipped: {self.results["skipped"]}

Status: {"PASSED" if self.results["failed"] == 0 else "FAILED"}
"""
        return report


def main() -> None:
    """
    CLI entry point.

    Raises:
        ValidationError: If arguments invalid
        WorkItemNotFoundError: If work item not found
        Various exceptions from runner methods
    """
    from solokit.core.exceptions import WorkItemNotFoundError
    from solokit.core.file_ops import load_json

    if len(sys.argv) < 2:
        raise ValidationError(
            message="Missing required argument: work_item_id",
            context={"usage": "python integration_test_runner.py <work_item_id>"},
            remediation="Provide work item ID as command-line argument",
        )

    work_item_id = sys.argv[1]

    # Load work item
    work_items_file = Path(".session/tracking/work_items.json")
    data = load_json(work_items_file)
    work_item = data["work_items"].get(work_item_id)

    if not work_item:
        raise WorkItemNotFoundError(work_item_id)

    # Run integration tests
    runner = IntegrationTestRunner(work_item)

    try:
        # Setup
        runner.setup_environment()

        # Execute tests
        results = runner.run_tests()

        # Print report
        output.info(runner.generate_report())

        # Teardown
        runner.teardown_environment()

        # Exit with code 1 if tests failed
        if results.get("failed", 0) > 0:
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception:
        # Attempt teardown on any failure
        try:
            runner.teardown_environment()
        except Exception as teardown_error:
            logger.warning(f"Teardown failed: {teardown_error}")

        # Re-raise the original exception for proper error handling
        raise


if __name__ == "__main__":
    main()
