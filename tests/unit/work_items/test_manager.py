"""Unit tests for work_item_manager module.

This module tests the WorkItemManager class which handles CRUD operations
for work items, dependencies, milestones, and related functionality.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from solokit.core.exceptions import (
    ErrorCode,
    FileOperationError,
    SpecValidationError,
    ValidationError,
    WorkItemAlreadyExistsError,
    WorkItemNotFoundError,
)
from solokit.work_items.manager import WorkItemManager


@pytest.fixture
def sample_work_items_data():
    """Provide sample work items data structure for testing."""
    return {
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


@pytest.fixture
def work_item_manager(tmp_path):
    """Provide a WorkItemManager instance with temp directory."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    session_dir = project_root / ".session"
    session_dir.mkdir()
    tracking_dir = session_dir / "tracking"
    tracking_dir.mkdir()
    specs_dir = session_dir / "specs"
    specs_dir.mkdir()

    return WorkItemManager(project_root)


@pytest.fixture
def work_item_manager_with_data(tmp_path, sample_work_items_data):
    """Provide a WorkItemManager instance with existing data."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    session_dir = project_root / ".session"
    session_dir.mkdir()
    tracking_dir = session_dir / "tracking"
    tracking_dir.mkdir()
    specs_dir = session_dir / "specs"
    specs_dir.mkdir()

    # Create work_items.json
    work_items_file = tracking_dir / "work_items.json"
    work_items_file.write_text(json.dumps(sample_work_items_data, indent=2))

    return WorkItemManager(project_root)


@pytest.fixture
def feature_template():
    """Provide a sample feature template."""
    return """# Feature: [Feature Name]

## Description
[Describe the feature]

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3
"""


@pytest.fixture
def bug_template():
    """Provide a sample bug template."""
    return """# Bug: [Bug Title]

## Problem
[Describe the bug]

## Expected Behavior
[What should happen]

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3
"""


class TestWorkItemManagerInit:
    """Tests for WorkItemManager initialization."""

    def test_init_with_project_root(self, tmp_path):
        """Test that WorkItemManager initializes with provided project root."""
        # Arrange
        project_root = tmp_path / "test_project"
        project_root.mkdir()

        # Act
        manager = WorkItemManager(project_root)

        # Assert
        assert manager.project_root == project_root
        assert manager.session_dir == project_root / ".session"
        assert manager.work_items_file == project_root / ".session" / "tracking" / "work_items.json"
        assert manager.specs_dir == project_root / ".session" / "specs"

    def test_init_without_project_root_uses_cwd(self):
        """Test that WorkItemManager uses current working directory when no root provided."""
        # Act
        manager = WorkItemManager()

        # Assert
        assert manager.project_root == Path.cwd()


# TestGenerateId moved to test_creator.py
# Tests for _generate_id are now in test_creator.py since it's a private method of WorkItemCreator


# TestWorkItemExists moved to test_repository.py
# Tests for work_item_exists are now in test_repository.py since it's a method of WorkItemRepository


# TestCreateSpecFile moved to test_creator.py
# Tests for _create_spec_file are now in test_creator.py since it's a private method of WorkItemCreator


# TestAddToTracking moved to test_repository.py
# Tests for add_work_item are now in test_repository.py since it's a method of WorkItemRepository


class TestCreateWorkItemFromArgs:
    """Tests for non-interactive work item creation."""

    def test_create_work_item_from_args_basic(self, work_item_manager, tmp_path):
        """Test creating work item with command-line arguments."""
        # Arrange
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        template_file = templates_dir / "feature_spec.md"
        template_file.write_text("# Feature: [Feature Name]")
        work_item_manager.templates_dir = templates_dir

        # Act
        result = work_item_manager.create_work_item_from_args("feature", "Test Feature", "high", "")

        # Assert
        assert result == "feature_test_feature"
        assert work_item_manager.work_items_file.exists()

    def test_create_work_item_from_args_invalid_type(self, work_item_manager):
        """Test that invalid work item type is rejected."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            work_item_manager.create_work_item_from_args("invalid_type", "Test Item", "high", "")

        assert "Invalid work item type" in str(exc_info.value)
        assert exc_info.value.code == ErrorCode.INVALID_WORK_ITEM_TYPE

    def test_create_work_item_from_args_invalid_priority(self, work_item_manager, tmp_path):
        """Test that invalid priority defaults to 'high'."""
        # Arrange
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        template_file = templates_dir / "feature_spec.md"
        template_file.write_text("# Feature: [Feature Name]")
        work_item_manager.templates_dir = templates_dir

        # Act
        result = work_item_manager.create_work_item_from_args(
            "feature", "Test Feature", "invalid_priority", ""
        )

        # Assert
        assert result is not None
        data = json.loads(work_item_manager.work_items_file.read_text())
        assert data["work_items"][result]["priority"] == "high"

    def test_create_work_item_from_args_with_dependencies(
        self, work_item_manager_with_data, tmp_path
    ):
        """Test creating work item with dependencies."""
        # Arrange
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        template_file = templates_dir / "feature_spec.md"
        template_file.write_text("# Feature: [Feature Name]")
        work_item_manager_with_data.templates_dir = templates_dir

        # Act
        result = work_item_manager_with_data.create_work_item_from_args(
            "feature", "New Feature", "high", "feature_foundation, feature_auth"
        )

        # Assert
        assert result is not None
        data = json.loads(work_item_manager_with_data.work_items_file.read_text())
        assert "feature_foundation" in data["work_items"][result]["dependencies"]
        assert "feature_auth" in data["work_items"][result]["dependencies"]

    def test_create_work_item_from_args_duplicate_id(self, work_item_manager_with_data, tmp_path):
        """Test that duplicate work item ID is rejected."""
        # Arrange
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        template_file = templates_dir / "feature_spec.md"
        template_file.write_text("# Feature: [Feature Name]")
        work_item_manager_with_data.templates_dir = templates_dir

        # Act & Assert
        with pytest.raises(WorkItemAlreadyExistsError) as exc_info:
            work_item_manager_with_data.create_work_item_from_args(
                "feature",
                "Foundation",  # Will generate same ID as existing item
                "high",
                "",
            )

        assert "feature_foundation" in str(exc_info.value)
        assert exc_info.value.code == ErrorCode.WORK_ITEM_ALREADY_EXISTS

    def test_create_work_item_from_args_nonexistent_dependency(
        self, work_item_manager_with_data, tmp_path
    ):
        """Test that nonexistent dependency is still accepted (warning only)."""
        # Arrange
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        template_file = templates_dir / "feature_spec.md"
        template_file.write_text("# Feature: [Feature Name]")
        work_item_manager_with_data.templates_dir = templates_dir

        # Act
        result = work_item_manager_with_data.create_work_item_from_args(
            "feature", "New Feature", "high", "nonexistent_dep"
        )

        # Assert - work item should be created despite nonexistent dependency
        assert result is not None
        data = json.loads(work_item_manager_with_data.work_items_file.read_text())
        assert "nonexistent_dep" in data["work_items"][result]["dependencies"]


