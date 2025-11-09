# Learn Command

**Usage:** `/sdd:learn`

**Description:** Capture insights, gotchas, and best practices discovered during development with intelligent suggestions.

## Overview

The `learn` command helps you capture valuable insights from your development sessions. Instead of manually typing everything, it analyzes your current session work and suggests potential learnings for you to select.

**Key features:**
- AI-generated learning suggestions based on session work
- Multi-select interface for quick capture
- Automatic categorization
- Optional tag inference
- Immediate availability in future sessions

## Interactive Flow

### Step 1: Session Analysis

Claude reviews your current session to identify potential learnings:
- Code changes made
- Problems solved
- Patterns or approaches used
- Technical insights discovered
- Gotchas or edge cases encountered

### Step 2: Learning Selection

You're presented with 2-4 suggested learnings using an interactive multi-select question:

**Question:** "I've identified some potential learnings from this session. Select all that apply, or add your own:"

**Options:**
- Multiple AI-generated suggestions based on session work
- Option to add custom learnings

**Example suggestions:**
- "TypeScript enums are type-safe at compile time but add runtime overhead"
- "Zod schemas can be inferred as TypeScript types using z.infer<>"
- "React useCallback dependencies must include all values used inside the callback"

### Step 3: Automatic Categorization

For each selected learning, Claude automatically assigns the most appropriate category:

**Categories:**
- `architecture_patterns` - Design decisions, patterns used, architectural approaches
- `gotchas` - Edge cases, pitfalls, bugs discovered
- `best_practices` - Effective approaches, recommended patterns
- `technical_debt` - Areas needing improvement, refactoring needed
- `performance_insights` - Optimization learnings, performance improvements
- `security` - Security-related discoveries, vulnerabilities fixed

Claude explains the categorization choice briefly.

### Step 4: Save and Confirm

Each selected learning is saved with:
- Auto-assigned category
- Inferred tags (when applicable)
- Current session number
- Timestamp

A summary is displayed showing all captured learnings.

## Learning Quality Guidelines

Good learnings are:
- **Specific** - "FastAPI middleware order matters for CORS" not "Middleware is important"
- **Actionable** - Contains concrete information you can act on
- **Memorable** - Captures the "aha moment" you experienced
- **Technical** - About tools, patterns, or gotchas (not generic advice)
- **Concise** - Clear and direct (1-2 sentences)

## Examples

### Example 1: FastAPI CORS Configuration Session

**Context:** User just worked on FastAPI CORS configuration

**User runs:**
```bash
/sdd:learn
```

**Claude analyzes and presents:**
```
I've identified some potential learnings from this session. Select all that apply, or add your own:

☐ FastAPI middleware order matters for CORS - app.add_middleware() calls must be in reverse order of execution
☐ CORSMiddleware must be added after other middleware to work correctly
☐ Type something - Add custom learnings (one per line)
```

**User selects:** Both options

**Claude categorizes and saves:**
```
Auto-categorizing selections:
  1. Learning 1 → gotchas (middleware ordering gotcha)
  2. Learning 2 → best_practices (correct configuration approach)

Adding tags: fastapi, cors, middleware
Saving to session 5...

✓ Captured 2 learnings:
  1. [gotchas] FastAPI middleware order matters for CORS - app.add_middleware() calls must be in reverse order of execution
  2. [best_practices] CORSMiddleware must be added after other middleware to work correctly

All learnings will be auto-curated and made available in future sessions.
```

### Example 2: React Component Development

**User runs:**
```bash
/sdd:learn
```

**Claude presents:**
```
I've identified some potential learnings from this session. Select all that apply, or add your own:

☐ React useCallback dependencies must include all values used inside the callback
☐ Memoization with useMemo helps prevent expensive recalculations
☐ useState setter functions can accept updater functions to avoid stale closures
☐ Type something - Add custom learnings (one per line)
```

**User selects:** First and third options, plus adds custom: "PropTypes are deprecated in favor of TypeScript"

**Claude processes:**
```
Auto-categorizing selections:
  1. Learning 1 → gotchas (dependency array gotcha)
  2. Learning 2 → best_practices (avoiding stale closures)
  3. Custom learning → best_practices (TypeScript recommendation)

Adding tags: react, hooks, typescript
Saving to session 12...

✓ Captured 3 learnings:
  1. [gotchas] React useCallback dependencies must include all values used inside the callback
  2. [best_practices] useState setter functions can accept updater functions to avoid stale closures
  3. [best_practices] PropTypes are deprecated in favor of TypeScript

All learnings will be auto-curated and made available in future sessions.
```

