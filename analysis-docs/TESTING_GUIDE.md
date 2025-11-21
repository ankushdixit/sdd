# Solokit End-to-End Template Testing Guide

## Overview

This guide walks you through comprehensive testing of all solokit project setup options, from initialization to pushing changes to a remote repository.

## Test Scope

### What We're Testing

- **4 Stacks**: saas_t3, ml_ai_fastapi, dashboard_refine, fullstack_nextjs
- **4 Tiers**: tier-1-essential, tier-2-standard, tier-3-comprehensive, tier-4-production
- **3 Options**: ci_cd, docker, env_templates
- **Complete Workflow**: init → work-new → start → code → validate → end → push

### Total Test Coverage

- **Phase 1**: 16 tests (all stack+tier combinations)
- **Phase 2**: 11 tests (options coverage)
- **Phase 3**: 4 tests (critical production paths)
- **Total**: 31 comprehensive end-to-end tests

---

## Quick Start

### Prerequisites

1. Python 3.9+ installed
2. Node.js 18+ installed (for JS stacks)
3. npm 9+ installed
4. Git installed and configured
5. solokit installed (`pip install -e .` in solokit directory)

### Running Tests

```bash
# Make the script executable
chmod +x test_all_templates.py

# Run Phase 1 (core matrix - 16 tests)
python test_all_templates.py --phase 1

# Run Phase 2 (options coverage - 11 tests)
python test_all_templates.py --phase 2

# Run Phase 3 (critical paths - 4 tests)
python test_all_templates.py --phase 3

# Run all phases (31 tests)
python test_all_templates.py --all

# Run a specific combination
python test_all_templates.py --specific saas_t3 tier-2-standard "ci_cd,docker"

# Keep test directories for inspection (don't cleanup on success)
python test_all_templates.py --phase 1 --no-cleanup

# Use custom workspace directory
python test_all_templates.py --phase 1 --workspace /tmp/my_tests
```

---

## Testing Strategy

### Phase 1: Core Matrix Testing (Priority: HIGH)

**Goal**: Validate that all base stack+tier combinations work without additional options.

**Tests**: 16 (4 stacks × 4 tiers)

**Why**: These are the foundational templates. If these fail, everything else will fail.

**Expected Duration**: ~4-6 hours (depending on system and network speed)

#### Combinations Tested:
1. saas_t3 + tier-1-essential
2. saas_t3 + tier-2-standard
3. saas_t3 + tier-3-comprehensive
4. saas_t3 + tier-4-production
5. ml_ai_fastapi + tier-1-essential
6. ml_ai_fastapi + tier-2-standard
7. ml_ai_fastapi + tier-3-comprehensive
8. ml_ai_fastapi + tier-4-production
9. dashboard_refine + tier-1-essential
10. dashboard_refine + tier-2-standard
11. dashboard_refine + tier-3-comprehensive
12. dashboard_refine + tier-4-production
13. fullstack_nextjs + tier-1-essential
14. fullstack_nextjs + tier-2-standard
15. fullstack_nextjs + tier-3-comprehensive
16. fullstack_nextjs + tier-4-production

**Key Things to Watch**:
- Dependency installation (npm/pip)
- File structure correctness
- Git initialization
- Session creation
- Quality gate execution

---

### Phase 2: Options Coverage Testing (Priority: MEDIUM)

**Goal**: Validate that additional options (CI/CD, Docker, env templates) install correctly and work with various combinations.

**Tests**: 11

**Why**: Options add significant value but are independent features that need separate validation.

**Expected Duration**: ~3-4 hours

#### Test Breakdown:

**Individual Options (3 tests)**:
- saas_t3 + tier-2-standard + ci_cd
- saas_t3 + tier-2-standard + docker
- saas_t3 + tier-2-standard + env_templates

**All Options Across Tiers (4 tests)**:
- saas_t3 + tier-1-essential + all options
- saas_t3 + tier-2-standard + all options
- saas_t3 + tier-3-comprehensive + all options
- saas_t3 + tier-4-production + all options

