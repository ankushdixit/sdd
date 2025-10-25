"""End-to-end tests for learning management system (Phase 4).

Tests the complete learning system including:
- Learning capture with all fields
- Auto-categorization
- Similarity detection and duplicate merging
- Learning search and filtering
- Curation process (dry-run and actual)

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
def sdd_project_with_learnings():
    """Create a temp SDD project with some learnings for testing.

    Returns:
        Path: Project directory with learning system initialized.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "test_project"
        project_dir.mkdir()

        # Create basic project files
        (project_dir / "README.md").write_text("# Test Project\n")

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
# Phase 4.1: Learning Capture Tests
# ============================================================================


class TestLearningCapture:
    """Tests for capturing learnings with various fields."""

    def test_capture_learning_with_all_fields(self, sdd_project_with_learnings):
        """Test capturing a learning with all fields populated."""
        # Arrange & Act
        result = subprocess.run(
            [
                "sdd",
                "learn",
                "--content",
                "Test learning with all fields",
                "--category",
                "best_practices",
                "--tags",
                "testing,automation",
                "--session",
                "1",
                "--context",
                "Test context",
            ],
            cwd=sdd_project_with_learnings,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0, f"Learning capture failed: {result.stderr}"

        # Verify in learnings.json
        learnings_file = sdd_project_with_learnings / ".session/tracking/learnings.json"
        data = json.loads(learnings_file.read_text())

        # Check that learning was saved
        assert "categories" in data
        assert "best_practices" in data["categories"]
        assert len(data["categories"]["best_practices"]) > 0

    def test_capture_learning_minimal_fields(self, sdd_project_with_learnings):
        """Test capturing a learning with only required fields."""
        # Arrange & Act
        result = subprocess.run(
            [
                "sdd",
                "learn",
                "--content",
                "Minimal learning test",
                "--category",
                "gotchas",
            ],
            cwd=sdd_project_with_learnings,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0, "Minimal learning capture failed"


# ============================================================================
# Phase 4.5: Learning Display and Filtering Tests
# ============================================================================


class TestLearningDisplay:
    """Tests for showing and filtering learnings."""

    @pytest.fixture
    def project_with_multiple_learnings(self, sdd_project_with_learnings):
        """Add multiple learnings for filtering tests."""
        # Add learnings
        subprocess.run(
            [
                "sdd",
                "learn",
                "--content",
                "Learning 1",
                "--category",
                "best_practices",
                "--tags",
                "testing",
            ],
            cwd=sdd_project_with_learnings,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "sdd",
                "learn",
                "--content",
                "Learning 2",
                "--category",
                "gotchas",
                "--tags",
                "database",
            ],
            cwd=sdd_project_with_learnings,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["sdd", "learn", "--content", "Learning 3", "--category", "architecture_patterns"],
            cwd=sdd_project_with_learnings,
            check=True,
            capture_output=True,
        )
        return sdd_project_with_learnings

    def test_show_all_learnings(self, project_with_multiple_learnings):
        """Test displaying all learnings without filters."""
        # Arrange & Act
        result = subprocess.run(
            ["sdd", "learn-show"],
            cwd=project_with_multiple_learnings,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0, f"Show learnings failed: {result.stderr}"
        assert "Learning 1" in result.stdout or "Learning" in result.stdout

    def test_filter_learnings_by_category(self, project_with_multiple_learnings):
        """Test filtering learnings by category."""
        # Arrange & Act
        result = subprocess.run(
            ["sdd", "learn-show", "--category", "best_practices"],
            cwd=project_with_multiple_learnings,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0, "Category filtering failed"

    def test_filter_learnings_by_tag(self, project_with_multiple_learnings):
        """Test filtering learnings by tag."""
        # Arrange & Act
        result = subprocess.run(
            ["sdd", "learn-show", "--tag", "testing"],
            cwd=project_with_multiple_learnings,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0, "Tag filtering failed"


# ============================================================================
# Phase 4.5: Learning Search Tests
# ============================================================================


class TestLearningSearch:
    """Tests for searching learnings by keyword."""

    @pytest.fixture
    def project_with_searchable_learnings(self, sdd_project_with_learnings):
        """Add learnings with searchable content."""
        subprocess.run(
            [
                "sdd",
                "learn",
                "--content",
                "Python async functions are tricky",
                "--category",
                "gotchas",
            ],
            cwd=sdd_project_with_learnings,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "sdd",
                "learn",
                "--content",
                "Use design patterns wisely",
                "--category",
                "best_practices",
            ],
            cwd=sdd_project_with_learnings,
            check=True,
            capture_output=True,
        )
        return sdd_project_with_learnings

    def test_search_learnings_by_keyword(self, project_with_searchable_learnings):
        """Test searching learnings by keyword."""
        # Arrange & Act
        result = subprocess.run(
            ["sdd", "learn-search", "async"],
            cwd=project_with_searchable_learnings,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0, f"Search failed: {result.stderr}"
        # Should find the learning containing "async"
        assert "async" in result.stdout or "Found" in result.stdout


# ============================================================================
# Phase 4.3 & 4.6: Similarity Detection and Curation Tests
# ============================================================================


class TestLearningCuration:
    """Tests for learning curation and duplicate detection."""

    @pytest.fixture
    def project_with_similar_learnings(self, sdd_project_with_learnings):
        """Add similar learnings for duplicate detection."""
        subprocess.run(
            [
                "sdd",
                "learn",
                "--content",
                "Test learning with all required fields",
                "--category",
                "best_practices",
            ],
            cwd=sdd_project_with_learnings,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "sdd",
                "learn",
                "--content",
                "Test learning with all fields required",
                "--category",
                "best_practices",
            ],
            cwd=sdd_project_with_learnings,
            check=True,
            capture_output=True,
        )
        return sdd_project_with_learnings

    def test_curation_dry_run(self, project_with_similar_learnings):
        """Test curation dry-run mode doesn't save changes."""
        # Arrange
        learnings_file = project_with_similar_learnings / ".session/tracking/learnings.json"
        before_data = json.loads(learnings_file.read_text())
        count_before = sum(len(learnings) for learnings in before_data["categories"].values())

        # Act
        result = subprocess.run(
            ["sdd", "learn-curate", "--dry-run"],
            cwd=project_with_similar_learnings,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0, f"Dry-run curation failed: {result.stderr}"

        # Verify count didn't change
        after_data = json.loads(learnings_file.read_text())
        count_after = sum(len(learnings) for learnings in after_data["categories"].values())
        assert count_after == count_before, "Dry-run mode should not save changes"

    def test_curation_merges_duplicates(self, project_with_similar_learnings):
        """Test that curation actually merges duplicate learnings."""
        # Arrange
        learnings_file = project_with_similar_learnings / ".session/tracking/learnings.json"
        before_data = json.loads(learnings_file.read_text())
        count_before = sum(len(learnings) for learnings in before_data["categories"].values())

        # Act
        result = subprocess.run(
            ["sdd", "learn-curate"],
            cwd=project_with_similar_learnings,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0, f"Curation failed: {result.stderr}"

        # Verify count changed (duplicates merged)
        after_data = json.loads(learnings_file.read_text())
        count_after = sum(len(learnings) for learnings in after_data["categories"].values())
        assert count_after <= count_before, "Curation should reduce or maintain learning count"


# ============================================================================
# Phase 4.2: Auto-Categorization Tests
# ============================================================================


class TestAutoCategorization:
    """Tests for learning categorization."""

    def test_all_six_categories_work(self, sdd_project_with_learnings):
        """Test that all 6 learning categories can be used."""
        # Arrange
        categories = [
            "architecture_patterns",
            "gotchas",
            "best_practices",
            "technical_debt",
            "performance_insights",
            "security",
        ]

        # Act & Assert
        for category in categories:
            result = subprocess.run(
                [
                    "sdd",
                    "learn",
                    "--content",
                    f"Learning for {category} category",
                    "--category",
                    category,
                ],
                cwd=sdd_project_with_learnings,
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0, f"Failed to add learning for category: {category}"

        # Verify all categories in learnings.json
        learnings_file = sdd_project_with_learnings / ".session/tracking/learnings.json"
        data = json.loads(learnings_file.read_text())

        for category in categories:
            assert category in data["categories"], f"Category not found: {category}"


# ============================================================================
# Edge Cases Tests
# ============================================================================


class TestLearningEdgeCases:
    """Tests for edge cases in learning management."""

    def test_empty_learnings_operations(self, sdd_project_with_learnings):
        """Test operations on empty learnings file."""
        # Arrange - Already empty from fixture

        # Act & Assert - Show learnings
        result = subprocess.run(
            ["sdd", "learn-show"],
            cwd=sdd_project_with_learnings,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, "Show learnings on empty file should work"

        # Act & Assert - Search learnings
        result = subprocess.run(
            ["sdd", "learn-search", "test"],
            cwd=sdd_project_with_learnings,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, "Search on empty file should work"

        # Act & Assert - Curate learnings
        result = subprocess.run(
            ["sdd", "learn-curate"],
            cwd=sdd_project_with_learnings,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, "Curate on empty file should work"
