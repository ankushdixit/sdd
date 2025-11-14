"""Integration tests for urgent flag end-to-end workflow.

This module tests the complete workflow of urgent flag operations including:
- Creating urgent work items with confirmation prompts
- Prioritization by work-next
- Auto-clearing on completion
- Auto-clearing on session completion via sk end
- Manual clearing via work-update
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from solokit.session.complete import main as session_complete_main
from solokit.work_items.manager import WorkItemManager
from solokit.work_items.repository import WorkItemRepository


@pytest.fixture
def test_project(tmp_path):
    """Create a test project with .session directory structure."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()

    session_dir = project_root / ".session"
    session_dir.mkdir()

    tracking_dir = session_dir / "tracking"
    tracking_dir.mkdir()

    specs_dir = session_dir / "specs"
    specs_dir.mkdir()

    # Initialize work_items.json
    work_items_file = tracking_dir / "work_items.json"
    work_items_file.write_text(
        json.dumps({"work_items": {}, "milestones": {}, "metadata": {}}, indent=2)
    )

    return project_root


@pytest.fixture
def manager(test_project):
    """Provide a WorkItemManager instance."""
    return WorkItemManager(test_project)


class TestUrgentWorkflowEndToEnd:
    """Integration tests for complete urgent workflow."""

    def test_create_and_retrieve_urgent_work_item(self, manager):
        """Test creating an urgent work item and retrieving it."""
        # Act - Create urgent work item
        work_id = manager.creator.create_from_args(
            work_type="bug",
            title="Critical Production Bug",
            priority="critical",
            dependencies="",
            urgent=True,
        )

        # Assert - Verify it's marked urgent in repository
        urgent_item = manager.repository.get_urgent_work_item()
        assert urgent_item is not None
        assert urgent_item["id"] == work_id
        assert urgent_item["urgent"] is True

    def test_work_next_prioritizes_urgent_over_critical(self, manager):
        """Test that work-next returns urgent item before critical non-urgent items."""
        # Arrange - Create critical non-urgent and low urgent items
        manager.creator.create_from_args("bug", "Critical Bug", "critical", "", urgent=False)
        urgent_id = manager.creator.create_from_args(
            "feature", "Low Priority Urgent", "low", "", urgent=True
        )

        # Act - Get next work item
        next_item = manager.scheduler.get_next()

        # Assert - Urgent item is returned despite lower priority
        assert next_item is not None
        assert next_item["id"] == urgent_id
        assert next_item["urgent"] is True
        assert next_item["priority"] == "low"

    def test_auto_clear_urgent_on_completion(self, manager):
        """Test that urgent flag is automatically cleared when work item is completed."""
        # Arrange - Create urgent work item
        work_id = manager.creator.create_from_args("bug", "Urgent Bug Fix", "high", "", urgent=True)

        # Act - Mark as completed
        manager.updater.update(work_id, status="completed")

        # Assert - Urgent flag should be cleared
        urgent_item = manager.repository.get_urgent_work_item()
        assert urgent_item is None  # No urgent item should exist

        item = manager.repository.get_work_item(work_id)
        assert item["status"] == "completed"
        assert item["urgent"] is False

    def test_auto_clear_urgent_on_session_completion(self, test_project, monkeypatch):
        """Test that urgent flag is automatically cleared when session is completed via sk end."""
        # Arrange - Setup project directory
        monkeypatch.chdir(test_project)

        session_dir = test_project / ".session"
        tracking_dir = session_dir / "tracking"
        history_dir = session_dir / "history"
        history_dir.mkdir(parents=True, exist_ok=True)

        # Create urgent work item
        work_id = "bug_urgent_session_test"
        work_items_data = {
            "work_items": {
                work_id: {
                    "id": work_id,
                    "type": "bug",
                    "title": "Urgent Bug for Session Test",
                    "status": "in_progress",
                    "priority": "critical",
                    "urgent": True,  # Mark as urgent
                    "dependencies": [],
                }
            },
            "milestones": {},
            "metadata": {"total_items": 1, "completed": 0, "in_progress": 1, "blocked": 0},
        }
        work_items_file = tracking_dir / "work_items.json"
        work_items_file.write_text(json.dumps(work_items_data, indent=2))

        # Create session status
        status_data = {
            "current_session": 1,
            "current_work_item": work_id,
            "status": "active",
        }
        status_file = tracking_dir / "status_update.json"
        status_file.write_text(json.dumps(status_data, indent=2))

        # Create a minimal spec file
        specs_dir = session_dir / "specs"
        specs_dir.mkdir(exist_ok=True)
        spec_file = specs_dir / f"{work_id}.md"
        spec_file.write_text(
            """# Bug: Urgent Bug for Session Test

## Description
Test urgent flag clearing on session completion

## Acceptance Criteria
- [ ] Test passes
"""
        )

        # Mock external dependencies
        with patch("solokit.session.complete.check_uncommitted_changes", return_value=True):
            with patch("solokit.session.complete.run_quality_gates") as mock_gates:
                mock_gates.return_value = ({"tests": {"status": "passed"}}, True, [])
                with patch("solokit.session.complete.extract_learnings_from_session", return_value=[]):
                    with patch("solokit.session.complete.generate_commit_message", return_value="Test commit"):
                        with patch("solokit.session.complete.complete_git_workflow") as mock_git:
                            mock_git.return_value = {"success": True, "message": "Success"}
                            with patch("solokit.session.complete.record_session_commits"):
                                with patch("solokit.session.complete.auto_extract_learnings", return_value=0):
                                    # Patch update_all_tracking to avoid subprocess calls
                                    with patch("solokit.session.complete.update_all_tracking"):
                                        with patch("solokit.session.complete.trigger_curation_if_needed"):
                                            # Act - Complete session with --complete flag
                                            with patch("sys.argv", ["session_complete.py", "--complete"]):
                                                result = session_complete_main()

        # Assert - Session completed successfully
        assert result == 0

        # Assert - Urgent flag should be cleared
        repository = WorkItemRepository(session_dir)
        urgent_item = repository.get_urgent_work_item()
        assert urgent_item is None, "Urgent flag should be cleared after session completion"

        item = repository.get_work_item(work_id)
        assert item["status"] == "completed", "Work item should be marked as completed"
        assert item["urgent"] is False, "Urgent flag should be False after completion"

    def test_manual_clear_urgent_flag(self, manager):
        """Test manually clearing urgent flag via work-update."""
        # Arrange - Create urgent work item
        work_id = manager.creator.create_from_args(
            "feature", "Urgent Feature", "high", "", urgent=True
        )

        # Act - Clear urgent flag manually
        manager.updater.update(work_id, clear_urgent=True)

        # Assert - Urgent flag should be cleared
        urgent_item = manager.repository.get_urgent_work_item()
        assert urgent_item is None

        item = manager.repository.get_work_item(work_id)
        assert item["urgent"] is False
        assert item["status"] == "not_started"  # Status unchanged

    def test_urgent_ignores_dependencies(self, manager):
        """Test that urgent items are returned by work-next even with unmet dependencies."""
        # Arrange - Create dependency and urgent item that depends on it
        dep_id = manager.creator.create_from_args("feature", "Base Feature", "high", "")

        urgent_id = manager.creator.create_from_args(
            "bug", "Urgent Dependent Bug", "high", dep_id, urgent=True
        )

        # Act - Get next work item
        next_item = manager.scheduler.get_next()

        # Assert - Urgent item is returned despite unmet dependency
        assert next_item is not None
        assert next_item["id"] == urgent_id
        assert dep_id in next_item.get("dependencies", [])

    def test_only_one_urgent_item_at_a_time(self, test_project):
        """Test that only one urgent item exists at a time in the system."""
        repository = WorkItemRepository(test_project / ".session")

        # Arrange - Create first urgent item
        repository.add_work_item("bug_urgent_1", "bug", "First Urgent", "high", [], urgent=True)

        # Act - Create second urgent item (should clear first)
        repository.add_work_item("bug_urgent_2", "bug", "Second Urgent", "high", [], urgent=False)
        repository.set_urgent_flag("bug_urgent_2", clear_others=True)

        # Assert - Only second item should be urgent
        urgent_item = repository.get_urgent_work_item()
        assert urgent_item is not None
        assert urgent_item["id"] == "bug_urgent_2"

        # Verify first item is no longer urgent
        first_item = repository.get_work_item("bug_urgent_1")
        assert first_item["urgent"] is False

    def test_work_list_shows_urgent_indicator(self, manager):
        """Test that work-list displays urgent items with indicator."""
        # Arrange - Create urgent and normal items
        manager.creator.create_from_args("bug", "Normal Bug", "high", "")
        manager.creator.create_from_args("feature", "Urgent Feature", "low", "", urgent=True)

        # Act - Get work item list
        result = manager.query.list_items()

        # Assert - Verify urgent item is in the list
        items = result["items"]
        urgent_items = [item for item in items if item.get("urgent", False)]
        assert len(urgent_items) == 1
        assert urgent_items[0]["title"] == "Urgent Feature"

    def test_urgent_workflow_with_normal_priority_ordering(self, manager):
        """Test complete workflow: urgent overrides priority, then normal ordering resumes."""
        # Arrange - Create items in different priorities
        manager.creator.create_from_args("feature", "Low Priority", "low", "")
        manager.creator.create_from_args("feature", "High Priority", "high", "")
        urgent_id = manager.creator.create_from_args(
            "bug", "Medium Urgent", "medium", "", urgent=True
        )

        # Act & Assert Step 1 - Urgent is returned first
        next_item = manager.scheduler.get_next()
        assert next_item["id"] == urgent_id

        # Complete urgent item
        manager.updater.update(urgent_id, status="completed")

        # Act & Assert Step 2 - Now high priority is returned (normal ordering)
        next_item = manager.scheduler.get_next()
        assert next_item["priority"] == "high"

    def test_backward_compatibility_with_old_work_items(self, test_project):
        """Test that old work items without urgent field are handled correctly."""
        # Arrange - Create work item manually without urgent field
        repository = WorkItemRepository(test_project / ".session")
        work_items_file = repository.work_items_file

        data = {
            "work_items": {
                "old_feature": {
                    "id": "old_feature",
                    "type": "feature",
                    "title": "Old Feature",
                    "status": "not_started",
                    "priority": "high",
                    "dependencies": [],
                }
            },
            "milestones": {},
            "metadata": {},
        }
        work_items_file.write_text(json.dumps(data, indent=2))

        # Act - Get urgent item (should return None)
        urgent = repository.get_urgent_work_item()

        # Assert
        assert urgent is None

        # Verify work item can still be retrieved
        item = repository.get_work_item("old_feature")
        assert item is not None
        assert item.get("urgent", False) is False


