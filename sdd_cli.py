#!/usr/bin/env python3
"""
SDD CLI Entry Point

Universal interface for all Session-Driven Development commands.
Solves module import issues by dynamically adding the plugin directory
to Python's path before importing any scripts.

Usage:
    sdd_cli.py <command> [args...]

Examples:
    sdd_cli.py work-list
    sdd_cli.py work-list --status not_started
    sdd_cli.py work-show feature_user_auth
    sdd_cli.py start
    sdd_cli.py learn-search "authentication"
"""

import argparse
import sys
from pathlib import Path

# CRITICAL: Add plugin directory to Python path BEFORE any imports
# This allows all scripts to import from 'scripts.module_name'
PLUGIN_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(PLUGIN_DIR))

# Import logging configuration
from scripts.logging_config import setup_logging  # noqa: E402

# Command routing table
# Format: 'command-name': (module_path, class_name, function_name, needs_argparse)
# - module_path: Python import path
# - class_name: Class to instantiate (None for standalone functions)
# - function_name: Method or function to call
# - needs_argparse: True if script has its own argparse handling
COMMANDS = {
    # Work Item Management (WorkItemManager class)
    "work-list": (
        "scripts.work_item_manager",
        "WorkItemManager",
        "list_work_items",
        False,
    ),
    "work-next": (
        "scripts.work_item_manager",
        "WorkItemManager",
        "get_next_work_item",
        False,
    ),
    "work-show": (
        "scripts.work_item_manager",
        "WorkItemManager",
        "show_work_item",
        False,
    ),
    "work-update": (
        "scripts.work_item_manager",
        "WorkItemManager",
        "update_work_item_interactive",
        False,
    ),
    "work-new": (
        "scripts.work_item_manager",
        "WorkItemManager",
        "create_work_item",
        False,
    ),
    # Dependency Graph (uses argparse in main)
    "work-graph": ("scripts.dependency_graph", None, "main", True),
    # Session Management (standalone main functions)
    "start": ("scripts.briefing_generator", None, "main", True),
    "end": ("scripts.session_complete", None, "main", True),
    "status": ("scripts.session_status", None, "get_session_status", False),
    "validate": ("scripts.session_validate", None, "main", True),
    # Learning System (uses argparse in main)
    "learn": ("scripts.learning_curator", None, "main", True),
    "learn-show": ("scripts.learning_curator", None, "main", True),
    "learn-search": ("scripts.learning_curator", None, "main", True),
    "learn-curate": ("scripts.learning_curator", None, "main", True),
    # Project Initialization
    "init": ("scripts.init_project", None, "init_project", False),
}


def parse_work_list_args(args):
    """Parse arguments for work-list command."""
    parser = argparse.ArgumentParser(description="List work items")
    parser.add_argument("--status", help="Filter by status")
    parser.add_argument("--type", help="Filter by type")
    parser.add_argument("--milestone", help="Filter by milestone")
    return parser.parse_args(args)


def parse_work_show_args(args):
    """Parse arguments for work-show command."""
    parser = argparse.ArgumentParser(description="Show work item details")
    parser.add_argument("work_id", help="Work item ID")
    return parser.parse_args(args)


def parse_work_new_args(args):
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
        default="high",
        help="Priority (critical, high, medium, low). Default: high",
    )
    parser.add_argument("--dependencies", "-d", default="", help="Comma-separated dependency IDs")
    return parser.parse_args(args)


def parse_work_update_args(args):
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


def route_command(command_name, args):
    """
    Route command to appropriate script/function.

    Args:
        command_name: Name of the command (e.g., 'work-list')
        args: List of command-line arguments

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    if command_name not in COMMANDS:
        print(f"Error: Unknown command '{command_name}'", file=sys.stderr)
        print(
            f"\nAvailable commands: {', '.join(sorted(COMMANDS.keys()))}",
            file=sys.stderr,
        )
        return 1

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
            return result if result is not None else 0

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
            elif isinstance(result, int):
                return result
            elif isinstance(result, bool):
                return 0 if result else 1
            else:
                return 0

        else:
            # Standalone function commands
            func = getattr(module, function_name)
            result = func()
            return result if result is not None else 0

    except ModuleNotFoundError as e:
        print(f"Error: Could not import module '{module_path}': {e}", file=sys.stderr)
        return 1
    except AttributeError as e:
        print(
            f"Error: Could not find function '{function_name}' in '{module_path}': {e}",
            file=sys.stderr,
        )
        return 1
    except Exception as e:
        print(f"Error executing command '{command_name}': {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


def main():
    """Main entry point for CLI."""
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
        print(
            "Usage: sdd_cli.py [--verbose] [--log-file FILE] <command> [args...]",
            file=sys.stderr,
        )
        print("\nGlobal flags:", file=sys.stderr)
        print("  --verbose, -v        Enable verbose (DEBUG) logging", file=sys.stderr)
        print("  --log-file FILE      Write logs to file", file=sys.stderr)
        print("\nAvailable commands:", file=sys.stderr)
        print("  Work Items:", file=sys.stderr)
        print(
            "    work-list, work-next, work-show, work-update, work-new, work-graph",
            file=sys.stderr,
        )
        print("  Sessions:", file=sys.stderr)
        print("    start, end, status, validate", file=sys.stderr)
        print("  Learnings:", file=sys.stderr)
        print("    learn, learn-show, learn-search, learn-curate", file=sys.stderr)
        print("  Initialization:", file=sys.stderr)
        print("    init", file=sys.stderr)
        return 1

    command = remaining[0]
    command_args = remaining[1:]

    exit_code = route_command(command, command_args)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
