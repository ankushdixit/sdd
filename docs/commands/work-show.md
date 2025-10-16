# Work Item Show Command

**Usage:** `/sdd:work-show <work_item_id>`

**Description:** Display detailed information about a specific work item.

**Behavior:**

1. Load work item from work_items.json
2. Load specification file from .session/specs/
3. Display comprehensive view:
   - Basic info (ID, type, status, priority)
   - Dependencies (with status)
   - Session history
   - Git branch info
   - Specification content
4. Show actionable next steps

**Example:**

```
User: /sdd:work-show feature_oauth

Claude:
================================================================================
Work Item: feature_oauth
================================================================================

Type: feature
Status: in_progress
Priority: high
Created: 2025-10-10

Dependencies:
  ✓ feature_user_model (completed)
  ✗ feature_database_migration (in progress)

Sessions:
  1. 2025-10-11 14:30-16:45 (2h 15m) - Initial implementation
  2. 2025-10-12 10:00-11:30 (1h 30m) - Added OAuth providers

Git Branch: session-003-feature_oauth
Commits: 5

Specification:
--------------
# Feature: OAuth Integration

## Overview
Enable users to log in using OAuth providers (Google, GitHub).

## User Story
As a user, I want to log in using my existing Google or GitHub account
so that I don't need to create another password.

[... rest of specification ...]

Next Steps:
- Continue working: /sdd:start
- Update fields: /sdd:work-update feature_oauth
- View related items: /sdd:work-list --milestone auth
```