**All Options Across Stacks (3 tests)**:
- ml_ai_fastapi + tier-3-comprehensive + all options
- dashboard_refine + tier-3-comprehensive + all options
- fullstack_nextjs + tier-3-comprehensive + all options
(Note: saas_t3 already covered in "All Options Across Tiers")

**Edge Cases (1 test)**:
- ml_ai_fastapi + tier-4-production + all options (Python stack with production tier)

**Key Things to Watch**:
- GitHub Actions workflow files present and valid
- Dockerfile builds successfully
- docker-compose.yml valid
- .env.example has all required variables
- Options don't conflict with each other

---

### Phase 3: Critical Paths Testing (Priority: HIGH)

**Goal**: Validate production-ready configurations that users are most likely to use in real projects.

**Tests**: 4

**Why**: These are the "golden path" configurations for serious production use.

**Expected Duration**: ~2-3 hours

#### Combinations Tested:
1. saas_t3 + tier-4-production + all options
2. ml_ai_fastapi + tier-4-production + all options
3. dashboard_refine + tier-3-comprehensive + all options
4. fullstack_nextjs + tier-3-comprehensive + all options

**Key Things to Watch**:
- All quality gates pass
- Observability setup (OpenTelemetry, Sentry)
- Health check endpoints work
- E2E tests run successfully
- Deployment configurations valid
- Production-ready security measures in place

---

## Manual Testing Workflow

If you want to test manually or investigate a specific configuration:

### Step 1: Create Test Directory

```bash
mkdir ~/test_solokit_template
cd ~/test_solokit_template
```

### Step 2: Initialize Project

```bash
# Interactive mode
solokit init

# Non-interactive mode
solokit init \
  --template saas_t3 \
  --tier tier-2-standard \
  --coverage-target 80 \
  --option ci_cd \
  --option docker \
  --non-interactive
```

### Step 3: Verify Installation

Check that key files exist:

```bash
# All stacks should have:
ls -la .session/
ls -la .git/
cat README.md

# Node.js stacks should have:
cat package.json
cat tsconfig.json

# Python stack should have:
cat pyproject.toml
cat requirements.txt

# If you selected options:
ls -la .github/workflows/  # ci_cd option
cat Dockerfile             # docker option
cat .env.example          # env_templates option
```

### Step 4: Install Dependencies

```bash
# Node.js stacks
npm install

# Python stack
pip install -e .
```

### Step 5: Create Work Item

```bash
# Interactive
solokit work-new

# Or manually create:
# 1. Create .session/specs/feat_001.md
# 2. Update .session/tracking/work_items.json
```

### Step 6: Start Session

```bash
solokit start feat_001

# Verify branch created:
git branch
# Should show: work/feat_001
```

### Step 7: Create Sample Code

For Node.js stacks:

```typescript
// lib/test-feature.ts
export function add(a: number, b: number): number {
  return a + b;
}
```

```typescript
// tests/test-feature.test.ts
import { add } from '../lib/test-feature';

describe('add', () => {
  it('should add two numbers', () => {
    expect(add(2, 3)).toBe(5);
  });
});
```

For Python stack:

```python
# src/test_feature.py
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b
```

```python
# tests/test_feature.py
from src.test_feature import add

def test_add():
    assert add(2, 3) == 5
```

Commit your changes:

```bash
git add .
git commit -m "Add test feature"
```

### Step 8: Validate Session

```bash
solokit validate

# This runs all quality gates:
# - Tests (with coverage)
# - Linting
# - Formatting
# - Type checking
# - Security scans
# - Documentation checks
```

### Step 9: End Session

```bash
solokit end

# This will:
# - Run validation again
# - Commit changes
# - Update tracking files
# - Capture learnings
# - Generate session summary
```

### Step 10: Push to Remote

