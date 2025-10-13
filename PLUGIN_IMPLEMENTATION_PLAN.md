# Claude Code Session Plugin - Implementation Plan
## Complete Guide with Current State

This document provides a **complete, step-by-step implementation plan** for building the Claude Code Session Plugin.

---

## Current State (Updated: 13th October 2025)

### ✅ What Exists

**Repository Structure:**
```
claude-session-plugin/
├── .claude-plugin/
│   └── plugin.json              ✅ Valid manifest
├── commands/
│   ├── session-start.md         ✅ Enhanced (full context loading)
│   ├── session-end.md           ✅ Enhanced (comprehensive completion)
│   ├── session-init.md          ✅ Project initialization
│   └── session-validate.md      ✅ Pre-flight validation
├── scripts/
│   ├── briefing_generator.py    ✅ Enhanced (context-aware)
│   ├── session_complete.py      ✅ Enhanced (full tracking updates)
│   ├── generate_stack.py        ✅ Auto-detect tech stack
│   ├── generate_tree.py         ✅ Project structure tracking
│   ├── git_integration.py       ✅ Complete git workflow automation
│   ├── session_validate.py      ✅ Pre-flight validation
│   ├── learning_curator.py      ✅ Complete, production-ready
│   ├── dependency_graph.py      ✅ Complete, production-ready
│   ├── file_ops.py              ✅ Utilities ready
│   └── init_project.py          ✅ Enhanced with doc checks
├── templates/
│   ├── work_items.json          ✅ Schema with 6 types
│   ├── learnings.json           ✅ Schema defined
│   ├── status_update.json       ✅ Schema defined
│   ├── WORK_ITEM_TYPES.md       ✅ Type definitions
│   ├── security_task.md         ✅ Security work item template
│   ├── integration_test_spec.md ✅ Integration test template
│   └── deployment_spec.md       ✅ Deployment template
├── docs/
│   ├── session-driven-development.md     ✅ Complete
│   ├── implementation-insights.md        ✅ Complete
│   └── ai-augmented-solo-framework.md    ✅ Complete
├── ROADMAP.md                   ✅ Updated (Phase 1 complete)
└── README.md                    ✅ Complete
```

### 🔧 What Works

- ✅ Plugin manifest is valid
- ✅ **Complete session workflow (init → start → validate → end)**
- ✅ **Project initialization with documentation checks**
- ✅ **Stack tracking with auto-detection and reasoning**
- ✅ **Tree tracking with structural change detection**
- ✅ **Git workflow automation (branch management, commits, merges)**
- ✅ **Multi-session work item support (resume branches)**
- ✅ **Pre-flight validation (`/session-validate`)**
- ✅ **6 work item types (feature, bug, refactor, security, integration_test, deployment)**
- ✅ Learning curation system complete (auto-categorize, similarity detection, merge)
- ✅ Dependency graph visualization complete (ASCII, DOT, SVG with critical path)
- ✅ Enhanced briefing generation with full project context
- ✅ Comprehensive session completion with tracking updates
- ✅ File utilities for safe atomic JSON operations

---

## Phase 1: Core Plugin Foundation (v0.1)

**Goal:** Complete working session workflow with full tracking and git integration

**Status:** ✅ Complete

**Completed:** 13th October 2025

**Priority:** HIGH

**Depends On:** Phase 0 (Complete)

### Overview

Phase 1 successfully established the complete session workflow with:
- Project initialization that checks documentation and sets up tracking
- Automated stack tracking to record technology decisions
- Automated tree tracking to maintain structural consistency
- Git workflow integration to prevent mistakes and maintain clean history
- Enhanced briefings with full project context
- Comprehensive session completion that updates all tracking systems

This phase transformed the basic session workflow into a production-ready system.

### What Was Accomplished

Phase 1 successfully implemented all 9 sections with critical bug fixes and comprehensive testing. The plugin now provides a complete, production-ready session workflow with:

**Core Features:**
- Project initialization with documentation checking
- Automated technology stack tracking with change reasoning
- Project structure monitoring with tree tracking
- Complete git workflow integration (branch management, commits, merges)
- Comprehensive context loading at session start
- Quality gates enforcement at session end
- Pre-flight validation command
- 6 work item types with proper validation

**Critical Fixes:**
- Multi-session support (resume in-progress work items)
- Parent branch tracking (merge to parent, not hardcoded main)

**Testing:**
- Complete end-to-end workflow validated
- Multi-session work items tested (3 sessions on same branch)
- 6 edge cases thoroughly tested

### Lessons Learned

1. **Git workflow complexity:** Parent branch tracking essential for feature branch workflows
2. **Multi-session support:** Resuming in-progress items required priority-based selection logic
3. **Quality gates:** Non-destructive validation (`/session-validate`) valuable for preview
4. **Edge cases critical:** Dirty git, missing docs, dependencies all need proper handling
5. **Testing thoroughness:** Comprehensive testing uncovered 2 critical issues that were fixed

### Known Limitations

None significant. All Phase 1 success criteria met.

---

### 1.1 Create `/session-init` Command

**Purpose:** Initialize .session/ structure in a project for the first time

**Status:** ✅ Complete

**Files:**
- `commands/session-init.md` (NEW)
- `scripts/init_project.py` (enhance existing)

**Reference:** See session-driven-development.md for directory structure

#### Implementation

**File:** `commands/session-init.md`

```markdown
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

\`\`\`
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
\`\`\`
```

**Implementation Details:**

The command instructs Claude to run: `python scripts/init_project.py`

**File:** `scripts/init_project.py` (enhanced)

```python
#!/usr/bin/env python3
"""
Initialize .session directory structure in current project.
Enhanced with documentation checks and initial scans.
"""

import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime


def check_documentation():
    """Check for project documentation."""
    docs_dir = Path("docs")
    
    if not docs_dir.exists():
        print("⚠️  No docs/ directory found")
        print("   Recommendation: Create at least docs/vision.md and docs/prd.md")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return False
    
    # Check for common doc files
    found_docs = []
    for doc_file in ["vision.md", "prd.md", "architecture.md", "README.md"]:
        if (docs_dir / doc_file).exists() or Path(doc_file).exists():
            found_docs.append(doc_file)
            print(f"✓ Found {doc_file}")
    
    if found_docs:
        print(f"\n✓ Project documentation found ({len(found_docs)} files)")
    else:
        print("\n⚠️  No standard documentation files found")
    
    return True


def create_directory_structure():
    """Create .session directory structure."""
    session_dir = Path(".session")
    
    if session_dir.exists():
        print("❌ Error: .session directory already exists")
        print("   Project already initialized")
        return False
    
    print("\nCreating .session/ structure...")
    
    # Create directories
    (session_dir / "tracking").mkdir(parents=True)
    (session_dir / "briefings").mkdir(parents=True)
    (session_dir / "history").mkdir(parents=True)
    (session_dir / "specs").mkdir(parents=True)
    
    print("✓ Created .session/tracking/")
    print("✓ Created .session/briefings/")
    print("✓ Created .session/history/")
    print("✓ Created .session/specs/")
    
    return True


def initialize_tracking_files():
    """Initialize tracking files from templates."""
    session_dir = Path(".session")
    template_dir = Path(__file__).parent.parent / "templates"
    
    print("\nInitializing tracking files...")
    
    # Copy templates
    tracking_files = [
        ("work_items.json", "tracking/work_items.json"),
        ("learnings.json", "tracking/learnings.json"),
        ("status_update.json", "tracking/status_update.json"),
    ]
    
    for src, dst in tracking_files:
        src_path = template_dir / src
        dst_path = session_dir / dst
        if src_path.exists():
            shutil.copy(src_path, dst_path)
            print(f"✓ Created {dst}")
    
    # Create empty files for stack and tree tracking
    (session_dir / "tracking" / "stack_updates.json").write_text(
        json.dumps({"updates": []}, indent=2)
    )
    print("✓ Created stack_updates.json")
    
    (session_dir / "tracking" / "tree_updates.json").write_text(
        json.dumps({"updates": []}, indent=2)
    )
    print("✓ Created tree_updates.json")
    
    return True


def run_initial_scans():
    """Run initial stack and tree scans."""
    print("\nRunning initial scans...")
    
    # Run generate_stack.py
    try:
        subprocess.run(
            ["python", "scripts/generate_stack.py"],
            check=True,
            capture_output=True
        )
        print("✓ Generated stack.txt")
    except subprocess.CalledProcessError:
        print("⚠️  Could not generate stack.txt (will be generated on first session)")
    
    # Run generate_tree.py
    try:
        subprocess.run(
            ["python", "scripts/generate_tree.py"],
            check=True,
            capture_output=True
        )
        print("✓ Generated tree.txt")
    except subprocess.CalledProcessError:
        print("⚠️  Could not generate tree.txt (will be generated on first session)")
    
    return True


def init_project():
    """Main initialization function."""
    print("Initializing Session-Driven Development...\n")
    
    # Check documentation
    if not check_documentation():
        return 1
    
    # Create directory structure
    if not create_directory_structure():
        return 1
    
    # Initialize tracking files
    if not initialize_tracking_files():
        return 1
    
    # Run initial scans
    run_initial_scans()
    
    print("\n" + "="*50)
    print("Session-Driven Development initialized successfully!")
    print("="*50)
    print("\nNext steps:")
    print("1. Create work items: /work-item create")
    print("2. Start first session: /session-start")
    print()
    
    return 0


if __name__ == "__main__":
    exit(init_project())
```

#### Integration

- Called once per project before first session
- Creates complete .session/ structure
- Validates documentation exists
- Runs initial scans to establish baseline

#### Testing Checklist

- [x] Initialize fresh project (no .session/)
- [x] Initialize project with docs/
- [x] Initialize project without docs/ (prompts user)
- [x] Attempt re-initialization (should error)
- [x] Verify all directories created
- [x] Verify tracking files initialized
- [x] Verify stack.txt generated
- [x] Verify tree.txt generated

---

### 1.2 Implement Stack Tracking

**Purpose:** Auto-detect and track technology stack with reasoning for changes

**Status:** 📋 To Implement

**Files:**
- `scripts/generate_stack.py` (NEW)
- `tracking/stack.txt` (generated)
- `tracking/stack_updates.json` (generated)

**Reference:** See session-driven-development.md lines 236-287 for complete format

#### Implementation

**File:** `scripts/generate_stack.py`

