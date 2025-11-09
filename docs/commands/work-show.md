# Work Show Command

**Usage:** `/sdd:work-show <work_item_id>`

**Description:** Display detailed information about a specific work item including specification, dependencies, session history, and git information.

## Overview

The `work-show` command provides a comprehensive view of a work item:
- Complete metadata (type, status, priority, dates)
- Dependencies with their statuses
- Session history and git commits
- Specification file preview
- Suggested next actions

## Usage

```bash
/sdd:work-show <work_item_id>
```

**Required argument:**
- `work_item_id` - ID of the work item to display

## Output Sections

### 1. Work Item Metadata
- Title and ID
- Type, status, priority
- Creation date
- Completion date (if completed)
- Milestone assignment (if any)

### 2. Dependencies
- List of dependencies with statuses
- Completion markers (✓ completed, 🚫 blocked)
- Blocking status explanation

### 3. Session History
- All sessions where item was worked on
- Session dates and durations
- Commits made in each session
- Quality gate results

### 4. Git Information
- Branch name (if exists)
- Associated commits
- File change statistics

### 5. Specification Preview
- First 30 lines of spec file
- Link to full spec file
- Completion status

### 6. Next Steps
- Suggested actions based on status
- Commands to run

## Examples

### Viewing Not Started Work Item

```bash
/sdd:work-show feature_auth
```

**Output:**
```
===========================================================================
WORK ITEM: feature_auth
===========================================================================

DETAILS:
  Title: Add user authentication
  Type: feature
  Status: not_started
  Priority: high
  Created: 2025-11-07
  Milestone: sprint_1

DEPENDENCIES (2):
  ✓ feature_database (completed on 2025-11-06)
  ✓ refactor_models (completed on 2025-11-07)

All dependencies satisfied. Ready to start!

SPECIFICATION:
  File: .session/specs/feature_auth.md
  Preview (first 30 lines):

  # Feature: Add User Authentication

  ## Objective
  Implement JWT-based authentication system with email/password login
  and optional OAuth2 providers (Google, GitHub).

  ## Context
  The application currently has no authentication. Users need secure
  login to access protected features...

  [... 20 more lines ...]

  [View full spec: .session/specs/feature_auth.md]

SESSION HISTORY:
  No sessions yet. This work item hasn't been started.

NEXT STEPS:
  Start working:    /sdd:start feature_auth
  Update priority:  /sdd:work-update feature_auth priority
  View all items:   /sdd:work-list
```

### Viewing In-Progress Work Item

```bash
/sdd:work-show bug_session_timeout
```

**Output:**
```
===========================================================================
WORK ITEM: bug_session_timeout
===========================================================================

DETAILS:
  Title: Fix session timeout error
  Type: bug
  Status: in_progress
  Priority: critical
  Created: 2025-11-08
  Started: 2025-11-08 14:30
  Milestone: sprint_1

DEPENDENCIES:
  (none)

SPECIFICATION:
  File: .session/specs/bug_session_timeout.md
  Preview (first 30 lines):

  # Bug: Fix Session Timeout Error

  ## Problem Description
  Users are experiencing unexpected session timeouts after 5 minutes
  of inactivity, even though the timeout is configured for 30 minutes...

  [... 25 more lines ...]

  [View full spec: .session/specs/bug_session_timeout.md]

SESSION HISTORY:
  Session 1 (current session)
    Started: 2025-11-08 14:30
    Duration: 1h 25m (ongoing)
    Commits: 2
      1. fix: Update session timeout configuration
         Files: 3 (+45, -12)
      2. test: Add session timeout tests
         Files: 2 (+78, -0)

GIT INFORMATION:
  Branch: fix/session-timeout
  Total commits: 2
  Files changed: 5 (+123, -12)

NEXT STEPS:
  Complete work:    /sdd:end
  Validate quality: /sdd:validate
  View status:      /sdd:status
```

### Viewing Completed Work Item

```bash
/sdd:work-show feature_dashboard
```

**Output:**
```
===========================================================================
WORK ITEM: feature_dashboard
===========================================================================

DETAILS:
  Title: Add admin dashboard
  Type: feature
  Status: completed ✓
  Priority: high
  Created: 2025-11-06
  Completed: 2025-11-08
  Duration: 2 days
  Milestone: sprint_1

DEPENDENCIES (2):
  ✓ feature_auth (completed on 2025-11-07)
  ✓ feature_database (completed on 2025-11-06)

SPECIFICATION:
  File: .session/specs/feature_dashboard.md
  [Completed - all acceptance criteria met]

SESSION HISTORY:
  Session 1
    Date: 2025-11-07
    Duration: 2h 15m
    Commits: 4
      1. feat: Add dashboard layout components
         Files: 8 (+345, -0)
      2. feat: Implement user statistics widget
         Files: 4 (+156, -0)
      3. feat: Add activity timeline widget
         Files: 3 (+98, -0)
      4. style: Apply dashboard styling
         Files: 5 (+234, -12)
    Quality: ✓ All tests passed | ✓ Linting | ✓ Coverage 87%

  Session 2
    Date: 2025-11-08
    Duration: 1h 45m
    Commits: 3
      1. feat: Add export functionality
         Files: 4 (+123, -0)
      2. test: Complete dashboard test coverage
         Files: 6 (+287, -0)
      3. docs: Update dashboard documentation
         Files: 2 (+89, -5)
    Quality: ✓ All tests passed | ✓ Linting | ✓ Coverage 92%

GIT INFORMATION:
  Branch: feature/admin-dashboard (merged to main)
  Total commits: 7
  Files changed: 32 (+1332, -17)

COMPLETION SUMMARY:
  ✓ All acceptance criteria met
  ✓ Tests: 45/45 passed
  ✓ Coverage: 92%
  ✓ Code review: Approved
  ✓ Documentation: Complete

NEXT STEPS:
  View learnings:   /sdd:learn-show --session feature_dashboard
  Related items:    /sdd:work-list --milestone sprint_1
  Dependents:       (no items depend on this)
```

