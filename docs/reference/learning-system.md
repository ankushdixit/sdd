# Learning System

Automated knowledge capture and curation for Claude Code sessions.

## Overview

The learning system automatically captures, categorizes, and organizes insights discovered during development. It helps build an organic knowledge base that grows with your project.

**Key Features:**
- Conversational learning capture during sessions
- AI-powered categorization into 6 types
- Automatic duplicate detection and merging
- Multi-source extraction (session summaries, git commits, inline comments)
- Advanced filtering and search
- Statistics dashboard and timeline views

## Learning Categories

Learnings are automatically categorized into 6 types:

### 1. Architecture Patterns
Design decisions, patterns used, architectural approaches.

**Examples:**
- "Using Repository Pattern for all database access ensures testability"
- "Event-driven architecture chosen for microservice communication"
- "CQRS pattern separates read and write models for better scalability"

### 2. Gotchas
Edge cases, pitfalls, bugs discovered, things that went wrong.

**Examples:**
- "FastAPI middleware order matters for CORS - add_middleware calls in reverse order"
- "SQLAlchemy lazy loading causes N+1 queries - use joinedload()"
- "React useEffect with missing dependencies causes stale closures"

### 3. Best Practices
Effective approaches identified, recommended patterns.

**Examples:**
- "Always use environment variables for secrets, never hardcode"
- "Write integration tests for API endpoints, not just unit tests"
- "Use type hints in Python for better IDE support and fewer bugs"

### 4. Technical Debt
Areas needing improvement, refactoring needed, temporary solutions.

**Examples:**
- "Authentication module needs refactoring - currently too tightly coupled"
- "Database migrations not versioned properly, should use Alembic"
- "Error handling is inconsistent across API endpoints"

### 5. Performance Insights
Optimization learnings, performance improvements.

**Examples:**
- "Database query optimization reduced API response time from 2s to 200ms"
- "Redis caching for frequently accessed data cut database load by 60%"
- "Debouncing search input prevents excessive API calls"

### 6. Security
Security-related discoveries, vulnerabilities fixed.

**Examples:**
- "SQL injection vulnerability fixed by using parameterized queries"
- "JWT tokens should expire after 1 hour to reduce attack window"
- "Input validation on API endpoints prevents XSS attacks"

## Commands

### `/sdd:learn` - Capture a Learning

Capture a learning discovered during development.

**Usage:**
```
/sdd:learn
```

Claude will ask:
1. What did you learn?
2. Which category? (architecture_patterns, gotchas, best_practices, technical_debt, performance_insights, security)
3. Any tags? (optional, comma-separated)
4. Any additional context? (optional)

**Example:**
```
You: /sdd:learn
Claude: What did you learn?
You: FastAPI middleware order matters for CORS - add_middleware calls must be in reverse order
Claude: Which category best fits this learning?
You: gotchas
Claude: Any tags to help find this later?
You: fastapi,cors,middleware
Claude: Any additional context?
You: Discovered while debugging CORS issues in session 5

✓ Learning captured!
  ID: 670b4de7
  Category: gotchas
  Tags: fastapi, cors, middleware

It will be auto-categorized and curated.
```

### `/sdd:learn-show` - Browse Learnings

View captured learnings with optional filtering.

**Usage:**
```
/sdd:learn-show [--category CATEGORY] [--tag TAG] [--session SESSION]
```

**Examples:**

Show all learnings:
```
/sdd:learn-show
```

Show only gotchas:
```
/sdd:learn-show --category gotchas
```

Show learnings tagged with "fastapi":
```
/sdd:learn-show --tag fastapi
```

Show learnings from session 5:
```
/sdd:learn-show --session 5
```

Combine filters:
```
/sdd:learn-show --category gotchas --tag fastapi
```

### `/sdd:learn-search` - Search Learnings

Full-text search across all learning content, tags, and context.

**Usage:**
```
/sdd:learn-search <query>
```

**Examples:**
```
/sdd:learn-search CORS
/sdd:learn-search "middleware order"
/sdd:learn-search authentication
```

### `/sdd:learn-curate` - Manual Curation

Run the curation process manually to categorize, detect duplicates, and merge similar learnings.

**Usage:**
```
/sdd:learn-curate [--dry-run]
```

**Dry-run mode** (preview only, no changes saved):
```
/sdd:learn-curate --dry-run
```

**Normal mode** (save changes):
```
/sdd:learn-curate
```

**What curation does:**
1. Categorizes uncategorized learnings using AI-powered keyword analysis
2. Detects duplicates using Jaccard and containment similarity algorithms
3. Merges similar learnings to reduce redundancy
4. Archives old learnings (older than 50 sessions)
5. Updates metadata (last_curated timestamp)

## Automatic Curation

