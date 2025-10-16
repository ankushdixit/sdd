# Learning Search Command

**Usage:** `/sdd:learn-search <query>`

**Description:** Full-text search across all learning content, tags, and context.

**Behavior:**

Performs case-insensitive search across all learnings to find matches in content, tags, context, and category names. Returns ranked results with relevance indicators.

## Arguments

### `<query>` (Required)
The search query - can be:
- Single word: `CORS`, `pytest`, `performance`
- Multiple words: `FastAPI middleware`, `database optimization`
- Phrases: `"middleware order matters"` (use quotes for exact phrases)

## Search Scope

The search looks for matches in:
1. **Learning content** (main text) - weighted highest
2. **Tags** - weighted high (exact tag matches score higher)
3. **Context/notes** - weighted medium
4. **Category names** - weighted low

## Execution

Extract the query from `$ARGUMENTS` and execute:

```bash
python3 scripts/learning_curator.py search "{{query}}"
```

Replace `{{query}}` with the user's search terms (preserve quotes if provided).

## Output Format

Results are displayed with relevance ranking:

```
=== Search Results for "cors" ===

Found 5 learnings:

[learn-007] ★★★ Exact match in tags
FastAPI middleware order matters
  Category: gotchas
  Tags: fastapi, cors, middleware
  Session: 5
  Captured: 2025-10-11 16:12:08

  FastAPI middleware executes in reverse order of registration.
  app.add_middleware(CORSMiddleware) must be added in reverse order.
  ^^^^^^^^^ matched text ^^^^^^^^^

[learn-008] ★★☆ Match in content
CORS preflight requests require OPTIONS method
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

  Use API Gateway pattern for centralized request handling...
```

Relevance indicators:
- `★★★` - Exact match in tags or high relevance
- `★★☆` - Match in content
- `★☆☆` - Match in context or category

## Examples

### Example 1: Single Word Search

```
User: /sdd:learn-search pytest

Claude: [Executes: python3 scripts/learning_curator.py search "pytest"]

=== Search Results for "pytest" ===

Found 7 learnings:

[learn-012] ★★★ Exact match in tags
pytest fixture scope gotcha
  Category: gotchas
  Tags: pytest, testing, fixtures
  Session: 7

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

... 5 more results ...

Total: 7 learnings found
```

### Example 2: Multi-Word Search

```
User: /sdd:learn-search fastapi middleware

Claude: [Executes: python3 scripts/learning_curator.py search "fastapi middleware"]

=== Search Results for "fastapi middleware" ===

Found 3 learnings:

[learn-007] ★★★ Match in tags and content
FastAPI middleware order matters
  Category: gotchas
  Tags: fastapi, cors, middleware
         ^^^^^^^       ^^^^^^^^^^
  Session: 5

  FastAPI middleware executes in reverse order of registration.
  ^^^^^^^  ^^^^^^^^^^

[learn-021] ★★☆ Match in content
Custom middleware for request logging
  Category: architecture_patterns
  Tags: logging, middleware, fastapi
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

Total: 3 learnings found
```

### Example 3: No Results

```
User: /sdd:learn-search kubernetes

Claude: [Executes: python3 scripts/learning_curator.py search "kubernetes"]

=== Search Results for "kubernetes" ===

No learnings found matching "kubernetes"

Suggestions:
- Try broader search terms (e.g., "container", "deployment")
- Browse by category: /sdd:learn-show --category architecture_patterns
- View all learnings: /sdd:learn-show
- Capture this as a new learning: /sdd:learn
```

### Example 4: Phrase Search

```
User: /sdd:learn-search "order matters"

Claude: [Executes: python3 scripts/learning_curator.py search "order matters"]

=== Search Results for "order matters" ===

Found 2 learnings:

[learn-007] ★★★ Exact phrase match
FastAPI middleware order matters
  Category: gotchas
  Tags: fastapi, cors, middleware
  Session: 5

  FastAPI middleware executes in reverse order of registration.
  Middleware order matters - calls must be in reverse order.
            ^^^^^^^^^^^^^

[learn-029] ★★☆ Partial match
Import statement ordering in Python
  Category: best_practices
  Tags: python, imports, style
  Session: 14

  Import order matters for module initialization. Standard library
         ^^^^^^^^^^^^
  first, then third-party, then local imports.

Total: 2 learnings found
```

## Search Tips

When presenting results, include helpful tips:

```
💡 Search Tips:
- Use specific keywords for better results (e.g., "pytest fixtures" instead of "testing")
- Try tag names to find related learnings (e.g., "fastapi", "security")
- Use category names to narrow scope (e.g., "gotchas", "best_practices")
- Combine with filters: /sdd:learn-show --category gotchas --tag fastapi
- Add quotes for exact phrases: /sdd:learn-search "order matters"
```

## Related Commands

- `/sdd:learn-show [--category] [--tag] [--session]` - Browse with filters
- `/sdd:learn` - Capture a new learning
- `/sdd:learn-curate` - Run curation to improve search results

## Advanced Features

### Search Statistics

When showing results, include statistics:

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
```

### Similar Learnings

After showing search results, suggest similar/related learnings:

```
Related learnings you might find useful:
  - [learn-015] Repository pattern for data access (architecture_patterns)
  - [learn-023] API Gateway configuration (architecture_patterns)
```

## Implementation

**Script:** `scripts/learning_curator.py`
**Subcommand:** `search`
**Database:** `.session/tracking/learnings.json`
**Algorithm:** Case-insensitive substring matching with relevance scoring based on match location (tags > content > context)
