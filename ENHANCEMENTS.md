# SDD Workflow Enhancements

This document tracks identified workflow improvements to make SDD more user-friendly and automated.

## Status Legend
- 🔵 IDENTIFIED - Enhancement identified, not yet implemented
- 🟡 IN_PROGRESS - Currently being worked on
- ✅ IMPLEMENTED - Completed and merged

---

## Enhancement #1: Auto Git Initialization in `sdd init`

**Status:** ✅ IMPLEMENTED

### Problem
Users must manually run `git init` before running `sdd init`, which is an unnecessary friction point and easy to forget.

### Current Workflow
```bash
mkdir my-project && cd my-project
mkdir docs
# ... create docs files ...
git init              # ← Manual step required
sdd init
```

### Proposed Solution
Automatically detect and initialize git repository during `sdd init`:

```python
# In scripts/init_workflow.py

def check_or_init_git(project_root: Path) -> bool:
    """Check if git is initialized, if not initialize it."""
    git_dir = project_root / ".git"

    if git_dir.exists():
        print("✓ Git repository already initialized")
        return True

    try:
        # Initialize git
        subprocess.run(
            ["git", "init"],
            cwd=project_root,
            check=True,
            capture_output=True
        )
        print("✓ Initialized git repository")

        # Set default branch to main (modern convention)
        subprocess.run(
            ["git", "branch", "-m", "main"],
            cwd=project_root,
            check=True,
            capture_output=True
        )

        return True
    except Exception as e:
        print(f"⚠️  Failed to initialize git: {e}")
        return False
```

### Benefits
- Eliminates manual step from setup
- Follows modern git conventions (main branch)
- Gracefully handles already-initialized repos
- One less thing for users to remember

### Implementation Tasks
- [ ] Add `check_or_init_git()` function to `scripts/init_workflow.py`
- [ ] Call it early in the init process (before creating .session directory)
- [ ] Add test for already-initialized repos
- [ ] Add test for new repo initialization
- [ ] Update documentation to remove manual `git init` step

---

## Enhancement #2: CHANGELOG Update Workflow

**Status:** ✅ IMPLEMENTED

### Problem
Documentation quality gate fails if CHANGELOG isn't updated, but:
1. Users don't know they need to update it until `/sdd:end` fails
2. No guidance on what to add to CHANGELOG
3. Check is too strict (requires update in working directory vs. branch commits)

### Current Pain Point
```bash
# User runs sdd end
❌ Documentation: ✗ FAILED
  ✗ CHANGELOG updated

# User is confused - what should I update?
```

### Proposed Multi-Part Solution

#### Part A: Git Prepare-Commit-Msg Hook (Reminder)
Install during `sdd init` to remind users:

```bash
# .git/hooks/prepare-commit-msg
#!/bin/bash

COMMIT_MSG_FILE=$1
COMMIT_SOURCE=$2

# Only run for regular commits (not merges, amends, etc.)
if [ -z "$COMMIT_SOURCE" ]; then
    cat >> "$COMMIT_MSG_FILE" << 'EOF'

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# REMINDERS:
#
# 📝 CHANGELOG: Update CHANGELOG.md for notable changes
#    (features, fixes, breaking changes)
#
# 💡 LEARNINGS: Add insights that will be auto-extracted during /sdd:end
#    LEARNING: <your learning here>
#
# Examples:
#    LEARNING: JWT refresh tokens should expire faster than access tokens
#    LEARNING: Always use parameterized queries to prevent SQL injection
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF
fi
```

#### Part B: Smarter CHANGELOG Detection
Check for CHANGELOG updates in branch commits, not just working directory:

