#!/usr/bin/env python3
"""
Sync SDD main repository to claude-plugins marketplace repository.

This script automates the process of syncing files from the main SDD repo
to the claude-plugins marketplace repo, handling transformations and preserving
plugin-specific files.

Usage:
    python scripts/sync_to_plugin.py [--main-repo PATH] [--plugin-repo PATH] [--dry-run]

Arguments:
    --main-repo PATH     Path to main SDD repository (default: current directory)
    --plugin-repo PATH   Path to claude-plugins repository (required)
    --dry-run           Show what would be synced without making changes
"""

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import List, Tuple, Dict


class PluginSyncer:
    """Handles syncing from main SDD repo to claude-plugins marketplace."""

    # Define file mappings: (source_path, dest_path, is_directory)
    FILE_MAPPINGS = [
        ("sdd_cli.py", "sdd/sdd_cli.py", False),
        ("scripts", "sdd/scripts", True),
        ("templates", "sdd/templates", True),
        ("hooks", "sdd/hooks", True),
        (".claude/commands", "sdd/commands", True),
    ]

    # Files to preserve in plugin repo (never overwrite)
    # These files are maintained separately in the plugin marketplace repo
    PRESERVE_FILES = [
        ".claude-plugin/plugin.json",  # Only update version field
        "README.md",  # Plugin has its own marketplace README
        "CONTRIBUTING.md",  # Directs contributors to main SDD repo
        "LICENSE",  # Static license file for marketplace
        "SECURITY.md",  # Static security policy for marketplace
        ".git",  # Git metadata
        ".github",  # Plugin repo's own workflows
    ]

    def __init__(self, main_repo: Path, plugin_repo: Path, dry_run: bool = False):
        """
        Initialize the syncer.

        Args:
            main_repo: Path to main SDD repository
            plugin_repo: Path to claude-plugins repository
            dry_run: If True, show what would be done without making changes
        """
        self.main_repo = main_repo.resolve()
        self.plugin_repo = plugin_repo.resolve()
        self.dry_run = dry_run
        self.changes: List[str] = []

    def validate_repos(self) -> bool:
        """Validate that both repositories exist and have expected structure."""
        # Check main repo
        if not self.main_repo.exists():
            print(f"❌ Main repo not found: {self.main_repo}")
            return False

        main_markers = ["sdd_cli.py", "pyproject.toml", ".claude/commands"]
        for marker in main_markers:
            if not (self.main_repo / marker).exists():
                print(f"❌ Main repo missing expected file/dir: {marker}")
                return False

        # Check plugin repo
        if not self.plugin_repo.exists():
            print(f"❌ Plugin repo not found: {self.plugin_repo}")
            return False

        plugin_markers = ["sdd", "sdd/.claude-plugin/plugin.json"]
        for marker in plugin_markers:
            if not (self.plugin_repo / marker).exists():
                print(f"❌ Plugin repo missing expected file/dir: {marker}")
                return False

        print("✅ Repository validation passed")
        return True

    def get_version_from_main(self) -> str:
        """Extract version from pyproject.toml in main repo."""
        pyproject_path = self.main_repo / "pyproject.toml"
        if not pyproject_path.exists():
            raise FileNotFoundError(f"pyproject.toml not found in {self.main_repo}")

        with open(pyproject_path, "r") as f:
            for line in f:
                if line.strip().startswith("version"):
                    # Extract version from line like: version = "0.5.7"
                    version = line.split("=")[1].strip().strip('"')
                    return version

        raise ValueError("Version not found in pyproject.toml")

    def update_plugin_version(self, version: str) -> None:
        """Update version in plugin.json."""
        plugin_json_path = self.plugin_repo / "sdd" / ".claude-plugin" / "plugin.json"

        if self.dry_run:
            print(f"[DRY RUN] Would update plugin.json version to {version}")
            self.changes.append(f"Update plugin.json version to {version}")
            return

        with open(plugin_json_path, "r") as f:
            plugin_data = json.load(f)

        old_version = plugin_data.get("version", "unknown")
        plugin_data["version"] = version

        with open(plugin_json_path, "w") as f:
            json.dump(plugin_data, f, indent=2)
            f.write("\n")  # Add trailing newline

        change_msg = f"Updated plugin.json version: {old_version} → {version}"
        print(f"✅ {change_msg}")
        self.changes.append(change_msg)

    def sync_file(self, src: Path, dest: Path) -> None:
        """Sync a single file from source to destination."""
        if self.dry_run:
            print(f"[DRY RUN] Would copy: {src.relative_to(self.main_repo)} → {dest.relative_to(self.plugin_repo)}")
            self.changes.append(f"Copy {src.relative_to(self.main_repo)} → {dest.relative_to(self.plugin_repo)}")
            return

        # Create parent directory if needed
        dest.parent.mkdir(parents=True, exist_ok=True)

        # Copy file
        shutil.copy2(src, dest)
        print(f"✅ Copied: {src.relative_to(self.main_repo)} → {dest.relative_to(self.plugin_repo)}")
        self.changes.append(f"Copied {src.relative_to(self.main_repo)}")

    def sync_directory(self, src: Path, dest: Path) -> None:
        """Sync a directory from source to destination."""
        if self.dry_run:
            print(f"[DRY RUN] Would sync directory: {src.relative_to(self.main_repo)} → {dest.relative_to(self.plugin_repo)}")

            # Count files to sync
            file_count = sum(1 for _ in src.rglob("*") if _.is_file())
            self.changes.append(f"Sync directory {src.relative_to(self.main_repo)} ({file_count} files)")
            return

        # Remove existing destination if it exists
        if dest.exists():
            shutil.rmtree(dest)

        # Copy entire directory tree
        shutil.copytree(src, dest)

        # Count files synced
        file_count = sum(1 for _ in dest.rglob("*") if _.is_file())
        print(f"✅ Synced directory: {src.relative_to(self.main_repo)} ({file_count} files)")
        self.changes.append(f"Synced directory {src.relative_to(self.main_repo)} ({file_count} files)")

    def sync_all_files(self) -> None:
        """Sync all files according to FILE_MAPPINGS."""
        print("\n🔄 Syncing files...")

        for src_rel, dest_rel, is_directory in self.FILE_MAPPINGS:
            src = self.main_repo / src_rel
            dest = self.plugin_repo / dest_rel

            if not src.exists():
                print(f"⚠️  Source not found (skipping): {src_rel}")
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

    def sync(self) -> bool:
        """
        Execute the sync process.

        Returns:
            True if sync succeeded, False otherwise
        """
        print("🚀 Starting plugin sync...\n")

        # Validate repositories
        if not self.validate_repos():
            return False

        # Get version from main repo
        try:
            version = self.get_version_from_main()
            print(f"📦 Main repo version: {version}\n")
        except (FileNotFoundError, ValueError) as e:
            print(f"❌ Error getting version: {e}")
            return False

        # Update plugin version
        self.update_plugin_version(version)

        # Sync all files
        self.sync_all_files()

        # Print summary
        print("\n" + "=" * 60)
        print(self.generate_summary())
        print("=" * 60)

        if self.dry_run:
            print("\n⚠️  This was a DRY RUN - no changes were made")
        else:
            print("\n✅ Sync completed successfully!")

        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Sync SDD main repository to claude-plugins marketplace repository"
    )
    parser.add_argument(
        "--main-repo",
        type=Path,
        default=Path.cwd(),
        help="Path to main SDD repository (default: current directory)",
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

    success = syncer.sync()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
