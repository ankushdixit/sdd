"""
Git Hooks Installer Module

Installs git hooks from templates.
"""

from __future__ import annotations

import logging
import shutil
import stat
from pathlib import Path

from solokit.core.exceptions import FileOperationError, NotAGitRepoError, TemplateNotFoundError

logger = logging.getLogger(__name__)


def install_git_hooks(project_root: Path | None = None) -> list[Path]:
    """
    Install git hooks from templates.

    Args:
        project_root: Root directory of the project. Defaults to current working directory.

    Returns:
        List of installed hook paths

    Raises:
        NotAGitRepoError: If .git/hooks directory doesn't exist (git not initialized).
        TemplateNotFoundError: If hook template file is not found.
        FileOperationError: If hook installation or permission setting fails.
    """
    if project_root is None:
        project_root = Path.cwd()

    git_hooks_dir = project_root / ".git" / "hooks"

    # Check if .git/hooks exists
    if not git_hooks_dir.exists():
        raise NotAGitRepoError(str(project_root))

    # Get template directory
    template_dir = Path(__file__).parent.parent / "templates" / "git-hooks"

    installed_hooks = []

    # Install prepare-commit-msg hook
    hook_template = template_dir / "prepare-commit-msg"
    hook_dest = git_hooks_dir / "prepare-commit-msg"

    if not hook_template.exists():
        raise TemplateNotFoundError(
            template_name="prepare-commit-msg", template_path=str(template_dir)
        )

    try:
        shutil.copy(hook_template, hook_dest)
        # Make executable (chmod +x)
        hook_dest.chmod(hook_dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        installed_hooks.append(hook_dest)
        logger.info("Installed git prepare-commit-msg hook")
    except Exception as e:
        raise FileOperationError(
            operation="install",
            file_path=str(hook_dest),
            details=f"Failed to copy or set permissions: {str(e)}",
            cause=e,
        )

    return installed_hooks
