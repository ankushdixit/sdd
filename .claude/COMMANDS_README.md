# Claude Code Commands

This directory contains **executable command files** for Claude Code slash commands.

## Directory Structure

```
.claude/commands/          ← Claude Code reads these at runtime
├── init.md                ← Instructions for /sdd:init
├── start.md               ← Instructions for /sdd:start
├── end.md                 ← Instructions for /sdd:end
├── validate.md            ← Instructions for /sdd:validate
├── status.md              ← Instructions for /sdd:status
├── work-new.md            ← Instructions for /sdd:work-new
├── work-list.md           ← Instructions for /sdd:work-list
├── work-show.md           ← Instructions for /sdd:work-show
├── work-update.md         ← Instructions for /sdd:work-update
├── work-next.md           ← Instructions for /sdd:work-next
├── work-graph.md          ← Instructions for /sdd:work-graph
├── learn.md               ← Instructions for /sdd:learn
├── learn-show.md          ← Instructions for /sdd:learn-show
├── learn-search.md        ← Instructions for /sdd:learn-search
└── learn-curate.md        ← Instructions for /sdd:learn-curate

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
- `/sdd:init` - Initialize project with Session-Driven Development
- `/sdd:start` - Begin work session with comprehensive briefing
- `/sdd:end` - Complete session with quality gates
- `/sdd:validate` - Check quality standards mid-session
- `/sdd:status` - Quick session overview

### Work Item Management
- `/sdd:work-new` - Create new work item interactively
- `/sdd:work-list` - List work items with filtering
- `/sdd:work-show` - Show detailed work item information
- `/sdd:work-update` - Update work item fields
- `/sdd:work-next` - Get next recommended work item
- `/sdd:work-graph` - Generate dependency graph visualization

### Learning System
- `/sdd:learn` - Capture a learning during development session
- `/sdd:learn-show` - Browse and filter learnings
- `/sdd:learn-search` - Search learnings by keyword
- `/sdd:learn-curate` - Run learning curation process

## How Commands Work

1. **You type**: `/sdd:work-list` in Claude Code
2. **Claude reads**: `.claude/commands/work-list.md`
3. **Claude executes**: The Python code/bash commands specified
4. **Claude displays**: Formatted results to you

## Context is NOT Lost

The `.claude/commands/` files are **concise by design**. Full context exists in:
- `commands/*.md` - Detailed command documentation
- `scripts/*.py` - Complete implementation with comments
- `docs/*.md` - Methodology and framework documentation
- `PLUGIN_IMPLEMENTATION_PLAN_PHASES_0-4.md` - Technical specs for Phases 0-4 (Foundation)
- `PLUGIN_IMPLEMENTATION_PLAN_PHASES_5+.md` - Technical specs for Phases 5+ (Quality & Operations)

The short command files are just **runtime instructions** for Claude to follow.
Think of them as "quick reference cards" not "full manuals".

## Testing Commands

To test in a new session:
1. Open Claude Code in this project
2. Type `/help` to see all commands
3. Commands appear with "(project)" label
4. Try any command (e.g., `/sdd:work-list`)

## Adding New Commands

To add a new command:
1. Create `.claude/commands/your-command.md`
2. Write concise instructions for Claude
3. Include Python/bash commands to execute
4. Create full documentation in `commands/your-command.md`
5. The command is immediately available as `/your-command`

No restart or configuration needed!
