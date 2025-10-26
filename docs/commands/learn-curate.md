# Learning Curate Command

**Usage:** `/sdd:learn-curate [--dry-run]`

**Description:** Run automatic categorization, similarity detection, and merging of learnings.

**Behavior:**

Performs comprehensive curation of the learning database to maintain quality and reduce redundancy. Includes categorization, deduplication, merging, and archiving.

## What Curation Does

The curation process consists of 5 phases:

### 1. **Categorization**
- Auto-categorizes learnings that are uncategorized or have `uncategorized` as category
- Uses keyword-based analysis to assign to one of 6 categories:
  - `architecture_patterns` - Design patterns, architectural decisions
  - `gotchas` - Edge cases, pitfalls, common mistakes
  - `best_practices` - Proven techniques, recommended approaches
  - `technical_debt` - Areas needing improvement, workarounds
  - `performance_insights` - Optimization techniques, profiling results
  - `security` - Security vulnerabilities, best practices, fixes

### 2. **Similarity Detection**
- Detects duplicate or highly similar learnings using two algorithms:
  - **Jaccard Similarity** (threshold: 0.6) - Measures word overlap
  - **Containment Similarity** (threshold: 0.8) - Detects if one learning contains another
- Identifies pairs of learnings that should potentially be merged

### 3. **Merging**
- Automatically merges similar learnings:
  - Keeps the longer, more detailed version as primary
  - Combines tags from both learnings
  - Records merge history (which learning was merged into which)
  - Preserves session information
- Reduces redundancy while preserving information

### 4. **Archiving**
- Archives learnings older than 50 sessions (configurable)
- Archived learnings are preserved but removed from active view
- Can be restored if needed
- Helps keep the active learning set focused

### 5. **Metadata Update**
- Updates `last_curated` timestamp
- Recalculates statistics
- Updates category distribution

## Arguments

### No arguments (Normal Curation)
Runs full curation and saves changes:
```bash
sdd learn-curate
```

### `--dry-run` (Preview Mode)
Shows what would be done without saving changes:
```bash
sdd learn-curate --dry-run
```

## Execution

Parse `$ARGUMENTS` to check for `--dry-run` flag, then execute:

```bash
sdd learn-curate [--dry-run]
```

## Output Format

### Normal Mode Output

```
=== Learning Curation ===

Starting curation of 45 learnings...

Phase 1: Categorization
  ✓ Categorized 8 learnings
    - 3 → gotchas
    - 2 → best_practices
    - 2 → architecture_patterns
    - 1 → security

Phase 2: Similarity Detection
  ✓ Found 5 potential duplicates
    - learn-007 ≈ learn-023 (similarity: 0.72)
    - learn-012 ≈ learn-034 (similarity: 0.85)
    - learn-018 ≈ learn-031 (similarity: 0.68)

Phase 3: Merging
  ✓ Merged 3 duplicate learnings
    - learn-023 merged into learn-007
    - learn-034 merged into learn-012
    - learn-031 merged into learn-018

Phase 4: Archiving
  ✓ Archived 2 old learnings (>50 sessions)
    - learn-001 (from session 1)
    - learn-002 (from session 2)

Phase 5: Metadata Update
  ✓ Updated statistics and timestamps

=== Curation Complete ===

Before: 45 learnings
After:  42 learnings (3 merged, 2 archived)

Changes saved to .session/tracking/learnings.json
```

### Dry-Run Mode Output

```
=== Learning Curation (DRY RUN) ===

This is a preview - no changes will be saved.

Starting curation of 45 learnings...

Phase 1: Categorization
  Would categorize 8 learnings
    - 3 → gotchas
    - 2 → best_practices
    - 2 → architecture_patterns
    - 1 → security

Phase 2: Similarity Detection
  Would find 5 potential duplicates
    - learn-007 ≈ learn-023 (similarity: 0.72)
      [learn-007] FastAPI middleware order matters
      [learn-023] Middleware execution order in FastAPI
    - learn-012 ≈ learn-034 (similarity: 0.85)
      [learn-012] pytest fixture scope gotcha
      [learn-034] pytest fixture scope persistence issue

Phase 3: Merging
  Would merge 3 duplicate learnings
    - learn-023 → learn-007 (keep learn-007, merge tags)
    - learn-034 → learn-012 (keep learn-012, merge tags)

Phase 4: Archiving
  Would archive 2 old learnings
    - learn-001 (from session 1, 52 sessions ago)
    - learn-002 (from session 2, 51 sessions ago)

=== Preview Complete ===

Would change: 45 → 42 learnings (3 merged, 2 archived)

To apply these changes, run: /sdd:learn-curate (without --dry-run)
```

