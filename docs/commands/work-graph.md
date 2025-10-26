# Work Item Graph Command

**Usage:** `/sdd:work-graph [OPTIONS]`

**Description:** Generate dependency graph visualization for work items with critical path analysis and bottleneck detection.

**Behavior:**

Creates visual representations of work item dependencies, helping identify critical paths, bottlenecks, and project structure. Supports multiple output formats and flexible filtering.

## Arguments

All arguments are optional. Multiple options can be combined.

### Format Options

#### `--format <format>`
Output format for the graph:
- `ascii` (default) - Terminal-friendly box drawing, color-coded
- `dot` - Graphviz DOT format (plaintext graph description)
- `svg` - SVG image (requires Graphviz installed)

#### `--output <file>`
Save graph to file instead of terminal output. Only works with `--format dot` or `--format svg`.

### Filter Options

#### `--status <status>`
Show only items with specific status:
- `not_started` - Items not yet begun
- `in_progress` - Items currently being worked on
- `completed` - Finished items
- `blocked` - Items waiting on dependencies

#### `--milestone <milestone>`
Show only items in a specific milestone.
Example: `--milestone "Phase 3"`

#### `--type <type>`
Show only specific work item types:
- `feature`, `bug`, `refactor`, `security`, `integration_test`, `deployment`

#### `--include-completed`
Include completed items in the graph (default: excluded for clarity)

#### `--focus <work_item_id>`
Show only the specified item and its dependency neighborhood:
- Direct dependencies (items this depends on)
- Direct dependents (items that depend on this)

### Analysis Options

#### `--critical-path`
Show only items on the critical path (longest dependency chain). These items determine the minimum project timeline.

#### `--bottlenecks`
Highlight bottleneck analysis - items that block 2+ other items. Sorted by impact (number of blocked items).

#### `--stats`
Show graph statistics without rendering full graph:
- Total items by status
- Completion percentage
- Critical path length
- Bottleneck count
- Timeline projection

## Execution

Parse `$ARGUMENTS` and construct the command:

```bash
sdd work-graph [OPTIONS]
```

Replace `[OPTIONS]` with any combination of the arguments above.

## Output Formats

### ASCII Format (Terminal)

Box-drawing characters with color coding:

```
Work Item Dependency Graph
==========================

┌─────────────────────────────┐
│ feature-001                 │ [●] In Progress (CRITICAL PATH)
│ User Authentication         │
│ Priority: high              │
└─────────────────────────────┘
              ↓
┌─────────────────────────────┐
│ feature-002                 │ [○] Not Started (CRITICAL PATH)
│ OAuth Integration           │
│ Priority: high              │
└─────────────────────────────┘
              ↓
┌─────────────────────────────┐
│ feature-003                 │ [○] Not Started
│ User Profile Page           │
│ Priority: medium            │
└─────────────────────────────┘

Legend:
  [✓] Completed  [●] In Progress  [○] Not Started  [✗] Blocked
  Red = Critical Path  Orange = Bottleneck

Critical Path Length: 3 items
Timeline Estimate: 3 sessions minimum
Bottlenecks: feature-001 (blocks 2 items)
```

### DOT Format (Graphviz)

Plaintext graph description:

```dot
digraph work_items {
  rankdir=LR;
  node [shape=box, style=rounded];

  "feature-001" [label="feature-001\nUser Authentication\nPriority: high", color=red, style=filled, fillcolor=lightblue];
  "feature-002" [label="feature-002\nOAuth Integration\nPriority: high", color=red];
  "feature-003" [label="feature-003\nUser Profile Page\nPriority: medium"];

  "feature-001" -> "feature-002" [color=red, penwidth=2];
  "feature-002" -> "feature-003";
}
```

### SVG Format (Visual)

Rendered graph image suitable for documentation, presentations, or embedding in reports.

## Examples

### Example 1: Basic Graph (All Incomplete Items)

```
User: /sdd:work-graph

Claude: [Executes: sdd work-graph]

Work Item Dependency Graph
==========================

Total: 12 work items (5 complete, 2 in progress, 5 not started)

┌─────────────────────────────┐
│ feature-001                 │ [●] In Progress (CRITICAL PATH)
│ User Authentication         │
└─────────────────────────────┘
              ↓
┌─────────────────────────────┐
│ feature-002                 │ [○] Not Started (CRITICAL PATH)
│ OAuth Integration           │
└─────────────────────────────┘
              ↓
┌─────────────────────────────┐
│ feature-003                 │ [○] Not Started
│ User Profile Page           │
└─────────────────────────────┘

... [9 more items] ...

Critical Path: 5 items
Timeline Estimate: 5 sessions minimum
Next Recommended: feature-001 (in progress, high priority, critical path)
```

