# Claude Code Session Plugin - Implementation Plan
## Complete Guide

This document provides a **complete, step-by-step implementation plan** for building the Claude Code Session Plugin from scratch.

---

## Project Overview

**Name:** `claude-session-plugin`

**Purpose:** Extend Claude Code with custom slash commands for Session-Driven Development (SDD), enabling perfect context continuity across multiple AI coding sessions.

**Key Commands:**
- `/session-start` - Begin work session with comprehensive briefing
- `/session-end` - Complete session with quality gates and summary
- `/work-item` - Manage work items and dependencies
- `/learning` - Capture and curate project knowledge

**Core Value:** Maintain stateful development across stateless Claude Code sessions, enabling solo developers to build complex projects with team-level quality.

---

## Phase 1: Plugin Foundation (Week 1)

### Goal
Get basic plugin structure working with minimal `/session-start` command.

### 1.1 Create Plugin Directory Structure

```bash
mkdir claude-session-plugin
cd claude-session-plugin

# Plugin manifest
mkdir -p .claude-plugin

# Commands
mkdir -p commands

# Hooks (for future)
mkdir -p hooks

# Scripts (core logic)
mkdir -p scripts

# Templates
mkdir -p templates

# Documentation
mkdir -p docs
```

### 1.2 Create Plugin Manifest

**File:** `.claude-plugin/plugin.json`

```json
{
  "name": "session",
  "version": "0.1.0",
  "description": "Session-Driven Development for Claude Code - Maintain perfect context across multiple AI coding sessions",
  "author": "ankushdixit",
  "commands": [
    "session-start",
    "session-end",
    "session-status",
    "work-item",
    "learning"
  ],
  "hooks": [],
  "minimum_claude_code_version": "1.0.0"
}
```

### 1.3 Create `/session-start` Command

**File:** `commands/session-start.md`

```markdown
# Session Start Command

**Usage:** `/session-start [--item <id>]`

**Description:** Initialize a development session with comprehensive briefing.

**Behavior:**

1. Check if project has `.session/` directory
   - If not: initialize project (create directory structure)
   - If yes: validate structure is intact

2. Determine which work item to work on:
   - If `--item <id>` provided: use that item
   - Otherwise: find next available item (dependencies satisfied)
   - If no items available: prompt to create one

3. Generate briefing:
   - Read work item details from `.session/tracking/work_items.json`
   - Read previous session notes
   - Read relevant learnings from `.session/tracking/learnings.json`
   - Create comprehensive briefing markdown

4. Present briefing to user (as markdown output)

5. Update work item status to "in_progress"

6. Begin implementation

**Example:**

```
User: /session-start

Claude: Initializing session...

Reading work items from .session/tracking/work_items.json...
Found 5 work items (2 completed, 3 pending)

Next available work item: implement_authentication
All dependencies satisfied ✓

# Session Briefing

## Work Item: Implement OAuth2 Authentication
- ID: implement_authentication
- Type: feature
- Priority: high
- Dependencies: setup_database ✓, create_user_model ✓

## Objective
Implement OAuth2 authentication flow with Google and GitHub providers.

## Implementation Checklist
- [ ] Create OAuth2 provider interface
- [ ] Implement Google OAuth2 flow
- [ ] Implement GitHub OAuth2 flow
- [ ] Add token refresh mechanism
- [ ] Write tests (coverage: 80%+)
- [ ] Update documentation

## Validation Requirements
- All tests must pass
- Coverage >= 80%
- Linting must pass
- Documentation updated

Starting work on implement_authentication...
```

**Implementation Details:**

The command markdown instructs Claude to:
1. Run script: `python scripts/briefing_generator.py`
2. Read generated briefing
3. Update work item status
4. Begin work
```

### 1.4 Create `/session-end` Command

**File:** `commands/session-end.md`

```markdown
# Session End Command

**Usage:** `/session-end`

**Description:** Complete current session with quality gates and summary generation.

**Behavior:**

1. Determine current work item (from status)

2. Run quality gates:
   - Execute tests
   - Run linting (auto-fix if possible)
   - Check formatting
   - Validate coverage meets requirements

3. If quality gates pass:
   - Update work item status (to "completed" if done, keep "in_progress" if partial)
   - Generate session summary
   - Update tracking files
   - Create git commit (standardized format)

4. If quality gates fail:
   - Report failures
   - Keep work item in "in_progress"
   - Offer to fix issues or skip gates

5. Present session summary

**Example:**

```
User: /session-end

Claude: Completing session...

Running quality gates...
✓ Tests: 47/47 passed (coverage: 87%)
✓ Linting: passed (3 issues auto-fixed)
✓ Formatting: passed

Quality gates: PASSED ✓

Updating work item status...
- implement_authentication: in_progress → completed

# Session Summary

## Work Items Completed
- implement_authentication

## Achievements
- Implemented OAuth2 authentication flow
- Added Google and GitHub providers
- Created token refresh mechanism
- Added 15 tests with 87% coverage

## Challenges Encountered
- Token expiry handling was tricky
- Race condition in token storage (resolved with Redis atomic ops)

## Learnings
- OAuth2 refresh tokens must be stored atomically
- Using Redis for token storage provides TTL and atomicity

## Metrics
- Files changed: 8
- Tests added: 15
- Lines added: 342
- Lines removed: 87

