#!/usr/bin/env python3
"""
Learning loading and relevance scoring.
Part of the briefing module decomposition.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from solokit.core.constants import MAX_SPEC_KEYWORDS
from solokit.core.exceptions import FileOperationError
from solokit.core.logging_config import get_logger

logger = get_logger(__name__)


class LearningLoader:
    """Load and score learnings based on relevance."""

    def __init__(self, session_dir: Path | None = None):
        """Initialize learning loader.

        Args:
            session_dir: Path to .session directory (defaults to .session)
        """
        self.session_dir = session_dir or Path(".session")
        self.learnings_file = self.session_dir / "tracking" / "learnings.json"

    def load_learnings(self) -> dict[str, Any]:
        """Load learnings from tracking file.

        Returns:
            Learnings data structure

        Raises:
            FileOperationError: If file read or JSON parsing fails
        """
        if not self.learnings_file.exists():
            return {"learnings": []}

        try:
            with open(self.learnings_file) as f:
                return json.load(f)  # type: ignore[no-any-return]
        except json.JSONDecodeError as e:
            raise FileOperationError(
                operation="parse",
                file_path=str(self.learnings_file),
                details=f"Invalid JSON format: {e.msg} at line {e.lineno}, column {e.colno}",
                cause=e,
            )
        except OSError as e:
            raise FileOperationError(
                operation="read",
                file_path=str(self.learnings_file),
                details=str(e),
                cause=e,
            )

    def get_relevant_learnings(
        self, learnings_data: dict, work_item: dict, spec_content: str = ""
    ) -> list[dict]:
        """Get learnings relevant to this work item using multi-factor scoring.

        Enhancement #11 Phase 4: Uses intelligent scoring algorithm instead of
        simple tag matching. Considers keyword matching, type-based relevance,
        recency weighting, and category bonuses.

        Args:
            learnings_data: Full learnings.json data structure
            work_item: Work item dictionary with title, type, tags
            spec_content: Optional spec content for keyword extraction

        Returns:
            Top 10 scored learnings
        """
        # Flatten all learnings from categories structure
        all_learnings = []
        categories = learnings_data.get("categories", {})

        # Handle both old format (learnings list) and new format (categories dict)
        if not categories and "learnings" in learnings_data:
            # Old format compatibility
            all_learnings = learnings_data.get("learnings", [])
            for learning in all_learnings:
                if "category" not in learning:
                    learning["category"] = "general"
        else:
            # New format with categories
            for category, learnings in categories.items():
                for learning in learnings:
                    learning_copy = learning.copy()
                    learning_copy["category"] = category
                    all_learnings.append(learning_copy)

        if not all_learnings:
            return []

        # Extract keywords from work item
        title_keywords = self._extract_keywords(work_item.get("title", ""))
        spec_keywords = self._extract_keywords(spec_content[:MAX_SPEC_KEYWORDS])
        work_type = work_item.get("type", "")
        work_tags = set(work_item.get("tags", []))

        scored = []
        for learning in all_learnings:
            score: float = 0
            content_lower = learning.get("content", "").lower()
            context_lower = learning.get("context", "").lower()
            learning_tags = set(learning.get("tags", []))
            category = learning.get("category", "general")

            # 1. Keyword matching (title and spec)
            content_keywords = self._extract_keywords(content_lower)
            title_matches = len(title_keywords & content_keywords)
            spec_matches = len(spec_keywords & content_keywords)
            score += title_matches * 3  # Title match is worth more
            score += spec_matches * 1.5

            # 2. Type-based matching
            if work_type in content_lower or work_type in context_lower:
                score += 5

            # 3. Tag matching (legacy support)
            tag_overlap = len(work_tags & learning_tags)
            score += tag_overlap * 2

            # 4. Category bonuses
            category_bonuses = {
                "best_practices": 3,
                "patterns": 2,
                "gotchas": 2,
                "architecture": 2,
            }
            score += category_bonuses.get(category, 0)

            # 5. Recency weighting (decay over time)
            created_at = learning.get("created_at", "")
            if created_at:
                days_ago = self._calculate_days_ago(created_at)
                if days_ago < 7:
                    score += 3  # Very recent
                elif days_ago < 30:
                    score += 2  # Recent
                elif days_ago < 90:
                    score += 1  # Moderately recent

            # Only include if score > 0
            if score > 0:
                scored.append((score, learning))

        # Sort by score (descending) and return top 10
        scored.sort(key=lambda x: x[0], reverse=True)
        return [learning for score, learning in scored[:10]]

    def _extract_keywords(self, text: str) -> set[str]:
        """Extract meaningful keywords from text (lowercase, >3 chars).

        Args:
            text: Text to extract keywords from

        Returns:
            Set of lowercase keywords longer than 3 characters
        """
        words = re.findall(r"\b\w+\b", text.lower())
        # Filter stop words and short words
        stop_words = {
            "the",
            "this",
            "that",
            "with",
            "from",
            "have",
            "will",
            "for",
            "and",
            "or",
            "not",
            "but",
            "was",
            "are",
            "been",
        }
        return {w for w in words if len(w) > 3 and w not in stop_words}

    def _calculate_days_ago(self, timestamp: str) -> int:
        """Calculate days since timestamp.

        Args:
            timestamp: ISO format timestamp string

        Returns:
            Number of days ago (defaults to 365 if parsing fails)

        Note:
            Returns 365 (considered "old") if timestamp is empty or invalid.
            This is intentional to avoid breaking the scoring algorithm.
        """
        if not timestamp:
            return 365  # Empty timestamp considered old

        try:
            ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            delta = datetime.now() - ts
            return delta.days
        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to parse timestamp '{timestamp}': {e}. Treating as old learning.")
            return 365  # Default to old if parsing fails