# Interactive work item creation tests removed - interactive mode has been removed
# Work items are now created via Claude Code's AskUserQuestion tool in slash commands
# See .claude/commands/work-new.md for the new interactive workflow


class TestListWorkItems:
    """Tests for listing work items."""

    def test_list_work_items_no_file(self, work_item_manager, capsys):
        """Test list_work_items when no work items file exists."""
        # Act
        result = work_item_manager.list_work_items()

        # Assert
        assert result["count"] == 0
        assert result["items"] == []
        captured = capsys.readouterr()
        assert "No work items found" in captured.out

    def test_list_work_items_all(self, work_item_manager_with_data):
        """Test listing all work items without filters."""
        # Act
        result = work_item_manager_with_data.list_work_items()

        # Assert
        assert result["count"] == 3
        assert len(result["items"]) == 3

    def test_list_work_items_filter_by_status(self, work_item_manager_with_data):
        """Test filtering work items by status."""
        # Act
        result = work_item_manager_with_data.list_work_items(status_filter="completed")

        # Assert
        assert result["count"] == 1
        assert result["items"][0]["id"] == "feature_foundation"

    def test_list_work_items_filter_by_type(self, work_item_manager_with_data):
        """Test filtering work items by type."""
        # Act
        result = work_item_manager_with_data.list_work_items(type_filter="bug")

        # Assert
        assert result["count"] == 1
        assert result["items"][0]["id"] == "bug_login_issue"

    def test_list_work_items_filter_by_milestone(self, work_item_manager_with_data):
        """Test filtering work items by milestone."""
        # Act
        result = work_item_manager_with_data.list_work_items(milestone_filter="v1.0")

        # Assert
        assert result["count"] == 2
        milestone_ids = [item["id"] for item in result["items"]]
        assert "feature_foundation" in milestone_ids
        assert "feature_auth" in milestone_ids

    def test_list_work_items_adds_blocked_flag(self, work_item_manager_with_data):
        """Test that _blocked flag is added to items."""
        # Act
        result = work_item_manager_with_data.list_work_items()

        # Assert
        bug_item = next(item for item in result["items"] if item["id"] == "bug_login_issue")
        assert "_blocked" in bug_item
        assert bug_item["_blocked"] is True  # Blocked because feature_auth is in_progress

    def test_list_work_items_adds_ready_flag(self, work_item_manager_with_data):
        """Test that _ready flag is added to items."""
        # Act
        result = work_item_manager_with_data.list_work_items()

        # Assert
        foundation = next(item for item in result["items"] if item["id"] == "feature_foundation")
        assert "_ready" in foundation


