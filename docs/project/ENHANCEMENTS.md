# SDD Workflow Enhancements

This document tracks identified workflow improvements to make SDD more user-friendly and automated.

## Status Legend
- 🔵 IDENTIFIED - Enhancement identified, not yet implemented
- 🟡 IN_PROGRESS - Currently being worked on
- ✅ IMPLEMENTED - Completed and merged

---

## Enhancement #1: Auto Git Initialization in `sdd init`
**Status:** ✅ IMPLEMENTED - Automatically detects and initializes git repository during `sdd init`.

---

## Enhancement #2: CHANGELOG Update Workflow
**Status:** ✅ IMPLEMENTED - Added git hooks for reminders and smarter CHANGELOG checking in branch commits.

---

## Enhancement #3: Pre-flight Commit Check in `/sdd:end`
**Status:** ✅ IMPLEMENTED - Added early check for uncommitted changes with clear guidance before running quality gates.

---

## Enhancement #4: Add OS-Specific Files to Initial .gitignore
**Status:** ✅ IMPLEMENTED - Updated .gitignore template to include OS-specific files (.DS_Store, Thumbs.db, etc.).

---

## Enhancement #5: Create Initial Commit on Main During sdd init
**Status:** ✅ IMPLEMENTED - Automatically creates initial commit on main branch after project initialization.

---

## Enhancement #7: Phase 1 - Documentation Reorganization & Project Files
**Status:** ✅ IMPLEMENTED (Session 8) - Reorganized docs/ directory, added .editorconfig and Makefile.

---

## Enhancement #8: Phase 2 - Test Suite Reorganization
**Status:** ✅ IMPLEMENTED (Session 9) - Reorganized tests by domain (unit/integration/e2e) with 1,401 tests and 85% coverage.

---

## Enhancement #6: Work Item Completion Status Control

**Status:** ✅ IMPLEMENTED (Session 11)

