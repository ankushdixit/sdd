"""
Centralized constants and configuration values for Solokit

This module contains all magic numbers, default values, paths, and
configuration constants used throughout the Solokit codebase.
"""

from pathlib import Path
from typing import Final

# ============================================================================
# Directory and Path Constants
# ============================================================================

# Session directory name
SESSION_DIR_NAME: Final[str] = ".session"

# Subdirectories within session directory
TRACKING_DIR_NAME: Final[str] = "tracking"
SPECS_DIR_NAME: Final[str] = "specs"
CONFIG_DIR_NAME: Final[str] = "config"
LEARNINGS_DIR_NAME: Final[str] = "learnings"
BRIEFINGS_DIR_NAME: Final[str] = "briefings"
STATUS_DIR_NAME: Final[str] = "status"

# Tracking file names
WORK_ITEMS_FILE: Final[str] = "work_items.json"
LEARNINGS_FILE: Final[str] = "learnings.json"
STATUS_UPDATE_FILE: Final[str] = "status_update.json"
SESSIONS_FILE: Final[str] = "sessions.json"
CONFIG_FILE: Final[str] = "config.json"

# ============================================================================
# Git Operation Timeouts (in seconds)
# ============================================================================

# Quick git operations (status, diff, log)
GIT_QUICK_TIMEOUT: Final[int] = 5

# Standard git operations (add, commit)
GIT_STANDARD_TIMEOUT: Final[int] = 10

# Long-running git operations (push, pull, clone)
GIT_LONG_TIMEOUT: Final[int] = 30

# ============================================================================
# Learning Curator Constants
# ============================================================================

# Maximum age of learnings before archiving (in sessions)
MAX_LEARNING_AGE_SESSIONS: Final[int] = 50

# Auto-curation threshold (number of uncategorized learnings)
AUTO_CURATE_THRESHOLD: Final[int] = 10

# Similarity thresholds for learning deduplication
JACCARD_SIMILARITY_THRESHOLD: Final[float] = 0.6
CONTAINMENT_SIMILARITY_THRESHOLD: Final[float] = 0.8

# Minimum similarity score for related learnings
MIN_RELATED_SIMILARITY: Final[float] = 0.3

# ============================================================================
# Session and Briefing Constants
# ============================================================================

# Maximum spec keywords to display
MAX_SPEC_KEYWORDS: Final[int] = 500

# Maximum number of recent learnings to show in briefing
MAX_RECENT_LEARNINGS: Final[int] = 10

# Maximum number of recent commits to show
MAX_RECENT_COMMITS: Final[int] = 20

# Maximum work items to show in status
MAX_STATUS_WORK_ITEMS: Final[int] = 15

# ============================================================================
# Quality Gate Constants
# ============================================================================

# Minimum test coverage percentage
MIN_TEST_COVERAGE: Final[float] = 80.0

# Maximum cyclomatic complexity per function
MAX_CYCLOMATIC_COMPLEXITY: Final[int] = 10

# Maximum line length
MAX_LINE_LENGTH: Final[int] = 100

# ============================================================================
# Performance Testing Constants
# ============================================================================

# Default performance regression threshold (1.1 = 10% slower)
PERFORMANCE_REGRESSION_THRESHOLD: Final[float] = 1.1

# Performance test timeout
PERFORMANCE_TEST_TIMEOUT: Final[int] = 10

# Number of warmup runs for performance tests
PERFORMANCE_WARMUP_RUNS: Final[int] = 3

# Number of measurement runs for performance tests
PERFORMANCE_MEASUREMENT_RUNS: Final[int] = 10

# ============================================================================
# API and HTTP Constants
# ============================================================================

# Default HTTP request timeout
HTTP_REQUEST_TIMEOUT: Final[int] = 5

# API endpoint timeout
API_ENDPOINT_TIMEOUT: Final[int] = 10

# ============================================================================
# Work Item Constants
# ============================================================================

# Work item types
WORK_ITEM_TYPES: Final[tuple[str, ...]] = (
    "feature",
    "bug",
    "refactor",
    "security",
    "integration_test",
    "deployment",
)

# Priority levels (in order from highest to lowest)
PRIORITY_LEVELS: Final[tuple[str, ...]] = (
    "critical",
    "high",
    "medium",
    "low",
)

# Work item statuses
WORK_ITEM_STATUSES: Final[tuple[str, ...]] = (
    "not_started",
    "in_progress",
    "completed",
    "blocked",
)

# Maximum work item ID length (for slug generation)
MAX_WORK_ITEM_ID_LENGTH: Final[int] = 40

