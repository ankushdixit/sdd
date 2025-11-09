# Status Command

**Usage:** `/sdd:status`

**Description:** Display current session status with progress overview, time tracking, and next steps.

## Overview

The `status` command provides a quick snapshot of:
- Current work item being worked on
- Session duration and time tracking
- Files changed in current session
- Git branch and commit information
- Milestone progress (if applicable)
- Next work items ready to start
- Quick action suggestions

## Usage

```bash
/sdd:status
```

No arguments needed - shows status for current session.

## Output Sections

### 1. Current Work Item
- Work item ID and title
- Type, priority, status
- Session number (if multi-session item)

### 2. Time Tracking
- Session start time
- Elapsed time in current session
- Total time across all sessions (for multi-session items)

### 3. Files Changed
- Modified files (M)
- Added files (A)
- Deleted files (D)
- File count

### 4. Git Information
- Current branch name
- Number of commits made
- Commit summaries

### 5. Milestone Progress
- Milestone name
- Completion percentage
- Related items status breakdown

### 6. Next Work Items
- Top 3 work items ready to start
- Priority indicators
- Blocked items count

### 7. Quick Actions
- Suggested next commands based on session state

## Examples

### Active Session

```bash
/sdd:status
```

**Output:**
```
================================================================================
SESSION STATUS
================================================================================

CURRENT WORK ITEM: feature_auth
  Title: Add user authentication
  Type: feature | Priority: high | Status: in_progress
  Session: 1

TIME TRACKING:
  Session started: 2025-11-09 14:30
  Elapsed: 1h 23m
  Total time: 1h 23m (first session)

FILES CHANGED (5):
  M  src/auth/jwt.ts
  M  src/api/routes/auth.ts
  A  src/middleware/auth.ts
  A  tests/auth/jwt.test.ts
  M  package.json

GIT INFORMATION:
  Branch: feat/user-authentication
  Commits: 3
    1. feat: Add JWT token generation
    2. feat: Implement login endpoint
    3. test: Add authentication tests

NEXT WORK ITEMS:
  Ready to Start (3):
    🟠 bug_session_timeout: Fix session timeout error
    🟡 refactor_api: Refactor API error handling
    🟢 feature_dashboard: Add admin dashboard

  Blocked (2):
    🟠 feature_search: Waiting on feature_auth
    🟡 integration_test_api: Waiting on feature_auth

QUICK ACTIONS:
  Validate session:   /sdd:validate
  Complete session:   /sdd:end
  View work item:     /sdd:work-show feature_auth
  List all items:     /sdd:work-list
```

### Multi-Session Work Item

```bash
/sdd:status
```

**Output:**
```
================================================================================
SESSION STATUS
================================================================================

CURRENT WORK ITEM: feature_dashboard
  Title: Add admin dashboard
  Type: feature | Priority: high | Status: in_progress
  Session: 2 (resuming)

TIME TRACKING:
  Session started: 2025-11-09 10:00
  Elapsed: 2h 15m
  Total time: 4h 30m (across 2 sessions)

PREVIOUS SESSIONS:
  Session 1: 2h 15m (2025-11-08)
    - 4 commits, 15 files changed
    - Quality: ✓ Tests passed | ✓ Linting

FILES CHANGED (8):
  M  src/dashboard/components/Stats.tsx
  M  src/dashboard/components/Chart.tsx
  A  src/dashboard/widgets/Timeline.tsx
  A  tests/dashboard/widgets.test.tsx
  M  src/api/routes/dashboard.ts
  M  package.json
  M  README.md
  M  docs/dashboard.md

GIT INFORMATION:
  Branch: feat/admin-dashboard
  Commits this session: 3
  Total commits: 7
    1. feat: Add export functionality
    2. test: Complete dashboard test coverage
    3. docs: Update dashboard documentation

MILESTONE PROGRESS: sprint_1
  Completed: 3/6 items (50%)
  In Progress: 1 (feature_dashboard)
  Not Started: 2

NEXT WORK ITEMS:
  Ready to Start (2):
    🟠 feature_notifications: Add email notifications
    🟡 refactor_models: Refactor data models

  Blocked (0)

QUICK ACTIONS:
  Validate session:   /sdd:validate
  Complete session:   /sdd:end
  View milestone:     /sdd:work-list --milestone sprint_1
  View work item:     /sdd:work-show feature_dashboard
```

