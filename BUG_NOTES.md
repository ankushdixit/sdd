# Additional Bugs Found During Testing

## Bug #5: Session Number Increments on Resume

**Issue:** When calling `sdd start` on an already in-progress work item, a new session number and briefing file is created instead of reusing the existing session.

**Root Cause:** In `scripts/briefing_generator.py` lines 614-617, session number always increments based on existing briefing files without checking if work item is already in progress.

**Expected Behavior:**
- If work item status is already "in_progress", reuse the existing session number
- Only create new session number when starting work item for first time

**Priority:** Medium

---

## Bug #6: init_project.py Has Outdated Default Commands

**Issue:** `sdd init` creates `.session/config.json` with old commands (`eslint .`, `prettier --write .`) instead of new npx-based commands.

**Root Cause:** `scripts/init_project.py` has its own hardcoded default config (lines 134-145) that wasn't updated when Bug #4 was fixed in `quality_gates.py`.

**Impact:** New projects initialized after Bug #4 fix still get old commands and won't work with locally-installed tools.

**Expected Behavior:**
- `init_project.py` should use same default commands as `quality_gates.py`
- Both should use `npx eslint` and `npx prettier` for JS/TS projects

**Priority:** High (directly related to Bug #4 fix)

---

## Bug #7: Milestone Items Missing ID Field

**Issue:** When calling `sdd start` on a work item with a milestone, briefing generation fails with `KeyError: 'id'`.

**Root Cause:** In `scripts/briefing_generator.py` lines 136-140, the `milestone_items` list is built from `items.values()` which doesn't include the work item IDs (dictionary keys). Later at line 405, the code tries to access `related_item["id"]` which doesn't exist.

**Impact:** Cannot start sessions for work items that belong to a milestone.

**Expected Behavior:**
- Milestone items should include their ID in the data structure
- Related items should be compared using the work item ID parameter

**Fix Applied:**
- Updated line 136-140 to include ID when building milestone_items list
- Changed line 405 to compare with `item_id` parameter instead of `item.get("id")`

**Priority:** High (blocks session start for milestone work items)

---

## Bug #8: Work Items Metadata Counters Not Updating

**Issue:** When work item status changes (e.g., from `in_progress` to `completed`), the metadata counters in `work_items.json` don't update. Shows stale values like `"completed": 0, "in_progress": 1` even after work item marked completed.

**Root Cause:**
- In `scripts/session_complete.py`, work item status is updated but metadata counters aren't recalculated before saving
- In `scripts/briefing_generator.py`, only `in_progress` counter was updated, not all counters

**Impact:** Metadata counters are inaccurate, showing wrong project status.

**Expected Behavior:**
- All metadata counters (`total_items`, `completed`, `in_progress`, `blocked`) should be recalculated whenever a work item status changes
- `last_updated` timestamp should be updated

**Fix Applied:**
- Added metadata counter update in `session_complete.py` before saving work_items.json
- Enhanced `briefing_generator.py` to update all counters, not just `in_progress`

**Priority:** Medium (cosmetic issue, doesn't block functionality)

---

## Bug #9: Session End Requires Interactive Input

**Issue:** `sdd end` command prompts for interactive input (learnings, work item completion status), which fails when run by Claude Code in non-interactive mode with `EOFError`.

**Root Cause:**
- `scripts/session_complete.py` lines 264-275: Uses `input()` without checking if stdin is a tty
- Lines 590-592: Also uses `input()` for work item completion status
- No handling for EOF errors when stdin is closed

**Impact:**
- Claude Code cannot run `sdd end` non-interactively without piping responses
- Learnings extraction fails in automated workflows
- Blocks automation of SDD workflow

**Expected Behavior:**
- Detect non-interactive mode (when stdin is not a tty)
- Skip manual learning extraction in non-interactive mode
- Default work item completion to 'no' in non-interactive mode
- Handle EOFError gracefully

**Fix Applied:**
- Added `sys.stdin.isatty()` check in `extract_learnings_from_session()`
- Added `sys.stdin.isatty()` check for work item completion prompt
- Added EOFError exception handling for both input prompts
- Print informative messages when skipping interactive prompts

**Future Enhancement:**
- Add command-line flags like `--complete` / `--incomplete` to `sdd end`
- Allow Claude Code to pass learnings via arguments or file
- Enable fully non-interactive session completion

**Priority:** High (blocks Claude Code automation)

---

## Bug #10: init_project.py Doesn't Validate Project Setup

**Issue:** `sdd init` creates `.session/` directory and config.json with quality gate commands (like `npx eslint`, `npm test`) without checking if the project has the necessary files and dependencies for those commands to work.

**Root Cause:** `scripts/init_project.py` doesn't perform any project validation before initialization:
- No project type detection (unlike `quality_gates.py` which has `_detect_language()`)
- No check for required config files (`package.json`, `tsconfig.json`, `.eslintrc.json`, `.prettierrc` for Node/TS projects)
- No check for installed dependencies (`node_modules/` for Node, `venv/` for Python)
- Creates config.json with commands that will fail if dependencies aren't installed

**Impact:**
Different scenarios produce different failures:

| Scenario | What Happens | Result |
|----------|--------------|--------|
| Blank project (no files) | `/sdd:init` succeeds | `/sdd:validate` fails: `npx eslint` fails (no package.json) |
| Has package.json only | `/sdd:init` succeeds | `/sdd:validate` fails: `npx eslint` fails (no node_modules) |
| Has package.json + configs | `/sdd:init` succeeds | `/sdd:validate` fails: `npx eslint` fails (no node_modules) |
| Fully set up (configs + deps) | `/sdd:init` succeeds | All quality gates work ✓ |

**Expected Behavior:**
- Detect project type (Python, JavaScript, TypeScript) using same logic as `quality_gates.py:208-219`
- Check for required config files based on project type
- Check for installed dependencies
- Provide actionable guidance if setup is incomplete:
  - "No package.json found. Create one with: npm init -y"
  - "Dependencies not installed. Run: npm install"
  - "Missing ESLint config. Create .eslintrc.json"
- Either:
  - Block initialization until setup is complete, OR
  - Create minimal config files and guide user to install dependencies

**Suggested Fix:**
Add a `validate_project_setup()` function to `init_project.py` that runs before creating `.session/`:
1. Detect project type (reuse logic from quality_gates.py)
2. Check for type-specific requirements (package.json for Node, pyproject.toml for Python)
3. Check for config files (.eslintrc, .prettierrc, tsconfig.json)
4. Check for installed dependencies (node_modules/, venv/)
5. Print helpful setup instructions for missing items
6. Ask user whether to continue or abort

**Priority:** High (affects project onboarding experience and can cause confusing failures later)

---

## Bug #11: work-new Command Requires Interactive Input ✅ FIXED

**Issue:** `sdd work-new` only works in interactive mode, requiring user to respond to prompts. This fails when run by Claude Code or in automated workflows with `EOFError`.

**Root Cause:** `scripts/work_item_manager.py:44-107` - The `create_work_item()` method uses `input()` without:
- Checking if stdin is a tty (`sys.stdin.isatty()`)
- Handling EOFError exceptions
- Supporting command-line arguments for non-interactive creation

**Impact:**
- Claude Code cannot create work items programmatically
- Automated testing requires manual intervention
- CI/CD pipelines cannot create work items
- Users must manually create work items or directly edit JSON files

**Fix Applied:**

1. **Updated `scripts/work_item_manager.py`:**
   - Added `sys.stdin.isatty()` check at the start of `create_work_item()` (line 49)
   - Added EOFError exception handling around all `input()` calls (lines 61-96)
   - Provided helpful error messages directing users to command-line arguments
   - Also updated `update_work_item_interactive()` with same protections (line 884)

2. **Updated `sdd_cli.py`:**
   - Added `parse_work_new_args()` function to parse command-line arguments (lines 103-121)
   - Supports both long and short flags: `--type/-t`, `--title/-T`, `--priority/-p`, `--dependencies/-d`
   - Updated routing logic to detect arguments and call appropriate method (lines 204-220)
   - If arguments provided: calls `create_work_item_from_args()` (non-interactive)
   - If no arguments: calls `create_work_item()` (interactive with proper error handling)

**Non-Interactive Usage:**
```bash
# Full form
sdd work-new --type feature --title "Implement calculator" --priority high --dependencies "dep1,dep2"

# Short form
sdd work-new -t feature -T "Implement calculator" -p high -d "dep1,dep2"

# Minimal (priority defaults to 'high')
sdd work-new --type bug --title "Fix login issue"
```

**Testing:**
Verified that:
- ✅ Non-interactive mode works with both long and short flags
- ✅ Dependencies are parsed correctly from comma-separated list
- ✅ Interactive mode detects non-tty environment and provides helpful error
- ✅ EOFError is handled gracefully with informative messages
- ✅ Both modes coexist seamlessly

**Related Issues:**
- Similar to Bug #9 (session end requiring interactive input) - both now fixed
- Both blocked Claude Code automation
- Both now support command-line argument mode

**Priority:** High (blocks automation and Claude Code usage) - **RESOLVED**

---

## Bug #12: Stack and Tree Generation Fails Due to Path Resolution

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

Both try to find `scripts/` in the **user's project directory** (e.g., `test-project/scripts/`), but the scripts are in the **SDD installation directory** (e.g., `/Users/user/Projects/sdd/scripts/` or `/opt/anaconda3/lib/python3.x/site-packages/sdd/scripts/`).

**Impact:**
- Stack.txt and tree.txt are **never created at all** (fails in both init and end)
- Briefings completely lack project context throughout all sessions
- Context7 validation may fail if it depends on stack.txt
- No workaround exists - files are simply never generated

**Expected Behavior:**
- `sdd init` should successfully generate initial stack.txt and tree.txt
- `sdd end` should successfully update stack.txt and tree.txt after each session
- Both files should be created in `.session/tracking` directory
- All sessions should have full project context

**Suggested Fix:**
Use absolute path resolution like other SDD scripts:
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

    # Similar fix for generate_tree.py
```

**Also fix in `session_complete.py` lines 119 and 147:**
- Use `str(Path(__file__).parent / "generate_stack.py")` instead of `"scripts/generate_stack.py"`
- Use `str(Path(__file__).parent / "generate_tree.py")` instead of `"scripts/generate_tree.py"`

**Related Issues:**
- This is NOT fixed by Bug #10 (which is about project setup validation)
- This is a path resolution issue specific to subprocess calls
- Other SDD scripts use `Path(__file__).parent` correctly

**Priority:** High (stack and tree are completely missing from all sessions, no workaround exists)

---

## Enhancement #1: Create Initial Smoke Tests During init

**Proposal:** `sdd init` should create a minimal test suite with basic smoke tests that validate the project setup and SDD initialization.

**Rationale:**
- Quality gates require tests to pass, but new projects often start without tests
- Work items focused on implementation (like FT-001) shouldn't need to add tests immediately
- Having baseline tests prevents quality gate failures and validates proper setup
- Provides test structure examples for developers

**Suggested Implementation:**

For **TypeScript/JavaScript** projects:
```typescript
// tests/sdd-setup.test.ts
describe('SDD Project Setup', () => {
  it('should have valid package.json', () => {
    const pkg = require('../package.json');
    expect(pkg.name).toBeDefined();
    expect(pkg.version).toBeDefined();
  });

  it('should have .session directory structure', () => {
    expect(fs.existsSync('.session/tracking')).toBe(true);
    expect(fs.existsSync('.session/specs')).toBe(true);
  });

  it('should have required config files', () => {
    expect(fs.existsSync('tsconfig.json')).toBe(true);
    expect(fs.existsSync('.eslintrc.json')).toBe(true);
  });
});
```

For **Python** projects:
```python
# tests/test_sdd_setup.py
def test_project_structure():
    """Verify SDD project structure exists."""
    assert Path('.session/tracking').exists()
    assert Path('.session/specs').exists()
    assert Path('pyproject.toml').exists() or Path('setup.py').exists()
```

**Benefits:**
- ✅ Quality gates pass immediately after `sdd init`
- ✅ Validates project setup is correct
- ✅ Provides test examples for developers
- ✅ Work items can focus on implementation without immediate test requirements
- ✅ Tests can be expanded/replaced as real features are added

**Implementation Details:**
1. Detect project type (same logic as Bug #10 fix)
2. Create `tests/` directory during `sdd init`
3. Generate language-appropriate setup tests
4. Tests should be clearly labeled as "SDD Setup Validation"
5. Update `.gitignore` to ensure tests/ is tracked

**Related Issues:**
- Bug #10 (project setup validation) - shares project type detection logic
- Current issue: FT-001 work item fails validation because no tests exist

**Priority:** Medium (enhancement, not a bug - but significantly improves UX)

---

## Bug #13: Learning Curator Fails to Process String-Format Learnings ✅ FIXED

**Issue:** When learnings are provided via `--learnings-file` as plain text strings (one per line), the learning curator fails with error: `'str' object has no attribute 'get'`

**Reproduction:**
1. Create `.session/temp_learnings.txt` with plain text learnings
2. Run `sdd end --learnings-file .session/temp_learnings.txt`
3. Learnings are displayed in summary but error occurs: "Failed to process learnings: 'str' object has no attribute 'get'"
4. Check `learnings.json` - learnings were NOT saved (file remains empty)

**Root Cause:** Format mismatch between `session_complete.py` (sends strings) and `learning_curator.py` (expects dicts).

In `session_complete.py:622`:
- `extract_learnings_from_session()` returns list of **strings**

In `session_complete.py:632`:
- Strings passed directly to `curator.add_learning_if_new(learning)`

In `learning_curator.py:653-661`:
- `add_learning_if_new(learning_dict)` expects **dict**
- Calls `learning_dict.get("content", "")` which fails on strings

**Impact:**
- Auto-learnings feature appears to work (displays learnings in summary)
- But learnings are NOT persisted to `learnings.json`
- Users think learnings are saved but they're lost after session ends
- Defeats the purpose of capturing institutional knowledge

**Fix Applied:**
Updated `session_complete.py:632-640` to convert strings to dict format:
```python
for learning in learnings:
    # Convert string to dict format expected by curator
    # Curator will auto-generate 'id' and auto-categorize
    learning_dict = {
        "content": learning,
        "learned_in": f"session_{session_num:03d}",
        "timestamp": datetime.now().isoformat(),
        "source": "temp_file" if args.learnings_file else "manual",
    }

    if curator.add_learning_if_new(learning_dict):
        added_count += 1
        # ... rest of code
```

**Testing:**
Verified with test script that:
- ✅ Learnings persist to `learnings.json`
- ✅ Auto-generated IDs created for each learning
- ✅ Auto-categorization works (best_practices, gotchas, etc.)
- ✅ All required fields present (content, learned_in, timestamp, id)
- ✅ Metadata counters update correctly

**Priority:** High (auto-learnings feature didn't actually save learnings) - **RESOLVED**
