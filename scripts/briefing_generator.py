#!/usr/bin/env python3
"""
Generate session briefing for next work item.
Enhanced with full project context loading.
"""

import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime


def load_work_items():
    """Load work items from tracking file."""
    work_items_file = Path(".session/tracking/work_items.json")
    if not work_items_file.exists():
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
        # Return first 50 lines (preview)
        lines = tree_file.read_text().split("\n")
        return "\n".join(lines[:50])
    return "Tree not yet generated"


def validate_environment():
    """Validate development environment."""
    checks = []

    # Check Python version
    checks.append(f"Python: {sys.version.split()[0]}")

    # Check git
    try:
        result = subprocess.run(
            ["git", "--version"], capture_output=True, text=True, timeout=5
        )
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

            spec = importlib.util.spec_from_file_location(
                "git_integration", git_module_path
            )
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
    env_checks = validate_environment()
    git_status = check_git_status()

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

    # Vision (if available)
    if "vision.md" in project_docs:
        vision_preview = project_docs["vision.md"][:500]
        briefing += f"### Vision\n{vision_preview}...\n\n"

    # Architecture (if available)
    if "architecture.md" in project_docs:
        arch_preview = project_docs["architecture.md"][:500]
        briefing += f"### Architecture\n{arch_preview}...\n\n"

    # Current stack
    briefing += f"### Current Stack\n```\n{current_stack}\n```\n\n"

    # Project structure preview
    briefing += f"### Project Structure (Preview)\n```\n{current_tree}\n```\n\n"

    # Work item details
    briefing += f"""## Work Item Details

### Objective
{item.get("rationale", "No rationale provided")}

### Dependencies
"""

    # Show dependency status
    if item.get("dependencies"):
        for dep in item["dependencies"]:
            briefing += f"- {dep} ✓ completed\n"
    else:
        briefing += "No dependencies\n"

    briefing += "\n## Implementation Checklist\n\n"

    # Acceptance criteria become checklist
    if item.get("acceptance_criteria"):
        for criterion in item["acceptance_criteria"]:
            briefing += f"- [ ] {criterion}\n"
    else:
        briefing += "- [ ] Implement functionality\n"
        briefing += "- [ ] Write tests\n"
        briefing += "- [ ] Update documentation\n"

    # Relevant learnings
    relevant_learnings = get_relevant_learnings(learnings_data, item)
    if relevant_learnings:
        briefing += "\n## Relevant Learnings\n\n"
        for learning in relevant_learnings:
            briefing += (
                f"**{learning.get('category', 'general')}:** {learning['content']}\n\n"
            )

    # Validation requirements
    briefing += "\n## Validation Requirements\n\n"
    criteria = item.get("validation_criteria", {})
    if criteria.get("tests_pass", True):
        briefing += "- Tests must pass\n"
    if criteria.get("coverage_min"):
        briefing += f"- Coverage >= {criteria['coverage_min']}%\n"
    if criteria.get("linting_pass", True):
        briefing += "- Linting must pass\n"
    if criteria.get("documentation_required", False):
        briefing += "- Documentation must be updated\n"

    return briefing


def main():
    """Main entry point."""
    # Ensure .session directory exists
    session_dir = Path(".session")
    if not session_dir.exists():
        print("Error: .session directory not found. Run project initialization first.")
        return 1

    # Load data
    work_items_data = load_work_items()
    learnings_data = load_learnings()

    # Find next work item
    item_id, item = get_next_work_item(work_items_data)

    if not item_id:
        print("No available work items. All dependencies must be satisfied first.")
        return 1

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

            spec = importlib.util.spec_from_file_location(
                "git_integration", git_module_path
            )
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
