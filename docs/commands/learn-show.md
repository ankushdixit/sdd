# Learn Show Command

**Usage:** `/sdd:learn-show [--category CATEGORY] [--tag TAG] [--session SESSION]`

**Description:** Browse and filter captured learnings with optional filters.

## Overview

The `learn-show` command displays all captured learnings in an organized format, with powerful filtering options to find specific insights. Learnings are grouped by category for easy browsing.

**Key features:**
- View all learnings or filter by category, tag, or session
- Category-grouped organization
- Detailed metadata (tags, session, timestamp)
- Learning statistics when showing all
- Quick integration with other learning commands

## Arguments

All arguments are optional. Without arguments, shows all learnings.

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

**Examples:** `fastapi`, `python`, `cors`, `testing`, `react`

### `--session <number>`

Show only learnings captured in a specific session number.

**Example:** `5` shows learnings from session 5

### Combining Filters

You can combine multiple filters:
```bash
/sdd:learn-show --category gotchas --tag fastapi
/sdd:learn-show --category gotchas --session 5
/sdd:learn-show --tag python --session 8
```

## Output Format

Learnings are displayed grouped by category with full metadata:

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

```bash
/sdd:learn-show
```

**Output:**
```
=== Architecture Patterns (5 learnings) ===

[learn-001] Microservices communication pattern
  Tags: architecture, microservices, api
  Session: 3

  Use API Gateway pattern for microservices communication...

[learn-015] Repository pattern for data access
  Tags: architecture, database, patterns
  Session: 8

  Implement repository pattern to abstract data access...

... more architecture patterns ...

=== Gotchas (8 learnings) ===

[learn-007] FastAPI middleware order matters
  Tags: fastapi, cors, middleware
  Session: 5

  FastAPI middleware executes in reverse order...

... more gotchas ...

=== Best Practices (12 learnings) ===

[learn-018] Use Depends() for dependency injection
  Tags: fastapi, dependencies, patterns
  Session: 9

  Use Depends() for dependency injection in FastAPI...

... more best practices ...

Total: 25 learnings across 3 categories
```

### Example 2: Filter by Category

```bash
/sdd:learn-show --category gotchas
```

**Output:**
```
=== Gotchas (8 learnings) ===

[learn-007] FastAPI middleware order matters
  Tags: fastapi, cors, middleware
  Session: 5
  Captured: 2025-10-11 16:12:08

  FastAPI middleware executes in reverse order of registration.
  app.add_middleware() calls must be in reverse order.

[learn-012] pytest fixture scope gotcha
  Tags: pytest, testing, fixtures
  Session: 7
  Captured: 2025-10-11 18:34:22

  pytest.fixture(scope='session') persists across all tests in file.
  Use scope='function' for test isolation.

[learn-023] React useCallback dependency gotcha
  Tags: react, hooks, dependencies
  Session: 11
  Captured: 2025-10-12 10:15:45

  React useCallback dependencies must include all values used inside
  the callback, or you'll get stale closures.

... 5 more gotchas ...

Total: 8 gotchas
```

### Example 3: Filter by Tag

```bash
/sdd:learn-show --tag fastapi
```

**Output:**
```
=== Learnings tagged with "fastapi" ===

[learn-007] FastAPI middleware order matters
  Category: gotchas
  Tags: fastapi, cors, middleware
  Session: 5
  Captured: 2025-10-11 16:12:08

  FastAPI middleware executes in reverse order of registration.

[learn-018] Use Depends() for dependency injection
  Category: best_practices
  Tags: fastapi, dependencies, patterns
  Session: 9
  Captured: 2025-10-12 08:22:11

  Use Depends() for dependency injection in FastAPI instead of
  manual parameter passing. Cleaner code and better testability.

[learn-025] FastAPI background tasks for async work
  Category: architecture_patterns
  Tags: fastapi, async, background
  Session: 13
  Captured: 2025-10-13 14:18:33

  Use BackgroundTasks for fire-and-forget async work in FastAPI
  endpoints. Don't block response for non-critical operations.

... 2 more fastapi learnings ...

Total: 5 learnings with tag "fastapi"
```

### Example 4: Filter by Session

```bash
/sdd:learn-show --session 5
```

