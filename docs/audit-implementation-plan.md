# SDD Codebase Audit - Implementation Plan

**Created**: October 18, 2025
**Based on**: Comprehensive Codebase Audit Report
**Overall Assessment**: 8.9/10 (Production Ready)
**Status**: Planning Phase

## Executive Summary

This document provides a detailed implementation plan for addressing the recommendations from the comprehensive codebase audit. The work is organized into 7 separate branches, prioritized by impact and urgency.

**Context Needed**: Token usage in audit session was ~31k/200k, so plenty of room for implementation in fresh sessions.

---

## Branch Organization Strategy

- **Individual branches per recommendation** - Maximum granularity for review
- **High Priority first (Branches 1-3)** - Critical improvements
- **Medium Priority second (Branches 4-7)** - Quality of life improvements
- **Base branch**: `main` (currently clean per git status)

---

## HIGH PRIORITY IMPLEMENTATIONS

### Branch 1: `feature/add-requirements-txt`

**Priority**: CRITICAL
**Estimated Effort**: 2-3 hours
**Risk**: Low
**Dependencies**: None

#### Objective
Create comprehensive `requirements.txt` with exact version pinning for all dependencies (core, optional, and development).

#### Current State
- No requirements.txt, pyproject.toml, or setup.py exists
- Dependencies scattered across documentation
- Cannot reproduce exact environment
- Difficult for new contributors to set up

#### Implementation Steps

**Step 1: Identify all dependencies**
```bash
# Search codebase for import statements
cd /Users/ankushdixit/Projects/sdd
grep -r "^import \|^from " scripts/ --include="*.py" | sort | uniq

# Search documentation for mentioned tools
grep -r "pytest\|ruff\|bandit\|safety\|eslint\|prettier" docs/ README.md
```

**Step 2: Check installed versions**
```bash
# If tools are installed, get exact versions
pip list | grep -E "pytest|ruff|bandit|safety"
npm list -g --depth=0 | grep -E "eslint|prettier"
```

**Step 3: Create requirements.txt**

Location: `/Users/ankushdixit/Projects/sdd/requirements.txt`

```txt
# SDD (Session-Driven Development) - Python Dependencies
# Generated: 2025-10-18

# ============================================================================
# CORE DEPENDENCIES (Required for basic functionality)
# ============================================================================
# Currently: None (uses Python 3.9+ standard library only)


# ============================================================================
# TESTING DEPENDENCIES (Required to run test suite)
# ============================================================================
pytest==7.4.3
pytest-cov==4.1.0


# ============================================================================
# CODE QUALITY TOOLS (Required for quality gates)
# ============================================================================
# Python linting and formatting
ruff==0.1.6

# Security scanning
bandit==1.7.5
safety==2.3.5


# ============================================================================
# OPTIONAL DEPENDENCIES (For specific features)
# ============================================================================
# Graph visualization (requires system graphviz installation)
# Uncomment if using /work-graph --format svg
# graphviz==0.20.1

# Docker support (for integration testing)
# docker==6.1.3
# docker-compose==1.29.2


# ============================================================================
# DEVELOPMENT DEPENDENCIES
# ============================================================================
# None currently - consider adding:
# ipython==8.17.2  # Better REPL for debugging
# black==23.11.0   # If preferring black over ruff format
```

**Step 4: Create requirements-dev.txt (optional but recommended)**

Location: `/Users/ankushdixit/Projects/sdd/requirements-dev.txt`

```txt
# Development dependencies (includes everything from requirements.txt)
-r requirements.txt

# Additional dev-only tools
ipython==8.17.2
black==23.11.0
```

**Step 5: Update README.md installation section**

Find section in `/Users/ankushdixit/Projects/sdd/README.md` (around line 50-100) and update:

```markdown
## Installation

### Prerequisites
- Python 3.9 or higher
- Git
- (Optional) Graphviz for graph visualization

### Quick Install

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd sdd
   ```

2. Install Python dependencies:
   ```bash
   # Core and testing dependencies
   pip install -r requirements.txt

   # Or for development (includes additional tools)
   pip install -r requirements-dev.txt
   ```

3. (Optional) Install JavaScript quality tools:
   ```bash
   npm install -g eslint prettier
   ```

4. (Optional) Install Graphviz for visualization:
   ```bash
   # macOS
   brew install graphviz

   # Ubuntu/Debian
   sudo apt-get install graphviz

   # Windows
   choco install graphviz
   ```

### Verify Installation

```bash
# Run test suite
pytest tests/

# Check quality tools
ruff check scripts/
bandit -r scripts/
```
```

**Step 6: Test installation in clean environment**

```bash
# Create test virtual environment
cd /tmp
python3 -m venv test_sdd_install
source test_sdd_install/bin/activate

# Clone and install
git clone /Users/ankushdixit/Projects/sdd test_sdd
cd test_sdd
git checkout feature/add-requirements-txt
pip install -r requirements.txt

# Verify
pytest tests/ -v
ruff check scripts/

# Cleanup
deactivate
cd /tmp
rm -rf test_sdd_install test_sdd
```

#### Success Criteria
- [ ] requirements.txt created with exact versions
- [ ] All dependencies from audit identified
- [ ] Installation tested in clean virtual environment
- [ ] README.md updated with installation instructions
- [ ] Tests pass after fresh install

#### Git Workflow
```bash
git checkout main
git pull origin main
git checkout -b feature/add-requirements-txt

# Make changes
git add requirements.txt README.md
git commit -m "Add requirements.txt with pinned dependencies

- Create requirements.txt with exact version pins
- Separate core, testing, quality, and optional dependencies
- Update README.md installation instructions
- Tested in clean virtual environment

Addresses audit recommendation: High Priority #1"

git push -u origin feature/add-requirements-txt

# Create PR
gh pr create --title "Add requirements.txt with pinned dependencies" \
  --body "$(cat <<'EOF'
## Summary
- Adds comprehensive requirements.txt with exact version pinning
- Updates README.md installation instructions
- Addresses High Priority recommendation #1 from codebase audit

## Changes
- New file: requirements.txt (all dependencies with exact versions)
- Updated: README.md (installation section)

## Testing
- Tested installation in clean virtual environment
- All tests pass after fresh install
- Quality tools (ruff, bandit) verified

## Audit Reference
Addresses critical finding: Missing dependency declaration (impact: HIGH)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

### Branch 2: `feature/add-ci-cd-pipeline`

**Priority**: HIGH
**Estimated Effort**: 3-4 hours
**Risk**: Low
**Dependencies**: Branch 1 (requirements.txt)

#### Objective
Add GitHub Actions workflow to automate testing, linting, and security scanning on all pushes and PRs.

#### Current State
- No CI/CD pipeline exists
- Tests run manually only
- No automated quality checks
- Risk of regressions on PRs

#### Implementation Steps

**Step 1: Create GitHub Actions workflow directory**
```bash
mkdir -p .github/workflows
```

**Step 2: Create main test workflow**

