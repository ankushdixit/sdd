---
description: List all work items with optional filtering
argument-hint: [--status STATUS] [--type TYPE] [--milestone MILESTONE]
---

# Work Item List

List all work items, optionally filtered by status, type, or milestone.

**Without filters**, run:
```bash
python3 -c "from scripts.work_item_manager import WorkItemManager; WorkItemManager().list_work_items()"
```

**With filters**, parse $ARGUMENTS and pass to the function. For example:
- `--status not_started` → `status_filter='not_started'`
- `--type feature` → `type_filter='feature'`
- `--milestone phase_2_mvp` → `milestone_filter='phase_2_mvp'`

Available filter values:
- **Status**: `not_started`, `in_progress`, `blocked`, `completed`
- **Type**: `feature`, `bug`, `refactor`, `security`, `integration_test`, `deployment`
- **Milestone**: Any milestone name from the project

Display the color-coded work item list with priority indicators (🔴 critical, 🟠 high, 🟡 medium, 🟢 low) and dependency status markers (✓ ready, 🚫 blocked).
