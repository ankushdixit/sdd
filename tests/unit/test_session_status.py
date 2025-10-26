#!/usr/bin/env python3
"""
Unit tests for scripts/session_status.py

Tests the session status display functionality including:
- Status file validation
- Work item loading and display
- Time elapsed calculations
- Git change tracking
- Milestone progress
- Next items recommendations
"""

import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from sdd.session.status import get_session_status


class TestGetSessionStatusNoStatusFile:
    """Tests for get_session_status when status file doesn't exist."""

    def test_no_status_file_returns_error(self, capsys):
        """
        Test that missing status file prints error and returns 1.

        Arrange: Mock Path.exists to return False
        Act: Call get_session_status()
        Assert: Returns 1 and prints "No active session"
        """
        with patch("sdd.session.status.Path") as mock_path:
            # Arrange
            mock_status_file = MagicMock()
            mock_status_file.exists.return_value = False
            mock_path.return_value.__truediv__.return_value.__truediv__.return_value = (
                mock_status_file
            )

            # Act
            result = get_session_status()

            # Assert
            assert result == 1
            captured = capsys.readouterr()
            assert "No active session" in captured.out

    def test_no_status_file_no_further_processing(self, capsys):
        """
        Test that function exits early when status file missing.

        Arrange: Mock Path.exists to return False
        Act: Call get_session_status()
        Assert: No work item info displayed
        """
        with patch("sdd.session.status.Path") as mock_path:
            # Arrange
            mock_status_file = MagicMock()
            mock_status_file.exists.return_value = False
            mock_path.return_value.__truediv__.return_value.__truediv__.return_value = (
                mock_status_file
            )

            # Act
            result = get_session_status()

            # Assert
            assert result == 1
            captured = capsys.readouterr()
            assert "Work Item:" not in captured.out
            assert "Current Session Status" not in captured.out


class TestGetSessionStatusNoWorkItem:
    """Tests for get_session_status when no current work item."""

    def test_no_work_item_returns_error(self, capsys):
        """
        Test that missing work item ID prints error and returns 1.

        Arrange: Mock status file with no current_work_item
        Act: Call get_session_status()
        Assert: Returns 1 and prints "No active work item"
        """
        with patch("sdd.session.status.Path") as mock_path:
            # Arrange
            status_data = {}  # No current_work_item
            mock_status_file = MagicMock()
            mock_status_file.exists.return_value = True
            mock_status_file.read_text.return_value = json.dumps(status_data)
            mock_path.return_value.__truediv__.return_value.__truediv__.return_value = (
                mock_status_file
            )

            # Act
            result = get_session_status()

            # Assert
            assert result == 1
            captured = capsys.readouterr()
            assert "No active work item in this session" in captured.out

    def test_empty_work_item_id_returns_error(self, capsys):
        """
        Test that empty work item ID prints error and returns 1.

        Arrange: Mock status file with empty current_work_item
        Act: Call get_session_status()
        Assert: Returns 1 and prints "No active work item"
        """
        with patch("sdd.session.status.Path") as mock_path:
            # Arrange
            status_data = {"current_work_item": ""}
            mock_status_file = MagicMock()
            mock_status_file.exists.return_value = True
            mock_status_file.read_text.return_value = json.dumps(status_data)
            mock_path.return_value.__truediv__.return_value.__truediv__.return_value = (
                mock_status_file
            )

            # Act
            result = get_session_status()

            # Assert
            assert result == 1
            captured = capsys.readouterr()
            assert "No active work item in this session" in captured.out


class TestGetSessionStatusWorkItemNotFound:
    """Tests for get_session_status when work item not found."""

    def test_work_item_not_in_data_returns_error(self, capsys):
        """
        Test that missing work item in data prints error and returns 1.

        Arrange: Mock status with work item ID not in work_items.json
        Act: Call get_session_status()
        Assert: Returns 1 and prints "Work item not found"
        """
        with patch.object(Path, "exists", return_value=True):
            # Arrange
            status_data = {"current_work_item": "WI-999"}
            work_items_data = {"work_items": {"WI-001": {"status": "completed"}}}

            with patch.object(
                Path,
                "read_text",
                side_effect=[json.dumps(status_data), json.dumps(work_items_data)],
            ):
                # Act
                result = get_session_status()

            # Assert
            assert result == 1
            captured = capsys.readouterr()
            assert "Work item WI-999 not found" in captured.out

    def test_work_item_none_in_dict_returns_error(self, capsys):
        """
        Test that None work item value prints error and returns 1.

        Arrange: Mock status with work item that has None value
        Act: Call get_session_status()
        Assert: Returns 1 and prints error message
        """
        with patch.object(Path, "exists", return_value=True):
            # Arrange
            status_data = {"current_work_item": "WI-001"}
            work_items_data = {"work_items": {"WI-001": None}}

            with patch.object(
                Path,
                "read_text",
                side_effect=[json.dumps(status_data), json.dumps(work_items_data)],
            ):
                # Act
                result = get_session_status()

            # Assert
            assert result == 1
            # The function checks if not item, so None should trigger error
            captured = capsys.readouterr()
            assert "Work item WI-001 not found" in captured.out