# TestIsBlocked moved to test_query.py
# Tests for _is_blocked are now in test_query.py since it's a private method of WorkItemQuery


# TestSortItems moved to test_query.py
# Tests for _sort_items are now in test_query.py since it's a private method of WorkItemQuery


class TestShowWorkItem:
    """Tests for displaying work item details."""

    def test_show_work_item_not_found(self, work_item_manager_with_data):
        """Test showing work item that doesn't exist."""
        # Act & Assert
        with pytest.raises(WorkItemNotFoundError) as exc_info:
            work_item_manager_with_data.show_work_item("nonexistent")

        assert "nonexistent" in str(exc_info.value)
        assert exc_info.value.code == ErrorCode.WORK_ITEM_NOT_FOUND

    def test_show_work_item_no_file(self, work_item_manager):
        """Test showing work item when no work items file exists."""
        # Act & Assert
        with pytest.raises(FileOperationError) as exc_info:
            work_item_manager.show_work_item("test")

        assert "No work items found" in str(exc_info.value)
        assert exc_info.value.code == ErrorCode.FILE_OPERATION_FAILED

    def test_show_work_item_displays_basic_info(self, work_item_manager_with_data, capsys):
        """Test that basic work item information is displayed."""
        # Act
        result = work_item_manager_with_data.show_work_item("feature_foundation")

        # Assert
        assert result is not None
        captured = capsys.readouterr()
        assert "feature_foundation" in captured.out
        assert "feature" in captured.out
        assert "completed" in captured.out
        assert "critical" in captured.out

    def test_show_work_item_displays_dependencies(self, work_item_manager_with_data, capsys):
        """Test that dependencies are displayed."""
        # Act
        result = work_item_manager_with_data.show_work_item("feature_auth")

        # Assert
        assert result is not None
        captured = capsys.readouterr()
        assert "Dependencies" in captured.out
        assert "feature_foundation" in captured.out

    def test_show_work_item_displays_sessions(self, work_item_manager_with_data, capsys):
        """Test that sessions are displayed."""
        # Act
        result = work_item_manager_with_data.show_work_item("feature_auth")

        # Assert
        assert result is not None
        captured = capsys.readouterr()
        assert "Sessions" in captured.out


