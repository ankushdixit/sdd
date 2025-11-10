"""
Documentation Structure Module

Creates documentation directory structure.
"""

from __future__ import annotations

import logging
from pathlib import Path

from solokit.core.exceptions import FileOperationError

logger = logging.getLogger(__name__)


def create_docs_structure(project_root: Path | None = None) -> list[Path]:
    """
    Create documentation directory structure.

    Args:
        project_root: Project root directory

    Returns:
        List of created directory paths

    Raises:
        FileOperationError: If directory creation fails
    """
    if project_root is None:
        project_root = Path.cwd()

    docs_dir = project_root / "docs"
    created_dirs = []

    directories = [
        docs_dir / "architecture",
        docs_dir / "architecture" / "decisions",  # ADRs
        docs_dir / "api",
        docs_dir / "guides",
    ]

    try:
        for dir_path in directories:
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(dir_path)
            logger.debug(f"Created {dir_path.relative_to(project_root)}")

        # Create placeholder README files
        (docs_dir / "architecture" / "README.md").write_text(
            "# Architecture\n\nArchitecture documentation and decisions.\n"
        )
        (docs_dir / "api" / "README.md").write_text(
            "# API Documentation\n\nAPI documentation goes here.\n"
        )
        (docs_dir / "guides" / "development.md").write_text(
            "# Development Guide\n\nDevelopment setup and workflow.\n"
        )
        (docs_dir / "guides" / "deployment.md").write_text(
            "# Deployment Guide\n\nDeployment instructions.\n"
        )

        # Create SECURITY.md
        security_path = docs_dir / "SECURITY.md"
        security_path.write_text(
            """# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability, please report it to the project maintainers.

## Security Best Practices

- Never commit secrets or credentials
- Use environment variables for sensitive configuration
- Keep dependencies up to date
- Follow secure coding practices
"""
        )

        logger.info(f"Created docs/ structure with {len(created_dirs)} directories")
        return created_dirs

    except Exception as e:
        raise FileOperationError(
            operation="create",
            file_path=str(docs_dir),
            details=f"Failed to create documentation structure: {str(e)}",
            cause=e,
        )