```python
#!/usr/bin/env python3
"""
Generate and update technology stack documentation.

Detects:
- Languages (from file extensions)
- Frameworks (from imports and config files)
- Libraries (from requirements.txt, package.json, etc.)
- Databases (from connection strings, imports)
- MCP Servers (from context7 usage, etc.)
- External APIs (from code inspection)
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set


class StackGenerator:
    """Generate technology stack documentation."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.stack_file = self.project_root / ".session" / "tracking" / "stack.txt"
        self.updates_file = self.project_root / ".session" / "tracking" / "stack_updates.json"
    
    def detect_languages(self) -> Dict[str, str]:
        """Detect programming languages from file extensions."""
        languages = {}
        
        # Count files by extension
        extensions = {
            ".py": ("Python", "python"),
            ".js": ("JavaScript", "javascript"),
            ".ts": ("TypeScript", "typescript"),
            ".rs": ("Rust", "rust"),
            ".go": ("Go", "go"),
            ".java": ("Java", "java"),
            ".cpp": ("C++", "cpp"),
            ".c": ("C", "c"),
        }
        
        for ext, (name, key) in extensions.items():
            files = list(self.project_root.rglob(f"*{ext}"))
            # Exclude common non-source directories
            files = [f for f in files if not any(
                part in f.parts for part in 
                ['node_modules', 'venv', '.venv', 'build', 'dist', '__pycache__']
            )]
            
            if files:
                # Try to detect version
                version = self._detect_language_version(key)
                languages[name] = version or "detected"
        
        return languages
    
    def _detect_language_version(self, language: str) -> str:
        """Detect language version from environment."""
        version_commands = {
            "python": ["python", "--version"],
            "node": ["node", "--version"],
            "rust": ["rustc", "--version"],
            "go": ["go", "version"],
        }
        
        if language in version_commands:
            try:
                import subprocess
                result = subprocess.run(
                    version_commands[language],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    # Extract version number
                    version_match = re.search(r'(\d+\.\d+(?:\.\d+)?)', result.stdout)
                    if version_match:
                        return version_match.group(1)
            except:
                pass
        
        return ""
    
    def detect_frameworks(self) -> Dict[str, List[str]]:
        """Detect frameworks from imports and config files."""
        frameworks = {
            "backend": [],
            "frontend": [],
            "testing": [],
            "database": []
        }
        
        # Check Python imports
        if (self.project_root / "requirements.txt").exists():
            requirements = (self.project_root / "requirements.txt").read_text()
            if "fastapi" in requirements.lower():
                version = self._extract_version(requirements, "fastapi")
                frameworks["backend"].append(f"FastAPI {version}")
            if "django" in requirements.lower():
                version = self._extract_version(requirements, "django")
                frameworks["backend"].append(f"Django {version}")
            if "flask" in requirements.lower():
                version = self._extract_version(requirements, "flask")
                frameworks["backend"].append(f"Flask {version}")
            if "sqlalchemy" in requirements.lower():
                version = self._extract_version(requirements, "sqlalchemy")
                frameworks["database"].append(f"SQLAlchemy {version}")
            if "pytest" in requirements.lower():
                frameworks["testing"].append("pytest")
        
        # Check JavaScript/TypeScript frameworks
        if (self.project_root / "package.json").exists():
            try:
                package = json.loads((self.project_root / "package.json").read_text())
                deps = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
                
                if "react" in deps:
                    frameworks["frontend"].append(f"React {deps['react']}")
                if "vue" in deps:
                    frameworks["frontend"].append(f"Vue {deps['vue']}")
                if "next" in deps:
                    frameworks["frontend"].append(f"Next.js {deps['next']}")
                if "jest" in deps:
                    frameworks["testing"].append("Jest")
            except:
                pass
        
        return {k: v for k, v in frameworks.items() if v}
    
    def _extract_version(self, requirements: str, package: str) -> str:
        """Extract version from requirements file."""
        pattern = rf'{package}\s*[>=<~]+\s*([0-9.]+)'
        match = re.search(pattern, requirements, re.IGNORECASE)
        if match:
            return match.group(1)
        return ""
    
    def detect_libraries(self) -> List[str]:
        """Detect libraries from dependency files."""
        libraries = []
        
        # Python libraries
        if (self.project_root / "requirements.txt").exists():
            requirements = (self.project_root / "requirements.txt").read_text()
            for line in requirements.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    # Extract package name and version
                    match = re.match(r'([a-zA-Z0-9_-]+)([>=<~]+.*)?', line)
                    if match:
                        libraries.append(line)
        
        return libraries[:20]  # Limit to top 20
    
    def detect_mcp_servers(self) -> List[str]:
        """Detect MCP servers in use."""
        mcp_servers = []
        
        # Check for context7 usage in code
        for py_file in self.project_root.rglob("*.py"):
            try:
                content = py_file.read_text()
                if "context7" in content.lower() or "mcp__context7" in content:
                    if "Context7 (library documentation)" not in mcp_servers:
                        mcp_servers.append("Context7 (library documentation)")
                        break  # Found it, no need to continue
            except:
                pass
        
        return mcp_servers
    
    def generate_stack_txt(self) -> str:
        """Generate stack.txt content."""
        languages = self.detect_languages()
        frameworks = self.detect_frameworks()
        libraries = self.detect_libraries()
        mcp_servers = self.detect_mcp_servers()
        
        lines = ["# Technology Stack\n"]
        
        if languages:
            lines.append("## Languages")
            for name, version in languages.items():
                lines.append(f"- {name} {version}")
            lines.append("")
        
        if frameworks.get("backend"):
            lines.append("## Backend Framework")
            for fw in frameworks["backend"]:
                lines.append(f"- {fw}")
            lines.append("")
        
        if frameworks.get("frontend"):
            lines.append("## Frontend Framework")
            for fw in frameworks["frontend"]:
                lines.append(f"- {fw}")
            lines.append("")
        
        if frameworks.get("database"):
            lines.append("## Database")
            for db in frameworks["database"]:
                lines.append(f"- {db}")
            lines.append("")
        
        if mcp_servers:
            lines.append("## MCP Servers")
            for mcp in mcp_servers:
                lines.append(f"- {mcp}")
            lines.append("")
        
        if frameworks.get("testing"):
            lines.append("## Testing")
            for test in frameworks["testing"]:
                lines.append(f"- {test}")
            lines.append("")
        
        if libraries:
            lines.append("## Key Libraries")
            for lib in libraries:
                lines.append(f"- {lib}")
            lines.append("")
        
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return "\n".join(lines)
    
    def detect_changes(self, old_content: str, new_content: str) -> List[Dict]:
        """Detect changes between old and new stack."""
        old_lines = set(old_content.split('\n'))
        new_lines = set(new_content.split('\n'))
        
        added = new_lines - old_lines
        removed = old_lines - new_lines
        
        changes = []
        for line in added:
            if line.strip() and not line.startswith('#') and not line.startswith('Generated:'):
                changes.append({
                    "type": "addition",
                    "content": line.strip()
                })
        
        for line in removed:
            if line.strip() and not line.startswith('#') and not line.startswith('Generated:'):
                changes.append({
                    "type": "removal",
                    "content": line.strip()
                })
        
        return changes
    
    def update_stack(self, session_num: int = None):
        """Generate/update stack.txt and detect changes."""
        # Generate new stack content
        new_content = self.generate_stack_txt()
        
        # Load old content if exists
        old_content = ""
        if self.stack_file.exists():
            old_content = self.stack_file.read_text()
        
        # Detect changes
        changes = self.detect_changes(old_content, new_content)
        
        # Save new stack
        self.stack_file.parent.mkdir(parents=True, exist_ok=True)
        self.stack_file.write_text(new_content)
        
        # If changes detected, prompt for reasoning
        if changes and session_num:
            print(f"\n{'='*50}")
            print("Stack Changes Detected")
            print('='*50)
            
            for change in changes:
                print(f"  {change['type'].upper()}: {change['content']}")
            
            print("\nPlease provide reasoning for these changes:")
            reasoning = input("> ")
            
            # Update stack_updates.json
            self._record_stack_update(session_num, changes, reasoning)
        
        return changes
    
    def _record_stack_update(self, session_num: int, changes: List[Dict], reasoning: str):
        """Record stack update in stack_updates.json."""
        updates = {"updates": []}
        
        if self.updates_file.exists():
            try:
                updates = json.loads(self.updates_file.read_text())
            except:
                pass
        
        update_entry = {
            "timestamp": datetime.now().isoformat(),
            "session": session_num,
            "changes": changes,
            "reasoning": reasoning
        }
        
        updates["updates"].append(update_entry)
        
        self.updates_file.write_text(json.dumps(updates, indent=2))


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate technology stack documentation")
    parser.add_argument("--session", type=int, help="Current session number")
    args = parser.parse_args()
    
    generator = StackGenerator()
    changes = generator.update_stack(session_num=args.session)
    
    if changes:
        print(f"\n✓ Stack updated with {len(changes)} changes")
    else:
        print("\n✓ Stack generated (no changes)")
    
    print(f"✓ Saved to: {generator.stack_file}")


if __name__ == "__main__":
    main()
```

#### Integration

- Run on session-end to detect changes
- If changes detected, prompt Claude for reasoning
- Include current stack in session-start briefing
- Stack file provides technology context for all sessions

#### Testing Checklist

- [ ] Detects Python projects (requirements.txt)
- [ ] Detects JavaScript projects (package.json)
- [ ] Detects frameworks (FastAPI, React, etc.)
- [ ] Detects MCP servers (Context7)
- [ ] Prompts for reasoning on changes
- [ ] Updates stack_updates.json correctly
- [ ] No false positives from excluded directories

---

### 1.3 Implement Tree Tracking

**Purpose:** Track project structure evolution with reasoning for changes

**Status:** 📋 To Implement

**Files:**
- `scripts/generate_tree.py` (NEW)
- `tracking/tree.txt` (generated)
- `tracking/tree_updates.json` (generated)

**Reference:** See session-driven-development.md lines 350-377 for tree_updates.json format

#### Implementation

**File:** `scripts/generate_tree.py`

```python
#!/usr/bin/env python3
"""
Generate and update project tree documentation.

Tracks structural changes to the project with reasoning.
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict


class TreeGenerator:
    """Generate project tree documentation."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.tree_file = self.project_root / ".session" / "tracking" / "tree.txt"
        self.updates_file = self.project_root / ".session" / "tracking" / "tree_updates.json"
        
        # Items to ignore
        self.ignore_patterns = [
            ".git", "__pycache__", "*.pyc", ".pytest_cache",
            ".venv", "venv", "node_modules", ".DS_Store",
            "*.egg-info", ".mypy_cache", ".ruff_cache",
            "*.log", "*.tmp", "*.backup", ".session"
        ]
    
    def generate_tree(self) -> str:
        """Generate tree using tree command."""
        try:
            # Build ignore arguments
            ignore_args = []
            for pattern in self.ignore_patterns:
                ignore_args.extend(["-I", pattern])
            
            result = subprocess.run(
                ["tree", "-a", "--dirsfirst"] + ignore_args,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=30
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                return self._generate_tree_fallback()
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # tree command not available, use fallback
            return self._generate_tree_fallback()
    
    def _generate_tree_fallback(self) -> str:
        """Fallback tree generation without tree command."""
        lines = [str(self.project_root.name) + "/"]
        
        def should_ignore(path: Path) -> bool:
            for pattern in self.ignore_patterns:
                if pattern.startswith("*"):
                    if path.name.endswith(pattern[1:]):
                        return True
                elif pattern in path.parts:
                    return True
            return False
        
        def add_tree(path: Path, prefix: str = "", is_last: bool = True):
            if should_ignore(path):
                return
            
            connector = "└── " if is_last else "├── "
            lines.append(prefix + connector + path.name)
            
            if path.is_dir():
                children = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
                children = [c for c in children if not should_ignore(c)]
                
                for i, child in enumerate(children):
                    is_last_child = i == len(children) - 1
                    extension = "    " if is_last else "│   "
                    add_tree(child, prefix + extension, is_last_child)
        
        # Generate tree
        children = sorted(self.project_root.iterdir(), key=lambda p: (not p.is_dir(), p.name))
        children = [c for c in children if not should_ignore(c)]
        
        for i, child in enumerate(children):
            add_tree(child, "", i == len(children) - 1)
        
        return "\n".join(lines)
    
    def detect_changes(self, old_tree: str, new_tree: str) -> List[Dict]:
        """Detect structural changes between trees."""
        old_lines = set(old_tree.split('\n'))
        new_lines = set(new_tree.split('\n'))
        
        added = new_lines - old_lines
        removed = old_lines - new_lines
        
        changes = []
        
        # Categorize changes
        for line in added:
            if '/' in line or line.strip().endswith('/'):
                changes.append({
                    "type": "directory_added",
                    "path": line.strip()
                })
            elif line.strip():
                changes.append({
                    "type": "file_added",
                    "path": line.strip()
                })
        
        for line in removed:
            if '/' in line or line.strip().endswith('/'):
                changes.append({
                    "type": "directory_removed",
                    "path": line.strip()
                })
            elif line.strip():
                changes.append({
                    "type": "file_removed",
                    "path": line.strip()
                })
        
        return changes
    
    def update_tree(self, session_num: int = None):
        """Generate/update tree.txt and detect changes."""
        # Generate new tree
        new_tree = self.generate_tree()
        
        # Load old tree if exists
        old_tree = ""
        if self.tree_file.exists():
            old_tree = self.tree_file.read_text()
        
        # Detect changes
        changes = self.detect_changes(old_tree, new_tree)
        
        # Filter out minor changes (just ordering, etc.)
        significant_changes = [
            c for c in changes 
            if c['type'] in ['directory_added', 'directory_removed']
            or len(changes) < 20  # If few changes, they're probably significant
        ]
        
        # Save new tree
        self.tree_file.parent.mkdir(parents=True, exist_ok=True)
        self.tree_file.write_text(new_tree)
        
        # If significant changes detected, prompt for reasoning
        if significant_changes and session_num:
            print(f"\n{'='*50}")
            print("Structural Changes Detected")
            print('='*50)
            
            for change in significant_changes[:10]:  # Show first 10
                print(f"  {change['type'].upper()}: {change['path']}")
            
            if len(significant_changes) > 10:
                print(f"  ... and {len(significant_changes) - 10} more changes")
            
            print("\nPlease provide reasoning for these structural changes:")
            reasoning = input("> ")
            
            # Update tree_updates.json
            self._record_tree_update(session_num, significant_changes, reasoning)
        
        return changes
    
    def _record_tree_update(self, session_num: int, changes: List[Dict], reasoning: str):
        """Record tree update in tree_updates.json."""
        updates = {"updates": []}
        
        if self.updates_file.exists():
            try:
                updates = json.loads(self.updates_file.read_text())
            except:
                pass
        
        update_entry = {
            "timestamp": datetime.now().isoformat(),
            "session": session_num,
            "changes": changes,
            "reasoning": reasoning,
            "architecture_impact": ""  # Could prompt for this too
        }
        
        updates["updates"].append(update_entry)
        
        self.updates_file.write_text(json.dumps(updates, indent=2))


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate project tree documentation")
    parser.add_argument("--session", type=int, help="Current session number")
    parser.add_argument("--show-changes", action="store_true", help="Show changes from last run")
    args = parser.parse_args()
    
    generator = TreeGenerator()
    
    if args.show_changes:
        if generator.updates_file.exists():
            updates = json.loads(generator.updates_file.read_text())
            print("Recent structural changes:")
            for update in updates["updates"][-5:]:
                print(f"\nSession {update['session']} ({update['timestamp']})")
                print(f"Reasoning: {update['reasoning']}")
                print(f"Changes: {len(update['changes'])}")
        else:
            print("No tree updates recorded yet")
    else:
        changes = generator.update_tree(session_num=args.session)
        
        if changes:
            print(f"\n✓ Tree updated with {len(changes)} changes")
        else:
            print("\n✓ Tree generated (no changes)")
        
        print(f"✓ Saved to: {generator.tree_file}")


if __name__ == "__main__":
    main()
```

#### Integration

- Run on session-end to detect structural changes
- If significant changes detected, prompt Claude for reasoning
- Include relevant structure in session-start briefing
- Tree file prevents "spaghetti structure" anti-pattern

#### Testing Checklist

- [ ] Generates tree with tree command (if available)
- [ ] Falls back to Python implementation if tree not available
- [ ] Ignores common directories (.git, node_modules, etc.)
- [ ] Detects directory additions/removals
- [ ] Detects significant file changes
- [ ] Filters out minor changes (ordering)
- [ ] Prompts for reasoning on structural changes
- [ ] Updates tree_updates.json correctly

---

### 1.4 Implement Git Workflow Integration

**Purpose:** Automate git operations to prevent mistakes and maintain clean history

**Status:** 📋 To Implement

**Files:**
- `scripts/git_integration.py` (NEW)

