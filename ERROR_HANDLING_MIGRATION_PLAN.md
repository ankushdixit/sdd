# Error Handling Migration Plan

## Executive Summary

**Analysis completed:** 2025-11-04
**Test baseline:** 1634 passing, 1 failing (pre-existing)

### Statistics

- **Total files needing migration:** 33 files
- **Return tuples (bool, str):** 26 instances across 8 files
- **sys.exit() calls:** 27 instances across 11 files
- **print() error messages:** 342 instances across 29 files
- **Broad Exception catches:** 75 instances across 22 files
- **Built-in exceptions raised:** 14 instances across 5 files

### Migration Complexity Distribution

- **Simple (1-5 points):** 11 files - Quick wins, mostly print() conversions
- **Medium (6-15 points):** 8 files - Moderate effort, some refactoring needed
- **Complex (16+ points):** 14 files - Significant refactoring required

---

## Parallel Migration Strategy

Your approach to use **parallel agents working on independent files** is excellent! Here's the recommended strategy:

### Phase 1: Simple Files (Parallel Batch 1) - 11 files

These files have low complexity and can be migrated independently without cross-dependencies.

**Group 1A - Core Utilities (4 files)**
- `src/sdd/core/file_ops.py` (score: 3)
- `src/sdd/core/command_runner.py` (score: 3)
- `src/sdd/core/types.py` (score: 2)
- `src/sdd/core/config.py` (score: 4)

**Group 1B - Briefing Components (7 files)**
- `src/sdd/session/briefing/git_context.py` (score: 4)
- `src/sdd/session/briefing/tree_generator.py` (score: 4)
- `src/sdd/session/briefing/formatter.py` (score: 3)
- `src/sdd/session/briefing/documentation_loader.py` (score: 3)
- `src/sdd/session/briefing/learning_loader.py` (score: 2)
- `src/sdd/session/briefing/stack_detector.py` (score: 2)
- `src/sdd/project/stack.py` (score: 5)

### Phase 2: Medium Files (Parallel Batch 2) - 8 files

These require moderate refactoring but are still independent.

**Group 2A - Work Items & Validation (4 files)**
- `src/sdd/work_items/spec_parser.py` (score: 13)
- `src/sdd/work_items/spec_validator.py` (score: 11)
- `src/sdd/session/validate.py` (score: 10)
- `src/sdd/quality/env_validator.py` (score: 7)

**Group 2B - CLI & Orchestration (4 files)**
- `src/sdd/cli.py` (score: 9) - **Important:** CLI entry point
- `src/sdd/session/briefing.py` (score: 13)
- `src/sdd/deployment/executor.py` (score: 15)
- `src/sdd/project/tree.py` (score: 10)

### Phase 3: Complex Files (Parallel Batch 3) - 14 files

These files are most complex and need careful handling.

**Group 3A - Core Business Logic (5 files)**
- `src/sdd/work_items/manager.py` (score: 85) - **CRITICAL**
- `src/sdd/session/complete.py` (score: 63)
- `src/sdd/learning/curator.py` (score: 59)
- `src/sdd/quality/gates.py` (score: 55)
- `src/sdd/git/integration.py` (score: 26)

**Group 3B - Testing & Quality (3 files)**
- `src/sdd/testing/integration_runner.py` (score: 49)
- `src/sdd/testing/performance.py` (score: 20)
- `src/sdd/quality/api_validator.py` (score: 19)

**Group 3C - Project Management (6 files)**
- `src/sdd/project/init.py` (score: 52)
- `src/sdd/work_items/delete.py` (score: 26)
- `src/sdd/core/config_validator.py` (score: 18)
- `src/sdd/project/sync_plugin.py` (score: 17)
- `src/sdd/session/status.py` (score: 17)
- `src/sdd/visualization/dependency_graph.py` (score: 16)

---

## Top 10 Most Complex Files

Priority order for review and careful migration:

1. **manager.py** (85) - 2 return tuples, 79 print errors
   - Critical file: Work item CRUD operations
   - Many print statements for user feedback
   - Needs careful error message preservation

2. **complete.py** (63) - 41 print errors, 11 broad exceptions
   - Session completion logic
   - Quality gate validation integration
   - User-facing output critical

