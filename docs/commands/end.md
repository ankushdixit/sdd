# End Command

**Usage:** `/sk:end`

**Description:** Complete the current development session with quality gates, commit validation, and learning capture.

## Overview

The `end` command completes a development session by:
- Capturing learnings from the work done
- Running quality gates (tests, linting, type checking)
- Validating all changes are committed
- Asking about work item completion status
- Updating project context files
- Generating session summary

## Before Ending: Capture Learnings

Before completing the session, you should capture 2-5 key learnings from the work done. You have two options:

### Option A: Commit Message LEARNING Tags (Recommended)

Include `LEARNING:` annotations in your commit messages. These will be automatically extracted during session completion:

```bash
git commit -m "Implement calculator add function

Added TypeScript add function with comprehensive tests.

LEARNING: TypeScript number type handles both integers and decimals seamlessly

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>"
```

**Multiple learnings in one commit:**
```bash
git commit -m "Add user authentication system

Implemented JWT-based authentication with refresh tokens.

LEARNING: JWT refresh tokens should have shorter expiry than access tokens
LEARNING: Always validate tokens on server-side, never trust client
LEARNING: Use httpOnly cookies for storing refresh tokens to prevent XSS

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Option B: Temporary Learnings File

Write learnings to `.session/temp_learnings.txt` (one per line):

```bash
cat > .session/temp_learnings.txt << 'EOF'
TypeScript number type handles both integers and decimals seamlessly
JWT refresh tokens should have shorter expiry than access tokens
Use httpOnly cookies for storing refresh tokens to prevent XSS
EOF
```

### What Makes a Good Learning?

- **Technical insights** discovered during implementation
- **Gotchas or edge cases** encountered and how to handle them
- **Best practices or patterns** that worked well
- **Architecture decisions** and their rationale
- **Performance or security considerations**
- **Things to remember** for future work
- **Library or framework behaviors** that were surprising or useful

**Examples of good learnings:**
- "React useEffect cleanup functions prevent memory leaks on unmount"
- "PostgreSQL JSONB indexes significantly improve query performance for JSON columns"
- "Prisma migrations should be reviewed manually before applying to production"
- "Next.js server actions require 'use server' directive at function level"

## Interactive Flow

### Step 1: Work Item Completion Status

The command asks you about work item completion:

**Question:** "Is this work item complete?"

**Options:**
- **Yes - Mark as completed**
  - Work item is done
  - Status changes to "completed"
  - Will not auto-resume in next session
  - Dependencies unblock for other work items

- **No - Keep as in-progress**
  - Work is ongoing
  - Status stays "in_progress"
  - Will auto-resume when you run `/sk:start` in the next session
  - Preserves all session context for continuation

- **Cancel**
  - Don't end session
  - Continue working
  - No changes made

### Step 2: Quality Gates

The command runs quality gates with different behavior based on your completion choice:

**When marking work item as "Complete" (`--complete` flag):**
- Quality gates are **enforced/blocking**
- All gates must pass to end the session
- If any gate fails, session end is aborted
- You must fix issues before completing

**When keeping work item "In-Progress" (`--incomplete` flag):**
- Quality gates **run but are non-blocking**
- Gates show warnings but don't prevent session end
- Useful when running out of Claude context
- Allows checkpointing work-in-progress
- Can resume work later without losing progress

**Quality gates checked:**
1. **Tests** - All tests must pass (or warned)
2. **Linting** - No linting errors (or warned)
3. **Type Checking** - No type errors (or warned, for TypeScript projects)
4. **Git Commits** - All changes must be committed (or warned)
5. **Coverage** - Meets project coverage threshold (or warned, if configured)

### Step 3: Update Context

After quality gates pass:
- **stack.txt** is regenerated (technology inventory)
- **tree.txt** is regenerated (directory structure)
- Work item status is updated
- Session history is recorded

### Step 4: Session Summary

The command displays:
- **Work accomplished** - Summary of what was done
- **Commit details** - Full messages with file change statistics
- **Quality gate results** - Pass/fail for each check
- **Learnings captured** - All learnings from commit messages and temp file
- **Work item status** - Completed or in-progress
- **Session duration**
- **Suggested next steps**

## Examples

### Completing a Work Item

```bash
/sk:end
```

**Interactive flow:**

```
Is this work item complete?

