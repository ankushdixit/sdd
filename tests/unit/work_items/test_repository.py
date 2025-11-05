"""Unit tests for work_item_repository module.

This module tests the WorkItemRepository class which handles data access
and persistence for work items and milestones.
"""

import json
from pathlib import Path

import pytest

from sdd.work_items.repository import WorkItemRepository


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


class TestWorkItemExists:
    """Tests for checking if work item exists."""

    def test_work_item_exists_when_file_missing(self, repository):
        """Test that work_item_exists returns False when work_items.json doesn't exist."""
        # Act
        result = repository.work_item_exists("feature_test")

        # Assert
        assert result is False

    def test_work_item_exists_when_item_present(self, repository_with_data):
        """Test that work_item_exists returns True for existing item."""
        # Act
        result = repository_with_data.work_item_exists("feature_foundation")

        # Assert
        assert result is True

    def test_work_item_exists_when_item_not_present(self, repository_with_data):
        """Test that work_item_exists returns False for non-existent item."""
        # Act
        result = repository_with_data.work_item_exists("feature_nonexistent")

        # Assert
        assert result is False


class TestAddWorkItem:
    """Tests for adding work items to tracking file."""

    def test_add_work_item_creates_new_file(self, repository):
        """Test that add_work_item creates work_items.json if it doesn't exist."""
        # Act
        repository.add_work_item(
            "feature_test", "feature", "Test Feature", "high", [], ".session/specs/feature_test.md"
        )

        # Assert
        assert repository.work_items_file.exists()
        data = json.loads(repository.work_items_file.read_text())
        assert "feature_test" in data["work_items"]

    def test_add_work_item_adds_work_item_fields(self, repository):
        """Test that all work item fields are added correctly."""
        # Act
        repository.add_work_item(
            "feature_test",
            "feature",
            "Test Feature",
            "critical",
            ["dep1", "dep2"],
            ".session/specs/feature_test.md",
        )

        # Assert
        data = json.loads(repository.work_items_file.read_text())
        item = data["work_items"]["feature_test"]
        assert item["id"] == "feature_test"
        assert item["type"] == "feature"
        assert item["title"] == "Test Feature"
        assert item["status"] == "not_started"
        assert item["priority"] == "critical"
        assert item["dependencies"] == ["dep1", "dep2"]
        assert item["milestone"] == ""
        assert item["spec_file"] == ".session/specs/feature_test.md"
        assert "created_at" in item
        assert item["sessions"] == []

    def test_add_work_item_updates_metadata_counters(self, repository_with_data):
        """Test that metadata counters are updated correctly."""
        # Arrange
        initial_data = json.loads(repository_with_data.work_items_file.read_text())
        initial_count = initial_data["metadata"]["total_items"]

        # Act
        repository_with_data.add_work_item("feature_new", "feature", "New Feature", "high", [], "")

        # Assert
        data = json.loads(repository_with_data.work_items_file.read_text())
        assert data["metadata"]["total_items"] == initial_count + 1
        assert "last_updated" in data["metadata"]

    def test_add_work_item_preserves_existing_items(self, repository_with_data):
        """Test that adding new work item preserves existing items."""
        # Arrange
        initial_data = json.loads(repository_with_data.work_items_file.read_text())
        initial_ids = set(initial_data["work_items"].keys())

        # Act
        repository_with_data.add_work_item("feature_new", "feature", "New Feature", "high", [], "")

        # Assert
        data = json.loads(repository_with_data.work_items_file.read_text())
        current_ids = set(data["work_items"].keys())
        assert initial_ids.issubset(current_ids)
        assert "feature_new" in current_ids


class TestGetWorkItem:
    """Tests for retrieving work items."""

    def test_get_work_item_existing(self, repository_with_data):
        """Test retrieving an existing work item."""
        # Act
        item = repository_with_data.get_work_item("feature_foundation")

        # Assert
        assert item is not None
        assert item["id"] == "feature_foundation"
        assert item["title"] == "Foundation Module"

    def test_get_work_item_nonexistent(self, repository_with_data):
        """Test retrieving a non-existent work item."""
        # Act
        item = repository_with_data.get_work_item("nonexistent")

        # Assert
        assert item is None

    def test_get_all_work_items(self, repository_with_data):
        """Test retrieving all work items."""
        # Act
        items = repository_with_data.get_all_work_items()

        # Assert
        assert len(items) == 3
        assert "feature_foundation" in items
        assert "feature_auth" in items
        assert "bug_login_issue" in items


class TestUpdateWorkItem:
    """Tests for updating work items."""

    def test_update_work_item_single_field(self, repository_with_data):
        """Test updating a single field."""
        # Act
        repository_with_data.update_work_item("feature_auth", {"status": "completed"})

        # Assert
        data = json.loads(repository_with_data.work_items_file.read_text())
        assert data["work_items"]["feature_auth"]["status"] == "completed"

    def test_update_work_item_multiple_fields(self, repository_with_data):
        """Test updating multiple fields."""
        # Act
        repository_with_data.update_work_item(
            "feature_auth", {"status": "completed", "priority": "critical"}
        )

        # Assert
        data = json.loads(repository_with_data.work_items_file.read_text())
        assert data["work_items"]["feature_auth"]["status"] == "completed"
        assert data["work_items"]["feature_auth"]["priority"] == "critical"

    def test_update_work_item_add_dependency(self, repository_with_data):
        """Test adding a dependency."""
        # Act
        repository_with_data.update_work_item(
            "feature_foundation", {"add_dependency": "feature_auth"}
        )

        # Assert
        data = json.loads(repository_with_data.work_items_file.read_text())
        assert "feature_auth" in data["work_items"]["feature_foundation"]["dependencies"]

    def test_update_work_item_remove_dependency(self, repository_with_data):
        """Test removing a dependency."""
        # Act
        repository_with_data.update_work_item(
            "feature_auth", {"remove_dependency": "feature_foundation"}
        )

        # Assert
        data = json.loads(repository_with_data.work_items_file.read_text())
        assert "feature_foundation" not in data["work_items"]["feature_auth"]["dependencies"]


class TestMilestones:
    """Tests for milestone operations."""

    def test_milestone_exists(self, repository_with_data):
        """Test checking if milestone exists."""
        # Act & Assert
        assert repository_with_data.milestone_exists("v1.0") is True
        assert repository_with_data.milestone_exists("v2.0") is False

    def test_get_milestone(self, repository_with_data):
        """Test retrieving a milestone."""
        # Act
        milestone = repository_with_data.get_milestone("v1.0")

        # Assert
        assert milestone is not None
        assert milestone["name"] == "v1.0"
        assert milestone["title"] == "Version 1.0 Release"

    def test_get_all_milestones(self, repository_with_data):
        """Test retrieving all milestones."""
        # Act
        milestones = repository_with_data.get_all_milestones()

        # Assert
        assert len(milestones) == 1
        assert "v1.0" in milestones

    def test_add_milestone(self, repository):
        """Test adding a new milestone."""
        # Act
        repository.add_milestone("v1.0", "Version 1.0", "First release", "2025-06-01")

        # Assert
        data = json.loads(repository.work_items_file.read_text())
        assert "v1.0" in data["milestones"]
        assert data["milestones"]["v1.0"]["title"] == "Version 1.0"
        assert data["milestones"]["v1.0"]["target_date"] == "2025-06-01"
