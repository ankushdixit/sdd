"""Unit tests for work_item_creator module.

This module tests the WorkItemCreator class which handles work item creation,
ID generation, spec file creation, and interactive prompts.
"""

import json

import pytest
from solokit.core.exceptions import (
    ErrorCode,
    ValidationError,
    WorkItemAlreadyExistsError,
)
from solokit.work_items.creator import WorkItemCreator
from solokit.work_items.repository import WorkItemRepository


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

    def test_create_from_args_with_urgent_flag_no_existing(self, creator, tmp_path):
        """Test creating work item with urgent flag when no urgent item exists."""
        # Arrange
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        template_file = templates_dir / "feature_spec.md"
        template_file.write_text("# Feature: [Feature Name]")
        creator.templates_dir = templates_dir

        # Act
        result = creator.create_from_args("feature", "Urgent Feature", "high", "", urgent=True)

        # Assert
        assert result is not None
        data = json.loads(creator.repository.work_items_file.read_text())
        assert data["work_items"][result]["urgent"] is True

    def test_create_from_args_with_urgent_flag_existing_urgent(
        self, creator_with_data, tmp_path, monkeypatch
    ):
        """Test creating urgent work item when another urgent item exists (user confirms override)."""
        # Arrange
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        template_file = templates_dir / "feature_spec.md"
        template_file.write_text("# Feature: [Feature Name]")
        creator_with_data.templates_dir = templates_dir

        # Add existing urgent work item
        data = json.loads(creator_with_data.repository.work_items_file.read_text())
        data["work_items"]["feature_foundation"]["urgent"] = True
        creator_with_data.repository.work_items_file.write_text(json.dumps(data))

        # Mock user input to confirm override
        monkeypatch.setattr("builtins.input", lambda _: "y")

        # Act
        result = creator_with_data.create_from_args(
            "feature", "New Urgent Feature", "high", "", urgent=True
        )

        # Assert
        assert result is not None
        data = json.loads(creator_with_data.repository.work_items_file.read_text())
        assert data["work_items"][result]["urgent"] is True
        # Old urgent flag should be cleared
        assert data["work_items"]["feature_foundation"]["urgent"] is False

    def test_create_from_args_with_urgent_flag_user_declines(
        self, creator_with_data, tmp_path, monkeypatch
    ):
        """Test creating urgent work item when user declines to override existing urgent item."""
        # Arrange
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        template_file = templates_dir / "feature_spec.md"
        template_file.write_text("# Feature: [Feature Name]")
        creator_with_data.templates_dir = templates_dir

        # Add existing urgent work item
        data = json.loads(creator_with_data.repository.work_items_file.read_text())
        data["work_items"]["feature_foundation"]["urgent"] = True
        creator_with_data.repository.work_items_file.write_text(json.dumps(data))

        # Mock user input to decline override
        monkeypatch.setattr("builtins.input", lambda _: "n")

        # Act
        result = creator_with_data.create_from_args(
            "feature", "New Feature", "high", "", urgent=True
        )

        # Assert
        assert result is not None
        data = json.loads(creator_with_data.repository.work_items_file.read_text())
        # New item should NOT be urgent
        assert data["work_items"][result]["urgent"] is False
        # Old urgent flag should remain
        assert data["work_items"]["feature_foundation"]["urgent"] is True


