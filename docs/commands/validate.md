# Validate Command

**Usage:** `/sdd:validate [--fix]`

**Description:** Check quality gates and session readiness without ending the session.

## Overview

The `validate` command runs pre-flight checks to ensure your work meets quality standards before completing the session. It's like a dry-run of `/sdd:end` without actually ending the session.

**Key benefits:**
- Catch issues early during development
- Avoid failed session completion
- Auto-fix linting and formatting issues
- Verify readiness before `/sdd:end`

## Usage

### Basic Validation

```bash
/sdd:validate
```

Runs all checks and reports results.

### Auto-Fix Mode

```bash
/sdd:validate --fix
```

Automatically fixes linting and formatting issues where possible.

## Quality Gates Checked

### 1. Tests
- Runs all test suites
- Must pass 100%
- Coverage must meet threshold

### 2. Linting
- Checks code style rules
- Identifies violations
- Can auto-fix with `--fix`

### 3. Type Checking
- TypeScript type errors (if applicable)
- Python type hints (if configured)
- Must pass with zero errors

### 4. Formatting
- Code formatting consistency
- Prettier/Black rules
- Can auto-fix with `--fix`

### 5. Git Status
- No uncommitted changes to `.session/` files
- Working directory state verified
- Branch validation

### 6. Code Coverage
- Meets minimum threshold (60%, 70%, 80%, or 90%)
- Shows current coverage percentage
- Identifies uncovered files

## Examples

### Successful Validation

```bash
/sdd:validate
```

**Output:**
```
Running session validation...
================================================================================

✓ Tests: All tests passed (18/18)
✓ Linting: No linting issues
✓ Type Checking: No type errors
✓ Formatting: Code properly formatted
✓ Git Status: Working directory ready
✓ Coverage: 85.2% (threshold: 80%)

================================================================================
✅ SESSION READY TO COMPLETE

All quality gates passed. Your work meets the standards.

Next steps:
  - Complete session:  /sdd:end
  - Continue working:  (make more changes)
  - View status:       /sdd:status
```

### Validation with Issues

```bash
/sdd:validate
```

**Output:**
```
Running session validation...
================================================================================

✓ Tests: All tests passed (18/18)
✗ Linting: 3 issues found
  src/auth/jwt.ts
    12:5   error  'token' is not defined  no-undef
    25:10  error  Missing return type     @typescript-eslint/explicit-function-return-type

  src/api/routes/auth.ts
    45:89  error  Line too long (95 > 88)  max-len

✓ Type Checking: No type errors
✗ Formatting: 2 files need formatting
  src/auth/jwt.ts
  src/middleware/auth.ts

✓ Git Status: Working directory ready
✓ Coverage: 87.5% (threshold: 80%)

================================================================================
⚠️  SESSION NOT READY

Fix the issues above before completing the session.

Quick fixes:
  - Auto-fix linting:      /sdd:validate --fix
  - Auto-fix formatting:   /sdd:validate --fix
  - Manual fixes needed:   src/auth/jwt.ts:12 (undefined variable)
```

### Auto-Fix Mode

```bash
/sdd:validate --fix
```

**Output:**
```
Running session validation with auto-fix...
================================================================================

✓ Tests: All tests passed (18/18)
⚙️  Linting: Auto-fixing...
  ✓ Fixed 2/3 issues
  ✗ Cannot auto-fix: src/auth/jwt.ts:12 ('token' is not defined)

⚙️  Formatting: Auto-formatting...
  ✓ Formatted 2 files
    - src/auth/jwt.ts
    - src/middleware/auth.ts

✓ Type Checking: No type errors
✓ Git Status: Working directory ready
✓ Coverage: 87.5% (threshold: 80%)

================================================================================
⚠️  SESSION ALMOST READY

Auto-fixed 4 issues. 1 manual fix still needed:
  src/auth/jwt.ts:12:5 - 'token' is not defined

After fixing:
  - Run /sdd:validate again to verify
  - Then /sdd:end to complete session
```

