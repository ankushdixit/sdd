#!/usr/bin/env python3
"""Display current session status."""

import json
import subprocess
from datetime import datetime
from pathlib import Path


def get_session_status():
    """Get current session status."""
    session_dir = Path(".session")
    status_file = session_dir / "tracking" / "status_update.json"

    if not status_file.exists():
        print("No active session.")
        return 1

    # Load status
    status = json.loads(status_file.read_text())
    work_item_id = status.get("current_work_item")

    if not work_item_id:
        print("No active work item in this session.")
        return 1

    # Load work item
    work_items_file = session_dir / "tracking" / "work_items.json"
    data = json.loads(work_items_file.read_text())
    item = data["work_items"].get(work_item_id)

    if not item:
        print(f"Work item {work_item_id} not found.")
        return 1

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
        result = subprocess.run(
            ["git", "diff", "--name-status", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0 and result.stdout:
            lines = result.stdout.strip().split("\n")
            print(f"Files Changed ({len(lines)}):")
            for line in lines[:10]:  # Show first 10
                print(f"  {line}")
            if len(lines) > 10:
                print(f"  ... and {len(lines) - 10} more")
            print()
    except Exception:
        pass

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
            completed = sum(1 for i in milestone_items if i["status"] == "completed")
            percent = int((completed / total) * 100) if total > 0 else 0

            in_prog = sum(1 for i in milestone_items if i["status"] == "in_progress")
            not_started = sum(1 for i in milestone_items if i["status"] == "not_started")

            print(f"Milestone: {milestone_name} ({percent}% complete)")
            print(f"  Related items: {in_prog} in progress, {not_started} not started")
            print()

    # Next items
    print("Next up:")
    items = data["work_items"]
    not_started = [(wid, i) for wid, i in items.items() if i["status"] == "not_started"][:3]

    priority_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}

    for wid, i in not_started:
        emoji = priority_emoji.get(i["priority"], "")
        # Check if blocked
        blocked = any(
            items.get(dep_id, {}).get("status") != "completed"
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
