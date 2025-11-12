"""Tests for briefing.py _cli_main() function to improve coverage.

This module specifically tests the CLI wrapper function _cli_main() which handles
exception scenarios (lines 310-374 in briefing.py).
"""

import importlib.util
from pathlib import Path
from unittest.mock import patch

from solokit.core.exceptions import (
    GitError,
    SessionAlreadyActiveError,
    SessionNotFoundError,
    UnmetDependencyError,
    ValidationError,
    WorkItemNotFoundError,
)
from solokit.core.types import WorkItemStatus

# Import the briefing.py file directly using spec_from_file_location
# The briefing package dynamically loads this as _briefing_module
briefing_file = (
    Path(__file__).parent.parent.parent.parent / "src" / "solokit" / "session" / "briefing.py"
)
spec = importlib.util.spec_from_file_location("_test_briefing_module", briefing_file)
briefing_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(briefing_module)


class TestCliMainFunction:
    """Tests for _cli_main() wrapper function."""

    def test_cli_main_returns_result_from_main(self):
        """Test that _cli_main() returns result from successful main()."""
        with patch.object(briefing_module, "main", return_value=0) as mock_main:
            result = briefing_module._cli_main()
            assert result == 0
            mock_main.assert_called_once()

    def test_cli_main_handles_session_not_found_error(self, capsys):
        """Test that _cli_main() handles SessionNotFoundError."""
        error = SessionNotFoundError()
        with patch.object(briefing_module, "main", side_effect=error):
            result = briefing_module._cli_main()
            assert result == error.exit_code
            captured = capsys.readouterr()
            assert "Error:" in captured.out
            assert error.message in captured.out

    def test_cli_main_handles_work_item_not_found_shows_available(self, capsys):
        """Test that _cli_main() shows available work items on WorkItemNotFoundError."""
        error = WorkItemNotFoundError("WORK-999")
        work_items_data = {
            "work_items": {
                "WORK-001": {
                    "title": "Feature A",
                    "status": WorkItemStatus.NOT_STARTED.value,
                },
                "WORK-002": {
                    "title": "Feature B",
                    "status": WorkItemStatus.IN_PROGRESS.value,
                },
            }
        }

        with patch.object(briefing_module, "main", side_effect=error):
            with patch.object(briefing_module, "load_work_items", return_value=work_items_data):
                result = briefing_module._cli_main()

                assert result == error.exit_code
                captured = capsys.readouterr()
                assert "Available work items:" in captured.out
                assert "WORK-001" in captured.out
                assert "Feature A" in captured.out

    def test_cli_main_handles_work_item_not_found_load_failure(self, capsys):
        """Test that _cli_main() handles WorkItemNotFoundError even when load fails."""
        error = WorkItemNotFoundError("WORK-999")

        with patch.object(briefing_module, "main", side_effect=error):
            with patch.object(
                briefing_module, "load_work_items", side_effect=Exception("Cannot load")
            ):
                result = briefing_module._cli_main()
                assert result == error.exit_code
                # Should not crash even if load fails

    def test_cli_main_handles_session_already_active_error(self, capsys):
        """Test that _cli_main() handles SessionAlreadyActiveError."""
        error = SessionAlreadyActiveError("WORK-002")

        with patch.object(briefing_module, "main", side_effect=error):
            result = briefing_module._cli_main()

            assert result == error.exit_code
            captured = capsys.readouterr()
            assert "Warning:" in captured.out
            assert "Options:" in captured.out
            assert "/end" in captured.out
            assert "--force" in captured.out

    def test_cli_main_handles_unmet_dependency_error_shows_details(self, capsys):
        """Test that _cli_main() shows dependency details on UnmetDependencyError."""
        error = UnmetDependencyError("WORK-002", "WORK-001")
        work_items_data = {
            "work_items": {
                "WORK-001": {
                    "title": "Dependency Feature",
                    "status": WorkItemStatus.NOT_STARTED.value,
                }
            }
        }

        with patch.object(briefing_module, "main", side_effect=error):
            with patch.object(briefing_module, "load_work_items", return_value=work_items_data):
                result = briefing_module._cli_main()

                assert result == error.exit_code
                captured = capsys.readouterr()
                assert "Dependency details:" in captured.out
                assert "WORK-001" in captured.out
                assert "Dependency Feature" in captured.out

    def test_cli_main_handles_unmet_dependency_error_load_failure(self, capsys):
        """Test that _cli_main() handles UnmetDependencyError even when load fails."""
        error = UnmetDependencyError("WORK-002", "WORK-001")

        with patch.object(briefing_module, "main", side_effect=error):
            with patch.object(
                briefing_module, "load_work_items", side_effect=Exception("Cannot load")
            ):
                result = briefing_module._cli_main()
                assert result == error.exit_code
                # Should not crash even if load fails

    def test_cli_main_handles_validation_error(self, capsys):
        """Test that _cli_main() handles ValidationError."""
        error = ValidationError(
            message="No available work items",
            code=None,
            remediation="Create a work item first",
        )

        with patch.object(briefing_module, "main", side_effect=error):
            result = briefing_module._cli_main()

            assert result == error.exit_code
            captured = capsys.readouterr()
            assert "No available work items" in captured.out
            assert "Create a work item first" in captured.out

    def test_cli_main_handles_validation_error_no_remediation(self, capsys):
        """Test that _cli_main() handles ValidationError without remediation."""
        error = ValidationError(message="Validation failed", code=None, remediation=None)

        with patch.object(briefing_module, "main", side_effect=error):
            result = briefing_module._cli_main()

            assert result == error.exit_code
            captured = capsys.readouterr()
            assert "Validation failed" in captured.out

    def test_cli_main_handles_git_error_returns_success(self, capsys):
        """Test that _cli_main() handles GitError and returns 0 (warnings only)."""
        error = GitError(message="Git command failed", code=None, remediation="Install git")

        with patch.object(briefing_module, "main", side_effect=error):
            result = briefing_module._cli_main()

            assert result == 0  # Git errors are warnings, not fatal
            captured = capsys.readouterr()
            assert "Warning:" in captured.out
            assert "Git command failed" in captured.out
            assert "Install git" in captured.out

    def test_cli_main_handles_git_error_no_remediation(self, capsys):
        """Test that _cli_main() handles GitError without remediation."""
        error = GitError(message="Git error", code=None, remediation=None)

        with patch.object(briefing_module, "main", side_effect=error):
            result = briefing_module._cli_main()

            assert result == 0
            captured = capsys.readouterr()
            assert "Warning:" in captured.out
            assert "Git error" in captured.out

    def test_cli_main_handles_unexpected_exception(self, capsys):
        """Test that _cli_main() handles unexpected exceptions."""
        with patch.object(briefing_module, "main", side_effect=RuntimeError("Unexpected error")):
            with patch.object(briefing_module, "logger") as mock_logger:
                result = briefing_module._cli_main()

                assert result == 1
                captured = capsys.readouterr()
                assert "Unexpected error:" in captured.out
                assert "Unexpected error" in captured.out
                mock_logger.exception.assert_called_once()
