#!/usr/bin/env python3
"""
Work Item Scheduler - Work queue and next item selection.

Handles finding the next work item to start based on dependencies and priority.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sdd.core.logging_config import get_logger
from sdd.core.types import Priority, WorkItemStatus

if TYPE_CHECKING:
    from .repository import WorkItemRepository

logger = get_logger(__name__)


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

        Returns:
            dict: Next work item to start, or None if none available
        """
        items = self.repository.get_all_work_items()

        if not items:
            print("No work items found.")
            return None

        # Filter to not_started items
        not_started = {
            wid: item
            for wid, item in items.items()
            if item["status"] == WorkItemStatus.NOT_STARTED.value
        }

        if not not_started:
            print("No work items available to start.")
            print("All items are either in progress or completed.")
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
            print("No work items ready to start. All have unmet dependencies.\n")
            print("Blocked items:")
            for work_id, item, blocking in blocked_items:
                print(f"  🔴 {work_id} - Blocked by: {', '.join(blocking)}")
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
        """Display the next recommended work item

        Args:
            next_id: ID of next item
            next_item: Next item data
            ready_items: List of ready items
            blocked_items: List of blocked items
            all_items: All work items
        """
        print("\nNext Recommended Work Item:")
        print("=" * 80)
        print()

        priority_emoji = {
            Priority.CRITICAL.value: "🔴",
            Priority.HIGH.value: "🟠",
            Priority.MEDIUM.value: "🟡",
            Priority.LOW.value: "🟢",
        }

        emoji = priority_emoji.get(next_item["priority"], "")
        print(f"{emoji} {next_item['priority'].upper()}: {next_item['title']}")
        print(f"ID: {next_id}")
        print(f"Type: {next_item['type']}")
        print(f"Priority: {next_item['priority']}")
        print("Ready to start: Yes ✓")
        print()

        # Dependencies
        deps = next_item.get("dependencies", [])
        if deps:
            print("Dependencies: All satisfied")
            for dep_id in deps:
                print(f"  ✓ {dep_id} (completed)")
        else:
            print("Dependencies: None")
        print()

        # Estimated effort
        estimated = next_item.get("estimated_effort", "Unknown")
        print(f"Estimated effort: {estimated}")
        print()

        print("To start: /start")
        print()

        # Show other items
        if len(ready_items) > 1 or blocked_items:
            print("Other items waiting:")
            for work_id, item in ready_items[1:3]:  # Show next 2 ready items
                emoji = priority_emoji.get(item["priority"], "")
                print(f"  {emoji} {work_id} - Ready ({item['priority']} priority)")

            for work_id, item, blocking in blocked_items[:2]:  # Show 2 blocked items
                print(f"  🔴 {work_id} - Blocked by: {', '.join(blocking[:2])}")
            print()
