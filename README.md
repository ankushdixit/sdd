# SDD (Session-Driven Development)

[![Tests](https://img.shields.io/badge/tests-343%20passing-brightgreen)](https://github.com/ankushdixit/sdd/tree/main/tests)
[![Python](https://img.shields.io/badge/python-3.9+-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/status-production--ready-brightgreen)](https://github.com/ankushdixit/sdd)
[![GitHub Stars](https://img.shields.io/github/stars/ankushdixit/sdd?style=social)](https://github.com/ankushdixit/sdd/stargazers)
[![GitHub Issues](https://img.shields.io/github/issues/ankushdixit/sdd)](https://github.com/ankushdixit/sdd/issues)

**Session-Driven Development for Claude Code** - Maintain perfect context across multiple AI coding sessions.

> **Note:** This is designed for solo developers using Claude Code. It provides comprehensive session management, quality gates, and knowledge accumulation for AI-augmented software development.

## Overview

**SDD** implements **Session-Driven Development**, a comprehensive methodology that enables AI coding assistants to work on software projects across multiple sessions with perfect context continuity, enforced quality standards, and accumulated institutional knowledge.

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
- `/init` - Initialize project with .session/ structure
- `/start` - Begin work session with comprehensive briefing
- `/end` - Complete session with quality gates and summary
- `/validate` - Pre-flight check before session completion
- `/status` - Quick session overview

**Work Item Management:**
- `/work-new` - Create new work item with dependencies
- `/work-list` - List work items with filters
- `/work-show` - Show work item details
- `/work-update` - Update work item fields
- `/work-next` - Get next recommended work item
- `/work-graph` - Visualize dependencies with critical path

**Learning Management:**
- `/learn` - Capture insight during development
- `/learn-show` - Browse learnings with filters
- `/learn-search` - Full-text search across learnings
- `/learn-curate` - Run curation process (categorize, deduplicate, merge)

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
/work-graph
/work-graph --critical-path
/work-graph --bottlenecks
/work-graph --milestone "Phase 3"

# Via CLI
python3 sdd/sdd_cli.py work-graph
python3 sdd/sdd_cli.py work-graph --format svg --output graph.svg
python3 sdd/sdd_cli.py work-graph --stats
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
/learn                    # Capture insight conversationally
/learn-show               # Browse all learnings
/learn-show --category gotchas --tag fastapi
/learn-search "CORS"      # Full-text search
/learn-curate             # Run curation (categorize, deduplicate, merge)

# Via CLI (from project root)
python3 sdd/sdd_cli.py learn-show
python3 sdd/sdd_cli.py learn-search "keyword"
python3 sdd/sdd_cli.py learn-curate --dry-run
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

- **Claude Code**: CLI application required for slash command integration
- **Python 3.9+**: Core scripts are written in Python
- **Git**: Required for version control integration
- **Optional Tools** (for quality gates):
  - `pytest` (Python testing)
  - `ruff` (Python linting/formatting)
  - `bandit`, `safety` (Python security scanning)
  - `eslint`, `prettier` (JavaScript/TypeScript linting/formatting)
  - `npm audit` (JavaScript/TypeScript security)
  - `graphviz` (for SVG dependency graph generation)

### Installation

Clone the repository into your project directory:

```bash
# Navigate to your project
cd /path/to/your/project

# Clone sdd into your project
git clone https://github.com/ankushdixit/sdd.git

# Make the CLI executable (recommended)
chmod +x sdd/sdd_cli.py

# The .claude/commands/ directory will be automatically discovered by Claude Code
```

**That's it!** Claude Code will automatically discover the commands from the `.claude/commands/` directory and make them available as `/init`, `/start`, `/end`, etc.

**Note:** All slash commands now route through `sdd_cli.py`, a universal CLI entry point that handles module imports correctly across different installation methods.

**What gets installed:**
- `sdd_cli.py` - Universal CLI entry point (handles all commands)
- `.claude/commands/` - 15 slash commands (automatically discovered by Claude Code)
- `scripts/` - Python backend logic (8,677 lines)
- `templates/` - Work item specification templates
- `docs/` - Comprehensive documentation
- `tests/` - 343 test cases for validation

**Alternative: Install in a separate directory**

You can also clone sdd anywhere and symlink the necessary directories:

```bash
# Clone to any location
git clone https://github.com/ankushdixit/sdd.git ~/sdd

# Make CLI executable
chmod +x ~/sdd/sdd_cli.py

# Create symlinks in your project
cd /path/to/your/project
ln -s ~/sdd/.claude .claude
ln -s ~/sdd/scripts scripts
ln -s ~/sdd/templates templates

# Verify slash commands work
# Commands automatically use: python3 scripts/../sdd_cli.py <command>
```

## Quick Start

### 1. Initialize Your Project

Start by initializing the Session-Driven Development structure in your project:

```
/init
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
/work-new
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
/start
```

Or specify a work item ID:

```
/start WI-001
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
  /learn
  ```

- **Check session status:**
  ```
  /status
  ```

- **Validate readiness:**
  ```
  /validate
  ```

### 5. Complete the Session

When done, end the session:

```
/end
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
    A["init"] --> B["work-new"]
    B --> C["work-list"]
    C --> D["start"]
    D --> E["Develop with Claude"]
    E --> F["learn"]
    E --> G["validate"]
    G --> H["end"]
    H --> I{"More work?"}
    I -->|Yes| B
    I -->|No| J["Done"]
```

## Work Item Management

### Viewing Work Items

```
/work-list                    # All work items
/work-list --status not_started  # Filter by status
/work-list --milestone "Phase 1"  # Filter by milestone
/work-show WI-001             # Show specific item
```

### Managing Dependencies

```
/work-graph                   # Visualize all dependencies
/work-graph --critical-path   # Show critical path
/work-graph --bottlenecks     # Identify blockers
/work-next                    # Get next available item
```

### Updating Work Items

```
/work-update WI-001 --status in_progress
/work-update WI-001 --priority high
```

## Configuration

Configure SDD via `.session/config.json` (created during `/init`):

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
- `required`: Block `/end` if fails
- `auto_fix`: Automatically fix issues (linting/formatting)
- `coverage_threshold`: Minimum test coverage (%)
- `fail_on`: Security threshold (critical, high, medium, low)

### Learning Curation

- `auto_curate`: Automatically run curation
- `frequency`: Run every N sessions

### Git Configuration

- `auto_push`: Automatically push after `/end`
- `auto_merge`: Automatically merge branch if work item complete

## Documentation

- [Session-Driven Development Framework](docs/session-driven-development.md) - Complete methodology specification
- [AI-Augmented Solo Framework](docs/ai-augmented-solo-framework.md) - Philosophical context and broader methodology
- [Implementation Insights](docs/implementation-insights.md) - Lessons learned and proven patterns
- [Learning System Guide](docs/learning-system.md) - Knowledge capture and curation details
- [Roadmap](ROADMAP.md) - Phased development plan

## Project Structure

```
sdd/
├── .claude/                  # Claude Code command definitions
│   └── commands/             # 15 slash commands (auto-discovered by Claude Code)
├── scripts/                  # Core Python logic (13 modules, 8,677 lines)
│   ├── work_item_manager.py  # Work item CRUD operations
│   ├── quality_gates.py      # Quality enforcement system
│   ├── learning_curator.py   # Knowledge capture & curation
│   ├── briefing_generator.py # Session context generation
│   ├── dependency_graph.py   # Dependency visualization
│   └── [8 more modules...]
├── templates/                # Work item specification templates
│   ├── feature_spec.md
│   ├── bug_spec.md
│   └── [4 more templates...]
├── docs/                     # Comprehensive documentation
│   ├── commands/             # Developer documentation for commands
│   ├── session-driven-development.md    # Complete SDD methodology
│   ├── ai-augmented-solo-framework.md   # Philosophical framework
│   └── [2 more docs...]
├── tests/                    # Test suites (343 tests total)
│   └── phase_1/ through phase_5_6/
├── ROADMAP.md                # Development roadmap
├── README.md                 # This file
└── [Development files...]    # Implementation plans, etc.
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
- **Integration:** Claude Code slash commands
- **Visualization:** Graphviz (for dependency graphs)
- **Testing:** pytest (for quality gates)
- **Linting:** ruff (for code quality)

## Core Algorithms

SDD includes battle-tested algorithms:

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

### Q: How do I install this in my project?

Clone the sdd repository into your project directory. Claude Code will automatically discover the commands from the `.claude/commands/` directory.

### Q: Do I need to install all the optional tools?

No. Quality gates gracefully skip when tools aren't available. Install only what you need for your project.

### Q: Can I use this with other AI assistants?

This is specifically designed for Claude Code's slash command system. It won't work with other AI tools without modification.

### Q: How much disk space does the .session directory use?

Typically 1-5 MB for most projects. It stores JSON files, text files, and small logs.

### Q: Can I customize work item types?

Currently, 6 built-in types are supported (feature, bug, refactor, security, integration_test, deployment). Custom types are planned for Phase 7.

### Q: Does this work with GitHub/GitLab?

Yes. It uses standard git commands and integrates with any git remote.

### Q: What happens if I forget to run /end?

Your work is still saved in git. You can manually update work items and tracking files, but you'll miss automated quality gates and learning extraction.

### Q: Can I use this on multiple projects?

Yes. Clone sdd into each project, or use symlinks from a single installation. Each project gets its own `.session/` directory with independent tracking.

## Troubleshooting

### /init fails with "Directory already exists"

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

### Commands fail with "Permission denied"

Make the CLI executable:
```bash
chmod +x sdd/sdd_cli.py
# Or if using symlink installation:
chmod +x ~/sdd/sdd_cli.py
```

### Commands fail with "ModuleNotFoundError"

Ensure you're running commands from your project root, not from within the `sdd/` directory. The CLI uses relative paths that work from the project root.

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
git clone https://github.com/ankushdixit/sdd.git
cd sdd

# Install development dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/

# Run specific phase tests
pytest tests/phase_1/
pytest tests/phase_5/test_phase_5_complete.py
```

## Credits

Built with insights from building complex software projects with Claude Code assistance.

Inspired by professional software development practices adapted for AI-augmented solo development.

---

**Ready for use!** Phases 0-5.6 complete with 343/343 tests passing.
