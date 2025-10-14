#!/usr/bin/env python3
"""
Integration test execution framework.

Supports:
- Multi-service orchestration
- Test environment setup/teardown
- Test data management
- Parallel test execution
- Result aggregation
"""

import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime


class IntegrationTestRunner:
    """Execute integration tests with multi-service orchestration."""

    def __init__(self, work_item: dict):
        """
        Initialize integration test runner.

        Args:
            work_item: Integration test work item with test specifications
        """
        self.work_item = work_item
        self.test_scenarios = work_item.get("test_scenarios", [])
        self.env_requirements = work_item.get("environment_requirements", {})
        self.results = {
            "scenarios": [],
            "start_time": None,
            "end_time": None,
            "total_duration": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0
        }

    def setup_environment(self) -> Tuple[bool, str]:
        """
        Set up integration test environment.

        Returns:
            (success: bool, message: str)
        """
        print("Setting up integration test environment...")

        # Check if Docker Compose file exists
        compose_file = self.env_requirements.get("compose_file", "docker-compose.integration.yml")
        if not Path(compose_file).exists():
            return False, f"Docker Compose file not found: {compose_file}"

        # Start services
        try:
            result = subprocess.run(
                ["docker-compose", "-f", compose_file, "up", "-d"],
                capture_output=True,
                text=True,
                timeout=180
            )

            if result.returncode != 0:
                return False, f"Failed to start services: {result.stderr}"

            print(f"✓ Services started from {compose_file}")
        except subprocess.TimeoutExpired:
            return False, "Timeout starting services (>3 minutes)"
        except Exception as e:
            return False, f"Error starting services: {str(e)}"

        # Wait for services to be healthy
        services = self.env_requirements.get("services_required", [])
        for service in services:
            if not self._wait_for_service(service):
                return False, f"Service {service} failed to become healthy"

        print(f"✓ All {len(services)} services are healthy")

        # Load test data
        if not self._load_test_data():
            return False, "Failed to load test data"

        print("✓ Integration test environment ready")
        return True, "Environment setup successful"

    def _wait_for_service(self, service: str, timeout: int = 60) -> bool:
        """
        Wait for service to be healthy.

        Args:
            service: Service name
            timeout: Maximum wait time in seconds

        Returns:
            True if service becomes healthy, False otherwise
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                result = subprocess.run(
                    ["docker-compose", "ps", "-q", service],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode == 0 and result.stdout.strip():
                    # Check health status
                    health_result = subprocess.run(
                        ["docker", "inspect", "--format='{{.State.Health.Status}}'",
                         result.stdout.strip()],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    if "healthy" in health_result.stdout:
                        return True

                time.sleep(2)
            except:
                time.sleep(2)

        return False

    def _load_test_data(self) -> bool:
        """Load test data fixtures."""
        fixtures = self.env_requirements.get("test_data_fixtures", [])

        for fixture in fixtures:
            fixture_path = Path(fixture)
            if not fixture_path.exists():
                print(f"⚠️  Fixture not found: {fixture}")
                continue

            # Execute fixture loading script
            try:
                subprocess.run(
                    ["python", str(fixture_path)],
                    check=True,
                    timeout=30
                )
                print(f"✓ Loaded fixture: {fixture}")
            except Exception as e:
                print(f"✗ Failed to load fixture {fixture}: {e}")
                return False

        return True

    def run_tests(self, language: str = None) -> Tuple[bool, dict]:
        """
        Execute all integration test scenarios.

        Args:
            language: Project language (python, javascript, typescript)

        Returns:
            (all_passed: bool, results: dict)
        """
        self.results["start_time"] = datetime.now().isoformat()

        print(f"\nRunning {len(self.test_scenarios)} integration test scenarios...\n")

        # Detect language if not provided
        if language is None:
            language = self._detect_language()

        # Run scenarios based on language
        if language == "python":
            all_passed = self._run_pytest()
        elif language in ["javascript", "typescript"]:
            all_passed = self._run_jest()
        else:
            return False, {"error": f"Unsupported language: {language}"}

        self.results["end_time"] = datetime.now().isoformat()

        # Calculate duration
        start = datetime.fromisoformat(self.results["start_time"])
        end = datetime.fromisoformat(self.results["end_time"])
        self.results["total_duration"] = (end - start).total_seconds()

        return all_passed, self.results

    def _run_pytest(self) -> bool:
        """Run integration tests using pytest."""
        test_dir = self.work_item.get("test_directory", "tests/integration")

        try:
            result = subprocess.run(
                [
                    "pytest",
                    test_dir,
                    "-v",
                    "--tb=short",
                    "--json-report",
                    "--json-report-file=integration-test-results.json"
                ],
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
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

            return result.returncode == 0

        except subprocess.TimeoutExpired:
            self.results["error"] = "Tests timed out after 10 minutes"
            return False
        except Exception as e:
            self.results["error"] = str(e)
            return False

    def _run_jest(self) -> bool:
        """Run integration tests using Jest."""
        try:
            result = subprocess.run(
                [
                    "npm", "test",
                    "--",
                    "--testPathPattern=integration",
                    "--json",
                    "--outputFile=integration-test-results.json"
                ],
                capture_output=True,
                text=True,
                timeout=600
            )

            # Parse results
            results_file = Path("integration-test-results.json")
            if results_file.exists():
                with open(results_file) as f:
                    test_data = json.load(f)

                self.results["passed"] = test_data.get("numPassedTests", 0)
                self.results["failed"] = test_data.get("numFailedTests", 0)
                self.results["skipped"] = test_data.get("numPendingTests", 0)

            return result.returncode == 0

        except subprocess.TimeoutExpired:
            self.results["error"] = "Tests timed out after 10 minutes"
            return False
        except Exception as e:
            self.results["error"] = str(e)
            return False

    def _detect_language(self) -> str:
        """Detect project language."""
        if Path("pyproject.toml").exists() or Path("setup.py").exists():
            return "python"
        elif Path("package.json").exists():
            if Path("tsconfig.json").exists():
                return "typescript"
            return "javascript"
        return "python"

    def teardown_environment(self) -> Tuple[bool, str]:
        """
        Tear down integration test environment.

        Returns:
            (success: bool, message: str)
        """
        print("\nTearing down integration test environment...")

        compose_file = self.env_requirements.get("compose_file", "docker-compose.integration.yml")

        try:
            # Stop and remove services
            result = subprocess.run(
                ["docker-compose", "-f", compose_file, "down", "-v"],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                return False, f"Failed to tear down services: {result.stderr}"

            print("✓ Services stopped and removed")
            print("✓ Volumes cleaned up")

            return True, "Environment teardown successful"

        except subprocess.TimeoutExpired:
            return False, "Timeout tearing down services"
        except Exception as e:
            return False, f"Error tearing down services: {str(e)}"

    def generate_report(self) -> str:
        """Generate integration test report."""
        report = f"""
