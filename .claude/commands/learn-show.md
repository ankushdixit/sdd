---
description: Browse and filter learnings
argument-hint: [--category CATEGORY] [--tag TAG] [--session SESSION]
---

# Show Learnings

View captured learnings with optional filtering.

## Usage

Parse $ARGUMENTS for filters and run the show-learnings command:

```bash
sk learn-show "$@"
```

### Filter Options

- `--category <category>` - Filter by category:
  - `architecture_patterns` - Design decisions and patterns
  - `gotchas` - Edge cases and pitfalls
  - `best_practices` - Effective approaches
  - `technical_debt` - Areas needing improvement
  - `performance_insights` - Optimization learnings
  - `security` - Security-related discoveries

- `--tag <tag>` - Filter by specific tag (e.g., `python`, `fastapi`, `cors`)

- `--session <number>` - Show learnings from specific session number

### Examples

Show all learnings:

```bash
sk learn-show
```

Show only gotchas:

```bash
sk learn-show --category gotchas
```

Show learnings tagged with "fastapi":

```bash
sk learn-show --tag fastapi
```

Show learnings from session 5:

```bash
sk learn-show --session 5
```

Combine filters (gotchas from session 5):

```bash
sk learn-show --category gotchas --session 5
```

## Display Format

The command will display learnings in organized format showing:

- Category grouping
- Learning content
- Tags (if any)
- Session number where captured
- Timestamp
- Learning ID

Present the output to the user in a clear, readable format.
