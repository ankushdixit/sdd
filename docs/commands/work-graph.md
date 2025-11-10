# Work Graph Command

**Usage:** `/sk:work-graph [OPTIONS]`

**Description:** Generate dependency graph visualization for work items with critical path analysis and bottleneck detection.

## Overview

The `work-graph` command creates visual representations of work item dependencies, helping you understand project structure, identify critical paths, detect bottlenecks, and make informed decisions about what to work on next.

**Key features:**
- Multiple output formats (ASCII, DOT, SVG)
- Critical path identification
- Bottleneck detection
- Flexible filtering by status, milestone, or type
- Focus mode for specific items
- Graph statistics and metrics
- Export capabilities for documentation

## Arguments

All arguments are optional and can be combined.

### Format Options

#### `--format <format>`

Output format for the graph:
- `ascii` (default) - Terminal-friendly box drawing with color coding
- `dot` - Graphviz DOT format (plaintext graph description)
- `svg` - SVG image (requires Graphviz installed)

#### `--output <file>`

Save graph to file instead of displaying in terminal. Only works with `--format dot` or `--format svg`.

**Example:** `--output project-dependencies.svg`

### Filter Options

#### `--status <status>`

Show only items with specific status:
- `not_started` - Items not yet begun
- `in_progress` - Items currently being worked on
- `completed` - Finished items
- `blocked` - Items waiting on dependencies

#### `--milestone <milestone>`

Show only items in a specific milestone.

**Example:** `--milestone "Phase 3"`

#### `--type <type>`

Show only specific work item types:
- `feature`, `bug`, `refactor`, `security`, `integration_test`, `deployment`

#### `--include-completed`

Include completed items in the graph (default: excluded for clarity).

**Use case:** Show full project history or milestone progress.

#### `--focus <work_item_id>`

Show only the specified item and its dependency neighborhood:
- Direct dependencies (items this depends on)
- Direct dependents (items that depend on this)

**Example:** `--focus feature_oauth`

### Analysis Options

#### `--critical-path`

Show only items on the critical path - the longest dependency chain that determines minimum project timeline.

**Use case:** Identify items that directly impact project completion date.

#### `--bottlenecks`

Highlight bottleneck analysis - items that block 2+ other items, sorted by impact.

**Use case:** Find high-impact items to prioritize for maximum unblocking.

#### `--stats`

Show graph statistics without rendering full graph:
- Total items by status
- Completion percentage
- Critical path length
- Bottleneck count
- Timeline projection

**Use case:** Quick health check of project status.

## Output Formats

### ASCII Format (Terminal)

Default format using box-drawing characters with color coding:

```
Work Item Dependency Graph
==========================

┌─────────────────────────────┐
│ feature_auth                │ [●] In Progress (CRITICAL PATH)
│ User Authentication         │
│ Priority: high              │
└─────────────────────────────┘
              ↓
┌─────────────────────────────┐
│ feature_oauth               │ [○] Not Started (CRITICAL PATH)
│ OAuth Integration           │
│ Priority: high              │
└─────────────────────────────┘
              ↓
┌─────────────────────────────┐
│ feature_profile             │ [○] Not Started
│ User Profile Page           │
│ Priority: medium            │
└─────────────────────────────┘

Legend:
  [✓] Completed  [●] In Progress  [○] Not Started  [✗] Blocked
  Red = Critical Path  Orange = Bottleneck

Critical Path Length: 3 items
Timeline Estimate: 3 sessions minimum
Bottlenecks: feature_auth (blocks 2 items)
```

### DOT Format (Graphviz)

Plaintext graph description for use with Graphviz tools:

```dot
digraph work_items {
  rankdir=LR;
  node [shape=box, style=rounded];

  "feature_auth" [label="feature_auth\nUser Authentication\nPriority: high",
                  color=red, style=filled, fillcolor=lightblue];
  "feature_oauth" [label="feature_oauth\nOAuth Integration\nPriority: high",
                   color=red];
  "feature_profile" [label="feature_profile\nUser Profile\nPriority: medium"];

  "feature_auth" -> "feature_oauth" [color=red, penwidth=2];
  "feature_oauth" -> "feature_profile";
}
```

### SVG Format (Visual)

Rendered graph image suitable for:
- Documentation
- Architecture reviews
- Presentations
- Team dashboards
- Embedding in reports

## Examples

### Example 1: Basic Graph (All Incomplete Items)

```bash
/sk:work-graph
```

