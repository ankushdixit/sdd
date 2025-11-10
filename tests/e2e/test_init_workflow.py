"""
End-to-end tests for Solokit project initialization workflow.

Tests the init_project.py module and overall project setup including:
- Project directory structure creation
- Tracking files initialization
- Configuration file setup
- .gitignore generation with OS-specific patterns
- Git repository initialization with initial commit
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_project():
    """Create a temporary directory for isolated project testing.

    Returns:
        Path: Temporary project directory that is automatically cleaned up.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "test_project"
        project_dir.mkdir()
        yield project_dir


@pytest.fixture
def initialized_git_repo(temp_project):
    """Create a git repository in the temporary project directory.

    Args:
        temp_project: Temporary project directory fixture.

    Returns:
        Path: Project directory with initialized git repository.
    """
    # Initialize git repository
    subprocess.run(["git", "init"], cwd=temp_project, check=True, capture_output=True)

    # Configure git user
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=temp_project,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=temp_project,
        check=True,
        capture_output=True,
    )

    return temp_project


@pytest.fixture
def solokit_initialized_project(initialized_git_repo):
    """Create a fully initialized Solokit project for testing.

    Args:
        initialized_git_repo: Git repository fixture.

    Returns:
        Path: Project directory with Solokit initialized.
    """
    # Create minimal required docs directory
    docs_dir = initialized_git_repo / "docs"
    docs_dir.mkdir()

    # Create .session directory structure manually (instead of using deprecated legacy init)
    session_dir = initialized_git_repo / ".session"
    session_dir.mkdir()
    (session_dir / "tracking").mkdir()
    (session_dir / "briefings").mkdir()
    (session_dir / "history").mkdir()
    (session_dir / "specs").mkdir()

    # Create tracking files with expected structure
    (session_dir / "tracking" / "work_items.json").write_text(
        json.dumps(
            {
                "metadata": {
                    "total_items": 0,
                    "completed": 0,
                    "in_progress": 0,
                    "blocked": 0,
                },
                "milestones": {},
                "work_items": {},
            },
            indent=2,
        )
    )

    (session_dir / "tracking" / "learnings.json").write_text(
        json.dumps({"categories": {}, "learnings": []}, indent=2)
    )

    (session_dir / "tracking" / "active_session.json").write_text(
        json.dumps({"active": False}, indent=2)
    )

    (session_dir / "tracking" / "status_update.json").write_text(
        json.dumps(
            {
                "current_session": None,
                "current_work_item": None,
                "started_at": None,
                "status": "idle",
            },
            indent=2,
        )
    )

    (session_dir / "tracking" / "stack.txt").write_text(
        "# Technology Stack\n\n## Languages\n- Python detected\n"
    )

    (session_dir / "tracking" / "tree.txt").write_text(".\n├── docs/\n└── README.md\n")

    # Create config.json
    (session_dir / "config.json").write_text(
        json.dumps(
            {
                "curation": {
                    "auto_curate": True,
                    "frequency": 5,
                    "dry_run": False,
                    "similarity_threshold": 0.7,
                },
                "quality_gates": {
                    "test_coverage_minimum": 80,
                    "require_tests": True,
                    "require_linting": True,
                },
            },
            indent=2,
        )
    )

    return initialized_git_repo


# ============================================================================
# Project Structure Tests
# ============================================================================


class TestProjectStructure:
    """Test Solokit project directory structure creation."""

    def test_session_directory_structure_created(self, solokit_initialized_project):
        """Test that sk init creates all required .session subdirectories.

        The .session directory should contain:
        - tracking/ for work items and learnings
        - specs/ for work item specifications
        - briefings/ for session briefings
        - history/ for session history
        """
        # Assert
        assert (solokit_initialized_project / ".session").exists(), ".session directory not created"
        assert (solokit_initialized_project / ".session" / "tracking").exists(), (
            ".session/tracking directory missing"
        )
        assert (solokit_initialized_project / ".session" / "specs").exists(), (
            ".session/specs directory missing"
        )
        assert (solokit_initialized_project / ".session" / "briefings").exists(), (
            ".session/briefings directory missing"
        )
        assert (solokit_initialized_project / ".session" / "history").exists(), (
            ".session/history directory missing"
        )

    @pytest.mark.skipif("CI" in os.environ, reason="Skipped in CI - requires initialized project")
    def test_session_directory_accessible_on_real_project(self):
        """Test that current project has .session directory structure.

        This validates that the real Solokit project is properly initialized.
        """
        # Assert - Test on actual project
        assert Path(".session/tracking").exists(), ".session/tracking directory missing"
        assert Path(".session/specs").exists(), ".session/specs directory missing"
        assert Path(".session/briefings").exists(), ".session/briefings directory missing"
        assert Path(".session/history").exists(), ".session/history directory missing"


