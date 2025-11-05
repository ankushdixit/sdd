#!/usr/bin/env python3
"""
Work Item Repository - Data access and persistence layer.

Handles CRUD operations for work items and milestones in work_items.json.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from sdd.core.file_ops import load_json, save_json
from sdd.core.logging_config import get_logger
from sdd.core.types import WorkItemStatus

logger = get_logger(__name__)


class WorkItemRepository:
    """Repository for work item data access and persistence"""

    def __init__(self, session_dir: Path):
        """Initialize repository with session directory

        Args:
            session_dir: Path to .session directory
        """
        self.session_dir = session_dir
        self.work_items_file = session_dir / "tracking" / "work_items.json"

    def load_all(self) -> dict[str, Any]:
        """Load all work items and milestones from work_items.json

        Returns:
            dict: Complete work items data including work_items and milestones
        """
        if not self.work_items_file.exists():
            return {"work_items": {}, "milestones": {}}

        return load_json(self.work_items_file)

    def save_all(self, data: dict[str, Any]) -> None:
        """Save all work items and milestones to work_items.json

        Args:
            data: Complete work items data to save
        """
        # Update metadata counters before saving
        self._update_metadata(data)
        save_json(self.work_items_file, data)

    def get_work_item(self, work_id: str) -> dict[str, Any] | None:
        """Get a single work item by ID

        Args:
            work_id: Work item ID

        Returns:
            dict: Work item data, or None if not found
        """
        data = self.load_all()
        work_items = data.get("work_items", {})
        result = work_items.get(work_id)
        return result if result is None else dict(result)

    def get_all_work_items(self) -> dict[str, Any]:
        """Get all work items

        Returns:
            dict: All work items keyed by ID
        """
        data = self.load_all()
        return dict(data.get("work_items", {}))

    def work_item_exists(self, work_id: str) -> bool:
        """Check if work item exists

        Args:
            work_id: Work item ID

        Returns:
            bool: True if work item exists
        """
        return self.get_work_item(work_id) is not None

    def add_work_item(
        self,
        work_id: str,
        work_type: str,
        title: str,
        priority: str,
        dependencies: list[str],
        spec_file: str = "",
    ) -> None:
        """Add a new work item to tracking

        Args:
            work_id: Unique work item ID
            work_type: Type of work item
            title: Work item title
            priority: Priority level
            dependencies: List of dependency IDs
            spec_file: Relative path to spec file
        """
        data = self.load_all()

        work_item = {
            "id": work_id,
            "type": work_type,
            "title": title,
            "status": WorkItemStatus.NOT_STARTED.value,
            "priority": priority,
            "dependencies": dependencies,
            "milestone": "",
            "spec_file": spec_file,
            "created_at": datetime.now().isoformat(),
            "sessions": [],
        }

        data.setdefault("work_items", {})[work_id] = work_item
        self.save_all(data)
        logger.info("Added work item: %s", work_id)

    def update_work_item(self, work_id: str, updates: dict[str, Any]) -> None:
        """Update a work item with new field values

        Args:
            work_id: Work item ID
            updates: Dictionary of field updates
        """
        data = self.load_all()
        items = data.get("work_items", {})

        if work_id not in items:
            return

        item = items[work_id]

        # Apply updates
        for field, value in updates.items():
            if field == "add_dependency":
                deps = item.get("dependencies", [])
                if value not in deps:
                    deps.append(value)
                    item["dependencies"] = deps
            elif field == "remove_dependency":
                deps = item.get("dependencies", [])
                if value in deps:
                    deps.remove(value)
                    item["dependencies"] = deps
            else:
                item[field] = value

        data["work_items"][work_id] = item
        self.save_all(data)
        logger.debug("Updated work item: %s", work_id)

    def delete_work_item(self, work_id: str) -> bool:
        """Delete a work item

        Args:
            work_id: Work item ID

        Returns:
            bool: True if deleted, False if not found
        """
        data = self.load_all()
        items = data.get("work_items", {})

        if work_id not in items:
            return False

        del items[work_id]
        data["work_items"] = items
        self.save_all(data)
        logger.info("Deleted work item: %s", work_id)
        return True

    def get_milestone(self, name: str) -> dict[str, Any] | None:
        """Get a milestone by name

        Args:
            name: Milestone name

        Returns:
            dict: Milestone data, or None if not found
        """
        data = self.load_all()
        milestones = data.get("milestones", {})
        result = milestones.get(name)
        return result if result is None else dict(result)

    def get_all_milestones(self) -> dict[str, Any]:
        """Get all milestones

        Returns:
            dict: All milestones keyed by name
        """
        data = self.load_all()
        return dict(data.get("milestones", {}))

    def milestone_exists(self, name: str) -> bool:
        """Check if milestone exists

        Args:
            name: Milestone name

        Returns:
            bool: True if milestone exists
        """
        return self.get_milestone(name) is not None

    def add_milestone(
        self, name: str, title: str, description: str, target_date: str | None = None
    ) -> None:
        """Add a new milestone

        Args:
            name: Unique milestone name
            title: Milestone title
            description: Milestone description
            target_date: Optional target completion date
        """
        data = self.load_all()

        milestone = {
            "name": name,
            "title": title,
            "description": description,
            "target_date": target_date or "",
            "status": "not_started",
            "created_at": datetime.now().isoformat(),
        }

        data.setdefault("milestones", {})[name] = milestone
        self.save_all(data)
        logger.info("Added milestone: %s", name)

    def _update_metadata(self, data: dict[str, Any]) -> None:
        """Update metadata counters

        Args:
            data: Work items data to update metadata for
        """
        if "metadata" not in data:
            data["metadata"] = {}

        work_items = data.get("work_items", {})
        data["metadata"]["total_items"] = len(work_items)
        data["metadata"]["completed"] = sum(
            1 for item in work_items.values() if item["status"] == WorkItemStatus.COMPLETED.value
        )
        data["metadata"]["in_progress"] = sum(
            1 for item in work_items.values() if item["status"] == WorkItemStatus.IN_PROGRESS.value
        )
        data["metadata"]["blocked"] = sum(
            1 for item in work_items.values() if item["status"] == WorkItemStatus.BLOCKED.value
        )
        data["metadata"]["last_updated"] = datetime.now().isoformat()
