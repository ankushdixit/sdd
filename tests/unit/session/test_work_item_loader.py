"""Comprehensive tests for work_item_loader.py module.

This module tests WorkItemLoader class methods including:
- load_work_items
- get_work_item
- get_next_work_item
- load_work_item_spec
- update_work_item_status (uncovered lines 154-209)
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from solokit.core.types import Priority, WorkItemStatus
from solokit.session.briefing.work_item_loader import WorkItemLoader


@pytest.fixture
def temp_session_dir(tmp_path):
    """Create temporary .session directory structure."""
    session_dir = tmp_path / ".session"
    tracking_dir = session_dir / "tracking"
    specs_dir = session_dir / "specs"

    session_dir.mkdir()
    tracking_dir.mkdir()
    specs_dir.mkdir()

    return session_dir


@pytest.fixture
def sample_work_items_data():
    """Create sample work items data structure."""
    return {
        "work_items": {
            "WORK-001": {
                "id": "WORK-001",
                "title": "Feature A",
                "type": "feature",
                "priority": Priority.HIGH.value,
                "status": WorkItemStatus.NOT_STARTED.value,
                "dependencies": [],
                "created_at": "2025-01-01T10:00:00",
                "updated_at": "2025-01-01T10:00:00",
            },
            "WORK-002": {
                "id": "WORK-002",
                "title": "Feature B",
                "type": "feature",
                "priority": Priority.MEDIUM.value,
                "status": WorkItemStatus.IN_PROGRESS.value,
                "dependencies": ["WORK-001"],
                "sessions": [{"session_num": 1, "started_at": "2025-01-02T10:00:00"}],
                "created_at": "2025-01-01T11:00:00",
                "updated_at": "2025-01-02T10:00:00",
            },
            "WORK-003": {
                "id": "WORK-003",
                "title": "Feature C",
                "type": "bug",
                "priority": Priority.LOW.value,
                "status": WorkItemStatus.COMPLETED.value,
                "dependencies": [],
                "created_at": "2025-01-01T12:00:00",
                "updated_at": "2025-01-03T10:00:00",
            },
        },
        "metadata": {
            "total_items": 3,
            "completed": 1,
            "in_progress": 1,
            "blocked": 0,
            "last_updated": "2025-01-03T10:00:00",
        },
    }


class TestWorkItemLoaderInit:
    """Tests for WorkItemLoader initialization."""

    def test_init_with_default_session_dir(self):
        """Test WorkItemLoader initializes with default .session directory."""
        # Arrange & Act
        loader = WorkItemLoader()

        # Assert
        assert loader.session_dir == Path(".session")
        assert loader.work_items_file == Path(".session/tracking/work_items.json")

    def test_init_with_custom_session_dir(self, temp_session_dir):
        """Test WorkItemLoader initializes with custom session directory."""
        # Arrange & Act
        loader = WorkItemLoader(session_dir=temp_session_dir)

        # Assert
        assert loader.session_dir == temp_session_dir
        assert loader.work_items_file == temp_session_dir / "tracking" / "work_items.json"


class TestLoadWorkItems:
    """Tests for load_work_items method."""

    def test_load_work_items_returns_data(self, temp_session_dir, sample_work_items_data):
        """Test load_work_items returns work items data from file."""
        # Arrange
        work_items_file = temp_session_dir / "tracking" / "work_items.json"
        work_items_file.write_text(json.dumps(sample_work_items_data))

        loader = WorkItemLoader(session_dir=temp_session_dir)

        # Act
        result = loader.load_work_items()

        # Assert
        assert result == sample_work_items_data
        assert len(result["work_items"]) == 3

    def test_load_work_items_returns_empty_when_file_missing(self, temp_session_dir):
        """Test load_work_items returns empty dict when file doesn't exist."""
        # Arrange
        loader = WorkItemLoader(session_dir=temp_session_dir)

        # Act
        result = loader.load_work_items()

        # Assert
        assert result == {"work_items": {}}

    def test_load_work_items_logs_debug_message(self, temp_session_dir, sample_work_items_data):
        """Test load_work_items logs debug message with file path."""
        # Arrange
        work_items_file = temp_session_dir / "tracking" / "work_items.json"
        work_items_file.write_text(json.dumps(sample_work_items_data))

        loader = WorkItemLoader(session_dir=temp_session_dir)

        with patch("solokit.session.briefing.work_item_loader.logger") as mock_logger:
            # Act
            loader.load_work_items()

            # Assert
            mock_logger.debug.assert_called_once()
            assert "Loading work items from:" in mock_logger.debug.call_args[0][0]

    def test_load_work_items_logs_warning_when_file_missing(self, temp_session_dir):
        """Test load_work_items logs warning when file doesn't exist."""
        # Arrange
        loader = WorkItemLoader(session_dir=temp_session_dir)

        with patch("solokit.session.briefing.work_item_loader.logger") as mock_logger:
            # Act
            loader.load_work_items()

            # Assert
            mock_logger.warning.assert_called_once()
            assert "Work items file not found" in mock_logger.warning.call_args[0][0]


