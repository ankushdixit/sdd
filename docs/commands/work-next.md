# Work Next Command

**Usage:** `/sdd:work-next`

**Description:** Get intelligent recommendations for the next work item to start based on dependencies and priority.

## Overview

The `work-next` command analyzes your work items and recommends the most important work that can be started immediately. It considers:
- Dependency satisfaction (only shows unblocked items)
- Priority levels (critical > high > medium > low)
- Work item types and context
- Current project state

## Usage

```bash
/sdd:work-next
```

No arguments needed - the command automatically analyzes all work items.

## Recommendation Algorithm

The command follows this logic:

### 1. Filter Available Work Items
- Status must be `not_started`
- All dependencies must be `completed`
- Excludes `in_progress`, `blocked`, and `completed` items

### 2. Sort by Priority
- **critical** - Blocking issues (highest priority)
- **high** - Important work
- **medium** - Normal priority
- **low** - Nice to have (lowest priority)

### 3. Recommend Top Item
- Returns the highest priority unblocked work item
- Provides rationale for the recommendation
- Shows context of other waiting items

## Output Format

```
RECOMMENDATION
==============

Next Work Item: feature_auth
Title: Add user authentication
Type: feature | Priority: high

RATIONALE:
- Highest priority unblocked work item
- All dependencies satisfied:
  ✓ feature_database (completed)
  ✓ refactor_models (completed)

CONTEXT:
Ready to Start (3 items):
  🟠 feature_auth: Add user authentication
  🟡 refactor_api: Refactor API error handling
  🟢 feature_dashboard: Add admin dashboard

Blocked (2 items):
  🟠 feature_search: Waiting on feature_auth
  🟡 integration_test_api: Waiting on feature_auth, bug_timeout

In Progress (1 item):
  🔴 bug_timeout: Fix database timeout

QUICK START:
  /sdd:start feature_auth
```

## Examples

### Standard Recommendation

```bash
/sdd:work-next
```

**Output:**
```
RECOMMENDATION
==============

Next Work Item: bug_session_timeout
Title: Fix session timeout error
Type: bug | Priority: critical

RATIONALE:
- Critical priority (blocks other work)
- All dependencies satisfied (no dependencies)
- Urgent bug fix needed

CONTEXT:
Ready to Start (4 items):
  🔴 bug_session_timeout: Fix session timeout (RECOMMENDED)
  🟠 feature_auth: Add user authentication
  🟡 refactor_api: Refactor API error handling
  🟢 feature_dashboard: Add admin dashboard

Blocked (0 items)

QUICK START:
  /sdd:start bug_session_timeout
```

### Multiple High-Priority Items

```bash
/sdd:work-next
```

**Output:**
```
RECOMMENDATION
==============

Next Work Item: feature_auth
Title: Add user authentication
Type: feature | Priority: high

RATIONALE:
- Tied for highest priority (high) with 2 other items
- Selected: feature_auth (created first)
- Blocks 3 other work items (high impact)

CONTEXT:
Ready to Start (3 items):
  🟠 feature_auth: Add user authentication (RECOMMENDED)
  🟠 feature_payment: Implement payment system
  🟠 feature_notifications: Add email notifications

Blocked (3 items):
  🟠 feature_search: Waiting on feature_auth
  🟡 feature_dashboard: Waiting on feature_auth
  🟡 integration_test_api: Waiting on feature_auth

NOTE: feature_auth blocks 3 other items. Completing it will
      unblock significant downstream work.

QUICK START:
  /sdd:start feature_auth
```

### No Ready Items

```bash
/sdd:work-next
```

**Output:**
```
NO RECOMMENDATION
=================

No work items are ready to start.

Blocked (3 items):
  🟠 feature_search: Waiting on feature_auth (in_progress)
  🟡 refactor_api: Waiting on feature_auth (in_progress)
  🟢 feature_dashboard: Waiting on feature_auth, feature_search (both incomplete)

In Progress (1 item):
  🟠 feature_auth: Add user authentication

NEXT STEPS:
1. Complete feature_auth to unblock 3 dependent items
2. Use /sdd:end to complete current work
3. Create new work items: /sdd:work-new
```

### All Work Completed

```bash
/sdd:work-next
```