```bash
# Create a test remote (for testing purposes)
git remote add origin <your-test-repo-url>
git push -u origin main

# Or the feature branch:
git push -u origin work/feat_001
```

---

## Common Issues and Solutions

### Issue 1: Dependency Installation Fails

**Symptoms**: npm install or pip install fails

**Causes**:
- Network issues
- Version conflicts
- Missing system dependencies

**Solutions**:
```bash
# Node.js: Clear cache and retry
npm cache clean --force
rm -rf node_modules package-lock.json
npm install

# Python: Use virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e .
```

### Issue 2: Quality Gates Fail

**Symptoms**: sk validate or sk end fails

**Causes**:
- Code doesn't meet quality standards
- Tests don't pass
- Coverage too low

**Solutions**:
```bash
# Run individual checks to identify issue:
npm run test           # or pytest
npm run lint           # or ruff check
npm run type-check     # or pyright

# Fix issues and retry
```

### Issue 3: Git Initialization Issues

**Symptoms**: .git directory missing or corrupt

**Causes**:
- Non-blank directory
- Git not installed
- Permission issues

**Solutions**:
```bash
# Ensure directory is empty
ls -la

# Manually initialize git
git init
git add .
git commit -m "Initial commit"
```

### Issue 4: Template Files Missing

**Symptoms**: Expected files not present after init

**Causes**:
- Template installation failed
- Wrong tier/option selected
- Bug in template installer

**Solutions**:
```bash
# Check solokit logs
cat .session/logs/init.log

# Verify template registry
cat $(python -c "import solokit; print(solokit.__path__[0])")/templates/template-registry.json

# Re-run init in fresh directory
```

### Issue 5: Session Commands Don't Work

**Symptoms**: sk start, sk end, sk validate fail

**Causes**:
- Session structure not created during init
- Work item doesn't exist
- Git state issues

**Solutions**:
```bash
# Verify session structure exists
ls -la .session/

# Check work item exists
cat .session/tracking/work_items.json

# Verify git status
git status
```

---

## Tracking Progress

Use the provided `TEST_PROGRESS.md` file to track which tests have been completed and which failed.

### Interpreting Results

The test script generates a JSON file with detailed results:

```json
{
  "timestamp": "20250117_143022",
  "total_tests": 16,
  "passed": 14,
  "failed": 2,
  "total_duration_seconds": 7234.5,
  "results": [
    {
      "test_id": "p1_001_saas_t3_tier-1-essential",
      "stack": "saas_t3",
      "tier": "tier-1-essential",
      "options": [],
      "success": true,
      "duration_seconds": 423.2,
      "errors": [],
      "warnings": [],
      "steps_completed": [
        "create_directory",
        "initialize",
        "verify_installation",
        "install_dependencies",
        "create_work_item",
        "start_session",
        "create_code",
        "validate_session",
        "end_session",
        "push_to_remote"
      ]
    }
  ]
}
```

### What to Do When Tests Fail

