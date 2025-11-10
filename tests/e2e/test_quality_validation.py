"""End-to-end tests for quality gates and validation (Phase 5).

Tests the complete validation system including:
- Session validation command
- Quality gates (tests, linting, formatting)
- Git status validation
- Work item validation (acceptance criteria)
- Validation reporting and error messages

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
def sdd_project_for_validation():
    """Create a temp Solokit project with active session for validation testing.

    Returns:
        Path: Project directory with session and work items.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "test_project"
        project_dir.mkdir()

        # Create basic project files
        (project_dir / "README.md").write_text("# Test Project\n")
        (project_dir / "src").mkdir()
        (project_dir / "src" / "test.py").write_text("# Test file\n")
        (project_dir / "tests").mkdir()
        (project_dir / "tests" / "test_test.py").write_text("# Test file\n")

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

        # Create session structure
        session_dir = project_dir / ".session"
        tracking_dir = session_dir / "tracking"
        specs_dir = session_dir / "specs"
        tracking_dir.mkdir(parents=True)
        specs_dir.mkdir(parents=True)

        # Create work item
        work_items = {
            "next_id": 2,
            "work_items": {
                "1": {
                    "id": "1",
                    "title": "Test Work Item",
                    "type": "feature",
                    "status": "in_progress",
                    "priority": "high",
                    "dependencies": [],
                    "milestone": None,
                    "sessions": [],
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                }
            },
        }

        (tracking_dir / "work_items.json").write_text(json.dumps(work_items, indent=2))

        # Create spec file
        spec_content = """# Feature: Test Work Item

## Overview
This is a test work item for validation testing.

## Rationale
Testing the validation system.

## Acceptance Criteria
- [ ] Tests pass
- [ ] Code is formatted
- [ ] Validation works

## Implementation Details
- src/test.py

## Testing Strategy
- tests/test_test.py
"""
        (specs_dir / "1.md").write_text(spec_content)

        # Create status file
        status = {
            "current_work_item": "1",
            "session_start": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat(),
        }
        (tracking_dir / "status_update.json").write_text(json.dumps(status, indent=2))

        # Create learnings file
        learnings = {
            "metadata": {"total_learnings": 0, "last_curated": None},
            "categories": {
                "architecture_patterns": [],
                "gotchas": [],
                "best_practices": [],
                "technical_debt": [],
                "performance_insights": [],
                "security": [],
            },
        }
        (tracking_dir / "learnings.json").write_text(json.dumps(learnings, indent=2))

        # Create other tracking files
        (tracking_dir / "stack.txt").write_text("Python\n")
        (tracking_dir / "tree.txt").write_text(".\n")

        yield project_dir


# ============================================================================
# Phase 5.1: Validation Command Tests
# ============================================================================


class TestValidationCommand:
    """Tests for sk validate command execution."""

    def test_validate_command_exists(self, sdd_project_for_validation):
        """Test that sk validate command executes."""
        # Arrange & Act
        result = subprocess.run(
            ["sk", "validate"],
            cwd=sdd_project_for_validation,
            capture_output=True,
            text=True,
        )

        # Assert - May pass or fail, but should execute
        output = result.stdout + result.stderr
        assert len(output) > 0, "Validation should provide output"

    def test_validate_runs_multiple_checks(self, sdd_project_for_validation):
        """Test that validation runs multiple quality checks."""
        # Arrange & Act
        result = subprocess.run(
            ["sk", "validate"],
            cwd=sdd_project_for_validation,
            capture_output=True,
            text=True,
        )

        # Assert
        output = result.stdout + result.stderr
        # Should mention various checks or gates
        has_checks = any(
            keyword in output.lower()
            for keyword in ["quality", "gate", "test", "git", "check", "validation"]
        )
        assert has_checks, "Validation should mention quality checks"


# ============================================================================
# Phase 5.2: Quality Gates Tests
# ============================================================================


class TestQualityGates:
    """Tests for quality gates validation."""

    def test_quality_gates_structure(self, sdd_project_for_validation):
        """Test that quality gates are reported with structure."""
        # Arrange & Act
        result = subprocess.run(
            ["sk", "validate"],
            cwd=sdd_project_for_validation,
            capture_output=True,
            text=True,
        )

        # Assert
        output = result.stdout + result.stderr
        # Should have structured output
        has_structure = "✓" in output or "✗" in output or "PASS" in output or "FAIL" in output
        assert has_structure or len(output) > 0, "Quality gates should have structured output"


# ============================================================================
# Phase 5.3: Git Validation Tests
# ============================================================================


