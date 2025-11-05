#!/usr/bin/env python3
"""
Work Item Updater - Update operations for work items.

Handles field updates with validation, both interactive and non-interactive.
"""

from __future__ import annotations

import sys
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sdd.core.error_handlers import log_errors
from sdd.core.exceptions import (
    ErrorCode,
    FileOperationError,
    ValidationError,
    WorkItemNotFoundError,
)
from sdd.core.logging_config import get_logger
from sdd.core.types import Priority, WorkItemStatus

if TYPE_CHECKING:
    from .repository import WorkItemRepository
    from .validator import WorkItemValidator

logger = get_logger(__name__)


class WorkItemUpdater:
    """Handles work item update operations"""

    PRIORITIES = Priority.values()

    def __init__(self, repository: WorkItemRepository, validator: WorkItemValidator | None = None):
        """Initialize updater with repository and optional validator

        Args:
            repository: WorkItemRepository instance for data access
            validator: Optional WorkItemValidator for validation
        """
        self.repository = repository
        self.validator = validator

    @log_errors()
    def update(self, work_id: str, **updates: Any) -> None:
        """Update work item fields

        Args:
            work_id: ID of the work item to update
            **updates: Field updates (status, priority, milestone, add_dependency, remove_dependency)

        Raises:
            FileOperationError: If work_items.json doesn't exist
            WorkItemNotFoundError: If work item doesn't exist
            ValidationError: If invalid status or priority provided
        """
        items = self.repository.get_all_work_items()

        if not items:
            raise FileOperationError(
                operation="read",
                file_path=str(self.repository.work_items_file),
                details="No work items found",
            )

        if work_id not in items:
            raise WorkItemNotFoundError(work_id)

        item = items[work_id]
        changes = []

        # Apply updates
        for field, value in updates.items():
            if field == "status":
                if value not in WorkItemStatus.values():
                    logger.warning("Invalid status: %s", value)
                    raise ValidationError(
                        message=f"Invalid status: {value}",
                        code=ErrorCode.INVALID_STATUS,
                        context={"status": value, "valid_statuses": WorkItemStatus.values()},
                        remediation=f"Valid statuses: {', '.join(WorkItemStatus.values())}",
                    )
                old_value = item["status"]
                item["status"] = value
                changes.append(f"  status: {old_value} → {value}")

            elif field == "priority":
                if value not in self.PRIORITIES:
                    logger.warning("Invalid priority: %s", value)
                    raise ValidationError(
                        message=f"Invalid priority: {value}",
                        code=ErrorCode.INVALID_PRIORITY,
                        context={"priority": value, "valid_priorities": self.PRIORITIES},
                        remediation=f"Valid priorities: {', '.join(self.PRIORITIES)}",
                    )
                old_value = item["priority"]
                item["priority"] = value
                changes.append(f"  priority: {old_value} → {value}")

            elif field == "milestone":
                old_value = item.get("milestone", "(none)")
                item["milestone"] = value
                changes.append(f"  milestone: {old_value} → {value}")

            elif field == "add_dependency":
                deps = item.get("dependencies", [])
                if value not in deps:
                    if self.repository.work_item_exists(value):
                        deps.append(value)
                        item["dependencies"] = deps
                        changes.append(f"  added dependency: {value}")
                    else:
                        logger.warning("Dependency '%s' not found", value)
                        raise WorkItemNotFoundError(value)

            elif field == "remove_dependency":
                deps = item.get("dependencies", [])
                if value in deps:
                    deps.remove(value)
                    item["dependencies"] = deps
                    changes.append(f"  removed dependency: {value}")

        if not changes:
            logger.info("No changes made to %s", work_id)
            raise ValidationError(
                message="No changes made",
                code=ErrorCode.MISSING_REQUIRED_FIELD,
                context={"work_item_id": work_id},
                remediation="Provide valid field updates",
            )

        # Record update
        item.setdefault("update_history", []).append(
            {"timestamp": datetime.now().isoformat(), "changes": changes}
        )

        # Save - pass the entire updated item as a dict of updates
        self.repository.update_work_item(work_id, item)

        # Success - user-facing output
        print(f"\nUpdated {work_id}:")
        for change in changes:
            print(change)
        print()

    @log_errors()
    def update_interactive(self, work_id: str) -> None:
        """Interactive work item update

        Args:
            work_id: ID of work item to update

        Raises:
            FileOperationError: If work_items.json doesn't exist
            ValidationError: If running in non-interactive environment
            WorkItemNotFoundError: If work item doesn't exist
        """
        items = self.repository.get_all_work_items()

        if not items:
            raise FileOperationError(
                operation="read",
                file_path=str(self.repository.work_items_file),
                details="No work items found",
            )

        # Check if running in non-interactive environment
        if not sys.stdin.isatty():
            logger.error("Cannot run interactive update in non-interactive environment")
            raise ValidationError(
                message="Cannot run interactive work item update in non-interactive mode",
                code=ErrorCode.INVALID_COMMAND,
                remediation=(
                    "Please use command-line arguments instead:\n"
                    "  sdd work-update <work_id> --status <status>\n"
                    "  sdd work-update <work_id> --priority <priority>\n"
                    "  sdd work-update <work_id> --milestone <milestone>"
                ),
            )

        if work_id not in items:
            raise WorkItemNotFoundError(work_id)

        item = items[work_id]

        print(f"\nUpdate Work Item: {work_id}\n")
        print("Current values:")
        print(f"  Status: {item['status']}")
        print(f"  Priority: {item['priority']}")
        print(f"  Milestone: {item.get('milestone', '(none)')}")
        print()

        print("What would you like to update?")
        print("1. Status")
        print("2. Priority")
        print("3. Milestone")
        print("4. Add dependency")
        print("5. Remove dependency")
        print("6. Cancel")
        print()

        try:
            choice = input("Your choice: ").strip()

            if choice == "1":
                status = input("New status (not_started/in_progress/blocked/completed): ").strip()
                self.update(work_id, status=status)
            elif choice == "2":
                priority = input("New priority (critical/high/medium/low): ").strip()
                self.update(work_id, priority=priority)
            elif choice == "3":
                milestone = input("Milestone name: ").strip()
                self.update(work_id, milestone=milestone)
            elif choice == "4":
                dep = input("Dependency ID to add: ").strip()
                self.update(work_id, add_dependency=dep)
            elif choice == "5":
                dep = input("Dependency ID to remove: ").strip()
                self.update(work_id, remove_dependency=dep)
            else:
                logger.info("Interactive update cancelled")
                raise ValidationError(
                    message="Interactive update cancelled",
                    code=ErrorCode.INVALID_COMMAND,
                    remediation="Select a valid option (1-6)",
                )
        except EOFError:
            logger.warning("EOFError during interactive update")
            raise ValidationError(
                message="Interactive input unavailable",
                code=ErrorCode.INVALID_COMMAND,
                remediation="Use command-line arguments instead",
            )
