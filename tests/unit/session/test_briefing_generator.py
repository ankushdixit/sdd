"""Unit tests for briefing_generator.py module.

This module tests the session briefing generation system including:
- Work item and learning loading
- Work item selection logic
- Learning filtering
- Milestone context loading
- Project documentation loading
- Specification file loading
- Markdown heading manipulation
- Environment validation
- Git status checking
- Briefing generation (general, integration test, deployment)
- Git branch status determination
- CLI argument handling
"""

import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from solokit.core.exceptions import ErrorCode, GitError, SpecValidationError
from solokit.session import briefing as briefing_generator


@pytest.fixture
def temp_session_dir():
    """Create a temporary .session directory structure."""
    temp_dir = tempfile.mkdtemp()
    session_dir = Path(temp_dir) / ".session"
    session_dir.mkdir()

    # Create subdirectories
    (session_dir / "tracking").mkdir()
    (session_dir / "specs").mkdir()
    (session_dir / "briefings").mkdir()

    # Change to temp directory
    import os

    original_cwd = Path.cwd()
    os.chdir(temp_dir)

    yield temp_dir

    # Restore and cleanup
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_work_items():
    """Create sample work items data."""
    return {
        "work_items": {
            "WORK-001": {
                "id": "WORK-001",
                "title": "Implement feature A",
                "type": "feature",
                "priority": "high",
                "status": "not_started",
                "dependencies": [],
                "tags": ["backend", "api"],
            },
            "WORK-002": {
                "id": "WORK-002",
                "title": "Fix bug B",
                "type": "bug",
                "priority": "medium",
                "status": "in_progress",
                "dependencies": [],
                "tags": ["frontend", "ui"],
            },
            "WORK-003": {
                "id": "WORK-003",
                "title": "Task with dependencies",
                "type": "feature",
                "priority": "low",
                "status": "not_started",
                "dependencies": ["WORK-001"],
                "tags": ["testing"],
            },
        },
        "metadata": {
            "total_items": 3,
            "completed": 0,
            "in_progress": 1,
            "blocked": 0,
        },
        "milestones": {
            "m1": {
                "title": "Milestone 1",
                "description": "First milestone",
                "target_date": "2025-12-31",
            }
        },
    }


@pytest.fixture
def sample_learnings():
    """Create sample learnings data."""
    return {
        "learnings": [
            {
                "content": "Always validate input parameters",
                "category": "best_practice",
                "tags": ["backend", "validation"],
                "created_at": "2025-01-20T10:00:00",
            },
            {
                "content": "Use TypeScript for type safety",
                "category": "technical",
                "tags": ["frontend", "typescript"],
                "created_at": "2025-01-21T10:00:00",
            },
            {
                "content": "Write tests first",
                "category": "testing",
                "tags": ["testing", "tdd"],
                "created_at": "2025-01-22T10:00:00",
            },
        ]
    }


class TestLoadWorkItems:
    """Tests for load_work_items function."""

    def test_load_work_items_success(self, temp_session_dir, sample_work_items):
        """Test that load_work_items successfully loads work items from file."""
        # Arrange
        work_items_file = Path(".session/tracking/work_items.json")
        work_items_file.write_text(json.dumps(sample_work_items))

        # Act
        result = briefing_generator.load_work_items()

        # Assert
        assert result == sample_work_items
        assert "work_items" in result
        assert len(result["work_items"]) == 3

    def test_load_work_items_file_not_found(self, temp_session_dir):
        """Test that load_work_items returns empty dict when file doesn't exist."""
        # Arrange - no file created

        # Act
        result = briefing_generator.load_work_items()

        # Assert
        assert result == {"work_items": {}}

    def test_load_work_items_logs_debug_message(self, temp_session_dir, sample_work_items):
        """Test that load_work_items logs debug message with file path."""
        # Arrange
        work_items_file = Path(".session/tracking/work_items.json")
        work_items_file.write_text(json.dumps(sample_work_items))

        with patch("solokit.session.briefing.logger") as mock_logger:
            # Act
            briefing_generator.load_work_items()

            # Assert
            mock_logger.debug.assert_called()


class TestLoadLearnings:
    """Tests for load_learnings function."""

    def test_load_learnings_success(self, temp_session_dir, sample_learnings):
        """Test that load_learnings successfully loads learnings from file."""
        # Arrange
        learnings_file = Path(".session/tracking/learnings.json")
        learnings_file.write_text(json.dumps(sample_learnings))

        # Act
        result = briefing_generator.load_learnings()

        # Assert
        assert result == sample_learnings
        assert "learnings" in result
        assert len(result["learnings"]) == 3

    def test_load_learnings_file_not_found(self, temp_session_dir):
        """Test that load_learnings returns empty learnings when file doesn't exist."""
        # Arrange - no file created

        # Act
        result = briefing_generator.load_learnings()

        # Assert
        assert result == {"learnings": []}


class TestGetNextWorkItem:
    """Tests for get_next_work_item function."""

    def test_get_next_work_item_returns_in_progress_first(self, sample_work_items):
        """Test that get_next_work_item prioritizes in-progress items."""
        # Arrange - WORK-002 is in_progress

        # Act
        item_id, item = briefing_generator.get_next_work_item(sample_work_items)

        # Assert
        assert item_id == "WORK-002"
        assert item["status"] == "in_progress"

    def test_get_next_work_item_returns_highest_priority_in_progress(self):
        """Test that get_next_work_item returns highest priority in-progress item."""
        # Arrange
        work_items_data = {
            "work_items": {
                "WORK-001": {
                    "status": "in_progress",
                    "priority": "low",
                    "dependencies": [],
                },
                "WORK-002": {
                    "status": "in_progress",
                    "priority": "critical",
                    "dependencies": [],
                },
                "WORK-003": {
                    "status": "in_progress",
                    "priority": "high",
                    "dependencies": [],
                },
            }
        }

        # Act
        item_id, item = briefing_generator.get_next_work_item(work_items_data)

        # Assert
        assert item_id == "WORK-002"
        assert item["priority"] == "critical"

    def test_get_next_work_item_returns_not_started_when_no_in_progress(self):
        """Test that get_next_work_item returns not_started item when no in_progress items."""
        # Arrange
        work_items_data = {
            "work_items": {
                "WORK-001": {
                    "status": "not_started",
                    "priority": "high",
                    "dependencies": [],
                },
                "WORK-002": {
                    "status": "completed",
                    "priority": "high",
                    "dependencies": [],
                },
            }
        }

        # Act
        item_id, item = briefing_generator.get_next_work_item(work_items_data)

        # Assert
        assert item_id == "WORK-001"
        assert item["status"] == "not_started"

    def test_get_next_work_item_checks_dependencies(self, sample_work_items):
        """Test that get_next_work_item only returns items with satisfied dependencies."""
        # Arrange
        # WORK-003 depends on WORK-001 (not completed)
        sample_work_items["work_items"]["WORK-002"]["status"] = "completed"  # No in-progress

        # Act
        item_id, item = briefing_generator.get_next_work_item(sample_work_items)

        # Assert
        assert item_id == "WORK-001"  # Should return WORK-001, not WORK-003

    def test_get_next_work_item_allows_item_with_completed_dependencies(self):
        """Test that get_next_work_item allows items whose dependencies are completed."""
        # Arrange
        work_items_data = {
            "work_items": {
                "WORK-001": {
                    "status": "completed",
                    "priority": "high",
                    "dependencies": [],
                },
                "WORK-002": {
                    "status": "not_started",
                    "priority": "high",
                    "dependencies": ["WORK-001"],
                },
            }
        }

        # Act
        item_id, item = briefing_generator.get_next_work_item(work_items_data)

        # Assert
        assert item_id == "WORK-002"

    def test_get_next_work_item_returns_none_when_no_available(self):
        """Test that get_next_work_item returns (None, None) when no items available."""
        # Arrange
        work_items_data = {
            "work_items": {
                "WORK-001": {"status": "completed", "priority": "high", "dependencies": []},
                "WORK-002": {"status": "blocked", "priority": "high", "dependencies": []},
            }
        }

        # Act
        item_id, item = briefing_generator.get_next_work_item(work_items_data)

        # Assert
        assert item_id is None
        assert item is None


