"""
Tests for git status finalization when switching work items.

Tests the fix for Bug: Git Branch Status Not Finalized When Switching Work Items
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_git_env(tmp_path):
    """Create a mock .session environment with completed work items."""
    session_dir = tmp_path / ".session"
    tracking_dir = session_dir / "tracking"
    specs_dir = session_dir / "specs"
    briefings_dir = session_dir / "briefings"

    session_dir.mkdir()
    tracking_dir.mkdir()
    specs_dir.mkdir()
    briefings_dir.mkdir()

    # Create mock work items with git tracking
    work_items = {
        "work_items": {
            "item_completed_with_stale_git": {
                "id": "item_completed_with_stale_git",
                "title": "Completed Item With Stale Git Status",
                "type": "feature",
                "status": "completed",
                "priority": "high",
                "dependencies": [],
                "git": {
                    "branch": "session-001-item_completed_with_stale_git",
                    "parent_branch": "main",
                    "status": "in_progress",  # Stale - should be updated
                },
                "sessions": [{"session_num": 1, "started_at": "2025-01-01T00:00:00"}],
            },
            "item_new": {
                "id": "item_new",
                "title": "New Item to Start",
                "type": "bug",
                "status": "not_started",
                "priority": "medium",
                "dependencies": [],
            },
            "item_in_progress": {
                "id": "item_in_progress",
                "title": "In Progress Item",
                "type": "feature",
                "status": "in_progress",
                "priority": "high",
                "dependencies": [],
                "git": {
                    "branch": "session-002-item_in_progress",
                    "parent_branch": "main",
                    "status": "in_progress",  # Should NOT be finalized
                },
                "sessions": [{"session_num": 2, "started_at": "2025-01-02T00:00:00"}],
            },
            "item_completed_no_git": {
                "id": "item_completed_no_git",
                "title": "Completed Item Without Git",
                "type": "bug",
                "status": "completed",
                "priority": "low",
                "dependencies": [],
            },
        },
        "metadata": {
            "total_items": 4,
            "completed": 2,
            "in_progress": 1,
            "blocked": 0,
        },
    }

    work_items_file = tracking_dir / "work_items.json"
    with open(work_items_file, "w") as f:
        json.dump(work_items, f, indent=2)

    # Create mock learnings
    learnings = {"learnings": []}
    learnings_file = tracking_dir / "learnings.json"
    with open(learnings_file, "w") as f:
        json.dump(learnings, f, indent=2)

    # Create mock stack and tree files
    (tracking_dir / "stack.txt").write_text("Test Stack")
    (tracking_dir / "tree.txt").write_text("Test Tree")

    # Create spec files
    for item_id in work_items["work_items"].keys():
        spec_file = specs_dir / f"{item_id}.md"
        spec_file.write_text(f"# {item_id}\n\nTest specification")

    return tmp_path


def test_determine_git_branch_final_status_merged(monkeypatch):
    """Test git status detection when branch is merged."""
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from scripts.briefing_generator import determine_git_branch_final_status

    branch_name = "session-001-feature_test"
    git_info = {"parent_branch": "main"}

    # Mock subprocess to simulate merged branch
    def mock_run(cmd, **kwargs):
        result = MagicMock()
        if "branch" in cmd and "--merged" in cmd:
            result.returncode = 0
            result.stdout = f"  {branch_name}\n  another-branch\n"
        return result

    with patch("subprocess.run", side_effect=mock_run):
        status = determine_git_branch_final_status(branch_name, git_info)

    assert status == "merged"


def test_determine_git_branch_final_status_pr_created(monkeypatch):
    """Test git status detection when PR is created (open)."""
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from scripts.briefing_generator import determine_git_branch_final_status

    branch_name = "session-002-feature_test"
    git_info = {"parent_branch": "main"}

    # Mock subprocess to simulate branch not merged but PR exists
    def mock_run(cmd, **kwargs):
        result = MagicMock()
        if "branch" in cmd and "--merged" in cmd:
            result.returncode = 0
            result.stdout = ""
        elif "gh" in cmd and "pr" in cmd:
            result.returncode = 0
            result.stdout = '[{"number": 123, "state": "OPEN"}]'
        return result

    with patch("subprocess.run", side_effect=mock_run):
        status = determine_git_branch_final_status(branch_name, git_info)

    assert status == "pr_created"


def test_determine_git_branch_final_status_pr_closed(monkeypatch):
    """Test git status detection when PR is closed without merge."""
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from scripts.briefing_generator import determine_git_branch_final_status

    branch_name = "session-003-feature_test"
    git_info = {"parent_branch": "main"}

    # Mock subprocess to simulate closed PR
    def mock_run(cmd, **kwargs):
        result = MagicMock()
        if "branch" in cmd and "--merged" in cmd:
            result.returncode = 0
            result.stdout = ""
        elif "gh" in cmd and "pr" in cmd:
            result.returncode = 0
            result.stdout = '[{"number": 124, "state": "CLOSED"}]'
        return result

    with patch("subprocess.run", side_effect=mock_run):
        status = determine_git_branch_final_status(branch_name, git_info)

    assert status == "pr_closed"


def test_determine_git_branch_final_status_pr_merged(monkeypatch):
    """Test git status detection when PR shows merged state."""
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from scripts.briefing_generator import determine_git_branch_final_status

    branch_name = "session-004-feature_test"
    git_info = {"parent_branch": "main"}

    # Mock subprocess to simulate merged PR
    def mock_run(cmd, **kwargs):
        result = MagicMock()
        if "branch" in cmd and "--merged" in cmd:
            result.returncode = 0
            result.stdout = ""
        elif "gh" in cmd and "pr" in cmd:
            result.returncode = 0
            result.stdout = '[{"number": 125, "state": "MERGED"}]'
        return result

    with patch("subprocess.run", side_effect=mock_run):
        status = determine_git_branch_final_status(branch_name, git_info)

    assert status == "merged"


def test_determine_git_branch_final_status_ready_for_pr_local(monkeypatch):
    """Test git status detection when branch exists locally but no PR."""
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from scripts.briefing_generator import determine_git_branch_final_status

    branch_name = "session-005-feature_test"
    git_info = {"parent_branch": "main"}

    # Mock subprocess to simulate local branch only
    def mock_run(cmd, **kwargs):
        result = MagicMock()
        if "branch" in cmd and "--merged" in cmd:
            result.returncode = 0
            result.stdout = ""
        elif "gh" in cmd and "pr" in cmd:
            # gh CLI not found or no PR
            raise FileNotFoundError()
        elif "show-ref" in cmd:
            result.returncode = 0
            result.stdout = f"abc123 refs/heads/{branch_name}"
        return result

    with patch("subprocess.run", side_effect=mock_run):
        status = determine_git_branch_final_status(branch_name, git_info)

    assert status == "ready_for_pr"


def test_determine_git_branch_final_status_ready_for_pr_remote(monkeypatch):
    """Test git status detection when branch exists remotely but no PR."""
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from scripts.briefing_generator import determine_git_branch_final_status

    branch_name = "session-006-feature_test"
    git_info = {"parent_branch": "main"}

    # Mock subprocess to simulate remote branch only
    def mock_run(cmd, **kwargs):
        result = MagicMock()
        if "branch" in cmd and "--merged" in cmd:
            result.returncode = 0
            result.stdout = ""
        elif "gh" in cmd and "pr" in cmd:
            raise FileNotFoundError()
        elif "show-ref" in cmd:
            result.returncode = 1  # Not found locally
        elif "ls-remote" in cmd:
            result.returncode = 0
            result.stdout = f"def456 refs/heads/{branch_name}"
        return result

    with patch("subprocess.run", side_effect=mock_run):
        status = determine_git_branch_final_status(branch_name, git_info)

    assert status == "ready_for_pr"


def test_determine_git_branch_final_status_deleted(monkeypatch):
    """Test git status detection when branch is deleted."""
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from scripts.briefing_generator import determine_git_branch_final_status

    branch_name = "session-007-feature_test"
    git_info = {"parent_branch": "main"}

    # Mock subprocess to simulate deleted branch
    def mock_run(cmd, **kwargs):
        result = MagicMock()
        if "branch" in cmd and "--merged" in cmd:
            result.returncode = 0
            result.stdout = ""
        elif "gh" in cmd and "pr" in cmd:
            raise FileNotFoundError()
        elif "show-ref" in cmd:
            result.returncode = 1  # Not found locally
        elif "ls-remote" in cmd:
            result.returncode = 0
            result.stdout = ""  # Not found remotely
        return result

    with patch("subprocess.run", side_effect=mock_run):
        status = determine_git_branch_final_status(branch_name, git_info)

    assert status == "deleted"


def test_finalize_previous_work_item_git_status(mock_git_env, capsys, monkeypatch):
    """Test finalization of previous work item's git status when starting new work item."""
    # Change to mock directory
    monkeypatch.chdir(mock_git_env)

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from scripts.briefing_generator import finalize_previous_work_item_git_status

    # Load work items
    work_items_file = mock_git_env / ".session" / "tracking" / "work_items.json"
    with open(work_items_file) as f:
        work_items_data = json.load(f)

    # Mock git commands to simulate merged branch
    def mock_run(cmd, **kwargs):
        result = MagicMock()
        if "branch" in cmd and "--merged" in cmd:
            result.returncode = 0
            result.stdout = "  session-001-item_completed_with_stale_git\n"
        return result

    with patch("subprocess.run", side_effect=mock_run):
        # Finalize when starting item_new
        finalize_previous_work_item_git_status(work_items_data, "item_new")

    # Check output message
    captured = capsys.readouterr()
    assert "Finalized git status for previous work item" in captured.out
    assert "item_completed_with_stale_git → merged" in captured.out

    # Verify work_items.json was updated
    with open(work_items_file) as f:
        updated_data = json.load(f)

    assert updated_data["work_items"]["item_completed_with_stale_git"]["git"]["status"] == "merged"