class TestUpdateWorkItem:
    """Tests for updating work items."""

    def test_update_work_item_no_file(self, work_item_manager):
        """Test updating work item when no file exists."""
        # Act & Assert
        with pytest.raises(FileOperationError) as exc_info:
            work_item_manager.update_work_item("test", status="completed")

        assert "No work items found" in str(exc_info.value)

    def test_update_work_item_not_found(self, work_item_manager_with_data):
        """Test updating non-existent work item."""
        # Act & Assert
        with pytest.raises(WorkItemNotFoundError) as exc_info:
            work_item_manager_with_data.update_work_item("nonexistent", status="completed")

        assert "nonexistent" in str(exc_info.value)

    def test_update_work_item_status(self, work_item_manager_with_data):
        """Test updating work item status."""
        # Act
        work_item_manager_with_data.update_work_item("feature_auth", status="completed")

        # Assert
        data = json.loads(work_item_manager_with_data.work_items_file.read_text())
        assert data["work_items"]["feature_auth"]["status"] == "completed"

    def test_update_work_item_invalid_status(self, work_item_manager_with_data):
        """Test updating with invalid status."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            work_item_manager_with_data.update_work_item("feature_auth", status="invalid")

        assert "Invalid status" in str(exc_info.value)
        assert exc_info.value.code == ErrorCode.INVALID_STATUS

    def test_update_work_item_priority(self, work_item_manager_with_data):
        """Test updating work item priority."""
        # Act
        work_item_manager_with_data.update_work_item("feature_auth", priority="critical")

        # Assert
        data = json.loads(work_item_manager_with_data.work_items_file.read_text())
        assert data["work_items"]["feature_auth"]["priority"] == "critical"

    def test_update_work_item_invalid_priority(self, work_item_manager_with_data):
        """Test updating with invalid priority."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            work_item_manager_with_data.update_work_item("feature_auth", priority="invalid")

        assert "Invalid priority" in str(exc_info.value)
        assert exc_info.value.code == ErrorCode.INVALID_PRIORITY

    def test_update_work_item_milestone(self, work_item_manager_with_data):
        """Test updating work item milestone."""
        # Act
        work_item_manager_with_data.update_work_item("bug_login_issue", milestone="v1.1")

        # Assert
        data = json.loads(work_item_manager_with_data.work_items_file.read_text())
        assert data["work_items"]["bug_login_issue"]["milestone"] == "v1.1"

    def test_update_work_item_add_dependency(self, work_item_manager_with_data):
        """Test adding dependency to work item."""
        # Act
        work_item_manager_with_data.update_work_item(
            "feature_foundation", add_dependency="feature_auth"
        )

        # Assert
        data = json.loads(work_item_manager_with_data.work_items_file.read_text())
        assert "feature_auth" in data["work_items"]["feature_foundation"]["dependencies"]

    def test_update_work_item_add_nonexistent_dependency(self, work_item_manager_with_data):
        """Test adding non-existent dependency."""
        # Act & Assert
        with pytest.raises(WorkItemNotFoundError) as exc_info:
            work_item_manager_with_data.update_work_item(
                "feature_foundation", add_dependency="nonexistent"
            )

        assert "nonexistent" in str(exc_info.value)

    def test_update_work_item_remove_dependency(self, work_item_manager_with_data):
        """Test removing dependency from work item."""
        # Act
        work_item_manager_with_data.update_work_item(
            "feature_auth", remove_dependency="feature_foundation"
        )

        # Assert
        data = json.loads(work_item_manager_with_data.work_items_file.read_text())
        assert "feature_foundation" not in data["work_items"]["feature_auth"]["dependencies"]

    def test_update_work_item_updates_metadata(self, work_item_manager_with_data):
        """Test that metadata counters are updated."""
        # Act
        work_item_manager_with_data.update_work_item("feature_auth", status="completed")

        # Assert
        data = json.loads(work_item_manager_with_data.work_items_file.read_text())
        assert data["metadata"]["completed"] == 2
        assert data["metadata"]["in_progress"] == 0
        assert "last_updated" in data["metadata"]

    def test_update_work_item_records_history(self, work_item_manager_with_data):
        """Test that update history is recorded."""
        # Act
        work_item_manager_with_data.update_work_item("feature_auth", status="completed")

        # Assert
        data = json.loads(work_item_manager_with_data.work_items_file.read_text())
        assert "update_history" in data["work_items"]["feature_auth"]
        assert len(data["work_items"]["feature_auth"]["update_history"]) > 0


# Interactive work item update tests removed - interactive mode has been removed
# Work items are now updated via Claude Code's AskUserQuestion tool in slash commands
# See .claude/commands/work-update.md for the new interactive workflow


class TestGetNextWorkItem:
    """Tests for getting next recommended work item."""

    def test_get_next_work_item_no_file(self, work_item_manager, capsys):
        """Test getting next work item when no file exists."""
        # Act
        result = work_item_manager.get_next_work_item()

        # Assert
        assert result is None
        captured = capsys.readouterr()
        assert "No work items found" in captured.out

    def test_get_next_work_item_none_available(self, work_item_manager_with_data, capsys):
        """Test when no work items are available to start."""
        # Arrange
        # Mark all items as completed or in_progress
        data = json.loads(work_item_manager_with_data.work_items_file.read_text())
        data["work_items"]["bug_login_issue"]["status"] = "completed"
        work_item_manager_with_data.work_items_file.write_text(json.dumps(data))

        # Act
        result = work_item_manager_with_data.get_next_work_item()

        # Assert
        assert result is None
        captured = capsys.readouterr()
        assert "No work items available" in captured.out

    def test_get_next_work_item_all_blocked(self, work_item_manager_with_data, capsys):
        """Test when all not_started items are blocked."""
        # Act (bug_login_issue is blocked by feature_auth which is in_progress)
        result = work_item_manager_with_data.get_next_work_item()

        # Assert
        assert result is None
        captured = capsys.readouterr()
        assert "No work items ready" in captured.out
        assert "Blocked" in captured.out

    def test_get_next_work_item_returns_highest_priority(self, work_item_manager_with_data):
        """Test that highest priority ready item is returned."""
        # Arrange
        # Complete feature_auth so bug_login_issue becomes ready
        data = json.loads(work_item_manager_with_data.work_items_file.read_text())
        data["work_items"]["feature_auth"]["status"] = "completed"
        # Add another not_started item with lower priority
        data["work_items"]["feature_low"] = {
            "id": "feature_low",
            "type": "feature",
            "status": "not_started",
            "priority": "low",
            "dependencies": [],
            "title": "Low Priority Feature",
        }
        work_item_manager_with_data.work_items_file.write_text(json.dumps(data))

        # Act
        result = work_item_manager_with_data.get_next_work_item()

        # Assert
        assert result is not None
        assert result["id"] == "bug_login_issue"  # High priority vs low