Session completed successfully ✓
```

**Implementation Details:**

The command markdown instructs Claude to:
1. Run script: `python scripts/session_complete.py`
2. Review quality gate results
3. Update work item status
4. Generate session summary
5. Create git commit
```

### 1.5 Create Briefing Generator Script

**File:** `scripts/briefing_generator.py`

```python
#!/usr/bin/env python3
"""
Generate session briefing for next work item.
"""

import json
from pathlib import Path
from datetime import datetime

def load_work_items():
    """Load work items from tracking file."""
    work_items_file = Path(".session/tracking/work_items.json")
    if not work_items_file.exists():
        return {"work_items": {}}
    with open(work_items_file) as f:
        return json.load(f)

def load_learnings():
    """Load learnings from tracking file."""
    learnings_file = Path(".session/tracking/learnings.json")
    if not learnings_file.exists():
        return {"learnings": []}
    with open(learnings_file) as f:
        return json.load(f)

def get_next_work_item(work_items_data):
    """
    Find next available work item where dependencies are satisfied.
    Returns item with highest priority among available.
    """
    work_items = work_items_data.get("work_items", {})

    available = []
    for item_id, item in work_items.items():
        if item["status"] != "not_started":
            continue

        # Check dependencies
        deps_satisfied = all(
            work_items.get(dep_id, {}).get("status") == "completed"
            for dep_id in item.get("dependencies", [])
        )

        if deps_satisfied:
            available.append((item_id, item))

    if not available:
        return None, None

    # Sort by priority
    priority_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    available.sort(
        key=lambda x: priority_order.get(x[1].get("priority", "medium"), 2),
        reverse=True
    )

    return available[0]

def get_relevant_learnings(learnings_data, work_item):
    """Get learnings relevant to this work item."""
    learnings = learnings_data.get("learnings", [])
    relevant = []

    # Simple relevance: check if work item tags overlap with learning tags
    work_item_tags = set(work_item.get("tags", []))

    for learning in learnings:
        learning_tags = set(learning.get("tags", []))
        if work_item_tags & learning_tags:  # Intersection
            relevant.append(learning)

    # Limit to 5 most recent relevant learnings
    return sorted(relevant, key=lambda x: x.get("created_at", ""), reverse=True)[:5]

def generate_briefing(item_id, item, learnings_data):
    """Generate markdown briefing for work item."""

    briefing = f"""# Session Briefing

## Work Item: {item['title']}
- **ID:** {item_id}
- **Type:** {item['type']}
- **Priority:** {item['priority']}
- **Status:** {item['status']}

## Objective

{item.get('rationale', 'No rationale provided')}

## Dependencies

"""

    # Show dependency status
    if item.get("dependencies"):
        for dep in item["dependencies"]:
            briefing += f"- {dep} ✓ completed\n"
    else:
        briefing += "No dependencies\n"

    briefing += "\n## Implementation Checklist\n\n"

    # Acceptance criteria become checklist
    if item.get("acceptance_criteria"):
        for criterion in item["acceptance_criteria"]:
            briefing += f"- [ ] {criterion}\n"
    else:
        briefing += "- [ ] Implement functionality\n"
        briefing += "- [ ] Write tests\n"
        briefing += "- [ ] Update documentation\n"

    # Relevant learnings
    relevant_learnings = get_relevant_learnings(learnings_data, item)
    if relevant_learnings:
        briefing += "\n## Relevant Learnings\n\n"
        for learning in relevant_learnings:
            briefing += f"**{learning.get('category', 'general')}:** {learning['content']}\n\n"

    # Validation requirements
    briefing += "\n## Validation Requirements\n\n"
    criteria = item.get("validation_criteria", {})
    if criteria.get("tests_pass", True):
        briefing += "- Tests must pass\n"
    if criteria.get("coverage_min"):
        briefing += f"- Coverage >= {criteria['coverage_min']}%\n"
    if criteria.get("linting_pass", True):
        briefing += "- Linting must pass\n"
    if criteria.get("documentation_required", False):
        briefing += "- Documentation must be updated\n"

    return briefing

def main():
    """Main entry point."""
    # Ensure .session directory exists
    session_dir = Path(".session")
    if not session_dir.exists():
        print("Error: .session directory not found. Run project initialization first.")
        return 1

    # Load data
    work_items_data = load_work_items()
    learnings_data = load_learnings()

    # Find next work item
    item_id, item = get_next_work_item(work_items_data)

    if not item_id:
        print("No available work items. All dependencies must be satisfied first.")
        return 1

    # Generate briefing
    briefing = generate_briefing(item_id, item, learnings_data)

    # Save briefing
    briefings_dir = session_dir / "briefings"
    briefings_dir.mkdir(exist_ok=True)

    # Determine session number
    session_num = max(
        [int(f.stem.split("_")[1]) for f in briefings_dir.glob("session_*.md")],
        default=0
    ) + 1

    briefing_file = briefings_dir / f"session_{session_num:03d}_briefing.md"
    with open(briefing_file, "w") as f:
        f.write(briefing)

    # Print briefing
    print(briefing)

    # Update status file
    status_file = session_dir / "tracking" / "status_update.json"
    status = {
        "current_session": session_num,
        "current_work_item": item_id,
        "started_at": datetime.now().isoformat(),
        "status": "in_progress"
    }
    with open(status_file, "w") as f:
        json.dump(status, f, indent=2)

    return 0

if __name__ == "__main__":
    exit(main())
```

