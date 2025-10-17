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

import sys
import argparse
from pathlib import Path

# CRITICAL: Add plugin directory to Python path BEFORE any imports
# This allows all scripts to import from 'scripts.module_name'
PLUGIN_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(PLUGIN_DIR))


# Command routing table
# Format: 'command-name': (module_path, class_name, function_name, needs_argparse)
# - module_path: Python import path
# - class_name: Class to instantiate (None for standalone functions)
# - function_name: Method or function to call
# - needs_argparse: True if script has its own argparse handling
COMMANDS = {
    # Work Item Management (WorkItemManager class)
    'work-list': ('scripts.work_item_manager', 'WorkItemManager', 'list_work_items', False),
    'work-next': ('scripts.work_item_manager', 'WorkItemManager', 'get_next_work_item', False),
    'work-show': ('scripts.work_item_manager', 'WorkItemManager', 'show_work_item', False),
    'work-update': ('scripts.work_item_manager', 'WorkItemManager', 'update_work_item_interactive', False),
    'work-new': ('scripts.work_item_manager', 'WorkItemManager', 'create_work_item', False),

    # Dependency Graph (uses argparse in main)
    'work-graph': ('scripts.dependency_graph', None, 'main', True),

    # Session Management (standalone main functions)
    'start': ('scripts.briefing_generator', None, 'main', True),
    'end': ('scripts.session_complete', None, 'main', True),
    'status': ('scripts.session_status', None, 'get_session_status', False),
    'validate': ('scripts.session_validate', None, 'main', True),

    # Learning System (uses argparse in main)
    'learn': ('scripts.learning_curator', None, 'main', True),
    'learn-show': ('scripts.learning_curator', None, 'main', True),
    'learn-search': ('scripts.learning_curator', None, 'main', True),
    'learn-curate': ('scripts.learning_curator', None, 'main', True),

    # Project Initialization
    'init': ('scripts.init_project', None, 'init_project', False),
}


def parse_work_list_args(args):
    """Parse arguments for work-list command."""
    parser = argparse.ArgumentParser(description='List work items')
    parser.add_argument('--status', help='Filter by status')
    parser.add_argument('--type', help='Filter by type')
    parser.add_argument('--milestone', help='Filter by milestone')
    return parser.parse_args(args)


def parse_work_show_args(args):
    """Parse arguments for work-show command."""
    parser = argparse.ArgumentParser(description='Show work item details')
    parser.add_argument('work_id', help='Work item ID')
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
        print(f"\nAvailable commands: {', '.join(sorted(COMMANDS.keys()))}", file=sys.stderr)
        return 1

    module_path, class_name, function_name, needs_argparse = COMMANDS[command_name]

    try:
        # Import the module
        module = __import__(module_path, fromlist=[class_name or function_name])

        # Handle different command types
        if needs_argparse:
            # Scripts with argparse: set sys.argv and call main()
            # The script's own argparse will handle arguments
            if command_name in ['learn', 'learn-show', 'learn-search', 'learn-curate']:
                # Learning commands need special handling for subcommands
                if command_name == 'learn':
                    sys.argv = ['learning_curator.py', 'add-learning'] + args
                elif command_name == 'learn-show':
                    sys.argv = ['learning_curator.py', 'show-learnings'] + args
                elif command_name == 'learn-search':
                    sys.argv = ['learning_curator.py', 'search'] + args
                elif command_name == 'learn-curate':
                    sys.argv = ['learning_curator.py', 'curate'] + args
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
            if command_name == 'work-list':
                parsed = parse_work_list_args(args)
                result = method(
                    status_filter=parsed.status,
                    type_filter=parsed.type,
                    milestone_filter=parsed.milestone
                )
            elif command_name == 'work-show':
                parsed = parse_work_show_args(args)
                result = method(parsed.work_id)
            elif command_name == 'work-next':
                result = method()
            elif command_name == 'work-new':
                result = method()
            elif command_name == 'work-update':
                # Interactive mode - expects work_id as first arg
                if args:
                    result = method(args[0])
                else:
                    print("Error: work-update requires a work item ID", file=sys.stderr)
                    return 1
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
        print(f"Error: Could not find function '{function_name}' in '{module_path}': {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error executing command '{command_name}': {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main entry point for CLI."""
    if len(sys.argv) < 2:
        print("Usage: sdd_cli.py <command> [args...]", file=sys.stderr)
        print(f"\nAvailable commands:", file=sys.stderr)
        print("  Work Items:", file=sys.stderr)
        print("    work-list, work-next, work-show, work-update, work-new, work-graph", file=sys.stderr)
        print("  Sessions:", file=sys.stderr)
        print("    start, end, status, validate", file=sys.stderr)
        print("  Learnings:", file=sys.stderr)
        print("    learn, learn-show, learn-search, learn-curate", file=sys.stderr)
        print("  Initialization:", file=sys.stderr)
        print("    init", file=sys.stderr)
        return 1

    command = sys.argv[1]
    args = sys.argv[2:]

    exit_code = route_command(command, args)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
