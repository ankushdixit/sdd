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

**Status:** 🟠 HIGH

**Discovered:** 2025-10-22 (During Session 1 - Enhancement #4 dogfooding)

### Problem

The learning curator has three bugs when extracting learnings during `/sdd:end`:

1. **Truncated learnings** - Multi-line LEARNING statements in commit messages are cut off at the first newline
2. **Extracts documentation examples** - Pulls example LEARNING statements from ENHANCEMENTS.md and other docs as if they were real learnings
3. **Inconsistent metadata structure** - Git-extracted learnings use `context` field while temp-file learnings use `learned_in` field, causing inconsistent data structure

### Current Behavior

When running `/sdd:end`, learnings.json contains:

**Truncated Learnings:**
```json
{
  "content": "The .gitignore patterns are added programmatically in",
  "source": "git_commit"
}
```

**Expected:**
```json
{
  "content": "The .gitignore patterns are added programmatically in ensure_gitignore_entries() function, not from a template file. This allows dynamic checking of which patterns already exist.",
  "source": "git_commit"
}
```

**Garbage from Examples:**
```json
{
  "content": "<your learning here>",
  "source": "inline_comment",
  "context": "ENHANCEMENTS.md:123"
}
```

**Inconsistent Metadata:**
```json
// Git-extracted learning (Session 1)
{
  "content": "The .gitignore patterns are added programmatically...",
  "source": "git_commit",
  "context": "Commit cb7d417e - Enhancement #4",
  "timestamp": "2025-10-22T23:18:57.687807"
  // Missing: learned_in field
}

// Temp-file learning (Session 2)
{
  "content": "Test pollution issues can cause tests to pass...",
  "source": "temp_file",
  "learned_in": "session_002",
  "timestamp": "2025-10-23T12:04:27.759210"
  // Missing: context field
}
```

### Root Cause

**Bug 1 - Truncated Learnings (scripts/learning_curator.py:570)**
```python
learning_pattern = r"LEARNING:\s*(.+?)(?=\n|$)"
```
This regex only captures to the first newline, stopping at line breaks even if the LEARNING statement continues.

**Bug 2 - Extracting from Documentation (extract_from_code_comments)**
The `extract_from_code_comments()` function scans ALL files including documentation (.md files) that contain example LEARNING statements for teaching purposes. These examples get extracted as real learnings.

**Bug 3 - Inconsistent Metadata Structure**
Different extraction methods in `learning_curator.py` use different metadata fields:
- Git extraction adds `context` (commit hash) but no `learned_in` (session)
- Temp file extraction adds `learned_in` (session) but no `context`
- This makes the learnings database inconsistent and harder to query/filter

### Impact

- **User Confusion**: Learnings database fills with incomplete/garbage entries
- **Loss of Context**: Truncated learnings lose valuable information
- **Data Quality**: Examples pollute the real learnings database
- **Curation Overhead**: Manual cleanup required after every session

### Expected Behavior

1. **Multi-line capture**: LEARNING statements should be captured completely, including line breaks within the statement
2. **Source filtering**: Only extract from actual source code files (.py, .js, .ts), not documentation files (.md)
3. **Validation**: Skip obvious garbage like placeholders ("<your learning here>")
4. **Consistent metadata**: All learnings should have both `learned_in` (session ID) and `context` (source details) fields regardless of extraction method

### Proposed Solution

#### Fix 1: Multi-line Learning Capture
Update regex to capture until the next blank line or end of message:

```python
# Before
learning_pattern = r"LEARNING:\s*(.+?)(?=\n|$)"

# After
learning_pattern = r"LEARNING:\s*(.+?)(?=\n\n|\Z)"  # Capture until double newline or end
```

Or handle multi-line in a different way:
```python
learning_pattern = r"LEARNING:\s*(.+?)(?=(?:\n(?![ \t]))|$)"  # Capture until unindented line
```

#### Fix 2: Filter Documentation Files
Update `extract_from_code_comments()` to skip documentation:

```python
def extract_from_code_comments(self):
    """Extract learnings from code comments (not documentation)."""
    learnings = []

    # Only scan actual code files
    code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs'}
    doc_extensions = {'.md', '.txt', '.rst'}

    for file_path in self._get_project_files():
        # Skip documentation files
        if file_path.suffix in doc_extensions:
            continue

        # Skip example/template directories
        if 'examples' in file_path.parts or 'templates' in file_path.parts:
            continue

        if file_path.suffix in code_extensions:
            # ... extract from this file
```

#### Fix 3: Standardize Metadata Structure
Ensure all learning entries have consistent metadata:

```python
def add_learning_metadata(learning: dict, session_id: str, source: str, context: str = None) -> dict:
    """Add consistent metadata to all learnings."""
    learning["learned_in"] = session_id
    learning["source"] = source
    if context:
        learning["context"] = context
    learning["timestamp"] = datetime.now().isoformat()
    return learning

# When extracting from git commits:
learning = {
    "content": extracted_content,
}
learning = add_learning_metadata(
    learning,
    session_id=current_session_id,
    source="git_commit",
    context=f"Commit {commit_hash[:8]} - {commit_title}"
)

# When extracting from temp file:
learning = {
    "content": extracted_content,
}
learning = add_learning_metadata(
    learning,
    session_id=current_session_id,
    source="temp_file",
    context=".session/temp_learnings.txt"
)
```

#### Fix 4: Validate Content
Add validation to skip garbage:

```python
def is_valid_learning(content: str) -> bool:
    """Check if extracted content is a valid learning."""
    # Skip placeholders and examples
    if '<' in content or '>' in content:
        return False
    if content in ['your learning here', 'example learning']:
        return False
    # Must have substance (more than just a few words)
    if len(content.split()) < 5:
        return False
    return True
```

### Reproduction Steps

1. Run `sdd init` in a project
2. Create a work item and start a session
3. Make commits with multi-line LEARNING statements:
   ```
   LEARNING: This is a multi-line learning that spans
   several lines to provide comprehensive context about
   the implementation.
   ```
4. Run `/sdd:end`
5. Check `.session/tracking/learnings.json`
6. Observe truncated learnings and documentation examples

### Workaround

Manually edit `.session/tracking/learnings.json` to:
1. Remove garbage entries (examples, placeholders)
2. Complete truncated learnings by checking git commit messages

### Related Issues

- Discovered during dogfooding Enhancement #4
- Session 1 generated 12 learnings, only 3 were valid

### Files Affected

- `scripts/learning_curator.py:570` - Regex pattern
- `scripts/learning_curator.py` - `extract_from_code_comments()` method
- `.session/tracking/learnings.json` - Affected by bug

---

## Bug #21: /start Command Ignores Work Item ID Argument

**Status:** 🟠 HIGH

**Discovered:** 2025-10-23 (During attempt to start work on Bug #20)

### Problem

The `/start` command (or `sdd start <work_item_id>`) completely ignores the work item ID argument provided by the user. Instead, it always uses the automatic work item selection logic which prioritizes resuming any in-progress work items, even when the user explicitly specifies a different work item to start.

### Current Behavior

When running:
```bash
sdd start bug_learning_curator_extracts_inco
```

The command:
1. Ignores the `bug_learning_curator_extracts_inco` argument
2. Calls `get_next_work_item()` which prioritizes in-progress items
3. Resumes `feature_create_initial_commit_on_main_` (session 1 in-progress item)
4. Creates/switches to that work item's git branch
5. Updates tracking files for the wrong work item

**Output:**
```
✓ Created git branch: session-002-feature_create_initial_commit_on_main_
✓ Work item status updated: feature_create_initial_commit_on_main_ → in_progress
# Session Briefing: Create initial commit on main during sdd init
```

### Expected Behavior

When a work item ID is provided as an argument:
1. Parse the command-line argument to get the specified work item ID
2. Validate the work item exists and dependencies are met
3. If another work item is in-progress, warn the user and ask for confirmation
4. Start the explicitly requested work item
5. Generate briefing for the requested work item

When no argument is provided, use automatic selection logic (current behavior).

### Root Cause

**scripts/briefing_generator.py:586-602**

The `main()` function never parses command-line arguments:

```python
def main():
    """Main entry point."""
    logger.info("Starting session briefing generation")

    # ... setup code ...

    # Load data
    work_items_data = load_work_items()
    learnings_data = load_learnings()

    # Find next work item
    item_id, item = get_next_work_item(work_items_data)  # BUG: Never checks sys.argv
```

The function should use argparse to handle optional work item ID argument, but it doesn't. The routing in `sdd_cli.py:73` marks `start` as `needs_argparse=True`, but the script doesn't actually parse arguments.

### Impact

- **Severity:** High (prevents explicit work item selection)
- **Affected Users:** Anyone trying to start a specific work item when another is in-progress
- **User Confusion:** Command appears to accept argument but silently ignores it
- **Workflow Disruption:** Users cannot override automatic work item selection
- **Data Integrity Risk:** Creates branches and updates tracking for wrong work item

### Expected Behavior Details

**With explicit work item ID:**
```bash
sdd start bug_learning_curator_extracts_inco
```
Should validate and start that specific work item, even if another is in-progress (with warning).

**Without work item ID:**
```bash
sdd start
```
Should use automatic selection (prioritize in-progress, then highest priority available).

**With in-progress conflict:**
```bash
sdd start new_item  # When another item is in-progress
```
Should warn:
```
⚠️  Warning: Work item 'feature_create_initial_commit_on_main_' is currently in-progress.
Starting a new work item will leave the current one incomplete.

Options:
1. Complete current work item first: /end
2. Force start new work item: sdd start new_item --force
3. Cancel: Ctrl+C
```

### Proposed Solution

Update `main()` in `scripts/briefing_generator.py`:

```python
def main():
    """Main entry point."""
    import argparse

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Start session for work item")
    parser.add_argument("work_item_id", nargs="?", help="Specific work item ID to start (optional)")
    parser.add_argument("--force", action="store_true", help="Force start even if another item is in-progress")
    args = parser.parse_args()

    logger.info("Starting session briefing generation")

    # ... existing setup code ...

    # Load data
    work_items_data = load_work_items()
    learnings_data = load_learnings()

    # Determine which work item to start
    if args.work_item_id:
        # User specified a work item explicitly
        item_id = args.work_item_id
        item = work_items_data.get("work_items", {}).get(item_id)

        if not item:
            logger.error("Work item not found: %s", item_id)
            print(f"Error: Work item '{item_id}' not found.")
            return 1

        # Check if another item is in-progress
        in_progress = [
            id for id, wi in work_items_data.get("work_items", {}).items()
            if wi["status"] == "in_progress" and id != item_id
        ]

        if in_progress and not args.force:
            print(f"⚠️  Warning: Work item '{in_progress[0]}' is currently in-progress.")
            print("Complete it first with /end or use --force to override.")
            return 1
    else:
        # Use automatic selection
        item_id, item = get_next_work_item(work_items_data)

        if not item_id:
            logger.warning("No available work items found")
            print("No available work items. All dependencies must be satisfied first.")
            return 1

    logger.info("Generating briefing for work item: %s", item_id)
    # ... rest of function ...
```

### Reproduction Steps

1. Have a work item in "in_progress" status (e.g., from a previous session)
2. Create a new work item
3. Try to start the new work item explicitly: `sdd start <new_work_item_id>`
4. Observe that the old in-progress item is resumed instead
5. Check git branch and briefing - they're for the wrong work item

### Workaround

1. Complete or abandon the in-progress work item first using `/end`
2. Then start the desired work item

OR

1. Manually update `.session/tracking/work_items.json` to change the in-progress item status to `not_started`
2. Then run `sdd start <desired_work_item_id>`

### Related Issues

- None

### Files Affected

- `scripts/briefing_generator.py:586` - `main()` function needs argument parsing
- `sdd_cli.py:73` - Already correctly marked as `needs_argparse=True`

---

## Bug #22: Git Branch Status Not Finalized When Switching Work Items

**Status:** 🟠 HIGH

**Discovered:** 2025-10-23 (During review of Session 1 completed work item)

### Problem

When a work item is completed and a new work item is started, the completed work item's git branch status remains "in_progress" even after the branch has been pushed, PR created, and merged. The git tracking data becomes stale and doesn't reflect the actual state of the branch.

This happens because `/sdd:end` ends a *session*, not a work item. A work item can span multiple sessions, so the git branch should remain "in_progress" as long as the work item is in progress. However, when starting a **new** work item, there's no mechanism to finalize the previous completed work item's git branch status.

### Current Behavior

After completing work item A and starting work item B:

**work_items.json for work item A:**
```json
{
  "status": "completed",
  "git": {
    "branch": "session-001-feature_add_os_specific_files_to_gitig",
    "status": "in_progress"  // ❌ Still shows in_progress
  }
}
```

**Actual git state:**
- Branch merged to main via PR #75
- Branch deleted locally
- PR closed and merged

The git.status is stale and doesn't reflect that the branch was successfully merged.

### Expected Behavior

When starting a new work item, the system should:

1. Check if a previous work item was active
2. If the previous work item is **completed**:
   - Inspect actual git state (branch existence, PR status, merge status)
   - Update git.status to reflect reality: `"merged"`, `"pr_created"`, `"pr_closed"`, `"ready_for_pr"`, etc.
3. If resuming the **same** work item:
   - Keep git.status as "in_progress" (no change needed)

**Expected work_items.json after starting new work item:**
```json
{
  "status": "completed",
  "git": {
    "branch": "session-001-feature_add_os_specific_files_to_gitig",
    "status": "merged"  // ✓ Reflects actual state
  }
}
```

### Root Cause

**Conceptual Issue:**
- `/sdd:end` completes a *session*, not a work item
- A work item can span multiple sessions, so its git branch should stay "in_progress" across sessions
- There's no mechanism to finalize git status when transitioning from one completed work item to a new work item

**Implementation Gap:**
- `scripts/briefing_generator.py` (start command) doesn't check or finalize previous work item's git status
- `scripts/session_complete.py` (end command) shouldn't finalize git status since the work item might continue in another session
- No sync mechanism exists to reconcile SDD's tracking with actual git state

### Impact

- **Severity:** High (data consistency issue)
- **Affected Users:** All users who complete work items and start new ones
- **Data Quality:** work_items.json contains stale git status information
- **User Confusion:** Git status doesn't reflect actual branch state
- **Reporting:** Historical tracking shows incorrect git workflow outcomes
- **Workaround Required:** Manual editing of work_items.json

### Proposed Solution

#### Update `/sdd:start` to Finalize Previous Work Item Git Status

**Location:** `scripts/briefing_generator.py:main()`

**Logic:**
```python
def main():
    """Main entry point."""
    # ... argument parsing ...

    # Load data
    work_items_data = load_work_items()
    learnings_data = load_learnings()

    # Determine which work item to start
    if args.work_item_id:
        item_id = args.work_item_id
        # ... validation ...
    else:
        item_id, item = get_next_work_item(work_items_data)

    # NEW: Finalize previous work item's git status if starting a new work item
    finalize_previous_work_item_git_status(work_items_data, item_id)

    # ... rest of existing logic ...
```

**New Function:**
```python
def finalize_previous_work_item_git_status(work_items_data, current_work_item_id):
    """
    Finalize git status for previous completed work item when starting a new one.

    This handles the case where:
    - Previous work item was completed
    - User performed git operations externally (pushed, created PR, merged)
    - Starting a new work item (not resuming the previous one)

    Args:
        work_items_data: Loaded work items data
        current_work_item_id: ID of work item being started
    """
    work_items = work_items_data.get("work_items", {})

    # Find previously active work item
    previous_work_item = None
    previous_work_item_id = None

    for wid, wi in work_items.items():
        # Skip current work item
        if wid == current_work_item_id:
            continue

        # Find work item with git branch in "in_progress" status
        git_info = wi.get("git", {})
        if git_info.get("status") == "in_progress":
            # Only finalize if work item itself is completed
            if wi.get("status") == "completed":
                previous_work_item = wi
                previous_work_item_id = wid
                break

    if not previous_work_item:
        # No previous work item to finalize
        return

    git_info = previous_work_item.get("git", {})
    branch_name = git_info.get("branch")

    if not branch_name:
        return

    logger.info(
        f"Finalizing git status for completed work item: {previous_work_item_id}"
    )

    # Inspect actual git state
    final_status = determine_git_branch_final_status(branch_name, git_info)

    # Update git status
    work_items[previous_work_item_id]["git"]["status"] = final_status

    # Save updated work items
    work_items_file = Path(".session/tracking/work_items.json")
    with open(work_items_file, "w") as f:
        json.dump(work_items_data, f, indent=2)

    logger.info(
        f"Updated git status for {previous_work_item_id}: in_progress → {final_status}"
    )
    print(f"✓ Finalized git status for previous work item: {previous_work_item_id} → {final_status}\n")


def determine_git_branch_final_status(branch_name, git_info):
    """
    Determine the final status of a git branch by inspecting actual git state.

    Returns one of: "merged", "pr_created", "pr_closed", "ready_for_pr", "deleted", "unknown"
    """
    parent_branch = git_info.get("parent_branch", "main")

    # Check 1: Is branch merged?
    try:
        result = subprocess.run(
            ["git", "branch", "--merged", parent_branch],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and branch_name in result.stdout:
            return "merged"
    except Exception:
        pass

    # Check 2: Does PR exist? (requires gh CLI)
    try:
        result = subprocess.run(
            ["gh", "pr", "list", "--head", branch_name, "--state", "all", "--json", "number,state"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            import json
            prs = json.loads(result.stdout)
            if prs:
                pr = prs[0]  # Get first/most recent PR
                pr_state = pr.get("state", "").upper()

                if pr_state == "MERGED":
                    return "merged"
                elif pr_state == "CLOSED":
                    return "pr_closed"
                elif pr_state == "OPEN":
                    return "pr_created"
    except Exception:
        pass

    # Check 3: Does branch still exist locally?
    try:
        result = subprocess.run(
            ["git", "show-ref", "--verify", f"refs/heads/{branch_name}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            # Branch exists locally, no PR found
            return "ready_for_pr"
    except Exception:
        pass

    # Check 4: Does branch exist remotely?
    try:
        result = subprocess.run(
            ["git", "ls-remote", "--heads", "origin", branch_name],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            # Branch exists remotely, no PR found
            return "ready_for_pr"
    except Exception:
        pass

    # Branch doesn't exist and no PR found
    return "deleted"
```

### Implementation Steps

1. Add `finalize_previous_work_item_git_status()` function to `scripts/briefing_generator.py`
2. Add `determine_git_branch_final_status()` helper function
3. Call finalization function in `main()` before starting new work item
4. Add logging for transparency
5. Handle cases where gh CLI is not available (skip PR detection)
6. Add tests for git state detection logic
7. Update documentation to explain git status lifecycle

### Reproduction Steps

1. Start work item A: `sdd start`
2. Make commits and complete work item A: `/sdd:end` (mark as complete)
3. Manually push branch, create PR, and merge to main
4. Start work item B: `sdd start`
5. Check work_items.json for work item A
6. Observe git.status still shows "in_progress" instead of "merged"

### Workaround

Manually edit `.session/tracking/work_items.json` and update the git.status field for completed work items:

```json
{
  "git": {
    "status": "merged"  // Update manually
  }
}
```

### Related Issues

- Related to Bug #21: Both involve improving /start command behavior
- Both bugs highlight gaps in state management when transitioning work items

### Files Affected

- `scripts/briefing_generator.py` - Add git status finalization logic in `main()`
- `.session/tracking/work_items.json` - Git status data corrected on work item transitions

### Alternative Approaches Considered

**❌ Finalize in `/sdd:end`:**
- Problem: Work item might continue in next session
- Would incorrectly finalize git status for multi-session work items

**❌ Background sync process:**
- Problem: Adds complexity, unclear when to run
- Current approach is simpler and more predictable

**✅ Finalize on `/sdd:start` (Chosen):**
- Natural checkpoint when switching work
- Respects session/work item boundary
- Only finalizes when work is truly complete and new work is starting

---

## Bug #23: Bug Spec Template Missing Acceptance Criteria Section

**Status:** 🟡 MEDIUM

**Discovered:** 2025-10-23 (During Session 3 - Bug #20 implementation)

### Problem

The bug specification template in `templates/bug_spec.md` does not include an "Acceptance Criteria" section. This causes spec validation to fail during `/sdd:validate` because the spec parser expects at least 3 acceptance criteria items for all work item types, including bugs.

### Current Behavior

When creating a bug spec from the template:
1. Template generates a spec file without "Acceptance Criteria" section
2. User fills in all other sections (Description, Root Cause, Fix Approach, etc.)
3. Running `/sdd:validate` fails with "Spec file incomplete" error
4. User must manually add the missing section

**Template currently has:**
- Description
- Steps to Reproduce
- Expected Behavior
- Actual Behavior
- Impact
- Root Cause Analysis
- Fix Approach
- Testing Strategy
- Prevention

**Missing:**
- Acceptance Criteria

### Expected Behavior

The bug spec template should include an "Acceptance Criteria" section with examples, similar to other spec templates (feature, refactor, etc.).

**Expected template structure:**
```markdown
## Acceptance Criteria

- [ ] Bug fix resolves the root cause identified in Root Cause Analysis
- [ ] All test scenarios in Testing Strategy pass
- [ ] No regression in related functionality
```

### Root Cause

**File:** `templates/bug_spec.md`

The template was created before the spec validation system was implemented in Phase 5.7. The validation now requires acceptance criteria for all work item types, but the bug template wasn't updated to include this section.

### Impact

- **Severity:** Medium (workaround available but causes friction)
- **Affected Users:** Anyone creating bug work items
- **User Friction:** Must manually add acceptance criteria section to every bug spec
- **Validation Friction:** Spec validation fails unnecessarily, confusing users
- **Documentation Gap:** Users don't know what acceptance criteria to write for bugs

### Proposed Solution

Update `templates/bug_spec.md` to include an "Acceptance Criteria" section after "Fix Approach" and before "Testing Strategy":

```markdown
## Fix Approach

[Detailed approach to fixing the bug...]

## Acceptance Criteria

<!-- Define specific, measurable criteria for considering this bug fixed -->
- [ ] [Specific fix criterion related to root cause]
- [ ] [Specific fix criterion related to behavior]
- [ ] [Specific fix criterion related to testing]
- [ ] [Add more as needed - minimum 3 required]

## Testing Strategy
```

**Recommended acceptance criteria for bugs:**
1. Root cause is addressed (not just symptoms)
2. All reproduction steps no longer trigger the bug
3. Comprehensive test coverage prevents regression
4. No new bugs introduced by the fix
5. Edge cases identified in testing strategy are handled

### Reproduction Steps

1. Run `sdd work-new` and select "bug" type
2. Fill in the generated spec file from template
3. Complete all sections except acceptance criteria (since it's not in template)
4. Run `sdd validate`
5. Observe validation failure: "Spec file incomplete - Acceptance Criteria (at least 3 items)"
6. Manually add acceptance criteria section

### Workaround

Manually add the "Acceptance Criteria" section to bug specs after creation:

```markdown
## Acceptance Criteria

- [ ] Bug is fixed and root cause is addressed
- [ ] All test scenarios pass
- [ ] No regression in related functionality
```

### Related Issues

- Discovered during Session 3 while fixing Bug #20
- Related to Phase 5.7 spec validation implementation
- Bug template needs to align with spec parser expectations (`scripts/spec_parser.py`)

### Files Affected

- `templates/bug_spec.md` - Add Acceptance Criteria section
- Potentially `templates/refactor_spec.md` and other templates - verify they all have this section

---

## Bug #24: Learning Curator Extracts Test Data Strings as Real Learnings

**Status:** 🟠 HIGH

**Discovered:** 2025-10-23 (During Session 3 - Bug #20 testing/dogfooding)

### Problem

The learning curator extracts Python string literals from test files as if they were real LEARNING statements. When test files contain strings like `"Valid code learning with enough words here"` in test data, these get extracted as actual learnings, polluting the learnings database with garbage entries.

### Current Behavior

After implementing Bug #20 fixes and running `/sdd:end`, the learnings.json contains garbage entries from test file strings:

```json
{
  "content": "annotations\n- Code comments - Extract # LEARNING: inline comments",
  "learned_in": "unknown",
  "source": "git_commit",
  "context": "Commit 9d32c883",
  "timestamp": "2025-10-23T13:19:53.069055",
  "id": "41cb7f06"
},
{
  "content": "Valid code learning with enough words here\")",
  "learned_in": "unknown",
  "source": "inline_comment",
  "context": "test_learning_curator_bug_fixes.py:152",
  "timestamp": "2025-10-23T13:19:53.088569",
  "id": "83323749"
},
{
  "content": "Valid code learning from main file with words\")",
  "learned_in": "unknown",
  "source": "inline_comment",
  "context": "test_learning_curator_bug_fixes.py:174",
  "timestamp": "2025-10-23T13:19:53.089708",
  "id": "ee61be3f"
},
{
  "content": "Example learning from template directory here\")",
  "learned_in": "unknown",
  "source": "inline_comment",
  "context": "test_learning_curator_bug_fixes.py:176",
  "timestamp": "2025-10-23T13:19:53.090501",
  "id": "bc794b20"
}
```

**Problems:**
1. Test data strings are extracted as learnings
2. Malformed content with trailing `")` characters
3. Truncated/fragment content from commit diffs
4. Test files should be excluded from learning extraction

### Expected Behavior

Test files and test data should never be extracted as learnings:
- `tests/` directory should be completely excluded
- String literals in test code should not be extracted
- Only actual `# LEARNING:` comments in production code should be extracted
- Malformed content (with `"`, `)`, `\` characters) should be rejected

### Root Cause

**Multiple issues in `scripts/learning_curator.py`:**

1. **Test directory not excluded** - File type filtering added in Bug #20 fix only excludes documentation extensions (`.md`, `.txt`, `.rst`) and `examples/`, `templates/` directories, but doesn't exclude `tests/` directory

2. **Pattern matching too broad** - The regex pattern `r"#\s*LEARNING:\s*(.+?)$"` matches any line containing this pattern, including Python string literals:
   ```python
   self.code_file.write_text("# LEARNING: Valid code learning with enough words here")
   ```
   This line in test code gets matched and extracts the string content

3. **Content validation insufficient** - `is_valid_learning()` checks for `<` `>` angle brackets and known placeholders, but doesn't detect:
   - Trailing quote and parenthesis characters (`")`)
   - String escape sequences (`\"`)
   - Other code syntax artifacts

### Impact

- **Severity:** High (pollutes learnings database with garbage)
- **Data Quality:** Learnings database contains test data and malformed entries
- **User Confusion:** Real learnings mixed with garbage entries
- **Curation Overhead:** Manual cleanup required to remove test artifacts
- **Trust Issues:** Users lose confidence in automated learning extraction

### Proposed Solution

#### Fix 1: Exclude Test Directories

Update `extract_from_code_comments()` in `scripts/learning_curator.py`:

```python
def extract_from_code_comments(self, changed_files: list[Path] = None, session_id: str = None) -> list[dict]:
    # ... existing code ...

    # Only scan actual code files, not documentation or tests
    code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs'}
    doc_extensions = {'.md', '.txt', '.rst'}
    excluded_dirs = {'examples', 'templates', 'tests', 'test', '__tests__', 'spec'}  # ← Add test directories

    for file_path in changed_files:
        # ... existing checks ...

        # Skip test directories
        if any(excluded_dir in file_path.parts for excluded_dir in excluded_dirs):
            continue

        # ... rest of extraction ...
```

#### Fix 2: Improve Content Validation

Enhance `is_valid_learning()` to detect code artifacts:

```python
def is_valid_learning(self, content: str) -> bool:
    """Check if extracted content is a valid learning (not placeholder/garbage)."""
    if not content or not isinstance(content, str):
        return False

    # Skip placeholders and examples (content with angle brackets)
    if '<' in content or '>' in content:
        return False

    # NEW: Skip content with code syntax artifacts
    code_artifacts = [
        '")',  # String literal ending
        '\"',  # Escaped quotes
        '\\n', # Escape sequences (visible in extracted content)
        '`',   # Backticks
    ]
    if any(artifact in content for artifact in code_artifacts):
        return False

    # NEW: Skip if content looks like a code fragment (ends with quote/paren)
    if content.strip().endswith(('")' , '";', '`,', "')", "';")):
        return False

    # Skip known placeholder text
    content_lower = content.lower().strip()
    placeholders = [
        'your learning here',
        'example learning',
        'todo',
        'tbd',
        'placeholder'
    ]
    if content_lower in placeholders:
        return False

    # Must have substance (more than just a few words)
    if len(content.split()) < 5:
        return False

    return True
```

#### Fix 3: Only Extract from Actual Comments

Update the regex pattern to be more strict about comment context:

```python
# Current pattern (too broad):
learning_pattern = r"#\s*LEARNING:\s*(.+?)$"

# Better pattern (only matches actual comments):
learning_pattern = r"^\s*#\s*LEARNING:\s*(.+?)$"  # Must start at line beginning (with optional whitespace)
```

This ensures we only match actual comment lines, not string literals containing the pattern.

### Reproduction Steps

1. Create a test file with test data strings containing "# LEARNING:" pattern:
   ```python
   def test_example():
       test_data = "# LEARNING: This is test data"
       file.write_text("# LEARNING: Another test string")
   ```
2. Run `/sdd:end` to complete session
3. Check `.session/tracking/learnings.json`
4. Observe test data strings extracted as learnings

### Workaround

Manually edit `.session/tracking/learnings.json` to remove:
1. All entries from `tests/` directory (check `context` field)
2. All entries with malformed content (ending in `")`, containing `\"`, etc.)
3. All entries that look like code fragments rather than complete sentences

### Related Issues

- Bug #20: Original learning curator bugs (partially addressed, but missed test directory exclusion)
- Enhancement #6: Work item completion status control (discovered during same dogfooding session)

### Files Affected

- `scripts/learning_curator.py` - `extract_from_code_comments()` method needs test directory exclusion
- `scripts/learning_curator.py` - `is_valid_learning()` method needs better artifact detection
- `.session/tracking/learnings.json` - Currently contains garbage entries that need cleanup

### Priority

High - Impacts data quality and user trust in automated learning extraction. Should be fixed before Bug #20 is considered fully resolved.

---

## Bug Template

```markdown
## Bug #XX: [Title]

**Status:** 🔴/🟠/🟡/🟢/✅

**Discovered:** YYYY-MM-DD

### Problem
Brief description of the bug

### Current Behavior
What happens now

### Expected Behavior
What should happen

### Root Cause
Why this happens

### Impact
Effect on users/system

### Proposed Solution
How to fix it

### Reproduction Steps
1. Step 1
2. Step 2
3. Observe issue

### Workaround
Temporary fix if available

### Related Issues
Links or references

### Files Affected
- file1.py
- file2.py
```
