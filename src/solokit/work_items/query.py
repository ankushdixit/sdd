#!/usr/bin/env python3
"""
Work Item Query - Listing, filtering, and displaying work items.

Handles work item queries, sorting, and formatted display.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from solokit.core.error_handlers import log_errors
from solokit.core.exceptions import FileOperationError, WorkItemNotFoundError
from solokit.core.logging_config import get_logger
from solokit.core.types import Priority, WorkItemStatus

if TYPE_CHECKING:
    from .repository import WorkItemRepository
from solokit.core.output import get_output

logger = get_logger(__name__)
output = get_output()


class WorkItemQuery:
    """Handles work item queries, filtering, and display"""

    def __init__(self, repository: WorkItemRepository):
        """Initialize query engine with repository

        Args:
            repository: WorkItemRepository instance for data access
        """
        self.repository = repository

    def list_items(
        self,
        status_filter: str | None = None,
        type_filter: str | None = None,
        milestone_filter: str | None = None,
    ) -> dict:
        """List work items with optional filtering

        Args:
            status_filter: Optional status filter
            type_filter: Optional type filter
            milestone_filter: Optional milestone filter

        Returns:
            dict: Dictionary with 'items' list and 'count'
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
            return {"items": [], "count": 0}

        # Apply filters
        filtered_items = {}
        for work_id, item in items.items():
            # Status filter
            if status_filter and item["status"] != status_filter:
                continue

            # Type filter
            if type_filter and item["type"] != type_filter:
                continue

            # Milestone filter
            if milestone_filter and item.get("milestone") != milestone_filter:
                continue

            filtered_items[work_id] = item

        # Check dependency status for each item
        for work_id, item in filtered_items.items():
            item["_blocked"] = self._is_blocked(item, items)
            item["_ready"] = (
                not item["_blocked"] and item["status"] == WorkItemStatus.NOT_STARTED.value
            )

        # Sort items
        sorted_items = self._sort_items(filtered_items)

        # Display
        self._display_items(sorted_items)

        return {"items": sorted_items, "count": len(sorted_items)}

    @log_errors()
    def show_item(self, work_id: str) -> dict[str, Any]:
        """Display detailed information about a work item

        Args:
            work_id: ID of the work item to display

        Returns:
            dict: The work item data

        Raises:
            FileOperationError: If work_items.json doesn't exist
            WorkItemNotFoundError: If work item doesn't exist
        """
        items = self.repository.get_all_work_items()

        if not items:
            raise FileOperationError(
                operation="read",
                file_path=str(self.repository.work_items_file),
                details="No work items found",
            )

        if work_id not in items:
            # Don't log error here - user-facing error message is clear
            raise WorkItemNotFoundError(work_id)

        item = items[work_id]

        # Display header
        output.info("=" * 80)
        output.info(f"Work Item: {work_id}")
        output.info("=" * 80)
        output.info("")

        # Basic info
        output.info(f"Type: {item['type']}")
        output.info(f"Status: {item['status']}")
        output.info(f"Priority: {item['priority']}")
        output.info(f"Created: {item.get('created_at', 'Unknown')[:10]}")
        output.info("")

        # Dependencies
        if item.get("dependencies"):
            output.info("Dependencies:")
            for dep_id in item["dependencies"]:
                if dep_id in items:
                    dep_status = items[dep_id]["status"]
                    icon = "✓" if dep_status == WorkItemStatus.COMPLETED.value else "✗"
                    output.info(f"  {icon} {dep_id} ({dep_status})")
                else:
                    output.info(f"  ? {dep_id} (not found)")
            output.info("")

        # Sessions
        sessions = item.get("sessions", [])
        if sessions:
            output.info(f"Sessions: {len(sessions)}")
            for i, session in enumerate(sessions[-5:], 1):  # Last 5 sessions
                session_num = session.get("session_number", i)
                date = session.get("date", "Unknown")
                duration = session.get("duration", "Unknown")
                notes = session.get("notes", "")
                output.info(f"  {session_num}. {date} ({duration}) - {notes[:50]}")
            output.info("")

        # Git info
        git_info = item.get("git", {})
        if git_info:
            output.info(f"Git Branch: {git_info.get('branch', 'N/A')}")
            commits = git_info.get("commits", [])
            output.info(f"Commits: {len(commits)}")
            output.info("")

        # Specification - use spec_file from work item config
        spec_file_path = item.get("spec_file", f".session/specs/{work_id}.md")
        spec_path = Path(spec_file_path)
        if spec_path.exists():
            output.info("Specification:")
            output.info("-" * 80)
            spec_content = spec_path.read_text()
            # Show first 50 lines (increased to include Acceptance Criteria section)
            lines = spec_content.split("\n")[:50]
            output.info("\n".join(lines))
            if len(spec_content.split("\n")) > 50:
                output.info(f"\n[... see full specification in {spec_file_path}]")
            output.info("")

        # Next steps
        output.info("Next Steps:")
        if item["status"] == WorkItemStatus.NOT_STARTED.value:
            # Check dependencies
            blocked = any(
                items.get(dep_id, {}).get("status") != WorkItemStatus.COMPLETED.value
                for dep_id in item.get("dependencies", [])
            )
            if blocked:
                output.info("- Waiting on dependencies to complete")
            else:
                output.info("- Start working: /start")
        elif item["status"] == WorkItemStatus.IN_PROGRESS.value:
            output.info("- Continue working: /start")
        elif item["status"] == WorkItemStatus.COMPLETED.value:
            output.info("- Work item is complete")

        output.info(f"- Update fields: /work-update {work_id}")
        if item.get("milestone"):
            output.info(f"- View related items: /work-list --milestone {item['milestone']}")
        output.info("")

        return item  # type: ignore[no-any-return]

    def _is_blocked(self, item: dict, all_items: dict) -> bool:
        """Check if work item is blocked by dependencies

        Args:
            item: Work item to check
            all_items: All work items

        Returns:
            bool: True if blocked
        """
        if item["status"] != WorkItemStatus.NOT_STARTED.value:
            return False

        dependencies = item.get("dependencies", [])
        if not dependencies:
            return False

        for dep_id in dependencies:
            if dep_id not in all_items:
                continue
            if all_items[dep_id]["status"] != WorkItemStatus.COMPLETED.value:
                return True

        return False

    def _sort_items(self, items: dict) -> list[dict]:
        """Sort items by priority, dependency status, and date

        Args:
            items: Items to sort

        Returns:
            list: Sorted list of items
        """
        priority_order = {
            Priority.CRITICAL.value: 0,
            Priority.HIGH.value: 1,
            Priority.MEDIUM.value: 2,
            Priority.LOW.value: 3,
        }

        items_list = list(items.values())

        # Sort by:
        # 1. Priority (critical first)
        # 2. Blocked status (ready items first)
        # 3. Status (in_progress first)
        # 4. Creation date (oldest first)
        items_list.sort(
            key=lambda x: (
                priority_order.get(x["priority"], 99),
                x.get("_blocked", False),
                0 if x["status"] == WorkItemStatus.IN_PROGRESS.value else 1,
                x.get("created_at", ""),
            )
        )

        return items_list

    def _display_items(self, items: list[dict]) -> None:
        """Display items with color coding and indicators

        Args:
            items: List of items to display
        """
        if not items:
            output.info("No work items found matching filters.")
            return

        # Count by status
        status_counts = {
            WorkItemStatus.NOT_STARTED.value: 0,
            WorkItemStatus.IN_PROGRESS.value: 0,
            WorkItemStatus.BLOCKED.value: 0,
            WorkItemStatus.COMPLETED.value: 0,
        }

        for item in items:
            # Count by actual status (blocked is a property, not a status)
            status_counts[item["status"]] += 1
            # Also track blocked count separately for display purposes
            if item.get("_blocked"):
                status_counts[WorkItemStatus.BLOCKED.value] += 1

        # Header
        total = len(items)
        output.info(
            f"\nWork Items ({total} total, "
            f"{status_counts[WorkItemStatus.IN_PROGRESS.value]} in progress, "
            f"{status_counts[WorkItemStatus.NOT_STARTED.value]} not started, "
            f"{status_counts[WorkItemStatus.COMPLETED.value]} completed)\n"
        )

        # Group by priority
        priority_groups: dict[str, list[Any]] = {
            Priority.CRITICAL.value: [],
            Priority.HIGH.value: [],
            Priority.MEDIUM.value: [],
            Priority.LOW.value: [],
        }

        for item in items:
            priority = item.get("priority", Priority.MEDIUM.value)
            priority_groups[priority].append(item)

        # Display each priority group
        priority_emoji = {
            Priority.CRITICAL.value: "🔴",
            Priority.HIGH.value: "🟠",
            Priority.MEDIUM.value: "🟡",
            Priority.LOW.value: "🟢",
        }

        for priority in [
            Priority.CRITICAL.value,
            Priority.HIGH.value,
            Priority.MEDIUM.value,
            Priority.LOW.value,
        ]:
            group_items = priority_groups[priority]
            if not group_items:
                continue

            output.info(f"{priority_emoji[priority]} {priority.upper()}")

            for item in group_items:
                status_icon = self._get_status_icon(item)
                work_id = item["id"]

                # Add urgent indicator if applicable
                urgent_indicator = "⚠️  " if item.get("urgent", False) else ""

                # Build status string
                if item.get("_blocked"):
                    # Show blocking dependencies
                    deps = item.get("dependencies", [])[:2]
                    status_str = f"(blocked - waiting on: {', '.join(deps)}) 🚫"
                elif item["status"] == WorkItemStatus.IN_PROGRESS.value:
                    sessions = len(item.get("sessions", []))
                    status_str = f"(in progress, session {sessions})"
                elif item["status"] == WorkItemStatus.COMPLETED.value:
                    sessions = len(item.get("sessions", []))
                    status_str = f"(completed, {sessions} session{'s' if sessions != 1 else ''})"
                elif item.get("_ready"):
                    status_str = "(ready to start) ✓"
                else:
                    status_str = ""

                output.info(f"  {urgent_indicator}{status_icon} {work_id} {status_str}")

            output.info("")

        # Legend
        output.info("Legend:")
        output.info("  [  ] Not started")
        output.info("  [>>] In progress")
        output.info("  [✓] Completed")
        output.info("  ⚠️  Urgent (requires immediate attention)")
        output.info("  🚫 Blocked by dependencies")
        output.info("  ✓ Ready to start")
        output.info("")

    def _get_status_icon(self, item: dict) -> str:
        """Get status icon for work item

        Args:
            item: Work item

        Returns:
            str: Status icon
        """
        if item["status"] == WorkItemStatus.COMPLETED.value:
            return "[✓]"
        elif item["status"] == WorkItemStatus.IN_PROGRESS.value:
            return "[>>]"
        else:
            return "[  ]"