**Output:**
```
Work Item Dependency Graph
==========================

Total: 12 work items (5 completed, 2 in progress, 5 not started)

┌─────────────────────────────┐
│ feature_auth                │ [●] In Progress (CRITICAL PATH)
│ User Authentication         │
│ Priority: high              │
└─────────────────────────────┘
              ↓
┌─────────────────────────────┐
│ feature_oauth               │ [○] Not Started (CRITICAL PATH)
│ OAuth Integration           │
│ Priority: high              │
└─────────────────────────────┘
              ↓
┌─────────────────────────────┐
│ feature_profile             │ [○] Not Started
│ User Profile Page           │
│ Priority: medium            │
└─────────────────────────────┘
              ↓
┌─────────────────────────────┐
│ feature_dashboard           │ [○] Not Started
│ Admin Dashboard             │
│ Priority: high              │
└─────────────────────────────┘

... [3 more items] ...

Critical Path: 5 items (feature_auth → feature_oauth → feature_dashboard → integration_auth → deployment_prod)
Timeline Estimate: 5 sessions minimum
Next Recommended: feature_auth (in progress, high priority, critical path)
Bottlenecks: feature_auth (blocks 4 items)
```

### Example 2: Critical Path Analysis

```bash
/sk:work-graph --critical-path
```

**Output:**
```
Critical Path Analysis
=====================

The critical path determines your minimum project timeline.
Focus on these items to minimize overall project duration.

Critical Path (5 items):

  1. [●] feature_auth: User Authentication
     Status: In Progress (Session 12)
     Impact: Blocks 4 downstream items
          ↓
  2. [○] feature_oauth: OAuth Integration
     Status: Not Started (depends on feature_auth)
     Impact: Blocks 3 downstream items
          ↓
  3. [○] feature_dashboard: Admin Dashboard
     Status: Not Started (depends on feature_oauth)
     Impact: Blocks 2 downstream items
          ↓
  4. [○] integration_auth: End-to-end Auth Tests
     Status: Not Started (depends on feature_dashboard)
     Impact: Blocks deployment
          ↓
  5. [○] deployment_prod: Production Deploy
     Status: Not Started (depends on integration_auth)
     Impact: Final milestone

Timeline Analysis:
  - Completed: 0/5 (0%)
  - In Progress: 1/5 (20%)
  - Remaining: 4/5 (80%)
  - Estimated Duration: 4+ sessions

💡 To minimize project duration:
   1. Complete feature_auth (currently in progress)
   2. Immediately start feature_oauth
   3. Continue sequentially through critical path
```

### Example 3: Bottleneck Detection

```bash
/sk:work-graph --bottlenecks
```

**Output:**
```
Bottleneck Analysis
===================

Items that block multiple other items. Prioritize these for maximum impact!

1. feature_auth: User Authentication (blocks 4 items) ⚠️ HIGH IMPACT
   Status: In Progress (Session 12)
   Priority: high
   Blocking:
     - feature_oauth: OAuth Integration
     - feature_profile: User Profile Page
     - feature_password_reset: Password Reset Flow
     - security_audit: Security Audit

   Impact: Completing this will unblock 33% of remaining work

2. feature_oauth: OAuth Integration (blocks 3 items)
   Status: Not Started (blocked by feature_auth)
   Priority: high
   Blocking:
     - feature_dashboard: Admin Dashboard
     - feature_rate_limit: API Rate Limiting
     - integration_auth: End-to-end Tests

   Impact: Next bottleneck after feature_auth completes

3. bug_db_pool: Database Connection Pool Issue (blocks 2 items)
   Status: Not Started
   Priority: critical
   Blocking:
     - feature_batch: Batch Processing
     - feature_jobs: Background Jobs

   Impact: Independent bottleneck, can work on in parallel

💡 Recommendation:
   Focus on completing feature_auth to unblock the most work.
   Bug_db_pool can be tackled in parallel by another team member.
```

### Example 4: Milestone View

```bash
/sk:work-graph --milestone "Phase 3" --include-completed
```

**Output:**
```
Phase 3 Dependency Graph
========================

Milestone: Phase 3 (8 items total, 2 completed, 1 in progress, 5 not started)

┌─────────────────────────────┐
│ feature_search              │ [✓] Completed (2025-11-05)
│ Search Functionality        │
└─────────────────────────────┘
              ↓
┌─────────────────────────────┐
│ feature_filters             │ [✓] Completed (2025-11-06)
│ Search Filters              │
└─────────────────────────────┘
              ↓
┌─────────────────────────────┐
│ feature_analytics           │ [●] In Progress (CRITICAL PATH)
│ Search Analytics            │
│ Session: 15                 │
└─────────────────────────────┘
              ↓
┌─────────────────────────────┐
│ integration_search          │ [○] Not Started (CRITICAL PATH)
│ Search Integration Tests    │
└─────────────────────────────┘
              ↓
┌─────────────────────────────┐
│ feature_export              │ [○] Not Started
│ Export Results              │
└─────────────────────────────┘

Phase 3 Progress:
  - Completed: 2/8 (25%)
  - In Progress: 1/8 (13%)
  - Not Started: 5/8 (62%)
  - Estimated Completion: 5+ sessions remaining

Next Items:
  1. feature_analytics (in progress, finish this first)
  2. integration_search (next on critical path)
  3. feature_export (can work in parallel)
```

