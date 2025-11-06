#!/usr/bin/env python3
"""
Get next recommended work items for interactive selection.

This script returns the top 4 ready-to-start work items based on:
- Dependencies are satisfied (not blocked)
- Priority (critical > high > medium > low)
- Status is not_started

Output format (one per line):
work_item_id | type | title | priority

Usage:
    python -m sdd.work_items.get_next_recommendations [--limit N]
"""

import json
import sys
from pathlib import Path
from typing import Any


def get_ready_work_items(limit: int = 4) -> list[dict[str, Any]]:
    """Get list of ready-to-start work items sorted by priority.

    Args:
        limit: Maximum number of items to return (default 4)

    Returns:
        list: Ready work items with id, type, title, priority
    """
    # Find work_items.json
    work_items_file = Path(".session/tracking/work_items.json")
    if not work_items_file.exists():
        print("Error: .session/tracking/work_items.json not found", file=sys.stderr)
        return []

    # Load work items
    try:
        with open(work_items_file) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {work_items_file}: {e}", file=sys.stderr)
        return []

    # Extract work_items from data structure
    work_items = data.get("work_items", {})
    if not work_items:
        print("No work items found", file=sys.stderr)
        return []

    # Filter to not_started items
    not_started = {
        wid: item for wid, item in work_items.items() if item.get("status") == "not_started"
    }

    if not not_started:
        print("No work items available to start", file=sys.stderr)
        return []

    # Check dependencies and filter to ready items
    ready_items = []

    for work_id, item in not_started.items():
        dependencies = item.get("dependencies", [])

        # Check if all dependencies are completed
        is_ready = True
        if dependencies:
            for dep_id in dependencies:
                dep_item = work_items.get(dep_id)
                if not dep_item or dep_item.get("status") != "completed":
                    is_ready = False
                    break

        if is_ready:
            ready_items.append(
                {
                    "id": work_id,
                    "type": item.get("type", "unknown"),
                    "title": item.get("title", "Untitled"),
                    "priority": item.get("priority", "medium"),
                }
            )

    if not ready_items:
        print("No work items ready to start. All have unmet dependencies.", file=sys.stderr)
        return []

    # Sort by priority (critical > high > medium > low)
    priority_order = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
    }
    ready_items.sort(key=lambda x: priority_order.get(x["priority"], 99))

    # Return top N items
    return ready_items[:limit]


def main() -> int:
    """Main entry point for script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Get next recommended work items for interactive selection"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=4,
        help="Maximum number of recommendations to return (default: 4)",
    )
    args = parser.parse_args()

    ready_items = get_ready_work_items(limit=args.limit)

    if not ready_items:
        sys.exit(1)

    # Output format: work_item_id | type | title | priority
    for item in ready_items:
        print(f"{item['id']} | {item['type']} | {item['title']} | {item['priority']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
