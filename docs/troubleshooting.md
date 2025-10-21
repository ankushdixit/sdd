# Troubleshooting Guide

## Common Issues and Solutions

### Undoing a Failed `/sdd:start` Command

If you run `/sdd:start` and it fails (e.g., spec file not found, wrong work item), you can undo the changes by reverting the session state:

#### What `/sdd:start` Changes:

1. **Work Item Status** - Sets status to "in_progress" in `.session/tracking/work_items.json`
2. **Session Tracking** - Adds a session entry to the work item
3. **Git Branch** - Creates/checks out a feature branch
4. **Status File** - Creates/updates `.session/tracking/status_update.json`
5. **Briefing File** - Creates `.session/briefings/session_XXX_briefing.md`

#### Manual Undo Steps:

**Option 1: Quick Reset (Recommended)**

```bash
# 1. Switch back to main branch
git checkout main

# 2. Delete the feature branch (if it was created)
git branch -D session-XXX-US-X-X  # Replace with actual branch name

# 3. Edit .session/tracking/work_items.json
# Change the work item status back to "not_started"
# Remove the "sessions" array entry
# Update the "updated_at" timestamp

# 4. Delete the status file
rm .session/tracking/status_update.json

# 5. Delete the briefing file (optional, for cleanup)
rm .session/briefings/session_XXX_briefing.md
```

**Option 2: Using Git to Reset Work Items**

```bash
# If you have work_items.json committed, you can restore it
git checkout HEAD -- .session/tracking/work_items.json

# Then manually handle git branch and status file as above
```

#### Automated Undo Script (Future Enhancement)

A `/sdd:undo` or `/sdd:reset` command could be added to automate this process.

---

### Spec File Not Found in Briefing

**Symptom:** Running `/sdd:start` generates a briefing, but the work item specification section shows "Specification file not found"

**Cause:** The spec file path in `work_items.json` doesn't match the actual file location.

**Solution:**

1. Check your work item definition in `.session/tracking/work_items.json`:
   ```json
   "spec_file": ".session/specs/US-0-1-project-initialization.md"
   ```

2. Verify the file exists at that path:
   ```bash
   ls -la .session/specs/US-0-1-project-initialization.md
   ```

3. If the filename is different, either:
   - **Option A:** Rename the spec file to match the `spec_file` field
   - **Option B:** Update the `spec_file` field in work_items.json to match the actual filename

**Note:** As of version 0.5.9+, the briefing generator uses the `spec_file` field from work_items.json, so you have flexibility in naming your spec files.

---

### Work Item Already In Progress

**Symptom:** When running `/sdd:start`, you get a work item that's already marked "in_progress"

**Cause:** A previous session was started but not completed with `/sdd:end`

**Solution:**

**Option 1: Resume the Session**
```bash
# Continue working on the in-progress item
/sdd:start
# This will resume the existing work item
```

**Option 2: Force Reset**
```bash
# Manually edit .session/tracking/work_items.json
# Change the status from "in_progress" to "not_started"
# Then run /sdd:start again
```

**Option 3: Complete the Session**
```bash
# If you're actually done with the work
/sdd:end
# This will mark it complete and move to the next item
```

---

### No Available Work Items

**Symptom:** `/sdd:start` says "No available work items. All dependencies must be satisfied first."

**Cause:** All remaining work items have unsatisfied dependencies.

**Solution:**

1. Check work item dependencies:
   ```bash
   /sdd:work-list --status not_started
   ```

2. Look at the dependency graph:
   ```bash
   /sdd:work-graph --bottlenecks
   ```

3. Either:
   - Complete the blocking work items first
   - Remove/modify dependencies if they're incorrect
   - Create a new work item without dependencies

---

### Git Branch Already Exists

**Symptom:** `/sdd:start` fails because the git branch already exists

**Cause:** A previous session created the branch but wasn't cleaned up

**Solution:**

```bash
# Option 1: Resume on existing branch
git checkout session-XXX-US-X-X
/sdd:start

# Option 2: Delete and recreate
git checkout main
git branch -D session-XXX-US-X-X
/sdd:start

# Option 3: Rename the old branch for archival
git branch -m session-XXX-US-X-X session-XXX-US-X-X-old
/sdd:start
```

---

### Briefing Shows Wrong Work Item

**Symptom:** The briefing shows a different work item than you expected

