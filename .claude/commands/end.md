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

## Step 2: Complete Session

Then run the session completion with learnings:

```bash
sdd end --learnings-file .session/temp_learnings.txt
```

This script validates quality gates:
- All tests pass
- Linting passes
- Git changes are committed
- Work item status is updated
- Learnings are captured

The script automatically updates project context files (stack.py and tree.py) after validation passes.

### Work Item Completion Control

During session completion, you will be prompted to explicitly mark the work item as complete or in-progress:

```
Work item: "Learning Curator Bug Fix"

Is this work item complete?
1. Yes - Mark as completed
2. No - Keep as in-progress (will resume in next session)
3. Cancel - Don't end session

Choice [1]: _
```

**Option 1 (Yes)**: Marks the work item as complete and ends the session. The work item will not auto-resume in the next session.

**Option 2 (No)**: Keeps the work item as in-progress and ends the session. The work item will automatically resume when you run `/start` in the next session, making it easy to work on large items across multiple sessions.

**Option 3 (Cancel)**: Aborts the `/end` operation entirely. The session remains active and you can continue working.

**Non-interactive Mode**: You can also use command-line flags to control completion status:

```bash
# Mark work item as completed
sdd end --complete --learnings-file .session/temp_learnings.txt

# Keep work item as in-progress
sdd end --incomplete --learnings-file .session/temp_learnings.txt
```

**Note**: Without flags in non-interactive mode, the work item defaults to "in-progress" for safety.

Show the user:
- Session summary with work accomplished
- **Commit details** (full messages + file change statistics) - Enhancement #11
- Quality gate results (pass/fail for each check)
- Learnings captured
- Suggested next steps

If any quality gates fail, display the specific errors and guide the user on what needs to be fixed before the session can be completed. Do not proceed with session completion until all quality gates pass.

## Enhanced Session Summaries (Enhancement #11)

Session summaries now include comprehensive commit details:
- **Full commit messages** (multi-line messages preserved)
- **File change statistics** from `git diff --stat` (files changed, insertions, deletions)
- Each commit listed with short SHA and message

This enriched session summary serves as the **single source of truth** for "Previous Work" sections in future session briefings when resuming in-progress work items.
