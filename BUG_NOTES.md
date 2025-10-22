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