### Example 5: Focus on Specific Item

```bash
/sk:work-graph --focus feature_oauth
```

**Output:**
```
Focused View: feature_oauth
===========================

Showing feature_oauth and its dependency neighborhood.

Dependencies (items feature_oauth depends on):

┌─────────────────────────────┐
│ feature_auth                │ [●] In Progress (Session 12)
│ User Authentication         │
│ Status: 70% complete        │
└─────────────────────────────┘
              ↓
┌─────────────────────────────┐
│ feature_oauth               │ [○] Not Started ← TARGET
│ OAuth Integration           │
│ Priority: high              │
└─────────────────────────────┘
              ↓
Dependents (items that depend on feature_oauth):

┌─────────────────────────────┐
│ feature_dashboard           │ [○] Not Started
│ Admin Dashboard             │
└─────────────────────────────┘

┌─────────────────────────────┐
│ feature_rate_limit          │ [○] Not Started
│ API Rate Limiting           │
└─────────────────────────────┘

┌─────────────────────────────┐
│ integration_auth            │ [○] Not Started
│ End-to-end Auth Tests       │
└─────────────────────────────┘

Analysis:
  - Blocked by: 1 item (feature_auth, in progress)
  - Blocks: 3 items (shown above)
  - On critical path: Yes
  - Estimated availability: After feature_auth completes (~1 session)

💡 feature_oauth cannot start until feature_auth is completed.
   Completing feature_oauth will unblock 3 downstream items.
```

### Example 6: Statistics Only

```bash
/sk:work-graph --stats
```

**Output:**
```
Work Item Graph Statistics
==========================

Total Work Items: 24

By Status:
  - Completed:     8 (33%) ████████░░░░░░░░
  - In Progress:   3 (13%) ███░░░░░░░░░░░░░
  - Not Started:  12 (50%) ████████████░░░░
  - Blocked:       1 (4%)  █░░░░░░░░░░░░░░░

By Type:
  - feature:           15 items (63%)
  - bug:                4 items (17%)
  - refactor:           2 items (8%)
  - security:           1 item  (4%)
  - integration_test:   1 item  (4%)
  - deployment:         1 item  (4%)

By Priority:
  - Critical:  2 items (8%)  - Requires immediate attention
  - High:      8 items (33%) - Important work
  - Medium:   10 items (42%) - Normal priority
  - Low:       4 items (17%) - Nice to have

By Milestone:
  - Phase 1:   6 items (100% complete) ✓
  - Phase 2:   8 items (75% complete)  ████████████░░░░
  - Phase 3:  10 items (20% complete)  ████░░░░░░░░░░░░

Critical Path:
  - Length: 7 items
  - Completed: 2 items (29%)
  - In Progress: 1 item (14%)
  - Remaining: 4 items (57%)
  - Estimated Duration: 4+ sessions

Bottlenecks:
  - 3 items blocking 2+ other items
  - Top bottleneck: feature_auth (blocks 4 items)
  - Second: feature_oauth (blocks 3 items)
  - Third: bug_db_pool (blocks 2 items)

Dependency Health:
  - Total dependencies: 18
  - Satisfied: 10 (56%)
  - Pending: 8 (44%)
  - Circular dependencies: 0 ✓

Next Recommended Items (ready to start):
  1. feature_auth (in progress, high priority, critical path)
  2. bug_db_pool (not started, critical priority, blocks 2)
  3. refactor_api (not started, medium priority, no blockers)

Project Health: ⚠️ Moderate
  - 50% work remaining
  - Critical path progressing (29% complete)
  - Some bottlenecks need attention
  - No circular dependencies detected
```

### Example 7: Export to SVG

```bash
/sk:work-graph --format svg --output project-dependencies.svg
```

**Output:**
```
Generating dependency graph...

✓ Dependency graph generated successfully!

Format: SVG
Output: project-dependencies.svg
Size: 24 work items, 18 dependencies
File size: 45.2 KB

The graph includes:
  - All work items color-coded by status
  - Critical path highlighted in red
  - Priority indicators on nodes
  - Milestone grouping
  - Bottlenecks marked with ⚠️

You can:
  - Open in browser: open project-dependencies.svg
  - Include in documentation
  - Share with team via Slack/email
  - Embed in presentations
  - Add to README or wiki

To view the graph now, run:
  open project-dependencies.svg
```

