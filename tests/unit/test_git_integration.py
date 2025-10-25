"""Unit tests for scripts/git_integration.py - Git workflow integration."""

import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

from scripts.git_integration import GitWorkflow

# ============================================================================
# Test GitWorkflow Initialization
# ============================================================================


class TestGitWorkflowInit:
    """Tests for GitWorkflow initialization."""

    def test_init_default_root(self):
        """Test GitWorkflow initialization with default root directory."""
        # Arrange & Act
        with (
            patch.object(Path, "cwd", return_value=Path("/test/root")),
            patch.object(GitWorkflow, "_load_config", return_value={}),
        ):
            workflow = GitWorkflow()

        # Assert
        assert workflow.project_root == Path("/test/root")
        assert workflow.work_items_file == Path("/test/root/.session/tracking/work_items.json")
        assert workflow.config_file == Path("/test/root/.session/config.json")

    def test_init_custom_root(self):
        """Test GitWorkflow initialization with custom root directory."""
        # Arrange
        custom_root = Path("/custom/path")

        # Act
        with patch.object(GitWorkflow, "_load_config", return_value={}):
            workflow = GitWorkflow(project_root=custom_root)

        # Assert
        assert workflow.project_root == custom_root
        assert workflow.work_items_file == Path("/custom/path/.session/tracking/work_items.json")
        assert workflow.config_file == Path("/custom/path/.session/config.json")

    def test_init_loads_config(self):
        """Test that GitWorkflow initialization loads configuration."""
        # Arrange
        mock_config = {"mode": "pr", "auto_push": True}

        # Act
        with patch.object(GitWorkflow, "_load_config", return_value=mock_config):
            workflow = GitWorkflow(Path("/test"))

        # Assert
        assert workflow.config == mock_config


# ============================================================================
# Test Config Loading
# ============================================================================


class TestLoadConfig:
    """Tests for _load_config method."""

    def test_load_config_file_exists(self, tmp_path):
        """Test loading config from existing file."""
        # Arrange
        config_data = {
            "git_workflow": {"mode": "local", "auto_push": False, "auto_create_pr": False}
        }
        config_file = tmp_path / ".session" / "config.json"
        config_file.parent.mkdir(parents=True)
        config_file.write_text(json.dumps(config_data))

        # Act
        workflow = GitWorkflow(project_root=tmp_path)

        # Assert
        assert workflow.config["mode"] == "local"
        assert workflow.config["auto_push"] is False

    def test_load_config_file_missing(self, tmp_path):
        """Test loading default config when file doesn't exist."""
        # Arrange & Act
        workflow = GitWorkflow(project_root=tmp_path)

        # Assert
        assert workflow.config["mode"] == "pr"
        assert workflow.config["auto_push"] is True
        assert workflow.config["auto_create_pr"] is True
        assert workflow.config["delete_branch_after_merge"] is True

    def test_load_config_file_invalid_json(self, tmp_path):
        """Test loading default config when JSON is invalid."""
        # Arrange
        config_file = tmp_path / ".session" / "config.json"
        config_file.parent.mkdir(parents=True)
        config_file.write_text("invalid json{")

        # Act
        workflow = GitWorkflow(project_root=tmp_path)

        # Assert - should fall back to defaults
        assert workflow.config["mode"] == "pr"
        assert workflow.config["auto_push"] is True

    def test_load_config_missing_git_workflow_key(self, tmp_path):
        """Test loading config when git_workflow key is missing."""
        # Arrange
        config_data = {"other_config": {"key": "value"}}
        config_file = tmp_path / ".session" / "config.json"
        config_file.parent.mkdir(parents=True)
        config_file.write_text(json.dumps(config_data))

        # Act
        workflow = GitWorkflow(project_root=tmp_path)

        # Assert - should return empty dict from .get()
        assert workflow.config == {}


# ============================================================================
# Test Check Git Status
# ============================================================================


