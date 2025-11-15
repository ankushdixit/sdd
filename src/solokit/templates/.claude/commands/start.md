---
description: Start a new development session with comprehensive briefing
argument-hint: [work_item_id]
---

# Session Start

## Step 1: Determine Work Item to Start

**If user provided a work item ID in `$ARGUMENTS`:**

- Skip to Step 3 and start that specific work item

**If no work item ID provided:**

- Continue to Step 2 for interactive selection

## Step 2: Get Recommendations and Ask User

Get the top 4 recommended work items:

```bash
python -m solokit.work_items.get_next_recommendations --limit 4
```

This will output ready-to-start work items in format:

```
work_item_id | type | title | priority
```

Parse the output and present options using `AskUserQuestion`:

**Question: Which work item do you want to start?**

- Question: "Select a work item to start working on:"
- Header: "Work Item"
- Multi-select: false
- Options (up to 4):
  - Label: "{work_item_id}: {title}", Description: "Type: {type} | Priority: {priority}"
  - Label: "{work_item_id}: {title}", Description: "Type: {type} | Priority: {priority}"
  - Label: "{work_item_id}: {title}", Description: "Type: {type} | Priority: {priority}"
  - Label: "{work_item_id}: {title}", Description: "Type: {type} | Priority: {priority}"

**Example option formatting:**

- Label: "feature_auth: Add user authentication"
- Description: "Type: feature | Priority: high"

**If no ready work items found:**

- The script will exit with error
- Show message: "No work items ready to start. All items are blocked by dependencies or already in progress."
- Display hint: "Use /work-list to see all work items and their status."
- Exit without calling command

## Step 3: Start Session

Based on the selected work item ID (either from user argument or interactive selection):

```bash
sk start {work_item_id}
```

Replace `{work_item_id}` with:

- The value from `$ARGUMENTS` if user provided it
- The selected work item ID from Step 2 if interactive selection was used

The briefing includes:

- Complete project context (technology stack, directory tree, documentation)
- **Previous work context** (for in-progress items) - commits made, files changed, quality gates from prior sessions
- **Full work item specification from `.session/specs/{work_item_id}.md`** (source of truth)
- Work item tracking details (title, type, priority, dependencies)
- Spec validation warnings (if specification is incomplete)
- **Top 10 relevant learnings** scored by keyword matching, type relevance, recency, and category
- Milestone context and progress (if the work item belongs to a milestone)

## Enhanced Briefings (Enhancement #11)

For **in-progress work items**, briefings include a "Previous Work" section with:

- All commits made in previous sessions (full messages, file stats)
- Quality gate results from each session
- Session dates and durations
- This makes multi-session work practical by eliminating context loss

**Learning relevance** uses multi-factor scoring:

- Keyword matching from work item title and spec
- Work item type matching
- Tag overlap (legacy support)
- Category bonuses (best_practices, patterns, architecture)
- Recency weighting (recent learnings score higher)
- Returns top 10 most relevant learnings (up from 5)

## Spec-First Architecture (Phase 5.7)

The spec file (`.session/specs/{work_item_id}.md`) is the **single source of truth** for work item content:

- Contains complete implementation details, acceptance criteria, and testing strategy
- Passed in full to Claude during session briefings (no compression)
- Validated for completeness before session starts
- If spec validation warnings appear, review and complete the spec before proceeding

After generating the briefing:

1. Display the complete briefing to the user
2. Update the work item status to "in_progress" using the work item manager
3. Begin implementation immediately following the guidelines below

## Implementation Guidelines

When implementing the work item, you MUST:

1. **Follow the spec strictly** - The work item specification in the briefing is your complete implementation guide
2. **Do not add features** - Only implement what is explicitly specified in the acceptance criteria
3. **Do not make assumptions** - If anything is unclear or ambiguous, ask the user for clarification before proceeding
4. **Check all requirements** - Ensure every acceptance criterion is met before considering the work complete
5. **Respect validation criteria** - Follow testing, documentation, and quality requirements specified in the spec
6. **Stay focused** - Do not deviate from the spec or add "helpful" extras unless explicitly requested

The specification defines the exact scope and boundaries of the work. Stay within them.

Now begin implementing the work item according to the specification.
