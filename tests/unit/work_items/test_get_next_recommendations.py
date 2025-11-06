"""Tests for get_next_recommendations module."""

import json
from unittest.mock import patch

import pytest

from sdd.work_items.get_next_recommendations import get_ready_work_items


@pytest.fixture
def setup_work_items(tmp_path, monkeypatch):
    """Setup work items file for testing."""
    # Change to tmp directory
    monkeypatch.chdir(tmp_path)

    # Create .session/tracking directory
    tracking_dir = tmp_path / ".session" / "tracking"
    tracking_dir.mkdir(parents=True)

    # Create work items data structure
    data = {
        "metadata": {
            "total_items": 6,
            "completed": 1,
            "in_progress": 1,
            "blocked": 0,
        },
        "milestones": {},
        "work_items": {
            "feature_auth": {
                "type": "feature",
                "title": "Add authentication",
                "status": "not_started",
                "priority": "high",
                "dependencies": [],
            },
            "feature_profile": {
                "type": "feature",
                "title": "User profile page",
                "status": "not_started",
                "priority": "medium",
                "dependencies": ["feature_auth"],
            },
            "bug_login": {
                "type": "bug",
                "title": "Fix login redirect",
                "status": "not_started",
                "priority": "critical",
                "dependencies": [],
            },
            "refactor_api": {
                "type": "refactor",
                "title": "Refactor API layer",
                "status": "not_started",
                "priority": "low",
                "dependencies": [],
            },
            "feature_dashboard": {
                "type": "feature",
                "title": "Admin dashboard",
                "status": "in_progress",
                "priority": "high",
                "dependencies": [],
            },
            "feature_export": {
                "type": "feature",
                "title": "Data export",
                "status": "completed",
                "priority": "medium",
                "dependencies": [],
            },
        },
    }

    work_items_file = tracking_dir / "work_items.json"
    with open(work_items_file, "w") as f:
        json.dump(data, f, indent=2)

    return tracking_dir


def test_get_ready_work_items_returns_ready_items(setup_work_items):
    """Test that get_ready_work_items returns items without dependencies."""
    ready = get_ready_work_items(limit=4)

    # Should return 3 ready items (bug_login, feature_auth, refactor_api)
    # feature_profile is blocked by feature_auth
    # feature_dashboard is in_progress
    # feature_export is completed
    assert len(ready) == 3

    # Check IDs are correct
    ids = [item["id"] for item in ready]
    assert "bug_login" in ids
    assert "feature_auth" in ids
    assert "refactor_api" in ids
    assert "feature_profile" not in ids  # Blocked
    assert "feature_dashboard" not in ids  # In progress
    assert "feature_export" not in ids  # Completed


def test_get_ready_work_items_sorted_by_priority(setup_work_items):
    """Test that items are sorted by priority (critical > high > medium > low)."""
    ready = get_ready_work_items(limit=4)

    # Should be sorted: bug_login (critical), feature_auth (high), refactor_api (low)
    assert ready[0]["id"] == "bug_login"
    assert ready[0]["priority"] == "critical"

    assert ready[1]["id"] == "feature_auth"
    assert ready[1]["priority"] == "high"

    assert ready[2]["id"] == "refactor_api"
    assert ready[2]["priority"] == "low"


def test_get_ready_work_items_respects_limit(setup_work_items):
    """Test that limit parameter works correctly."""
    # Get only 2 items
    ready = get_ready_work_items(limit=2)
    assert len(ready) == 2
    assert ready[0]["id"] == "bug_login"  # Critical
    assert ready[1]["id"] == "feature_auth"  # High

    # Get only 1 item
    ready = get_ready_work_items(limit=1)
    assert len(ready) == 1
    assert ready[0]["id"] == "bug_login"


def test_get_ready_work_items_filters_blocked_items(tmp_path, monkeypatch):
    """Test that items with unmet dependencies are filtered out."""
    monkeypatch.chdir(tmp_path)
    tracking_dir = tmp_path / ".session" / "tracking"
    tracking_dir.mkdir(parents=True)

    data = {
        "metadata": {},
        "milestones": {},
        "work_items": {
            "feature_base": {
                "type": "feature",
                "title": "Base feature",
                "status": "not_started",
                "priority": "high",
                "dependencies": [],
            },
            "feature_dependent": {
                "type": "feature",
                "title": "Dependent feature",
                "status": "not_started",
                "priority": "critical",  # Higher priority but blocked
                "dependencies": ["feature_base"],
            },
        },
    }

    work_items_file = tracking_dir / "work_items.json"
    with open(work_items_file, "w") as f:
        json.dump(data, f, indent=2)

    ready = get_ready_work_items(limit=4)

    # Only feature_base should be ready
    assert len(ready) == 1
    assert ready[0]["id"] == "feature_base"


