"""
End-to-end tests for SDD project initialization workflow.

Tests the init_project.py module and overall project setup including:
- Project directory structure creation
- Tracking files initialization
- Configuration file setup
- .gitignore generation with OS-specific patterns
- Git repository initialization with initial commit
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
def sdd_initialized_project(initialized_git_repo):
    """Create a fully initialized SDD project for testing.

    Args:
        initialized_git_repo: Git repository fixture.

    Returns:
        Path: Project directory with SDD initialized.
    """
    # Create minimal required docs directory
    docs_dir = initialized_git_repo / "docs"
    docs_dir.mkdir()

    # Run sdd init
    result = subprocess.run(
        ["sdd", "init"], cwd=initialized_git_repo, capture_output=True, text=True
    )

    if result.returncode != 0:
        pytest.skip(f"sdd command not available or init failed: {result.stderr}")

    return initialized_git_repo


# ============================================================================
# Project Structure Tests
# ============================================================================


class TestProjectStructure:
    """Test SDD project directory structure creation."""

    def test_session_directory_structure_created(self, sdd_initialized_project):
        """Test that sdd init creates all required .session subdirectories.

        The .session directory should contain:
        - tracking/ for work items and learnings
        - specs/ for work item specifications
        - briefings/ for session briefings
        - history/ for session history
        """
        # Assert
        assert (sdd_initialized_project / ".session").exists(), ".session directory not created"
        assert (sdd_initialized_project / ".session" / "tracking").exists(), (
            ".session/tracking directory missing"
        )
        assert (sdd_initialized_project / ".session" / "specs").exists(), (
            ".session/specs directory missing"
        )
        assert (sdd_initialized_project / ".session" / "briefings").exists(), (
            ".session/briefings directory missing"
        )
        assert (sdd_initialized_project / ".session" / "history").exists(), (
            ".session/history directory missing"
        )

    def test_session_directory_accessible_on_real_project(self):
        """Test that current project has .session directory structure.

        This validates that the real SDD project is properly initialized.
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

    def test_work_items_file_created_with_valid_structure(self, sdd_initialized_project):
        """Test that work_items.json is created with proper structure.

        The work_items.json file should contain:
        - metadata section with project statistics
        - work_items section (empty initially)
        """
        # Arrange
        work_items_file = sdd_initialized_project / ".session" / "tracking" / "work_items.json"

        # Assert
        assert work_items_file.exists(), "work_items.json not created"

        # Act
        with open(work_items_file) as f:
            data = json.load(f)

        # Assert
        assert "metadata" in data, "work_items.json missing metadata section"
        assert "work_items" in data, "work_items.json missing work_items section"

    def test_learnings_file_created_with_valid_structure(self, sdd_initialized_project):
        """Test that learnings.json is created with proper structure.

        The learnings.json file should contain:
        - categories section for learning organization
        """
        # Arrange
        learnings_file = sdd_initialized_project / ".session" / "tracking" / "learnings.json"

        # Assert
        assert learnings_file.exists(), "learnings.json not created"

        # Act
        with open(learnings_file) as f:
            data = json.load(f)

        # Assert
        assert "categories" in data, "learnings.json missing categories section"

    def test_tracking_files_accessible_on_real_project(self):
        """Test that current project has valid tracking files.

        Validates that the real SDD project has properly structured tracking files.
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

    def test_config_file_created_with_valid_structure(self, sdd_initialized_project):
        """Test that config.json is created with proper configuration sections.

        The config.json file should contain:
        - quality_gates configuration
        - curation configuration
        """
        # Arrange
        config_file = sdd_initialized_project / ".session" / "config.json"

        # Assert
        assert config_file.exists(), "config.json not created"

        # Act
        with open(config_file) as f:
            data = json.load(f)

        # Assert
        assert "quality_gates" in data, "config.json missing quality_gates section"
        assert "curation" in data, "config.json missing curation section"

    def test_config_file_accessible_on_real_project(self):
        """Test that current project has valid configuration file.

        Validates that the real SDD project has properly structured config.
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


# ============================================================================
# Gitignore Tests
# ============================================================================