```python
# In scripts/quality_gates.py

def check_changelog_updated(self) -> tuple[bool, dict]:
    """Check if CHANGELOG was updated in the current branch."""
    try:
        # Get the base branch (usually main or master)
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            cwd=self.project_root
        )
        current_branch = result.stdout.strip()

        # Don't check if we're on main/master
        if current_branch in ["main", "master"]:
            return True, {"status": "skipped", "reason": "On main branch"}

        # Check if CHANGELOG.md was modified in any commit on this branch
        result = subprocess.run(
            ["git", "log", "--name-only", "--pretty=format:", "main..HEAD"],
            capture_output=True,
            text=True,
            cwd=self.project_root
        )

        if "CHANGELOG.md" in result.stdout:
            return True, {"status": "updated", "message": "CHANGELOG updated in branch"}
        else:
            return False, {
                "status": "not_updated",
                "message": "CHANGELOG not updated in branch",
                "help": [
                    "Update CHANGELOG.md with your changes:",
                    "",
                    "## [Unreleased]",
                    "### Added",
                    "- Your feature or change here",
                    "",
                    "Then commit: git add CHANGELOG.md && git commit"
                ]
            }
    except Exception as e:
        return True, {"status": "error", "reason": f"Could not check: {e}"}
```

#### Part C: Better Error Messages
When CHANGELOG check fails, provide actionable guidance:

```python
if not changelog_updated:
    print("\n📝 CHANGELOG Update Required")
    print("=" * 60)
    print("Add your changes to CHANGELOG.md:")
    print()
    print("## [Unreleased]")
    print("### Added")
    print("- Feature: User authentication with JWT")
    print("- Tests: Comprehensive auth endpoint tests")
    print()
    print("Then commit:")
    print("  git add CHANGELOG.md")
    print("  git commit -m 'docs: Update CHANGELOG'")
    print("=" * 60)
```

### Benefits
- Proactive reminders during normal workflow
- Clear guidance on what to update
- Less strict check (branch-level vs working directory)
- Better error messages with examples

### Implementation Tasks
- [ ] Create git hooks template in `templates/git-hooks/prepare-commit-msg`
- [ ] Install hook during `sdd init`
- [ ] Make hook executable (`chmod +x`)
- [ ] Update `check_changelog_updated()` to check branch commits
- [ ] Add helpful error messages with examples
- [ ] Test with branches that have/haven't updated CHANGELOG
- [ ] Update documentation with CHANGELOG best practices

---

## Enhancement #3: Pre-flight Commit Check in `/sdd:end`

**Status:** ✅ IMPLEMENTED

### Problem
Users run `/sdd:end` with uncommitted changes and get confusing error messages:
1. Error doesn't clearly state "you need to commit first"
2. No guidance on what to commit or how
3. Quality gate failure happens after running all checks (wastes time)

### Current Experience
```bash
sdd end
# ... runs all quality gates ...
❌ Documentation: ✗ FAILED
  ✗ CHANGELOG updated

# User is confused - they have uncommitted changes but error talks about CHANGELOG
```

### Proposed Solution

#### Early Pre-flight Check
Check for uncommitted changes BEFORE running quality gates:

```python
# In scripts/session_complete.py - add at the very start

def check_uncommitted_changes() -> bool:
    """Check for uncommitted changes and guide user to commit first."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )

        uncommitted = [line for line in result.stdout.split("\n") if line.strip()]

        # Filter out .session/tracking files (they're updated by sdd end)
        user_changes = [
            line for line in uncommitted
            if not line.strip().endswith(".session/tracking/")
        ]

        if not user_changes:
            return True  # All good

        # Display uncommitted changes
        print("\n" + "=" * 60)
        print("⚠️  UNCOMMITTED CHANGES DETECTED")
        print("=" * 60)
        print("\nYou have uncommitted changes:")
        print()

        for line in user_changes[:15]:  # Show first 15
            print(f"   {line}")

        if len(user_changes) > 15:
            print(f"   ... and {len(user_changes) - 15} more")

        print("\n" + "=" * 60)
        print("📋 REQUIRED STEPS BEFORE /sdd:end:")
        print("=" * 60)
        print()
        print("1. Review your changes:")
        print("   git status")
        print()
        print("2. Update CHANGELOG.md with session changes:")
        print("   ## [Unreleased]")
        print("   ### Added")
        print("   - Your feature or change")
        print()
        print("3. Commit everything:")
        print("   git add -A")
        print("   git commit -m 'Implement feature X")
        print()
        print("   LEARNING: Key insight from implementation")
        print()
        print("   🤖 Generated with [Claude Code](https://claude.com/claude-code)")
        print("   Co-Authored-By: Claude <noreply@anthropic.com>'")
        print()
        print("4. Then run:")
        print("   sdd end")
        print()
        print("=" * 60)

        # In interactive mode, allow override
        if sys.stdin.isatty():
            print()
            response = input("Continue anyway? (y/n): ")
            return response.lower() == 'y'
        else:
            print("\nNon-interactive mode: exiting")
            print("Please commit your changes and run 'sdd end' again.")
            return False

    except Exception as e:
        print(f"Warning: Could not check git status: {e}")
        return True  # Don't block on errors

# At the very start of main():
def main():
    print("Completing session...\n")

    # Pre-flight check - do this BEFORE quality gates
    if not check_uncommitted_changes():
        print("\n❌ Session completion aborted")
        print("Commit your changes and try again.\n")
        sys.exit(1)

    # Now run quality gates...
    print("Running comprehensive quality gates...\n")
    # ... rest of the function
```

### Benefits
- Fails fast - checks before running expensive quality gates
- Clear, actionable guidance with examples
- Shows exactly what files need to be committed
- Step-by-step instructions
- Still allows override in interactive mode for advanced users

### Implementation Tasks
- [ ] Add `check_uncommitted_changes()` function to `scripts/session_complete.py`
- [ ] Call it at the very start of `main()` before quality gates
- [ ] Filter out `.session/tracking/` files (updated by sdd end itself)
- [ ] Add clear, formatted error messages with step-by-step guidance
- [ ] Support interactive override (y/n prompt)
- [ ] Test with uncommitted changes
- [ ] Test with clean working directory
- [ ] Update `/sdd:end` command documentation

---

## Implementation Plan

### Phase 1: Quick Wins (Estimated: 1 session)
1. Enhancement #1: Git auto-init
2. Enhancement #3: Pre-flight commit check

### Phase 2: CHANGELOG Workflow (Estimated: 1-2 sessions)
1. Enhancement #2: Git hooks + smarter checking

### Testing Strategy
For each enhancement:
- Unit tests for new functions
- Integration test with full SDD workflow
- Test both interactive and non-interactive modes
- Verify error messages are clear and helpful

### Success Criteria
- Users can run `sdd init` without manual `git init`
- Users get clear guidance when `/sdd:end` fails
- CHANGELOG reminders appear during normal workflow
- Error messages provide actionable next steps
- No regressions in existing functionality

---

## Enhancement #4: Add OS-Specific Files to Initial .gitignore

**Status:** ✅ IMPLEMENTED

### Problem
OS-specific files like `.DS_Store` (macOS) are not included in the initial `.gitignore` created during `sdd init`. This leads to:
1. These files being accidentally committed during the first session
2. Users having to manually add them to `.gitignore` mid-session
3. Extra commits to remove them from tracking

### Current Experience
```bash
# During first session
git add -A
git commit -m "..."
# .DS_Store gets committed

# Later, user has to:
# 1. Add .DS_Store to .gitignore
# 2. git rm --cached .DS_Store
# 3. Make another commit
```

### Proposed Solution
Update the `.gitignore` template in `templates/gitignore_template.txt` to include common OS-specific files:

```gitignore
# SDD-related patterns
.session/briefings/
.session/history/
coverage/
node_modules/
dist/
venv/
.venv/
*.pyc
__pycache__/

# OS-specific files
.DS_Store           # macOS
.DS_Store?          # macOS
._*                 # macOS resource forks
.Spotlight-V100     # macOS
.Trashes            # macOS
Thumbs.db           # Windows
ehthumbs.db         # Windows
Desktop.ini         # Windows
$RECYCLE.BIN/       # Windows
*~                  # Linux backup files
```