class TestUrgentEdgeCases:
    """Integration tests for edge cases in urgent workflow."""

    def test_multiple_status_changes_preserve_urgent_until_completed(self, manager):
        """Test that urgent flag persists through status changes until completion."""
        # Arrange - Create urgent item
        work_id = manager.creator.create_from_args("bug", "Urgent Bug", "high", "", urgent=True)

        # Act - Change status to in_progress
        manager.updater.update(work_id, status="in_progress")

        # Assert - Still urgent
        urgent_item = manager.repository.get_urgent_work_item()
        assert urgent_item is not None
        assert urgent_item["id"] == work_id

        # Act - Change status to blocked
        manager.updater.update(work_id, status="blocked")

        # Assert - Still urgent
        urgent_item = manager.repository.get_urgent_work_item()
        assert urgent_item is not None

        # Act - Change to completed
        manager.updater.update(work_id, status="completed")

        # Assert - No longer urgent
        urgent_item = manager.repository.get_urgent_work_item()
        assert urgent_item is None

    def test_urgent_with_multiple_dependencies(self, manager):
        """Test urgent item with multiple unmet dependencies is still prioritized."""
        # Arrange - Create multiple dependencies
        dep1 = manager.creator.create_from_args("feature", "Dep 1", "high", "")
        dep2 = manager.creator.create_from_args("feature", "Dep 2", "high", "")

        urgent_id = manager.creator.create_from_args(
            "bug", "Urgent with Deps", "high", f"{dep1},{dep2}", urgent=True
        )

        # Act - Get next work item
        next_item = manager.scheduler.get_next()

        # Assert - Urgent item is returned
        assert next_item["id"] == urgent_id
        assert len(next_item.get("dependencies", [])) == 2
