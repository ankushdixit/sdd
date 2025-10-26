"""Unit tests for session_validate module.

This module tests session validation functionality including:
- Git status checking
- Work item criteria validation
- Quality gates preview integration
- Tracking update detection
- Full validation workflow
"""

import json
from unittest.mock import Mock, patch

import pytest

from sdd.session.validate import SessionValidator


@pytest.fixture
def temp_session_dir(tmp_path):
    """Create temporary .session directory structure.

    Returns:
        Path: Path to temporary .session directory with tracking subdirectory.
    """
    session_dir = tmp_path / ".session"
    tracking_dir = session_dir / "tracking"
    specs_dir = session_dir / "specs"

    session_dir.mkdir()
    tracking_dir.mkdir()
    specs_dir.mkdir()

    # Create minimal config.json
    config = {
        "quality_gates": {
            "test_execution": {"enabled": True, "required": True},
            "linting": {"enabled": True, "required": False},
            "formatting": {"enabled": True, "required": False},
        }
    }
    (session_dir / "config.json").write_text(json.dumps(config))

    return session_dir


@pytest.fixture
def mock_quality_gates():
    """Create lightweight mock for QualityGates to avoid slow execution.

    Returns:
        Mock: Mock QualityGates instance with basic methods.
    """
    mock_qg = Mock()
    mock_qg.config = {
        "test_execution": {"enabled": True, "required": True},
        "linting": {"enabled": True, "required": False},
        "formatting": {"enabled": True, "required": False},
    }
    mock_qg.run_tests.return_value = (True, {"status": "passed", "reason": "All tests passed"})
    mock_qg.run_linting.return_value = (True, {"status": "passed"})
    mock_qg.run_formatting.return_value = (True, {"status": "passed"})
    return mock_qg


