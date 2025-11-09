# Learn Curate Command

**Usage:** `/sdd:learn-curate [--dry-run]`

**Description:** Run automatic categorization, similarity detection, and merging of learnings to maintain database quality.

## Overview

The `learn-curate` command performs comprehensive curation of your learning database to reduce redundancy and maintain quality. It automatically categorizes uncategorized learnings, detects duplicates, merges similar content, and archives old learnings.

**Key features:**
- Auto-categorization using keyword analysis
- Duplicate detection with similarity algorithms
- Automatic merging to reduce redundancy
- Archiving of old learnings (>50 sessions)
- Dry-run mode for previewing changes
- Detailed curation reports

## What Curation Does

The curation process consists of 5 phases:

### 1. Categorization

Auto-categorizes learnings that are uncategorized or have `uncategorized` as category.

**Uses keyword-based analysis to assign to one of 6 categories:**
- `architecture_patterns` - Design patterns, architectural decisions
- `gotchas` - Edge cases, pitfalls, common mistakes
- `best_practices` - Proven techniques, recommended approaches
- `technical_debt` - Areas needing improvement, workarounds
- `performance_insights` - Optimization techniques, profiling results
- `security` - Security vulnerabilities, best practices, fixes

### 2. Similarity Detection

Detects duplicate or highly similar learnings using two algorithms:

**Jaccard Similarity (threshold: 0.6)**
- Measures word overlap between learnings
- `Similarity = (Common Words) / (Total Unique Words)`

**Containment Similarity (threshold: 0.8)**
- Detects if one learning contains another
- `Containment = (Words in Smaller) / (Total Words in Smaller)`

### 3. Merging

Automatically merges similar learnings:
- Keeps the longer, more detailed version as primary
- Combines tags from both learnings
- Records merge history (which learning was merged into which)
- Preserves session information
- Reduces redundancy while preserving information

### 4. Archiving

Archives learnings older than 50 sessions (configurable):
- Archived learnings preserved but removed from active view
- Can be restored if needed
- Keeps active learning set focused

### 5. Metadata Update

Updates learning database metadata:
- Sets `last_curated` timestamp
- Recalculates statistics
- Updates category distribution

## Arguments

### No arguments (Normal Curation)

Runs full curation and saves changes:
```bash
/sdd:learn-curate
```

### `--dry-run` (Preview Mode)

Shows what would be done without saving changes:
```bash
/sdd:learn-curate --dry-run
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

```bash
/sdd:learn-curate
```

**Output:**
```
Running learning curation...

=== Learning Curation ===

Starting curation of 28 learnings...

Phase 1: Categorization
  ✓ Categorized 2 learnings
    - 1 → gotchas
    - 1 → best_practices

Phase 2: Similarity Detection
  ✓ Found 1 potential duplicate
    - learn-015 ≈ learn-027 (similarity: 0.73)

Phase 3: Merging
  ✓ Merged 1 duplicate learning
    - learn-027 merged into learn-015
    - Combined tags: ruff, linting, python, performance

Phase 4: Archiving
  ✓ No learnings to archive

Phase 5: Metadata Update
  ✓ Updated statistics

=== Curation Complete ===

Before: 28 learnings
After:  27 learnings (1 merged, 0 archived)

✓ Changes saved to .session/tracking/learnings.json
```

### Example 2: Dry-Run Preview

```bash
/sdd:learn-curate --dry-run
```

**Output:**
```
Previewing curation (no changes will be saved)...

=== Learning Curation (DRY RUN) ===

Starting curation of 28 learnings...

Phase 1: Categorization
  ✓ All learnings already categorized

Phase 2: Similarity Detection
  Would find 1 potential duplicate
    - learn-015 ≈ learn-027 (similarity: 0.73)
      [learn-015] Use ruff for faster Python linting
      [learn-027] Ruff provides faster linting than pylint

Phase 3: Merging
  Would merge 1 duplicate learning
    - learn-027 → learn-015
      Keep: "Use ruff for faster Python linting"
      Merge tags: ruff, linting, python, performance