# TestValidateIntegrationTest tests - these are testing the public API through manager
# but they need to patch the validator module instead of manager module
class TestValidateIntegrationTest:
    """Tests for integration test validation."""

    @patch("solokit.work_items.validator.spec_parser.parse_spec_file")
    def test_validate_integration_test_missing_spec(self, mock_parse, work_item_manager):
        """Test validation fails when spec file is missing."""
        # Arrange
        mock_parse.side_effect = FileNotFoundError()
        work_item = {"id": "test", "type": "integration_test", "spec_file": "test.md"}

        # Act & Assert
        with pytest.raises(FileOperationError) as exc_info:
            work_item_manager.validate_integration_test(work_item)

        assert "not found" in str(exc_info.value).lower()
        assert exc_info.value.code == ErrorCode.FILE_OPERATION_FAILED

    @patch("solokit.work_items.validator.spec_parser.parse_spec_file")
    def test_validate_integration_test_invalid_spec(self, mock_parse, work_item_manager):
        """Test validation fails with invalid spec file."""
        # Arrange
        mock_parse.side_effect = ValueError("Invalid spec")
        work_item = {"id": "test", "type": "integration_test"}

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            work_item_manager.validate_integration_test(work_item)

        assert "Invalid spec" in str(exc_info.value)
        assert exc_info.value.code == ErrorCode.SPEC_VALIDATION_FAILED

    @patch("solokit.work_items.validator.spec_parser.parse_spec_file")
    def test_validate_integration_test_missing_required_sections(
        self, mock_parse, work_item_manager
    ):
        """Test validation fails when required sections are missing."""
        # Arrange
        mock_parse.return_value = {
            "scope": "",
            "test_scenarios": [],
            "performance_benchmarks": None,
            "environment_requirements": "",
            "acceptance_criteria": [],
        }
        work_item = {"id": "test", "dependencies": ["dep1"]}

        # Act & Assert
        with pytest.raises(SpecValidationError) as exc_info:
            work_item_manager.validate_integration_test(work_item)

        assert len(exc_info.value.context["validation_errors"]) > 0
        assert exc_info.value.code == ErrorCode.SPEC_VALIDATION_FAILED

    @patch("solokit.work_items.validator.spec_parser.parse_spec_file")
    def test_validate_integration_test_no_dependencies(self, mock_parse, work_item_manager):
        """Test validation fails when no dependencies provided."""
        # Arrange
        mock_parse.return_value = {
            "scope": "Test scope",
            "test_scenarios": [{"name": "Test", "content": "Content"}],
            "performance_benchmarks": "Benchmarks",
            "environment_requirements": "Requirements",
            "acceptance_criteria": ["1", "2", "3"],
        }
        work_item = {"id": "test", "dependencies": []}

        # Act & Assert
        with pytest.raises(SpecValidationError) as exc_info:
            work_item_manager.validate_integration_test(work_item)

        errors = exc_info.value.context["validation_errors"]
        assert any("dependencies" in err.lower() for err in errors)

    @patch("solokit.work_items.validator.spec_parser.parse_spec_file")
    def test_validate_integration_test_valid(self, mock_parse, work_item_manager):
        """Test validation passes with valid integration test."""
        # Arrange
        mock_parse.return_value = {
            "scope": "Test scope",
            "test_scenarios": [
                {"name": "Scenario 1", "content": "Test content 1"},
                {"name": "Scenario 2", "content": "Test content 2"},
            ],
            "performance_benchmarks": "Benchmarks",
            "environment_requirements": "Requirements",
            "acceptance_criteria": ["Criterion 1", "Criterion 2", "Criterion 3"],
        }
        work_item = {"id": "test", "dependencies": ["dep1", "dep2"]}

        # Act - should not raise
        work_item_manager.validate_integration_test(work_item)
        # Assert - if we get here, validation passed

    @patch("solokit.work_items.validator.spec_parser.parse_spec_file")
    def test_validate_integration_test_insufficient_acceptance_criteria(
        self, mock_parse, work_item_manager
    ):
        """Test validation fails with less than 3 acceptance criteria."""
        # Arrange
        mock_parse.return_value = {
            "scope": "Test scope",
            "test_scenarios": [{"name": "Test", "content": "Content"}],
            "performance_benchmarks": "Benchmarks",
            "environment_requirements": "Requirements",
            "acceptance_criteria": ["1", "2"],  # Only 2 items
        }
        work_item = {"id": "test", "dependencies": ["dep1"]}

        # Act & Assert
        with pytest.raises(SpecValidationError) as exc_info:
            work_item_manager.validate_integration_test(work_item)

        errors = exc_info.value.context["validation_errors"]
        assert any("at least 3" in err for err in errors)


