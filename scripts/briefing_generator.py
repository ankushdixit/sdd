#!/usr/bin/env python3
"""
Generate session briefing for next work item.
Enhanced with full project context loading.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.logging_config import get_logger

logger = get_logger(__name__)

# Import spec validator for validation warnings
try:
    from spec_validator import format_validation_report, validate_spec_file
except ImportError:
    # Gracefully handle if spec_validator not available
    validate_spec_file = None
    format_validation_report = None


def load_work_items():
    """Load work items from tracking file."""
    work_items_file = Path(".session/tracking/work_items.json")
    logger.debug("Loading work items from: %s", work_items_file)
    if not work_items_file.exists():
        logger.warning("Work items file not found: %s", work_items_file)
        return {"work_items": {}}
    with open(work_items_file) as f:
        return json.load(f)


def load_learnings():
    """Load learnings from tracking file."""
    learnings_file = Path(".session/tracking/learnings.json")
    if not learnings_file.exists():
        return {"learnings": []}
    with open(learnings_file) as f:
        return json.load(f)


def get_next_work_item(work_items_data):
    """
    Find next available work item where dependencies are satisfied.
    Prioritizes resuming in-progress items over starting new work.
    Returns item with highest priority among available.
    """
    work_items = work_items_data.get("work_items", {})
    priority_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}

    # PRIORITY 1: Resume in-progress work
    in_progress_items = []
    for item_id, item in work_items.items():
        if item["status"] == "in_progress":
            in_progress_items.append((item_id, item))

    if in_progress_items:
        # Sort by priority and return highest
        in_progress_items.sort(
            key=lambda x: priority_order.get(x[1].get("priority", "medium"), 2),
            reverse=True,
        )
        return in_progress_items[0]

    # PRIORITY 2: Start new work
    available = []
    for item_id, item in work_items.items():
        if item["status"] != "not_started":
            continue

        # Check dependencies
        deps_satisfied = all(
            work_items.get(dep_id, {}).get("status") == "completed"
            for dep_id in item.get("dependencies", [])
        )

        if deps_satisfied:
            available.append((item_id, item))

    if not available:
        return None, None

    # Sort by priority
    available.sort(
        key=lambda x: priority_order.get(x[1].get("priority", "medium"), 2),
        reverse=True,
    )

    return available[0]


def get_relevant_learnings(learnings_data, work_item):
    """Get learnings relevant to this work item."""
    learnings = learnings_data.get("learnings", [])
    relevant = []

    # Simple relevance: check if work item tags overlap with learning tags
    work_item_tags = set(work_item.get("tags", []))

    for learning in learnings:
        learning_tags = set(learning.get("tags", []))
        if work_item_tags & learning_tags:  # Intersection
            relevant.append(learning)

    # Limit to 5 most recent relevant learnings
    return sorted(relevant, key=lambda x: x.get("created_at", ""), reverse=True)[:5]


def load_milestone_context(work_item):
    """Load milestone context for briefing."""
    milestone_name = work_item.get("milestone")
    if not milestone_name:
        return None

    work_items_file = Path(".session/tracking/work_items.json")
    if not work_items_file.exists():
        return None

    with open(work_items_file) as f:
        data = json.load(f)

    milestones = data.get("milestones", {})
    milestone = milestones.get(milestone_name)

    if not milestone:
        return None

    # Calculate progress
    items = data.get("work_items", {})
    milestone_items = [item for item in items.values() if item.get("milestone") == milestone_name]

    total = len(milestone_items)
    completed = sum(1 for item in milestone_items if item["status"] == "completed")
    percent = int((completed / total) * 100) if total > 0 else 0

    return {
        "name": milestone_name,
        "title": milestone["title"],
        "description": milestone["description"],
        "target_date": milestone.get("target_date", ""),
        "progress": percent,
        "total_items": total,
        "completed_items": completed,
        "milestone_items": milestone_items,
    }


def load_project_docs():
    """Load project documentation for context."""
    docs = {}

    # Look for common doc files
    doc_files = ["docs/vision.md", "docs/prd.md", "docs/architecture.md", "README.md"]

    for doc_file in doc_files:
        path = Path(doc_file)
        if path.exists():
            docs[path.name] = path.read_text()

    return docs


def load_current_stack():
    """Load current technology stack."""
    stack_file = Path(".session/tracking/stack.txt")
    if stack_file.exists():
        return stack_file.read_text()
    return "Stack not yet generated"


def load_current_tree():
    """Load current project structure."""
    tree_file = Path(".session/tracking/tree.txt")
    if tree_file.exists():
        # Return full tree
        return tree_file.read_text()
    return "Tree not yet generated"


def load_work_item_spec(work_item) -> str:
    """Load work item specification file.

    Args:
        work_item: Either a work item dict with 'spec_file' and 'id' fields,
                  or a string work_item_id (for backwards compatibility)
    """
    # Handle backwards compatibility: accept both dict and string
    if isinstance(work_item, str):
        # Legacy call with just work_item_id string
        work_item_id = work_item
        spec_file = Path(".session/specs") / f"{work_item_id}.md"
    else:
        # New call with work item dict
        # Use spec_file from work item if available, otherwise fallback to ID-based pattern
        spec_file_path = work_item.get("spec_file")
        if spec_file_path:
            spec_file = Path(spec_file_path)
        else:
            # Fallback to legacy pattern for backwards compatibility
            spec_file = Path(".session/specs") / f"{work_item['id']}.md"

    if spec_file.exists():
        return spec_file.read_text()
    return f"Specification file not found: {spec_file}"


def shift_heading_levels(markdown_content: str, shift: int) -> str:
    """Shift all markdown heading levels by a specified amount.

    Args:
        markdown_content: The markdown text to process
        shift: Number of levels to shift (positive = deeper, e.g., H1 → H3 if shift=2)

    Returns:
        Modified markdown with shifted heading levels

    Example:
        shift_heading_levels("# Title\n## Section", 2)
        Returns: "### Title\n#### Section"
    """
    if not markdown_content or shift <= 0:
        return markdown_content

    lines = markdown_content.split("\n")
    result = []

    for line in lines:
        # Check if line starts with heading marker
        if line.startswith("#"):
            # Count existing heading level
            heading_level = 0
            for char in line:
                if char == "#":
                    heading_level += 1
                else:
                    break

            # Calculate new level (cap at 6 for markdown)
            new_level = min(heading_level + shift, 6)

            # Reconstruct line with new heading level
            rest_of_line = line[heading_level:]
            result.append("#" * new_level + rest_of_line)
        else:
            result.append(line)

    return "\n".join(result)


def validate_environment():
    """Validate development environment."""
    checks = []

    # Check Python version
    checks.append(f"Python: {sys.version.split()[0]}")

    # Check git
    try:
        result = subprocess.run(["git", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            checks.append(f"Git: {result.stdout.strip()}")
        else:
            checks.append("Git: NOT FOUND")
    except:  # noqa: E722
        checks.append("Git: NOT FOUND")

    return checks


def check_git_status():
    """Check git status for session start."""
    try:
        # Import git workflow
        git_module_path = Path(__file__).parent / "git_integration.py"
        if git_module_path.exists():
            import importlib.util

            spec = importlib.util.spec_from_file_location("git_integration", git_module_path)
            git_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(git_module)

            workflow = git_module.GitWorkflow()
            is_clean, status_msg = workflow.check_git_status()
            current_branch = workflow.get_current_branch()

            return {"clean": is_clean, "status": status_msg, "branch": current_branch}
    except Exception as e:
        return {"clean": False, "status": f"Error checking git: {e}", "branch": None}

    return {"clean": True, "status": "Git check skipped", "branch": None}


def generate_briefing(item_id, item, learnings_data):
    """Generate comprehensive markdown briefing with full project context."""

    # Load all context
    project_docs = load_project_docs()
    current_stack = load_current_stack()
    current_tree = load_current_tree()
    work_item_spec = load_work_item_spec(item)
    env_checks = validate_environment()
    git_status = check_git_status()

    # Validate spec completeness (Phase 5.7.5)
    spec_validation_warning = None
    if validate_spec_file is not None:
        is_valid, errors = validate_spec_file(item_id, item["type"])
        if not is_valid:
            spec_validation_warning = format_validation_report(item_id, item["type"], errors)

    # Start briefing
    briefing = f"""# Session Briefing: {item["title"]}