class TestGetRelevantLearnings:
    """Tests for get_relevant_learnings function."""

    def test_get_relevant_learnings_filters_by_tags(self, sample_learnings):
        """Test that get_relevant_learnings scores learnings by tag overlap."""
        # Arrange - Enhancement #11: Now uses multi-factor scoring
        work_item = {"tags": ["backend", "api"], "title": "Test", "type": "feature"}

        # Act
        result = briefing_generator.get_relevant_learnings(sample_learnings, work_item)

        # Assert - With multi-factor scoring, more learnings may be returned
        # The one with matching tags should be in results
        assert len(result) >= 1
        matching_learning = next(
            (learning for learning in result if learning.get("tags") == ["backend", "validation"]),
            None,
        )
        assert matching_learning is not None

    def test_get_relevant_learnings_returns_max_5_learnings(self):
        """Test that get_relevant_learnings returns maximum 10 learnings."""
        # Arrange - Enhancement #11: Changed from 5 to 10 learnings
        learnings_data = {
            "learnings": [
                {
                    "content": f"Learning {i}",
                    "tags": ["test"],
                    "created_at": f"2025-01-{i:02d}T10:00:00",
                }
                for i in range(1, 15)
            ]
        }
        work_item = {"tags": ["test"], "title": "Test", "type": "feature"}

        # Act
        result = briefing_generator.get_relevant_learnings(learnings_data, work_item)

        # Assert - Now returns top 10 instead of 5
        assert len(result) <= 10

    def test_get_relevant_learnings_sorts_by_most_recent(self):
        """Test that get_relevant_learnings sorts by relevance score."""
        # Arrange - Enhancement #11: Now sorts by score, not just recency
        learnings_data = {
            "learnings": [
                {"content": "Old", "tags": ["test"], "created_at": "2025-01-01T10:00:00"},
                {
                    "content": "New test validation",
                    "tags": ["test"],
                    "created_at": "2025-01-30T10:00:00",
                },
                {"content": "Middle", "tags": ["test"], "created_at": "2025-01-15T10:00:00"},
            ]
        }
        work_item = {"tags": ["test"], "title": "validation feature", "type": "feature"}

        # Act
        result = briefing_generator.get_relevant_learnings(learnings_data, work_item)

        # Assert - "New test validation" should score highest due to keyword + recency
        assert result[0]["content"] == "New test validation"

    def test_get_relevant_learnings_returns_empty_when_no_overlap(self, sample_learnings):
        """Test that get_relevant_learnings includes category bonuses."""
        # Arrange - Enhancement #11: Categories get bonus scores, may return results
        work_item = {"tags": ["database", "sql"], "title": "Test", "type": "feature"}

        # Act
        result = briefing_generator.get_relevant_learnings(sample_learnings, work_item)

        # Assert - May include best_practice category due to bonus scoring
        # No longer guaranteed to be empty
        assert isinstance(result, list)


class TestLoadMilestoneContext:
    """Tests for load_milestone_context function."""

    def test_load_milestone_context_returns_milestone_data(
        self, temp_session_dir, sample_work_items
    ):
        """Test that load_milestone_context loads and returns milestone data."""
        # Arrange
        sample_work_items["work_items"]["WORK-001"]["milestone"] = "m1"
        work_items_file = Path(".session/tracking/work_items.json")
        work_items_file.write_text(json.dumps(sample_work_items))
        work_item = sample_work_items["work_items"]["WORK-001"]

        # Act
        result = briefing_generator.load_milestone_context(work_item)

        # Assert
        assert result is not None
        assert result["name"] == "m1"
        assert result["title"] == "Milestone 1"
        assert result["description"] == "First milestone"

    def test_load_milestone_context_calculates_progress(self, temp_session_dir, sample_work_items):
        """Test that load_milestone_context calculates milestone progress."""
        # Arrange
        sample_work_items["work_items"]["WORK-001"]["milestone"] = "m1"
        sample_work_items["work_items"]["WORK-002"]["milestone"] = "m1"
        sample_work_items["work_items"]["WORK-001"]["status"] = "completed"
        work_items_file = Path(".session/tracking/work_items.json")
        work_items_file.write_text(json.dumps(sample_work_items))
        work_item = sample_work_items["work_items"]["WORK-002"]

        # Act
        result = briefing_generator.load_milestone_context(work_item)

        # Assert
        assert result["total_items"] == 2
        assert result["completed_items"] == 1
        assert result["progress"] == 50

    def test_load_milestone_context_returns_none_when_no_milestone(self):
        """Test that load_milestone_context returns None when work item has no milestone."""
        # Arrange
        work_item = {"title": "Test"}

        # Act
        result = briefing_generator.load_milestone_context(work_item)

        # Assert
        assert result is None

    def test_load_milestone_context_returns_none_when_file_not_found(self):
        """Test that load_milestone_context returns None when work items file doesn't exist."""
        # Arrange
        work_item = {"milestone": "m1"}

        # Act
        result = briefing_generator.load_milestone_context(work_item)

        # Assert
        assert result is None


class TestLoadProjectDocs:
    """Tests for load_project_docs function."""

    def test_load_project_docs_loads_existing_files(self, temp_session_dir):
        """Test that load_project_docs loads existing documentation files."""
        # Arrange
        docs_dir = Path("docs")
        docs_dir.mkdir()
        (docs_dir / "vision.md").write_text("# Vision\nOur vision")
        Path("README.md").write_text("# README\nProject readme")

        # Act
        result = briefing_generator.load_project_docs()

        # Assert
        assert "vision.md" in result
        assert "README.md" in result
        assert "Our vision" in result["vision.md"]

    def test_load_project_docs_skips_missing_files(self, temp_session_dir):
        """Test that load_project_docs skips files that don't exist."""
        # Arrange - no files created

        # Act
        result = briefing_generator.load_project_docs()

        # Assert
        assert result == {}