Phase 4: Archiving
  ✓ No learnings to archive

=== Preview Complete ===

Would change: 28 → 27 learnings (1 merged, 0 archived)

To apply these changes, run: /sdd:learn-curate (without --dry-run)
```

### Example 3: No Changes Needed

```bash
/sdd:learn-curate
```

**Output:**
```
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

### Example 4: Heavy Curation Needed

```bash
/sdd:learn-curate
```

**Output:**
```
=== Learning Curation ===

Starting curation of 67 learnings...

Phase 1: Categorization
  ✓ Categorized 12 learnings
    - 5 → gotchas
    - 4 → best_practices
    - 2 → architecture_patterns
    - 1 → security

Phase 2: Similarity Detection
  ✓ Found 15 potential duplicates
    - learn-007 ≈ learn-023 (similarity: 0.72)
    - learn-012 ≈ learn-034 (similarity: 0.85)
    - learn-015 ≈ learn-027 ≈ learn-041 (cluster of 3)
    ... 12 more pairs ...

Phase 3: Merging
  ✓ Merged 8 duplicate learnings
    - learn-023 merged into learn-007
    - learn-034 merged into learn-012
    - learn-027, learn-041 merged into learn-015
    ... 5 more merges ...

Phase 4: Archiving
  ✓ Archived 5 old learnings (>50 sessions)
    - learn-001 through learn-005

Phase 5: Metadata Update
  ✓ Updated statistics

=== Curation Complete ===

Before: 67 learnings
After:  54 learnings (8 merged, 5 archived)

Significant cleanup performed! Your learning database is now more focused.

✓ Changes saved
```

## When to Run Curation

### Manual Curation

Run manually when:
- You've captured many new learnings and want to organize them
- You suspect duplicate learnings exist
- You want to preview curation effects (with `--dry-run`)
- You're testing or debugging the curation process
- You notice uncategorized learnings

### Automatic Curation

Curation also runs automatically:
- Triggered every N sessions (default: 5, configurable)
- Runs at session completion if threshold reached
- Can be disabled in `.session/config.json`

**Example automatic trigger:**
```
Session 15 completed.

Auto-curation threshold reached (every 5 sessions).
Running automatic curation...

[Curation output...]

✓ Curation complete
```

## Understanding Similarity Algorithms

### Jaccard Similarity (0.6 threshold)

Measures word overlap between two learnings:

```
Similarity = (Common Words) / (Total Unique Words)
```

**Example:**
```
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
```

**Example:**
```
Learning A: "Use pytest for testing"
Learning B: "Use pytest for testing Python applications effectively"

Words in A: {use, pytest, for, testing}
All in B: Yes (4/4 = 1.0)
Containment: 1.0 (above threshold, would merge)
```

### Why These Thresholds?

- **Jaccard 0.6**: Catches similar learnings while avoiding false positives
- **Containment 0.8**: Merges clear subsets without being too aggressive
- Both thresholds are configurable in `.session/config.json`

## Merge Strategy

When merging learnings, the algorithm:

### 1. Determines Primary Learning

```
Primary = longer learning (more detailed)
Secondary = shorter learning (less detailed)
```

### 2. Combines Tags

```
Merged tags = Primary tags ∪ Secondary tags
```

**Example:**
```
Primary tags: [fastapi, cors]
Secondary tags: [fastapi, middleware, cors]
Result: [fastapi, cors, middleware]
```

### 3. Records Merge History

```json
{
  "merge_history": [
    {
      "merged_id": "learn-023",
      "merged_at": "2025-10-13T14:22:15",
      "reason": "Jaccard similarity 0.72"
    }
  ]
}
```

## Use Cases

### Periodic Cleanup

```bash
# Every few weeks, review and clean up
/sdd:learn-curate --dry-run     # Preview changes
/sdd:learn-curate                # Apply changes
```

### Before Important Milestones

```bash
# Before releasing or demo
/sdd:learn-curate
/sdd:learn-show                  # Verify clean state
```

