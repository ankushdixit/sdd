# Work Update Command

**Usage:** `/sdd:work-update <work_item_id> <field>`

**Description:** Update a specific field of an existing work item using interactive UI.

## Overview

The `work-update` command allows you to modify work item properties:
- Priority
- Milestone assignment
- Dependencies (add or remove)

**Note:** Status changes are NOT allowed via this command. Status is managed automatically by the session workflow (`/sdd:start` sets to in_progress, `/sdd:end` sets to completed).

## Usage

```bash
/sdd:work-update <work_item_id> <field>
```

**Required arguments:**
- `work_item_id` - ID of the work item to update
- `field` - Field to update (priority, milestone, add-dependency, remove-dependency)

## Available Fields

### priority
Update work item priority level

```bash
/sdd:work-update feature_auth priority
```

### milestone
Assign work item to a milestone

```bash
/sdd:work-update feature_auth milestone
```

### add-dependency
Add a dependency to the work item

```bash
/sdd:work-update feature_auth add-dependency
```

### remove-dependency
Remove an existing dependency

```bash
/sdd:work-update feature_auth remove-dependency
```

## Interactive Flow

### Step 1: Fast Metadata Lookup

The command quickly displays current work item details:

```
Current: feature_auth
- Type: feature
- Status: not_started
- Priority: high
- Milestone: (none)
- Dependencies: feature_database
```