## Quick Reference
- **Work Item ID:** {item_id}
- **Type:** {item["type"]}
- **Priority:** {item["priority"]}
- **Status:** {item["status"]}

## Environment Status
"""

    # Show environment checks
    for check in env_checks:
        briefing += f"- {check}\n"

    # Show git status
    briefing += "\n### Git Status\n"
    briefing += f"- Status: {git_status['status']}\n"
    if git_status.get("branch"):
        briefing += f"- Current Branch: {git_status['branch']}\n"

    # Project context section
    briefing += "\n## Project Context\n\n"

    # Vision (if available) - shift headings to maintain hierarchy under H3
    if "vision.md" in project_docs:
        shifted_vision = shift_heading_levels(project_docs["vision.md"], 3)
        briefing += f"### Vision\n\n{shifted_vision}\n\n"

    # Architecture (if available) - shift headings to maintain hierarchy under H3
    if "architecture.md" in project_docs:
        shifted_arch = shift_heading_levels(project_docs["architecture.md"], 3)
        briefing += f"### Architecture\n\n{shifted_arch}\n\n"

    # Current stack
    briefing += f"### Current Stack\n```\n{current_stack}\n```\n\n"

    # Project structure - full tree
    briefing += f"### Project Structure\n```\n{current_tree}\n```\n\n"

    # Spec validation warning (if spec is incomplete)
    if spec_validation_warning:
        briefing += f"""## ⚠️ Specification Validation Warning

