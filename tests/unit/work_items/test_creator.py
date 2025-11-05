"""Unit tests for work_item_creator module.

This module tests the WorkItemCreator class which handles work item creation,
ID generation, spec file creation, and interactive prompts.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from sdd.core.exceptions import (
    ErrorCode,
    ValidationError,
    WorkItemAlreadyExistsError,
)
from sdd.work_items.creator import WorkItemCreator
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
    specs_dir = session_dir / "specs"
    specs_dir.mkdir()

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
    specs_dir = session_dir / "specs"
    specs_dir.mkdir()

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
                "sessions": [],
            },
        },
        "metadata": {"total_items": 2, "completed": 1, "in_progress": 1},
        "milestones": {},
    }
    work_items_file.write_text(json.dumps(sample_data, indent=2))

    return WorkItemRepository(session_dir)


@pytest.fixture
def creator(repository):
    """Provide a WorkItemCreator instance."""
    return WorkItemCreator(repository)


@pytest.fixture
def creator_with_data(repository_with_data):
    """Provide a WorkItemCreator instance with existing data."""
    return WorkItemCreator(repository_with_data)


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


class TestGenerateId:
    """Tests for work item ID generation."""

    def test_generate_id_basic(self, creator):
        """Test generating ID from type and title."""
        # Act
        work_id = creator._generate_id("feature", "User Authentication")

        # Assert
        assert work_id == "feature_user_authentication"

    def test_generate_id_removes_special_characters(self, creator):
        """Test that special characters are replaced with underscores."""
        # Act
        work_id = creator._generate_id("bug", "Fix: Login-Error!")

        # Assert
        assert work_id == "bug_fix_login_error"

    def test_generate_id_truncates_long_titles(self, creator):
        """Test that long titles are truncated to 30 characters."""
        # Arrange
        long_title = "A" * 50

        # Act
        work_id = creator._generate_id("feature", long_title)

        # Assert
        assert work_id == "feature_" + "a" * 30
        assert len(work_id.replace("feature_", "")) == 30

    def test_generate_id_strips_leading_trailing_underscores(self, creator):
        """Test that leading/trailing underscores are stripped."""
        # Act
        work_id = creator._generate_id("refactor", "___Clean Code___")

        # Assert
        assert work_id == "refactor_clean_code"
        assert not work_id.endswith("_")

    @pytest.mark.parametrize(
        "work_type", ["feature", "bug", "refactor", "security", "integration_test", "deployment"]
    )
    def test_generate_id_all_work_types(self, creator, work_type):
        """Test ID generation for all supported work types."""
        # Act
        work_id = creator._generate_id(work_type, "Test Item")

        # Assert
        assert work_id.startswith(f"{work_type}_")
        assert "test_item" in work_id


class TestCreateSpecFile:
    """Tests for specification file creation."""

    def test_create_spec_file_feature(self, creator, feature_template, tmp_path):
        """Test creating a feature specification file."""
        # Arrange
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        template_file = templates_dir / "feature_spec.md"
        template_file.write_text(feature_template)
        creator.templates_dir = templates_dir

        # Act
        result = creator._create_spec_file("feature_test", "feature", "Test Feature")

        # Assert
        assert result == ".session/specs/feature_test.md"
        spec_path = creator.specs_dir / "feature_test.md"
        assert spec_path.exists()
        content = spec_path.read_text()
        assert "Test Feature" in content
        assert "[Feature Name]" not in content

    def test_create_spec_file_bug(self, creator, bug_template, tmp_path):
        """Test creating a bug specification file."""
        # Arrange
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        template_file = templates_dir / "bug_spec.md"
        template_file.write_text(bug_template)
        creator.templates_dir = templates_dir

        # Act
        result = creator._create_spec_file("bug_test", "bug", "Test Bug")

        # Assert
        assert result == ".session/specs/bug_test.md"
        spec_path = creator.specs_dir / "bug_test.md"
        assert spec_path.exists()
        content = spec_path.read_text()
        assert "Test Bug" in content
        assert "[Bug Title]" not in content

    def test_create_spec_file_missing_template(self, creator, tmp_path):
        """Test that _create_spec_file returns empty string when template missing."""
        # Arrange
        empty_templates_dir = tmp_path / "empty_templates"
        empty_templates_dir.mkdir()
        creator.templates_dir = empty_templates_dir

        # Act
        result = creator._create_spec_file("feature_test", "feature", "Test Feature")

        # Assert
        assert result == ""
        # Verify spec file was NOT created
        spec_path = creator.specs_dir / "feature_test.md"
        assert not spec_path.exists()

    def test_create_spec_file_creates_specs_directory(self, creator):
        """Test that _create_spec_file creates specs directory if missing."""
        # Arrange
        creator.specs_dir.rmdir()
        assert not creator.specs_dir.exists()

        # Act (will fail due to missing template, but directory should be created)
        creator._create_spec_file("feature_test", "feature", "Test")

        # Assert
        assert creator.specs_dir.exists()


class TestCreateFromArgs:
    """Tests for non-interactive work item creation."""

    def test_create_from_args_basic(self, creator, tmp_path):
        """Test creating work item with command-line arguments."""
        # Arrange
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        template_file = templates_dir / "feature_spec.md"
        template_file.write_text("# Feature: [Feature Name]")
        creator.templates_dir = templates_dir

        # Act
        result = creator.create_from_args("feature", "Test Feature", "high", "")

        # Assert
        assert result == "feature_test_feature"
        assert creator.repository.work_items_file.exists()

    def test_create_from_args_invalid_type(self, creator):
        """Test that invalid work item type is rejected."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            creator.create_from_args("invalid_type", "Test Item", "high", "")

        assert "Invalid work item type" in str(exc_info.value)
        assert exc_info.value.code == ErrorCode.INVALID_WORK_ITEM_TYPE

    def test_create_from_args_invalid_priority(self, creator, tmp_path):
        """Test that invalid priority defaults to 'high'."""
        # Arrange
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        template_file = templates_dir / "feature_spec.md"
        template_file.write_text("# Feature: [Feature Name]")
        creator.templates_dir = templates_dir

        # Act
        result = creator.create_from_args("feature", "Test Feature", "invalid_priority", "")

        # Assert
        assert result is not None
        data = json.loads(creator.repository.work_items_file.read_text())
        assert data["work_items"][result]["priority"] == "high"

    def test_create_from_args_with_dependencies(self, creator_with_data, tmp_path):
        """Test creating work item with dependencies."""
        # Arrange
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        template_file = templates_dir / "feature_spec.md"
        template_file.write_text("# Feature: [Feature Name]")
        creator_with_data.templates_dir = templates_dir

        # Act
        result = creator_with_data.create_from_args(
            "feature", "New Feature", "high", "feature_foundation, feature_auth"
        )

        # Assert
        assert result is not None
        data = json.loads(creator_with_data.repository.work_items_file.read_text())
        assert "feature_foundation" in data["work_items"][result]["dependencies"]
        assert "feature_auth" in data["work_items"][result]["dependencies"]

    def test_create_from_args_duplicate_id(self, creator_with_data, tmp_path):
        """Test that duplicate work item ID is rejected."""
        # Arrange
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        template_file = templates_dir / "feature_spec.md"
        template_file.write_text("# Feature: [Feature Name]")
        creator_with_data.templates_dir = templates_dir

        # Act & Assert
        with pytest.raises(WorkItemAlreadyExistsError) as exc_info:
            creator_with_data.create_from_args(
                "feature",
                "Foundation",  # Will generate same ID as existing item
                "high",
                "",
            )

        assert "feature_foundation" in str(exc_info.value)
        assert exc_info.value.code == ErrorCode.WORK_ITEM_ALREADY_EXISTS

    def test_create_from_args_nonexistent_dependency(self, creator_with_data, tmp_path):
        """Test that nonexistent dependency is still accepted (warning only)."""
        # Arrange
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        template_file = templates_dir / "feature_spec.md"
        template_file.write_text("# Feature: [Feature Name]")
        creator_with_data.templates_dir = templates_dir

        # Act
        result = creator_with_data.create_from_args(
            "feature", "New Feature", "high", "nonexistent_dep"
        )

        # Assert - work item should be created despite nonexistent dependency
        assert result is not None
        data = json.loads(creator_with_data.repository.work_items_file.read_text())
        assert "nonexistent_dep" in data["work_items"][result]["dependencies"]