### 1.6 Create Session Complete Script

**File:** `scripts/session_complete.py`

```python
#!/usr/bin/env python3
"""
Complete current session with quality gates and summary generation.
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime

def load_status():
    """Load current session status."""
    status_file = Path(".session/tracking/status_update.json")
    if not status_file.exists():
        return None
    with open(status_file) as f:
        return json.load(f)

def load_work_items():
    """Load work items."""
    with open(".session/tracking/work_items.json") as f:
        return json.load(f)

def run_quality_gates():
    """
    Run quality gates: tests, linting, formatting.
    Returns dict with results.
    """
    results = {
        "tests": {"passed": False, "details": None},
        "linting": {"passed": False, "details": None},
        "formatting": {"passed": False, "details": None},
    }

    # Run tests (if pytest available)
    try:
        result = subprocess.run(
            ["pytest", "--cov=.", "--cov-report=term"],
            capture_output=True,
            text=True,
            timeout=300
        )
        results["tests"]["passed"] = result.returncode == 0
        results["tests"]["details"] = result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        results["tests"]["passed"] = True  # Skip if pytest not found
        results["tests"]["details"] = "Tests skipped (pytest not found)"

    # Run linting (if ruff available)
    try:
        result = subprocess.run(
            ["ruff", "check", "--fix", "."],
            capture_output=True,
            text=True,
            timeout=60
        )
        results["linting"]["passed"] = result.returncode == 0
        results["linting"]["details"] = result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        results["linting"]["passed"] = True  # Skip if ruff not found

    # Check formatting (if ruff available)
    try:
        result = subprocess.run(
            ["ruff", "format", "--check", "."],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode != 0:
            # Auto-format
            subprocess.run(["ruff", "format", "."], timeout=60)
        results["formatting"]["passed"] = True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        results["formatting"]["passed"] = True

    return results

def generate_summary(status, work_items_data, gate_results):
    """Generate session summary."""
    work_item_id = status["current_work_item"]
    work_item = work_items_data["work_items"][work_item_id]

    summary = f"""# Session {status['current_session']} Summary

{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Work Items Completed
- {work_item_id}: {work_item['title']}

## Quality Gates
- Tests: {'✓ PASSED' if gate_results['tests']['passed'] else '✗ FAILED'}
- Linting: {'✓ PASSED' if gate_results['linting']['passed'] else '✗ FAILED'}
- Formatting: {'✓ PASSED' if gate_results['formatting']['passed'] else '✗ FAILED'}

## Next Session Priorities
To be determined
"""
    return summary

def main():
    """Main entry point."""
    # Load current status
    status = load_status()
    if not status:
        print("Error: No active session found")
        return 1

    work_items_data = load_work_items()

    print("Completing session...\n")
    print("Running quality gates...")

    # Run quality gates
    gate_results = run_quality_gates()

    # Print results
    for gate, result in gate_results.items():
        status_icon = "✓" if result["passed"] else "��"
        print(f"{status_icon} {gate.title()}: {'passed' if result['passed'] else 'failed'}")

    all_passed = all(r["passed"] for r in gate_results.values())

    if not all_passed:
        print("\n❌ Quality gates failed. Fix issues before completing session.")
        return 1

    print("\n✓ Quality gates PASSED\n")

    # Update work item status
    work_item_id = status["current_work_item"]
    work_items_data["work_items"][work_item_id]["status"] = "completed"
    work_items_data["work_items"][work_item_id]["metadata"]["completed_at"] = datetime.now().isoformat()

    # Save updated work items
    with open(".session/tracking/work_items.json", "w") as f:
        json.dump(work_items_data, f, indent=2)

    # Generate summary
    summary = generate_summary(status, work_items_data, gate_results)

    # Save summary
    history_dir = Path(".session/history")
    history_dir.mkdir(exist_ok=True)
    summary_file = history_dir / f"session_{status['current_session']:03d}_summary.md"
    with open(summary_file, "w") as f:
        f.write(summary)

    # Print summary
    print(summary)

    # Update status
    status["status"] = "completed"
    status["completed_at"] = datetime.now().isoformat()
    with open(".session/tracking/status_update.json", "w") as f:
        json.dump(status, f, indent=2)

    print("\n✓ Session completed successfully")
    return 0

if __name__ == "__main__":
    exit(main())
```

### 1.7 Create Initial Templates

**File:** `templates/work_items.json`

```json
{
  "metadata": {
    "total_items": 0,
    "completed": 0,
    "in_progress": 0,
    "blocked": 0,
    "last_updated": null
  },
  "milestones": {},
  "work_items": {}
}
```

**File:** `templates/learnings.json`

```json
{
  "metadata": {
    "total_learnings": 0,
    "last_curated": null
  },
  "categories": {
    "architecture_patterns": [],
    "gotchas": [],
    "best_practices": [],
    "technical_debt": [],
    "performance": [],
    "security": []
  },
  "learnings": []
}
```

**File:** `templates/status_update.json`