### Viewing Blocked Work Item

```bash
/sdd:work-show feature_search
```

**Output:**
```
===========================================================================
WORK ITEM: feature_search
===========================================================================

DETAILS:
  Title: Implement search feature
  Type: feature
  Status: blocked 🚫
  Priority: high
  Created: 2025-11-08
  Milestone: sprint_2

DEPENDENCIES (2):
  🚫 feature_auth (in_progress) - BLOCKING
  ✓ feature_database (completed on 2025-11-06)

Blocked by 1 incomplete dependency.

BLOCKING REASON:
  Cannot start until feature_auth is completed.
  feature_auth is currently in progress.

SPECIFICATION:
  File: .session/specs/feature_search.md
  Preview (first 30 lines):

  # Feature: Implement Search Feature

  ## Objective
  Add full-text search functionality across products, users, and content...

  [... 25 more lines ...]

  [View full spec: .session/specs/feature_search.md]

SESSION HISTORY:
  No sessions yet. Waiting on dependencies.

DEPENDENCY STATUS:
  feature_auth is 70% complete (based on commits and spec progress)
  Estimated unblock: ~1-2 sessions remaining

NEXT STEPS:
  View blocker:     /sdd:work-show feature_auth
  Check progress:   /sdd:status
  Update deps:      /sdd:work-update feature_search remove-dependency
  View graph:       /sdd:work-graph --focus feature_search
```

## Work Item States

### not_started
- Work item created but not yet begun
- May have dependencies (satisfied or not)
- Can start immediately if dependencies satisfied

### in_progress
- Currently being worked on
- Has active session
- Cannot start another work item until ended

### blocked
- Has unsatisfied dependencies
- Cannot start until blockers complete
- Automatically unblocks when dependencies finish

### completed
- All work finished
- Quality gates passed
- Marked complete in `/sdd:end`

## Understanding Dependencies

**✓ Completed dependency:**
```
✓ feature_database (completed on 2025-11-06)
```
- Green checkmark
- Shows completion date
- Not blocking

**🚫 Blocking dependency:**
```
🚫 feature_auth (in_progress) - BLOCKING
```
- Red X marker
- Shows current status
- Prevents work from starting

**(none):**
```
DEPENDENCIES:
  (none)
```
- No dependencies
- Can start immediately

## Session History Details

Each session shows:
- **Date and duration** - When and how long
- **Commits** - All commits made
- **File statistics** - Lines added/removed
- **Quality gates** - Test, lint, coverage results

This helps understand:
- How much work was done
- What files were changed
- Quality of implementation
- Progress across sessions

## Specification Preview

Shows first 30 lines of spec file:
- Quick overview without opening file
- See objectives and context
- Check acceptance criteria
- Link to view full file

**To view full spec:**
```bash
cat .session/specs/<work_item_id>.md
```

## Next Steps Suggestions

The command provides contextual suggestions:

**For not_started items:**
- Start working
- Update priority
- Review dependencies

**For in_progress items:**
- Complete work
- Validate quality
- View status

**For blocked items:**
- View blockers
- Check progress
- Update dependencies
- Visualize graph

**For completed items:**
- View learnings
- Find related items
- Check dependents

## Error Handling

### Work Item Not Found

```bash
/sdd:work-show nonexistent_item
```

**Output:**
```
ERROR: Work item 'nonexistent_item' not found

Available work items:
  feature_auth (in_progress)
  bug_timeout (not_started)
  refactor_api (not_started)
  feature_dashboard (completed)

Use /sdd:work-list to see all work items.
```

### Missing Argument

```bash
/sdd:work-show
```

**Output:**
```
ERROR: Usage: /sdd:work-show <work_item_id>

Example:
  /sdd:work-show feature_auth

Use /sdd:work-list to see all work items.
```

### Specification File Missing

```
SPECIFICATION:
  File: .session/specs/feature_auth.md
  ⚠️  Spec file not found

  This work item may have been created before spec-first architecture.
  Create spec file manually or recreate work item.
```

## Integration with Other Commands

### Before Starting Work

```bash
/sdd:work-show feature_auth  # Review details
/sdd:start feature_auth      # Start working
```

### During Work

```bash
/sdd:work-show bug_timeout   # Check progress
/sdd:status                  # Quick status
/sdd:validate                # Check quality
```

### After Completion

```bash
/sdd:work-show feature_dashboard      # Review completion
/sdd:learn-show --session feature_dashboard  # View learnings
/sdd:work-list --status completed     # See all completed
```

### For Blocked Items

```bash
/sdd:work-show feature_search        # See what's blocking
/sdd:work-show feature_auth          # Check blocker progress
/sdd:work-graph --focus feature_search  # Visualize
```

## Performance

The command is optimized for speed:
- Fast metadata lookup from JSON
- Spec file preview (not full read)
- Cached git information
- Efficient dependency resolution

## See Also

- [Work List Command](work-list.md) - List all work items
- [Work Update Command](work-update.md) - Update work item fields
- [Work Graph Command](work-graph.md) - Visualize dependencies
- [Start Command](start.md) - Begin working on a work item
- [Status Command](status.md) - Quick status overview