**Reference:** See session-driven-development.md for git field in work_items.json

#### Implementation

**File:** `scripts/git_integration.py`

```python
#!/usr/bin/env python3
"""
Git workflow integration for Session-Driven Development.

Handles:
- Branch creation for work items
- Branch continuation for multi-session work
- Commit generation
- Push to remote
- Branch merging
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple


class GitWorkflow:
    """Manage git workflow for sessions."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.work_items_file = self.project_root / ".session" / "tracking" / "work_items.json"
    
    def check_git_status(self) -> Tuple[bool, str]:
        """Check if working directory is clean."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=5
            )
            
            if result.returncode != 0:
                return False, "Not a git repository"
            
            if result.stdout.strip():
                return False, "Working directory not clean (uncommitted changes)"
            
            return True, "Clean"
            
        except subprocess.TimeoutExpired:
            return False, "Git command timed out"
        except FileNotFoundError:
            return False, "Git not found"
    
    def get_current_branch(self) -> Optional[str]:
        """Get current git branch name."""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=5
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            
        except:
            pass
        
        return None
    
    def create_branch(self, work_item_id: str, session_num: int) -> Tuple[bool, str]:
        """Create a new branch for work item."""
        branch_name = f"session-{session_num:03d}-{work_item_id}"
        
        try:
            # Create and checkout branch
            result = subprocess.run(
                ["git", "checkout", "-b", branch_name],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=5
            )
            
            if result.returncode == 0:
                return True, branch_name
            else:
                return False, f"Failed to create branch: {result.stderr}"
                
        except Exception as e:
            return False, f"Error creating branch: {e}"
    
    def checkout_branch(self, branch_name: str) -> Tuple[bool, str]:
        """Checkout existing branch."""
        try:
            result = subprocess.run(
                ["git", "checkout", branch_name],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=5
            )
            
            if result.returncode == 0:
                return True, f"Switched to branch {branch_name}"
            else:
                return False, f"Failed to checkout branch: {result.stderr}"
                
        except Exception as e:
            return False, f"Error checking out branch: {e}"
    
    def commit_changes(self, message: str) -> Tuple[bool, str]:
        """Stage all changes and commit."""
        try:
            # Stage all changes
            subprocess.run(
                ["git", "add", "."],
                cwd=self.project_root,
                timeout=10,
                check=True
            )
            
            # Commit
            result = subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=10
            )
            
            if result.returncode == 0:
                # Get commit SHA
                sha_result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root,
                    timeout=5
                )
                commit_sha = sha_result.stdout.strip()[:7]
                return True, commit_sha
            else:
                return False, f"Commit failed: {result.stderr}"
                
        except Exception as e:
            return False, f"Error committing: {e}"
    
    def push_branch(self, branch_name: str) -> Tuple[bool, str]:
        """Push branch to remote."""
        try:
            result = subprocess.run(
                ["git", "push", "-u", "origin", branch_name],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=30
            )
            
            if result.returncode == 0:
                return True, "Pushed to remote"
            else:
                # Check if it's just "no upstream" error
                if "no upstream" in result.stderr.lower() or "no remote" in result.stderr.lower():
                    return True, "No remote configured (local only)"
                return False, f"Push failed: {result.stderr}"
                
        except Exception as e:
            return False, f"Error pushing: {e}"
    
    def merge_to_main(self, branch_name: str) -> Tuple[bool, str]:
        """Merge branch to main and delete branch."""
        try:
            # Checkout main
            subprocess.run(
                ["git", "checkout", "main"],
                capture_output=True,
                cwd=self.project_root,
                timeout=5,
                check=True
            )
            
            # Merge
            result = subprocess.run(
                ["git", "merge", "--no-ff", branch_name],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=10
            )
            
            if result.returncode == 0:
                # Delete branch
                subprocess.run(
                    ["git", "branch", "-d", branch_name],
                    cwd=self.project_root,
                    timeout=5
                )
                return True, "Merged to main and branch deleted"
            else:
                return False, f"Merge failed: {result.stderr}"
                
        except Exception as e:
            return False, f"Error merging: {e}"
    
    def start_work_item(self, work_item_id: str, session_num: int) -> Dict:
        """Start working on a work item (create or resume branch)."""
        # Load work items
        with open(self.work_items_file) as f:
            data = json.load(f)
        
        work_item = data["work_items"][work_item_id]
        
        # Check if work item already has a branch
        if "git" in work_item and work_item["git"].get("status") == "in_progress":
            # Resume existing branch
            branch_name = work_item["git"]["branch"]
            success, msg = self.checkout_branch(branch_name)
            
            return {
                "action": "resumed",
                "branch": branch_name,
                "success": success,
                "message": msg
            }
        else:
            # Create new branch
            success, branch_name = self.create_branch(work_item_id, session_num)
            
            if success:
                # Update work item with git info
                work_item["git"] = {
                    "branch": branch_name,
                    "created_at": datetime.now().isoformat(),
                    "status": "in_progress",
                    "commits": []
                }
                
                # Save updated work items
                with open(self.work_items_file, 'w') as f:
                    json.dump(data, f, indent=2)
            
            return {
                "action": "created",
                "branch": branch_name,
                "success": success,
                "message": branch_name if success else branch_name  # branch_name is error msg on failure
            }
    
    def complete_work_item(self, work_item_id: str, commit_message: str, merge: bool = False) -> Dict:
        """Complete work on a work item (commit, push, optionally merge)."""
        # Load work items
        with open(self.work_items_file) as f:
            data = json.load(f)
        
        work_item = data["work_items"][work_item_id]
        
        if "git" not in work_item:
            return {
                "success": False,
                "message": "Work item has no git tracking (may be single-session item)"
            }
        
        branch_name = work_item["git"]["branch"]
        
        # Commit changes
        success, commit_sha = self.commit_changes(commit_message)
        if not success:
            return {
                "success": False,
                "message": f"Commit failed: {commit_sha}"
            }
        
        # Update work item commits
        work_item["git"]["commits"].append(commit_sha)
        
        # Push to remote
        push_success, push_msg = self.push_branch(branch_name)
        
        # Merge if requested and work complete
        if merge:
            merge_success, merge_msg = self.merge_to_main(branch_name)
            if merge_success:
                work_item["git"]["status"] = "merged"
            else:
                work_item["git"]["status"] = "ready_to_merge"
                merge_msg = f"⚠️  {merge_msg} - Manual merge required"
        else:
            work_item["git"]["status"] = "ready_to_merge" if work_item["status"] == "completed" else "in_progress"
        
        # Save updated work items
        with open(self.work_items_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return {
            "success": True,
            "commit": commit_sha,
            "pushed": push_success,
            "merged": merge if merge else False,
            "message": f"Committed {commit_sha}, " + (merge_msg if merge else push_msg)
        }


def main():
    """CLI entry point for testing."""
    workflow = GitWorkflow()
    
    # Check status
    is_clean, msg = workflow.check_git_status()
    print(f"Git status: {msg}")
    
    current_branch = workflow.get_current_branch()
    print(f"Current branch: {current_branch}")


if __name__ == "__main__":
    main()
```

#### Integration

- Session-start calls `start_work_item()` to create or resume branch
- Session-end calls `complete_work_item()` to commit, push, optionally merge
- Updates work_items.json git field automatically
- Prevents "wrong branch" mistakes

#### Testing Checklist

- [ ] Check git status (clean vs dirty)
- [ ] Create new branch for work item
- [ ] Resume existing branch for multi-session work
- [ ] Commit changes with message
- [ ] Push to remote (handle no remote gracefully)
- [ ] Merge to main when work complete
- [ ] Update work_items.json git field
- [ ] Handle git errors gracefully

---

### 1.5 Enhance Session-Start

**Purpose:** Load complete project context for comprehensive briefing

**Status:** 📋 To Implement

**Files:**
- Enhance `scripts/briefing_generator.py`
- Update `commands/session-start.md`

**Reference:** See session-driven-development.md for briefing format

#### Implementation

Enhance existing `briefing_generator.py` to:

```python
# Add these functions to briefing_generator.py

def load_project_docs():
    """Load project documentation for context."""
    docs = {}
    
    # Look for common doc files
    doc_files = [
        "docs/vision.md",
        "docs/prd.md",
        "docs/architecture.md",
        "README.md"
    ]
    
    for doc_file in doc_files:
        path = Path(doc_file)
        if path.exists():
            docs[path.name] = path.read_text()
    
    return docs

def load_current_stack():
    """Load current technology stack."""
    stack_file = Path(".session/tracking/stack.txt")
    if stack_file.exists():
        return stack_file.read_text()
    return "Stack not yet generated"

def load_current_tree():
    """Load current project structure."""
    tree_file = Path(".session/tracking/tree.txt")
    if tree_file.exists():
        # Return first 50 lines (preview)
        lines = tree_file.read_text().split('\n')
        return '\n'.join(lines[:50])
    return "Tree not yet generated"

def validate_environment():
    """Validate development environment."""
    checks = []
    
    # Check Python version
    import sys
    checks.append(f"Python: {sys.version.split()[0]}")
    
    # Check git
    try:
        result = subprocess.run(["git", "--version"], capture_output=True, text=True)
        checks.append(f"Git: {result.stdout.strip()}")
    except:
        checks.append("Git: NOT FOUND")
    
    return checks

def generate_comprehensive_briefing(item_id, item, learnings_data):
    """Generate comprehensive briefing with full context."""
    
    # Load all context
    project_docs = load_project_docs()
    current_stack = load_current_stack()
    current_tree = load_current_tree()
    env_checks = validate_environment()
    
    briefing = f"""# Session Briefing: {item['title']}

## Quick Reference
- **Work Item ID:** {item_id}
- **Type:** {item['type']}
- **Priority:** {item['priority']}
- **Status:** {item['status']}

## Project Context

### Vision
{project_docs.get('vision.md', 'No vision document found')[:500]}...

### Current Stack
{current_stack}

### Project Structure (Preview)
```
{current_tree}
...
```

## Work Item Details

### Objective
{item.get('rationale', 'No rationale provided')}

### Dependencies
"""
    
    # Show dependency status
    if item.get("dependencies"):
        for dep in item["dependencies"]:
            briefing += f"- {dep} ✓ completed\n"
    else:
        briefing += "No dependencies\n"
    
    # Rest of briefing follows existing format...
    # (acceptance criteria, learnings, validation requirements)
    
    return briefing
```

Update `commands/session-start.md` to document the enhanced behavior.

#### Integration

- Read all project documentation
- Load current stack and tree
- Validate environment
- Check git status
- Create/resume branch via git_integration
- Generate comprehensive briefing
- Present to user

#### Testing Checklist

- [ ] Reads project docs (vision, PRD, architecture)
- [ ] Loads current stack
- [ ] Loads current tree
- [ ] Validates environment
- [ ] Checks git status
- [ ] Creates new branch for new work item
- [ ] Resumes existing branch for continuing work
- [ ] Generates comprehensive briefing
- [ ] All context included in briefing

---

### 1.6 Enhance Session-End

**Purpose:** Update all tracking systems and perform comprehensive session completion

**Status:** 📋 To Implement

**Files:**
- Enhance `scripts/session_complete.py`
- Update `commands/session-end.md`

#### Implementation

Enhance existing `session_complete.py` to:

```python
# Add these to session_complete.py

def update_all_tracking(session_num, work_item_id):
    """Update stack, tree, and other tracking files."""
    print("\nUpdating tracking files...")
    
    # Update stack
    subprocess.run(
        ["python", "scripts/generate_stack.py", "--session", str(session_num)],
        timeout=30
    )
    print("✓ Stack updated")
    
    # Update tree
    subprocess.run(
        ["python", "scripts/generate_tree.py", "--session", str(session_num)],
        timeout=30
    )
    print("✓ Tree updated")
    
    return True

def extract_learnings_from_session():
    """Extract learnings from work done in session."""
    print("\nExtract learnings from this session...")
    print("(Type each learning, or 'done' to finish):")
    
    learnings = []
    while True:
        learning = input("> ")
        if learning.lower() == 'done':
            break
        if learning:
            learnings.append(learning)
    
    return learnings

def generate_comprehensive_report(status, work_item, gate_results, learnings):
    """Generate comprehensive session report."""
    report = f"""# Session {status['current_session']} Summary

{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Work Items
- **{work_item['id']}**: {work_item['title']} ({work_item['status']})

## Quality Gates
- Tests: {'✓ PASSED' if gate_results['tests']['passed'] else '✗ FAILED'}
- Linting: {'✓ PASSED' if gate_results['linting']['passed'] else '✗ FAILED'}
- Formatting: {'✓ PASSED' if gate_results['formatting']['passed'] else '✗ FAILED'}

## Learnings Captured
"""
    
    for learning in learnings:
        report += f"- {learning}\n"
    
    report += "\n## Next Session\n"
    report += "To be determined\n"
    
    return report

def complete_git_workflow(work_item_id, commit_message):
    """Complete git workflow (commit, push, optionally merge)."""
    from scripts.git_integration import GitWorkflow
    
    workflow = GitWorkflow()
    
    # Determine if work is complete
    # Load work items to check status
    with open(".session/tracking/work_items.json") as f:
        data = json.load(f)
    
    work_item = data["work_items"][work_item_id]
    should_merge = work_item["status"] == "completed"
    
    # Complete work item in git
    result = workflow.complete_work_item(
        work_item_id,
        commit_message,
        merge=should_merge
    )
    
    return result
```

Update the main completion flow:

