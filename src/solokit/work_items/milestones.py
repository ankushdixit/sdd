#!/usr/bin/env python3
"""
Milestone Manager - Milestone creation and progress tracking.

Handles milestone CRUD operations and progress calculation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from solokit.core.error_handlers import log_errors
from solokit.core.exceptions import ErrorCode, ValidationError
from solokit.core.logging_config import get_logger
from solokit.core.types import WorkItemStatus

if TYPE_CHECKING:
    from .repository import WorkItemRepository
from solokit.core.output import get_output

logger = get_logger(__name__)
output = get_output()


class MilestoneManager:
    """Handles milestone management operations"""

    def __init__(self, repository: WorkItemRepository):
        """Initialize milestone manager with repository

        Args:
            repository: WorkItemRepository instance for data access
        """
        self.repository = repository

    @log_errors()
    def create(
        self, name: str, title: str, description: str, target_date: str | None = None
    ) -> None:
        """Create a new milestone

        Args:
            name: Milestone name (unique identifier)
            title: Milestone title
            description: Milestone description
            target_date: Optional target completion date

        Raises:
            ValidationError: If milestone with this name already exists
        """
        if self.repository.milestone_exists(name):
            logger.error("Milestone '%s' already exists", name)
            raise ValidationError(
                message=f"Milestone '{name}' already exists",
                code=ErrorCode.WORK_ITEM_ALREADY_EXISTS,
                context={"milestone_name": name},
                remediation="Choose a different milestone name",
            )

        self.repository.add_milestone(name, title, description, target_date)
        logger.info("Created milestone: %s", name)
        output.info(f"✓ Created milestone: {name}")

    def get_progress(self, milestone_name: str) -> dict:
        """Calculate milestone progress

        Args:
            milestone_name: Name of the milestone

        Returns:
            dict: Progress statistics including total, completed, in_progress, not_started, percent
        """
        items = self.repository.get_all_work_items()

        # Filter items in this milestone
        milestone_items = [
            item for item in items.values() if item.get("milestone") == milestone_name
        ]

        if not milestone_items:
            return {
                "total": 0,
                "completed": 0,
                "in_progress": 0,
                "not_started": 0,
                "percent": 0,
            }

        total = len(milestone_items)
        completed = sum(
            1 for item in milestone_items if item["status"] == WorkItemStatus.COMPLETED.value
        )
        in_progress = sum(
            1 for item in milestone_items if item["status"] == WorkItemStatus.IN_PROGRESS.value
        )
        not_started = sum(
            1 for item in milestone_items if item["status"] == WorkItemStatus.NOT_STARTED.value
        )
        percent = int((completed / total) * 100) if total > 0 else 0

        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "not_started": not_started,
            "percent": percent,
        }

    def list_all(self) -> None:
        """List all milestones with progress"""
        milestones = self.repository.get_all_milestones()

        if not milestones:
            output.info("No milestones found.")
            return

        output.info("\nMilestones:\n")

        for name, milestone in milestones.items():
            progress = self.get_progress(name)
            percent = progress["percent"]

            # Progress bar
            bar_length = 20
            filled = int(bar_length * percent / 100)
            bar = "█" * filled + "░" * (bar_length - filled)

            output.info(f"{milestone['title']}")
            output.info(f"  [{bar}] {percent}%")
            output.info(
                f"  {progress['completed']}/{progress['total']} complete, "
                f"{progress['in_progress']} in progress"
            )

            if milestone.get("target_date"):
                output.info(f"  Target: {milestone['target_date']}")
            output.info("")