## Examples

### Example 1: Normal Curation

```
User: /sdd:learn-curate

Claude: Running learning curation...

[Executes: sdd learn-curate]

=== Learning Curation ===

Starting curation of 28 learnings...

Phase 1: Categorization
  ✓ Categorized 2 learnings

Phase 2: Similarity Detection
  ✓ Found 1 potential duplicate

Phase 3: Merging
  ✓ Merged 1 duplicate learning

Phase 4: Archiving
  ✓ No learnings to archive

Phase 5: Metadata Update
  ✓ Updated statistics

=== Curation Complete ===

Before: 28 learnings
After:  27 learnings (1 merged, 0 archived)

✓ Changes saved
```

### Example 2: Dry-Run Preview

```
User: /sdd:learn-curate --dry-run

Claude: Previewing curation (no changes will be saved)...

[Executes: sdd learn-curate --dry-run]

=== Learning Curation (DRY RUN) ===

Starting curation of 28 learnings...

Phase 2: Similarity Detection
  Would find 1 potential duplicate
    - learn-015 ≈ learn-027 (similarity: 0.73)
      [learn-015] Use ruff for faster Python linting
      [learn-027] Ruff provides faster linting than pylint

Phase 3: Merging
  Would merge 1 duplicate learning
    - learn-027 → learn-015 (keep learn-015, merge tags: "ruff,linting,python,performance")

=== Preview Complete ===

Would change: 28 → 27 learnings (1 merged)

To apply these changes, run: /sdd:learn-curate (without --dry-run)
```

### Example 3: No Changes Needed

```
User: /sdd:learn-curate

Claude: [Executes: sdd learn-curate]

=== Learning Curation ===

Starting curation of 15 learnings...

Phase 1: Categorization
  ✓ All learnings already categorized

Phase 2: Similarity Detection
  ✓ No duplicates found

Phase 3: Merging
  ✓ No merging needed

Phase 4: Archiving
  ✓ No learnings to archive

Phase 5: Metadata Update
  ✓ Updated statistics

=== Curation Complete ===

Your learnings are already well-curated! No changes needed.

Total: 15 learnings across 4 categories
```

## When to Run Curation

### Manual Curation
Run manually when:
- You've captured many new learnings and want to organize them
- You suspect duplicate learnings exist
- You want to preview curation effects (with `--dry-run`)
- You're testing or debugging the curation process

### Automatic Curation
Curation also runs automatically:
- Triggered every N sessions (default: 5, configurable in `.session/config.json`)
- Runs at session completion if threshold reached
- Can be disabled in configuration

## Understanding Similarity Algorithms

### Jaccard Similarity (0.6 threshold)
Measures word overlap between two learnings:
```
Similarity = (Common Words) / (Total Unique Words)

Example:
Learning A: "FastAPI middleware order matters"
Learning B: "Middleware execution order in FastAPI"

Common words: {fastapi, middleware, order}
Total unique: {fastapi, middleware, order, matters, execution, in}
Similarity: 3/6 = 0.50 (below threshold, not merged)
```

### Containment Similarity (0.8 threshold)
Detects if one learning is contained in another:
```
Containment = (Words in Smaller) / (Total Words in Smaller)

Example:
Learning A: "Use pytest for testing"
Learning B: "Use pytest for testing Python applications effectively"

Containment: 4/4 = 1.0 (above threshold, would merge)
```

## Configuration

Curation settings in `.session/config.json`:

```json
{
  "curation": {
    "auto_curate": true,
    "frequency": 5,
    "dry_run": false,
    "similarity_threshold": 0.7,
    "categories": [
      "architecture_patterns",
      "gotchas",
      "best_practices",
      "technical_debt",
      "performance_insights",
      "security"
    ]
  }
}
```

## Integration

This command integrates with:
- **Session Workflow** - Auto-runs every N sessions during `/sdd:end`
- **Learning Capture** - Newly captured learnings are categorized during curation
- **Learning Display** - Curated learnings appear organized in `/sdd:learn-show`
- **Search** - Better categorization improves search results

## Related Commands

- `/sdd:learn` - Capture a new learning
- `/sdd:learn-show [--category]` - Browse curated learnings
- `/sdd:learn-search <query>` - Search across learnings

## Implementation

**Module:** `sdd.learning.curator`
**Subcommand:** `curate`
**Database:** `.session/tracking/learnings.json`
**Configuration:** `.session/config.json`
**Algorithms:** Jaccard similarity, Containment similarity, Keyword-based categorization
