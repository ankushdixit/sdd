---
description: Update work item fields
argument-hint: <work_item_id> <field>
---

# Work Item Update

Update a specific field of an existing work item using interactive UI.

## Usage

```
/work-update <work_item_id> <field>
```

**Fields:** priority, milestone, add-dependency, remove-dependency

**Note:** Status changes are NOT allowed via this command. Status is managed automatically by session workflow (/start sets to in_progress, /end sets to completed).

**Examples:**
```
/work-update bug_timeout priority
/work-update feature_search milestone
/work-update integration_test_api add-dependency
/work-update feature_dashboard remove-dependency
```

## Instructions

1. **Parse arguments** from the command:
   - First argument: `work_item_id` (required)
   - Second argument: `field` (required)

   **If either is missing:**
   - Show error: "Usage: /work-update <work_item_id> <field>"
   - Show valid fields: priority, milestone, add-dependency, remove-dependency
   - Exit

   **If field = "status":**
   - Show error: "Status changes are not allowed via /work-update. Status is managed by session workflow (/start, /end)."
   - Exit

2. **Load and display current work item details** (optimized - fast metadata-only lookup):
   - Use `python -m sdd.work_items.get_metadata <work_item_id>` for fast metadata retrieval
   - This script reads ONLY the work item metadata from JSON, not the full spec file (much faster!)
   - If work item doesn't exist: Show error and suggest using `/work-list` to see available items
   - Display current values concisely:
     ```
     Current: {work_item_id}
     - Type: {type}
     - Status: {status}
     - Priority: {priority}
     - Milestone: {milestone or "(none)"}
     - Dependencies: {dependencies or "(none)"}
     ```

3. **Ask for the new value** based on field specified (use `AskUserQuestion`):

   **If field = "priority":**
   - Question: "Select new priority for {work_item_id}:"
   - Header: "Priority"
   - Multi-select: false
   - Options:
     - Label: "critical", Description: "Blocking issue or urgent requirement"
     - Label: "high", Description: "Important work to be done soon"
     - Label: "medium", Description: "Normal priority work"
     - Label: "low", Description: "Nice to have, can be deferred"

   **If field = "milestone":**
   - Question: "Enter milestone name for {work_item_id}:"
   - Header: "Milestone"
   - Multi-select: false
   - Options (provide examples, user selects "Type something"):
     - Label: "Sprint 1", Description: "Example milestone"
     - Label: "Q1 2025", Description: "Example milestone"

   **If field = "add-dependency":**
   - Query `.session/tracking/work_items.json` for available work items
   - Filter to show only: not_started, in_progress, or blocked items (exclude completed and self)
   - **Smart filtering**: Filter by relevance based on work item's title (e.g., if updating "feature_auth_ui", show auth-related items)
   - Question: "Select work items to add as dependencies for {work_item_id}: (Select multiple)"
   - Header: "Dependencies"
   - **Multi-select: true** (allows selecting multiple dependencies at once)
   - Options: Show up to 4 most relevant work items (prioritize: not_started > in_progress > blocked):
     - Label: "{work_item_id}", Description: "[{priority}] [{type}] {title} ({status})"
   - Note: User can select "Type something" to manually enter comma-separated IDs

   **If field = "remove-dependency":**
   - Use `python -m sdd.work_items.get_metadata <work_item_id> --with-deps` to get dependency details
   - This returns dependency IDs WITH their type and title in ONE efficient call!
   - If no dependencies: Show error "Work item has no dependencies to remove"
   - Question: "Select dependencies to remove from {work_item_id}: (Select multiple)"
   - Header: "Remove"
   - **Multi-select: true** (allows removing multiple dependencies at once)
   - Options: Show all current dependencies with details:
     - Label: "{dependency_id}", Description: "[{type}] {title} ({status})"

4. **Execute the update**:

   **For all fields:**
   ```bash
   sdd work-update <work_item_id> --<field> <value>
   ```

   **For dependencies** (if multiple selected, join with commas):
   ```bash
   sdd work-update <work_item_id> --add-dependency "dep1,dep2,dep3"
   sdd work-update <work_item_id> --remove-dependency "dep1,dep2"
   ```

   Examples:
   ```bash
   sdd work-update bug_timeout --priority critical
   sdd work-update feature_search --milestone "Sprint 2"
   sdd work-update integration_test_api --add-dependency feature_api_client
   sdd work-update integration_test_api --add-dependency "feature_api,feature_db,bug_auth"
   sdd work-update feature_dashboard --remove-dependency "bug_css_layout,feature_old"
   ```

5. **Show the output** to the user, which includes:
   - Confirmation of the update
   - Old value → New value
   - Update timestamp

## Error Handling

If the command fails:
- **Missing arguments**: Show usage and valid fields
- **Invalid work_item_id**: Show error and list available work items
- **Status field specified**: Show error explaining status is managed by session workflow
- **Invalid field**: Show error and list valid fields (priority, milestone, add-dependency, remove-dependency)
- **Invalid field value**: Re-prompt with valid options
- **Dependency doesn't exist**: Re-prompt with valid dependencies
- **No dependencies to remove**: Show error with message

## Notes

- Updates are automatically tracked in the work item's update_history
- Each update records timestamp and the changes made
- Status changes to "completed" trigger completion metadata
- The field argument uses hyphens (add-dependency, remove-dependency) matching the CLI flags
