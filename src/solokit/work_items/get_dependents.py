"""Fast dependent lookup for Claude Code integration.

This module provides optimized lookup of work items that depend on a given work item.
Used by /work-delete command to check if deleting a work item will affect others.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def get_dependents(work_item_id: str) -> list[dict[str, Any]]:
    """Get list of work items that depend on the given work item.

    Args:
        work_item_id: ID of the work item to check for dependents

    Returns:
        List of dependent work items with keys: id, type, title, status

    Raises:
        FileNotFoundError: If work_items.json doesn't exist
        json.JSONDecodeError: If work_items.json is invalid
    """
    # Find .session directory
    session_dir = _find_session_dir()
    if not session_dir:
        print("Error: Not in an Solokit project (no .session directory found)", file=sys.stderr)
        return []

    # Load work items
    work_items_file = session_dir / "tracking" / "work_items.json"
    if not work_items_file.exists():
        print(f"Error: Work items file not found: {work_items_file}", file=sys.stderr)
        return []

    try:
        with open(work_items_file) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {work_items_file}: {e}", file=sys.stderr)
        return []

    # Extract work_items from the data structure
    work_items = data.get("work_items", {})
    if not work_items:
        print("No work items found", file=sys.stderr)
        return []

    # Find dependents (work items that have this work_item_id in their dependencies)
    dependents = []
    for item_id, item in work_items.items():
        dependencies = item.get("dependencies", [])
        if work_item_id in dependencies:
            dependents.append(
                {
                    "id": item_id,
                    "type": item.get("type", "unknown"),
                    "title": item.get("title", "Untitled"),
                    "status": item.get("status", "unknown"),
                }
            )

    return dependents


def _find_session_dir() -> Path | None:
    """Find the .session directory by walking up from current directory."""
    current = Path.cwd()
    while current != current.parent:
        session_dir = current / ".session"
        if session_dir.is_dir():
            return session_dir
        current = current.parent
    return None


def main() -> None:
    """CLI entry point for get_dependents script.

    Usage:
        python -m solokit.work_items.get_dependents <work_item_id>
    """
    import argparse

    parser = argparse.ArgumentParser(description="Get work items that depend on a given work item")
    parser.add_argument("work_item_id", help="ID of the work item to check for dependents")

    args = parser.parse_args()

    # Get dependents
    dependents = get_dependents(args.work_item_id)

    # Output results
    if not dependents:
        print(f"No work items depend on '{args.work_item_id}'")
        sys.exit(0)

    print(f"Found {len(dependents)} work item(s) that depend on '{args.work_item_id}':")
    print()
    for dep in dependents:
        print(f"ID: {dep['id']}")
        print(f"Type: {dep['type']}")
        print(f"Title: {dep['title']}")
        print(f"Status: {dep['status']}")
        print()


if __name__ == "__main__":
    main()
