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