class TestSessionValidatorInit:
    """Test suite for SessionValidator initialization."""

    def test_init_with_default_project_root(self, temp_session_dir):
        """Test SessionValidator initializes with current directory as default project root."""
        # Arrange & Act
        with patch("sdd.session.validate.Path.cwd", return_value=temp_session_dir.parent):
            with patch("sdd.session.validate.QualityGates"):
                validator = SessionValidator()

        # Assert
        assert validator.project_root == temp_session_dir.parent
        assert validator.session_dir == temp_session_dir

    def test_init_with_custom_project_root(self, temp_session_dir):
        """Test SessionValidator initializes with custom project root path."""
        # Arrange
        project_root = temp_session_dir.parent

        # Act
        with patch("sdd.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        # Assert
        assert validator.project_root == project_root
        assert validator.session_dir == temp_session_dir

    def test_init_creates_quality_gates_instance(self, temp_session_dir):
        """Test SessionValidator creates QualityGates instance with config path."""
        # Arrange
        project_root = temp_session_dir.parent

        # Act
        with patch("sdd.session.validate.QualityGates") as mock_qg_class:
            _validator = SessionValidator(project_root=project_root)

        # Assert
        expected_config_path = temp_session_dir / "config.json"
        mock_qg_class.assert_called_once_with(expected_config_path)


class TestCheckGitStatus:
    """Test suite for check_git_status method."""

    def test_check_git_status_returns_success_for_clean_directory(self, temp_session_dir):
        """Test check_git_status returns passed=True for clean working directory."""
        # Arrange
        project_root = temp_session_dir.parent
        with patch("sdd.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""  # Clean directory

        mock_branch = Mock()
        mock_branch.stdout = "main\n"

        # Act
        with patch("subprocess.run", side_effect=[mock_result, mock_branch]):
            result = validator.check_git_status()

        # Assert
        assert result["passed"] is True
        assert "main" in result["message"]
        assert result["details"]["branch"] == "main"
        assert result["details"]["changes"] == 0

    def test_check_git_status_returns_success_with_non_tracking_changes(self, temp_session_dir):
        """Test check_git_status returns passed=True when changes don't include tracking files."""
        # Arrange
        project_root = temp_session_dir.parent
        with patch("sdd.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = " M src/main.py\n M tests/test_foo.py\n"

        mock_branch = Mock()
        mock_branch.stdout = "feature-branch\n"

        # Act
        with patch("subprocess.run", side_effect=[mock_result, mock_branch]):
            result = validator.check_git_status()

        # Assert
        assert result["passed"] is True
        assert "feature-branch" in result["message"]
        assert result["details"]["changes"] == 2

    def test_check_git_status_fails_with_uncommitted_tracking_files(self, temp_session_dir):
        """Test check_git_status returns passed=False when tracking files are uncommitted."""
        # Arrange
        project_root = temp_session_dir.parent
        with patch("sdd.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = (
            " M .session/tracking/status_update.json\n M .session/tracking/work_items.json\n"
        )

        # Act
        with patch("subprocess.run", return_value=mock_result):
            result = validator.check_git_status()

        # Assert
        assert result["passed"] is False
        assert "Uncommitted tracking files" in result["message"]
        assert "2 files" in result["message"]

    def test_check_git_status_fails_when_not_git_repository(self, temp_session_dir):
        """Test check_git_status returns passed=False when directory is not a git repo."""
        # Arrange
        project_root = temp_session_dir.parent
        with patch("sdd.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        mock_result = Mock()
        mock_result.returncode = 128  # Git error code for "not a git repository"

        # Act
        with patch("subprocess.run", return_value=mock_result):
            result = validator.check_git_status()

        # Assert
        assert result["passed"] is False
        assert "Not a git repository" in result["message"]

    def test_check_git_status_handles_subprocess_exception(self, temp_session_dir):
        """Test check_git_status handles subprocess exceptions gracefully."""
        # Arrange
        project_root = temp_session_dir.parent
        with patch("sdd.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        # Act
        with patch("subprocess.run", side_effect=Exception("Git command failed")):
            result = validator.check_git_status()

        # Assert
        assert result["passed"] is False
        assert "Git check failed" in result["message"]


class TestPreviewQualityGates:
    """Test suite for preview_quality_gates method."""

    def test_preview_quality_gates_all_pass(self, temp_session_dir, mock_quality_gates):
        """Test preview_quality_gates returns passed=True when all gates pass."""
        # Arrange
        project_root = temp_session_dir.parent
        with patch("sdd.session.validate.QualityGates", return_value=mock_quality_gates):
            validator = SessionValidator(project_root=project_root)

        # Act
        result = validator.preview_quality_gates()

        # Assert
        assert result["passed"] is True
        assert result["message"] == "All quality gates pass"
        assert "tests" in result["gates"]
        assert result["gates"]["tests"]["passed"] is True

    def test_preview_quality_gates_tests_fail(self, temp_session_dir, mock_quality_gates):
        """Test preview_quality_gates returns passed=False when tests fail."""
        # Arrange
        project_root = temp_session_dir.parent
        mock_quality_gates.run_tests.return_value = (
            False,
            {"status": "failed", "reason": "2 tests failed"},
        )

        with patch("sdd.session.validate.QualityGates", return_value=mock_quality_gates):
            validator = SessionValidator(project_root=project_root)

        # Act
        result = validator.preview_quality_gates()

        # Assert
        assert result["passed"] is False
        assert result["message"] == "Some quality gates fail"
        assert result["gates"]["tests"]["passed"] is False
        assert "2 tests failed" in result["gates"]["tests"]["message"]

    def test_preview_quality_gates_skips_tests_when_auto_fix_enabled(
        self, temp_session_dir, mock_quality_gates
    ):
        """Test preview_quality_gates skips tests when auto_fix=True."""
        # Arrange
        project_root = temp_session_dir.parent
        with patch("sdd.session.validate.QualityGates", return_value=mock_quality_gates):
            validator = SessionValidator(project_root=project_root)

        # Act
        result = validator.preview_quality_gates(auto_fix=True)

        # Assert
        assert "tests" not in result["gates"]  # Tests should be skipped
        mock_quality_gates.run_tests.assert_not_called()

    def test_preview_quality_gates_handles_optional_tests(
        self, temp_session_dir, mock_quality_gates
    ):
        """Test preview_quality_gates marks optional tests as passed even if they fail."""
        # Arrange
        project_root = temp_session_dir.parent
        mock_quality_gates.config["test_execution"]["required"] = False
        mock_quality_gates.run_tests.return_value = (False, {"status": "failed"})

        with patch("sdd.session.validate.QualityGates", return_value=mock_quality_gates):
            validator = SessionValidator(project_root=project_root)

        # Act
        result = validator.preview_quality_gates()

        # Assert
        assert result["gates"]["tests"]["passed"] is True
        assert "not required" in result["gates"]["tests"]["message"]

    def test_preview_quality_gates_handles_disabled_gates(
        self, temp_session_dir, mock_quality_gates
    ):
        """Test preview_quality_gates skips disabled quality gates."""
        # Arrange
        project_root = temp_session_dir.parent
        mock_quality_gates.config["test_execution"]["enabled"] = False

        with patch("sdd.session.validate.QualityGates", return_value=mock_quality_gates):
            validator = SessionValidator(project_root=project_root)

        # Act
        result = validator.preview_quality_gates()

        # Assert
        assert "tests" not in result["gates"]
        mock_quality_gates.run_tests.assert_not_called()

    def test_preview_quality_gates_auto_fix_linting(self, temp_session_dir, mock_quality_gates):
        """Test preview_quality_gates passes auto_fix parameter to linting."""
        # Arrange
        project_root = temp_session_dir.parent
        mock_quality_gates.config["linting"]["required"] = (
            True  # Make required to see auto-fix message
        )
        mock_quality_gates.run_linting.return_value = (True, {"status": "passed", "fixed": True})

        with patch("sdd.session.validate.QualityGates", return_value=mock_quality_gates):
            validator = SessionValidator(project_root=project_root)

        # Act
        result = validator.preview_quality_gates(auto_fix=True)

        # Assert
        mock_quality_gates.run_linting.assert_called_once_with(auto_fix=True)
        assert "auto-fixed" in result["gates"]["linting"]["message"]

    def test_preview_quality_gates_auto_fix_formatting(self, temp_session_dir, mock_quality_gates):
        """Test preview_quality_gates passes auto_fix parameter to formatting."""
        # Arrange
        project_root = temp_session_dir.parent
        mock_quality_gates.config["formatting"]["required"] = (
            True  # Make required to see auto-fix message
        )
        mock_quality_gates.run_formatting.return_value = (
            True,
            {"status": "passed", "formatted": True},
        )

        with patch("sdd.session.validate.QualityGates", return_value=mock_quality_gates):
            validator = SessionValidator(project_root=project_root)

        # Act
        result = validator.preview_quality_gates(auto_fix=True)

        # Assert
        mock_quality_gates.run_formatting.assert_called_once_with(auto_fix=True)
        assert "auto-formatted" in result["gates"]["formatting"]["message"]


class TestValidateWorkItemCriteria:
    """Test suite for validate_work_item_criteria method."""

    def test_validate_work_item_criteria_fails_when_no_active_session(self, temp_session_dir):
        """Test validate_work_item_criteria returns passed=False when status file doesn't exist."""
        # Arrange
        project_root = temp_session_dir.parent
        with patch("sdd.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        # Act
        result = validator.validate_work_item_criteria()

        # Assert
        assert result["passed"] is False
        assert result["message"] == "No active session"

    def test_validate_work_item_criteria_fails_when_no_current_work_item(self, temp_session_dir):
        """Test validate_work_item_criteria returns passed=False when no current work item set."""
        # Arrange
        project_root = temp_session_dir.parent
        status_file = temp_session_dir / "tracking" / "status_update.json"
        status_file.write_text(json.dumps({"current_work_item": None}))

        with patch("sdd.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        # Act
        result = validator.validate_work_item_criteria()

        # Assert
        assert result["passed"] is False
        assert result["message"] == "No current work item"

    def test_validate_work_item_criteria_fails_when_spec_file_missing(self, temp_session_dir):
        """Test validate_work_item_criteria returns passed=False when spec file doesn't exist."""
        # Arrange
        project_root = temp_session_dir.parent

        # Create status and work items
        status_file = temp_session_dir / "tracking" / "status_update.json"
        status_file.write_text(json.dumps({"current_work_item": "WORK-001"}))

        work_items_file = temp_session_dir / "tracking" / "work_items.json"
        work_items = {
            "work_items": {
                "WORK-001": {
                    "id": "WORK-001",
                    "type": "feature",
                    "spec_file": ".session/specs/WORK-001.md",
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items))

        with patch("sdd.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        # Act
        result = validator.validate_work_item_criteria()

        # Assert
        assert result["passed"] is False
        assert "Spec file missing" in result["message"]

    def test_validate_work_item_criteria_fails_when_spec_file_invalid(self, temp_session_dir):
        """Test validate_work_item_criteria returns passed=False when spec parsing fails."""
        # Arrange
        project_root = temp_session_dir.parent

        # Create status and work items
        status_file = temp_session_dir / "tracking" / "status_update.json"
        status_file.write_text(json.dumps({"current_work_item": "WORK-001"}))

        work_items_file = temp_session_dir / "tracking" / "work_items.json"
        work_items = {
            "work_items": {
                "WORK-001": {
                    "id": "WORK-001",
                    "type": "feature",
                    "spec_file": ".session/specs/WORK-001.md",
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items))

        # Create spec file
        spec_file = temp_session_dir / "specs" / "WORK-001.md"
        spec_file.write_text("Invalid spec content")

        with patch("sdd.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        # Act
        with patch(
            "sdd.work_items.spec_parser.parse_spec_file", side_effect=Exception("Parse error")
        ):
            result = validator.validate_work_item_criteria()

        # Assert
        assert result["passed"] is False
        assert "Spec file invalid" in result["message"]

    def test_validate_work_item_criteria_fails_when_acceptance_criteria_insufficient(
        self, temp_session_dir
    ):
        """Test validate_work_item_criteria returns passed=False when fewer than 3 acceptance criteria."""
        # Arrange
        project_root = temp_session_dir.parent

        # Create status and work items
        status_file = temp_session_dir / "tracking" / "status_update.json"
        status_file.write_text(json.dumps({"current_work_item": "WORK-001"}))

        work_items_file = temp_session_dir / "tracking" / "work_items.json"
        work_items = {
            "work_items": {
                "WORK-001": {
                    "id": "WORK-001",
                    "type": "feature",
                    "spec_file": ".session/specs/WORK-001.md",
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items))

        # Create spec file
        spec_file = temp_session_dir / "specs" / "WORK-001.md"
        spec_file.write_text("# Spec")

        with patch("sdd.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        # Act
        with patch(
            "sdd.work_items.spec_parser.parse_spec_file",
            return_value={"acceptance_criteria": ["AC1", "AC2"]},
        ):
            result = validator.validate_work_item_criteria()

        # Assert
        assert result["passed"] is False
        assert "Spec file incomplete" in result["message"]
        assert "Acceptance Criteria (at least 3 items)" in result["missing_sections"]

    def test_validate_work_item_criteria_validates_feature_sections(self, temp_session_dir):
        """Test validate_work_item_criteria checks feature-specific required sections."""
        # Arrange
        project_root = temp_session_dir.parent

        # Create status and work items
        status_file = temp_session_dir / "tracking" / "status_update.json"
        status_file.write_text(json.dumps({"current_work_item": "WORK-001"}))

        work_items_file = temp_session_dir / "tracking" / "work_items.json"
        work_items = {
            "work_items": {
                "WORK-001": {
                    "id": "WORK-001",
                    "type": "feature",
                    "spec_file": ".session/specs/WORK-001.md",
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items))

        # Create spec file
        spec_file = temp_session_dir / "specs" / "WORK-001.md"
        spec_file.write_text("# Spec")

        with patch("sdd.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        # Act
        parsed_spec = {
            "acceptance_criteria": ["AC1", "AC2", "AC3"]
        }  # Missing overview and implementation_details
        with patch("sdd.work_items.spec_parser.parse_spec_file", return_value=parsed_spec):
            result = validator.validate_work_item_criteria()

        # Assert
        assert result["passed"] is False
        assert "Overview" in result["missing_sections"]
        assert "Implementation Details" in result["missing_sections"]

    def test_validate_work_item_criteria_validates_bug_sections(self, temp_session_dir):
        """Test validate_work_item_criteria checks bug-specific required sections."""
        # Arrange
        project_root = temp_session_dir.parent

        # Create status and work items
        status_file = temp_session_dir / "tracking" / "status_update.json"
        status_file.write_text(json.dumps({"current_work_item": "BUG-001"}))

        work_items_file = temp_session_dir / "tracking" / "work_items.json"
        work_items = {
            "work_items": {
                "BUG-001": {
                    "id": "BUG-001",
                    "type": "bug",
                    "spec_file": ".session/specs/BUG-001.md",
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items))

        # Create spec file
        spec_file = temp_session_dir / "specs" / "BUG-001.md"
        spec_file.write_text("# Spec")

        with patch("sdd.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        # Act
        parsed_spec = {
            "acceptance_criteria": ["AC1", "AC2", "AC3"]
        }  # Missing description and fix_approach
        with patch("sdd.work_items.spec_parser.parse_spec_file", return_value=parsed_spec):
            result = validator.validate_work_item_criteria()

        # Assert
        assert result["passed"] is False
        assert "Description" in result["missing_sections"]
        assert "Fix Approach" in result["missing_sections"]

    def test_validate_work_item_criteria_validates_integration_test_sections(
        self, temp_session_dir
    ):
        """Test validate_work_item_criteria checks integration test-specific required sections."""
        # Arrange
        project_root = temp_session_dir.parent

        # Create status and work items
        status_file = temp_session_dir / "tracking" / "status_update.json"
        status_file.write_text(json.dumps({"current_work_item": "TEST-001"}))

        work_items_file = temp_session_dir / "tracking" / "work_items.json"
        work_items = {
            "work_items": {
                "TEST-001": {
                    "id": "TEST-001",
                    "type": "integration_test",
                    "spec_file": ".session/specs/TEST-001.md",
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items))

        # Create spec file
        spec_file = temp_session_dir / "specs" / "TEST-001.md"
        spec_file.write_text("# Spec")

        with patch("sdd.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        # Act
        parsed_spec = {
            "acceptance_criteria": ["AC1", "AC2", "AC3"]
        }  # Missing scope and test_scenarios
        with patch("sdd.work_items.spec_parser.parse_spec_file", return_value=parsed_spec):
            result = validator.validate_work_item_criteria()

        # Assert
        assert result["passed"] is False
        assert "Scope" in result["missing_sections"]
        assert "Test Scenarios (at least 1)" in result["missing_sections"]

    def test_validate_work_item_criteria_passes_complete_feature_spec(self, temp_session_dir):
        """Test validate_work_item_criteria returns passed=True for complete feature spec."""
        # Arrange
        project_root = temp_session_dir.parent

        # Create status and work items
        status_file = temp_session_dir / "tracking" / "status_update.json"
        status_file.write_text(json.dumps({"current_work_item": "WORK-001"}))

        work_items_file = temp_session_dir / "tracking" / "work_items.json"
        work_items = {
            "work_items": {
                "WORK-001": {
                    "id": "WORK-001",
                    "type": "feature",
                    "spec_file": ".session/specs/WORK-001.md",
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items))

        # Create spec file
        spec_file = temp_session_dir / "specs" / "WORK-001.md"
        spec_file.write_text("# Spec")

        with patch("sdd.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        # Act
        parsed_spec = {
            "acceptance_criteria": ["AC1", "AC2", "AC3"],
            "overview": "Feature overview",
            "implementation_details": "Details",
        }
        with patch("sdd.work_items.spec_parser.parse_spec_file", return_value=parsed_spec):
            result = validator.validate_work_item_criteria()

        # Assert
        assert result["passed"] is True
        assert result["message"] == "Work item spec is complete"


class TestCheckTrackingUpdates:
    """Test suite for check_tracking_updates method."""

    def test_check_tracking_updates_returns_no_changes(self, temp_session_dir):
        """Test check_tracking_updates returns passed=True with no changes message."""
        # Arrange
        project_root = temp_session_dir.parent
        with patch("sdd.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        # Act
        result = validator.check_tracking_updates()

        # Assert
        assert result["passed"] is True
        assert result["message"] == "No tracking updates"
        assert result["changes"]["stack"]["has_changes"] is False
        assert result["changes"]["tree"]["has_changes"] is False

    def test_check_tracking_updates_detects_changes(self, temp_session_dir):
        """Test check_tracking_updates detects changes when stack or tree modified."""
        # Arrange
        project_root = temp_session_dir.parent
        with patch("sdd.session.validate.QualityGates"):
            validator = SessionValidator(project_root=project_root)

        # Act
        with patch.object(
            validator,
            "_check_stack_changes",
            return_value={"has_changes": True, "message": "Stack updated"},
        ):
            result = validator.check_tracking_updates()

        # Assert
        assert result["passed"] is True  # Always passes
        assert result["message"] == "Tracking updates detected"
        assert result["changes"]["stack"]["has_changes"] is True


class TestValidate:
    """Test suite for full validate workflow."""

    def test_validate_all_checks_pass(self, temp_session_dir, mock_quality_gates, capsys):
        """Test validate returns ready=True when all checks pass."""
        # Arrange
        project_root = temp_session_dir.parent

        # Create complete session setup
        status_file = temp_session_dir / "tracking" / "status_update.json"
        status_file.write_text(json.dumps({"current_work_item": "WORK-001"}))

        work_items_file = temp_session_dir / "tracking" / "work_items.json"
        work_items = {
            "work_items": {
                "WORK-001": {
                    "id": "WORK-001",
                    "type": "feature",
                    "spec_file": ".session/specs/WORK-001.md",
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items))

        spec_file = temp_session_dir / "specs" / "WORK-001.md"
        spec_file.write_text("# Spec")

        with patch("sdd.session.validate.QualityGates", return_value=mock_quality_gates):
            validator = SessionValidator(project_root=project_root)

        # Mock all checks to pass
        mock_git_result = Mock()
        mock_git_result.returncode = 0
        mock_git_result.stdout = ""

        mock_branch = Mock()
        mock_branch.stdout = "main\n"

        parsed_spec = {
            "acceptance_criteria": ["AC1", "AC2", "AC3"],
            "overview": "Overview",
            "implementation_details": "Details",
        }

        # Act
        with patch("subprocess.run", side_effect=[mock_git_result, mock_branch]):
            with patch("sdd.work_items.spec_parser.parse_spec_file", return_value=parsed_spec):
                result = validator.validate()

        # Assert
        assert result["ready"] is True
        assert all(check["passed"] for check in result["checks"].values())

        # Check console output
        captured = capsys.readouterr()
        assert "Session ready to complete!" in captured.out

    def test_validate_some_checks_fail(self, temp_session_dir, mock_quality_gates, capsys):
        """Test validate returns ready=False when some checks fail."""
        # Arrange
        project_root = temp_session_dir.parent

        with patch("sdd.session.validate.QualityGates", return_value=mock_quality_gates):
            validator = SessionValidator(project_root=project_root)

        # Mock git check to fail
        mock_git_result = Mock()
        mock_git_result.returncode = 128

        # Act
        with patch("subprocess.run", return_value=mock_git_result):
            result = validator.validate()

        # Assert
        assert result["ready"] is False

        # Check console output
        captured = capsys.readouterr()
        assert "Session not ready to complete" in captured.out

    def test_validate_passes_auto_fix_parameter(self, temp_session_dir, mock_quality_gates):
        """Test validate passes auto_fix parameter to quality gates preview."""
        # Arrange
        project_root = temp_session_dir.parent

        # Create minimal session setup
        status_file = temp_session_dir / "tracking" / "status_update.json"
        status_file.write_text(json.dumps({"current_work_item": "WORK-001"}))

        work_items_file = temp_session_dir / "tracking" / "work_items.json"
        work_items = {
            "work_items": {
                "WORK-001": {
                    "id": "WORK-001",
                    "type": "feature",
                    "spec_file": ".session/specs/WORK-001.md",
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items))

        spec_file = temp_session_dir / "specs" / "WORK-001.md"
        spec_file.write_text("# Spec")

        with patch("sdd.session.validate.QualityGates", return_value=mock_quality_gates):
            validator = SessionValidator(project_root=project_root)

        # Mock git
        mock_git_result = Mock()
        mock_git_result.returncode = 0
        mock_git_result.stdout = ""

        mock_branch = Mock()
        mock_branch.stdout = "main\n"

        parsed_spec = {
            "acceptance_criteria": ["AC1", "AC2", "AC3"],
            "overview": "Overview",
            "implementation_details": "Details",
        }

        # Act
        with patch("subprocess.run", side_effect=[mock_git_result, mock_branch]):
            with patch("sdd.work_items.spec_parser.parse_spec_file", return_value=parsed_spec):
                validator.validate(auto_fix=True)

        # Assert
        mock_quality_gates.run_linting.assert_called_with(auto_fix=True)
        mock_quality_gates.run_formatting.assert_called_with(auto_fix=True)