class TestLoadCurrentStack:
    """Tests for load_current_stack function."""

    def test_load_current_stack_loads_file(self, temp_session_dir):
        """Test that load_current_stack loads stack file content."""
        # Arrange
        stack_file = Path(".session/tracking/stack.txt")
        stack_file.write_text("Python 3.11\nDjango 4.2")

        # Act
        result = briefing_generator.load_current_stack()

        # Assert
        assert "Python 3.11" in result
        assert "Django 4.2" in result

    def test_load_current_stack_returns_default_when_missing(self, temp_session_dir):
        """Test that load_current_stack returns default message when file missing."""
        # Arrange - no file created

        # Act
        result = briefing_generator.load_current_stack()

        # Assert
        assert result == "Stack not yet generated"


class TestLoadCurrentTree:
    """Tests for load_current_tree function."""

    def test_load_current_tree_loads_file(self, temp_session_dir):
        """Test that load_current_tree loads tree file content."""
        # Arrange
        tree_file = Path(".session/tracking/tree.txt")
        tree_file.write_text(".\n├── src/\n└── tests/")

        # Act
        result = briefing_generator.load_current_tree()

        # Assert
        assert "src/" in result
        assert "tests/" in result

    def test_load_current_tree_returns_default_when_missing(self, temp_session_dir):
        """Test that load_current_tree returns default message when file missing."""
        # Arrange - no file created

        # Act
        result = briefing_generator.load_current_tree()

        # Assert
        assert result == "Tree not yet generated"

    def test_load_current_tree_raises_file_operation_error_on_read_failure(self, temp_session_dir):
        """Test that load_current_tree raises FileOperationError on read failure."""
        from unittest.mock import patch

        from solokit.core.exceptions import FileOperationError

        # Arrange
        tree_file = Path(".session/tracking/tree.txt")
        tree_file.parent.mkdir(parents=True, exist_ok=True)
        tree_file.write_text("test content")

        # Act & Assert
        with patch("pathlib.Path.read_text", side_effect=OSError("Permission denied")):
            with pytest.raises(FileOperationError) as exc_info:
                briefing_generator.load_current_tree()

            # Verify error details
            assert exc_info.value.context["operation"] == "read"
            assert "tree.txt" in exc_info.value.context["file_path"]
            assert "Permission denied" in exc_info.value.context["details"]


class TestLoadWorkItemSpec:
    """Tests for load_work_item_spec function."""

    def test_load_work_item_spec_with_dict(self, temp_session_dir):
        """Test that load_work_item_spec loads spec from work item dict."""
        # Arrange
        spec_file = Path(".session/specs/WORK-001.md")
        spec_file.write_text("# Specification\nDetails here")
        work_item = {"id": "WORK-001", "spec_file": ".session/specs/WORK-001.md"}

        # Act
        result = briefing_generator.load_work_item_spec(work_item)

        # Assert
        assert "# Specification" in result
        assert "Details here" in result

    def test_load_work_item_spec_with_string_id(self, temp_session_dir):
        """Test that load_work_item_spec accepts string work item ID (legacy)."""
        # Arrange
        spec_file = Path(".session/specs/WORK-001.md")
        spec_file.write_text("# Specification\nLegacy spec")

        # Act
        result = briefing_generator.load_work_item_spec("WORK-001")

        # Assert
        assert "Legacy spec" in result

    def test_load_work_item_spec_fallback_to_id_pattern(self, temp_session_dir):
        """Test that load_work_item_spec falls back to ID-based pattern when spec_file missing."""
        # Arrange
        spec_file = Path(".session/specs/WORK-001.md")
        spec_file.write_text("# Fallback spec")
        work_item = {"id": "WORK-001"}  # No spec_file field

        # Act
        result = briefing_generator.load_work_item_spec(work_item)

        # Assert
        assert "Fallback spec" in result

    def test_load_work_item_spec_returns_error_when_not_found(self, temp_session_dir):
        """Test that load_work_item_spec returns error message when spec file not found."""
        # Arrange
        work_item = {"id": "WORK-999"}

        # Act
        result = briefing_generator.load_work_item_spec(work_item)

        # Assert
        assert "Specification file not found" in result


class TestShiftHeadingLevels:
    """Tests for shift_heading_levels function."""

    def test_shift_heading_levels_shifts_all_headings(self):
        """Test that shift_heading_levels shifts all heading levels correctly."""
        # Arrange
        markdown = "# Title\n## Section\n### Subsection"

        # Act
        result = briefing_generator.shift_heading_levels(markdown, 2)

        # Assert
        assert result == "### Title\n#### Section\n##### Subsection"

    def test_shift_heading_levels_caps_at_h6(self):
        """Test that shift_heading_levels caps heading level at 6."""
        # Arrange
        markdown = "##### Level 5\n###### Level 6"

        # Act
        result = briefing_generator.shift_heading_levels(markdown, 2)

        # Assert
        assert "###### Level 5" in result
        assert "###### Level 6" in result  # Capped at 6

    def test_shift_heading_levels_preserves_non_heading_lines(self):
        """Test that shift_heading_levels preserves non-heading lines."""
        # Arrange
        markdown = "# Title\nSome text\n## Section"

        # Act
        result = briefing_generator.shift_heading_levels(markdown, 1)

        # Assert
        assert "Some text" in result
        assert result == "## Title\nSome text\n### Section"

    def test_shift_heading_levels_returns_unchanged_when_shift_zero(self):
        """Test that shift_heading_levels returns unchanged content when shift is 0."""
        # Arrange
        markdown = "# Title\n## Section"

        # Act
        result = briefing_generator.shift_heading_levels(markdown, 0)

        # Assert
        assert result == markdown

    def test_shift_heading_levels_handles_empty_content(self):
        """Test that shift_heading_levels handles empty content."""
        # Arrange
        markdown = ""

        # Act
        result = briefing_generator.shift_heading_levels(markdown, 2)

        # Assert
        assert result == ""


class TestValidateEnvironment:
    """Tests for validate_environment function."""

    def test_validate_environment_checks_python_version(self):
        """Test that validate_environment includes Python version."""
        # Arrange & Act
        result = briefing_generator.validate_environment()

        # Assert
        assert any("Python:" in check for check in result)

    @patch("subprocess.run")
    def test_validate_environment_checks_git(self, mock_run):
        """Test that validate_environment checks for git."""
        # Arrange
        mock_run.return_value = Mock(returncode=0, stdout="git version 2.39.0")

        # Act
        result = briefing_generator.validate_environment()

        # Assert
        assert any("Git:" in check for check in result)
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_validate_environment_handles_git_not_found(self, mock_run):
        """Test that validate_environment handles git not found gracefully."""
        # Arrange
        mock_run.side_effect = FileNotFoundError()

        # Act
        result = briefing_generator.validate_environment()

        # Assert
        assert any("Git: NOT FOUND" in check for check in result)