def test_finalize_only_completed_work_items(mock_git_env, monkeypatch):
    """Test that only completed work items with stale git status are finalized."""
    monkeypatch.chdir(mock_git_env)

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from scripts.briefing_generator import finalize_previous_work_item_git_status

    # Load work items
    work_items_file = mock_git_env / ".session" / "tracking" / "work_items.json"
    with open(work_items_file) as f:
        work_items_data = json.load(f)

    # Get original in_progress item git status
    original_status = work_items_data["work_items"]["item_in_progress"]["git"]["status"]

    # Mock git commands
    def mock_run(cmd, **kwargs):
        result = MagicMock()
        result.returncode = 0
        result.stdout = ""
        return result

    with patch("subprocess.run", side_effect=mock_run):
        # Finalize when starting item_new
        finalize_previous_work_item_git_status(work_items_data, "item_new")

    # Reload to check updates
    with open(work_items_file) as f:
        updated_data = json.load(f)

    # In-progress item should NOT be finalized (should keep original status)
    assert updated_data["work_items"]["item_in_progress"]["git"]["status"] == original_status


def test_finalize_skips_work_item_without_git_branch(mock_git_env, capsys, monkeypatch):
    """Test finalization skips work items without git branch."""
    monkeypatch.chdir(mock_git_env)

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from scripts.briefing_generator import finalize_previous_work_item_git_status

    # Modify work items to have completed item without git branch at top
    work_items_file = mock_git_env / ".session" / "tracking" / "work_items.json"
    with open(work_items_file) as f:
        work_items_data = json.load(f)

    # Remove git info from completed item
    del work_items_data["work_items"]["item_completed_with_stale_git"]["git"]
    with open(work_items_file, "w") as f:
        json.dump(work_items_data, f, indent=2)

    # Reload
    with open(work_items_file) as f:
        work_items_data = json.load(f)

    # Finalize when starting item_new
    finalize_previous_work_item_git_status(work_items_data, "item_new")

    # Should not crash and should skip gracefully
    captured = capsys.readouterr()
    # No finalization message should be shown
    assert "Finalized git status" not in captured.out