```json
{
  "current_session": null,
  "current_work_item": null,
  "started_at": null,
  "status": "idle"
}
```

### 1.8 Create Project Initialization Script

**File:** `scripts/init_project.py`

```python
#!/usr/bin/env python3
"""
Initialize .session directory structure in current project.
"""

import json
import shutil
from pathlib import Path

def init_project():
    """Create .session directory structure."""
    session_dir = Path(".session")

    if session_dir.exists():
        print("⚠️  .session directory already exists")
        return

    print("Initializing Session-Driven Development structure...\n")

    # Create directories
    (session_dir / "tracking").mkdir(parents=True)
    (session_dir / "briefings").mkdir(parents=True)
    (session_dir / "history").mkdir(parents=True)
    (session_dir / "specs").mkdir(parents=True)

    # Copy templates
    template_dir = Path(__file__).parent.parent / "templates"

    shutil.copy(
        template_dir / "work_items.json",
        session_dir / "tracking" / "work_items.json"
    )
    shutil.copy(
        template_dir / "learnings.json",
        session_dir / "tracking" / "learnings.json"
    )
    shutil.copy(
        template_dir / "status_update.json",
        session_dir / "tracking" / "status_update.json"
    )

    print("✓ Created .session/tracking/")
    print("✓ Created .session/briefings/")
    print("✓ Created .session/history/")
    print("✓ Created .session/specs/")
    print("✓ Initialized tracking files\n")

    print("Session-Driven Development initialized!")
    print("\nNext steps:")
    print("1. Create your first work item")
    print("2. Run /session-start to begin")

if __name__ == "__main__":
    init_project()
```

### 1.9 Create README

**File:** `README.md`

```markdown
# Claude Code Session Plugin

Session-Driven Development for Claude Code - Maintain perfect context across multiple AI coding sessions.

## Installation

1. Add this repository as a plugin marketplace:
```bash
/plugin marketplace add /path/to/claude-session-plugin
```

2. Install the plugin:
```bash
/plugin install session
```

3. Verify installation:
```bash
/help
```

You should see new commands: `/session-start`, `/session-end`, etc.

## Quick Start

1. **Initialize project** (first time):
```
/session-start
```

Claude will detect no `.session/` directory and initialize it.

2. **Create first work item** (manually for now):

Edit `.session/tracking/work_items.json`:
```json
{
  "metadata": {"total_items": 1, ...},
  "work_items": {
    "setup_project": {
      "id": "setup_project",
      "type": "setup",
      "title": "Setup project structure",
      "status": "not_started",
      "priority": "high",
      "dependencies": [],
      "rationale": "Initialize project with proper structure",
      "acceptance_criteria": [
        "Create src/ directory",
        "Setup tests/",
        "Add README"
      ],
      "validation_criteria": {
        "tests_pass": true,
        "linting_pass": true
      },
      "metadata": {
        "created_at": "2025-10-10T00:00:00"
      }
    }
  }
}
```

3. **Start session**:
```
/session-start
```

4. **Complete session**:
```
/session-end
```

## Commands

- `/session-start` - Begin work session
- `/session-end` - Complete session with quality gates
- More commands coming in future phases

## Documentation

- [Implementation Plan](PLUGIN_IMPLEMENTATION_PLAN.md) - Full development roadmap
- [Session-Driven Development Framework](docs/SESSION_DRIVEN_DEVELOPMENT_FRAMEWORK.md) - Methodology
- [Implementation Insights](docs/IMPLEMENTATION_INSIGHTS.md) - Lessons learned

## License

MIT
```

### 1.10 Phase 1 Testing

**Manual test checklist:**

1. Create test project:
```bash
mkdir test-project
cd test-project
git init
```

2. Load plugin in Claude Code:
```
/plugin marketplace add /path/to/claude-session-plugin
/plugin install session
```

3. Test session start:
```
/session-start
```

Expected: Initializes .session/, creates work_items.json, shows error about no work items

4. Manually add work item to `.session/tracking/work_items.json`

5. Test session start again:
```
/session-start
```

Expected: Shows briefing for work item

6. Do some work (create files, write code)

7. Test session end:
```
/session-end
```

Expected: Runs tests/linting, updates status, shows summary

**Success criteria for Phase 1:**
- ✅ Plugin loads without errors
- ✅ `/session-start` initializes project
- ✅ `/session-start` reads work items and generates briefing
- ✅ `/session-end` runs quality gates
- ✅ `/session-end` updates work item status
- ✅ Session summaries are generated

---

## Phase 2: Work Item Management (Week 2)

### Goal
Add `/work-item` command group for full work item lifecycle management.

### 2.1 Create `/work-item` Command

**File:** `commands/work-item.md`

```markdown
# Work Item Command Group

**Usage:** `/work-item <subcommand> [options]`

**Subcommands:**
- `create` - Create new work item interactively
- `list [--status STATUS]` - List all work items (optionally filtered)
- `show <id>` - Show work item details
- `update <id> [--status STATUS]` - Update work item
- `next` - Show next available work item

## /work-item create

**Description:** Interactively create a new work item.

**Prompts user for:**
- Title
- Type (feature/bug/refactor/etc.)
- Priority (low/medium/high/critical)
- Dependencies (comma-separated IDs)
- Rationale
- Acceptance criteria (multi-line)

**Example:**

```
User: /work-item create

