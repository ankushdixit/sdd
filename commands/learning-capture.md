# Learning Capture Command

**Usage:** `/learning-capture`

**Description:** Capture insights, gotchas, and best practices discovered during development.

**Behavior:**

This command captures learnings conversationally by asking the user for details, then adding them to the learnings database.

## Information to Collect

Ask the user for the following information in a conversational manner:

### 1. Learning Content (Required)
- Ask: "What did you learn?"
- This is the main insight, gotcha, or best practice
- Should be clear and actionable
- Examples:
  - "FastAPI middleware order matters for CORS - app.add_middleware() calls must be in reverse order of execution"
  - "pytest.fixture(scope='session') persists across all tests in file, use with caution"
  - "ruff's import sorting conflicts with isort - choose one or the other"

### 2. Category (Required)
- Ask: "Which category best fits this learning?"
- Options:
  - `architecture_patterns` - Design decisions, architectural approaches, patterns used
  - `gotchas` - Edge cases, pitfalls, bugs discovered, common mistakes
  - `best_practices` - Effective approaches, recommended patterns, proven techniques
  - `technical_debt` - Areas needing improvement, refactoring opportunities, workarounds
  - `performance_insights` - Optimization learnings, performance improvements, profiling results
  - `security` - Security-related discoveries, vulnerabilities fixed, security best practices

### 3. Tags (Optional)
- Ask: "Any tags to help find this later? (comma-separated, or 'none')"
- Examples: `fastapi,cors,middleware` or `pytest,fixtures,testing`
- Tags help with searching and filtering
- If user says "none", omit the `--tags` parameter

### 4. Context (Optional)
- Ask: "Any additional context? (file paths, related work items, session notes, or 'none')"
- Examples:
  - "Discovered in session 5 while debugging CORS issues"
  - "Related to work item feature-003"
  - "Found in src/middleware/cors.py:42"
- If user says "none", omit the `--context` parameter

## Execution

After collecting all information:

1. **Get current session number** from `.session/tracking/status_update.json`
2. **Run the learning curator script**:

```bash
python3 scripts/learning_curator.py add-learning \
  --content "{{content}}" \
  --category "{{category}}" \
  --tags "{{tags}}" \
  --session "{{session_number}}" \
  --context "{{context}}"
```

Replace placeholders:
- `{{content}}` - The learning content (always use quotes)
- `{{category}}` - One of the 6 categories
- `{{tags}}` - Comma-separated tags (omit `--tags` if none)
- `{{session_number}}` - Current session from status_update.json
- `{{context}}` - Additional context (omit `--context` if none)

3. **Display confirmation** showing:
   - Learning ID (from script output)
   - Category assigned
   - Tags (if any)
   - Message: "Learning captured! It will be included in curation."

## Examples

### Example 1: Complete Learning

```
User: /learning-capture

Claude: What did you learn?
User: FastAPI middleware order matters for CORS - add_middleware() calls execute in reverse order

Claude: Which category best fits this learning?
  - architecture_patterns
  - gotchas
  - best_practices
  - technical_debt
  - performance_insights
  - security
User: gotchas

Claude: Any tags to help find this later? (comma-separated, or 'none')
User: fastapi, cors, middleware

Claude: Any additional context? (file paths, session notes, or 'none')
User: Discovered in session 5 while debugging CORS preflight issues

[Executes: python3 scripts/learning_curator.py add-learning ...]

Claude: ✓ Learning captured!
  ID: learn-042
  Category: gotchas
  Tags: fastapi, cors, middleware

  This learning will be included in the next curation run.
```

### Example 2: Minimal Learning

```
User: /learning-capture

Claude: What did you learn?
User: Use ruff instead of black for faster formatting

Claude: Which category?
User: best_practices

Claude: Any tags? (comma-separated, or 'none')
User: none

Claude: Any context? (or 'none')
User: none

[Executes: python3 scripts/learning_curator.py add-learning --content "Use ruff instead of black for faster formatting" --category "best_practices" --session "3"]

Claude: ✓ Learning captured!
  ID: learn-043
  Category: best_practices

  This learning will be included in the next curation run.
```

## Integration

This command integrates with:
- **Learning Curation System** - Learnings are auto-categorized and deduplicated during curation
- **Session Workflow** - Session number is tracked for each learning
- **Search & Browse** - Learnings can be found via `/learning-search` and `/learning-show`

## Related Commands

- `/learning-show` - Browse learnings with filters
- `/learning-search` - Full-text search across learnings
- `/learning-curate` - Run curation process (categorize, deduplicate, merge)

## Implementation

**Script:** `scripts/learning_curator.py`
**Subcommand:** `add-learning`
**Database:** `.session/tracking/learnings.json`