### Example 2: Critical Path Analysis

```
User: /sdd:work-graph --critical-path

Claude: [Executes: sdd work-graph --critical-path]

Critical Path Analysis
=====================

The critical path determines your minimum project timeline.

Critical Path (5 items):

  1. [●] feature-001: User Authentication (Session 12, in progress)
          ↓
  2. [○] feature-002: OAuth Integration (depends on feature-001)
          ↓
  3. [○] feature-006: Admin Dashboard (depends on feature-002)
          ↓
  4. [○] integration-001: End-to-end Auth Tests (depends on feature-006)
          ↓
  5. [○] deployment-001: Production Deploy (depends on integration-001)

Timeline:
  - Completed: 0/5 (0%)
  - In Progress: 1/5 (20%)
  - Remaining: 4/5 (80%)
  - Estimated Duration: 4+ sessions

💡 To minimize project duration, prioritize completing critical path items.
```

### Example 3: Bottleneck Detection

```
User: /sdd:work-graph --bottlenecks

Claude: [Executes: sdd work-graph --bottlenecks]

Bottleneck Analysis
===================

Items that block multiple other items (prioritize these!):

1. feature-001: User Authentication (blocks 4 items)
   Status: In Progress (Session 12)
   Blocking:
     - feature-002: OAuth Integration
     - feature-003: User Profile Page
     - feature-005: Password Reset Flow
     - security-001: Security Audit

2. feature-002: OAuth Integration (blocks 3 items)
   Status: Not Started
   Blocking:
     - feature-006: Admin Dashboard
     - feature-007: API Rate Limiting
     - integration-001: End-to-end Tests

3. bug-003: Database Connection Pool Issue (blocks 2 items)
   Status: Not Started
   Blocking:
     - feature-008: Batch Processing
     - feature-009: Background Jobs

💡 Completing feature-001 will unblock 4 items.
   This is your highest-impact work item.
```

### Example 4: Milestone View

```
User: /sdd:work-graph --milestone "Phase 3" --include-completed

Claude: [Executes: sdd work-graph --milestone "Phase 3" --include-completed]

Phase 3 Dependency Graph
========================

Milestone: Phase 3 (8 items total)

┌─────────────────────────────┐
│ feature-010                 │ [✓] Completed
│ Search Functionality        │
└─────────────────────────────┘
              ↓
┌─────────────────────────────┐
│ feature-011                 │ [✓] Completed
│ Search Filters              │
└─────────────────────────────┘
              ↓
┌─────────────────────────────┐
│ feature-012                 │ [●] In Progress (CRITICAL PATH)
│ Search Analytics            │
└─────────────────────────────┘
              ↓
┌─────────────────────────────┐
│ integration-002             │ [○] Not Started (CRITICAL PATH)
│ Search Integration Tests    │
└─────────────────────────────┘

Progress: 2/8 completed (25%)
Next Item: feature-012 (in progress)
```

### Example 5: Focus on Specific Item

```
User: /sdd:work-graph --focus feature-002

Claude: [Executes: sdd work-graph --focus feature-002]

Focused View: feature-002
=========================

Dependencies (items feature-002 depends on):

┌─────────────────────────────┐
│ feature-001                 │ [●] In Progress
│ User Authentication         │
└─────────────────────────────┘
              ↓
┌─────────────────────────────┐
│ feature-002                 │ [○] Not Started (TARGET)
│ OAuth Integration           │
└─────────────────────────────┘
              ↓
Dependents (items that depend on feature-002):

┌─────────────────────────────┐
│ feature-006                 │ [○] Not Started
│ Admin Dashboard             │
└─────────────────────────────┘

┌─────────────────────────────┐
│ feature-007                 │ [○] Not Started
│ API Rate Limiting           │
└─────────────────────────────┘

Status: feature-002 cannot start until feature-001 is completed
Impact: Completing feature-002 will unblock 2 items
```

### Example 6: Statistics Only

```
User: /sdd:work-graph --stats

Claude: [Executes: sdd work-graph --stats]

Work Item Graph Statistics
==========================

Total Work Items: 24

By Status:
  - Completed:     8 (33%)
  - In Progress:   3 (13%)
  - Not Started:  12 (50%)
  - Blocked:       1 (4%)

By Type:
  - feature:           15 items
  - bug:                4 items
  - refactor:           2 items
  - security:           1 item
  - integration_test:   1 item
  - deployment:         1 item

By Priority:
  - Critical:  2 items
  - High:      8 items
  - Medium:   10 items
  - Low:       4 items

By Milestone:
  - Phase 1:   6 items (100% complete)
  - Phase 2:   8 items (75% complete)
  - Phase 3:  10 items (20% complete)

Critical Path:
  - Length: 7 items
  - Completed: 2 items (29%)
  - Remaining: 5 items
  - Estimated Duration: 5+ sessions

Bottlenecks:
  - 3 items blocking 2+ other items
  - Top bottleneck: feature-001 (blocks 4 items)

Next Recommended Items:
  1. feature-001 (in progress, high priority, critical path)
  2. bug-005 (blocked by feature-001, high priority)
  3. refactor-002 (no dependencies, medium priority)
```

