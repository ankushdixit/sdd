# Start Command

**Usage:** `/sdd:start [work_item_id]`

**Description:** Start a new development session with comprehensive briefing.

## Overview

The `start` command initializes a development session by:
- Selecting a work item (interactively or via argument)
- Generating a comprehensive briefing with full context
- Updating work item status to "in_progress"
- Beginning implementation following the specification

## Usage

### With Work Item ID

Start a specific work item directly:

```bash
/sdd:start feature_auth
```

### Interactive Selection

Run without arguments to see recommended work items:

```bash
/sdd:start
```

You'll be presented with up to 4 ready-to-start work items prioritized by:
- Dependencies satisfied
- Priority level
- Creation order

If no work items are ready (all blocked or in progress), you'll see an error message with guidance to use `/sdd:work-list` to review work item statuses.

## Briefing Contents

The session briefing includes:

### 1. Project Context
- Technology stack inventory (from `stack.txt`)
- Directory tree structure (from `tree.txt`)
- Project documentation

### 2. Work Item Details
- Title, type, priority, and status
- Dependencies and their completion status
- Milestone context (if applicable)

### 3. Full Specification
- Complete content from `.session/specs/{work_item_id}.md`
- This is the **single source of truth** for implementation
- Includes all acceptance criteria, validation requirements, and testing strategy
- Spec validation warnings if specification is incomplete

### 4. Previous Work Context (For In-Progress Items)
- All commits made in previous sessions
  - Full commit messages
  - File change statistics
- Quality gate results from each session
- Session dates and durations
- This eliminates context loss for multi-session work

### 5. Relevant Learnings (Top 10)
- Selected using multi-factor scoring:
  - Keyword matching from work item title and spec
  - Work item type matching
  - Tag overlap
  - Category bonuses (best_practices, patterns, architecture)
  - Recency weighting (recent learnings score higher)

### 6. Milestone Progress (If Applicable)
- Milestone details and progress
- Related work items in the milestone

## Implementation Guidelines

When implementing the work item, you MUST:

1. **Follow the spec strictly** - The work item specification in the briefing is your complete implementation guide

2. **Do not add features** - Only implement what is explicitly specified in the acceptance criteria

3. **Do not make assumptions** - If anything is unclear or ambiguous, ask the user for clarification before proceeding

4. **Check all requirements** - Ensure every acceptance criterion is met before considering the work complete

5. **Respect validation criteria** - Follow testing, documentation, and quality requirements specified in the spec

6. **Stay focused** - Do not deviate from the spec or add "helpful" extras unless explicitly requested

The specification defines the exact scope and boundaries of the work. Stay within them.

## Spec-First Architecture

The spec file (`.session/specs/{work_item_id}.md`) is the **single source of truth** for work item content:

- Contains complete implementation details, acceptance criteria, and testing strategy
- Passed in full to Claude during session briefings (no compression)
- Validated for completeness before session starts
- If spec validation warnings appear, review and complete the spec before proceeding

The `work_items.json` file only stores metadata (type, priority, status, dependencies). All implementation details live in the spec file.

## Examples

### Starting First Available Work Item

```bash
/sdd:start
```

**Output:**
```
Select a work item to start working on:

○ feature_auth: Add user authentication
  Type: feature | Priority: high

○ bug_timeout: Fix database connection timeout
  Type: bug | Priority: critical

○ refactor_api: Refactor API error handling
  Type: refactor | Priority: medium

○ Type something...
```

After selection, you'll receive the complete briefing and begin implementation.

### Starting Specific Work Item

```bash
/sdd:start feature_auth
```

**Output:**
```
=============================================================================
SESSION BRIEFING: feature_auth
=============================================================================

WORK ITEM: Add user authentication
TYPE: feature | PRIORITY: high | STATUS: in_progress

DEPENDENCIES:
✓ feature_database (completed)
✓ refactor_models (completed)

PREVIOUS WORK:
Session 1 (2025-11-08):
  - 3 commits
  - Files changed: 12 (+450, -120)
  - Quality: ✓ Tests passed | ✓ Linting | ✓ Coverage 85%

SPECIFICATION:
[Full spec content from .session/specs/feature_auth.md]

RELEVANT LEARNINGS:
1. [best_practices] Always validate JWT tokens on server-side...
2. [security] Use bcrypt for password hashing with cost factor 12...
[8 more learnings]

=============================================================================
BEGIN IMPLEMENTATION
=============================================================================
```

## Error Handling

### No Ready Work Items

```
ERROR: No work items ready to start

All work items are either:
- Blocked by dependencies
- Already in progress
- Completed

Use /sdd:work-list to see all work items and their status.
Use /sdd:work-new to create a new work item.
```

### Invalid Work Item ID

```
ERROR: Work item 'invalid_id' not found

Use /sdd:work-list to see all available work items.
```

### Work Item Already In Progress

```
ERROR: Work item 'feature_auth' is already in progress

To continue working on this item:
  /sdd:start feature_auth

To end current session first:
  /sdd:end
```

## After Starting

Once the session starts:

1. **Review the briefing** - Understand the full context and requirements
2. **Check previous work** - If resuming, review what was done in prior sessions
3. **Follow the spec** - Implement exactly what's specified in acceptance criteria
4. **Use learnings** - Apply relevant learnings from past sessions
5. **Stay focused** - Don't deviate from the specification

When implementation is complete:

```bash
/sdd:end
```

This will run quality gates, capture learnings, and create a session summary.

## See Also

- [End Command](end.md) - Complete a development session
- [Work New Command](work-new.md) - Create new work items
- [Work List Command](work-list.md) - View all work items
- [Work Next Command](work-next.md) - Get work item recommendations
- [Writing Specs Guide](../guides/writing-specs.md) - How to write effective specifications
