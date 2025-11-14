#!/usr/bin/env python3
"""
Work Item Updater - Update operations for work items.

Handles field updates with validation, both interactive and non-interactive.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from solokit.core.error_handlers import log_errors
from solokit.core.exceptions import (
    ErrorCode,
    FileOperationError,
    ValidationError,
    WorkItemNotFoundError,
)
from solokit.core.logging_config import get_logger
from solokit.core.types import Priority, WorkItemStatus

if TYPE_CHECKING:
    from .repository import WorkItemRepository
    from .validator import WorkItemValidator
from solokit.core.output import get_output

logger = get_logger(__name__)
output = get_output()


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
            **updates: Field updates (status, priority, milestone, add_dependency, remove_dependency, set_urgent, clear_urgent)

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
                    # Don't log warning here - user-facing error message is clear
                    raise ValidationError(
                        message=f"Invalid status: {value}",
                        code=ErrorCode.INVALID_STATUS,
                        context={"status": value, "valid_statuses": WorkItemStatus.values()},
                        remediation=f"Valid statuses: {', '.join(WorkItemStatus.values())}",
                    )
                old_value = item["status"]
                item["status"] = value
                changes.append(f"  status: {old_value} → {value}")

                # Auto-clear urgent flag when work item is completed
                if value == WorkItemStatus.COMPLETED.value and item.get("urgent", False):
                    item["urgent"] = False
                    self.repository.clear_urgent_flag(work_id)
                    changes.append("  urgent flag: auto-cleared (work item completed)")
                    logger.info("Auto-cleared urgent flag from completed work item: %s", work_id)

            elif field == "priority":
                if value not in self.PRIORITIES:
                    # Don't log warning here - user-facing error message is clear
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
                # Support comma-separated list of dependencies
                deps = item.get("dependencies", [])
                dep_ids = [d.strip() for d in value.split(",") if d.strip()]

                for dep_id in dep_ids:
                    if dep_id not in deps:
                        if self.repository.work_item_exists(dep_id):
                            deps.append(dep_id)
                            changes.append(f"  added dependency: {dep_id}")
                        else:
                            logger.warning("Dependency '%s' not found", dep_id)
                            raise WorkItemNotFoundError(dep_id)
                    else:
                        # Dependency already exists - inform user
                        output.warning(f"Dependency '{dep_id}' already exists (skipped)")

                item["dependencies"] = deps

            elif field == "remove_dependency":
                # Support comma-separated list of dependencies
                deps = item.get("dependencies", [])
                dep_ids = [d.strip() for d in value.split(",") if d.strip()]

                for dep_id in dep_ids:
                    if dep_id in deps:
                        deps.remove(dep_id)
                        changes.append(f"  removed dependency: {dep_id}")

                item["dependencies"] = deps

            elif field == "set_urgent":
                if not item.get("urgent", False):
                    # Check if another item is already urgent
                    existing_urgent = self.repository.get_urgent_work_item()
                    if existing_urgent and existing_urgent["id"] != work_id:
                        # Clear the existing urgent item
                        self.repository.clear_urgent_flag(existing_urgent["id"])
                        output.info(
                            f"Cleared urgent flag from '{existing_urgent['id']}' "
                            f"({existing_urgent['title']})"
                        )

                    item["urgent"] = True
                    changes.append("  urgent flag: set")
                    self.repository.set_urgent_flag(
                        work_id, clear_others=False
                    )  # Already cleared above
                    logger.info("Set urgent flag on work item: %s", work_id)
                else:
                    output.warning("Work item is already marked as urgent (no change made)")

            elif field == "clear_urgent":
                if item.get("urgent", False):
                    item["urgent"] = False
                    changes.append("  urgent flag: cleared")
                    self.repository.clear_urgent_flag(work_id)
                else:
                    output.warning("Work item is not marked as urgent (no change made)")

        if not changes:
            # Don't log here - user-facing error message is clear
            raise ValidationError(
                message="No changes to update",
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
        output.info(f"\nUpdated {work_id}:")
        for change in changes:
            output.info(change)
        output.info("")
