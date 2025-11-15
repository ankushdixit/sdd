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

- **status** - Update status (not_started/in_progress/blocked/completed)
- **priority** - Change priority level (critical/high/medium/low)
- **milestone** - Set or update milestone
- **add-dependency** - Add dependency relationships
- **remove-dependency** - Remove existing dependencies
- **set-urgent** - Mark work item as urgent (only one item can be urgent at a time)
- **clear-urgent** - Remove urgent flag from work item

## What It Does

The command will:

- Display current work item details
- Prompt for the new value based on field type
- Show available options for selection (priority, dependencies, etc.)
- Validate changes and update the work item
- Display confirmation with old → new values

## Examples

```bash
sk work-update feat_001 --status in_progress
sk work-update feat_001 --priority critical
sk work-update feat_001 --add-dependency bug_002
sk work-update feat_001 --milestone "v1.0"
sk work-update feat_001 --status completed --priority high
sk work-update feat_001 --set-urgent
sk work-update feat_001 --clear-urgent
```

## Field-Specific Behavior

**Status:** Update to not_started, in_progress, blocked, or completed

**Priority:** Change to critical, high, medium, or low

**Milestone:** Set milestone name (e.g., "Sprint 1", "v1.0", "Q1 2025")

**Add-dependency:** Add work item IDs as dependencies (comma-separated)

**Remove-dependency:** Remove work item IDs from dependencies (comma-separated)

**Set-urgent:** Mark this item as urgent (requires immediate attention). Only ONE item can be urgent at a time. If another item is already urgent, it will be automatically cleared.

**Clear-urgent:** Remove the urgent flag from this work item

Show all command output to the user in a clear, formatted display.
