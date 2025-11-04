#!/usr/bin/env python3
"""
Generate session briefing for next work item.
Enhanced with full project context loading.

This module has been refactored into a package structure.
All functionality is now in sdd.session.briefing.* modules.
This file maintains the CLI entry point and backward compatibility.
"""

import json
from datetime import datetime
from pathlib import Path

from sdd.core.logging_config import get_logger
from sdd.core.types import WorkItemStatus

# Import from refactored briefing package
from sdd.session.briefing import (
    calculate_days_ago,  # noqa: F401
    check_command_exists,  # noqa: F401
    check_git_status,  # noqa: F401
    determine_git_branch_final_status,  # noqa: F401
    extract_keywords,  # noqa: F401
    extract_section,  # noqa: F401
    finalize_previous_work_item_git_status,
    generate_briefing,
    generate_deployment_briefing,  # noqa: F401
    generate_integration_test_briefing,  # noqa: F401
    generate_previous_work_section,  # noqa: F401
    get_next_work_item,  # noqa: F401
    get_relevant_learnings,  # noqa: F401
    load_current_stack,  # noqa: F401
    load_current_tree,  # noqa: F401
    load_learnings,  # noqa: F401
    load_milestone_context,  # noqa: F401
    load_project_docs,  # noqa: F401
    load_work_item_spec,  # noqa: F401
    load_work_items,  # noqa: F401
    shift_heading_levels,  # noqa: F401
    validate_environment,  # noqa: F401
)

logger = get_logger(__name__)