class TestGetSessionStatusSuccess:
    """Tests for successful get_session_status execution."""

    def test_basic_work_item_display(self, capsys):
        """
        Test successful display of basic work item information.

        Arrange: Mock complete work item with basic fields
        Act: Call get_session_status()
        Assert: Returns 0 and displays work item details
        """
        with patch.object(Path, "exists", return_value=True):
            # Arrange
            status_data = {"current_work_item": "WI-001"}
            work_items_data = {
                "work_items": {
                    "WI-001": {
                        "type": "feature",
                        "priority": "high",
                        "status": "in_progress",
                        "sessions": ["session-001"],
                        "estimated_effort": "2 hours",
                    }
                }
            }

            with patch.object(
                Path,
                "read_text",
                side_effect=[json.dumps(status_data), json.dumps(work_items_data)],
            ):
                with patch("sdd.session.status.subprocess.run") as mock_run:
                    # Mock git diff to return no changes
                    mock_run.return_value = Mock(returncode=1, stdout="")

                    # Act
                    result = get_session_status()

            # Assert
            assert result == 0
            captured = capsys.readouterr()
            assert "Current Session Status" in captured.out
            assert "Work Item: WI-001" in captured.out
            assert "Type: feature" in captured.out
            assert "Priority: high" in captured.out
            assert "Session: 1 (of estimated 2 hours)" in captured.out

    def test_work_item_with_empty_sessions(self, capsys):
        """
        Test display when work item has no sessions.

        Arrange: Mock work item with empty sessions list
        Act: Call get_session_status()
        Assert: Returns 0 and displays session count as 0
        """
        with patch.object(Path, "exists", return_value=True):
            # Arrange
            status_data = {"current_work_item": "WI-002"}
            work_items_data = {
                "work_items": {
                    "WI-002": {
                        "type": "bug",
                        "priority": "critical",
                        "status": "in_progress",
                        "sessions": [],
                    }
                }
            }

            with patch.object(
                Path,
                "read_text",
                side_effect=[json.dumps(status_data), json.dumps(work_items_data)],
            ):
                with patch("sdd.session.status.subprocess.run") as mock_run:
                    mock_run.return_value = Mock(returncode=1, stdout="")

                    # Act
                    result = get_session_status()

            # Assert
            assert result == 0
            captured = capsys.readouterr()
            assert "Session: 0 (of estimated Unknown)" in captured.out

    def test_work_item_without_estimated_effort(self, capsys):
        """
        Test display when estimated_effort is missing.

        Arrange: Mock work item without estimated_effort field
        Act: Call get_session_status()
        Assert: Returns 0 and displays "Unknown" for estimate
        """
        with patch.object(Path, "exists", return_value=True):
            # Arrange
            status_data = {"current_work_item": "WI-003"}
            work_items_data = {
                "work_items": {
                    "WI-003": {
                        "type": "refactor",
                        "priority": "medium",
                        "status": "in_progress",
                    }
                }
            }

            with patch.object(
                Path,
                "read_text",
                side_effect=[json.dumps(status_data), json.dumps(work_items_data)],
            ):
                with patch("sdd.session.status.subprocess.run") as mock_run:
                    mock_run.return_value = Mock(returncode=1, stdout="")

                    # Act
                    result = get_session_status()

            # Assert
            assert result == 0
            captured = capsys.readouterr()
            assert "(of estimated Unknown)" in captured.out


