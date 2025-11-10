"""
Environment File Generator Module

Generates .env.example and .editorconfig files.
"""

from __future__ import annotations

import logging
from pathlib import Path

from solokit.core.exceptions import FileOperationError

logger = logging.getLogger(__name__)


def generate_editorconfig(project_root: Path | None = None) -> Path:
    """
    Generate .editorconfig for universal editor configuration.

    Args:
        project_root: Project root directory

    Returns:
        Path to .editorconfig file

    Raises:
        FileOperationError: If file creation fails
    """
    if project_root is None:
        project_root = Path.cwd()

    editorconfig_path = project_root / ".editorconfig"

    content = """root = true

[*]
indent_style = space
indent_size = 2
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.md]
trim_trailing_whitespace = false

[*.py]
indent_size = 4

[Makefile]
indent_style = tab
"""

    try:
        editorconfig_path.write_text(content)
        logger.info("Generated .editorconfig")
        return editorconfig_path
    except Exception as e:
        raise FileOperationError(
            operation="write",
            file_path=str(editorconfig_path),
            details=f"Failed to write .editorconfig: {str(e)}",
            cause=e,
        )


def generate_env_example_nextjs(project_root: Path) -> Path:
    """Generate .env.example for Next.js stacks."""
    env_path = project_root / ".env.example"

    content = """# Database
DATABASE_URL="postgresql://user:password@localhost:5432/dbname"

# Next.js
NEXTAUTH_SECRET=""
NEXTAUTH_URL="http://localhost:3000"

# API
API_BASE_URL="http://localhost:3000/api"

# Optional: Error Tracking (Tier 4)
SENTRY_DSN=""

# Optional: Analytics (Tier 4)
NEXT_PUBLIC_VERCEL_ANALYTICS_ID=""
"""

    env_path.write_text(content)
    return env_path


def generate_env_example_python(project_root: Path) -> Path:
    """Generate .env.example for Python stacks."""
    env_path = project_root / ".env.example"

    content = """# Database
DATABASE_URL="postgresql://user:password@localhost:5432/dbname"

# API
API_HOST="0.0.0.0"
API_PORT=8000
API_RELOAD=true

# Security
SECRET_KEY="your-secret-key-here"
ALLOWED_ORIGINS="http://localhost:3000,http://localhost:8000"

# Optional: Monitoring (Tier 4)
SENTRY_DSN=""
PROMETHEUS_PORT=9090
"""

    env_path.write_text(content)
    return env_path


def generate_env_files(template_id: str, project_root: Path | None = None) -> list[Path]:
    """
    Generate environment template files.

    Args:
        template_id: Template identifier
        project_root: Project root directory

    Returns:
        List of created file paths

    Raises:
        FileOperationError: If file creation fails
    """
    if project_root is None:
        project_root = Path.cwd()

    created_files = []

    try:
        # Generate .editorconfig (universal)
        editorconfig_path = generate_editorconfig(project_root)
        created_files.append(editorconfig_path)

        # Generate .env.example based on template type
        if template_id == "ml_ai_fastapi":
            env_path = generate_env_example_python(project_root)
        else:
            env_path = generate_env_example_nextjs(project_root)

        created_files.append(env_path)
        logger.info("Generated .env.example")

        logger.info(f"Generated {len(created_files)} environment files")
        return created_files

    except Exception as e:
        raise FileOperationError(
            operation="create",
            file_path=str(project_root),
            details=f"Failed to generate environment files: {str(e)}",
            cause=e,
        )