**Output:**
```
NO RECOMMENDATION
=================

All work items are completed! 🎉

Summary:
  ✓ 15 work items completed
  ✓ 0 work items remaining

NEXT STEPS:
- Create new work items: /sdd:work-new
- Review completed work: /sdd:work-list --status completed
- Plan next milestone: /sdd:work-list --milestone next_phase
```

## Understanding the Context Section

### Ready to Start
Work items with:
- Status: `not_started`
- All dependencies: `completed`
- Can be started immediately

**Sorted by priority** (critical → high → medium → low)

### Blocked
Work items waiting on dependencies:
- Status: `blocked` or `not_started` with incomplete dependencies
- Shows which dependencies are blocking
- Cannot start until dependencies complete

### In Progress
Currently active work items:
- Status: `in_progress`
- Being worked on in current or recent session
- Should be completed before starting new work

## Priority Indicators

- 🔴 **critical** - Blocking issue, urgent requirement
- 🟠 **high** - Important work to be done soon
- 🟡 **medium** - Normal priority work
- 🟢 **low** - Nice to have, can be deferred

## Impact Analysis

The command identifies high-impact work items:

**Blocks multiple items:**
```
NOTE: feature_auth blocks 5 other items. Completing it will
      unblock significant downstream work.
```

**Critical path item:**
```
NOTE: feature_database is on the critical path. It determines
      the earliest project completion date.
```

**Milestone critical:**
```
NOTE: This item is required for milestone "Phase 1 MVP" (due soon).
```

## Integration with Other Commands

### After Getting Recommendation

```bash
/sdd:work-next
# See recommendation: feature_auth

/sdd:start feature_auth
# Start working on recommended item
```

### Compare with Manual Selection

```bash
/sdd:work-next
# Algorithm recommendation

/sdd:work-list --status not_started
# See all available items

/sdd:start <chosen_item>
# Start your choice
```

### Check After Completing Work

```bash
/sdd:end
# Complete current work item

/sdd:work-next
# Get next recommendation automatically
```

## Recommendation Strategies

### Strategy 1: Priority-First (Default)
Always picks highest priority unblocked item
- Best for: Projects with clear priorities
- Pro: Ensures important work gets done first
- Con: May ignore high-impact low-priority items

### Strategy 2: Impact-Aware
Consider both priority and downstream impact
- The command shows impact in rationale
- You can manually choose high-impact items
- Look for "blocks N items" notes

### Strategy 3: Milestone-Driven
Focus on items in current milestone
- Use `/sdd:work-list --milestone current_sprint`
- Filter by milestone first
- Then apply priority sorting

## When to Override Recommendation

Consider starting a different item when:

1. **Context Switching Cost**
   - Recommended item requires different skillset
   - Current mental context suits different item better

2. **External Dependencies**
   - Waiting on stakeholder feedback
   - Third-party API access needed

3. **Team Coordination**
   - Another team member working on related code
   - Avoiding merge conflicts

4. **Time Constraints**
   - Quick wins needed before deadline
   - Low-priority but fast items available

## Error Handling

### No Work Items Exist

```bash
/sdd:work-next
```

**Output:**
```
NO RECOMMENDATION
=================

No work items found.

Create your first work item:
  /sdd:work-new
```

### All Items In Progress

```bash
/sdd:work-next
```

**Output:**
```
NO RECOMMENDATION
=================

All work items are either completed or in progress.

In Progress (2 items):
  🟠 feature_auth
  🔴 bug_timeout

Complete current work before starting new items:
  /sdd:end
```

## Best Practices

### 1. Check Regularly
```bash
# After completing work
/sdd:end
/sdd:work-next

# Before starting new work
/sdd:work-next
/sdd:start
```

### 2. Review Context
- Don't just start recommended item blindly
- Review blocked items and their dependencies
- Consider downstream impact

### 3. Update Priorities
```bash
# If recommendation doesn't match needs
/sdd:work-update <item_id> priority
# Then check again
/sdd:work-next
```

### 4. Break Down Large Items
If recommended item is too large:
```bash
# Create smaller sub-items
/sdd:work-new  # Create smaller task
/sdd:work-update <new_item> add-dependency
# Add large item as dependency
```

## See Also

- [Start Command](start.md) - Begin working on recommended item
- [Work List Command](work-list.md) - View all work items
- [Work Update Command](work-update.md) - Change priorities
- [Work Graph Command](work-graph.md) - Visualize dependencies
- [End Command](end.md) - Complete current work