class TestCheckGitStatus:
    """Tests for check_git_status method."""

    def test_check_git_status_clean(self, tmp_path):
        """Test check_git_status with clean working directory."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=0, stdout="")

        # Act
        with patch("subprocess.run", return_value=mock_result):
            is_clean, msg = workflow.check_git_status()

        # Assert
        assert is_clean is True
        assert msg == "Clean"

    def test_check_git_status_dirty(self, tmp_path):
        """Test check_git_status with uncommitted changes."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=0, stdout=" M file.txt\n")

        # Act
        with patch("subprocess.run", return_value=mock_result):
            is_clean, msg = workflow.check_git_status()

        # Assert
        assert is_clean is False
        assert "not clean" in msg.lower()

    def test_check_git_status_not_git_repo(self, tmp_path):
        """Test check_git_status when not in git repository."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=128, stdout="")

        # Act
        with patch("subprocess.run", return_value=mock_result):
            is_clean, msg = workflow.check_git_status()

        # Assert
        assert is_clean is False
        assert "not a git repository" in msg.lower()

    def test_check_git_status_timeout(self, tmp_path):
        """Test check_git_status when git command times out."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)

        # Act
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("git", 5)):
            is_clean, msg = workflow.check_git_status()

        # Assert
        assert is_clean is False
        assert "timed out" in msg.lower()

    def test_check_git_status_git_not_found(self, tmp_path):
        """Test check_git_status when git is not installed."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)

        # Act
        with patch("subprocess.run", side_effect=FileNotFoundError):
            is_clean, msg = workflow.check_git_status()

        # Assert
        assert is_clean is False
        assert "not found" in msg.lower()


# ============================================================================
# Test Get Current Branch
# ============================================================================


class TestGetCurrentBranch:
    """Tests for get_current_branch method."""

    def test_get_current_branch_success(self, tmp_path):
        """Test getting current branch successfully."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=0, stdout="feature-branch\n")

        # Act
        with patch("subprocess.run", return_value=mock_result):
            branch = workflow.get_current_branch()

        # Assert
        assert branch == "feature-branch"

    def test_get_current_branch_main(self, tmp_path):
        """Test getting current branch when on main."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=0, stdout="main\n")

        # Act
        with patch("subprocess.run", return_value=mock_result):
            branch = workflow.get_current_branch()

        # Assert
        assert branch == "main"

    def test_get_current_branch_detached_head(self, tmp_path):
        """Test getting current branch in detached HEAD state."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=0, stdout="")

        # Act
        with patch("subprocess.run", return_value=mock_result):
            branch = workflow.get_current_branch()

        # Assert
        assert branch == ""

    def test_get_current_branch_git_error(self, tmp_path):
        """Test getting current branch when git command fails."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=128, stdout="")

        # Act
        with patch("subprocess.run", return_value=mock_result):
            branch = workflow.get_current_branch()

        # Assert
        assert branch is None

    def test_get_current_branch_exception(self, tmp_path):
        """Test getting current branch when exception occurs."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)

        # Act
        with patch("subprocess.run", side_effect=Exception("Git error")):
            branch = workflow.get_current_branch()

        # Assert
        assert branch is None


# ============================================================================
# Test Create Branch
# ============================================================================


class TestCreateBranch:
    """Tests for create_branch method."""

    def test_create_branch_success(self, tmp_path):
        """Test creating a new branch successfully."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_get_branch = Mock(return_value="main")
        mock_checkout = Mock(returncode=0, stderr="")

        # Act
        with (
            patch.object(workflow, "get_current_branch", mock_get_branch),
            patch("subprocess.run", return_value=mock_checkout),
        ):
            success, branch_name, parent_branch = workflow.create_branch("feature_foo", 5)

        # Assert
        assert success is True
        assert branch_name == "session-005-feature_foo"
        assert parent_branch == "main"

    def test_create_branch_naming_convention(self, tmp_path):
        """Test that branch name follows session-NNN-work_item_id convention."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_get_branch = Mock(return_value="main")
        mock_checkout = Mock(returncode=0, stderr="")

        # Act
        with (
            patch.object(workflow, "get_current_branch", mock_get_branch),
            patch("subprocess.run", return_value=mock_checkout),
        ):
            success, branch_name, parent = workflow.create_branch("bug_123", 42)

        # Assert
        assert success is True
        assert branch_name == "session-042-bug_123"

    def test_create_branch_captures_parent(self, tmp_path):
        """Test that create_branch captures parent branch before creating new branch."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_get_branch = Mock(return_value="develop")
        mock_checkout = Mock(returncode=0, stderr="")

        # Act
        with (
            patch.object(workflow, "get_current_branch", mock_get_branch),
            patch("subprocess.run", return_value=mock_checkout),
        ):
            success, branch_name, parent_branch = workflow.create_branch("feature_bar", 10)

        # Assert
        assert parent_branch == "develop"

    def test_create_branch_git_error(self, tmp_path):
        """Test creating branch when git command fails."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_get_branch = Mock(return_value="main")
        mock_checkout = Mock(returncode=128, stderr="fatal: branch exists")

        # Act
        with (
            patch.object(workflow, "get_current_branch", mock_get_branch),
            patch("subprocess.run", return_value=mock_checkout),
        ):
            success, msg, parent = workflow.create_branch("feature_dup", 1)

        # Assert
        assert success is False
        assert "failed to create branch" in msg.lower()
        assert parent is None

    def test_create_branch_exception(self, tmp_path):
        """Test creating branch when exception occurs."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_get_branch = Mock(return_value="main")

        # Act
        with (
            patch.object(workflow, "get_current_branch", mock_get_branch),
            patch("subprocess.run", side_effect=Exception("Git error")),
        ):
            result = workflow.create_branch("feature_err", 1)

        # Assert
        assert result[0] is False
        assert "error creating branch" in result[1].lower()


# ============================================================================
# Test Checkout Branch
# ============================================================================


class TestCheckoutBranch:
    """Tests for checkout_branch method."""

    def test_checkout_branch_success(self, tmp_path):
        """Test checking out an existing branch successfully."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=0, stderr="")

        # Act
        with patch("subprocess.run", return_value=mock_result):
            success, msg = workflow.checkout_branch("feature-branch")

        # Assert
        assert success is True
        assert "switched to branch" in msg.lower()

    def test_checkout_branch_not_exists(self, tmp_path):
        """Test checking out a branch that doesn't exist."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=1, stderr="error: pathspec 'missing' did not match")

        # Act
        with patch("subprocess.run", return_value=mock_result):
            success, msg = workflow.checkout_branch("missing-branch")

        # Assert
        assert success is False
        assert "failed to checkout" in msg.lower()

    def test_checkout_branch_exception(self, tmp_path):
        """Test checking out branch when exception occurs."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)

        # Act
        with patch("subprocess.run", side_effect=Exception("Git error")):
            success, msg = workflow.checkout_branch("some-branch")

        # Assert
        assert success is False
        assert "error checking out" in msg.lower()


