#!/usr/bin/env python3
"""
Project directory tree loading.
Part of the briefing module decomposition.
"""

from pathlib import Path

from sdd.core.logging_config import get_logger

logger = get_logger(__name__)


class TreeGenerator:
    """Load and generate project directory tree."""

    def __init__(self, session_dir: Path = None):
        """Initialize tree generator.

        Args:
            session_dir: Path to .session directory (defaults to .session)
        """
        self.session_dir = session_dir or Path(".session")
        self.tree_file = self.session_dir / "tracking" / "tree.txt"

    def load_current_tree(self) -> str:
        """Load current project structure.

        Returns:
            Project tree as string
        """
        if self.tree_file.exists():
            try:
                # Return full tree
                return self.tree_file.read_text()
            except Exception as e:
                logger.warning("Failed to load tree file: %s", e)
                return "Tree not yet generated"
        return "Tree not yet generated"
