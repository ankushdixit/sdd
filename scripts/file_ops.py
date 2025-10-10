"""File operations utilities

Simple utilities for file and JSON operations.
"""

import json
import shutil
from pathlib import Path
from typing import Any


def load_json(file_path: Path) -> dict[str, Any]:
    """Load JSON file"""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path) as f:
        return json.load(f)


def save_json(file_path: Path, data: dict[str, Any], indent: int = 2) -> None:
    """Save data to JSON file with atomic write"""
    # Write to temp file first
    temp_path = file_path.with_suffix(".tmp")

    with open(temp_path, "w") as f:
        json.dump(data, f, indent=indent, default=str)

    # Atomic rename
    temp_path.replace(file_path)


def ensure_directory(path: Path) -> None:
    """Ensure directory exists"""
    path.mkdir(parents=True, exist_ok=True)


def backup_file(file_path: Path) -> Path:
    """Create backup of a file"""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
    shutil.copy2(file_path, backup_path)
    return backup_path


def read_file(file_path: Path) -> str:
    """Read file contents"""
    with open(file_path) as f:
        return f.read()


def write_file(file_path: Path, content: str) -> None:
    """Write content to file"""
    with open(file_path, "w") as f:
        f.write(content)
