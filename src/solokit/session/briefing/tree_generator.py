#!/usr/bin/env python3
"""
Project directory tree loading.
Part of the briefing module decomposition.
"""

from __future__ import annotations

from pathlib import Path

from solokit.core.error_handlers import log_errors
from solokit.core.exceptions import FileOperationError
from solokit.core.logging_config import get_logger

logger = get_logger(__name__)


class TreeGenerator:
    """Load and generate project directory tree."""

    def __init__(self, session_dir: Path | None = None):
        """Initialize tree generator.

        Args:
            session_dir: Path to .session directory (defaults to .session)
        """
        self.session_dir = session_dir or Path(".session")
        self.tree_file = self.session_dir / "tracking" / "tree.txt"

    @log_errors()
    def load_current_tree(self) -> str:
        """Load current project structure.

        Returns:
            Project tree as string

        Raises:
            FileOperationError: If tree file exists but cannot be read
        """
        if not self.tree_file.exists():
            return "Tree not yet generated"

        try:
            # Return full tree
            return self.tree_file.read_text()
        except OSError as e:
            raise FileOperationError(
                operation="read",
                file_path=str(self.tree_file),
                details=f"Failed to read tree file: {e}",
                cause=e,
            ) from e