Location: `/Users/ankushdixit/Projects/sdd/.github/workflows/tests.yml`

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    name: Test Python ${{ matrix.python-version }}
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11", "3.12"]

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}
        cache: 'pip'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run tests with pytest
      run: |
        pytest tests/ -v --tb=short

    - name: Upload test results
      if: always()
      uses: actions/upload-artifact@v4
      with:
        name: test-results-${{ matrix.python-version }}
        path: |
          .pytest_cache/
          test-results/

  lint:
    name: Lint and Format Check
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.11"
        cache: 'pip'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install ruff

    - name: Run ruff check
      run: |
        ruff check scripts/ tests/ sdd_cli.py

    - name: Run ruff format check
      run: |
        ruff format --check scripts/ tests/ sdd_cli.py

  security:
    name: Security Scanning
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.11"
        cache: 'pip'

    - name: Install security tools
      run: |
        python -m pip install --upgrade pip
        pip install bandit safety

    - name: Run bandit security scan
      run: |
        bandit -r scripts/ sdd_cli.py -f json -o bandit-report.json
        bandit -r scripts/ sdd_cli.py

    - name: Run safety check
      run: |
        pip install -r requirements.txt
        safety check --json || true  # Don't fail on vulnerabilities, just warn

    - name: Upload security reports
      if: always()
      uses: actions/upload-artifact@v4
      with:
        name: security-reports
        path: |
          bandit-report.json

  coverage:
    name: Test Coverage
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.11"
        cache: 'pip'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run tests with coverage
      run: |
        pytest tests/ --cov=scripts --cov-report=xml --cov-report=term

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v4
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
        fail_ci_if_error: false
```

**Step 3: Create pre-commit workflow (optional but recommended)**

Location: `/Users/ankushdixit/Projects/sdd/.github/workflows/pre-commit.yml`

```yaml
name: Pre-commit Checks

on:
  pull_request:
    branches: [ main, develop ]

jobs:
  pre-commit:
    name: Pre-commit Checks
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.11"

    - name: Check for secrets
      run: |
        # Check for common secret patterns
        ! grep -r "password\s*=\s*['\"].*['\"]" scripts/ tests/ || (echo "Found hardcoded password" && exit 1)
        ! grep -r "api_key\s*=\s*['\"].*['\"]" scripts/ tests/ || (echo "Found hardcoded API key" && exit 1)
        ! grep -r "secret\s*=\s*['\"].*['\"]" scripts/ tests/ || (echo "Found hardcoded secret" && exit 1)

    - name: Check file sizes
      run: |
        # Check for large files (>1MB)
        find . -type f -size +1M ! -path "./.git/*" -exec ls -lh {} \; | awk '{print $9, $5}' || true

    - name: Check for debug statements
      run: |
        # Warn about debug statements (don't fail)
        grep -rn "import pdb\|pdb.set_trace()\|breakpoint()" scripts/ tests/ || true
