"""Unit tests for milestone_manager module.

This module tests the MilestoneManager class which handles milestone
creation and progress tracking.
"""

import json

import pytest
from solokit.work_items.milestones import MilestoneManager
from solokit.work_items.repository import WorkItemRepository


@pytest.fixture
def repository(tmp_path):
    """Provide a WorkItemRepository instance with temp directory."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    session_dir = project_root / ".session"
    session_dir.mkdir()
    tracking_dir = session_dir / "tracking"
    tracking_dir.mkdir()

    return WorkItemRepository(session_dir)


@pytest.fixture
def repository_with_data(tmp_path):
    """Provide a WorkItemRepository instance with existing data."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    session_dir = project_root / ".session"
    session_dir.mkdir()
    tracking_dir = session_dir / "tracking"
    tracking_dir.mkdir()

    # Create work_items.json with sample data
    work_items_file = tracking_dir / "work_items.json"
    sample_data = {
        "work_items": {
            "feature_foundation": {
                "id": "feature_foundation",
                "title": "Foundation Module",
                "type": "feature",
                "status": "completed",
                "priority": "critical",
                "dependencies": [],
                "milestone": "v1.0",
                "spec_file": ".session/specs/feature_foundation.md",
                "created_at": "2025-01-01T00:00:00",
                "sessions": [],
            },
            "feature_auth": {
                "id": "feature_auth",
                "title": "User Authentication",
                "type": "feature",
                "status": "in_progress",
                "priority": "high",
                "dependencies": ["feature_foundation"],
                "milestone": "v1.0",
                "spec_file": ".session/specs/feature_auth.md",
                "created_at": "2025-01-02T00:00:00",
                "sessions": [{"session_number": 1, "date": "2025-01-03", "duration": "1h"}],
            },
        },
        "metadata": {
            "total_items": 2,
            "completed": 1,
            "in_progress": 1,
        },
        "milestones": {
            "v1.0": {
                "name": "v1.0",
                "title": "Version 1.0 Release",
                "description": "Initial release",
                "target_date": "2025-06-01",
                "status": "in_progress",
                "created_at": "2025-01-01T00:00:00",
            }
        },
    }
    work_items_file.write_text(json.dumps(sample_data, indent=2))

    return WorkItemRepository(session_dir)


@pytest.fixture
def milestone_manager(repository):
    """Provide a MilestoneManager instance."""
    return MilestoneManager(repository)


@pytest.fixture
def milestone_manager_with_data(repository_with_data):
    """Provide a MilestoneManager instance with existing data."""
    return MilestoneManager(repository_with_data)


class TestGetMilestoneProgress:
    """Tests for milestone progress calculation."""

    def test_get_milestone_progress_no_file(self, milestone_manager):
        """Test getting milestone progress when no file exists."""
        # Act
        result = milestone_manager.get_progress("v1.0")

        # Assert
        # When no file exists, repository returns empty dict, so no items for milestone
        assert result["total"] == 0
        assert result["percent"] == 0

    def test_get_milestone_progress_no_items(self, milestone_manager_with_data):
        """Test getting progress for milestone with no items."""
        # Act
        result = milestone_manager_with_data.get_progress("v2.0")

        # Assert
        assert result["total"] == 0
        assert result["percent"] == 0

    def test_get_milestone_progress_with_items(self, milestone_manager_with_data):
        """Test getting progress for milestone with items."""
        # Act
        result = milestone_manager_with_data.get_progress("v1.0")

        # Assert
        assert result["total"] == 2
        assert result["completed"] == 1
        assert result["in_progress"] == 1
        assert result["percent"] == 50