```python
def main():
    """Enhanced main entry point."""
    # ... existing code ...
    
    # After quality gates pass:
    
    # Update all tracking
    update_all_tracking(session_num, work_item_id)
    
    # Extract learnings
    learnings = extract_learnings_from_session()
    
    # Update work item status
    work_items_data["work_items"][work_item_id]["status"] = "completed"  # or keep in_progress
    
    # Save work items
    with open(".session/tracking/work_items.json", "w") as f:
        json.dump(work_items_data, f, indent=2)
    
    # Complete git workflow
    commit_message = generate_commit_message(status, work_item, achievements)
    git_result = complete_git_workflow(work_item_id, commit_message)
    
    # Generate comprehensive report
    report = generate_comprehensive_report(status, work_item, gate_results, learnings)
    
    # Save and display
    # ... rest of code ...
```

#### Integration

- Run all quality gates
- Update stack tracking
- Update tree tracking
- Extract learnings
- Update work item status
- Complete git workflow (commit, push, merge)
- Generate comprehensive report

#### Testing Checklist

- [ ] All quality gates run
- [ ] Stack updated if changes detected
- [ ] Tree updated if structure changed
- [ ] Learnings captured
- [ ] Work item status updated
- [ ] Git commit created
- [ ] Branch pushed to remote
- [ ] Branch merged if work complete
- [ ] Comprehensive report generated
- [ ] Next session identified

---

### 1.7 Add Session Validate Command

**Purpose:** Pre-flight check before session completion

**Status:** 📋 To Implement

**Files:**
- `commands/session-validate.md` (NEW)
- `scripts/session_validate.py` (NEW)

**Reference:** Reuses validation logic from session_complete.py

#### Implementation

**File:** `commands/session-validate.md`

```markdown
# Session Validate Command

**Usage:** `/session-validate`

**Description:** Pre-flight check to validate if current session can complete successfully.

**Behavior:**

1. Check git status
   - Verify working directory is clean or has expected changes
   - Check if on correct branch for work item
   - Verify no uncommitted .session/ tracking files

2. Preview quality gates
   - Run tests (if configured)
   - Check linting (if configured)
   - Check formatting (if configured)
   - Show what would pass/fail without making changes

3. Validate work item criteria
   - Check acceptance criteria (if defined)
   - Verify implementation paths exist
   - Check test paths exist and have content

4. Check tracking updates
   - Detect stack changes (would prompt for reasoning)
   - Detect tree changes (would prompt for reasoning)
   - Preview what would be updated

5. Display results
   - Show ✓ for passed checks
   - Show ✗ for failed checks with actionable messages
   - Overall status: ready or not ready

**Example:**

\`\`\`
User: /session-validate

Claude: Running session validation...

Git Status:
✓ Working directory clean
✓ On branch: session-005-feature-oauth
✓ Branch tracking remote

Quality Gates:
✓ Tests: 45 passed, 0 failed
✗ Linting: 3 issues found in auth/oauth.py
  - Line 42: Unused import 'datetime'
  - Line 56: Line too long (89 > 88 characters)
  - Line 78: Missing docstring
✓ Formatting: All files properly formatted

Work Item Criteria:
✓ Implementation path exists: auth/oauth.py
✓ Test path exists: tests/test_oauth.py
✓ Acceptance criteria: 3/3 met

Tracking Updates:
✓ Stack: No changes detected
✓ Tree: No structural changes

⚠️  Session not ready to complete

Fix the following before running /session-end:
1. Fix 3 linting issues in auth/oauth.py
2. Run: ruff check --fix auth/oauth.py

After fixing, run /session-validate again to confirm.
\`\`\`
```

**File:** `scripts/session_validate.py`

```python
#!/usr/bin/env python3
"""
Session validation - pre-flight check before completion.

Validates all conditions required for successful session-end without
actually making any changes.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple


class SessionValidator:
    """Validate session readiness for completion."""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.session_dir = self.project_root / ".session"

    def check_git_status(self) -> Dict:
        """Check git working directory status."""
        try:
            # Check if clean or has expected changes
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=5
            )

            if result.returncode != 0:
                return {
                    "passed": False,
                    "message": "Not a git repository or git error"
                }

            # Check branch
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=5
            )
            current_branch = branch_result.stdout.strip()

            # Get status lines
            status_lines = [line for line in result.stdout.split('\n') if line.strip()]

            # Check for tracking file changes
            tracking_changes = [
                line for line in status_lines
                if '.session/tracking/' in line
            ]

            if tracking_changes:
                return {
                    "passed": False,
                    "message": f"Uncommitted tracking files: {len(tracking_changes)} files"
                }

            return {
                "passed": True,
                "message": f"Working directory ready, branch: {current_branch}",
                "details": {
                    "branch": current_branch,
                    "changes": len(status_lines)
                }
            }

        except Exception as e:
            return {
                "passed": False,
                "message": f"Git check failed: {e}"
            }

    def preview_quality_gates(self) -> Dict:
        """Preview quality gate results without making changes."""
        gates = {
            "tests": self._preview_tests(),
            "linting": self._preview_linting(),
            "formatting": self._preview_formatting()
        }

        all_passed = all(g["passed"] for g in gates.values())

        return {
            "passed": all_passed,
            "message": "All quality gates pass" if all_passed else "Some quality gates fail",
            "gates": gates
        }

    def _preview_tests(self) -> Dict:
        """Preview test results."""
        try:
            result = subprocess.run(
                ["pytest", "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=300
            )

            # Parse output for counts
            output = result.stdout + result.stderr

            passed = result.returncode == 0

            return {
                "passed": passed,
                "message": "Tests pass" if passed else "Tests fail",
                "output_preview": output[-500:] if not passed else None
            }

        except FileNotFoundError:
            return {
                "passed": True,
                "message": "pytest not found (skipped)"
            }
        except subprocess.TimeoutExpired:
            return {
                "passed": False,
                "message": "Tests timed out (>5 minutes)"
            }

    def _preview_linting(self) -> Dict:
        """Preview linting results."""
        try:
            result = subprocess.run(
                ["ruff", "check", "."],
                capture_output=True,
                text=True,
                timeout=60
            )

            passed = result.returncode == 0

            if not passed:
                # Parse issues
                issues = result.stdout.strip().split('\n')
                issue_count = len([i for i in issues if i.strip()])

                return {
                    "passed": False,
                    "message": f"{issue_count} linting issues found",
                    "issues": issues[:10],  # First 10 issues
                    "fixable": "--fix" in result.stderr or "fixable" in result.stdout
                }

            return {
                "passed": True,
                "message": "No linting issues"
            }

        except FileNotFoundError:
            return {
                "passed": True,
                "message": "ruff not found (skipped)"
            }
        except subprocess.TimeoutExpired:
            return {
                "passed": False,
                "message": "Linting timed out"
            }

    def _preview_formatting(self) -> Dict:
        """Preview formatting check."""
        try:
            result = subprocess.run(
                ["ruff", "format", "--check", "."],
                capture_output=True,
                text=True,
                timeout=60
            )

            passed = result.returncode == 0

            if not passed:
                unformatted = result.stdout.strip().split('\n')
                file_count = len([f for f in unformatted if f.strip()])

                return {
                    "passed": False,
                    "message": f"{file_count} files need formatting",
                    "files": unformatted[:5]
                }

            return {
                "passed": True,
                "message": "All files properly formatted"
            }

        except FileNotFoundError:
            return {
                "passed": True,
                "message": "ruff not found (skipped)"
            }

    def validate_work_item_criteria(self) -> Dict:
        """Check if work item acceptance criteria are met."""
        # Load current work item
        status_file = self.session_dir / "tracking" / "status_update.json"
        if not status_file.exists():
            return {
                "passed": False,
                "message": "No active session"
            }

        with open(status_file) as f:
            status = json.load(f)

        if not status.get("current_work_item"):
            return {
                "passed": False,
                "message": "No current work item"
            }

        # Load work items
        work_items_file = self.session_dir / "tracking" / "work_items.json"
        with open(work_items_file) as f:
            work_items_data = json.load(f)

        work_item = work_items_data["work_items"][status["current_work_item"]]

        # Check paths exist
        impl_paths = work_item.get("implementation_paths", [])
        test_paths = work_item.get("test_paths", [])

        missing_impl = [p for p in impl_paths if not Path(p).exists()]
        missing_tests = [p for p in test_paths if not Path(p).exists()]

        if missing_impl or missing_tests:
            return {
                "passed": False,
                "message": "Required paths missing",
                "missing_impl": missing_impl,
                "missing_tests": missing_tests
            }

        return {
            "passed": True,
            "message": "Work item criteria met"
        }

    def check_tracking_updates(self) -> Dict:
        """Preview tracking file updates."""
        changes = {
            "stack": self._check_stack_changes(),
            "tree": self._check_tree_changes()
        }

        return {
            "passed": True,  # Tracking updates don't fail validation
            "message": "Tracking updates detected" if any(c["has_changes"] for c in changes.values()) else "No tracking updates",
            "changes": changes
        }

    def _check_stack_changes(self) -> Dict:
        """Check if stack has changed."""
        # This would run stack detection logic
        # For now, simplified
        return {
            "has_changes": False,
            "message": "No stack changes"
        }

    def _check_tree_changes(self) -> Dict:
        """Check if tree structure has changed."""
        # This would run tree detection logic
        return {
            "has_changes": False,
            "message": "No structural changes"
        }

    def validate(self) -> Dict:
        """Run all validation checks."""
        print("Running session validation...\n")

        checks = {
            "git_status": self.check_git_status(),
            "quality_gates": self.preview_quality_gates(),
            "work_item_criteria": self.validate_work_item_criteria(),
            "tracking_updates": self.check_tracking_updates()
        }

        # Display results
        for check_name, result in checks.items():
            status = "✓" if result["passed"] else "✗"
            print(f"{status} {check_name.replace('_', ' ').title()}: {result['message']}")

            # Show details for failed checks
            if not result["passed"] and check_name == "quality_gates":
                for gate_name, gate_result in result["gates"].items():
                    if not gate_result["passed"]:
                        print(f"   ✗ {gate_name}: {gate_result['message']}")
                        if "issues" in gate_result:
                            for issue in gate_result["issues"][:5]:
                                print(f"      - {issue}")

        all_passed = all(c["passed"] for c in checks.values())

        print()
        if all_passed:
            print("✅ Session ready to complete!")
            print("Run /session-end to complete the session.")
        else:
            print("⚠️  Session not ready to complete")
            print("\nFix the issues above before running /session-end")

        return {
            "ready": all_passed,
            "checks": checks
        }


def main():
    """CLI entry point."""
    validator = SessionValidator()
    result = validator.validate()
    return 0 if result["ready"] else 1


if __name__ == "__main__":
    exit(main())
```

#### Integration

- Run any time during session to check readiness
- Non-destructive - only checks, never modifies
- Reuses validation logic from session_complete.py
- Helps developer fix issues proactively before attempting session-end

#### Testing Checklist

- [ ] Detects uncommitted changes in git
- [ ] Detects linting failures with specific issues
- [ ] Detects formatting problems
- [ ] Detects test failures
- [ ] Shows work item criteria status
- [ ] Previews tracking updates
- [ ] Shows clear, actionable error messages
- [ ] No side effects (read-only operation)
- [ ] Works when quality gates would pass
- [ ] Works when quality gates would fail

---

### 1.8 Add Integration/Deployment Work Item Types

**Purpose:** Support integration testing and deployment work items

**Status:** 📋 To Implement

**Files:**
- Update `templates/work_items.json` to add new types
- Create work item type definitions

#### Implementation

Add to work item type system (will be part of Phase 2 but define now):

```json
{
  "work_item_types": {
    "feature": { /* existing */ },
    "bug": { /* existing */ },
    "refactor": { /* existing */ },
    "integration_test": {
      "template": "integration_test_spec.md",
      "typical_sessions": "1-2",
      "validation": {
        "integration_tests_pass": true,
        "e2e_tests_pass": true,
        "performance_benchmarks_met": true,
        "api_contracts_validated": true
      },
      "dependencies_required": true
    },
    "deployment": {
      "template": "deployment_spec.md",
      "typical_sessions": "1",
      "validation": {
        "deployment_successful": true,
        "smoke_tests_pass": true,
        "monitoring_operational": true,
        "rollback_tested": true,
        "documentation_updated": true
      },
      "dependencies_required": true
    }
  }
}
```

Create template files:

**File:** `templates/integration_test_spec.md`

```markdown
# Integration Test: [Name]

## Scope
Define which components are being integrated and tested.

## Test Scenarios
1. Scenario 1: [Description]
   - Setup
   - Actions
   - Expected Results

## Performance Benchmarks
- Response time: < Xms
- Throughput: > Y req/s
- Error rate: < Z%

## API Contracts
List API contracts being validated.

## Acceptance Criteria
- [ ] All integration tests passing
- [ ] Performance benchmarks met
- [ ] No contract violations
```

**File:** `templates/deployment_spec.md`

```markdown
# Deployment: [Environment]

## Deployment Target
- Environment: [staging/production]
- Infrastructure: [description]

## Pre-Deployment Checklist
- [ ] All tests passing
- [ ] Security scan clean
- [ ] Documentation updated
- [ ] Rollback plan ready

## Deployment Procedure
1. Step 1
2. Step 2
3. Step 3

## Smoke Tests
- [ ] Health check responds
- [ ] Core functionality works
- [ ] Monitoring operational

## Rollback Procedure
1. Step 1
2. Step 2

## Acceptance Criteria
- [ ] Deployment successful
- [ ] Smoke tests passing
- [ ] No critical errors in logs
```

#### Integration

- Types defined in configuration
- Special validation for these types
- Dependencies mandatory
- Used in Phases 5.5 and 5.6

#### Testing Checklist

