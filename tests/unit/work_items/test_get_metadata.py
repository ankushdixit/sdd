"""Unit tests for get_metadata module.

Tests the lightweight work item metadata retrieval utility.
"""

import json

import pytest

from sdd.work_items.get_metadata import get_work_item_metadata


@pytest.fixture
def work_items_data(tmp_path):
    """Create test work_items.json file."""
    session_dir = tmp_path / ".session"
    tracking_dir = session_dir / "tracking"
    tracking_dir.mkdir(parents=True)

    work_items_file = tracking_dir / "work_items.json"
    data = {
        "metadata": {
            "total_items": 2,
            "completed": 0,
            "in_progress": 1,
            "blocked": 0,
        },
        "work_items": {
            "feature_auth": {
                "id": "feature_auth",
                "type": "feature",
                "title": "Add authentication",
                "status": "in_progress",
                "priority": "high",
                "dependencies": ["feature_db"],
                "milestone": "Sprint 1",
            },
            "feature_db": {
                "id": "feature_db",
                "type": "feature",
                "title": "Database setup",
                "status": "completed",
                "priority": "critical",
                "dependencies": [],
                "milestone": "",
            },
        },
    }

    work_items_file.write_text(json.dumps(data, indent=2))
    return tmp_path, data


class TestGetWorkItemMetadata:
    """Tests for get_work_item_metadata function."""

    def test_get_existing_work_item(self, work_items_data, monkeypatch):
        """Test retrieving metadata for an existing work item."""
        tmp_path, data = work_items_data
        monkeypatch.chdir(tmp_path)

        result = get_work_item_metadata("feature_auth")

        assert result is not None
        assert result["id"] == "feature_auth"
        assert result["type"] == "feature"
        assert result["title"] == "Add authentication"
        assert result["status"] == "in_progress"
        assert result["priority"] == "high"
        assert result["dependencies"] == ["feature_db"]
        assert result["milestone"] == "Sprint 1"

    def test_get_work_item_with_no_milestone(self, work_items_data, monkeypatch):
        """Test retrieving work item with empty milestone."""
        tmp_path, data = work_items_data
        monkeypatch.chdir(tmp_path)

        result = get_work_item_metadata("feature_db")

        assert result is not None
        assert result["milestone"] == ""
        assert result["dependencies"] == []

    def test_get_nonexistent_work_item(self, work_items_data, monkeypatch):
        """Test retrieving non-existent work item returns None."""
        tmp_path, data = work_items_data
        monkeypatch.chdir(tmp_path)

        result = get_work_item_metadata("nonexistent_item")

        assert result is None

    def test_missing_work_items_file(self, tmp_path, monkeypatch):
        """Test when work_items.json doesn't exist."""
        monkeypatch.chdir(tmp_path)

        result = get_work_item_metadata("feature_auth")

        assert result is None

    def test_work_item_without_dependencies_field(self, tmp_path, monkeypatch):
        """Test work item that doesn't have dependencies field."""
        session_dir = tmp_path / ".session"
        tracking_dir = session_dir / "tracking"
        tracking_dir.mkdir(parents=True)

        work_items_file = tracking_dir / "work_items.json"
        data = {
            "work_items": {
                "feature_test": {
                    "id": "feature_test",
                    "type": "feature",
                    "title": "Test feature",
                    "status": "not_started",
                    "priority": "medium",
                    # No dependencies field
                }
            }
        }

        work_items_file.write_text(json.dumps(data))
        monkeypatch.chdir(tmp_path)

        result = get_work_item_metadata("feature_test")

        assert result is not None
        assert result["dependencies"] == []

    def test_work_item_without_milestone_field(self, tmp_path, monkeypatch):
        """Test work item that doesn't have milestone field."""
        session_dir = tmp_path / ".session"
        tracking_dir = session_dir / "tracking"
        tracking_dir.mkdir(parents=True)

        work_items_file = tracking_dir / "work_items.json"
        data = {
            "work_items": {
                "feature_test": {
                    "id": "feature_test",
                    "type": "feature",
                    "title": "Test feature",
                    "status": "not_started",
                    "priority": "medium",
                    "dependencies": [],
                    # No milestone field
                }
            }
        }

        work_items_file.write_text(json.dumps(data))
        monkeypatch.chdir(tmp_path)

        result = get_work_item_metadata("feature_test")

        assert result is not None
        assert result["milestone"] == ""

    def test_only_returns_metadata_not_spec(self, work_items_data, monkeypatch):
        """Test that only metadata is returned, not spec content."""
        tmp_path, data = work_items_data
        monkeypatch.chdir(tmp_path)

        result = get_work_item_metadata("feature_auth")

        # Should only have these metadata fields
        expected_keys = {"id", "type", "title", "status", "priority", "dependencies", "milestone"}
        assert set(result.keys()) == expected_keys

        # Should NOT have spec-related fields
        assert "spec_file" not in result
        assert "sessions" not in result
        assert "git" not in result

    def test_include_dependency_details_false_by_default(self, work_items_data, monkeypatch):
        """Test that dependency details are not included by default."""
        tmp_path, data = work_items_data
        monkeypatch.chdir(tmp_path)

        result = get_work_item_metadata("feature_auth")

        assert "dependencies" in result
        assert result["dependencies"] == ["feature_db"]
        assert "dependency_details" not in result

    def test_include_dependency_details_true(self, work_items_data, monkeypatch):
        """Test that dependency details are included when requested."""
        tmp_path, data = work_items_data
        monkeypatch.chdir(tmp_path)

        result = get_work_item_metadata("feature_auth", include_dependency_details=True)

        assert "dependencies" in result
        assert result["dependencies"] == ["feature_db"]
        assert "dependency_details" in result
        assert len(result["dependency_details"]) == 1

        dep_detail = result["dependency_details"][0]
        assert dep_detail["id"] == "feature_db"
        assert dep_detail["type"] == "feature"
        assert dep_detail["title"] == "Database setup"
        assert dep_detail["status"] == "completed"

    def test_include_dependency_details_with_no_dependencies(self, work_items_data, monkeypatch):
        """Test that dependency_details is not added when work item has no dependencies."""
        tmp_path, data = work_items_data
        monkeypatch.chdir(tmp_path)

        result = get_work_item_metadata("feature_db", include_dependency_details=True)

        assert "dependencies" in result
        assert result["dependencies"] == []
        assert "dependency_details" not in result

    def test_include_dependency_details_with_multiple_dependencies(self, tmp_path, monkeypatch):
        """Test dependency details with multiple dependencies."""
        session_dir = tmp_path / ".session"
        tracking_dir = session_dir / "tracking"
        tracking_dir.mkdir(parents=True)

        work_items_file = tracking_dir / "work_items.json"
        data = {
            "work_items": {
                "feature_main": {
                    "id": "feature_main",
                    "type": "feature",
                    "title": "Main feature",
                    "status": "not_started",
                    "priority": "high",
                    "dependencies": ["feature_a", "feature_b", "feature_c"],
                },
                "feature_a": {
                    "id": "feature_a",
                    "type": "feature",
                    "title": "Feature A",
                    "status": "completed",
                    "priority": "high",
                },
                "feature_b": {
                    "id": "feature_b",
                    "type": "bug",
                    "title": "Bug B",
                    "status": "in_progress",
                    "priority": "critical",
                },
                "feature_c": {
                    "id": "feature_c",
                    "type": "refactor",
                    "title": "Refactor C",
                    "status": "not_started",
                    "priority": "medium",
                },
            }
        }

        work_items_file.write_text(json.dumps(data))
        monkeypatch.chdir(tmp_path)

        result = get_work_item_metadata("feature_main", include_dependency_details=True)

        assert len(result["dependency_details"]) == 3
        assert result["dependency_details"][0]["id"] == "feature_a"
        assert result["dependency_details"][1]["id"] == "feature_b"
        assert result["dependency_details"][2]["id"] == "feature_c"

    def test_include_dependency_details_skips_missing_dependencies(self, tmp_path, monkeypatch):
        """Test that missing/invalid dependencies are skipped in details."""
        session_dir = tmp_path / ".session"
        tracking_dir = session_dir / "tracking"
        tracking_dir.mkdir(parents=True)

        work_items_file = tracking_dir / "work_items.json"
        data = {
            "work_items": {
                "feature_main": {
                    "id": "feature_main",
                    "type": "feature",
                    "title": "Main feature",
                    "status": "not_started",
                    "priority": "high",
                    "dependencies": ["feature_a", "nonexistent_item", "feature_b"],
                },
                "feature_a": {
                    "id": "feature_a",
                    "type": "feature",
                    "title": "Feature A",
                    "status": "completed",
                    "priority": "high",
                },
                "feature_b": {
                    "id": "feature_b",
                    "type": "bug",
                    "title": "Bug B",
                    "status": "in_progress",
                    "priority": "critical",
                },
            }
        }

        work_items_file.write_text(json.dumps(data))
        monkeypatch.chdir(tmp_path)

        result = get_work_item_metadata("feature_main", include_dependency_details=True)

        # Should only include the 2 valid dependencies, skip the missing one
        assert len(result["dependency_details"]) == 2
        assert result["dependency_details"][0]["id"] == "feature_a"
        assert result["dependency_details"][1]["id"] == "feature_b"