# ============================================================================
# Test Commit Changes
# ============================================================================


class TestCommitChanges:
    """Tests for commit_changes method."""

    def test_commit_changes_success(self, tmp_path):
        """Test committing changes successfully."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_add = Mock(returncode=0)
        mock_commit = Mock(returncode=0, stderr="")
        mock_sha = Mock(returncode=0, stdout="abc1234567890\n")

        # Act
        with patch("subprocess.run", side_effect=[mock_add, mock_commit, mock_sha]):
            success, commit_sha = workflow.commit_changes("feat: Add new feature")

        # Assert
        assert success is True
        assert commit_sha == "abc1234"

    def test_commit_changes_multiline_message(self, tmp_path):
        """Test committing with multiline commit message."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_add = Mock(returncode=0)
        mock_commit = Mock(returncode=0, stderr="")
        mock_sha = Mock(returncode=0, stdout="def5678\n")
        message = "feat: Add feature\n\nDetailed description here"

        # Act
        with patch("subprocess.run", side_effect=[mock_add, mock_commit, mock_sha]) as mock_run:
            success, commit_sha = workflow.commit_changes(message)

        # Assert
        assert success is True
        assert commit_sha == "def5678"
        # Verify commit message was passed correctly
        assert mock_run.call_args_list[1][0][0] == ["git", "commit", "-m", message]

    def test_commit_changes_nothing_to_commit(self, tmp_path):
        """Test committing when there are no changes."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_add = Mock(returncode=0)
        mock_commit = Mock(returncode=1, stderr="nothing to commit, working tree clean")

        # Act
        with patch("subprocess.run", side_effect=[mock_add, mock_commit]):
            success, msg = workflow.commit_changes("feat: No changes")

        # Assert
        assert success is False
        assert "commit failed" in msg.lower()

    def test_commit_changes_git_error(self, tmp_path):
        """Test committing when git command fails."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_add = Mock(returncode=0)
        mock_commit = Mock(returncode=128, stderr="fatal: unable to commit")

        # Act
        with patch("subprocess.run", side_effect=[mock_add, mock_commit]):
            success, msg = workflow.commit_changes("fix: Bug fix")

        # Assert
        assert success is False
        assert "commit failed" in msg.lower()

    def test_commit_changes_exception(self, tmp_path):
        """Test committing when exception occurs."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)

        # Act
        with patch("subprocess.run", side_effect=Exception("Git error")):
            success, msg = workflow.commit_changes("feat: Feature")

        # Assert
        assert success is False
        assert "error committing" in msg.lower()


# ============================================================================
# Test Push Branch
# ============================================================================


class TestPushBranch:
    """Tests for push_branch method."""

    def test_push_branch_success(self, tmp_path):
        """Test pushing branch to remote successfully."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=0, stderr="")

        # Act
        with patch("subprocess.run", return_value=mock_result):
            success, msg = workflow.push_branch("feature-branch")

        # Assert
        assert success is True
        assert "pushed to remote" in msg.lower()

    def test_push_branch_no_remote(self, tmp_path):
        """Test pushing when no remote is configured."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=128, stderr="fatal: No remote repository specified")

        # Act
        with patch("subprocess.run", return_value=mock_result):
            success, msg = workflow.push_branch("feature-branch")

        # Assert
        assert success is True
        assert "no remote" in msg.lower()

    def test_push_branch_no_upstream(self, tmp_path):
        """Test pushing when no upstream is configured."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(
            returncode=128, stderr="fatal: The current branch has no upstream branch"
        )

        # Act
        with patch("subprocess.run", return_value=mock_result):
            success, msg = workflow.push_branch("feature-branch")

        # Assert
        assert success is True
        assert "no remote" in msg.lower() or "no upstream" in msg.lower()

    def test_push_branch_network_error(self, tmp_path):
        """Test pushing when network error occurs."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=1, stderr="fatal: unable to access")

        # Act
        with patch("subprocess.run", return_value=mock_result):
            success, msg = workflow.push_branch("feature-branch")

        # Assert
        assert success is False
        assert "push failed" in msg.lower()

    def test_push_branch_exception(self, tmp_path):
        """Test pushing when exception occurs."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)

        # Act
        with patch("subprocess.run", side_effect=Exception("Network error")):
            success, msg = workflow.push_branch("feature-branch")

        # Assert
        assert success is False
        assert "error pushing" in msg.lower()