def test_get_ready_work_items_includes_completed_dependency(tmp_path, monkeypatch):
    """Test that items with completed dependencies are included."""
    monkeypatch.chdir(tmp_path)
    tracking_dir = tmp_path / ".session" / "tracking"
    tracking_dir.mkdir(parents=True)

    data = {
        "metadata": {},
        "milestones": {},
        "work_items": {
            "feature_base": {
                "type": "feature",
                "title": "Base feature",
                "status": "completed",  # Completed
                "priority": "high",
                "dependencies": [],
            },
            "feature_dependent": {
                "type": "feature",
                "title": "Dependent feature",
                "status": "not_started",
                "priority": "high",
                "dependencies": ["feature_base"],  # Dependency is completed
            },
        },
    }

    work_items_file = tracking_dir / "work_items.json"
    with open(work_items_file, "w") as f:
        json.dump(data, f, indent=2)

    ready = get_ready_work_items(limit=4)

    # feature_dependent should be ready since its dependency is completed
    assert len(ready) == 1
    assert ready[0]["id"] == "feature_dependent"


def test_get_ready_work_items_no_work_items(tmp_path, monkeypatch):
    """Test handling when no work items exist."""
    monkeypatch.chdir(tmp_path)
    tracking_dir = tmp_path / ".session" / "tracking"
    tracking_dir.mkdir(parents=True)

    data = {"metadata": {}, "milestones": {}, "work_items": {}}

    work_items_file = tracking_dir / "work_items.json"
    with open(work_items_file, "w") as f:
        json.dump(data, f, indent=2)

    ready = get_ready_work_items(limit=4)
    assert ready == []


def test_get_ready_work_items_no_ready_items(tmp_path, monkeypatch):
    """Test handling when all items are either in_progress or completed."""
    monkeypatch.chdir(tmp_path)
    tracking_dir = tmp_path / ".session" / "tracking"
    tracking_dir.mkdir(parents=True)

    data = {
        "metadata": {},
        "milestones": {},
        "work_items": {
            "feature_a": {
                "type": "feature",
                "title": "Feature A",
                "status": "in_progress",
                "priority": "high",
                "dependencies": [],
            },
            "feature_b": {
                "type": "feature",
                "title": "Feature B",
                "status": "completed",
                "priority": "high",
                "dependencies": [],
            },
        },
    }

    work_items_file = tracking_dir / "work_items.json"
    with open(work_items_file, "w") as f:
        json.dump(data, f, indent=2)

    ready = get_ready_work_items(limit=4)
    assert ready == []


def test_get_ready_work_items_all_blocked(tmp_path, monkeypatch):
    """Test handling when all not_started items are blocked."""
    monkeypatch.chdir(tmp_path)
    tracking_dir = tmp_path / ".session" / "tracking"
    tracking_dir.mkdir(parents=True)

    data = {
        "metadata": {},
        "milestones": {},
        "work_items": {
            "feature_base": {
                "type": "feature",
                "title": "Base feature",
                "status": "in_progress",  # Not completed yet
                "priority": "high",
                "dependencies": [],
            },
            "feature_dependent": {
                "type": "feature",
                "title": "Dependent feature",
                "status": "not_started",
                "priority": "high",
                "dependencies": ["feature_base"],  # Blocked
            },
        },
    }

    work_items_file = tracking_dir / "work_items.json"
    with open(work_items_file, "w") as f:
        json.dump(data, f, indent=2)

    ready = get_ready_work_items(limit=4)
    assert ready == []


def test_get_ready_work_items_missing_file(tmp_path, monkeypatch):
    """Test handling when work_items.json doesn't exist."""
    monkeypatch.chdir(tmp_path)

    ready = get_ready_work_items(limit=4)
    assert ready == []


def test_get_ready_work_items_invalid_json(tmp_path, monkeypatch):
    """Test handling of invalid JSON."""
    monkeypatch.chdir(tmp_path)
    tracking_dir = tmp_path / ".session" / "tracking"
    tracking_dir.mkdir(parents=True)

    work_items_file = tracking_dir / "work_items.json"
    with open(work_items_file, "w") as f:
        f.write("{ invalid json }")

    ready = get_ready_work_items(limit=4)
    assert ready == []


def test_get_ready_work_items_output_format(setup_work_items):
    """Test that output has correct fields."""
    ready = get_ready_work_items(limit=1)

    assert len(ready) == 1
    item = ready[0]

    # Check all required fields are present
    assert "id" in item
    assert "type" in item
    assert "title" in item
    assert "priority" in item

    # Check values are correct
    assert item["id"] == "bug_login"
    assert item["type"] == "bug"
    assert item["title"] == "Fix login redirect"
    assert item["priority"] == "critical"


def test_main_with_custom_limit(setup_work_items):
    """Test main function with custom limit."""
    from sdd.work_items.get_next_recommendations import main

    with patch("sys.argv", ["get_next_recommendations.py", "--limit", "2"]):
        result = main()

    assert result == 0


def test_main_no_ready_items(tmp_path, monkeypatch):
    """Test main function when no ready items exist."""
    from sdd.work_items.get_next_recommendations import main

    monkeypatch.chdir(tmp_path)

    with patch("sys.argv", ["get_next_recommendations.py"]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1  # Should exit with error code