class TestCreateInteractive:
    """Tests for interactive work item creation."""

    def test_create_interactive_non_interactive_environment(self, creator):
        """Test that interactive creation fails in non-interactive environment."""
        # Arrange & Act & Assert
        with patch("sys.stdin.isatty", return_value=False):
            with pytest.raises(ValidationError) as exc_info:
                creator.create_interactive()

            assert "non-interactive" in str(exc_info.value).lower()
            assert exc_info.value.code == ErrorCode.INVALID_COMMAND

    @patch("sys.stdin.isatty", return_value=True)
    @patch("builtins.input")
    def test_create_interactive_eoferror_on_type(self, mock_input, mock_isatty, creator):
        """Test that EOFError during type selection is handled."""
        # Arrange
        mock_input.side_effect = EOFError()

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            creator.create_interactive()

        assert "Interactive input unavailable" in str(exc_info.value)
        assert exc_info.value.code == ErrorCode.INVALID_COMMAND

    @patch("sys.stdin.isatty", return_value=True)
    @patch("builtins.input")
    def test_create_interactive_eoferror_on_title(self, mock_input, mock_isatty, creator):
        """Test that EOFError during title input is handled."""
        # Arrange
        mock_input.side_effect = ["1", EOFError()]  # Select feature, then EOFError on title

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            creator.create_interactive()

        assert "Interactive input unavailable" in str(exc_info.value)
        assert exc_info.value.code == ErrorCode.INVALID_COMMAND


