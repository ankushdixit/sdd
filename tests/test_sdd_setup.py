"""SDD Project Setup Validation Tests"""

import json
from pathlib import Path

import pytest

# Skip all tests in this file if .session doesn't exist (not initialized)
pytestmark = pytest.mark.skipif(
    not Path(".session").exists(),
    reason=".session directory not found (SDD not initialized)",
)


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
    assert has_metadata, (
        "No project metadata file found (pyproject.toml, setup.py, or package.json)"
    )