### Example 8: Combined Filters

```bash
/sk:work-graph --status not_started --milestone "Phase 3" --type feature
```

**Output:**
```
Filtered Work Items
===================

Active Filters:
  - Status: not_started
  - Milestone: Phase 3
  - Type: feature

Found 5 matching items:

┌─────────────────────────────┐
│ feature_analytics           │ [○] Not Started (CRITICAL PATH)
│ Search Analytics Dashboard  │
│ Priority: high              │
│ Depends on: feature_filters │
└─────────────────────────────┘
              ↓
┌─────────────────────────────┐
│ feature_export              │ [○] Not Started
│ Export Search Results       │
│ Priority: medium            │
│ Depends on: feature_analytics│
└─────────────────────────────┘

┌─────────────────────────────┐
│ feature_sharing             │ [○] Not Started
│ Share Search Results        │
│ Priority: low               │
│ No dependencies             │
└─────────────────────────────┘

... [2 more items] ...

Analysis:
  - 2 of these are on the critical path
  - 3 have no blockers and can start immediately
  - 2 are waiting on other Phase 3 items

Next Recommended: feature_analytics
  - Critical path item
  - High priority
  - Blocked by feature_filters (70% complete)
  - Will unblock 2 downstream items
```

### Example 9: Type-Specific Graph

```bash
/sk:work-graph --type bug --include-completed
```

**Output:**
```
Bug Tracking Graph
==================

Showing all bug work items (completed and incomplete)

┌─────────────────────────────┐
│ bug_login_timeout           │ [✓] Completed (2025-11-03)
│ Fix login timeout issue     │
└─────────────────────────────┘

┌─────────────────────────────┐
│ bug_db_pool                 │ [○] Not Started (BOTTLENECK)
│ Database pool exhaustion    │
│ Priority: critical          │
└─────────────────────────────┘
              ↓
┌─────────────────────────────┐
│ bug_memory_leak             │ [○] Not Started
│ Memory leak in batch jobs   │
│ Priority: high              │
│ Depends on: bug_db_pool     │
└─────────────────────────────┘

┌─────────────────────────────┐
│ bug_cors_preflight          │ [●] In Progress (Session 14)
│ CORS preflight failing      │
│ Priority: high              │
└─────────────────────────────┘

Bug Summary:
  - Total bugs: 4
  - Fixed: 1 (25%)
  - In Progress: 1 (25%)
  - Open: 2 (50%)
  - Critical: 1 (bug_db_pool)

💡 bug_db_pool is blocking other work. Consider prioritizing.
```

## Understanding the Visualization

### Node Colors and Symbols

**Status Indicators:**
- `[✓]` - Completed (green)
- `[●]` - In Progress (blue)
- `[○]` - Not Started (black/white)
- `[✗]` - Blocked (gray)
- `[⚠]` - Bottleneck (orange)

**Color Coding:**
- **Red nodes/text**: Critical path items (determine project timeline)
- **Green**: Completed items
- **Blue**: In progress items
- **Orange**: Bottleneck items (blocking 2+ others)
- **Gray**: Blocked items

### Edge (Arrow) Styles

- **Solid arrows** → : Standard dependencies
- **Bold red arrows** ⇒ : Critical path connections
- **Dashed arrows** ⇢ : Optional/soft dependencies

### Priority Indicators

- 🔴 Critical
- 🟠 High
- 🟡 Medium
- 🟢 Low

## Use Cases

### 1. Project Planning

```bash
/sk:work-graph --stats
```

Get high-level overview of project structure, completion status, and timeline.

### 2. Sprint Planning

```bash
/sk:work-graph --milestone "Sprint 5" --status not_started
```

See what's available to work on in upcoming sprint.

### 3. Timeline Estimation

```bash
/sk:work-graph --critical-path
```

Identify minimum project duration and items that directly impact deadline.

### 4. Unblocking Work

```bash
/sk:work-graph --bottlenecks
```

Find high-impact items to prioritize for maximum team unblocking.

### 5. Documentation

```bash
/sk:work-graph --format svg --output docs/architecture/dependencies.svg
```

Generate visual documentation for:
- Architecture reviews
- Stakeholder presentations
- Team onboarding
- Technical documentation

### 6. Status Reports

```bash
/sk:work-graph --milestone "Q4 Goals" --include-completed
```

