---
description: List all work items with optional filtering
argument-hint: [--status STATUS] [--type TYPE] [--milestone MILESTONE]
---

# Work Item List

List all work items, optionally filtered by status, type, or milestone.

Run the following command:

```bash
sk work-list "$@"
```

The CLI will automatically parse and handle filters from `$ARGUMENTS`:

- `--status not_started` → Filters by status
- `--type feature` → Filters by type
- `--milestone phase_2_mvp` → Filters by milestone

Available filter values:

- **Status**: `not_started`, `in_progress`, `blocked`, `completed`
- **Type**: `feature`, `bug`, `refactor`, `security`, `integration_test`, `deployment`
- **Milestone**: Any milestone name from the project

Display the color-coded work item list with priority indicators (🔴 critical, 🟠 high, 🟡 medium, 🟢 low) and dependency status markers (✓ ready, 🚫 blocked).