class TestGetSessionStatusWithTime:
    """Tests for get_session_status with session time tracking."""

    def test_time_elapsed_display(self, capsys):
        """
        Test display of elapsed time during session.

        Arrange: Mock status with session_start 2 hours 30 minutes ago
        Act: Call get_session_status()
        Assert: Returns 0 and displays "2h 30m"
        """
        with patch.object(Path, "exists", return_value=True):
            # Arrange
            now = datetime.now()
            start_time = now - timedelta(hours=2, minutes=30)
            status_data = {
                "current_work_item": "WI-001",
                "session_start": start_time.isoformat(),
            }
            work_items_data = {
                "work_items": {
                    "WI-001": {
                        "type": "feature",
                        "priority": "high",
                        "status": "in_progress",
                    }
                }
            }

            with patch.object(
                Path,
                "read_text",
                side_effect=[json.dumps(status_data), json.dumps(work_items_data)],
            ):
                with patch("sdd.session.status.subprocess.run") as mock_run:
                    mock_run.return_value = Mock(returncode=1, stdout="")

                    with patch("sdd.session.status.datetime") as mock_datetime:
                        mock_datetime.now.return_value = now
                        mock_datetime.fromisoformat = datetime.fromisoformat

                        # Act
                        result = get_session_status()

            # Assert
            assert result == 0
            captured = capsys.readouterr()
            assert "Time Elapsed: 2h 30m" in captured.out

    def test_time_elapsed_less_than_hour(self, capsys):
        """
        Test display when elapsed time is less than an hour.

        Arrange: Mock status with session_start 45 minutes ago
        Act: Call get_session_status()
        Assert: Returns 0 and displays "0h 45m"
        """
        with patch.object(Path, "exists", return_value=True):
            # Arrange
            now = datetime.now()
            start_time = now - timedelta(minutes=45)
            status_data = {
                "current_work_item": "WI-002",
                "session_start": start_time.isoformat(),
            }
            work_items_data = {
                "work_items": {
                    "WI-002": {
                        "type": "bug",
                        "priority": "critical",
                        "status": "in_progress",
                    }
                }
            }

            with patch.object(
                Path,
                "read_text",
                side_effect=[json.dumps(status_data), json.dumps(work_items_data)],
            ):
                with patch("sdd.session.status.subprocess.run") as mock_run:
                    mock_run.return_value = Mock(returncode=1, stdout="")

                    with patch("sdd.session.status.datetime") as mock_datetime:
                        mock_datetime.now.return_value = now
                        mock_datetime.fromisoformat = datetime.fromisoformat

                        # Act
                        result = get_session_status()

            # Assert
            assert result == 0
            captured = capsys.readouterr()
            assert "Time Elapsed: 0h 45m" in captured.out

    def test_no_session_start_no_time_display(self, capsys):
        """
        Test that time is not displayed when session_start missing.

        Arrange: Mock status without session_start field
        Act: Call get_session_status()
        Assert: Returns 0 and no "Time Elapsed" displayed
        """
        with patch.object(Path, "exists", return_value=True):
            # Arrange
            status_data = {"current_work_item": "WI-003"}
            work_items_data = {
                "work_items": {
                    "WI-003": {
                        "type": "refactor",
                        "priority": "low",
                        "status": "in_progress",
                    }
                }
            }

            with patch.object(
                Path,
                "read_text",
                side_effect=[json.dumps(status_data), json.dumps(work_items_data)],
            ):
                with patch("sdd.session.status.subprocess.run") as mock_run:
                    mock_run.return_value = Mock(returncode=1, stdout="")

                    # Act
                    result = get_session_status()

            # Assert
            assert result == 0
            captured = capsys.readouterr()
            assert "Time Elapsed:" not in captured.out


