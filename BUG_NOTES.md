# Active Bugs - Session-Driven Development

This document tracks currently unfixed bugs discovered during testing and development.

**Last Updated:** 2025-10-22 after comprehensive end-to-end testing

---

## Bug #12: Stack and Tree Generation Fails Due to Path Resolution

**Status:** ✅ FIXED

**Issue:** Stack.txt and tree.txt are never successfully generated, failing in TWO places:

1. During `sdd init`:
```
⚠️  Could not generate stack.txt (will be generated on first session)
⚠️  Could not generate tree.txt (will be generated on first session)
```

2. During `sdd end`:
```
⚠️  Stack update failed (exit code 2)
  Error: python: can't open file '/Users/.../test-project/scripts/generate_stack.py': [Errno 2] No such file or directory
⚠️  Tree update failed (exit code 2)
  Error: python: can't open file '/Users/.../test-project/scripts/generate_tree.py': [Errno 2] No such file or directory
```

**Root Cause:** Incorrect path resolution in **two scripts**:

1. `scripts/init_project.py:226,233`:
```python
subprocess.run(["python", "scripts/generate_stack.py"], ...)
subprocess.run(["python", "scripts/generate_tree.py"], ...)
```

2. `scripts/session_complete.py:119,147`:
```python
subprocess.run(["python", "scripts/generate_stack.py", "--session", str(session_num), ...])
subprocess.run(["python", "scripts/generate_tree.py", "--session", str(session_num), ...])
```

Both try to find `scripts/` in the **user's project directory** (e.g., `test-flow/scripts/`), but the scripts are in the **SDD installation directory** (e.g., `/Users/user/Projects/sdd/scripts/` or `/opt/anaconda3/lib/python3.x/site-packages/sdd/scripts/`).

**Impact:**
- Stack.txt and tree.txt are **never updated** after initial creation
- Briefings may have stale project context throughout sessions
- Context7 validation may fail if it depends on updated stack.txt
- No workaround exists - files are not regenerated during sessions

**Expected Behavior:**
- `sdd init` should successfully generate initial stack.txt and tree.txt
- `sdd end` should successfully update stack.txt and tree.txt after each session
- Both files should be updated in `.session/tracking` directory
- All sessions should have current project context

**Suggested Fix:**
Use absolute path resolution like other SDD scripts:

In `init_project.py`:
```python
def run_initial_scans():
    """Run initial stack and tree scans."""
    print("\nRunning initial scans...")

    # Get SDD installation directory
    script_dir = Path(__file__).parent  # Points to SDD scripts directory

    # Run generate_stack.py with absolute path
    try:
        subprocess.run(
            ["python", str(script_dir / "generate_stack.py")],
            check=True,
            capture_output=True
        )
        print("✓ Generated stack.txt")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Could not generate stack.txt: {e}")
```

In `session_complete.py` lines 119 and 147:
```python
# Get script directory for absolute path
script_dir = Path(__file__).parent

# Use absolute paths
subprocess.run(["python", str(script_dir / "generate_stack.py"), "--session", str(session_num), ...])
subprocess.run(["python", str(script_dir / "generate_tree.py"), "--session", str(session_num), ...])
```

**Verification:**
- Confirmed in test-flow test: Files exist but timestamps show they weren't updated during `sdd end`
- Initial files created at 16:20 during init
- Session ended at 16:38 but files not updated

**Priority:** High (project context becomes stale across sessions)

---

## Bug #14: Init-Generated Test File Has Linting Errors

**Status:** ✅ FIXED

**Issue:** When `sdd init` creates the TypeScript setup test file (`tests/sdd-setup.test.ts`), it contains linting errors that cause quality gate failures:

```
/path/to/tests/sdd-setup.test.ts
  2:10  error  'resolve' is defined but never used             @typescript-eslint/no-unused-vars
  6:17  error  Require statement not part of import statement  @typescript-eslint/no-var-requires
```

**Root Cause:**
Template in `scripts/init_project.py` generates code that doesn't comply with ESLint TypeScript rules:
- Imports `resolve` from 'path' but never uses it
- Uses `require()` for package.json instead of ES6 import

**Impact:**
- First `sdd validate` or `sdd end` command fails on linting
- User must manually fix auto-generated test file before session can complete
- Creates confusion - tests pass, but quality gates fail
- Poor developer experience for new projects

**Expected Behavior:**
- Init-generated test files should pass all quality gates without modification
- Should use ES6 imports consistently
- Should not import unused modules

**Suggested Fix:**
Update the TypeScript test template in `init_project.py` (around line 500-520):

Current code:
```typescript
import { existsSync } from 'fs';
import { resolve } from 'path';

describe('SDD Project Setup', () => {
  it('should have valid package.json', () => {
    const pkg = require('../package.json');
    expect(pkg.name).toBeDefined();
    expect(pkg.version).toBeDefined();
  });
```

Fixed code:
```typescript
import { existsSync } from 'fs';
import pkg from '../package.json';

describe('SDD Project Setup', () => {
  it('should have valid package.json', () => {
    expect(pkg.name).toBeDefined();
    expect(pkg.version).toBeDefined();
  });
```

