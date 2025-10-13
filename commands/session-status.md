# Session Status Command

**Usage:** `/session-status`

**Description:** Display current session state and progress.

**Displays:**
- Current work item
- Time elapsed in session
- Files changed (git diff)
- Git branch status
- Milestone progress (if applicable)
- Next upcoming work items

**Example:**

```
User: /session-status

Claude:
Current Session Status
================================================================================

Work Item: feature_user_profile
Type: feature
Priority: high
Session: 2 (of estimated 3)

Time Elapsed: 1h 23m

Files Changed (5):
  M  src/models/user.py
  M  src/api/profile.py
  A  tests/test_profile.py
  M  README.md
  M  requirements.txt

Git Branch: session-003-feature_user_profile
Commits: 3

Milestone: auth-mvp (45% complete)
  Related items: 2 in progress, 3 not started

Next up:
  🟠 feature_oauth_integration (blocked)
  🟡 feature_email_notifications (ready)

Quick actions:
  - Validate session: /session-validate
  - Complete session: /session-end
  - View work item: /work-item show feature_user_profile
```
