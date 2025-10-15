# Claude Code Session Plugin

**Session-Driven Development for Claude Code** - Maintain perfect context across multiple AI coding sessions.

> **Note:** This plugin is designed for solo developers using Claude Code. It provides comprehensive session management, quality gates, and knowledge accumulation for AI-augmented software development.

## Overview

The Claude Code Session Plugin implements **Session-Driven Development (SDD)**, a comprehensive methodology that enables AI coding assistants to work on software projects across multiple sessions with perfect context continuity, enforced quality standards, and accumulated institutional knowledge.

### The Problem

Traditional AI coding sessions suffer from:
- **Context loss** between sessions - AI forgets what was done previously
- **Quality entropy** over time - Standards slip without enforcement
- **Knowledge fragmentation** across interactions - Learnings get lost
- **Lack of process rigor** - No systematic workflow for complex projects

### The Solution

Session-Driven Development provides:
- **Perfect context continuity** through automated briefings that load full project state
- **Quality enforcement** via automated validation gates (tests, linting, security scans)
- **Knowledge accumulation** through learnings system with AI-powered categorization
- **Dependency-driven workflow** (logical ordering based on dependencies, not arbitrary sequences)
- **Living documentation** that stays current automatically with git integration

## Features

### Core Commands

**Session Management:**
- `/session-init` - Initialize project with .session/ structure
- `/session-start` - Begin work session with comprehensive briefing
- `/session-end` - Complete session with quality gates and summary
- `/session-validate` - Pre-flight check before session completion
- `/session-status` - Quick session overview

**Work Item Management:**
- `/work-item-create` - Create new work item with dependencies
- `/work-item-list` - List work items with filters
- `/work-item-show` - Show work item details
- `/work-item-update` - Update work item fields
- `/work-item-next` - Get next recommended work item
- `/work-item-graph` - Visualize dependencies with critical path

**Learning Management:**
- `/learning-capture` - Capture insight during development
- `/learning-show` - Browse learnings with filters
- `/learning-search` - Full-text search across learnings
- `/learning-curate` - Run curation process (categorize, deduplicate, merge)

### Key Capabilities

✅ **Stateful Development** - Perfect context handoffs between sessions
✅ **Quality Gates** - Tests, linting, formatting enforced before completion
✅ **Dependency Management** - Work items ordered by logical dependencies
✅ **Learning System** - Auto-categorized knowledge base with smart deduplication
✅ **Visualization** - Dependency graphs with critical path analysis
✅ **Git Integration** - Standardized commits with session summaries

### Dependency Graph Visualization

Visualize project structure and identify bottlenecks with dependency graphs:

```bash
# Via slash command
/work-item-graph
/work-item-graph --critical-path
/work-item-graph --bottlenecks
/work-item-graph --milestone "Phase 3"

# Via CLI
python3 scripts/dependency_graph.py
python3 scripts/dependency_graph.py --format svg --output graph.svg
python3 scripts/dependency_graph.py --stats
```

**Features:**
- **Critical Path Highlighting** - Red nodes/edges show longest dependency chain
- **Bottleneck Detection** - Identify items blocking multiple other items
- **Multiple Formats** - ASCII (terminal), DOT (Graphviz), SVG (visual)
- **Flexible Filtering** - By status, milestone, type, or focus on specific items
- **Timeline Projection** - Estimate completion based on dependency levels

### Learning System

Automated knowledge capture and curation with AI-powered categorization:

```bash
# Via slash commands
/learning-capture            # Capture insight conversationally
/learning-show               # Browse all learnings
/learning-show --category gotchas --tag fastapi
/learning-search "CORS"      # Full-text search
/learning-curate             # Run curation (categorize, deduplicate, merge)

# Via CLI
python3 scripts/learning_curator.py statistics
python3 scripts/learning_curator.py timeline --sessions 10
python3 scripts/learning_curator.py curate --dry-run
```

**Features:**
- **6 Learning Categories** - Auto-categorized (architecture, gotchas, best practices, technical debt, performance, security)
- **3 Extraction Sources** - Session summaries, git commits (`LEARNING:` annotations), inline code comments (`# LEARNING:`)
- **Similarity Detection** - Jaccard + containment algorithms detect duplicates
- **Smart Deduplication** - Automatically merges similar learnings
- **Advanced Filtering** - By category, tag, session, date range
- **Statistics Dashboard** - Total learnings, by category, top tags, growth over time
- **Timeline View** - Learning history by session
- **Auto-Curation** - Runs every N sessions (configurable)

