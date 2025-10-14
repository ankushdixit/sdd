# Claude Code Session Plugin

**Session-Driven Development for Claude Code** - Maintain perfect context across multiple AI coding sessions.

## Overview

This Claude Code plugin implements Session-Driven Development (SDD), a comprehensive methodology that enables AI coding assistants to work on software projects across multiple sessions with perfect context continuity, enforced quality standards, and accumulated institutional knowledge.

### The Problem

Traditional AI coding sessions suffer from:
- **Context loss** between sessions
- **Quality entropy** over time
- **Knowledge fragmentation** across interactions
- **Lack of process rigor**

### The Solution

SDD provides:
- **Perfect context continuity** through automated briefings
- **Quality enforcement** via automated validation gates
- **Knowledge accumulation** through learnings system
- **Dependency-driven workflow** (logical ordering, not arbitrary sequences)
- **Living documentation** that stays current

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

> **Note:** This is a personal development tool. Installation instructions will be added once Phase 1 is complete.

## Quick Start

> **Note:** Quick start guide will be added once core functionality is implemented.

## Documentation

- [Session-Driven Development Framework](docs/session-driven-development.md) - Complete methodology specification
- [AI-Augmented Solo Framework](docs/ai-augmented-solo-framework.md) - Philosophical context and broader methodology
- [Implementation Insights](docs/implementation-insights.md) - Lessons learned and proven patterns
- [Roadmap](ROADMAP.md) - Phased development plan
- **Implementation Plans:**
  - [Phases 0-4 (Foundation)](PLUGIN_IMPLEMENTATION_PLAN_PHASES_0-4.md) - ✅ Complete
  - [Phases 5+ (Quality & Operations)](PLUGIN_IMPLEMENTATION_PLAN_PHASES_5+.md) - In Progress

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

**Current Phase:** Phase 5 - Quality Gates (v0.5) ✅ **COMPLETE**

**Completed Phases:**
- ✅ **Phase 0:** Git Setup & Repository Initialization
- ✅ **Phase 1:** Core Plugin Foundation (Session workflow, stack/tree tracking, git integration)
- ✅ **Phase 2:** Work Item System (CRUD operations, dependencies, milestones)
- ✅ **Phase 3:** Visualization (Dependency graphs, critical path analysis)
- ✅ **Phase 4:** Learning Management (Auto-capture, AI categorization, similarity detection)
- ✅ **Phase 5:** Quality Gates (Test execution, security scanning, linting, formatting, documentation, Context7, custom rules)

**Next Phase:** Phase 5.5 - Integration & System Testing

### Roadmap

- [x] **Phase 1:** Core plugin structure with `/session-start` and `/session-end`
- [x] **Phase 2:** Work item management system
- [x] **Phase 3:** Dependency graph visualization
- [x] **Phase 4:** Learning capture and curation
- [x] **Phase 5:** Quality gates enhancement (test execution, security, linting, formatting, documentation, custom rules)
- [ ] **Phase 5.5:** Integration & system testing
- [ ] **Phase 6:** Documentation and polish

See [ROADMAP.md](ROADMAP.md) for detailed phase breakdown.

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

## Contributing

This is a personal development tool. Not currently accepting contributions.

## License

MIT License - See LICENSE file for details

## Credits

Built with insights from building complex software projects with Claude Code assistance.

Inspired by professional software development practices adapted for AI-augmented solo development.

---

**Status:** In active development. Not yet ready for production use.
