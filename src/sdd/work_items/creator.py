#!/usr/bin/env python3
"""
Work Item Creator - Interactive and non-interactive work item creation.

Handles user prompts, ID generation, and spec file creation.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from sdd.core.error_handlers import log_errors
from sdd.core.exceptions import (
    ErrorCode,
    ValidationError,
    WorkItemAlreadyExistsError,
)
from sdd.core.logging_config import get_logger
from sdd.core.types import WorkItemStatus, WorkItemType

if TYPE_CHECKING:
    from .repository import WorkItemRepository

logger = get_logger(__name__)


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
    def create_interactive(self) -> str:
        """Interactive work item creation

        Returns:
            str: The created work item ID

        Raises:
            ValidationError: If running in non-interactive environment or invalid input
            WorkItemAlreadyExistsError: If work item with generated ID already exists
        """
        logger.info("Starting interactive work item creation")

        # Check if running in non-interactive environment
        if not sys.stdin.isatty():
            logger.error("Cannot run interactive mode in non-interactive environment")
            raise ValidationError(
                message="Cannot run interactive work item creation in non-interactive mode",
                code=ErrorCode.INVALID_COMMAND,
                remediation=(
                    "Please use command-line arguments instead:\n"
                    "  sdd work-new --type <type> --title <title> [--priority <priority>] [--dependencies <deps>]\n"
                    "\nExample:\n"
                    '  sdd work-new --type feature --title "Implement calculator" --priority high'
                ),
            )

        print("Creating new work item...\n")

        # 1. Select type
        try:
            work_type = self._prompt_type()
            if not work_type:
                logger.debug("Work item creation cancelled - no type selected")
                raise ValidationError(
                    message="Work item creation cancelled - no type selected",
                    code=ErrorCode.INVALID_WORK_ITEM_TYPE,
                    remediation="Select a valid work item type (1-6)",
                )
        except EOFError:
            logger.warning("EOFError during type selection")
            raise ValidationError(
                message="Interactive input unavailable",
                code=ErrorCode.INVALID_COMMAND,
                remediation="Use command-line arguments instead",
            )

        # 2. Get title
        try:
            title = self._prompt_title()
            if not title:
                logger.debug("Work item creation cancelled - no title provided")
                raise ValidationError(
                    message="Work item creation cancelled - no title provided",
                    code=ErrorCode.MISSING_REQUIRED_FIELD,
                    context={"field": "title"},
                    remediation="Title is required for work items",
                )
        except EOFError:
            logger.warning("EOFError during title input")
            raise ValidationError(
                message="Interactive input unavailable",
                code=ErrorCode.INVALID_COMMAND,
                remediation="Use command-line arguments instead",
            )

        # 3. Get priority
        try:
            priority = self._prompt_priority()
        except EOFError:
            logger.warning("EOFError during priority input, using default 'high'")
            logger.info("Input unavailable, using default priority 'high'")
            priority = "high"

        # 4. Get dependencies
        try:
            dependencies = self._prompt_dependencies(work_type)
        except EOFError:
            logger.warning("EOFError during dependencies input, using no dependencies")
            logger.info("Input unavailable, no dependencies will be added")
            dependencies = []

        # 5. Generate ID
        work_id = self._generate_id(work_type, title)
        logger.debug("Generated work item ID: %s", work_id)

        # 6. Check for duplicates
        if self.repository.work_item_exists(work_id):
            logger.error("Work item %s already exists", work_id)
            raise WorkItemAlreadyExistsError(work_id)

        # 7. Create specification file
        spec_file = self._create_spec_file(work_id, work_type, title)
        if not spec_file:
            logger.warning("Could not create specification file for %s", work_id)
            logger.warning("Warning: Could not create specification file")

        # 8. Add to work_items.json
        self.repository.add_work_item(work_id, work_type, title, priority, dependencies, spec_file)
        logger.info("Work item created: %s (type=%s, priority=%s)", work_id, work_type, priority)

        # 9. Confirm (user-facing output)
        self._print_creation_confirmation(work_id, work_type, priority, dependencies, spec_file)

        return work_id

    @log_errors()
    def create_from_args(
        self, work_type: str, title: str, priority: str = "high", dependencies: str = ""
    ) -> str:
        """Create work item from command-line arguments (non-interactive)

        Args:
            work_type: Type of work item (feature, bug, refactor, etc.)
            title: Title of the work item
            priority: Priority level (critical, high, medium, low)
            dependencies: Comma-separated dependency IDs

        Returns:
            str: The created work item ID

        Raises:
            ValidationError: If work type is invalid
            WorkItemAlreadyExistsError: If work item with generated ID already exists
        """
        logger.info("Creating work item from args: type=%s, title=%s", work_type, title)

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

        # Add to work_items.json
        self.repository.add_work_item(work_id, work_type, title, priority, dep_list, spec_file)
        logger.info("Work item created: %s (type=%s, priority=%s)", work_id, work_type, priority)

        # Confirm
        self._print_creation_confirmation(work_id, work_type, priority, dep_list, spec_file)

        return work_id

    def _prompt_type(self) -> str | None:
        """Prompt user to select work item type

        Returns:
            str: Selected work item type, or None if invalid
        """
        print("Select work item type:")
        print("1. feature - Standard feature development")
        print("2. bug - Bug fix")
        print("3. refactor - Code refactoring")
        print("4. security - Security-focused work")
        print("5. integration_test - Integration testing")
        print("6. deployment - Deployment to environment")
        print()

        choice = input("Your choice (1-6): ").strip()

        type_map = {
            "1": "feature",
            "2": "bug",
            "3": "refactor",
            "4": "security",
            "5": "integration_test",
            "6": "deployment",
        }

        return type_map.get(choice)

    def _prompt_title(self) -> str:
        """Prompt for work item title

        Returns:
            str: The work item title

        Raises:
            ValidationError: If title is empty
        """
        title = input("\nTitle: ").strip()
        if not title:
            raise ValidationError(
                message="Title is required",
                code=ErrorCode.MISSING_REQUIRED_FIELD,
                context={"field": "title"},
                remediation="Provide a non-empty title for the work item",
            )
        return title

    def _prompt_priority(self) -> str:
        """Prompt for priority

        Returns:
            str: Priority level
        """
        priority = input("\nPriority (critical/high/medium/low) [high]: ").strip().lower()
        if not priority:
            priority = "high"
        if priority not in self.PRIORITIES:
            print("⚠️  Invalid priority, using 'high'")
            priority = "high"
        return priority

    def _prompt_dependencies(self, work_type: str) -> list[str]:
        """Prompt for dependencies

        Args:
            work_type: Type of work item (affects whether dependencies are required)

        Returns:
            list: List of dependency IDs
        """
        required = work_type in ["integration_test", "deployment"]

        prompt = "\nDependencies (comma-separated IDs"
        if required:
            prompt += ", REQUIRED): "
        else:
            prompt += ", or press Enter for none): "

        deps_input = input(prompt).strip()

        if not deps_input:
            if required:
                print("⚠️  Warning: This work item type requires dependencies")
                return self._prompt_dependencies(work_type)  # Retry
            return []

        # Parse and validate
        deps = [d.strip() for d in deps_input.split(",")]
        deps = [d for d in deps if d]  # Remove empty

        # Validate dependencies exist
        valid_deps = []
        for dep in deps:
            if self.repository.work_item_exists(dep):
                valid_deps.append(dep)
            else:
                print(f"⚠️  Warning: Dependency '{dep}' not found, skipping")

        return valid_deps

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

    def _print_creation_confirmation(
        self,
        work_id: str,
        work_type: str,
        priority: str,
        dependencies: list[str],
        spec_file: str,
    ) -> None:
        """Print creation confirmation message

        Args:
            work_id: Created work item ID
            work_type: Work item type
            priority: Priority level
            dependencies: List of dependency IDs
            spec_file: Path to spec file
        """
        print(f"\n{'=' * 50}")
        print("Work item created successfully!")
        print("=" * 50)
        print(f"\nID: {work_id}")
        print(f"Type: {work_type}")
        print(f"Priority: {priority}")
        print(f"Status: {WorkItemStatus.NOT_STARTED.value}")
        if dependencies:
            print(f"Dependencies: {', '.join(dependencies)}")

        if spec_file:
            print(f"\nSpecification saved to: {spec_file}")

        print("\nNext steps:")
        print(f"1. Edit specification: {spec_file}")
        print("2. Start working: /start")
        print()
