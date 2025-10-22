---
description: Complete the current development session with quality gates and summary
---

# Session End

Before completing the session, **generate learnings** from the work done:

## Step 1: Generate Learnings

Review the session work and create 2-5 key learnings. Write them to `.session/temp_learnings.txt` (one learning per line). Consider:
- Technical insights discovered during implementation
- Gotchas or edge cases encountered
- Best practices or patterns that worked well
- Architecture decisions and their rationale
- Performance or security considerations
- Things to remember for future work

Example learnings:
```
TypeScript ESLint requires --ext flags when using glob patterns
Metadata counters need explicit updates after status changes
Non-interactive scripts should check sys.stdin.isatty() before using input()
```

Write the learnings file:
```bash
cat > .session/temp_learnings.txt << 'EOF'
[Learning 1]
[Learning 2]
[Learning 3]
EOF
```

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