class TestValidateDeployment:
    """Tests for deployment validation."""

    @patch("solokit.work_items.validator.spec_parser.parse_spec_file")
    def test_validate_deployment_missing_spec(self, mock_parse, work_item_manager):
        """Test validation fails when spec file is missing."""
        # Arrange
        mock_parse.side_effect = FileNotFoundError()
        work_item = {"id": "test", "type": "deployment", "spec_file": "test.md"}

        # Act & Assert
        with pytest.raises(FileOperationError) as exc_info:
            work_item_manager.validate_deployment(work_item)

        assert "not found" in str(exc_info.value).lower()
        assert exc_info.value.code == ErrorCode.FILE_OPERATION_FAILED

    @patch("solokit.work_items.validator.spec_parser.parse_spec_file")
    def test_validate_deployment_missing_required_sections(self, mock_parse, work_item_manager):
        """Test validation fails when required sections are missing."""
        # Arrange
        mock_parse.return_value = {
            "deployment_scope": "",
            "deployment_procedure": None,
            "environment_configuration": "",
            "rollback_procedure": None,
            "smoke_tests": [],
            "acceptance_criteria": [],
        }
        work_item = {"id": "test"}

        # Act & Assert
        with pytest.raises(SpecValidationError) as exc_info:
            work_item_manager.validate_deployment(work_item)

        errors = exc_info.value.context["validation_errors"]
        assert len(errors) > 0

    @patch("solokit.work_items.validator.spec_parser.parse_spec_file")
    def test_validate_deployment_missing_deployment_subsections(
        self, mock_parse, work_item_manager
    ):
        """Test validation fails when deployment procedure subsections are missing."""
        # Arrange
        mock_parse.return_value = {
            "deployment_scope": "Scope",
            "deployment_procedure": {
                "pre_deployment": "",
                "deployment_steps": "Steps",
                "post_deployment": "",
            },
            "environment_configuration": "Config",
            "rollback_procedure": {"triggers": "Triggers", "steps": "Steps"},
            "smoke_tests": ["Test 1"],
            "acceptance_criteria": ["1", "2", "3"],
        }
        work_item = {"id": "test"}

        # Act & Assert
        with pytest.raises(SpecValidationError) as exc_info:
            work_item_manager.validate_deployment(work_item)

        errors = exc_info.value.context["validation_errors"]
        assert any("pre-deployment" in err.lower() for err in errors)
        assert any("post-deployment" in err.lower() for err in errors)

    @patch("solokit.work_items.validator.spec_parser.parse_spec_file")
    def test_validate_deployment_missing_rollback_subsections(self, mock_parse, work_item_manager):
        """Test validation fails when rollback procedure subsections are missing."""
        # Arrange
        mock_parse.return_value = {
            "deployment_scope": "Scope",
            "deployment_procedure": {
                "pre_deployment": "Pre",
                "deployment_steps": "Steps",
                "post_deployment": "Post",
            },
            "environment_configuration": "Config",
            "rollback_procedure": {"triggers": "", "steps": ""},
            "smoke_tests": ["Test 1"],
            "acceptance_criteria": ["1", "2", "3"],
        }
        work_item = {"id": "test"}

        # Act & Assert
        with pytest.raises(SpecValidationError) as exc_info:
            work_item_manager.validate_deployment(work_item)

        errors = exc_info.value.context["validation_errors"]
        assert any("rollback triggers" in err.lower() for err in errors)
        assert any("rollback steps" in err.lower() for err in errors)

    @patch("solokit.work_items.validator.spec_parser.parse_spec_file")
    def test_validate_deployment_no_smoke_tests(self, mock_parse, work_item_manager):
        """Test validation fails when no smoke tests provided."""
        # Arrange
        mock_parse.return_value = {
            "deployment_scope": "Scope",
            "deployment_procedure": {
                "pre_deployment": "Pre",
                "deployment_steps": "Steps",
                "post_deployment": "Post",
            },
            "environment_configuration": "Config",
            "rollback_procedure": {"triggers": "Triggers", "steps": "Steps"},
            "smoke_tests": [],  # Empty
            "acceptance_criteria": ["1", "2", "3"],
        }
        work_item = {"id": "test"}

        # Act & Assert
        with pytest.raises(SpecValidationError) as exc_info:
            work_item_manager.validate_deployment(work_item)

        errors = exc_info.value.context["validation_errors"]
        assert any("smoke test" in err.lower() for err in errors)

    @patch("solokit.work_items.validator.spec_parser.parse_spec_file")
    def test_validate_deployment_valid(self, mock_parse, work_item_manager):
        """Test validation passes with valid deployment."""
        # Arrange
        mock_parse.return_value = {
            "deployment_scope": "Production deployment",
            "deployment_procedure": {
                "pre_deployment": "Pre-deployment checks",
                "deployment_steps": "Deployment steps",
                "post_deployment": "Post-deployment verification",
            },
            "environment_configuration": "Environment config",
            "rollback_procedure": {"triggers": "Rollback triggers", "steps": "Rollback steps"},
            "smoke_tests": ["Smoke test 1", "Smoke test 2"],
            "acceptance_criteria": ["Criterion 1", "Criterion 2", "Criterion 3"],
        }
        work_item = {"id": "test"}

        # Act - should not raise
        work_item_manager.validate_deployment(work_item)
        # Assert - if we get here, validation passed