### Test Failures

```bash
/sdd:validate
```

**Output:**
```
Running session validation...
================================================================================

✗ Tests: 2/15 tests failed

Failed tests:
  tests/auth/jwt.test.ts
    ✗ should validate expired token
      Expected: 401
      Received: 200

  tests/api/auth.test.ts
    ✗ should reject invalid credentials
      AssertionError: Expected authentication to fail

✓ Linting: No linting issues
✓ Type Checking: No type errors
✓ Formatting: Code properly formatted
✓ Git Status: Working directory ready
✗ Coverage: 72.3% (threshold: 80%)

================================================================================
⚠️  SESSION NOT READY

Fix failing tests before completing the session.

Debug failing tests:
  npm test -- tests/auth/jwt.test.ts
  npm test -- tests/api/auth.test.ts

After fixing:
  - Run /sdd:validate to verify
  - Then /sdd:end when ready
```

### Coverage Below Threshold

```bash
/sdd:validate
```

**Output:**
```
Running session validation...
================================================================================

✓ Tests: All tests passed (15/15)
✓ Linting: No linting issues
✓ Type Checking: No type errors
✓ Formatting: Code properly formatted
✓ Git Status: Working directory ready
✗ Coverage: 72.5% (threshold: 80%)

Uncovered files:
  src/auth/jwt.ts          45.2% (needs +34.8%)
  src/middleware/auth.ts   68.1% (needs +11.9%)
  src/api/routes/auth.ts   89.4% ✓

================================================================================
⚠️  SESSION NOT READY

Coverage is below threshold. Add more tests.

Focus on:
  1. src/auth/jwt.ts - lowest coverage (45.2%)
  2. src/middleware/auth.ts - needs 12% more

After adding tests:
  - Run /sdd:validate to check progress
  - Then /sdd:end when threshold met
```

## Auto-Fix Capabilities

### What Can Be Auto-Fixed

**Linting:**
- Missing semicolons
- Incorrect indentation
- Unused imports (removal)
- Spacing issues
- Quote style

**Formatting:**
- Code style (Prettier/Black)
- Line breaks
- Indentation consistency
- Trailing whitespace

### What Cannot Be Auto-Fixed

**Linting:**
- Undefined variables
- Missing function implementations
- Logic errors
- Type mismatches

**Tests:**
- Test failures (require code changes)

**Coverage:**
- Low coverage (require new tests)

## Quality Gate Details

### Tests

```
✓ Tests: All tests passed (18/18)
```

- Runs all test suites (unit, integration, e2e)
- All tests must pass
- No skipped tests counted
- Test duration shown

**Common failures:**
- Assertion errors
- Timeout errors
- Setup/teardown issues

### Linting

```
✗ Linting: 3 issues found
```

- Checks code style rules
- ESLint for JavaScript/TypeScript
- Ruff for Python
- Shows file, line, and rule

**Auto-fixable:**
- Formatting issues
- Import organization
- Simple style violations

### Type Checking

```
✓ Type Checking: No type errors
```

- TypeScript: `tsc --noEmit`
- Python: `pyright` or `mypy`
- Checks all files in project

**Common errors:**
- Type mismatches
- Missing type definitions
- Invalid property access

### Formatting

```
✗ Formatting: 2 files need formatting
```

- Prettier for JavaScript/TypeScript
- Black for Python
- Consistent code style

**Auto-fixable:**
- All formatting issues
- Line length
- Indentation
- Whitespace

### Git Status

```
✓ Git Status: Working directory ready
```

- All changes committed or staged
- No uncommitted `.session/` files
- Branch validation

**Common issues:**
- Untracked files
- Uncommitted changes
- Wrong branch

### Coverage

```
✓ Coverage: 85.2% (threshold: 80%)
```

- Line coverage percentage
- Branch coverage (if configured)
- Shows uncovered files