### Benefits
- Cleaner git history from the start
- No accidental commits of OS files
- Follows industry best practices
- Works across all major operating systems
- One less thing for users to worry about

### Implementation Tasks
- [ ] Update `templates/gitignore_template.txt` with OS-specific patterns
- [ ] Add comments explaining each pattern group
- [ ] Test on macOS, Windows, and Linux
- [ ] Verify patterns are correct and comprehensive
- [ ] Update initialization tests

---

## Enhancement #5: Create Initial Commit on Main During sdd init

**Status:** ✅ IMPLEMENTED

### Problem
When `sdd init` creates a git repository, it doesn't create an initial commit on the main branch. This causes issues:
1. Documentation quality gate fails on first session (no main branch to compare against)
2. Users must manually create a main branch before `/sdd:end` works
3. Violates standard git workflow expectations

### Current Experience
```bash
sdd init
# Git initialized but no commits

sdd start work-item-1
# ... make changes ...

sdd end
# ❌ Documentation: FAILED - no main branch exists
# User has to manually: git branch main <commit-hash>
```

### Proposed Solution
After creating all initialization files, create an initial commit on the main branch:

```python
# In scripts/init_workflow.py

def create_initial_commit(project_root: Path):
    """Create initial commit after project initialization."""
    try:
        # Stage all initialized files
        subprocess.run(
            ["git", "add", "-A"],
            cwd=project_root,
            check=True,
            capture_output=True
        )

        # Create initial commit
        commit_message = """chore: Initialize project with Session-Driven Development

Project initialized with SDD framework including:
- Project structure and configuration files
- Quality gates and testing setup
- Session tracking infrastructure
- Documentation templates

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"""

        subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=project_root,
            check=True,
            capture_output=True
        )

        print("✓ Created initial commit on main branch")
        return True

    except Exception as e:
        print(f"⚠️  Failed to create initial commit: {e}")
        print("You may need to commit manually before starting sessions")
        return False

# Call this at the end of init_project():
def init_project():
    # ... existing init code ...

    # Create initial commit (after all files are created)
    create_initial_commit(project_root)

    print("\n✅ SDD Initialized Successfully!")
```

### Benefits
- Establishes proper main branch baseline immediately
- Documentation quality gates work on first session
- Follows standard git workflow conventions
- No manual intervention needed
- Clean project history from the start

### Implementation Tasks
- [x] Add `create_initial_commit()` function to `scripts/init_project.py`
- [x] Call it after all initialization files are created
- [x] Include comprehensive commit message listing what was initialized
- [x] Handle errors gracefully (warn but don't fail init)
- [x] Update tests to verify initial commit exists
- [x] Test with both new repos and existing repos (handles existing repos by checking commit count)
- [x] Update documentation to reflect automatic initial commit

---

## Updated Implementation Plan

### Phase 1: Quick Wins (Estimated: 1 session)
1. Enhancement #1: Git auto-init ✅ IMPLEMENTED
2. Enhancement #3: Pre-flight commit check ✅ IMPLEMENTED
3. Enhancement #4: Add .DS_Store to .gitignore ✅ IMPLEMENTED
4. Enhancement #5: Create initial commit on main ✅ IMPLEMENTED

### Phase 2: CHANGELOG Workflow (Estimated: 1-2 sessions)
1. Enhancement #2: Git hooks + smarter checking ✅ IMPLEMENTED

### Testing Strategy
For each enhancement:
- Unit tests for new functions
- Integration test with full SDD workflow
- Test both interactive and non-interactive modes
- Verify error messages are clear and helpful
- **Test on macOS, Windows, and Linux** (for #4)
- **Test with new and existing git repos** (for #5)