Show progress on milestone objectives for:
- Standups
- Manager check-ins
- Stakeholder updates

### 7. Dependency Analysis

```bash
/sk:work-graph --focus feature_complex_item
```

Understand dependencies before starting complex work item.

### 8. Bug Triage

```bash
/sk:work-graph --type bug --stats
```

See bug distribution and dependencies for prioritization.

## Best Practices

### 1. Regular Critical Path Reviews

```bash
# Weekly review
/sk:work-graph --critical-path
```

Stay aware of items that impact project timeline.

### 2. Bottleneck Monitoring

```bash
# Before sprint planning
/sk:work-graph --bottlenecks
```

Identify and address bottlenecks proactively.

### 3. Milestone Visualization

```bash
# Start of milestone
/sk:work-graph --milestone "current" --format svg --output milestone-start.svg

# End of milestone
/sk:work-graph --milestone "current" --include-completed --format svg --output milestone-complete.svg
```

Document milestone progress visually.

### 4. Focus Before Starting Work

```bash
# Before starting complex item
/sk:work-graph --focus <work_item_id>
```

Understand full context of dependencies and impact.

### 5. Export for Communication

```bash
# For stakeholder review
/sk:work-graph --format svg --output stakeholder-review.svg
```

Visual graphs communicate better than text lists.

## Error Handling

### Work Item Not Found (Focus Mode)

```bash
/sk:work-graph --focus nonexistent_item
```

**Output:**
```
ERROR: Work item 'nonexistent_item' not found

Available work items:
  feature_auth, feature_oauth, feature_profile, bug_db_pool, ...

Use /sk:work-list to see all work items.
```

### No Items Match Filters

```bash
/sk:work-graph --status completed --milestone "Future Phase"
```

**Output:**
```
No work items match the specified filters.

Active Filters:
  - Status: completed
  - Milestone: Future Phase

Suggestions:
  - Remove --status filter to see all items in milestone
  - Check milestone name: /sk:work-list --milestone "Future Phase"
  - View all milestones: /sk:work-list
```

### Graphviz Not Installed (SVG Format)

```bash
/sk:work-graph --format svg --output graph.svg
```

**Output:**
```
ERROR: SVG format requires Graphviz

Graphviz not found on your system.

To install:
  macOS:   brew install graphviz
  Ubuntu:  sudo apt-get install graphviz
  Windows: choco install graphviz

Falling back to DOT format...

✓ Generated graph.dot instead
  You can convert to SVG after installing Graphviz:
    dot -Tsvg graph.dot -o graph.svg
```

### Circular Dependencies Detected

```bash
/sk:work-graph
```

**Output:**
```
⚠️  WARNING: Circular dependencies detected!

Circular dependency chain:
  feature_a → feature_b → feature_c → feature_a

This creates a deadlock - none of these items can start.

To fix:
  1. /sk:work-show feature_a
  2. /sk:work-update feature_a remove-dependency
  3. Remove the circular dependency

Graph generated with circular dependencies marked.
```

## Integration with Other Commands

### Before Starting Work

```bash
/sk:work-graph --bottlenecks     # Find high-impact item
/sk:work-next                     # Get recommendation
/sk:start <recommended_item>      # Begin work
```

### During Sprint Planning

```bash
/sk:work-graph --milestone "Sprint 5" --stats
/sk:work-list --milestone "Sprint 5" --status not_started
/sk:work-next  # Get first item to start
```

### After Completing Work

```bash
/sk:end                          # Complete current work
/sk:work-graph --bottlenecks     # See if you unblocked work
/sk:work-next                    # Get next item
```

### For Documentation

```bash
/sk:work-graph --format svg --output docs/dependencies.svg
# Commit and push for team visibility
```

## Performance

The command is optimized for:
- Fast graph construction (O(V + E) where V=items, E=dependencies)
- Efficient critical path computation (DFS-based)
- Quick filtering without full graph traversal
- Minimal memory usage even with hundreds of items
- Typical runtime: <1 second for 50-100 work items

## Requirements

**For ASCII and DOT formats:**
- No external dependencies required
- Works out of the box

**For SVG format:**
- Requires Graphviz installed
  - macOS: `brew install graphviz`
  - Ubuntu: `sudo apt-get install graphviz`
  - Windows: `choco install graphviz`
- Falls back to DOT format with instructions if not installed

## See Also

- [Work Next Command](work-next.md) - Get next recommended work item (considers dependencies)
- [Work List Command](work-list.md) - List work items with filters
- [Work Show Command](work-show.md) - Show detailed work item with dependency info
- [Work Update Command](work-update.md) - Update dependencies
- [Start Command](start.md) - Start working on recommended item
