---
description: Capture a learning during development session
---

# Learning Capture

Record insights, gotchas, and best practices discovered during development.

## Usage

Ask the user for learning details conversationally:

1. **Learning Content** - Ask: "What did you learn?"
2. **Category** - Ask: "Which category best fits this learning?"
   - `architecture_patterns` - Design decisions, patterns used, architectural approaches
   - `gotchas` - Edge cases, pitfalls, bugs discovered
   - `best_practices` - Effective approaches, recommended patterns
   - `technical_debt` - Areas needing improvement, refactoring needed
   - `performance_insights` - Optimization learnings, performance improvements
   - `security` - Security-related discoveries, vulnerabilities fixed
3. **Tags** (optional) - Ask: "Any tags to help find this later? (comma-separated, or 'none')"
4. **Context** (optional) - Ask: "Any additional context? (file paths, session notes, or 'none')"

## After Collecting Information

Get the current session number from status_update.json, then run:

```bash
python3 scripts/learning_curator.py add-learning \
  --content "{{content}}" \
  --category "{{category}}" \
  --tags "{{tags}}" \
  --session "{{current_session}}" \
  --context "{{context}}"
```

Replace:
- `{{content}}` with the learning content (use quotes)
- `{{category}}` with one of the 6 categories
- `{{tags}}` with comma-separated tags (or omit if none)
- `{{current_session}}` with session number from status_update.json
- `{{context}}` with additional context (or omit if none)

Display confirmation to user showing:
- Learning ID
- Category
- Tags (if any)
- Message: "Learning captured! It will be auto-categorized and curated."

## Example

User: "I learned that FastAPI middleware order matters for CORS"

Questions:
- What did you learn? → "FastAPI middleware order matters for CORS - app.add_middleware() calls must be in reverse order of execution"
- Which category? → gotchas
- Any tags? → fastapi, cors, middleware
- Context? → Discovered in session 5 while debugging CORS issues

Command:
```bash
python3 scripts/learning_curator.py add-learning \
  --content "FastAPI middleware order matters for CORS - app.add_middleware() calls must be in reverse order of execution" \
  --category "gotchas" \
  --tags "fastapi,cors,middleware" \
  --session "5" \
  --context "Discovered while debugging CORS issues"
```
