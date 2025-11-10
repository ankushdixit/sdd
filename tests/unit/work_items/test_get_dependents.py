"""Tests for get_dependents module."""

import json
from pathlib import Path

import pytest

from solokit.work_items.get_dependents import get_dependents


@pytest.fixture
def mock_work_items_with_deps(tmp_path, monkeypatch):
    """Create mock work items file with dependency relationships."""
    # Create .session structure
    session_dir = tmp_path / ".session"
    tracking_dir = session_dir / "tracking"
    tracking_dir.mkdir(parents=True)

    # Create work items with various dependency relationships
    data = {
        "metadata": {
            "total_items": 5,
            "completed": 0,
            "in_progress": 0,
            "blocked": 0,
        },
        "milestones": {},
        "work_items": {
            "feature_base": {
                "type": "feature",
                "title": "Base feature",
                "status": "not_started",
                "dependencies": [],
            },
            "feature_depends_on_base": {
                "type": "feature",
                "title": "Feature that depends on base",
                "status": "not_started",
                "dependencies": ["feature_base"],
            },
            "bug_depends_on_base": {
                "type": "bug",
                "title": "Bug fix that depends on base",
                "status": "in_progress",
                "dependencies": ["feature_base"],
            },
            "feature_independent": {
                "type": "feature",
                "title": "Independent feature",
                "status": "not_started",
                "dependencies": [],
            },
            "feature_depends_on_dependent": {
                "type": "feature",
                "title": "Feature with transitive dependency",
                "status": "not_started",
                "dependencies": ["feature_depends_on_base"],
            },
        },
    }

    work_items_file = tracking_dir / "work_items.json"
    with open(work_items_file, "w") as f:
        json.dump(data, f, indent=2)

    # Mock Path.cwd() to return our tmp_path
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

    return tmp_path, data["work_items"]


class TestGetDependents:
    """Tests for get_dependents function."""

    def test_get_dependents_with_multiple(self, mock_work_items_with_deps):
        """Test finding multiple dependents."""
        tmp_path, _ = mock_work_items_with_deps
        dependents = get_dependents("feature_base")

        # feature_base has 2 direct dependents
        assert len(dependents) == 2
        ids = {d["id"] for d in dependents}
        assert ids == {"feature_depends_on_base", "bug_depends_on_base"}

    def test_get_dependents_with_one(self, mock_work_items_with_deps):
        """Test finding single dependent."""
        tmp_path, _ = mock_work_items_with_deps
        dependents = get_dependents("feature_depends_on_base")

        # feature_depends_on_base has 1 dependent
        assert len(dependents) == 1
        assert dependents[0]["id"] == "feature_depends_on_dependent"

    def test_get_dependents_with_none(self, mock_work_items_with_deps):
        """Test work item with no dependents."""
        tmp_path, _ = mock_work_items_with_deps
        dependents = get_dependents("feature_independent")

        # feature_independent has no dependents
        assert len(dependents) == 0

    def test_get_dependents_nonexistent_item(self, mock_work_items_with_deps):
        """Test checking dependents for non-existent work item."""
        tmp_path, _ = mock_work_items_with_deps
        dependents = get_dependents("feature_does_not_exist")

        # Non-existent item has no dependents
        assert len(dependents) == 0

    def test_get_dependents_missing_session_dir(self, tmp_path, monkeypatch):
        """Test behavior when .session directory doesn't exist."""
        monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

        dependents = get_dependents("any_item")
        assert dependents == []

    def test_get_dependents_missing_work_items_file(self, tmp_path, monkeypatch):
        """Test behavior when work_items.json doesn't exist."""
        session_dir = tmp_path / ".session" / "tracking"
        session_dir.mkdir(parents=True)
        monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

        dependents = get_dependents("any_item")
        assert dependents == []

    def test_get_dependents_invalid_json(self, tmp_path, monkeypatch):
        """Test behavior with invalid JSON."""
        session_dir = tmp_path / ".session" / "tracking"
        session_dir.mkdir(parents=True)
        work_items_file = session_dir / "work_items.json"
        work_items_file.write_text("{ invalid json")
        monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

        dependents = get_dependents("any_item")
        assert dependents == []

    def test_get_dependents_empty_work_items(self, tmp_path, monkeypatch):
        """Test with empty work items."""
        session_dir = tmp_path / ".session" / "tracking"
        session_dir.mkdir(parents=True)
        work_items_file = session_dir / "work_items.json"
        data = {
            "metadata": {},
            "milestones": {},
            "work_items": {},
        }
        work_items_file.write_text(json.dumps(data))
        monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

        dependents = get_dependents("any_item")
        assert dependents == []

    def test_get_dependents_structure(self, mock_work_items_with_deps):
        """Test that returned dependents have correct structure."""
        tmp_path, _ = mock_work_items_with_deps
        dependents = get_dependents("feature_base")

        for dep in dependents:
            assert "id" in dep
            assert "type" in dep
            assert "title" in dep
            assert "status" in dep
            assert isinstance(dep["id"], str)
            assert isinstance(dep["type"], str)
            assert isinstance(dep["title"], str)
            assert isinstance(dep["status"], str)

    def test_get_dependents_with_missing_dependencies_field(self, tmp_path, monkeypatch):
        """Test work items without dependencies field."""
        session_dir = tmp_path / ".session"
        tracking_dir = session_dir / "tracking"
        tracking_dir.mkdir(parents=True)

        data = {
            "metadata": {},
            "milestones": {},
            "work_items": {
                "feature_a": {
                    "type": "feature",
                    "title": "Feature A",
                    "status": "not_started",
                    # No dependencies field
                },
                "feature_b": {
                    "type": "feature",
                    "title": "Feature B",
                    "status": "not_started",
                    "dependencies": ["feature_a"],
                },
            },
        }

        work_items_file = tracking_dir / "work_items.json"
        with open(work_items_file, "w") as f:
            json.dump(data, f)

        monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

        dependents = get_dependents("feature_a")
        assert len(dependents) == 1
        assert dependents[0]["id"] == "feature_b"

    def test_get_dependents_with_empty_dependencies(self, tmp_path, monkeypatch):
        """Test work items with empty dependencies list."""
        session_dir = tmp_path / ".session"
        tracking_dir = session_dir / "tracking"
        tracking_dir.mkdir(parents=True)

        data = {
            "metadata": {},
            "milestones": {},
            "work_items": {
                "feature_a": {
                    "type": "feature",
                    "title": "Feature A",
                    "status": "not_started",
                    "dependencies": [],
                },
                "feature_b": {
                    "type": "feature",
                    "title": "Feature B",
                    "status": "not_started",
                    "dependencies": [],
                },
            },
        }

        work_items_file = tracking_dir / "work_items.json"
        with open(work_items_file, "w") as f:
            json.dump(data, f)

        monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

        dependents = get_dependents("feature_a")
        assert len(dependents) == 0
