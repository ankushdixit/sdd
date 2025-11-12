#!/usr/bin/env python3
"""
Work Item Creator - Interactive and non-interactive work item creation.

Handles user prompts, ID generation, and spec file creation.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from solokit.core.error_handlers import log_errors
from solokit.core.exceptions import (
    ErrorCode,
    ValidationError,
    WorkItemAlreadyExistsError,
)
from solokit.core.logging_config import get_logger
from solokit.core.types import WorkItemStatus, WorkItemType

if TYPE_CHECKING:
    from .repository import WorkItemRepository
from solokit.core.output import get_output

logger = get_logger(__name__)
output = get_output()


class WorkItemCreator:
    """Handles work item creation with interactive and non-interactive modes"""

    WORK_ITEM_TYPES = WorkItemType.values()
    PRIORITIES = ["critical", "high", "medium", "low"]

    def __init__(self, repository: WorkItemRepository):
        """Initialize creator with repository

        Args:
            repository: WorkItemRepository instance for data access
        """
        self.repository = repository
        self.project_root = repository.session_dir.parent
        self.specs_dir = repository.session_dir / "specs"
        self.templates_dir = Path(__file__).parent.parent / "templates"

    @log_errors()
    def create_from_args(
        self,
        work_type: str,
        title: str,
        priority: str = "high",
        dependencies: str = "",
        urgent: bool = False,
    ) -> str:
        """Create work item from command-line arguments (non-interactive)

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
        """
        logger.info(
            "Creating work item from args: type=%s, title=%s, urgent=%s", work_type, title, urgent
        )

        # Validate work type
        if work_type not in self.WORK_ITEM_TYPES:
            logger.error("Invalid work item type: %s", work_type)
            raise ValidationError(
                message=f"Invalid work item type '{work_type}'",
                code=ErrorCode.INVALID_WORK_ITEM_TYPE,
                context={"work_type": work_type, "valid_types": self.WORK_ITEM_TYPES},
                remediation=f"Valid types: {', '.join(self.WORK_ITEM_TYPES)}",
            )

        # Validate priority
        if priority not in self.PRIORITIES:
            logger.warning("Invalid priority '%s', using 'high'", priority)
            logger.warning("Invalid priority '%s', using 'high'", priority)
            priority = "high"

        # Parse dependencies
        dep_list = []
        if dependencies:
            dep_list = [d.strip() for d in dependencies.split(",") if d.strip()]
            logger.debug("Parsed dependencies: %s", dep_list)
            # Validate dependencies exist
            for dep_id in dep_list:
                if not self.repository.work_item_exists(dep_id):
                    logger.warning("Dependency '%s' does not exist", dep_id)
                    logger.warning("Warning: Dependency '%s' does not exist", dep_id)

        # Generate ID
        work_id = self._generate_id(work_type, title)
        logger.debug("Generated work item ID: %s", work_id)

        # Check for duplicates
        if self.repository.work_item_exists(work_id):
            logger.error("Work item %s already exists", work_id)
            raise WorkItemAlreadyExistsError(work_id)

        # Create specification file
        spec_file = self._create_spec_file(work_id, work_type, title)
        if not spec_file:
            logger.warning("Could not create specification file for %s", work_id)
            logger.warning("Warning: Could not create specification file")

        # Handle urgent flag enforcement (single-item constraint)
        should_set_urgent = urgent
        if urgent:
            existing_urgent = self.repository.get_urgent_work_item()
            if existing_urgent:
                should_set_urgent = self._confirm_urgent_override(existing_urgent)

        # Add to work_items.json
        self.repository.add_work_item(
            work_id, work_type, title, priority, dep_list, spec_file, urgent=should_set_urgent
        )
        logger.info(
            "Work item created: %s (type=%s, priority=%s, urgent=%s)",
            work_id,
            work_type,
            priority,
            should_set_urgent,
        )

        # Confirm
        self._print_creation_confirmation(
            work_id, work_type, priority, dep_list, spec_file, should_set_urgent
        )

        return work_id

    def _generate_id(self, work_type: str, title: str) -> str:
        """Generate work item ID from type and title

        Args:
            work_type: Type of work item
            title: Work item title

        Returns:
            str: Generated work item ID
        """
        # Clean title: lowercase, alphanumeric + underscore only
        clean_title = re.sub(r"[^a-z0-9]+", "_", title.lower())
        clean_title = clean_title.strip("_")

        # Truncate if too long
        if len(clean_title) > 30:
            clean_title = clean_title[:30]

        return f"{work_type}_{clean_title}"

    def _create_spec_file(self, work_id: str, work_type: str, title: str) -> str:
        """Create specification file from template

        Args:
            work_id: Work item ID
            work_type: Type of work item
            title: Work item title

        Returns:
            str: Relative path to the created spec file, or empty string if failed
        """
        # Ensure specs directory exists
        self.specs_dir.mkdir(parents=True, exist_ok=True)

        # Load template
        template_file = self.templates_dir / f"{work_type}_spec.md"
        if not template_file.exists():
            return ""

        template_content = template_file.read_text()

        # Replace title placeholder
        if work_type == "feature":
            spec_content = template_content.replace("[Feature Name]", title)
        elif work_type == "bug":
            spec_content = template_content.replace("[Bug Title]", title)
        elif work_type == "refactor":
            spec_content = template_content.replace("[Refactor Title]", title)
        elif work_type == "security":
            spec_content = template_content.replace("[Name]", title)
        elif work_type == "integration_test":
            spec_content = template_content.replace("[Name]", title)
        elif work_type == "deployment":
            spec_content = template_content.replace("[Environment]", title)
        else:
            spec_content = template_content

        # Save spec file
        spec_path = self.specs_dir / f"{work_id}.md"
        spec_path.write_text(spec_content)

        # Return relative path from project root
        return f".session/specs/{work_id}.md"

    def _confirm_urgent_override(self, existing_urgent: dict) -> bool:
        """Prompt user to confirm clearing existing urgent item

        Args:
            existing_urgent: The currently urgent work item data

        Returns:
            bool: True if user confirmed override, False otherwise
        """
        existing_id = existing_urgent.get("id", "unknown")
        existing_title = existing_urgent.get("title", "Unknown Title")

        output.warning(f"\nWork item '{existing_id}' is currently marked urgent: {existing_title}")
        response = input("Clear and set new urgent item? (y/N): ").strip().lower()

        if response == "y":
            self.repository.clear_urgent_flag(existing_id)
            output.success(f"Cleared urgent flag from '{existing_id}'")
            return True
        else:
            output.info("Keeping existing urgent item. New item will not be marked urgent.")
            return False

    def _print_creation_confirmation(
        self,
        work_id: str,
        work_type: str,
        priority: str,
        dependencies: list[str],
        spec_file: str,
        urgent: bool = False,
    ) -> None:
        """Print creation confirmation message

        Args:
            work_id: Created work item ID
            work_type: Work item type
            priority: Priority level
            dependencies: List of dependency IDs
            spec_file: Path to spec file
            urgent: Whether the item is marked urgent
        """
        output.info(f"\n{'=' * 50}")
        output.info("Work item created successfully!")
        output.info("=" * 50)
        output.info(f"\nID: {work_id}")
        output.info(f"Type: {work_type}")
        output.info(f"Priority: {priority}")
        output.info(f"Status: {WorkItemStatus.NOT_STARTED.value}")
        if urgent:
            output.warning("Urgent: YES (will be prioritized above all other work items)")
        if dependencies:
            output.info(f"Dependencies: {', '.join(dependencies)}")

        if spec_file:
            output.info(f"\nSpecification saved to: {spec_file}")

        output.info("\nNext steps:")
        output.info(f"1. Edit specification: {spec_file}")
        output.info("2. Start working: /start")
        output.info("")
