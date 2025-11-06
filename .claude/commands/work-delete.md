---
description: Delete a work item from the system
argument-hint: <work_item_id>
---

# Work Item Delete

Delete a work item from the SDD system with dependency checking and interactive confirmation.

## Usage

```
/work-delete <work_item_id>
```

## Instructions

1. **Parse the work_item_id** from the command arguments

   **If missing:**
   - Show error: "Usage: /work-delete <work_item_id>"
   - Exit

2. **Load and display work item details** (optimized):
   - Use `python -m sdd.work_items.get_metadata <work_item_id> --with-deps` for fast lookup
   - If work item doesn't exist: Show error and suggest using `/work-list`
   - Display current values:
     ```
     Work Item: {work_item_id}
     - Title: {title}
     - Type: {type}
     - Status: {status}
     - Dependencies: {dependencies or "(none)"}
     ```

3. **Check for dependents** (work items that depend on this one):
   - **Use optimized script**: Run `python -m sdd.work_items.get_dependents <work_item_id>`
   - This script efficiently finds all work items that depend on the given work item
   - If dependents exist, show warning:
     ```
     ⚠️  WARNING: {count} work item(s) depend on this item:
       - {dependent_id_1} [{type}] {title}
       - {dependent_id_2} [{type}] {title}

     Deleting this item will NOT update their dependencies.
     You'll need to manually update them after deletion.
     ```

4. **Ask for confirmation** using `AskUserQuestion`:

   **Question: Deletion Confirmation**
   - Question: "How would you like to delete '{work_item_id}'?"
   - Header: "Delete"
   - Multi-select: false
   - Options:
     - Label: "Delete work item only (keep spec file)", Description: "Remove from work_items.json but keep .session/specs/{work_item_id}.md for reference"
     - Label: "Delete work item and spec file", Description: "Permanently remove both the work item and its specification file"
     - Label: "Cancel deletion", Description: "Do not delete anything"

5. **Execute deletion** based on user selection:

   **If "Delete work item only" selected:**
   ```bash
   sdd work-delete <work_item_id> --keep-spec
   ```

   **If "Delete work item and spec file" selected:**
   ```bash
   sdd work-delete <work_item_id> --delete-spec
   ```

   **If "Cancel deletion" selected:**
   - Show message: "Deletion cancelled."
   - Exit without calling command

6. **Show the output** to the user:
   - Confirmation of deletion
   - If spec file was deleted, confirm that too
   - If dependents exist, remind user to update them:
     ```
     ⚠️  Reminder: Update dependencies for these work items:
       /work-update {dependent_1} remove-dependency
       /work-update {dependent_2} remove-dependency
     ```

## Examples

```bash
sdd work-delete feature_obsolete_item --keep-spec
sdd work-delete feature_test_item --delete-spec
```

## Error Handling

If the command fails:
- **Missing work_item_id**: Show usage
- **Work item doesn't exist**: Show error and list available items
- **Missing flag**: This should never happen (command file ensures flag is provided)

## Important Notes

1. **Deletion is permanent** - Work items cannot be recovered after deletion
2. **Dependents are NOT modified** - If other work items depend on the deleted item, their dependencies are NOT automatically updated. User must manually update them.
3. **Spec files are optional** - User can choose to keep the spec file for reference
4. **Manual cleanup required** - After deleting a work item with dependents, remind user to update those dependencies using `/work-update <id> remove-dependency`

## Safety Features

- **Dependency checking**: Lists work items that depend on the item being deleted
- **Interactive confirmation**: Requires user confirmation with clear options
- **Metadata updates**: Automatically updates work item counts and statistics
- **Validation**: Prevents deletion of non-existent work items
- **Warnings**: Clear warnings about dependents that need manual updates

## Related Commands

- `/work-list` - List all work items to find items to delete
- `/work-show <id>` - View work item details before deleting
- `/work-update <id> remove-dependency` - Update dependencies after deleting a work item