○ Yes - Mark as completed
  Work item is done. Will not auto-resume in next session.

● No - Keep as in-progress
  Work is ongoing. Will auto-resume when you run /start in the next session.

○ Cancel
  Don't end session. Continue working.

→ Selected: Yes - Mark as completed

Running quality gates...
✓ All tests passed (18/18)
✓ Linting passed
✓ Type checking passed
✓ All changes committed (3 commits)
✓ Coverage: 85.2% (target: 80%)

Updating project context...
✓ Regenerated stack.txt
✓ Regenerated tree.txt

=============================================================================
SESSION SUMMARY
=============================================================================

WORK ITEM: feature_auth - Add user authentication
STATUS: Completed ✓

COMMITS (3):
1. feat: Add JWT token generation
   Files: 5 (+120, -0)
   - src/auth/jwt.ts
   - src/auth/types.ts
   - tests/auth/jwt.test.ts

2. feat: Implement login endpoint
   Files: 3 (+85, -15)
   - src/api/routes/auth.ts
   - src/middleware/auth.ts

3. docs: Update authentication guide
   Files: 1 (+45, -0)
   - docs/authentication.md

LEARNINGS CAPTURED (4):
1. JWT refresh tokens should have shorter expiry than access tokens
2. Always validate tokens on server-side, never trust client
3. Use httpOnly cookies for storing refresh tokens to prevent XSS
4. TypeScript discriminated unions work great for auth state management

QUALITY GATES:
✓ Tests: 18/18 passed
✓ Linting: No errors
✓ Type checking: No errors
✓ Coverage: 85.2%

SESSION DURATION: 45 minutes

NEXT STEPS:
- Start next work item: /sk:start
- Review work items: /sk:work-list
- View learnings: /sk:learn-show
```

### Keeping Work In Progress (Non-Blocking Gates)

```bash
/sk:end
```

**Interactive flow:**

```
Is this work item complete?

○ Yes - Mark as completed

● No - Keep as in-progress
  Work is ongoing. Will auto-resume when you run /start in the next session.

○ Cancel

→ Selected: No - Keep as in-progress

Running quality gates (non-blocking)...
✓ All tests passed (12/12)
✓ Linting passed
✓ All changes committed (2 commits)

Session ended. Work item remains in-progress.

When you run /sk:start next time, this work item will auto-resume
with full context from this session.
```

**Example with failing gates (non-blocking):**

```
Is this work item complete?

○ Yes - Mark as completed

● No - Keep as in-progress
  Work is ongoing. Will auto-resume when you run /start in the next session.

○ Cancel

→ Selected: No - Keep as in-progress

Running quality gates (non-blocking)...
⚠️  Tests: 2/15 tests failed (WARNING - not blocking)
⚠️  Coverage: 72.3% (threshold: 80%) (WARNING - not blocking)
✓ Linting passed
✓ All changes committed (2 commits)

Session ended with warnings. Work item remains in-progress.

Quality gate warnings (fix in next session):
  - 2 failing tests need attention
  - Coverage needs 7.7% increase

When you run /sk:start next time, this work item will auto-resume
with full context from this session.
```

## Quality Gate Failures (Complete Mode Only)

When using `--complete` mode, quality gates are enforced. If any gates fail, the session end is aborted and you must fix the issues:

**Note:** In `--incomplete` mode, these same checks run but only show warnings - they do not block session end.

### Test Failures

```
✗ Tests failed: 2/15 tests failed

Failed tests:
  - test/auth/jwt.test.ts: "should validate expired token"
  - test/api/auth.test.ts: "should reject invalid credentials"

Fix the failing tests before ending the session:
  npm test
```

### Uncommitted Changes

```
✗ Uncommitted changes detected

Uncommitted files:
  M  src/auth/jwt.ts
  M  src/api/routes/auth.ts
  ?? tests/auth/new-test.ts

Commit all changes before ending the session:
  git add .
  git commit -m "Your message"
