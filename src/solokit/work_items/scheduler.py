#!/usr/bin/env python3
"""
Work Item Scheduler - Work queue and next item selection.

Handles finding the next work item to start based on dependencies and priority.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from solokit.core.logging_config import get_logger
from solokit.core.types import Priority, WorkItemStatus

if TYPE_CHECKING:
    from .repository import WorkItemRepository
from solokit.core.output import get_output

logger = get_logger(__name__)
output = get_output()


class WorkItemScheduler:
    """Handles work item scheduling and queue management"""

    def __init__(self, repository: WorkItemRepository):
        """Initialize scheduler with repository

        Args:
            repository: WorkItemRepository instance for data access
        """
        self.repository = repository

    def get_next(self) -> dict[str, Any] | None:
        """Find next work item to start based on dependencies and priority

        Urgent items are always prioritized first, regardless of dependencies or priority.

        Returns:
            dict: Next work item to start, or None if none available
        """
        items = self.repository.get_all_work_items()

        if not items:
            output.info("⚠️ No work items found in this project\n")
            output.info("To get started:")
            output.info(
                "  1. Create a work item: sk work-new --type feature --title '...' --priority high"
            )
            output.info("  2. Or use /work-new in Claude Code for interactive creation\n")
            output.info("💡 Work items help track your development tasks and sessions")
            return None

        # Check for urgent items first (highest priority, ignores dependencies)
        urgent_item = self.repository.get_urgent_work_item()
        if urgent_item and urgent_item.get("status") == WorkItemStatus.NOT_STARTED.value:
            output.info("\n⚠️  URGENT ITEM DETECTED\n")
            output.info(f"ID: {urgent_item.get('id', 'unknown')}")
            output.info(f"Title: {urgent_item.get('title', 'Unknown')}")
            output.info(f"Type: {urgent_item.get('type', 'unknown')}")
            output.info(f"Priority: {urgent_item.get('priority', 'unknown')}")
            output.info("\nThis item requires immediate attention and overrides normal priority.")
            output.info(f"To start: /start {urgent_item.get('id', '')}\n")
            return urgent_item

        # Filter to not_started items
        not_started = {
            wid: item
            for wid, item in items.items()
            if item["status"] == WorkItemStatus.NOT_STARTED.value
        }

        if not not_started:
            output.info("No work items available to start.")
            output.info("All items are either in progress or completed.")
            return None

        # Check dependencies and categorize
        ready_items = []
        blocked_items = []

        for work_id, item in not_started.items():
            is_blocked = self._is_blocked(item, items)
            if is_blocked:
                # Find what's blocking
                blocking = [
                    dep_id
                    for dep_id in item.get("dependencies", [])
                    if items.get(dep_id, {}).get("status") != WorkItemStatus.COMPLETED.value
                ]
                blocked_items.append((work_id, item, blocking))
            else:
                ready_items.append((work_id, item))

        if not ready_items:
            output.info("No work items ready to start. All have unmet dependencies.\n")
            output.info("Blocked items:")
            for work_id, item, blocking in blocked_items:
                output.info(f"  🔴 {work_id} - Blocked by: {', '.join(blocking)}")
            return None

        # Sort ready items by priority
        priority_order = {
            Priority.CRITICAL.value: 0,
            Priority.HIGH.value: 1,
            Priority.MEDIUM.value: 2,
            Priority.LOW.value: 3,
        }
        ready_items.sort(key=lambda x: priority_order.get(x[1]["priority"], 99))

        # Get top item
        next_id, next_item = ready_items[0]

        # Display
        self._display_next_item(next_id, next_item, ready_items, blocked_items, items)

        return next_item  # type: ignore[no-any-return]

    def _is_blocked(self, item: dict, all_items: dict) -> bool:
        """Check if work item is blocked by dependencies

        Args:
            item: Work item to check
            all_items: All work items

        Returns:
            bool: True if blocked
        """
        dependencies = item.get("dependencies", [])
        if not dependencies:
            return False

        for dep_id in dependencies:
            if dep_id not in all_items:
                continue
            if all_items[dep_id]["status"] != WorkItemStatus.COMPLETED.value:
                return True

        return False

    def _display_next_item(
        self,
        next_id: str,
        next_item: dict,
        ready_items: list,
        blocked_items: list,
        all_items: dict,
    ) -> None:
        """Display the next recommended work item in a table format

        Args:
            next_id: ID of next item
            next_item: Next item data
            ready_items: List of ready items
            blocked_items: List of blocked items
            all_items: All work items
        """
        output.info("\n📋 Next Recommended Work Items:")
        output.info("")

        priority_emoji = {
            Priority.CRITICAL.value: "🔴",
            Priority.HIGH.value: "🟠",
            Priority.MEDIUM.value: "🟡",
            Priority.LOW.value: "🟢",
        }

        # Build table rows
        rows = []

        # Add ready items first (top one will be recommended)
        for idx, (work_id, item) in enumerate(ready_items[:5]):  # Show top 5 ready items
            emoji = priority_emoji.get(item["priority"], "")
            title = item["title"][:30] + "..." if len(item["title"]) > 30 else item["title"]
            marker = "→" if idx == 0 else " "  # Arrow for recommended item
            rows.append(
                {
                    "marker": marker,
                    "id": work_id,
                    "type": item["type"],
                    "priority": f"{emoji} {item['priority']}",
                    "status": "✓ ready",
                    "blockers": "0",
                    "title": title,
                }
            )

        # Add blocked items
        for work_id, item, blocking in blocked_items[:3]:  # Show top 3 blocked items
            title = item["title"][:30] + "..." if len(item["title"]) > 30 else item["title"]
            blocker_count = str(len(blocking))
            rows.append(
                {
                    "marker": " ",
                    "id": work_id,
                    "type": item["type"],
                    "priority": f"{priority_emoji.get(item['priority'], '')} {item['priority']}",
                    "status": "blocked",
                    "blockers": blocker_count,
                    "title": title,
                }
            )

        # Calculate column widths
        max_id_len = max((len(r["id"]) for r in rows), default=10)
        max_type_len = max((len(r["type"]) for r in rows), default=8)
        max_title_len = max((len(r["title"]) for r in rows), default=20)

        # Print table header
        header = (
            f"  {'ID':<{max_id_len}} | {'Type':<{max_type_len}} | "
            f"{'Priority':<10} | {'Status':<9} | {'Blocks':<6} | {'Title':<{max_title_len}}"
        )
        separator = "  " + "-" * len(header.replace("  ", ""))
        output.info(header)
        output.info(separator)

        # Print table rows
        for row in rows:
            line = (
                f"{row['marker']} {row['id']:<{max_id_len}} | {row['type']:<{max_type_len}} | "
                f"{row['priority']:<10} | {row['status']:<9} | {row['blockers']:<6} | {row['title']:<{max_title_len}}"
            )
            output.info(line)

        output.info("")
        output.info(f"💡 Top recommendation: {next_id}")
        output.info(f"   To start: /start {next_id}")
        output.info("")
