# Session Init Command

**Usage:** `/session-init`

**Description:** Initialize Session-Driven Development structure in current project.

**Behavior:**

1. Check if .session/ directory already exists
   - If exists: Show error "Project already initialized"
   - If not: Proceed with initialization

2. Check for project documentation
   - Look for docs/ folder in project root
   - Check for common doc files: README.md, vision.md, prd.md, architecture.md
   - If no documentation found:
     - Warn user that documentation is recommended
     - Suggest creating at least: docs/vision.md, docs/prd.md
     - Ask if user wants to continue anyway
   - If documentation exists: Proceed

3. Create directory structure:
   - .session/tracking/
   - .session/briefings/
   - .session/history/
   - .session/specs/

4. Initialize tracking files from templates:
   - tracking/work_items.json (empty)
   - tracking/learnings.json (empty structure)
   - tracking/status_update.json (idle state)
   - tracking/stack.txt (will be generated)
   - tracking/stack_updates.json (empty)
   - tracking/tree.txt (will be generated)
   - tracking/tree_updates.json (empty)

5. Run initial scans:
   - Run generate_stack.py to detect current stack
   - Run generate_tree.py to capture initial structure

6. Report initialization complete

**Example:**

```
User: /session-init

Claude: Initializing Session-Driven Development...

Checking for project documentation...
✓ Found docs/ directory
✓ Found docs/vision.md
✓ Found docs/architecture.md

Creating .session/ structure...
✓ Created .session/tracking/
✓ Created .session/briefings/
✓ Created .session/history/
✓ Created .session/specs/

Initializing tracking files...
✓ Created work_items.json
✓ Created learnings.json
✓ Created status_update.json

Running initial scans...
✓ Generated stack.txt (detected: Python 3.11, FastAPI, PostgreSQL)
✓ Generated tree.txt

Session-Driven Development initialized successfully!

Next steps:
1. Create work items: /work-item create
2. Start first session: /session-start
```

**Implementation:**

Run: `python scripts/init_project.py`