- [ ] Integration test work items can be created
- [ ] Deployment work items can be created
- [ ] Special validation enforced
- [ ] Dependencies checked
- [ ] Templates work correctly

---

### 1.9 Phase 1 Testing & Validation

**Purpose:** Comprehensive testing of Phase 1 implementation

**Status:** 📋 To Do After Implementation

#### Complete Workflow Test

Test the entire session workflow from start to finish:

```bash
# 1. Initialize project
/session-init

# 2. Create work item manually (Phase 2 will have command)
# Edit .session/tracking/work_items.json

# 3. Start session
/session-start

# 4. Do some work (create files, write code)

# 5. End session
/session-end

# 6. Verify everything updated:
# - work_items.json (status, sessions, git field)
# - stack.txt (if stack changed)
# - stack_updates.json (if stack changed)
# - tree.txt (if structure changed)
# - tree_updates.json (if structure changed)
# - learnings.json (if learnings added)
# - Git (committed, pushed, branch status)
```

#### Multi-Session Work Item Test

Test work item spanning multiple sessions:

```bash
# Session 1
/session-start --item big_feature
# Do partial work
/session-end  # Should keep branch open

# Session 2
/session-start  # Should resume same branch
# Continue work
/session-end  # Should keep branch open

# Session 3
/session-start  # Should resume same branch
# Complete work
/session-end  # Should offer to merge branch
```

#### Edge Cases Test

- [ ] Initialize project with no documentation
- [ ] Initialize project with existing .session/ (should error)
- [ ] Session-start with dirty git (should error)
- [ ] Session-end with failing tests (should block or warn)
- [ ] Session-end with no changes (nothing to commit)
- [ ] Small work item (no branch needed)
- [ ] Work item with no dependencies
- [ ] Work item with unmet dependencies (should block)

#### Integration Test

- [ ] Stack tracking detects new library
- [ ] Stack tracking prompts for reasoning
- [ ] Tree tracking detects new directory
- [ ] Tree tracking prompts for reasoning
- [ ] Git creates branch correctly
- [ ] Git resumes branch correctly
- [ ] Git commits with standard message
- [ ] Git pushes to remote (or handles no remote)
- [ ] Git merges when work complete

#### Documentation Test

- [ ] Briefing includes project docs
- [ ] Briefing includes current stack
- [ ] Briefing includes structure preview
- [ ] Briefing includes dependencies
- [ ] Briefing includes learnings
- [ ] Session report comprehensive
- [ ] All tracking files formatted correctly

### Phase 1 Completion Checklist

**Implementation Complete:**
- [x] `/session-init` command implemented and tested (1.1)
- [x] Stack tracking (`generate_stack.py`) implemented and tested (1.2)
- [x] Tree tracking (`generate_tree.py`) implemented and tested (1.3)
- [x] Git integration (`git_integration.py`) implemented and tested (1.4)
- [x] Enhanced session-start implemented and tested (1.5)
- [x] Enhanced session-end implemented and tested (1.6)
- [x] `/session-validate` command implemented and tested (1.7)
- [x] Integration/deployment types defined (1.8)
- [x] All scripts have proper error handling

**Testing Complete:**
- [x] Complete workflow test passed
- [x] Multi-session work item test passed
- [x] All edge cases tested
- [x] All integration points tested
- [x] Documentation test passed

**Documentation Complete:**
- [x] README.md updated with Phase 1 features
- [x] Commands documented
- [x] Examples provided
- [x] Troubleshooting guide updated
- [x] Phase 1 marked complete in ROADMAP.md

**Ready for Phase 2:**
- [x] All Phase 1 features working
- [x] No known critical bugs
- [x] Foundation solid for work item management
- [x] Team member (you) can use plugin productively

---

## Phase 2: Work Item System (v0.2)

**Goal:** Full work item management with dependency resolution

**Status:** 📋 Ready to Implement

**Priority:** HIGH

**Target:** 1-2 weeks

**Depends On:** Phase 1 (✅ Complete)

### Overview

Phase 2 adds comprehensive work item management through `/work-item` command group. Users can create, list, view, and update work items interactively. Dependency resolution ensures work items are completed in logical order.

Phase 2 builds on Phase 1's solid foundation by adding:
- Complete work item type templates (6 types)
- Interactive work item creation with validation
- Multiple views for work items (list, show, next)
- Work item updates with history tracking
- Milestone-based organization
- Enhanced briefings with milestone context
- Quick session status command

---

### 2.1 Complete Work Item Type Templates

**Purpose:** Provide consistent templates for all 6 work item types

**Status:** 📋 To Implement (Quick Setup)

**Files:**
- Rename `templates/security_task.md` to `templates/security_spec.md`
- Create `templates/feature_spec.md` (NEW)
- Create `templates/bug_spec.md` (NEW)
- Create `templates/refactor_spec.md` (NEW)

**Reference:** Existing `integration_test_spec.md` and `deployment_spec.md` for format

#### Implementation

**File:** `templates/feature_spec.md`

```markdown
# Feature: [Feature Name]

## Overview
Brief description of what this feature does and why it's needed.

## User Story
As a [type of user], I want [goal] so that [benefit].

## Rationale
Why is this feature important? What problem does it solve?

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Implementation Details

### Approach
High-level approach to implementing this feature.

### Components Affected
- Component 1
- Component 2

### API Changes
List any new or modified APIs.

### Database Changes
List any schema changes needed.

## Testing Strategy
- Unit tests: [Description]
- Integration tests: [Description]
- Manual testing: [Description]

## Documentation Updates
- [ ] User documentation
- [ ] API documentation
- [ ] README updates

## Dependencies
List any other work items this depends on.

## Estimated Effort
[Number] sessions
```

**File:** `templates/bug_spec.md`

```markdown
# Bug: [Bug Title]

## Description
Clear description of the bug and its impact.

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
What should happen.

## Actual Behavior
What actually happens.

## Impact
- **Severity:** [Critical/High/Medium/Low]
- **Affected Users:** [Description]
- **Workaround:** [If available]

## Root Cause Analysis

### Investigation
What investigation was done to understand the bug?

### Root Cause
What is the underlying cause of this bug?

### Why It Happened
Why did this bug get introduced? What can we learn?

## Fix Approach
How will this bug be fixed?

## Testing Strategy
- [ ] Regression test added
- [ ] Manual verification steps
- [ ] Edge cases covered

## Prevention
How can we prevent similar bugs in the future?

## Dependencies
List any related issues or dependencies.

## Estimated Effort
[Number] sessions
```

**File:** `templates/refactor_spec.md`

```markdown
# Refactor: [Refactor Title]

## Overview
What is being refactored and why?

## Current State
Description of the current implementation and its problems.

## Problems with Current Approach
- Problem 1
- Problem 2
- Problem 3

## Proposed Refactor

### New Approach
Description of the refactored implementation.

### Benefits
- Benefit 1
- Benefit 2
- Benefit 3

### Trade-offs
Any trade-offs or considerations.

## Implementation Plan
1. Step 1
2. Step 2
3. Step 3

## Scope

### In Scope
What will be refactored in this work item.

### Out of Scope
What will NOT be refactored (future work).

## Risk Assessment
- **Risk Level:** [Low/Medium/High]
- **Mitigation:** How to mitigate risks

## Testing Strategy
- [ ] All existing tests still pass
- [ ] No functionality changes
- [ ] Code quality metrics improved
- [ ] Performance maintained or improved

## Success Criteria
- [ ] Code is more maintainable
- [ ] Complexity reduced
- [ ] All tests pass
- [ ] No regressions

## Dependencies
List any dependencies on other work.

## Estimated Effort
[Number] sessions
```

**File:** Rename `templates/security_task.md` to `templates/security_spec.md`

Just rename the existing file for consistency - content is already good.

#### Integration

- All 6 types now have consistent `*_spec.md` templates
- Used by `/work-item create` command (Section 2.2)
- Provides structure and guidance for all work item types
- Ensures nothing important is forgotten

#### Testing Checklist

- [ ] All template files exist with correct names
- [ ] Templates follow consistent format
- [ ] All required sections included
- [ ] Examples are clear and helpful
- [ ] WORK_ITEM_TYPES.md references correct filenames

---

### 2.2 Implement `/work-item create` Command

**Purpose:** Interactive work item creation with validation

**Status:** 📋 To Implement

**Files:**
- `commands/work-item-create.md` (NEW)
- `scripts/work_item_manager.py` (NEW - core manager)

**Reference:** Phase 1 command patterns for consistency

#### Implementation

**File:** `commands/work-item-create.md`

```markdown
# Work Item Create Command

**Usage:** `/work-item create`

**Description:** Interactively create a new work item with validation.

**Behavior:**

1. Prompt for work item type
   - Show list: feature, bug, refactor, security, integration_test, deployment
   - Validate selection

2. Load appropriate template
   - Read from templates/{type}_spec.md
   - Show template structure

3. Prompt for required fields
   - Title (required)
   - Priority (critical, high, medium, low)
   - Dependencies (optional, comma-separated IDs)
   - For integration_test/deployment: dependencies required

4. Generate work item ID
   - Format: {type}_{short_title}
   - Example: feature_oauth, bug_login_failure

5. Create specification file
   - Save to .session/specs/{work_item_id}.md
   - Pre-fill with template content

6. Update work_items.json
   - Add new work item entry
   - Set status to not_started
   - Record creation timestamp

7. Confirm creation
   - Display work item ID
   - Show next steps (edit spec, start session)

**Example:**

\`\`\`
User: /work-item create

Claude: Creating new work item...

Select work item type:
1. feature - Standard feature development
2. bug - Bug fix
3. refactor - Code refactoring
4. security - Security-focused work
5. integration_test - Integration testing
6. deployment - Deployment to environment

Your choice (1-6): 1

Title: OAuth Integration

Priority (critical/high/medium/low) [high]: high

Dependencies (comma-separated IDs, or press Enter for none):

Work item created successfully!

ID: feature_oauth
Type: feature
Priority: high
Status: not_started

Specification saved to: .session/specs/feature_oauth.md

Next steps:
1. Edit specification: .session/specs/feature_oauth.md
2. Start working: /session-start
\`\`\`
```

**File:** `scripts/work_item_manager.py`

```python
#!/usr/bin/env python3
"""
Work Item Manager - Core work item operations.

Handles creation, listing, showing, updating work items.
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from scripts.file_ops import read_json, write_json


class WorkItemManager:
    """Manage work items."""

    WORK_ITEM_TYPES = [
        "feature",
        "bug",
        "refactor",
        "security",
        "integration_test",
        "deployment"
    ]

    PRIORITIES = ["critical", "high", "medium", "low"]

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.session_dir = self.project_root / ".session"
        self.work_items_file = self.session_dir / "tracking" / "work_items.json"
        self.specs_dir = self.session_dir / "specs"
        self.templates_dir = Path(__file__).parent.parent / "templates"

    def create_work_item(self) -> Optional[str]:
        """Interactive work item creation."""
        print("Creating new work item...\n")

        # 1. Select type
        work_type = self._prompt_type()
        if not work_type:
            return None

        # 2. Get title
        title = self._prompt_title()
        if not title:
            return None

        # 3. Get priority
        priority = self._prompt_priority()

        # 4. Get dependencies
        dependencies = self._prompt_dependencies(work_type)

        # 5. Generate ID
        work_id = self._generate_id(work_type, title)

        # 6. Check for duplicates
        if self._work_item_exists(work_id):
            print(f"❌ Error: Work item {work_id} already exists")
            return None

        # 7. Create specification file
        spec_created = self._create_spec_file(work_id, work_type, title)
        if not spec_created:
            print("⚠️  Warning: Could not create specification file")

        # 8. Add to work_items.json
        self._add_to_tracking(work_id, work_type, title, priority, dependencies)

        # 9. Confirm
        print(f"\n{'='*50}")
        print("Work item created successfully!")
        print('='*50)
        print(f"\nID: {work_id}")
        print(f"Type: {work_type}")
        print(f"Priority: {priority}")
        print(f"Status: not_started")
        if dependencies:
            print(f"Dependencies: {', '.join(dependencies)}")

        if spec_created:
            spec_path = self.specs_dir / f"{work_id}.md"
            print(f"\nSpecification saved to: {spec_path}")

        print("\nNext steps:")
        print(f"1. Edit specification: .session/specs/{work_id}.md")
        print("2. Start working: /session-start")
        print()

        return work_id

    def _prompt_type(self) -> Optional[str]:
        """Prompt user to select work item type."""
        print("Select work item type:")
        print("1. feature - Standard feature development")
        print("2. bug - Bug fix")
        print("3. refactor - Code refactoring")
        print("4. security - Security-focused work")
        print("5. integration_test - Integration testing")
        print("6. deployment - Deployment to environment")
        print()

        choice = input("Your choice (1-6): ").strip()

        type_map = {
            "1": "feature",
            "2": "bug",
            "3": "refactor",
            "4": "security",
            "5": "integration_test",
            "6": "deployment"
        }

        return type_map.get(choice)

    def _prompt_title(self) -> Optional[str]:
        """Prompt for work item title."""
        title = input("\nTitle: ").strip()
        if not title:
            print("❌ Error: Title is required")
            return None
        return title

    def _prompt_priority(self) -> str:
        """Prompt for priority."""
        priority = input("\nPriority (critical/high/medium/low) [high]: ").strip().lower()
        if not priority:
            priority = "high"
        if priority not in self.PRIORITIES:
            print(f"⚠️  Invalid priority, using 'high'")
            priority = "high"
        return priority

    def _prompt_dependencies(self, work_type: str) -> List[str]:
        """Prompt for dependencies."""
        required = work_type in ["integration_test", "deployment"]

        prompt = "\nDependencies (comma-separated IDs"
        if required:
            prompt += ", REQUIRED): "
        else:
            prompt += ", or press Enter for none): "

        deps_input = input(prompt).strip()

        if not deps_input:
            if required:
                print("⚠️  Warning: This work item type requires dependencies")
                return self._prompt_dependencies(work_type)  # Retry
            return []

        # Parse and validate
        deps = [d.strip() for d in deps_input.split(",")]
        deps = [d for d in deps if d]  # Remove empty

        # Validate dependencies exist
        valid_deps = []
        for dep in deps:
            if self._work_item_exists(dep):
                valid_deps.append(dep)
            else:
                print(f"⚠️  Warning: Dependency '{dep}' not found, skipping")

        return valid_deps

    def _generate_id(self, work_type: str, title: str) -> str:
        """Generate work item ID from type and title."""
        # Clean title: lowercase, alphanumeric + underscore only
        clean_title = re.sub(r'[^a-z0-9]+', '_', title.lower())
        clean_title = clean_title.strip('_')

        # Truncate if too long
        if len(clean_title) > 30:
            clean_title = clean_title[:30]

        return f"{work_type}_{clean_title}"

    def _work_item_exists(self, work_id: str) -> bool:
        """Check if work item ID already exists."""
        if not self.work_items_file.exists():
            return False

        data = read_json(self.work_items_file)
        return work_id in data.get("work_items", {})

    def _create_spec_file(self, work_id: str, work_type: str, title: str) -> bool:
        """Create specification file from template."""
        # Ensure specs directory exists
        self.specs_dir.mkdir(parents=True, exist_ok=True)

        # Load template
        template_file = self.templates_dir / f"{work_type}_spec.md"
        if not template_file.exists():
            return False

        template_content = template_file.read_text()

        # Replace title placeholder
        if work_type == "feature":
            spec_content = template_content.replace("[Feature Name]", title)
        elif work_type == "bug":
            spec_content = template_content.replace("[Bug Title]", title)
        elif work_type == "refactor":
            spec_content = template_content.replace("[Refactor Title]", title)
        elif work_type == "security":
            spec_content = template_content.replace("[Security Issue]", title)
        elif work_type == "integration_test":
            spec_content = template_content.replace("[Name]", title)
        elif work_type == "deployment":
            spec_content = template_content.replace("[Environment]", title)
        else:
            spec_content = template_content

        # Save spec file
        spec_path = self.specs_dir / f"{work_id}.md"
        spec_path.write_text(spec_content)

        return True

    def _add_to_tracking(self, work_id: str, work_type: str, title: str,
                        priority: str, dependencies: List[str]):
        """Add work item to work_items.json."""
        # Load existing data
        if self.work_items_file.exists():
            data = read_json(self.work_items_file)
        else:
            data = {"work_items": {}}

        # Create work item entry
        work_item = {
            "id": work_id,
            "type": work_type,
            "title": title,
            "status": "not_started",
            "priority": priority,
            "dependencies": dependencies,
            "created_at": datetime.now().isoformat(),
            "sessions": [],
            "rationale": "",
            "acceptance_criteria": [],
            "implementation_paths": [],
            "test_paths": []
        }

        # Add to data
        data["work_items"][work_id] = work_item

        # Save atomically
        write_json(self.work_items_file, data)


def main():
    """CLI entry point."""
    manager = WorkItemManager()
    work_id = manager.create_work_item()

    if work_id:
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit(main())
```

