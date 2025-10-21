#!/usr/bin/env python3
"""
Work Item Manager - Core work item operations.

Handles creation, listing, showing, updating work items.
"""

import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts import spec_parser
from scripts.file_ops import load_json, save_json
from scripts.logging_config import get_logger

logger = get_logger(__name__)


class WorkItemManager:
    """Manage work items."""

    WORK_ITEM_TYPES = [
        "feature",
        "bug",
        "refactor",
        "security",
        "integration_test",
        "deployment",
    ]

    PRIORITIES = ["critical", "high", "medium", "low"]

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.session_dir = self.project_root / ".session"
        self.work_items_file = self.session_dir / "tracking" / "work_items.json"
        self.specs_dir = self.session_dir / "specs"
        self.templates_dir = Path(__file__).parent.parent / "templates"

    def create_work_item(self) -> Optional[str]:
        """Interactive work item creation."""
        logger.info("Starting interactive work item creation")
        print("Creating new work item...\n")

        # 1. Select type
        work_type = self._prompt_type()
        if not work_type:
            logger.debug("Work item creation cancelled - no type selected")
            return None

        # 2. Get title
        title = self._prompt_title()
        if not title:
            logger.debug("Work item creation cancelled - no title provided")
            return None

        # 3. Get priority
        priority = self._prompt_priority()

        # 4. Get dependencies
        dependencies = self._prompt_dependencies(work_type)

        # 5. Generate ID
        work_id = self._generate_id(work_type, title)
        logger.debug("Generated work item ID: %s", work_id)

        # 6. Check for duplicates
        if self._work_item_exists(work_id):
            logger.error("Work item %s already exists", work_id)
            print(f"❌ Error: Work item {work_id} already exists")
            return None

        # 7. Create specification file
        spec_file = self._create_spec_file(work_id, work_type, title)
        if not spec_file:
            logger.warning("Could not create specification file for %s", work_id)
            print("⚠️  Warning: Could not create specification file")

        # 8. Add to work_items.json
        self._add_to_tracking(work_id, work_type, title, priority, dependencies, spec_file)
        logger.info("Work item created: %s (type=%s, priority=%s)", work_id, work_type, priority)

        # 9. Confirm
        print(f"\n{'=' * 50}")
        print("Work item created successfully!")
        print("=" * 50)
        print(f"\nID: {work_id}")
        print(f"Type: {work_type}")
        print(f"Priority: {priority}")
        print("Status: not_started")
        if dependencies:
            print(f"Dependencies: {', '.join(dependencies)}")

        if spec_file:
            print(f"\nSpecification saved to: {spec_file}")

        print("\nNext steps:")
        print(f"1. Edit specification: .session/specs/{work_id}.md")
        print("2. Start working: /start")
        print()

        return work_id

    def create_work_item_from_args(
        self, work_type: str, title: str, priority: str = "high", dependencies: str = ""
    ) -> Optional[str]:
        """Create work item from command-line arguments (non-interactive)."""
        logger.info("Creating work item from args: type=%s, title=%s", work_type, title)

        # Validate work type
        if work_type not in self.WORK_ITEM_TYPES:
            logger.error("Invalid work item type: %s", work_type)
            print(f"❌ Error: Invalid work item type '{work_type}'")
            print(f"Valid types: {', '.join(self.WORK_ITEM_TYPES)}")
            return None

        # Validate priority
        if priority not in self.PRIORITIES:
            logger.warning("Invalid priority '%s', using 'high'", priority)
            print(f"⚠️  Invalid priority '{priority}', using 'high'")
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
                    print(f"⚠️  Warning: Dependency '{dep_id}' does not exist")

        # Generate ID
        work_id = self._generate_id(work_type, title)
        logger.debug("Generated work item ID: %s", work_id)

        # Check for duplicates
        if self._work_item_exists(work_id):
            logger.error("Work item %s already exists", work_id)
            print(f"❌ Error: Work item {work_id} already exists")
            return None

        # Create specification file
        spec_file = self._create_spec_file(work_id, work_type, title)
        if not spec_file:
            logger.warning("Could not create specification file for %s", work_id)
            print("⚠️  Warning: Could not create specification file")

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
        print("Status: not_started")
        if dep_list:
            print(f"Dependencies: {', '.join(dep_list)}")

        if spec_file:
            print(f"\nSpecification saved to: {spec_file}")

        print("\nNext steps:")
        print(f"1. Edit specification: .session/specs/{work_id}.md")
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

    def _prompt_title(self) -> Optional[str]:
        """Prompt for work item title."""
        title = input("\nTitle: ").strip()
        if not title:
            print("❌ Error: Title is required")
            return None
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
    ):
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
            "status": "not_started",
            "priority": priority,
            "dependencies": dependencies,
            "milestone": "",
            "spec_file": spec_file,
            "created_at": datetime.now().isoformat(),
            "sessions": [],
        }

        # Add to data
        data["work_items"][work_id] = work_item

        # Save atomically
        save_json(self.work_items_file, data)

    def validate_integration_test(self, work_item: dict) -> tuple[bool, list[str]]:
        """
        Validate integration test work item by parsing spec file.

        Updated in Phase 5.7.3 to use spec_parser instead of JSON fields.

        Returns:
            (is_valid: bool, errors: List[str])
        """
        errors = []
        work_id = work_item.get("id")

        # Parse spec file
        try:
            parsed_spec = spec_parser.parse_spec_file(work_id)
        except FileNotFoundError:
            errors.append(f"Spec file not found: .session/specs/{work_id}.md")
            return False, errors
        except ValueError as e:
            errors.append(f"Invalid spec file: {str(e)}")
            return False, errors

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

        return len(errors) == 0, errors

    def validate_deployment(self, work_item: dict) -> tuple[bool, list[str]]:
        """
        Validate deployment work item by parsing spec file.

        Updated in Phase 5.7.3 to use spec_parser instead of JSON fields.

        Returns:
            (is_valid, errors)
        """
        errors = []
        work_id = work_item.get("id")

        # Parse spec file
        try:
            parsed_spec = spec_parser.parse_spec_file(work_id)
        except FileNotFoundError:
            errors.append(f"Spec file not found: .session/specs/{work_id}.md")
            return False, errors
        except ValueError as e:
            errors.append(f"Invalid spec file: {str(e)}")
            return False, errors

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

        return len(errors) == 0, errors

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
            item["_ready"] = not item["_blocked"] and item["status"] == "not_started"

        # Sort items
        sorted_items = self._sort_items(filtered_items)

        # Display
        self._display_items(sorted_items)

        return {"items": sorted_items, "count": len(sorted_items)}

    def _is_blocked(self, item: dict, all_items: dict) -> bool:
        """Check if work item is blocked by dependencies."""
        if item["status"] != "not_started":
            return False

        dependencies = item.get("dependencies", [])
        if not dependencies:
            return False

        for dep_id in dependencies:
            if dep_id not in all_items:
                continue
            if all_items[dep_id]["status"] != "completed":
                return True

        return False

    def _sort_items(self, items: dict) -> list[dict]:
        """Sort items by priority, dependency status, and date."""
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}

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
                0 if x["status"] == "in_progress" else 1,
                x.get("created_at", ""),
            )
        )

        return items_list

    def _display_items(self, items: list[dict]):
        """Display items with color coding and indicators."""
        if not items:
            print("No work items found matching filters.")
            return

        # Count by status
        status_counts = {
            "not_started": 0,
            "in_progress": 0,
            "blocked": 0,
            "completed": 0,
        }

        for item in items:
            if item.get("_blocked"):
                status_counts["blocked"] += 1
            else:
                status_counts[item["status"]] += 1

        # Header
        total = len(items)
        print(
            f"\nWork Items ({total} total, "
            f"{status_counts['in_progress']} in progress, "
            f"{status_counts['not_started']} not started, "
            f"{status_counts['completed']} completed)\n"
        )

        # Group by priority
        priority_groups = {"critical": [], "high": [], "medium": [], "low": []}

        for item in items:
            priority = item.get("priority", "medium")
            priority_groups[priority].append(item)

        # Display each priority group
        priority_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}

        for priority in ["critical", "high", "medium", "low"]:
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
                elif item["status"] == "in_progress":
                    sessions = len(item.get("sessions", []))
                    status_str = f"(in progress, session {sessions})"
                elif item["status"] == "completed":
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
        if item["status"] == "completed":
            return "[✓]"
        elif item["status"] == "in_progress":
            return "[>>]"
        else:
            return "[  ]"

    def show_work_item(self, work_id: str) -> Optional[dict]:
        """Display detailed information about a work item."""
        if not self.work_items_file.exists():
            print("No work items found.")
            return None

        data = load_json(self.work_items_file)
        items = data.get("work_items", {})

        if work_id not in items:
            print(f"❌ Error: Work item '{work_id}' not found")
            print("\nAvailable work items:")
            for wid in list(items.keys())[:5]:
                print(f"  - {wid}")
            return None

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
                    icon = "✓" if dep_status == "completed" else "✗"
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

        # Specification
        spec_path = self.specs_dir / f"{work_id}.md"
        if spec_path.exists():
            print("Specification:")
            print("-" * 80)
            spec_content = spec_path.read_text()
            # Show first 50 lines (increased to include Acceptance Criteria section)
            lines = spec_content.split("\n")[:50]
            print("\n".join(lines))
            if len(spec_content.split("\n")) > 50:
                print(f"\n[... see full specification in .session/specs/{work_id}.md]")
            print()

        # Next steps
        print("Next Steps:")
        if item["status"] == "not_started":
            # Check dependencies
            blocked = any(
                items.get(dep_id, {}).get("status") != "completed"
                for dep_id in item.get("dependencies", [])
            )
            if blocked:
                print("- Waiting on dependencies to complete")
            else:
                print("- Start working: /start")
        elif item["status"] == "in_progress":
            print("- Continue working: /start")
        elif item["status"] == "completed":
            print("- Work item is complete")

        print(f"- Update fields: /work-update {work_id}")
        if item.get("milestone"):
            print(f"- View related items: /work-list --milestone {item['milestone']}")
        print()

        return item

    def update_work_item(self, work_id: str, **updates) -> bool:
        """Update work item fields."""
        if not self.work_items_file.exists():
            print("No work items found.")
            return False

        data = load_json(self.work_items_file)
        items = data.get("work_items", {})

        if work_id not in items:
            print(f"❌ Error: Work item '{work_id}' not found")
            return False

        item = items[work_id]
        changes = []

        # Apply updates
        for field, value in updates.items():
            if field == "status":
                if value not in ["not_started", "in_progress", "blocked", "completed"]:
                    print(f"⚠️  Invalid status: {value}")
                    continue
                old_value = item["status"]
                item["status"] = value
                changes.append(f"  status: {old_value} → {value}")

            elif field == "priority":
                if value not in self.PRIORITIES:
                    print(f"⚠️  Invalid priority: {value}")
                    continue
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
                        print(f"⚠️  Dependency '{value}' not found")

            elif field == "remove_dependency":
                deps = item.get("dependencies", [])
                if value in deps:
                    deps.remove(value)
                    item["dependencies"] = deps
                    changes.append(f"  removed dependency: {value}")

        if not changes:
            print("No changes made.")
            return False

        # Record update
        item.setdefault("update_history", []).append(
            {"timestamp": datetime.now().isoformat(), "changes": changes}
        )

        # Save
        data["work_items"][work_id] = item
        save_json(self.work_items_file, data)

        print(f"\nUpdated {work_id}:")
        for change in changes:
            print(change)
        print()

        return True

    def update_work_item_interactive(self, work_id: str) -> bool:
        """Interactive work item update."""
        if not self.work_items_file.exists():
            print("No work items found.")
            return False

        data = load_json(self.work_items_file)
        items = data.get("work_items", {})

        if work_id not in items:
            print(f"❌ Error: Work item '{work_id}' not found")
            return False

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

        choice = input("Your choice: ").strip()

        if choice == "1":
            status = input("New status (not_started/in_progress/blocked/completed): ").strip()
            return self.update_work_item(work_id, status=status)
        elif choice == "2":
            priority = input("New priority (critical/high/medium/low): ").strip()
            return self.update_work_item(work_id, priority=priority)
        elif choice == "3":
            milestone = input("Milestone name: ").strip()
            return self.update_work_item(work_id, milestone=milestone)
        elif choice == "4":
            dep = input("Dependency ID to add: ").strip()
            return self.update_work_item(work_id, add_dependency=dep)
        elif choice == "5":
            dep = input("Dependency ID to remove: ").strip()
            return self.update_work_item(work_id, remove_dependency=dep)
        else:
            print("Cancelled.")
            return False

    def get_next_work_item(self) -> Optional[dict]:
        """Find next work item to start."""
        if not self.work_items_file.exists():
            print("No work items found.")
            return None

        data = load_json(self.work_items_file)
        items = data.get("work_items", {})

        # Filter to not_started items
        not_started = {wid: item for wid, item in items.items() if item["status"] == "not_started"}

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
                    if items.get(dep_id, {}).get("status") != "completed"
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
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        ready_items.sort(key=lambda x: priority_order.get(x[1]["priority"], 99))

        # Get top item
        next_id, next_item = ready_items[0]

        # Display
        print("\nNext Recommended Work Item:")
        print("=" * 80)
        print()

        priority_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}

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

        return next_item

    def create_milestone(
        self, name: str, title: str, description: str, target_date: Optional[str] = None
    ) -> bool:
        """Create a new milestone."""
        if not self.work_items_file.exists():
            data = {"work_items": {}, "milestones": {}}
        else:
            data = load_json(self.work_items_file)
            if "milestones" not in data:
                data["milestones"] = {}

        if name in data["milestones"]:
            print(f"❌ Milestone '{name}' already exists")
            return False

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

        print(f"✓ Created milestone: {name}")
        return True

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
        completed = sum(1 for item in milestone_items if item["status"] == "completed")
        in_progress = sum(1 for item in milestone_items if item["status"] == "in_progress")
        not_started = sum(1 for item in milestone_items if item["status"] == "not_started")
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


def main():
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
