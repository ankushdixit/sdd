"""Unit tests for integration_test_runner module.

This module tests the IntegrationTestRunner class which executes integration tests
with multi-service orchestration using Docker Compose.
"""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from sdd.testing.integration_runner import IntegrationTestRunner


class TestIntegrationTestRunnerInit:
    """Tests for IntegrationTestRunner initialization."""

    def test_init_with_valid_work_item_and_spec_file(self, tmp_path):
        """Test that IntegrationTestRunner initializes with valid work item and spec file."""
        # Arrange
        work_item = {"id": "INTEG-001", "type": "integration_test", "title": "Test API Integration"}

        mock_parsed_spec = {
            "test_scenarios": [
                {
                    "name": "Happy path",
                    "setup": "Start services",
                    "actions": ["Send request"],
                    "expected_results": "HTTP 200",
                }
            ],
            "environment_requirements": "postgresql\nredis\ndocker-compose.integration.yml",
        }

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec

            # Act
            runner = IntegrationTestRunner(work_item)

            # Assert
            assert runner.work_item == work_item
            assert len(runner.test_scenarios) == 1
            assert runner.test_scenarios[0]["name"] == "Happy path"
            assert "postgresql" in runner.env_requirements["services_required"]
            assert "redis" in runner.env_requirements["services_required"]
            assert runner.results["passed"] == 0
            assert runner.results["failed"] == 0
            assert runner.results["skipped"] == 0

    def test_init_without_work_item_id_raises_error(self):
        """Test that initialization fails when work item has no ID."""
        # Arrange
        work_item = {"type": "integration_test", "title": "Test without ID"}

        # Act & Assert
        with pytest.raises(ValueError, match="Work item must have 'id' field"):
            IntegrationTestRunner(work_item)

    def test_init_with_missing_spec_file_raises_error(self):
        """Test that initialization fails when spec file is not found."""
        # Arrange
        work_item = {"id": "INTEG-002", "type": "integration_test"}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.side_effect = FileNotFoundError("Spec file not found")

            # Act & Assert
            with pytest.raises(ValueError, match="Spec file not found for work item: INTEG-002"):
                IntegrationTestRunner(work_item)

    def test_init_with_invalid_spec_file_raises_error(self):
        """Test that initialization fails when spec file parsing fails."""
        # Arrange
        work_item = {"id": "INTEG-003", "type": "integration_test"}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.side_effect = Exception("Invalid YAML")

            # Act & Assert
            with pytest.raises(ValueError, match="Failed to parse spec file for INTEG-003"):
                IntegrationTestRunner(work_item)

    def test_init_results_dictionary_initialized_correctly(self):
        """Test that results dictionary is initialized with all required keys."""
        # Arrange
        work_item = {"id": "INTEG-004"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec

            # Act
            runner = IntegrationTestRunner(work_item)

            # Assert
            expected_keys = [
                "scenarios",
                "start_time",
                "end_time",
                "total_duration",
                "passed",
                "failed",
                "skipped",
            ]
            assert all(key in runner.results for key in expected_keys)
            assert runner.results["start_time"] is None
            assert runner.results["end_time"] is None
            assert runner.results["total_duration"] == 0


class TestEnvironmentRequirementsParsing:
    """Tests for parsing environment requirements from spec text."""

    def test_parse_environment_requirements_with_empty_text(self):
        """Test parsing with empty environment requirements text."""
        # Arrange
        work_item = {"id": "INTEG-005"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec

            # Act
            runner = IntegrationTestRunner(work_item)

            # Assert
            assert runner.env_requirements["services_required"] == []
            assert runner.env_requirements["compose_file"] == "docker-compose.integration.yml"

    def test_parse_environment_requirements_with_postgresql(self):
        """Test parsing environment requirements with PostgreSQL service."""
        # Arrange
        work_item = {"id": "INTEG-006"}
        mock_parsed_spec = {
            "test_scenarios": [],
            "environment_requirements": "PostgreSQL database\nRedis cache",
        }

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec

            # Act
            runner = IntegrationTestRunner(work_item)

            # Assert
            assert "PostgreSQL" in runner.env_requirements["services_required"]
            assert "Redis" in runner.env_requirements["services_required"]

    def test_parse_environment_requirements_with_custom_compose_file(self):
        """Test parsing environment requirements with custom Docker Compose file."""
        # Arrange
        work_item = {"id": "INTEG-007"}
        env_text = "MongoDB database\nUse `docker-compose.custom.yml` for orchestration"
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": env_text}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec

            # Act
            runner = IntegrationTestRunner(work_item)

            # Assert
            assert runner.env_requirements["compose_file"] == "docker-compose.custom.yml"
            assert "MongoDB" in runner.env_requirements["services_required"]

    def test_parse_environment_requirements_with_multiple_services(self):
        """Test parsing environment requirements with multiple different services."""
        # Arrange
        work_item = {"id": "INTEG-008"}
        env_text = """postgresql database
redis for caching
nginx reverse proxy
kafka message broker"""
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": env_text}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec

            # Act
            runner = IntegrationTestRunner(work_item)

            # Assert
            assert len(runner.env_requirements["services_required"]) == 4
            assert "postgresql" in runner.env_requirements["services_required"]
            assert "redis" in runner.env_requirements["services_required"]
            assert "nginx" in runner.env_requirements["services_required"]
            assert "kafka" in runner.env_requirements["services_required"]


class TestLanguageDetection:
    """Tests for project language detection."""

    def test_detect_language_python_with_pyproject_toml(self, tmp_path, monkeypatch):
        """Test that Python is detected when pyproject.toml exists."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pyproject.toml").write_text("[tool.poetry]\nname = 'test'")

        work_item = {"id": "INTEG-009"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            # Act
            detected = runner._detect_language()

            # Assert
            assert detected == "python"

    def test_detect_language_python_with_setup_py(self, tmp_path, monkeypatch):
        """Test that Python is detected when setup.py exists."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        (tmp_path / "setup.py").write_text("from setuptools import setup")

        work_item = {"id": "INTEG-010"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            # Act
            detected = runner._detect_language()

            # Assert
            assert detected == "python"

    def test_detect_language_javascript_with_package_json(self, tmp_path, monkeypatch):
        """Test that JavaScript is detected when package.json exists without tsconfig.json."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        (tmp_path / "package.json").write_text("{}")

        work_item = {"id": "INTEG-011"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            # Act
            detected = runner._detect_language()

            # Assert
            assert detected == "javascript"

    def test_detect_language_typescript_with_both_configs(self, tmp_path, monkeypatch):
        """Test that TypeScript is detected when both package.json and tsconfig.json exist."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        (tmp_path / "package.json").write_text("{}")
        (tmp_path / "tsconfig.json").write_text("{}")

        work_item = {"id": "INTEG-012"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            # Act
            detected = runner._detect_language()

            # Assert
            assert detected == "typescript"

    def test_detect_language_defaults_to_python(self, tmp_path, monkeypatch):
        """Test that language detection defaults to Python when no config files exist."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        work_item = {"id": "INTEG-013"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            # Act
            detected = runner._detect_language()

            # Assert
            assert detected == "python"


class TestReportGeneration:
    """Tests for integration test report generation."""

    def test_generate_report_with_passed_tests(self):
        """Test report generation when all tests pass."""
        # Arrange
        work_item = {"id": "INTEG-014", "title": "API Integration Tests"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            runner.results = {
                "start_time": "2024-01-01T10:00:00",
                "end_time": "2024-01-01T10:05:30",
                "total_duration": 330.0,
                "passed": 10,
                "failed": 0,
                "skipped": 1,
            }

            # Act
            report = runner.generate_report()

            # Assert
            assert "Integration Test Report" in report
            assert "INTEG-014" in report
            assert "API Integration Tests" in report
            assert "PASSED" in report
            assert "10" in report
            assert "0" in report

    def test_generate_report_with_failed_tests(self):
        """Test report generation when tests fail."""
        # Arrange
        work_item = {"id": "INTEG-015", "title": "Database Integration Tests"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            runner.results = {
                "start_time": "2024-01-01T10:00:00",
                "end_time": "2024-01-01T10:05:30",
                "total_duration": 330.0,
                "passed": 8,
                "failed": 2,
                "skipped": 0,
            }

            # Act
            report = runner.generate_report()

            # Assert
            assert "Integration Test Report" in report
            assert "FAILED" in report
            assert "2" in report

    def test_generate_report_includes_duration(self):
        """Test that report includes test duration in seconds."""
        # Arrange
        work_item = {"id": "INTEG-016"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            runner.results = {"total_duration": 42.5, "passed": 5, "failed": 0, "skipped": 0}

            # Act
            report = runner.generate_report()

            # Assert
            assert "42.50 seconds" in report


class TestIntegrationTestRunnerStructure:
    """Tests for file structure and method existence."""

    def test_integration_test_runner_file_exists(self):
        """Test that integration_test_runner.py file exists."""
        # Arrange & Act
        file_path = Path("src/sdd/testing/integration_runner.py")

        # Assert
        assert file_path.exists()

    def test_integration_test_runner_has_required_methods(self):
        """Test that IntegrationTestRunner class has all required methods."""
        # Arrange
        work_item = {"id": "INTEG-017"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        required_methods = [
            "setup_environment",
            "_wait_for_service",
            "_load_test_data",
            "run_tests",
            "_run_pytest",
            "_run_jest",
            "_detect_language",
            "teardown_environment",
            "generate_report",
            "_parse_environment_requirements",
        ]

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec

            # Act
            runner = IntegrationTestRunner(work_item)

            # Assert
            for method in required_methods:
                assert hasattr(runner, method), f"Missing method: {method}"

    def test_integration_test_runner_file_has_main_function(self):
        """Test that integration_test_runner.py has main function."""
        # Arrange
        file_path = Path("src/sdd/testing/integration_runner.py")
        content = file_path.read_text()

        # Act & Assert
        assert "def main():" in content

    def test_integration_test_runner_file_has_required_imports(self):
        """Test that integration_test_runner.py has required imports."""
        # Arrange
        file_path = Path("src/sdd/testing/integration_runner.py")
        content = file_path.read_text()

        required_imports = [
            "import subprocess",
            "import json",
            "import time",
            "from pathlib import Path",
            "from datetime import datetime",
        ]

        # Act & Assert
        for imp in required_imports:
            assert imp in content, f"Missing import: {imp}"

    def test_integration_test_runner_class_defined(self):
        """Test that IntegrationTestRunner class is defined."""
        # Arrange
        file_path = Path("src/sdd/testing/integration_runner.py")
        content = file_path.read_text()

        # Act & Assert
        assert "class IntegrationTestRunner:" in content


class TestDockerComposeSupport:
    """Tests for Docker Compose integration configuration."""

    def test_custom_compose_file_configuration(self):
        """Test that custom Docker Compose file is configured correctly."""
        # Arrange
        work_item = {"id": "INTEG-018"}
        env_text = "Services defined in custom-compose.yml for orchestration"
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": env_text}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec

            # Act
            runner = IntegrationTestRunner(work_item)

            # Assert
            assert runner.env_requirements["compose_file"] == "custom-compose.yml"

    def test_multiple_services_configured_correctly(self):
        """Test that multiple services are configured from environment requirements."""
        # Arrange
        work_item = {"id": "INTEG-019"}
        env_text = """postgres database (db)
redis cache
nginx API gateway"""
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": env_text}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec

            # Act
            runner = IntegrationTestRunner(work_item)

            # Assert
            services = runner.env_requirements["services_required"]
            assert len(services) >= 2
            assert any("postgres" in s.lower() for s in services)
            assert any("redis" in s.lower() for s in services)

    def test_test_scenarios_stored_correctly(self):
        """Test that test scenarios from spec are stored correctly."""
        # Arrange
        work_item = {"id": "INTEG-020"}
        mock_parsed_spec = {
            "test_scenarios": [{"name": "Scenario 1"}, {"name": "Scenario 2"}],
            "environment_requirements": "",
        }

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec

            # Act
            runner = IntegrationTestRunner(work_item)

            # Assert
            assert len(runner.test_scenarios) == 2
            assert runner.test_scenarios[0]["name"] == "Scenario 1"
            assert runner.test_scenarios[1]["name"] == "Scenario 2"

    def test_work_item_data_accessible(self):
        """Test that work item data is accessible after initialization."""
        # Arrange
        work_item = {"id": "INTEG-021", "title": "Integration Test", "type": "integration_test"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec

            # Act
            runner = IntegrationTestRunner(work_item)

            # Assert
            assert runner.work_item["id"] == "INTEG-021"
            assert runner.work_item["title"] == "Integration Test"
            assert runner.work_item["type"] == "integration_test"


class TestEnvironmentSetup:
    """Tests for integration test environment setup."""

    def test_setup_environment_success_with_valid_compose_file(self, tmp_path, monkeypatch):
        """Test successful environment setup with valid Docker Compose file."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        compose_file = tmp_path / "docker-compose.integration.yml"
        compose_file.write_text("version: '3'\nservices:\n  test:\n    image: test")

        work_item = {"id": "INTEG-022"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(returncode=0, stderr="")
                with patch.object(runner, "_load_test_data", return_value=True):
                    # Act
                    success, message = runner.setup_environment()

                    # Assert
                    assert success
                    assert "successful" in message.lower()

    def test_setup_environment_fails_when_compose_file_missing(self, tmp_path, monkeypatch):
        """Test that setup fails when Docker Compose file doesn't exist."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        work_item = {"id": "INTEG-023"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            # Act
            success, message = runner.setup_environment()

            # Assert
            assert not success
            assert "not found" in message.lower()

    def test_setup_environment_fails_when_docker_compose_command_fails(self, tmp_path, monkeypatch):
        """Test that setup fails when docker-compose command returns non-zero exit code."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        compose_file = tmp_path / "docker-compose.integration.yml"
        compose_file.write_text("version: '3'")

        work_item = {"id": "INTEG-024"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(returncode=1, stderr="Error starting services")

                # Act
                success, message = runner.setup_environment()

                # Assert
                assert not success
                assert "failed to start" in message.lower()

    def test_setup_environment_handles_timeout(self, tmp_path, monkeypatch):
        """Test that setup handles timeout when starting services takes too long."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        compose_file = tmp_path / "docker-compose.integration.yml"
        compose_file.write_text("version: '3'")

        work_item = {"id": "INTEG-025"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.TimeoutExpired("docker-compose", 180)

                # Act
                success, message = runner.setup_environment()

                # Assert
                assert not success
                assert "timeout" in message.lower()

    def test_setup_environment_waits_for_services_to_be_healthy(self, tmp_path, monkeypatch):
        """Test that setup waits for required services to become healthy."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        compose_file = tmp_path / "docker-compose.integration.yml"
        compose_file.write_text("version: '3'")

        work_item = {"id": "INTEG-026"}
        env_text = "postgresql database\nredis cache"
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": env_text}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(returncode=0, stderr="")
                with patch.object(runner, "_wait_for_service", return_value=True) as mock_wait:
                    with patch.object(runner, "_load_test_data", return_value=True):
                        # Act
                        success, message = runner.setup_environment()

                        # Assert
                        assert success
                        assert mock_wait.call_count == 2  # Called for postgresql and redis

    def test_setup_environment_fails_when_service_not_healthy(self, tmp_path, monkeypatch):
        """Test that setup fails when a required service doesn't become healthy."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        compose_file = tmp_path / "docker-compose.integration.yml"
        compose_file.write_text("version: '3'")

        work_item = {"id": "INTEG-027"}
        env_text = "postgresql database"
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": env_text}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(returncode=0, stderr="")
                with patch.object(runner, "_wait_for_service", return_value=False):
                    # Act
                    success, message = runner.setup_environment()

                    # Assert
                    assert not success
                    assert "failed to become healthy" in message.lower()

    def test_setup_environment_fails_when_test_data_loading_fails(self, tmp_path, monkeypatch):
        """Test that setup fails when test data loading fails."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        compose_file = tmp_path / "docker-compose.integration.yml"
        compose_file.write_text("version: '3'")

        work_item = {"id": "INTEG-028"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(returncode=0, stderr="")
                with patch.object(runner, "_load_test_data", return_value=False):
                    # Act
                    success, message = runner.setup_environment()

                    # Assert
                    assert not success
                    assert "failed to load test data" in message.lower()

    def test_setup_environment_handles_generic_exception(self, tmp_path, monkeypatch):
        """Test that setup handles generic exceptions correctly."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        compose_file = tmp_path / "docker-compose.integration.yml"
        compose_file.write_text("version: '3'")

        work_item = {"id": "INTEG-052"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = Exception("Docker not available")

                # Act
                success, message = runner.setup_environment()

                # Assert
                assert not success
                assert "error starting services" in message.lower()
                assert "Docker not available" in message


class TestWaitForService:
    """Tests for service health checking."""

    def test_wait_for_service_returns_true_when_service_healthy(self):
        """Test that wait_for_service returns True when service becomes healthy."""
        # Arrange
        work_item = {"id": "INTEG-029"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            with patch("subprocess.run") as mock_run:
                # First call returns container ID, second call shows healthy status
                mock_run.side_effect = [
                    Mock(returncode=0, stdout="abc123\n"),
                    Mock(returncode=0, stdout="'healthy'"),
                ]

                # Act
                result = runner._wait_for_service("test-service", timeout=5)

                # Assert
                assert result is True

    def test_wait_for_service_returns_false_when_timeout_exceeded(self):
        """Test that wait_for_service returns False when timeout is exceeded."""
        # Arrange
        work_item = {"id": "INTEG-030"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            with patch("subprocess.run") as mock_run:
                # Always return unhealthy
                mock_run.side_effect = [
                    Mock(returncode=0, stdout="abc123\n"),
                    Mock(returncode=0, stdout="'starting'"),
                ] * 100

                with patch("time.sleep"):  # Speed up test
                    # Act
                    result = runner._wait_for_service("test-service", timeout=1)

                    # Assert
                    assert result is False

    def test_wait_for_service_handles_exception_gracefully(self):
        """Test that wait_for_service handles exceptions and continues polling."""
        # Arrange
        work_item = {"id": "INTEG-031"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            with patch("subprocess.run") as mock_run:
                # First call raises exception, second succeeds
                mock_run.side_effect = [
                    Exception("Connection refused"),
                    Mock(returncode=0, stdout="abc123\n"),
                    Mock(returncode=0, stdout="'healthy'"),
                ]

                with patch("time.sleep"):
                    # Act
                    result = runner._wait_for_service("test-service", timeout=5)

                    # Assert
                    assert result is True


class TestLoadTestData:
    """Tests for test data fixture loading."""

    def test_load_test_data_returns_true_when_no_fixtures(self):
        """Test that load_test_data returns True when no fixtures are configured."""
        # Arrange
        work_item = {"id": "INTEG-032"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            # Act
            result = runner._load_test_data()

            # Assert
            assert result is True

    def test_load_test_data_executes_fixtures_successfully(self, tmp_path):
        """Test that load_test_data executes all fixtures successfully."""
        # Arrange
        fixture1 = tmp_path / "fixture1.py"
        fixture1.write_text("print('Fixture 1')")
        fixture2 = tmp_path / "fixture2.py"
        fixture2.write_text("print('Fixture 2')")

        work_item = {"id": "INTEG-033"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)
            runner.env_requirements["test_data_fixtures"] = [str(fixture1), str(fixture2)]

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(returncode=0)

                # Act
                result = runner._load_test_data()

                # Assert
                assert result is True
                assert mock_run.call_count == 2

    def test_load_test_data_returns_false_when_fixture_fails(self, tmp_path):
        """Test that load_test_data returns False when a fixture execution fails."""
        # Arrange
        fixture = tmp_path / "fixture.py"
        fixture.write_text("raise Exception('Fixture failed')")

        work_item = {"id": "INTEG-034"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)
            runner.env_requirements["test_data_fixtures"] = [str(fixture)]

            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.CalledProcessError(1, ["python"])

                # Act
                result = runner._load_test_data()

                # Assert
                assert result is False

    def test_load_test_data_skips_missing_fixtures(self, tmp_path):
        """Test that load_test_data skips missing fixture files and continues."""
        # Arrange
        work_item = {"id": "INTEG-035"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)
            runner.env_requirements["test_data_fixtures"] = [str(tmp_path / "nonexistent.py")]

            # Act
            result = runner._load_test_data()

            # Assert
            assert result is True  # Should succeed even with missing fixture


class TestRunTests:
    """Tests for test execution."""

    def test_run_tests_executes_pytest_for_python_project(self):
        """Test that run_tests executes pytest for Python projects."""
        # Arrange
        work_item = {"id": "INTEG-036"}
        mock_parsed_spec = {"test_scenarios": [{"name": "Test 1"}], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            with patch.object(runner, "_run_pytest", return_value=True):
                # Act
                all_passed, results = runner.run_tests(language="python")

                # Assert
                assert all_passed
                assert results["start_time"] is not None
                assert results["end_time"] is not None
                assert results["total_duration"] >= 0

    def test_run_tests_executes_jest_for_javascript_project(self):
        """Test that run_tests executes jest for JavaScript projects."""
        # Arrange
        work_item = {"id": "INTEG-037"}
        mock_parsed_spec = {"test_scenarios": [{"name": "Test 1"}], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            with patch.object(runner, "_run_jest", return_value=True):
                # Act
                all_passed, results = runner.run_tests(language="javascript")

                # Assert
                assert all_passed

    def test_run_tests_detects_language_automatically(self, tmp_path, monkeypatch):
        """Test that run_tests detects project language when not specified."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        (tmp_path / "pyproject.toml").write_text("[tool.poetry]")

        work_item = {"id": "INTEG-038"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            with patch.object(runner, "_run_pytest", return_value=True):
                # Act
                all_passed, results = runner.run_tests()

                # Assert
                assert all_passed  # Should auto-detect python

    def test_run_tests_returns_error_for_unsupported_language(self):
        """Test that run_tests returns error for unsupported language."""
        # Arrange
        work_item = {"id": "INTEG-039"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            # Act
            all_passed, results = runner.run_tests(language="ruby")

            # Assert
            assert not all_passed
            assert "error" in results
            assert "unsupported" in results["error"].lower()


class TestRunPytest:
    """Tests for pytest execution."""

    def test_run_pytest_success_with_all_tests_passing(self, tmp_path):
        """Test pytest execution when all tests pass."""
        # Arrange
        work_item = {"id": "INTEG-040", "test_directory": "tests/integration"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        results_file = tmp_path / "integration-test-results.json"
        results_data = {
            "summary": {"passed": 10, "failed": 0, "skipped": 1},
            "tests": [{"name": "test_1", "outcome": "passed"}],
        }
        results_file.write_text(json.dumps(results_data))

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(returncode=0)
                with patch("pathlib.Path.exists", return_value=True):
                    with patch(
                        "builtins.open",
                        MagicMock(
                            return_value=MagicMock(
                                __enter__=lambda _: MagicMock(read=lambda: json.dumps(results_data))
                            )
                        ),
                    ):
                        # Act
                        result = runner._run_pytest()

                        # Assert
                        assert result is True
                        assert runner.results["passed"] == 10
                        assert runner.results["failed"] == 0

    def test_run_pytest_handles_test_failures(self):
        """Test pytest execution when tests fail."""
        # Arrange
        work_item = {"id": "INTEG-041"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(returncode=1)
                with patch("pathlib.Path.exists", return_value=False):
                    # Act
                    result = runner._run_pytest()

                    # Assert
                    assert result is False

    def test_run_pytest_handles_timeout(self):
        """Test pytest execution handles timeout correctly."""
        # Arrange
        work_item = {"id": "INTEG-042"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.TimeoutExpired("pytest", 600)

                # Act
                result = runner._run_pytest()

                # Assert
                assert result is False
                assert "timed out" in runner.results.get("error", "").lower()

    def test_run_pytest_handles_generic_exception(self):
        """Test pytest execution handles generic exceptions correctly."""
        # Arrange
        work_item = {"id": "INTEG-051"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = Exception("pytest not installed")

                # Act
                result = runner._run_pytest()

                # Assert
                assert result is False
                assert "error" in runner.results
                assert "pytest not installed" in runner.results["error"]


class TestRunJest:
    """Tests for Jest execution."""

    def test_run_jest_success_with_all_tests_passing(self, tmp_path):
        """Test Jest execution when all tests pass."""
        # Arrange
        work_item = {"id": "INTEG-046"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        results_file = tmp_path / "integration-test-results.json"
        results_data = {
            "numPassedTests": 15,
            "numFailedTests": 0,
            "numPendingTests": 2,
        }
        results_file.write_text(json.dumps(results_data))

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(returncode=0)
                with patch("pathlib.Path.exists", return_value=True):
                    with patch(
                        "builtins.open",
                        MagicMock(
                            return_value=MagicMock(
                                __enter__=lambda _: MagicMock(read=lambda: json.dumps(results_data))
                            )
                        ),
                    ):
                        # Act
                        result = runner._run_jest()

                        # Assert
                        assert result is True
                        assert runner.results["passed"] == 15
                        assert runner.results["failed"] == 0
                        assert runner.results["skipped"] == 2

    def test_run_jest_handles_test_failures(self):
        """Test Jest execution when tests fail."""
        # Arrange
        work_item = {"id": "INTEG-047"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(returncode=1)
                with patch("pathlib.Path.exists", return_value=False):
                    # Act
                    result = runner._run_jest()

                    # Assert
                    assert result is False

    def test_run_jest_handles_timeout(self):
        """Test Jest execution handles timeout correctly."""
        # Arrange
        work_item = {"id": "INTEG-048"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.TimeoutExpired("npm", 600)

                # Act
                result = runner._run_jest()

                # Assert
                assert result is False
                assert "timed out" in runner.results.get("error", "").lower()

    def test_run_jest_handles_exception(self):
        """Test Jest execution handles generic exceptions correctly."""
        # Arrange
        work_item = {"id": "INTEG-049"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = Exception("npm not found")

                # Act
                result = runner._run_jest()

                # Assert
                assert result is False
                assert "error" in runner.results
                assert "npm not found" in runner.results["error"]


class TestTeardownEnvironment:
    """Tests for environment teardown."""

    def test_teardown_environment_success(self, tmp_path, monkeypatch):
        """Test successful environment teardown."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        work_item = {"id": "INTEG-043"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(returncode=0, stderr="")

                # Act
                success, message = runner.teardown_environment()

                # Assert
                assert success
                assert "successful" in message.lower()

    def test_teardown_environment_fails_on_docker_compose_error(self):
        """Test teardown failure when docker-compose command fails."""
        # Arrange
        work_item = {"id": "INTEG-044"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(returncode=1, stderr="Error stopping services")

                # Act
                success, message = runner.teardown_environment()

                # Assert
                assert not success
                assert "failed to tear down" in message.lower()

    def test_teardown_environment_handles_timeout(self):
        """Test teardown handles timeout when stopping services takes too long."""
        # Arrange
        work_item = {"id": "INTEG-045"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.TimeoutExpired("docker-compose", 60)

                # Act
                success, message = runner.teardown_environment()

                # Assert
                assert not success
                assert "timeout" in message.lower()

    def test_teardown_environment_handles_generic_exception(self):
        """Test teardown handles generic exceptions correctly."""
        # Arrange
        work_item = {"id": "INTEG-050"}
        mock_parsed_spec = {"test_scenarios": [], "environment_requirements": ""}

        with patch("sdd.testing.integration_runner.spec_parser") as mock_parser:
            mock_parser.parse_spec_file.return_value = mock_parsed_spec
            runner = IntegrationTestRunner(work_item)

            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = Exception("Docker daemon not running")

                # Act
                success, message = runner.teardown_environment()

                # Assert
                assert not success
                assert "error tearing down" in message.lower()
                assert "Docker daemon not running" in message
