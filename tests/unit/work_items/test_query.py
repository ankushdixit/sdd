"""Unit tests for work_item_query module.

This module tests the WorkItemQuery class which handles listing, filtering,
sorting, and displaying work items.
"""

import json
from pathlib import Path

import pytest

from sdd.work_items.query import WorkItemQuery
from sdd.work_items.repository import WorkItemRepository


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
            "bug_login_issue": {
                "id": "bug_login_issue",
                "title": "Login Issue",
                "type": "bug",
                "status": "not_started",
                "priority": "high",
                "dependencies": ["feature_auth"],
                "milestone": "",
                "spec_file": ".session/specs/bug_login_issue.md",
                "created_at": "2025-01-03T00:00:00",
                "sessions": [],
            },
        },
        "metadata": {
            "total_items": 3,
            "completed": 1,
            "in_progress": 1,
            "blocked": 0,
            "last_updated": "2025-01-03T00:00:00",
        },
        "milestones": {},
    }
    work_items_file.write_text(json.dumps(sample_data, indent=2))

    return WorkItemRepository(session_dir)


@pytest.fixture
def query(repository_with_data):
    """Provide a WorkItemQuery instance."""
    return WorkItemQuery(repository_with_data)


class TestIsBlocked:
    """Tests for dependency blocking logic."""

    def test_is_blocked_completed_item_not_blocked(self, query):
        """Test that completed items are never blocked."""
        # Arrange
        all_items = query.repository.get_all_work_items()
        item = all_items["feature_foundation"]

        # Act
        result = query._is_blocked(item, all_items)

        # Assert
        assert result is False

    def test_is_blocked_no_dependencies(self, query):
        """Test that items without dependencies are not blocked."""
        # Arrange
        all_items = query.repository.get_all_work_items()
        item = all_items["feature_foundation"]

        # Act
        result = query._is_blocked(item, all_items)

        # Assert
        assert result is False

    def test_is_blocked_incomplete_dependency(self, query):
        """Test that item is blocked when dependency is incomplete."""
        # Arrange
        all_items = query.repository.get_all_work_items()
        item = all_items["bug_login_issue"]

        # Act
        result = query._is_blocked(item, all_items)

        # Assert
        assert result is True

    def test_is_blocked_all_dependencies_complete(self, query):
        """Test that item is not blocked when all dependencies are complete."""
        # Arrange
        # Add new item that depends on completed item
        data = json.loads(query.repository.work_items_file.read_text())
        data["work_items"]["feature_new"] = {
            "id": "feature_new",
            "status": "not_started",
            "dependencies": ["feature_foundation"],
        }
        query.repository.work_items_file.write_text(json.dumps(data))

        all_items = query.repository.get_all_work_items()
        item = all_items["feature_new"]

        # Act
        result = query._is_blocked(item, all_items)

        # Assert
        assert result is False

    def test_is_blocked_missing_dependency(self, query):
        """Test that missing dependency is ignored."""
        # Arrange
        item = {"id": "test", "status": "not_started", "dependencies": ["nonexistent"]}
        all_items = {}

        # Act
        result = query._is_blocked(item, all_items)

        # Assert
        assert result is False


class TestSortItems:
    """Tests for work item sorting."""

    def test_sort_items_by_priority(self, query):
        """Test that items are sorted by priority."""
        # Arrange
        items = {
            "low": {
                "priority": "low",
                "status": "not_started",
                "_blocked": False,
                "created_at": "2025-01-01",
            },
            "critical": {
                "priority": "critical",
                "status": "not_started",
                "_blocked": False,
                "created_at": "2025-01-01",
            },
            "medium": {
                "priority": "medium",
                "status": "not_started",
                "_blocked": False,
                "created_at": "2025-01-01",
            },
        }

        # Act
        result = query._sort_items(items)

        # Assert
        priorities = [item["priority"] for item in result]
        assert priorities == ["critical", "medium", "low"]

    def test_sort_items_ready_before_blocked(self, query):
        """Test that ready items come before blocked items."""
        # Arrange
        items = {
            "blocked": {
                "priority": "high",
                "status": "not_started",
                "_blocked": True,
                "created_at": "2025-01-01",
            },
            "ready": {
                "priority": "high",
                "status": "not_started",
                "_blocked": False,
                "created_at": "2025-01-02",
            },
        }

        # Act
        result = query._sort_items(items)

        # Assert
        assert result[0]["_blocked"] is False
        assert result[1]["_blocked"] is True

    def test_sort_items_in_progress_first(self, query):
        """Test that in_progress items come first."""
        # Arrange
        items = {
            "not_started": {
                "priority": "high",
                "status": "not_started",
                "_blocked": False,
                "created_at": "2025-01-01",
            },
            "in_progress": {
                "priority": "high",
                "status": "in_progress",
                "_blocked": False,
                "created_at": "2025-01-02",
            },
        }

        # Act
        result = query._sort_items(items)

        # Assert
        assert result[0]["status"] == "in_progress"


class TestGetStatusIcon:
    """Tests for status icon helper."""

    def test_get_status_icon_completed(self, query):
        """Test status icon for completed item."""
        # Act
        icon = query._get_status_icon({"status": "completed"})

        # Assert
        assert icon == "[✓]"

    def test_get_status_icon_in_progress(self, query):
        """Test status icon for in_progress item."""
        # Act
        icon = query._get_status_icon({"status": "in_progress"})

        # Assert
        assert icon == "[>>]"

    def test_get_status_icon_not_started(self, query):
        """Test status icon for not_started item."""
        # Act
        icon = query._get_status_icon({"status": "not_started"})

        # Assert
        assert icon == "[  ]"
