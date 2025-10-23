"""SDD Project Setup Validation Tests"""

import json
import subprocess
from pathlib import Path

import pytest


def test_project_structure():
    """Verify SDD project structure exists."""
    assert Path(".session/tracking").exists(), ".session/tracking directory missing"
    assert Path(".session/specs").exists(), ".session/specs directory missing"
    assert Path(".session/briefings").exists(), ".session/briefings directory missing"
    assert Path(".session/history").exists(), ".session/history directory missing"


def test_tracking_files():
    """Verify tracking files exist and are valid JSON."""
    work_items_file = Path(".session/tracking/work_items.json")
    assert work_items_file.exists(), "work_items.json missing"

    with open(work_items_file) as f:
        data = json.load(f)
        assert "metadata" in data
        assert "work_items" in data

    learnings_file = Path(".session/tracking/learnings.json")
    assert learnings_file.exists(), "learnings.json missing"

    with open(learnings_file) as f:
        data = json.load(f)
        assert "categories" in data


def test_session_config():
    """Verify session config exists and is valid."""
    config_file = Path(".session/config.json")
    assert config_file.exists(), "config.json missing"

    with open(config_file) as f:
        data = json.load(f)
        assert "quality_gates" in data
        assert "curation" in data


def test_project_metadata():
    """Verify project has basic metadata files."""
    # At least one of these should exist
    has_metadata = (
        Path("pyproject.toml").exists()
        or Path("setup.py").exists()
        or Path("package.json").exists()
    )
    assert (
        has_metadata
    ), "No project metadata file found (pyproject.toml, setup.py, or package.json)"


def test_initial_commit_exists():
    """Verify that an initial commit was created during sdd init."""
    # Check if .git directory exists
    assert Path(".git").exists(), "Git repository not initialized"

    try:
        # Get commit count
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        commit_count = int(result.stdout.strip())
        assert commit_count > 0, "No commits found in repository"

        # Get the first commit message
        result = subprocess.run(
            ["git", "log", "--reverse", "--format=%B", "-n", "1"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        first_commit_message = result.stdout.strip()

        # Verify it's an SDD initialization commit
        assert (
            "Initialize project with Session-Driven Development" in first_commit_message
            or "Session-Driven Development" in first_commit_message
        ), f"First commit doesn't appear to be SDD initialization commit. Message: {first_commit_message[:100]}"

    except subprocess.CalledProcessError as e:
        pytest.fail(f"Git command failed: {e}")
