# Work List Command

**Usage:** `/sdd:work-list [--status STATUS] [--type TYPE] [--milestone MILESTONE]`

**Description:** List all work items with optional filtering and color-coded status indicators.

## Overview

The `work-list` command displays all work items with:
- Color-coded priority indicators
- Dependency status markers
- Optional filtering by status, type, or milestone
- Sorted by creation order

## Usage

### List All Work Items

```bash
/sdd:work-list
```

Shows all work items regardless of status.

### Filter by Status

```bash
/sdd:work-list --status not_started
/sdd:work-list --status in_progress
/sdd:work-list --status blocked
/sdd:work-list --status completed
```

**Available status values:**
- `not_started` - Ready to start (dependencies satisfied)
- `in_progress` - Currently being worked on
- `blocked` - Waiting on dependencies
- `completed` - Finished

### Filter by Type

```bash
/sdd:work-list --type feature
/sdd:work-list --type bug
/sdd:work-list --type refactor
```

**Available type values:**
- `feature` - Feature development
- `bug` - Bug fixes
- `refactor` - Code refactoring
- `security` - Security improvements
- `integration_test` - Integration tests
- `deployment` - Deployment tasks

### Filter by Milestone

```bash
/sdd:work-list --milestone sprint_1
/sdd:work-list --milestone phase_2_mvp
```

Shows only work items assigned to the specified milestone.

### Combine Filters

```bash
/sdd:work-list --status not_started --type feature
/sdd:work-list --type bug --milestone sprint_1
```

## Output Format

Work items are displayed with color-coded indicators:

```
WORK ITEMS
==========

🔴 feature_auth: Add user authentication
   Type: feature | Priority: critical | Status: not_started
   Dependencies: ✓ feature_database, ✓ refactor_models
   Milestone: sprint_1

🟠 bug_timeout: Fix database connection timeout
   Type: bug | Priority: high | Status: in_progress
   Dependencies: (none)

🟡 refactor_api: Refactor API error handling
   Type: refactor | Priority: medium | Status: not_started
   Dependencies: 🚫 feature_auth (not_started)
   Milestone: sprint_2

🟢 feature_dashboard: Add admin dashboard
   Type: feature | Priority: low | Status: completed
   Dependencies: ✓ feature_auth
   Completed: 2025-11-08
```

### Priority Indicators

- 🔴 **critical** - Blocking issue or urgent requirement
- 🟠 **high** - Important work to be done soon
- 🟡 **medium** - Normal priority work
- 🟢 **low** - Nice to have, can be deferred

### Dependency Status Markers

- ✓ **Ready** - Dependency completed
- 🚫 **Blocked** - Dependency not completed (shows current status)
- **(none)** - No dependencies

## Examples

### View All Work Items

```bash
/sdd:work-list
```

**Output:**
```
WORK ITEMS (5 total)
====================

🟠 feature_auth: Add user authentication
   Type: feature | Priority: high | Status: not_started
   Dependencies: ✓ feature_database
   Spec: .session/specs/feature_auth.md

🔴 bug_session_timeout: Fix session timeout error
   Type: bug | Priority: critical | Status: in_progress
   Dependencies: (none)
   Spec: .session/specs/bug_session_timeout.md
   Started: 2025-11-09

🟡 refactor_models: Refactor data models
   Type: refactor | Priority: medium | Status: not_started
   Dependencies: 🚫 feature_auth (not_started)
   Spec: .session/specs/refactor_models.md

🟠 feature_search: Implement search feature
   Type: feature | Priority: high | Status: not_started
   Dependencies: ✓ feature_database, 🚫 feature_auth (not_started)
   Milestone: sprint_2
   Spec: .session/specs/feature_search.md

🟢 integration_test_api: Add API integration tests
   Type: integration_test | Priority: low | Status: completed
   Dependencies: ✓ feature_auth, ✓ bug_session_timeout
   Completed: 2025-11-08
   Spec: .session/specs/integration_test_api.md
```

