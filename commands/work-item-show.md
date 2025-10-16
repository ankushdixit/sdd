---
description: Show detailed information about a specific work item
argument-hint: <work_item_id>
---

# Work Item Show

Display detailed information for a specific work item by running:

```bash
python3 -c "from scripts.work_item_manager import WorkItemManager; WorkItemManager().show_work_item('$ARGUMENTS')"
```

The work item ID is provided in $ARGUMENTS.

This displays comprehensive details:
- **Work Item Info**: Type, status, priority, creation date
- **Dependencies**: List of dependencies with their current status
- **Session History**: All sessions where this work item was worked on
- **Git Information**: Branch name and associated commits
- **Specification Preview**: First 30 lines of the spec file
- **Next Steps**: Suggested actions based on current status

Show all information to the user in a clear, formatted display. This helps understand the full context of a work item before starting work on it.