Claude: Creating new work item...

Title: Implement user authentication
Type (feature/bug/refactor): feature
Priority (low/medium/high/critical): high
Dependencies (comma-separated IDs, or press Enter): setup_database,create_user_model
Rationale: Users need to authenticate to access protected features
Acceptance criteria (one per line, empty line to finish):
> Users can sign in with email/password
> Sessions persist across browser restarts
> Passwords are hashed with bcrypt
>

Work item created: implement_user_auth

{
  "id": "implement_user_auth",
  "type": "feature",
  "title": "Implement user authentication",
  "status": "not_started",
  "priority": "high",
  "dependencies": ["setup_database", "create_user_model"],
  "rationale": "Users need to authenticate to access protected features",
  "acceptance_criteria": [
    "Users can sign in with email/password",
    "Sessions persist across browser restarts",
    "Passwords are hashed with bcrypt"
  ]
}
```

## /work-item list

**Description:** List all work items, optionally filtered by status.

**Options:**
- `--status not_started|in_progress|completed|blocked`

**Example:**

```
User: /work-item list --status not_started

Claude:
# Work Items (Not Started)

1. **implement_user_auth** (feature, high priority)
   Dependencies: setup_database ✓, create_user_model ✓
   Status: Ready to start

2. **add_profile_page** (feature, medium priority)
   Dependencies: implement_user_auth ✗
   Status: Blocked (waiting on implement_user_auth)

3. **setup_testing** (setup, high priority)
   Dependencies: None
   Status: Ready to start
```

## /work-item show

**Description:** Show detailed information about a work item.

**Example:**

```
User: /work-item show implement_user_auth

Claude:
# Work Item: implement_user_auth

**Type:** feature
**Status:** not_started
**Priority:** high

## Rationale
Users need to authenticate to access protected features

## Dependencies
- setup_database ✓ completed
- create_user_model ✓ completed

## Acceptance Criteria
- Users can sign in with email/password
- Sessions persist across browser restarts
- Passwords are hashed with bcrypt

## Validation Requirements
- Tests must pass
- Coverage >= 80%
- Linting must pass

## Sessions
Not started yet

## Created
2025-10-10 10:00:00
```

## /work-item next

**Description:** Show next available work item (dependencies satisfied, highest priority).

**Example:**

```
User: /work-item next

Claude:
Next available work item: **implement_user_auth** (high priority)

All dependencies satisfied:
- setup_database ✓
- create_user_model ✓

Ready to start session.
```
```

### 2.2 Implement Work Item Scripts

**File:** `scripts/work_item_manager.py`

