#!/usr/bin/env python3
"""
Documentation discovery and loading.
Part of the briefing module decomposition.
"""

from __future__ import annotations

from pathlib import Path

from solokit.core.exceptions import FileOperationError
from solokit.core.logging_config import get_logger

logger = get_logger(__name__)


class DocumentationLoader:
    """Load project documentation for context."""

    def __init__(self, project_root: Path | None = None):
        """Initialize documentation loader.

        Args:
            project_root: Path to project root (defaults to current directory)
        """
        self.project_root = project_root or Path.cwd()

    def load_project_docs(self) -> dict[str, str]:
        """Load project documentation for context.

        Returns:
            Dictionary mapping doc filename to content
        """
        docs = {}

        # Look for common doc files
        doc_files = ["docs/vision.md", "docs/prd.md", "docs/architecture.md", "README.md"]

        for doc_file in doc_files:
            path = self.project_root / doc_file
            if path.exists():
                try:
                    docs[path.name] = path.read_text()
                    logger.debug("Loaded documentation: %s", doc_file)
                except (OSError, UnicodeDecodeError) as e:
                    raise FileOperationError(
                        operation="read",
                        file_path=str(path),
                        details=f"Failed to read documentation file: {e}",
                        cause=e,
                    ) from e

        return docs
