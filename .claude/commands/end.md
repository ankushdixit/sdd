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

Show the user:
- Session summary with work accomplished
- List of files changed
- Quality gate results (pass/fail for each check)
- Learnings captured
- Suggested next steps

If any quality gates fail, display the specific errors and guide the user on what needs to be fixed before the session can be completed. Do not proceed with session completion until all quality gates pass.
