#!/usr/bin/env python3
"""
SDD CLI Entry Point

Universal interface for all Session-Driven Development commands.

Usage:
    sdd <command> [args...]

Examples:
    sdd work-list
    sdd work-list --status not_started
    sdd work-show feature_user_auth
    sdd start
    sdd learn-search "authentication"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sdd.core.error_formatter import ErrorFormatter

# Import error handling infrastructure
from sdd.core.exceptions import (
    ErrorCode,
    SDDError,
    SystemError,
)

# Import logging configuration
from sdd.core.logging_config import get_logger, setup_logging
from sdd.core.output import get_output
from sdd.core.types import Priority

logger = get_logger(__name__)
output = get_output()

# Command routing table
# Format: 'command-name': (module_path, class_name, function_name, needs_argparse)
# - module_path: Python import path
# - class_name: Class to instantiate (None for standalone functions)
# - function_name: Method or function to call
# - needs_argparse: True if script has its own argparse handling
COMMANDS = {
    # Work Item Management (WorkItemManager class)
    "work-list": (
        "sdd.work_items.manager",
        "WorkItemManager",
        "list_work_items",
        False,
    ),
    "work-next": (
        "sdd.work_items.manager",
        "WorkItemManager",
        "get_next_work_item",
        False,
    ),
    "work-show": (
        "sdd.work_items.manager",
        "WorkItemManager",
        "show_work_item",
        False,
    ),
    "work-update": (
        "sdd.work_items.manager",
        "WorkItemManager",
        "update_work_item_interactive",
        False,
    ),
    "work-new": (
        "sdd.work_items.manager",
        "WorkItemManager",
        "create_work_item",
        False,
    ),
    "work-delete": ("sdd.work_items.delete", None, "main", True),
    # Dependency Graph (uses argparse in main)
    "work-graph": ("sdd.visualization.dependency_graph", None, "main", True),
    # Session Management (standalone main functions)
    "start": ("sdd.session.briefing", None, "main", True),
    "end": ("sdd.session.complete", None, "main", True),
    "status": ("sdd.session.status", None, "get_session_status", False),
    "validate": ("sdd.session.validate", None, "main", True),
    # Learning System (uses argparse in main)
    "learn": ("sdd.learning.curator", None, "main", True),
    "learn-show": ("sdd.learning.curator", None, "main", True),
    "learn-search": ("sdd.learning.curator", None, "main", True),
    "learn-curate": ("sdd.learning.curator", None, "main", True),
    # Project Initialization
    "init": ("sdd.project.init", None, "init_project", False),
}


def parse_work_list_args(args: list[str]) -> argparse.Namespace:
    """Parse arguments for work-list command."""
    parser = argparse.ArgumentParser(description="List work items")
    parser.add_argument("--status", help="Filter by status")
    parser.add_argument("--type", help="Filter by type")
    parser.add_argument("--milestone", help="Filter by milestone")
    return parser.parse_args(args)


def parse_work_show_args(args: list[str]) -> argparse.Namespace:
    """Parse arguments for work-show command."""
    parser = argparse.ArgumentParser(description="Show work item details")
    parser.add_argument("work_id", help="Work item ID")
    return parser.parse_args(args)


def parse_work_new_args(args: list[str]) -> argparse.Namespace:
    """Parse arguments for work-new command."""
    parser = argparse.ArgumentParser(description="Create a new work item")
    parser.add_argument(
        "--type",
        "-t",
        help="Work item type (feature, bug, refactor, security, integration_test, deployment)",
    )
    parser.add_argument("--title", "-T", help="Work item title")
    parser.add_argument(
        "--priority",
        "-p",
        default=Priority.HIGH.value,
        help="Priority (critical, high, medium, low). Default: high",
    )
    parser.add_argument("--dependencies", "-d", default="", help="Comma-separated dependency IDs")
    return parser.parse_args(args)


def parse_work_update_args(args: list[str]) -> argparse.Namespace:
    """Parse arguments for work-update command."""
    parser = argparse.ArgumentParser(description="Update work item fields")
    parser.add_argument("work_id", help="Work item ID")
    parser.add_argument(
        "--status", help="Update status (not_started/in_progress/blocked/completed)"
    )
    parser.add_argument("--priority", help="Update priority (critical/high/medium/low)")
    parser.add_argument("--milestone", help="Update milestone")
    parser.add_argument("--add-dependency", help="Add dependency by ID")
    parser.add_argument("--remove-dependency", help="Remove dependency by ID")
    return parser.parse_args(args)


def route_command(command_name: str, args: list[str]) -> int:
    """
    Route command to appropriate script/function.

    Args:
        command_name: Name of the command (e.g., 'work-list')
        args: List of command-line arguments

    Returns:
        Exit code (0 for success, non-zero for error)

    Raises:
        SystemError: If command is unknown or execution fails
    """
    if command_name not in COMMANDS:
        available = ", ".join(sorted(COMMANDS.keys()))
        raise SystemError(
            message=f"Unknown command '{command_name}'",
            code=ErrorCode.INVALID_COMMAND,
            context={"command": command_name, "available_commands": list(COMMANDS.keys())},
            remediation=f"Available commands: {available}",
        )

    module_path, class_name, function_name, needs_argparse = COMMANDS[command_name]

    try:
        # Import the module
        module = __import__(module_path, fromlist=[class_name or function_name])

        # Handle different command types
        if needs_argparse:
            # Scripts with argparse: set sys.argv and call main()
            # The script's own argparse will handle arguments
            if command_name in ["learn", "learn-show", "learn-search", "learn-curate"]:
                # Learning commands need special handling for subcommands
                if command_name == "learn":
                    sys.argv = ["learning_curator.py", "add-learning"] + args
                elif command_name == "learn-show":
                    sys.argv = ["learning_curator.py", "show-learnings"] + args
                elif command_name == "learn-search":
                    sys.argv = ["learning_curator.py", "search"] + args
                elif command_name == "learn-curate":
                    sys.argv = ["learning_curator.py", "curate"] + args
            else:
                # Other argparse commands (work-graph, start, end, validate)
                sys.argv = [command_name] + args

            func = getattr(module, function_name)
            result = func()
            return int(result) if result is not None else 0

        elif class_name:
            # Class-based commands: instantiate class and call method
            cls = getattr(module, class_name)
            instance = cls()
            method = getattr(instance, function_name)

            # Special argument handling for specific commands
            if command_name == "work-list":
                parsed = parse_work_list_args(args)
                result = method(
                    status_filter=parsed.status,
                    type_filter=parsed.type,
                    milestone_filter=parsed.milestone,
                )
            elif command_name == "work-show":
                parsed = parse_work_show_args(args)
                result = method(parsed.work_id)
            elif command_name == "work-next":
                result = method()
            elif command_name == "work-new":
                # Parse arguments
                parsed = parse_work_new_args(args)

                # Check if type and title are provided (non-interactive mode)
                if parsed.type and parsed.title:
                    # Non-interactive mode: use create_work_item_from_args
                    non_interactive_method = getattr(instance, "create_work_item_from_args")
                    result = non_interactive_method(
                        work_type=parsed.type,
                        title=parsed.title,
                        priority=parsed.priority,
                        dependencies=parsed.dependencies,
                    )
                else:
                    # Interactive mode: use create_work_item
                    result = method()
            elif command_name == "work-update":
                # Parse arguments
                parsed = parse_work_update_args(args)

                # Check if any flags are provided (non-interactive mode)
                has_flags = any(
                    [
                        parsed.status,
                        parsed.priority,
                        parsed.milestone,
                        parsed.add_dependency,
                        parsed.remove_dependency,
                    ]
                )

                if has_flags:
                    # Non-interactive mode: use update_work_item with kwargs
                    non_interactive_method = getattr(instance, "update_work_item")
                    kwargs = {}
                    if parsed.status:
                        kwargs["status"] = parsed.status
                    if parsed.priority:
                        kwargs["priority"] = parsed.priority
                    if parsed.milestone:
                        kwargs["milestone"] = parsed.milestone
                    if parsed.add_dependency:
                        kwargs["add_dependency"] = parsed.add_dependency
                    if parsed.remove_dependency:
                        kwargs["remove_dependency"] = parsed.remove_dependency

                    result = non_interactive_method(parsed.work_id, **kwargs)
                else:
                    # Interactive mode: use update_work_item_interactive
                    result = method(parsed.work_id)
            else:
                result = method()

            # Handle different return types
            if result is None:
                return 0
            elif isinstance(result, bool):
                return 0 if result else 1
            elif isinstance(result, int):
                return result
            else:
                return 0

        else:
            # Standalone function commands
            func = getattr(module, function_name)
            result = func()
            return int(result) if result is not None else 0

    except ModuleNotFoundError as e:
        raise SystemError(
            message=f"Could not import module '{module_path}'",
            code=ErrorCode.MODULE_NOT_FOUND,
            context={"module_path": module_path, "command": command_name},
            remediation="Check that the command is properly installed",
            cause=e,
        ) from e
    except AttributeError as e:
        raise SystemError(
            message=f"Could not find function '{function_name}' in module '{module_path}'",
            code=ErrorCode.FUNCTION_NOT_FOUND,
            context={"function": function_name, "module": module_path, "command": command_name},
            remediation="This appears to be an internal error - please report it",
            cause=e,
        ) from e
    except SDDError:
        # Re-raise SDDError exceptions to be caught by main()
        raise
    except Exception as e:
        # Wrap unexpected exceptions
        raise SystemError(
            message=f"Unexpected error executing command '{command_name}'",
            code=ErrorCode.COMMAND_FAILED,
            context={"command": command_name},
            cause=e,
        ) from e


def main() -> int:
    """
    Main entry point for CLI with centralized error handling.

    This function implements the standard error handling pattern:
    - Parse arguments
    - Route to command handlers
    - Catch all exceptions in centralized handler
    - Format errors using ErrorFormatter
    - Return appropriate exit codes

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    try:
        # Parse global flags first
        parser = argparse.ArgumentParser(
            description="Session-Driven Development CLI",
            add_help=False,  # Don't show help yet, let commands handle it
        )
        parser.add_argument(
            "--verbose",
            "-v",
            action="store_true",
            help="Enable verbose (DEBUG) logging",
        )
        parser.add_argument(
            "--log-file",
            type=str,
            help="Write logs to file",
        )

        # Parse known args (global flags) and leave rest for command routing
        args, remaining = parser.parse_known_args()

        # Setup logging based on global flags
        log_level = "DEBUG" if args.verbose else "INFO"
        log_file = Path(args.log_file) if args.log_file else None
        setup_logging(level=log_level, log_file=log_file)

        # Check if command is provided
        if len(remaining) < 1:
            output.error("Usage: sdd [--verbose] [--log-file FILE] <command> [args...]")
            output.error("\nGlobal flags:")
            output.error("  --verbose, -v        Enable verbose (DEBUG) logging")
            output.error("  --log-file FILE      Write logs to file")
            output.error("\nAvailable commands:")
            output.error("  Work Items:")
            output.error(
                "    work-list, work-next, work-show, work-update, work-new, work-delete, work-graph"
            )
            output.error("  Sessions:")
            output.error("    start, end, status, validate")
            output.error("  Learnings:")
            output.error("    learn, learn-show, learn-search, learn-curate")
            output.error("  Initialization:")
            output.error("    init")
            return 1

        command = remaining[0]
        command_args = remaining[1:]

        # Route command - will raise exceptions on error
        exit_code = route_command(command, command_args)
        return exit_code

    except SDDError as e:
        # Structured SDD errors with proper formatting
        ErrorFormatter.print_error(e, verbose=args.verbose if "args" in locals() else False)
        return e.exit_code

    except KeyboardInterrupt:
        # User cancelled operation
        output.error("\n\nOperation cancelled by user")
        return 130

    except Exception as e:
        # Unexpected errors - show full details
        ErrorFormatter.print_error(e, verbose=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
