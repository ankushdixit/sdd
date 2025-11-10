# Learn Search Command

**Usage:** `/sk:learn-search <query>`

**Description:** Full-text search across all learning content, tags, and context with relevance ranking.

## Overview

The `learn-search` command performs case-insensitive full-text search across your entire learning database. Results are ranked by relevance and display matched text for easy scanning.

**Key features:**
- Searches learning content, tags, context, and categories
- Relevance-based ranking
- Highlighted matched text
- Supports single words, phrases, and multi-word queries
- Case-insensitive matching
- Quick integration with filtered browsing

## Arguments

### `<query>` (Required)

The search query - can be:
- **Single word**: `CORS`, `pytest`, `performance`
- **Multiple words**: `FastAPI middleware`, `database optimization`
- **Phrases**: `"middleware order matters"` (use quotes for exact phrases)

## Search Scope

The search looks for matches in (ordered by weight):

1. **Learning content** (main text) - Highest weight
2. **Tags** - High weight (exact tag matches score higher)
3. **Context/notes** - Medium weight
4. **Category names** - Low weight

## Relevance Indicators

Results show relevance with star ratings:
- `★★★` - Exact match in tags or very high relevance
- `★★☆` - Match in learning content
- `★☆☆` - Match in context or category

## Output Format

Search results are displayed with relevance ranking and match highlighting:

```
=== Search Results for "cors" ===

Found 5 learnings:

[learn-007] ★★★ Exact match in tags
FastAPI middleware order matters
  Category: gotchas
  Tags: fastapi, cors, middleware
              ^^^^
  Session: 5
  Captured: 2025-10-11 16:12:08

  FastAPI middleware executes in reverse order of registration.
  app.add_middleware(CORSMiddleware) must be added in reverse order.
                     ^^^^^^^^^^^^^^

[learn-008] ★★☆ Match in content
CORS preflight requests require OPTIONS method
^^^^
  Category: security
  Tags: http, security, browser
  Session: 5

  Browser sends OPTIONS preflight request before actual request when
  making cross-origin requests. Server must handle OPTIONS for CORS.
                                                                 ^^^^

[learn-023] ★☆☆ Match in context
API Gateway configuration
  Category: architecture_patterns
  Tags: api, gateway, architecture
  Session: 12
  Context: Related to CORS setup in gateway layer
                       ^^^^

  Use API Gateway pattern for centralized request handling...

Total: 5 learnings found
```

## Examples

### Example 1: Single Word Search

```bash
/sk:learn-search pytest
```

**Output:**
```
=== Search Results for "pytest" ===

Found 7 learnings:

[learn-012] ★★★ Exact match in tags
pytest fixture scope gotcha
^^^^^^
  Category: gotchas
  Tags: pytest, testing, fixtures
        ^^^^^^
  Session: 7
  Captured: 2025-10-11 18:34:22

  pytest.fixture(scope='session') persists across all tests in file.
  ^^^^^^
  Use scope='function' for test isolation.

[learn-019] ★★☆ Match in content
Mocking external APIs in tests
  Category: best_practices
  Tags: testing, mocking, api
  Session: 10

  Use pytest-mock for cleaner test mocking. Avoid manual mock setup.
       ^^^^^^^^^^

[learn-024] ★★☆ Match in content
Parametrized testing for better coverage
  Category: best_practices
  Tags: testing, pytest, parametrize
                 ^^^^^^
  Session: 13

  Use pytest.mark.parametrize to test multiple inputs efficiently.
       ^^^^^^

... 4 more results ...

Total: 7 learnings found
```

### Example 2: Multi-Word Search

```bash
/sk:learn-search fastapi middleware
```