### After Bulk Learning Capture

```bash
# After capturing many learnings
/sdd:learn                       # Capture 10 learnings
/sdd:learn                       # Capture more
/sdd:learn-curate               # Organize everything
```

### Testing Similarity Thresholds

```bash
# Test different thresholds
/sdd:learn-curate --dry-run     # See what would merge
# Adjust thresholds in config
/sdd:learn-curate --dry-run     # See new results
/sdd:learn-curate                # Apply when satisfied
```

## Integration with Other Commands

### Capture → Curate Workflow

```bash
/sdd:learn                       # Capture learnings during session
# ... more work ...
/sdd:learn                       # Capture more learnings
/sdd:learn-curate               # Clean up at end of day
```

### Browse → Curate → Browse

```bash
/sdd:learn-show                  # See current state
/sdd:learn-curate --dry-run     # Preview cleanup
/sdd:learn-curate                # Apply changes
/sdd:learn-show                  # Verify improved organization
```

### Search Quality Improvement

```bash
/sdd:learn-search "middleware"   # Search before curation
/sdd:learn-curate                # Merge duplicates, improve categorization
/sdd:learn-search "middleware"   # Cleaner, better results
```

## Configuration

Curation settings in `.session/config.json`:

```json
{
  "curation": {
    "auto_curate": true,
    "frequency": 5,
    "dry_run": false,
    "archive_threshold_sessions": 50,
    "similarity_threshold_jaccard": 0.6,
    "similarity_threshold_containment": 0.8,
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

**Configuration options:**
- `auto_curate`: Enable/disable automatic curation
- `frequency`: Run curation every N sessions
- `dry_run`: Always run in dry-run mode (preview only)
- `archive_threshold_sessions`: Archive learnings older than N sessions
- `similarity_threshold_jaccard`: Jaccard similarity threshold (0.0-1.0)
- `similarity_threshold_containment`: Containment threshold (0.0-1.0)

## Best Practices

### 1. Preview Before Applying

Always check dry-run first for significant changes:
```bash
/sdd:learn-curate --dry-run     # Review what will happen
/sdd:learn-curate                # Apply if looks good
```

### 2. Run Periodically

Don't let learnings accumulate too long:
```bash
# Every 5-10 sessions
/sdd:learn-curate
```

### 3. Review Merge Decisions

Check merged learnings occasionally:
```bash
/sdd:learn-show                  # Look for merged learnings
# Review merge_history field in learnings.json if needed
```

### 4. Adjust Thresholds Carefully

Start conservative, then tune:
```bash
# Default: 0.6 Jaccard, 0.8 Containment
# Too many duplicates? Lower thresholds
# Too aggressive merging? Raise thresholds
```

## Common Scenarios

### Scenario 1: Too Many Duplicates

**Problem:** Search returns multiple similar learnings

**Solution:**
```bash
/sdd:learn-curate --dry-run     # Preview merges
/sdd:learn-curate                # Apply merges
/sdd:learn-search "middleware"   # Verify cleaner results
```

### Scenario 2: Uncategorized Learnings

**Problem:** Many learnings showing as "uncategorized"

**Solution:**
```bash
/sdd:learn-curate                # Auto-categorize
/sdd:learn-show                  # Verify categories assigned
```

### Scenario 3: Old Learnings Cluttering

**Problem:** Too many old learnings no longer relevant

**Solution:**
```bash
/sdd:learn-curate                # Archive old learnings
# Or adjust archive_threshold_sessions in config
```

## Performance

Curation is optimized for:
- Fast similarity computation (O(n²) with early termination)
- Efficient keyword matching for categorization
- Minimal memory usage even with hundreds of learnings
- Quick JSON read/write operations
- Typical runtime: 1-5 seconds for 50-100 learnings

## See Also

- [Learn Command](learn.md) - Capture new learnings
- [Learn Show Command](learn-show.md) - Browse curated learnings
- [Learn Search Command](learn-search.md) - Better search with curation
- [End Command](end.md) - Auto-curation triggers during session end