{spec_validation_warning}

**Note:** Please review and complete the specification before proceeding with implementation.

"""

    # Work item specification - shift headings to maintain hierarchy under H2
    shifted_spec = shift_heading_levels(work_item_spec, 2)
    briefing += f"""## Work Item Specification

{shifted_spec}

## Dependencies
"""

    # Show dependency status
    if item.get("dependencies"):
        for dep in item["dependencies"]:
            briefing += f"- {dep} ✓ completed\n"
    else:
        briefing += "No dependencies\n"

    # Add milestone context
    milestone_context = load_milestone_context(item)
    if milestone_context:
        briefing += f"""
## Milestone Context

**{milestone_context["title"]}**
{milestone_context["description"]}

Progress: {milestone_context["progress"]}% ({milestone_context["completed_items"]}/{milestone_context["total_items"]} items complete)
"""
        if milestone_context["target_date"]:
            briefing += f"Target Date: {milestone_context['target_date']}\n"

        briefing += "\nRelated work items in this milestone:\n"
        # Show other items in same milestone
        for related_item in milestone_context["milestone_items"]:
            if related_item["id"] != item.get("id"):
                status_icon = "✓" if related_item["status"] == "completed" else "○"
                briefing += f"- {status_icon} {related_item['id']} - {related_item['title']}\n"
        briefing += "\n"

    # Relevant learnings
    relevant_learnings = get_relevant_learnings(learnings_data, item)
    if relevant_learnings:
        briefing += "\n## Relevant Learnings\n\n"
        for learning in relevant_learnings:
            briefing += f"**{learning.get('category', 'general')}:** {learning['content']}\n\n"

    return briefing


def check_command_exists(command: str) -> bool:
    """Check if a command is available."""
    try:
        subprocess.run([command, "--version"], capture_output=True, timeout=5)
        return True
    except Exception:
        return False


def generate_integration_test_briefing(work_item: dict) -> str:
    """
    Generate integration test specific briefing sections.

    Args:
        work_item: Integration test work item

    Returns:
        Additional briefing sections for integration tests
    """
    if work_item.get("type") != "integration_test":
        return ""

    briefing = "\n## Integration Test Context\n\n"

    # 1. Components being integrated (from scope description)
    scope = work_item.get("scope", "")
    if scope and len(scope) > 20:
        briefing += "**Integration Scope:**\n"
        briefing += f"{scope[:200]}...\n\n" if len(scope) > 200 else f"{scope}\n\n"

    # 2. Environment requirements
    env_requirements = work_item.get("environment_requirements", {})
    services = env_requirements.get("services_required", [])

    if services:
        briefing += "**Required Services:**\n"
        for service in services:
            briefing += f"- {service}\n"
        briefing += "\n"

    # 3. Test scenarios summary
    scenarios = work_item.get("test_scenarios", [])
    if scenarios:
        briefing += f"**Test Scenarios ({len(scenarios)} total):**\n"
        for i, scenario in enumerate(scenarios[:5], 1):  # Show first 5
            scenario_name = scenario.get("name", scenario.get("description", f"Scenario {i}"))
            briefing += f"{i}. {scenario_name}\n"

        if len(scenarios) > 5:
            briefing += f"... and {len(scenarios) - 5} more scenarios\n"
        briefing += "\n"

    # 4. Performance benchmarks
    benchmarks = work_item.get("performance_benchmarks", {})
    if benchmarks:
        briefing += "**Performance Requirements:**\n"

        response_time = benchmarks.get("response_time", {})
        if response_time:
            briefing += f"- Response time: p95 < {response_time.get('p95', 'N/A')}ms\n"

        throughput = benchmarks.get("throughput", {})
        if throughput:
            briefing += f"- Throughput: > {throughput.get('minimum', 'N/A')} req/s\n"

        briefing += "\n"

    # 5. API contracts
    contracts = work_item.get("api_contracts", [])
    if contracts:
        briefing += f"**API Contracts ({len(contracts)} contracts):**\n"
        for contract in contracts:
            briefing += f"- {contract.get('contract_file', 'N/A')} (version: {contract.get('version', 'N/A')})\n"
        briefing += "\n"

    # 6. Environment validation status
    briefing += "**Pre-Session Checks:**\n"

    # Check Docker
    docker_available = check_command_exists("docker")
    briefing += f"- Docker: {'✓ Available' if docker_available else '✗ Not found'}\n"

    # Check Docker Compose
    compose_available = check_command_exists("docker-compose")
    briefing += f"- Docker Compose: {'✓ Available' if compose_available else '✗ Not found'}\n"

    # Check compose file
    compose_file = env_requirements.get("compose_file", "docker-compose.integration.yml")
    compose_exists = Path(compose_file).exists()
    briefing += f"- Compose file ({compose_file}): {'✓ Found' if compose_exists else '✗ Missing'}\n"

    briefing += "\n"

    return briefing


def generate_deployment_briefing(work_item: dict) -> str:
    """
    Generate deployment-specific briefing section.

    Args:
        work_item: Deployment work item

    Returns:
        Deployment briefing text
    """
    if work_item.get("type") != "deployment":
        return ""

    briefing = []
    briefing.append("\n" + "=" * 60)
    briefing.append("DEPLOYMENT CONTEXT")
    briefing.append("=" * 60)

    spec = work_item.get("specification", "")

    # Parse deployment scope
    briefing.append("\n**Deployment Scope:**")
    # NOTE: Framework stub - Parse deployment scope from spec using spec_parser.py
    # Extract "## Deployment Scope" section and parse Application/Environment/Version fields
    briefing.append("  Application: [parse from spec]")
    briefing.append("  Environment: [parse from spec]")
    briefing.append("  Version: [parse from spec]")

    # Parse deployment procedure
    briefing.append("\n**Deployment Procedure:**")
    # NOTE: Framework stub - Parse deployment steps from spec using spec_parser.py
    # Extract "## Deployment Steps" section and count pre/during/post steps
    briefing.append("  Pre-deployment: [X steps]")
    briefing.append("  Deployment: [Y steps]")
    briefing.append("  Post-deployment: [Z steps]")

    # Parse rollback procedure
    briefing.append("\n**Rollback Procedure:**")
    # NOTE: Framework stub - Parse rollback details from spec using spec_parser.py
    # Extract "## Rollback Procedure" section for triggers and time estimates
    has_rollback = "rollback procedure" in spec.lower()
    briefing.append(f"  Rollback triggers defined: {'Yes' if has_rollback else 'No'}")
    briefing.append("  Estimated rollback time: [X minutes]")

    # Environment pre-checks
    briefing.append("\n**Pre-Session Environment Checks:**")
    try:
        import sys

        sys.path.insert(0, str(Path(__file__).parent))
        from environment_validator import EnvironmentValidator

        # NOTE: Framework stub - Parse target environment from spec using spec_parser.py
        # Extract from "## Deployment Scope" or "## Environment" section
        environment = "staging"  # Default fallback
        validator = EnvironmentValidator(environment)
        passed, results = validator.validate_all()

        briefing.append(f"  Environment validation: {'✓ PASSED' if passed else '✗ FAILED'}")
        for validation in results.get("validations", []):
            status = "✓" if validation["passed"] else "✗"
            briefing.append(f"    {status} {validation['name']}")
    except Exception as e:
        briefing.append(f"  Environment validation: ✗ Error ({str(e)})")

    briefing.append("\n" + "=" * 60)

    return "\n".join(briefing)


def main():
    """Main entry point."""
    logger.info("Starting session briefing generation")

    # Ensure .session directory exists
    session_dir = Path(".session")
    if not session_dir.exists():
        logger.error(".session directory not found")
        print("Error: .session directory not found. Run project initialization first.")
        return 1

    # Load data
    work_items_data = load_work_items()
    learnings_data = load_learnings()

    # Find next work item
    item_id, item = get_next_work_item(work_items_data)

    if not item_id:
        logger.warning("No available work items found")
        print("No available work items. All dependencies must be satisfied first.")
        return 1

    logger.info("Generating briefing for work item: %s", item_id)
    # Generate briefing
    briefing = generate_briefing(item_id, item, learnings_data)

    # Save briefing
    briefings_dir = session_dir / "briefings"
    briefings_dir.mkdir(exist_ok=True)

    # Determine session number
    session_num = (
        max(
            [int(f.stem.split("_")[1]) for f in briefings_dir.glob("session_*.md")],
            default=0,
        )
        + 1
    )

    # Start git workflow for work item
    try:
        # Import git workflow
        git_module_path = Path(__file__).parent / "git_integration.py"
        if git_module_path.exists():
            import importlib.util

            spec = importlib.util.spec_from_file_location("git_integration", git_module_path)
            git_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(git_module)

            workflow = git_module.GitWorkflow()
            git_result = workflow.start_work_item(item_id, session_num)

            if git_result["success"]:
                if git_result["action"] == "created":
                    print(f"✓ Created git branch: {git_result['branch']}\n")
                else:
                    print(f"✓ Resumed git branch: {git_result['branch']}\n")
            else:
                print(f"⚠️  Git workflow warning: {git_result['message']}\n")
    except Exception as e:
        print(f"⚠️  Could not start git workflow: {e}\n")

    # Update work item status and session tracking
    work_items_file = session_dir / "tracking" / "work_items.json"
    if work_items_file.exists():
        with open(work_items_file) as f:
            work_items_data = json.load(f)

        # Update work item status
        if item_id in work_items_data["work_items"]:
            work_item = work_items_data["work_items"][item_id]
            work_item["status"] = "in_progress"
            work_item["updated_at"] = datetime.now().isoformat()

            # Add session tracking
            if "sessions" not in work_item:
                work_item["sessions"] = []
            work_item["sessions"].append(
                {"session_num": session_num, "started_at": datetime.now().isoformat()}
            )

            # Update metadata
            work_items_data["metadata"]["in_progress"] = sum(
                1
                for item in work_items_data["work_items"].values()
                if item["status"] == "in_progress"
            )
            work_items_data["metadata"]["last_updated"] = datetime.now().isoformat()

            # Save updated work items
            with open(work_items_file, "w") as f:
                json.dump(work_items_data, f, indent=2)

    briefing_file = briefings_dir / f"session_{session_num:03d}_briefing.md"
    with open(briefing_file, "w") as f:
        f.write(briefing)

    # Print briefing
    print(briefing)

    # Update status file
    status_file = session_dir / "tracking" / "status_update.json"
    status = {
        "current_session": session_num,
        "current_work_item": item_id,
        "started_at": datetime.now().isoformat(),
        "status": "in_progress",
    }
    with open(status_file, "w") as f:
        json.dump(status, f, indent=2)

    return 0


if __name__ == "__main__":
    exit(main())
