---
description: Start a new development session with comprehensive briefing
argument-hint: [work_item_id]
---

# Session Start

Generate a comprehensive session briefing by running:

```bash
sdd start "$@"
```

If the user provided a work item ID in `$ARGUMENTS`, it will be passed through `"$@"`. If no ID is provided, the script will automatically find the next available work item.

The briefing includes:
- Complete project context (technology stack, directory tree, documentation)
- **Full work item specification from `.session/specs/{work_item_id}.md`** (source of truth)
- Work item tracking details (title, type, priority, dependencies)
- Spec validation warnings (if specification is incomplete)
- Relevant past learnings from previous sessions
- Milestone context and progress (if the work item belongs to a milestone)

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
