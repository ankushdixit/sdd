# Work Item Next Command

**Usage:** `/work-item next`

**Description:** Show the next recommended work item to start.

**Logic:**
1. Filter to not_started items
2. Check dependencies (skip blocked items)
3. Sort by priority
4. Return highest priority, unblocked item
5. Explain why other items are blocked

**Example:**

```
User: /work-item next

Claude:
Next Recommended Work Item:
================================================================================

🟠 HIGH: feature_user_profile
ID: feature_user_profile
Type: feature
Priority: high
Ready to start: Yes ✓

Dependencies: All satisfied
  ✓ feature_user_model (completed)

Estimated effort: 2-3 sessions

To start: /session-start

Other items waiting:
  🔴 feature_oauth_integration - Blocked by: feature_database_migration
  🟡 feature_email_notifications - Ready (medium priority)
```
