# Work Delete Command

**Usage:** `/sdd:work-delete <work_item_id>`

**Description:** Delete a work item from the system with dependency checking and interactive confirmation.

## Overview

The `work-delete` command safely removes work items from the system:
- Checks for dependent work items
- Interactive confirmation with options
- Choice to keep or delete specification file
- Automatic metadata updates
- Warnings about manual cleanup needed

## Usage

```bash
/sdd:work-delete <work_item_id>
```

**Required argument:**
- `work_item_id` - ID of the work item to delete

## Interactive Flow

### Step 1: Dependency Check

The command finds work items that depend on the target:

```
Work Item: feature_obsolete
- Title: Obsolete Feature
- Type: feature
- Status: not_started
- Dependencies: (none)

⚠️  WARNING: 2 work item(s) depend on this item:
  - bug_related_fix [bug] Fix related issue
  - feature_dashboard [feature] Add dashboard

Deleting this item will NOT update their dependencies.
You'll need to manually update them after deletion.
```

If no dependents exist:
```
Work Item: feature_test
- Title: Test Feature
- Type: feature
- Status: not_started
- Dependencies: (none)

No other work items depend on this item.
Safe to delete.
```

### Step 2: Deletion Options

You'll be asked how to proceed:

**Question:** "How would you like to delete '{work_item_id}'?"

**Options:**

1. **Delete work item only (keep spec file)**
   - Removes from work_items.json
   - Keeps `.session/specs/{work_item_id}.md` for reference
   - Useful if you want to keep the specification documentation

2. **Delete work item and spec file**
   - Removes from work_items.json
   - Deletes `.session/specs/{work_item_id}.md`
   - Complete removal from the system

3. **Cancel deletion**
   - No changes made
   - Work item remains intact

### Step 3: Confirmation and Cleanup Reminder

After deletion:
```
✓ Deleted work item 'feature_obsolete'
✓ Deleted spec file '.session/specs/feature_obsolete.md'

⚠️  Reminder: Update dependencies for these work items:
  /sdd:work-update bug_related_fix remove-dependency
  /sdd:work-update feature_dashboard remove-dependency

Deletion successful.
```

## Examples

### Deleting Obsolete Work Item

```bash
/sdd:work-delete feature_old_implementation
```

**Interactive flow:**

```
Work Item: feature_old_implementation
- Title: Old Implementation Approach
- Type: feature
- Status: not_started
- Dependencies: feature_database

⚠️  WARNING: 1 work item(s) depend on this item:
  - bug_implementation_fix [bug] Fix implementation issue

Deleting this item will NOT update their dependencies.
You'll need to manually update them after deletion.

How would you like to delete 'feature_old_implementation'?

● Delete work item only (keep spec file)
  Remove from work_items.json but keep .session/specs/feature_old_implementation.md

○ Delete work item and spec file
  Permanently remove both the work item and its specification file

○ Cancel deletion
  Do not delete anything

→ Selected: Delete work item and spec file

✓ Deleted work item 'feature_old_implementation'
✓ Deleted spec file '.session/specs/feature_old_implementation.md'

⚠️  Reminder: Update dependencies for these work items:
  /sdd:work-update bug_implementation_fix remove-dependency

Deletion successful.
```

### Deleting Test Work Item

```bash
/sdd:work-delete feature_test
```

**Interactive flow:**

```
Work Item: feature_test
- Title: Test Feature
- Type: feature
- Status: completed
- Dependencies: (none)
- Completed: 2025-11-08

No other work items depend on this item.
Safe to delete.

How would you like to delete 'feature_test'?

○ Delete work item only (keep spec file)
○ Delete work item and spec file
● Cancel deletion

→ Selected: Cancel deletion

Deletion cancelled.
```

## What Gets Deleted

### Work Item Metadata (Always)

Removed from `.session/tracking/work_items.json`:
- Work item ID and metadata
- Title, type, priority, status
- Dependencies list
- Milestone assignment
- Creation and completion timestamps
- Session history
- Git commit information

### Specification File (Optional)

If "Delete work item and spec file" selected:
- File at `.session/specs/{work_item_id}.md` is deleted
- Cannot be recovered unless in git history
- Contains full implementation details and acceptance criteria

If "Delete work item only" selected:
- Spec file remains at `.session/specs/{work_item_id}.md`
- Can be used for reference or documentation
- Can be manually deleted later if needed

### Metadata Updates (Automatic)