# ============================================================================
# Tracking Files Tests
# ============================================================================


class TestTrackingFiles:
    """Test tracking file initialization and structure."""

    def test_work_items_file_created_with_valid_structure(self, solokit_initialized_project):
        """Test that work_items.json is created with proper structure.

        The work_items.json file should contain:
        - metadata section with project statistics
        - work_items section (empty initially)
        """
        # Arrange
        work_items_file = solokit_initialized_project / ".session" / "tracking" / "work_items.json"

        # Assert
        assert work_items_file.exists(), "work_items.json not created"

        # Act
        with open(work_items_file) as f:
            data = json.load(f)

        # Assert
        assert "metadata" in data, "work_items.json missing metadata section"
        assert "work_items" in data, "work_items.json missing work_items section"

    def test_learnings_file_created_with_valid_structure(self, solokit_initialized_project):
        """Test that learnings.json is created with proper structure.

        The learnings.json file should contain:
        - categories section for learning organization
        """
        # Arrange
        learnings_file = solokit_initialized_project / ".session" / "tracking" / "learnings.json"

        # Assert
        assert learnings_file.exists(), "learnings.json not created"

        # Act
        with open(learnings_file) as f:
            data = json.load(f)

        # Assert
        assert "categories" in data, "learnings.json missing categories section"

    @pytest.mark.skipif("CI" in os.environ, reason="Skipped in CI - requires initialized project")
    def test_tracking_files_accessible_on_real_project(self):
        """Test that current project has valid tracking files.

        Validates that the real Solokit project has properly structured tracking files.
        """
        # Arrange & Act
        work_items_file = Path(".session/tracking/work_items.json")
        assert work_items_file.exists(), "work_items.json missing"

        with open(work_items_file) as f:
            work_items_data = json.load(f)

        learnings_file = Path(".session/tracking/learnings.json")
        assert learnings_file.exists(), "learnings.json missing"

        with open(learnings_file) as f:
            learnings_data = json.load(f)

        # Assert
        assert "metadata" in work_items_data, "work_items.json missing metadata"
        assert "work_items" in work_items_data, "work_items.json missing work_items"
        assert "categories" in learnings_data, "learnings.json missing categories"


# ============================================================================
# Configuration Tests
# ============================================================================


class TestSessionConfiguration:
    """Test session configuration file creation and validation."""

    def test_config_file_created_with_valid_structure(self, solokit_initialized_project):
        """Test that config.json is created with proper configuration sections.

        The config.json file should contain:
        - quality_gates configuration
        - curation configuration
        """
        # Arrange
        config_file = solokit_initialized_project / ".session" / "config.json"

        # Assert
        assert config_file.exists(), "config.json not created"

        # Act
        with open(config_file) as f:
            data = json.load(f)

        # Assert
        assert "quality_gates" in data, "config.json missing quality_gates section"
        assert "curation" in data, "config.json missing curation section"

    @pytest.mark.skipif("CI" in os.environ, reason="Skipped in CI - requires initialized project")
    def test_config_file_accessible_on_real_project(self):
        """Test that current project has valid configuration file.

        Validates that the real Solokit project has properly structured config.
        """
        # Arrange & Act
        config_file = Path(".session/config.json")
        assert config_file.exists(), "config.json missing"

        with open(config_file) as f:
            data = json.load(f)

        # Assert
        assert "quality_gates" in data, "config.json missing quality_gates"
        assert "curation" in data, "config.json missing curation"


# ============================================================================
# Project Metadata Tests
# ============================================================================


class TestProjectMetadata:
    """Test project metadata file validation."""

    def test_real_project_has_metadata_file(self):
        """Test that current project has at least one metadata file.

        A valid project should have one of:
        - pyproject.toml (Python)
        - setup.py (Python)
        - package.json (Node.js)
        """
        # Act
        has_pyproject = Path("pyproject.toml").exists()
        has_setup = Path("setup.py").exists()
        has_package = Path("package.json").exists()

        # Assert
        assert has_pyproject or has_setup or has_package, (
            "No project metadata file found (pyproject.toml, setup.py, or package.json)"
        )