class TestGetWorkItem:
    """Tests for get_work_item method."""

    def test_get_work_item_returns_item_by_id(self, temp_session_dir, sample_work_items_data):
        """Test get_work_item returns specific work item by ID."""
        # Arrange
        work_items_file = temp_session_dir / "tracking" / "work_items.json"
        work_items_file.write_text(json.dumps(sample_work_items_data))

        loader = WorkItemLoader(session_dir=temp_session_dir)

        # Act
        result = loader.get_work_item("WORK-001")

        # Assert
        assert result is not None
        assert result["id"] == "WORK-001"
        assert result["title"] == "Feature A"

    def test_get_work_item_returns_none_when_not_found(
        self, temp_session_dir, sample_work_items_data
    ):
        """Test get_work_item returns None when work item doesn't exist."""
        # Arrange
        work_items_file = temp_session_dir / "tracking" / "work_items.json"
        work_items_file.write_text(json.dumps(sample_work_items_data))

        loader = WorkItemLoader(session_dir=temp_session_dir)

        # Act
        result = loader.get_work_item("WORK-999")

        # Assert
        assert result is None

    def test_get_work_item_with_preloaded_data(self, sample_work_items_data):
        """Test get_work_item works with pre-loaded work items data."""
        # Arrange
        loader = WorkItemLoader()

        # Act
        result = loader.get_work_item("WORK-002", work_items_data=sample_work_items_data)

        # Assert
        assert result is not None
        assert result["id"] == "WORK-002"
        assert result["status"] == WorkItemStatus.IN_PROGRESS.value


class TestGetNextWorkItem:
    """Tests for get_next_work_item method."""

    def test_get_next_work_item_prioritizes_in_progress(self, sample_work_items_data):
        """Test get_next_work_item prioritizes in-progress items."""
        # Arrange
        loader = WorkItemLoader()

        # Act
        item_id, item = loader.get_next_work_item(sample_work_items_data)

        # Assert
        assert item_id == "WORK-002"
        assert item["status"] == WorkItemStatus.IN_PROGRESS.value

    def test_get_next_work_item_returns_highest_priority_in_progress(self):
        """Test get_next_work_item returns highest priority among in-progress items."""
        # Arrange
        work_items_data = {
            "work_items": {
                "WORK-001": {
                    "status": WorkItemStatus.IN_PROGRESS.value,
                    "priority": Priority.LOW.value,
                    "dependencies": [],
                },
                "WORK-002": {
                    "status": WorkItemStatus.IN_PROGRESS.value,
                    "priority": Priority.CRITICAL.value,
                    "dependencies": [],
                },
                "WORK-003": {
                    "status": WorkItemStatus.IN_PROGRESS.value,
                    "priority": Priority.HIGH.value,
                    "dependencies": [],
                },
            }
        }
        loader = WorkItemLoader()

        # Act
        item_id, item = loader.get_next_work_item(work_items_data)

        # Assert
        assert item_id == "WORK-002"
        assert item["priority"] == Priority.CRITICAL.value

    def test_get_next_work_item_starts_new_work_when_no_in_progress(self):
        """Test get_next_work_item returns not_started item when no in_progress items."""
        # Arrange
        work_items_data = {
            "work_items": {
                "WORK-001": {
                    "status": WorkItemStatus.NOT_STARTED.value,
                    "priority": Priority.HIGH.value,
                    "dependencies": [],
                },
                "WORK-002": {
                    "status": WorkItemStatus.COMPLETED.value,
                    "priority": Priority.HIGH.value,
                    "dependencies": [],
                },
            }
        }
        loader = WorkItemLoader()

        # Act
        item_id, item = loader.get_next_work_item(work_items_data)

        # Assert
        assert item_id == "WORK-001"
        assert item["status"] == WorkItemStatus.NOT_STARTED.value

    def test_get_next_work_item_skips_items_with_unmet_dependencies(self, sample_work_items_data):
        """Test get_next_work_item skips items with unmet dependencies."""
        # Arrange
        # Make WORK-002 not_started and dependent on WORK-001 (not completed)
        sample_work_items_data["work_items"]["WORK-002"]["status"] = (
            WorkItemStatus.NOT_STARTED.value
        )
        loader = WorkItemLoader()

        # Act
        item_id, item = loader.get_next_work_item(sample_work_items_data)

        # Assert
        assert item_id == "WORK-001"  # Should return WORK-001, not WORK-002

    def test_get_next_work_item_returns_none_when_no_available(self):
        """Test get_next_work_item returns (None, None) when no items available."""
        # Arrange
        work_items_data = {
            "work_items": {
                "WORK-001": {
                    "status": WorkItemStatus.COMPLETED.value,
                    "priority": Priority.HIGH.value,
                    "dependencies": [],
                },
                "WORK-002": {
                    "status": WorkItemStatus.BLOCKED.value,
                    "priority": Priority.HIGH.value,
                    "dependencies": [],
                },
            }
        }
        loader = WorkItemLoader()

        # Act
        item_id, item = loader.get_next_work_item(work_items_data)

        # Assert
        assert item_id is None
        assert item is None