### View Only Incomplete Work

```bash
/sdd:work-list --status not_started
/sdd:work-list --status in_progress
/sdd:work-list --status blocked
```

Or use bash to exclude completed:
```bash
/sdd:work-list | grep -v "completed"
```

### View Specific Types

```bash
/sdd:work-list --type feature
```

**Output:**
```
WORK ITEMS (features only)
===========================

🟠 feature_auth: Add user authentication
   Type: feature | Priority: high | Status: not_started

🟠 feature_search: Implement search feature
   Type: feature | Priority: high | Status: not_started
   Milestone: sprint_2

🟢 feature_dashboard: Add admin dashboard
   Type: feature | Priority: low | Status: completed
   Completed: 2025-11-08
```

### View Milestone Progress

```bash
/sdd:work-list --milestone sprint_1
```

**Output:**
```
WORK ITEMS (milestone: sprint_1)
=================================

🟠 feature_auth: Add user authentication
   Type: feature | Priority: high | Status: not_started
   Dependencies: ✓ feature_database

🔴 bug_session_timeout: Fix session timeout error
   Type: bug | Priority: critical | Status: in_progress
   Dependencies: 🚫 feature_auth (not_started)

Summary: 2 items (1 not_started, 1 in_progress, 0 completed)
```

### Find Blocked Work Items

```bash
/sdd:work-list --status blocked
```

**Output:**
```
WORK ITEMS (blocked)
====================

🟡 refactor_models: Refactor data models
   Type: refactor | Priority: medium | Status: blocked
   Dependencies: 🚫 feature_auth (not_started)
   Blocked by: feature_auth

No other blocked work items found.
```

## Work Item Information

Each work item displays:

1. **Priority indicator** (🔴🟠🟡🟢)
2. **Work item ID and title**
3. **Type, priority, and status**
4. **Dependencies** with completion markers
5. **Milestone** (if assigned)
6. **Spec file path**
7. **Started/Completed date** (if applicable)

## Empty Results

If no work items match the filters:

```bash
/sdd:work-list --status completed
```

**Output:**
```
WORK ITEMS (status: completed)
===============================

No completed work items found.

Create a work item: /sdd:work-new
View all work items: /sdd:work-list
```

## Sorting

Work items are sorted by:
1. **Status** - in_progress first, then not_started, blocked, completed
2. **Priority** - critical > high > medium > low
3. **Creation time** - older items first (within same status/priority)

## Command Options

```bash
/sdd:work-list                      # All work items
/sdd:work-list --status STATUS      # Filter by status
/sdd:work-list --type TYPE          # Filter by type
/sdd:work-list --milestone NAME     # Filter by milestone
/sdd:work-list --status STATUS --type TYPE  # Multiple filters
```

## Understanding Dependencies

Dependencies are shown with their current status:

**✓ feature_database**
- Dependency is completed
- This work item can proceed

**🚫 feature_auth (not_started)**
- Dependency is not completed
- Shows current status of blocker
- This work item is blocked

**🚫 feature_auth (in_progress)**
- Dependency is being worked on
- Work item remains blocked until completed

**(none)**
- No dependencies
- Work item can start immediately

## Integration with Other Commands

Use `work-list` to:

**Find work to start:**
```bash
/sdd:work-list --status not_started
/sdd:start feature_auth
```

**Check milestone progress:**
```bash
/sdd:work-list --milestone sprint_1
```

**View completed work:**
```bash
/sdd:work-list --status completed
```

**Update work item:**
```bash
/sdd:work-list
/sdd:work-update feature_auth priority
```

## See Also

- [Work New Command](work-new.md) - Create new work items
- [Work Show Command](work-show.md) - View detailed work item information
- [Work Update Command](work-update.md) - Update work item fields
- [Work Next Command](work-next.md) - Get recommended work item to start
- [Start Command](start.md) - Begin working on a work item
