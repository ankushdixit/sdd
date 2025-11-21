# Solokit Template Testing - Quick Start

## What This Is

A comprehensive testing suite to validate all solokit project setup options end-to-end.

## What Gets Tested

- **4 Stacks**: SaaS T3, ML/AI FastAPI, Dashboard Refine, Full-Stack Next.js
- **4 Tiers**: Essential, Standard, Comprehensive, Production-Ready
- **3 Options**: CI/CD, Docker, Environment Templates
- **Complete Workflow**: init → create work item → start session → code → validate → end → push

## Quick Start (5 minutes to first test)

### 1. Install Prerequisites

```bash
# Verify you have everything
python --version   # 3.9+
node --version     # 18+
npm --version      # 9+
git --version      # Any recent version

# Install solokit if not already
pip install -e .
```

### 2. Run Your First Test

```bash
# Test a single configuration
python test_all_templates.py --specific saas_t3 tier-1-essential ""

# This will:
# - Create a test project
# - Install dependencies
# - Create a work item
# - Start a session
# - Create sample code
# - Validate and end session
# - Push to a test remote
# - Report results
```

### 3. View Results

```bash
# Analyze the results
python analyze_test_results.py --latest

# Or specify a results file
python analyze_test_results.py test_results/test_results_20250117_143022.json
```

## Running Complete Test Suites

### Phase 1: Core Testing (16 tests, ~4-6 hours)

Tests all stack+tier combinations without options.

```bash
python test_all_templates.py --phase 1
```

**When to run**: Before any release to ensure base templates work.

### Phase 2: Options Testing (11 tests, ~3-4 hours)

Tests additional options (CI/CD, Docker, env templates).

```bash
python test_all_templates.py --phase 2
```

**When to run**: When you modify optional features.

### Phase 3: Critical Paths (4 tests, ~2-3 hours)

Tests production-ready configurations.

```bash
python test_all_templates.py --phase 3
```

**When to run**: Before major releases or when validating production templates.

### All Tests (31 tests, ~6-10 hours)

```bash
python test_all_templates.py --all
```

**When to run**: Major releases, quarterly validation, after significant template changes.

## Analyzing Results

### Quick Summary

```bash
python analyze_test_results.py --latest --summary
```

### Full Analysis

```bash
python analyze_test_results.py --latest --all
```

### Specific Sections

```bash
# Just show failures
python analyze_test_results.py --latest --failures

# Stack-by-stack breakdown
python analyze_test_results.py --latest --stacks

# Performance metrics
python analyze_test_results.py --latest --performance

# Get recommendations
python analyze_test_results.py --latest --recommendations
```

### Generate Markdown Report

```bash
python analyze_test_results.py --latest --markdown TEST_REPORT.md
```

## Tracking Progress

Use the provided checklist:

```bash
# Open in your editor
code TEST_PROGRESS.md

# Or view in terminal
cat TEST_PROGRESS.md
```

Update checkboxes as you complete tests and add notes about issues found.

## When Tests Fail

### 1. Check the Results

```bash
python analyze_test_results.py --latest --failures
```

### 2. Inspect the Project

Failed test directories are kept automatically:

```bash
cd ~/solokit_test_workspace/test_p1_001_saas_t3_tier-1-essential
ls -la
```

### 3. Try Manual Reproduction

```bash
mkdir ~/manual_test
cd ~/manual_test
solokit init --template saas_t3 --tier tier-1-essential --non-interactive
# ... follow the manual steps in TESTING_GUIDE.md
```

### 4. Fix the Issue

```bash
# Find the template files
cd src/solokit/templates/saas_t3/

# Edit the problematic file
vi tier-1-essential/jest.config.ts

# Test the fix
python test_all_templates.py --specific saas_t3 tier-1-essential ""
```

### 5. Verify No Regressions

```bash
# Run all tests for that stack
python test_all_templates.py --phase 1
```

## Advanced Usage

### Custom Workspace

```bash
python test_all_templates.py --phase 1 --workspace /tmp/my_tests
```

### Keep Test Directories

```bash
python test_all_templates.py --phase 1 --no-cleanup
```

### Test Specific Combination

```bash
# Stack, tier, comma-separated options
python test_all_templates.py --specific saas_t3 tier-2-standard "ci_cd,docker"
```

## Files Created

- **test_all_templates.py** - Main testing script
- **analyze_test_results.py** - Results analysis script
- **TESTING_GUIDE.md** - Comprehensive testing guide
- **TEST_PROGRESS.md** - Progress tracking checklist
- **test_results/** - JSON results files (auto-created)
- **~/solokit_test_workspace/** - Test projects (auto-created)

## Expected Timeline

| Phase | Tests | Duration | Best For |
|-------|-------|----------|----------|
| Single Test | 1 | 5-15 min | Quick validation |
| Phase 1 | 16 | 4-6 hours | Core template validation |
| Phase 2 | 11 | 3-4 hours | Options validation |
| Phase 3 | 4 | 2-3 hours | Production readiness |
| All Phases | 31 | 6-10 hours | Complete validation |

## Tips for Success

1. **Start Small**: Run a single test first to ensure your environment is set up correctly
2. **Run Overnight**: Full test suites take hours; run them overnight or during lunch
3. **Monitor Progress**: Check `test_results/` periodically to catch issues early
4. **Keep Notes**: Use TEST_PROGRESS.md to track issues and insights
5. **Fix Incrementally**: Don't wait until all tests complete; fix issues as you find them
6. **Check Disk Space**: Each test creates a project; ensure you have 10GB+ free

## Common Issues

### "Command not found: solokit"

```bash
# Install solokit first
pip install -e .

# Or use full path
python -m solokit init ...
```

### "Permission denied"

```bash
# Make scripts executable
chmod +x test_all_templates.py analyze_test_results.py
```

### "Dependency installation too slow"

```bash
# Use npm cache or pip cache
npm cache verify
pip cache info

# Or run on faster network
```

### "Tests timing out"

```bash
# Edit test_all_templates.py and increase timeout values
# Look for timeout=300, timeout=600, timeout=900
# Increase as needed for slow systems
```

## Next Steps

1. **Read TESTING_GUIDE.md** for comprehensive details
2. **Run a single test** to verify your setup
3. **Run Phase 1** to test core templates
4. **Track progress** in TEST_PROGRESS.md
5. **Fix issues** as you find them
6. **Run remaining phases** as needed

## Getting Help

If you encounter issues:

1. Check the **TESTING_GUIDE.md** for detailed troubleshooting
2. Review the **error messages** in the results JSON
3. Inspect the **failed project directory**
4. Try **manual reproduction** following the guide
5. Check **solokit logs** in `.session/logs/`

## Summary

You now have a complete testing infrastructure to validate all solokit templates. Start with a single test, verify everything works, then run full phases as needed. Good luck!