**Output:**
```
=== Learnings from Session 5 ===

[learn-007] FastAPI middleware order matters
  Category: gotchas
  Tags: fastapi, cors, middleware
  Captured: 2025-10-11 16:12:08

  FastAPI middleware executes in reverse order of registration.

[learn-008] CORS preflight requests require OPTIONS method
  Category: security
  Tags: cors, security, http
  Captured: 2025-10-11 16:45:20

  Browser sends OPTIONS preflight request before actual request
  when making cross-origin requests. Server must handle OPTIONS.

[learn-009] CORSMiddleware configuration for production
  Category: security
  Tags: cors, security, fastapi
  Captured: 2025-10-11 17:02:15

  Never use allow_origins=["*"] in production. Specify exact
  origins or use environment-based configuration.

Total: 3 learnings from session 5
```

### Example 5: Combine Filters

```bash
/sdd:learn-show --category gotchas --tag fastapi
```

**Output:**
```
=== Gotchas tagged with "fastapi" ===

[learn-007] FastAPI middleware order matters
  Tags: fastapi, cors, middleware
  Session: 5
  Captured: 2025-10-11 16:12:08

  FastAPI middleware executes in reverse order of registration.

[learn-029] FastAPI path parameter validation gotcha
  Tags: fastapi, validation, pydantic
  Session: 14
  Captured: 2025-10-13 11:28:45

  Path parameters are always strings. Use Pydantic Path() for
  automatic type conversion and validation.

Total: 2 gotchas with tag "fastapi"
```

### Example 6: No Results

```bash
/sdd:learn-show --category gotchas --tag kubernetes
```

**Output:**
```
No learnings found matching your filters.

Applied filters:
  Category: gotchas
  Tag: kubernetes

Suggestions:
  - Remove a filter to see more results
  - Try /sdd:learn-show --tag kubernetes (all categories)
  - Try /sdd:learn-show --category gotchas (all tags)
  - Try /sdd:learn-search kubernetes (full-text search)
  - Capture a new learning: /sdd:learn
```

## Learning Statistics

When showing all learnings (no filters), statistics are displayed:

```bash
/sdd:learn-show
```

**Output:**
```
=== Learning Statistics ===

Total Learnings: 42
Active Learnings: 42
Archived Learnings: 3

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
  - Average per session: 1.6 learnings

Last Curation: 2025-10-13 09:15:22 (2 sessions ago)

=== All Learnings ===

... displays all learnings grouped by category ...
```

## Use Cases

### Review What You've Learned

```bash
# After several sessions, review insights
/sdd:learn-show
```

### Find Category-Specific Insights

```bash
# Before refactoring, review technical debt
/sdd:learn-show --category technical_debt

# Before optimizing, review performance insights
/sdd:learn-show --category performance_insights

# Before deploying, review security learnings
/sdd:learn-show --category security
```

### Technology-Specific Review

```bash
# Before working on FastAPI feature
/sdd:learn-show --tag fastapi

# Before writing tests
/sdd:learn-show --tag testing

# Before database changes
/sdd:learn-show --tag database
```

### Session Retrospective

```bash
# Review what was learned in a specific session
/sdd:learn-show --session 12

# Compare learnings from recent sessions
/sdd:learn-show --session 20
/sdd:learn-show --session 21
/sdd:learn-show --session 22
```

## Integration with Other Commands

### Before Starting Work

```bash
# Review relevant learnings before starting
/sdd:learn-show --tag authentication
/sdd:start feature_auth
```

### After Capturing Learnings

```bash
/sdd:learn                          # Capture learnings
/sdd:learn-show --session 15        # Verify they were captured
/sdd:learn-show --category gotchas  # See in context
```

### With Search

```bash
# Broad search, then focused browsing
/sdd:learn-search "middleware"
/sdd:learn-show --tag middleware    # More structured view
```

### Before Curation

```bash
# Check current state before curating
/sdd:learn-show
/sdd:learn-curate --dry-run
/sdd:learn-curate
/sdd:learn-show                     # Verify curation results
```

## Quick Actions

Common browsing patterns:

```bash
# Quick category views
/sdd:learn-show --category gotchas
/sdd:learn-show --category best_practices
/sdd:learn-show --category security

# Recent learnings
/sdd:learn-show --session $(cat .session/tracking/status_update.json | jq -r '.session_number')

# Technology reviews
/sdd:learn-show --tag python
/sdd:learn-show --tag fastapi
/sdd:learn-show --tag react
/sdd:learn-show --tag typescript
```

## Performance

The command is optimized for:
- Fast JSON reading from `.session/tracking/learnings.json`
- Efficient filtering without full scan
- Category-based indexing
- Instant response even with hundreds of learnings

## See Also

- [Learn Command](learn.md) - Capture new learnings
- [Learn Search Command](learn-search.md) - Full-text search across learnings
- [Learn Curate Command](learn-curate.md) - Run curation process
- [Start Command](start.md) - Relevant learnings shown in session briefing