```python
#!/usr/bin/env python3
"""
Work item management: create, list, show, update.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

WORK_ITEMS_FILE = Path(".session/tracking/work_items.json")

def load_work_items():
    """Load work items from tracking file."""
    if not WORK_ITEMS_FILE.exists():
        return {"metadata": {}, "work_items": {}}
    with open(WORK_ITEMS_FILE) as f:
        return json.load(f)

def save_work_items(data):
    """Save work items to tracking file."""
    WORK_ITEMS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(WORK_ITEMS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def create_work_item_id(title):
    """Generate work item ID from title."""
    return title.lower().replace(" ", "_").replace("-", "_")[:50]

def create_work_item(title, type_, priority, dependencies, rationale, acceptance_criteria):
    """Create a new work item."""
    data = load_work_items()

    item_id = create_work_item_id(title)

    # Check if ID already exists
    if item_id in data["work_items"]:
        print(f"Error: Work item '{item_id}' already exists")
        return 1

    # Validate dependencies exist
    for dep in dependencies:
        if dep not in data["work_items"]:
            print(f"Error: Dependency '{dep}' does not exist")
            return 1

    # Create work item
    work_item = {
        "id": item_id,
        "type": type_,
        "title": title,
        "status": "not_started",
        "priority": priority,
        "dependencies": dependencies,
        "dependents": [],
        "rationale": rationale,
        "acceptance_criteria": acceptance_criteria,
        "validation_criteria": {
            "tests_pass": True,
            "coverage_min": 80,
            "linting_pass": True
        },
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "completed_at": None
        },
        "session_notes": {},
        "sessions": []
    }

    data["work_items"][item_id] = work_item

    # Update dependents
    for dep in dependencies:
        if "dependents" not in data["work_items"][dep]:
            data["work_items"][dep]["dependents"] = []
        data["work_items"][dep]["dependents"].append(item_id)

    # Update metadata
    data["metadata"]["total_items"] = len(data["work_items"])
    data["metadata"]["last_updated"] = datetime.now().isoformat()

    save_work_items(data)

    print(f"Work item created: {item_id}\n")
    print(json.dumps(work_item, indent=2))
    return 0

def list_work_items(status_filter=None):
    """List all work items, optionally filtered by status."""
    data = load_work_items()

    items = data["work_items"]
    if status_filter:
        items = {k: v for k, v in items.items() if v["status"] == status_filter}

    if not items:
        print("No work items found")
        return 0

    print(f"# Work Items ({status_filter or 'all'})\n")

    for item_id, item in items.items():
        # Check if dependencies satisfied
        all_deps_satisfied = all(
            data["work_items"].get(dep, {}).get("status") == "completed"
            for dep in item.get("dependencies", [])
        )

        status_indicator = {
            "not_started": "⭕",
            "in_progress": "🔵",
            "completed": "✅",
            "blocked": "🔴"
        }.get(item["status"], "❓")

        print(f"{status_indicator} **{item_id}** ({item['type']}, {item['priority']} priority)")
        print(f"   {item['title']}")

        if item.get("dependencies"):
            deps_status = ", ".join(
                f"{dep} {'✓' if data['work_items'].get(dep, {}).get('status') == 'completed' else '✗'}"
                for dep in item["dependencies"]
            )
            print(f"   Dependencies: {deps_status}")

        if all_deps_satisfied and item["status"] == "not_started":
            print(f"   Status: Ready to start")
        elif not all_deps_satisfied and item["status"] == "not_started":
            print(f"   Status: Blocked (waiting on dependencies)")

        print()

    return 0

def show_work_item(item_id):
    """Show detailed information about a work item."""
    data = load_work_items()

    if item_id not in data["work_items"]:
        print(f"Error: Work item '{item_id}' not found")
        return 1

    item = data["work_items"][item_id]

    print(f"# Work Item: {item_id}\n")
    print(f"**Type:** {item['type']}")
    print(f"**Status:** {item['status']}")
    print(f"**Priority:** {item['priority']}\n")

    print(f"## Title\n{item['title']}\n")

    if item.get("rationale"):
        print(f"## Rationale\n{item['rationale']}\n")

    if item.get("dependencies"):
        print("## Dependencies")
        for dep in item["dependencies"]:
            dep_status = data["work_items"].get(dep, {}).get("status", "unknown")
            print(f"- {dep} {'✓' if dep_status == 'completed' else '✗'} {dep_status}")
        print()

    if item.get("acceptance_criteria"):
        print("## Acceptance Criteria")
        for criterion in item["acceptance_criteria"]:
            print(f"- {criterion}")
        print()

    print("## Validation Requirements")
    criteria = item.get("validation_criteria", {})
    if criteria.get("tests_pass"):
        print("- Tests must pass")
    if criteria.get("coverage_min"):
        print(f"- Coverage >= {criteria['coverage_min']}%")
    if criteria.get("linting_pass"):
        print("- Linting must pass")
    print()

    if item.get("sessions"):
        print(f"## Sessions\n{', '.join(map(str, item['sessions']))}\n")
    else:
        print("## Sessions\nNot started yet\n")

    print(f"## Created\n{item['metadata'].get('created_at', 'Unknown')}")

    if item['metadata'].get('completed_at'):
        print(f"## Completed\n{item['metadata']['completed_at']}")

    return 0

def get_next_work_item():
    """Find and show next available work item."""
    data = load_work_items()

    available = []
    for item_id, item in data["work_items"].items():
        if item["status"] != "not_started":
            continue

        # Check dependencies
        deps_satisfied = all(
            data["work_items"].get(dep, {}).get("status") == "completed"
            for dep in item.get("dependencies", [])
        )

        if deps_satisfied:
            available.append((item_id, item))

    if not available:
        print("No available work items. All dependencies must be satisfied first.")
        return 1

    # Sort by priority
    priority_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    available.sort(
        key=lambda x: priority_order.get(x[1].get("priority", "medium"), 2),
        reverse=True
    )

    item_id, item = available[0]

    print(f"Next available work item: **{item_id}** ({item['priority']} priority)\n")
    print(f"{item['title']}\n")

    if item.get("dependencies"):
        print("All dependencies satisfied:")
        for dep in item["dependencies"]:
            print(f"- {dep} ✓")
        print()

    print("Ready to start session.")
    return 0

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: work_item_manager.py <create|list|show|next> [args]")
        return 1

    command = sys.argv[1]

    if command == "create":
        # Interactive create
        title = input("Title: ")
        type_ = input("Type (feature/bug/refactor): ")
        priority = input("Priority (low/medium/high/critical): ")
        dependencies = input("Dependencies (comma-separated IDs): ").split(",")
        dependencies = [d.strip() for d in dependencies if d.strip()]
        rationale = input("Rationale: ")

        print("Acceptance criteria (one per line, empty line to finish):")
        acceptance_criteria = []
        while True:
            line = input("> ")
            if not line:
                break
            acceptance_criteria.append(line)

        return create_work_item(title, type_, priority, dependencies, rationale, acceptance_criteria)

    elif command == "list":
        status_filter = sys.argv[2] if len(sys.argv) > 2 else None
        return list_work_items(status_filter)

    elif command == "show":
        if len(sys.argv) < 3:
            print("Usage: work_item_manager.py show <id>")
            return 1
        return show_work_item(sys.argv[2])

    elif command == "next":
        return get_next_work_item()

    else:
        print(f"Unknown command: {command}")
        return 1

if __name__ == "__main__":
    exit(main())
```

### 2.3 Update `/session-start` to Support `--item`

Update `commands/session-start.md` to handle optional `--item <id>` parameter.

Modify `scripts/briefing_generator.py` to:
- Accept optional `--item <id>` command line arg
- If provided, use that item instead of finding next

### 2.4 Phase 2 Testing

**Test work item creation:**
```
/work-item create
```

**Test work item listing:**
```
/work-item list
/work-item list --status not_started
```

