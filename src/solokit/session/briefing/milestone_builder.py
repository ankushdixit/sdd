#!/usr/bin/env python3
"""
Milestone context building.
Part of the briefing module decomposition.
"""

from __future__ import annotations

import json
from pathlib import Path

from solokit.core.logging_config import get_logger
from solokit.core.types import WorkItemStatus

logger = get_logger(__name__)


class MilestoneBuilder:
    """Build milestone context for briefings."""

    def __init__(self, session_dir: Path | None = None):
        """Initialize milestone builder.

        Args:
            session_dir: Path to .session directory (defaults to .session)
        """
        self.session_dir = session_dir or Path(".session")
        self.work_items_file = self.session_dir / "tracking" / "work_items.json"

    def load_milestone_context(self, work_item: dict) -> dict | None:
        """Load milestone context for briefing.

        Args:
            work_item: Work item dictionary

        Returns:
            Milestone context dict or None if not in a milestone
        """
        milestone_name = work_item.get("milestone")
        if not milestone_name:
            return None

        if not self.work_items_file.exists():
            return None

        with open(self.work_items_file) as f:
            data = json.load(f)

        milestones = data.get("milestones", {})
        milestone = milestones.get(milestone_name)

        if not milestone:
            return None

        # Calculate progress
        items = data.get("work_items", {})
        milestone_items = [
            {**item, "id": item_id}
            for item_id, item in items.items()
            if item.get("milestone") == milestone_name
        ]

        total = len(milestone_items)
        completed = sum(
            1 for item in milestone_items if item["status"] == WorkItemStatus.COMPLETED.value
        )
        percent = int((completed / total) * 100) if total > 0 else 0

        return {
            "name": milestone_name,
            "title": milestone["title"],
            "description": milestone["description"],
            "target_date": milestone.get("target_date", ""),
            "progress": percent,
            "total_items": total,
            "completed_items": completed,
            "milestone_items": milestone_items,
        }
