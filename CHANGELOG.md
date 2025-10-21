# Changelog

All notable changes to the SDD (Session-Driven Development) project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Spec-Kit integration (Phase 6)
- Advanced features and polish (Phase 7)
- Package distribution via PyPI

---

## [0.5.8] - 2025-10-21

### Added
- **Marketplace Plugin Support**: SDD now works as a Claude Code marketplace plugin
- One-time setup command for plugin users: `pip install -e ~/.claude/plugins/marketplaces/claude-plugins/sdd`
- Simplified installation documentation with clear paths for both marketplace and direct installation

### Changed
- **Unified CLI**: All 15 slash command files now use `sdd` command instead of relative paths
- Updated command files: `init.md`, `start.md`, `end.md`, `status.md`, `validate.md`, `learn*.md`, `work-*.md`
- Simplified README installation section with two clear options (marketplace vs. direct)
- Updated all CLI examples throughout documentation to use `sdd` command
- Updated marketplace README (`claude-plugins/README.md`) with v0.5.8 installation instructions
- Updated Architecture Notes to reflect v0.5.8 changes

### Technical Details
- **Files Modified**: 18 files total
  - 15 command files (`.claude/commands/*.md`)
  - 1 main README (`README.md`)
  - 1 marketplace README (in separate repo)
  - 1 pyproject.toml (version bump)
- **Breaking Changes**: Command files no longer use `python3 scripts/../sdd_cli.py` - now use `sdd` CLI
- **Migration**: Users must run `pip install -e .` if not already done

### Migration Guide

**For marketplace plugin users:**
```bash
pip install -e ~/.claude/plugins/marketplaces/claude-plugins/sdd
```

**For existing direct installations:**
```bash
cd /path/to/sdd
pip install -e .
```

All slash commands will now work via the `sdd` CLI.

### Benefits
- ✅ Plugin works from marketplace installation
- ✅ No need to clone SDD into every project
- ✅ Cleaner, more standard approach
- ✅ Works identically whether installed directly or via marketplace
- ✅ Aligns with Python package best practices

