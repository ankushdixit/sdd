"""Unit tests for work item updater urgent flag functionality.

This module tests the WorkItemUpdater class's handling of urgent flag operations
including auto-clear on completion and manual clearing.
"""

import json

import pytest
from solokit.work_items.repository import WorkItemRepository
from solokit.work_items.updater import WorkItemUpdater
from solokit.work_items.validator import WorkItemValidator


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
def updater(repository):
    """Provide a WorkItemUpdater instance."""
    validator = WorkItemValidator()
    return WorkItemUpdater(repository, validator)


class TestUrgentAutoClear:
    """Tests for automatic clearing of urgent flag on completion."""

    def test_auto_clear_urgent_on_completion(self, repository, updater):
        """Test that urgent flag is auto-cleared when status changes to completed."""
        # Arrange
        repository.add_work_item("bug_urgent", "bug", "Urgent Bug", "high", [], urgent=True)

        # Act
        updater.update("bug_urgent", status="completed")

        # Assert
        data = json.loads(repository.work_items_file.read_text())
        assert data["work_items"]["bug_urgent"]["status"] == "completed"
        assert data["work_items"]["bug_urgent"]["urgent"] is False

    def test_no_auto_clear_on_non_completion_status(self, repository, updater):
        """Test that urgent flag is NOT cleared when changing to non-completed status."""
        # Arrange
        repository.add_work_item("bug_urgent", "bug", "Urgent Bug", "high", [], urgent=True)

        # Act
        updater.update("bug_urgent", status="in_progress")

        # Assert
        data = json.loads(repository.work_items_file.read_text())
        assert data["work_items"]["bug_urgent"]["status"] == "in_progress"
        assert data["work_items"]["bug_urgent"]["urgent"] is True

    def test_auto_clear_only_affects_urgent_items(self, repository, updater):
        """Test that auto-clear only affects items that are marked urgent."""
        # Arrange
        repository.add_work_item("feature_normal", "feature", "Normal Feature", "high", [])

        # Act
        updater.update("feature_normal", status="completed")

        # Assert
        data = json.loads(repository.work_items_file.read_text())
        assert data["work_items"]["feature_normal"]["status"] == "completed"
        assert data["work_items"]["feature_normal"]["urgent"] is False  # Should still be False


class TestManualClearUrgent:
    """Tests for manual clearing of urgent flag."""

    def test_manual_clear_urgent_flag(self, repository, updater):
        """Test manually clearing urgent flag via update."""
        # Arrange
        repository.add_work_item("bug_urgent", "bug", "Urgent Bug", "high", [], urgent=True)

        # Act
        updater.update("bug_urgent", clear_urgent=True)

        # Assert
        data = json.loads(repository.work_items_file.read_text())
        assert data["work_items"]["bug_urgent"]["urgent"] is False

    def test_clear_urgent_on_non_urgent_item(self, repository, updater):
        """Test clearing urgent flag on item that's not urgent (no changes made)."""
        from solokit.core.exceptions import ValidationError

        # Arrange
        repository.add_work_item("feature_normal", "feature", "Normal Feature", "high", [])

        # Act & Assert - Should raise ValidationError since no changes were made
        with pytest.raises(ValidationError, match="No changes to update"):
            updater.update("feature_normal", clear_urgent=True)

    def test_clear_urgent_with_other_updates(self, repository, updater):
        """Test clearing urgent flag combined with other updates."""
        # Arrange
        repository.add_work_item("bug_urgent", "bug", "Urgent Bug", "high", [], urgent=True)

        # Act
        updater.update("bug_urgent", status="in_progress", clear_urgent=True)

        # Assert
        data = json.loads(repository.work_items_file.read_text())
        assert data["work_items"]["bug_urgent"]["status"] == "in_progress"
        assert data["work_items"]["bug_urgent"]["urgent"] is False


class TestUrgentFlagEdgeCases:
    """Tests for edge cases in urgent flag handling."""

    def test_update_priority_preserves_urgent(self, repository, updater):
        """Test that updating priority preserves urgent flag."""
        # Arrange
        repository.add_work_item("bug_urgent", "bug", "Urgent Bug", "high", [], urgent=True)

        # Act
        updater.update("bug_urgent", priority="critical")

        # Assert
        data = json.loads(repository.work_items_file.read_text())
        assert data["work_items"]["bug_urgent"]["priority"] == "critical"
        assert data["work_items"]["bug_urgent"]["urgent"] is True

    def test_add_dependency_preserves_urgent(self, repository, updater):
        """Test that adding dependencies preserves urgent flag."""
        # Arrange
        repository.add_work_item("feature_base", "feature", "Base Feature", "high", [])
        repository.add_work_item("bug_urgent", "bug", "Urgent Bug", "high", [], urgent=True)

        # Act
        updater.update("bug_urgent", add_dependency="feature_base")

        # Assert
        data = json.loads(repository.work_items_file.read_text())
        assert "feature_base" in data["work_items"]["bug_urgent"]["dependencies"]
        assert data["work_items"]["bug_urgent"]["urgent"] is True
