# Work Item Update Command

**Usage:** `/work-item update <work_item_id> [--field value]`

**Description:** Update work item fields interactively or with flags.

**Updatable Fields:**
- `--status` - Change status (not_started, in_progress, blocked, completed)
- `--priority` - Change priority (critical, high, medium, low)
- `--milestone` - Assign to milestone
- `--add-dependency` - Add a dependency
- `--remove-dependency` - Remove a dependency

**Behavior:**

1. Load work item
2. If flags provided: Apply updates directly
3. If no flags: Interactive mode
4. Validate updates based on type
5. Record update in history
6. Save atomically

**Example:**

```
User: /work-item update feature_oauth --priority critical

Claude: Updated feature_oauth
  priority: high → critical

User: /work-item update feature_oauth

Claude: Update Work Item: feature_oauth

Current values:
  Status: in_progress
  Priority: critical
  Milestone: (none)

What would you like to update?
1. Status
2. Priority
3. Milestone
4. Add dependency
5. Remove dependency
6. Cancel

Your choice: 3

Enter milestone name: auth-mvp

Updated feature_oauth:
  milestone: (none) → auth-mvp
```
