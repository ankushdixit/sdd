---
description: Create a new work item interactively
---

# Work Item Create

Create a new work item using rich interactive UI components.

## Instructions

1. **First, gather basic information** using the `AskUserQuestion` tool with these 4 questions:

   **Question 1: Work Item Type**
   - Question: "What type of work item would you like to create?"
   - Header: "Type"
   - Multi-select: false
   - Options (limit: 4 options max):
     - Label: "feature", Description: "Standard feature development - New functionality or enhancement"
     - Label: "bug", Description: "Bug fix - Resolve an issue or defect"
     - Label: "refactor", Description: "Code refactoring - Improve code structure without changing behavior"
     - Label: "security", Description: "Security-focused work - Address security vulnerabilities or improvements"
   - Note: User can select "Type something" to manually enter: integration_test or deployment

   **Question 2: Title**
   - Question: "Enter a brief, descriptive title for the work item:"
   - Header: "Title"
   - Multi-select: false
   - Options: Provide 2-4 example titles based on the type selected in Question 1:
     - If type=feature: "Add authentication system", "Implement search feature"
     - If type=bug: "Fix database connection timeout", "Resolve login error"
     - If type=refactor: "Refactor authentication module", "Simplify error handling"
     - If type=security: "Fix SQL injection vulnerability", "Add input sanitization"
   - Note: User will select "Type something" to enter their custom title

   **Question 3: Priority**
   - Question: "What is the priority level for this work item?"
   - Header: "Priority"
   - Multi-select: false
   - Options:
     - Label: "critical", Description: "Blocking issue or urgent requirement"
     - Label: "high", Description: "Important work to be done soon (recommended default)"
     - Label: "medium", Description: "Normal priority work"
     - Label: "low", Description: "Nice to have, can be deferred"

   **Question 4: Urgent Status**
   - Question: "Does this work item require immediate attention? (Only ONE item can be urgent at a time)"
   - Header: "Urgent"
   - Multi-select: false
   - Options:
     - Label: "No", Description: "Normal workflow - will be prioritized by priority level and dependencies"
     - Label: "Yes", Description: "Mark as urgent - will override all other priority and be worked on immediately"

2. **Then, ask about dependencies** in a separate follow-up question (after you have the title):

   **Question 5: Dependencies (separate AskUserQuestion call)**
   - Question: "Does this work item depend on other work items? (Select all that apply)"
   - Header: "Dependencies"
   - Multi-select: true
   - Options:
     - **Use optimized script**: Run `python -m solokit.work_items.get_dependencies --title "<title_from_question_2>" --max 3`
     - This script automatically:
       - Excludes completed items (shows only: not_started, in_progress, blocked)
       - Filters by relevance based on the title
       - Returns up to 3 most relevant items
     - Parse the output and create options:
       - Format: Label: "{work_item_id}", Description: "[{priority}] [{type}] {title} ({status})"
       - Always include: Label: "No dependencies", Description: "This work item has no dependencies"
   - If more than 3 relevant items exist, user can select "Type something" to enter comma-separated IDs manually
   - If NO incomplete work items exist (script returns "No available dependencies found"), only show "No dependencies" option

3. **Validate inputs:**
   - Ensure type is one of: feature, bug, refactor, security, integration_test, deployment
   - Ensure title is not empty
   - Ensure priority is one of: critical, high, medium, low
   - Dependencies can be empty (no dependencies)
   - Urgent should be converted to boolean: "Yes" → add --urgent flag, "No" → omit flag

4. **Create the work item** by running:

```bash
sk work-new --type <type> --title "<title>" --priority <priority> --dependencies "<dep1,dep2>" [--urgent]
```

Examples:

```bash
# Normal work item with dependencies
sk work-new --type feature --title "Add user authentication" --priority high --dependencies "feature_database_setup,bug_session_timeout"

# Normal work item without dependencies
sk work-new --type feature --title "Add user authentication" --priority high --dependencies ""

# Urgent work item (if user selected "Yes" for urgent)
sk work-new --type bug --title "Critical security fix" --priority critical --urgent
```

4. **Show the output** to the user, which includes:
   - Created work item ID
   - Work item type and priority
   - Status (will be "not_started")
   - Dependencies (if any)
   - Path to the specification file (`.session/specs/{work_item_id}.md`)

## Error Handling

If the command fails:

- Check the error message
- If dependency doesn't exist: Re-prompt with valid dependencies list
- If work item already exists: Suggest using a different title or updating the existing item
- If validation error: Re-prompt with corrected information

## Next Step: Fill Out the Spec File

**IMPORTANT:** After creating the work item, you must fill out the specification file:

1. Open `.session/specs/{work_item_id}.md`
2. Follow the template structure and inline guidance comments
3. Complete all required sections for the work item type
4. Remove HTML comment instructions when done

The spec file is the **single source of truth** for work item content. All implementation details, acceptance criteria, and testing strategies should be documented in the spec file, not in `work_items.json`.

For guidance on writing effective specs, see:

- `docs/guides/writing-specs.md` - Best practices and examples
- `docs/reference/spec-template-structure.md` - Template structure reference
- `src/solokit/templates/{type}_spec.md` - Template examples for each work item type