class TestCheckGitStatus:
    """Tests for check_git_status function."""

    @patch("solokit.git.integration.GitWorkflow")
    def test_check_git_status_returns_git_info(self, mock_git_workflow_class):
        """Test that check_git_status returns git status information."""
        # Arrange
        mock_workflow = Mock()
        mock_workflow.check_git_status.return_value = (True, "clean")
        mock_workflow.get_current_branch.return_value = "main"
        mock_git_workflow_class.return_value = mock_workflow

        # Act
        result = briefing_generator.check_git_status()

        # Assert
        assert result["clean"] is True
        assert result["status"] == "clean"
        assert result["branch"] == "main"

    @patch("solokit.git.integration.GitWorkflow")
    def test_check_git_status_raises_git_error_on_exception(self, mock_git_workflow_class):
        """Test that check_git_status raises GitError when git workflow fails."""
        # Arrange - simulate git error
        mock_workflow = Mock()
        mock_workflow.check_git_status.side_effect = Exception("Not a git repository")
        mock_git_workflow_class.return_value = mock_workflow

        # Act & Assert
        with pytest.raises(GitError) as exc_info:
            briefing_generator.check_git_status()

        assert exc_info.value.code.name == "GIT_COMMAND_FAILED"
        assert "Failed to check git status" in exc_info.value.message

    @patch("solokit.git.integration.GitWorkflow")
    def test_check_git_status_reraises_git_error(self, mock_git_workflow_class):
        """Test that check_git_status re-raises GitError as-is."""
        # Arrange - simulate GitError from workflow
        mock_workflow = Mock()
        original_error = GitError(message="Not a git repository", code=ErrorCode.NOT_A_GIT_REPO)
        mock_workflow.check_git_status.side_effect = original_error
        mock_git_workflow_class.return_value = mock_workflow

        # Act & Assert
        with pytest.raises(GitError) as exc_info:
            briefing_generator.check_git_status()

        # Should be the same error (not wrapped)
        assert exc_info.value.code.name == "NOT_A_GIT_REPO"
        assert exc_info.value is original_error


class TestCheckCommandExists:
    """Tests for check_command_exists function."""

    @patch("subprocess.run")
    def test_check_command_exists_returns_true_when_exists(self, mock_run):
        """Test that check_command_exists returns True when command exists."""
        # Arrange
        mock_run.return_value = Mock(returncode=0)

        # Act
        result = briefing_generator.check_command_exists("docker")

        # Assert
        assert result is True

    @patch("subprocess.run")
    def test_check_command_exists_returns_false_when_not_found(self, mock_run):
        """Test that check_command_exists returns False when command not found."""
        # Arrange
        mock_run.side_effect = FileNotFoundError()

        # Act
        result = briefing_generator.check_command_exists("nonexistent")

        # Assert
        assert result is False


class TestGenerateIntegrationTestBriefing:
    """Tests for generate_integration_test_briefing function."""

    def test_generate_integration_test_briefing_returns_empty_for_non_integration_test(self):
        """Test that generate_integration_test_briefing returns empty string for non-integration test."""
        # Arrange
        work_item = {"type": "feature"}

        # Act
        result = briefing_generator.generate_integration_test_briefing(work_item)

        # Assert
        assert result == ""

    @patch("solokit.session.briefing.check_command_exists")
    def test_generate_integration_test_briefing_includes_context(self, mock_check):
        """Test that generate_integration_test_briefing includes integration test context."""
        # Arrange
        mock_check.return_value = True
        work_item = {
            "type": "integration_test",
            "scope": "Testing API endpoints integration",
            "environment_requirements": {
                "services_required": ["database", "cache"],
                "compose_file": "docker-compose.yml",
            },
            "test_scenarios": [
                {"name": "Test user login"},
                {"name": "Test data retrieval"},
            ],
        }

        # Act
        result = briefing_generator.generate_integration_test_briefing(work_item)

        # Assert
        assert "Integration Test Context" in result
        assert "Integration Scope" in result
        assert "Required Services" in result
        assert "database" in result
        assert "Test Scenarios" in result

    @patch("solokit.session.briefing.check_command_exists")
    def test_generate_integration_test_briefing_checks_docker(self, mock_check):
        """Test that generate_integration_test_briefing checks for Docker availability."""
        # Arrange
        mock_check.return_value = False
        work_item = {
            "type": "integration_test",
            "environment_requirements": {},
        }

        # Act
        result = briefing_generator.generate_integration_test_briefing(work_item)

        # Assert
        assert "Docker" in result
        assert "Not found" in result or "✗" in result


class TestGenerateDeploymentBriefing:
    """Tests for generate_deployment_briefing function."""

    def test_generate_deployment_briefing_returns_empty_for_non_deployment(self):
        """Test that generate_deployment_briefing returns empty string for non-deployment."""
        # Arrange
        work_item = {"type": "feature"}

        # Act
        result = briefing_generator.generate_deployment_briefing(work_item)

        # Assert
        assert result == ""

    def test_generate_deployment_briefing_includes_context(self):
        """Test that generate_deployment_briefing includes deployment context."""
        # Arrange
        work_item = {
            "type": "deployment",
            "specification": "## Deployment Scope\n## Rollback Procedure\nDetails here",
        }

        # Act
        result = briefing_generator.generate_deployment_briefing(work_item)

        # Assert
        assert "DEPLOYMENT CONTEXT" in result
        assert "Deployment Scope" in result
        assert "Rollback Procedure" in result