def main():
    """Main entry point."""
    import argparse

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Start session for work item")
    parser.add_argument(
        "work_item_id",
        nargs="?",
        help="Specific work item ID to start (optional)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force start even if another item is in-progress",
    )
    args = parser.parse_args()

    logger.info("Starting session briefing generation")

    # Ensure .session directory exists
    session_dir = Path(".session")
    if not session_dir.exists():
        logger.error(".session directory not found")
        print("Error: .session directory not found. Run project initialization first.")
        return 1

    # Load data
    work_items_data = load_work_items()
    learnings_data = load_learnings()

    # Determine which work item to start
    if args.work_item_id:
        # User specified a work item explicitly
        item_id = args.work_item_id
        item = work_items_data.get("work_items", {}).get(item_id)

        if not item:
            logger.error("Work item not found: %s", item_id)
            print(f"❌ Error: Work item '{item_id}' not found.")
            print("\nAvailable work items:")
            for wid, wi in work_items_data.get("work_items", {}).items():
                status_emoji = {
                    WorkItemStatus.NOT_STARTED.value: "○",
                    WorkItemStatus.IN_PROGRESS.value: "◐",
                    WorkItemStatus.COMPLETED.value: "✓",
                    WorkItemStatus.BLOCKED.value: "✗",
                }.get(wi["status"], "○")
                print(f"  {status_emoji} {wid} - {wi['title']} ({wi['status']})")
            return 1

        # Check if a DIFFERENT work item is in-progress (excluding the requested one)
        in_progress = [
            (id, wi)
            for id, wi in work_items_data.get("work_items", {}).items()
            if wi["status"] == WorkItemStatus.IN_PROGRESS.value and id != item_id
        ]

        # If another item is in-progress, warn and exit (unless --force)
        if in_progress and not args.force:
            in_progress_id = in_progress[0][0]
            print(f"\n⚠️  Warning: Work item '{in_progress_id}' is currently in-progress.")
            print("Starting a new work item will leave the current one incomplete.\n")
            print("Options:")
            print("1. Complete current work item first: /end")
            print(f"2. Force start new work item: sdd start {item_id} --force")
            print("3. Cancel: Ctrl+C\n")
            logger.warning(
                "Blocked start of %s due to in-progress item: %s (use --force to override)",
                item_id,
                in_progress_id,
            )
            return 1

        # Check dependencies are satisfied
        deps_satisfied = all(
            work_items_data.get("work_items", {}).get(dep_id, {}).get("status")
            == WorkItemStatus.COMPLETED.value
            for dep_id in item.get("dependencies", [])
        )

        if not deps_satisfied:
            unmet_deps = [
                dep_id
                for dep_id in item.get("dependencies", [])
                if work_items_data.get("work_items", {}).get(dep_id, {}).get("status")
                != "completed"
            ]
            logger.error("Work item %s has unmet dependencies: %s", item_id, unmet_deps)
            print(f"❌ Error: Work item '{item_id}' has unmet dependencies:")
            for dep_id in unmet_deps:
                dep = work_items_data.get("work_items", {}).get(dep_id, {})
                print(
                    f"  - {dep_id}: {dep.get('title', 'Unknown')} (status: {dep.get('status', 'unknown')})"
                )
            print("\nPlease complete dependencies first.")
            return 1

        # Note: If requested item is already in-progress, no conflict - just resume it
        logger.info("User explicitly requested work item: %s", item_id)
    else:
        # Use automatic selection
        item_id, item = get_next_work_item(work_items_data)

        if not item_id:
            logger.warning("No available work items found")
            print("No available work items. All dependencies must be satisfied first.")
            return 1

    # Finalize previous work item's git status if starting a new work item
    finalize_previous_work_item_git_status(work_items_data, item_id)

    logger.info("Generating briefing for work item: %s", item_id)
    # Generate briefing
    briefing = generate_briefing(item_id, item, learnings_data)

    # Save briefing
    briefings_dir = session_dir / "briefings"
    briefings_dir.mkdir(exist_ok=True)

    # Determine session number
    # If work item is already in progress, reuse existing session number
    if item.get("status") == WorkItemStatus.IN_PROGRESS.value and item.get("sessions"):
        session_num = item["sessions"][-1]["session_num"]
        logger.info("Resuming existing session %d for work item %s", session_num, item_id)
    else:
        # Create new session number for new work or restarted work
        session_num = (
            max(
                [int(f.stem.split("_")[1]) for f in briefings_dir.glob("session_*.md")],
                default=0,
            )
            + 1
        )
        logger.info("Starting new session %d for work item %s", session_num, item_id)

    # Start git workflow for work item
    try:
        # Import git workflow from new location
        from sdd.git.integration import GitWorkflow

        workflow = GitWorkflow()
        git_result = workflow.start_work_item(item_id, session_num)

        if git_result["success"]:
            if git_result["action"] == "created":
                print(f"✓ Created git branch: {git_result['branch']}\n")
            else:
                print(f"✓ Resumed git branch: {git_result['branch']}\n")
        else:
            print(f"⚠️  Git workflow warning: {git_result['message']}\n")
    except Exception as e:
        print(f"⚠️  Could not start git workflow: {e}\n")

    # Update work item status and session tracking
    work_items_file = session_dir / "tracking" / "work_items.json"
    if work_items_file.exists():
        with open(work_items_file) as f:
            work_items_data = json.load(f)

        # Update work item status
        if item_id in work_items_data["work_items"]:
            work_item = work_items_data["work_items"][item_id]
            work_item["status"] = WorkItemStatus.IN_PROGRESS.value
            work_item["updated_at"] = datetime.now().isoformat()

            # Add session tracking
            if "sessions" not in work_item:
                work_item["sessions"] = []
            work_item["sessions"].append(
                {"session_num": session_num, "started_at": datetime.now().isoformat()}
            )

            # Update metadata counters
            work_items = work_items_data.get("work_items", {})
            work_items_data["metadata"]["total_items"] = len(work_items)
            work_items_data["metadata"]["completed"] = sum(
                1
                for item in work_items.values()
                if item["status"] == WorkItemStatus.COMPLETED.value
            )
            work_items_data["metadata"]["in_progress"] = sum(
                1
                for item in work_items.values()
                if item["status"] == WorkItemStatus.IN_PROGRESS.value
            )
            work_items_data["metadata"]["blocked"] = sum(
                1 for item in work_items.values() if item["status"] == WorkItemStatus.BLOCKED.value
            )
            work_items_data["metadata"]["last_updated"] = datetime.now().isoformat()

            # Save updated work items
            with open(work_items_file, "w") as f:
                json.dump(work_items_data, f, indent=2)

            # Notify that status has been updated
            print(f"✓ Work item status updated: {item_id} → in_progress\n")

    briefing_file = briefings_dir / f"session_{session_num:03d}_briefing.md"

    # Always write briefing file to include fresh context (Enhancement #11 Phase 2)
    # This is critical for in-progress items to show previous work context
    with open(briefing_file, "w") as f:
        f.write(briefing)

    if item.get("status") == WorkItemStatus.IN_PROGRESS.value:
        logger.info("Updated briefing with previous work context: %s", briefing_file)
    else:
        logger.info("Created briefing file: %s", briefing_file)

    # Print briefing (always show it, whether new or existing)
    print(briefing)

    # Update status file
    status_file = session_dir / "tracking" / "status_update.json"
    status = {
        "current_session": session_num,
        "current_work_item": item_id,
        "started_at": datetime.now().isoformat(),
        "status": WorkItemStatus.IN_PROGRESS.value,
    }
    with open(status_file, "w") as f:
        json.dump(status, f, indent=2)

    return 0


if __name__ == "__main__":
    exit(main())
