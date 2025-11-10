"""
System utilities for cross-platform compatibility.

This module provides utilities for detecting system capabilities and
adapting behavior for better cross-platform compatibility.
"""

from __future__ import annotations

import shutil
import sys


def get_python_binary() -> str:
    """
    Detect available Python binary (python vs python3).

    On many modern systems (especially macOS), only `python3` is available
    while older systems or some Linux distributions have `python` pointing
    to Python 3.

    Returns:
        str: The Python binary name ("python3", "python", or sys.executable)

    Example:
        >>> binary = get_python_binary()
        >>> print(f"Use: {binary} -m solokit.work_items.get_metadata")
    """
    if shutil.which("python3"):
        return "python3"
    elif shutil.which("python"):
        return "python"
    else:
        # Fallback to current interpreter
        return sys.executable


def format_python_command(module_path: str, args: str = "") -> str:
    """
    Format a python -m command with correct binary and arguments.

    Args:
        module_path: Python module path (e.g., "solokit.work_items.get_metadata")
        args: Optional arguments to append

    Returns:
        str: Formatted command (e.g., "python3 -m solokit.work_items.get_metadata <args>")

    Example:
        >>> cmd = format_python_command("solokit.work_items.get_metadata", "feat_001 --with-deps")
        >>> print(cmd)
        python3 -m solokit.work_items.get_metadata feat_001 --with-deps
    """
    binary = get_python_binary()
    if args:
        return f"{binary} -m {module_path} {args}"
    return f"{binary} -m {module_path}"
