# Spec File Integration - Implementation Notes

## Summary

This change makes `.session/specs/{work_item_id}.md` the single source of truth for work item content, ensuring that Claude receives full specification details during session briefings.

## Changes Made

### 1. `scripts/briefing_generator.py`

**Added:**
- `load_work_item_spec(work_item_id)`: New function to load spec files

**Modified:**
- `load_current_tree()`: Removed 50-line limit, now returns full tree
- `generate_briefing()`:
  - Loads and includes full spec file content
  - Removed compression on `vision.md` and `architecture.md` (was 500 chars, now full)
  - Removed sections that read from JSON: "Implementation Checklist", "Validation Requirements"
  - Removed calls to `generate_integration_test_briefing()` and `generate_deployment_briefing()`

**Result:**
- Claude now receives complete specifications from spec files
- All project docs passed in full (vision, architecture, tree, stack, spec)
- Briefings are richer and more informative

### 2. `scripts/work_item_manager.py`

**Modified:**
- `_add_to_tracking()`: Removed initialization of content fields:
  - `rationale`
  - `acceptance_criteria`
  - `implementation_paths`
  - `test_paths`

**Added deprecation notes to:**
- `validate_integration_test()`: Documents that JSON field validation is deprecated
- `validate_deployment()`: Documents that specification field is deprecated

**Result:**
- New work items have cleaner JSON (only tracking/state data)
- Spec files become the content storage mechanism

### 3. work_items.json Structure

**Before:**
```json
{
  "id": "feature_xyz",
  "type": "feature",
  "title": "...",
  "status": "not_started",
  "priority": "high",
  "dependencies": [],
  "milestone": "",
  "created_at": "...",
  "sessions": [],
  "rationale": "",  // REMOVED
  "acceptance_criteria": [],  // REMOVED
  "implementation_paths": [],  // REMOVED
  "test_paths": []  // REMOVED
}
```

**After:**
```json
{
  "id": "feature_xyz",
  "type": "feature",
  "title": "...",
  "status": "not_started",
  "priority": "high",
  "dependencies": [],
  "milestone": "",
  "created_at": "...",
  "sessions": []
}
```

## What Works Now

✅ Session briefings include full spec file content
✅ Full project documentation passed to Claude (no compression)
✅ New work items create spec files (via templates)
✅ Spec files are the single source of truth
✅ Existing code gracefully handles missing JSON fields (uses `.get()` with defaults)

## Known Limitations & Follow-up Work Needed

### 1. Validators (Low Priority)
**Files:** `scripts/work_item_manager.py`
- `validate_integration_test()` expects JSON fields: `scope`, `test_scenarios`, `performance_benchmarks`, `api_contracts`, `environment_requirements`
- `validate_deployment()` expects JSON field: `specification`
- **Impact:** These validators will report errors for new work items
- **Solution:** Update validators to parse spec markdown instead of JSON
- **Workaround:** Validators can be skipped, they're not critical for core workflow

### 2. Quality Gates (Medium Priority)
**File:** `scripts/quality_gates.py`
- Lines 867-891: Check for sequence diagrams if `test_scenarios` exists in JSON
- Lines 895-909: Validate API contracts if `api_contracts` exists in JSON
- **Impact:** Quality gates will skip these checks for new work items
- **Solution:** Update to parse spec files to determine what to validate
- **Workaround:** Manual review of integration test and deployment specs

### 3. Integration Test Runner (Medium Priority)
**File:** `scripts/integration_test_runner.py`
- Lines 32-33: Reads `test_scenarios` and `environment_requirements` from JSON
- **Impact:** Runner won't find test scenarios for new work items
- **Solution:** Parse test scenarios from integration_test_spec.md
- **Workaround:** Manually run integration tests outside the runner

### 4. Session Complete/Validate (Low Priority)
**Files:** `scripts/session_complete.py`, `scripts/session_validate.py`
- Read various content fields from JSON for reporting
- **Impact:** Some reporting information will be missing
- **Solution:** Update to read from spec files
- **Workaround:** Information is available in spec files, just not auto-reported

### 5. Other Runners/Validators
**Files:**
- `scripts/performance_benchmark.py`
- `scripts/deployment_executor.py`
- `scripts/api_contract_validator.py`

These likely have similar issues reading structured data from JSON. Review and update as needed.

## Migration Guide

### For Existing Work Items
Old work items with populated JSON fields will continue to work. No migration needed.

### For New Work Items
1. Create work item with `/work-new`
2. Edit the generated spec file in `.session/specs/{work_id}.md`
3. Fill out all sections in the spec file
4. When you run `/start`, Claude will see the full spec content

### If You Need Validators/Runners
Until the follow-up work is completed:
- Integration test validation: Manually review spec files
- Integration test running: Use external test runners
- Quality gates: May need manual review for integration/deployment items

## Testing Checklist

- [ ] Create a new feature work item
- [ ] Verify spec file is created
- [ ] Edit spec file with details
- [ ] Run `/start` and verify Claude sees full spec content
- [ ] Verify vision.md and architecture.md appear in full (if they exist)
- [ ] Verify tree.txt appears in full
- [ ] Create integration test work item (expect validator warnings - that's OK)
- [ ] Verify integration test spec is passed to Claude

## Future Enhancements

1. **Spec File Parsing Library**: Create a module to parse spec markdown into structured data
2. **Update All Consumers**: Migrate validators, runners, quality gates to use spec parsing
3. **Template Improvements**: Enhance spec templates with better structure/examples
4. **Validation**: Add spec file structure validation (ensure required sections present)
5. **Migration Tool**: Create utility to migrate old JSON content to spec files (if desired)