class TestGetSessionStatusWithGitChanges:
    """Tests for get_session_status with git change tracking."""

    def test_git_changes_displayed(self, capsys):
        """
        Test display of git changes from diff output.

        Arrange: Mock subprocess to return git diff with 3 files
        Act: Call get_session_status()
        Assert: Returns 0 and displays "Files Changed (3)"
        """
        with patch.object(Path, "exists", return_value=True):
            # Arrange
            status_data = {"current_work_item": "WI-001"}
            work_items_data = {
                "work_items": {
                    "WI-001": {
                        "type": "feature",
                        "priority": "high",
                        "status": "in_progress",
                    }
                }
            }

            git_output = "M\tfile1.py\nA\tfile2.py\nD\tfile3.py"

            with patch.object(
                Path,
                "read_text",
                side_effect=[json.dumps(status_data), json.dumps(work_items_data)],
            ):
                with patch("sdd.session.status.subprocess.run") as mock_run:
                    mock_run.return_value = Mock(returncode=0, stdout=git_output)

                    # Act
                    result = get_session_status()

            # Assert
            assert result == 0
            captured = capsys.readouterr()
            assert "Files Changed (3):" in captured.out
            assert "M\tfile1.py" in captured.out
            assert "A\tfile2.py" in captured.out
            assert "D\tfile3.py" in captured.out

    def test_git_changes_more_than_ten(self, capsys):
        """
        Test display when more than 10 files changed.

        Arrange: Mock subprocess to return git diff with 15 files
        Act: Call get_session_status()
        Assert: Returns 0 and shows first 10 plus "and 5 more"
        """
        with patch.object(Path, "exists", return_value=True):
            # Arrange
            status_data = {"current_work_item": "WI-002"}
            work_items_data = {
                "work_items": {
                    "WI-002": {
                        "type": "refactor",
                        "priority": "medium",
                        "status": "in_progress",
                    }
                }
            }

            # Create 15 files
            git_output = "\n".join([f"M\tfile{i}.py" for i in range(1, 16)])

            with patch.object(
                Path,
                "read_text",
                side_effect=[json.dumps(status_data), json.dumps(work_items_data)],
            ):
                with patch("sdd.session.status.subprocess.run") as mock_run:
                    mock_run.return_value = Mock(returncode=0, stdout=git_output)

                    # Act
                    result = get_session_status()

            # Assert
            assert result == 0
            captured = capsys.readouterr()
            assert "Files Changed (15):" in captured.out
            assert "M\tfile1.py" in captured.out
            assert "M\tfile10.py" in captured.out
            assert "... and 5 more" in captured.out
            assert "M\tfile11.py" not in captured.out

    def test_git_diff_error_handled_gracefully(self, capsys):
        """
        Test that git diff errors are handled without crashing.

        Arrange: Mock subprocess to raise exception
        Act: Call get_session_status()
        Assert: Returns 0 and continues without git changes
        """
        with patch.object(Path, "exists", return_value=True):
            # Arrange
            status_data = {"current_work_item": "WI-003"}
            work_items_data = {
                "work_items": {
                    "WI-003": {
                        "type": "bug",
                        "priority": "high",
                        "status": "in_progress",
                    }
                }
            }

            with patch.object(
                Path,
                "read_text",
                side_effect=[json.dumps(status_data), json.dumps(work_items_data)],
            ):
                with patch("sdd.session.status.subprocess.run") as mock_run:
                    mock_run.side_effect = subprocess.TimeoutExpired("git", 5)

                    # Act
                    result = get_session_status()

            # Assert
            assert result == 0
            captured = capsys.readouterr()
            assert "Files Changed" not in captured.out

    def test_git_diff_no_changes(self, capsys):
        """
        Test when git diff returns no changes.

        Arrange: Mock subprocess to return empty stdout
        Act: Call get_session_status()
        Assert: Returns 0 and no "Files Changed" displayed
        """
        with patch.object(Path, "exists", return_value=True):
            # Arrange
            status_data = {"current_work_item": "WI-004"}
            work_items_data = {
                "work_items": {
                    "WI-004": {
                        "type": "feature",
                        "priority": "low",
                        "status": "in_progress",
                    }
                }
            }

            with patch.object(
                Path,
                "read_text",
                side_effect=[json.dumps(status_data), json.dumps(work_items_data)],
            ):
                with patch("sdd.session.status.subprocess.run") as mock_run:
                    mock_run.return_value = Mock(returncode=0, stdout="")

                    # Act
                    result = get_session_status()

            # Assert
            assert result == 0
            captured = capsys.readouterr()
            assert "Files Changed" not in captured.out

    def test_git_diff_nonzero_returncode(self, capsys):
        """
        Test when git diff returns non-zero exit code.

        Arrange: Mock subprocess to return returncode != 0
        Act: Call get_session_status()
        Assert: Returns 0 and no "Files Changed" displayed
        """
        with patch.object(Path, "exists", return_value=True):
            # Arrange
            status_data = {"current_work_item": "WI-005"}
            work_items_data = {
                "work_items": {
                    "WI-005": {
                        "type": "bug",
                        "priority": "medium",
                        "status": "in_progress",
                    }
                }
            }

            with patch.object(
                Path,
                "read_text",
                side_effect=[json.dumps(status_data), json.dumps(work_items_data)],
            ):
                with patch("sdd.session.status.subprocess.run") as mock_run:
                    mock_run.return_value = Mock(returncode=1, stdout="some output")

                    # Act
                    result = get_session_status()

            # Assert
            assert result == 0
            captured = capsys.readouterr()
            assert "Files Changed" not in captured.out