**Cause:** The system automatically selects the next available work item based on:
1. In-progress items (resumes these first)
2. Not-started items with satisfied dependencies
3. Priority ordering (critical > high > medium > low)

**Solution:**

```bash
# Specify which work item you want to start
/sdd:start --item US-X-X

# Or check what the next item will be
/sdd:work-next
```

---

### Environment Validation Fails

**Symptom:** Briefing shows environment checks failing (Git not found, Python wrong version, etc.)

**Cause:** Required development tools aren't installed or configured

**Solution:**

1. **Install missing tools:**
   ```bash
   # Git
   brew install git  # macOS
   sudo apt install git  # Linux

   # Python (use appropriate version)
   brew install python@3.11  # macOS
   ```

2. **Check installations:**
   ```bash
   git --version
   python --version
   ```

3. **Update PATH if needed:**
   ```bash
   # Add to ~/.bashrc or ~/.zshrc
   export PATH="/usr/local/bin:$PATH"
   ```

---

### Next.js Initialization Conflicts with `.session/` Directory

**Symptom:** When trying to initialize a Next.js project with `create-next-app`, you get an error:
```
Error: The directory contains files that could conflict:
  .session/
Either try using a new directory name, or remove the files listed above.
```

**Cause:** The SDD framework creates a `.session/` directory for tracking work items, learnings, and session state. Tools like `create-next-app` detect this as a conflict because they expect an empty directory.

**Solutions:**

**Option 1: Initialize in Parent Directory (Recommended)**
```bash
# If you're in the SDD project directory, initialize Next.js in the current directory
# using the --force flag (use with caution)
npx create-next-app@latest . --typescript --tailwind --app --use-npm
# When prompted about conflicts, confirm to proceed
```

**Option 2: Manual Setup**
```bash
# Instead of using create-next-app, manually set up Next.js
npm install next@latest react@latest react-dom@latest
npm install --save-dev typescript @types/react @types/node
npm install --save-dev tailwindcss postcss autoprefixer

# Create necessary config files manually
npx tailwindcss init -p

# Create directory structure
mkdir -p app
```

**Option 3: Temporary Workaround**
```bash
# Temporarily rename .session directory
mv .session .session.tmp

# Run create-next-app
npx create-next-app@latest . --typescript --tailwind --app --use-npm

# Restore .session directory
mv .session.tmp .session
```

**Note:** The `.session/` directory is essential for SDD to function. Do not delete it or add it to `.gitignore` if you're using Session-Driven Development workflow.

---

### `work-update` Command Fails with EOFError

**Symptom:** Running `sdd work-update US-0-1 --status in_progress` fails with:
```
EOFError: EOF when reading a line
```

**Cause:** Prior to version 0.5.10, the `work-update` command always used interactive mode, even when flags were provided. This caused it to prompt for user input, which fails when Claude runs it non-interactively.

**Solution:**

**For SDD v0.5.10+:** This is fixed! The `work-update` command now supports both interactive and non-interactive modes:

```bash
# Non-interactive mode (with flags)
sdd work-update US-0-1 --status completed
sdd work-update US-0-1 --priority high
sdd work-update US-0-1 --milestone "MVP"
sdd work-update US-0-1 --add-dependency US-0-2
sdd work-update US-0-1 --remove-dependency US-0-3

# Interactive mode (no flags)
sdd work-update US-0-1
# Prompts: What would you like to update?
```

**For older versions:** Upgrade to the latest version or avoid using `work-update` in non-interactive contexts.

**Important for Claude Code Users:**
- The `/sdd:start` command automatically updates the work item status to `in_progress`
- You do NOT need to manually run `sdd work-update US-0-1 --status in_progress` after starting a session
- The briefing will show: `✓ Work item status updated: US-0-1 → in_progress`

---

## Getting Help

If you encounter issues not covered here:

1. Check the [Session-Driven Development docs](./session-driven-development.md)
2. Review the [Configuration guide](./configuration.md)
3. Open an issue on the [SDD GitHub repository](https://github.com/anthropics/sdd)
4. Check the command-specific docs in `docs/commands/`

---

## Debug Mode

For more verbose output during troubleshooting:

```bash
# Enable debug logging (if implemented)
export SDD_DEBUG=1

# Run commands
/sdd:start

# Check logs
tail -f .session/debug.log
```
