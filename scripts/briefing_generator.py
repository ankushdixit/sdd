#!/usr/bin/env python3
"""
Generate session briefing for next work item.
"""

import json
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
    Returns item with highest priority among available.
    """
    work_items = work_items_data.get("work_items", {})

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
    priority_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    available.sort(
        key=lambda x: priority_order.get(x[1].get("priority", "medium"), 2),
        reverse=True
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


def generate_briefing(item_id, item, learnings_data):
    """Generate markdown briefing for work item."""

    briefing = f"""# Session Briefing

## Work Item: {item['title']}
- **ID:** {item_id}
- **Type:** {item['type']}
- **Priority:** {item['priority']}
- **Status:** {item['status']}

## Objective

{item.get('rationale', 'No rationale provided')}

## Dependencies

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
            briefing += f"**{learning.get('category', 'general')}:** {learning['content']}\n\n"

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
    session_num = max(
        [int(f.stem.split("_")[1]) for f in briefings_dir.glob("session_*.md")],
        default=0
    ) + 1

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
        "status": "in_progress"
    }
    with open(status_file, "w") as f:
        json.dump(status, f, indent=2)

    return 0


if __name__ == "__main__":
    exit(main())