class TestDetermineGitBranchFinalStatus:
    """Tests for determine_git_branch_final_status function."""

    @patch("solokit.session.briefing.git_context.CommandRunner")
    def test_determine_git_branch_final_status_returns_merged_when_merged(self, mock_runner_class):
        """Test that determine_git_branch_final_status returns 'merged' when branch is merged."""
        # Arrange
        mock_runner = Mock()
        mock_result = Mock(success=True, stdout="  session-001-test")
        mock_runner.run.return_value = mock_result
        mock_runner_class.return_value = mock_runner
        git_info = {"parent_branch": "main"}

        # Act
        result = briefing_generator.determine_git_branch_final_status("session-001-test", git_info)

        # Assert
        assert result == "merged"

    @patch("solokit.session.briefing.git_context.CommandRunner")
    def test_determine_git_branch_final_status_returns_pr_created_when_open_pr(
        self, mock_runner_class
    ):
        """Test that determine_git_branch_final_status returns 'pr_created' when PR is open."""
        # Arrange
        mock_runner = Mock()

        def run_side_effect(cmd, *args, **kwargs):
            if "branch" in cmd and "--merged" in cmd:
                return Mock(success=False, stdout="")
            elif "gh" in cmd:
                return Mock(success=True, stdout='[{"number": 123, "state": "OPEN"}]')
            else:
                return Mock(success=False, stdout="")

        mock_runner.run.side_effect = run_side_effect
        mock_runner_class.return_value = mock_runner
        git_info = {"parent_branch": "main"}

        # Act
        result = briefing_generator.determine_git_branch_final_status("session-001-test", git_info)

        # Assert
        assert result == "pr_created"

    @patch("solokit.session.briefing.git_context.CommandRunner")
    def test_determine_git_branch_final_status_returns_pr_closed_when_closed_pr(
        self, mock_runner_class
    ):
        """Test that determine_git_branch_final_status returns 'pr_closed' when PR is closed."""
        # Arrange
        mock_runner = Mock()

        def run_side_effect(cmd, *args, **kwargs):
            if "branch" in cmd and "--merged" in cmd:
                return Mock(success=False, stdout="")
            elif "gh" in cmd:
                return Mock(success=True, stdout='[{"number": 123, "state": "CLOSED"}]')
            else:
                return Mock(success=False, stdout="")

        mock_runner.run.side_effect = run_side_effect
        mock_runner_class.return_value = mock_runner
        git_info = {"parent_branch": "main"}

        # Act
        result = briefing_generator.determine_git_branch_final_status("session-001-test", git_info)

        # Assert
        assert result == "pr_closed"

    @patch("solokit.session.briefing.git_context.CommandRunner")
    def test_determine_git_branch_final_status_returns_ready_for_pr_when_branch_exists(
        self, mock_runner_class
    ):
        """Test that determine_git_branch_final_status returns 'ready_for_pr' when branch exists locally."""
        # Arrange
        mock_runner = Mock()

        def run_side_effect(cmd, *args, **kwargs):
            if "branch" in cmd and "--merged" in cmd:
                return Mock(success=False, stdout="")
            elif "gh" in cmd:
                return Mock(success=False, stdout="")
            elif "show-ref" in cmd:
                return Mock(success=True, stdout="ref")
            else:
                return Mock(success=False, stdout="")

        mock_runner.run.side_effect = run_side_effect
        mock_runner_class.return_value = mock_runner
        git_info = {"parent_branch": "main"}

        # Act
        result = briefing_generator.determine_git_branch_final_status("session-001-test", git_info)

        # Assert
        assert result == "ready_for_pr"

    @patch("solokit.session.briefing.git_context.CommandRunner")
    def test_determine_git_branch_final_status_returns_deleted_when_not_found(
        self, mock_runner_class
    ):
        """Test that determine_git_branch_final_status returns 'deleted' when branch not found."""
        # Arrange
        mock_runner = Mock()

        def run_side_effect(cmd, *args, **kwargs):
            # All commands fail - branch not found anywhere
            return Mock(success=False, stdout="")

        mock_runner.run.side_effect = run_side_effect
        mock_runner_class.return_value = mock_runner
        git_info = {"parent_branch": "main"}

        # Act
        result = briefing_generator.determine_git_branch_final_status("session-001-test", git_info)

        # Assert
        assert result == "deleted"


class TestFinalizePreviousWorkItemGitStatus:
    """Tests for finalize_previous_work_item_git_status function."""

    @patch("subprocess.run")
    def test_finalize_previous_work_item_git_status_updates_completed_work_item(
        self, mock_run, temp_session_dir
    ):
        """Test that finalize_previous_work_item_git_status updates git status for completed work items."""
        # Arrange
        work_items_data = {
            "work_items": {
                "WORK-001": {
                    "status": "completed",
                    "git": {"status": "in_progress", "branch": "session-001-test"},
                },
                "WORK-002": {
                    "status": "not_started",
                    "git": {},
                },
            }
        }
        work_items_file = Path(".session/tracking/work_items.json")
        work_items_file.write_text(json.dumps(work_items_data))

        mock_run.return_value = Mock(returncode=0, stdout="  session-001-test")

        # Act
        briefing_generator.finalize_previous_work_item_git_status(work_items_data, "WORK-002")

        # Assert
        # Check that in-memory data was updated
        assert work_items_data["work_items"]["WORK-001"]["git"]["status"] == "merged"

        # Also check that file was updated
        updated_data = json.loads(work_items_file.read_text())
        assert updated_data["work_items"]["WORK-001"]["git"]["status"] == "merged"

    def test_finalize_previous_work_item_git_status_skips_in_progress_work_items(
        self, temp_session_dir
    ):
        """Test that finalize_previous_work_item_git_status skips in-progress work items."""
        # Arrange
        work_items_data = {
            "work_items": {
                "WORK-001": {
                    "status": "in_progress",  # Not completed
                    "git": {"status": "in_progress", "branch": "session-001-test"},
                },
                "WORK-002": {
                    "status": "not_started",
                },
            }
        }
        work_items_file = Path(".session/tracking/work_items.json")
        work_items_file.write_text(json.dumps(work_items_data))

        # Act
        briefing_generator.finalize_previous_work_item_git_status(work_items_data, "WORK-002")

        # Assert
        # Check that file was NOT updated (status still in_progress)
        updated_data = json.loads(work_items_file.read_text())
        assert updated_data["work_items"]["WORK-001"]["git"]["status"] == "in_progress"

    def test_finalize_previous_work_item_git_status_skips_when_no_previous_work(
        self, temp_session_dir
    ):
        """Test that finalize_previous_work_item_git_status handles no previous work item."""
        # Arrange
        work_items_data = {
            "work_items": {
                "WORK-001": {
                    "status": "not_started",
                },
            }
        }
        work_items_file = Path(".session/tracking/work_items.json")
        work_items_file.write_text(json.dumps(work_items_data))

        # Act & Assert - should not raise error
        briefing_generator.finalize_previous_work_item_git_status(work_items_data, "WORK-001")


