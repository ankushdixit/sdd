#!/usr/bin/env python3
"""
Technology stack detection and information loading.
Part of the briefing module decomposition.
"""

from __future__ import annotations

from pathlib import Path

from solokit.core.error_handlers import log_errors
from solokit.core.exceptions import FileOperationError
from solokit.core.logging_config import get_logger

logger = get_logger(__name__)


class StackDetector:
    """Detect and load technology stack information."""

    def __init__(self, session_dir: Path | None = None):
        """Initialize stack detector.

        Args:
            session_dir: Path to .session directory (defaults to .session)
        """
        self.session_dir = session_dir or Path(".session")
        self.stack_file = self.session_dir / "tracking" / "stack.txt"

    @log_errors()
    def load_current_stack(self) -> str:
        """Load current technology stack.

        Returns:
            Stack information as string

        Raises:
            FileOperationError: If stack file exists but cannot be read
        """
        if not self.stack_file.exists():
            return "Stack not yet generated"

        try:
            return self.stack_file.read_text()
        except OSError as e:
            raise FileOperationError(
                operation="read",
                file_path=str(self.stack_file),
                details=f"Failed to read stack file: {e}",
                cause=e,
            ) from e