**Discovered:** 2025-10-23 (During Session 3 - Bug #20 implementation)

### Problem

The current workflow lacks explicit control over work item completion status:

**No prompt when ending session**: `/sdd:end` appears to default the work item status to "completed" without asking the user. This is problematic because:
- Work items may span multiple sessions (not complete in one session)
- Users have no explicit control over the completion status
- If the work isn't done, the status is incorrectly set to completed
- No clear way to keep work items in-progress for resumption in next session

### Current Behavior

**When running `/sdd:end`:**
- Session ends
- Work item status is set (appears to default to "completed")
- No prompt asking: "Is this work item complete?"
- User has no explicit control
- If work is incomplete, status is incorrectly set, causing issues when resuming

### Expected Behavior

When running `/sdd:end`, prompt the user for work item completion status:

```bash
$ /sdd:end

Running quality gates...
✓ Tests: pass
✓ Linting: pass
✓ Formatting: pass

Work item: "Learning Curator Bug Fix"

Is this work item complete?
1. Yes - Mark as completed (default)
2. No - Keep as in-progress (will resume in next session)
3. Cancel - Don't end session

Choice [1]: _
```

**Behavior:**
- **Option 1 (completed)**: Sets work item status to "completed", ends session
- **Option 2 (in-progress)**: Leaves work item status as "in_progress", ends session, work will be auto-resumed on next `/start`
- **Option 3 (cancel)**: Cancels `/end`, returns to session

**Non-interactive mode:**
- Add `--complete` flag: Forces completion
- Add `--incomplete` flag: Forces in-progress
- No flag: Interactive prompt (or default to incomplete for safety)

```bash
sdd end --complete      # Mark as complete
sdd end --incomplete    # Keep in-progress
sdd end                 # Prompt (interactive) or default incomplete (non-interactive)
```

### Root Cause

- `scripts/session_complete.py` doesn't prompt for work item status
- Defaults to marking work item as complete (or leaves it in-progress?)
- User intent is not captured
- No explicit control flow for multi-session work items

### Impact

- **User Confusion**: Status updates happen implicitly without user input
- **Data Quality**: Work item status may be incorrect (marked complete when incomplete)
- **Multi-session Work**: No clear way to keep work item in-progress across sessions
- **Workflow Control**: Users lack explicit control over completion status
- **Resume Issues**: Incorrectly completed items don't auto-resume when they should

### Proposed Solution

Add completion status prompt to `/sdd:end`

**Location:** `scripts/session_complete.py`

Add interactive prompt before updating work item status:

```python
def prompt_work_item_completion(work_item_title: str, non_interactive: bool = False) -> bool:
    """
    Prompt user to mark work item as complete or in-progress.

    Returns:
        True if work item should be marked complete
        False if work item should remain in-progress
    """
    if non_interactive:
        # In non-interactive mode, default to incomplete for safety
        # User must explicitly use --complete flag to mark as done
        return False

    print(f"\nWork item: \"{work_item_title}\"\n")
    print("Is this work item complete?")
    print("1. Yes - Mark as completed")
    print("2. No - Keep as in-progress (will resume in next session)")
    print("3. Cancel - Don't end session")
    print()

    while True:
        choice = input("Choice [1]: ").strip() or "1"

        if choice == "1":
            return True  # Mark complete
        elif choice == "2":
            return False  # Keep in-progress
        elif choice == "3":
            print("\nSession end cancelled")
            sys.exit(0)
        else:
            print("Invalid choice. Enter 1, 2, or 3.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--complete", action="store_true", help="Mark work item as completed")
    parser.add_argument("--incomplete", action="store_true", help="Keep work item as in-progress")
    args = parser.parse_args()

    # ... quality gates ...

    # Determine if non-interactive
    non_interactive = not sys.stdin.isatty() or args.complete or args.incomplete

    # Determine work item completion status
    if args.complete:
        is_complete = True
    elif args.incomplete:
        is_complete = False
    else:
        is_complete = prompt_work_item_completion(work_item_title, non_interactive)

    # Update work item status
    if is_complete:
        work_items_data["work_items"][work_item_id]["status"] = "completed"
        print(f"\n✓ Marking work item '{work_item_title}' as complete")
    else:
        # Keep as in_progress
        print(f"\n✓ Keeping work item '{work_item_title}' as in-progress (will resume in next session)")
```

### Benefits

- Explicit user control over work item completion
- Prevents incorrect status updates
- Supports multi-session work items properly
- Clear workflow for incomplete work
- Aligns with 1 session = 1 work item model
- Natural session boundaries for commits, reviews, and breaks

### Implementation Tasks

- [ ] Add `prompt_work_item_completion()` to `scripts/session_complete.py`
- [ ] Add `--complete` and `--incomplete` flags to argparse
- [ ] Update work item status logic to use prompt result
- [ ] Handle non-interactive mode (default to incomplete for safety)
- [ ] Add tests for interactive prompt
- [ ] Add tests for flag handling
- [ ] Update documentation for `/end` command
- [ ] Test multi-session workflow (mark incomplete, resume in next session)

### Files Affected

- `scripts/session_complete.py` - Add completion prompt and flags
- `.claude/commands/end.md` - Document new flags and prompt behavior

### Related Issues

- Related to Bug #21: `/start` command ignores work item ID argument
- Related to Bug #22: Git branch status not finalized when switching work items
- All three issues involve improving work item lifecycle management

### Priority

**High** - Core workflow issue affecting data quality and multi-session work items

### Rationale for Not Including Mid-Session Completion

Originally, this enhancement included a "Part 2" for mid-session work item completion. After critical analysis, this was removed because:

- **Violates 1:1 model**: SDD follows 1 branch = 1 work item = 1 session model
- **Git complexity**: Switching work items mid-session complicates git branch management
- **Context pollution**: Work Item A's context pollutes Work Item B's available context window
- **Wrong problem**: Need for mid-session switching suggests work items are too small (should be tasks, not work items)
- **Minimal benefit**: Saves ~30 seconds but adds significant complexity
- **Natural boundaries**: Session boundaries provide natural points for commits, reviews, breaks

**Better approach**: Scope work items properly (30-120 minutes) so they naturally fit one session.

---

## Enhancement #9: Phase 3 - Complete Phase 5.9 (src/ Layout Transition)

**Status:** 🔵 IDENTIFIED

**Discovered:** 2025-10-24 (Aligns with ROADMAP.md Phase 5.9)

**Related:** ROADMAP.md Phase 5.9 - Package Structure Refactoring

### Problem

The current codebase uses a **hybrid packaging approach** (documented in README Architecture Notes) that works but has technical debt:

**Current issues:**
1. **Flat scripts/ directory** - All 23 Python modules at root level, no logical grouping
2. **sys.path manipulation** - 38 files use `sys.path.insert(0, ...)` to handle imports
3. **Non-standard structure** - Doesn't follow Python packaging best practices
4. **Import inconsistencies** - Mix of `from scripts.X import Y` patterns
5. **sdd_cli.py at root** - Should be part of package structure

**From ROADMAP Phase 5.9:**
```
Planned Refactoring (Phase 5.9):
- 🔄 Move scripts/ → sdd/scripts/
- 🔄 Move sdd_cli.py → sdd/cli.py
- 🔄 Remove all sys.path manipulation (38 files)
- 🔄 Update imports to use from sdd.scripts.X pattern
- 🔄 Full compliance with Python packaging standards
```

**Impact:**
- **Maintainability** - Current structure requires understanding of sys.path hacks
- **Contributor friction** - Non-standard imports confuse new contributors
- **Package distribution** - Works but not ideal for PyPI distribution
- **IDE support** - Some IDEs struggle with current import patterns
- **Testing complexity** - Tests must account for sys.path manipulation

### Current State

```
sdd/
├── sdd_cli.py                  ← Should be sdd/cli.py
├── scripts/                    ← Should be sdd/scripts/ or sdd/core/
│   ├── __init__.py
│   ├── work_item_manager.py   ← Uses sys.path
│   ├── learning_curator.py    ← Uses sys.path
│   ├── quality_gates.py       ← Uses sys.path
│   └── ... (23 files total)   ← All use sys.path
├── templates/                  ← Should be sdd/templates/
├── tests/                      ← OK as is
├── docs/                       ← OK as is
├── pyproject.toml
└── setup.py
```

**Current pyproject.toml:**
```toml
[project.scripts]
sdd = "sdd_cli:main"

[tool.setuptools]
py-modules = ["sdd_cli"]
packages = ["scripts", "templates"]
```

**Current import pattern (in 38 files):**
```python
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.work_item_manager import WorkItemManager
from scripts.quality_gates import QualityGates
```

### Proposed Solution

Transition to **standard Python src/ layout** following best practices:

```
sdd/
├── src/
│   └── sdd/
│       ├── __init__.py
│       ├── __version__.py          # NEW: Version management
│       ├── cli.py                  # MOVED from sdd_cli.py
│       ├── core/                   # NEW: Core functionality
│       │   ├── __init__.py
│       │   ├── file_ops.py        # FROM scripts/
│       │   ├── logging_config.py  # FROM scripts/
│       │   └── config_validator.py # FROM scripts/
│       ├── session/                # NEW: Session management
│       │   ├── __init__.py
│       │   ├── complete.py        # FROM scripts/session_complete.py
│       │   ├── status.py          # FROM scripts/session_status.py
│       │   ├── validate.py        # FROM scripts/session_validate.py
│       │   └── briefing.py        # FROM scripts/briefing_generator.py
│       ├── work_items/             # NEW: Work item management
│       │   ├── __init__.py
│       │   ├── manager.py         # FROM scripts/work_item_manager.py
│       │   ├── spec_parser.py     # FROM scripts/
│       │   └── spec_validator.py  # FROM scripts/
│       ├── learning/               # NEW: Learning system
│       │   ├── __init__.py
│       │   └── curator.py         # FROM scripts/learning_curator.py
│       ├── quality/                # NEW: Quality gates
│       │   ├── __init__.py
│       │   ├── gates.py           # FROM scripts/quality_gates.py
│       │   ├── env_validator.py   # FROM scripts/environment_validator.py
│       │   └── api_validator.py   # FROM scripts/api_contract_validator.py
│       ├── visualization/          # NEW: Visualization
│       │   ├── __init__.py
│       │   └── dependency_graph.py # FROM scripts/
│       ├── git/                    # NEW: Git integration
│       │   ├── __init__.py
│       │   └── integration.py     # FROM scripts/git_integration.py
│       ├── testing/                # NEW: Testing utilities
│       │   ├── __init__.py
│       │   ├── integration_runner.py  # FROM scripts/integration_test_runner.py
│       │   └── performance.py     # FROM scripts/performance_benchmark.py
│       ├── deployment/             # NEW: Deployment
│       │   ├── __init__.py
│       │   └── executor.py        # FROM scripts/deployment_executor.py
│       ├── project/                # NEW: Project management
│       │   ├── __init__.py
│       │   ├── init.py            # FROM scripts/init_project.py
│       │   ├── stack.py           # FROM scripts/generate_stack.py
│       │   ├── tree.py            # FROM scripts/generate_tree.py
│       │   └── sync_plugin.py     # FROM scripts/sync_to_plugin.py
│       └── templates/              # MOVED from root templates/
│           ├── __init__.py
│           └── ... (all templates)
├── tests/                          # UNCHANGED (stays at project root)
├── docs/                           # UNCHANGED
├── .claude/                        # UNCHANGED (needs command path updates)
├── pyproject.toml                  # UPDATED
└── setup.py                        # REMOVED (pyproject.toml is sufficient)
```

#### Updated pyproject.toml

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "sdd"
version = "0.6.0"  # Bump for major refactoring
# ... rest of project metadata ...

[project.scripts]
sdd = "sdd.cli:main"  # CHANGED from sdd_cli:main

[tool.setuptools]
package-dir = {"" = "src"}  # NEW: Use src layout
packages = ["sdd"]           # CHANGED: Just sdd package

[tool.setuptools.package-data]
"sdd.templates" = ["*.md", "*.json"]  # CHANGED: Templates in package
```

#### Updated Import Patterns

**Before (current):**
```python
# In scripts/session_complete.py
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.work_item_manager import WorkItemManager
from scripts.quality_gates import QualityGates
from scripts.file_ops import load_json
```

**After (standard):**
```python
# In src/sdd/session/complete.py
from sdd.work_items.manager import WorkItemManager
from sdd.quality.gates import QualityGates
from sdd.core.file_ops import load_json
```

**Benefits:**
- ✅ No sys.path manipulation needed
- ✅ Standard Python imports
- ✅ Better IDE autocomplete and type checking
- ✅ Clearer dependencies and module boundaries

### Benefits

- ✅ **Standard Python packaging** - Follows PEP 517/518 best practices
- ✅ **No sys.path hacks** - Eliminates all 38 instances of sys.path manipulation
- ✅ **Better IDE support** - Standard imports work perfectly with IDEs
- ✅ **Clearer organization** - Modules grouped by domain (session/, work_items/, etc.)
- ✅ **PyPI-ready** - Proper structure for package distribution
- ✅ **Better testing** - Tests import from installed package, not sys.path tricks
- ✅ **Contributor-friendly** - Standard structure familiar to Python developers
- ✅ **Type checking** - Tools like mypy work better with standard structure

### Implementation Tasks

**Phase 3.1: Create src/ Structure**
- [ ] Create src/sdd/ directory structure
- [ ] Create all subdirectories (core/, session/, work_items/, etc.)
- [ ] Create __init__.py files for all packages
- [ ] Create src/sdd/__version__.py with version management

**Phase 3.2: Move and Rename Files**
- [ ] Move sdd_cli.py → src/sdd/cli.py
- [ ] Move scripts/file_ops.py → src/sdd/core/file_ops.py
- [ ] Move scripts/logging_config.py → src/sdd/core/logging_config.py
- [ ] Move scripts/config_validator.py → src/sdd/core/config_validator.py
- [ ] Move scripts/session_complete.py → src/sdd/session/complete.py
- [ ] Move scripts/session_status.py → src/sdd/session/status.py
- [ ] Move scripts/session_validate.py → src/sdd/session/validate.py
- [ ] Move scripts/briefing_generator.py → src/sdd/session/briefing.py
- [ ] Move scripts/work_item_manager.py → src/sdd/work_items/manager.py
- [ ] Move scripts/spec_parser.py → src/sdd/work_items/spec_parser.py
- [ ] Move scripts/spec_validator.py → src/sdd/work_items/spec_validator.py
- [ ] Move scripts/learning_curator.py → src/sdd/learning/curator.py
- [ ] Move scripts/quality_gates.py → src/sdd/quality/gates.py
- [ ] Move scripts/environment_validator.py → src/sdd/quality/env_validator.py
- [ ] Move scripts/api_contract_validator.py → src/sdd/quality/api_validator.py
- [ ] Move scripts/dependency_graph.py → src/sdd/visualization/dependency_graph.py
- [ ] Move scripts/git_integration.py → src/sdd/git/integration.py
- [ ] Move scripts/integration_test_runner.py → src/sdd/testing/integration_runner.py
- [ ] Move scripts/performance_benchmark.py → src/sdd/testing/performance.py
- [ ] Move scripts/deployment_executor.py → src/sdd/deployment/executor.py
- [ ] Move scripts/init_project.py → src/sdd/project/init.py
- [ ] Move scripts/generate_stack.py → src/sdd/project/stack.py
- [ ] Move scripts/generate_tree.py → src/sdd/project/tree.py
- [ ] Move scripts/sync_to_plugin.py → src/sdd/project/sync_plugin.py
- [ ] Move templates/ → src/sdd/templates/

**Phase 3.3: Update All Imports (38+ files)**
- [ ] Update imports in src/sdd/cli.py
- [ ] Update imports in all src/sdd/**/*.py files (remove sys.path, use sdd.* imports)
- [ ] Update test imports (use sdd.* instead of scripts.*)
- [ ] Update .claude/commands/*.md (if they reference file paths)

**Phase 3.4: Update Configuration**
- [ ] Update pyproject.toml with src layout
- [ ] Update pyproject.toml [project.scripts] entry point
- [ ] Update pyproject.toml package-data for templates
- [ ] Remove setup.py (pyproject.toml is sufficient per PEP 517/518)
- [ ] Update .gitignore if needed

**Phase 3.5: Update Documentation**
- [ ] Update README.md Architecture Notes section (remove hybrid approach note)
- [ ] Update CONTRIBUTING.md import patterns
- [ ] Update ROADMAP.md - Mark Phase 5.9 as complete
- [ ] Update any other docs referencing scripts/ structure

**Phase 3.6: Validation**
- [ ] Uninstall old package: `pip uninstall sdd`
- [ ] Install new package: `pip install -e .`
- [ ] Verify `sdd` command works
- [ ] Run full test suite: `pytest tests/`
- [ ] Verify all 1408 tests pass
- [ ] Test slash commands in Claude Code
- [ ] Test CLI: `sdd init`, `sdd status`, etc.
- [ ] Verify package can be built: `python -m build`

**Phase 3.7: Cleanup**
- [ ] Remove old scripts/ directory (after validation)
- [ ] Remove old sdd_cli.py (after validation)
- [ ] Remove old templates/ directory (after validation)
- [ ] Clean up any backup files

### Files Affected

**Moved/Renamed:**
- sdd_cli.py → src/sdd/cli.py
- All 23 files in scripts/ → src/sdd/*/
- templates/ → src/sdd/templates/

**Modified (import updates):**
- All 38 files with sys.path manipulation
- All test files (import path changes)
- .claude/commands/*.md (if needed)

**Modified (configuration):**
- pyproject.toml
- CONTRIBUTING.md
- README.md
- ROADMAP.md

**Removed:**
- scripts/ directory (after migration)
- sdd_cli.py (after migration)
- templates/ directory (after migration)
- setup.py (after migration)

### Estimated Effort

**Time:** 3-5 hours (comprehensive changes requiring careful testing)

**Complexity:** High - Touches all Python files, requires careful import updates

**Risk:** Medium - High impact but well-defined transformation. Tests provide safety net.

### Dependencies

**Depends on:**
- Enhancement #7 (Phase 1) - Nice to have documentation organized first
- Enhancement #8 (Phase 2) - Nice to have tests organized before major refactoring

**Blocked by:** None - Can be done independently, but safer after Phases 1 & 2

**Enables:**
- Proper Python package distribution
- Better contributor experience
- Foundation for future modularization

### Testing Strategy

1. **Create feature branch** - Do all work in isolated branch
2. **Incremental migration** - Move one domain at a time (start with core/, then session/, etc.)
3. **Test after each domain** - Run tests after moving each subdomain
4. **Keep scripts/ until validated** - Don't delete old structure until new structure is fully tested
5. **Full regression** - Run complete test suite before final commit
6. **Manual CLI testing** - Test all CLI commands work
7. **Claude Code integration testing** - Test all slash commands work

### Migration Checklist

Before starting:
- [ ] Create feature branch: `git checkout -b feature/phase-5-9-src-layout`
- [ ] Ensure all tests pass on main: `pytest tests/`
- [ ] Document current test count (1408 tests)

During migration:
- [ ] Follow task list above sequentially
- [ ] Test after each major section
- [ ] Keep notes of any issues encountered

After migration:
- [ ] All tests pass: `pytest tests/` (1408/1408)
- [ ] CLI works: `sdd --help`, `sdd init`, `sdd status`
- [ ] Slash commands work in Claude Code
- [ ] Package builds: `python -m build`
- [ ] Editable install works: `pip install -e .`

Final steps:
- [ ] Update CHANGELOG.md with Phase 5.9 completion
- [ ] Update version to 0.6.0 in pyproject.toml
- [ ] Commit changes with detailed message
- [ ] Open PR for review
- [ ] After PR approval, merge to main
- [ ] Tag release: `git tag v0.6.0`

### Related Work

**From ROADMAP.md Phase 5.9:**
This enhancement completes the planned package structure refactoring outlined in the roadmap.

**From CONTRIBUTING.md:**
Current contributor guide documents the hybrid approach and will be updated to reflect standard Python imports after this enhancement is complete.

**From README.md Architecture Notes:**
The "Hybrid Packaging Approach" section explains current limitations and points to this enhancement as the solution.

---

## Enhancement #10: Add Delete Functionality for Work Items

**Status:** 🔵 IDENTIFIED

**Discovered:** 2025-10-24 (During Bug #23 session)

### Problem

Currently, there is no way to delete work items from the system. Once a work item is created, it remains in the work_items.json file forever, even if it becomes obsolete, was created in error, or is no longer relevant.

**Issues:**
- Work items created by mistake cannot be removed
- Obsolete work items clutter the work item list
- No command or API to delete work items
- Manual JSON editing is the only workaround
- Data integrity issues if manual deletion is done incorrectly

### Current Behavior

When a work item needs to be removed:
1. User must manually edit `.session/tracking/work_items.json`
2. Find and remove the work item entry
3. Update metadata (total_items count)
4. Risk of JSON syntax errors or broken references
5. No validation or cleanup of related data

### Expected Behavior

Provide a `/work-delete` command (or `sdd work-delete <work_item_id>`) that:
1. Validates the work item exists
2. Checks if work item has dependents (warn before deleting)
3. Confirms deletion with user
4. Removes work item from work_items.json
5. Cleans up spec file if desired
6. Updates metadata
7. Provides option to delete git branch if it exists

### Proposed Solution

#### Command: `/work-delete <work_item_id>`

```bash
sdd work-delete feature_obsolete_item

⚠️  Warning: This will permanently delete work item 'feature_obsolete_item'

Work item details:
  Title: Obsolete Feature
  Type: feature
  Status: not_started
  Dependencies: none
  Dependents: bug_related_fix (1 item depends on this)

Options:
  1. Delete work item only (keep spec file)
  2. Delete work item and spec file
  3. Cancel

Choice [1]: 2

✓ Deleted work item 'feature_obsolete_item'
✓ Deleted spec file '.session/specs/feature_obsolete_item.md'
⚠️  Note: Work item 'bug_related_fix' depends on this item - update dependencies

Delete successful.
```

#### Implementation

**New script:** `scripts/work_item_delete.py`

```python
def delete_work_item(work_item_id: str, delete_spec: bool = False):
    """
    Delete a work item from the system.

    Args:
        work_item_id: ID of work item to delete
        delete_spec: Whether to also delete the spec file
    """
    # Load work items
    work_items_data = load_work_items()
    work_items = work_items_data.get("work_items", {})

    # Validate work item exists
    if work_item_id not in work_items:
        print(f"Error: Work item '{work_item_id}' not found.")
        return False

    item = work_items[work_item_id]

    # Check for dependents
    dependents = find_dependents(work_items, work_item_id)

    # Show work item details
    print(f"\n⚠️  Warning: This will permanently delete work item '{work_item_id}'")
    print("\nWork item details:")
    print(f"  Title: {item.get('title')}")
    print(f"  Type: {item.get('type')}")
    print(f"  Status: {item.get('status')}")
    print(f"  Dependencies: {', '.join(item.get('dependencies', [])) or 'none'}")

    if dependents:
        print(f"  Dependents: {', '.join(dependents)} ({len(dependents)} item(s) depend on this)")
    else:
        print("  Dependents: none")

    # Confirm deletion
    print("\nOptions:")
    print("  1. Delete work item only (keep spec file)")
    print("  2. Delete work item and spec file")
    print("  3. Cancel")

    choice = input("\nChoice [1]: ").strip() or "1"

    if choice == "3":
        print("Deletion cancelled.")
        return False

    delete_spec = (choice == "2")

    # Perform deletion
    del work_items[work_item_id]

    # Update metadata
    work_items_data["metadata"]["total_items"] = len(work_items)

    # Save work items
    save_work_items(work_items_data)
    print(f"✓ Deleted work item '{work_item_id}'")

    # Delete spec file if requested
    if delete_spec:
        spec_file = Path(item.get("spec_file", ""))
        if spec_file.exists():
            spec_file.unlink()
            print(f"✓ Deleted spec file '{spec_file}'")

    # Warn about dependents
    if dependents:
        print(f"\n⚠️  Note: The following work items depend on this item:")
        for dep in dependents:
            print(f"    - {dep}")
        print("  Update their dependencies manually if needed.")

    print("\nDeletion successful.")
    return True


def find_dependents(work_items: dict, work_item_id: str) -> list[str]:
    """Find work items that depend on the given work item."""
    dependents = []
    for wid, item in work_items.items():
        deps = item.get("dependencies", [])
        if work_item_id in deps:
            dependents.append(wid)
    return dependents
```

### Benefits

- ✅ **Clean data management** - Remove obsolete or erroneous work items
- ✅ **User-friendly** - Interactive prompts with safety checks
- ✅ **Dependency awareness** - Warns about dependent work items
- ✅ **Flexible** - Option to keep or delete spec file
- ✅ **Safe** - Confirmation required before deletion
- ✅ **Data integrity** - Updates metadata automatically

### Implementation Tasks

- [ ] Create `scripts/work_item_delete.py` with deletion logic
- [ ] Add `find_dependents()` helper function
- [ ] Add interactive confirmation prompts
- [ ] Add option to delete spec file
- [ ] Update metadata after deletion
- [ ] Create slash command `.claude/commands/work-delete.md`
- [ ] Add tests for deletion logic
- [ ] Add tests for dependency checking
- [ ] Handle edge cases (in-progress work items, git branches)
- [ ] Update documentation

### Files Affected

**New:**
- `scripts/work_item_delete.py` - Deletion logic
- `.claude/commands/work-delete.md` - Command documentation

**Modified:**
- `.session/tracking/work_items.json` - Work item removed
- Spec file (optional deletion)

### Related Issues

- Discovered during Bug #23 work when template was updated
- Related to work item lifecycle management

### Priority

Medium - Nice to have for data management, but not blocking core workflow

---

## Enhancement #11: Enhanced Session Briefings with Context Continuity

**Status:** 🔵 IDENTIFIED

**Discovered:** 2025-10-25 (During Session 11 - Enhancement #6 implementation)

### Problem

Session briefings currently lack critical context for multi-session work items and relevant learnings:

**Missing Previous Work Context for In-Progress Items:**
- When resuming an `in_progress` work item, Claude has no deterministic context about what was done in previous sessions
- Git commits exist but may not be fetched by Claude
- Session summaries exist but are not included in briefings
- Claude must manually search git history or read changed files to understand progress
- This creates friction and potential gaps in understanding

**Missing Relevant Learnings:**
- Learnings from previous sessions are stored in `.session/tracking/learnings.json`
- These learnings are never included in briefings
- Claude must manually search learnings, which may not happen
- Valuable context and insights are lost between sessions

**Why Briefings Matter:**
- The briefing file is **guaranteed to be in Claude's context** at session start
- Git history, learnings, and other sources may or may not be fetched
- Briefings provide deterministic, reliable context delivery

### Current Behavior

**For In-Progress Work Items:**
```markdown
## Quick Reference
- **Work Item ID:** feature_example
- **Status:** in_progress

## Work Item Specification
[Full spec from .session/specs/]

## Dependencies
[Dependency list]
```

**For All Work Items:**
- No learnings included
- No way to see related insights from past sessions
- Claude must manually search `.session/tracking/learnings.json`

### Expected Behavior

**1. Previous Work Section for In-Progress Items:**

```markdown
## Previous Work

### Session 11 (2025-10-25)
**Status:** Session ended with work item in-progress (incomplete)

**Git Commits:**
- e227799: feat: Add work item completion status control to /sdd:end
  - Added interactive 3-choice prompt
  - Added --complete and --incomplete flags
  - Updated documentation

**Files Changed:**
- scripts/session_complete.py (+80 lines)
- tests/unit/test_session_complete.py (+60 lines)
- .claude/commands/end.md (+32 lines)
- CHANGELOG.md (+9 lines)

**Quality Gates:**
- ✓ Tests: PASSED (85.48% coverage)
- ✓ Security: PASSED
- ✓ Linting: PASSED
- ✓ Formatting: PASSED
- ✓ Documentation: PASSED

**Session Summary:**
All acceptance criteria partially implemented:
- [x] Interactive prompt added
- [x] Command-line flags added
- [x] Tests written (8 unit tests)
- [ ] Integration tests needed (deferred to next session)
- [x] Documentation updated
```

**2. Relevant Learnings Section for All Work Items:**

```markdown
## Relevant Learnings

### From Similar Work
- **Session 5** (work_item: feature_git_integration):
  "When adding interactive prompts to CLI tools, always provide both interactive
   and non-interactive modes. Default to safest option in non-interactive."

- **Session 8** (work_item: bug_quality_gates):
  "Python subprocess calls need sys.executable instead of 'python3' to ensure
   venv Python is used."

### From Related Topics
- **Session 3** (topic: testing):
  "Mock input() calls need to return exact expected values ('1', '2', '3')
   not legacy values ('y', 'n')."
```

### Root Cause

**`scripts/briefing_generator.py` Limitations:**
- Doesn't detect when work item is `in_progress` vs `not_started`
- Doesn't load previous session summaries for in-progress items
- Doesn't extract git commit history from the work item's git metadata
- Doesn't search or filter learnings by relevance to current work item
- Doesn't include any learning context in briefings

**Data Sources Available but Not Used:**
1. `.session/tracking/work_items.json` - Contains git commits array
2. `.session/history/session_NNN_summary.md` - Contains previous session details
3. `.session/tracking/learnings.json` - Contains all captured learnings
4. Git history via `git log <branch>` - Contains detailed commit information

### Impact

**High Impact:**
- **Context Loss**: Critical information about previous work is lost between sessions
- **Duplicate Work**: Claude may re-implement already-completed parts
- **Missed Insights**: Relevant learnings are not surfaced automatically
- **Inefficiency**: Claude must manually search for context that should be provided
- **Inconsistency**: Whether context is found depends on whether Claude searches (non-deterministic)

**Multi-Session Workflow Broken:**
- The new `--incomplete` flag enables multi-session work items
- But without previous work context, continuation is difficult
- Claude starts each session "cold" without knowing what was done

### Proposed Solution

**Phase 1: Previous Work Section for In-Progress Items**

Modify `scripts/briefing_generator.py` to:

1. **Detect in-progress status:**
   ```python
   if work_item["status"] == "in_progress":
       briefing += generate_previous_work_section(work_item, work_item_id)
   ```

2. **Load session summaries:**
   ```python
   def get_previous_sessions(work_item_id):
       # Find all session summaries that worked on this work item
       # Parse session_NNN_summary.md files
       # Return list of session numbers and summaries
   ```

3. **Extract git commits:**
   ```python
   def format_git_commits(work_item):
       commits = work_item.get("git", {}).get("commits", [])
       # Format with sha, message, timestamp
       # Optionally include file change stats via git diff
   ```

4. **Include quality gate results:**
   ```python
   # Load from session summary
   # Show which gates passed/failed in previous session
   ```

**Phase 2: Relevant Learnings for All Work Items**

1. **Learning Relevance Scoring:**
   ```python
   def find_relevant_learnings(work_item, all_learnings):
       # Score learnings by:
       # - Keyword match with work item title/spec
       # - Same work item type (feature/bug/refactor)
       # - Related files (if learning mentions files in current work)
       # - Recency (recent learnings weighted higher)
       # Return top 5-10 most relevant
   ```

2. **Learning Categories:**
   - **From Similar Work**: Learnings from same work item type
   - **From Related Topics**: Learnings mentioning similar concepts
   - **From Modified Files**: Learnings about files being changed

3. **Learning Format in Briefing:**
   ```markdown
   ## Relevant Learnings

   ### [Category]
   - **Session X** (work_item: ...):
     "Learning content..."
     [Relevance: Mentions similar file/concept/pattern]
   ```

### Implementation Tasks

**Phase 1: Previous Work Section**
- [ ] Add `generate_previous_work_section()` function
- [ ] Add `get_previous_sessions()` to find related session summaries
- [ ] Add `format_git_commits()` to extract commit details
- [ ] Add `get_session_quality_gates()` to load previous quality results
- [ ] Integrate into main briefing generation flow
- [ ] Add tests for previous work section generation
- [ ] Test with actual in-progress work item

**Phase 2: Relevant Learnings**
- [ ] Add `find_relevant_learnings()` function with scoring algorithm
- [ ] Add keyword matching logic (work item title, spec content)
- [ ] Add file-based relevance (learnings mentioning files in work item)
- [ ] Add type-based relevance (same work item type)
- [ ] Add recency weighting
- [ ] Format learnings section for briefing
- [ ] Add tests for learning relevance scoring
- [ ] Add tests for learning section generation

**Documentation:**
- [ ] Update `docs/architecture/session-driven-development.md`
- [ ] Add examples to briefing documentation
- [ ] Update `.claude/commands/start.md` to mention enhanced context

### Files Affected

**Modified:**
- `scripts/briefing_generator.py` - Add previous work and learnings sections
- `scripts/spec_parser.py` - May need to extract keywords from specs
- Tests for briefing generation

**New (maybe):**
- `scripts/learning_relevance.py` - Learning scoring and filtering logic

### Benefits

**Deterministic Context Delivery:**
- ✓ Previous work context guaranteed in briefing
- ✓ Relevant learnings guaranteed in briefing
- ✓ No reliance on Claude manually searching

**Better Multi-Session Support:**
- ✓ Claude knows exactly what was done before
- ✓ Can continue work seamlessly
- ✓ Avoids duplicate implementation

**Knowledge Reuse:**
- ✓ Past learnings automatically surfaced
- ✓ Common patterns reused across work items
- ✓ Mistakes avoided through shared insights

**Improved Quality:**
- ✓ Better informed implementation decisions
- ✓ Consistency across sessions
- ✓ Reduced context-gathering overhead

### Priority

**High** - Critical for multi-session workflow success

The new `--incomplete` flag (Enhancement #6) enables multi-session work items, but without enhanced briefing context, the workflow is incomplete. This enhancement makes multi-session work practical and efficient.

### Related

- **Enhancement #6**: Work Item Completion Status Control (enables multi-session work)
- **Learning System**: Already captures learnings, needs to surface them in briefings

---