# ============================================================================
# Test Delete Remote Branch
# ============================================================================


class TestDeleteRemoteBranch:
    """Tests for delete_remote_branch method."""

    def test_delete_remote_branch_success(self, tmp_path):
        """Test deleting remote branch successfully."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=0, stderr="")

        # Act
        with patch("subprocess.run", return_value=mock_result):
            success, msg = workflow.delete_remote_branch("feature-branch")

        # Assert
        assert success is True
        assert "deleted remote branch" in msg.lower()

    def test_delete_remote_branch_not_exists(self, tmp_path):
        """Test deleting remote branch that doesn't exist."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=1, stderr="error: remote ref does not exist")

        # Act
        with patch("subprocess.run", return_value=mock_result):
            success, msg = workflow.delete_remote_branch("missing-branch")

        # Assert
        assert success is True  # Not an error if already deleted
        assert "doesn't exist" in msg.lower()

    def test_delete_remote_branch_error(self, tmp_path):
        """Test deleting remote branch when error occurs."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=1, stderr="fatal: unable to delete")

        # Act
        with patch("subprocess.run", return_value=mock_result):
            success, msg = workflow.delete_remote_branch("feature-branch")

        # Assert
        assert success is False
        assert "failed to delete" in msg.lower()

    def test_delete_remote_branch_exception(self, tmp_path):
        """Test deleting remote branch when exception occurs."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)

        # Act
        with patch("subprocess.run", side_effect=Exception("Network error")):
            success, msg = workflow.delete_remote_branch("feature-branch")

        # Assert
        assert success is False
        assert "error deleting" in msg.lower()


# ============================================================================
# Test Push Main to Remote
# ============================================================================


class TestPushMainToRemote:
    """Tests for push_main_to_remote method."""

    def test_push_main_to_remote_success(self, tmp_path):
        """Test pushing main to remote successfully."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=0, stderr="")

        # Act
        with patch("subprocess.run", return_value=mock_result):
            success, msg = workflow.push_main_to_remote()

        # Assert
        assert success is True
        assert "pushed main to remote" in msg.lower()

    def test_push_main_to_remote_custom_branch(self, tmp_path):
        """Test pushing custom branch to remote."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=0, stderr="")

        # Act
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            success, msg = workflow.push_main_to_remote("develop")

        # Assert
        assert success is True
        assert "pushed develop to remote" in msg.lower()
        assert mock_run.call_args[0][0] == ["git", "push", "origin", "develop"]

    def test_push_main_to_remote_error(self, tmp_path):
        """Test pushing main to remote when error occurs."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_result = Mock(returncode=1, stderr="fatal: unable to push")

        # Act
        with patch("subprocess.run", return_value=mock_result):
            success, msg = workflow.push_main_to_remote()

        # Assert
        assert success is False
        assert "failed to push" in msg.lower()

    def test_push_main_to_remote_exception(self, tmp_path):
        """Test pushing main to remote when exception occurs."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)

        # Act
        with patch("subprocess.run", side_effect=Exception("Network error")):
            success, msg = workflow.push_main_to_remote()

        # Assert
        assert success is False
        assert "error pushing" in msg.lower()


# ============================================================================
# Test Create Pull Request
# ============================================================================