3. **curator.py** (59) - 1 sys.exit, 41 print errors, 8 broad exceptions
   - Learning curation system
   - Many user-facing messages
   - AI integration points

4. **gates.py** (55) - 10 return tuples, 7 print errors, 9 broad exceptions
   - Quality gate execution
   - Return tuples for gate results
   - Consider keeping tuple returns for multi-gate status

5. **init.py** (52) - 34 print errors, 9 broad exceptions
   - Project initialization
   - Heavy user interaction
   - Setup wizard functionality

6. **integration_runner.py** (49) - 3 return tuples, 5 sys.exit, 11 print, 8 broad exceptions, 3 built-ins
   - Test execution
   - Subprocess management
   - Multiple error patterns

7. **delete.py** (26) - 20 print errors, 3 broad exceptions
   - Work item deletion
   - User confirmation flows
   - Safety checks

8. **integration.py** (26) - 8 return tuples, 2 print errors
   - Git operations
   - Perfect example from spec: return tuples → exceptions
   - Clear migration path

9. **performance.py** (20) - 3 sys.exit, 8 print errors, 3 broad exceptions
   - Benchmarking
   - Timing-sensitive code

10. **api_validator.py** (19) - 3 sys.exit, 9 print errors, 2 broad exceptions
    - API contract validation
    - Schema validation

---

## Recommended Approach for Parallel Migration

### Step 1: Prepare Agent Instructions Template

Create a standardized instruction template for each agent:

```markdown
## Migration Task: [FILE_NAME]

### Context
- File: src/sdd/[path]/[file].py
- Test file: tests/unit/test_[file].py
- Complexity score: [X]

### Current Patterns
- Return tuples: [X] instances at lines [...]
- sys.exit() calls: [X] instances at lines [...]
- print() errors: [X] instances at lines [...]
- Broad Exception catches: [X] instances at lines [...]
- Built-in exceptions: [X] instances at lines [...]

### Migration Goals
1. Replace return tuples with appropriate exceptions from sdd.core.exceptions
2. Remove sys.exit() calls, raise exceptions instead
3. Replace print() error messages with raising exceptions
4. Replace broad Exception catches with specific exception types
5. Replace built-in exceptions (ValueError, etc.) with SDDError hierarchy
6. Update all function signatures and docstrings
7. Update/create comprehensive unit tests
8. Ensure all tests pass

### Key Exceptions to Use
[List relevant exceptions based on file function]

### Dependencies
- Import: from sdd.core.exceptions import [...]
- Import: from sdd.core.error_handlers import [...]
- Test file should import pytest and use pytest.raises()

### Validation
- All existing tests must pass
- New tests for error paths added
- No print() or sys.exit() in business logic
- All exceptions are SDDError subclasses
```

### Step 2: Spawn Parallel Agents

For each phase, spawn multiple agents in parallel:

**Phase 1 Example:**
```bash
# Spawn 11 agents in parallel (or in groups of 3-4 based on resources)
Agent 1: Migrate src/sdd/core/file_ops.py
Agent 2: Migrate src/sdd/core/command_runner.py
Agent 3: Migrate src/sdd/core/types.py
Agent 4: Migrate src/sdd/core/config.py
...
```

### Step 3: Verification Strategy

After each phase:

1. **Run full test suite:** `pytest tests/ -v`
2. **Check coverage:** Ensure error paths are tested
3. **Verify patterns:** Run the analysis script again to confirm migration
4. **Integration check:** Run a sample end-to-end workflow

### Step 4: Special Considerations

#### CLI Entry Point (cli.py)
- **Must be migrated carefully** - it's the main error handler
- Add centralized try-except in main()
- Use ErrorFormatter for display
- Map exceptions to exit codes
- Keep this file for Phase 2 or do it manually

#### Return Tuples in Quality Gates (gates.py)
- Consider if tuple returns make sense for multi-gate results
- May keep (success, results_dict) pattern for aggregate status
- Use exceptions only for errors, not for reporting gate results

#### Work Item Manager (manager.py)
- Highest complexity (85 points)
- Most print() statements for user feedback
- Consider migrating in 2 steps:
  1. First: Add exception raising alongside print statements
  2. Second: Remove print statements after CLI is updated

---

## File-by-File Migration Details

### Simple Files