```

### Linting Errors

```
✗ Linting failed: 5 errors

src/auth/jwt.ts
  12:5   error  'token' is not defined  no-undef
  25:10  error  Missing return type    @typescript-eslint/explicit-function-return-type

Fix linting errors:
  npm run lint
  npm run lint --fix  (auto-fix if possible)
```

## Command Options

The command internally uses these options based on your interactive selection:

```bash
sk end --complete --learnings-file .session/temp_learnings.txt
sk end --incomplete --learnings-file .session/temp_learnings.txt
```

But you don't need to specify these - the interactive flow handles it.

## When to Use `--incomplete` Mode

The `--incomplete` flag is extremely useful in these scenarios:

### Running Out of Claude Context

**Problem:** You're nearing the end of your Claude Code context window and quality gates are failing, but you want to checkpoint your work.

**Solution:**
```bash
/sk:end
# Select: "No - Keep as in-progress"
```

This allows you to:
- Save all your work and learnings
- End the session gracefully
- Resume later with full context
- Continue fixing quality issues in next session

### Work-in-Progress Checkpoint

**Problem:** You need to take a break but aren't done with the work item, and some tests are still failing.

**Solution:** Use `--incomplete` to checkpoint without fixing all issues immediately.

**Example workflow:**
```
Session 1 (2 hours):
  - Implement 70% of feature
  - Some tests failing
  - Running out of time
  → /sk:end --incomplete  (checkpoints work)

Session 2 (next day):
  - Resume with full context
  - Fix remaining tests
  - Complete feature
  → /sk:end --complete  (enforces quality gates)
```

### Key Benefits of `--incomplete`

1. **No Data Loss**: All commits, learnings, and context saved
2. **Flexible Workflow**: Don't need to fix everything immediately
3. **Context Preservation**: Resume exactly where you left off
4. **Quality Visibility**: Still see what needs fixing, just not blocked
5. **Progress Tracking**: Work item stays "in_progress" for auto-resume

## Learning Auto-Extraction

Learnings are extracted from:

1. **Commit messages** - Any line starting with `LEARNING:`
2. **Temporary file** - `.session/temp_learnings.txt` if it exists
3. **Both sources** - If both exist, learnings from both are captured

Learnings are automatically:
- Timestamped with session date
- Associated with work item
- Categorized (if category keywords detected)
- Added to `.session/tracking/learnings.json`
- Available for future sessions via `/sk:learn-show` and `/sk:learn-search`

## Multi-Session Work Items

For work items spanning multiple sessions:

**Session 1:**
```bash
/sk:start feature_complex
# ... work on feature ...
/sk:end  → Select "No - Keep as in-progress"
```

**Session 2:**
```bash
/sk:start  → Auto-resumes feature_complex with full context
# ... continue work ...
/sk:end  → Select "Yes - Mark as completed"
```

The briefing in Session 2 includes:
- All commits from Session 1
- Quality gate results from Session 1
- Session 1 duration and date
- Full work context preserved

## After Session Ends

Once the session ends successfully:

1. **Work item updated** - Status changed to completed or stays in-progress
2. **History recorded** - Session added to `.session/history/`
3. **Context updated** - stack.txt and tree.txt refreshed
4. **Learnings saved** - Available for future reference
5. **Ready for next session** - Run `/sk:start` to begin next work item

## Error Recovery

### Can't Fix Issues Now?

If quality gates fail and you can't fix immediately:

1. **Don't cancel the session** - You'll lose the work item association
2. **Fix the issues:**
   ```bash
   # Fix tests
   npm test

   # Fix linting
   npm run lint --fix

   # Commit remaining changes
   git add .
   git commit -m "Fix quality gate issues"
   ```
3. **Try ending again:**
   ```bash
   /sk:end
   ```

### Accidentally Cancelled?

If you cancelled the session but meant to end it:
- Your work is preserved in commits
- Work item status is unchanged
- Simply run `/sk:end` again

## See Also

- [Start Command](start.md) - Begin a development session
- [Validate Command](validate.md) - Check quality gates without ending session
- [Learn Show Command](learn-show.md) - View captured learnings
- [Status Command](status.md) - View current session status