```

**Step 4: Update README.md with badges**

Add to top of `/Users/ankushdixit/Projects/sdd/README.md` (after existing badges):

```markdown
[![Tests](https://github.com/<username>/sdd/workflows/Tests/badge.svg)](https://github.com/<username>/sdd/actions?query=workflow%3ATests)
[![codecov](https://codecov.io/gh/<username>/sdd/branch/main/graph/badge.svg)](https://codecov.io/gh/<username>/sdd)
```

**Step 5: Create .codecov.yml (optional - for coverage config)**

Location: `/Users/ankushdixit/Projects/sdd/.codecov.yml`

```yaml
coverage:
  status:
    project:
      default:
        target: auto
        threshold: 1%
    patch:
      default:
        target: auto
        threshold: 1%

comment:
  layout: "header, diff, flags, files"
  behavior: default
  require_changes: false
```

**Step 6: Test workflow locally (if act is installed)**

```bash
# Install act (GitHub Actions local runner)
# macOS: brew install act
# Then test:
act -l  # List available jobs
act push  # Simulate push event
```

#### Success Criteria
- [ ] GitHub Actions workflows created
- [ ] Tests run on Python 3.9, 3.10, 3.11, 3.12
- [ ] Linting and security checks included
- [ ] Workflows trigger on push/PR
- [ ] Badges added to README.md
- [ ] First workflow run succeeds

#### Git Workflow
```bash
git checkout main
git pull origin main
git checkout -b feature/add-ci-cd-pipeline

# Make changes
git add .github/ README.md .codecov.yml
git commit -m "Add GitHub Actions CI/CD pipeline

- Create test workflow for Python 3.9-3.12
- Add linting workflow with ruff
- Add security scanning with bandit and safety
- Add coverage reporting with codecov
- Add pre-commit checks for secrets and file sizes
- Update README with CI badges

Addresses audit recommendation: High Priority #2"

git push -u origin feature/add-ci-cd-pipeline

# Create PR (this will trigger the workflows!)
gh pr create --title "Add GitHub Actions CI/CD pipeline" \
  --body "..." # Similar to Branch 1
```

---

### Branch 3: `feature/resolve-todos`

**Priority**: HIGH
**Estimated Effort**: 2-4 hours
**Risk**: Medium (requires understanding context)
**Dependencies**: None

#### Objective
Review and resolve all TODO/FIXME/HACK comments in the codebase (6 files identified).

#### Current State
- 6 files contain TODO/FIXME markers
- Technical debt not tracked
- Unclear what's intentional vs. forgotten

#### Files to Review

**File 1: `scripts/session_complete.py`**
```bash
grep -n "TODO\|FIXME\|HACK" scripts/session_complete.py
```
Action: Review each TODO, determine if it should be:
- Completed now
- Converted to work item
- Removed (if no longer relevant)

**File 2: `scripts/quality_gates.py`**
```bash
grep -n "TODO\|FIXME\|HACK" scripts/quality_gates.py
```
Action: Same as above

**File 3: `scripts/briefing_generator.py`**
```bash
grep -n "TODO\|FIXME\|HACK" scripts/briefing_generator.py
```
Action: Same as above

**File 4: `scripts/environment_validator.py`**
```bash
grep -n "TODO\|FIXME\|HACK" scripts/environment_validator.py
```
Action: Same as above

**File 5: `scripts/deployment_executor.py`**
```bash
grep -n "TODO\|FIXME\|HACK" scripts/deployment_executor.py
```
Action: Same as above

**File 6: `tests/phase_5_5/test_phase_5_5_6.py`**
```bash
grep -n "TODO\|FIXME\|HACK" tests/phase_5_5/test_phase_5_5_6.py
```
Action: Same as above

#### Implementation Strategy

**For each TODO found:**

1. **Read surrounding context** - Understand what the TODO is suggesting
2. **Determine action**:
   - **Complete now** - If simple and clear
   - **Create work item** - If requires significant work
   - **Remove** - If no longer applicable
   - **Document** - If intentional deferred work

3. **If creating work item**: Use `/work-new` to create proper work item with:
   - Type: improvement or bug
   - Priority: based on impact
   - Description: from TODO comment
   - Rationale: why it's being deferred

**Example approach**:
```bash
# Start session
cd /Users/ankushdixit/Projects/sdd

# Review first file
cat scripts/session_complete.py | grep -B5 -A5 "TODO"

# For each TODO, decide and either:
# Option A: Fix it now (edit file)
# Option B: Create work item
./sdd_cli.py work-new
# Option C: Remove if stale
```

#### Tracking Template

Create temporary tracking file during implementation:

`/tmp/todo-resolution-tracking.md`:
```markdown
# TODO Resolution Tracking

## scripts/session_complete.py
- Line X: TODO description
  - Action: [COMPLETED | WORK_ITEM | REMOVED | KEPT]
  - Work Item ID (if applicable): work_item_XXX
  - Notes: ...

## scripts/quality_gates.py
- Line Y: TODO description
  - Action: ...

... (repeat for all files)
```

#### Success Criteria
- [ ] All 6 files reviewed
- [ ] All TODOs resolved (completed, tracked, or removed)
- [ ] Work items created for deferred work
- [ ] No orphaned TODO comments remain
- [ ] Tests still pass

#### Git Workflow
```bash
git checkout main
git pull origin main
git checkout -b feature/resolve-todos

# Review and fix each file
# (Iterative process)

git add scripts/*.py tests/phase_5_5/test_phase_5_5_6.py
git commit -m "Resolve all TODO/FIXME comments in codebase

Files reviewed and updated:
- scripts/session_complete.py
- scripts/quality_gates.py
- scripts/briefing_generator.py
- scripts/environment_validator.py
- scripts/deployment_executor.py
- tests/phase_5_5/test_phase_5_5_6.py

Actions taken:
- Completed X actionable TODOs
- Created Y work items for complex deferred work
- Removed Z stale comments

Addresses audit recommendation: High Priority #3"

git push -u origin feature/resolve-todos
gh pr create # ...
```

---

## MEDIUM PRIORITY IMPLEMENTATIONS

### Branch 4: `feature/add-logging-framework`

**Priority**: MEDIUM
**Estimated Effort**: 6-8 hours
**Risk**: Medium (refactoring core modules)
**Dependencies**: None (but test with Branch 1 requirements.txt)

#### Objective
Replace print() statements with Python logging module in core modules only, while keeping print() in CLI entry points for user-facing output.

#### Scope Decision (from user preferences)
- **Core modules only**: work_item_manager.py, quality_gates.py, briefing_generator.py, spec_parser.py, learning_curator.py
- **Keep print() in**: sdd_cli.py, slash command files (.claude/commands/*.py if any)

#### Current State
- 459 print() statements across codebase
- No centralized logging configuration
- Cannot control verbosity
- Harder to debug production issues

#### Implementation Steps

**Step 1: Create logging configuration module**

Location: `/Users/ankushdixit/Projects/sdd/scripts/logging_config.py`

```python
"""Centralized logging configuration for SDD."""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """
    Configure logging for SDD.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to write logs to
        format_string: Optional custom format string

    Returns:
        Configured root logger
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Create formatter
    formatter = logging.Formatter(format_string)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.

    Args:
        name: Module name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
```

**Step 2: Update sdd_cli.py to support --verbose flag**

Add to `/Users/ankushdixit/Projects/sdd/sdd_cli.py` (near top of main function):

```python
import argparse
from scripts.logging_config import setup_logging

def main():
    """Main entry point for SDD CLI."""
    # Parse global flags
    parser = argparse.ArgumentParser(
        description="Session-Driven Development CLI",
        add_help=False  # We'll handle help in subcommands
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose (DEBUG) logging"
    )
    parser.add_argument(
        "--log-file",
        type=str,
        help="Write logs to file"
    )

    # Parse known args (leaves unknown for subcommands)
    args, remaining = parser.parse_known_args()

    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    log_file = Path(args.log_file) if args.log_file else None
    setup_logging(level=log_level, log_file=log_file)

    # Continue with existing command routing...
    # (rest of existing main() code)
```

**Step 3: Refactor work_item_manager.py**

Pattern to apply:
```python
# At top of file
from scripts.logging_config import get_logger

logger = get_logger(__name__)

# Replace patterns:
# OLD: print(f"✓ Work item created: {work_id}")
# NEW: logger.info("Work item created: %s", work_id)
#      print(f"✓ Work item created: {work_id}")  # Keep for user feedback

# OLD: print(f"Error: {error}")
# NEW: logger.error("Error: %s", error)
#      print(f"❌ Error: {error}")  # Keep for user feedback

# OLD: print(f"Debug: {debug_info}") (if exists)
# NEW: logger.debug("Debug: %s", debug_info)
#      # Remove print for debug info
```

**Guidelines**:
- **User-facing success/error messages**: Keep print() + add logger call
- **Internal state changes**: logger only (no print)
- **Debug information**: logger.debug() only (no print)
- **Warnings**: logger.warning() + print if user needs to know

**Step 4: Refactor quality_gates.py**

Same pattern as Step 3. Focus areas:
- Gate execution results (user-facing: keep print + add logger)
- Internal validation logic (logger only)
- Tool execution details (logger.debug only)

**Step 5: Refactor briefing_generator.py**

Same pattern. Focus areas:
- Briefing generation progress (user-facing: keep print + add logger)
- Context loading details (logger.debug only)
- File parsing (logger.debug only)

**Step 6: Refactor spec_parser.py**

Same pattern. Focus areas:
- Parsing errors (logger.error + print for user)
- Parsing progress (logger.debug only)
- Validation warnings (logger.warning + print for user)

**Step 7: Refactor learning_curator.py**

Same pattern. Focus areas:
- Curation results (user-facing: keep print + add logger)
- Similarity calculations (logger.debug only)
- Internal curation logic (logger only)

**Step 8: Update documentation**

Add to `/Users/ankushdixit/Projects/sdd/README.md` in usage section:

```markdown
### Logging and Debugging

SDD uses Python's logging module. Control verbosity:

```bash
# Normal output (INFO level)
./sdd_cli.py status

# Verbose output (DEBUG level)
./sdd_cli.py --verbose status

# Save logs to file
./sdd_cli.py --log-file sdd.log status

# Combine flags
./sdd_cli.py --verbose --log-file debug.log start
```

Log levels:
- **INFO**: Normal operation, important events
- **DEBUG**: Detailed diagnostic information
- **WARNING**: Something unexpected but handled
- **ERROR**: Something failed
```

**Step 9: Add tests for logging**

Create `/Users/ankushdixit/Projects/sdd/tests/test_logging.py`:

```python
"""Tests for logging configuration."""

import logging
from pathlib import Path
from scripts.logging_config import setup_logging, get_logger


def test_setup_logging_default():
    """Test default logging setup."""
    logger = setup_logging()
    assert logger.level == logging.INFO
    assert len(logger.handlers) >= 1


def test_setup_logging_debug():
    """Test DEBUG level logging."""
    logger = setup_logging(level="DEBUG")
    assert logger.level == logging.DEBUG


def test_setup_logging_with_file(tmp_path):
    """Test logging to file."""
    log_file = tmp_path / "test.log"
    logger = setup_logging(log_file=log_file)

    logger.info("Test message")

    assert log_file.exists()
    content = log_file.read_text()
    assert "Test message" in content


def test_get_logger():
    """Test getting module-specific logger."""
    logger = get_logger("test_module")
    assert logger.name == "test_module"
```

#### Success Criteria
- [ ] logging_config.py created
- [ ] sdd_cli.py supports --verbose and --log-file
- [ ] 5 core modules refactored (work_item_manager, quality_gates, briefing_generator, spec_parser, learning_curator)
- [ ] User-facing print() statements preserved
- [ ] Internal operations use logger only
- [ ] Documentation updated
- [ ] Tests pass
- [ ] Logging tests added

#### Git Workflow
```bash
git checkout main
git pull origin main
git checkout -b feature/add-logging-framework

# Implement changes
git add scripts/logging_config.py scripts/work_item_manager.py # ... etc
git commit -m "Add Python logging framework to core modules

- Create centralized logging configuration
- Add --verbose and --log-file flags to CLI
- Refactor 5 core modules to use logging:
  - work_item_manager.py
  - quality_gates.py
  - briefing_generator.py
  - spec_parser.py
  - learning_curator.py
- Preserve user-facing print() statements
- Add logging tests
- Update documentation

Addresses audit recommendation: Medium Priority #4"

git push -u origin feature/add-logging-framework
gh pr create # ...
```

---

### Branch 5: `feature/add-changelog`

**Priority**: MEDIUM
**Estimated Effort**: 2-3 hours
**Risk**: Low
**Dependencies**: None

#### Objective
Create CHANGELOG.md following Keep a Changelog format, documenting all phases from ROADMAP.md as releases.

#### Current State
- No CHANGELOG.md exists
- Release history scattered in ROADMAP.md
- Difficult for users to track changes between versions

#### Implementation Steps

**Step 1: Review ROADMAP.md for version history**

```bash
grep -n "Phase\|Status:\|Completion Date:" /Users/ankushdixit/Projects/sdd/ROADMAP.md
```

Extract:
- Phase numbers (map to version numbers)
- Completion dates
- Major features per phase
- Statistics (tests, LOC)

**Step 2: Create CHANGELOG.md**

Location: `/Users/ankushdixit/Projects/sdd/CHANGELOG.md`

Template based on [Keep a Changelog](https://keepachangelog.com/):

```markdown
# Changelog

All notable changes to the SDD (Session-Driven Development) project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Individual branches for audit recommendations
- CI/CD pipeline
- Logging framework
- Package refactoring

## [0.5.7] - 2024-XX-XX (Phase 5.7 Complete)

### Added
- Spec-first architecture with full context loading
- Comprehensive markdown parser for spec files (700+ lines)
- Support for 6 work item types in spec format
- HTML comment stripping and parsing
- Section-based extraction for all work item fields

### Changed
- Work items now store minimal tracking data only
- Full content loaded from `.session/specs/*.md` files
- Eliminated dual storage of content
- No content truncation or compression

### Technical Details
- **Tests Added**: 49 tests across 6 test files
- **Code Added**: ~1,200 lines (spec_parser.py + updates)
- **Documentation**: spec-template-structure.md, writing-specs.md

### Reference
See ROADMAP.md Phase 5.7 for complete details.

## [0.5.6] - 2024-XX-XX (Phase 5.6 Complete)

### Added
- Deployment automation framework
- Docker Compose support
- Health check validation
- Rollback mechanisms
- Production deployment workflows

### Changed
- Quality gates now include deployment validation
- Session completion includes optional deployment

### Technical Details
- **Tests Added**: 65 tests across 5 test files
- **Code Added**: ~800 lines (deployment_executor.py)
- **Focus**: Production deployment safety

### Reference
See ROADMAP.md Phase 5.6 for complete details.

## [0.5.5] - 2024-XX-XX (Phase 5.5 Complete)

### Added
- Comprehensive integration testing framework
- Multi-scenario integration tests
- 178 integration tests covering all workflows
- E2E testing for complete session workflows
- Docker integration for deployment testing

### Changed
- Quality gates now tested in integration scenarios
- Work item creation tested across all types
- Learning system tested end-to-end

### Technical Details
- **Tests Added**: 178 tests across 7 test files
- **Coverage**: All core workflows
- **Focus**: System integration validation

### Reference
See ROADMAP.md Phase 5.5 for complete details.

## [0.5.0] - 2024-XX-XX (Phase 5 Complete)

### Added
- Quality gates system
- Multi-language quality enforcement (Python, JavaScript/TypeScript)
- Test execution requirements
- Linting and security scanning
- Configurable quality gates
- 12 comprehensive quality gate tests

### Changed
- Session completion now enforces quality standards
- Optional vs. required quality checks configurable

### Technical Details
- **Tests Added**: 12 tests
- **Tools Supported**: pytest, ruff, bandit, safety, eslint, prettier, npm audit
- **Configuration**: `.session/config.json`

### Reference
See ROADMAP.md Phase 5 for complete details.

## [0.4.0] - 2024-XX-XX (Phase 4 Complete)

### Added
- Learning capture and curation system
- Automatic learning categorization
- Tag-based learning organization
- Jaccard similarity for duplicate detection
- Search and browse functionality
- 12 learning system tests

### Changed
- Sessions now include learning capture
- Auto-curation every 5 sessions (configurable)

### Technical Details
- **Tests Added**: 12 tests
- **Categories**: architecture, testing, workflow, tooling, documentation
- **Storage**: `.session/learnings.json`

### Reference
See ROADMAP.md Phase 4 for complete details.

## [0.3.0] - 2024-XX-XX (Phase 3 Complete)

### Added
- Work item dependency graph visualization
- DOT and SVG format support
- Critical path analysis
- Bottleneck detection
- Dependency statistics
- 11 visualization tests

### Changed
- Work items now support dependency tracking
- Enhanced dependency validation

### Technical Details
- **Tests Added**: 11 tests
- **Formats**: DOT, SVG (requires graphviz)
- **Features**: Critical path, bottleneck detection, filtering

### Reference
See ROADMAP.md Phase 3 for complete details.

## [0.2.0] - 2024-XX-XX (Phase 2 Complete)

### Added
- Work item management system
- 6 work item types (feature, bug, improvement, research, documentation, deployment)
- CRUD operations for work items
- Status tracking (backlog, in_progress, completed, blocked)
- Priority levels (critical, high, medium, low)
- Milestone organization
- 9 work item tests

### Changed
- Sessions now include work item tracking
- Work item state persisted in `.session/work_items.json`

### Technical Details
- **Tests Added**: 9 tests
- **Storage**: JSON-based work item tracking
- **CLI Commands**: work-new, work-list, work-show, work-update

### Reference
See ROADMAP.md Phase 2 for complete details.

## [0.1.0] - 2024-XX-XX (Phase 1 Complete)

### Added
- Core session management framework
- Session initialization (`/init`)
- Session start (`/start`)
- Session completion (`/end`)
- Status tracking (`/status`)
- Git integration
- Environment validation
- 6 core tests

### Technical Details
- **Tests Added**: 6 tests
- **Infrastructure**: `.session/` directory structure
- **Configuration**: JSON-based session state

### Reference
See ROADMAP.md Phase 1 for complete details.

## [0.0.0] - Initial Concept

### Added
- Project concept and methodology
- Session-driven development framework design
- AI-augmented workflow principles

---

## Version Numbering

Versions follow semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

Phases map to versions:
- Phase 1 = v0.1.0
- Phase 2 = v0.2.0
- Phase 5.7 = v0.5.7
- Future v1.0.0 = Production-ready release

## Links

- [Roadmap](./ROADMAP.md) - Detailed development history
- [Contributing](./CONTRIBUTING.md) - How to contribute
- [Documentation](./docs/) - Full documentation
```

**Step 3: Add actual completion dates**

```bash
# Review git history for completion dates
git log --oneline --grep="Phase 5.7" | head -1
# Use commit dates to fill in YYYY-MM-DD for each version
```

**Step 4: Update README.md to link to CHANGELOG**

Add to `/Users/ankushdixit/Projects/sdd/README.md` (in appropriate section):

```markdown
## Release History

See [CHANGELOG.md](./CHANGELOG.md) for detailed release notes and version history.

Current version: **0.5.7** (Phase 5.7 Complete - Spec-first Architecture)
```

**Step 5: Link ROADMAP.md to CHANGELOG**

Add to top of `/Users/ankushdixit/Projects/sdd/ROADMAP.md`:

```markdown
> **Note**: For user-friendly release notes, see [CHANGELOG.md](./CHANGELOG.md). This roadmap contains detailed technical implementation history.
```

#### Success Criteria
- [ ] CHANGELOG.md created following Keep a Changelog format
- [ ] All phases documented as versions
- [ ] Completion dates added (from git history)
- [ ] README.md links to changelog
- [ ] ROADMAP.md references changelog

#### Git Workflow
```bash
git checkout main
git pull origin main
git checkout -b feature/add-changelog

git add CHANGELOG.md README.md ROADMAP.md
git commit -m "Add CHANGELOG.md with complete version history

- Create CHANGELOG.md following Keep a Changelog format
- Document all phases (0.1.0 through 0.5.7)
- Add completion dates from git history
- Link from README.md and ROADMAP.md
- Follow semantic versioning

Addresses audit recommendation: Medium Priority #5"

git push -u origin feature/add-changelog
gh pr create # ...
```

---

### Branch 6: `feature/package-refactor`

**Priority**: MEDIUM
**Estimated Effort**: 8-12 hours
**Risk**: HIGH (major refactoring)
**Dependencies**: Branch 1 (requirements.txt strongly recommended first)

#### Objective
Create proper Python package structure with `__init__.py` files and `setup.py`/`pyproject.toml`, enabling `pip install` and removing sys.path manipulation from 36 files.

#### Current State
- 36 files manually manipulate sys.path
- No proper Python package structure
- Cannot `pip install -e .`
- Not standard Python packaging

#### ⚠️ Warning
This is a **major refactoring** that touches many files. Recommend:
1. Ensure Branch 1 (requirements.txt) merged first
2. Ensure all tests passing before starting
3. Test incrementally during refactoring
4. Consider breaking into sub-branches if needed

#### Implementation Steps

**Step 1: Understand current import patterns**

```bash
# Find all sys.path manipulations
grep -rn "sys.path.insert" scripts/ .claude/commands/

# Find all current imports
grep -rn "^from scripts\." scripts/ .claude/commands/ tests/

# Map dependencies between modules
# (This helps understand what imports what)
```

**Step 2: Create package structure**

Target structure:
```
sdd/
├── pyproject.toml          # NEW - Package metadata
├── setup.py               # NEW - Setup script (optional, for compatibility)
├── sdd/                   # NEW - Package directory
│   ├── __init__.py        # NEW - Package init
│   ├── cli.py             # RENAMED from sdd_cli.py
│   ├── scripts/
│   │   ├── __init__.py    # NEW
│   │   ├── work_item_manager.py
│   │   ├── quality_gates.py
│   │   └── ... (all existing scripts)
│   └── commands/          # RENAMED from .claude/commands
│       ├── __init__.py    # NEW
│       └── ... (all slash command implementations)
├── tests/                 # KEEP - Tests outside package
│   ├── __init__.py        # NEW
│   └── ... (all existing tests)
└── templates/             # KEEP - Templates outside package
    └── ...
```

**Step 3: Create pyproject.toml**

Location: `/Users/ankushdixit/Projects/sdd/pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "sdd"
version = "0.5.7"
description = "Session-Driven Development - AI-augmented development workflow framework"
readme = "README.md"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
maintainers = [
    {name = "Your Name", email = "your.email@example.com"}
]
keywords = ["development", "workflow", "ai", "session-driven", "productivity"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Software Development :: Quality Assurance",
]
requires-python = ">=3.9"
dependencies = []  # Core has no dependencies (uses stdlib only)

[project.optional-dependencies]
test = [
    "pytest==7.4.3",
    "pytest-cov==4.1.0",
]
quality = [
    "ruff==0.1.6",
    "bandit==1.7.5",
    "safety==2.3.5",
]
viz = [
    "graphviz==0.20.1",
]
dev = [
    "sdd[test,quality,viz]",
    "ipython==8.17.2",
]

[project.urls]
Homepage = "https://github.com/yourusername/sdd"
Documentation = "https://github.com/yourusername/sdd/blob/main/README.md"
Repository = "https://github.com/yourusername/sdd"
Issues = "https://github.com/yourusername/sdd/issues"
Changelog = "https://github.com/yourusername/sdd/blob/main/CHANGELOG.md"

[project.scripts]
sdd = "sdd.cli:main"

[tool.setuptools]
packages = ["sdd", "sdd.scripts", "sdd.commands"]

[tool.setuptools.package-data]
sdd = ["py.typed"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = "-v --tb=short"

[tool.ruff]
line-length = 100
target-version = "py39"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]
ignore = ["E501"]  # Line too long (handled by formatter)

[tool.coverage.run]
source = ["sdd"]
omit = ["tests/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
```

**Step 4: Create setup.py (optional, for older pip versions)**

Location: `/Users/ankushdixit/Projects/sdd/setup.py`

```python
"""Setup script for backward compatibility with older pip versions."""
from setuptools import setup

# All configuration in pyproject.toml
setup()
```

**Step 5: Create package structure**

```bash
cd /Users/ankushdixit/Projects/sdd

# Create sdd package directory
mkdir -p sdd/scripts sdd/commands

# Move sdd_cli.py to sdd/cli.py
git mv sdd_cli.py sdd/cli.py

# Move all scripts
git mv scripts/*.py sdd/scripts/

# Create __init__.py files
touch sdd/__init__.py
touch sdd/scripts/__init__.py
touch sdd/commands/__init__.py
touch tests/__init__.py
```

**Step 6: Create sdd/__init__.py**

Location: `/Users/ankushdixit/Projects/sdd/sdd/__init__.py`

```python
"""
SDD (Session-Driven Development)

AI-augmented development workflow framework for systematic,
high-quality software development.
"""

__version__ = "0.5.7"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from sdd.scripts.work_item_manager import WorkItemManager
from sdd.scripts.session_manager import SessionManager
from sdd.scripts.quality_gates import QualityGates

__all__ = [
    "WorkItemManager",
    "SessionManager",
    "QualityGates",
    "__version__",
]
```

**Step 7: Update imports in all files**

**Pattern for scripts/:**

OLD:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.file_ops import load_json
from scripts.work_item_manager import WorkItemManager
```

NEW:
```python
from sdd.scripts.file_ops import load_json
from sdd.scripts.work_item_manager import WorkItemManager
```

**Pattern for tests/:**

OLD:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.work_item_manager import WorkItemManager
```

NEW:
```python
from sdd.scripts.work_item_manager import WorkItemManager
```

**Files to update** (36 files based on audit):
- All files in `sdd/scripts/` (20 files)
- All test files (multiple files across phases)
- Slash command implementations if they import scripts

**Step 8: Update sdd/cli.py**

Update COMMANDS routing table to use new import paths:

OLD:
```python
COMMANDS = {
    "start": ("scripts.session_start", "SessionStart", ...),
}
```

NEW:
```python
COMMANDS = {
    "start": ("sdd.scripts.session_start", "SessionStart", ...),
}
```

**Step 9: Update .gitignore**

Add to `/Users/ankushdixit/Projects/sdd/.gitignore`:

```
# Package build artifacts
build/
dist/
*.egg-info/
*.egg

# Compiled Python
__pycache__/
*.py[cod]
*$py.class
*.so
```

**Step 10: Test installation**

```bash
# Create clean virtual environment
cd /tmp
python3 -m venv test_sdd_package
source test_sdd_package/bin/activate

# Install in editable mode
cd /Users/ankushdixit/Projects/sdd
pip install -e .

# Verify installation
which sdd
sdd --help

# Run tests
pip install -e ".[test]"
pytest tests/

# Cleanup
deactivate
```

**Step 11: Update documentation**

Update `/Users/ankushdixit/Projects/sdd/README.md`:

```markdown
## Installation

### Option 1: Install from source (editable)

```bash
git clone <repo-url>
cd sdd
pip install -e .

# With test dependencies
pip install -e ".[test]"

# With all optional dependencies
pip install -e ".[dev]"
```

### Option 2: Install from source (standard)

```bash
pip install git+https://github.com/yourusername/sdd.git
```

### Option 3: Install from PyPI (when published)

```bash
pip install sdd
```

## Usage

After installation, use the `sdd` command:

```bash
sdd --help
sdd status
sdd work-list
```
```

**Step 12: Test all workflows**

```bash
# Test each major workflow after refactoring
cd /Users/ankushdixit/Projects/sdd

# Initialize project
sdd init

# Create work item
sdd work-new

# List work items
sdd work-list

# Start session
sdd start

# Run quality gates
sdd validate

# etc.
```

#### Success Criteria
- [ ] pyproject.toml created with complete metadata
- [ ] Package structure created (sdd/, __init__.py files)
- [ ] All 36 files updated (sys.path removed, imports fixed)
- [ ] sdd/cli.py updated with new import paths
- [ ] Tests updated and passing
- [ ] `pip install -e .` works
- [ ] `sdd` command available after install
- [ ] All workflows tested and working
- [ ] Documentation updated

#### Git Workflow

**WARNING**: This creates many file moves. Ensure git tracks renames properly.

```bash
git checkout main
git pull origin main
git checkout -b feature/package-refactor

# Make changes incrementally, testing after each major step

# Commit 1: Create package structure
git add pyproject.toml setup.py sdd/ tests/__init__.py
git commit -m "Create Python package structure

- Add pyproject.toml with full metadata
- Add setup.py for compatibility
- Create sdd/ package directory with __init__.py
- Move sdd_cli.py to sdd/cli.py
- Move scripts/ to sdd/scripts/
- Add __init__.py to all package directories"

# Commit 2: Update imports
git add sdd/scripts/*.py sdd/cli.py tests/
git commit -m "Refactor imports to use package structure

- Remove sys.path manipulation from 36 files
- Update all imports to use 'sdd.scripts.*' pattern
- Update CLI routing table for new paths
- Update test imports"

# Commit 3: Update documentation
git add README.md .gitignore
git commit -m "Update documentation for package installation

- Update installation instructions
- Add PyPI preparation notes
- Update .gitignore for package artifacts"

git push -u origin feature/package-refactor
gh pr create --title "Refactor to proper Python package structure" \
  --body "..." # Detailed description
```

#### Rollback Plan

If this breaks too many things:
```bash
git checkout main
git branch -D feature/package-refactor
# Start over with smaller incremental steps
```

---

### Branch 7: `feature/add-config-validation`

**Priority**: MEDIUM
**Estimated Effort**: 3-4 hours
**Risk**: Low
**Dependencies**: None

#### Objective
Add JSON schema validation for `.session/config.json` to catch configuration errors early with helpful error messages.

#### Current State
- Config loaded without validation
- Typos in config cause silent failures or obscure errors
- No documentation of valid config structure

#### Implementation Steps

**Step 1: Create JSON schema**

Location: `/Users/ankushdixit/Projects/sdd/templates/config.schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://github.com/yourusername/sdd/schemas/config.json",
  "title": "SDD Configuration",
  "description": "Configuration for Session-Driven Development workflows",
  "type": "object",
  "properties": {
    "quality_gates": {
      "type": "object",
      "description": "Quality gate configuration",
      "properties": {
        "test": {
          "type": "object",
          "properties": {
            "required": {"type": "boolean"},
            "command": {"type": "string"},
            "timeout": {"type": "integer", "minimum": 1}
          },
          "required": ["required"]
        },
        "lint": {
          "type": "object",
          "properties": {
            "required": {"type": "boolean"},
            "command": {"type": "string"},
            "timeout": {"type": "integer", "minimum": 1}
          },
          "required": ["required"]
        },
        "security": {
          "type": "object",
          "properties": {
            "required": {"type": "boolean"},
            "severity": {
              "type": "string",
              "enum": ["critical", "high", "medium", "low"]
            },
            "timeout": {"type": "integer", "minimum": 1}
          },
          "required": ["required"]
        }
      }
    },
    "learning": {
      "type": "object",
      "description": "Learning system configuration",
      "properties": {
        "auto_curate_frequency": {
          "type": "integer",
          "minimum": 1,
          "description": "Auto-curate every N sessions"
        },
        "similarity_threshold": {
          "type": "number",
          "minimum": 0,
          "maximum": 1,
          "description": "Threshold for duplicate detection"
        }
      }
    },
    "session": {
      "type": "object",
      "description": "Session management configuration",
      "properties": {
        "auto_commit": {
          "type": "boolean",
          "description": "Automatically commit changes on session end"
        },
        "require_work_item": {
          "type": "boolean",
          "description": "Require work item for session start"
        }
      }
    }
  },
  "additionalProperties": true
}
```

**Step 2: Create validation module**

Location: `/Users/ankushdixit/Projects/sdd/scripts/config_validator.py`

```python
"""Configuration validation using JSON schema."""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


def validate_config(
    config_path: Path,
    schema_path: Path
) -> Tuple[bool, List[str]]:
    """
    Validate configuration against JSON schema.

    Args:
        config_path: Path to config.json
        schema_path: Path to config.schema.json

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    try:
        import jsonschema
    except ImportError:
        # If jsonschema not installed, skip validation
        return True, ["Warning: jsonschema not installed, skipping validation"]

    # Load config
    if not config_path.exists():
        return False, [f"Config file not found: {config_path}"]

    with open(config_path) as f:
        config = json.load(f)

    # Load schema
    if not schema_path.exists():
        return True, [f"Warning: Schema file not found: {schema_path}"]

    with open(schema_path) as f:
        schema = json.load(f)

    # Validate
    try:
        jsonschema.validate(instance=config, schema=schema)
        return True, []
    except jsonschema.ValidationError as e:
        error_msg = _format_validation_error(e)
        return False, [error_msg]
    except jsonschema.SchemaError as e:
        return False, [f"Invalid schema: {e.message}"]


def _format_validation_error(error: Any) -> str:
    """Format validation error for user-friendly display."""
    path = " -> ".join(str(p) for p in error.path) if error.path else "root"
    return f"Validation error at '{path}': {error.message}"


def load_and_validate_config(
    config_path: Path,
    schema_path: Path
) -> Dict[str, Any]:
    """
    Load and validate configuration.

    Args:
        config_path: Path to config.json
        schema_path: Path to config.schema.json

    Returns:
        Loaded configuration

    Raises:
        ValueError: If configuration is invalid
    """
    is_valid, errors = validate_config(config_path, schema_path)

    if not is_valid:
        error_msg = "Configuration validation failed:\n" + "\n".join(errors)
        raise ValueError(error_msg)

    # Load and return config
    with open(config_path) as f:
        return json.load(f)
```

**Step 3: Update quality_gates.py to use validation**

In `/Users/ankushdixit/Projects/sdd/scripts/quality_gates.py`, update `_load_config` method:

```python
from scripts.config_validator import load_and_validate_config

def _load_config(self, config_path: Path) -> dict:
    """Load quality gate configuration with validation."""
    if not config_path.exists():
        return self._default_config()

    schema_path = config_path.parent / "config.schema.json"

    try:
        config = load_and_validate_config(config_path, schema_path)
        return config.get("quality_gates", self._default_config())
    except ValueError as e:
        print(f"❌ {e}")
        print("Using default configuration")
        return self._default_config()
```

**Step 4: Update session initialization to include schema**

In `/Users/ankushdixit/Projects/sdd/scripts/session_init.py`, add schema file creation:

```python
# In session initialization, copy schema to .session/
def initialize_session(project_root: Path) -> None:
    """Initialize session with config schema."""
    session_dir = project_root / ".session"
    session_dir.mkdir(exist_ok=True)

    # Copy schema file
    schema_source = Path(__file__).parent.parent / ".session" / "config.schema.json"
    schema_dest = session_dir / "config.schema.json"

    if schema_source.exists() and not schema_dest.exists():
        shutil.copy(schema_source, schema_dest)

    # ... rest of initialization
```

**Step 5: Update requirements.txt**

Add to `/Users/ankushdixit/Projects/sdd/requirements.txt`:

```txt
# Configuration validation
jsonschema==4.20.0
```

**Step 6: Create documentation**

Location: `/Users/ankushdixit/Projects/sdd/docs/configuration.md`

```markdown
# SDD Configuration

SDD uses JSON-based configuration stored in `.session/config.json`.

## Configuration Schema

Configuration is validated against `.session/config.schema.json` to catch errors early.

### Example Configuration

```json
{
  "quality_gates": {
    "test": {
      "required": true,
      "command": "pytest tests/",
      "timeout": 300
    },
    "lint": {
      "required": false,
      "command": "ruff check .",
      "timeout": 60
    },
    "security": {
      "required": true,
      "severity": "high",
      "timeout": 120
    }
  },
  "learning": {
    "auto_curate_frequency": 5,
    "similarity_threshold": 0.7
  },
  "session": {
    "auto_commit": false,
    "require_work_item": true
  }
}
```

## Validation

Configuration is automatically validated when loaded. If validation fails:

1. Error messages show exactly what's wrong
2. System falls back to default configuration
3. Session continues (graceful degradation)

### Common Validation Errors

**Wrong type**:
```
Validation error at 'quality_gates -> test -> required': True is not of type 'string'
```
Fix: Change `"required": "true"` to `"required": true`

**Invalid value**:
```
Validation error at 'learning -> similarity_threshold': 1.5 is greater than the maximum of 1
```
Fix: Use value between 0 and 1

**Missing required field**:
```
Validation error at 'quality_gates -> test': 'required' is a required property
```
Fix: Add `"required": true` or `"required": false`

## Schema Reference

See `.session/config.schema.json` for complete schema documentation.
```

**Step 7: Add tests**

Create `/Users/ankushdixit/Projects/sdd/tests/test_config_validation.py`:

```python
"""Tests for configuration validation."""

import json
from pathlib import Path
import pytest
from scripts.config_validator import validate_config, load_and_validate_config


@pytest.fixture
def schema_path(tmp_path):
    """Create minimal schema for testing."""
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "test_field": {"type": "string"}
        },
        "required": ["test_field"]
    }
    path = tmp_path / "schema.json"
    path.write_text(json.dumps(schema))
    return path


def test_valid_config(tmp_path, schema_path):
    """Test validation of valid configuration."""
    config = {"test_field": "value"}
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))

    is_valid, errors = validate_config(config_path, schema_path)

    assert is_valid
    assert len(errors) == 0


def test_invalid_config_wrong_type(tmp_path, schema_path):
    """Test validation fails with wrong type."""
    config = {"test_field": 123}  # Should be string
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))

    is_valid, errors = validate_config(config_path, schema_path)

    assert not is_valid
    assert len(errors) > 0
    assert "test_field" in errors[0]


def test_invalid_config_missing_required(tmp_path, schema_path):
    """Test validation fails with missing required field."""
    config = {}  # Missing test_field
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))

    is_valid, errors = validate_config(config_path, schema_path)

    assert not is_valid
    assert len(errors) > 0


def test_load_and_validate_raises_on_invalid(tmp_path, schema_path):
    """Test load_and_validate_config raises ValueError on invalid config."""
    config = {"test_field": 123}
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))

    with pytest.raises(ValueError, match="Configuration validation failed"):
        load_and_validate_config(config_path, schema_path)
```

#### Success Criteria
- [ ] config.schema.json created with complete schema
- [ ] config_validator.py created with validation logic
- [ ] quality_gates.py updated to validate on load
- [ ] session_init.py updated to copy schema
- [ ] requirements.txt updated (jsonschema)
- [ ] Documentation created (docs/configuration.md)
- [ ] Tests created and passing
- [ ] Validation tested with invalid configs

#### Git Workflow

```bash
git checkout main
git pull origin main
git checkout -b feature/add-config-validation

git add templates/config.schema.json scripts/config_validator.py
git add scripts/quality_gates.py scripts/session_init.py
git add docs/configuration.md tests/test_config_validation.py
git add requirements.txt

git commit -m "Add JSON schema validation for configuration

- Create config.schema.json with complete schema
- Add config_validator.py for validation logic
- Update quality_gates.py to validate on load
- Update session_init.py to copy schema
- Add jsonschema to requirements.txt
- Create configuration documentation
- Add validation tests

Addresses audit recommendation: Medium Priority #7"

git push -u origin feature/add-config-validation
gh pr create # ...
```

---

## Implementation Order & Timeline

### Recommended Sequence

**Week 1: High Priority**
1. Branch 1: requirements.txt (2-3 hours) - Monday
2. Branch 2: CI/CD pipeline (3-4 hours) - Tuesday
3. Branch 3: Resolve TODOs (2-4 hours) - Wednesday

**Week 2: Medium Priority - Easy Wins**
4. Branch 5: CHANGELOG (2-3 hours) - Monday
5. Branch 7: Config validation (3-4 hours) - Tuesday

**Week 3: Medium Priority - Major Work**
6. Branch 4: Logging framework (6-8 hours) - Monday-Tuesday
7. Branch 6: Package refactor (8-12 hours) - Wednesday-Friday

### Time Estimates Summary

| Branch | Priority | Effort | Risk | Dependencies |
|--------|----------|--------|------|--------------|
| 1. requirements.txt | HIGH | 2-3h | Low | None |
| 2. CI/CD | HIGH | 3-4h | Low | Branch 1 |
| 3. Resolve TODOs | HIGH | 2-4h | Med | None |
| 4. Logging | MEDIUM | 6-8h | Med | None |
| 5. CHANGELOG | MEDIUM | 2-3h | Low | None |
| 6. Package refactor | MEDIUM | 8-12h | High | Branch 1 |
| 7. Config validation | MEDIUM | 3-4h | Low | None |
| **Total** | - | **28-38h** | - | - |

---

## Testing Strategy

### For Each Branch

1. **Before starting**:
   ```bash
   git checkout main
   git pull origin main
   pytest tests/  # Ensure all tests pass
   ```

2. **During development**:
   ```bash
   # Run tests frequently
   pytest tests/ -v

   # Run quality checks
   ruff check .
   bandit -r scripts/
   ```

3. **Before committing**:
   ```bash
   # Full test suite
   pytest tests/

   # Verify no regressions
   ./sdd_cli.py status
   ./sdd_cli.py work-list
   ```

4. **After PR merge**:
   ```bash
   git checkout main
   git pull origin main
   pytest tests/  # Verify integration
   ```

---

## Rollback Plans

### If Branch Breaks Things

1. **Identify issue**: Run tests, check logs
2. **Quick fix** (if possible): Fix in branch, force push
3. **Revert PR** (if complex):
   ```bash
   git revert <merge-commit>
   git push origin main
   ```
4. **Start over**: Delete branch, analyze failure, retry

### If Multiple Branches Conflict

1. **Pause merging**: Don't merge more branches
2. **Resolve conflicts**: Rebase or merge main into feature branches
3. **Re-test**: Ensure tests pass after resolution
4. **Resume**: Continue merging in order

---

## Success Metrics

### How to Know We're Done

**High Priority Complete** when:
- [ ] requirements.txt exists and works
- [ ] CI/CD runs on every PR
- [ ] No TODO/FIXME comments remain unaddressed
- [ ] All tests passing
- [ ] Documentation updated

**Medium Priority Complete** when:
- [ ] Logging framework in place (core modules)
- [ ] CHANGELOG.md published
- [ ] Package installable via `pip install -e .`
- [ ] Config validation working
- [ ] All tests passing
- [ ] Documentation updated

**Overall Complete** when:
- [ ] All 7 branches merged
- [ ] Comprehensive codebase audit score improves from 8.9/10 to 9.5+/10
- [ ] No regressions in functionality
- [ ] New session in a new project works end-to-end

---

## Notes for Implementation

### Context Management

- Each branch should be implemented in a **fresh Claude Code session**
- This document provides all necessary context
- Reference: "Audit Implementation Plan - Branch X"

### When Starting Each Branch

1. Read this document fully
2. Check dependencies (is Branch 1 merged?)
3. Review current state (`git status`, `git log`)
4. Run tests before starting
5. Follow steps systematically
6. Test incrementally
7. Document any deviations

### When Stuck

1. **Check audit report** - May have additional context
2. **Check ROADMAP.md** - May explain existing patterns
3. **Run tests** - Often reveal what's broken
4. **Git diff** - See what changed
5. **Rollback and retry** - Sometimes starting fresh helps

### Communication

If implementing with others:
- Update this document with actual completion dates
- Note any deviations from plan
- Document lessons learned
- Update CHANGELOG.md after each branch

---

## Appendix: File Locations Quick Reference

```
/Users/ankushdixit/Projects/sdd/
├── requirements.txt                    # Branch 1
├── .github/workflows/                  # Branch 2
│   ├── tests.yml
│   └── pre-commit.yml
├── CHANGELOG.md                        # Branch 5
├── pyproject.toml                      # Branch 6
├── setup.py                            # Branch 6
├── sdd/                                # Branch 6
│   ├── __init__.py
│   ├── cli.py
│   └── scripts/
│       ├── __init__.py
│       ├── logging_config.py           # Branch 4
│       ├── config_validator.py         # Branch 7
│       └── ...
├── .session/
│   └── config.schema.json              # Branch 7
├── docs/
│   ├── audit-implementation-plan.md    # THIS FILE
│   └── configuration.md                # Branch 7
└── tests/
    ├── __init__.py                     # Branch 6
    ├── test_logging.py                 # Branch 4
    └── test_config_validation.py       # Branch 7
```

---

## Document Maintenance

This document should be updated:
- ✅ After completing each branch (mark as done, add completion date)
- ✅ If deviating from plan (document changes)
- ✅ If discovering new issues (add to recommendations)
- ✅ After full implementation (add retrospective)

**Last Updated**: 2025-10-18 (Created)
**Status**: Planning Phase
**Branches Completed**: 0/7

---

**END OF IMPLEMENTATION PLAN**