# TestMilestones - public API tests kept here for integration testing
class TestMilestones:
    """Tests for milestone operations."""

    def test_create_milestone_new(self, work_item_manager):
        """Test creating a new milestone."""
        # Act - should not raise
        work_item_manager.create_milestone("v1.0", "Version 1.0", "First release", "2025-06-01")

        # Assert
        data = json.loads(work_item_manager.work_items_file.read_text())
        assert "v1.0" in data["milestones"]
        assert data["milestones"]["v1.0"]["title"] == "Version 1.0"

    def test_create_milestone_duplicate(self, work_item_manager_with_data):
        """Test that duplicate milestone is rejected."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            work_item_manager_with_data.create_milestone("v1.0", "Duplicate", "Test", None)

        assert "already exists" in str(exc_info.value)
        assert "v1.0" in str(exc_info.value)

    def test_create_milestone_no_target_date(self, work_item_manager):
        """Test creating milestone without target date."""
        # Act - should not raise
        work_item_manager.create_milestone("v1.0", "Version 1.0", "First release", None)

        # Assert
        data = json.loads(work_item_manager.work_items_file.read_text())
        assert data["milestones"]["v1.0"]["target_date"] == ""

    def test_get_milestone_progress_no_items(self, work_item_manager_with_data):
        """Test getting progress for milestone with no items."""
        # Act
        result = work_item_manager_with_data.get_milestone_progress("v2.0")

        # Assert
        assert result["total"] == 0
        assert result["percent"] == 0

    def test_get_milestone_progress_with_items(self, work_item_manager_with_data):
        """Test getting progress for milestone with items."""
        # Act
        result = work_item_manager_with_data.get_milestone_progress("v1.0")

        # Assert
        assert result["total"] == 2
        assert result["completed"] == 1
        assert result["in_progress"] == 1
        assert result["percent"] == 50

    def test_list_milestones_no_file(self, work_item_manager, capsys):
        """Test listing milestones when no file exists."""
        # Act
        work_item_manager.list_milestones()

        # Assert
        captured = capsys.readouterr()
        assert "No milestones found" in captured.out

    def test_list_milestones_empty(self, work_item_manager_with_data, capsys):
        """Test listing when milestones exist but are empty."""
        # Arrange
        data = json.loads(work_item_manager_with_data.work_items_file.read_text())
        data["milestones"] = {}
        work_item_manager_with_data.work_items_file.write_text(json.dumps(data))

        # Act
        work_item_manager_with_data.list_milestones()

        # Assert
        captured = capsys.readouterr()
        assert "No milestones found" in captured.out

    def test_list_milestones_displays_progress(self, work_item_manager_with_data, capsys):
        """Test that milestone progress is displayed."""
        # Act
        work_item_manager_with_data.list_milestones()

        # Assert
        captured = capsys.readouterr()
        assert "Version 1.0 Release" in captured.out
        assert "%" in captured.out
        assert "Target" in captured.out


class TestMainCLI:
    """Tests for the main() CLI entry point."""

    def test_main_missing_type_and_title(self, tmp_path, capsys, monkeypatch):
        """Test main function with missing required arguments."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        session_dir = project_root / ".session"
        session_dir.mkdir()
        (session_dir / "tracking").mkdir()

        monkeypatch.chdir(project_root)
        monkeypatch.setattr("sys.argv", ["manager"])

        from solokit.work_items.manager import main

        # Act & Assert
        with pytest.raises(SystemExit):
            main()

    def test_main_missing_title(self, tmp_path, capsys, monkeypatch):
        """Test main function with missing title argument."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        session_dir = project_root / ".session"
        session_dir.mkdir()
        (session_dir / "tracking").mkdir()

        monkeypatch.chdir(project_root)
        monkeypatch.setattr("sys.argv", ["manager", "--type", "feature"])

        from solokit.work_items.manager import main

        # Act & Assert
        with pytest.raises(SystemExit):
            main()

    def test_main_missing_type(self, tmp_path, capsys, monkeypatch):
        """Test main function with missing type argument."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        session_dir = project_root / ".session"
        session_dir.mkdir()
        (session_dir / "tracking").mkdir()

        monkeypatch.chdir(project_root)
        monkeypatch.setattr("sys.argv", ["manager", "--title", "Test Feature"])

        from solokit.work_items.manager import main

        # Act & Assert
        with pytest.raises(SystemExit):
            main()

    def test_main_successful_creation(self, tmp_path, monkeypatch):
        """Test main function successfully creates work item."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        session_dir = project_root / ".session"
        session_dir.mkdir()
        (session_dir / "tracking").mkdir()
        (session_dir / "specs").mkdir()

        # Create templates
        templates_dir = tmp_path / "project" / "templates"
        templates_dir.mkdir()
        template_file = templates_dir / "feature_spec.md"
        template_file.write_text("# Feature: [Feature Name]")

        monkeypatch.chdir(project_root)
        monkeypatch.setattr(
            "sys.argv",
            ["manager", "--type", "feature", "--title", "Test Feature", "--priority", "high"],
        )

        from solokit.work_items.manager import main

        # Act
        result = main()

        # Assert
        assert result == 0

    def test_main_with_dependencies(self, tmp_path, monkeypatch):
        """Test main function with dependencies argument."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        session_dir = project_root / ".session"
        session_dir.mkdir()
        tracking_dir = session_dir / "tracking"
        tracking_dir.mkdir()
        (session_dir / "specs").mkdir()

        # Create work_items.json with existing dependency
        work_items_file = tracking_dir / "work_items.json"
        data = {
            "work_items": {
                "feature_base": {
                    "id": "feature_base",
                    "type": "feature",
                    "title": "Base Feature",
                    "status": "completed",
                    "priority": "high",
                    "dependencies": [],
                }
            },
            "metadata": {},
            "milestones": {},
        }
        work_items_file.write_text(json.dumps(data))

        # Create templates
        templates_dir = tmp_path / "project" / "templates"
        templates_dir.mkdir()
        template_file = templates_dir / "feature_spec.md"
        template_file.write_text("# Feature: [Feature Name]")

        monkeypatch.chdir(project_root)
        monkeypatch.setattr(
            "sys.argv",
            [
                "manager",
                "--type",
                "feature",
                "--title",
                "Dependent Feature",
                "--dependencies",
                "feature_base",
            ],
        )

        from solokit.work_items.manager import main

        # Act
        result = main()

        # Assert
        assert result == 0

    def test_main_with_invalid_priority(self, tmp_path, monkeypatch):
        """Test main function with invalid priority (should default to high)."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        session_dir = project_root / ".session"
        session_dir.mkdir()
        (session_dir / "tracking").mkdir()
        (session_dir / "specs").mkdir()

        # Create templates
        templates_dir = tmp_path / "project" / "templates"
        templates_dir.mkdir()
        template_file = templates_dir / "feature_spec.md"
        template_file.write_text("# Feature: [Feature Name]")

        monkeypatch.chdir(project_root)
        monkeypatch.setattr(
            "sys.argv",
            [
                "manager",
                "--type",
                "feature",
                "--title",
                "Test Feature",
                "--priority",
                "invalid",
            ],
        )

        from solokit.work_items.manager import main

        # Act
        result = main()

        # Assert
        assert result == 0  # Should succeed with default priority


# TestGetStatusIcon moved to test_query.py
# Tests for _get_status_icon are now in test_query.py since it's a private method of WorkItemQuery