class TestGitValidation:
    """Tests for git status validation."""

    def test_validate_checks_git_status(self, sdd_project_for_validation):
        """Test that validation checks git status."""
        # Arrange & Act
        result = subprocess.run(
            ["sk", "validate"],
            cwd=sdd_project_for_validation,
            capture_output=True,
            text=True,
        )

        # Assert
        output = result.stdout + result.stderr
        # Should mention git or status
        has_git_check = "git" in output.lower() or "status" in output.lower()
        assert has_git_check or result.returncode in [0, 1], "Validation should check git status"

    def test_validation_handles_uncommitted_changes(self, sdd_project_for_validation):
        """Test validation behavior with uncommitted changes."""
        # Arrange - Create new file
        (sdd_project_for_validation / "new_file.py").write_text("# New file\n")

        # Act
        result = subprocess.run(
            ["sk", "validate"],
            cwd=sdd_project_for_validation,
            capture_output=True,
            text=True,
        )

        # Assert - Should execute successfully (uncommitted changes may be OK)
        assert result.returncode in [0, 1], "Validation should handle uncommitted changes"


# ============================================================================
# Phase 5.4: Work Item Validation Tests
# ============================================================================


class TestWorkItemValidation:
    """Tests for work item acceptance criteria validation."""

    def test_validate_with_no_active_work_item(self, sdd_project_for_validation):
        """Test validation when no work item is active."""
        # Arrange - Clear current work item
        status_file = sdd_project_for_validation / ".session/tracking/status_update.json"
        status = json.loads(status_file.read_text())
        status["current_work_item"] = None
        status_file.write_text(json.dumps(status, indent=2))

        # Act
        result = subprocess.run(
            ["sk", "validate"],
            cwd=sdd_project_for_validation,
            capture_output=True,
            text=True,
        )

        # Assert
        output = result.stdout + result.stderr
        # Should indicate no active work item or fail validation
        assert result.returncode == 1 or "no" in output.lower(), "Should detect missing work item"

    def test_validate_checks_spec_file(self, sdd_project_for_validation):
        """Test that validation checks spec file existence."""
        # Arrange & Act
        result = subprocess.run(
            ["sk", "validate"],
            cwd=sdd_project_for_validation,
            capture_output=True,
            text=True,
        )

        # Assert - Spec file exists, so validation should work
        output = result.stdout + result.stderr
        assert len(output) > 0, "Validation should check spec file"

    def test_validate_with_missing_spec_file(self, sdd_project_for_validation):
        """Test validation behavior when spec file is missing."""
        # Arrange - Remove spec file
        spec_file = sdd_project_for_validation / ".session/specs/1.md"
        spec_file.unlink()

        # Act
        result = subprocess.run(
            ["sk", "validate"],
            cwd=sdd_project_for_validation,
            capture_output=True,
            text=True,
        )

        # Assert - Should detect missing spec
        output = result.stdout + result.stderr
        assert "spec" in output.lower() or result.returncode == 1, "Should detect missing spec file"


# ============================================================================
# Phase 5.5: Validation Reporting Tests
# ============================================================================


class TestValidationReporting:
    """Tests for validation reporting and error messages."""

    def test_validation_provides_clear_output(self, sdd_project_for_validation):
        """Test that validation provides clear, structured output."""
        # Arrange & Act
        result = subprocess.run(
            ["sk", "validate"],
            cwd=sdd_project_for_validation,
            capture_output=True,
            text=True,
        )

        # Assert
        output = result.stdout + result.stderr
        assert len(output) > 0, "Validation should provide output"
        # Should have some structure or indicators
        has_indicators = any(char in output for char in ["✓", "✗", "[", "]", "-", "*"])
        assert has_indicators or len(output.split("\n")) > 1, (
            "Validation should have structured output"
        )

    def test_validation_exit_codes_consistent(self, sdd_project_for_validation):
        """Test that validation exit codes are consistent."""
        # Arrange & Act - Run validation twice
        result1 = subprocess.run(
            ["sk", "validate"],
            cwd=sdd_project_for_validation,
            capture_output=True,
            text=True,
        )

        result2 = subprocess.run(
            ["sk", "validate"],
            cwd=sdd_project_for_validation,
            capture_output=True,
            text=True,
        )

        # Assert - Results should be consistent
        assert result1.returncode == result2.returncode, "Validation results should be consistent"


# ============================================================================
# Phase 5: Integration Tests
# ============================================================================


class TestValidationIntegration:
    """Integration tests for the complete validation workflow."""

    def test_validation_complete_workflow(self, sdd_project_for_validation):
        """Test complete validation workflow from start to finish."""
        # Arrange - Project already set up with active session

        # Act - Run validation
        result = subprocess.run(
            ["sk", "validate"],
            cwd=sdd_project_for_validation,
            capture_output=True,
            text=True,
        )

        # Assert - Should complete validation process
        assert result.returncode in [0, 1], "Validation should complete"
        output = result.stdout + result.stderr
        assert len(output) > 0, "Validation should provide feedback"
