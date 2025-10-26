---
description: Delete a work item from the system
---

# Work Item Delete

Delete a work item from the SDD system with dependency checking and interactive confirmation.

Run the following command:

```bash
sdd work-delete <work_item_id>
```

Replace `<work_item_id>` with the actual work item ID to delete (e.g., `feature_obsolete_item`).

## Command Behavior

The delete command will:

1. **Validate** that the work item exists
2. **Check dependencies** to find work items that depend on this one
3. **Display work item details** including:
   - Title, type, status
   - Dependencies (what this item depends on)
   - Dependents (what items depend on this one)
4. **Prompt for confirmation** with three options:
   - Option 1: Delete work item only (keep spec file)
   - Option 2: Delete work item and spec file
   - Option 3: Cancel deletion
5. **Perform deletion** if confirmed:
   - Remove work item from `work_items.json`
   - Update metadata (total_items, status counts)
   - Optionally delete spec file
   - Warn about dependent work items that may need updating

## Non-Interactive Mode

For automation or scripts, use command-line flags:

**Delete work item only (keep spec):**
```bash
sdd work-delete <work_item_id> --keep-spec
```

**Delete work item and spec:**
```bash
sdd work-delete <work_item_id> --delete-spec
```

## Examples

**Interactive deletion:**
```bash
sdd work-delete feature_obsolete_item
```

Output:
```
⚠️  Warning: This will permanently delete work item 'feature_obsolete_item'

Work item details:
  Title: Obsolete Feature
  Type: feature
  Status: not_started
  Dependencies: none
  Dependents: bug_related_fix (1 item depends on this)

Options:
  1. Delete work item only (keep spec file)
  2. Delete work item and spec file
  3. Cancel

Choice [1]: 2

✓ Deleted work item 'feature_obsolete_item'
✓ Deleted spec file '.session/specs/feature_obsolete_item.md'
⚠️  Note: The following work items depend on this item:
    - bug_related_fix
  Update their dependencies manually if needed.

Deletion successful.
```

**Non-interactive deletion (keep spec):**
```bash
sdd work-delete feature_test_item --keep-spec
```

**Non-interactive deletion (delete spec):**
```bash
sdd work-delete feature_test_item --delete-spec
```

## Important Notes

1. **Deletion is permanent** - Work items cannot be recovered after deletion
2. **Dependents are not modified** - If other work items depend on the deleted item, their dependencies are NOT automatically updated. You will receive a warning listing affected work items
3. **Manual cleanup required** - After deleting a work item with dependents, you should manually update or remove those dependencies using `/work-update`
4. **Spec files are optional** - You can choose to keep the spec file for reference even after deleting the work item

## When to Use This Command

Use `/work-delete` when:
- A work item was created by mistake
- A work item is obsolete or no longer relevant
- You want to clean up your work item list
- You need to remove test or experimental work items

## Safety Features

- **Dependency checking**: Lists work items that depend on the item being deleted
- **Interactive confirmation**: Requires user confirmation before deletion
- **Metadata updates**: Automatically updates work item counts and statistics
- **Validation**: Prevents deletion of non-existent work items
- **Warnings**: Clear warnings about dependents that may need manual updates

## Related Commands

- `/work-list` - List all work items to find items to delete
- `/work-show <id>` - View work item details before deleting
- `/work-update <id>` - Update dependencies after deleting a work item
