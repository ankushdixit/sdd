"""Shared pytest fixtures for SDD test suite.

This module provides common fixtures used across unit, integration, and e2e tests.
"""

import json
import logging
from typing import Any

import pytest


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test isolation.

    Returns:
        Path: Temporary directory path that is automatically cleaned up.
    """
    return tmp_path


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary SDD project directory structure.

    Creates:
        - .session/ directory
        - work_items/ directory
        - learnings/ directory
        - specs/ directory

    Returns:
        Path: Root directory of temporary project.
    """
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Create standard SDD directories
    (project_dir / ".session").mkdir()
    (project_dir / "work_items").mkdir()
    (project_dir / "learnings").mkdir()
    (project_dir / "specs").mkdir()

    return project_dir


@pytest.fixture
def sample_config() -> dict[str, Any]:
    """Provide a sample SDD configuration dictionary.

    Returns:
        dict: Sample configuration with default values.
    """
    return {
        "project_name": "test_project",
        "integration_tests": {"enabled": True, "performance_benchmarks": True},
        "api_contracts": {"enabled": True},
        "quality_gates": {
            "coverage_threshold": 75,
            "enable_linting": True,
            "enable_security_scan": True,
        },
    }


@pytest.fixture
def sample_work_item() -> dict[str, Any]:
    """Provide a sample work item dictionary.

    Returns:
        dict: Sample work item with all required fields.
    """
    return {
        "id": "WI-001",
        "title": "Test Work Item",
        "type": "feature",
        "status": "not_started",
        "description": "A sample work item for testing",
        "dependencies": [],
        "milestone": None,
        "priority": "medium",
    }


@pytest.fixture
def sample_learning() -> dict[str, Any]:
    """Provide a sample learning dictionary.

    Returns:
        dict: Sample learning entry with all required fields.
    """
    return {
        "id": "L-001",
        "session_id": "S-001",
        "category": "technical",
        "content": "Test learning content",
        "tags": ["test", "sample"],
        "timestamp": "2025-10-24T10:00:00",
    }


@pytest.fixture
def mock_git_repo(temp_project_dir):
    """Initialize a mock git repository in the temporary project directory.

    Args:
        temp_project_dir: Temporary project directory fixture.

    Returns:
        Path: Root directory with initialized git repository.
    """
    import subprocess

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=temp_project_dir, capture_output=True, check=True)

    # Configure git user for commits
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=temp_project_dir,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=temp_project_dir,
        capture_output=True,
        check=True,
    )

    return temp_project_dir


@pytest.fixture
def config_file(temp_project_dir, sample_config):
    """Create a config.json file in the temporary project.

    Args:
        temp_project_dir: Temporary project directory fixture.
        sample_config: Sample configuration fixture.

    Returns:
        Path: Path to the created config.json file.
    """
    config_path = temp_project_dir / ".session" / "config.json"
    config_path.write_text(json.dumps(sample_config, indent=2))
    return config_path


@pytest.fixture
def work_items_dir(temp_project_dir):
    """Provide path to work_items directory in temporary project.

    Args:
        temp_project_dir: Temporary project directory fixture.

    Returns:
        Path: Path to work_items directory.
    """
    return temp_project_dir / "work_items"


@pytest.fixture
def learnings_dir(temp_project_dir):
    """Provide path to learnings directory in temporary project.

    Args:
        temp_project_dir: Temporary project directory fixture.

    Returns:
        Path: Path to learnings directory.
    """
    return temp_project_dir / "learnings"


@pytest.fixture
def specs_dir(temp_project_dir):
    """Provide path to specs directory in temporary project.

    Args:
        temp_project_dir: Temporary project directory fixture.

    Returns:
        Path: Path to specs directory.
    """
    return temp_project_dir / "specs"


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging configuration before each test.

    This fixture runs automatically before each test to ensure
    logging state doesn't leak between tests.
    """
    # Remove all handlers from root logger
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Reset to default level
    root_logger.setLevel(logging.WARNING)

    yield

    # Cleanup after test
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)


@pytest.fixture
def capture_logs():
    """Capture log messages during test execution.

    Returns:
        list: List of log records captured during test.
    """

    class LogCapture(logging.Handler):
        def __init__(self):
            super().__init__()
            self.records = []

        def emit(self, record):
            self.records.append(record)

    handler = LogCapture()
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    yield handler.records

    logger.removeHandler(handler)
