# SDD Bug Tracker

This document tracks bugs discovered during development and testing.

## Status Legend
- 🔴 CRITICAL - Blocks core functionality
- 🟠 HIGH - Significant impact on user experience
- 🟡 MEDIUM - Noticeable but has workarounds
- 🟢 LOW - Minor issue or cosmetic
- ✅ FIXED - Bug has been resolved

---

## Bug #20: Learning Curator Extracts Incomplete and Example Learnings
**Status:** ✅ FIXED (Session 3) - Fixed regex patterns, added file type filtering, and standardized metadata structure.

---

## Bug #21: /start Command Ignores Work Item ID Argument
**Status:** ✅ FIXED (Session 6) - Added argument parsing to briefing_generator.py to respect explicit work item selection.

---

## Bug #22: Git Branch Status Not Finalized When Switching Work Items
**Status:** ✅ FIXED (Session 7) - Implemented automatic git branch status finalization when starting new work items.

---

## Bug #23: Bug Spec Template Missing Acceptance Criteria Section
**Status:** ✅ FIXED (Session 4) - Added Acceptance Criteria section to bug_spec.md and refactor_spec.md templates.

---

## Bug #24: Learning Curator Extracts Test Data Strings as Real Learnings
**Status:** ✅ FIXED (Session 5) - Excluded test directories from learning extraction and improved content validation.

---

## Bug #25: /sdd:end Requires Pre-committed Changes, Cannot Commit as Part of Session End

**Status:** 🟡 MEDIUM

**Discovered:** 2025-11-06 (During Session 30 - feature_change_sdd_end_default_behavio)

### Description

The `/sdd:end` command currently requires all changes to be committed before it can run. If there are uncommitted changes in the working directory, the command aborts with an error message instructing the user to commit first, then run `/sdd:end` again. This creates friction in the workflow because:

1. Users must manually commit changes before ending the session
2. The session end cannot create a final commit with the session summary
3. It's redundant - the git workflow tries to commit during session end anyway
4. The error is confusing because the command *would* commit if allowed to proceed

**Current Behavior:**
```
❌ Session completion aborted
Commit your changes and try again.
```

This occurs at the pre-flight check in `complete.py:check_uncommitted_changes()` which aborts if changes are detected.

### Steps to Reproduce

1. Start a work session with `/sdd:start work_item_id`
2. Make code changes but don't commit them
3. Run `/sdd:end --learnings-file .session/temp_learnings.txt`
4. Observe: Command aborts with uncommitted changes error

**Environment:**
- OS: macOS Darwin 24.6.0
- Python: 3.11.7
- Git: 2.45.2
- SDD Version: Current (Session 30)

### Expected Behavior

The `/sdd:end` command should:
1. Accept uncommitted changes in the working directory
2. Create a commit automatically with the session summary message
3. Run quality gates on the code as-is
4. Complete the git workflow (commit, push, merge/PR as configured)

This would match the natural development flow where developers work, run quality checks, and then commit everything in one atomic session end operation.

### Actual Behavior

The command aborts with:
```
==================================================
UNCOMMITTED CHANGES DETECTED
==================================================

You have uncommitted changes:
   M src/sdd/session/complete.py
   M src/sdd/quality/gates.py
   ... and N more

==================================================
📋 REQUIRED STEPS BEFORE /sdd:end:
==================================================
1. Review your changes: git status
2. Update CHANGELOG.md
3. Commit everything: git add -A && git commit -m '...'
4. Then run: sdd end
```

The user must exit, manually commit, then re-run `/sdd:end`.

### Impact

- **Severity:** Medium - Has workaround but disrupts workflow
- **Affected Users:** All users running `/sdd:end` with uncommitted changes
- **Affected Versions:** Current implementation
- **Business Impact:**
  - Adds friction to development workflow
  - Extra manual steps required
  - Inconsistent with the automated philosophy of SDD
- **Workaround:** Manually commit all changes before running `/sdd:end`

### Root Cause Analysis

#### Investigation

