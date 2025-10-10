# Session End Command

**Usage:** `/session-end`

**Description:** Complete current session with quality gates and summary generation.

**Behavior:**

1. Determine current work item (from status)

2. Run quality gates:
   - Execute tests
   - Run linting (auto-fix if possible)
   - Check formatting
   - Validate coverage meets requirements

3. If quality gates pass:
   - Update work item status (to "completed" if done, keep "in_progress" if partial)
   - Generate session summary
   - Update tracking files
   - Create git commit (standardized format)

4. If quality gates fail:
   - Report failures
   - Keep work item in "in_progress"
   - Offer to fix issues or skip gates

5. Present session summary

**Example:**

```
User: /session-end

Claude: Completing session...

Running quality gates...
✓ Tests: 47/47 passed (coverage: 87%)
✓ Linting: passed (3 issues auto-fixed)
✓ Formatting: passed

Quality gates: PASSED ✓

Updating work item status...
- implement_authentication: in_progress → completed

# Session Summary

## Work Items Completed
- implement_authentication

## Achievements
- Implemented OAuth2 authentication flow
- Added Google and GitHub providers
- Created token refresh mechanism
- Added 15 tests with 87% coverage

## Challenges Encountered
- Token expiry handling was tricky
- Race condition in token storage (resolved with Redis atomic ops)

## Learnings
- OAuth2 refresh tokens must be stored atomically
- Using Redis for token storage provides TTL and atomicity

## Metrics
- Files changed: 8
- Tests added: 15
- Lines added: 342
- Lines removed: 87

Session completed successfully ✓
```

**Implementation Details:**

The command markdown instructs Claude to:
1. Run script: `python scripts/session_complete.py`
2. Review quality gate results
3. Update work item status
4. Generate session summary
5. Create git commit