## Installation

### Prerequisites

- **Claude Code**: This plugin requires Claude Code
- **Python 3.9+**: Core scripts are written in Python
- **Git**: Required for version control integration
- **Optional Tools** (for quality gates):
  - `pytest` (Python testing)
  - `ruff` (Python linting/formatting)
  - `bandit`, `safety` (Python security scanning)
  - `eslint`, `prettier` (JavaScript/TypeScript linting/formatting)
  - `npm audit` (JavaScript/TypeScript security)
  - `graphviz` (for SVG dependency graph generation)

### Setup

1. **Clone the plugin repository:**
   ```bash
   # Clone to a dedicated location (NOT your project folder)
   cd ~/plugins  # or any directory you prefer for plugins
   git clone https://github.com/yourusername/claude-session-plugin.git
   ```

2. **Configure Claude Code to use the plugin:**

   Claude Code automatically detects plugins in the `.claude/` directory. To use this plugin:

   **Option A: Symlink (Recommended)**
   ```bash
   # Create symlink from your plugin location to Claude Code's plugin directory
   ln -s ~/plugins/claude-session-plugin ~/.claude/plugins/claude-session-plugin
   ```

   **Option B: Configure in Claude Code settings**

   Add the plugin path to your Claude Code configuration. (Exact method depends on Claude Code version)

3. **Verify installation:**

   Open any project in Claude Code and type `/session-` - you should see autocomplete suggestions for available session commands.

### Using the Plugin in Your Existing Project

The plugin works with **any existing project**:

1. **Navigate to your project in Claude Code**
   ```bash
   cd ~/my-existing-project
   # Open Claude Code here
   ```

2. **Initialize SDD in your project:**
   ```
   /session-init
   ```

   This creates a `.session/` directory in your project root with:
   - `work_items.json` - Your task list
   - `learnings.json` - Knowledge base
   - `status_update.json` - Session state
   - `tracking/` - Stack, tree, and other artifacts
   - `config.json` - Project-specific configuration

3. **Start using the plugin:**
   ```
   /work-item-create
   /session-start
   # ... do your work ...
   /session-end
   ```

**Important Notes:**
- The plugin **does not modify** your existing code or git history
- The `.session/` directory is project-specific (add to `.gitignore` if you want)
- You can use the plugin in multiple projects simultaneously
- Each project maintains its own work items, learnings, and tracking

## Quick Start

### 1. Initialize Your Project

Start by initializing the Session-Driven Development structure in your project:

```
/session-init
```

This creates:
- `.session/` directory with tracking files
- `work_items.json` for task management
- `learnings.json` for knowledge capture
- `status_update.json` for session state
- `tracking/` subdirectory for stack, tree, and other artifacts
- `config.json` with project configuration

### 2. Create Your First Work Item

Create a work item (task) to work on:

```
/work-item-create
```

Follow the conversational prompts to specify:
- Type (feature, bug, refactor, security, integration_test, deployment)
- Title and description
- Acceptance criteria
- Dependencies (if any)
- Priority level

### 3. Start a Development Session

When ready to work, start a session:

```
/session-start
```

Or specify a work item ID:

```
/session-start WI-001
```

This generates a comprehensive briefing including:
- Work item details and acceptance criteria
- Project documentation (vision, architecture, PRD)
- Current technology stack
- Project structure (tree)
- Git status and branch information
- Related learnings from past sessions
- Dependency context

### 4. Work on Your Task

Develop your feature/fix with Claude Code's assistance. During the session:

- **Capture learnings:**
  ```
  /learning-capture
  ```

- **Check session status:**
  ```
  /session-status
  ```

- **Validate readiness:**
  ```
  /session-validate
  ```

### 5. Complete the Session

When done, end the session:

```
/session-end
```

This automatically:
- Runs quality gates (tests, linting, security scans)
- Updates stack and tree tracking
- Extracts learnings from your work
- Commits changes with standardized message
- Pushes to remote
- Updates work item status
- Generates session summary

## Typical Workflow