### No Active Session

```bash
/sdd:status
```

**Output:**
```
================================================================================
SESSION STATUS
================================================================================

NO ACTIVE SESSION

Last completed session:
  Work Item: feature_auth
  Completed: 2025-11-09 16:45
  Duration: 2h 15m
  Commits: 5
  Quality: ✓ All gates passed

PROJECT STATUS:
  Total work items: 8
  Completed: 3 (37%)
  In Progress: 0
  Ready to Start: 3
  Blocked: 2

NEXT WORK ITEMS:
  Ready to Start (3):
    🔴 bug_session_timeout: Fix session timeout error
    🟠 refactor_api: Refactor API error handling
    🟢 feature_dashboard: Add admin dashboard

QUICK ACTIONS:
  Get recommendation: /sdd:work-next
  Start work:         /sdd:start
  Create work item:   /sdd:work-new
  View all items:     /sdd:work-list
```

## Time Tracking Details

### Session Duration
- Real-time elapsed time
- Format: hours and minutes (e.g., "1h 23m")
- Updates continuously during session

### Multi-Session Tracking
For work items spanning multiple sessions:
- Shows current session number
- Total time across all sessions
- Previous session summaries

**Example:**
```
Session: 2 (resuming)
Elapsed: 1h 15m
Total time: 3h 30m (across 2 sessions)
```

## File Change Tracking

Shows git-tracked changes:
- **M** - Modified files
- **A** - Added (new) files
- **D** - Deleted files
- **R** - Renamed files

**File statistics:**
```
FILES CHANGED (12):
  M  src/auth/jwt.ts
  M  src/api/routes/auth.ts
  A  src/middleware/auth.ts
  [... 9 more files ...]
```

Large file lists are truncated with count.

## Milestone Progress

When work item is in a milestone:

```
MILESTONE PROGRESS: sprint_1
  Completed: 4/8 items (50%)
  In Progress: 1 (feature_dashboard)
  Not Started: 3
  Blocked: 0

  Progress bar: [████████░░░░░░░░] 50%
```

Shows:
- Completion percentage
- Status breakdown
- Visual progress bar

## Next Work Items Preview

Shows top 3 items ready to start:
- Sorted by priority (critical → low)
- Color-coded priority indicators
- Shows blocked count

**Helps answer:**
- What should I work on next?
- What's blocked and why?
- What's the project pipeline?

## Quick Actions

Context-aware suggestions:

**During active session:**
- Validate session
- Complete session
- View current work item

**No active session:**
- Get next recommendation
- Start new work
- Create work item

## Use Cases

### Check Progress During Work

```bash
# While working
/sdd:status
# See time elapsed, files changed, commits made
```

### Before Taking a Break

```bash
/sdd:status
# Review current state
# Decide if good stopping point
```

### After Resuming

```bash
/sdd:status
# See where you left off
# Review previous session work
# Continue from context
```

### Planning Next Work

```bash
/sdd:status
# See what's ready to start
# Check milestone progress
# Decide next priority
```

## Integration with Other Commands

### During Development

```bash
/sdd:status          # Quick overview
/sdd:validate        # Check quality gates
/sdd:end             # Complete when done
```

### Between Sessions

```bash
/sdd:status          # See project state
/sdd:work-next       # Get recommendation
/sdd:start           # Begin new work
```

### Milestone Tracking

```bash
/sdd:status                        # See milestone progress
/sdd:work-list --milestone sprint_1  # Detailed view
/sdd:work-graph --milestone sprint_1 # Visualize
```

## Performance

The command is fast:
- No file system scanning
- Cached git information
- Optimized JSON parsing
- Instant response

## See Also

- [Start Command](start.md) - Begin working on a work item
- [End Command](end.md) - Complete current session
- [Validate Command](validate.md) - Check quality gates
- [Work Next Command](work-next.md) - Get recommendations
- [Work Show Command](work-show.md) - View work item details
