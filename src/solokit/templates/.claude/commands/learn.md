---
description: Capture a learning during development session
---

# Learning Capture

Record insights, gotchas, and best practices discovered during development.

## Step 1: Analyze Session and Generate Learning Suggestions

Review what was accomplished in the current session:

- What code was written/changed
- What problems were solved
- What patterns or approaches were used
- What technical insights were discovered
- What gotchas or edge cases were encountered

Generate 2-3 learning suggestions based on the session work. Good learnings are:

- Specific technical insights (not generic)
- Actionable and memorable
- About tools, patterns, or gotchas encountered
- Clear and concise (1-2 sentences)

## Step 2: Ask User to Select Learnings

Use `AskUserQuestion` with multi-select to let user choose learnings:

**Question: Select Learnings from This Session**

- Question: "I've identified some potential learnings from this session. Select all that apply, or add your own:"
- Header: "Learnings"
- Multi-select: true
- Options (up to 4 total):
  - Option 1: [Your generated learning suggestion 1]
  - Option 2: [Your generated learning suggestion 2]
  - Option 3: [Your generated learning suggestion 3] (if applicable)
  - Option 4: [Your generated learning suggestion 4] (if applicable)

**Example Options:**

- "TypeScript enums are type-safe at compile time but add runtime overhead"
- "Zod schemas can be inferred as TypeScript types using z.infer<>"
- "React useCallback dependencies must include all values used inside the callback"

## Step 3: For Each Selected Learning, Determine Category

For each learning the user selected (or entered), automatically suggest the most appropriate category:

**Categories:**

- `architecture_patterns` - Design decisions, patterns used, architectural approaches
- `gotchas` - Edge cases, pitfalls, bugs discovered
- `best_practices` - Effective approaches, recommended patterns
- `technical_debt` - Areas needing improvement, refactoring needed
- `performance_insights` - Optimization learnings, performance improvements
- `security` - Security-related discoveries, vulnerabilities fixed

Use your judgment to auto-assign the category based on the learning content. You can briefly explain your categorization choice to the user.

## Step 4: Save Each Learning

For each learning selected/entered by the user:

1. Get the current session number from `.session/tracking/status_update.json`
2. Run the add-learning command:

```bash
sk learn add-learning \
  --content "{{content}}" \
  --category "{{category}}" \
  --session "{{current_session}}"
```

Replace:

- `{{content}}` with the learning content (use quotes, escape if needed)
- `{{category}}` with the auto-assigned category
- `{{current_session}}` with session number from status_update.json

**Optional flags:**

- Add `--tags "tag1,tag2"` if relevant tags can be inferred from the learning
- Add `--context "..."` if there's specific file/session context

3. After adding all learnings, display a summary:

```
✓ Captured 3 learnings:
  1. [gotchas] TypeScript enums are type-safe at compile time but add runtime overhead
  2. [best_practices] Zod schemas can be inferred as TypeScript types using z.infer<>
  3. [architecture_patterns] Repository pattern separates data access from business logic

All learnings will be auto-curated and made available in future sessions.
```

## Example Workflow

**Scenario:** User runs `/learn` after working on FastAPI CORS configuration

**Step 1:** Claude analyzes session and generates suggestions:

- "FastAPI middleware order matters for CORS - app.add_middleware() calls must be in reverse order of execution"
- "CORSMiddleware must be added after other middleware to work correctly"

**Step 2:** AskUserQuestion shows:

```
I've identified some potential learnings from this session. Select all that apply, or add your own:

☐ FastAPI middleware order matters for CORS - app.add_middleware() calls must be in reverse order of execution
☐ CORSMiddleware must be added after other middleware to work correctly
☐ Type something - Add custom learnings (one per line)
```

User selects first two options.

**Step 3:** Claude auto-categorizes:

- Learning 1 → `gotchas` (middleware ordering gotcha)
- Learning 2 → `best_practices` (correct configuration approach)

**Step 4:** Claude runs commands:

```bash
sk learn add-learning \
  --content "FastAPI middleware order matters for CORS - app.add_middleware() calls must be in reverse order of execution" \
  --category "gotchas" \
  --tags "fastapi,cors,middleware" \
  --session "5"

sk learn add-learning \
  --content "CORSMiddleware must be added after other middleware to work correctly" \
  --category "best_practices" \
  --tags "fastapi,cors,middleware" \
  --session "5"
```

**Output to user:**

```
✓ Captured 2 learnings:
  1. [gotchas] FastAPI middleware order matters for CORS - app.add_middleware() calls must be in reverse order of execution
  2. [best_practices] CORSMiddleware must be added after other middleware to work correctly

All learnings will be auto-curated and made available in future sessions.
```
