---
description: Validate current session meets quality standards without ending it
---

# Session Validate

Run the validation script to check quality standards:

```bash
sdd validate
```

The validation checks:
- **Tests**: All test suites pass
- **Linting**: Code passes ruff linting rules
- **Type Checking**: Type hints are valid (if type checking is configured)
- **Code Coverage**: Meets minimum coverage threshold
- **Git Status**: Working directory is clean or has expected changes
- **Acceptance Criteria**: Work item requirements are met

Display the validation results to the user with a clear pass/fail status for each check. If any checks fail, show the specific errors and suggest how to fix them. This command allows checking quality during development without ending the session.