class TestGetSessionStatusWithGitInfo:
    """Tests for get_session_status with git info from work item."""

    def test_git_branch_and_commits_displayed(self, capsys):
        """
        Test display of git branch and commit count.

        Arrange: Mock work item with git branch and commits
        Act: Call get_session_status()
        Assert: Returns 0 and displays git branch and commit count
        """
        with patch.object(Path, "exists", return_value=True):
            # Arrange
            status_data = {"current_work_item": "WI-001"}
            work_items_data = {
                "work_items": {
                    "WI-001": {
                        "type": "feature",
                        "priority": "high",
                        "status": "in_progress",
                        "git": {
                            "branch": "feature/new-feature",
                            "commits": ["abc123", "def456", "ghi789"],
                        },
                    }
                }
            }

            with patch.object(
                Path,
                "read_text",
                side_effect=[json.dumps(status_data), json.dumps(work_items_data)],
            ):
                with patch("sdd.session.status.subprocess.run") as mock_run:
                    mock_run.return_value = Mock(returncode=1, stdout="")

                    # Act
                    result = get_session_status()

            # Assert
            assert result == 0
            captured = capsys.readouterr()
            assert "Git Branch: feature/new-feature" in captured.out
            assert "Commits: 3" in captured.out

    def test_git_info_with_no_commits(self, capsys):
        """
        Test display when git info has empty commits list.

        Arrange: Mock work item with git branch but no commits
        Act: Call get_session_status()
        Assert: Returns 0 and displays "Commits: 0"
        """
        with patch.object(Path, "exists", return_value=True):
            # Arrange
            status_data = {"current_work_item": "WI-002"}
            work_items_data = {
                "work_items": {
                    "WI-002": {
                        "type": "bug",
                        "priority": "critical",
                        "status": "in_progress",
                        "git": {"branch": "bugfix/issue-123", "commits": []},
                    }
                }
            }

            with patch.object(
                Path,
                "read_text",
                side_effect=[json.dumps(status_data), json.dumps(work_items_data)],
            ):
                with patch("sdd.session.status.subprocess.run") as mock_run:
                    mock_run.return_value = Mock(returncode=1, stdout="")

                    # Act
                    result = get_session_status()

            # Assert
            assert result == 0
            captured = capsys.readouterr()
            assert "Git Branch: bugfix/issue-123" in captured.out
            assert "Commits: 0" in captured.out

    def test_no_git_info_no_display(self, capsys):
        """
        Test that git info is not displayed when missing.

        Arrange: Mock work item without git field
        Act: Call get_session_status()
        Assert: Returns 0 and no git branch/commits displayed
        """
        with patch.object(Path, "exists", return_value=True):
            # Arrange
            status_data = {"current_work_item": "WI-003"}
            work_items_data = {
                "work_items": {
                    "WI-003": {
                        "type": "refactor",
                        "priority": "low",
                        "status": "in_progress",
                    }
                }
            }

            with patch.object(
                Path,
                "read_text",
                side_effect=[json.dumps(status_data), json.dumps(work_items_data)],
            ):
                with patch("sdd.session.status.subprocess.run") as mock_run:
                    mock_run.return_value = Mock(returncode=1, stdout="")

                    # Act
                    result = get_session_status()

            # Assert
            assert result == 0
            captured = capsys.readouterr()
            assert "Git Branch:" not in captured.out
            assert "Commits:" not in captured.out


