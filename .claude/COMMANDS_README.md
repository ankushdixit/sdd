# Claude Code Commands

This directory contains **executable command files** for Claude Code slash commands.

## Directory Structure

```
.claude/commands/          ← Claude Code reads these at runtime
├── session-init.md        ← Instructions for /session-init
├── session-start.md       ← Instructions for /session-start
├── session-end.md         ← Instructions for /session-end
├── session-validate.md    ← Instructions for /session-validate
├── session-status.md      ← Instructions for /session-status
├── work-item-create.md    ← Instructions for /work-item-create
├── work-item-list.md      ← Instructions for /work-item-list
├── work-item-show.md      ← Instructions for /work-item-show
├── work-item-update.md    ← Instructions for /work-item-update
└── work-item-next.md      ← Instructions for /work-item-next

commands/                  ← Full documentation (not used by Claude Code)
└── *.md                   ← Detailed specs for developers
```

## Two Types of Files

### `.claude/commands/*.md` (This Directory)
**Purpose**: Executable instructions for Claude Code
**Content**: Concise, actionable steps Claude follows
**Format**: Natural language instructions + code snippets
**Length**: Short (typically 20-50 lines)
**Example**:
```markdown
Execute: `python3 scripts/work_item_manager.py`
Display results to user.
```

### `commands/*.md` (Documentation Directory)
**Purpose**: Comprehensive documentation for developers
**Content**: Full specifications, examples, behavior details
**Format**: Structured documentation with examples
**Length**: Long (typically 50-150 lines)
**Example**: Full usage examples, edge cases, implementation details

## Available Commands

### Session Management
- `/session-init` - Initialize project with Session-Driven Development
- `/session-start` - Begin work session with comprehensive briefing
- `/session-end` - Complete session with quality gates
- `/session-validate` - Check quality standards mid-session
- `/session-status` - Quick session overview

### Work Item Management
- `/work-item-create` - Create new work item interactively
- `/work-item-list` - List work items with filtering
- `/work-item-show` - Show detailed work item information
- `/work-item-update` - Update work item fields
- `/work-item-next` - Get next recommended work item

## How Commands Work

1. **You type**: `/work-item-list` in Claude Code
2. **Claude reads**: `.claude/commands/work-item-list.md`
3. **Claude executes**: The Python code/bash commands specified
4. **Claude displays**: Formatted results to you

## Context is NOT Lost

The `.claude/commands/` files are **concise by design**. Full context exists in:
- `commands/*.md` - Detailed command documentation
- `scripts/*.py` - Complete implementation with comments
- `docs/*.md` - Methodology and framework documentation
- `PLUGIN_IMPLEMENTATION_PLAN.md` - Complete technical specifications

The short command files are just **runtime instructions** for Claude to follow.
Think of them as "quick reference cards" not "full manuals".

## Testing Commands

To test in a new session:
1. Open Claude Code in this project
2. Type `/help` to see all commands
3. Commands appear with "(project)" label
4. Try any command (e.g., `/work-item-list`)

## Adding New Commands

To add a new command:
1. Create `.claude/commands/your-command.md`
2. Write concise instructions for Claude
3. Include Python/bash commands to execute
4. Create full documentation in `commands/your-command.md`
5. The command is immediately available as `/your-command`

No restart or configuration needed!
