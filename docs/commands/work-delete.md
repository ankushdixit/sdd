# work-delete

Delete a work item from the SDD system.

## Synopsis

```bash
sdd work-delete <work_item_id> [--keep-spec | --delete-spec]
```

## Description

The `work-delete` command safely removes a work item from the system with dependency checking and interactive confirmation. It provides options to keep or delete the associated specification file.

## Arguments

### Required

- `<work_item_id>` - The ID of the work item to delete

### Optional Flags

- `--keep-spec` - Delete work item only, keep the specification file (non-interactive mode)
- `--delete-spec` - Delete both work item and specification file (non-interactive mode)

## Behavior

### Interactive Mode (default)

When no flags are provided, the command runs in interactive mode:

1. Validates the work item exists
2. Finds and displays dependent work items
3. Shows work item details (title, type, status, dependencies, dependents)
4. Prompts for confirmation with three options:
   - `1` - Delete work item only (keep spec file)
   - `2` - Delete work item and spec file
   - `3` - Cancel deletion
5. Performs deletion if confirmed
6. Updates metadata automatically
7. Warns about dependent work items

### Non-Interactive Mode

When `--keep-spec` or `--delete-spec` flags are provided:

- Skips interactive prompts
- Performs deletion with specified option
- Useful for automation and scripting

## Examples

### Interactive Deletion

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

### Non-Interactive Deletion (Keep Spec)

```bash
sdd work-delete feature_test_item --keep-spec
```

### Non-Interactive Deletion (Delete Spec)

```bash
sdd work-delete feature_test_item --delete-spec
```

### Cancelling Deletion

In interactive mode, choose option 3:
```
Choice [1]: 3
Deletion cancelled.
```

## What Gets Deleted

### Work Item Entry

The work item is removed from `.session/tracking/work_items.json`, including:
- All work item metadata
- Session history
- Git information
- Dependencies list

### Metadata Updates

The following metadata fields are automatically updated:
- `total_items` - Decremented by 1
- `completed` - Updated if deleted item was completed
- `in_progress` - Updated if deleted item was in progress
- `blocked` - Updated if deleted item was blocked

### Specification File (Optional)

If `--delete-spec` is chosen or option 2 is selected:
- The spec file at `.session/specs/{work_item_id}.md` is deleted
- If the spec file doesn't exist, a warning is shown but deletion continues

## Important Notes

### Dependent Work Items

**Work items that depend on the deleted item are NOT automatically updated.**

If you delete a work item that other items depend on:
1. You will receive a warning listing all dependent items
2. Those items will still have the deleted work item in their `dependencies` array
3. You must manually update or remove those dependencies using:
   ```bash
   sdd work-update <dependent_id> --remove-dependency <deleted_id>
   ```

### Deletion is Permanent

Once a work item is deleted:
- It cannot be recovered from the system
- Git history may still contain related commits
- Spec file can be recovered if kept or from git history

### Use Cases

Delete work items when:
- Created by mistake (wrong type, duplicate, etc.)
- Obsolete or no longer relevant
- Cleaning up test/experimental items
- Consolidating similar work items

## Safety Features

1. **Existence Validation** - Prevents deletion of non-existent items
2. **Dependency Checking** - Lists items that depend on the target
3. **Interactive Confirmation** - Requires explicit user confirmation
4. **Metadata Integrity** - Automatically updates all counts and statistics
5. **Clear Warnings** - Shows dependent items that may need manual updates
6. **Spec File Options** - Allows keeping spec for reference

## Error Handling

### Work Item Not Found

```bash
$ sdd work-delete nonexistent_item

❌ Error: Work item 'nonexistent_item' not found.

Available work items:
  - feature_auth
  - feature_dashboard
  - bug_login_issue
  ... and 5 more
```

### No Work Items File

```bash
$ sdd work-delete any_item

❌ Error: No work items found.
```

### Non-Interactive Without Flags

If run in non-interactive environment (CI/CD, scripts) without flags:

```
❌ Error: Cannot run interactive deletion in non-interactive mode

Please use command-line flags:
  sdd work-delete <work_item_id> --keep-spec   (delete work item only)
  sdd work-delete <work_item_id> --delete-spec (delete work item and spec)
```

## Related Commands

- [`work-list`](work-list.md) - List all work items to find items to delete
- [`work-show`](work-show.md) - View detailed work item information before deleting
- [`work-update`](work-update.md) - Update work item dependencies after deletion
- [`work-new`](work-new.md) - Create new work items

## See Also

- [Work Item Management Guide](../guides/work-item-management.md)
- [Session-Driven Development](../architecture/session-driven-development.md)