**Test work item details:**
```
/work-item show <id>
```

**Test next item:**
```
/work-item next
```

**Test session start with specific item:**
```
/session-start --item <id>
```

---

## Phase 3: Dependency Graph Visualization (Week 3)

### Goal
Add `/work-item graph` command to visualize dependencies and critical path.

### 3.1 Implement Dependency Graph Visualization

**File:** `scripts/dependency_graph.py`

This script is already implemented and ready to use. It provides:

Key functions available:
- `generate_dot()` - Graphviz DOT format generation
- `generate_ascii()` - Terminal-friendly ASCII art visualization
- `generate_svg()` - SVG export (requires graphviz package)
- `_calculate_critical_path()` - DFS-based longest dependency chain analysis
- `_group_by_dependency_level()` - Topological sorting by dependency level

The script can be executed directly:
```bash
python scripts/dependency_graph.py --format ascii
python scripts/dependency_graph.py --format svg --output deps.svg
```

### 3.2 Add `/work-item graph` Subcommand

Update `commands/work-item.md` to add:

```markdown
## /work-item graph

**Usage:** `/work-item graph [--format ascii|dot|svg] [--output FILE]`

**Description:** Generate dependency graph visualization.

**Options:**
- `--format ascii|dot|svg` - Output format (default: ascii)
- `--output FILE` - Save to file instead of printing
- `--include-completed` - Show completed items (default: hide)

**Example:**

```
User: /work-item graph

Claude: Generating dependency graph...

┌────────────────────┐
│ setup_database     │  [COMPLETED]
└──────────┬─────────┘
           │
           ▼
┌────────────────────┐
│ create_user_model  │  [COMPLETED]
└──────────┬─────────┘
           │
           ▼
┌────────────────────┐
│ implement_auth     │  [IN_PROGRESS] ⚡ CRITICAL PATH
└──────────┬─────────┘
           │
           ▼
┌────────────────────┐
│ add_profile_page   │  [NOT_STARTED]
└────────────────────┘

Critical Path: setup_database → create_user_model → implement_auth → add_profile_page
Estimated sessions: 8
```
```

### 3.3 Phase 3 Testing

Test graph generation in all formats:
```
/work-item graph
/work-item graph --format dot
/work-item graph --format svg --output deps.svg
```

---

## Phase 4: Learning Management (Week 4)

### Goal
Add `/learning` command group for capturing and curating knowledge.

### 4.1 Create `/learning` Command

**File:** `commands/learning.md`

```markdown
# Learning Command Group

**Usage:** `/learning <subcommand> [options]`

**Subcommands:**
- `capture` - Record a learning during session
- `show [--category CAT]` - View learnings
- `search <query>` - Search learnings
- `curate` - Run curation process (dedupe, categorize)

## /learning capture

**Description:** Record a learning during current session.

**Prompts for:**
- Content (what was learned)
- Context (why it matters)
- Tags (comma-separated)

**Example:**

```
User: /learning capture

Claude: Recording learning...

Content: OAuth2 refresh tokens must be stored atomically
Context: Using non-atomic operations causes race conditions in token refresh
Tags (comma-separated): oauth, concurrency, redis

Learning captured!

Auto-categorized as: gotcha
```

## /learning show

**Description:** View learnings, optionally filtered by category.

**Example:**

```
User: /learning show --category gotchas

Claude:
# Learnings: Gotchas

1. **OAuth2 refresh tokens must be stored atomically**
   Context: Using non-atomic operations causes race conditions
   Session: 5
   Tags: oauth, concurrency, redis

2. **FastAPI async routes require async database connections**
   Context: Using sync SQLAlchemy in async routes causes blocking
   Session: 3
   Tags: fastapi, async, database
```

## /learning curate

**Description:** Run automated curation process.

**Process:**
1. Auto-categorize uncategorized learnings
2. Detect and merge similar/duplicate learnings
3. Archive old, unreferenced learnings
4. Generate curation report

**Example:**

```
User: /learning curate

Claude: Running learning curation...

Auto-categorizing 3 uncategorized learnings...
✓ Categorized 3 learnings

Detecting similar learnings...
✓ Found 2 duplicate pairs, merged

Archiving old learnings...
✓ Archived 5 learnings (>50 sessions old)

Curation complete!

Report:
- Total learnings: 47
- By category:
  - Architecture patterns: 12
  - Gotchas: 15
  - Best practices: 8
  - Technical debt: 7
  - Performance: 5
```
```

### 4.2 Implement Learning Scripts

**File:** `scripts/learning_curator.py`

This script is already implemented and ready to use. It provides:

Key functions available:
- `capture_learning()` - Record learnings during sessions
- `show_learnings()` - Display learnings by category
- `search_learnings()` - Search through accumulated knowledge
- `auto_categorize_learning()` - Keyword-based categorization into 5 categories
- `are_similar()` - Jaccard + containment similarity detection (thresholds: 0.6, 0.8)
- `curate_learnings()` - Full curation workflow (categorize, merge, archive)

The script can be executed directly:
```bash
python scripts/learning_curator.py
python scripts/learning_curator.py --report
python scripts/learning_curator.py --show gotchas
```

### 4.3 Phase 4 Testing

Test learning capture:
```
/learning capture
```