### Example 7: Export to SVG

```
User: /sdd:work-graph --format svg --output project-dependencies.svg

Claude: [Executes: sdd work-graph --format svg --output project-dependencies.svg]

✓ Dependency graph generated successfully!

Format: SVG
Output: project-dependencies.svg
Size: 24 work items, 18 dependencies

The graph includes:
  - Critical path highlighted in red
  - Color coding by status
  - Priority indicators
  - Milestone grouping

You can:
  - Open in browser to view
  - Include in documentation
  - Share with team
  - Embed in presentations

To view: open project-dependencies.svg
```

### Example 8: Combined Filters

```
User: /sdd:work-graph --status not_started --milestone "Phase 3" --type feature

Claude: [Executes: sdd work-graph --status not_started --milestone "Phase 3" --type feature]

Filtered Work Items
===================

Filters: Status=not_started, Milestone=Phase 3, Type=feature

Found 6 matching items:

┌─────────────────────────────┐
│ feature-012                 │ [○] Not Started (CRITICAL PATH)
│ Search Analytics            │
└─────────────────────────────┘

┌─────────────────────────────┐
│ feature-013                 │ [○] Not Started
│ Export Functionality        │
└─────────────────────────────┘

... [4 more items] ...

2 of these are on the critical path.
Next Recommended: feature-012 (critical path, high priority, no blockers)
```

## Understanding the Visualization

### Node Colors

- **Red nodes/text**: Critical path items (determine project timeline)
- **Green**: Completed items (✓)
- **Blue**: In progress items (●)
- **Black/White**: Not started items (○)
- **Orange**: Bottleneck items (blocking 2+ others)
- **Gray**: Blocked items (✗)

### Edge (Arrow) Styles

- **Solid arrows**: Standard dependencies
- **Bold red arrows**: Critical path connections
- **Dashed arrows**: Optional/soft dependencies

### Symbols

- `[✓]` - Completed
- `[●]` - In Progress
- `[○]` - Not Started
- `[✗]` - Blocked
- `[⚠]` - Bottleneck

## Use Cases

### 1. Project Planning
```bash
/sdd:work-graph --stats
```
Get overview of project structure and completion status.

### 2. Sprint Planning
```bash
/sdd:work-graph --milestone "Sprint 5" --status not_started
```
See what's available to work on in upcoming sprint.

### 3. Timeline Estimation
```bash
/sdd:work-graph --critical-path
```
Identify minimum project duration.

### 4. Unblocking Work
```bash
/sdd:work-graph --bottlenecks
```
Find high-impact items to prioritize.

### 5. Documentation
```bash
/sdd:work-graph --format svg --output docs/dependencies.svg
```
Generate visual documentation for architecture reviews.

### 6. Status Reports
```bash
/sdd:work-graph --milestone "Q4 Goals" --include-completed
```
Show progress on milestone objectives.

## Tips

**For terminal viewing:**
- Use ASCII format (default) for best readability
- Exclude completed items for cleaner view
- Focus on critical path to prioritize work

**For documentation:**
- Export to SVG format for visual diagrams
- Include completed items to show progress
- Use milestone filters for phase-specific views

**For planning:**
- Check bottlenecks regularly to avoid blocking work
- Review critical path when estimating timelines
- Use stats view for quick health checks

## Integration

This command integrates with:
- **Work Item System** - Reads from `.session/tracking/work_items.json`
- **Dependency Resolution** - DFS-based critical path algorithm
- **Milestone Tracking** - Filter by milestone
- **Priority System** - Visual priority indicators

## Related Commands

- `/sdd:work-next` - Get next recommended work item (considers dependencies)
- `/sdd:work-list` - List work items with filters
- `/sdd:work-show <id>` - Show detailed work item including dependency info
- `/sdd:start <id>` - Start working on recommended item

## Requirements

**For ASCII and DOT formats:**
- No external dependencies required

**For SVG format:**
- Requires Graphviz installed (`brew install graphviz` on macOS)
- If Graphviz not installed, falls back to DOT format with instructions

## Implementation

**Module:** `sdd.visualization.dependency_graph`
**Algorithm:** DFS-based critical path analysis with Kahn's algorithm for cycle detection
**Output:** ASCII art with box-drawing characters, DOT language, or SVG via Graphviz
**Database:** `.session/tracking/work_items.json`
