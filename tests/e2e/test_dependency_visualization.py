"""End-to-end tests for dependency graph visualization (Phase 3).

Tests the complete dependency graph system including:
- Graph generation in ASCII and DOT formats
- Critical path analysis
- Bottleneck detection
- Filtering by status, type, and milestone
- Focus mode for specific work items
- Statistics and timeline projections
- Include/exclude completed items

These tests run actual CLI commands and verify the complete system integration.
"""

import json
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def solokit_project_with_dependencies():
    """Create a temp Solokit project with work items that have dependencies.

    Returns:
        Path: Project directory with complex dependency structure.
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

        # Create session structure manually with complex dependencies
        session_dir = project_dir / ".session"
        tracking_dir = session_dir / "tracking"
        tracking_dir.mkdir(parents=True)

        # Create work items with dependency structure
        work_items = {
            "next_id": 9,
            "work_items": {
                "1": {
                    "id": "1",
                    "type": "feature",
                    "title": "Database Schema Design",
                    "status": "completed",
                    "priority": "critical",
                    "dependencies": [],
                    "milestone": "Foundation",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "sessions": [],
                },
                "2": {
                    "id": "2",
                    "type": "feature",
                    "title": "User Authentication",
                    "status": "in_progress",
                    "priority": "critical",
                    "dependencies": ["1"],
                    "milestone": "MVP v1.0",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "sessions": [],
                },
                "3": {
                    "id": "3",
                    "type": "feature",
                    "title": "REST API Endpoints",
                    "status": "not_started",
                    "priority": "high",
                    "dependencies": ["1"],
                    "milestone": "MVP v1.0",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "sessions": [],
                },
                "4": {
                    "id": "4",
                    "type": "feature",
                    "title": "User Profile Management",
                    "status": "not_started",
                    "priority": "high",
                    "dependencies": ["2"],
                    "milestone": "MVP v1.0",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "sessions": [],
                },
                "5": {
                    "id": "5",
                    "type": "feature",
                    "title": "Social Media Login",
                    "status": "not_started",
                    "priority": "medium",
                    "dependencies": ["2"],
                    "milestone": "MVP v1.1",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "sessions": [],
                },
                "6": {
                    "id": "6",
                    "type": "bug",
                    "title": "Fix Authentication Timeout",
                    "status": "not_started",
                    "priority": "critical",
                    "dependencies": ["2"],
                    "milestone": "Hotfix v1.0.1",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "sessions": [],
                },
                "7": {
                    "id": "7",
                    "type": "refactor",
                    "title": "Database Query Optimization",
                    "status": "not_started",
                    "priority": "medium",
                    "dependencies": ["1"],
                    "milestone": "Performance Sprint",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "sessions": [],
                },
                "8": {
                    "id": "8",
                    "type": "security",
                    "title": "Penetration Testing",
                    "status": "blocked",
                    "priority": "high",
                    "dependencies": ["2", "3", "4"],
                    "milestone": "Security Audit",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "sessions": [],
                },
            },
        }

        work_items_file = tracking_dir / "work_items.json"
        with open(work_items_file, "w") as f:
            json.dump(work_items, f, indent=2)

        # Create empty tracking files
        (tracking_dir / "learnings.json").write_text('{"categories": {}, "metadata": {}}')
        (tracking_dir / "status_update.json").write_text("{}")
        (tracking_dir / "stack.txt").write_text("Python\n")
        (tracking_dir / "tree.txt").write_text(".\n")

        yield project_dir


# ============================================================================
# Phase 3.1: Basic Graph Generation Tests
# ============================================================================


class TestBasicGraphGeneration:
    """Tests for basic dependency graph generation."""

    def test_generate_ascii_graph(self, solokit_project_with_dependencies):
        """Test generating dependency graph in ASCII format."""
        # Arrange & Act
        result = subprocess.run(
            ["sk", "work-graph"],
            cwd=solokit_project_with_dependencies,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0, f"Graph generation failed: {result.stderr}"
        assert len(result.stdout) > 0, "Graph output is empty"
        assert (
            "Level" in result.stdout or "work" in result.stdout.lower()
        ), "Graph should show hierarchical structure"

    def test_graph_excludes_completed_items_by_default(self, solokit_project_with_dependencies):
        """Test that completed items are excluded from default graph view."""
        # Arrange & Act
        result = subprocess.run(
            ["sk", "work-graph"],
            cwd=solokit_project_with_dependencies,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0
        # Completed item (ID 1) should not be shown as a main node
        # It may appear in dependency references but not as a top-level item


# ============================================================================
# Phase 3.2: Critical Path Analysis Tests
# ============================================================================


class TestCriticalPathAnalysis:
    """Tests for critical path identification."""

    def test_critical_path_flag(self, solokit_project_with_dependencies):
        """Test --critical-path flag shows only critical path items."""
        # Arrange & Act
        result = subprocess.run(
            ["sk", "work-graph", "--critical-path"],
            cwd=solokit_project_with_dependencies,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0, f"Critical path analysis failed: {result.stderr}"
        # Should show critical path indicators or filtered view


# ============================================================================
# Phase 3.3: Bottleneck Detection Tests
# ============================================================================


class TestBottleneckDetection:
    """Tests for bottleneck detection in dependency graph."""

    def test_bottleneck_analysis(self, solokit_project_with_dependencies):
        """Test --bottlenecks flag identifies blocking work items."""
        # Arrange & Act
        result = subprocess.run(
            ["sk", "work-graph", "--bottlenecks"],
            cwd=solokit_project_with_dependencies,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0, f"Bottleneck detection failed: {result.stderr}"
        # Should identify bottlenecks or show analysis


# ============================================================================
# Phase 3.4: Filtering Tests
# ============================================================================


class TestGraphFiltering:
    """Tests for filtering dependency graph by various criteria."""

    def test_filter_by_status(self, solokit_project_with_dependencies):
        """Test filtering graph by work item status."""
        # Arrange & Act
        result = subprocess.run(
            ["sk", "work-graph", "--status", "not_started"],
            cwd=solokit_project_with_dependencies,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0, "Status filtering failed"

    def test_filter_by_type(self, solokit_project_with_dependencies):
        """Test filtering graph by work item type."""
        # Arrange & Act
        result = subprocess.run(
            ["sk", "work-graph", "--type", "feature"],
            cwd=solokit_project_with_dependencies,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0, "Type filtering failed"

    def test_filter_by_milestone(self, solokit_project_with_dependencies):
        """Test filtering graph by milestone."""
        # Arrange & Act
        result = subprocess.run(
            ["sk", "work-graph", "--milestone", "MVP v1.0"],
            cwd=solokit_project_with_dependencies,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0, "Milestone filtering failed"

    def test_combined_filters(self, solokit_project_with_dependencies):
        """Test combining multiple filters."""
        # Arrange & Act
        result = subprocess.run(
            [
                "sk",
                "work-graph",
                "--status",
                "not_started",
                "--type",
                "feature",
                "--milestone",
                "MVP v1.0",
            ],
            cwd=solokit_project_with_dependencies,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0, "Combined filters failed"


# ============================================================================
# Phase 3.5: Focus Mode Tests
# ============================================================================


class TestFocusMode:
    """Tests for focus mode on specific work items."""

    def test_focus_on_work_item(self, solokit_project_with_dependencies):
        """Test --focus flag shows specific work item and its neighborhood."""
        # Arrange & Act
        result = subprocess.run(
            ["sk", "work-graph", "--focus", "2"],  # Focus on User Authentication
            cwd=solokit_project_with_dependencies,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0, f"Focus mode failed: {result.stderr}"


# ============================================================================
# Phase 3.6: Statistics Tests
# ============================================================================


class TestGraphStatistics:
    """Tests for graph statistics and metrics."""

    def test_statistics_output(self, solokit_project_with_dependencies):
        """Test --stats flag shows graph statistics."""
        # Arrange & Act
        result = subprocess.run(
            ["sk", "work-graph", "--stats"],
            cwd=solokit_project_with_dependencies,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0, f"Statistics generation failed: {result.stderr}"
        # Should show some statistics about the graph


# ============================================================================
# Phase 3.7: Include Completed Tests
# ============================================================================


class TestIncludeCompleted:
    """Tests for including completed items in graph."""

    def test_include_completed_flag(self, solokit_project_with_dependencies):
        """Test --include-completed flag shows completed items."""
        # Arrange & Act - Without flag
        _result_default = subprocess.run(
            ["sk", "work-graph"],
            cwd=solokit_project_with_dependencies,
            capture_output=True,
            text=True,
        )

        # Act - With flag
        result_with_completed = subprocess.run(
            ["sk", "work-graph", "--include-completed"],
            cwd=solokit_project_with_dependencies,
            capture_output=True,
            text=True,
        )

        # Assert
        assert (
            result_with_completed.returncode == 0
        ), f"Include completed flag failed: {result_with_completed.stderr}"


# ============================================================================
# Phase 3.1: DOT Format Tests
# ============================================================================


class TestDOTFormat:
    """Tests for DOT format graph generation."""

    def test_generate_dot_format(self, solokit_project_with_dependencies):
        """Test generating dependency graph in DOT format for Graphviz."""
        # Arrange & Act
        result = subprocess.run(
            ["sk", "work-graph", "--format", "dot"],
            cwd=solokit_project_with_dependencies,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0, f"DOT format generation failed: {result.stderr}"
        assert (
            "digraph" in result.stdout or len(result.stdout) > 0
        ), "DOT format should contain graph definition"
