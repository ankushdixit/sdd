---
description: Complete the current development session with quality gates and summary
---

# Session End

Complete the current session by running validation and generating summary:

```bash
sdd end
```

This script validates quality gates:
- All tests pass
- Linting passes
- Git changes are committed
- Work item status is updated

The script automatically updates project context files (stack.py and tree.py) after validation passes.

Show the user:
- Session summary with work accomplished
- List of files changed
- Quality gate results (pass/fail for each check)
- Suggested next steps

If any quality gates fail, display the specific errors and guide the user on what needs to be fixed before the session can be completed. Do not proceed with session completion until all quality gates pass.