def test_finalize_does_not_run_when_resuming_same_item(mock_git_env, capsys, monkeypatch):
    """Test finalization does not run when resuming the same work item."""
    monkeypatch.chdir(mock_git_env)

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from scripts.briefing_generator import finalize_previous_work_item_git_status

    # Load work items
    work_items_file = mock_git_env / ".session" / "tracking" / "work_items.json"
    with open(work_items_file) as f:
        work_items_data = json.load(f)

    # Get original git status
    original_status = work_items_data["work_items"]["item_completed_with_stale_git"]["git"][
        "status"
    ]

    # Mock git commands
    def mock_run(cmd, **kwargs):
        result = MagicMock()
        result.returncode = 0
        result.stdout = ""
        return result

    with patch("subprocess.run", side_effect=mock_run):
        # Try to finalize when "starting" the same completed item
        # (This should not happen in practice, but tests the logic)
        finalize_previous_work_item_git_status(work_items_data, "item_completed_with_stale_git")

    # Should not finalize the same item
    captured = capsys.readouterr()
    assert "Finalized git status" not in captured.out

    # Status should remain unchanged
    with open(work_items_file) as f:
        updated_data = json.load(f)
    assert (
        updated_data["work_items"]["item_completed_with_stale_git"]["git"]["status"]
        == original_status
    )


def test_gh_cli_not_available_graceful_fallback(monkeypatch):
    """Test graceful handling when gh CLI is not available."""
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from scripts.briefing_generator import determine_git_branch_final_status

    branch_name = "session-008-feature_test"
    git_info = {"parent_branch": "main"}

    # Mock subprocess to simulate gh CLI not found
    def mock_run(cmd, **kwargs):
        result = MagicMock()
        if "branch" in cmd and "--merged" in cmd:
            result.returncode = 0
            result.stdout = ""
        elif "gh" in cmd:
            # gh CLI not available
            raise FileNotFoundError("gh command not found")
        elif "show-ref" in cmd:
            result.returncode = 0
            result.stdout = f"abc123 refs/heads/{branch_name}"
        return result

    with patch("subprocess.run", side_effect=mock_run):
        # Should fall back to checking local branch
        status = determine_git_branch_final_status(branch_name, git_info)

    # Should still work and detect branch as ready_for_pr
    assert status == "ready_for_pr"
