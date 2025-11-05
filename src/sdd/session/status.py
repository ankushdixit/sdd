#!/usr/bin/env python3
"""Display current session status."""

import json
import logging
from datetime import datetime
from pathlib import Path

from sdd.core.command_runner import CommandRunner
from sdd.core.exceptions import (
    FileNotFoundError,
    FileOperationError,
    SessionNotFoundError,
    ValidationError,
    WorkItemNotFoundError,
)
from sdd.core.types import Priority, WorkItemStatus

logger = logging.getLogger(__name__)


def get_session_status():
    """
    Get current session status.

    Loads and displays the current session status including:
    - Work item information
    - Time elapsed
    - Git changes
    - Milestone progress
    - Next items

    Returns:
        int: Exit code (0 for success, error code for failure)

    Raises:
        SessionNotFoundError: If no active session exists
        FileNotFoundError: If required session files are missing
        FileOperationError: If file read operations fail
        ValidationError: If session data is invalid
        WorkItemNotFoundError: If work item doesn't exist
    """
    session_dir = Path(".session")
    status_file = session_dir / "tracking" / "status_update.json"

    if not status_file.exists():
        raise SessionNotFoundError()

    # Load status
    try:
        status = json.loads(status_file.read_text())
    except json.JSONDecodeError as e:
        raise FileOperationError(
            operation="read",
            file_path=str(status_file),
            details=f"Invalid JSON: {e}",
            cause=e,
        )
    except OSError as e:
        raise FileOperationError(
            operation="read",
            file_path=str(status_file),
            details=str(e),
            cause=e,
        )

    work_item_id = status.get("current_work_item")

    if not work_item_id:
        raise ValidationError(
            message="No active work item in this session",
            context={"status_file": str(status_file)},
            remediation="Start a work item with 'sdd start <work_item_id>'",
        )

    # Load work item
    work_items_file = session_dir / "tracking" / "work_items.json"

    if not work_items_file.exists():
        raise FileNotFoundError(
            file_path=str(work_items_file),
            file_type="work items",
        )

    try:
        data = json.loads(work_items_file.read_text())
    except json.JSONDecodeError as e:
        raise FileOperationError(
            operation="read",
            file_path=str(work_items_file),
            details=f"Invalid JSON: {e}",
            cause=e,
        )
    except OSError as e:
        raise FileOperationError(
            operation="read",
            file_path=str(work_items_file),
            details=str(e),
            cause=e,
        )

    item = data["work_items"].get(work_item_id)

    if not item:
        raise WorkItemNotFoundError(work_item_id)

    print("\nCurrent Session Status")
    print("=" * 80)
    print()

    # Work item info
    print(f"Work Item: {work_item_id}")
    print(f"Type: {item['type']}")
    print(f"Priority: {item['priority']}")

    sessions = len(item.get("sessions", []))
    estimated = item.get("estimated_effort", "Unknown")
    print(f"Session: {sessions} (of estimated {estimated})")
    print()

    # Time elapsed (if session start time recorded)
    session_start = status.get("session_start")
    if session_start:
        start_time = datetime.fromisoformat(session_start)
        elapsed = datetime.now() - start_time
        hours = int(elapsed.total_seconds() // 3600)
        minutes = int((elapsed.total_seconds() % 3600) // 60)
        print(f"Time Elapsed: {hours}h {minutes}m")
        print()

    # Git changes
    try:
        runner = CommandRunner(default_timeout=5)
        result = runner.run(["git", "diff", "--name-status", "HEAD"])

        if result.success and result.stdout:
            lines = result.stdout.strip().split("\n")
            print(f"Files Changed ({len(lines)}):")
            for line in lines[:10]:  # Show first 10
                print(f"  {line}")
            if len(lines) > 10:
                print(f"  ... and {len(lines) - 10} more")
            print()
    except Exception as e:
        # Git operations are optional for status display
        # Log but don't fail if git command fails
        logger.debug(f"Failed to get git changes: {e}")

    # Git branch
    git_info = item.get("git", {})
    if git_info:
        branch = git_info.get("branch", "N/A")
        commits = len(git_info.get("commits", []))
        print(f"Git Branch: {branch}")
        print(f"Commits: {commits}")
        print()

    # Milestone
    milestone_name = item.get("milestone")
    if milestone_name:
        milestones = data.get("milestones", {})
        milestone = milestones.get(milestone_name)
        if milestone:
            # Calculate progress (simplified)
            milestone_items = [
                i for i in data["work_items"].values() if i.get("milestone") == milestone_name
            ]
            total = len(milestone_items)
            completed = sum(
                1 for i in milestone_items if i["status"] == WorkItemStatus.COMPLETED.value
            )
            percent = int((completed / total) * 100) if total > 0 else 0

            in_prog = sum(
                1 for i in milestone_items if i["status"] == WorkItemStatus.IN_PROGRESS.value
            )
            not_started = sum(
                1 for i in milestone_items if i["status"] == WorkItemStatus.NOT_STARTED.value
            )

            print(f"Milestone: {milestone_name} ({percent}% complete)")
            print(f"  Related items: {in_prog} in progress, {not_started} not started")
            print()

    # Next items
    print("Next up:")
    items = data["work_items"]
    not_started = [
        (wid, i) for wid, i in items.items() if i["status"] == WorkItemStatus.NOT_STARTED.value
    ][:3]

    priority_emoji = {
        Priority.CRITICAL.value: "🔴",
        Priority.HIGH.value: "🟠",
        Priority.MEDIUM.value: "🟡",
        Priority.LOW.value: "🟢",
    }

    for wid, i in not_started:
        emoji = priority_emoji.get(i["priority"], "")
        # Check if blocked
        blocked = any(
            items.get(dep_id, {}).get("status") != WorkItemStatus.COMPLETED.value
            for dep_id in i.get("dependencies", [])
        )
        status_str = "(blocked)" if blocked else "(ready)"
        print(f"  {emoji} {wid} {status_str}")
    print()

    # Quick actions
    print("Quick actions:")
    print("  - Validate session: /validate")
    print("  - Complete session: /end")
    print(f"  - View work item: /work-show {work_item_id}")
    print()

    return 0


if __name__ == "__main__":
    exit(get_session_status())
