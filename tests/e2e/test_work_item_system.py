"""End-to-end tests for work item system (Phase 2).

Tests the complete work item management system including:
- Work item type templates (6 types)
- Work item creation with all types
- Work item listing with filtering
- Work item details display
- Work item field updates
- Dependency management
- Milestone tracking
- Next work item recommendation
- Session status display

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
def sdd_project_with_work_items():
    """Create a temp SDD project with multiple work items for testing.

    Returns:
        tuple: (project_dir, work_item_ids) where work_item_ids is a list of created IDs.
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

        # Create work items
        work_items_to_create = [
            ("feature", "User Authentication", "high"),
            ("bug", "Fix Login Redirect", "critical"),
            ("refactor", "Optimize Database Queries", "medium"),
            ("security", "Add CSRF Protection", "high"),
            ("integration_test", "Test Auth Flow", "medium"),
            ("deployment", "Deploy to Production", "high"),
        ]

        created_ids = []
        for wtype, title, priority in work_items_to_create:
            result = subprocess.run(
                ["sdd", "work-new", "--type", wtype, "--title", title, "--priority", priority],
                cwd=project_dir,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                # Extract ID from work_items.json
                work_items_file = project_dir / ".session/tracking/work_items.json"
                work_items_data = json.loads(work_items_file.read_text())
                # Get the last added work item
                work_item_id = list(work_items_data["work_items"].keys())[-1]
                created_ids.append(work_item_id)

        yield project_dir, created_ids


# ============================================================================
# Phase 2.1: Work Item Type Templates Tests
# ============================================================================


class TestWorkItemTypeTemplates:
    """Tests for work item type templates."""

    def test_all_work_item_templates_exist(self):
        """Test that all 6 work item type templates exist."""
        # Arrange
        templates_dir = Path(__file__).parent.parent.parent / "src" / "sdd" / "templates"
        expected_templates = [
            "feature_spec.md",
            "bug_spec.md",
            "refactor_spec.md",
            "security_spec.md",
            "integration_test_spec.md",
            "deployment_spec.md",
        ]

        # Act & Assert
        for template in expected_templates:
            template_path = templates_dir / template
            assert template_path.exists(), f"Template not found: {template}"
            assert template_path.stat().st_size > 100, f"Template too short: {template}"

    def test_work_item_types_documentation_exists(self):
        """Test that WORK_ITEM_TYPES.md documents all types."""
        # Arrange
        templates_dir = Path(__file__).parent.parent.parent / "src" / "sdd" / "templates"
        types_file = templates_dir / "WORK_ITEM_TYPES.md"
        work_item_types = [
            "feature",
            "bug",
            "refactor",
            "security",
            "integration_test",
            "deployment",
        ]

        # Act
        assert types_file.exists(), "WORK_ITEM_TYPES.md not found"
        types_content = types_file.read_text()

        # Assert
        for wtype in work_item_types:
            assert wtype in types_content, f"Work item type not documented: {wtype}"


# ============================================================================
# Phase 2.2: Work Item Creation Tests
# ============================================================================


class TestWorkItemCreation:
    """Tests for work item creation with all types."""

    def test_create_all_six_work_item_types(self, sdd_project_with_work_items):
        """Test creating all 6 work item types."""
        # Arrange
        project_dir, created_ids = sdd_project_with_work_items

        # Act
        work_items_file = project_dir / ".session/tracking/work_items.json"
        work_items_data = json.loads(work_items_file.read_text())

        # Assert
        assert len(created_ids) == 6, f"Expected 6 work items, got {len(created_ids)}"
        assert len(work_items_data["work_items"]) >= 6, "Not all work items saved"

        # Verify all types present
        types_found = [item["type"] for item in work_items_data["work_items"].values()]
        expected_types = [
            "feature",
            "bug",
            "refactor",
            "security",
            "integration_test",
            "deployment",
        ]

        for expected_type in expected_types:
            assert expected_type in types_found, f"Work item type not created: {expected_type}"

    def test_work_item_spec_files_created(self, sdd_project_with_work_items):
        """Test that spec files are created for all work items."""
        # Arrange
        project_dir, created_ids = sdd_project_with_work_items

        # Act & Assert
        for work_id in created_ids:
            spec_file = project_dir / ".session/specs" / f"{work_id}.md"
            assert spec_file.exists(), f"Spec file not created: {work_id}.md"
            assert spec_file.stat().st_size > 0, f"Spec file is empty: {work_id}.md"

    def test_work_item_with_dependencies(self, sdd_project_with_work_items):
        """Test creating a work item with dependencies."""
        # Arrange
        project_dir, created_ids = sdd_project_with_work_items
        base_work_id = created_ids[0]

        # Act
        result = subprocess.run(
            [
                "sdd",
                "work-new",
                "--type",
                "feature",
                "--title",
                "User Profile Page",
                "--priority",
                "medium",
                "--dependencies",
                base_work_id,
            ],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0, (
            f"Failed to create work item with dependency: {result.stderr}"
        )

        work_items_file = project_dir / ".session/tracking/work_items.json"
        work_items_data = json.loads(work_items_file.read_text())

        # Find the new work item
        dependent_item = None
        for item in work_items_data["work_items"].values():
            if item["title"] == "User Profile Page":
                dependent_item = item
                break

        assert dependent_item is not None, "Dependent work item not found"
        assert base_work_id in dependent_item["dependencies"], (
            f"Dependency not recorded: {base_work_id}"
        )


# ============================================================================
# Phase 2.3: Work Item List Tests
# ============================================================================


class TestWorkItemList:
    """Tests for work item listing with filtering."""

    def test_list_all_work_items(self, sdd_project_with_work_items):
        """Test listing all work items."""
        # Arrange
        project_dir, _ = sdd_project_with_work_items

        # Act
        result = subprocess.run(
            ["sdd", "work-list"],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0, f"List command failed: {result.stderr}"
        assert "Work Items" in result.stdout or len(result.stdout) > 0, "List output empty"

    def test_list_filter_by_type(self, sdd_project_with_work_items):
        """Test filtering work items by type."""
        # Arrange
        project_dir, _ = sdd_project_with_work_items

        # Act
        result = subprocess.run(
            ["sdd", "work-list", "--type", "feature"],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0, "Type filter failed"
        # Should contain feature items
        assert "feature" in result.stdout.lower() or "User Authentication" in result.stdout

    def test_list_filter_by_status(self, sdd_project_with_work_items):
        """Test filtering work items by status."""
        # Arrange
        project_dir, _ = sdd_project_with_work_items

        # Act
        result = subprocess.run(
            ["sdd", "work-list", "--status", "not_started"],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0, "Status filter failed"


# ============================================================================
# Phase 2.4: Work Item Show Tests
# ============================================================================


class TestWorkItemShow:
    """Tests for work item details display."""

    def test_show_work_item_details(self, sdd_project_with_work_items):
        """Test showing detailed work item information."""
        # Arrange
        project_dir, created_ids = sdd_project_with_work_items
        work_id = created_ids[0]

        # Act
        result = subprocess.run(
            ["sdd", "work-show", work_id],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0, f"Show command failed: {result.stderr}"

        output = result.stdout
        required_sections = ["Work Item:", "Type:", "Status:", "Priority:"]

        for section in required_sections:
            assert section in output, f"Missing section: {section}"

        assert work_id in output, f"Work item ID not in output: {work_id}"


# ============================================================================
# Phase 2.5: Work Item Update Tests
# ============================================================================


class TestWorkItemUpdate:
    """Tests for work item field updates."""

    def test_update_work_item_priority(self, sdd_project_with_work_items):
        """Test updating work item priority."""
        # Arrange
        project_dir, created_ids = sdd_project_with_work_items
        work_id = created_ids[0]

        # Act
        result = subprocess.run(
            ["sdd", "work-update", work_id, "--priority", "medium"],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0, f"Update failed: {result.stderr}"

        work_items_file = project_dir / ".session/tracking/work_items.json"
        work_items_data = json.loads(work_items_file.read_text())
        item = work_items_data["work_items"][work_id]

        assert item["priority"] == "medium", f"Priority not updated: {item['priority']}"

    def test_update_work_item_status(self, sdd_project_with_work_items):
        """Test updating work item status."""
        # Arrange
        project_dir, created_ids = sdd_project_with_work_items
        work_id = created_ids[0]

        # Act
        result = subprocess.run(
            ["sdd", "work-update", work_id, "--status", "in_progress"],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0, "Status update failed"

        work_items_file = project_dir / ".session/tracking/work_items.json"
        work_items_data = json.loads(work_items_file.read_text())
        item = work_items_data["work_items"][work_id]

        assert item["status"] == "in_progress", f"Status not updated: {item['status']}"

    def test_update_work_item_milestone(self, sdd_project_with_work_items):
        """Test updating work item milestone."""
        # Arrange
        project_dir, created_ids = sdd_project_with_work_items
        work_id = created_ids[0]

        # Act
        result = subprocess.run(
            ["sdd", "work-update", work_id, "--milestone", "MVP Phase 1"],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0, "Milestone update failed"

        work_items_file = project_dir / ".session/tracking/work_items.json"
        work_items_data = json.loads(work_items_file.read_text())
        item = work_items_data["work_items"][work_id]

        assert item["milestone"] == "MVP Phase 1", f"Milestone not updated: {item['milestone']}"


# ============================================================================
# Phase 2.6 & 2.7: Work Item Next and Milestone Tests
# ============================================================================


class TestWorkItemNextAndMilestones:
    """Tests for next work item recommendation and milestone tracking."""

    def test_work_next_recommendation(self, sdd_project_with_work_items):
        """Test getting next recommended work item."""
        # Arrange
        project_dir, _ = sdd_project_with_work_items

        # Act
        result = subprocess.run(
            ["sdd", "work-next"],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0, f"work-next failed: {result.stderr}"
        # Should provide some recommendation or message
        assert len(result.stdout) > 0 or len(result.stderr) > 0, "No output from work-next"

    def test_milestone_filtering(self, sdd_project_with_work_items):
        """Test filtering work items by milestone."""
        # Arrange
        project_dir, created_ids = sdd_project_with_work_items

        # Update some work items with milestone
        for work_id in created_ids[:3]:
            subprocess.run(
                ["sdd", "work-update", work_id, "--milestone", "MVP Phase 1"],
                cwd=project_dir,
                check=True,
                capture_output=True,
            )

        # Act
        result = subprocess.run(
            ["sdd", "work-list", "--milestone", "MVP Phase 1"],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0, "Milestone filter failed"


# ============================================================================
# Phase 2.9: Session Status Tests
# ============================================================================


class TestSessionStatus:
    """Tests for session status command."""

    def test_session_status_displays(self, sdd_project_with_work_items):
        """Test that session status command executes."""
        # Arrange
        project_dir, _ = sdd_project_with_work_items

        # Act
        result = subprocess.run(
            ["sdd", "status"],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )

        # Assert - May show no active work item or status, both are acceptable
        output = result.stdout + result.stderr
        assert result.returncode in [0, 1], "Status command should execute"
        assert len(output) > 0, "Status command should provide output"
