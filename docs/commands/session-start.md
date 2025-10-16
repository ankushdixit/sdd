# Session Start Command

**Usage:** `/session-start [--item <id>]`

**Description:** Initialize a development session with comprehensive briefing.

**Behavior:**

1. Check if project has `.session/` directory
   - If not: initialize project (create directory structure)
   - If yes: validate structure is intact

2. Determine which work item to work on:
   - If `--item <id>` provided: use that item
   - Otherwise: find next available item (dependencies satisfied)
   - If no items available: prompt to create one

3. Generate briefing:
   - Read work item details from `.session/tracking/work_items.json`
   - Read previous session notes
   - Read relevant learnings from `.session/tracking/learnings.json`
   - Create comprehensive briefing markdown

4. Present briefing to user (as markdown output)

5. Update work item status to "in_progress"

6. Begin implementation

**Example:**

```
User: /session-start

Claude: Initializing session...

Reading work items from .session/tracking/work_items.json...
Found 5 work items (2 completed, 3 pending)

Next available work item: implement_authentication
All dependencies satisfied ✓

# Session Briefing

## Work Item: Implement OAuth2 Authentication
- ID: implement_authentication
- Type: feature
- Priority: high
- Dependencies: setup_database ✓, create_user_model ✓

## Objective
Implement OAuth2 authentication flow with Google and GitHub providers.

## Implementation Checklist
- [ ] Create OAuth2 provider interface
- [ ] Implement Google OAuth2 flow
- [ ] Implement GitHub OAuth2 flow
- [ ] Add token refresh mechanism
- [ ] Write tests (coverage: 80%+)
- [ ] Update documentation

## Validation Requirements
- All tests must pass
- Coverage >= 80%
- Linting must pass
- Documentation updated

Starting work on implement_authentication...
```

**Implementation Details:**

The command markdown instructs Claude to:
1. Run script: `python scripts/briefing_generator.py`
2. Read generated briefing
3. Update work item status
4. Begin work