#### file_ops.py (score: 3)
- **Patterns:** 1 print error, 1 broad exception
- **Strategy:** Already has custom exceptions, migrate to SDDError hierarchy
- **Exceptions:** FileOperationError, FileNotFoundError
- **Test file:** tests/unit/test_file_ops.py ✓ exists

#### command_runner.py (score: 3)
- **Patterns:** 1 print error, 1 broad exception, 1 subprocess call
- **Strategy:** Use @convert_subprocess_errors decorator
- **Exceptions:** CommandExecutionError, SubprocessError
- **Test file:** tests/unit/test_command_runner.py ✓ exists

#### types.py (score: 2)
- **Patterns:** 2 built-in exceptions (ValueError)
- **Strategy:** Replace ValueError with ValidationError
- **Exceptions:** ValidationError with INVALID_WORK_ITEM_TYPE, INVALID_STATUS
- **Test file:** tests/unit/test_types.py ✓ exists

### Medium Files

#### git/integration.py (score: 26)
- **Patterns:** 8 return tuples, 2 print errors
- **Perfect example from spec:**
  - `check_git_status() -> tuple[bool, str]` → raises NotAGitRepoError, WorkingDirNotCleanError
  - Use @convert_subprocess_errors decorator
  - Use @log_errors decorator
- **Exceptions:** NotAGitRepoError, WorkingDirNotCleanError, GitError
- **Test file:** tests/unit/test_git_integration.py ✓ exists

#### cli.py (score: 9)
- **Patterns:** 1 sys.exit, 5 print errors, 1 broad exception
- **Strategy:** Add centralized error handler in main()
- **Key changes:**
  ```python
  def main():
      try:
          # route command
      except SDDError as e:
          ErrorFormatter.print_error(e, verbose=args.verbose)
          return e.exit_code
      except Exception as e:
          ErrorFormatter.print_error(e, verbose=True)
          return 1
  ```
- **Test file:** None - integration tests exist

### Complex Files

#### work_items/manager.py (score: 85)
- **Patterns:** 2 return tuples, 79 print errors
- **Strategy:**
  - Replace print() with appropriate exceptions
  - Many prints are informational, not errors - keep some as logger.info()
  - Return tuples → exceptions
  - Work item CRUD operations should raise WorkItemNotFoundError, WorkItemAlreadyExistsError
- **Exceptions:** WorkItemNotFoundError, WorkItemAlreadyExistsError, ValidationError
- **Test file:** tests/unit/test_work_item_manager.py ✓ exists
- **Note:** This is the most complex file - consider manual review

#### quality/gates.py (score: 55)
- **Patterns:** 10 return tuples, 7 print errors, 9 broad exceptions
- **Strategy:**
  - Return tuples may be valid for gate results: `(passed: bool, results: dict)`
  - Use exceptions for errors during gate execution
  - Replace broad Exception catches with specific types
- **Exceptions:** QualityGateError, TestFailedError, SubprocessError
- **Test file:** tests/unit/test_quality_gates.py ✓ exists
- **Note:** Discuss return tuple pattern - might be appropriate here

---

## Testing Strategy

### Test Coverage Requirements

Each migrated file must have:

1. **Existing tests updated** - pytest.raises() for new exceptions
2. **New error path tests** - Cover all exception types
3. **Integration tests** - Ensure end-to-end flows work
4. **Backwards compatibility** - Ensure behavior is preserved

### Example Test Pattern

**Before:**
```python
def test_check_git_status_not_repo():
    success, message = check_git_status()
    assert not success
    assert "Not a git repository" in message
```

**After:**
```python
def test_check_git_status_not_repo():
    with pytest.raises(NotAGitRepoError) as exc_info:
        check_git_status()
    assert exc_info.value.code == ErrorCode.NOT_A_GIT_REPO
    assert exc_info.value.remediation is not None
```

---

## Validation Checklist

After each file migration:

- [ ] All print() statements for errors removed (or converted to logger calls)
- [ ] All sys.exit() calls removed from business logic
- [ ] All return tuples replaced with exceptions (or explicitly kept with justification)
- [ ] All broad Exception catches replaced with specific types
- [ ] All built-in exceptions replaced with SDDError hierarchy
- [ ] Appropriate decorators added (@log_errors, @convert_subprocess_errors)
- [ ] All tests updated and passing
- [ ] New error path tests added
- [ ] Function signatures updated
- [ ] Docstrings updated with "Raises:" sections
- [ ] No diagnostics/warnings introduced

