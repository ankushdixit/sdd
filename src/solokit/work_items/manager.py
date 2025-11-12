#!/usr/bin/env python3
"""
Work Item Manager - Main orchestrator for work item operations.

Delegates to specialized modules for different concerns:
- creator: Work item creation and prompts
- repository: Data access and persistence
- validator: Validation logic
- query: Listing, filtering, and display
- updater: Update operations
- scheduler: Work queue and next item selection
- milestones: Milestone management
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from solokit.core.constants import get_session_dir, get_specs_dir
from solokit.core.types import Priority, WorkItemType

from .creator import WorkItemCreator
from .milestones import MilestoneManager
from .query import WorkItemQuery
from .repository import WorkItemRepository
from .scheduler import WorkItemScheduler
from .updater import WorkItemUpdater
from .validator import WorkItemValidator


class WorkItemManager:
    """Main orchestrator for work item operations"""

    WORK_ITEM_TYPES = WorkItemType.values()
    PRIORITIES = Priority.values()

    def __init__(self, project_root: Path | None = None):
        """Initialize manager with dependency injection

        Args:
            project_root: Optional project root path (defaults to current directory)
        """
        self.project_root = project_root or Path.cwd()
        self.session_dir = get_session_dir(self.project_root)

        # Initialize components
        self.repository = WorkItemRepository(self.session_dir)
        self.creator = WorkItemCreator(self.repository)
        self.validator = WorkItemValidator()
        self.query = WorkItemQuery(self.repository)
        self.updater = WorkItemUpdater(self.repository, self.validator)
        self.scheduler = WorkItemScheduler(self.repository)
        self.milestones = MilestoneManager(self.repository)

        # Legacy compatibility - maintain these paths for backward compatibility
        self.work_items_file = self.repository.work_items_file
        self.specs_dir = get_specs_dir(self.project_root)
        self.templates_dir = Path(__file__).parent.parent / "templates"

    # Delegate creation methods
    def create_work_item_from_args(
        self,
        work_type: str,
        title: str,
        priority: str = "high",
        dependencies: str = "",
        urgent: bool = False,
    ) -> str:
        """Create work item from command-line arguments

        Args:
            work_type: Type of work item (feature, bug, refactor, etc.)
            title: Title of the work item
            priority: Priority level (critical, high, medium, low)
            dependencies: Comma-separated dependency IDs
            urgent: Whether this item requires immediate attention

        Returns:
            str: The created work item ID

        Raises:
            ValidationError: If work type is invalid
            WorkItemAlreadyExistsError: If work item with generated ID already exists
            FileOperationError: If spec file creation or tracking update fails
        """
        return self.creator.create_from_args(work_type, title, priority, dependencies, urgent)

    # Delegate query methods
    def list_work_items(
        self,
        status_filter: str | None = None,
        type_filter: str | None = None,
        milestone_filter: str | None = None,
    ) -> dict:
        """List work items with optional filters

        Args:
            status_filter: Optional status filter
            type_filter: Optional type filter
            milestone_filter: Optional milestone filter

        Returns:
            dict: Dictionary with 'items' list and 'count'
        """
        return self.query.list_items(status_filter, type_filter, milestone_filter)

    def show_work_item(self, work_id: str) -> dict[str, Any]:
        """Show detailed information about a work item

        Args:
            work_id: ID of the work item to display

        Returns:
            dict: The work item data

        Raises:
            FileOperationError: If work_items.json doesn't exist
            WorkItemNotFoundError: If work item doesn't exist
        """
        return self.query.show_item(work_id)

    # Delegate update methods
    def update_work_item(self, work_id: str, **updates: Any) -> None:
        """Update a work item

        Args:
            work_id: ID of the work item to update
            **updates: Field updates (status, priority, milestone, add_dependency, remove_dependency)

        Raises:
            FileOperationError: If work_items.json doesn't exist
            WorkItemNotFoundError: If work item doesn't exist
            ValidationError: If invalid status or priority provided
        """
        return self.updater.update(work_id, **updates)

    # Delegate scheduler methods
    def get_next_work_item(self) -> dict[str, Any] | None:
        """Get next recommended work item based on dependencies and priority

        Returns:
            dict: Next work item to start, or None if none available
        """
        return self.scheduler.get_next()

    # Delegate validation methods
    def validate_integration_test(self, work_item: dict) -> None:
        """Validate integration test work item

        Args:
            work_item: Work item dictionary to validate

        Raises:
            FileOperationError: If spec file not found
            ValidationError: If spec validation fails (with validation errors in context)
        """
        return self.validator.validate_integration_test(work_item)

    def validate_deployment(self, work_item: dict) -> None:
        """Validate deployment work item

        Args:
            work_item: Work item dictionary to validate

        Raises:
            FileOperationError: If spec file not found
            ValidationError: If spec validation fails (with validation errors in context)
        """
        return self.validator.validate_deployment(work_item)

    # Delegate milestone methods
    def create_milestone(
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
            FileOperationError: If saving milestone fails
        """
        return self.milestones.create(name, title, description, target_date)

    def get_milestone_progress(self, milestone_name: str) -> dict:
        """Get milestone progress

        Args:
            milestone_name: Name of the milestone

        Returns:
            dict: Progress statistics including total, completed, in_progress, not_started, percent
        """
        return self.milestones.get_progress(milestone_name)

    def list_milestones(self) -> None:
        """List all milestones with progress"""
        return self.milestones.list_all()


def main() -> int:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Work Item Manager")
    parser.add_argument(
        "--type",
        help="Work item type (feature, bug, refactor, security, integration_test, deployment)",
    )
    parser.add_argument("--title", help="Work item title")
    parser.add_argument("--priority", default="high", help="Priority (critical, high, medium, low)")
    parser.add_argument("--dependencies", default="", help="Comma-separated dependency IDs")

    args = parser.parse_args()

    manager = WorkItemManager()

    # Require type and title arguments (no interactive mode)
    if not args.type or not args.title:
        parser.error("Both --type and --title are required")

    work_id = manager.create_work_item_from_args(
        work_type=args.type,
        title=args.title,
        priority=args.priority,
        dependencies=args.dependencies,
    )

    if work_id:
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit(main())
