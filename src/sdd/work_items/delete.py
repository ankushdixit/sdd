#!/usr/bin/env python3
"""
Work Item Deletion - Safe deletion of work items.

Handles deletion of work items with dependency checking and interactive confirmation.
"""

import sys
from pathlib import Path
from typing import Optional

from sdd.core.file_ops import load_json, save_json
from sdd.core.logging_config import get_logger

logger = get_logger(__name__)


def find_dependents(work_items: dict, work_item_id: str) -> list[str]:
    """
    Find work items that depend on the given work item.

    Args:
        work_items: Dictionary of all work items
        work_item_id: ID to find dependents for

    Returns:
        List of work item IDs that depend on this item
    """
    dependents = []
    for wid, item in work_items.items():
        deps = item.get("dependencies", [])
        if work_item_id in deps:
            dependents.append(wid)
    return dependents


def delete_work_item(
    work_item_id: str, delete_spec: Optional[bool] = None, project_root: Optional[Path] = None
) -> bool:
    """
    Delete a work item from the system.

    Args:
        work_item_id: ID of work item to delete
        delete_spec: Whether to also delete the spec file (None for interactive prompt)
        project_root: Project root path (defaults to current directory)

    Returns:
        True if deletion successful, False otherwise
    """
    # Setup paths
    if project_root is None:
        project_root = Path.cwd()

    session_dir = project_root / ".session"
    work_items_file = session_dir / "tracking" / "work_items.json"

    # Check if work items file exists
    if not work_items_file.exists():
        logger.error("Work items file not found")
        print("❌ Error: No work items found.")
        return False

    # Load work items
    try:
        work_items_data = load_json(work_items_file)
    except Exception as e:
        logger.error("Failed to load work items: %s", e)
        print(f"❌ Error: Failed to load work items: {e}")
        return False

    work_items = work_items_data.get("work_items", {})

    # Validate work item exists
    if work_item_id not in work_items:
        logger.error("Work item '%s' not found", work_item_id)
        print(f"❌ Error: Work item '{work_item_id}' not found.")
        print("\nAvailable work items:")
        for wid in list(work_items.keys())[:5]:
            print(f"  - {wid}")
        if len(work_items) > 5:
            print(f"  ... and {len(work_items) - 5} more")
        return False

    item = work_items[work_item_id]

    # Find dependents
    dependents = find_dependents(work_items, work_item_id)

    # Show work item details
    print(f"\n⚠️  Warning: This will permanently delete work item '{work_item_id}'")
    print("\nWork item details:")
    print(f"  Title: {item.get('title', 'N/A')}")
    print(f"  Type: {item.get('type', 'N/A')}")
    print(f"  Status: {item.get('status', 'N/A')}")

    dependencies = item.get("dependencies", [])
    if dependencies:
        print(f"  Dependencies: {', '.join(dependencies)}")
    else:
        print("  Dependencies: none")

    if dependents:
        print(f"  Dependents: {', '.join(dependents)} ({len(dependents)} item(s) depend on this)")
    else:
        print("  Dependents: none")

    # Get deletion choice
    if delete_spec is None:
        # Interactive mode
        if not sys.stdin.isatty():
            logger.error("Cannot run interactive mode in non-interactive environment")
            print("\n❌ Error: Cannot run interactive deletion in non-interactive mode")
            print("\nPlease use command-line flags:")
            print("  sdd work-delete <work_item_id> --keep-spec   (delete work item only)")
            print("  sdd work-delete <work_item_id> --delete-spec (delete work item and spec)")
            return False

        print("\nOptions:")
        print("  1. Delete work item only (keep spec file)")
        print("  2. Delete work item and spec file")
        print("  3. Cancel")
        print()

        try:
            choice = input("Choice [1]: ").strip() or "1"
        except (EOFError, KeyboardInterrupt):
            logger.warning("User cancelled deletion via EOF/interrupt")
            print("\n\nDeletion cancelled.")
            return False

        if choice == "3":
            logger.info("User cancelled deletion")
            print("Deletion cancelled.")
            return False

        delete_spec = choice == "2"
    else:
        # Non-interactive mode - show what will be done
        if delete_spec:
            print("\n→ Will delete work item and spec file")
        else:
            print("\n→ Will delete work item only (keeping spec file)")

    # Perform deletion
    logger.info("Deleting work item '%s'", work_item_id)
    del work_items[work_item_id]

    # Update metadata
    work_items_data["work_items"] = work_items
    if "metadata" not in work_items_data:
        work_items_data["metadata"] = {}

    work_items_data["metadata"]["total_items"] = len(work_items)
    work_items_data["metadata"]["completed"] = sum(
        1 for item in work_items.values() if item["status"] == "completed"
    )
    work_items_data["metadata"]["in_progress"] = sum(
        1 for item in work_items.values() if item["status"] == "in_progress"
    )
    work_items_data["metadata"]["blocked"] = sum(
        1 for item in work_items.values() if item["status"] == "blocked"
    )

    # Save work items
    try:
        save_json(work_items_file, work_items_data)
        logger.info("Successfully updated work_items.json")
        print(f"✓ Deleted work item '{work_item_id}'")
    except Exception as e:
        logger.error("Failed to save work items: %s", e)
        print(f"❌ Error: Failed to save changes: {e}")
        return False

    # Delete spec file if requested
    if delete_spec:
        spec_file_path = item.get("spec_file", f".session/specs/{work_item_id}.md")
        spec_path = project_root / spec_file_path

        if spec_path.exists():
            try:
                spec_path.unlink()
                logger.info("Deleted spec file: %s", spec_file_path)
                print(f"✓ Deleted spec file '{spec_file_path}'")
            except Exception as e:
                logger.warning("Failed to delete spec file: %s", e)
                print(f"⚠️  Warning: Could not delete spec file: {e}")
        else:
            logger.debug("Spec file not found: %s", spec_file_path)
            print(f"⚠️  Note: Spec file '{spec_file_path}' not found")

    # Warn about dependents
    if dependents:
        print("\n⚠️  Note: The following work items depend on this item:")
        for dep in dependents:
            print(f"    - {dep}")
        print("  Update their dependencies manually if needed.")

    print("\nDeletion successful.")
    logger.info("Work item deletion completed successfully")
    return True


def main():
    """CLI entry point for work item deletion."""
    import argparse

    parser = argparse.ArgumentParser(description="Delete a work item")
    parser.add_argument("work_item_id", help="ID of work item to delete")
    parser.add_argument(
        "--keep-spec",
        action="store_true",
        help="Keep the spec file (delete work item only)",
    )
    parser.add_argument(
        "--delete-spec",
        action="store_true",
        help="Delete both work item and spec file",
    )

    args = parser.parse_args()

    # Determine delete_spec value
    delete_spec_value = None
    if args.keep_spec and args.delete_spec:
        print("❌ Error: Cannot specify both --keep-spec and --delete-spec")
        return 1
    elif args.keep_spec:
        delete_spec_value = False
    elif args.delete_spec:
        delete_spec_value = True

    # Perform deletion
    success = delete_work_item(args.work_item_id, delete_spec=delete_spec_value)
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
