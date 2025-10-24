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

---

## Enhancement #6: Work Item Completion Status Control

**Status:** 🔵 IDENTIFIED

**Discovered:** 2025-10-23 (During Session 3 - Bug #20 implementation)

### Problem

The current workflow has two major issues with work item completion status:

1. **No prompt when ending session**: `/sdd:end` appears to default the work item status to "completed" without asking the user. This is problematic because:
   - Work items may span multiple sessions (not complete in one session)
   - Users have no explicit control over the completion status
   - If the work isn't done, the status is incorrectly set to completed

2. **No mid-session completion**: Users cannot mark a work item as complete during a session and immediately pick up the next work item without ending the session first. Current workflow:
   ```bash
   /start work_item_1       # Start work
   # ... work and complete work_item_1 ...
   /end                     # Must end session
   /start                   # Start new session for work_item_2
   ```

### Current Behavior

**When running `/sdd:end`:**
- Session ends
- Work item status is set (appears to default to "completed")
- No prompt asking: "Is this work item complete?"
- User has no explicit control

**Mid-session completion:**
- Not possible to mark work item as done and pick next one
- Must end session, then start new session
- Creates unnecessary session churn for small work items

### Expected Behavior

#### Part 1: Prompt for Work Item Completion Status

When running `/sdd:end`, ask the user:

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

#### Part 2: Mid-Session Work Item Completion

Add new command: `/work-complete` (or similar)

```bash
$ /work-complete

✓ Marked "Learning Curator Bug Fix" as completed

Starting next work item...

# Briefing for next work item
...
```

**Behavior:**
1. Runs quality gates for current work item
2. If gates pass, marks work item as completed
3. Automatically calls `get_next_work_item()` to find next work
4. Generates briefing for next work item
5. Updates session tracking to new work item
6. Continues same session (no session end/start churn)

**Alternative: Allow `/start` during active session**

```bash
$ /start work_item_2

⚠️  Warning: Work item "bug_fix_1" is currently in-progress.

Options:
1. Complete current work and start new work item
2. Abandon current work (mark incomplete) and start new work item
3. Cancel

Choice [1]: _
```

### Root Cause

**Part 1: No completion prompt**
- `scripts/session_complete.py` doesn't prompt for work item status
- Defaults to marking work item as complete (or leaves it in-progress?)
- User intent is not captured

**Part 2: No mid-session completion**
- Session-driven workflow assumes one session = one work item
- No command exists to complete work item without ending session
- Workflow inefficiency for small/quick work items

### Impact

**Part 1:**
- **User Confusion**: Status updates happen implicitly
- **Data Quality**: Work item status may be incorrect (marked complete when incomplete)
- **Multi-session Work**: No clear way to keep work item in-progress across sessions
- **Workflow Control**: Users lack explicit control over completion status

**Part 2:**
- **Workflow Inefficiency**: Must end/start session for each work item
- **Session Churn**: Creates many small sessions instead of one productive session
- **Productivity**: Slows down momentum when tackling multiple small items

### Proposed Solution

#### Part 1: Add Completion Status Prompt to `/sdd:end`

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

#### Part 2: Add Mid-Session Completion Command

**Option A: New `/work-complete` command**

Create new slash command in `.claude/commands/work-complete.md`:

```markdown
# Work Complete

Mark the current work item as complete and start the next work item without ending the session.

Usage:
/work-complete

This command:
1. Validates current work meets quality gates
2. Marks current work item as completed
3. Finds and starts next available work item
4. Continues in same session (no session restart)

Use this when you've completed a work item mid-session and want to immediately start the next one.
```

**Implementation:** `scripts/work_complete.py`

```python
def main():
    # 1. Load current work item
    # 2. Run quality gates
    # 3. If passed, mark work item as completed
    # 4. Call get_next_work_item()
    # 5. Generate briefing for next work item
    # 6. Update session tracking
    # 7. Display new briefing
```

**Option B: Enhance `/start` to handle active work items**

Modify `scripts/briefing_generator.py` to allow starting new work when work is in-progress:

```python
def main():
    # ... existing arg parsing ...

    # Check if a work item is currently in-progress
    current_work = find_in_progress_work_item()

    if current_work and args.work_item_id and current_work != args.work_item_id:
        # User wants to switch work items
        print(f"⚠️  Work item '{current_work}' is currently in-progress.\n")
        print("Options:")
        print("1. Complete current work and start new work item")
        print("2. Abandon current work (mark incomplete) and start new work item")
        print("3. Cancel")

        choice = input("\nChoice [1]: ").strip() or "1"

        if choice == "1":
            # Run quality gates for current work
            # If pass, mark as completed
            # Start new work item
        elif choice == "2":
            # Leave current work as in-progress
            # Start new work item
        elif choice == "3":
            sys.exit(0)
```

### Benefits

**Part 1:**
- Explicit user control over work item completion
- Prevents incorrect status updates
- Supports multi-session work items properly
- Clear workflow for incomplete work

**Part 2:**
- Eliminates session churn for small work items
- Maintains productivity momentum
- Reduces overhead of session end/start cycle
- Allows tackling multiple small items in one session

### Implementation Tasks

**Part 1: Completion Prompt**
- [ ] Add `prompt_work_item_completion()` to `scripts/session_complete.py`
- [ ] Add `--complete` and `--incomplete` flags to argparse
- [ ] Update work item status logic to use prompt result
- [ ] Handle non-interactive mode (default to incomplete for safety)
- [ ] Add tests for interactive prompt
- [ ] Add tests for flag handling
- [ ] Update documentation for `/end` command

**Part 2: Mid-Session Completion**
- [ ] Decide on approach (new command vs enhanced `/start`)
- [ ] Implement chosen approach
- [ ] Add quality gate validation
- [ ] Add work item status updates
- [ ] Add briefing generation for next work item
- [ ] Add tests for mid-session transitions
- [ ] Update documentation

### Files Affected

**Part 1:**
- `scripts/session_complete.py` - Add completion prompt and flags
- `.claude/commands/end.md` - Document new flags

**Part 2 (Option A - new command):**
- `scripts/work_complete.py` - New script for mid-session completion
- `.claude/commands/work-complete.md` - New command documentation

**Part 2 (Option B - enhanced start):**
- `scripts/briefing_generator.py` - Add work item switching logic
- `.claude/commands/start.md` - Document work item switching

### Related Issues

- Related to Bug #21: `/start` command ignores work item ID argument
- Related to Bug #22: Git branch status not finalized when switching work items
- All three issues involve improving work item lifecycle management

### Priority

**Part 1:** High - Core workflow issue affecting data quality
**Part 2:** Medium - Nice to have for workflow efficiency

---

## Enhancement #7: Phase 1 - Documentation Reorganization & Project Files

**Status:** 🔵 IDENTIFIED

**Discovered:** 2025-10-24 (Project structure review)

### Problem

The project root directory is cluttered with too many markdown files (10+ files), making it harder to navigate and understand the project structure. Additionally, several standard project convenience files are missing:

**Current root directory issues:**
- 10+ markdown files in root (README, CHANGELOG, ROADMAP, BUGS, ENHANCEMENTS, NOTES, SECURITY, CONTRIBUTING, LICENSE)
- Documentation scattered between root and docs/ directory
- No clear organization or categorization
- Missing developer convenience files (.editorconfig, Makefile)
- No high-level architecture documentation
- docs/ directory has flat structure (no logical grouping)

**Impact:**
- Harder for new contributors to find relevant documentation
- Cluttered appearance reduces professionalism
- Missing convenience files slows down common development tasks
- No clear documentation hierarchy

### Current State

```
sdd/
├── README.md
├── CHANGELOG.md
├── ROADMAP.md              ← Should be in docs/
├── BUGS.md                 ← Should be in docs/
├── ENHANCEMENTS.md         ← Should be in docs/
├── NOTES.md                ← Should be in docs/
├── SECURITY.md             ← Should be in docs/
├── CONTRIBUTING.md
├── LICENSE
├── docs/
│   ├── session-driven-development.md
│   ├── ai-augmented-solo-framework.md
│   ├── implementation-insights.md
│   ├── writing-specs.md
│   ├── configuration.md
│   ├── troubleshooting.md
│   ├── learning-system.md
│   ├── spec-template-structure.md
│   └── commands/           ← Only organized subdirectory
```

Missing files:
- No .editorconfig (editor consistency)
- No Makefile (common development tasks)
- No docs/ARCHITECTURE.md (high-level overview)
- No docs/README.md (documentation index)

### Proposed Solution

#### 1. Reorganize Documentation Structure

Create logical subdirectories in docs/:

```
docs/
├── README.md                    # NEW: Documentation index
├── ARCHITECTURE.md              # NEW: High-level architecture overview
├── SECURITY.md                  # MOVED from root
├── project/                     # NEW: Project management docs
│   ├── ROADMAP.md              # MOVED from root
│   ├── BUGS.md                 # MOVED from root
│   └── ENHANCEMENTS.md         # MOVED from root
├── development/                 # NEW: Development notes
│   └── NOTES.md                # MOVED from root
├── guides/                      # NEW: User guides
│   ├── getting-started.md      # NEW: Extract from README
│   ├── writing-specs.md        # MOVED from docs/
│   ├── configuration.md        # MOVED from docs/
│   └── troubleshooting.md      # MOVED from docs/
├── architecture/                # NEW: Architecture docs
│   ├── session-driven-development.md   # MOVED from docs/
│   ├── ai-augmented-solo-framework.md  # MOVED from docs/
│   └── implementation-insights.md       # MOVED from docs/
├── reference/                   # NEW: Reference documentation
│   ├── learning-system.md      # MOVED from docs/
│   └── spec-template-structure.md  # MOVED from docs/
└── commands/                    # KEEP: Command documentation
```

#### 2. Add Missing Project Files

**Create .editorconfig:**
```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.{py,md,json,yaml,yml}]
indent_style = space
indent_size = 4

[*.{json,yaml,yml}]
indent_size = 2

[Makefile]
indent_style = tab
```

**Create Makefile:**
```makefile
.PHONY: help install test lint format clean build

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

install:  ## Install package in development mode
	pip install -e .

install-dev:  ## Install with development dependencies
	pip install -e ".[dev]"

test:  ## Run all tests
	pytest tests/ -v

test-coverage:  ## Run tests with coverage report
	pytest tests/ --cov=scripts --cov-report=html --cov-report=term

lint:  ## Run code linter
	ruff check scripts/ tests/

format:  ## Format code automatically
	ruff format scripts/ tests/

clean:  ## Clean build artifacts and cache files
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	rm -rf .pytest_cache/ .ruff_cache/ htmlcov/

build:  ## Build package distribution
	python -m build
```

**Create docs/ARCHITECTURE.md:**
High-level system architecture overview with component diagrams, data flow, and design principles.

**Create docs/README.md:**
Documentation index with organized links to all documentation sections.

#### 3. Update All References

Files with references that need updating:
- **README.md**: Update links to ROADMAP.md, SECURITY.md, and all docs/ links
- **CHANGELOG.md**: Update references to ROADMAP.md
- **CONTRIBUTING.md**: Update all docs/ references to new structure
- **Other markdown files**: Check for cross-references

#### 4. Improve .gitignore

Verify all runtime artifacts are properly excluded:
```gitignore
# Python
*.pyc
__pycache__/
*.egg-info/
dist/
build/

# Testing
.pytest_cache/
.ruff_cache/
.coverage
htmlcov/

# OS
.DS_Store
Thumbs.db

# Virtual environments
venv/
.venv/
```

### Benefits

- ✅ **Cleaner root directory** - Reduces from 10 files to 4 essential files (README, CHANGELOG, CONTRIBUTING, LICENSE)
- ✅ **Better discoverability** - Logical grouping makes docs easier to find
- ✅ **Professional appearance** - Follows industry best practices
- ✅ **Developer convenience** - Makefile provides quick access to common tasks
- ✅ **Editor consistency** - .editorconfig ensures consistent formatting across team
- ✅ **Documentation hierarchy** - Clear organization from getting started to advanced topics
- ✅ **Zero code changes** - No risk of breaking existing functionality
- ✅ **GitHub compatibility** - SECURITY.md works from docs/ directory

### Implementation Tasks

**File Moves:**
- [ ] Create docs/ subdirectories (project/, development/, guides/, architecture/, reference/)
- [ ] Move ROADMAP.md → docs/project/ROADMAP.md
- [ ] Move BUGS.md → docs/project/BUGS.md
- [ ] Move ENHANCEMENTS.md → docs/project/ENHANCEMENTS.md
- [ ] Move NOTES.md → docs/development/NOTES.md
- [ ] Move SECURITY.md → docs/SECURITY.md
- [ ] Move writing-specs.md → docs/guides/writing-specs.md
- [ ] Move configuration.md → docs/guides/configuration.md
- [ ] Move troubleshooting.md → docs/guides/troubleshooting.md
- [ ] Move session-driven-development.md → docs/architecture/session-driven-development.md
- [ ] Move ai-augmented-solo-framework.md → docs/architecture/ai-augmented-solo-framework.md
- [ ] Move implementation-insights.md → docs/architecture/implementation-insights.md
- [ ] Move learning-system.md → docs/reference/learning-system.md
- [ ] Move spec-template-structure.md → docs/reference/spec-template-structure.md

**New Files:**
- [ ] Create .editorconfig with standard settings
- [ ] Create Makefile with common development tasks
- [ ] Create docs/ARCHITECTURE.md with high-level overview
- [ ] Create docs/README.md as documentation index
- [ ] Create docs/guides/getting-started.md (extract from README if needed)

**Reference Updates:**
- [ ] Update README.md - Fix all docs/ links to new structure
- [ ] Update README.md - Fix ROADMAP.md and SECURITY.md links
- [ ] Update CHANGELOG.md - Fix ROADMAP.md references
- [ ] Update CONTRIBUTING.md - Fix all docs/ references
- [ ] Search all .md files for broken links and update

**Validation:**
- [ ] Run `pytest tests/` to ensure nothing broke
- [ ] Check all markdown links work (use link checker or manual verification)
- [ ] Verify GitHub can find SECURITY.md (GitHub checks docs/ automatically)
- [ ] Test Makefile targets (make help, make test, make lint, etc.)
- [ ] Verify .editorconfig is recognized by common editors

**.gitignore Improvements:**
- [ ] Review .gitignore for any missing patterns
- [ ] Add any OS-specific files not already covered
- [ ] Ensure all build/test artifacts are excluded

### Files Affected

**Moved:**
- ROADMAP.md
- BUGS.md
- ENHANCEMENTS.md
- NOTES.md
- SECURITY.md
- docs/writing-specs.md
- docs/configuration.md
- docs/troubleshooting.md
- docs/session-driven-development.md
- docs/ai-augmented-solo-framework.md
- docs/implementation-insights.md
- docs/learning-system.md
- docs/spec-template-structure.md

**Created:**
- .editorconfig
- Makefile
- docs/README.md
- docs/ARCHITECTURE.md
- docs/guides/getting-started.md (optional)

**Modified (reference updates):**
- README.md
- CHANGELOG.md
- CONTRIBUTING.md
- Potentially other .md files with cross-references

### Estimated Effort

**Time:** 20-30 minutes

**Complexity:** Low - Simple file moves and additions, no code changes

**Risk:** Very low - No code changes, only documentation reorganization

### Dependencies

**None** - This enhancement is independent and can be implemented immediately.

**Enables:**
- Sets foundation for cleaner project structure
- Prepares for Phase 2 (test reorganization)
- Establishes documentation patterns for future additions

### Testing Strategy

1. **Before making changes:**
   - Run full test suite: `pytest tests/` (establish baseline)
   - Document current test count and status

2. **After making changes:**
   - Run full test suite again: `pytest tests/`
   - Verify same number of tests pass
   - Check no new failures introduced

3. **Documentation validation:**
   - Manually check key documentation links
   - Verify GitHub renders SECURITY.md properly
   - Test Makefile commands in clean environment

4. **Git validation:**
   - Ensure git history tracks file moves properly
   - Verify no files accidentally deleted
   - Check .gitignore excludes all runtime artifacts

---

## Enhancement #8: Phase 2 - Test Suite Reorganization

**Status:** 🔵 IDENTIFIED

**Discovered:** 2025-10-24 (Project structure review)

### Problem

The current test suite is organized by development phases (phase_1, phase_2, ..., phase_5_7), which made sense during incremental development but creates challenges for long-term maintenance:

**Current issues:**
- **Hard to navigate** - New contributors don't know which phase contains which functionality
- **No semantic organization** - Tests grouped by when they were written, not what they test
- **Doesn't match typical Python projects** - Most Python projects use unit/integration/e2e structure
- **Difficult to run specific test types** - Can't easily run "all unit tests" or "all integration tests"
- **Discovery problems** - Finding tests for a specific module requires searching multiple phase directories

**Impact:**
- **Onboarding friction** - New contributors struggle to find relevant tests
- **Maintenance difficulty** - Adding tests for existing modules means choosing arbitrary phase
- **Test organization entropy** - No clear guideline where new tests should go
- **Coverage analysis complexity** - Hard to identify coverage gaps by domain

### Current State

```
tests/
├── phase_1/
│   └── test_phase_1_complete.py          (6 tests - Init workflow)
├── phase_2/
│   └── test_phase_2_complete.py          (9 tests - Work items)
├── phase_3/
│   └── test_phase_3_complete.py          (11 tests - Dependency graph)
├── phase_4/
│   └── test_phase_4_complete.py          (12 tests - Learning system)
├── phase_5/
│   └── test_phase_5_complete.py          (12 tests - Quality gates)
├── phase_5_5/
│   ├── test_phase_5_5_1.py through 7.py  (178 tests - Integration testing)
├── phase_5_6/
│   ├── test_phase_5_6_1.py through 5.py  (65 tests - Deployment)
├── phase_5_7/
│   ├── test_phase_5_7_1.py through 6.py  (49 tests - Spec-first)
├── test_config_validation.py             (Orphaned in root)
├── test_gitignore_os_patterns.py         (Orphaned in root)
├── test_logging.py                       (Orphaned in root)
├── test_sdd_setup.py                     (Orphaned in root)
└── test_session_validate.py              (Orphaned in root)
```

**Total:** 392 tests across 24 files

### Proposed Solution

Reorganize tests by **domain and test type** instead of development phase:

```
tests/
├── conftest.py                           # NEW: Shared fixtures and test utilities
├── unit/                                 # NEW: Fast, isolated unit tests
│   ├── test_work_item_manager.py        # Work item CRUD operations
│   ├── test_learning_curator.py         # Learning categorization, deduplication
│   ├── test_dependency_graph.py         # Graph algorithms, critical path
│   ├── test_spec_parser.py              # Spec parsing and validation
│   ├── test_spec_validator.py           # Spec completeness checks
│   ├── test_quality_gates.py            # Individual gate logic
│   ├── test_git_integration.py          # Git operations
│   ├── test_config_validation.py        # Config schema validation
│   ├── test_logging.py                  # Logging configuration
│   └── test_file_ops.py                 # File operations utilities
├── integration/                          # NEW: Multi-component integration tests
│   ├── test_session_workflow.py         # start → work → end workflow
│   ├── test_quality_pipeline.py         # Full quality gate pipeline
│   ├── test_learning_extraction.py      # Learning extraction from commits/code
│   ├── test_work_item_lifecycle.py      # Work item creation → completion
│   ├── test_briefing_generation.py      # Briefing with all components
│   ├── test_deployment_workflow.py      # Deployment spec → execution
│   └── test_git_workflow.py             # Git integration end-to-end
├── e2e/                                  # NEW: Full end-to-end workflows
│   ├── test_init_to_complete.py         # sdd init → work → end (complete flow)
│   ├── test_multi_session_workflow.py   # Multiple sessions on same work item
│   └── test_feature_complete_workflow.py # Feature spec → implementation → completion
├── fixtures/                             # NEW: Test data and fixtures
│   ├── sample_work_items.json
│   ├── sample_learnings.json
│   ├── sample_specs/
│   └── mock_repos/
└── legacy/                               # Keep phase tests for reference/regression
    ├── phase_1/
    ├── phase_2/
    ├── phase_3/
    ├── phase_4/
    ├── phase_5/
    ├── phase_5_5/
    ├── phase_5_6/
    └── phase_5_7/
```

#### Migration Strategy

**Step 1: Create new structure**
- Create unit/, integration/, e2e/, fixtures/, legacy/ directories
- Move existing phase tests to legacy/ (preserve for regression)

**Step 2: Extract and reorganize tests**
For each domain (work_items, learning, quality_gates, etc.):
- Extract unit tests from phase tests
- Group by module under test
- Create integration tests for multi-component scenarios
- Create e2e tests for complete workflows

**Step 3: Create shared fixtures**
- Extract common setup code to conftest.py
- Create reusable fixtures for temporary directories, mock repos, sample data
- Reduce code duplication across tests

**Step 4: Update imports**
- Update test imports to match new structure
- Update pytest configuration in pyproject.toml
- Ensure test discovery still works

**Step 5: Validate and clean up**
- Run full test suite to ensure all tests still pass
- Verify test count matches (392 tests)
- Once validated, can optionally remove legacy/ tests (or keep for safety)

### Benefits

- ✅ **Better organization** - Tests grouped by what they test, not when written
- ✅ **Easier navigation** - Clear semantic structure (unit/integration/e2e)
- ✅ **Faster test execution** - Can run unit tests only for quick feedback
- ✅ **Better for contributors** - Industry-standard structure familiar to Python developers
- ✅ **Improved coverage analysis** - Easy to see coverage by domain
- ✅ **Clearer test purpose** - Test type (unit/integration/e2e) indicates scope
- ✅ **Reduced duplication** - Shared fixtures in conftest.py
- ✅ **Selective test runs** - `pytest tests/unit/` or `pytest tests/integration/`

### Implementation Tasks

**Directory Structure:**
- [ ] Create tests/unit/ directory
- [ ] Create tests/integration/ directory
- [ ] Create tests/e2e/ directory
- [ ] Create tests/fixtures/ directory
- [ ] Create tests/legacy/ directory
- [ ] Create tests/conftest.py with shared fixtures

**Move Phase Tests to Legacy:**
- [ ] Move tests/phase_1/ → tests/legacy/phase_1/
- [ ] Move tests/phase_2/ → tests/legacy/phase_2/
- [ ] Move tests/phase_3/ → tests/legacy/phase_3/
- [ ] Move tests/phase_4/ → tests/legacy/phase_4/
- [ ] Move tests/phase_5/ → tests/legacy/phase_5/
- [ ] Move tests/phase_5_5/ → tests/legacy/phase_5_5/
- [ ] Move tests/phase_5_6/ → tests/legacy/phase_5_6/
- [ ] Move tests/phase_5_7/ → tests/legacy/phase_5_7/

**Create Unit Tests (extract from phase tests):**
- [ ] Create test_work_item_manager.py (from phase_2, phase_5_7)
- [ ] Create test_learning_curator.py (from phase_4)
- [ ] Create test_dependency_graph.py (from phase_3)
- [ ] Create test_spec_parser.py (from phase_5_7)
- [ ] Create test_spec_validator.py (from phase_5_7)
- [ ] Create test_quality_gates.py (from phase_5)
- [ ] Create test_git_integration.py (from phase_1, phase_5)
- [ ] Move test_config_validation.py → tests/unit/
- [ ] Move test_logging.py → tests/unit/
- [ ] Create test_file_ops.py

**Create Integration Tests:**
- [ ] Create test_session_workflow.py (from phase_1 complete workflow tests)
- [ ] Create test_quality_pipeline.py (from phase_5, phase_5_5)
- [ ] Create test_learning_extraction.py (from phase_4)
- [ ] Create test_work_item_lifecycle.py (from phase_2, phase_5_7)
- [ ] Create test_briefing_generation.py (from phase_1, phase_5_7)
- [ ] Create test_deployment_workflow.py (from phase_5_6)
- [ ] Create test_git_workflow.py (from phase_1, phase_5)

**Create E2E Tests:**
- [ ] Create test_init_to_complete.py (full SDD workflow)
- [ ] Create test_multi_session_workflow.py (multiple sessions)
- [ ] Create test_feature_complete_workflow.py (from phase_5_7 complete tests)

**Create Shared Fixtures:**
- [ ] Extract common setup to conftest.py
- [ ] Create sample data fixtures (work_items, learnings, specs)
- [ ] Create mock repository fixtures
- [ ] Create temporary directory fixtures

**Update Configuration:**
- [ ] Update pyproject.toml [tool.pytest.ini_options]
- [ ] Update test discovery patterns
- [ ] Add test markers for unit/integration/e2e

**Validation:**
- [ ] Run `pytest tests/unit/` - verify all unit tests pass
- [ ] Run `pytest tests/integration/` - verify all integration tests pass
- [ ] Run `pytest tests/e2e/` - verify all e2e tests pass
- [ ] Run `pytest tests/` - verify total test count is 392
- [ ] Run `pytest tests/legacy/` - verify legacy tests still pass (regression check)
- [ ] Verify test coverage is maintained or improved

**Documentation:**
- [ ] Update CONTRIBUTING.md with new test structure
- [ ] Add test writing guidelines (where to put new tests)
- [ ] Update README.md test structure documentation

**Optional Cleanup:**
- [ ] After validation, decide whether to keep or remove legacy/ tests
- [ ] Document decision in NOTES.md or ARCHITECTURE.md

### Files Affected

**All test files** (24 files) will be moved or reorganized:
- tests/phase_*/test_*.py → tests/legacy/phase_*/
- New domain-based test files in unit/, integration/, e2e/

**Configuration files:**
- pyproject.toml (pytest configuration)
- CONTRIBUTING.md (test guidelines)
- README.md (test documentation)

### Estimated Effort

**Time:** 2-4 hours (careful extraction and validation required)

**Complexity:** Medium - Requires careful test extraction and import updates

**Risk:** Low-Medium - All changes are test-only, no production code affected. Legacy tests provide safety net.

### Dependencies

**Depends on:** None - Can be done independently

**Enables:**
- Better test organization for future development
- Easier test maintenance and contribution
- Foundation for Phase 3 (when src/ layout is implemented, tests will already be organized properly)

### Testing Strategy

1. **Preserve legacy tests first** - Move all phase tests to legacy/ before any extraction
2. **Extract incrementally** - Do one domain at a time (work_items, then learning, etc.)
3. **Run tests after each extraction** - Ensure new tests pass and match coverage
4. **Keep running total** - Track test count to ensure all 392 tests are preserved
5. **Use legacy as regression check** - Keep legacy tests until new organization is proven stable

### Migration Script Approach

Consider creating a migration script to help with the reorganization:

```python
# scripts/migrate_tests.py

"""
Helper script to migrate tests from phase-based to domain-based structure.
Analyzes phase tests and suggests which domain tests they belong in.
"""

def analyze_test_file(file_path):
    """Analyze a test file and suggest target domain."""
    # Read file, analyze imports and test names
    # Suggest: unit/test_work_item_manager.py or integration/test_session_workflow.py
    pass

def extract_tests(source, target):
    """Extract specific tests from source file to target file."""
    pass

if __name__ == "__main__":
    # Analyze all phase tests
    # Generate migration plan
    # Optionally execute migration
    pass
```

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
├── tests/                          # UNCHANGED (or use tests/ at root)
├── docs/                           # UNCHANGED
├── .claude/                        # UNCHANGED (needs command path updates)
├── pyproject.toml                  # UPDATED
└── setup.py                        # UPDATED or removed
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
- [ ] Update or remove setup.py (pyproject.toml preferred)
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
- [ ] Verify all 392 tests pass
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
- setup.py (or removed)
- CONTRIBUTING.md
- README.md
- ROADMAP.md

**Removed:**
- scripts/ directory (after migration)
- sdd_cli.py (after migration)
- templates/ directory (after migration)

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
- [ ] Document current test count (392 tests)

During migration:
- [ ] Follow task list above sequentially
- [ ] Test after each major section
- [ ] Keep notes of any issues encountered

After migration:
- [ ] All tests pass: `pytest tests/` (392/392)
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