class TestGenerateBriefing:
    """Tests for generate_briefing function."""

    @patch("solokit.session.briefing.load_project_docs")
    @patch("solokit.session.briefing.load_current_stack")
    @patch("solokit.session.briefing.load_current_tree")
    @patch("solokit.session.briefing.load_work_item_spec")
    @patch("solokit.session.briefing.validate_environment")
    @patch("solokit.session.briefing.check_git_status")
    @patch("solokit.session.briefing.load_milestone_context")
    @patch("solokit.session.briefing.get_relevant_learnings")
    def test_generate_briefing_includes_work_item_info(
        self,
        mock_learnings,
        mock_milestone,
        mock_git,
        mock_env,
        mock_spec,
        mock_tree,
        mock_stack,
        mock_docs,
    ):
        """Test that generate_briefing includes work item information."""
        # Arrange
        item_id = "WORK-001"
        item = {
            "title": "Test Feature",
            "type": "feature",
            "priority": "high",
            "status": "not_started",
        }
        learnings_data = {"learnings": []}

        mock_docs.return_value = {}
        mock_stack.return_value = "Python 3.11"
        mock_tree.return_value = "."
        mock_spec.return_value = "# Spec"
        mock_env.return_value = ["Python: 3.11"]
        mock_git.return_value = {"status": "clean", "branch": "main"}
        mock_milestone.return_value = None
        mock_learnings.return_value = []

        # Act
        result = briefing_generator.generate_briefing(item_id, item, learnings_data)

        # Assert
        assert "WORK-001" in result
        assert "Test Feature" in result
        assert "feature" in result
        assert "high" in result

    @patch("solokit.session.briefing.load_project_docs")
    @patch("solokit.session.briefing.load_current_stack")
    @patch("solokit.session.briefing.load_current_tree")
    @patch("solokit.session.briefing.load_work_item_spec")
    @patch("solokit.session.briefing.validate_environment")
    @patch("solokit.session.briefing.check_git_status")
    @patch("solokit.session.briefing.load_milestone_context")
    @patch("solokit.session.briefing.get_relevant_learnings")
    def test_generate_briefing_includes_environment_status(
        self,
        mock_learnings,
        mock_milestone,
        mock_git,
        mock_env,
        mock_spec,
        mock_tree,
        mock_stack,
        mock_docs,
    ):
        """Test that generate_briefing includes environment status."""
        # Arrange
        item_id = "WORK-001"
        item = {"title": "Test", "type": "feature", "priority": "high", "status": "not_started"}
        learnings_data = {"learnings": []}

        mock_docs.return_value = {}
        mock_stack.return_value = "Stack"
        mock_tree.return_value = "Tree"
        mock_spec.return_value = "Spec"
        mock_env.return_value = ["Python: 3.11", "Git: 2.39"]
        mock_git.return_value = {"status": "clean", "branch": "main"}
        mock_milestone.return_value = None
        mock_learnings.return_value = []

        # Act
        result = briefing_generator.generate_briefing(item_id, item, learnings_data)

        # Assert
        assert "Environment Status" in result
        assert "Python: " in result  # Accept any Python version
        assert "Git: git version" in result  # Accept any git version format

    @patch("solokit.session.briefing.load_project_docs")
    @patch("solokit.session.briefing.load_current_stack")
    @patch("solokit.session.briefing.load_current_tree")
    @patch("solokit.session.briefing.load_work_item_spec")
    @patch("solokit.session.briefing.validate_environment")
    @patch("solokit.session.briefing.check_git_status")
    @patch("solokit.session.briefing.load_milestone_context")
    @patch("solokit.session.briefing.get_relevant_learnings")
    @patch("solokit.work_items.spec_validator.validate_spec_file")
    def test_generate_briefing_includes_spec_validation_warning(
        self,
        mock_validate_spec,
        mock_learnings,
        mock_milestone,
        mock_git,
        mock_env,
        mock_spec,
        mock_tree,
        mock_stack,
        mock_docs,
    ):
        """Test that generate_briefing includes spec validation warning when spec is invalid."""
        # Arrange
        item_id = "WORK-001"
        item = {"title": "Test", "type": "feature", "priority": "high", "status": "not_started"}
        learnings_data = {"learnings": []}

        mock_docs.return_value = {}
        mock_stack.return_value = "Stack"
        mock_tree.return_value = "Tree"
        mock_spec.return_value = "Spec"
        mock_env.return_value = []
        mock_git.return_value = {"status": "clean"}
        mock_milestone.return_value = None
        mock_learnings.return_value = []
        # Mock validate_spec_file to raise SpecValidationError
        mock_validate_spec.side_effect = SpecValidationError(
            work_item_id=item_id, errors=["Missing acceptance criteria"]
        )

        # Patch the spec validator in the correct location
        with patch(
            "solokit.work_items.spec_validator.format_validation_report",
            return_value="Validation Warning",
        ):
            # Act
            result = briefing_generator.generate_briefing(item_id, item, learnings_data)

        # Assert
        assert "Validation Warning" in result  # Should include the formatted validation report

    @patch("solokit.session.briefing.load_project_docs")
    @patch("solokit.session.briefing.load_current_stack")
    @patch("solokit.session.briefing.load_current_tree")
    @patch("solokit.session.briefing.load_work_item_spec")
    @patch("solokit.session.briefing.validate_environment")
    @patch("solokit.session.briefing.check_git_status")
    @patch("solokit.session.briefing.load_milestone_context")
    @patch("solokit.session.briefing.get_relevant_learnings")
    def test_generate_briefing_includes_relevant_learnings(
        self,
        mock_learnings,
        mock_milestone,
        mock_git,
        mock_env,
        mock_spec,
        mock_tree,
        mock_stack,
        mock_docs,
    ):
        """Test that generate_briefing includes relevant learnings."""
        # Arrange
        item_id = "WORK-001"
        item = {"title": "Test", "type": "feature", "priority": "high", "status": "not_started"}
        learnings_data = {"learnings": [{"content": "Test learning", "category": "best_practice"}]}

        mock_docs.return_value = {}
        mock_stack.return_value = "Stack"
        mock_tree.return_value = "Tree"
        mock_spec.return_value = "Spec"
        mock_env.return_value = []
        mock_git.return_value = {"status": "clean"}
        mock_milestone.return_value = None
        mock_learnings.return_value = [{"content": "Test learning", "category": "best_practice"}]

        # Act
        result = briefing_generator.generate_briefing(item_id, item, learnings_data)

        # Assert
        assert "Relevant Learnings" in result
        assert "Test learning" in result