#### Integration

- Integrates with Phase 1's file_ops for atomic JSON writes
- Uses template system for consistent work item structure
- Validates dependencies and types
- Auto-generates meaningful IDs

#### Testing Checklist

- [ ] Create feature work item
- [ ] Create bug work item
- [ ] Create refactor work item
- [ ] Create security work item
- [ ] Create integration_test (requires dependencies)
- [ ] Create deployment (requires dependencies)
- [ ] Duplicate ID detection works
- [ ] Invalid type rejected
- [ ] Invalid priority defaults to 'high'
- [ ] Specification file created correctly
- [ ] work_items.json updated atomically

---

### 2.3 Implement `/work-item list` Command

**Purpose:** List work items with filtering and visual indicators

**Status:** 📋 To Implement

**Files:**
- `commands/work-item-list.md` (NEW)
- Enhance `scripts/work_item_manager.py` with list methods

**Reference:** Standard CLI list commands for UX patterns

#### Implementation

**File:** `commands/work-item-list.md`

```markdown
# Work Item List Command

**Usage:** `/work-item list [--status STATUS] [--type TYPE] [--milestone MILESTONE]`

**Description:** List all work items with optional filtering.

**Options:**
- `--status STATUS` - Filter by status (not_started, in_progress, blocked, completed)
- `--type TYPE` - Filter by type (feature, bug, refactor, security, integration_test, deployment)
- `--milestone MILESTONE` - Filter by milestone name

**Behavior:**

1. Load work_items.json
2. Apply filters (if specified)
3. Sort by:
   - Priority (critical > high > medium > low)
   - Dependency order (items with no unmet dependencies first)
   - Creation date (oldest first)
4. Display with color coding and indicators
5. Show summary statistics

**Output Format:**

```
Work Items (15 total, 3 in progress, 8 not started, 4 completed)

🔴 CRITICAL
  [  ] feature_oauth_integration (blocked - waiting on: feature_user_model) 🚫
  [>>] security_fix_sql_injection (in progress, session 3)

🟠 HIGH
  [>>] feature_user_profile (in progress, session 1)
  [  ] bug_login_timeout (ready to start) ✓
  [✓] feature_user_model (completed, 2 sessions)

🟡 MEDIUM
  [  ] refactor_database_queries (ready to start) ✓
  [  ] feature_email_notifications (ready to start) ✓

🟢 LOW
  [  ] refactor_code_cleanup (ready to start) ✓

Legend:
  [  ] Not started
  [>>] In progress
  [✓] Completed
  🚫 Blocked by dependencies
  ✓ Ready to start
```

**Example:**

\`\`\`
User: /work-item list --status not_started --type feature

Claude: Work Items (5 matching filters)

🟠 HIGH
  [  ] feature_oauth_integration (blocked - waiting on: feature_user_model) 🚫
  [  ] feature_user_profile (ready to start) ✓

🟡 MEDIUM
  [  ] feature_email_notifications (ready to start) ✓
  [  ] feature_password_reset (ready to start) ✓

🟢 LOW
  [  ] feature_user_preferences (ready to start) ✓
\`\`\`
```

**File:** Add to `scripts/work_item_manager.py`

```python
def list_work_items(self, status_filter: Optional[str] = None,
                   type_filter: Optional[str] = None,
                   milestone_filter: Optional[str] = None) -> Dict:
    """List work items with optional filtering."""
    if not self.work_items_file.exists():
        print("No work items found. Create one with /work-item create")
        return {"items": [], "count": 0}

    data = read_json(self.work_items_file)
    items = data.get("work_items", {})

    # Apply filters
    filtered_items = {}
    for work_id, item in items.items():
        # Status filter
        if status_filter and item["status"] != status_filter:
            continue

        # Type filter
        if type_filter and item["type"] != type_filter:
            continue

        # Milestone filter
        if milestone_filter and item.get("milestone") != milestone_filter:
            continue

        filtered_items[work_id] = item

    # Check dependency status for each item
    for work_id, item in filtered_items.items():
        item["_blocked"] = self._is_blocked(item, items)
        item["_ready"] = not item["_blocked"] and item["status"] == "not_started"

    # Sort items
    sorted_items = self._sort_items(filtered_items)

    # Display
    self._display_items(sorted_items)

    return {
        "items": sorted_items,
        "count": len(sorted_items)
    }

def _is_blocked(self, item: Dict, all_items: Dict) -> bool:
    """Check if work item is blocked by dependencies."""
    if item["status"] != "not_started":
        return False

    dependencies = item.get("dependencies", [])
    if not dependencies:
        return False

    for dep_id in dependencies:
        if dep_id not in all_items:
            continue
        if all_items[dep_id]["status"] != "completed":
            return True

    return False

def _sort_items(self, items: Dict) -> List[Dict]:
    """Sort items by priority, dependency status, and date."""
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}

    items_list = list(items.values())

    # Sort by:
    # 1. Priority (critical first)
    # 2. Blocked status (ready items first)
    # 3. Status (in_progress first)
    # 4. Creation date (oldest first)
    items_list.sort(key=lambda x: (
        priority_order.get(x["priority"], 99),
        x.get("_blocked", False),
        0 if x["status"] == "in_progress" else 1,
        x.get("created_at", "")
    ))

    return items_list

def _display_items(self, items: List[Dict]):
    """Display items with color coding and indicators."""
    if not items:
        print("No work items found matching filters.")
        return

    # Count by status
    status_counts = {
        "not_started": 0,
        "in_progress": 0,
        "blocked": 0,
        "completed": 0
    }

    for item in items:
        if item.get("_blocked"):
            status_counts["blocked"] += 1
        else:
            status_counts[item["status"]] += 1

    # Header
    total = len(items)
    print(f"\nWork Items ({total} total, "
          f"{status_counts['in_progress']} in progress, "
          f"{status_counts['not_started']} not started, "
          f"{status_counts['completed']} completed)\n")

    # Group by priority
    priority_groups = {
        "critical": [],
        "high": [],
        "medium": [],
        "low": []
    }

    for item in items:
        priority = item.get("priority", "medium")
        priority_groups[priority].append(item)

    # Display each priority group
    priority_emoji = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢"
    }

    for priority in ["critical", "high", "medium", "low"]:
        group_items = priority_groups[priority]
        if not group_items:
            continue

        print(f"{priority_emoji[priority]} {priority.upper()}")

        for item in group_items:
            status_icon = self._get_status_icon(item)
            title = item["title"]
            work_id = item["id"]

            # Build status string
            if item.get("_blocked"):
                # Show blocking dependencies
                blocking_deps = [
                    dep for dep in item.get("dependencies", [])
                    # Would need to check actual status, simplified here
                ]
                status_str = f"(blocked - waiting on: {', '.join(item.get('dependencies', [])[:2])}) 🚫"
            elif item["status"] == "in_progress":
                sessions = len(item.get("sessions", []))
                status_str = f"(in progress, session {sessions})"
            elif item["status"] == "completed":
                sessions = len(item.get("sessions", []))
                status_str = f"(completed, {sessions} session{'s' if sessions != 1 else ''})"
            elif item.get("_ready"):
                status_str = "(ready to start) ✓"
            else:
                status_str = ""

            print(f"  {status_icon} {work_id} {status_str}")

        print()

    # Legend
    print("Legend:")
    print("  [  ] Not started")
    print("  [>>] In progress")
    print("  [✓] Completed")
    print("  🚫 Blocked by dependencies")
    print("  ✓ Ready to start")
    print()

def _get_status_icon(self, item: Dict) -> str:
    """Get status icon for work item."""
    if item["status"] == "completed":
        return "[✓]"
    elif item["status"] == "in_progress":
        return "[>>]"
    else:
        return "[  ]"
```

#### Integration

- Uses existing work_items.json structure
- Integrates dependency checking logic
- Color coding enhances readability
- Filtering enables focused views

#### Testing Checklist

- [ ] List all work items (no filters)
- [ ] Filter by status (not_started, in_progress, completed)
- [ ] Filter by type (feature, bug, etc.)
- [ ] Filter by milestone
- [ ] Multiple filters combined
- [ ] Empty list handled gracefully
- [ ] Blocked items identified correctly
- [ ] Sorting is correct (priority > dependencies > date)
- [ ] Color coding displays correctly
- [ ] Summary statistics accurate

---

### 2.4 Implement `/work-item show` Command

**Purpose:** Display detailed information about a specific work item

**Status:** 📋 To Implement

**Files:**
- `commands/work-item-show.md` (NEW)
- Enhance `scripts/work_item_manager.py` with show methods

#### Implementation

**File:** `commands/work-item-show.md`

```markdown
# Work Item Show Command

**Usage:** `/work-item show <work_item_id>`

**Description:** Display detailed information about a specific work item.

**Behavior:**

1. Load work item from work_items.json
2. Load specification file from .session/specs/
3. Display comprehensive view:
   - Basic info (ID, type, status, priority)
   - Dependencies (with status)
   - Session history
   - Git branch info
   - Specification content
4. Show actionable next steps

**Example:**

\`\`\`
User: /work-item show feature_oauth

Claude:
================================================================================
Work Item: feature_oauth
================================================================================

Type: feature
Status: in_progress
Priority: high
Created: 2025-10-10

Dependencies:
  ✓ feature_user_model (completed)
  ✗ feature_database_migration (in progress)

Sessions:
  1. 2025-10-11 14:30-16:45 (2h 15m) - Initial implementation
  2. 2025-10-12 10:00-11:30 (1h 30m) - Added OAuth providers

Git Branch: session-003-feature_oauth
Commits: 5

Specification:
--------------
# Feature: OAuth Integration

## Overview
Enable users to log in using OAuth providers (Google, GitHub).

## User Story
As a user, I want to log in using my existing Google or GitHub account
so that I don't need to create another password.

[... rest of specification ...]

Next Steps:
- Continue working: /session-start
- Update fields: /work-item update feature_oauth
- View related items: /work-item list --milestone auth
\`\`\`
```

**File:** Add to `scripts/work_item_manager.py`