1. Reviewed `src/sdd/session/complete.py:838-926` - `check_uncommitted_changes()` function
2. Function was designed as a safety check to prevent accidental session ends
3. The git workflow (`complete_git_workflow()`) at line 1183 attempts to commit anyway
4. The pre-flight check at line 1030 blocks execution before the commit can happen

**Key Findings:**
- The safety check was added to prevent users from losing uncommitted work
- However, the git workflow already handles committing changes gracefully
- The check_uncommitted_changes() function has an interactive override (y/n prompt) but defaults to abort in non-interactive mode
- The git workflow's `commit_changes()` method handles "nothing to commit" gracefully

#### Root Cause

The `check_uncommitted_changes()` function (line 838) was implemented as a defensive check but is now overly restrictive. The original intent was to prevent data loss, but:

1. The git workflow already commits changes safely
2. The quality gates run on the current state regardless
3. The abort prevents the natural flow of: work → quality check → commit → end session

**Code:**
```python
# src/sdd/session/complete.py:1029-1034
# Pre-flight check - ensure changes are committed
if not check_uncommitted_changes():
    logger.warning("Session completion aborted due to uncommitted changes")
    output.info("\n❌ Session completion aborted")
    output.info("Commit your changes and try again.\n")
    return 1
```

#### Why It Happened

**Contributing Factors:**
- Safety-first design philosophy (prevent data loss)
- Original implementation assumed manual commits
- Git workflow was later enhanced to handle commits automatically
- The pre-flight check was not updated when git workflow gained commit capabilities

### Fix Approach

**Option 1: Remove the Pre-flight Check (Recommended)**

Remove or make the `check_uncommitted_changes()` call optional, allowing the git workflow to handle commits naturally:

```python
# src/sdd/session/complete.py:1029-1034
# Optional: Check for uncommitted changes (warning only, don't block)
has_uncommitted = check_uncommitted_changes()
if has_uncommitted:
    output.info("\n⚠️  Uncommitted changes detected - will commit during session end")
```

**Option 2: Make Check Optional with Flag**

Add a `--allow-uncommitted` flag:
```python
parser.add_argument(
    "--allow-uncommitted",
    action="store_true",
    help="Allow session end with uncommitted changes (will auto-commit)",
)
```

**Option 3: Smart Detection**

Only abort if there are uncommitted changes that would conflict with session end operations (e.g., changes to `.session/` tracking files that sdd end will modify):

```python
# Filter out only user changes, ignore .session/ tracking files
user_changes = [
    line for line in uncommitted
    if ".session/tracking/" not in line
    and ".session/briefings/" not in line
]

if user_changes:
    output.warning("Will commit your changes during session end")
else:
    # Only tracking file changes - safe to proceed
    pass
```

**Recommended Approach:** Option 1 (Remove blocking check) is cleanest because:
- Git workflow already handles commits safely
- Quality gates run on current state
- Matches expected behavior ("end session" should commit everything)
- Reduces friction in the development loop

**Files Modified:**
- `src/sdd/session/complete.py` - Modify `main()` to make check non-blocking
- `tests/unit/session/test_complete.py` - Update tests for new behavior
- `docs/commands/end.md` - Update documentation to reflect that uncommitted changes are OK

### Acceptance Criteria

- [ ] `/sdd:end` can run with uncommitted changes in working directory
- [ ] Uncommitted changes are automatically committed during session end
- [ ] Quality gates still run on the current code state
- [ ] CHANGELOG must still be updated (can be checked in quality gates)
- [ ] Git workflow commits all changes with proper session message
- [ ] Tests verify the new behavior
- [ ] Documentation reflects that pre-committing is no longer required
- [ ] Backward compatible - doesn't break users who still pre-commit manually

### Related Issues

- Enhancement #6: Multi-session work items benefit from this fix (easier to end sessions mid-work)
- Git workflow already has commit logic at `src/sdd/git/integration.py:419-503`

### Notes

This bug was discovered during Session 30 when analyzing warnings from `/sdd:end` execution. The git workflow showed:
```
⚠️  Git: Commit failed: Commit failed:
```

This happened because all changes were already committed (the pre-flight check passed), so there was nothing to commit during git workflow. This indicates the check is redundant - if it passes, git workflow has nothing to do; if it fails, git workflow never gets to run.

