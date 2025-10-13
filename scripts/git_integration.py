#!/usr/bin/env python3
"""
Git workflow integration for Session-Driven Development.

Handles:
- Branch creation for work items
- Branch continuation for multi-session work
- Commit generation
- Push to remote
- Branch merging
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple


class GitWorkflow:
    """Manage git workflow for sessions."""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.work_items_file = (
            self.project_root / ".session" / "tracking" / "work_items.json"
        )

    def check_git_status(self) -> Tuple[bool, str]:
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

    def create_branch(self, work_item_id: str, session_num: int) -> Tuple[bool, str]:
        """Create a new branch for work item."""
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
                return True, branch_name
            else:
                return False, f"Failed to create branch: {result.stderr}"

        except Exception as e:
            return False, f"Error creating branch: {e}"

    def checkout_branch(self, branch_name: str) -> Tuple[bool, str]:
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

    def commit_changes(self, message: str) -> Tuple[bool, str]:
        """Stage all changes and commit."""
        try:
            # Stage all changes
            subprocess.run(
                ["git", "add", "."], cwd=self.project_root, timeout=10, check=True
            )

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

    def push_branch(self, branch_name: str) -> Tuple[bool, str]:
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
                if (
                    "no upstream" in result.stderr.lower()
                    or "no remote" in result.stderr.lower()
                ):
                    return True, "No remote configured (local only)"
                return False, f"Push failed: {result.stderr}"

        except Exception as e:
            return False, f"Error pushing: {e}"

    def merge_to_main(self, branch_name: str) -> Tuple[bool, str]:
        """Merge branch to main and delete branch."""
        try:
            # Checkout main
            subprocess.run(
                ["git", "checkout", "main"],
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
                return True, "Merged to main and branch deleted"
            else:
                return False, f"Merge failed: {result.stderr}"

        except Exception as e:
            return False, f"Error merging: {e}"

    def start_work_item(self, work_item_id: str, session_num: int) -> Dict:
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
            success, branch_name = self.create_branch(work_item_id, session_num)

            if success:
                # Update work item with git info
                work_item["git"] = {
                    "branch": branch_name,
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
        self, work_item_id: str, commit_message: str, merge: bool = False
    ) -> Dict:
        """Complete work on a work item (commit, push, optionally merge)."""
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

        # Commit changes
        success, commit_sha = self.commit_changes(commit_message)
        if not success:
            return {"success": False, "message": f"Commit failed: {commit_sha}"}

        # Update work item commits
        work_item["git"]["commits"].append(commit_sha)

        # Push to remote
        push_success, push_msg = self.push_branch(branch_name)

        # Merge if requested and work complete
        if merge:
            merge_success, merge_msg = self.merge_to_main(branch_name)
            if merge_success:
                work_item["git"]["status"] = "merged"
            else:
                work_item["git"]["status"] = "ready_to_merge"
                merge_msg = f"⚠️  {merge_msg} - Manual merge required"
        else:
            work_item["git"]["status"] = (
                "ready_to_merge"
                if work_item["status"] == "completed"
                else "in_progress"
            )

        # Save updated work items
        with open(self.work_items_file, "w") as f:
            json.dump(data, f, indent=2)

        return {
            "success": True,
            "commit": commit_sha,
            "pushed": push_success,
            "merged": merge if merge else False,
            "message": f"Committed {commit_sha}, " + (merge_msg if merge else push_msg),
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