### Example 3: No Session Work Yet

**User runs:**
```bash
/sdd:learn
```

**Claude responds:**
```
I don't see any significant code changes or problem-solving in the current session yet.

Would you like to:
1. Add a custom learning anyway? I can help categorize it.
2. Continue working and capture learnings later when you've made more progress.

What learning would you like to capture?
```

**User types:** "pytest-asyncio fixtures must use async def, not regular def"

**Claude processes:**
```
Auto-categorizing: gotchas (common async fixture mistake)
Adding tags: pytest, async, fixtures
Saving to session 8...

✓ Captured 1 learning:
  1. [gotchas] pytest-asyncio fixtures must use async def, not regular def

Learning will be auto-curated and made available in future sessions.
```

## How Learnings Are Used

### During Sessions

When you start a work item with `/sdd:start`, relevant learnings are automatically surfaced in the briefing:

```
=== RELEVANT LEARNINGS ===

From previous sessions:
  [gotchas] FastAPI middleware order matters for CORS
  [best_practices] Use Zod for API validation instead of manual checks
  [security] Always validate CORS origins - don't use allow_origins=["*"] in production
```

### Manual Browsing

Browse all learnings anytime:
```bash
/sdd:learn-show                    # All learnings
/sdd:learn-show --category gotchas # Only gotchas
/sdd:learn-show --tag fastapi      # FastAPI-related
```

### Search

Search across all learnings:
```bash
/sdd:learn-search "CORS"
/sdd:learn-search "middleware order"
```

### Auto-Curation

Learnings are automatically curated to:
- Ensure proper categorization
- Merge duplicates
- Archive old learnings
- Maintain quality

## Implementation Details

When you select learnings, the command:

1. Gets current session number from `.session/tracking/status_update.json`
2. For each learning, runs:
```bash
sdd learn add-learning \
  --content "{{content}}" \
  --category "{{category}}" \
  --session "{{current_session}}" \
  --tags "{{inferred_tags}}" \
  --context "{{optional_context}}"
```

3. Stores in `.session/tracking/learnings.json`
4. Makes immediately available for future sessions

## Tips for Effective Learning Capture

### 1. Capture During Session

Capture learnings while they're fresh:
```bash
# After solving a tricky bug
/sdd:learn

# After discovering a better pattern
/sdd:learn

# Before ending session
/sdd:learn
```

### 2. Be Specific

**Good:**
- "Zod schemas can be inferred as TypeScript types using z.infer<>"
- "pytest.fixture(scope='session') persists across all tests, use scope='function' for isolation"

**Too Vague:**
- "TypeScript is useful"
- "Testing is important"

### 3. Include Context

Add context when it helps:
- "Found while debugging src/auth/jwt.ts:42"
- "Related to work item feature_authentication"
- "Discovered during production incident investigation"

### 4. Don't Overthink

The AI suggestions make it easy - just select what resonates. You can always:
- Add custom learnings
- Skip suggestions that aren't useful
- Come back later with `/sdd:learn`

## When to Capture Learnings

**Ideal times:**
- After solving a difficult bug
- When discovering a better approach
- After reading documentation and trying something new
- When encountering an edge case
- Before ending a session (while context is fresh)

**Not necessary:**
- For every small code change
- For well-known patterns you already use
- For simple corrections

## Integration with Other Commands

### Session Workflow

```bash
/sdd:start feature_auth    # Relevant learnings shown in briefing
# ... work on feature ...
/sdd:learn                 # Capture new insights
# ... more work ...
/sdd:learn                 # Capture more insights
/sdd:end                   # Session complete
```

### Learning Management

```bash
/sdd:learn                           # Capture learnings
/sdd:learn-show                      # Browse all
/sdd:learn-show --category gotchas   # Filter by category
/sdd:learn-search "FastAPI"          # Search
/sdd:learn-curate                    # Manual curation
```

## See Also

- [Learn Show Command](learn-show.md) - Browse and filter learnings
- [Learn Search Command](learn-search.md) - Search across learnings
- [Learn Curate Command](learn-curate.md) - Run curation process
- [Start Command](start.md) - Learnings appear in session briefing
- [End Command](end.md) - Alternative learning capture via commit messages