class TestCreatePullRequest:
    """Tests for create_pull_request method."""

    def test_create_pull_request_success(self, tmp_path):
        """Test creating pull request successfully."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        work_item = {
            "id": "feature_1",
            "type": "feature",
            "title": "New Feature",
            "description": "Desc",
        }
        mock_gh_check = Mock(returncode=0)
        mock_pr_create = Mock(returncode=0, stdout="https://github.com/user/repo/pull/42\n")

        # Act
        with patch("subprocess.run", side_effect=[mock_gh_check, mock_pr_create]):
            success, msg = workflow.create_pull_request(
                "feature_1", "session-001-feature_1", work_item, 1
            )

        # Assert
        assert success is True
        assert "pr created" in msg.lower()
        assert "github.com" in msg

    def test_create_pull_request_gh_not_installed(self, tmp_path):
        """Test creating PR when gh CLI is not installed."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        work_item = {"id": "feature_1", "type": "feature", "title": "New Feature"}
        mock_gh_check = Mock(returncode=127)

        # Act
        with patch("subprocess.run", return_value=mock_gh_check):
            success, msg = workflow.create_pull_request(
                "feature_1", "session-001-feature_1", work_item, 1
            )

        # Assert
        assert success is False
        assert "gh cli not installed" in msg.lower()

    def test_create_pull_request_gh_error(self, tmp_path):
        """Test creating PR when gh command fails."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        work_item = {"id": "feature_1", "type": "feature", "title": "New Feature"}
        mock_gh_check = Mock(returncode=0)
        mock_pr_create = Mock(returncode=1, stderr="error: authentication failed")

        # Act
        with patch("subprocess.run", side_effect=[mock_gh_check, mock_pr_create]):
            success, msg = workflow.create_pull_request(
                "feature_1", "session-001-feature_1", work_item, 1
            )

        # Assert
        assert success is False
        assert "failed to create pr" in msg.lower()

    def test_create_pull_request_exception(self, tmp_path):
        """Test creating PR when exception occurs."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        work_item = {"id": "feature_1", "type": "feature", "title": "New Feature"}

        # Act
        with patch("subprocess.run", side_effect=Exception("Network error")):
            success, msg = workflow.create_pull_request(
                "feature_1", "session-001-feature_1", work_item, 1
            )

        # Assert
        assert success is False
        assert "error creating pr" in msg.lower()


# ============================================================================
# Test Format PR Title
# ============================================================================


class TestFormatPRTitle:
    """Tests for _format_pr_title method."""

    def test_format_pr_title_default_template(self, tmp_path):
        """Test formatting PR title with default template."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        work_item = {"type": "feature", "title": "Add user authentication"}

        # Act
        title = workflow._format_pr_title(work_item, 5)

        # Assert
        assert "Feature:" in title
        assert "Add user authentication" in title

    def test_format_pr_title_custom_template(self, tmp_path):
        """Test formatting PR title with custom template."""
        # Arrange
        config_data = {"git_workflow": {"pr_title_template": "[{session_num}] {type}: {title}"}}
        config_file = tmp_path / ".session" / "config.json"
        config_file.parent.mkdir(parents=True)
        config_file.write_text(json.dumps(config_data))
        workflow = GitWorkflow(project_root=tmp_path)
        work_item = {"type": "bug", "title": "Fix login issue"}

        # Act
        title = workflow._format_pr_title(work_item, 10)

        # Assert
        assert "[10]" in title
        assert "bug" in title.lower()
        assert "Fix login issue" in title

    def test_format_pr_title_missing_fields(self, tmp_path):
        """Test formatting PR title with missing work item fields."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        work_item = {}  # Empty work item

        # Act
        title = workflow._format_pr_title(work_item, 1)

        # Assert
        assert "Feature:" in title  # Default type
        assert "Work Item" in title  # Default title


# ============================================================================
# Test Format PR Body
# ============================================================================


