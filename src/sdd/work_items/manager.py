#!/usr/bin/env python3
"""
Work Item Manager - Core work item operations.

Handles creation, listing, showing, updating work items.
"""

import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from sdd.core.error_handlers import log_errors
from sdd.core.exceptions import (
    ErrorCode,
    FileOperationError,
    ValidationError,
    WorkItemAlreadyExistsError,
    WorkItemNotFoundError,
)
from sdd.core.file_ops import load_json, save_json
from sdd.core.logging_config import get_logger
from sdd.core.types import Priority, WorkItemStatus, WorkItemType
from sdd.work_items import spec_parser

logger = get_logger(__name__)


class WorkItemManager:
    """Manage work items."""

    WORK_ITEM_TYPES = WorkItemType.values()
    PRIORITIES = Priority.values()

    def __init__(self, project_root: Path | None = None):
        """Initialize WorkItemManager with project root path."""
        self.project_root = project_root or Path.cwd()
        self.session_dir = self.project_root / ".session"
        self.work_items_file = self.session_dir / "tracking" / "work_items.json"
        self.specs_dir = self.session_dir / "specs"
        self.templates_dir = Path(__file__).parent.parent / "templates"

    @log_errors()
    def create_work_item(self) -> str:
        """Interactive work item creation.

        Returns:
            str: The created work item ID

        Raises:
            ValidationError: If running in non-interactive environment or invalid input
            WorkItemAlreadyExistsError: If work item with generated ID already exists
            FileOperationError: If spec file creation or tracking update fails
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
        if self._work_item_exists(work_id):
            logger.error("Work item %s already exists", work_id)
            raise WorkItemAlreadyExistsError(work_id)

        # 7. Create specification file
        spec_file = self._create_spec_file(work_id, work_type, title)
        if not spec_file:
            logger.warning("Could not create specification file for %s", work_id)
            logger.warning("Warning: Could not create specification file")

        # 8. Add to work_items.json
        self._add_to_tracking(work_id, work_type, title, priority, dependencies, spec_file)
        logger.info("Work item created: %s (type=%s, priority=%s)", work_id, work_type, priority)

        # 9. Confirm (user-facing output kept as print)
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

        return work_id

    @log_errors()
    def create_work_item_from_args(
        self, work_type: str, title: str, priority: str = "high", dependencies: str = ""
    ) -> str:
        """Create work item from command-line arguments (non-interactive).

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
            FileOperationError: If spec file creation or tracking update fails
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
            work_items_data = load_json(self.work_items_file)
            for dep_id in dep_list:
                if dep_id not in work_items_data.get("work_items", {}):
                    logger.warning("Dependency '%s' does not exist", dep_id)
                    logger.warning("Warning: Dependency '%s' does not exist", dep_id)

        # Generate ID
        work_id = self._generate_id(work_type, title)
        logger.debug("Generated work item ID: %s", work_id)

        # Check for duplicates
        if self._work_item_exists(work_id):
            logger.error("Work item %s already exists", work_id)
            raise WorkItemAlreadyExistsError(work_id)

        # Create specification file
        spec_file = self._create_spec_file(work_id, work_type, title)
        if not spec_file:
            logger.warning("Could not create specification file for %s", work_id)
            logger.warning("Warning: Could not create specification file")

        # Add to work_items.json
        self._add_to_tracking(work_id, work_type, title, priority, dep_list, spec_file)
        logger.info("Work item created: %s (type=%s, priority=%s)", work_id, work_type, priority)

        # Confirm
        print(f"\n{'=' * 50}")
        print("Work item created successfully!")
        print("=" * 50)
        print(f"\nID: {work_id}")
        print(f"Type: {work_type}")
        print(f"Priority: {priority}")
        print(f"Status: {WorkItemStatus.NOT_STARTED.value}")
        if dep_list:
            print(f"Dependencies: {', '.join(dep_list)}")

        if spec_file:
            print(f"\nSpecification saved to: {spec_file}")

        print("\nNext steps:")
        print(f"1. Edit specification: {spec_file}")
        print("2. Start working: /start")
        print()

        return work_id

    def _prompt_type(self) -> Optional[str]:
        """Prompt user to select work item type."""
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
        """Prompt for work item title.

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
        """Prompt for priority."""
        priority = input("\nPriority (critical/high/medium/low) [high]: ").strip().lower()
        if not priority:
            priority = "high"
        if priority not in self.PRIORITIES:
            print("⚠️  Invalid priority, using 'high'")
            priority = "high"
        return priority

    def _prompt_dependencies(self, work_type: str) -> list[str]:
        """Prompt for dependencies."""
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
            if self._work_item_exists(dep):
                valid_deps.append(dep)
            else:
                print(f"⚠️  Warning: Dependency '{dep}' not found, skipping")

        return valid_deps

    def _generate_id(self, work_type: str, title: str) -> str:
        """Generate work item ID from type and title."""
        # Clean title: lowercase, alphanumeric + underscore only
        clean_title = re.sub(r"[^a-z0-9]+", "_", title.lower())
        clean_title = clean_title.strip("_")

        # Truncate if too long
        if len(clean_title) > 30:
            clean_title = clean_title[:30]

        return f"{work_type}_{clean_title}"

    def _work_item_exists(self, work_id: str) -> bool:
        """Check if work item ID already exists."""
        if not self.work_items_file.exists():
            return False

        data = load_json(self.work_items_file)
        return work_id in data.get("work_items", {})

    def _create_spec_file(self, work_id: str, work_type: str, title: str) -> str:
        """Create specification file from template.

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

    def _add_to_tracking(
        self,
        work_id: str,
        work_type: str,
        title: str,
        priority: str,
        dependencies: list[str],
        spec_file: str = "",
    ) -> None:
        """Add work item to work_items.json."""
        # Load existing data
        if self.work_items_file.exists():
            data = load_json(self.work_items_file)
        else:
            data = {"work_items": {}}

        # Create work item entry
        work_item = {
            "id": work_id,
            "type": work_type,
            "title": title,
            "status": WorkItemStatus.NOT_STARTED.value,
            "priority": priority,
            "dependencies": dependencies,
            "milestone": "",
            "spec_file": spec_file,
            "created_at": datetime.now().isoformat(),
            "sessions": [],
        }

        # Add to data
        data["work_items"][work_id] = work_item

        # Update metadata counters
        if "metadata" not in data:
            data["metadata"] = {}

        work_items = data.get("work_items", {})
        data["metadata"]["total_items"] = len(work_items)
        data["metadata"]["completed"] = sum(
            1 for item in work_items.values() if item["status"] == WorkItemStatus.COMPLETED.value
        )
        data["metadata"]["in_progress"] = sum(
            1 for item in work_items.values() if item["status"] == WorkItemStatus.IN_PROGRESS.value
        )
        data["metadata"]["blocked"] = sum(
            1 for item in work_items.values() if item["status"] == WorkItemStatus.BLOCKED.value
        )
        data["metadata"]["last_updated"] = datetime.now().isoformat()

        # Save atomically
        save_json(self.work_items_file, data)

    @log_errors()
    def validate_integration_test(self, work_item: dict) -> None:
        """
        Validate integration test work item by parsing spec file.

        Updated in Phase 5.7.3 to use spec_parser instead of JSON fields.

        Args:
            work_item: Work item dictionary to validate

        Raises:
            FileOperationError: If spec file not found
            ValidationError: If spec validation fails (with validation errors in context)
        """
        errors = []
        work_id: str = str(work_item.get("id", ""))

        # Parse spec file - pass full work_item dict to support custom spec filenames
        try:
            parsed_spec = spec_parser.parse_spec_file(work_item)
        except FileNotFoundError:
            spec_file = work_item.get("spec_file", f".session/specs/{work_id}.md")
            raise FileOperationError(
                operation="read",
                file_path=spec_file,
                details="Spec file not found",
            )
        except ValueError as e:
            raise ValidationError(
                message=f"Invalid spec file: {str(e)}",
                code=ErrorCode.SPEC_VALIDATION_FAILED,
                context={"work_item_id": work_id},
                remediation=f"Fix spec file validation errors for {work_id}",
                cause=e,
            )

        # Validate required sections exist and are not empty
        required_sections = {
            "scope": "Scope",
            "test_scenarios": "Test Scenarios",
            "performance_benchmarks": "Performance Benchmarks",
            "environment_requirements": "Environment Requirements",
            "acceptance_criteria": "Acceptance Criteria",
        }

        for field_name, section_name in required_sections.items():
            value = parsed_spec.get(field_name)
            if value is None or (isinstance(value, str) and not value.strip()):
                errors.append(f"Missing required section: {section_name}")
            elif isinstance(value, list) and len(value) == 0:
                errors.append(f"Section '{section_name}' is empty")

        # Validate test scenarios - must have at least 1 scenario
        test_scenarios = parsed_spec.get("test_scenarios", [])
        if len(test_scenarios) == 0:
            errors.append("At least one test scenario required")
        else:
            # Check that each scenario has content
            for i, scenario in enumerate(test_scenarios):
                if not scenario.get("content") or not scenario.get("content").strip():
                    scenario_name = scenario.get("name", f"Scenario {i + 1}")
                    errors.append(f"{scenario_name}: Missing scenario content")

        # Validate acceptance criteria - should have at least 3 items (per spec validation rules)
        acceptance_criteria = parsed_spec.get("acceptance_criteria", [])
        if len(acceptance_criteria) < 3:
            errors.append(
                f"Acceptance criteria should have at least 3 items (found {len(acceptance_criteria)})"
            )

        # Check for work item dependencies
        dependencies = work_item.get("dependencies", [])
        if not dependencies:
            errors.append("Integration tests must have dependencies (component implementations)")

        # If errors found, raise ValidationError with all errors in context
        if errors:
            from sdd.core.exceptions import SpecValidationError

            raise SpecValidationError(
                work_item_id=work_id,
                errors=errors,
                remediation=f"Fix validation errors in {work_id} spec file",
            )

    @log_errors()
    def validate_deployment(self, work_item: dict) -> None:
        """
        Validate deployment work item by parsing spec file.

        Updated in Phase 5.7.3 to use spec_parser instead of JSON fields.

        Args:
            work_item: Work item dictionary to validate

        Raises:
            FileOperationError: If spec file not found
            ValidationError: If spec validation fails (with validation errors in context)
        """
        errors = []
        work_id: str = str(work_item.get("id", ""))

        # Parse spec file - pass full work_item dict to support custom spec filenames
        try:
            parsed_spec = spec_parser.parse_spec_file(work_item)
        except FileNotFoundError:
            spec_file = work_item.get("spec_file", f".session/specs/{work_id}.md")
            raise FileOperationError(
                operation="read",
                file_path=spec_file,
                details="Spec file not found",
            )
        except ValueError as e:
            raise ValidationError(
                message=f"Invalid spec file: {str(e)}",
                code=ErrorCode.SPEC_VALIDATION_FAILED,
                context={"work_item_id": work_id},
                remediation=f"Fix spec file validation errors for {work_id}",
                cause=e,
            )

        # Validate required sections exist and are not empty
        required_sections = {
            "deployment_scope": "Deployment Scope",
            "deployment_procedure": "Deployment Procedure",
            "environment_configuration": "Environment Configuration",
            "rollback_procedure": "Rollback Procedure",
            "smoke_tests": "Smoke Tests",
            "acceptance_criteria": "Acceptance Criteria",
        }

        for field_name, section_name in required_sections.items():
            value = parsed_spec.get(field_name)
            if value is None:
                errors.append(f"Missing required section: {section_name}")
            elif isinstance(value, str) and not value.strip():
                errors.append(f"Section '{section_name}' is empty")
            elif isinstance(value, list) and len(value) == 0:
                errors.append(f"Section '{section_name}' is empty")
            elif isinstance(value, dict) and not any(value.values()):
                errors.append(f"Section '{section_name}' is empty")

        # Validate deployment procedure subsections
        deployment_proc = parsed_spec.get("deployment_procedure")
        if deployment_proc:
            if (
                not deployment_proc.get("pre_deployment")
                or not deployment_proc.get("pre_deployment").strip()
            ):
                errors.append("Missing pre-deployment checklist/steps")
            if (
                not deployment_proc.get("deployment_steps")
                or not deployment_proc.get("deployment_steps").strip()
            ):
                errors.append("Missing deployment steps")
            if (
                not deployment_proc.get("post_deployment")
                or not deployment_proc.get("post_deployment").strip()
            ):
                errors.append("Missing post-deployment steps")

        # Validate rollback procedure subsections
        rollback_proc = parsed_spec.get("rollback_procedure")
        if rollback_proc:
            if not rollback_proc.get("triggers") or not rollback_proc.get("triggers").strip():
                errors.append("Missing rollback triggers")
            if not rollback_proc.get("steps") or not rollback_proc.get("steps").strip():
                errors.append("Missing rollback steps")

        # Validate smoke tests - must have at least 1 test
        smoke_tests = parsed_spec.get("smoke_tests", [])
        if len(smoke_tests) == 0:
            errors.append("At least one smoke test required")

        # Validate acceptance criteria - should have at least 3 items
        acceptance_criteria = parsed_spec.get("acceptance_criteria", [])
        if len(acceptance_criteria) < 3:
            errors.append(
                f"Acceptance criteria should have at least 3 items (found {len(acceptance_criteria)})"
            )

        # If errors found, raise ValidationError with all errors in context
        if errors:
            from sdd.core.exceptions import SpecValidationError

            raise SpecValidationError(
                work_item_id=work_id,
                errors=errors,
                remediation=f"Fix validation errors in {work_id} spec file",
            )

    def list_work_items(
        self,
        status_filter: Optional[str] = None,
        type_filter: Optional[str] = None,
        milestone_filter: Optional[str] = None,
    ) -> dict:
        """List work items with optional filtering."""
        if not self.work_items_file.exists():
            print("No work items found. Create one with /work-item create")
            return {"items": [], "count": 0}

        data = load_json(self.work_items_file)
        items = data.get("work_items", {})

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

    def _is_blocked(self, item: dict, all_items: dict) -> bool:
        """Check if work item is blocked by dependencies."""
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
        """Sort items by priority, dependency status, and date."""
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
        """Display items with color coding and indicators."""
        if not items:
            print("No work items found matching filters.")
            return

        # Count by status
        status_counts = {
            WorkItemStatus.NOT_STARTED.value: 0,
            WorkItemStatus.IN_PROGRESS.value: 0,
            WorkItemStatus.BLOCKED.value: 0,
            WorkItemStatus.COMPLETED.value: 0,
        }

        for item in items:
            if item.get("_blocked"):
                status_counts[WorkItemStatus.BLOCKED.value] += 1
            else:
                status_counts[item["status"]] += 1

        # Header
        total = len(items)
        print(
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

            print(f"{priority_emoji[priority]} {priority.upper()}")

            for item in group_items:
                status_icon = self._get_status_icon(item)
                work_id = item["id"]

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

                print(f"  {status_icon} {work_id} {status_str}")

            print()

        # Legend
        print("Legend:")
        print("  [  ] Not started")
        print("  [>>] In progress")
        print("  [✓] Completed")
        print("  🚫 Blocked by dependencies")
        print("  ✓ Ready to start")
        print()

    def _get_status_icon(self, item: dict) -> str:
        """Get status icon for work item."""
        if item["status"] == WorkItemStatus.COMPLETED.value:
            return "[✓]"
        elif item["status"] == WorkItemStatus.IN_PROGRESS.value:
            return "[>>]"
        else:
            return "[  ]"

    @log_errors()
    def show_work_item(self, work_id: str) -> dict[str, Any]:
        """Display detailed information about a work item.

        Args:
            work_id: ID of the work item to display

        Returns:
            dict: The work item data

        Raises:
            FileOperationError: If work_items.json doesn't exist
            WorkItemNotFoundError: If work item doesn't exist
        """
        if not self.work_items_file.exists():
            raise FileOperationError(
                operation="read",
                file_path=str(self.work_items_file),
                details="No work items found",
            )

        data = load_json(self.work_items_file)
        items = data.get("work_items", {})

        if work_id not in items:
            # Log available work items for context
            available = list(items.keys())[:5]
            logger.error(f"Work item '{work_id}' not found. Available: {', '.join(available)}")
            raise WorkItemNotFoundError(work_id)

        item = items[work_id]

        # Display header
        print("=" * 80)
        print(f"Work Item: {work_id}")
        print("=" * 80)
        print()

        # Basic info
        print(f"Type: {item['type']}")
        print(f"Status: {item['status']}")
        print(f"Priority: {item['priority']}")
        print(f"Created: {item.get('created_at', 'Unknown')[:10]}")
        print()

        # Dependencies
        if item.get("dependencies"):
            print("Dependencies:")
            for dep_id in item["dependencies"]:
                if dep_id in items:
                    dep_status = items[dep_id]["status"]
                    icon = "✓" if dep_status == WorkItemStatus.COMPLETED.value else "✗"
                    print(f"  {icon} {dep_id} ({dep_status})")
                else:
                    print(f"  ? {dep_id} (not found)")
            print()

        # Sessions
        sessions = item.get("sessions", [])
        if sessions:
            print(f"Sessions: {len(sessions)}")
            for i, session in enumerate(sessions[-5:], 1):  # Last 5 sessions
                session_num = session.get("session_number", i)
                date = session.get("date", "Unknown")
                duration = session.get("duration", "Unknown")
                notes = session.get("notes", "")
                print(f"  {session_num}. {date} ({duration}) - {notes[:50]}")
            print()

        # Git info
        git_info = item.get("git", {})
        if git_info:
            print(f"Git Branch: {git_info.get('branch', 'N/A')}")
            commits = git_info.get("commits", [])
            print(f"Commits: {len(commits)}")
            print()

        # Specification - use spec_file from work item config
        spec_file_path = item.get("spec_file", f".session/specs/{work_id}.md")
        spec_path = Path(spec_file_path)
        if spec_path.exists():
            print("Specification:")
            print("-" * 80)
            spec_content = spec_path.read_text()
            # Show first 50 lines (increased to include Acceptance Criteria section)
            lines = spec_content.split("\n")[:50]
            print("\n".join(lines))
            if len(spec_content.split("\n")) > 50:
                print(f"\n[... see full specification in {spec_file_path}]")
            print()

        # Next steps
        print("Next Steps:")
        if item["status"] == WorkItemStatus.NOT_STARTED.value:
            # Check dependencies
            blocked = any(
                items.get(dep_id, {}).get("status") != WorkItemStatus.COMPLETED.value
                for dep_id in item.get("dependencies", [])
            )
            if blocked:
                print("- Waiting on dependencies to complete")
            else:
                print("- Start working: /start")
        elif item["status"] == WorkItemStatus.IN_PROGRESS.value:
            print("- Continue working: /start")
        elif item["status"] == WorkItemStatus.COMPLETED.value:
            print("- Work item is complete")

        print(f"- Update fields: /work-update {work_id}")
        if item.get("milestone"):
            print(f"- View related items: /work-list --milestone {item['milestone']}")
        print()

        return item  # type: ignore[no-any-return]

    @log_errors()
    def update_work_item(self, work_id: str, **updates: Any) -> None:
        """Update work item fields.

        Args:
            work_id: ID of the work item to update
            **updates: Field updates (status, priority, milestone, add_dependency, remove_dependency)

        Raises:
            FileOperationError: If work_items.json doesn't exist
            WorkItemNotFoundError: If work item doesn't exist
            ValidationError: If invalid status or priority provided
        """
        if not self.work_items_file.exists():
            raise FileOperationError(
                operation="read", file_path=str(self.work_items_file), details="No work items found"
            )

        data = load_json(self.work_items_file)
        items = data.get("work_items", {})

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
                    if value in items:
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

        # Save
        data["work_items"][work_id] = item

        # Update metadata counters (Bug #17 fix)
        if "metadata" not in data:
            data["metadata"] = {}

        work_items = data.get("work_items", {})
        data["metadata"]["total_items"] = len(work_items)
        data["metadata"]["completed"] = sum(
            1 for item in work_items.values() if item["status"] == WorkItemStatus.COMPLETED.value
        )
        data["metadata"]["in_progress"] = sum(
            1 for item in work_items.values() if item["status"] == WorkItemStatus.IN_PROGRESS.value
        )
        data["metadata"]["blocked"] = sum(
            1 for item in work_items.values() if item["status"] == WorkItemStatus.BLOCKED.value
        )
        data["metadata"]["last_updated"] = datetime.now().isoformat()

        save_json(self.work_items_file, data)

        # Success - keep user-facing output as print()
        print(f"\nUpdated {work_id}:")
        for change in changes:
            print(change)
        print()

    @log_errors()
    def update_work_item_interactive(self, work_id: str) -> None:
        """Interactive work item update.

        Args:
            work_id: ID of work item to update

        Raises:
            FileOperationError: If work_items.json doesn't exist
            ValidationError: If running in non-interactive environment
            WorkItemNotFoundError: If work item doesn't exist
        """
        if not self.work_items_file.exists():
            raise FileOperationError(
                operation="read", file_path=str(self.work_items_file), details="No work items found"
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

        data = load_json(self.work_items_file)
        items = data.get("work_items", {})

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
                self.update_work_item(work_id, status=status)
            elif choice == "2":
                priority = input("New priority (critical/high/medium/low): ").strip()
                self.update_work_item(work_id, priority=priority)
            elif choice == "3":
                milestone = input("Milestone name: ").strip()
                self.update_work_item(work_id, milestone=milestone)
            elif choice == "4":
                dep = input("Dependency ID to add: ").strip()
                self.update_work_item(work_id, add_dependency=dep)
            elif choice == "5":
                dep = input("Dependency ID to remove: ").strip()
                self.update_work_item(work_id, remove_dependency=dep)
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

    def get_next_work_item(self) -> Optional[dict[str, Any]]:
        """Find next work item to start."""
        if not self.work_items_file.exists():
            print("No work items found.")
            return None

        data = load_json(self.work_items_file)
        items = data.get("work_items", {})

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

        return next_item  # type: ignore[no-any-return]

    @log_errors()
    def create_milestone(
        self, name: str, title: str, description: str, target_date: Optional[str] = None
    ) -> None:
        """Create a new milestone.

        Args:
            name: Milestone name (unique identifier)
            title: Milestone title
            description: Milestone description
            target_date: Optional target completion date

        Raises:
            WorkItemAlreadyExistsError: If milestone with this name already exists (reusing for consistency)
            FileOperationError: If saving milestone fails
        """
        if not self.work_items_file.exists():
            data: dict[str, Any] = {"work_items": {}, "milestones": {}}
        else:
            data = load_json(self.work_items_file)
            if "milestones" not in data:
                data["milestones"] = {}

        if name in data["milestones"]:
            logger.error("Milestone '%s' already exists", name)
            # Reuse WorkItemAlreadyExistsError for consistency
            raise ValidationError(
                message=f"Milestone '{name}' already exists",
                code=ErrorCode.WORK_ITEM_ALREADY_EXISTS,
                context={"milestone_name": name},
                remediation="Choose a different milestone name",
            )

        milestone = {
            "name": name,
            "title": title,
            "description": description,
            "target_date": target_date or "",
            "status": "not_started",
            "created_at": datetime.now().isoformat(),
        }

        data["milestones"][name] = milestone
        save_json(self.work_items_file, data)

        logger.info("Created milestone: %s", name)
        print(f"✓ Created milestone: {name}")

    def get_milestone_progress(self, milestone_name: str) -> dict:
        """Calculate milestone progress."""
        if not self.work_items_file.exists():
            return {"error": "No work items found"}

        data = load_json(self.work_items_file)
        items = data.get("work_items", {})

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

    def list_milestones(self) -> None:
        """List all milestones with progress."""
        if not self.work_items_file.exists():
            print("No milestones found.")
            return

        data = load_json(self.work_items_file)
        milestones = data.get("milestones", {})

        if not milestones:
            print("No milestones found.")
            return

        print("\nMilestones:\n")

        for name, milestone in milestones.items():
            progress = self.get_milestone_progress(name)
            percent = progress["percent"]

            # Progress bar
            bar_length = 20
            filled = int(bar_length * percent / 100)
            bar = "█" * filled + "░" * (bar_length - filled)

            print(f"{milestone['title']}")
            print(f"  [{bar}] {percent}%")
            print(
                f"  {progress['completed']}/{progress['total']} complete, "
                f"{progress['in_progress']} in progress"
            )

            if milestone.get("target_date"):
                print(f"  Target: {milestone['target_date']}")
            print()


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

    # If arguments provided, use non-interactive mode
    if args.type and args.title:
        work_id = manager.create_work_item_from_args(
            work_type=args.type,
            title=args.title,
            priority=args.priority,
            dependencies=args.dependencies,
        )
    else:
        # Otherwise, use interactive mode
        work_id = manager.create_work_item()

    if work_id:
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit(main())