**Output:**
```
=== Search Results for "fastapi middleware" ===

Found 3 learnings:

[learn-007] ★★★ Match in tags and content
FastAPI middleware order matters
^^^^^^^  ^^^^^^^^^^
  Category: gotchas
  Tags: fastapi, cors, middleware
         ^^^^^^^       ^^^^^^^^^^
  Session: 5

  FastAPI middleware executes in reverse order of registration.
  ^^^^^^^  ^^^^^^^^^^

[learn-021] ★★☆ Match in content
Custom middleware for request logging
       ^^^^^^^^^^
  Category: architecture_patterns
  Tags: logging, middleware, fastapi
                 ^^^^^^^^^^  ^^^^^^^
  Session: 11

  Create custom FastAPI middleware for structured logging...
                  ^^^^^^^  ^^^^^^^^^^

[learn-034] ★☆☆ Match in context
Authentication flow implementation
  Category: security
  Tags: auth, security
  Session: 15
  Context: Uses FastAPI middleware for token validation
                 ^^^^^^^  ^^^^^^^^^^

  Implement JWT token validation in authentication middleware...

Total: 3 learnings found
```

### Example 3: Phrase Search

```bash
/sk:learn-search "order matters"
```

**Output:**
```
=== Search Results for "order matters" ===

Found 2 learnings:

[learn-007] ★★★ Exact phrase match
FastAPI middleware order matters
                   ^^^^^^^^^^^^^
  Category: gotchas
  Tags: fastapi, cors, middleware
  Session: 5

  FastAPI middleware executes in reverse order of registration.
  Middleware order matters - calls must be in reverse order.
             ^^^^^^^^^^^^^

[learn-029] ★★☆ Partial match
Import statement ordering in Python
                 ^^^^^^^^^^^^
  Category: best_practices
  Tags: python, imports, style
  Session: 14

  Import order matters for module initialization. Standard library
         ^^^^^^^^^^^^^
  first, then third-party, then local imports.

Total: 2 learnings found
```

### Example 4: No Results

```bash
/sk:learn-search kubernetes
```

**Output:**
```
=== Search Results for "kubernetes" ===

No learnings found matching "kubernetes"

Suggestions:
  - Try broader search terms (e.g., "container", "deployment")
  - Browse by category: /sk:learn-show --category architecture_patterns
  - View all learnings: /sk:learn-show
  - Capture this as a new learning: /sk:learn
```

### Example 5: Category-Specific Search

```bash
/sk:learn-search security
```

**Output:**
```
=== Search Results for "security" ===

Found 8 learnings:

[learn-008] ★★★ Match in category and tags
CORS preflight requests require OPTIONS method
  Category: security
            ^^^^^^^^
  Tags: cors, security, http
              ^^^^^^^^
  Session: 5

  Browser sends OPTIONS preflight for cross-origin requests.
  Always handle OPTIONS method for secure CORS configuration.

[learn-009] ★★★ Match in category and tags
CORSMiddleware configuration for production
  Category: security
            ^^^^^^^^
  Tags: cors, security, fastapi
              ^^^^^^^^
  Session: 5

  Never use allow_origins=["*"] in production. Security risk!
                                                ^^^^^^^^

[learn-031] ★★☆ Match in content
SQL injection prevention with parameterized queries
  Category: best_practices
  Tags: database, sql, security
                       ^^^^^^^^
  Session: 14

  Always use parameterized queries to prevent SQL injection attacks.
  Security best practice for database operations.
  ^^^^^^^^

... 5 more security-related learnings ...

Total: 8 learnings found across 3 categories
```

### Example 6: Technology Stack Search

```bash
/sk:learn-search react hooks
```

**Output:**
```
=== Search Results for "react hooks" ===

Found 6 learnings:

[learn-023] ★★★ Match in tags and content
React useCallback dependency gotcha
^^^^^
  Category: gotchas
  Tags: react, hooks, dependencies
        ^^^^^  ^^^^^
  Session: 11

  React useCallback dependencies must include all values used inside
  ^^^^^
  the callback, or you'll get stale closures.

[learn-027] ★★☆ Match in content
Custom hooks for reusable logic
       ^^^^^
  Category: best_practices
  Tags: react, hooks, patterns
        ^^^^^  ^^^^^
  Session: 12

  Extract reusable logic into custom React hooks. Better composition.
                                      ^^^^^  ^^^^^

[learn-033] ★★☆ Match in content
useState updater functions
  Category: best_practices
  Tags: react, hooks, state
        ^^^^^  ^^^^^
  Session: 15

  Use updater functions with useState to avoid stale closures in
                                          React hooks.
                                          ^^^^^  ^^^^^

... 3 more results ...

Total: 6 learnings found
```