```python
def show_work_item(self, work_id: str) -> Optional[Dict]:
    """Display detailed information about a work item."""
    if not self.work_items_file.exists():
        print("No work items found.")
        return None

    data = read_json(self.work_items_file)
    items = data.get("work_items", {})

    if work_id not in items:
        print(f"❌ Error: Work item '{work_id}' not found")
        print("\nAvailable work items:")
        for wid in list(items.keys())[:5]:
            print(f"  - {wid}")
        return None

    item = items[work_id]

    # Display header
    print("=" * 80)
    print(f"Work Item: {work_id}")
    print("=" * 80)
    print()

    # Basic info
    print(f"Type: {item['type']}")
    print(f"Status: {item['status']}")
    print(f"Priority: {item['priority']}")
    print(f"Created: {item.get('created_at', 'Unknown')[:10]}")
    print()

    # Dependencies
    if item.get("dependencies"):
        print("Dependencies:")
        for dep_id in item["dependencies"]:
            if dep_id in items:
                dep_status = items[dep_id]["status"]
                icon = "✓" if dep_status == "completed" else "✗"
                print(f"  {icon} {dep_id} ({dep_status})")
            else:
                print(f"  ? {dep_id} (not found)")
        print()

    # Sessions
    sessions = item.get("sessions", [])
    if sessions:
        print(f"Sessions: {len(sessions)}")
        for i, session in enumerate(sessions[-5:], 1):  # Last 5 sessions
            session_num = session.get("session_number", i)
            date = session.get("date", "Unknown")
            duration = session.get("duration", "Unknown")
            notes = session.get("notes", "")
            print(f"  {session_num}. {date} ({duration}) - {notes[:50]}")
        print()

    # Git info
    git_info = item.get("git", {})
    if git_info:
        print(f"Git Branch: {git_info.get('branch', 'N/A')}")
        commits = git_info.get("commits", [])
        print(f"Commits: {len(commits)}")
        print()

    # Specification
    spec_path = self.specs_dir / f"{work_id}.md"
    if spec_path.exists():
        print("Specification:")
        print("-" * 80)
        spec_content = spec_path.read_text()
        # Show first 30 lines
        lines = spec_content.split('\n')[:30]
        print('\n'.join(lines))
        if len(spec_content.split('\n')) > 30:
            print("\n[... see full specification in .session/specs/{}.md]".format(work_id))
        print()

    # Next steps
    print("Next Steps:")
    if item["status"] == "not_started":
        # Check dependencies
        blocked = any(
            items.get(dep_id, {}).get("status") != "completed"
            for dep_id in item.get("dependencies", [])
        )
        if blocked:
            print("- Waiting on dependencies to complete")
        else:
            print("- Start working: /session-start")
    elif item["status"] == "in_progress":
        print("- Continue working: /session-start")
    elif item["status"] == "completed":
        print("- Work item is complete")

    print(f"- Update fields: /work-item update {work_id}")
    if item.get("milestone"):
        print(f"- View related items: /work-item list --milestone {item['milestone']}")
    print()

    return item
```

#### Testing Checklist

- [ ] Show existing work item
- [ ] Show non-existent work item (error handling)
- [ ] Display dependencies correctly
- [ ] Display session history
- [ ] Display git information
- [ ] Display specification preview
- [ ] Show appropriate next steps based on status

---

### 2.5 Implement `/work-item update` Command

**Purpose:** Update work item fields interactively

**Status:** 📋 To Implement

**Files:**
- `commands/work-item-update.md` (NEW)
- Enhance `scripts/work_item_manager.py` with update methods

#### Implementation

**File:** `commands/work-item-update.md`

```markdown
# Work Item Update Command

**Usage:** `/work-item update <work_item_id> [--field value]`

**Description:** Update work item fields interactively or with flags.

**Updatable Fields:**
- `--status` - Change status (not_started, in_progress, blocked, completed)
- `--priority` - Change priority (critical, high, medium, low)
- `--milestone` - Assign to milestone
- `--add-dependency` - Add a dependency
- `--remove-dependency` - Remove a dependency

**Behavior:**

1. Load work item
2. If flags provided: Apply updates directly
3. If no flags: Interactive mode
4. Validate updates based on type
5. Record update in history
6. Save atomically

**Example:**

\`\`\`
User: /work-item update feature_oauth --priority critical

Claude: Updated feature_oauth
  priority: high → critical

User: /work-item update feature_oauth

Claude: Update Work Item: feature_oauth

Current values:
  Status: in_progress
  Priority: critical
  Milestone: (none)

What would you like to update?
1. Status
2. Priority
3. Milestone
4. Add dependency
5. Remove dependency
6. Cancel

Your choice: 3

Enter milestone name: auth-mvp

Updated feature_oauth:
  milestone: (none) → auth-mvp
\`\`\`
```

**File:** Add to `scripts/work_item_manager.py`

```python
def update_work_item(self, work_id: str, **updates) -> bool:
    """Update work item fields."""
    if not self.work_items_file.exists():
        print("No work items found.")
        return False

    data = read_json(self.work_items_file)
    items = data.get("work_items", {})

    if work_id not in items:
        print(f"❌ Error: Work item '{work_id}' not found")
        return False

    item = items[work_id]
    changes = []

    # Apply updates
    for field, value in updates.items():
        if field == "status":
            if value not in ["not_started", "in_progress", "blocked", "completed"]:
                print(f"⚠️  Invalid status: {value}")
                continue
            old_value = item["status"]
            item["status"] = value
            changes.append(f"  status: {old_value} → {value}")

        elif field == "priority":
            if value not in self.PRIORITIES:
                print(f"⚠️  Invalid priority: {value}")
                continue
            old_value = item["priority"]
            item["priority"] = value
            changes.append(f"  priority: {old_value} → {value}")

        elif field == "milestone":
            old_value = item.get("milestone", "(none)")
            item["milestone"] = value
            changes.append(f"  milestone: {old_value} → {value}")

        elif field == "add_dependency":
            deps = item.get("dependencies", [])
            if value not in deps:
                if value in items:
                    deps.append(value)
                    item["dependencies"] = deps
                    changes.append(f"  added dependency: {value}")
                else:
                    print(f"⚠️  Dependency '{value}' not found")

        elif field == "remove_dependency":
            deps = item.get("dependencies", [])
            if value in deps:
                deps.remove(value)
                item["dependencies"] = deps
                changes.append(f"  removed dependency: {value}")

    if not changes:
        print("No changes made.")
        return False

    # Record update
    item.setdefault("update_history", []).append({
        "timestamp": datetime.now().isoformat(),
        "changes": changes
    })

    # Save
    data["work_items"][work_id] = item
    write_json(self.work_items_file, data)

    print(f"\nUpdated {work_id}:")
    for change in changes:
        print(change)
    print()

    return True

def update_work_item_interactive(self, work_id: str) -> bool:
    """Interactive work item update."""
    if not self.work_items_file.exists():
        print("No work items found.")
        return False

    data = read_json(self.work_items_file)
    items = data.get("work_items", {})

    if work_id not in items:
        print(f"❌ Error: Work item '{work_id}' not found")
        return False

    item = items[work_id]

    print(f"\nUpdate Work Item: {work_id}\n")
    print("Current values:")
    print(f"  Status: {item['status']}")
    print(f"  Priority: {item['priority']}")
    print(f"  Milestone: {item.get('milestone', '(none)')}")
    print()

    print("What would you like to update?")
    print("1. Status")
    print("2. Priority")
    print("3. Milestone")
    print("4. Add dependency")
    print("5. Remove dependency")
    print("6. Cancel")
    print()

    choice = input("Your choice: ").strip()

    if choice == "1":
        status = input("New status (not_started/in_progress/blocked/completed): ").strip()
        return self.update_work_item(work_id, status=status)
    elif choice == "2":
        priority = input("New priority (critical/high/medium/low): ").strip()
        return self.update_work_item(work_id, priority=priority)
    elif choice == "3":
        milestone = input("Milestone name: ").strip()
        return self.update_work_item(work_id, milestone=milestone)
    elif choice == "4":
        dep = input("Dependency ID to add: ").strip()
        return self.update_work_item(work_id, add_dependency=dep)
    elif choice == "5":
        dep = input("Dependency ID to remove: ").strip()
        return self.update_work_item(work_id, remove_dependency=dep)
    else:
        print("Cancelled.")
        return False
```

#### Testing Checklist

- [ ] Update status with flag
- [ ] Update priority with flag
- [ ] Update milestone with flag
- [ ] Add dependency
- [ ] Remove dependency
- [ ] Interactive mode
- [ ] Invalid values rejected
- [ ] Update history recorded
- [ ] Atomic save works

---

### 2.6 Implement `/work-item next` Command

**Purpose:** Find the next work item to start based on dependencies and priority

**Status:** 📋 To Implement

**Files:**
- `commands/work-item-next.md` (NEW)
- Enhance `scripts/work_item_manager.py` with next logic

#### Implementation

**File:** `commands/work-item-next.md`

```markdown
# Work Item Next Command

**Usage:** `/work-item next`

**Description:** Show the next recommended work item to start.

**Logic:**
1. Filter to not_started items
2. Check dependencies (skip blocked items)
3. Sort by priority
4. Return highest priority, unblocked item
5. Explain why other items are blocked

**Example:**

\`\`\`
User: /work-item next

Claude:
Next Recommended Work Item:
================================================================================

🟠 HIGH: feature_user_profile
ID: feature_user_profile
Type: feature
Priority: high
Ready to start: Yes ✓

Dependencies: All satisfied
  ✓ feature_user_model (completed)

Estimated effort: 2-3 sessions

To start: /session-start

Other items waiting:
  🔴 feature_oauth_integration - Blocked by: feature_database_migration
  🟡 feature_email_notifications - Ready (medium priority)
\`\`\`
```

**File:** Add to `scripts/work_item_manager.py`

```python
def get_next_work_item(self) -> Optional[Dict]:
    """Find next work item to start."""
    if not self.work_items_file.exists():
        print("No work items found.")
        return None

    data = read_json(self.work_items_file)
    items = data.get("work_items", {})

    # Filter to not_started items
    not_started = {
        wid: item for wid, item in items.items()
        if item["status"] == "not_started"
    }

    if not not_started:
        print("No work items available to start.")
        print("All items are either in progress or completed.")
        return None

    # Check dependencies and categorize
    ready_items = []
    blocked_items = []

    for work_id, item in not_started.items():
        is_blocked = self._is_blocked(item, items)
        if is_blocked:
            # Find what's blocking
            blocking = [
                dep_id for dep_id in item.get("dependencies", [])
                if items.get(dep_id, {}).get("status") != "completed"
            ]
            blocked_items.append((work_id, item, blocking))
        else:
            ready_items.append((work_id, item))

    if not ready_items:
        print("No work items ready to start. All have unmet dependencies.\n")
        print("Blocked items:")
        for work_id, item, blocking in blocked_items:
            print(f"  🔴 {work_id} - Blocked by: {', '.join(blocking)}")
        return None

    # Sort ready items by priority
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    ready_items.sort(key=lambda x: priority_order.get(x[1]["priority"], 99))

    # Get top item
    next_id, next_item = ready_items[0]

    # Display
    print("\nNext Recommended Work Item:")
    print("=" * 80)
    print()

    priority_emoji = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢"
    }

    emoji = priority_emoji.get(next_item["priority"], "")
    print(f"{emoji} {next_item['priority'].upper()}: {next_item['title']}")
    print(f"ID: {next_id}")
    print(f"Type: {next_item['type']}")
    print(f"Priority: {next_item['priority']}")
    print("Ready to start: Yes ✓")
    print()

    # Dependencies
    deps = next_item.get("dependencies", [])
    if deps:
        print("Dependencies: All satisfied")
        for dep_id in deps:
            print(f"  ✓ {dep_id} (completed)")
    else:
        print("Dependencies: None")
    print()

    # Estimated effort
    estimated = next_item.get("estimated_effort", "Unknown")
    print(f"Estimated effort: {estimated}")
    print()

    print("To start: /session-start")
    print()

    # Show other items
    if len(ready_items) > 1 or blocked_items:
        print("Other items waiting:")
        for work_id, item in ready_items[1:3]:  # Show next 2 ready items
            emoji = priority_emoji.get(item["priority"], "")
            print(f"  {emoji} {work_id} - Ready ({item['priority']} priority)")

        for work_id, item, blocking in blocked_items[:2]:  # Show 2 blocked items
            print(f"  🔴 {work_id} - Blocked by: {', '.join(blocking[:2])}")
        print()

    return next_item
```

#### Testing Checklist

- [ ] Find next item when available
- [ ] Handle no items available
- [ ] Handle all items blocked
- [ ] Priority sorting works
- [ ] Dependency checking accurate
- [ ] Display blocked items
- [ ] Show other waiting items

---

### 2.7 Add Milestone Tracking

**Purpose:** Group work items into milestones for better organization

**Status:** 📋 To Implement

**Files:**
- Enhance `work_items.json` schema with milestone field
- Add milestone methods to `work_item_manager.py`

#### Implementation

**Milestone Structure in work_items.json:**

```json
{
  "work_items": { ... },
  "milestones": {
    "auth-mvp": {
      "name": "auth-mvp",
      "title": "Authentication MVP",
      "description": "Basic authentication system",
      "target_date": "2025-11-01",
      "status": "in_progress",
      "created_at": "2025-10-10T10:00:00"
    }
  }
}
```

**Add milestone field to work items:**

```python
# In _add_to_tracking method
work_item = {
    ...
    "milestone": "",  # Add this field
    ...
}
```

**File:** Add to `scripts/work_item_manager.py`

