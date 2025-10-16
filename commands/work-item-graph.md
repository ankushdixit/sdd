---
description: Generate dependency graph visualization for work items
argument-hint: [--format FORMAT] [--status STATUS] [--milestone MILESTONE] [--type TYPE] [--focus ID] [--critical-path] [--bottlenecks] [--stats] [--include-completed] [--output FILE]
---

# Work Item Graph

Generate visual dependency graphs showing relationships between work items, with critical path highlighting and bottleneck analysis.

## Usage

Ask the user what type of graph they want to generate:

1. **Format** - Ask: "What output format would you like?"
   - Options: ascii (default, terminal display), dot (Graphviz), svg (requires Graphviz)
   - Default to ascii if not specified

2. **Filters** - Ask: "Any filters to apply? (or 'none' for all work items)"
   - Status: only show items with specific status (not_started, in_progress, completed)
   - Milestone: only show items in specific milestone
   - Type: only show specific work item types
   - Include completed: whether to show completed items (default: no)

3. **Special views** - Ask: "Need any special analysis?"
   - critical-path: Show only critical path items
   - bottlenecks: Highlight bottleneck analysis
   - stats: Show graph statistics
   - focus <work_item_id>: Show neighborhood of specific item

## After Collecting Information

Run the appropriate command based on user input:

**Basic usage:**
```bash
python3 scripts/dependency_graph.py
```

**With format:**
```bash
python3 scripts/dependency_graph.py --format dot
python3 scripts/dependency_graph.py --format svg --output graph.svg
```

**With filters:**
```bash
python3 scripts/dependency_graph.py --status not_started
python3 scripts/dependency_graph.py --milestone "Phase 3"
python3 scripts/dependency_graph.py --type feature
python3 scripts/dependency_graph.py --include-completed
```

**Special views:**
```bash
python3 scripts/dependency_graph.py --critical-path
python3 scripts/dependency_graph.py --bottlenecks
python3 scripts/dependency_graph.py --stats
python3 scripts/dependency_graph.py --focus feature_add_authentication
```

**Combined filters:**
```bash
python3 scripts/dependency_graph.py --status not_started --milestone "Phase 3" --format svg --output phase3.svg
```

## Output

The command will generate a visual graph showing:
- Work items as nodes (with ID, title, status)
- Dependencies as edges (arrows from dependency to dependent)
- Critical path highlighted in red
- Color coding by status and priority
- Bottlenecks identified

Display the output to the user and explain key insights:
- Which items are on critical path (determines project timeline)
- Which items are bottlenecks (blocking multiple other items)
- Completion percentage
- Next recommended items to work on

## Examples

### Example 1: Basic ASCII Graph
```bash
python3 scripts/dependency_graph.py
```
Shows all incomplete work items with dependencies in terminal-friendly format.

### Example 2: Critical Path Only
```bash
python3 scripts/dependency_graph.py --critical-path
```
Shows only items on the critical path (longest dependency chain).

### Example 3: Bottleneck Analysis
```bash
python3 scripts/dependency_graph.py --bottlenecks
```
Lists items that block 2+ other items, sorted by impact.

### Example 4: Milestone Planning
```bash
python3 scripts/dependency_graph.py --milestone "Phase 3" --format svg --output phase3_dependencies.svg
```
Generate visual graph of Phase 3 dependencies for documentation.

### Example 5: Focus on Specific Item
```bash
python3 scripts/dependency_graph.py --focus feature_oauth
```
Show only feature_oauth and its dependency neighborhood (dependencies + dependents).

### Example 6: Statistics
```bash
python3 scripts/dependency_graph.py --stats
```
Show completion statistics and critical path length without rendering full graph.

## Interpreting the Output

**Node Colors:**
- **Red**: Critical path items (determine project timeline)
- **Green**: Completed items
- **Blue**: In progress items
- **Black/White**: Not started items
- **Orange**: Blocked items

**Arrows:**
- Point from dependency → dependent
- Bold red arrows = critical path connections

**Bottlenecks:**
- Items that block 2+ other items
- Prioritize completing these to unblock downstream work

**Critical Path:**
- Longest chain of dependencies
- Determines minimum project timeline
- Focus here to minimize overall project duration
