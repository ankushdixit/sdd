---
description: Start a new development session with comprehensive briefing
argument-hint: [work_item_id]
---

# Session Start

Generate a comprehensive session briefing by running:

```bash
python3 scripts/../sdd_cli.py start "$@"
```

If the user provided a work item ID in `$ARGUMENTS`, it will be passed through `"$@"`. If no ID is provided, the script will automatically find the next available work item.

The briefing includes:
- Complete project context (technology stack, directory tree, documentation)
- Work item details (title, type, priority, dependencies)
- Acceptance criteria and specifications
- Relevant past learnings from previous sessions
- Milestone context and progress (if the work item belongs to a milestone)

After generating the briefing:
1. Display the complete briefing to the user
2. Update the work item status to "in_progress" using the work item manager
3. Confirm the session has started and the user can begin working