**Meeting threshold:**
- Add tests for uncovered code
- Remove dead code
- Focus on critical paths

## Use Cases

### During Development

```bash
# Write some code
/sdd:validate
# See if tests still pass
# Fix any issues
# Continue coding
```

### Before Breaks

```bash
# Finishing for the day
/sdd:validate
# Ensure everything passes
# Leave work in good state
/sdd:end
```

### After Major Changes

```bash
# Refactored large section
/sdd:validate
# Verify nothing broke
# Check coverage maintained
```

### CI/CD Preview

```bash
# Before pushing
/sdd:validate
# See what CI will check
# Fix issues locally
# Push with confidence
```

## Integration with Other Commands

### Standard Workflow

```bash
/sdd:start feature_auth    # Begin work
# ... make changes ...
/sdd:validate              # Check quality (repeat as needed)
# ... fix issues ...
/sdd:validate              # Verify fixes
/sdd:end                   # Complete session
```

### Fix-Validate Loop

```bash
/sdd:validate              # Find issues
# ... fix manually ...
/sdd:validate --fix        # Auto-fix remaining
/sdd:validate              # Final verification
/sdd:end                   # Complete
```

### Quick Status Check

```bash
/sdd:status                # See progress
/sdd:validate              # Check quality
# Decide: continue or complete
```

## Exit Codes

When run directly (not through Claude):

```bash
sdd validate
echo $?
```

- `0` - All quality gates passed
- `1` - One or more quality gates failed
- `2` - Command error or invalid usage

Useful for CI/CD pipelines and scripts.

## Configuration

Quality gates configured in project files:

**JavaScript/TypeScript:**
- `jest.config.js` - Test and coverage settings
- `eslint.config.js` - Linting rules
- `.prettierrc` - Formatting rules
- `tsconfig.json` - Type checking

**Python:**
- `pyproject.toml` - Test, lint, format, coverage
- `pytest.ini` - Test configuration
- `ruff.toml` - Linting rules

**Coverage thresholds** set during `sdd init`:
- tier-1: 60%
- tier-2: 70%
- tier-3: 80%
- tier-4: 80%

## Best Practices

### 1. Validate Frequently

```bash
# Not just before /sdd:end
# Run during development
/sdd:validate
```

Catches issues early when they're easier to fix.

### 2. Use Auto-Fix

```bash
# Let tool fix what it can
/sdd:validate --fix
# Then fix remaining manually
```

Saves time on routine issues.

### 3. Fix Tests First

When multiple gates fail:
1. Fix tests (ensures code works)
2. Fix linting (improves code quality)
3. Fix formatting (cosmetic)

### 4. Understand Failures

Don't just make errors go away:
- Read error messages
- Understand root cause
- Fix properly, not just to pass

### 5. Check After Refactoring

Major code changes:
```bash
/sdd:validate  # Before refactor
# ... refactor ...
/sdd:validate  # After refactor
```

Ensure refactoring didn't break anything.

## Common Issues

### "Tests pass locally but validation fails"

**Cause:** Test isolation issues or environment differences

**Solution:**
```bash
# Clean and re-run
rm -rf node_modules .next
npm install
npm test
```

### "Auto-fix doesn't fix everything"

**Cause:** Some issues require manual intervention

**Solution:** Review error messages, fix manually, then re-validate

### "Coverage dropped unexpectedly"

**Cause:** Added code without tests

**Solution:** Add tests for new code or remove dead code

## Performance

Validation runs:
- Tests: Full test suite (1-60s depending on project)
- Linting: Fast (1-5s)
- Type checking: Fast (1-10s)
- Formatting: Fast (1-3s)
- Coverage: Included with tests

**Total time:** Usually 5-60 seconds depending on test suite size.

## See Also

- [End Command](end.md) - Complete session with same quality gates
- [Status Command](status.md) - Check session progress
- [Start Command](start.md) - Begin working on a work item
