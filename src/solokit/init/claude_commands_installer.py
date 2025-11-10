"""
Claude Commands Installer Module

Installs Claude Code slash commands to project .claude/commands directory.
This enables project-specific slash commands like /start, /end, /work-new, etc.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from solokit.core.exceptions import FileOperationError, TemplateNotFoundError

logger = logging.getLogger(__name__)


def install_claude_commands(project_root: Path | None = None) -> list[Path]:
    """
    Install Claude Code slash commands from package to project .claude/commands directory.

    This enables users who installed via PyPI to use slash commands in their project
    without the /sk: prefix (e.g., /start instead of /sk:start).

    Args:
        project_root: Root directory of the project. Defaults to current working directory.

    Returns:
        List of installed command file paths

    Raises:
        TemplateNotFoundError: If .claude/commands directory is not found in package.
        FileOperationError: If command installation fails.
    """
    if project_root is None:
        project_root = Path.cwd()

    # Destination: project's .claude/commands directory
    commands_dest_dir = project_root / ".claude" / "commands"

    # Source: .claude/commands from the installed package templates
    # Commands are stored in templates/.claude/commands to ensure they're packaged in the wheel
    package_dir = Path(__file__).parent.parent
    commands_source_dir = package_dir / "templates" / ".claude" / "commands"

    # Check if source commands directory exists
    if not commands_source_dir.exists():
        raise TemplateNotFoundError(
            template_name=".claude/commands",
            template_path=str(package_dir),
        )

    installed_commands = []

    try:
        # Create .claude/commands directory in project
        commands_dest_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created directory: {commands_dest_dir.relative_to(project_root)}")

        # Copy all .md command files
        command_files = list(commands_source_dir.glob("*.md"))

        if not command_files:
            logger.warning(
                f"No .md files found in {commands_source_dir}. "
                "Slash commands may not work properly."
            )

        for cmd_file in command_files:
            dest_file = commands_dest_dir / cmd_file.name
            shutil.copy2(cmd_file, dest_file)
            installed_commands.append(dest_file)
            logger.debug(f"Installed command: {cmd_file.name}")

        logger.info(f"Installed {len(installed_commands)} Claude Code slash commands")
        logger.info("You can now use slash commands like /start, /end, /work-new in Claude Code")

    except Exception as e:
        raise FileOperationError(
            operation="install",
            file_path=str(commands_dest_dir),
            details=f"Failed to install Claude Code commands: {str(e)}",
            cause=e,
        )

    return installed_commands