### Reference
See [ROADMAP.md Phase 5.8](./ROADMAP.md#phase-58-marketplace-plugin-support-v058---unified-cli) for complete details.

---

## [0.5.7] - 2025-10-18

### Added
- **Spec-first architecture**: `.session/specs/*.md` files are now the single source of truth for work item content
- Comprehensive markdown parser (`spec_parser.py`, 700+ lines) supporting all 6 work item types
- Spec file validation system with required section checks and quality gates
- Complete context loading - removed all compression (50-line tree limit, 500-char doc limits)
- Writing guide (`docs/writing-specs.md`, 500+ lines) with examples for all work item types
- Template structure documentation (`docs/spec-template-structure.md`)

### Changed
- Eliminated dual storage problem - work item content now only in spec files, not `work_items.json`
- Enhanced all 6 spec templates with comprehensive examples and inline guidance
- Updated briefing system to load full spec content without truncation
- Refactored validators and runners to use spec parser
- Quality gates now validate spec completeness before session completion

### Removed
- Content fields from `work_items.json` (rationale, acceptance_criteria, implementation_paths, test_paths)
- Compression limits on project documentation
- Duplicate briefing sections

### Technical Details
- **Tests Added**: 49 tests across 6 test files
- **Code Added**: ~3,200 lines (spec_parser.py, spec_validator.py, templates, docs)
- **Files Created**: 8 new files (validator, docs, test files)
- **Files Enhanced**: 12 files (briefing_generator, quality_gates, templates, commands)

### Reference
See [ROADMAP.md Phase 5.7](./ROADMAP.md#phase-57-spec-file-first-architecture-v057---single-source-of-truth) for complete details.

---

## [0.5.6] - 2025-10-15

### Added
- **Deployment work item type** with comprehensive validation framework
- Deployment execution framework with pre-deployment validation and rollback automation
- Environment validation system with 7 validation types (connectivity, configuration, dependencies, health checks, monitoring, infrastructure, capacity)
- Deployment quality gates integrated with `quality_gates.py`
- Multi-environment support (staging vs production with different configurations)
- Automated smoke test execution with timeout and retry support
- Dry-run mode for deployment simulation

### Changed
- Enhanced `deployment_spec.md` template with 11 sections including deployment procedure, rollback, smoke tests
- Session workflow now includes deployment-specific briefings and summaries
- Quality gates include deployment validation before execution

### Technical Details
- **Tests Added**: 65 tests across 5 test files
- **Code Added**: ~2,049 lines (deployment_executor.py, environment_validator.py, enhanced templates)
- **Validation Types**: 7 comprehensive environment checks
- **Focus**: Production deployment safety and automation

### Reference
See [ROADMAP.md Phase 5.6](./ROADMAP.md#phase-56-deployment--launch-v056---deployment-support) for complete details.

---

## [0.5.5] - 2025-10-15

### Added
- **Integration testing framework** with comprehensive validation
- Enhanced integration test work item type with multi-component dependency tracking
- Integration test execution framework with Docker Compose orchestration
- Performance benchmarking system with regression detection (10% threshold)
- API contract validation with breaking change detection
- Integration quality gates with environment validation
- Integration documentation requirements (architecture diagrams, sequence diagrams, API contracts)

### Changed
- Enhanced `integration_test_spec.md` template with test scenarios, performance benchmarks
- Session workflow includes integration-specific briefings and summaries
- Quality gates validate integration test environment before execution

### Technical Details
- **Tests Added**: 178 tests across 7 test files
- **Code Added**: ~5,458 lines (integration_test_runner.py, performance_benchmark.py, api_contract_validator.py)
- **Performance Tracking**: Latency percentiles (p50, p75, p90, p95, p99), throughput, response time
- **Focus**: Multi-service integration validation and performance regression detection

### Reference
See [ROADMAP.md Phase 5.5](./ROADMAP.md#phase-55-integration--system-testing-v055---testing-support) for complete details.

---

## [0.5] - 2025-10-14

### Added
- **Quality gates system** for automated quality enforcement at session completion
- Test execution with coverage parsing and multi-language support (Python, JavaScript, TypeScript)
- Security scanning integration (bandit, safety, npm audit) with severity-based filtering
- Linting and formatting with auto-fix modes (ruff, eslint, prettier)
- Documentation validation (CHANGELOG, docstrings, README)
- Context7 MCP integration (stub ready for production)
- Custom validation rules (per-work-item and project-level)
- Quality gate reporting with remediation guidance

### Changed
- Session completion now enforces quality standards before allowing completion
- Extracted quality gate logic into dedicated `quality_gates.py` module (770 lines)
- Added quality gates configuration to `.session/config.json` during `/init`

### Fixed
- pytest exit code 5 ("no tests collected") now treated as skipped, not failed
- Auto-fix modes for linting and formatting improve developer experience

### Technical Details
- **Tests Added**: 54 tests across all quality gate types
- **Code Added**: 875 lines (quality_gates.py, config integration)
- **Tools Supported**: pytest, ruff, bandit, safety, eslint, prettier, npm audit
- **Configuration**: Required vs optional gate enforcement

### Reference
See [ROADMAP.md Phase 5](./ROADMAP.md#phase-5-quality-gates-v05---validation--security) for complete details.

---

## [0.4] - 2025-10-14

### Added
- **Learning capture and curation system** for knowledge management
- 4 learning commands: `/learn`, `/learn-show`, `/learn-search`, `/learn-curate`
- Auto-categorization into 6 categories (architecture_patterns, gotchas, best_practices, technical_debt, performance_insights, security)
- Similarity detection using Jaccard (0.6) and containment (0.8) thresholds
- Automatic duplicate detection and merging
- Multi-source learning extraction (session summaries, git commits with `LEARNING:`, inline `# LEARNING:` comments)
- Enhanced browsing with filters (category, tags, date range, session number)
- Statistics dashboard and timeline view
- Auto-curation trigger every N sessions (default 5, configurable)

### Changed
- Sessions now include automated learning capture at completion
- `.session/config.json` includes learning configuration (auto_curate_frequency, similarity_threshold)

### Technical Details
- **Tests Added**: 53 tests across all learning features
- **Code Added**: ~1,587 lines (commands, documentation, integration)
- **Documentation**: `docs/learning-system.md` guide (550 lines)
- **Categories**: 6 comprehensive categories covering software development learnings

### Reference
See [ROADMAP.md Phase 4](./ROADMAP.md#phase-4-learning-management-v04---knowledge-capture) for complete details.

---

## [0.3] - 2025-10-13

### Added
- **Work item dependency graph visualization** with critical path analysis
- `/work-graph` command with multiple output formats (ASCII, DOT, SVG)
- Graph filtering options (status, milestone, type, focus node, include-completed)
- Critical path analysis with automatic highlighting in all formats
- Bottleneck detection (items blocking 2+ others)
- Graph statistics (total items, completion percentage, critical path length)
- Neighborhood view with `--focus` for exploring specific work items

### Changed
- Enhanced `dependency_graph.py` with 313 new lines for CLI integration
- Graph visualization updates automatically when work items change

### Technical Details
- **Tests Added**: 36 tests across 6 sections
- **Code Added**: 426 lines (command integration, enhanced graph features)
- **Formats**: ASCII (terminal-friendly), DOT (Graphviz), SVG (documentation)
- **Focus**: Understanding project structure and identifying bottlenecks

### Reference
See [ROADMAP.md Phase 3](./ROADMAP.md#phase-3-visualization-v03---dependency-graphs) for complete details.

---

## [0.2] - 2025-10-13

### Added
- **Work item management system** with full CRUD operations
- 6 work item types (feature, bug, refactor, security, integration_test, deployment)
- 5 work item commands: `/work-new`, `/work-list`, `/work-show`, `/work-update`, `/work-next`
- Dependency tracking and resolution
- Priority levels (critical, high, medium, low) with visual indicators (🔴🟠🟡🟢)
- Milestone organization and progress tracking
- Status tracking (backlog, in_progress, completed, blocked)
- Conversational interface for work item creation (Claude Code compatible)

### Changed
- Sessions now include comprehensive work item tracking
- Briefings include milestone context and dependency status
- `/status` command shows work item context and progress

### Technical Details
- **Tests Added**: 9 tests for work item management
- **Code Added**: `work_item_manager.py` (500+ lines)
- **CLI Commands**: Non-interactive mode for Claude Code compatibility
- **Storage**: JSON-based work item tracking in `.session/work_items.json`

### Reference
See [ROADMAP.md Phase 2](./ROADMAP.md#phase-2-work-item-system-v02---task-management) for complete details.

---

## [0.1] - 2025-10-13

### Added
- **Core session management framework** with complete workflow
- `/init` command for project initialization
- Stack tracking system (`generate_stack.py`) with technology detection
- Tree tracking system (`generate_tree.py`) with structure change detection
- Git workflow integration (`git_integration.py`) with branch management
- Enhanced `/start` with comprehensive context loading (docs, stack, tree, git)
- Enhanced `/end` with tracking updates and quality gates
- `/validate` command for pre-flight checks before session completion
- Multi-session work item support (resume on same branch)

### Changed
- Session initialization creates `.session/` directory structure
- Briefings include full project context (vision, architecture, stack, tree)
- Session completion updates all tracking files automatically

### Technical Details
- **Tests Added**: 6 core tests
- **Code Added**: 2,174 lines across 12 scripts
- **Infrastructure**: `.session/` directory with tracking files
- **Git Integration**: Automatic branch creation, commit, push, merge

### Reference
See [ROADMAP.md Phase 1](./ROADMAP.md#phase-1-core-plugin-foundation-v01---essential-session-workflow) for complete details.

---

## [0.0] - 2025-10-10

### Added
- **Foundation and documentation** for Session-Driven Development methodology
- Repository structure with `.claude/commands/` directory (16 slash commands)
- Basic briefing generation (`briefing_generator.py`)
- Basic session completion (`session_complete.py`)
- Learning curation system (`learning_curator.py`) - complete and production-ready
- Dependency graph visualization (`dependency_graph.py`) - complete and production-ready
- File operation utilities (`file_ops.py`)
- Comprehensive methodology documentation (`docs/session-driven-development.md`)
- Implementation insights documentation (`docs/implementation-insights.md`)
- AI-augmented framework reference (`docs/ai-augmented-solo-framework.md`)

### Technical Details
- **Work Item Schema**: Defined in `templates/work_items.json`
- **Learning Schema**: Defined in `templates/learnings.json`
- **Algorithms**: Dependency resolution (DFS-based), Learning categorization (keyword-based), Similarity detection (Jaccard + containment)

### Reference
See [ROADMAP.md Phase 0](./ROADMAP.md#phase-0-foundation--documentation-v00---complete) for complete details.

---

## Version Numbering

Versions follow semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

Phase mapping to versions:
- Phase 0 = v0.0
- Phase 1 = v0.1
- Phase 2 = v0.2
- Phase 3 = v0.3
- Phase 4 = v0.4
- Phase 5 = v0.5
- Phase 5.5 = v0.5.5
- Phase 5.6 = v0.5.6
- Phase 5.7 = v0.5.7
- Phase 6 = v0.6 (planned)
- Phase 7 = v0.7+ (planned)
- Future v1.0.0 = Production-ready release

## Links

- [Roadmap](./ROADMAP.md) - Detailed development history and technical implementation
- [Contributing](./CONTRIBUTING.md) - How to contribute (if available)
- [Documentation](./docs/) - Full documentation
- [Session-Driven Development Methodology](./docs/session-driven-development.md) - Complete methodology specification