---

## Estimated Timeline

Based on complexity scores and parallel processing:

- **Phase 1 (11 simple files):** 2-3 hours with 4-5 parallel agents
- **Phase 2 (8 medium files):** 3-4 hours with 3-4 parallel agents
- **Phase 3 (14 complex files):** 5-7 hours with 3-4 parallel agents

**Total estimated time:** 10-14 hours of actual work

**With parallel agents:** Could be completed in 3-4 sessions

---

## Risk Mitigation

### High-Risk Files

These files require extra caution:

1. **cli.py** - Entry point, affects all commands
2. **manager.py** - Core work item operations
3. **complete.py** - Session completion, critical flow
4. **gates.py** - Quality validation, affects /end command

### Mitigation Strategies

1. **Backup before migration:** Ensure git is clean before starting
2. **Test after each phase:** Run full test suite between phases
3. **Manual review for complex files:** manager.py, cli.py should be reviewed
4. **Incremental commits:** Commit after each successful file migration
5. **Rollback plan:** Keep ability to revert if issues found

---

## Post-Migration Verification

Run these checks after completing all migrations:

```bash
# 1. Run full test suite
pytest tests/ -v --cov=src/sdd --cov-report=term-missing

# 2. Re-run analysis script
python scripts/analyze_error_handling_migration.py

# 3. Run integration tests
pytest tests/integration/ -v
pytest tests/e2e/ -v

# 4. Test key workflows manually
sdd init
sdd work-list
sdd start
sdd validate
sdd end

# 5. Check for remaining anti-patterns
grep -r "sys.exit" src/sdd --include="*.py" | grep -v "# OK:"
grep -r "except Exception:" src/sdd --include="*.py" | grep -v "# OK:"
```

---

## Agent Instruction Templates

### Template for Simple Files

```markdown
Migrate [FILE_NAME] to use standardized error handling.

**File:** src/sdd/[path]/[file].py
**Test:** tests/unit/test_[file].py
**Complexity:** [SCORE]

**Steps:**
1. Add imports: from sdd.core.exceptions import [relevant exceptions]
2. Replace [X] print() error statements with exceptions
3. Replace [X] broad Exception catches with specific types
4. Update tests to use pytest.raises()
5. Run tests: pytest tests/unit/test_[file].py -v
6. Verify no diagnostics introduced

**Exceptions to use:**
- [List based on file function]
```

### Template for Complex Files

```markdown
Migrate [FILE_NAME] to use standardized error handling.

**File:** src/sdd/[path]/[file].py
**Test:** tests/unit/test_[file].py
**Complexity:** [SCORE] (COMPLEX)

**Current patterns:**
- Return tuples: [X] at lines [...]
- sys.exit(): [X] at lines [...]
- print() errors: [X] at lines [...]
- Broad exceptions: [X] at lines [...]

**Migration plan:**
1. Add imports from sdd.core.exceptions
2. Replace return tuples with exceptions:
   - Function [name] at line [X]: Use [ExceptionType]
   - Function [name] at line [X]: Use [ExceptionType]
3. Remove sys.exit() calls:
   - Line [X]: Raise [ExceptionType] instead
4. Replace print() error messages:
   - Categorize: errors vs info vs warnings
   - Errors → raise exceptions
   - Info → logger.info()
   - Warnings → logger.warning()
5. Replace broad Exception catches:
   - Line [X]: Catch [SpecificType] instead
6. Add decorators:
   - @log_errors() for key functions
   - @convert_subprocess_errors for subprocess calls
7. Update all affected tests
8. Add new error path tests
9. Run full test suite

**Critical:** This file is [describe importance]. Extra care needed.
```

---

## Next Steps

1. **Review this plan** - Confirm the parallel approach and groupings
2. **Prepare agent environment** - Ensure each agent can run tests independently
3. **Start with Phase 1** - Migrate simple files first to validate approach
4. **Iterate** - Adjust strategy based on Phase 1 learnings
5. **Scale to Phase 2 & 3** - Apply lessons learned

**Ready to proceed?** We can start spawning parallel agents for Phase 1!
