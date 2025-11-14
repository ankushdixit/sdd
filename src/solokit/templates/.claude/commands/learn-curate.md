---
description: Run learning curation process
argument-hint: [--dry-run]
---

# Curate Learnings

Run automatic categorization, similarity detection, and merging of learnings.

## What Curation Does

The curation process:

1. **Categorizes** uncategorized learnings using AI-powered keyword analysis
2. **Detects duplicates** using Jaccard and containment similarity algorithms
3. **Merges similar learnings** to reduce redundancy
4. **Archives old learnings** (learnings older than 50 sessions)
5. **Updates metadata** (last_curated timestamp)

## Usage

### Normal Curation (Save Changes)

```bash
sk learn-curate
```

This will:

- Process all learnings
- Save changes to learnings.json
- Display summary of actions taken

### Dry-Run Mode (Preview Only)

```bash
sk learn-curate --dry-run
```

This will:

- Show what changes would be made
- NOT save any changes
- Useful for previewing curation results

## When to Run Curation

Manual curation is useful when:

- You've captured many learnings and want to organize them
- You want to check for duplicate learnings
- You want to preview what auto-curation would do
- You're testing the curation process

Note: Curation also runs automatically every N sessions (configurable in .session/config.json).

## Output Format

Display the curation summary showing:

- Initial learning count
- Number of learnings categorized
- Number of duplicates merged
- Number of learnings archived
- Final learning count

Example output:

```
=== Learning Curation ===

Initial learnings: 45

✓ Categorized 8 learnings
✓ Merged 3 duplicate learnings
✓ Archived 2 old learnings

Final learnings: 42

✓ Learnings saved
```

## Understanding the Process

**Categorization:** Uses keyword analysis to assign learnings to one of 6 categories:

- architecture_patterns, gotchas, best_practices, technical_debt, performance_insights, security

**Similarity Detection:** Uses two algorithms:

- **Jaccard similarity:** Measures word overlap (threshold: 0.6)
- **Containment similarity:** Detects if one learning contains another (threshold: 0.8)

**Merging:** Combines tags and tracks merge history when duplicates are found.

**Archiving:** Moves learnings older than 50 sessions to archive (preserves them but removes from active view).
