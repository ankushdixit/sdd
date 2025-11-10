"""Learning repository for CRUD operations and data persistence"""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from solokit.core.config import get_config_manager
from solokit.core.error_handlers import log_errors
from solokit.core.file_ops import load_json, save_json
from solokit.core.logging_config import get_logger
from solokit.core.output import get_output

logger = get_logger(__name__)
output = get_output()


class LearningRepository:
    """Manages CRUD operations and data persistence for learnings"""

    def __init__(self, session_dir: Path):
        """
        Initialize repository

        Args:
            session_dir: Path to .session directory
        """
        self.session_dir = session_dir
        self.learnings_path = session_dir / "tracking" / "learnings.json"

        # Load curation config
        config_path = session_dir / "config.json"
        config_manager = get_config_manager()
        config_manager.load_config(config_path)
        self.config = config_manager.curation

    def load_learnings(self) -> dict[str, Any]:
        """
        Load learnings from file

        Returns:
            Learnings dictionary with metadata and categories
        """
        if self.learnings_path.exists():
            data = load_json(self.learnings_path)
            # Ensure metadata exists
            if "metadata" not in data:
                data["metadata"] = {
                    "total_learnings": self.count_all_learnings(data),
                    "last_curated": data.get("last_curated"),
                }
            return data
        else:
            # Create default structure
            return {
                "metadata": {
                    "total_learnings": 0,
                    "last_curated": None,
                },
                "last_curated": None,
                "curator": "session_curator",
                "categories": {
                    "architecture_patterns": [],
                    "gotchas": [],
                    "best_practices": [],
                    "technical_debt": [],
                    "performance_insights": [],
                },
                "archived": [],
            }

    def save_learnings(self, learnings: dict[str, Any]) -> None:
        """
        Save learnings to file

        Args:
            learnings: Learnings dictionary to save
        """
        save_json(self.learnings_path, learnings)
        logger.debug(f"Saved learnings to {self.learnings_path}")

    def count_all_learnings(self, learnings: dict[str, Any]) -> int:
        """
        Count all learnings across all categories

        Args:
            learnings: Learnings dictionary

        Returns:
            Total count of learnings
        """
        count = 0
        categories = learnings.get("categories", {})

        for category in categories.values():
            count += len(category)

        count += len(learnings.get("archived", []))

        return count

    def update_total_learnings(self, learnings: dict[str, Any]) -> None:
        """
        Update total_learnings metadata counter

        Args:
            learnings: Learnings dictionary to update
        """
        if "metadata" not in learnings:
            learnings["metadata"] = {}
        learnings["metadata"]["total_learnings"] = self.count_all_learnings(learnings)

    @log_errors()
    def add_learning(
        self,
        content: str,
        category: str,
        session: int | None = None,
        tags: list[str] | None = None,
        context: str | None = None,
    ) -> str:
        """
        Add a new learning to the repository

        Args:
            content: Learning content text
            category: Category to add learning to
            session: Optional session number
            tags: Optional list of tags
            context: Optional context string

        Returns:
            Learning ID of the created learning
        """
        learnings = self.load_learnings()

        # Generate unique ID
        learning_id = str(uuid.uuid4())[:8]

        # Create learning object
        learning: dict[str, Any] = {
            "id": learning_id,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "learned_in": f"session_{session:03d}" if session else "unknown",
        }

        if tags:
            learning["tags"] = tags

        if context:
            learning["context"] = context

        # Add to category
        categories = learnings.setdefault("categories", {})
        if category not in categories:
            categories[category] = []

        categories[category].append(learning)

        # Update total_learnings counter
        self.update_total_learnings(learnings)

        # Save
        self.save_learnings(learnings)

        output.info("\n✓ Learning captured!")
        output.info(f"  ID: {learning_id}")
        output.info(f"  Category: {category}")
        if tags:
            output.info(f"  Tags: {', '.join(learning['tags'])}")
        output.info("\nIt will be auto-categorized and curated.\n")

        return learning_id

    def add_learning_if_new(
        self, learning_dict: dict[str, Any], similarity_checker: Any = None
    ) -> bool:
        """
        Add learning if it doesn't already exist (based on similarity)

        Args:
            learning_dict: Learning dictionary to add
            similarity_checker: Optional similarity checker with are_similar method

        Returns:
            True if learning was added, False if it already exists
        """
        learnings = self.load_learnings()
        categories = learnings.get("categories", {})

        # Check against all existing learnings if similarity checker provided
        if similarity_checker:
            for category_learnings in categories.values():
                for existing in category_learnings:
                    if similarity_checker.are_similar(existing, learning_dict):
                        return False  # Skip, already exists

        # Auto-categorize if needed
        category = learning_dict.get("category")
        if not category:
            # Default to best_practices if no category specified
            category = "best_practices"

        # Add to category
        if category not in categories:
            categories[category] = []

        # Generate ID if missing
        if "id" not in learning_dict:
            learning_dict["id"] = str(uuid.uuid4())[:8]

        categories[category].append(learning_dict)

        # Update total_learnings counter
        self.update_total_learnings(learnings)

        # Save
        self.save_learnings(learnings)

        return True  # Successfully added

    def get_curation_config(self) -> Any:
        """
        Get curation configuration

        Returns:
            Curation config object
        """
        return self.config

    def learning_exists(
        self,
        category_learnings: list[dict[str, Any]],
        new_learning: dict[str, Any],
        similarity_checker: Any,
    ) -> bool:
        """
        Check if a similar learning already exists in category

        Args:
            category_learnings: List of learnings in category
            new_learning: New learning to check
            similarity_checker: Similarity checker with are_similar method

        Returns:
            True if similar learning exists
        """
        for existing in category_learnings:
            if similarity_checker.are_similar(existing, new_learning):
                return True
        return False