Uses optimized metadata-only lookup (doesn't read full spec file) for fast response.

### Step 2: Interactive Selection

Based on the field specified, you'll be prompted to select the new value.

## Examples

### Update Priority

```bash
/sdd:work-update bug_timeout priority
```

**Interactive flow:**

```
Current: bug_timeout
- Type: bug
- Status: in_progress
- Priority: medium
- Milestone: sprint_1
- Dependencies: (none)

Select new priority for bug_timeout:

○ critical
  Blocking issue or urgent requirement

● high
  Important work to be done soon

○ medium
  Normal priority work

○ low
  Nice to have, can be deferred

→ Selected: high

Updated bug_timeout priority: medium → high
```

### Assign Milestone

```bash
/sdd:work-update feature_search milestone
```

**Interactive flow:**

```
Current: feature_search
- Type: feature
- Status: not_started
- Priority: high
- Milestone: (none)
- Dependencies: feature_auth

Enter milestone name for feature_search:

○ Sprint 1
  Example milestone

○ Q1 2025
  Example milestone

● Type something...

→ Enter custom: sprint_2

Updated feature_search milestone: (none) → sprint_2
```

### Add Dependency

```bash
/sdd:work-update feature_dashboard add-dependency
```

**Interactive flow:**

```
Current: feature_dashboard
- Type: feature
- Status: not_started
- Priority: medium
- Milestone: sprint_2
- Dependencies: (none)

Select dependency to add for feature_dashboard:

□ feature_auth: [high] [feature] Add authentication (in_progress)
□ feature_search: [high] [feature] Implement search (not_started)
□ refactor_api: [medium] [refactor] Refactor API (not_started)

→ Selected: feature_auth

Added dependency: feature_dashboard → feature_auth

Status updated: not_started → blocked
(Work item is now blocked until feature_auth completes)
```

**Smart filtering:** Shows only relevant, incomplete work items. Excludes:
- Completed work items
- The work item itself
- Items that would create circular dependencies

### Remove Dependency

```bash
/sdd:work-update feature_dashboard remove-dependency
```

**Interactive flow:**

```
Current: feature_dashboard
- Type: feature
- Status: blocked
- Priority: medium
- Milestone: sprint_2
- Dependencies: feature_auth, feature_search

Select dependency to remove from feature_dashboard:

○ feature_auth: [high] [feature] Add authentication (in_progress)
○ feature_search: [high] [feature] Implement search (not_started)

→ Selected: feature_search

Removed dependency: feature_dashboard ↛ feature_search

Remaining dependencies: feature_auth
Status: blocked (still waiting on feature_auth)
```

## Status Management

**Important:** You cannot change work item status using this command.

If you try:
```bash
/sdd:work-update feature_auth status
```

**Output:**
```
ERROR: Status changes are not allowed via /work-update.

Status is managed by session workflow:
  - /sdd:start → Sets to "in_progress"
  - /sdd:end → Sets to "completed" or keeps "in_progress"

Use these commands to change status.
```

**Status transitions are automatic:**
- `not_started` → `in_progress` when you run `/sdd:start`
- `not_started` → `blocked` when you add an incomplete dependency
- `blocked` → `not_started` when all dependencies complete
- `in_progress` → `completed` when you run `/sdd:end` and select "Yes"
- `in_progress` → `in_progress` when you run `/sdd:end` and select "No"

## Validation

The command validates:

### Priority Updates
- Must be one of: critical, high, medium, low
- Can update at any time regardless of status

### Milestone Updates
- Can be any string (no validation)
- Can be empty to remove milestone assignment
- Can update at any time

### Add Dependency
- Dependency must exist
- Dependency cannot be completed (no point depending on completed work)
- Dependency cannot be the work item itself (no self-dependencies)
- Dependency cannot create circular dependencies
- **Automatically blocks work item** if dependency is not completed

### Remove Dependency
- Dependency must currently exist for the work item
- **Automatically unblocks work item** if it was the last incomplete dependency

## Error Handling

### Missing Arguments

```bash
/sdd:work-update feature_auth
```

**Output:**
```
ERROR: Usage: /sdd:work-update <work_item_id> <field>

Valid fields: priority, milestone, add-dependency, remove-dependency

Example:
  /sdd:work-update feature_auth priority
  /sdd:work-update feature_auth milestone
```

### Work Item Not Found

```bash
/sdd:work-update nonexistent_item priority
```

**Output:**
```
ERROR: Work item 'nonexistent_item' not found

Use /sdd:work-list to see all available work items.
```

### Invalid Field

```bash
/sdd:work-update feature_auth invalid_field
```

**Output:**
```
ERROR: Invalid field 'invalid_field'

Valid fields: priority, milestone, add-dependency, remove-dependency
```

### Circular Dependency

```bash
/sdd:work-update feature_auth add-dependency
# Select feature_search (which already depends on feature_auth)
```

**Output:**
```
ERROR: Circular dependency detected

Cannot add feature_search as dependency because:
  feature_search → feature_auth (already exists)
  feature_auth → feature_search (would create cycle)

This would create an unresolvable dependency chain.
```

### Completed Dependency

```bash
/sdd:work-update feature_dashboard add-dependency
# Try to select feature_auth (which is completed)
```

**Output:**
```
ERROR: Cannot add completed work item as dependency

feature_auth is already completed. There's no point in depending on
completed work items.

Only incomplete work items (not_started, in_progress, blocked) can be
added as dependencies.
```

## Optimized Performance

The command uses fast metadata-only lookup:
- Reads only `work_items.json` metadata
- Does NOT read full spec files
- Provides instant response for current values
- Only loads spec when absolutely necessary

## Automatic Status Updates

When you modify dependencies, status is automatically updated:

**Adding incomplete dependency:**
```
Before: feature_dashboard (not_started, no dependencies)
Add dependency: feature_auth (in_progress)
After: feature_dashboard (blocked, depends on feature_auth)
```

**Removing last incomplete dependency:**
```
Before: feature_dashboard (blocked, depends on feature_auth)
Remove dependency: feature_auth
After: feature_dashboard (not_started, no dependencies)
```

**Removing one of multiple dependencies:**
```
Before: feature_dashboard (blocked, depends on feature_auth, feature_search)
Remove dependency: feature_search
After: feature_dashboard (blocked, depends on feature_auth)
Status: Still blocked because feature_auth is incomplete
```

## Integration with Other Commands

### After updating priority:
```bash
/sdd:work-update feature_auth priority
/sdd:work-list --type feature  # See updated priority
/sdd:work-next  # New priority affects recommendations
```

### After updating milestone:
```bash
/sdd:work-update feature_auth milestone
/sdd:work-list --milestone sprint_1  # See items in milestone
```

### After updating dependencies:
```bash
/sdd:work-update feature_dashboard add-dependency
/sdd:work-show feature_dashboard  # Verify dependencies
/sdd:work-graph  # Visualize dependency graph
```

## See Also

- [Work List Command](work-list.md) - List all work items
- [Work Show Command](work-show.md) - View detailed work item information
- [Work Graph Command](work-graph.md) - Visualize dependencies
- [Work New Command](work-new.md) - Create new work items
- [Work Delete Command](work-delete.md) - Delete work items
