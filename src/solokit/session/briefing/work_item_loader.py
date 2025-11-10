#!/usr/bin/env python3
"""
Work item loading and dependency resolution.
Part of the briefing module decomposition.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from solokit.core.logging_config import get_logger
from solokit.core.types import Priority, WorkItemStatus

logger = get_logger(__name__)


class WorkItemLoader:
    """Load work items and their dependencies."""

    def __init__(self, session_dir: Path | None = None):
        """Initialize work item loader.

        Args:
            session_dir: Path to .session directory (defaults to .session)
        """
        self.session_dir = session_dir or Path(".session")
        self.work_items_file = self.session_dir / "tracking" / "work_items.json"

    def load_work_items(self) -> dict[str, Any]:
        """Load work items from tracking file.

        Returns:
            Work items data structure with 'work_items' dict
        """
        logger.debug("Loading work items from: %s", self.work_items_file)
        if not self.work_items_file.exists():
            logger.warning("Work items file not found: %s", self.work_items_file)
            return {"work_items": {}}
        with open(self.work_items_file) as f:
            return json.load(f)  # type: ignore[no-any-return]

    def get_work_item(
        self, work_item_id: str, work_items_data: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """Get a specific work item by ID.

        Args:
            work_item_id: Work item identifier
            work_items_data: Pre-loaded work items data (optional)

        Returns:
            Work item dict or None if not found
        """
        if work_items_data is None:
            work_items_data = self.load_work_items()

        return work_items_data.get("work_items", {}).get(work_item_id)  # type: ignore[no-any-return]

    def get_next_work_item(self, work_items_data: dict) -> tuple[str | None, dict | None]:
        """Find next available work item where dependencies are satisfied.

        Prioritizes resuming in-progress items over starting new work.
        Returns item with highest priority among available.

        Args:
            work_items_data: Loaded work items data structure

        Returns:
            Tuple of (item_id, item) or (None, None) if no work available
        """
        work_items = work_items_data.get("work_items", {})
        priority_order = {
            Priority.CRITICAL.value: 4,
            Priority.HIGH.value: 3,
            Priority.MEDIUM.value: 2,
            Priority.LOW.value: 1,
        }

        # PRIORITY 1: Resume in-progress work
        in_progress_items = []
        for item_id, item in work_items.items():
            if item["status"] == WorkItemStatus.IN_PROGRESS.value:
                in_progress_items.append((item_id, item))

        if in_progress_items:
            # Sort by priority and return highest
            in_progress_items.sort(
                key=lambda x: priority_order.get(x[1].get("priority", Priority.MEDIUM.value), 2),
                reverse=True,
            )
            return in_progress_items[0]

        # PRIORITY 2: Start new work
        available = []
        for item_id, item in work_items.items():
            if item["status"] != WorkItemStatus.NOT_STARTED.value:
                continue

            # Check dependencies
            deps_satisfied = all(
                work_items.get(dep_id, {}).get("status") == WorkItemStatus.COMPLETED.value
                for dep_id in item.get("dependencies", [])
            )

            if deps_satisfied:
                available.append((item_id, item))

        if not available:
            return None, None

        # Sort by priority
        available.sort(
            key=lambda x: priority_order.get(x[1].get("priority", Priority.MEDIUM.value), 2),
            reverse=True,
        )

        return available[0]

    def load_work_item_spec(self, work_item: str | dict[str, Any]) -> str:
        """Load work item specification file.

        Args:
            work_item: Either a work item dict with 'spec_file' and 'id' fields,
                      or a string work_item_id (for backwards compatibility)

        Returns:
            Specification content as string
        """
        # Handle backwards compatibility: accept both dict and string
        if isinstance(work_item, str):
            # Legacy call with just work_item_id string
            work_item_id = work_item
            spec_file = self.session_dir / "specs" / f"{work_item_id}.md"
        else:
            # New call with work item dict
            # Use spec_file from work item if available, otherwise fallback to ID-based pattern
            spec_file_path = work_item.get("spec_file")
            if spec_file_path:
                spec_file = Path(spec_file_path)
            else:
                # Fallback to legacy pattern for backwards compatibility
                work_item_id_raw = work_item.get("id")
                if not work_item_id_raw:
                    return "Specification file not found: work item has no id"
                spec_file = self.session_dir / "specs" / f"{work_item_id_raw}.md"

        if spec_file.exists():
            return spec_file.read_text()
        return f"Specification file not found: {spec_file}"

    def update_work_item_status(
        self, work_item_id: str, status: str, session_num: int | None = None
    ) -> bool:
        """Update work item status and optionally add session tracking.

        Args:
            work_item_id: Work item identifier
            status: New status value
            session_num: Optional session number to add to tracking

        Returns:
            True if update successful, False otherwise
        """
        if not self.work_items_file.exists():
            logger.error("Work items file not found: %s", self.work_items_file)
            return False

        with open(self.work_items_file) as f:
            work_items_data = json.load(f)

        if work_item_id not in work_items_data["work_items"]:
            logger.error("Work item not found: %s", work_item_id)
            return False

        work_item = work_items_data["work_items"][work_item_id]
        work_item["status"] = status
        work_item["updated_at"] = datetime.now().isoformat()

        # Add session tracking if session_num provided
        if session_num is not None:
            if "sessions" not in work_item:
                work_item["sessions"] = []
            work_item["sessions"].append(
                {"session_num": session_num, "started_at": datetime.now().isoformat()}
            )

        # Update metadata counters
        work_items = work_items_data.get("work_items", {})
        work_items_data["metadata"]["total_items"] = len(work_items)
        work_items_data["metadata"]["completed"] = sum(
            1 for item in work_items.values() if item["status"] == WorkItemStatus.COMPLETED.value
        )
        work_items_data["metadata"]["in_progress"] = sum(
            1 for item in work_items.values() if item["status"] == WorkItemStatus.IN_PROGRESS.value
        )
        work_items_data["metadata"]["blocked"] = sum(
            1 for item in work_items.values() if item["status"] == WorkItemStatus.BLOCKED.value
        )
        work_items_data["metadata"]["last_updated"] = datetime.now().isoformat()

        # Save updated work items
        with open(self.work_items_file, "w") as f:
            json.dump(work_items_data, f, indent=2)

        logger.info("Updated work item %s status to %s", work_item_id, status)
        return True