**Verification:**
- Discovered during test-flow testing
- Required manual fix to pass linting quality gate
- Also ensure `tsconfig.json` has `"resolveJsonModule": true` for JSON imports

**Priority:** High (blocks quality gates on fresh projects, poor UX)

---

## Bug #15: Git Commits Not Tracked in Work Items

**Status:** ✅ FIXED

**Issue:** When commits are made during a session and tracked in git, the commit information is not recorded in `work_items.json`. The `git.commits` array remains empty even after successful commits.

**Root Cause:**
`scripts/session_complete.py` or `scripts/briefing_generator.py` does not update the work item's `git.commits` array when commits are created during the session.

**Example:**
After completing session with commit `d24585e`, work_items.json shows:
```json
"git": {
  "branch": "session-001-feature_implement_calculator_core",
  "parent_branch": "fix/bug-11-work-new-non-interactive",
  "created_at": "2025-10-22T16:28:31.844685",
  "status": "in_progress",
  "commits": []  // ❌ Should contain commit d24585e
}
```

**Impact:**
- No record of what commits were made during each session
- Cannot track progress or review session changes via work item metadata
- Harder to audit work done in each session
- Git integration incomplete

**Expected Behavior:**
- After each commit during a session, update work_items.json with commit info:
  - Commit SHA
  - Commit message
  - Timestamp
  - Files changed (optional)

**Suggested Fix:**
Either:
1. Hook into git commit process to automatically update work_items.json
2. During `sdd end`, scan git log for commits on session branch and record them
3. Provide git commit wrapper that records to work_items.json

Recommended approach:
```python
# In session_complete.py after git operations
def record_session_commits(work_item_id, branch_name):
    """Record commits made during session to work item tracking."""
    # Get commits on session branch
    result = subprocess.run(
        ["git", "log", "--pretty=format:%H|%s|%ai", f"{parent_branch}..{branch_name}"],
        capture_output=True,
        text=True
    )

    commits = []
    for line in result.stdout.strip().split('\n'):
        if line:
            sha, message, timestamp = line.split('|', 2)
            commits.append({
                "sha": sha,
                "message": message,
                "timestamp": timestamp
            })

    # Update work_items.json
    work_items_data = load_json(work_items_file)
    work_items_data["work_items"][work_item_id]["git"]["commits"] = commits
    save_json(work_items_file, work_items_data)
```

**Verification:**
- Confirmed in test-flow testing: Made commit d24585e but commits array stayed empty
- Work item shows git branch correctly but no commit tracking