```mermaid
graph TD
    A[/session-init] --> B[/work-item-create]
    B --> C[/work-item-list]
    C --> D[/session-start]
    D --> E[Develop with Claude]
    E --> F[/learning-capture]
    E --> G[/session-validate]
    G --> H[/session-end]
    H --> I{More work?}
    I -->|Yes| B
    I -->|No| J[Done]
```

## Work Item Management

### Viewing Work Items

```
/work-item-list                    # All work items
/work-item-list --status not_started  # Filter by status
/work-item-list --milestone "Phase 1"  # Filter by milestone
/work-item-show WI-001             # Show specific item
```

### Managing Dependencies

```
/work-item-graph                   # Visualize all dependencies
/work-item-graph --critical-path   # Show critical path
/work-item-graph --bottlenecks     # Identify blockers
/work-item-next                    # Get next available item
```

### Updating Work Items

```
/work-item-update WI-001 --status in_progress
/work-item-update WI-001 --priority high
```

## Configuration

The plugin is configured via `.session/config.json` (created during `/session-init`):

```json
{
  "quality_gates": {
    "tests": {"enabled": true, "required": true, "coverage_threshold": 80},
    "linting": {"enabled": true, "required": false, "auto_fix": true},
    "formatting": {"enabled": true, "required": false, "auto_fix": true},
    "security": {"enabled": true, "required": true, "fail_on": "high"},
    "documentation": {"enabled": true, "required": false}
  },
  "learning_curation": {
    "auto_curate": true,
    "frequency": 5
  },
  "git": {
    "auto_push": true,
    "auto_merge": false
  }
}
```

### Quality Gate Configuration

- `enabled`: Run this gate
- `required`: Block session-end if fails
- `auto_fix`: Automatically fix issues (linting/formatting)
- `coverage_threshold`: Minimum test coverage (%)
- `fail_on`: Security threshold (critical, high, medium, low)

### Learning Curation

- `auto_curate`: Automatically run curation
- `frequency`: Run every N sessions

### Git Configuration

- `auto_push`: Automatically push after session-end
- `auto_merge`: Automatically merge branch if work item complete

## Documentation

- [Session-Driven Development Framework](docs/session-driven-development.md) - Complete methodology specification
- [AI-Augmented Solo Framework](docs/ai-augmented-solo-framework.md) - Philosophical context and broader methodology
- [Implementation Insights](docs/implementation-insights.md) - Lessons learned and proven patterns
- [Learning System Guide](docs/learning-system.md) - Knowledge capture and curation details
- [Roadmap](ROADMAP.md) - Phased development plan

## Project Structure

```
claude-session-plugin/
├── .claude/                  # Claude Code plugin runtime
│   └── commands/             # ✅ Executable slash commands (16 commands)
├── commands/                 # Developer documentation for commands
├── scripts/                  # Core Python logic (13 modules)
│   ├── dependency_graph.py   # ✅ Dependency visualization (ready)
│   ├── learning_curator.py   # ✅ Learning management (ready)
│   └── file_ops.py           # ✅ Utilities (ready)
├── templates/                # JSON schema templates
├── docs/                     # Comprehensive documentation
├── ROADMAP.md               # Development roadmap
├── PLUGIN_IMPLEMENTATION_PLAN_PHASES_0-4.md  # Implementation guide (Phases 0-4)
└── PLUGIN_IMPLEMENTATION_PLAN_PHASES_5+.md   # Implementation guide (Phases 5+)
```

## Development Status

**Current Status:** Production-ready for personal use (Phases 0-5.6 complete)

### Completed Phases

| Phase | Version | Description | Status |
|-------|---------|-------------|--------|
| Phase 0 | v0.0 | Foundation & Documentation | ✅ Complete |
| Phase 1 | v0.1 | Core Plugin Foundation | ✅ Complete |
| Phase 2 | v0.2 | Work Item System | ✅ Complete |
| Phase 3 | v0.3 | Dependency Visualization | ✅ Complete |
| Phase 4 | v0.4 | Learning Management | ✅ Complete |
| Phase 5 | v0.5 | Quality Gates | ✅ Complete |
| Phase 5.5 | v0.5.5 | Integration Testing | ✅ Complete |
| Phase 5.6 | v0.5.6 | Deployment Support | ✅ Complete |

### Test Coverage

**Total: 343/343 tests passing (100%)**