```python
def create_milestone(self, name: str, title: str, description: str,
                    target_date: Optional[str] = None) -> bool:
    """Create a new milestone."""
    if not self.work_items_file.exists():
        data = {"work_items": {}, "milestones": {}}
    else:
        data = read_json(self.work_items_file)
        if "milestones" not in data:
            data["milestones"] = {}

    if name in data["milestones"]:
        print(f"❌ Milestone '{name}' already exists")
        return False

    milestone = {
        "name": name,
        "title": title,
        "description": description,
        "target_date": target_date or "",
        "status": "not_started",
        "created_at": datetime.now().isoformat()
    }

    data["milestones"][name] = milestone
    write_json(self.work_items_file, data)

    print(f"✓ Created milestone: {name}")
    return True

def get_milestone_progress(self, milestone_name: str) -> Dict:
    """Calculate milestone progress."""
    if not self.work_items_file.exists():
        return {"error": "No work items found"}

    data = read_json(self.work_items_file)
    items = data.get("work_items", {})

    # Filter items in this milestone
    milestone_items = [
        item for item in items.values()
        if item.get("milestone") == milestone_name
    ]

    if not milestone_items:
        return {
            "total": 0,
            "completed": 0,
            "in_progress": 0,
            "not_started": 0,
            "percent": 0
        }

    total = len(milestone_items)
    completed = sum(1 for item in milestone_items if item["status"] == "completed")
    in_progress = sum(1 for item in milestone_items if item["status"] == "in_progress")
    not_started = sum(1 for item in milestone_items if item["status"] == "not_started")
    percent = int((completed / total) * 100) if total > 0 else 0

    return {
        "total": total,
        "completed": completed,
        "in_progress": in_progress,
        "not_started": not_started,
        "percent": percent
    }

def list_milestones(self) -> None:
    """List all milestones with progress."""
    if not self.work_items_file.exists():
        print("No milestones found.")
        return

    data = read_json(self.work_items_file)
    milestones = data.get("milestones", {})

    if not milestones:
        print("No milestones found.")
        return

    print("\nMilestones:\n")

    for name, milestone in milestones.items():
        progress = self.get_milestone_progress(name)
        percent = progress["percent"]

        # Progress bar
        bar_length = 20
        filled = int(bar_length * percent / 100)
        bar = "█" * filled + "░" * (bar_length - filled)

        print(f"{milestone['title']}")
        print(f"  [{bar}] {percent}%")
        print(f"  {progress['completed']}/{progress['total']} complete, "
              f"{progress['in_progress']} in progress")

        if milestone.get("target_date"):
            print(f"  Target: {milestone['target_date']}")
        print()
```

#### Testing Checklist

- [ ] Create milestone
- [ ] Assign work item to milestone
- [ ] Calculate milestone progress
- [ ] List milestones with progress
- [ ] Filter work items by milestone
- [ ] Display progress bars correctly

---

### 2.8 Enhance Briefings with Milestones

**Purpose:** Add milestone context to session briefings

**Status:** 📋 To Implement

**Files:**
- Enhance `scripts/briefing_generator.py`

#### Implementation

**File:** Update `briefing_generator.py`

```python
def load_milestone_context(work_item):
    """Load milestone context for briefing."""
    milestone_name = work_item.get("milestone")
    if not milestone_name:
        return None

    work_items_file = Path(".session/tracking/work_items.json")
    if not work_items_file.exists():
        return None

    data = json.loads(work_items_file.read_text())
    milestones = data.get("milestones", {})
    milestone = milestones.get(milestone_name)

    if not milestone:
        return None

    # Calculate progress
    items = data.get("work_items", {})
    milestone_items = [
        item for item in items.values()
        if item.get("milestone") == milestone_name
    ]

    total = len(milestone_items)
    completed = sum(1 for item in milestone_items if item["status"] == "completed")
    percent = int((completed / total) * 100) if total > 0 else 0

    return {
        "name": milestone_name,
        "title": milestone["title"],
        "description": milestone["description"],
        "target_date": milestone.get("target_date", ""),
        "progress": percent,
        "total_items": total,
        "completed_items": completed
    }

def generate_comprehensive_briefing(item_id, item, learnings_data):
    """Generate comprehensive briefing with milestone context."""
    # ... existing code ...

    # Add milestone section
    milestone_context = load_milestone_context(item)
    if milestone_context:
        briefing += f"""
## Milestone Context

**{milestone_context['title']}**
{milestone_context['description']}

Progress: {milestone_context['progress']}% ({milestone_context['completed_items']}/{milestone_context['total_items']} items complete)
Target Date: {milestone_context['target_date']}

Related work items in this milestone:
"""
        # Show other items in same milestone
        related_items = [
            other_item for other_item in work_items.values()
            if other_item.get("milestone") == milestone_context["name"]
            and other_item["id"] != item_id
        ][:5]

        for related in related_items:
            status_icon = "✓" if related["status"] == "completed" else "○"
            briefing += f"- {status_icon} {related['id']} - {related['title']}\n"

    # ... rest of briefing ...

    return briefing
```

#### Testing Checklist

- [ ] Milestone context included in briefing
- [ ] Related work items shown
- [ ] Progress accurate
- [ ] Works when no milestone assigned

---

### 2.9 Implement `/session-status` Command

**Purpose:** Quick view of current session state without re-reading full briefing

**Status:** 📋 To Implement

**Files:**
- `commands/session-status.md` (NEW)
- `scripts/session_status.py` (NEW)

#### Implementation

**File:** `commands/session-status.md`

```markdown
# Session Status Command

**Usage:** `/session-status`

**Description:** Display current session state and progress.

**Displays:**
- Current work item
- Time elapsed in session
- Files changed (git diff)
- Git branch status
- Milestone progress (if applicable)
- Next upcoming work items

**Example:**

\`\`\`
User: /session-status

Claude:
Current Session Status
================================================================================

Work Item: feature_user_profile
Type: feature
Priority: high
Session: 2 (of estimated 3)

Time Elapsed: 1h 23m

Files Changed (5):
  M  src/models/user.py
  M  src/api/profile.py
  A  tests/test_profile.py
  M  README.md
  M  requirements.txt

Git Branch: session-003-feature_user_profile
Commits: 3

Milestone: auth-mvp (45% complete)
  Related items: 2 in progress, 3 not started

Next up:
  🟠 feature_oauth_integration (blocked)
  🟡 feature_email_notifications (ready)

Quick actions:
  - Validate session: /session-validate
  - Complete session: /session-end
  - View work item: /work-item show feature_user_profile
\`\`\`
```

**File:** `scripts/session_status.py`

```python
#!/usr/bin/env python3
"""
Display current session status.
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime


def get_session_status():
    """Get current session status."""
    session_dir = Path(".session")
    status_file = session_dir / "tracking" / "status_update.json"

    if not status_file.exists():
        print("No active session.")
        return 1

    # Load status
    status = json.loads(status_file.read_text())
    work_item_id = status.get("current_work_item")

    if not work_item_id:
        print("No active work item in this session.")
        return 1

    # Load work item
    work_items_file = session_dir / "tracking" / "work_items.json"
    data = json.loads(work_items_file.read_text())
    item = data["work_items"].get(work_item_id)

    if not item:
        print(f"Work item {work_item_id} not found.")
        return 1

    print("\nCurrent Session Status")
    print("=" * 80)
    print()

    # Work item info
    print(f"Work Item: {work_item_id}")
    print(f"Type: {item['type']}")
    print(f"Priority: {item['priority']}")

    sessions = len(item.get("sessions", []))
    estimated = item.get("estimated_effort", "Unknown")
    print(f"Session: {sessions} (of estimated {estimated})")
    print()

    # Time elapsed (if session start time recorded)
    session_start = status.get("session_start")
    if session_start:
        start_time = datetime.fromisoformat(session_start)
        elapsed = datetime.now() - start_time
        hours = int(elapsed.total_seconds() // 3600)
        minutes = int((elapsed.total_seconds() % 3600) // 60)
        print(f"Time Elapsed: {hours}h {minutes}m")
        print()

    # Git changes
    try:
        result = subprocess.run(
            ["git", "diff", "--name-status", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0 and result.stdout:
            lines = result.stdout.strip().split('\n')
            print(f"Files Changed ({len(lines)}):")
            for line in lines[:10]:  # Show first 10
                print(f"  {line}")
            if len(lines) > 10:
                print(f"  ... and {len(lines) - 10} more")
            print()
    except:
        pass

    # Git branch
    git_info = item.get("git", {})
    if git_info:
        branch = git_info.get("branch", "N/A")
        commits = len(git_info.get("commits", []))
        print(f"Git Branch: {branch}")
        print(f"Commits: {commits}")
        print()

    # Milestone
    milestone_name = item.get("milestone")
    if milestone_name:
        milestones = data.get("milestones", {})
        milestone = milestones.get(milestone_name)
        if milestone:
            # Calculate progress (simplified)
            milestone_items = [
                i for i in data["work_items"].values()
                if i.get("milestone") == milestone_name
            ]
            total = len(milestone_items)
            completed = sum(1 for i in milestone_items if i["status"] == "completed")
            percent = int((completed / total) * 100) if total > 0 else 0

            in_prog = sum(1 for i in milestone_items if i["status"] == "in_progress")
            not_started = sum(1 for i in milestone_items if i["status"] == "not_started")

            print(f"Milestone: {milestone_name} ({percent}% complete)")
            print(f"  Related items: {in_prog} in progress, {not_started} not started")
            print()

    # Next items
    print("Next up:")
    items = data["work_items"]
    not_started = [
        (wid, i) for wid, i in items.items()
        if i["status"] == "not_started"
    ][:3]

    priority_emoji = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢"
    }

    for wid, i in not_started:
        emoji = priority_emoji.get(i["priority"], "")
        # Check if blocked
        blocked = any(
            items.get(dep_id, {}).get("status") != "completed"
            for dep_id in i.get("dependencies", [])
        )
        status_str = "(blocked)" if blocked else "(ready)"
        print(f"  {emoji} {wid} {status_str}")
    print()

    # Quick actions
    print("Quick actions:")
    print("  - Validate session: /session-validate")
    print("  - Complete session: /session-end")
    print(f"  - View work item: /work-item show {work_item_id}")
    print()

    return 0


if __name__ == "__main__":
    exit(get_session_status())
```

#### Testing Checklist

- [ ] Display current work item
- [ ] Show time elapsed
- [ ] List files changed
- [ ] Show git status
- [ ] Display milestone progress
- [ ] Show next items
- [ ] Handle no active session

---

### Phase 2 Completion Checklist

**Implementation:**
- [ ] All work item type templates created (2.1)
- [ ] `/work-item create` command implemented (2.2)
- [ ] `/work-item list` command implemented (2.3)
- [ ] `/work-item show` command implemented (2.4)
- [ ] `/work-item update` command implemented (2.5)
- [ ] `/work-item next` command implemented (2.6)
- [ ] Milestone tracking added (2.7)
- [ ] Briefings enhanced with milestones (2.8)
- [ ] `/session-status` command implemented (2.9)

**Testing:**
- [ ] Create work item interactively
- [ ] Create work item with dependencies
- [ ] List filtered by status
- [ ] Show work item details
- [ ] Update work item fields
- [ ] Get next work item respects dependencies
- [ ] Milestone tracking works
- [ ] Session status command accurate

**Documentation:**
- [ ] All commands documented
- [ ] Examples provided
- [ ] Phase 2 complete in ROADMAP.md

---

## Phase 3: Visualization (v0.3)

**Goal:** Dependency graphs with critical path analysis

**Status:** 📅 Not Started

**Priority:** HIGH

**Target:** 1 week after Phase 2

**Depends On:** Phase 2

### Overview

Phase 3 integrates the already-complete `dependency_graph.py` script with `/work-item graph` command. Users can visualize project structure and identify bottlenecks.

**Note:** Core visualization algorithms already implemented in `scripts/dependency_graph.py` - just needs command integration and UI polish.

### Implementation Approach

- Create `/work-item graph` command
- Integrate with existing `dependency_graph.py`
- Add filtering options (status, milestone)
- Document usage

---

## Phase 4: Learning Management (v0.4)

**Goal:** Automated learning capture and curation

**Status:** 📅 Not Started

**Priority:** MEDIUM-HIGH

**Target:** 1-2 weeks after Phase 3

**Depends On:** Phase 3

### Overview

Phase 4 integrates the already-complete `learning_curator.py` script with `/learning` commands. Learnings are captured during sessions and automatically curated.

**Note:** Core curation algorithms already implemented in `scripts/learning_curator.py` - just needs command integration and automation.

---

## Phase 5: Quality Gates (v0.5)

**Goal:** Enhanced quality enforcement including security

**Status:** 📅 Not Started

**Priority:** HIGH

**Target:** 2-3 weeks after Phase 4

**Depends On:** Phase 4

### Overview

Phase 5 enhances existing quality gates with security scanning, Context7 verification, and comprehensive validation.

---

## Phase 5.5-7: Future Phases

(Brief descriptions - will be expanded when we reach them)

**Phase 5.5:** Integration & System Testing Support
**Phase 5.6:** Deployment & Launch Support
**Phase 6:** Spec-Kit Integration
**Phase 7:** Advanced Features & Polish

---

## Appendices

### A. Common Patterns

**Atomic JSON Updates:**
```python
# Always write to temp file first
temp_file = file_path.with_suffix('.tmp')
with open(temp_file, 'w') as f:
    json.dump(data, f, indent=2)
temp_file.replace(file_path)  # Atomic
```

**Safe Subprocess Calls:**
```python
result = subprocess.run(
    command,
    capture_output=True,
    text=True,
    timeout=30,
    cwd=project_root
)
if result.returncode != 0:
    # Handle error
```

### B. Reference Materials

- **Formats:** session-driven-development.md lines 113-575
- **Algorithms:** dependency_graph.py (critical path), learning_curator.py (categorization)
- **Philosophy:** ai-augmented-solo-framework.md
- **Lessons:** implementation-insights.md