Curation runs automatically every N sessions (configurable in `.session/config.json`).

**Note:** The config.json file is automatically created when you run `/sdd:init` to initialize the project.

**Configuration:**
```json
{
  "curation": {
    "auto_curate": true,
    "frequency": 5,
    "dry_run": false,
    "similarity_threshold": 0.7
  }
}
```

**Options:**
- `auto_curate`: Enable/disable automatic curation (default: true)
- `frequency`: Run curation every N sessions (default: 5)
- `dry_run`: Preview mode, don't save changes (default: false)
- `similarity_threshold`: Similarity threshold for duplicate detection (default: 0.7)

## Learning Extraction

Learnings are automatically extracted from multiple sources:

### 1. Session Summaries
Extracts learnings from "Challenges Encountered" and "Learnings Captured" sections in session summary files.

**Example:**
```markdown
## Challenges Encountered
- FastAPI middleware order matters for CORS
- SQLAlchemy lazy loading caused N+1 queries
```

Both bullet points are automatically extracted as learnings.

### 2. Git Commit Messages
Extracts `LEARNING:` annotations from commit messages.

**Example:**
```bash
git commit -m "Fix CORS issue

LEARNING: FastAPI middleware order matters for CORS - add_middleware calls must be in reverse order

🤖 Generated with Claude Code"
```

The LEARNING annotation is automatically extracted.

### 3. Inline Code Comments
Extracts `# LEARNING:` comments from recently changed files.

**Example (Python):**
```python
# LEARNING: Always use parameterized queries to prevent SQL injection
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
```

The learning is automatically extracted from the code comment.

## Similarity Detection

The system uses two algorithms to detect duplicate learnings:

### Jaccard Similarity
Measures word overlap between two learnings.

**Formula:** `similarity = |A ∩ B| / |A ∪ B|`

**Threshold:** 0.6 (configurable)

**Example:**
- Learning A: "FastAPI middleware order matters for CORS"
- Learning B: "CORS middleware in FastAPI must be added in reverse order"
- Similarity: ~0.7 (high overlap) → Merged

### Containment Similarity
Checks if one learning is a substring of another.

**Formula:** `containment = |A ∩ B| / min(|A|, |B|)`

**Threshold:** 0.8

**Example:**
- Learning A: "FastAPI middleware order matters"
- Learning B: "FastAPI middleware order matters for CORS"
- Containment: 1.0 (A is contained in B) → Merged

### Stopword Removal
Common words (the, and, or, is, are, etc.) are removed before comparison to focus on meaningful keywords.

## Advanced Features

### Statistics Dashboard

View learning statistics with `python3 scripts/learning_curator.py statistics`:

```
=== Learning Statistics ===

Total learnings: 45

By Category:
----------------------------------------
  Architecture Patterns              12
  Gotchas                           15
  Best Practices                    10
  Technical Debt                     5
  Performance Insights               3
  Security                           0

Top Tags:
----------------------------------------
  fastapi                           20
  python                            15
  database                          10
  authentication                     8
  testing                            7

Sessions with Most Learnings:
----------------------------------------
  Session 5                          8
  Session 12                         7
  Session 8                          6
```

### Timeline View

View learning history by session with `python3 scripts/learning_curator.py timeline`:

```
=== Learning Timeline (Last 10 Sessions) ===

Session 012: 7 learning(s)
  - Redis caching reduced database load by 60%
  - JWT tokens should expire after 1 hour
  - Input validation prevents XSS attacks
  ... and 4 more

Session 011: 3 learning(s)
  - Database query optimization reduced response time
  - Use joinedload() to prevent N+1 queries
  - Always use environment variables for secrets

Session 010: 5 learning(s)
  - FastAPI middleware order matters for CORS
  - SQLAlchemy lazy loading causes issues
  - Write integration tests for API endpoints
  ... and 2 more
```

### Related Learnings

Find similar learnings using `curator.get_related_learnings(learning_id)`:

```python
from scripts.learning_curator import LearningsCurator

curator = LearningsCurator()
related = curator.get_related_learnings("670b4de7", limit=5)

for learning in related:
    print(f"- {learning['content']}")
    print(f"  Category: {learning['category']}")
    print(f"  Similarity: {learning.get('similarity_score', 'N/A')}%")
```

## Workflows

### Workflow 1: Capturing Learnings During Development

1. Work on a feature/fix
2. Discover something worth remembering
3. Use `/sdd:learn` to record it
4. Claude asks questions conversationally
5. Learning is saved and will be auto-curated

### Workflow 2: Browsing Learnings

1. Use `/sdd:learn-show` to see all learnings
2. Filter by category: `/sdd:learn-show --category gotchas`
3. Filter by tag: `/sdd:learn-show --tag fastapi`
4. Search for specific content: `/sdd:learn-search CORS`

