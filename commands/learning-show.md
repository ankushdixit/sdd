# Learning Show Command

**Usage:** `/learning-show [--category CATEGORY] [--tag TAG] [--session SESSION]`

**Description:** Browse and filter captured learnings with optional filters.

**Behavior:**

Display all captured learnings, optionally filtered by category, tag, or session number. Learnings are organized by category for easy browsing.

## Arguments

All arguments are optional. If no arguments provided, shows all learnings.

### `--category <category>`
Filter learnings by category:
- `architecture_patterns` - Design decisions, architectural approaches, patterns used
- `gotchas` - Edge cases, pitfalls, bugs discovered, common mistakes
- `best_practices` - Effective approaches, recommended patterns, proven techniques
- `technical_debt` - Areas needing improvement, refactoring opportunities
- `performance_insights` - Optimization learnings, performance improvements
- `security` - Security-related discoveries, vulnerabilities fixed

### `--tag <tag>`
Filter learnings containing a specific tag (case-insensitive match).
Examples: `fastapi`, `python`, `cors`, `testing`

### `--session <number>`
Show only learnings captured in a specific session.
Example: `5` shows learnings from session 5

## Execution

Parse the arguments and execute:

```bash
python3 scripts/learning_curator.py show-learnings [OPTIONS]
```

Where `[OPTIONS]` are any combination of:
- `--category <category>`
- `--tag <tag>`
- `--session <number>`

## Output Format

The script displays learnings grouped by category:

```
=== Architecture Patterns (2 learnings) ===

[learn-001] Microservices communication pattern
  Tags: architecture, microservices, api
  Session: 3
  Captured: 2025-10-10 14:23:15

  Use API Gateway pattern for microservices communication. Each service
  exposes REST API through gateway, maintaining service independence.

[learn-015] Repository pattern for data access
  Tags: architecture, database, patterns
  Session: 8
  Captured: 2025-10-12 09:45:32

  Implement repository pattern to abstract data access. Makes testing
  easier and allows switching database implementations.

=== Gotchas (3 learnings) ===

[learn-007] FastAPI middleware order matters
  Tags: fastapi, cors, middleware
  Session: 5
  Captured: 2025-10-11 16:12:08

  FastAPI middleware executes in reverse order of registration.
  app.add_middleware() calls must be added in reverse order of desired execution.

... more learnings ...

Total: 12 learnings across 4 categories
```

## Examples

### Example 1: Show All Learnings

```
User: /learning-show

Claude: [Executes: python3 scripts/learning_curator.py show-learnings]

=== Architecture Patterns (5 learnings) ===
... displays all architecture learnings ...

=== Gotchas (8 learnings) ===
... displays all gotchas ...

=== Best Practices (12 learnings) ===
... displays all best practices ...

Total: 25 learnings across 3 categories
```

### Example 2: Filter by Category

```
User: /learning-show --category gotchas

Claude: [Executes: python3 scripts/learning_curator.py show-learnings --category gotchas]

=== Gotchas (8 learnings) ===

[learn-007] FastAPI middleware order matters
  Tags: fastapi, cors, middleware
  Session: 5

  FastAPI middleware executes in reverse order...

[learn-012] pytest fixture scope gotcha
  Tags: pytest, testing, fixtures
  Session: 7

  pytest.fixture(scope='session') persists across all tests...

... more gotchas ...

Total: 8 gotchas
```

### Example 3: Filter by Tag

```
User: /learning-show --tag fastapi

Claude: [Executes: python3 scripts/learning_curator.py show-learnings --tag fastapi]

=== Learnings tagged with "fastapi" ===

[learn-007] FastAPI middleware order matters
  Category: gotchas
  Tags: fastapi, cors, middleware
  Session: 5

  FastAPI middleware executes in reverse order...

[learn-018] FastAPI dependency injection best practice
  Category: best_practices
  Tags: fastapi, dependencies, patterns
  Session: 9

  Use Depends() for dependency injection in FastAPI...

Total: 5 learnings with tag "fastapi"
```

### Example 4: Filter by Session

```
User: /learning-show --session 5

Claude: [Executes: python3 scripts/learning_curator.py show-learnings --session 5]

=== Learnings from Session 5 ===

[learn-007] FastAPI middleware order matters
  Category: gotchas
  Tags: fastapi, cors, middleware

  FastAPI middleware executes in reverse order...

[learn-008] CORS preflight requests require OPTIONS method
  Category: security
  Tags: cors, security, http

  Browser sends OPTIONS preflight request before actual request...

Total: 3 learnings from session 5
```

### Example 5: Combine Filters

```
User: /learning-show --category gotchas --tag fastapi

Claude: [Executes: python3 scripts/learning_curator.py show-learnings --category gotchas --tag fastapi]

=== Gotchas tagged with "fastapi" ===

[learn-007] FastAPI middleware order matters
  Tags: fastapi, cors, middleware
  Session: 5

  FastAPI middleware executes in reverse order...

Total: 2 gotchas with tag "fastapi"
```

## No Results Handling

If no learnings match the filters:

```
No learnings found matching your filters.

Try:
- /learning-show (show all learnings)
- /learning-search <query> (full-text search)
- /learning-capture (capture a new learning)
```

## Integration

This command integrates with:
- **Learning Curation System** - Shows curated, deduplicated learnings
- **Categorization System** - Learnings organized by 6 categories
- **Tagging System** - Filter by user-defined tags
- **Session Tracking** - Filter by session number

## Related Commands

- `/learning-capture` - Capture a new learning
- `/learning-search <query>` - Full-text search across learnings
- `/learning-curate` - Run curation process (categorize, deduplicate, merge)

## Statistics View

When showing all learnings (no filters), also display statistics:

```
=== Learning Statistics ===

Total Learnings: 42
By Category:
  - best_practices: 15 (36%)
  - gotchas: 12 (29%)
  - architecture_patterns: 8 (19%)
  - performance_insights: 4 (10%)
  - security: 2 (5%)
  - technical_debt: 1 (2%)

Most Common Tags:
  1. python (18 learnings)
  2. fastapi (12 learnings)
  3. testing (9 learnings)
  4. database (7 learnings)
  5. security (5 learnings)

Recent Growth:
  - Last 5 sessions: 8 new learnings
  - This session: 2 new learnings
```

## Implementation

**Script:** `scripts/learning_curator.py`
**Subcommand:** `show-learnings`
**Database:** `.session/tracking/learnings.json`
