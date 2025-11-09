# Work New Command

**Usage:** `/sdd:work-new`

**Description:** Create a new work item interactively with rich UI components.

## Overview

The `work-new` command creates new work items through an interactive flow that:
- Guides you through selecting work item type, title, priority
- Shows relevant dependencies based on context
- Creates a specification file from the appropriate template
- Updates work item tracking

## Interactive Flow

The command asks 4 questions using interactive UI:

### 1. Work Item Type

**Question:** "What type of work item would you like to create?"

**Options:**
- **feature** - Standard feature development (new functionality or enhancement)
- **bug** - Bug fix (resolve an issue or defect)
- **refactor** - Code refactoring (improve structure without changing behavior)
- **security** - Security-focused work (address vulnerabilities or improvements)

You can also type custom types: `integration_test` or `deployment`

### 2. Title

**Question:** "Enter a brief, descriptive title for the work item:"

The command provides example titles based on your selected type:
- **feature**: "Add authentication system", "Implement search feature"
- **bug**: "Fix database connection timeout", "Resolve login error"
- **refactor**: "Refactor authentication module", "Simplify error handling"
- **security**: "Fix SQL injection vulnerability", "Add input sanitization"

Select "Type something" to enter your custom title.

### 3. Priority

**Question:** "What is the priority level for this work item?"

**Options:**
- **critical** - Blocking issue or urgent requirement
- **high** - Important work to be done soon (recommended default)
- **medium** - Normal priority work
- **low** - Nice to have, can be deferred

### 4. Dependencies

**Question:** "Does this work item depend on other work items?"

The command automatically:
- Excludes completed items
- Filters by relevance based on your title
- Shows up to 3 most relevant incomplete work items

**Options format:**
```
work_item_id: [priority] [type] Title (status)
```

**Example:**
```
feature_database: [high] [feature] Setup database schema (in_progress)
refactor_models: [medium] [refactor] Refactor data models (not_started)
No dependencies: This work item has no dependencies
```

If no incomplete work items exist, only "No dependencies" option is shown.

You can select multiple dependencies (multi-select enabled).

## After Creation

Once the work item is created:

1. **Work item added to tracking** (`.session/tracking/work_items.json`)
   - Status: "not_started"
   - Type, priority, dependencies recorded

2. **Specification file created** (`.session/specs/{work_item_id}.md`)
   - Pre-filled with appropriate template based on type
   - Contains inline guidance comments
   - Ready for you to complete

3. **Output shows:**
   - Generated work item ID
   - Work item details
   - Path to spec file
   - Next steps

## Filling Out the Specification

**IMPORTANT:** The spec file is the **single source of truth** for work item content.

After creation, you must:

1. Open `.session/specs/{work_item_id}.md`
2. Follow the template structure and inline guidance comments
3. Complete all required sections for the work item type:
   - **Objective** - What needs to be accomplished
   - **Context** - Background and motivation
   - **Acceptance Criteria** - Specific, testable requirements
   - **Implementation Details** - Technical approach
   - **Validation Requirements** - Testing and quality standards
4. Remove HTML comment instructions when done

The spec file contains the complete implementation plan. The `work_items.json` file only stores metadata.

## Examples

### Creating a Feature

```bash
/sdd:work-new
```

**Interactive flow:**

```
What type of work item would you like to create?
● feature
○ bug
○ refactor
○ security

Enter a brief, descriptive title:
> Add user authentication

What is the priority level?
● high
○ critical
○ medium
○ low

Does this work item depend on other work items?
□ feature_database: [high] [feature] Setup database (in_progress)
□ refactor_models: [medium] [refactor] Refactor models (not_started)
☑ No dependencies

Work item created successfully!

ID: feature_auth
Type: feature
Priority: high
Status: not_started
Dependencies: None

Specification file: .session/specs/feature_auth.md

Next steps:
1. Complete the specification file
2. Start working: /sdd:start feature_auth
```

### Creating a Bug Fix with Dependencies

```bash
/sdd:work-new
```

**Interactive flow:**

```
What type of work item would you like to create?
○ feature
● bug
○ refactor
○ security

Enter a brief, descriptive title:
> Fix session timeout error

What is the priority level?
● critical
○ high
○ medium
○ low

Does this work item depend on other work items?
☑ feature_auth: [high] [feature] Add authentication (in_progress)
□ No dependencies

Work item created successfully!

ID: bug_session_timeout
Type: bug
Priority: critical
Status: not_started
Dependencies: feature_auth

Specification file: .session/specs/bug_session_timeout.md

Next steps:
1. Complete the specification file
2. Wait for dependencies to complete
3. Start working when ready: /sdd:start bug_session_timeout
```

## Work Item ID Generation

IDs are automatically generated from type and title:

- Format: `{type}_{simplified_title}`
- Title is simplified: lowercase, alphanumeric and underscores only
- Example: "Add User Authentication" → `feature_add_user_authentication`

## Spec Templates

Each work item type has a specific template:

- **feature** - Feature development with acceptance criteria
- **bug** - Bug report with reproduction steps
- **refactor** - Refactoring goals and validation
- **security** - Security assessment and remediation
- **integration_test** - Test plan and coverage
- **deployment** - Deployment checklist and rollback plan

Templates are located at: `src/sdd/templates/{type}_spec.md`

## Validation

The command validates:
- Type is one of supported types
- Title is not empty
- Priority is valid
- Dependencies exist and are not completed
- No duplicate work item IDs

## Error Handling

### Duplicate Work Item

```
ERROR: Work item 'feature_auth' already exists

Use a different title or update the existing item:
  /sdd:work-update feature_auth
```

### Invalid Dependency

```
ERROR: Dependency 'invalid_id' not found

Available work items:
  feature_database (in_progress)
  refactor_models (not_started)

Use /sdd:work-list to see all work items.
```

### Empty Title

```
ERROR: Work item title cannot be empty

Please provide a descriptive title for the work item.
```

## After Creating Work Item

1. **Review the spec file:**
   ```bash
   cat .session/specs/{work_item_id}.md
   ```

2. **Complete all sections** following inline guidance

3. **Verify completeness** - Ensure all acceptance criteria are clear

4. **Start working:**
   ```bash
   /sdd:start {work_item_id}
   ```

## See Also

- [Work List Command](work-list.md) - View all work items
- [Work Show Command](work-show.md) - View work item details
- [Work Update Command](work-update.md) - Update work item fields
- [Start Command](start.md) - Begin working on a work item
- [Writing Specs Guide](../guides/writing-specs.md) - Best practices for specifications
- [Spec Template Structure](../reference/spec-template-structure.md) - Template reference