The following are automatically updated:
- Total work items count
- Status-specific counts (completed, in_progress, blocked)
- Dependency relationships for this work item
- **Note:** Dependents are NOT automatically updated

## Important Warnings

### Dependent Work Items

**CRITICAL:** Work items that depend on the deleted item are NOT automatically updated.

**Before deletion:**
```
feature_dashboard depends on: feature_auth, feature_search
```

**After deleting feature_auth:**
```
feature_dashboard still depends on: feature_auth (DELETED), feature_search
```

**You must manually clean up:**
```bash
/sdd:work-update feature_dashboard remove-dependency
# Select feature_auth from the list
```

### Deletion is Permanent

Once deleted:
- Work item cannot be recovered from the system
- Only git history may contain related information
- Spec file can be recovered from git if it was deleted

### When to Delete

**Good reasons to delete:**
- Created by mistake (wrong type, duplicate)
- Work is obsolete or no longer relevant
- Cleaning up test/experimental items
- Consolidating duplicate work items

**Consider alternatives first:**
- If work is deferred, leave as "not_started" with low priority
- If work is cancelled, complete with note in commit message
- If work changes scope, update the spec file instead

## Error Handling

### Work Item Not Found

```bash
/sdd:work-delete nonexistent_item
```

**Output:**
```
ERROR: Work item 'nonexistent_item' not found

Available work items:
  feature_auth (in_progress)
  bug_timeout (not_started)
  refactor_api (not_started)

Use /sdd:work-list to see all work items.
```

### Missing Argument

```bash
/sdd:work-delete
```

**Output:**
```
ERROR: Usage: /sdd:work-delete <work_item_id>

Example:
  /sdd:work-delete feature_obsolete

Use /sdd:work-list to see all work items.
```

### Spec File Already Deleted

```
✓ Deleted work item 'feature_test'
⚠️  Spec file not found: .session/specs/feature_test.md
  (May have been manually deleted)

Deletion successful.
```

## Safety Features

1. **Existence Validation** - Verifies work item exists before deletion
2. **Dependency Checking** - Lists all dependent work items
3. **Interactive Confirmation** - Requires explicit user choice
4. **Metadata Integrity** - Automatically updates all counts
5. **Clear Warnings** - Shows dependent items needing manual cleanup
6. **Spec File Options** - Choice to keep for reference
7. **Optimized Performance** - Fast metadata-only lookup

## Use Cases

### Clean Up Duplicates

```bash
/sdd:work-list --type feature
# Find: feature_auth_v1 and feature_auth_v2 (duplicates)

/sdd:work-delete feature_auth_v1
# Select: Delete work item and spec file
```

### Remove Test Items

```bash
/sdd:work-list --type feature | grep test
# Find: feature_test_experiment

/sdd:work-delete feature_test_experiment
# Select: Delete work item and spec file
```

### Archive Obsolete Work

```bash
/sdd:work-delete feature_old_approach
# Select: Delete work item only (keep spec file)
# Spec file kept for historical reference
```

## After Deletion Workflow

### 1. Check for Dependents

```bash
/sdd:work-list --status blocked
# See if any items are now referencing deleted work item
```

### 2. Update Dependencies

```bash
/sdd:work-update <dependent_id> remove-dependency
# Remove reference to deleted work item
```

### 3. Verify Cleanup

```bash
/sdd:work-show <dependent_id>
# Verify dependencies are correct
```

### 4. Check Dependency Graph

```bash
/sdd:work-graph
# Visualize that no broken dependencies exist
```

## Integration with Other Commands

### Before Deletion

```bash
/sdd:work-show feature_obsolete  # Review details
/sdd:work-list  # Check dependents
/sdd:work-delete feature_obsolete  # Delete
```

### After Deletion

```bash
/sdd:work-list --status blocked  # Find affected items
/sdd:work-update <id> remove-dependency  # Clean up
/sdd:work-graph  # Verify graph integrity
```

## Optimized Performance

The command uses fast metadata-only lookup:
- Reads only `work_items.json` metadata
- Doesn't load full spec files
- Quickly finds dependents
- Instant response for current values

## See Also

- [Work List Command](work-list.md) - List all work items
- [Work Show Command](work-show.md) - View work item details before deleting
- [Work Update Command](work-update.md) - Update dependencies after deletion
- [Work New Command](work-new.md) - Create new work items
- [Work Graph Command](work-graph.md) - Visualize dependencies
