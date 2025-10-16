# Work Item Create Command

**Usage:** `/work-item create`

**Description:** Interactively create a new work item with validation.

**Behavior:**

1. Prompt for work item type
   - Show list: feature, bug, refactor, security, integration_test, deployment
   - Validate selection

2. Load appropriate template
   - Read from templates/{type}_spec.md
   - Show template structure

3. Prompt for required fields
   - Title (required)
   - Priority (critical, high, medium, low)
   - Dependencies (optional, comma-separated IDs)
   - For integration_test/deployment: dependencies required

4. Generate work item ID
   - Format: {type}_{short_title}
   - Example: feature_oauth, bug_login_failure

5. Create specification file
   - Save to .session/specs/{work_item_id}.md
   - Pre-fill with template content

6. Update work_items.json
   - Add new work item entry
   - Set status to not_started
   - Record creation timestamp

7. Confirm creation
   - Display work item ID
   - Show next steps (edit spec, start session)

**Example:**

```
User: /work-item create

Claude: Creating new work item...

Select work item type:
1. feature - Standard feature development
2. bug - Bug fix
3. refactor - Code refactoring
4. security - Security-focused work
5. integration_test - Integration testing
6. deployment - Deployment to environment

Your choice (1-6): 1

Title: OAuth Integration

Priority (critical/high/medium/low) [high]: high

Dependencies (comma-separated IDs, or press Enter for none):

Work item created successfully!

ID: feature_oauth
Type: feature
Priority: high
Status: not_started

Specification saved to: .session/specs/feature_oauth.md

Next steps:
1. Edit specification: .session/specs/feature_oauth.md
2. Start working: /sdd:start
```