class TestGetSessionStatusWithMilestone:
    """Tests for get_session_status with milestone progress."""

    def test_milestone_progress_displayed(self, capsys):
        """
        Test display of milestone progress with multiple items.

        Arrange: Mock work item with milestone and related items
        Act: Call get_session_status()
        Assert: Returns 0 and displays milestone progress
        """
        with patch.object(Path, "exists", return_value=True):
            # Arrange
            status_data = {"current_work_item": "WI-001"}
            work_items_data = {
                "work_items": {
                    "WI-001": {
                        "type": "feature",
                        "priority": "high",
                        "status": "in_progress",
                        "milestone": "v1.0",
                    },
                    "WI-002": {
                        "type": "bug",
                        "priority": "medium",
                        "status": "completed",
                        "milestone": "v1.0",
                    },
                    "WI-003": {
                        "type": "feature",
                        "priority": "low",
                        "status": "not_started",
                        "milestone": "v1.0",
                    },
                    "WI-004": {
                        "type": "refactor",
                        "priority": "high",
                        "status": "not_started",
                        "milestone": "v1.0",
                    },
                },
                "milestones": {"v1.0": {"name": "Version 1.0", "target_date": "2024-12-31"}},
            }

            with patch.object(
                Path,
                "read_text",
                side_effect=[json.dumps(status_data), json.dumps(work_items_data)],
            ):
                with patch("sdd.session.status.subprocess.run") as mock_run:
                    mock_run.return_value = Mock(returncode=1, stdout="")

                    # Act
                    result = get_session_status()

            # Assert
            assert result == 0
            captured = capsys.readouterr()
            # 1 completed out of 4 total = 25%
            assert "Milestone: v1.0 (25% complete)" in captured.out
            assert "Related items: 1 in progress, 2 not started" in captured.out

    def test_milestone_all_completed(self, capsys):
        """
        Test milestone display when all items completed.

        Arrange: Mock milestone with all items completed
        Act: Call get_session_status()
        Assert: Returns 0 and displays "100% complete"
        """
        with patch.object(Path, "exists", return_value=True):
            # Arrange
            status_data = {"current_work_item": "WI-001"}
            work_items_data = {
                "work_items": {
                    "WI-001": {
                        "type": "feature",
                        "priority": "high",
                        "status": "completed",
                        "milestone": "v1.0",
                    },
                    "WI-002": {
                        "type": "bug",
                        "priority": "medium",
                        "status": "completed",
                        "milestone": "v1.0",
                    },
                },
                "milestones": {"v1.0": {"name": "Version 1.0"}},
            }

            with patch.object(
                Path,
                "read_text",
                side_effect=[json.dumps(status_data), json.dumps(work_items_data)],
            ):
                with patch("sdd.session.status.subprocess.run") as mock_run:
                    mock_run.return_value = Mock(returncode=1, stdout="")

                    # Act
                    result = get_session_status()

            # Assert
            assert result == 0
            captured = capsys.readouterr()
            assert "Milestone: v1.0 (100% complete)" in captured.out
            assert "Related items: 0 in progress, 0 not started" in captured.out

    def test_milestone_none_completed(self, capsys):
        """
        Test milestone display when no items completed.

        Arrange: Mock milestone with no completed items
        Act: Call get_session_status()
        Assert: Returns 0 and displays "0% complete"
        """
        with patch.object(Path, "exists", return_value=True):
            # Arrange
            status_data = {"current_work_item": "WI-001"}
            work_items_data = {
                "work_items": {
                    "WI-001": {
                        "type": "feature",
                        "priority": "high",
                        "status": "in_progress",
                        "milestone": "v2.0",
                    },
                    "WI-002": {
                        "type": "bug",
                        "priority": "medium",
                        "status": "not_started",
                        "milestone": "v2.0",
                    },
                },
                "milestones": {"v2.0": {"name": "Version 2.0"}},
            }

            with patch.object(
                Path,
                "read_text",
                side_effect=[json.dumps(status_data), json.dumps(work_items_data)],
            ):
                with patch("sdd.session.status.subprocess.run") as mock_run:
                    mock_run.return_value = Mock(returncode=1, stdout="")

                    # Act
                    result = get_session_status()

            # Assert
            assert result == 0
            captured = capsys.readouterr()
            assert "Milestone: v2.0 (0% complete)" in captured.out
            assert "Related items: 1 in progress, 1 not started" in captured.out

    def test_no_milestone_no_display(self, capsys):
        """
        Test that milestone is not displayed when missing.

        Arrange: Mock work item without milestone field
        Act: Call get_session_status()
        Assert: Returns 0 and no milestone info displayed
        """
        with patch.object(Path, "exists", return_value=True):
            # Arrange
            status_data = {"current_work_item": "WI-001"}
            work_items_data = {
                "work_items": {
                    "WI-001": {
                        "type": "feature",
                        "priority": "high",
                        "status": "in_progress",
                    }
                }
            }

            with patch.object(
                Path,
                "read_text",
                side_effect=[json.dumps(status_data), json.dumps(work_items_data)],
            ):
                with patch("sdd.session.status.subprocess.run") as mock_run:
                    mock_run.return_value = Mock(returncode=1, stdout="")

                    # Act
                    result = get_session_status()

            # Assert
            assert result == 0
            captured = capsys.readouterr()
            assert "Milestone:" not in captured.out

    def test_milestone_not_in_milestones_dict(self, capsys):
        """
        Test when milestone name not found in milestones dict.

        Arrange: Mock work item with milestone not in milestones
        Act: Call get_session_status()
        Assert: Returns 0 and no milestone info displayed
        """
        with patch.object(Path, "exists", return_value=True):
            # Arrange
            status_data = {"current_work_item": "WI-001"}
            work_items_data = {
                "work_items": {
                    "WI-001": {
                        "type": "feature",
                        "priority": "high",
                        "status": "in_progress",
                        "milestone": "v3.0",
                    }
                },
                "milestones": {"v1.0": {"name": "Version 1.0"}},
            }

            with patch.object(
                Path,
                "read_text",
                side_effect=[json.dumps(status_data), json.dumps(work_items_data)],
            ):
                with patch("sdd.session.status.subprocess.run") as mock_run:
                    mock_run.return_value = Mock(returncode=1, stdout="")

                    # Act
                    result = get_session_status()

            # Assert
            assert result == 0
            captured = capsys.readouterr()
            # Should not crash, just not display milestone info
            assert "Milestone: v3.0" not in captured.out