class TestLoadWorkItemSpec:
    """Tests for load_work_item_spec method."""

    def test_load_work_item_spec_with_dict_and_spec_file(self, temp_session_dir):
        """Test load_work_item_spec loads spec from work item dict with spec_file."""
        # Arrange
        spec_file = temp_session_dir / "specs" / "WORK-001.md"
        spec_file.write_text("# Specification\nDetails here")

        # Use absolute path or path relative to project root that resolves correctly
        work_item = {"id": "WORK-001", "spec_file": str(spec_file)}
        loader = WorkItemLoader(session_dir=temp_session_dir)

        # Act
        result = loader.load_work_item_spec(work_item)

        # Assert
        assert "# Specification" in result
        assert "Details here" in result

    def test_load_work_item_spec_with_dict_no_spec_file_fallback(self, temp_session_dir):
        """Test load_work_item_spec falls back to ID-based pattern when spec_file missing."""
        # Arrange
        spec_file = temp_session_dir / "specs" / "WORK-001.md"
        spec_file.write_text("# Fallback spec")

        work_item = {"id": "WORK-001"}  # No spec_file field
        loader = WorkItemLoader(session_dir=temp_session_dir)

        # Act
        result = loader.load_work_item_spec(work_item)

        # Assert
        assert "Fallback spec" in result

    def test_load_work_item_spec_with_string_id_legacy(self, temp_session_dir):
        """Test load_work_item_spec accepts string work item ID (legacy)."""
        # Arrange
        spec_file = temp_session_dir / "specs" / "WORK-001.md"
        spec_file.write_text("# Legacy spec")

        loader = WorkItemLoader(session_dir=temp_session_dir)

        # Act
        result = loader.load_work_item_spec("WORK-001")

        # Assert
        assert "Legacy spec" in result

    def test_load_work_item_spec_returns_error_when_not_found(self, temp_session_dir):
        """Test load_work_item_spec returns error message when spec file not found."""
        # Arrange
        work_item = {"id": "WORK-999"}
        loader = WorkItemLoader(session_dir=temp_session_dir)

        # Act
        result = loader.load_work_item_spec(work_item)

        # Assert
        assert "Specification file not found" in result

    def test_load_work_item_spec_returns_error_when_no_id(self, temp_session_dir):
        """Test load_work_item_spec returns error when work item has no id."""
        # Arrange
        work_item = {}  # No id field
        loader = WorkItemLoader(session_dir=temp_session_dir)

        # Act
        result = loader.load_work_item_spec(work_item)

        # Assert
        assert "Specification file not found: work item has no id" in result


