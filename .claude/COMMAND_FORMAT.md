# Claude Code Command Format Standard

Based on [Official Anthropic Documentation](https://docs.claude.com/en/docs/claude-code/slash-commands#custom-slash-commands)

All command files in `.claude/commands/` must follow the official format with frontmatter and natural instruction style.

## Official Format Structure

Every command file must follow this template:

```markdown
---
description: Brief description of what the command does
argument-hint: [optional arguments]
---

# Command Title

Natural instructions for Claude on how to execute this command.

Include specific guidance on:
- How to run the command (with code blocks)
- What parameters to use
- What the command does
- What to display to the user
- Any special considerations
```

## Format Elements

### 1. Frontmatter (Required)

**YAML frontmatter** enclosed in `---` delimiters at the top of the file.

**Required fields:**
- `description`: Brief description shown in `/help` command

**Optional fields:**
- `argument-hint`: Helps autocomplete (e.g., `[work_item_id]`, `<pr-number> [priority]`)
- `allowed-tools`: Restrict tools Claude can use (e.g., `Bash(git add:*)`)
- `model`: Override model for this command
- `disable-model-invocation`: Prevent SlashCommand tool from calling this

**Example:**
```yaml
---
description: Create a new work item interactively
---
```

**Example with arguments:**
```yaml
---
description: Show detailed information about a specific work item
argument-hint: <work_item_id>
---
```

**Example with git tools:**
```yaml
---
description: Create a git commit
argument-hint: [message]
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)
---
```

### 2. Title (Optional but Recommended)

Use a markdown `# Heading` after frontmatter for clarity:

```markdown
# Session Init
```

### 3. Instruction Content

**Write as natural instructions for Claude**, not imperative commands.

**Good style:**
```markdown
Run the initialization script to set up Session-Driven Development infrastructure:

```bash
python3 scripts/init_project.py
```

This script will create:
- `.session/` directory structure with all subdirectories
- Tracking files: `work_items.json`, `learnings.json`, `status_update.json`

After running the script, show the user the success message and explain next steps.
```

**Bad style (avoid):**
```markdown
Execute: `python3 scripts/init_project.py`

Display the success message to the user.
```

The bad style uses imperative commands ("Execute:", "Display:") rather than natural instructions.

### 4. Argument Placeholders

Use these placeholders for dynamic values:

- `$ARGUMENTS` - Captures all arguments as a single string
- `$1`, `$2`, `$3` - Individual positional arguments

**Example:**
```markdown
The work item ID is provided in $ARGUMENTS.

```bash
python3 -c "from scripts.work_item_manager import WorkItemManager; WorkItemManager().show_work_item('$ARGUMENTS')"
```
```

**Example with positional args:**
```markdown
When field and value are provided (e.g., `--status completed`), parse $ARGUMENTS to extract:
- Work item ID (first argument: $1)
- Field name and value (remaining arguments)

Then run:
```bash
python3 -c "from scripts.work_item_manager import WorkItemManager; WorkItemManager().update_work_item('$1', field_name='value')"
```
```

### 5. Bash Command Execution (Optional)

Commands can execute bash commands *before* running using `!` prefix:

```markdown
---
allowed-tools: Bash(git status:*)
---

## Context

- Current git status: !`git status`
- Current branch: !`git branch --show-current`

## Your task

Based on the above changes, create a single git commit.
```

### 6. File References (Optional)

Include file contents using `@` prefix:

```markdown
Review the implementation in @src/utils/helpers.js

Compare @src/old-version.js with @src/new-version.js
```

## Complete Examples

### Simple Command (init.md)

```markdown
---
description: Initialize a new Session-Driven Development project
---

# Session Init

Run the initialization script to set up Session-Driven Development infrastructure:

```bash
python3 scripts/init_project.py
```

This script will create:
- `.session/` directory structure with all subdirectories
- Tracking files: `work_items.json`, `learnings.json`, `status_update.json`
- Project context files: `stack.txt` and `tree.txt`

After running the script, show the user the success message and explain the next steps for getting started with the session-driven workflow.
```

### Command with Arguments (work-show.md)

```markdown
---
description: Show detailed information about a specific work item
argument-hint: <work_item_id>
---

# Work Item Show

Display detailed information for a specific work item by running:

```bash
python3 -c "from scripts.work_item_manager import WorkItemManager; WorkItemManager().show_work_item('$ARGUMENTS')"
```

The work item ID is provided in $ARGUMENTS.

This displays comprehensive details:
- **Work Item Info**: Type, status, priority, creation date
- **Dependencies**: List of dependencies with their current status
- **Session History**: All sessions where this work item was worked on
- **Git Information**: Branch name and associated commits
- **Specification Preview**: First 30 lines of the spec file
- **Next Steps**: Suggested actions based on current status

Show all information to the user in a clear, formatted display. This helps understand the full context of a work item before starting work on it.
```

### Command with Multiple Modes (work-update.md)

```markdown
---
description: Update work item fields
argument-hint: <work_item_id> [--field value]
---

# Work Item Update

Update fields of an existing work item. This command supports two modes:

## Interactive Mode

When only the work item ID is provided, start an interactive update session:

```bash
python3 -c "from scripts.work_item_manager import WorkItemManager; WorkItemManager().update_work_item_interactive('$ARGUMENTS')"
```

The script will prompt the user to choose what to update:
1. Status (not_started, in_progress, blocked, completed)
2. Priority (critical, high, medium, low)
3. Milestone (assign or change milestone)
4. Add dependency (link to another work item)
5. Remove dependency (unlink from another work item)

## Direct Update Mode

When field and value are provided (e.g., `--status completed`), parse $ARGUMENTS to extract:
- Work item ID (first argument: $1)
- Field name and value (remaining arguments)

Then run:
```bash
python3 -c "from scripts.work_item_manager import WorkItemManager; WorkItemManager().update_work_item('$1', field_name='value')"
```

After updating, display the changes made showing old → new values. All updates are automatically tracked in the work item's update_history.
```

### Command with Filters (work-list.md)

```markdown
---
description: List all work items with optional filtering
argument-hint: [--status STATUS] [--type TYPE] [--milestone MILESTONE]
---

# Work Item List

List all work items, optionally filtered by status, type, or milestone.

**Without filters**, run:
```bash
python3 -c "from scripts.work_item_manager import WorkItemManager; WorkItemManager().list_work_items()"
```

**With filters**, parse $ARGUMENTS and pass to the function. For example:
- `--status not_started` → `status_filter='not_started'`
- `--type feature` → `type_filter='feature'`
- `--milestone phase_2_mvp` → `milestone_filter='phase_2_mvp'`

Available filter values:
- **Status**: `not_started`, `in_progress`, `blocked`, `completed`
- **Type**: `feature`, `bug`, `refactor`, `security`, `integration_test`, `deployment`
- **Milestone**: Any milestone name from the project

Display the color-coded work item list with priority indicators (🔴 critical, 🟠 high, 🟡 medium, 🟢 low) and dependency status markers (✓ ready, 🚫 blocked).
```

## Key Differences from Previous Format

### ❌ Old Format (Incorrect)
```markdown
Initialize a new Session-Driven Development project.

Execute: `python3 scripts/init_project.py`

Display the success message to the user.
```

### ✅ New Format (Correct)
```markdown
---
description: Initialize a new Session-Driven Development project
---

# Session Init

Run the initialization script to set up Session-Driven Development infrastructure:

```bash
python3 scripts/init_project.py
```

After running the script, show the user the success message and explain the next steps.
```

**Key improvements:**
1. ✅ Added frontmatter with `description`
2. ✅ Natural instruction style instead of imperative commands
3. ✅ No "Execute:" or "Display:" prefixes
4. ✅ Formatted code in fenced code blocks
5. ✅ Instructions written as guidance, not orders

## Validation Checklist

Before committing a command file:

- [ ] Frontmatter exists with `---` delimiters
- [ ] `description` field is populated
- [ ] `argument-hint` included if command accepts arguments
- [ ] Instructions written in natural language (not imperative)
- [ ] No "Execute:", "Display:", "Replace:" style commands
- [ ] Code blocks use fenced syntax (triple backticks)
- [ ] Argument placeholders use `$ARGUMENTS`, `$1`, `$2` format
- [ ] File explains what to show user (not "Display to user")
- [ ] Tested command appears in `/help` with correct description
- [ ] Command executes correctly in Claude Code session

## Plugin Command Structure

For plugins, commands in `commands/` directory follow the same format. Commands are namespaced by the plugin name:

```
commands/
  init.md           → /sdd:init
  work-new.md       → /sdd:work-new
  work-list.md      → /sdd:work-list
```

Commands are automatically namespaced by plugin name (e.g., `/sdd:command-name`).

## References

- [Official Slash Commands Documentation](https://docs.claude.com/en/docs/claude-code/slash-commands)
- [Custom Slash Commands](https://docs.claude.com/en/docs/claude-code/slash-commands#custom-slash-commands)
- [Plugin Commands](https://docs.claude.com/en/docs/claude-code/slash-commands#plugin-commands)