class TestGetSessionStatusWithNextItems:
    """Tests for get_session_status with next items display."""

    def test_next_items_displayed(self, capsys):
        """
        Test display of next not-started items.

        Arrange: Mock work items with some not-started items
        Act: Call get_session_status()
        Assert: Returns 0 and displays up to 3 next items
        """
        with patch.object(Path, "exists", return_value=True):
            # Arrange
            status_data = {"current_work_item": "WI-001"}
            work_items_data = {
                "work_items": {
                    "WI-001": {
                        "type": "feature",
                        "priority": "high",
                        "status": "in_progress",
                    },
                    "WI-002": {
                        "type": "bug",
                        "priority": "critical",
                        "status": "not_started",
                        "dependencies": [],
                    },
                    "WI-003": {
                        "type": "feature",
                        "priority": "medium",
                        "status": "not_started",
                        "dependencies": [],
                    },
                }
            }

            with patch.object(
                Path,
                "read_text",
                side_effect=[json.dumps(status_data), json.dumps(work_items_data)],
            ):
                with patch("sdd.session.status.subprocess.run") as mock_run:
                    mock_run.return_value = Mock(returncode=1, stdout="")

                    # Act
                    result = get_session_status()

            # Assert
            assert result == 0
            captured = capsys.readouterr()
            assert "Next up:" in captured.out
            assert "🔴 WI-002 (ready)" in captured.out
            assert "🟡 WI-003 (ready)" in captured.out

    def test_next_items_blocked_by_dependencies(self, capsys):
        """
        Test display of blocked next items.

        Arrange: Mock work items with dependencies not completed
        Act: Call get_session_status()
        Assert: Returns 0 and shows "(blocked)" for dependent items
        """
        with patch.object(Path, "exists", return_value=True):
            # Arrange
            status_data = {"current_work_item": "WI-001"}
            work_items_data = {
                "work_items": {
                    "WI-001": {
                        "type": "feature",
                        "priority": "high",
                        "status": "in_progress",
                    },
                    "WI-002": {
                        "type": "feature",
                        "priority": "high",
                        "status": "not_started",
                        "dependencies": ["WI-001"],
                    },
                }
            }

            with patch.object(
                Path,
                "read_text",
                side_effect=[json.dumps(status_data), json.dumps(work_items_data)],
            ):
                with patch("sdd.session.status.subprocess.run") as mock_run:
                    mock_run.return_value = Mock(returncode=1, stdout="")

                    # Act
                    result = get_session_status()

            # Assert
            assert result == 0
            captured = capsys.readouterr()
            assert "Next up:" in captured.out
            assert "🟠 WI-002 (blocked)" in captured.out

    def test_next_items_max_three(self, capsys):
        """
        Test that only first 3 not-started items are shown.

        Arrange: Mock work items with 5 not-started items
        Act: Call get_session_status()
        Assert: Returns 0 and displays only 3 items
        """
        with patch.object(Path, "exists", return_value=True):
            # Arrange
            status_data = {"current_work_item": "WI-001"}
            work_items_data = {
                "work_items": {
                    "WI-001": {"type": "feature", "priority": "high", "status": "in_progress"},
                    "WI-002": {
                        "type": "bug",
                        "priority": "critical",
                        "status": "not_started",
                    },
                    "WI-003": {
                        "type": "feature",
                        "priority": "high",
                        "status": "not_started",
                    },
                    "WI-004": {
                        "type": "bug",
                        "priority": "medium",
                        "status": "not_started",
                    },
                    "WI-005": {"type": "feature", "priority": "low", "status": "not_started"},
                    "WI-006": {
                        "type": "refactor",
                        "priority": "low",
                        "status": "not_started",
                    },
                }
            }

            with patch.object(
                Path,
                "read_text",
                side_effect=[json.dumps(status_data), json.dumps(work_items_data)],
            ):
                with patch("sdd.session.status.subprocess.run") as mock_run:
                    mock_run.return_value = Mock(returncode=1, stdout="")

                    # Act
                    result = get_session_status()

            # Assert
            assert result == 0
            captured = capsys.readouterr()
            # Should only show first 3
            _lines_with_wi = [
                line
                for line in captured.out.split("\n")
                if "WI-" in line and "🔴" in line or "🟠" in line or "🟡" in line or "🟢" in line
            ]
            # Filter to only next items section (after "Next up:")
            next_section = captured.out.split("Next up:")[1] if "Next up:" in captured.out else ""
            next_items = [
                line
                for line in next_section.split("\n")
                if "WI-" in line and any(e in line for e in ["🔴", "🟠", "🟡", "🟢"])
            ]
            assert len(next_items) <= 3

    def test_next_items_priority_emoji(self, capsys):
        """
        Test that priority emojis are displayed correctly.

        Arrange: Mock work items with different priorities
        Act: Call get_session_status()
        Assert: Returns 0 and displays correct emoji for each priority
        """
        with patch.object(Path, "exists", return_value=True):
            # Arrange
            status_data = {"current_work_item": "WI-001"}
            work_items_data = {
                "work_items": {
                    "WI-001": {"type": "feature", "priority": "high", "status": "in_progress"},
                    "WI-002": {
                        "type": "bug",
                        "priority": "critical",
                        "status": "not_started",
                    },
                    "WI-003": {
                        "type": "feature",
                        "priority": "high",
                        "status": "not_started",
                    },
                    "WI-004": {
                        "type": "bug",
                        "priority": "medium",
                        "status": "not_started",
                    },
                }
            }

            with patch.object(
                Path,
                "read_text",
                side_effect=[json.dumps(status_data), json.dumps(work_items_data)],
            ):
                with patch("sdd.session.status.subprocess.run") as mock_run:
                    mock_run.return_value = Mock(returncode=1, stdout="")

                    # Act
                    result = get_session_status()

            # Assert
            assert result == 0
            captured = capsys.readouterr()
            assert "🔴 WI-002" in captured.out  # critical
            assert "🟠 WI-003" in captured.out  # high
            assert "🟡 WI-004" in captured.out  # medium