# ============================================================================
# CLI and User Interface Constants
# ============================================================================

# Minimum arguments for CLI commands
MIN_CLI_ARGS: Final[int] = 1

# Progress bar length
PROGRESS_BAR_LENGTH: Final[int] = 20

# ============================================================================
# File Size and Limit Constants
# ============================================================================

# Maximum file size for parsing (in bytes) - 10MB
MAX_FILE_SIZE_BYTES: Final[int] = 10 * 1024 * 1024

# Maximum number of files to process in batch
MAX_BATCH_FILE_COUNT: Final[int] = 100

# ============================================================================
# Subprocess and Process Constants
# ============================================================================

# Default subprocess timeout (for general operations)
DEFAULT_SUBPROCESS_TIMEOUT: Final[int] = 10

# Exit codes
EXIT_SUCCESS: Final[int] = 0
EXIT_FAILURE: Final[int] = 1

# ============================================================================
# Quality Gate Timeouts (in seconds)
# ============================================================================

# Quick quality checks (version checks, git operations)
QUALITY_CHECK_QUICK_TIMEOUT: Final[int] = 5

# Standard quality checks (linting, formatting)
QUALITY_CHECK_STANDARD_TIMEOUT: Final[int] = 60

# Long-running quality checks (formatting tools, complex linting)
QUALITY_CHECK_LONG_TIMEOUT: Final[int] = 60

# Very long quality checks (full formatting, security scans)
QUALITY_CHECK_VERY_LONG_TIMEOUT: Final[int] = 120

# Test runner timeout (20 minutes for full test suites)
TEST_RUNNER_TIMEOUT: Final[int] = 1200

# ============================================================================
# Integration Testing Timeouts (in seconds)
# ============================================================================

# Docker command timeout (ps, version checks)
DOCKER_COMMAND_TIMEOUT: Final[int] = 5

# Docker compose up/down timeout
DOCKER_COMPOSE_TIMEOUT: Final[int] = 180

# Fixture setup timeout
FIXTURE_SETUP_TIMEOUT: Final[int] = 30

# Integration test execution timeout (10 minutes)
INTEGRATION_TEST_TIMEOUT: Final[int] = 600

# Cleanup operation timeout
CLEANUP_TIMEOUT: Final[int] = 60

# ============================================================================
# Session and Workflow Timeouts (in seconds)
# ============================================================================

# Session status checks
SESSION_STATUS_TIMEOUT: Final[int] = 5

# Session completion operations
SESSION_COMPLETE_TIMEOUT: Final[int] = 30

# Learning extraction timeout
LEARNING_EXTRACTION_TIMEOUT: Final[int] = 60

# Briefing generation timeout
BRIEFING_GENERATION_TIMEOUT: Final[int] = 30

# ============================================================================
# Project Initialization Timeouts (in seconds)
# ============================================================================

# Stack detection timeout (quick check)
STACK_DETECTION_TIMEOUT: Final[int] = 2

# Tree generation timeout
TREE_GENERATION_TIMEOUT: Final[int] = 30

# Dependency graph generation timeout
DEPENDENCY_GRAPH_TIMEOUT: Final[int] = 30

# ============================================================================
# Helper Functions
# ============================================================================


def get_session_dir(project_root: Path) -> Path:
    """Get the session directory path for a project"""
    return project_root / SESSION_DIR_NAME


def get_tracking_dir(project_root: Path) -> Path:
    """Get the tracking directory path for a project"""
    return get_session_dir(project_root) / TRACKING_DIR_NAME


def get_specs_dir(project_root: Path) -> Path:
    """Get the specs directory path for a project"""
    return get_session_dir(project_root) / SPECS_DIR_NAME


def get_briefings_dir(project_root: Path) -> Path:
    """Get the briefings directory path for a project"""
    return get_session_dir(project_root) / BRIEFINGS_DIR_NAME


def get_status_dir(project_root: Path) -> Path:
    """Get the status directory path for a project"""
    return get_session_dir(project_root) / STATUS_DIR_NAME


def get_work_items_file(project_root: Path) -> Path:
    """Get the work items file path"""
    return get_tracking_dir(project_root) / WORK_ITEMS_FILE


def get_learnings_file(project_root: Path) -> Path:
    """Get the learnings file path"""
    return get_tracking_dir(project_root) / LEARNINGS_FILE


def get_config_file(project_root: Path) -> Path:
    """Get the config file path"""
    return get_session_dir(project_root) / CONFIG_FILE