class TestFormatPRBody:
    """Tests for _format_pr_body method."""

    def test_format_pr_body_default_template(self, tmp_path):
        """Test formatting PR body with default template."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        work_item = {
            "id": "feature_1",
            "description": "Add authentication feature",
            "git": {"commits": ["abc1234", "def5678"]},
        }

        # Act
        body = workflow._format_pr_body(work_item, "feature_1", 5)

        # Assert
        assert "Work Item: feature_1" in body
        assert "Add authentication feature" in body
        assert "Claude Code" in body

    def test_format_pr_body_with_commits(self, tmp_path):
        """Test formatting PR body with commit messages in custom template."""
        # Arrange
        config_data = {
            "git_workflow": {"pr_body_template": "## {work_item_id}\n\nCommits:\n{commit_messages}"}
        }
        config_file = tmp_path / ".session" / "config.json"
        config_file.parent.mkdir(parents=True)
        config_file.write_text(json.dumps(config_data))
        workflow = GitWorkflow(project_root=tmp_path)
        work_item = {
            "id": "bug_1",
            "description": "Fix bug",
            "git": {"commits": ["abc1234", "def5678"]},
        }

        # Act
        body = workflow._format_pr_body(work_item, "bug_1", 3)

        # Assert
        assert "- abc1234" in body
        assert "- def5678" in body

    def test_format_pr_body_no_commits(self, tmp_path):
        """Test formatting PR body with no commits uses default text in custom template."""
        # Arrange
        config_data = {
            "git_workflow": {"pr_body_template": "## {work_item_id}\n\n{commit_messages}"}
        }
        config_file = tmp_path / ".session" / "config.json"
        config_file.parent.mkdir(parents=True)
        config_file.write_text(json.dumps(config_data))
        workflow = GitWorkflow(project_root=tmp_path)
        work_item = {"id": "feature_1", "description": "Feature"}

        # Act
        body = workflow._format_pr_body(work_item, "feature_1", 1)

        # Assert
        assert "See commits for details" in body

    def test_format_pr_body_custom_template(self, tmp_path):
        """Test formatting PR body with custom template."""
        # Arrange
        config_data = {
            "git_workflow": {
                "pr_body_template": "## {work_item_id}\n\nType: {type}\n\n{description}"
            }
        }
        config_file = tmp_path / ".session" / "config.json"
        config_file.parent.mkdir(parents=True)
        config_file.write_text(json.dumps(config_data))
        workflow = GitWorkflow(project_root=tmp_path)
        work_item = {"type": "refactor", "description": "Refactor code"}

        # Act
        body = workflow._format_pr_body(work_item, "refactor_1", 2)

        # Assert
        assert "## refactor_1" in body
        assert "Type: refactor" in body
        assert "Refactor code" in body


# ============================================================================
# Test Merge to Parent
# ============================================================================


class TestMergeToParent:
    """Tests for merge_to_parent method."""

    def test_merge_to_parent_success(self, tmp_path):
        """Test merging branch to parent successfully."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_checkout = Mock(returncode=0)
        mock_merge = Mock(returncode=0, stderr="")
        mock_delete = Mock(returncode=0)

        # Act
        with patch("subprocess.run", side_effect=[mock_checkout, mock_merge, mock_delete]):
            success, msg = workflow.merge_to_parent("feature-branch", "main")

        # Assert
        assert success is True
        assert "merged to main" in msg.lower()
        assert "branch deleted" in msg.lower()

    def test_merge_to_parent_custom_parent(self, tmp_path):
        """Test merging to custom parent branch."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_checkout = Mock(returncode=0)
        mock_merge = Mock(returncode=0, stderr="")
        mock_delete = Mock(returncode=0)

        # Act
        with patch(
            "subprocess.run", side_effect=[mock_checkout, mock_merge, mock_delete]
        ) as mock_run:
            success, msg = workflow.merge_to_parent("feature-branch", "develop")

        # Assert
        assert success is True
        assert "merged to develop" in msg.lower()
        # Verify checkout called with correct parent
        assert mock_run.call_args_list[0][0][0] == ["git", "checkout", "develop"]

    def test_merge_to_parent_merge_conflict(self, tmp_path):
        """Test merging when merge conflict occurs."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)
        mock_checkout = Mock(returncode=0)
        mock_merge = Mock(returncode=1, stderr="CONFLICT: merge conflict in file.txt")

        # Act
        with patch("subprocess.run", side_effect=[mock_checkout, mock_merge]):
            success, msg = workflow.merge_to_parent("feature-branch", "main")

        # Assert
        assert success is False
        assert "merge failed" in msg.lower()

    def test_merge_to_parent_exception(self, tmp_path):
        """Test merging when exception occurs."""
        # Arrange
        workflow = GitWorkflow(project_root=tmp_path)

        # Act
        with patch("subprocess.run", side_effect=Exception("Git error")):
            success, msg = workflow.merge_to_parent("feature-branch", "main")

        # Assert
        assert success is False
        assert "error merging" in msg.lower()


# ============================================================================
# Test Start Work Item
# ============================================================================


