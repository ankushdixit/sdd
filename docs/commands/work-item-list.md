# Work Item List Command

**Usage:** `/work-item list [--status STATUS] [--type TYPE] [--milestone MILESTONE]`

**Description:** List all work items with optional filtering.

**Options:**
- `--status STATUS` - Filter by status (not_started, in_progress, blocked, completed)
- `--type TYPE` - Filter by type (feature, bug, refactor, security, integration_test, deployment)
- `--milestone MILESTONE` - Filter by milestone name

**Behavior:**

1. Load work_items.json
2. Apply filters (if specified)
3. Sort by:
   - Priority (critical > high > medium > low)
   - Dependency order (items with no unmet dependencies first)
   - Creation date (oldest first)
4. Display with color coding and indicators
5. Show summary statistics

**Output Format:**

```
Work Items (15 total, 3 in progress, 8 not started, 4 completed)

🔴 CRITICAL
  [  ] feature_oauth_integration (blocked - waiting on: feature_user_model) 🚫
  [>>] security_fix_sql_injection (in progress, session 3)

🟠 HIGH
  [>>] feature_user_profile (in progress, session 1)
  [  ] bug_login_timeout (ready to start) ✓
  [✓] feature_user_model (completed, 2 sessions)

🟡 MEDIUM
  [  ] refactor_database_queries (ready to start) ✓
  [  ] feature_email_notifications (ready to start) ✓

🟢 LOW
  [  ] refactor_code_cleanup (ready to start) ✓

Legend:
  [  ] Not started
  [>>] In progress
  [✓] Completed
  🚫 Blocked by dependencies
  ✓ Ready to start
```

**Example:**

```
User: /work-item list --status not_started --type feature

Claude: Work Items (5 matching filters)

🟠 HIGH
  [  ] feature_oauth_integration (blocked - waiting on: feature_user_model) 🚫
  [  ] feature_user_profile (ready to start) ✓

🟡 MEDIUM
  [  ] feature_email_notifications (ready to start) ✓
  [  ] feature_password_reset (ready to start) ✓

🟢 LOW
  [  ] feature_user_preferences (ready to start) ✓
```