- Phase 1: 6/6 tests ✅
- Phase 2: 9/9 tests ✅
- Phase 3: 11/11 tests ✅
- Phase 4: 12/12 tests ✅
- Phase 5: 12/12 tests ✅
- Phase 5.5: 178/178 tests ✅
- Phase 5.6: 65/65 tests ✅
- Phase 0: Manual validation ✅

### Upcoming Phases

- **Phase 6** (v0.6): Spec-Kit Integration - Import work items from specifications
- **Phase 7** (v0.7+): Advanced Features - Templates, metrics, AI enhancements

See [ROADMAP.md](ROADMAP.md) for detailed phase breakdown and timelines.

## Technology Stack

- **Language:** Python 3.9+
- **Plugin System:** Claude Code native extensions
- **Visualization:** Graphviz (for dependency graphs)
- **Testing:** pytest (for quality gates)
- **Linting:** ruff (for code quality)

## Core Algorithms

This plugin includes battle-tested algorithms:

- **Dependency Resolution** - DFS-based critical path analysis
- **Learning Categorization** - Keyword-based auto-categorization (6 categories)
- **Similarity Detection** - Jaccard + containment similarity for deduplication
- **Quality Gates** - Multi-stage validation pipeline

## Design Principles

1. **AI-Native Design** - Built for Claude's environment, not as external tool
2. **Atomic Operations** - Safe file writes, consistent state updates
3. **Fail-Safe** - Quality gates prevent broken states from propagating
4. **Zero Context Loss** - Comprehensive briefings ensure perfect handoffs
5. **Deterministic** - Repeatable, predictable workflows

## FAQ

### Q: How do I use this plugin in my existing project?

The plugin is installed **once** in Claude Code's plugin directory, then works in **any project**:

1. Clone the plugin to a dedicated location (e.g., `~/plugins/claude-session-plugin`)
2. Symlink or configure it in Claude Code's plugin system
3. Navigate to your existing project in Claude Code
4. Run `/session-init` to create the `.session/` directory
5. Start using session commands in your project

The plugin creates a `.session/` folder in your project root but doesn't modify your existing code.

### Q: Do I need to install all the optional tools?

No. Quality gates gracefully skip when tools aren't available. Install only what you need for your project.

### Q: Can I use this with other AI assistants?

The plugin is specifically designed for Claude Code's environment and slash command system. It won't work with other AI tools without modification.

### Q: How much disk space does the .session directory use?

Typically 1-5 MB for most projects. It stores JSON files, text files, and small logs.

### Q: Can I customize work item types?

Currently, 6 built-in types are supported (feature, bug, refactor, security, integration_test, deployment). Custom types are planned for Phase 7.

### Q: Does this work with GitHub/GitLab?

Yes. The plugin uses standard git commands and integrates with any git remote.

### Q: What happens if I forget to run /session-end?

Your work is still saved in git. You can manually update work items and tracking files, but you'll miss automated quality gates and learning extraction.

### Q: Can I use this on multiple projects?

Yes. Each project gets its own `.session/` directory. The plugin detects and uses the correct context automatically.

## Troubleshooting

### Session-init fails with "Directory already exists"

The `.session/` directory already exists. Either delete it (`rm -rf .session/`) or use your existing setup.

### Quality gates fail even though tests pass

Check:
1. Exit codes from test commands
2. Coverage threshold in config
3. Required vs optional gate settings

### Git integration not working

Ensure:
1. Git repository is initialized (`git init`)
2. Remote is configured (`git remote -v`)
3. Working directory is clean or changes are staged

### Learning curation not triggering

Check `.session/config.json`:
- `auto_curate` should be `true`
- `frequency` should be a positive integer (default: 5)

## Contributing

Contributions are welcome! This project follows standard open-source contribution guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes with tests
4. Run the test suite (`pytest tests/`)
5. Commit your changes
6. Push to your fork
7. Open a Pull Request

### Development Setup

```bash
# Clone the repo
git clone https://github.com/yourusername/claude-session-plugin.git
cd claude-session-plugin

# Install development dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/

# Run specific phase tests
pytest tests/phase_1/
pytest tests/phase_5/test_phase_5_complete.py
```

## License

MIT License

Copyright (c) 2025 Claude Session Plugin Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Credits

Built with insights from building complex software projects with Claude Code assistance.

Inspired by professional software development practices adapted for AI-augmented solo development.

---

**Ready for use!** Phases 0-5.6 complete with 343/343 tests passing.
