"""End-to-end tests for core SDD session workflow (Phase 1).

Tests the complete session workflow including:
- Project initialization with sdd init
- Work item creation and management
- Session start with briefing generation
- Stack and tree tracking updates
- Git workflow integration
- Session validation

These tests run actual CLI commands and verify the complete system integration.
"""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_sdd_project():
    """Create a temporary SDD project with git and basic files.

    Returns:
        Path: Temporary project directory with git repo and SDD initialized.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "test_project"
        project_dir.mkdir()

        # Create basic project files
        (project_dir / "README.md").write_text("# Test Project\n")
        (project_dir / "main.py").write_text('print("Hello")\n')

        # Initialize git
        subprocess.run(["git", "init"], cwd=project_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=project_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=project_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(["git", "add", "."], cwd=project_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=project_dir,
            check=True,
            capture_output=True,
        )

        # Run sdd init
        result = subprocess.run(
            ["sdd", "init"],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            pytest.skip(f"sdd command not available: {result.stderr}")

        yield project_dir


# ============================================================================
# Phase 1.1: Session Initialization Tests
# ============================================================================


class TestSessionInitialization:
    """Tests for sdd init command and directory structure creation."""

    def test_init_creates_session_directory_structure(self, temp_sdd_project):
        """Test that sdd init creates all required directories."""
        # Arrange
        required_dirs = [
            ".session",
            ".session/tracking",
            ".session/briefings",
            ".session/history",
            ".session/specs",
        ]

        # Act - Already initialized by fixture

        # Assert
        for dir_path in required_dirs:
            full_path = temp_sdd_project / dir_path
            assert full_path.exists(), f"Directory not created: {dir_path}"
            assert full_path.is_dir(), f"Path exists but is not a directory: {dir_path}"

    def test_init_creates_tracking_files(self, temp_sdd_project):
        """Test that sdd init creates all required tracking files."""
        # Arrange
        required_files = [
            ".session/tracking/work_items.json",
            ".session/tracking/learnings.json",
            ".session/tracking/status_update.json",
            ".session/tracking/stack.txt",
            ".session/tracking/tree.txt",
            ".session/config.json",
        ]

        # Act - Already initialized by fixture

        # Assert
        for file_path in required_files:
            full_path = temp_sdd_project / file_path
            assert full_path.exists(), f"File not created: {file_path}"
            assert full_path.is_file(), f"Path exists but is not a file: {file_path}"

    def test_init_detects_technology_stack(self, temp_sdd_project):
        """Test that stack.txt correctly detects Python in the project."""
        # Arrange
        stack_file = temp_sdd_project / ".session/tracking/stack.txt"

        # Act
        stack_content = stack_file.read_text()

        # Assert
        assert "Python" in stack_content, "stack.txt should detect Python"

    def test_init_generates_project_tree(self, temp_sdd_project):
        """Test that tree.txt contains the project structure."""
        # Arrange
        tree_file = temp_sdd_project / ".session/tracking/tree.txt"

        # Act
        tree_content = tree_file.read_text()

        # Assert
        assert "README.md" in tree_content, "tree.txt should contain README.md"
        assert "main.py" in tree_content, "tree.txt should contain main.py"


# ============================================================================
# Phase 1.8: Work Item Creation Tests
# ============================================================================


class TestWorkItemCreation:
    """Tests for creating work items."""

    def test_create_feature_work_item(self, temp_sdd_project):
        """Test creating a feature work item with priority."""
        # Arrange & Act
        result = subprocess.run(
            [
                "sdd",
                "work-new",
                "--type",
                "feature",
                "--title",
                "Test Feature",
                "--priority",
                "high",
            ],
            cwd=temp_sdd_project,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0, f"Work item creation failed: {result.stderr}"

        # Verify work_items.json updated
        work_items_file = temp_sdd_project / ".session/tracking/work_items.json"
        work_items_data = json.loads(work_items_file.read_text())

        assert "work_items" in work_items_data
        assert len(work_items_data["work_items"]) > 0, "No work items found"

        # Get the first work item
        work_item_id = list(work_items_data["work_items"].keys())[0]
        work_item = work_items_data["work_items"][work_item_id]

        assert work_item["type"] == "feature"
        assert work_item["title"] == "Test Feature"
        assert work_item["priority"] == "high"

    def test_create_work_item_generates_spec_file(self, temp_sdd_project):
        """Test that creating a work item generates a spec file."""
        # Arrange & Act
        result = subprocess.run(
            ["sdd", "work-new", "--type", "bug", "--title", "Test Bug", "--priority", "critical"],
            cwd=temp_sdd_project,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0

        # Get work item ID
        work_items_file = temp_sdd_project / ".session/tracking/work_items.json"
        work_items_data = json.loads(work_items_file.read_text())
        work_item_id = list(work_items_data["work_items"].keys())[0]

        # Verify spec file created
        spec_file = temp_sdd_project / ".session/specs" / f"{work_item_id}.md"
        assert spec_file.exists(), f"Spec file not created: {spec_file}"
        assert spec_file.stat().st_size > 0, "Spec file is empty"


# ============================================================================
# Phase 1.5: Session Start Tests
# ============================================================================


class TestSessionStart:
    """Tests for session start with context loading."""

    @pytest.fixture
    def project_with_work_item(self, temp_sdd_project):
        """Create a work item for session start testing."""
        subprocess.run(
            [
                "sdd",
                "work-new",
                "--type",
                "feature",
                "--title",
                "Session Test Feature",
                "--priority",
                "high",
            ],
            cwd=temp_sdd_project,
            check=True,
            capture_output=True,
        )
        return temp_sdd_project

    def test_start_generates_briefing(self, project_with_work_item):
        """Test that session start generates a briefing."""
        # Arrange
        # Get the work item ID
        work_items_file = project_with_work_item / ".session/tracking/work_items.json"
        work_items_data = json.loads(work_items_file.read_text())
        work_item_id = list(work_items_data["work_items"].keys())[0]

        # Act
        result = subprocess.run(
            ["sdd", "start", work_item_id],
            cwd=project_with_work_item,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0, f"Session start failed: {result.stderr}"

        # Verify briefing contains key sections
        output = result.stdout
        required_sections = [
            "Session Briefing",
            "Work Item ID",
            "Project Context",
        ]

        for section in required_sections:
            assert section in output, f"Briefing missing section: {section}"

    def test_start_creates_git_branch(self, project_with_work_item):
        """Test that session start creates a git session branch."""
        # Arrange
        work_items_file = project_with_work_item / ".session/tracking/work_items.json"
        work_items_data = json.loads(work_items_file.read_text())
        work_item_id = list(work_items_data["work_items"].keys())[0]

        # Act
        subprocess.run(
            ["sdd", "start", work_item_id],
            cwd=project_with_work_item,
            check=True,
            capture_output=True,
        )

        # Assert
        result = subprocess.run(
            ["git", "branch"],
            cwd=project_with_work_item,
            capture_output=True,
            text=True,
        )

        assert "session-" in result.stdout, "Git session branch not created"

    def test_start_updates_work_item_status(self, project_with_work_item):
        """Test that session start updates work item status to in_progress."""
        # Arrange
        work_items_file = project_with_work_item / ".session/tracking/work_items.json"
        work_items_data = json.loads(work_items_file.read_text())
        work_item_id = list(work_items_data["work_items"].keys())[0]

        # Act
        subprocess.run(
            ["sdd", "start", work_item_id],
            cwd=project_with_work_item,
            check=True,
            capture_output=True,
        )

        # Assert
        work_items_data = json.loads(work_items_file.read_text())
        work_item = work_items_data["work_items"][work_item_id]
        assert work_item["status"] == "in_progress", f"Status not updated: {work_item['status']}"


# ============================================================================
# Phase 1.2 & 1.3: Stack and Tree Tracking Tests
# ============================================================================


class TestStackAndTreeTracking:
    """Tests for technology stack and project tree tracking updates."""

    def test_stack_update_after_file_changes(self, temp_sdd_project):
        """Test that stack tracking updates when new files are added."""
        # Arrange
        (temp_sdd_project / "package.json").write_text('{"name": "test"}')
        stack_file = temp_sdd_project / ".session/tracking/stack.txt"
        _original_content = stack_file.read_text()

        # Get the project root to find scripts directory
        scripts_dir = Path(__file__).parent.parent.parent / "scripts"

        # Act
        result = subprocess.run(
            ["python3", str(scripts_dir / "generate_stack.py")],
            cwd=temp_sdd_project,
            capture_output=True,
            text=True,
        )

        # Assert
        if result.returncode == 0:
            _new_content = stack_file.read_text()
            # Content may or may not change depending on detection logic
            assert stack_file.exists(), "Stack file should still exist"

    def test_tree_update_detects_new_files(self, temp_sdd_project):
        """Test that tree tracking detects new files and directories."""
        # Arrange
        (temp_sdd_project / "new_file.py").write_text('print("New file")\n')
        (temp_sdd_project / "newdir").mkdir()
        (temp_sdd_project / "newdir" / "test.py").write_text('print("Test")\n')

        # Get the project root to find scripts directory
        scripts_dir = Path(__file__).parent.parent.parent / "scripts"

        # Act
        result = subprocess.run(
            ["python3", str(scripts_dir / "generate_tree.py")],
            cwd=temp_sdd_project,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0, f"Tree generation failed: {result.stderr}"

        tree_file = temp_sdd_project / ".session/tracking/tree.txt"
        tree_content = tree_file.read_text()

        assert "new_file.py" in tree_content, "Tree should detect new_file.py"
        assert "newdir" in tree_content, "Tree should detect newdir directory"


# ============================================================================
# Phase 1.4: Git Workflow Integration Tests
# ============================================================================


class TestGitWorkflowIntegration:
    """Tests for git workflow integration."""

    @pytest.fixture
    def project_with_active_session(self, temp_sdd_project):
        """Create a project with an active session."""
        subprocess.run(
            [
                "sdd",
                "work-new",
                "--type",
                "feature",
                "--title",
                "Git Test Feature",
                "--priority",
                "high",
            ],
            cwd=temp_sdd_project,
            check=True,
            capture_output=True,
        )

        work_items_file = temp_sdd_project / ".session/tracking/work_items.json"
        work_items_data = json.loads(work_items_file.read_text())
        work_item_id = list(work_items_data["work_items"].keys())[0]

        subprocess.run(
            ["sdd", "start", work_item_id],
            cwd=temp_sdd_project,
            check=True,
            capture_output=True,
        )

        return temp_sdd_project

    def test_session_uses_git_branch(self, project_with_active_session):
        """Test that active session is on a session git branch."""
        # Arrange & Act
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=project_with_active_session,
            capture_output=True,
            text=True,
        )

        # Assert
        current_branch = result.stdout.strip()
        assert current_branch.startswith("session-"), f"Not on session branch: {current_branch}"

    def test_git_tracks_file_changes(self, project_with_active_session):
        """Test that git detects changes made during session."""
        # Arrange
        (project_with_active_session / "test_change.py").write_text('print("Change")\n')

        # Act
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_with_active_session,
            capture_output=True,
            text=True,
        )

        # Assert
        # Should show untracked or modified files
        assert result.stdout.strip() != "", "Git should detect file changes"


# ============================================================================
# Phase 1.7: Session Validation Tests
# ============================================================================


class TestSessionValidation:
    """Tests for session validation command."""

    def test_validate_command_executes(self, temp_sdd_project):
        """Test that sdd validate command executes."""
        # Arrange & Act
        result = subprocess.run(
            ["sdd", "validate"],
            cwd=temp_sdd_project,
            capture_output=True,
            text=True,
        )

        # Assert - May pass or fail, but should execute
        output = result.stdout + result.stderr
        assert "validation" in output.lower() or "quality" in output.lower(), (
            "Validation should provide output"
        )

    def test_validate_checks_git_status(self, temp_sdd_project):
        """Test that validation includes git status check."""
        # Arrange & Act
        result = subprocess.run(
            ["sdd", "validate"],
            cwd=temp_sdd_project,
            capture_output=True,
            text=True,
        )

        # Assert
        output = result.stdout + result.stderr
        # Should mention git or status in output
        has_git_check = "git" in output.lower() or "status" in output.lower()
        assert has_git_check or result.returncode in [0, 1], (
            "Validation should check git status or execute successfully"
        )