class TestCreateSpecFileTemplateReplacement:
    """Tests for spec file template replacement for all work types."""

    def test_create_spec_file_refactor(self, creator, tmp_path):
        """Test creating a refactor specification file."""
        # Arrange
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        template_file = templates_dir / "refactor_spec.md"
        template_file.write_text("# Refactor: [Refactor Title]\n\nGoals...")
        creator.templates_dir = templates_dir

        # Act
        result = creator._create_spec_file("refactor_test", "refactor", "Code Cleanup")

        # Assert
        assert result == ".session/specs/refactor_test.md"
        spec_path = creator.specs_dir / "refactor_test.md"
        assert spec_path.exists()
        content = spec_path.read_text()
        assert "Code Cleanup" in content
        assert "[Refactor Title]" not in content

    def test_create_spec_file_security(self, creator, tmp_path):
        """Test creating a security specification file."""
        # Arrange
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        template_file = templates_dir / "security_spec.md"
        template_file.write_text("# Security: [Name]\n\nVulnerability...")
        creator.templates_dir = templates_dir

        # Act
        result = creator._create_spec_file("security_test", "security", "SQL Injection Fix")

        # Assert
        assert result == ".session/specs/security_test.md"
        spec_path = creator.specs_dir / "security_test.md"
        assert spec_path.exists()
        content = spec_path.read_text()
        assert "SQL Injection Fix" in content
        assert "[Name]" not in content

    def test_create_spec_file_integration_test(self, creator, tmp_path):
        """Test creating an integration_test specification file."""
        # Arrange
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        template_file = templates_dir / "integration_test_spec.md"
        template_file.write_text("# Integration Test: [Name]\n\nScope...")
        creator.templates_dir = templates_dir

        # Act
        result = creator._create_spec_file(
            "integration_test_api", "integration_test", "API Integration"
        )

        # Assert
        assert result == ".session/specs/integration_test_api.md"
        spec_path = creator.specs_dir / "integration_test_api.md"
        assert spec_path.exists()
        content = spec_path.read_text()
        assert "API Integration" in content
        assert "[Name]" not in content

    def test_create_spec_file_deployment(self, creator, tmp_path):
        """Test creating a deployment specification file."""
        # Arrange
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        template_file = templates_dir / "deployment_spec.md"
        template_file.write_text("# Deployment: [Environment]\n\nProcedure...")
        creator.templates_dir = templates_dir

        # Act
        result = creator._create_spec_file("deployment_prod", "deployment", "Production")

        # Assert
        assert result == ".session/specs/deployment_prod.md"
        spec_path = creator.specs_dir / "deployment_prod.md"
        assert spec_path.exists()
        content = spec_path.read_text()
        assert "Production" in content
        assert "[Environment]" not in content

    def test_create_spec_file_unknown_type_no_replacement(self, creator, tmp_path):
        """Test that unknown work type doesn't replace any placeholders."""
        # Arrange
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        template_file = templates_dir / "custom_spec.md"
        template_file.write_text("# Custom: [Placeholder]\n\nContent...")
        creator.templates_dir = templates_dir

        # Act
        result = creator._create_spec_file("custom_test", "custom", "Test Title")

        # Assert
        assert result == ".session/specs/custom_test.md"
        spec_path = creator.specs_dir / "custom_test.md"
        assert spec_path.exists()
        content = spec_path.read_text()
        # No replacement should occur for unknown types
        assert "[Placeholder]" in content


class TestPrintCreationConfirmation:
    """Tests for creation confirmation message."""

    def test_print_creation_confirmation_basic(self, creator, capsys):
        """Test basic confirmation message without dependencies or urgent flag."""
        # Act
        creator._print_creation_confirmation(
            "feature_test", "feature", "high", [], ".session/specs/feature_test.md", False
        )

        # Assert
        captured = capsys.readouterr()
        assert "Work item created successfully" in captured.out
        assert "feature_test" in captured.out
        assert "feature" in captured.out
        assert "high" in captured.out
        assert "not_started" in captured.out

    def test_print_creation_confirmation_with_dependencies(self, creator, capsys):
        """Test confirmation message with dependencies."""
        # Act
        creator._print_creation_confirmation(
            "feature_test",
            "feature",
            "high",
            ["dep1", "dep2"],
            ".session/specs/feature_test.md",
            False,
        )

        # Assert
        captured = capsys.readouterr()
        assert "Dependencies: dep1, dep2" in captured.out

    def test_print_creation_confirmation_with_urgent_flag(self, creator, capsys):
        """Test confirmation message with urgent flag."""
        # Act
        creator._print_creation_confirmation(
            "feature_test", "feature", "high", [], ".session/specs/feature_test.md", True
        )

        # Assert
        captured = capsys.readouterr()
        assert "Urgent: YES" in captured.out
        assert "will be prioritized above all other work items" in captured.out