class TestStartWorkItem:
    """Tests for start_work_item method."""

    def test_start_work_item_create_new_branch(self, tmp_path):
        """Test starting work item with new branch creation."""
        # Arrange
        work_items_file = tmp_path / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)
        work_items_data = {
            "work_items": {
                "feature_1": {"id": "feature_1", "title": "New Feature", "status": "in_progress"}
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))
        workflow = GitWorkflow(project_root=tmp_path)

        # Act
        with patch.object(
            workflow, "create_branch", return_value=(True, "session-001-feature_1", "main")
        ):
            result = workflow.start_work_item("feature_1", 1)

        # Assert
        assert result["action"] == "created"
        assert result["branch"] == "session-001-feature_1"
        assert result["success"] is True

        # Verify work item was updated
        with open(work_items_file) as f:
            data = json.load(f)
            assert "git" in data["work_items"]["feature_1"]
            assert data["work_items"]["feature_1"]["git"]["branch"] == "session-001-feature_1"
            assert data["work_items"]["feature_1"]["git"]["parent_branch"] == "main"
            assert data["work_items"]["feature_1"]["git"]["status"] == "in_progress"

    def test_start_work_item_resume_existing_branch(self, tmp_path):
        """Test starting work item with existing branch."""
        # Arrange
        work_items_file = tmp_path / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)
        work_items_data = {
            "work_items": {
                "feature_1": {
                    "id": "feature_1",
                    "git": {"branch": "session-001-feature_1", "status": "in_progress"},
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))
        workflow = GitWorkflow(project_root=tmp_path)

        # Act
        with patch.object(workflow, "checkout_branch", return_value=(True, "Switched to branch")):
            result = workflow.start_work_item("feature_1", 1)

        # Assert
        assert result["action"] == "resumed"
        assert result["branch"] == "session-001-feature_1"
        assert result["success"] is True

    def test_start_work_item_create_branch_failure(self, tmp_path):
        """Test starting work item when branch creation fails."""
        # Arrange
        work_items_file = tmp_path / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)
        work_items_data = {"work_items": {"feature_1": {"id": "feature_1"}}}
        work_items_file.write_text(json.dumps(work_items_data))
        workflow = GitWorkflow(project_root=tmp_path)

        # Act
        with patch.object(workflow, "create_branch", return_value=(False, "Branch exists", None)):
            result = workflow.start_work_item("feature_1", 1)

        # Assert
        assert result["action"] == "created"
        assert result["success"] is False
        assert "Branch exists" in result["message"]


# ============================================================================
# Test Complete Work Item
# ============================================================================


