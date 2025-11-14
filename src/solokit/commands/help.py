"""
Help command for Solokit CLI.

Displays all available commands with descriptions, organized by category.
Also provides detailed help for specific commands.
"""

from __future__ import annotations

import sys
from typing import Any

from solokit.core.output import get_output

output = get_output()

# Command descriptions organized by category
COMMAND_CATEGORIES: dict[str, dict[str, str]] = {
    "Work Items Management": {
        "work-list": "List all work items with optional filtering",
        "work-show": "Display detailed information about a specific work item",
        "work-new": "Create a new work item interactively",
        "work-update": "Update fields of an existing work item",
        "work-delete": "Delete a work item from the system",
        "work-next": "Get the next recommended work item to start",
        "work-graph": "Generate dependency graph visualization",
    },
    "Session Management": {
        "start": "Start a new development session with comprehensive briefing",
        "end": "Complete the current session with quality gates and summary",
        "status": "Display current session status and progress",
        "validate": "Validate current session meets quality standards",
    },
    "Learning System": {
        "learn": "Capture a learning during development session",
        "learn-show": "Browse and filter captured learnings",
        "learn-search": "Search learnings by keyword",
        "learn-curate": "Run AI-powered learning curation process",
    },
    "Project Management": {
        "init": "Initialize a new Session-Driven Development project",
    },
    "Utilities": {
        "help": "Show help for commands",
        "version": "Show version information",
        "doctor": "Run comprehensive system diagnostics",
        "config": "Display and manage configuration",
    },
}

# Detailed help for specific commands
COMMAND_DETAILS: dict[str, dict[str, Any]] = {
    "work-list": {
        "description": "List all work items with optional filtering by status, type, or milestone.",
        "usage": "sk work-list [--status STATUS] [--type TYPE] [--milestone MILESTONE]",
        "options": [
            ("--status", "Filter by status (not_started, in_progress, blocked, completed)"),
            (
                "--type",
                "Filter by type (feature, bug, refactor, security, integration_test, deployment)",
            ),
            ("--milestone", "Filter by milestone name"),
        ],
        "examples": [
            "sk work-list",
            "sk work-list --status not_started",
            "sk work-list --type feature --priority high",
        ],
    },
    "work-show": {
        "description": "Display detailed information about a specific work item including specification, dependencies, and status.",
        "usage": "sk work-show <work_item_id>",
        "options": [],
        "examples": [
            "sk work-show feat_001",
            "sk work-show bug_fix_authentication",
        ],
    },
    "work-new": {
        "description": "Create a new work item with title, type, and priority.",
        "usage": "sk work-new --type TYPE --title TITLE --priority PRIORITY [--dependencies DEPS] [--urgent]",
        "options": [
            (
                "--type, -t",
                "Work item type (feature, bug, refactor, security, integration_test, deployment)",
            ),
            ("--title, -T", "Work item title (required)"),
            ("--priority, -p", "Priority level (critical, high, medium, low)"),
            ("--dependencies, -d", "Comma-separated list of dependency work item IDs"),
            ("--urgent", "Mark as urgent (only one item can be urgent at a time)"),
        ],
        "examples": [
            'sk work-new --type feature --title "Add user auth" --priority high',
            'sk work-new -t bug -T "Fix login error" -p critical',
            'sk work-new -t refactor -T "Improve queries" -p medium --dependencies feat_001',
            'sk work-new -t bug -T "Critical hotfix" -p critical --urgent',
        ],
    },
    "work-update": {
        "description": "Update fields of an existing work item such as status, priority, or dependencies.",
        "usage": "sk work-update <work_item_id> [OPTIONS]",
        "options": [
            ("--status", "Update status (not_started, in_progress, blocked, completed)"),
            ("--priority", "Update priority (critical, high, medium, low)"),
            ("--milestone", "Update milestone"),
            ("--add-dependency", "Add a dependency by work item ID"),
            ("--remove-dependency", "Remove a dependency by work item ID"),
            ("--set-urgent", "Mark item as urgent (only one can be urgent at a time)"),
            ("--clear-urgent", "Remove urgent flag from item"),
        ],
        "examples": [
            "sk work-update feat_001 --status in_progress",
            "sk work-update feat_001 --priority critical",
            "sk work-update feat_001 --add-dependency bug_002",
            "sk work-update feat_001 --set-urgent",
            "sk work-update feat_001 --clear-urgent",
        ],
    },
    "work-delete": {
        "description": "Delete a work item from the system permanently.",
        "usage": "sk work-delete <work_item_id>",
        "options": [],
        "examples": [
            "sk work-delete feat_001",
        ],
    },
    "work-next": {
        "description": "Get the next recommended work item to start based on dependencies and priority.",
        "usage": "sk work-next",
        "options": [],
        "examples": [
            "sk work-next",
        ],
    },
    "work-graph": {
        "description": "Generate a dependency graph visualization for work items.",
        "usage": "sk work-graph [OPTIONS]",
        "options": [
            ("--format", "Output format (dot, mermaid, ascii)"),
            ("--status", "Filter by status"),
            ("--milestone", "Filter by milestone"),
            ("--type", "Filter by type"),
            ("--focus", "Focus on specific work item ID"),
            ("--critical-path", "Show critical path only"),
            ("--bottlenecks", "Identify bottlenecks"),
            ("--stats", "Show statistics"),
            ("--output", "Output file path"),
        ],
        "examples": [
            "sk work-graph",
            "sk work-graph --format mermaid --focus feat_001",
            "sk work-graph --critical-path --output graph.dot",
        ],
    },
    "start": {
        "description": "Start a new development session with a comprehensive briefing including project context, work item specs, and relevant learnings.",
        "usage": "sk start [work_item_id]",
        "options": [],
        "examples": [
            "sk start",
            "sk start feat_001",
        ],
    },
    "end": {
        "description": "Complete the current development session, running quality gates, capturing learnings, and generating a session summary.",
        "usage": "sk end",
        "options": [],
        "examples": [
            "sk end",
        ],
    },
    "status": {
        "description": "Display current session status including work item progress, time tracking, and quality gate results.",
        "usage": "sk status",
        "options": [],
        "examples": [
            "sk status",
        ],
    },
    "validate": {
        "description": "Validate that the current session meets quality standards without ending the session.",
        "usage": "sk validate",
        "options": [],
        "examples": [
            "sk validate",
        ],
    },
    "learn": {
        "description": "Capture a learning during a development session. Records insights, best practices, and mistakes to avoid.",
        "usage": "sk learn",
        "options": [],
        "examples": [
            "sk learn",
        ],
    },
    "learn-show": {
        "description": "Browse and filter captured learnings by category, tag, or session.",
        "usage": "sk learn-show [--category CATEGORY] [--tag TAG] [--session SESSION]",
        "options": [
            ("--category", "Filter by category"),
            ("--tag", "Filter by tag"),
            ("--session", "Filter by session ID"),
        ],
        "examples": [
            "sk learn-show",
            "sk learn-show --category best_practices",
            "sk learn-show --tag authentication",
        ],
    },
    "learn-search": {
        "description": "Search learnings by keyword across all captured learnings.",
        "usage": "sk learn-search <query>",
        "options": [],
        "examples": [
            'sk learn-search "authentication"',
            'sk learn-search "database optimization"',
        ],
    },
    "learn-curate": {
        "description": "Run AI-powered curation process to extract, organize, and deduplicate learnings.",
        "usage": "sk learn-curate [--dry-run]",
        "options": [
            ("--dry-run", "Preview curation changes without applying them"),
        ],
        "examples": [
            "sk learn-curate",
            "sk learn-curate --dry-run",
        ],
    },
    "init": {
        "description": "Initialize a new Session-Driven Development project with templates and configuration.",
        "usage": "sk init",
        "options": [],
        "examples": [
            "sk init",
        ],
    },
    "version": {
        "description": "Display version information including Solokit version, Python version, and platform.",
        "usage": "sk version",
        "options": [],
        "examples": [
            "sk version",
            "sk --version",
            "sk -V",
        ],
    },
    "doctor": {
        "description": "Run comprehensive system diagnostics to verify setup and identify configuration issues.",
        "usage": "sk doctor",
        "options": [],
        "examples": [
            "sk doctor",
            "sk doctor --verbose",
        ],
    },
    "config": {
        "description": "Display current configuration with formatting and validation status.",
        "usage": "sk config show [--json]",
        "options": [
            ("--json", "Output configuration as JSON"),
        ],
        "examples": [
            "sk config show",
            "sk config show --json",
        ],
    },
}


