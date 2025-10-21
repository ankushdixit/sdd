---
description: Update work item fields
argument-hint: <work_item_id> [--field value]
---

# Work Item Update

Update fields of an existing work item. This command supports two modes:

## Interactive Mode

When only the work item ID is provided, start an interactive update session:

```bash
sdd work-update "$@"
```

The script will prompt the user to choose what to update:
1. Status (not_started, in_progress, blocked, completed)
2. Priority (critical, high, medium, low)
3. Milestone (assign or change milestone)
4. Add dependency (link to another work item)
5. Remove dependency (unlink from another work item)

## Direct Update Mode

Currently, only interactive mode is supported through the CLI. To use direct field updates, use the interactive mode and select the field to update when prompted.

After updating, display the changes made showing old → new values. All updates are automatically tracked in the work item's update_history.