class TestCompleteWorkItem:
    """Tests for complete_work_item method."""

    def test_complete_work_item_commit_and_push(self, tmp_path):
        """Test completing work item with commit and push."""
        # Arrange
        work_items_file = tmp_path / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)
        work_items_data = {
            "work_items": {
                "feature_1": {
                    "id": "feature_1",
                    "status": "in_progress",
                    "git": {
                        "branch": "session-001-feature_1",
                        "parent_branch": "main",
                        "status": "in_progress",
                        "commits": [],
                    },
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))
        workflow = GitWorkflow(project_root=tmp_path)

        # Act
        with (
            patch.object(workflow, "commit_changes", return_value=(True, "abc1234")),
            patch.object(workflow, "push_branch", return_value=(True, "Pushed")),
        ):
            result = workflow.complete_work_item("feature_1", "feat: Complete feature", False, 1)

        # Assert
        assert result["success"] is True
        assert result["commit"] == "abc1234"
        assert result["pushed"] is True

        # Verify work item was updated
        with open(work_items_file) as f:
            data = json.load(f)
            assert "abc1234" in data["work_items"]["feature_1"]["git"]["commits"]

    def test_complete_work_item_with_pr_mode(self, tmp_path):
        """Test completing work item with PR creation in pr mode."""
        # Arrange
        work_items_file = tmp_path / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)
        work_items_data = {
            "work_items": {
                "feature_1": {
                    "id": "feature_1",
                    "status": "completed",
                    "git": {
                        "branch": "session-001-feature_1",
                        "parent_branch": "main",
                        "status": "in_progress",
                        "commits": [],
                    },
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))

        config_data = {"git_workflow": {"mode": "pr", "auto_create_pr": True}}
        config_file = tmp_path / ".session" / "config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(json.dumps(config_data))

        workflow = GitWorkflow(project_root=tmp_path)

        # Act
        with (
            patch.object(workflow, "commit_changes", return_value=(True, "abc1234")),
            patch.object(workflow, "push_branch", return_value=(True, "Pushed")),
            patch.object(
                workflow,
                "create_pull_request",
                return_value=(True, "PR created: https://github.com/user/repo/pull/1"),
            ),
        ):
            result = workflow.complete_work_item("feature_1", "feat: Complete", True, 1)

        # Assert
        assert result["success"] is True

        # Verify work item git status updated to pr_created
        with open(work_items_file) as f:
            data = json.load(f)
            assert data["work_items"]["feature_1"]["git"]["status"] == "pr_created"

    def test_complete_work_item_with_local_merge(self, tmp_path):
        """Test completing work item with local merge in local mode."""
        # Arrange
        work_items_file = tmp_path / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)
        work_items_data = {
            "work_items": {
                "feature_1": {
                    "id": "feature_1",
                    "status": "completed",
                    "git": {
                        "branch": "session-001-feature_1",
                        "parent_branch": "main",
                        "status": "in_progress",
                        "commits": [],
                    },
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))

        config_data = {"git_workflow": {"mode": "local", "delete_branch_after_merge": True}}
        config_file = tmp_path / ".session" / "config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(json.dumps(config_data))

        workflow = GitWorkflow(project_root=tmp_path)

        # Act
        with (
            patch.object(workflow, "commit_changes", return_value=(True, "abc1234")),
            patch.object(workflow, "push_branch", return_value=(True, "Pushed")),
            patch.object(workflow, "merge_to_parent", return_value=(True, "Merged")),
            patch.object(workflow, "push_main_to_remote", return_value=(True, "Pushed main")),
            patch.object(workflow, "delete_remote_branch", return_value=(True, "Deleted")),
        ):
            result = workflow.complete_work_item("feature_1", "feat: Complete", True, 1)

        # Assert
        assert result["success"] is True

        # Verify work item git status updated to merged
        with open(work_items_file) as f:
            data = json.load(f)
            assert data["work_items"]["feature_1"]["git"]["status"] == "merged"

    def test_complete_work_item_no_git_tracking(self, tmp_path):
        """Test completing work item without git tracking."""
        # Arrange
        work_items_file = tmp_path / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)
        work_items_data = {"work_items": {"feature_1": {"id": "feature_1", "status": "completed"}}}
        work_items_file.write_text(json.dumps(work_items_data))
        workflow = GitWorkflow(project_root=tmp_path)

        # Act
        result = workflow.complete_work_item("feature_1", "feat: Complete", False, 1)

        # Assert
        assert result["success"] is False
        assert "no git tracking" in result["message"].lower()

    def test_complete_work_item_nothing_to_commit_with_existing_commits(self, tmp_path):
        """Test completing work item when nothing to commit but existing commits exist."""
        # Arrange
        work_items_file = tmp_path / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)
        work_items_data = {
            "work_items": {
                "feature_1": {
                    "id": "feature_1",
                    "status": "in_progress",
                    "git": {
                        "branch": "session-001-feature_1",
                        "parent_branch": "main",
                        "status": "in_progress",
                        "commits": [],
                    },
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))
        workflow = GitWorkflow(project_root=tmp_path)

        mock_git_log = Mock(returncode=0, stdout="abc1234\ndef5678\n")

        # Act
        with (
            patch.object(workflow, "commit_changes", return_value=(False, "nothing to commit")),
            patch.object(workflow, "push_branch", return_value=(True, "Pushed")),
            patch("subprocess.run", return_value=mock_git_log),
        ):
            result = workflow.complete_work_item("feature_1", "feat: Complete", False, 1)

        # Assert
        assert result["success"] is True
        assert "Found 2 existing commit(s)" in result["commit"]

        # Verify commits were added to work item
        with open(work_items_file) as f:
            data = json.load(f)
            assert "abc1234" in data["work_items"]["feature_1"]["git"]["commits"]
            assert "def5678" in data["work_items"]["feature_1"]["git"]["commits"]

    def test_complete_work_item_commit_failure(self, tmp_path):
        """Test completing work item when commit fails."""
        # Arrange
        work_items_file = tmp_path / ".session" / "tracking" / "work_items.json"
        work_items_file.parent.mkdir(parents=True)
        work_items_data = {
            "work_items": {
                "feature_1": {
                    "id": "feature_1",
                    "git": {
                        "branch": "session-001-feature_1",
                        "commits": [],
                    },
                }
            }
        }
        work_items_file.write_text(json.dumps(work_items_data))
        workflow = GitWorkflow(project_root=tmp_path)

        # Act
        with patch.object(workflow, "commit_changes", return_value=(False, "fatal: error")):
            result = workflow.complete_work_item("feature_1", "feat: Complete", False, 1)

        # Assert
        assert result["success"] is False
        assert "commit failed" in result["message"].lower()


# ============================================================================
# Test Main Function
# ============================================================================


class TestMain:
    """Tests for main function."""

    def test_main_prints_status(self, tmp_path, capsys):
        """Test main function prints git status and current branch."""
        # Arrange
        mock_workflow = Mock()
        mock_workflow.check_git_status.return_value = (True, "Clean")
        mock_workflow.get_current_branch.return_value = "main"

        # Act
        with patch("scripts.git_integration.GitWorkflow", return_value=mock_workflow):
            from scripts.git_integration import main

            main()

        # Assert
        captured = capsys.readouterr()
        assert "Git status:" in captured.out
        assert "Current branch:" in captured.out
