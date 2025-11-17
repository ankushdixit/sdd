---
description: Complete the current development session with quality gates and summary
---

# Session End

Before completing the session, **capture learnings** from the work done:

## Step 1: Generate Learnings

Review the session work and create 2-5 key learnings. You have two ways to capture learnings:

### Option A: Commit Message LEARNING Tags (Recommended)

Include `LEARNING:` annotations in your commit messages. These will be automatically extracted during session completion:

```bash
git commit -m "Implement calculator add function

Added TypeScript add function with comprehensive tests.

LEARNING: TypeScript number type handles both integers and decimals seamlessly

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Option B: Temporary Learnings File

Write learnings to `.session/temp_learnings.txt` (one learning per line):

```bash
cat > .session/temp_learnings.txt << 'EOF'
[Learning 1]
[Learning 2]
[Learning 3]
EOF
```

**What makes a good learning:**

- Technical insights discovered during implementation
- Gotchas or edge cases encountered
- Best practices or patterns that worked well
- Architecture decisions and their rationale
- Performance or security considerations
- Things to remember for future work

## Step 2: Ask About Work Item Completion

Before completing the session, ask the user about the work item completion status using `AskUserQuestion`:

**Question: Work Item Completion Status**

- Question: "Is this work item complete?"
- Header: "Completion"
- Multi-select: false
- Options:
  - Label: "Yes - Mark as completed", Description: "Work item is done. Will not auto-resume in next session."
  - Label: "No - Keep as in-progress", Description: "Work is ongoing. Will auto-resume when you run /start in the next session."
  - Label: "Cancel", Description: "Don't end session. Continue working."

**Important**: Display the work item title in the question text so the user knows which item they're completing.

## Step 3: Complete Session

Based on the user's selection:

**If "Yes - Mark as completed" selected:**

```bash
sk end --complete --learnings-file .session/temp_learnings.txt
```

**Quality gate behavior:** Enforced/blocking - all gates must pass to end session.

**If "No - Keep as in-progress" selected:**

```bash
sk end --incomplete --learnings-file .session/temp_learnings.txt
```

**Quality gate behavior:** Non-blocking - gates run and show warnings but don't prevent session end. This is extremely useful when running out of Claude context with failing quality gates, allowing you to checkpoint your work-in-progress.

**If "Cancel" selected:**

- Show message: "Session end cancelled. You can continue working."
- Exit without calling command

**Quality gates checked (behavior depends on --complete vs --incomplete):**

- All tests pass (enforced in --complete, warned in --incomplete)
- Linting passes (enforced in --complete, warned in --incomplete)
- Git changes are committed (enforced in --complete, warned in --incomplete)
- Coverage threshold met (enforced in --complete, warned in --incomplete)
- Work item status is updated
- Learnings are captured

The script automatically updates project context files (stack.txt and tree.txt) after validation.

## Step 4: Show Results

Show the user:

- Session summary with work accomplished
- **Commit details** (full messages + file change statistics) - Enhancement #11
- Quality gate results (pass/fail for each check)
- Learnings captured
- Work item completion status (completed or in-progress)
- Suggested next steps

**For --complete mode:** If any quality gates fail, display the specific errors and guide the user on what needs to be fixed before the session can be completed. Do not proceed with session completion until all quality gates pass.

**For --incomplete mode:** If any quality gates fail, display warnings but allow the session to complete. Inform the user that these issues can be addressed in the next session when they resume the work item.

## Enhanced Session Summaries (Enhancement #11)

Session summaries now include comprehensive commit details:

- **Full commit messages** (multi-line messages preserved)
- **File change statistics** from `git diff --stat` (files changed, insertions, deletions)
- Each commit listed with short SHA and message

This enriched session summary serves as the **single source of truth** for "Previous Work" sections in future session briefings when resuming in-progress work items.
