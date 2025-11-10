#!/usr/bin/env python3
"""
Sync Solokit main repository to claude-plugins marketplace repository.

This script automates the process of syncing files from the main Solokit repo
to the claude-plugins marketplace repo, handling transformations and preserving
plugin-specific files.

Note: This script is automatically executed by GitHub Actions on every push to main.
      See .github/workflows/sync-plugin.yml for the automation workflow.

Usage:
    python src/solokit/project/sync_plugin.py [--main-repo PATH] [--plugin-repo PATH] [--dry-run]

Arguments:
    --main-repo PATH     Path to main Solokit repository (default: current directory)
    --plugin-repo PATH   Path to claude-plugins repository (required)
    --dry-run           Show what would be synced without making changes
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

from solokit.core.exceptions import (
    ErrorCode,
    FileOperationError,
    ValidationError,
)
from solokit.core.exceptions import (
    FileNotFoundError as SolokitFileNotFoundError,
)
from solokit.core.logging_config import get_logger

logger = get_logger(__name__)


class PluginSyncer:
    """Handles syncing from main Solokit repo to claude-plugins marketplace."""

    # Define file mappings: (source_path, dest_path, is_directory)
    FILE_MAPPINGS = [
        ("src/solokit", "solokit/src/solokit", True),
        (".claude/commands", "solokit/commands", True),
        ("pyproject.toml", "solokit/pyproject.toml", False),
    ]

    # Files to preserve in plugin repo (never overwrite)
    # These files are maintained separately in the plugin marketplace repo
    PRESERVE_FILES = [
        ".claude-plugin/plugin.json",  # Only update version field
        "README.md",  # Plugin has its own marketplace README
        "CONTRIBUTING.md",  # Directs contributors to main Solokit repo
        "LICENSE",  # Static license file for marketplace
        "SECURITY.md",  # Static security policy for marketplace
        ".git",  # Git metadata
        ".github",  # Plugin repo's own workflows
    ]

    def __init__(self, main_repo: Path, plugin_repo: Path, dry_run: bool = False):
        """
        Initialize the syncer.

        Args:
            main_repo: Path to main Solokit repository
            plugin_repo: Path to claude-plugins repository
            dry_run: If True, show what would be done without making changes
        """
        self.main_repo = main_repo.resolve()
        self.plugin_repo = plugin_repo.resolve()
        self.dry_run = dry_run
        self.changes: list[str] = []

    def validate_repos(self) -> None:
        """
        Validate that both repositories exist and have expected structure.

        Raises:
            SolokitFileNotFoundError: If repository path doesn't exist
            ValidationError: If repository is missing expected files/directories
        """
        # Check main repo
        if not self.main_repo.exists():
            raise SolokitFileNotFoundError(
                file_path=str(self.main_repo), file_type="main repository"
            )

        main_markers = ["src/solokit/cli.py", "pyproject.toml", ".claude/commands"]
        for marker in main_markers:
            if not (self.main_repo / marker).exists():
                raise ValidationError(
                    message=f"Main repository missing expected file/directory: {marker}",
                    code=ErrorCode.CONFIG_VALIDATION_FAILED,
                    context={
                        "repository": str(self.main_repo),
                        "missing_marker": marker,
                        "marker_type": "file" if "." in marker else "directory",
                    },
                    remediation=f"Ensure {self.main_repo} is a valid Solokit repository",
                )

        # Check plugin repo
        if not self.plugin_repo.exists():
            raise SolokitFileNotFoundError(
                file_path=str(self.plugin_repo), file_type="plugin repository"
            )

        plugin_markers = ["solokit", "solokit/.claude-plugin/plugin.json"]
        for marker in plugin_markers:
            if not (self.plugin_repo / marker).exists():
                raise ValidationError(
                    message=f"Plugin repository missing expected file/directory: {marker}",
                    code=ErrorCode.CONFIG_VALIDATION_FAILED,
                    context={
                        "repository": str(self.plugin_repo),
                        "missing_marker": marker,
                        "marker_type": "file" if "plugin.json" in marker else "directory",
                    },
                    remediation=f"Ensure {self.plugin_repo} is a valid claude-plugins repository",
                )

        logger.info("Repository validation passed")

    def get_version_from_main(self) -> str:
        """
        Extract version from pyproject.toml in main repo.

        Returns:
            Version string (e.g., "0.5.7")

        Raises:
            SolokitFileNotFoundError: If pyproject.toml doesn't exist
            ValidationError: If version field not found in pyproject.toml
            FileOperationError: If file cannot be read
        """
        pyproject_path = self.main_repo / "pyproject.toml"
        if not pyproject_path.exists():
            raise SolokitFileNotFoundError(
                file_path=str(pyproject_path), file_type="pyproject.toml"
            )

        try:
            with open(pyproject_path) as f:
                for line in f:
                    if line.strip().startswith("version"):
                        # Extract version from line like: version = "0.5.7"
                        version = line.split("=")[1].strip().strip('"')
                        return version
        except OSError as e:
            raise FileOperationError(
                operation="read", file_path=str(pyproject_path), details=str(e), cause=e
            )

        raise ValidationError(
            message="Version not found in pyproject.toml",
            code=ErrorCode.MISSING_REQUIRED_FIELD,
            context={"file_path": str(pyproject_path), "expected_field": "version"},
            remediation="Ensure pyproject.toml contains a 'version = \"x.y.z\"' line",
        )

    def update_plugin_version(self, version: str) -> None:
        """
        Update version in plugin.json.

        Args:
            version: Version string to set (e.g., "0.5.7")

        Raises:
            FileOperationError: If plugin.json cannot be read, parsed, or written
        """
        plugin_json_path = self.plugin_repo / "solokit" / ".claude-plugin" / "plugin.json"

        if self.dry_run:
            logger.info(f"[DRY RUN] Would update plugin.json version to {version}")
            self.changes.append(f"Update plugin.json version to {version}")
            return

        try:
            with open(plugin_json_path) as f:
                plugin_data = json.load(f)
        except json.JSONDecodeError as e:
            raise FileOperationError(
                operation="parse",
                file_path=str(plugin_json_path),
                details=f"Invalid JSON: {e}",
                cause=e,
            )
        except OSError as e:
            raise FileOperationError(
                operation="read", file_path=str(plugin_json_path), details=str(e), cause=e
            )

        old_version = plugin_data.get("version", "unknown")
        plugin_data["version"] = version

        try:
            with open(plugin_json_path, "w") as f:
                json.dump(plugin_data, f, indent=2)
                f.write("\n")  # Add trailing newline
        except OSError as e:
            raise FileOperationError(
                operation="write", file_path=str(plugin_json_path), details=str(e), cause=e
            )

        change_msg = f"Updated plugin.json version: {old_version} → {version}"
        logger.info(change_msg)
        self.changes.append(change_msg)

    def sync_file(self, src: Path, dest: Path) -> None:
        """
        Sync a single file from source to destination.

        Args:
            src: Source file path
            dest: Destination file path

        Raises:
            FileOperationError: If file copy operation fails
        """
        if self.dry_run:
            logger.info(
                f"[DRY RUN] Would copy: {src.relative_to(self.main_repo)} → {dest.relative_to(self.plugin_repo)}"
            )
            self.changes.append(
                f"Copy {src.relative_to(self.main_repo)} → {dest.relative_to(self.plugin_repo)}"
            )
            return

        try:
            # Create parent directory if needed
            dest.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            shutil.copy2(src, dest)
        except (OSError, shutil.Error) as e:
            raise FileOperationError(
                operation="copy",
                file_path=str(src),
                details=f"Failed to copy to {dest}: {e}",
                cause=e,
            )

        logger.info(
            f"Copied: {src.relative_to(self.main_repo)} → {dest.relative_to(self.plugin_repo)}"
        )
        self.changes.append(f"Copied {src.relative_to(self.main_repo)}")

    def sync_directory(self, src: Path, dest: Path) -> None:
        """
        Sync a directory from source to destination.

        Args:
            src: Source directory path
            dest: Destination directory path

        Raises:
            FileOperationError: If directory sync operation fails
        """
        if self.dry_run:
            logger.info(
                f"[DRY RUN] Would sync directory: {src.relative_to(self.main_repo)} → {dest.relative_to(self.plugin_repo)}"
            )

            # Count files to sync
            file_count = sum(1 for _ in src.rglob("*") if _.is_file())
            self.changes.append(
                f"Sync directory {src.relative_to(self.main_repo)} ({file_count} files)"
            )
            return

        try:
            # Remove existing destination if it exists
            if dest.exists():
                shutil.rmtree(dest)

            # Copy entire directory tree
            shutil.copytree(src, dest)
        except (OSError, shutil.Error) as e:
            raise FileOperationError(
                operation="sync_directory",
                file_path=str(src),
                details=f"Failed to sync directory to {dest}: {e}",
                cause=e,
            )

        # Count files synced
        file_count = sum(1 for _ in dest.rglob("*") if _.is_file())
        logger.info(f"Synced directory: {src.relative_to(self.main_repo)} ({file_count} files)")
        self.changes.append(
            f"Synced directory {src.relative_to(self.main_repo)} ({file_count} files)"
        )

    def sync_all_files(self) -> None:
        """
        Sync all files according to FILE_MAPPINGS.

        Raises:
            FileOperationError: If any file/directory sync operation fails
        """
        logger.info("Syncing files...")

        for src_rel, dest_rel, is_directory in self.FILE_MAPPINGS:
            src = self.main_repo / src_rel
            dest = self.plugin_repo / dest_rel

            if not src.exists():
                logger.warning(f"Source not found (skipping): {src_rel}")
                continue

            if is_directory:
                self.sync_directory(src, dest)
            else:
                self.sync_file(src, dest)

    def generate_summary(self) -> str:
        """Generate a summary of all changes made."""
        summary_lines = [
            "# Plugin Sync Summary",
            "",
            f"Main repo: {self.main_repo}",
            f"Plugin repo: {self.plugin_repo}",
            f"Dry run: {self.dry_run}",
            "",
            "## Changes:",
        ]

        if self.changes:
            for change in self.changes:
                summary_lines.append(f"- {change}")
        else:
            summary_lines.append("- No changes made")

        return "\n".join(summary_lines)

    def sync(self) -> None:
        """
        Execute the sync process.

        Raises:
            SolokitFileNotFoundError: If repository paths don't exist
            ValidationError: If repositories are missing expected files
            FileOperationError: If file operations fail
        """
        logger.info("Starting plugin sync...")

        # Validate repositories
        self.validate_repos()

        # Get version from main repo
        version = self.get_version_from_main()
        logger.info(f"Main repo version: {version}")

        # Update plugin version
        self.update_plugin_version(version)

        # Sync all files
        self.sync_all_files()

        # Print summary
        logger.info("=" * 60)
        logger.info(self.generate_summary())
        logger.info("=" * 60)

        if self.dry_run:
            logger.warning("This was a DRY RUN - no changes were made")
        else:
            logger.info("Sync completed successfully!")


def main() -> None:
    """
    Main entry point.

    Exit codes:
        0: Success
        1: General error
        2: Validation error
        3: File not found
        4: Configuration error
        5: System/file operation error
    """
    parser = argparse.ArgumentParser(
        description="Sync Solokit main repository to claude-plugins marketplace repository"
    )
    parser.add_argument(
        "--main-repo",
        type=Path,
        default=Path.cwd(),
        help="Path to main Solokit repository (default: current directory)",
    )
    parser.add_argument(
        "--plugin-repo",
        type=Path,
        required=True,
        help="Path to claude-plugins repository",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be synced without making changes",
    )

    args = parser.parse_args()

    # Create syncer and run
    syncer = PluginSyncer(
        main_repo=args.main_repo,
        plugin_repo=args.plugin_repo,
        dry_run=args.dry_run,
    )

    try:
        syncer.sync()
        sys.exit(0)
    except SolokitFileNotFoundError as e:
        logger.error(f"File not found: {e.message}")
        if e.remediation:
            logger.error(f"Remediation: {e.remediation}")
        sys.exit(e.exit_code)
    except ValidationError as e:
        logger.error(f"Validation error: {e.message}")
        if e.remediation:
            logger.error(f"Remediation: {e.remediation}")
        sys.exit(e.exit_code)
    except FileOperationError as e:
        logger.error(f"File operation error: {e.message}")
        if e.remediation:
            logger.error(f"Remediation: {e.remediation}")
        sys.exit(e.exit_code)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
