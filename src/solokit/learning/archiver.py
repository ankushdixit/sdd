"""Learning archiving module"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from solokit.core.constants import MAX_LEARNING_AGE_SESSIONS
from solokit.core.file_ops import load_json
from solokit.core.logging_config import get_logger

logger = get_logger(__name__)


class LearningArchiver:
    """Handles archiving of old, unreferenced learnings"""

    def __init__(self, session_dir: Path, max_age_sessions: int = MAX_LEARNING_AGE_SESSIONS):
        """
        Initialize archiver

        Args:
            session_dir: Path to .session directory
            max_age_sessions: Maximum age in sessions before archiving (default: 50)
        """
        self.session_dir = session_dir
        self.max_age_sessions = max_age_sessions

    def archive_old_learnings(
        self, learnings: dict[str, Any], max_age_sessions: int | None = None
    ) -> int:
        """
        Archive old, unreferenced learnings

        Args:
            learnings: Learnings dict with 'categories' key
            max_age_sessions: Override default max age (optional)

        Returns:
            Number of learnings archived
        """
        max_age = max_age_sessions if max_age_sessions is not None else self.max_age_sessions
        archived_count = 0
        categories = learnings.get("categories", {})

        # Get current session number from tracking
        current_session = self._get_current_session_number()

        for category_name, category_learnings in categories.items():
            to_archive = []

            for i, learning in enumerate(category_learnings):
                # Extract session number from learned_in field
                session_num = self._extract_session_number(learning.get("learned_in", ""))

                # Archive if too old
                if session_num and current_session > 0 and current_session - session_num > max_age:
                    to_archive.append(i)

            # Move to archive
            archived = learnings.setdefault("archived", [])
            for idx in sorted(to_archive, reverse=True):
                learning = category_learnings.pop(idx)
                learning["archived_from"] = category_name
                learning["archived_at"] = datetime.now().isoformat()
                archived.append(learning)
                archived_count += 1

        logger.info(f"Archived {archived_count} old learnings")
        return archived_count

    def _get_current_session_number(self) -> int:
        """
        Get the current session number from work items

        Returns:
            Maximum session number found, or 0 if none found
        """
        try:
            work_items_path = self.session_dir / "tracking" / "work_items.json"
            if work_items_path.exists():
                data = load_json(work_items_path)
                # Find max session number across all work items
                max_session = 0
                for item in data.get("work_items", {}).values():
                    sessions = item.get("sessions", [])
                    if sessions and isinstance(sessions, list):
                        # Extract session_num from each session dict
                        session_nums = [
                            s.get("session_num", 0) for s in sessions if isinstance(s, dict)
                        ]
                        if session_nums:
                            max_session = max(max_session, max(session_nums))
                return max_session
        except (ValueError, KeyError, TypeError) as e:
            logger.warning(f"Failed to get current session number: {e}")
            return 0
        return 0

    def _extract_session_number(self, session_id: str) -> int:
        """
        Extract numeric session number from session ID

        Args:
            session_id: Session ID string (e.g., "session_001", "001", "1")

        Returns:
            Extracted session number or 0 if extraction fails
        """
        try:
            # Handle formats like "session_001", "001", "1", etc.
            match = re.search(r"\d+", session_id)
            if match:
                return int(match.group())
        except (ValueError, AttributeError) as e:
            logger.debug(f"Failed to extract session number from '{session_id}': {e}")
            return 0
        return 0