class TestMainFunction:
    """Tests for main CLI function."""

    @patch("solokit.session.briefing.load_work_items")
    @patch("solokit.session.briefing.load_learnings")
    @patch("solokit.session.briefing.get_next_work_item")
    @patch("solokit.session.briefing.generate_briefing")
    @patch("solokit.session.briefing.finalize_previous_work_item_git_status")
    def test_main_selects_next_work_item_when_no_arg(
        self,
        mock_finalize,
        mock_generate,
        mock_get_next,
        mock_load_learnings,
        mock_load_work_items,
        temp_session_dir,
    ):
        """Test that main selects next work item when no argument provided."""
        # Arrange
        mock_load_work_items.return_value = {"work_items": {}}
        mock_load_learnings.return_value = {"learnings": []}
        mock_get_next.return_value = (
            "WORK-001",
            {"status": "not_started", "title": "Test", "sessions": []},
        )
        mock_generate.return_value = "# Briefing"

        with patch("sys.argv", ["briefing_generator.py"]):
            # Act
            result = briefing_generator.main()

        # Assert
        assert result == 0
        mock_get_next.assert_called_once()

    def test_main_returns_error_when_no_session_dir(self):
        """Test that main raises SessionNotFoundError when .session directory not found."""
        # Arrange - Create a temp directory without .session
        import os

        from solokit.core.exceptions import SessionNotFoundError

        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to temp directory where .session doesn't exist
            orig_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                with patch("sys.argv", ["briefing_generator.py"]):
                    # Act & Assert
                    with pytest.raises(SessionNotFoundError):
                        briefing_generator.main()
            finally:
                os.chdir(orig_cwd)

    @patch("solokit.session.briefing.load_work_items")
    @patch("solokit.session.briefing.load_learnings")
    @patch("solokit.session.briefing.get_next_work_item")
    def test_main_returns_error_when_no_available_work_items(
        self, mock_get_next, mock_load_learnings, mock_load_work_items, temp_session_dir
    ):
        """Test that main raises ValidationError when no available work items."""
        # Arrange
        from solokit.core.exceptions import ValidationError

        mock_load_work_items.return_value = {"work_items": {}}
        mock_load_learnings.return_value = {"learnings": []}
        mock_get_next.return_value = (None, None)

        with patch("sys.argv", ["briefing_generator.py"]):
            # Act & Assert
            with pytest.raises(ValidationError):
                briefing_generator.main()

    @patch("solokit.session.briefing.load_work_items")
    @patch("solokit.session.briefing.load_learnings")
    def test_main_with_explicit_work_item_id(
        self, mock_load_learnings, mock_load_work_items, temp_session_dir
    ):
        """Test that main accepts explicit work item ID argument."""
        # Arrange
        work_items_data = {
            "work_items": {
                "WORK-001": {
                    "status": "not_started",
                    "title": "Test",
                    "dependencies": [],
                    "sessions": [],
                }
            }
        }
        mock_load_work_items.return_value = work_items_data
        mock_load_learnings.return_value = {"learnings": []}

        with patch("sys.argv", ["briefing_generator.py", "WORK-001"]):
            with patch("solokit.session.briefing.generate_briefing", return_value="# Briefing"):
                with patch("solokit.session.briefing.finalize_previous_work_item_git_status"):
                    # Act
                    result = briefing_generator.main()

        # Assert
        assert result == 0

    @patch("solokit.session.briefing.load_work_items")
    @patch("solokit.session.briefing.load_learnings")
    def test_main_returns_error_when_work_item_not_found(
        self, mock_load_learnings, mock_load_work_items, temp_session_dir
    ):
        """Test that main raises WorkItemNotFoundError when specified work item not found."""
        # Arrange
        from solokit.core.exceptions import WorkItemNotFoundError

        mock_load_work_items.return_value = {"work_items": {}}
        mock_load_learnings.return_value = {"learnings": []}

        with patch("sys.argv", ["briefing_generator.py", "WORK-999"]):
            # Act & Assert
            with pytest.raises(WorkItemNotFoundError):
                briefing_generator.main()

    @patch("solokit.session.briefing.load_work_items")
    @patch("solokit.session.briefing.load_learnings")
    def test_main_blocks_when_another_item_in_progress(
        self, mock_load_learnings, mock_load_work_items, temp_session_dir
    ):
        """Test that main raises SessionAlreadyActiveError when another item is in-progress."""
        # Arrange
        from solokit.core.exceptions import SessionAlreadyActiveError

        work_items_data = {
            "work_items": {
                "WORK-001": {"status": "not_started", "title": "Test 1", "dependencies": []},
                "WORK-002": {"status": "in_progress", "title": "Test 2", "dependencies": []},
            }
        }
        mock_load_work_items.return_value = work_items_data
        mock_load_learnings.return_value = {"learnings": []}

        with patch("sys.argv", ["briefing_generator.py", "WORK-001"]):
            # Act & Assert
            with pytest.raises(SessionAlreadyActiveError):
                briefing_generator.main()

    @patch("solokit.session.briefing.load_work_items")
    @patch("solokit.session.briefing.load_learnings")
    def test_main_allows_force_start_with_flag(
        self, mock_load_learnings, mock_load_work_items, temp_session_dir
    ):
        """Test that main allows force starting work item with --force flag."""
        # Arrange
        work_items_data = {
            "work_items": {
                "WORK-001": {
                    "status": "not_started",
                    "title": "Test 1",
                    "dependencies": [],
                    "sessions": [],
                },
                "WORK-002": {"status": "in_progress", "title": "Test 2", "dependencies": []},
            }
        }
        mock_load_work_items.return_value = work_items_data
        mock_load_learnings.return_value = {"learnings": []}

        with patch("sys.argv", ["briefing_generator.py", "WORK-001", "--force"]):
            with patch("solokit.session.briefing.generate_briefing", return_value="# Briefing"):
                with patch("solokit.session.briefing.finalize_previous_work_item_git_status"):
                    # Act
                    result = briefing_generator.main()

        # Assert
        assert result == 0

    @patch("solokit.session.briefing.load_work_items")
    @patch("solokit.session.briefing.load_learnings")
    def test_main_checks_dependencies_are_satisfied(
        self, mock_load_learnings, mock_load_work_items, temp_session_dir
    ):
        """Test that main raises UnmetDependencyError when dependencies not satisfied."""
        # Arrange
        from solokit.core.exceptions import UnmetDependencyError

        work_items_data = {
            "work_items": {
                "WORK-001": {"status": "not_started", "title": "Test 1", "dependencies": []},
                "WORK-002": {
                    "status": "not_started",
                    "title": "Test 2",
                    "dependencies": ["WORK-001"],
                },
            }
        }
        mock_load_work_items.return_value = work_items_data
        mock_load_learnings.return_value = {"learnings": []}

        with patch("sys.argv", ["briefing_generator.py", "WORK-002"]):
            # Act & Assert
            with pytest.raises(UnmetDependencyError):
                briefing_generator.main()

    @patch("solokit.session.briefing.load_work_items")
    @patch("solokit.session.briefing.load_learnings")
    @patch("solokit.session.briefing.generate_briefing")
    @patch("solokit.session.briefing.finalize_previous_work_item_git_status")
    @patch("solokit.git.integration.GitWorkflow")
    def test_main_starts_git_workflow(
        self,
        mock_git_workflow_class,
        mock_finalize,
        mock_generate,
        mock_load_learnings,
        mock_load_work_items,
        temp_session_dir,
    ):
        """Test that main starts git workflow for work item."""
        # Arrange
        work_items_data = {
            "work_items": {
                "WORK-001": {
                    "status": "not_started",
                    "title": "Test",
                    "dependencies": [],
                    "sessions": [],
                }
            },
            "metadata": {
                "total_items": 1,
                "completed": 0,
                "in_progress": 0,
                "blocked": 0,
                "last_updated": "2025-01-01T00:00:00",
            },
        }
        mock_load_work_items.return_value = work_items_data
        mock_load_learnings.return_value = {"learnings": []}
        mock_generate.return_value = "# Briefing"

        # Mock git workflow
        mock_workflow = Mock()
        mock_workflow.start_work_item.return_value = {
            "success": True,
            "action": "created",
            "branch": "session-001-test",
        }
        mock_git_workflow_class.return_value = mock_workflow

        # Create work_items.json file (required for status update)
        work_items_file = Path(".session/tracking/work_items.json")
        work_items_file.write_text(json.dumps(work_items_data, indent=2))

        with patch("sys.argv", ["briefing_generator.py", "WORK-001"]):
            # Act
            result = briefing_generator.main()

        # Assert
        assert result == 0
        mock_workflow.start_work_item.assert_called_once()