def show_help() -> int:
    """
    Display all commands organized by category.

    Returns:
        Exit code (0 for success)
    """
    output.info("Usage: sk [--verbose] [--log-file FILE] <command> [args...]")
    output.info("")
    output.info("Global flags:")
    output.info("  --verbose, -v     Enable verbose DEBUG logging")
    output.info("  --log-file FILE   Write logs to file")
    output.info("  --version, -V     Show version information")
    output.info("  --help, -h        Show this help message")
    output.info("")

    for category, commands in COMMAND_CATEGORIES.items():
        output.info(f"{category}:")
        for cmd, desc in commands.items():
            output.info(f"  {cmd:18} {desc}")
        output.info("")

    output.info("For detailed help on a specific command:")
    output.info("  sk help <command>")
    output.info("")
    output.info("Examples:")
    output.info("  sk help work-new")
    output.info("  sk help start")
    output.info("")

    return 0


def show_command_help(command_name: str) -> int:
    """
    Display detailed help for a specific command.

    Args:
        command_name: Name of the command to show help for

    Returns:
        Exit code (0 for success, 1 for unknown command)
    """
    if command_name not in COMMAND_DETAILS:
        output.error(f"Unknown command: {command_name}")
        output.error("")
        output.error("Available commands:")
        for _category, commands in COMMAND_CATEGORIES.items():
            for cmd in commands:
                output.error(f"  {cmd}")
        output.error("")
        output.error("Run 'sk help' to see all commands with descriptions.")
        return 1

    details = COMMAND_DETAILS[command_name]

    output.info(f"Command: sk {command_name}")
    output.info("")
    output.info("Description:")
    output.info(f"  {details['description']}")
    output.info("")
    output.info("Usage:")
    output.info(f"  {details['usage']}")
    output.info("")

    if details.get("options"):
        output.info("Options:")
        for option, description in details["options"]:
            output.info(f"  {option:25} {description}")
        output.info("")

    if details.get("examples"):
        output.info("Examples:")
        for example in details["examples"]:
            output.info(f"  {example}")
        output.info("")

    return 0


def main() -> int:
    """
    Main entry point for help command.

    Parses arguments and shows either general help or command-specific help.

    Returns:
        Exit code (0 for success)
    """
    # Check if command-specific help was requested
    if len(sys.argv) > 1:
        command_name = sys.argv[1]
        return show_command_help(command_name)
    else:
        return show_help()


if __name__ == "__main__":
    sys.exit(main())
