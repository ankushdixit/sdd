# Session Validate Command

**Usage:** `/sdd:validate`

**Description:** Pre-flight check to validate if current session can complete successfully.

**Behavior:**

1. Check git status
   - Verify working directory is clean or has expected changes
   - Check if on correct branch for work item
   - Verify no uncommitted .session/ tracking files

2. Preview quality gates
   - Run tests (if configured)
   - Check linting (if configured)
   - Check formatting (if configured)
   - Show what would pass/fail without making changes

3. Validate work item criteria
   - Check acceptance criteria (if defined)
   - Verify implementation paths exist
   - Check test paths exist and have content

4. Check tracking updates
   - Detect stack changes (would prompt for reasoning)
   - Detect tree changes (would prompt for reasoning)
   - Preview what would be updated

5. Display results
   - Show ✓ for passed checks
   - Show ✗ for failed checks with actionable messages
   - Overall status: ready or not ready

**Example:**

```
User: /sdd:validate

Claude: Running session validation...

✓ Git Status: Working directory ready, branch: session-005-feature-oauth
✓ Quality Gates: All quality gates pass
✓ Work Item Criteria: Work item criteria met
✓ Tracking Updates: No tracking updates

✅ Session ready to complete!
Run /sdd:end to complete the session.
```

**Example with issues:**

```
User: /sdd:validate

Claude: Running session validation...

✓ Git Status: Working directory ready, branch: session-005-feature-oauth
✗ Quality Gates: Some quality gates fail
   ✗ linting: 3 linting issues found
      - scripts/auth.py:42:1: F401 'datetime' imported but unused
      - scripts/auth.py:56:89: E501 line too long (89 > 88 characters)
      - scripts/auth.py:78:1: D100 Missing docstring
✓ Work Item Criteria: Work item criteria met
✓ Tracking Updates: No tracking updates

⚠️  Session not ready to complete

Fix the issues above before running /sdd:end
```

**Implementation:**

Run: `sdd validate`