1. **Check the error messages** in the results JSON
2. **Inspect the project directory** (it's kept for failed tests)
3. **Review steps_completed** to see where it failed
4. **Try manually reproducing** the issue
5. **File issues** with details or fix the template directly

---

## Fixing Template Issues

When you find an issue, follow this process:

### 1. Identify the Issue

- Which stack/tier/option combination?
- What step fails?
- What's the error message?
- Is it reproducible?

### 2. Locate the Template Files

Templates are in: `/src/solokit/templates/{stack}/`

Structure:
```
saas_t3/
├── base/                 # Core files (always installed)
├── tier-1-essential/     # Tier 1 additions
├── tier-2-standard/      # Tier 2 additions
├── tier-3-comprehensive/ # Tier 3 additions
├── tier-4-production/    # Tier 4 additions
├── ci-cd/               # CI/CD option
├── docker/              # Docker option
└── env-templates/       # Environment templates option
```

### 3. Make the Fix

Example: Fix missing file in tier-2-standard

```bash
cd src/solokit/templates/saas_t3/tier-2-standard/
# Add or edit the problematic file
vi .husky/pre-commit
```

### 4. Test the Fix

```bash
# Run the specific test case again
python test_all_templates.py --specific saas_t3 tier-2-standard ""

# Or manually test
mkdir ~/test_fix
cd ~/test_fix
solokit init --template saas_t3 --tier tier-2-standard --non-interactive
```

### 5. Verify No Regressions

```bash
# Run all tests for that stack
python test_all_templates.py --phase 1 | grep saas_t3
```

### 6. Update Tests

If you added new functionality, add tests:

```bash
# Add unit test
vi tests/unit/init/test_template_installer.py

# Add integration test
vi tests/integration/init/test_stack_generation.py
```

### 7. Commit the Fix

```bash
git add src/solokit/templates/
git commit -m "Fix: Missing pre-commit hook in tier-2-standard for saas_t3"
```

---

## Known Issues to Watch For

Based on the analysis, here are known issues you might encounter:

### 1. Sentry Installation (tier-4-production, Node.js stacks)
- **Issue**: `@sentry/nextjs` requires `patch-package` to be installed first
- **Expected**: Installation may fail or require manual intervention
- **Fix**: Add `patch-package` as dependency or update installation order

### 2. Pre-commit Hooks (tier-2+)
- **Issue**: Removed from tier-2+ due to conflicts
- **Expected**: Pre-commit hooks not installed even though documented
- **Fix**: Either re-add as option or update documentation

### 3. Python Version Compatibility
- **Issue**: Some tier-3+ dependencies require Python 3.11+
- **Expected**: Installation fails on Python 3.9 or 3.10
- **Fix**: Update requirements or add version checks

### 4. Coverage Thresholds
- **Issue**: Strict coverage enforcement may fail on minimal code
- **Expected**: Validation fails even with working code
- **Fix**: Adjust coverage thresholds for test scenarios

### 5. Dependency Vulnerabilities
- **Issue**: `@lhci/cli` has 4 LOW severity vulnerabilities
- **Expected**: Security scans may flag these
- **Fix**: These are accepted dev dependencies; update security config

---

## Performance Benchmarks

Expected duration for each test:

| Stack | Tier | Avg Duration | Notes |
|-------|------|--------------|-------|
| saas_t3 | tier-1 | 6-8 min | npm install ~5 min |
| saas_t3 | tier-2 | 7-9 min | + Husky setup |
| saas_t3 | tier-3 | 10-12 min | + Playwright install |
| saas_t3 | tier-4 | 12-15 min | + Sentry setup |
| ml_ai_fastapi | tier-1 | 3-5 min | pip install faster |
| ml_ai_fastapi | tier-2 | 4-6 min | + security tools |
| ml_ai_fastapi | tier-3 | 6-8 min | + locust |
| ml_ai_fastapi | tier-4 | 7-10 min | + OpenTelemetry |
| dashboard_refine | tier-1 | 6-8 min | Similar to saas_t3 |
| fullstack_nextjs | tier-1 | 6-8 min | Similar to saas_t3 |

**Total estimated time for all 31 tests**: 6-10 hours

---

## Next Steps After Testing

1. **Review Results**: Analyze the JSON results file
2. **Fix Issues**: Address any failed tests
3. **Update Documentation**: Document any quirks or workarounds found
4. **Add Regression Tests**: Create tests for bugs you fixed
5. **Improve Templates**: Enhance based on findings
6. **Update Version**: Bump version after fixes

---

## Support

If you encounter issues not covered in this guide:

1. Check the results JSON for detailed error messages
2. Review the project directory that failed (kept automatically)
3. Try running the workflow manually to isolate the issue
4. Check solokit logs in `.session/logs/`
5. File an issue with reproduction steps

---

## Appendix: Test Checklist

See `TEST_PROGRESS.md` for a complete checklist of all 31 tests.
