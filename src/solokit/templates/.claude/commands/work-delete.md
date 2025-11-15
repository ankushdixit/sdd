---
description: Delete a work item from the system
argument-hint: <work_item_id>
---

# Work Item Delete

Delete a work item from the system with optional spec file removal.

## Usage

```bash
sk work-delete "$@"
```

The work item ID is provided in `$ARGUMENTS` and passed through `"$@"`.

## What It Does

The command will:

- Display work item details and check for dependents
- Warn if other work items depend on this one
- Prompt for confirmation with options:
  - Delete work item only (keep spec file)
  - Delete both work item and spec file
  - Cancel deletion
- Execute deletion based on your selection
- Remind you to update dependent work items if needed

## Examples

```bash
sk work-delete feature_obsolete_item
sk work-delete bug_fixed_issue
```

## Important Notes

- **Deletion is permanent** - Work items cannot be recovered
- **Dependents are NOT modified** - If other items depend on the deleted item, you must manually update them using `/work-update <id> remove-dependency`
- **Spec files are optional** - You can choose to keep the spec file for reference

Show all command output to the user in a clear, formatted display.
