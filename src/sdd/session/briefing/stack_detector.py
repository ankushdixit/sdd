#!/usr/bin/env python3
"""
Technology stack detection and information loading.
Part of the briefing module decomposition.
"""

from pathlib import Path

from sdd.core.logging_config import get_logger

logger = get_logger(__name__)


class StackDetector:
    """Detect and load technology stack information."""

    def __init__(self, session_dir: Path = None):
        """Initialize stack detector.

        Args:
            session_dir: Path to .session directory (defaults to .session)
        """
        self.session_dir = session_dir or Path(".session")
        self.stack_file = self.session_dir / "tracking" / "stack.txt"

    def load_current_stack(self) -> str:
        """Load current technology stack.

        Returns:
            Stack information as string
        """
        if self.stack_file.exists():
            try:
                return self.stack_file.read_text()
            except Exception as e:
                logger.warning("Failed to load stack file: %s", e)
                return "Stack not yet generated"
        return "Stack not yet generated"