Integration Test Report
{'='*80}

Work Item: {self.work_item.get('id', 'N/A')}
Test Name: {self.work_item.get('title', 'N/A')}

Duration: {self.results['total_duration']:.2f} seconds

Results:
  ✓ Passed:  {self.results['passed']}
  ✗ Failed:  {self.results['failed']}
  ○ Skipped: {self.results['skipped']}

Status: {'PASSED' if self.results['failed'] == 0 else 'FAILED'}
"""
        return report


def main():
    """CLI entry point."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python integration_test_runner.py <work_item_id>")
        sys.exit(1)

    work_item_id = sys.argv[1]

    # Load work item
    from file_ops import load_json
    work_items_file = Path(".session/tracking/work_items.json")
    data = load_json(work_items_file)
    work_item = data["work_items"].get(work_item_id)

    if not work_item:
        print(f"Work item not found: {work_item_id}")
        sys.exit(1)

    # Run integration tests
    runner = IntegrationTestRunner(work_item)

    # Setup
    success, message = runner.setup_environment()
    if not success:
        print(f"✗ Environment setup failed: {message}")
        sys.exit(1)

    # Execute tests
    try:
        all_passed, results = runner.run_tests()

        # Print report
        print(runner.generate_report())

        # Teardown
        success, message = runner.teardown_environment()
        if not success:
            print(f"⚠️  Warning: {message}")

        sys.exit(0 if all_passed else 1)

    except Exception as e:
        print(f"✗ Integration tests failed: {e}")
        runner.teardown_environment()
        sys.exit(1)


if __name__ == "__main__":
    main()