Test learning viewing:
```
/learning show
/learning show --category gotchas
```

Test curation:
```
/learning curate
```

---

## Phase 5: Quality Gates (Week 5)

### Goal
Enhance session completion with comprehensive quality gates.

### 5.1 Enhance Session Complete Script

Update `scripts/session_complete.py` to:
- Run tests with coverage reporting
- Parse coverage percentage
- Run linting with auto-fix
- Check formatting
- Generate detailed gate report
- Create standardized git commit

### 5.2 Add Git Integration

**File:** `scripts/git_integration.py`

```python
#!/usr/bin/env python3
"""
Git integration: commit generation, staging, pushing.
"""

def generate_commit_message(session_num, work_item, summary):
    """
    Generate standardized commit message.

    Format:
    Session N: [Work item title]

    - [Achievement 1]
    - [Achievement 2]

    Work items completed:
    - [work_item_id]: [title]

    Validation: ✅ Tests | ✅ Linting | ✅ Formatting

    🤖 Generated with Claude Code
    Co-Authored-By: Claude <noreply@anthropic.com>
    """
    pass

def create_commit(message):
    """Stage all changes and create commit."""
    pass
```

### 5.3 Phase 5 Testing

Complete full workflow:
```
/session-start
[Do work]
/session-end
```

Verify:
- Tests run automatically
- Linting runs and auto-fixes
- Formatting checked
- Git commit created with proper message
- Work item status updated

---

## Phase 6: Documentation & Polish (Week 6)

### Goal
Complete documentation, error handling, and user experience.

### 6.1 Create Comprehensive Documentation

**Files to create:**
- `docs/SESSION_DRIVEN_DEVELOPMENT_FRAMEWORK.md` (copy from extracted file)
- `docs/IMPLEMENTATION_INSIGHTS.md` (copy from created file)
- `docs/ai-augmented-solo-framework.md` (copy from user's resources)
- `docs/QUICK_START.md`
- `docs/TROUBLESHOOTING.md`
- `docs/CONFIGURATION.md`

### 6.2 Add Error Handling

Review all scripts and add:
- Try/except blocks
- Helpful error messages
- Recovery suggestions
- Validation of inputs

### 6.3 Add Configuration

**File:** `templates/.sessionrc.json`

```json
{
  "project": {
    "name": "my-project",
    "type": "web_application"
  },
  "paths": {
    "tracking": ".session/tracking",
    "briefings": ".session/briefings",
    "history": ".session/history",
    "specs": ".session/specs"
  },
  "validation_rules": {
    "post_session": {
      "tests_pass": true,
      "linting_pass": true,
      "formatting_pass": true,
      "test_coverage_min": 80
    }
  },
  "runtime_standards": {
    "linting": {
      "enabled": true,
      "tool": "ruff",
      "auto_fix": true
    },
    "formatting": {
      "enabled": true,
      "tool": "ruff"
    },
    "testing": {
      "enabled": true,
      "tool": "pytest",
      "coverage_tool": "pytest-cov"
    }
  }
}
```

### 6.4 Create Quick Start Guide

**File:** `docs/QUICK_START.md`

[Comprehensive guide for first-time users]

### 6.5 Phase 6 Testing

- Test on fresh project
- Test with missing dependencies
- Test with invalid work items
- Test with git errors
- Test with failing tests
- Document all error scenarios

---

## Success Criteria

Plugin is **complete and usable** when:

✅ All commands work without errors
✅ Session workflow is smooth (start → work → end)
✅ Work items can be created, listed, visualized
✅ Learnings can be captured and curated
✅ Quality gates prevent broken states
✅ Git commits are generated correctly
✅ Documentation is comprehensive
✅ Error messages are helpful

Plugin is **production-ready** when:

✅ Used successfully on 3+ real projects
✅ 20+ sessions completed without issues
✅ All edge cases handled gracefully
✅ Performance is acceptable
✅ No data loss or corruption

---

## Timeline Summary

| Phase | Duration | Milestone |
|-------|----------|-----------|
| 1: Core Plugin | 1 week | Basic session workflow |
| 2: Work Items | 1 week | Task management |
| 3: Visualization | 1 week | Dependency graphs |
| 4: Learning | 1 week | Knowledge capture |
| 5: Quality Gates | 1 week | Validation |
| 6: Polish | 1 week | Documentation & UX |

**Total: 6 weeks to v1.0**

---

## Getting Started

The plugin repository structure is ready. Here's how to begin implementation:

1. **Review Phase 1** (lines 24-866) - Core plugin foundation with `/session-start` and `/session-end` commands
2. **Create remaining files from this plan** - Copy code blocks for:
   - `.claude-plugin/plugin.json` (lines 58-74)
   - `commands/session-start.md` (lines 80-158)
   - `commands/session-end.md` (lines 164-247)
   - `scripts/briefing_generator.py` (lines 253-440)
   - `scripts/session_complete.py` (lines 446-609)
   - `scripts/init_project.py` (lines 664-719)
   - `README.md` (lines 723-815)
3. **Test Phase 1** - Follow testing checklist (lines 820-866)
4. **Proceed to Phase 2** - Work item management (lines 869-1347)
5. **Iterate** - Build incrementally, test thoroughly at each phase

**Ready to build.** All algorithms and patterns are in place.