class TestPromptMethods:
    """Tests for prompt helper methods."""

    def test_prompt_type_valid_choice(self, creator):
        """Test _prompt_type with valid choice."""
        # Arrange
        with patch("builtins.input", return_value="1"):
            # Act
            result = creator._prompt_type()

        # Assert
        assert result == "feature"

    def test_prompt_type_invalid_choice(self, creator):
        """Test _prompt_type with invalid choice returns None."""
        # Arrange
        with patch("builtins.input", return_value="99"):
            # Act
            result = creator._prompt_type()

        # Assert
        assert result is None

    @pytest.mark.parametrize(
        "choice,expected",
        [
            ("1", "feature"),
            ("2", "bug"),
            ("3", "refactor"),
            ("4", "security"),
            ("5", "integration_test"),
            ("6", "deployment"),
        ],
    )
    def test_prompt_type_all_choices(self, creator, choice, expected):
        """Test _prompt_type for all valid choices."""
        # Arrange
        with patch("builtins.input", return_value=choice):
            # Act
            result = creator._prompt_type()

        # Assert
        assert result == expected

    def test_prompt_title_valid(self, creator):
        """Test _prompt_title with valid input."""
        # Arrange
        with patch("builtins.input", return_value="Test Title"):
            # Act
            result = creator._prompt_title()

        # Assert
        assert result == "Test Title"

    def test_prompt_title_empty_returns_none(self, creator):
        """Test _prompt_title with empty input raises ValidationError."""
        # Arrange
        with patch("builtins.input", return_value=""):
            # Act & Assert
            with pytest.raises(ValidationError) as exc_info:
                creator._prompt_title()

            assert "required" in str(exc_info.value).lower()
            assert exc_info.value.code == ErrorCode.MISSING_REQUIRED_FIELD

    def test_prompt_priority_default(self, creator):
        """Test _prompt_priority defaults to 'high'."""
        # Arrange
        with patch("builtins.input", return_value=""):
            # Act
            result = creator._prompt_priority()

        # Assert
        assert result == "high"

    def test_prompt_priority_valid(self, creator):
        """Test _prompt_priority with valid priority."""
        # Arrange
        with patch("builtins.input", return_value="critical"):
            # Act
            result = creator._prompt_priority()

        # Assert
        assert result == "critical"

    def test_prompt_priority_invalid_uses_default(self, creator, capsys):
        """Test _prompt_priority with invalid input uses 'high'."""
        # Arrange
        with patch("builtins.input", return_value="invalid"):
            # Act
            result = creator._prompt_priority()

        # Assert
        assert result == "high"
        captured = capsys.readouterr()
        assert "Invalid" in captured.out

    def test_prompt_dependencies_optional_empty(self, creator):
        """Test _prompt_dependencies for optional work type with no input."""
        # Arrange
        with patch("builtins.input", return_value=""):
            # Act
            result = creator._prompt_dependencies("feature")

        # Assert
        assert result == []

    def test_prompt_dependencies_with_valid_deps(self, creator_with_data):
        """Test _prompt_dependencies with valid dependency IDs."""
        # Arrange
        with patch("builtins.input", return_value="feature_foundation, feature_auth"):
            # Act
            result = creator_with_data._prompt_dependencies("feature")

        # Assert
        assert "feature_foundation" in result
        assert "feature_auth" in result

    def test_prompt_dependencies_filters_invalid(self, creator_with_data, capsys):
        """Test _prompt_dependencies filters out non-existent dependencies."""
        # Arrange
        with patch("builtins.input", return_value="feature_foundation, nonexistent"):
            # Act
            result = creator_with_data._prompt_dependencies("feature")

        # Assert
        assert "feature_foundation" in result
        assert "nonexistent" not in result
        captured = capsys.readouterr()
        assert "not found" in captured.out