**Priority:** Medium (tracking/auditing feature, doesn't block workflow)

---

## Bug #16: Learnings Not Extracted in Non-Interactive Mode

**Status:** ✅ FIXED

**Issue:** When running `sdd end` in non-interactive mode (via Claude Code), learnings are not automatically extracted from session artifacts. The `learnings.json` file remains empty despite session work being completed.

**Output seen:**
```
Auto-extracting learnings from session artifacts...
No new learnings extracted

Skipping manual learning extraction (non-interactive mode)
```

**Root Cause:**
`scripts/session_complete.py` has two learning extraction paths:
1. Auto-extraction from session artifacts (appears not to work)
2. Manual input prompts (skipped in non-interactive mode)

The auto-extraction either:
- Is not implemented
- Doesn't find any learnings in session artifacts
- Has bugs preventing extraction

**Impact:**
- Knowledge from sessions is not captured automatically
- No learnings accumulate over time in non-interactive workflows
- Defeats the purpose of the learning system for Claude Code usage
- Manual workaround required to capture learnings

**Expected Behavior:**
- Auto-extract learnings from:
  - Commit messages
  - Code comments marked with specific tags
  - Session briefing notes
  - Error messages and fixes
  - Test results and coverage improvements
- Store extracted learnings to `learnings.json` automatically
- Provide summary of learnings captured

**Suggested Fix:**

Option 1: Enhance auto-extraction in `session_complete.py`:
```python
def auto_extract_learnings_from_session(session_dir, work_item_type):
    """Extract learnings from session artifacts."""
    learnings = []

    # 1. Extract from commit messages
    commits = get_session_commits()
    for commit in commits:
        # Look for learning indicators in commit messages
        if any(keyword in commit.message.lower() for keyword in ['learned', 'gotcha', 'important', 'note']):
            learnings.append({
                "content": f"From commit: {commit.message}",
                "category": "best_practices",
                "source": "commit_message"
            })

    # 2. Extract from code comments
    # Look for comments with specific markers: # LEARNING:, // TODO:, etc.

    # 3. Extract from test results
    # Failed tests that were fixed = gotchas

    return learnings
```

Option 2: Support learnings via command-line argument:
```bash
sdd end --learnings-file .session/temp_learnings.txt
```

Option 3: Create learnings file during session and parse at end:
```
# During session, Claude Code writes to:
.session/tracking/session_001_learnings.txt

# At end, parse and add to learnings.json
```

**Verification:**
- Confirmed in test-flow testing: learnings.json remained empty after session
- Auto-extraction reported "No new learnings extracted"

**Priority:** Medium (learning system not functioning in Claude Code workflows)

---

## Bug #17: Work Item Metadata Counter Not Updated on New Work Items

**Status:** 🟡 PARTIALLY FIXED

**Issue:** When creating new work items via `sdd work-new`, metadata counters in `work_items.json` are not updated to reflect the new totals.

**Fix Applied:**
Updated `scripts/work_item_manager.py` `_add_to_tracking()` method (lines 377-386) to calculate and update all metadata counters when adding work items:
```python
# Update metadata counters
if "metadata" not in data:
    data["metadata"] = {}

work_items = data.get("work_items", {})
data["metadata"]["total_items"] = len(work_items)
data["metadata"]["completed"] = sum(1 for item in work_items.values() if item["status"] == "completed")
data["metadata"]["in_progress"] = sum(1 for item in work_items.values() if item["status"] == "in_progress")
data["metadata"]["blocked"] = sum(1 for item in work_items.values() if item["status"] == "blocked")
data["metadata"]["last_updated"] = datetime.now().isoformat()
```

**Remaining Issue:**
This fix is only in the uncommitted changes. Needs to be:
1. Committed to a branch
2. Tested
3. Merged to main

Also need to verify that other operations that change work items also update metadata:
- `sdd work-update` - status changes
- `sdd start` - status changes to in_progress
- `sdd end` - status changes to completed (if user confirms)

**Status:** Fix exists but not committed/deployed

**Priority:** Medium (cosmetic, but important for accurate project tracking)

---

## Bug #18: Learning Extraction Fails with Multi-Paragraph Commits

**Status:** ✅ FIXED (fix/bug-18-19-learning-work-completion)

**Issue:** The learning extraction from git commits fails when commit messages have multiple paragraphs. The `LEARNING:` tag is not found even when present.

**Root Cause:** In `scripts/learning_curator.py` line 573, the code splits commit messages by `\n\n`:
```python
commits = result.stdout.split("\n\n")
```

This breaks multi-paragraph commit messages into separate blocks. Only the first block contains `|||`, so subsequent blocks (which may contain `LEARNING:` tags) are skipped.

**Example:**
```
Commit message:
  Line 1|||Title

  Paragraph 2

  LEARNING: Something important
```

Gets split into:
- Block 0: "Line 1|||Title" (has |||, checked)
- Block 1: "Paragraph 2" (no |||, skipped)
- Block 2: "LEARNING: Something..." (no |||, skipped!)

**Impact:** Learnings in commit messages are never extracted, defeating the auto-learning feature.

**Suggested Fix:**
Parse each full commit block before splitting, not after:
```python
# Split by commit separator (double newline + hash)
commit_pattern = r'([a-f0-9]{40}\|\|\|.+?)(?=\n[a-f0-9]{40}\|\|\||$)'
for match in re.finditer(commit_pattern, result.stdout, re.DOTALL):
    commit_block = match.group(1)
    commit_hash, message = commit_block.split('|||', 1)
    # Now search full message for LEARNING:
    ...
```

**Priority:** Medium (learnings feature not functioning)

---

## Bug #19: Non-Interactive Work Completion Always Defaults to 'n'

**Status:** ✅ FIXED (fix/bug-18-19-learning-work-completion)

**Issue:** When running `sdd end` in non-interactive mode (Claude Code), work items are never marked as completed automatically, even when all acceptance criteria are met.

**Output:**
```
Is work item 'Basic calculator (add, subtract)' complete? (y/n):
> (non-interactive mode: defaulting to 'n')
```

**Root Cause:** `session_complete.py` prompts for work completion confirmation but defaults to 'n' in non-interactive mode, leaving items perpetually in_progress.

**Impact:**
- Work items never reach completed status automatically
- Dependency chains don't progress
- Manual `sdd work-update` required after every session

**Suggested Fix:**
In non-interactive mode, automatically mark work as complete if all quality gates pass and there are no validation errors.

**Priority:** Medium (workflow inconvenience, manual workaround available)

---

## Summary of Critical Issues

**Fixed in fix/bug-12-stack-tree-path-resolution branch:**
- Bug #12: Stack/tree generation broken ✅ FIXED
- Bug #14: Init-generated tests fail linting ✅ FIXED
- Bug #15: Commits not tracked in work items ✅ FIXED
- Bug #16: Learnings not extracted ✅ FIXED

**Previously Fixed:**
- Bug #11: work-new non-interactive mode ✅ (committed to fix/bug-11-work-new-non-interactive)
- Bug #17: Metadata counters ✅ (committed to main)

---

## Testing Notes

All bugs verified during end-to-end testing with test-flow project (2025-10-22).

Test flow executed:
1. ✅ `sdd init` - created TypeScript project
2. ✅ `sdd work-new --type feature --title "..."` - created 3 work items
3. ✅ Filled spec files manually
4. ✅ `sdd start` - started session 001
5. ✅ Implemented calculator with tests
6. ✅ `sdd validate` - all quality gates passed after fixes
7. ✅ `sdd end` - completed session

Issues discovered during steps above are documented in this file.