---

## Bug Template

Use this template when documenting new bugs. Copy the structure below and fill in all sections with specific details.

```markdown
## Bug #XX: [Bug Title]

**Status:** 🔴 CRITICAL / 🟠 HIGH / 🟡 MEDIUM / 🟢 LOW

**Discovered:** YYYY-MM-DD (During [context: session, testing, production, etc.])

### Description

Clear, concise description of the bug and its impact on users/system.

**Example:**
> User authentication fails intermittently when logging in from mobile devices. Users see a "Session expired" error even though they just created a new session. This affects approximately 15% of mobile login attempts based on error logs.

### Steps to Reproduce

Detailed steps that reliably reproduce the bug:

1. Step 1
2. Step 2
3. Step 3

**Environment:**
- Device/Browser: [e.g., iPhone 14 Pro, Chrome 119]
- OS Version: [e.g., iOS 17.0, Windows 11]
- App/System Version: [e.g., v2.3.1]
- Network: [e.g., WiFi, 5G]

### Expected Behavior

What should happen when the user performs the steps above.

### Actual Behavior

What actually happens, including error messages, logs, screenshots.

**Error Log (if applicable):**
```
[Include relevant error messages or log entries]
```

**Screenshot:** [Attach or describe visual issues]

### Impact

- **Severity:** [Critical/High/Medium/Low] (with justification)
- **Affected Users:** [percentage/number of users affected]
- **Affected Versions:** [which versions have this bug]
- **Business Impact:** [effect on metrics, user experience, revenue]
- **Workaround:** [temporary fix if available, or "None"]

### Root Cause Analysis

#### Investigation

Document what you did to investigate: logs reviewed, code analyzed, experiments run.

**Example:**
1. Reviewed application logs for past 7 days
2. Identified pattern: failures only occur on mobile devices
3. Checked cache metrics: intermittent connection timeouts
4. Analyzed relevant code in [file:line]
5. Reproduced locally with [conditions]

**Key Findings:**
- Finding 1
- Finding 2
- Finding 3

#### Root Cause

The underlying technical cause of the bug.

**Code:**
```python
# Current buggy code in file.py:47-52
def problematic_function():
    # Show the problematic code
    pass
```

#### Why It Happened

Why was this bug introduced? What can we learn?

**Contributing Factors:**
- Factor 1 (e.g., insufficient testing)
- Factor 2 (e.g., missing monitoring)
- Factor 3 (e.g., incorrect assumptions)

### Fix Approach

How will this bug be fixed? Include code changes if relevant.

**Code Changes:**
```python
# Fixed code in file.py:47-58
def fixed_function():
    # Show the corrected code
    pass
```

**Files Modified:**
- `path/to/file1.py` - Description of changes
- `path/to/file2.py` - Description of changes

### Acceptance Criteria

- [ ] Root cause is identified and addressed (not just symptoms)
- [ ] All reproduction steps no longer trigger the bug
- [ ] Comprehensive tests added to prevent regression
- [ ] No new bugs or regressions introduced by the fix
- [ ] Edge cases identified in investigation are handled
- [ ] All tests pass (unit, integration, and manual)

### Testing Strategy

#### Regression Tests
- [ ] Add unit test for [specific scenario]
- [ ] Add integration test for [workflow]
- [ ] Add test to verify [edge case]

#### Manual Verification
- [ ] Test on [environment/device]
- [ ] Test with [specific conditions]
- [ ] Verify [expected outcome]

#### Edge Cases
- [ ] Test with [edge case 1]
- [ ] Test with [edge case 2]

### Prevention

How can we prevent similar bugs in the future?

- Add tests for [scenario]
- Set up monitoring/alerting for [metric]
- Code review checklist: [specific check]
- Documentation: [what to document]

### Workaround

Temporary fix available to users while bug is being fixed, or "None" if no workaround exists.

### Related Issues

- Bug #XX: [related bug]
- Enhancement #XX: [related enhancement]
- External issue: [link]

### Files Affected

- `path/to/file1.py:line` - Description
- `path/to/file2.py:line` - Description
```
