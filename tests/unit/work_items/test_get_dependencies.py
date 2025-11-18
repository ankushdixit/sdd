"""Tests for get_dependencies module."""

import json
from pathlib import Path

import pytest
from solokit.work_items.get_dependencies import (
    _filter_by_relevance,
    get_available_dependencies,
)


@pytest.fixture
def mock_work_items(tmp_path, monkeypatch):
    """Create mock work items file for testing."""
    # Create .session structure
    session_dir = tmp_path / ".session"
    tracking_dir = session_dir / "tracking"
    tracking_dir.mkdir(parents=True)

    # Create work items data structure (matches actual JSON format)
    data = {
        "metadata": {
            "total_items": 4,
            "completed": 1,
            "in_progress": 1,
            "blocked": 1,
        },
        "milestones": {},
        "work_items": {
            "feature_auth": {
                "type": "feature",
                "title": "Add authentication",
                "status": "not_started",
                "dependencies": [],
            },
            "feature_api": {
                "type": "feature",
                "title": "Build REST API",
                "status": "in_progress",
                "dependencies": [],
            },
            "bug_login": {
                "type": "bug",
                "title": "Fix login error",
                "status": "blocked",
                "dependencies": ["feature_auth"],
            },
            "feature_done": {
                "type": "feature",
                "title": "Completed feature",
                "status": "completed",
                "dependencies": [],
            },
        },
    }

    work_items_file = tracking_dir / "work_items.json"
    with open(work_items_file, "w") as f:
        json.dump(data, f, indent=2)

    # Mock Path.cwd() to return our tmp_path
    monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

    return tmp_path, data["work_items"]


class TestGetAvailableDependencies:
    """Tests for get_available_dependencies function."""

    def test_basic_retrieval(self, mock_work_items):
        """Test basic dependency retrieval."""
        tmp_path, _ = mock_work_items
        deps = get_available_dependencies()

        # Should return 3 non-completed items
        assert len(deps) == 3
        ids = {d["id"] for d in deps}
        assert ids == {"feature_auth", "feature_api", "bug_login"}

    def test_exclude_completed_by_default(self, mock_work_items):
        """Test that completed items are excluded by default."""
        tmp_path, _ = mock_work_items
        deps = get_available_dependencies()

        # Should not include completed items
        ids = {d["id"] for d in deps}
        assert "feature_done" not in ids

    def test_custom_exclude_statuses(self, mock_work_items):
        """Test custom status exclusion."""
        tmp_path, _ = mock_work_items
        deps = get_available_dependencies(exclude_statuses=["completed", "blocked"])

        # Should exclude both completed and blocked
        assert len(deps) == 2
        ids = {d["id"] for d in deps}
        assert ids == {"feature_auth", "feature_api"}

    def test_max_results_limit(self, mock_work_items):
        """Test max_results parameter."""
        tmp_path, _ = mock_work_items
        deps = get_available_dependencies(max_results=2)

        # Should return at most 2 items
        assert len(deps) == 2

    def test_title_filter(self, mock_work_items):
        """Test smart filtering by title."""
        tmp_path, _ = mock_work_items
        deps = get_available_dependencies(
            title_filter="authentication system",
            max_results=10,
        )

        # Should prioritize feature_auth (matches "authentication")
        assert len(deps) > 0
        assert deps[0]["id"] == "feature_auth"

    def test_missing_session_dir(self, tmp_path, monkeypatch):
        """Test behavior when .session directory doesn't exist."""
        # Mock cwd to directory without .session
        monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

        deps = get_available_dependencies()
        assert deps == []

    def test_missing_work_items_file(self, tmp_path, monkeypatch):
        """Test behavior when work_items.json doesn't exist."""
        # Create .session but no work_items.json
        session_dir = tmp_path / ".session" / "tracking"
        session_dir.mkdir(parents=True)
        monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

        deps = get_available_dependencies()
        assert deps == []

    def test_invalid_json(self, tmp_path, monkeypatch):
        """Test behavior with invalid JSON."""
        # Create .session with invalid JSON
        session_dir = tmp_path / ".session" / "tracking"
        session_dir.mkdir(parents=True)
        work_items_file = session_dir / "work_items.json"
        work_items_file.write_text("{ invalid json")
        monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

        deps = get_available_dependencies()
        assert deps == []

    def test_empty_work_items(self, tmp_path, monkeypatch):
        """Test with empty work items file."""
        session_dir = tmp_path / ".session" / "tracking"
        session_dir.mkdir(parents=True)
        work_items_file = session_dir / "work_items.json"
        work_items_file.write_text("{}")
        monkeypatch.setattr(Path, "cwd", lambda: tmp_path)

        deps = get_available_dependencies()
        assert deps == []

    def test_dependency_structure(self, mock_work_items):
        """Test that returned dependencies have correct structure."""
        tmp_path, _ = mock_work_items
        deps = get_available_dependencies()

        for dep in deps:
            assert "id" in dep
            assert "type" in dep
            assert "title" in dep
            assert "status" in dep
            assert isinstance(dep["id"], str)
            assert isinstance(dep["type"], str)
            assert isinstance(dep["title"], str)
            assert isinstance(dep["status"], str)


