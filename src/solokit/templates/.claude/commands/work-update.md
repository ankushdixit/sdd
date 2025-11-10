---
description: Update work item fields
argument-hint: <work_item_id> <field>
---

# Work Item Update

Update specific fields of an existing work item.

## Usage

```bash
sk work-update "$@"
```

The work item ID and field are provided in `$ARGUMENTS` and passed through `"$@"`.

## Supported Fields

- **priority** - Change priority level (critical/high/medium/low)
- **milestone** - Set or update milestone
- **add-dependency** - Add dependency relationships
- **remove-dependency** - Remove existing dependencies

**Note:** Status is managed by session workflow (`/start`, `/end`) and cannot be changed directly.

## What It Does

The command will:
- Display current work item details
- Prompt for the new value based on field type
- Show available options for selection (priority, dependencies, etc.)
- Validate changes and update the work item
- Display confirmation with old → new values

## Examples

```bash
sk work-update bug_timeout priority
sk work-update feature_search milestone
sk work-update integration_test_api add-dependency
sk work-update feature_dashboard remove-dependency
```

## Field-Specific Behavior

**Priority:** Select from critical, high, medium, or low

**Milestone:** Enter milestone name (e.g., "Sprint 1", "Q1 2025")

**Add-dependency:** Select one or more work items to add as dependencies

**Remove-dependency:** Select one or more existing dependencies to remove

Show all command output to the user in a clear, formatted display.
