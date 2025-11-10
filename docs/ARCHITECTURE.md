# Solokit Architecture Overview

Session-Driven Development (Solokit) is a structured workflow system for AI-augmented software development. This document provides a high-level overview of the system architecture.

## Core Concepts

### Session-Driven Workflow

Solokit organizes development work into discrete **sessions**, each focused on completing a single work item. A session follows this lifecycle:

1. **Start** (`/start`) - Creates a comprehensive briefing with project context
2. **Implementation** - AI and developer work together on the work item
3. **Validation** (`/validate`) - Checks quality gates are met
4. **End** (`/end`) - Captures learnings and updates work item status

### Work Items

Work items are the fundamental unit of work in Solokit. Each work item:

- Has a unique ID and type (feature, bug, refactor, security, integration_test, deployment)
- Contains a detailed specification in `.session/specs/{work_item_id}.md`
- Tracks status (not_started, in_progress, blocked, completed)
- Can have dependencies on other work items
- Belongs to optional milestones for grouping

### Learning System

Solokit automatically captures and curates knowledge from development sessions:

- **Capture** (`/learn`) - Record insights during development
- **Storage** - Learnings stored in `.session/learnings.json`
- **Curation** (`/learn-curate`) - AI extracts and organizes key insights
- **Retrieval** (`/learn-show`, `/learn-search`) - Query past learnings

## System Components

### CLI Entry Point

`src/solokit/cli.py` - Main command-line interface that routes commands to appropriate modules.

### Core Modules

Python package organized by domain in `src/solokit/`:

**Core (`solokit.core`):**
- **file_ops.py** - Centralized JSON file I/O operations with atomic writes, validation hooks, and consistent error handling
- **logging_config.py** - Logging configuration
- **config_validator.py** - Configuration validation

**Session Management (`solokit.session`):**
- **briefing.py** - Generates comprehensive session briefings
- **complete.py** - Handles session completion and learning capture
- **status.py** - Displays current session status
- **validate.py** - Validates quality gates

**Work Items (`solokit.work_items`):**
- **manager.py** - CRUD operations for work items
- **spec_parser.py** - Parses work item specifications
- **spec_validator.py** - Validates spec completeness

**Learning (`solokit.learning`):**
- **curator.py** - AI-powered learning extraction and organization

**Quality (`solokit.quality`):**
- **gates.py** - Test and validation execution
- **env_validator.py** - Environment validation
- **api_validator.py** - API contract validation

**Visualization (`solokit.visualization`):**
- **dependency_graph.py** - Visualizes work item dependencies

**Git Integration (`solokit.git`):**
- **integration.py** - Git branch and status management

**Testing (`solokit.testing`):**
- **integration_runner.py** - Integration test execution
- **performance.py** - Performance benchmarking

**Deployment (`solokit.deployment`):**
- **executor.py** - Deployment execution

**Project (`solokit.project`):**
- **init.py** - Project initialization
- **stack.py** - Technology stack generation
- **tree.py** - Project tree generation
- **sync_plugin.py** - Plugin synchronization

### Configuration

- `.session/config.json` - Project configuration
- `src/solokit/templates/config.schema.json` - Configuration schema

### Session State

Located in `.session/`:

- `work_items.json` - All work item metadata
- `learnings.json` - Captured learnings
- `specs/` - Work item specifications
- `briefings/` - Generated session briefings
- `status/` - Session status updates

### Templates

Located in `templates/`:

- Work item spec templates (feature, bug, refactor, security, etc.)
- Test setup templates for Python, JavaScript, TypeScript
- Configuration templates

## Data Flow

### Session Start

```
User runs /start
  → briefing_generator.py
    → Loads project context (stack, tree, git status)
    → Selects next work item (or uses specified ID)
    → Loads spec from .session/specs/{id}.md
    → Validates spec completeness
    → Retrieves relevant learnings
    → Creates git branch
    → Generates comprehensive briefing
    → Updates work item status to in_progress
  → Returns briefing to AI/user
```

### Session End

```
User runs /end
  → session_complete.py
    → Runs quality gates (tests, linting)
    → Validates all acceptance criteria met
    → Captures learnings (/learn prompts)
    → Updates work item status to completed
    → Records session metrics
    → Updates git branch status
    → Generates session summary
  → Returns summary to user
```

### Learning Curation

```
User runs /learn-curate
  → learning_curator.py
    → Loads all learnings
    → Groups by category
    → Uses AI to extract key insights
    → Removes duplicates and test data
    → Generates structured learning entries
    → Updates learnings.json
  → Returns curation report
```

## Integration Points

### Git Integration

- Automatic branch creation per session (`session-NNN-{work_item_id}`)
- Git status tracking for work items
- Branch status finalization on completion

### GitHub Integration

- Issue template integration
- GitHub Actions workflows (pre-commit, tests, plugin sync)
- Pull request workflows

### Testing

- pytest for Python tests
- Integration test framework
- Quality gate validation

### Claude Code Integration

Slash commands in `.claude/commands/` map to Solokit CLI commands, enabling seamless AI-assisted development.

## Design Principles

1. **Spec-First Architecture** - Specifications are the single source of truth
2. **Session Isolation** - Each session is self-contained and focused
3. **Learning Accumulation** - Knowledge is captured and reused across sessions
4. **Quality Gates** - Automated validation ensures consistency
5. **AI Augmentation** - AI assists but doesn't replace developer judgment
6. **Git-Centric** - Git tracks all work and maintains history
7. **Type Safety** - Typed work items enable advanced querying and filtering

## Further Reading

- [Solokit Methodology](architecture/solokit-methodology.md)
- [AI-Augmented Solo Framework](architecture/ai-augmented-solo-framework.md)
- [Implementation Insights](architecture/implementation-insights.md)
- [Configuration Guide](guides/configuration.md)
- [Writing Specifications](guides/writing-specs.md)