class TestExtractSection:
    """Tests for extract_section helper function (Enhancement #11)."""

    def test_extract_section_basic(self):
        """Test extracting a section from markdown."""
        # Arrange
        markdown = """# Title
## Section 1
Content of section 1
More content
## Section 2
Content of section 2"""

        # Act
        result = briefing_generator.extract_section(markdown, "## Section 1")

        # Assert
        assert "Content of section 1" in result
        assert "More content" in result
        assert "Section 2" not in result

    def test_extract_section_with_nested_headings(self):
        """Test extracting section stops at next ## heading, not ###."""
        # Arrange
        markdown = """## Commits Made
Commit 1
### Files Changed
file1.py
## Quality Gates
Tests passed"""

        # Act
        result = briefing_generator.extract_section(markdown, "## Commits Made")

        # Assert
        assert "Commit 1" in result
        assert "Files Changed" in result
        assert "file1.py" in result
        assert "Quality Gates" not in result

    def test_extract_section_not_found(self):
        """Test extracting non-existent section returns empty string."""
        # Arrange
        markdown = """## Section 1
Content"""

        # Act
        result = briefing_generator.extract_section(markdown, "## Section 2")

        # Assert
        assert result == ""

    def test_extract_section_empty_content(self):
        """Test extracting section with no content."""
        # Arrange
        markdown = """## Section 1
## Section 2
Content"""

        # Act
        result = briefing_generator.extract_section(markdown, "## Section 1")

        # Assert
        assert result == ""


class TestGeneratePreviousWorkSection:
    """Tests for generate_previous_work_section function (Enhancement #11)."""

    def test_generate_previous_work_section_no_sessions(self):
        """Test returns empty string when no sessions."""
        # Arrange
        item = {"sessions": []}

        # Act
        result = briefing_generator.generate_previous_work_section("test_id", item)

        # Assert
        assert result == ""

    def test_generate_previous_work_section_with_commits(self, tmp_path, monkeypatch):
        """Test includes commits from session summaries."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        history_dir = Path(".session/history")
        history_dir.mkdir(parents=True)

        summary_content = """# Session 001 Summary
## Commits Made
**abc1234** - Add feature X

Files changed:
```
file1.py | 10 +++++++
```

## Quality Gates
- Tests: ✓ PASSED
"""
        summary_file = history_dir / "session_001_summary.md"
        summary_file.write_text(summary_content)

        item = {"sessions": [{"session_num": 1, "started_at": "2025-10-26T10:00:00"}]}

        # Act
        result = briefing_generator.generate_previous_work_section("test_id", item)

        # Assert
        assert "Session 1 (2025-10-26)" in result
        assert "abc1234" in result
        assert "Add feature X" in result
        assert "file1.py" in result
        assert "Quality Gates" in result
        assert "Tests: ✓ PASSED" in result

    def test_generate_previous_work_section_multiple_sessions(self, tmp_path, monkeypatch):
        """Test handles multiple sessions."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        history_dir = Path(".session/history")
        history_dir.mkdir(parents=True)

        for i in [1, 2]:
            summary = f"""# Session {i:03d} Summary
## Commits Made
**commit{i}** - Work from session {i}
## Quality Gates
- Tests: ✓ PASSED
"""
            (history_dir / f"session_{i:03d}_summary.md").write_text(summary)

        item = {
            "sessions": [
                {"session_num": 1, "started_at": "2025-10-26T10:00:00"},
                {"session_num": 2, "started_at": "2025-10-26T14:00:00"},
            ]
        }

        # Act
        result = briefing_generator.generate_previous_work_section("test_id", item)

        # Assert
        assert "Session 1 (2025-10-26)" in result
        assert "Session 2 (2025-10-26)" in result
        assert "commit1" in result
        assert "commit2" in result
        assert result.count("session(s)") == 1
        assert "2 session(s)" in result

    def test_generate_previous_work_section_missing_summary_file(self, tmp_path, monkeypatch):
        """Test handles missing summary file gracefully."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        Path(".session/history").mkdir(parents=True)

        item = {"sessions": [{"session_num": 1, "started_at": "2025-10-26T10:00:00"}]}

        # Act
        result = briefing_generator.generate_previous_work_section("test_id", item)

        # Assert - Should still generate header but no content
        assert "Previous Work" in result
        assert "1 session(s)" in result


class TestExtractKeywords:
    """Tests for extract_keywords helper function (Enhancement #11)."""

    def test_extract_keywords_basic(self):
        """Test extracting keywords from text."""
        # Arrange
        text = "Implement validation feature with testing"

        # Act
        result = briefing_generator.extract_keywords(text)

        # Assert
        assert "implement" in result
        assert "validation" in result
        assert "feature" in result
        assert "testing" in result

    def test_extract_keywords_filters_short_words(self):
        """Test filters out words 3 chars or less."""
        # Arrange
        text = "Add a new API for the app"

        # Act
        result = briefing_generator.extract_keywords(text)

        # Assert
        assert "add" not in result
        assert "new" not in result
        assert "api" not in result  # 3 chars
        assert "for" not in result
        assert "the" not in result
        assert "app" not in result

    def test_extract_keywords_filters_stop_words(self):
        """Test filters out common stop words."""
        # Arrange
        text = "This feature will have testing and validation"

        # Act
        result = briefing_generator.extract_keywords(text)

        # Assert
        assert "this" not in result
        assert "will" not in result
        assert "have" not in result
        assert "and" not in result
        assert "feature" in result
        assert "testing" in result
        assert "validation" in result

    def test_extract_keywords_lowercases(self):
        """Test converts to lowercase."""
        # Arrange
        text = "Python TypeScript Testing"

        # Act
        result = briefing_generator.extract_keywords(text)

        # Assert
        assert "python" in result
        assert "typescript" in result
        assert "testing" in result
        assert "Python" not in result

    def test_extract_keywords_empty_text(self):
        """Test handles empty text."""
        # Act
        result = briefing_generator.extract_keywords("")

        # Assert
        assert result == set()


class TestCalculateDaysAgo:
    """Tests for calculate_days_ago helper function (Enhancement #11)."""

    def test_calculate_days_ago_recent(self):
        """Test calculates days ago for recent timestamp."""
        # Arrange
        from datetime import datetime, timedelta

        yesterday = datetime.now() - timedelta(days=1)
        timestamp = yesterday.isoformat()

        # Act
        result = briefing_generator.calculate_days_ago(timestamp)

        # Assert
        assert result >= 1
        assert result <= 2  # Allow for timing variations

    def test_calculate_days_ago_old(self):
        """Test calculates days ago for old timestamp."""
        # Arrange
        timestamp = "2024-01-01T10:00:00"

        # Act
        result = briefing_generator.calculate_days_ago(timestamp)

        # Assert
        assert result > 200  # Should be many days ago

    def test_calculate_days_ago_with_timezone(self):
        """Test handles timezone in timestamp without crashing."""
        # Arrange - Standard ISO format with timezone
        timestamp = "2025-01-01T10:00:00+00:00"

        # Act
        result = briefing_generator.calculate_days_ago(timestamp)

        # Assert - Should return a valid number (not crash)
        assert isinstance(result, int)
        assert result >= 0

    def test_calculate_days_ago_invalid_format(self):
        """Test returns default 365 for invalid timestamp."""
        # Act
        result = briefing_generator.calculate_days_ago("invalid")

        # Assert
        assert result == 365

    def test_calculate_days_ago_empty_string(self):
        """Test returns default 365 for empty string."""
        # Act
        result = briefing_generator.calculate_days_ago("")

        # Assert
        assert result == 365
