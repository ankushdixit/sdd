#!/usr/bin/env python3
"""
Git workflow integration for Session-Driven Development.

Handles:
- Branch creation for work items
- Branch continuation for multi-session work
- Commit generation
- Push to remote
- Branch merging (local or PR-based)
- PR creation and management
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional


class GitWorkflow:
    """Manage git workflow for sessions."""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.work_items_file = self.project_root / ".session" / "tracking" / "work_items.json"
        self.config_file = self.project_root / ".session" / "config.json"
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Load git workflow configuration."""
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    config = json.load(f)
                    return config.get("git_workflow", {})
            except Exception:
                pass
        # Default configuration if file doesn't exist
        return {
            "mode": "pr",
            "auto_push": True,
            "auto_create_pr": True,
            "delete_branch_after_merge": True,
        }

    def check_git_status(self) -> tuple[bool, str]:
        """Check if working directory is clean."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=5,
            )

            if result.returncode != 0:
                return False, "Not a git repository"

            if result.stdout.strip():
                return False, "Working directory not clean (uncommitted changes)"

            return True, "Clean"

        except subprocess.TimeoutExpired:
            return False, "Git command timed out"
        except FileNotFoundError:
            return False, "Git not found"

    def get_current_branch(self) -> Optional[str]:
        """Get current git branch name."""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=5,
            )

            if result.returncode == 0:
                return result.stdout.strip()

        except:  # noqa: E722
            pass

        return None

    def create_branch(self, work_item_id: str, session_num: int) -> tuple[bool, str, Optional[str]]:
        """Create a new branch for work item. Returns (success, branch_name, parent_branch)."""
        # Capture parent branch BEFORE creating new branch
        parent_branch = self.get_current_branch()
        branch_name = f"session-{session_num:03d}-{work_item_id}"

        try:
            # Create and checkout branch
            result = subprocess.run(
                ["git", "checkout", "-b", branch_name],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=5,
            )

            if result.returncode == 0:
                return True, branch_name, parent_branch
            else:
                return False, f"Failed to create branch: {result.stderr}", None

        except Exception as e:
            return False, f"Error creating branch: {e}"

    def checkout_branch(self, branch_name: str) -> tuple[bool, str]:
        """Checkout existing branch."""
        try:
            result = subprocess.run(
                ["git", "checkout", branch_name],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=5,
            )

            if result.returncode == 0:
                return True, f"Switched to branch {branch_name}"
            else:
                return False, f"Failed to checkout branch: {result.stderr}"

        except Exception as e:
            return False, f"Error checking out branch: {e}"

    def commit_changes(self, message: str) -> tuple[bool, str]:
        """Stage all changes and commit."""
        try:
            # Stage all changes
            subprocess.run(["git", "add", "."], cwd=self.project_root, timeout=10, check=True)

            # Commit
            result = subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=10,
            )

            if result.returncode == 0:
                # Get commit SHA
                sha_result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root,
                    timeout=5,
                )
                commit_sha = sha_result.stdout.strip()[:7]
                return True, commit_sha
            else:
                return False, f"Commit failed: {result.stderr}"

        except Exception as e:
            return False, f"Error committing: {e}"

    def push_branch(self, branch_name: str) -> tuple[bool, str]:
        """Push branch to remote."""
        try:
            result = subprocess.run(
                ["git", "push", "-u", "origin", branch_name],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=30,
            )

            if result.returncode == 0:
                return True, "Pushed to remote"
            else:
                # Check if it's just "no upstream" error
                if "no upstream" in result.stderr.lower() or "no remote" in result.stderr.lower():
                    return True, "No remote configured (local only)"
                return False, f"Push failed: {result.stderr}"

        except Exception as e:
            return False, f"Error pushing: {e}"

    def delete_remote_branch(self, branch_name: str) -> tuple[bool, str]:
        """Delete branch from remote."""
        try:
            result = subprocess.run(
                ["git", "push", "origin", "--delete", branch_name],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=10,
            )

            if result.returncode == 0:
                return True, f"Deleted remote branch {branch_name}"
            else:
                # Not an error if branch doesn't exist on remote
                if "remote ref does not exist" in result.stderr.lower():
                    return True, f"Remote branch {branch_name} doesn't exist (already deleted?)"
                return False, f"Failed to delete remote branch: {result.stderr}"

        except Exception as e:
            return False, f"Error deleting remote branch: {e}"

    def push_main_to_remote(self, branch_name: str = "main") -> tuple[bool, str]:
        """Push main (or other parent branch) to remote after local merge."""
        try:
            result = subprocess.run(
                ["git", "push", "origin", branch_name],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=30,
            )

            if result.returncode == 0:
                return True, f"Pushed {branch_name} to remote"
            else:
                return False, f"Failed to push {branch_name}: {result.stderr}"

        except Exception as e:
            return False, f"Error pushing {branch_name}: {e}"

    def create_pull_request(
        self, work_item_id: str, branch_name: str, work_item: dict, session_num: int
    ) -> tuple[bool, str]:
        """Create a pull request using gh CLI."""
        try:
            # Check if gh CLI is available
            check_gh = subprocess.run(
                ["gh", "--version"],
                capture_output=True,
                cwd=self.project_root,
                timeout=5,
            )

            if check_gh.returncode != 0:
                return False, "gh CLI not installed. Install from: https://cli.github.com/"

            # Generate PR title and body from templates
            title = self._format_pr_title(work_item, session_num)
            body = self._format_pr_body(work_item, work_item_id, session_num)

            # Create PR using gh CLI
            result = subprocess.run(
                ["gh", "pr", "create", "--title", title, "--body", body],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=30,
            )

            if result.returncode == 0:
                pr_url = result.stdout.strip()
                return True, f"PR created: {pr_url}"
            else:
                return False, f"Failed to create PR: {result.stderr}"

        except Exception as e:
            return False, f"Error creating PR: {e}"

    def _format_pr_title(self, work_item: dict, session_num: int) -> str:
        """Format PR title from template."""
        template = self.config.get("pr_title_template", "{type}: {title}")
        return template.format(
            type=work_item.get("type", "feature").title(),
            title=work_item.get("title", "Work Item"),
            work_item_id=work_item.get("id", "unknown"),
            session_num=session_num,
        )

    def _format_pr_body(self, work_item: dict, work_item_id: str, session_num: int) -> str:
        """Format PR body from template."""
        template = self.config.get(
            "pr_body_template",
            "## Work Item: {work_item_id}\n\n{description}\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)",
        )

        # Get recent commits for this work item
        commit_messages = ""
        if "git" in work_item and "commits" in work_item["git"]:
            commits = work_item["git"]["commits"]
            if commits:
                commit_messages = "\n".join([f"- {c}" for c in commits])

        return template.format(
            work_item_id=work_item_id,
            type=work_item.get("type", "feature"),
            title=work_item.get("title", ""),
            description=work_item.get("description", ""),
            session_num=session_num,
            commit_messages=commit_messages if commit_messages else "See commits for details",
        )

    def merge_to_parent(self, branch_name: str, parent_branch: str = "main") -> tuple[bool, str]:
        """Merge branch to parent branch and delete branch."""
        try:
            # Checkout parent branch (not hardcoded main)
            subprocess.run(
                ["git", "checkout", parent_branch],
                capture_output=True,
                cwd=self.project_root,
                timeout=5,
                check=True,
            )

            # Merge
            result = subprocess.run(
                ["git", "merge", "--no-ff", branch_name],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=10,
            )

            if result.returncode == 0:
                # Delete branch
                subprocess.run(
                    ["git", "branch", "-d", branch_name],
                    cwd=self.project_root,
                    timeout=5,
                )
                return True, f"Merged to {parent_branch} and branch deleted"
            else:
                return False, f"Merge failed: {result.stderr}"

        except Exception as e:
            return False, f"Error merging: {e}"

    def start_work_item(self, work_item_id: str, session_num: int) -> dict:
        """Start working on a work item (create or resume branch)."""
        # Load work items
        with open(self.work_items_file) as f:
            data = json.load(f)

        work_item = data["work_items"][work_item_id]

        # Check if work item already has a branch
        if "git" in work_item and work_item["git"].get("status") == "in_progress":
            # Resume existing branch
            branch_name = work_item["git"]["branch"]
            success, msg = self.checkout_branch(branch_name)

            return {
                "action": "resumed",
                "branch": branch_name,
                "success": success,
                "message": msg,
            }
        else:
            # Create new branch
            success, branch_name, parent_branch = self.create_branch(work_item_id, session_num)

            if success:
                # Update work item with git info (including parent branch)
                work_item["git"] = {
                    "branch": branch_name,
                    "parent_branch": parent_branch,  # Store parent for merging
                    "created_at": datetime.now().isoformat(),
                    "status": "in_progress",
                    "commits": [],
                }

                # Save updated work items
                with open(self.work_items_file, "w") as f:
                    json.dump(data, f, indent=2)

            return {
                "action": "created",
                "branch": branch_name,
                "success": success,
                "message": branch_name
                if success
                else branch_name,  # branch_name is error msg on failure
            }

    def complete_work_item(
        self, work_item_id: str, commit_message: str, merge: bool = False, session_num: int = 1
    ) -> dict:
        """Complete work on a work item (commit, push, optionally merge or create PR).

        Behavior depends on git_workflow.mode config:
        - "pr": Commit, push, create pull request (no local merge)
        - "local": Commit, push, merge locally, push main, delete remote branch
        """
        # Load work items
        with open(self.work_items_file) as f:
            data = json.load(f)

        work_item = data["work_items"][work_item_id]

        if "git" not in work_item:
            return {
                "success": False,
                "message": "Work item has no git tracking (may be single-session item)",
            }

        branch_name = work_item["git"]["branch"]
        workflow_mode = self.config.get("mode", "pr")

        # Step 1: Commit changes
        success, commit_sha = self.commit_changes(commit_message)
        if not success:
            return {"success": False, "message": f"Commit failed: {commit_sha}"}

        # Update work item commits
        work_item["git"]["commits"].append(commit_sha)

        # Step 2: Push to remote (if enabled)
        push_success, push_msg = self.push_branch(branch_name)

        # Step 3: Handle completion based on workflow mode
        if merge and work_item["status"] == "completed":
            if workflow_mode == "pr":
                # PR Mode: Create pull request (no local merge)
                pr_success, pr_msg = False, "PR creation skipped (auto_create_pr disabled)"

                if self.config.get("auto_create_pr", True):
                    pr_success, pr_msg = self.create_pull_request(
                        work_item_id, branch_name, work_item, session_num
                    )

                if pr_success:
                    work_item["git"]["status"] = "pr_created"
                    work_item["git"]["pr_url"] = pr_msg.split(": ")[-1] if ": " in pr_msg else ""
                else:
                    work_item["git"]["status"] = "ready_for_pr"

                message = f"Committed {commit_sha}, Pushed to remote. {pr_msg}"

            else:
                # Local Mode: Merge locally, push main, delete remote branch
                parent_branch = work_item["git"].get("parent_branch", "main")

                # Merge locally
                merge_success, merge_msg = self.merge_to_parent(branch_name, parent_branch)

                if merge_success:
                    # Push merged main to remote
                    push_main_success, push_main_msg = self.push_main_to_remote(parent_branch)

                    # Delete remote branch if configured
                    if self.config.get("delete_branch_after_merge", True):
                        delete_success, delete_msg = self.delete_remote_branch(branch_name)
                    else:
                        delete_msg = "Remote branch kept (delete_branch_after_merge disabled)"

                    work_item["git"]["status"] = "merged"
                    message = f"Committed {commit_sha}, {merge_msg}, {push_main_msg}, {delete_msg}"
                else:
                    work_item["git"]["status"] = "ready_to_merge"
                    message = f"Committed {commit_sha}, ⚠️  {merge_msg} - Manual merge required"
        else:
            # Work not complete or merge not requested
            work_item["git"]["status"] = (
                "ready_to_merge" if work_item["status"] == "completed" else "in_progress"
            )
            message = f"Committed {commit_sha}, {push_msg}"

        # Save updated work items
        with open(self.work_items_file, "w") as f:
            json.dump(data, f, indent=2)

        return {
            "success": True,
            "commit": commit_sha,
            "pushed": push_success,
            "message": message,
        }


def main():
    """CLI entry point for testing."""
    workflow = GitWorkflow()

    # Check status
    is_clean, msg = workflow.check_git_status()
    print(f"Git status: {msg}")

    current_branch = workflow.get_current_branch()
    print(f"Current branch: {current_branch}")


if __name__ == "__main__":
    main()