## Search Tips

When presenting results, helpful tips are included:

```
💡 Search Tips:
- Use specific keywords for better results (e.g., "pytest fixtures" instead of "testing")
- Try tag names to find related learnings (e.g., "fastapi", "security")
- Use category names to narrow scope (e.g., "gotchas", "best_practices")
- Combine with filters: /sk:learn-show --category gotchas --tag fastapi
- Add quotes for exact phrases: /sk:learn-search "order matters"
```

## Search Statistics

When showing results, include category distribution:

```
=== Search Results for "fastapi" ===

Found 12 learnings across 4 categories:
  - best_practices: 5 learnings
  - gotchas: 4 learnings
  - architecture_patterns: 2 learnings
  - security: 1 learning

Most relevant tag combinations:
  - fastapi + middleware (3 learnings)
  - fastapi + testing (2 learnings)
  - fastapi + dependencies (2 learnings)

... search results ...
```

## Use Cases

### Quick Keyword Lookup

```bash
# Remember something about CORS
/sk:learn-search CORS

# Find pytest-related insights
/sk:learn-search pytest

# Search for performance tips
/sk:learn-search performance
```

### Problem-Specific Search

```bash
# Debugging middleware issues
/sk:learn-search middleware

# Authentication problems
/sk:learn-search authentication

# Database optimization
/sk:learn-search database optimization
```

### Technology Review

```bash
# Before working with FastAPI
/sk:learn-search FastAPI

# React development
/sk:learn-search React

# TypeScript patterns
/sk:learn-search TypeScript
```

### Pattern Discovery

```bash
# Find architectural patterns
/sk:learn-search pattern

# Security best practices
/sk:learn-search security

# Performance optimization
/sk:learn-search optimization
```

## Integration with Other Commands

### Search Then Browse

```bash
# Broad search
/sk:learn-search middleware

# Focused browsing based on search results
/sk:learn-show --tag middleware
/sk:learn-show --category gotchas --tag middleware
```

### Search Before Starting Work

```bash
# Search for relevant insights
/sk:learn-search authentication

# Review filtered results
/sk:learn-show --tag auth

# Start work with context
/sk:start feature_auth
```

### Search After Learning

```bash
# Capture new learning
/sk:learn

# Verify it's searchable
/sk:learn-search "middleware order"

# See related learnings
/sk:learn-show --category gotchas
```

## Advanced Search Patterns

### Combining Searches

```bash
# First broad search
/sk:learn-search testing

# Then narrow down
/sk:learn-search pytest fixtures

# Then very specific
/sk:learn-search "pytest fixture scope"
```

### Technology + Concept

```bash
/sk:learn-search "FastAPI dependencies"
/sk:learn-search "React state management"
/sk:learn-search "Python async patterns"
```

### Problem-Solution Searches

```bash
/sk:learn-search "CORS error"
/sk:learn-search "slow query"
/sk:learn-search "memory leak"
```

## Search Quality

### Good Queries

Specific and descriptive:
- `FastAPI middleware CORS`
- `pytest fixture scope`
- `React useCallback dependencies`
- `SQL injection prevention`

### Less Effective Queries

Too broad or generic:
- `error` (too many matches)
- `bug` (not specific enough)
- `code` (matches almost everything)
- `issue` (too vague)

## Similar Learnings Feature

After showing search results, related learnings may be suggested:

```
=== Search Results for "fastapi" ===

... search results ...

Related learnings you might find useful:
  - [learn-015] Repository pattern for data access (architecture_patterns)
  - [learn-023] API Gateway configuration (architecture_patterns)
  - [learn-031] SQL injection prevention (best_practices)
```

## Performance

The search is optimized for:
- Fast full-text search across all fields
- Relevance scoring without heavy computation
- Efficient JSON parsing
- Match highlighting with minimal overhead
- Instant response even with hundreds of learnings

## See Also

- [Learn Command](learn.md) - Capture new learnings
- [Learn Show Command](learn-show.md) - Browse with structured filters
- [Learn Curate Command](learn-curate.md) - Improve search quality through curation
- [Start Command](start.md) - Relevant learnings shown automatically