class TestUpdateWorkItemStatus:
    """Tests for update_work_item_status method (uncovered lines 154-209)."""

    def test_update_work_item_status_returns_false_when_file_missing(self, temp_session_dir):
        """Test update_work_item_status returns False when work items file doesn't exist."""
        # Arrange
        loader = WorkItemLoader(session_dir=temp_session_dir)

        # Act
        result = loader.update_work_item_status("WORK-001", WorkItemStatus.IN_PROGRESS.value)

        # Assert
        assert result is False

    def test_update_work_item_status_returns_false_when_work_item_not_found(
        self, temp_session_dir, sample_work_items_data
    ):
        """Test update_work_item_status returns False when work item doesn't exist."""
        # Arrange
        work_items_file = temp_session_dir / "tracking" / "work_items.json"
        work_items_file.write_text(json.dumps(sample_work_items_data))

        loader = WorkItemLoader(session_dir=temp_session_dir)

        # Act
        result = loader.update_work_item_status("WORK-999", WorkItemStatus.IN_PROGRESS.value)

        # Assert
        assert result is False

    def test_update_work_item_status_updates_status_successfully(
        self, temp_session_dir, sample_work_items_data
    ):
        """Test update_work_item_status updates status and returns True."""
        # Arrange
        work_items_file = temp_session_dir / "tracking" / "work_items.json"
        work_items_file.write_text(json.dumps(sample_work_items_data))

        loader = WorkItemLoader(session_dir=temp_session_dir)

        # Act
        result = loader.update_work_item_status("WORK-001", WorkItemStatus.IN_PROGRESS.value)

        # Assert
        assert result is True

        # Verify file was updated
        updated_data = json.loads(work_items_file.read_text())
        assert updated_data["work_items"]["WORK-001"]["status"] == WorkItemStatus.IN_PROGRESS.value
        assert "updated_at" in updated_data["work_items"]["WORK-001"]

    def test_update_work_item_status_adds_session_tracking(
        self, temp_session_dir, sample_work_items_data
    ):
        """Test update_work_item_status adds session tracking when session_num provided."""
        # Arrange
        work_items_file = temp_session_dir / "tracking" / "work_items.json"
        work_items_file.write_text(json.dumps(sample_work_items_data))

        loader = WorkItemLoader(session_dir=temp_session_dir)

        # Act
        result = loader.update_work_item_status(
            "WORK-001", WorkItemStatus.IN_PROGRESS.value, session_num=1
        )

        # Assert
        assert result is True

        # Verify session was added
        updated_data = json.loads(work_items_file.read_text())
        assert "sessions" in updated_data["work_items"]["WORK-001"]
        assert len(updated_data["work_items"]["WORK-001"]["sessions"]) == 1
        assert updated_data["work_items"]["WORK-001"]["sessions"][0]["session_num"] == 1

    def test_update_work_item_status_appends_to_existing_sessions(
        self, temp_session_dir, sample_work_items_data
    ):
        """Test update_work_item_status appends to existing sessions list."""
        # Arrange
        work_items_file = temp_session_dir / "tracking" / "work_items.json"
        work_items_file.write_text(json.dumps(sample_work_items_data))

        loader = WorkItemLoader(session_dir=temp_session_dir)

        # Act - Add session 2 to WORK-002 (which already has session 1)
        result = loader.update_work_item_status(
            "WORK-002", WorkItemStatus.IN_PROGRESS.value, session_num=2
        )

        # Assert
        assert result is True

        # Verify session was appended
        updated_data = json.loads(work_items_file.read_text())
        assert len(updated_data["work_items"]["WORK-002"]["sessions"]) == 2
        assert updated_data["work_items"]["WORK-002"]["sessions"][1]["session_num"] == 2

    def test_update_work_item_status_updates_metadata_counters(
        self, temp_session_dir, sample_work_items_data
    ):
        """Test update_work_item_status updates metadata counters correctly."""
        # Arrange
        work_items_file = temp_session_dir / "tracking" / "work_items.json"
        work_items_file.write_text(json.dumps(sample_work_items_data))

        loader = WorkItemLoader(session_dir=temp_session_dir)

        # Act - Change WORK-001 from not_started to in_progress
        result = loader.update_work_item_status("WORK-001", WorkItemStatus.IN_PROGRESS.value)

        # Assert
        assert result is True

        # Verify metadata was updated
        updated_data = json.loads(work_items_file.read_text())
        assert updated_data["metadata"]["total_items"] == 3
        assert updated_data["metadata"]["in_progress"] == 2  # Should increase from 1 to 2
        assert updated_data["metadata"]["completed"] == 1
        assert updated_data["metadata"]["blocked"] == 0
        assert "last_updated" in updated_data["metadata"]

    def test_update_work_item_status_updates_completed_counter(
        self, temp_session_dir, sample_work_items_data
    ):
        """Test update_work_item_status updates completed counter correctly."""
        # Arrange
        work_items_file = temp_session_dir / "tracking" / "work_items.json"
        work_items_file.write_text(json.dumps(sample_work_items_data))

        loader = WorkItemLoader(session_dir=temp_session_dir)

        # Act - Change WORK-002 from in_progress to completed
        result = loader.update_work_item_status("WORK-002", WorkItemStatus.COMPLETED.value)

        # Assert
        assert result is True

        # Verify metadata was updated
        updated_data = json.loads(work_items_file.read_text())
        assert updated_data["metadata"]["completed"] == 2  # Should increase from 1 to 2
        assert updated_data["metadata"]["in_progress"] == 0  # Should decrease from 1 to 0

    def test_update_work_item_status_updates_blocked_counter(
        self, temp_session_dir, sample_work_items_data
    ):
        """Test update_work_item_status updates blocked counter correctly."""
        # Arrange
        work_items_file = temp_session_dir / "tracking" / "work_items.json"
        work_items_file.write_text(json.dumps(sample_work_items_data))

        loader = WorkItemLoader(session_dir=temp_session_dir)

        # Act - Change WORK-001 from not_started to blocked
        result = loader.update_work_item_status("WORK-001", WorkItemStatus.BLOCKED.value)

        # Assert
        assert result is True

        # Verify metadata was updated
        updated_data = json.loads(work_items_file.read_text())
        assert updated_data["metadata"]["blocked"] == 1  # Should increase from 0 to 1

    def test_update_work_item_status_logs_success(self, temp_session_dir, sample_work_items_data):
        """Test update_work_item_status logs success message."""
        # Arrange
        work_items_file = temp_session_dir / "tracking" / "work_items.json"
        work_items_file.write_text(json.dumps(sample_work_items_data))

        loader = WorkItemLoader(session_dir=temp_session_dir)

        with patch("solokit.session.briefing.work_item_loader.logger") as mock_logger:
            # Act
            loader.update_work_item_status("WORK-001", WorkItemStatus.IN_PROGRESS.value)

            # Assert
            mock_logger.info.assert_called_once()
            # Check the format string and arguments separately
            call_args = mock_logger.info.call_args
            assert "Updated work item %s status to %s" == call_args[0][0]
            assert call_args[0][1] == "WORK-001"
            assert call_args[0][2] == WorkItemStatus.IN_PROGRESS.value

    def test_update_work_item_status_logs_error_when_file_missing(self, temp_session_dir):
        """Test update_work_item_status logs error when file doesn't exist."""
        # Arrange
        loader = WorkItemLoader(session_dir=temp_session_dir)

        with patch("solokit.session.briefing.work_item_loader.logger") as mock_logger:
            # Act
            loader.update_work_item_status("WORK-001", WorkItemStatus.IN_PROGRESS.value)

            # Assert
            mock_logger.error.assert_called_once()
            assert "Work items file not found" in mock_logger.error.call_args[0][0]

    def test_update_work_item_status_logs_error_when_work_item_not_found(
        self, temp_session_dir, sample_work_items_data
    ):
        """Test update_work_item_status logs error when work item doesn't exist."""
        # Arrange
        work_items_file = temp_session_dir / "tracking" / "work_items.json"
        work_items_file.write_text(json.dumps(sample_work_items_data))

        loader = WorkItemLoader(session_dir=temp_session_dir)

        with patch("solokit.session.briefing.work_item_loader.logger") as mock_logger:
            # Act
            loader.update_work_item_status("WORK-999", WorkItemStatus.IN_PROGRESS.value)

            # Assert
            mock_logger.error.assert_called_once()
            # Check the format string and arguments separately
            call_args = mock_logger.error.call_args
            assert "Work item not found: %s" == call_args[0][0]
            assert call_args[0][1] == "WORK-999"