class TestFilterByRelevance:
    """Tests for _filter_by_relevance function."""

    def test_exact_word_match(self):
        """Test that exact word matches score highest."""
        items = [
            {"id": "1", "type": "feature", "title": "Add authentication", "status": "not_started"},
            {"id": "2", "type": "feature", "title": "Build API", "status": "not_started"},
            {"id": "3", "type": "feature", "title": "User auth system", "status": "not_started"},
        ]

        filtered = _filter_by_relevance(items, "authentication")
        assert filtered[0]["id"] == "1"  # Exact match

    def test_partial_word_match(self):
        """Test partial word matching."""
        items = [
            {
                "id": "1",
                "type": "feature",
                "title": "Authorization system",
                "status": "not_started",
            },
            {"id": "2", "type": "feature", "title": "Build API", "status": "not_started"},
        ]

        filtered = _filter_by_relevance(items, "auth")
        assert filtered[0]["id"] == "1"  # Partial match with "authorization"

    def test_multiple_word_matches(self):
        """Test matching multiple words."""
        items = [
            {
                "id": "1",
                "type": "feature",
                "title": "User authentication system",
                "status": "not_started",
            },
            {"id": "2", "type": "feature", "title": "User profile", "status": "not_started"},
            {"id": "3", "type": "feature", "title": "Build system", "status": "not_started"},
        ]

        filtered = _filter_by_relevance(items, "user authentication")
        assert filtered[0]["id"] == "1"  # Matches both words

    def test_no_matches_returns_all(self):
        """Test that no matches returns all items."""
        items = [
            {"id": "1", "type": "feature", "title": "Feature A", "status": "not_started"},
            {"id": "2", "type": "feature", "title": "Feature B", "status": "not_started"},
        ]

        filtered = _filter_by_relevance(items, "xyz")
        assert len(filtered) == 2  # Returns all when no matches

    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        items = [
            {"id": "1", "type": "feature", "title": "Add Authentication", "status": "not_started"},
            {"id": "2", "type": "feature", "title": "Build API", "status": "not_started"},
        ]

        filtered = _filter_by_relevance(items, "AUTHENTICATION")
        assert filtered[0]["id"] == "1"  # Case-insensitive match

    def test_empty_title(self):
        """Test with empty title filter."""
        items = [
            {"id": "1", "type": "feature", "title": "Feature A", "status": "not_started"},
            {"id": "2", "type": "feature", "title": "Feature B", "status": "not_started"},
        ]

        filtered = _filter_by_relevance(items, "")
        assert len(filtered) == 2  # Returns all items

    def test_empty_items(self):
        """Test with empty items list."""
        filtered = _filter_by_relevance([], "test")
        assert filtered == []


class TestMainCLI:
    """Tests for the main() CLI entry point."""

    def test_main_basic_usage(self, mock_work_items, capsys, monkeypatch):
        """Test main function with basic usage."""
        tmp_path, _ = mock_work_items
        monkeypatch.setattr("sys.argv", ["get_dependencies"])

        from solokit.work_items.get_dependencies import main

        # Act
        main()

        # Assert
        captured = capsys.readouterr()
        assert "Found" in captured.out
        assert "available dependencies" in captured.out
        assert "feature_auth" in captured.out

    def test_main_with_title_filter(self, mock_work_items, capsys, monkeypatch):
        """Test main function with --title filter."""
        tmp_path, _ = mock_work_items
        monkeypatch.setattr("sys.argv", ["get_dependencies", "--title", "authentication"])

        from solokit.work_items.get_dependencies import main

        # Act
        main()

        # Assert
        captured = capsys.readouterr()
        assert "feature_auth" in captured.out

    def test_main_with_max_results(self, mock_work_items, capsys, monkeypatch):
        """Test main function with --max parameter."""
        tmp_path, _ = mock_work_items
        monkeypatch.setattr("sys.argv", ["get_dependencies", "--max", "1"])

        from solokit.work_items.get_dependencies import main

        # Act
        main()

        # Assert
        captured = capsys.readouterr()
        assert "Found 1 available" in captured.out

    def test_main_with_exclude_status(self, mock_work_items, capsys, monkeypatch):
        """Test main function with --exclude-status parameter."""
        tmp_path, _ = mock_work_items
        monkeypatch.setattr(
            "sys.argv", ["get_dependencies", "--exclude-status", "completed,blocked"]
        )

        from solokit.work_items.get_dependencies import main

        # Act
        main()

        # Assert
        captured = capsys.readouterr()
        # Should only show not_started and in_progress items
        assert "feature_auth" in captured.out
        assert "feature_api" in captured.out

    def test_main_no_dependencies_found(self, tmp_path, capsys, monkeypatch):
        """Test main function when no dependencies are found."""
        # Create empty work items
        session_dir = tmp_path / ".session"
        tracking_dir = session_dir / "tracking"
        tracking_dir.mkdir(parents=True)
        work_items_file = tracking_dir / "work_items.json"
        data = {
            "work_items": {
                "feature_done": {
                    "type": "feature",
                    "title": "Done",
                    "status": "completed",
                    "dependencies": [],
                }
            }
        }
        work_items_file.write_text(json.dumps(data))
        monkeypatch.setattr(Path, "cwd", lambda: tmp_path)
        monkeypatch.setattr("sys.argv", ["get_dependencies"])

        from solokit.work_items.get_dependencies import main

        # Act & Assert
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "No available dependencies found" in captured.err

    def test_main_output_format(self, mock_work_items, capsys, monkeypatch):
        """Test that main output has correct format."""
        tmp_path, _ = mock_work_items
        monkeypatch.setattr("sys.argv", ["get_dependencies", "--max", "1"])

        from solokit.work_items.get_dependencies import main

        # Act
        main()

        # Assert
        captured = capsys.readouterr()
        # Check output format includes required fields
        assert "ID:" in captured.out
        assert "Type:" in captured.out
        assert "Title:" in captured.out
        assert "Status:" in captured.out