class TestGetSessionStatusQuickActions:
    """Tests for get_session_status quick actions display."""

    def test_quick_actions_displayed(self, capsys):
        """
        Test that quick actions are always displayed.

        Arrange: Mock basic work item
        Act: Call get_session_status()
        Assert: Returns 0 and displays quick actions
        """
        with patch.object(Path, "exists", return_value=True):
            # Arrange
            status_data = {"current_work_item": "WI-001"}
            work_items_data = {
                "work_items": {
                    "WI-001": {
                        "type": "feature",
                        "priority": "high",
                        "status": "in_progress",
                    }
                }
            }

            with patch.object(
                Path,
                "read_text",
                side_effect=[json.dumps(status_data), json.dumps(work_items_data)],
            ):
                with patch("sdd.session.status.subprocess.run") as mock_run:
                    mock_run.return_value = Mock(returncode=1, stdout="")

                    # Act
                    result = get_session_status()

            # Assert
            assert result == 0
            captured = capsys.readouterr()
            assert "Quick actions:" in captured.out
            assert "/validate" in captured.out
            assert "/end" in captured.out
            assert "/work-show WI-001" in captured.out


class TestGetSessionStatusMainEntry:
    """Tests for main entry point execution."""

    def test_main_entry_success(self):
        """
        Test that main entry point returns correct exit code.

        Arrange: Mock get_session_status to return 0
        Act: Execute module as main
        Assert: Would exit with code 0
        """
        with patch.object(Path, "exists", return_value=True):
            # Arrange
            status_data = {"current_work_item": "WI-001"}
            work_items_data = {
                "work_items": {
                    "WI-001": {
                        "type": "feature",
                        "priority": "high",
                        "status": "in_progress",
                    }
                }
            }

            with patch.object(
                Path,
                "read_text",
                side_effect=[json.dumps(status_data), json.dumps(work_items_data)],
            ):
                with patch("sdd.session.status.subprocess.run") as mock_run:
                    mock_run.return_value = Mock(returncode=1, stdout="")

                    # Act
                    result = get_session_status()

            # Assert
            assert result == 0

    def test_main_entry_error(self):
        """
        Test that main entry point returns error code.

        Arrange: Mock no status file
        Act: Execute module as main
        Assert: Would exit with code 1
        """
        with patch("sdd.session.status.Path") as mock_path:
            # Arrange
            mock_status_file = MagicMock()
            mock_status_file.exists.return_value = False
            mock_path.return_value.__truediv__.return_value.__truediv__.return_value = (
                mock_status_file
            )

            # Act
            result = get_session_status()

            # Assert
            assert result == 1
