"""Unit tests for work item scheduler module.

This module tests the WorkItemScheduler class which handles work item
prioritization and next item selection, including urgent item prioritization.
"""

import pytest

from solokit.work_items.repository import WorkItemRepository
from solokit.work_items.scheduler import WorkItemScheduler


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
def scheduler(repository):
    """Provide a WorkItemScheduler instance."""
    return WorkItemScheduler(repository)


class TestUrgentPrioritization:
    """Tests for urgent item prioritization in scheduler."""

    def test_get_next_returns_urgent_item_first(self, repository, scheduler):
        """Test that urgent item is returned first, ignoring priority."""
        # Arrange
        repository.add_work_item("bug_urgent", "bug", "Urgent Bug", "low", [], urgent=True)
        repository.add_work_item("feature_critical", "feature", "Critical Feature", "critical", [])

        # Act
        next_item = scheduler.get_next()

        # Assert
        assert next_item is not None
        assert next_item["id"] == "bug_urgent"
        assert next_item["urgent"] is True

    def test_get_next_ignores_dependencies_for_urgent(self, repository, scheduler):
        """Test that urgent item is returned even with unmet dependencies."""
        # Arrange
        repository.add_work_item("feature_foundation", "feature", "Foundation", "high", [])
        repository.add_work_item(
            "bug_urgent", "bug", "Urgent Bug", "high", ["feature_foundation"], urgent=True
        )

        # Act
        next_item = scheduler.get_next()

        # Assert
        assert next_item is not None
        assert next_item["id"] == "bug_urgent"

    def test_get_next_returns_normal_priority_when_no_urgent(self, repository, scheduler):
        """Test that normal prioritization works when no urgent items exist."""
        # Arrange
        repository.add_work_item("feature_low", "feature", "Low Priority", "low", [])
        repository.add_work_item("bug_critical", "bug", "Critical Bug", "critical", [])

        # Act
        next_item = scheduler.get_next()

        # Assert
        assert next_item is not None
        assert next_item["id"] == "bug_critical"  # Critical priority comes first

    def test_get_next_skips_in_progress_urgent(self, repository, scheduler):
        """Test that in-progress urgent items are skipped."""
        # Arrange
        repository.add_work_item("bug_urgent", "bug", "Urgent Bug", "high", [], urgent=True)
        repository.update_work_item("bug_urgent", {"status": "in_progress"})
        repository.add_work_item("feature_normal", "feature", "Normal Feature", "high", [])

        # Act
        next_item = scheduler.get_next()

        # Assert
        assert next_item is not None
        assert next_item["id"] == "feature_normal"

    def test_get_next_skips_completed_urgent(self, repository, scheduler):
        """Test that completed urgent items are skipped."""
        # Arrange
        repository.add_work_item("bug_urgent", "bug", "Urgent Bug", "high", [], urgent=True)
        repository.update_work_item("bug_urgent", {"status": "completed"})
        repository.add_work_item("feature_normal", "feature", "Normal Feature", "high", [])

        # Act
        next_item = scheduler.get_next()

        # Assert
        assert next_item is not None
        assert next_item["id"] == "feature_normal"

    def test_get_next_returns_none_when_only_urgent_in_progress(self, repository, scheduler):
        """Test that None is returned when only urgent item is in progress."""
        # Arrange
        repository.add_work_item("bug_urgent", "bug", "Urgent Bug", "high", [], urgent=True)
        repository.update_work_item("bug_urgent", {"status": "in_progress"})

        # Act
        next_item = scheduler.get_next()

        # Assert
        assert next_item is None

    def test_get_next_with_multiple_urgent_items(self, repository, scheduler):
        """Test behavior with multiple urgent items (should only have one in practice)."""
        # Arrange - This shouldn't happen in practice but test the behavior
        repository.add_work_item("bug_urgent_1", "bug", "Urgent Bug 1", "low", [], urgent=True)
        repository.add_work_item("bug_urgent_2", "bug", "Urgent Bug 2", "high", [], urgent=True)

        # Act
        next_item = scheduler.get_next()

        # Assert - Should return one of the urgent items
        assert next_item is not None
        assert next_item["urgent"] is True