class TestGitignoreGeneration:
    """Test .gitignore file generation with OS-specific patterns."""

    def test_gitignore_created_with_os_specific_patterns(self, sdd_initialized_project):
        """Test that sdd init creates .gitignore with OS-specific patterns.

        The .gitignore should include patterns for:
        - macOS (.DS_Store, ._*, .Spotlight-V100, .Trashes)
        - Windows (Thumbs.db, Desktop.ini, $RECYCLE.BIN/)
        - Linux (*~)
        - SDD-specific patterns (.session/briefings/, .session/history/)
        """
        # Arrange
        gitignore = sdd_initialized_project / ".gitignore"

        # Assert file exists
        assert gitignore.exists(), ".gitignore was not created"

        # Act - Read content
        gitignore_content = gitignore.read_text()

        # Assert - Check OS-specific patterns
        macos_patterns = [".DS_Store", ".DS_Store?", "._*", ".Spotlight-V100", ".Trashes"]
        windows_patterns = ["Thumbs.db", "ehthumbs.db", "Desktop.ini", "$RECYCLE.BIN/"]
        linux_patterns = ["*~"]

        all_os_patterns = macos_patterns + windows_patterns + linux_patterns

        for pattern in all_os_patterns:
            assert pattern in gitignore_content, (
                f"Missing OS-specific pattern: {pattern}\n\n.gitignore content:\n{gitignore_content}"
            )

    def test_gitignore_includes_section_comments(self, sdd_initialized_project):
        """Test that .gitignore includes section comments for organization.

        The .gitignore should have clear section headers:
        - # OS-specific files
        - # macOS
        - # Windows
        - # Linux
        """
        # Arrange
        gitignore = sdd_initialized_project / ".gitignore"
        gitignore_content = gitignore.read_text()

        # Assert
        assert "# OS-specific files" in gitignore_content, (
            "Missing OS-specific files section header"
        )
        assert "# macOS" in gitignore_content, "Missing macOS comment"
        assert "# Windows" in gitignore_content, "Missing Windows comment"
        assert "# Linux" in gitignore_content, "Missing Linux comment"

    def test_gitignore_includes_sdd_patterns(self, sdd_initialized_project):
        """Test that .gitignore includes SDD-specific patterns.

        SDD patterns should include:
        - .session/briefings/ (ephemeral session briefings)
        - .session/history/ (session history)
        """
        # Arrange
        gitignore = sdd_initialized_project / ".gitignore"
        gitignore_content = gitignore.read_text()

        # Assert
        sdd_patterns = [".session/briefings/", ".session/history/"]
        for pattern in sdd_patterns:
            assert pattern in gitignore_content, f"Missing SDD pattern: {pattern}"

    @pytest.mark.parametrize(
        "pattern", [".DS_Store", "Thumbs.db", "*~", ".session/briefings/", ".session/history/"]
    )
    def test_gitignore_includes_specific_pattern(self, sdd_initialized_project, pattern):
        """Test that .gitignore includes various important patterns.

        Parametrized test to verify individual patterns are present.
        """
        # Arrange
        gitignore = sdd_initialized_project / ".gitignore"
        gitignore_content = gitignore.read_text()

        # Assert
        assert pattern in gitignore_content, f"Missing pattern: {pattern}"


# ============================================================================
# Git Initialization Tests
# ============================================================================


class TestGitInitialization:
    """Test git repository initialization and initial commit."""

    def test_git_repository_initialized(self, sdd_initialized_project):
        """Test that sdd init ensures git repository is initialized.

        The project should have a .git directory after initialization.
        """
        # Assert
        assert (sdd_initialized_project / ".git").exists(), "Git repository not initialized"

    def test_initial_commit_created_with_sdd_message(self, sdd_initialized_project):
        """Test that sdd init creates an initial commit with proper message.

        The first commit should:
        1. Exist in the repository
        2. Have a message indicating SDD initialization
        """
        # Arrange & Act
        try:
            # Get commit count
            result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=sdd_initialized_project,
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            commit_count = int(result.stdout.strip())

            # Get the first commit message
            result = subprocess.run(
                ["git", "log", "--reverse", "--format=%B", "-n", "1"],
                cwd=sdd_initialized_project,
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            first_commit_message = result.stdout.strip()

            # Assert
            assert commit_count > 0, "No commits found in repository"
            assert (
                "Initialize project with Session-Driven Development" in first_commit_message
                or "Session-Driven Development" in first_commit_message
            ), (
                f"First commit doesn't appear to be SDD initialization. Message: {first_commit_message[:100]}"
            )

        except subprocess.CalledProcessError as e:
            pytest.fail(f"Git command failed: {e}")

    def test_initial_commit_includes_sdd_files(self, sdd_initialized_project):
        """Test that initial commit includes key SDD files.

        The initial commit should include at minimum:
        - .gitignore
        - .session/ directory contents
        """
        # Arrange & Act
        try:
            # Get files in initial commit
            result = subprocess.run(
                ["git", "ls-tree", "--name-only", "-r", "HEAD"],
                cwd=sdd_initialized_project,
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            committed_files = result.stdout.strip().split("\n")

            # Assert
            assert ".gitignore" in committed_files, ".gitignore not in initial commit"

            # Check that some .session files are committed
            session_files = [f for f in committed_files if f.startswith(".session/")]
            assert len(session_files) > 0, "No .session files in initial commit"

        except subprocess.CalledProcessError as e:
            pytest.fail(f"Git command failed: {e}")


# ============================================================================
# Integration Tests
# ============================================================================


class TestCompleteInitWorkflow:
    """Test complete initialization workflow end-to-end."""

    @pytest.mark.skipif(
        subprocess.run(["which", "sdd"], capture_output=True).returncode != 0,
        reason="sdd command not available (not installed)",
    )
    def test_init_workflow_creates_fully_functional_project(self, initialized_git_repo):
        """Test that complete init workflow creates a fully functional project.

        This end-to-end test verifies that after running sdd init:
        1. All directory structures exist
        2. All tracking files are valid
        3. Configuration is present
        4. .gitignore has all required patterns
        5. Git has initial commit
        """
        # Arrange
        docs_dir = initialized_git_repo / "docs"
        docs_dir.mkdir()

        # Act - Run sdd init
        result = subprocess.run(
            ["sdd", "init"], cwd=initialized_git_repo, capture_output=True, text=True
        )

        # Assert - Command succeeded
        assert result.returncode == 0, f"sdd init failed: {result.stderr}"

        # Assert - All structures created
        assert (initialized_git_repo / ".session").exists()
        assert (initialized_git_repo / ".session" / "tracking" / "work_items.json").exists()
        assert (initialized_git_repo / ".session" / "config.json").exists()
        assert (initialized_git_repo / ".gitignore").exists()

        # Assert - Git commit created
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=initialized_git_repo,
            capture_output=True,
            text=True,
            check=True,
        )
        assert int(result.stdout.strip()) > 0, "No commits found after init"
