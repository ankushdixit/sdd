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

- `/session-start` - Begin work session with comprehensive briefing
- `/session-end` - Complete session with quality gates and summary
- `/work-item` - Manage work items and dependencies
- `/learning` - Capture and curate project knowledge

### Key Capabilities

✅ **Stateful Development** - Perfect context handoffs between sessions
✅ **Quality Gates** - Tests, linting, formatting enforced before completion
✅ **Dependency Management** - Work items ordered by logical dependencies
✅ **Learning System** - Auto-categorized knowledge base with smart deduplication
✅ **Visualization** - Dependency graphs with critical path analysis
✅ **Git Integration** - Standardized commits with session summaries

## Installation

> **Note:** This is a personal development tool. Installation instructions will be added once Phase 1 is complete.

## Quick Start

> **Note:** Quick start guide will be added once core functionality is implemented.

## Documentation

- [Session-Driven Development Framework](docs/session-driven-development.md) - Complete methodology specification
- [AI-Augmented Solo Framework](docs/ai-augmented-solo-framework.md) - Philosophical context and broader methodology
- [Implementation Insights](docs/implementation-insights.md) - Lessons learned and proven patterns
- [Roadmap](ROADMAP.md) - Phased development plan
- [Implementation Plan](PLUGIN_IMPLEMENTATION_PLAN.md) - Detailed technical implementation guide

## Project Structure

```
claude-session-plugin/
├── .claude-plugin/           # Plugin configuration (to be created)
├── commands/                 # Slash command definitions (to be created)
├── scripts/                  # Core Python logic
│   ├── dependency_graph.py   # ✅ Dependency visualization (ready)
│   ├── learning_curator.py   # ✅ Learning management (ready)
│   └── file_ops.py           # ✅ Utilities (ready)
├── templates/                # JSON schema templates
├── docs/                     # Comprehensive documentation
├── ROADMAP.md               # Development roadmap
└── PLUGIN_IMPLEMENTATION_PLAN.md  # Implementation guide
```

## Development Status

**Current Phase:** Phase 0 - Git Setup & Repository Initialization ✅

**Next Phase:** Phase 1 - Basic Plugin Structure

### Roadmap

- [ ] **Phase 1:** Core plugin structure with `/session-start` and `/session-end`
- [ ] **Phase 2:** Work item management system
- [ ] **Phase 3:** Dependency graph visualization
- [ ] **Phase 4:** Learning capture and curation
- [ ] **Phase 5:** Quality gates enhancement
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