### Workflow 3: Automatic Extraction

1. Complete a session with `/sdd:end`
2. System auto-extracts learnings from:
   - Session summary (Challenges section)
   - Git commit messages (LEARNING: annotations)
   - Inline code comments (# LEARNING:)
3. Extracted learnings are automatically categorized
4. Duplicates are skipped

### Workflow 4: Curation

1. Capture learnings throughout multiple sessions
2. Every 5 sessions, auto-curation runs
3. Curation categorizes, detects duplicates, and merges similar learnings
4. Manual curation: `/sdd:learn-curate` or `/sdd:learn-curate --dry-run`

## Best Practices

### Capture Learnings Immediately
Capture learnings as soon as you discover them, while the context is fresh.

### Use Descriptive Tags
Tags help you find learnings later. Use specific tags like "fastapi", "cors", "authentication" rather than generic "bug", "issue".

### Add Context
Include file paths, session numbers, or brief notes in the context field. This helps you remember where the learning came from.

### Review Learnings Regularly
Use `/sdd:learn-show` to review captured learnings periodically. This reinforces knowledge retention.

### Use LEARNING Annotations
Add `LEARNING:` annotations in git commit messages and `# LEARNING:` comments in code for automatic extraction.

### Run Curation Periodically
Curation keeps your knowledge base organized. Run it manually with `/sdd:learn-curate` or let it run automatically every N sessions.

## Troubleshooting

### Curation Not Running Automatically
Check `.session/config.json`:
```json
{
  "curation": {
    "auto_curate": true,
    "frequency": 5
  }
}
```

Ensure `auto_curate` is `true` and `frequency` is set.

### Duplicates Not Being Merged
The similarity threshold may be too high. Adjust in `.session/config.json`:
```json
{
  "curation": {
    "similarity_threshold": 0.6
  }
}
```

Lower values (0.5-0.6) detect more duplicates, higher values (0.7-0.8) are more conservative.

### Extraction Not Finding Learnings
- **Session summaries:** Ensure summaries have "## Challenges Encountered" or "## Learnings Captured" sections
- **Git commits:** Use exact format: `LEARNING: <your learning text>`
- **Code comments:** Use exact format: `# LEARNING: <your learning text>`

### Learnings File Corrupted
The learnings file is at `.session/tracking/learnings.json`. If corrupted, you can reset it:
```bash
rm .session/tracking/learnings.json
python3 scripts/learning_curator.py curate
```

This creates a fresh learnings file.

## Data Storage

Learnings are stored in `.session/tracking/learnings.json`:

```json
{
  "last_curated": "2025-10-13T22:30:00",
  "curator": "session_curator",
  "categories": {
    "gotchas": [
      {
        "id": "670b4de7",
        "content": "FastAPI middleware order matters for CORS",
        "timestamp": "2025-10-13T22:47:07.683518",
        "learned_in": "session_001",
        "tags": ["fastapi", "cors", "middleware"],
        "context": "Discovered while debugging CORS issues"
      }
    ],
    "architecture_patterns": [],
    "best_practices": [],
    "technical_debt": [],
    "performance_insights": [],
    "security": []
  },
  "archived": []
}
```

## Integration with Session Workflow

The learning system is fully integrated with the session workflow:

1. **Session Start**: Load existing learnings for context
2. **During Session**: Capture learnings with `/sdd:learn`
3. **Session End**:
   - Auto-extract learnings from session summary, git commits, code comments
   - Auto-curate every N sessions
   - Manual learning capture
4. **Between Sessions**: Browse, search, review learnings

## Command Line Interface

All learning commands are also available via CLI:

```bash
# Add a learning
python3 scripts/learning_curator.py add-learning \
  --content "Your learning here" \
  --category gotchas \
  --tags "tag1,tag2" \
  --session 5

# Show learnings
python3 scripts/learning_curator.py show-learnings \
  --category gotchas \
  --tag fastapi \
  --session 5

# Search learnings
python3 scripts/learning_curator.py search "CORS"

# Curate learnings
python3 scripts/learning_curator.py curate
python3 scripts/learning_curator.py curate --dry-run

# Statistics
python3 scripts/learning_curator.py statistics

# Timeline
python3 scripts/learning_curator.py timeline --sessions 10

# Report (legacy)
python3 scripts/learning_curator.py report
```

## Summary

The learning system helps you:
- ✅ Capture insights discovered during development
- ✅ Organize knowledge into 6 categories automatically
- ✅ Find learnings with powerful search and filtering
- ✅ Avoid duplicate learnings with similarity detection
- ✅ Extract learnings from multiple sources automatically
- ✅ Track learning growth over time with statistics and timeline
- ✅ Build an organic knowledge base that grows with your project

Start capturing learnings today with `/sdd:learn`!
