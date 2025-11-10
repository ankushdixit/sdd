"""
Initial Scans Module

Runs initial stack and tree scans to populate .session/tracking/.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from solokit.core.command_runner import CommandRunner
from solokit.core.constants import GIT_STANDARD_TIMEOUT

logger = logging.getLogger(__name__)


def run_stack_scan(project_root: Path | None = None) -> bool:
    """
    Run stack scan to generate stack.txt.

    Args:
        project_root: Project root directory

    Returns:
        True if scan succeeded
    """
    if project_root is None:
        project_root = Path.cwd()

    # Get Solokit installation directory
    script_dir = Path(__file__).parent.parent / "project"
    stack_script = script_dir / "stack.py"

    if not stack_script.exists():
        logger.warning(f"Stack script not found: {stack_script}")
        return False

    runner = CommandRunner(default_timeout=GIT_STANDARD_TIMEOUT, working_dir=project_root)

    try:
        # Use sys.executable to ensure we use the same Python interpreter
        result = runner.run([sys.executable, str(stack_script)], check=True)
        if result.success:
            logger.info("Generated stack.txt")
            return True
        else:
            logger.warning("Could not generate stack.txt")
            if result.stderr:
                logger.warning(f"Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        logger.warning(f"Stack generation failed: {e}")
        return False


def run_tree_scan(project_root: Path | None = None) -> bool:
    """
    Run tree scan to generate tree.txt.

    Args:
        project_root: Project root directory

    Returns:
        True if scan succeeded
    """
    if project_root is None:
        project_root = Path.cwd()

    # Get Solokit installation directory
    script_dir = Path(__file__).parent.parent / "project"
    tree_script = script_dir / "tree.py"

    if not tree_script.exists():
        logger.warning(f"Tree script not found: {tree_script}")
        return False

    runner = CommandRunner(default_timeout=GIT_STANDARD_TIMEOUT, working_dir=project_root)

    try:
        # Use sys.executable to ensure we use the same Python interpreter
        result = runner.run([sys.executable, str(tree_script)], check=True)
        if result.success:
            logger.info("Generated tree.txt")
            return True
        else:
            logger.warning("Could not generate tree.txt")
            if result.stderr:
                logger.warning(f"Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        logger.warning(f"Tree generation failed: {e}")
        return False


def run_initial_scans(project_root: Path | None = None) -> dict[str, bool]:
    """
    Run initial stack and tree scans.

    Args:
        project_root: Project root directory

    Returns:
        Dictionary with scan results: {"stack": bool, "tree": bool}
    """
    logger.info("Generating project context...")

    stack_success = run_stack_scan(project_root)
    tree_success = run_tree_scan(project_root)

    return {"stack": stack_success, "tree": tree_success}
