#!/usr/bin/env python3
"""
Generate and update project tree documentation.

Tracks structural changes to the project with reasoning.
"""

import json
from datetime import datetime
from pathlib import Path

from sdd.core.command_runner import CommandRunner


class TreeGenerator:
    """Generate project tree documentation."""

    def __init__(self, project_root: Path = None):
        """Initialize TreeGenerator with project root path."""
        self.project_root = project_root or Path.cwd()
        self.tree_file = self.project_root / ".session" / "tracking" / "tree.txt"
        self.updates_file = self.project_root / ".session" / "tracking" / "tree_updates.json"
        self.runner = CommandRunner(default_timeout=30, working_dir=self.project_root)

        # Items to ignore
        self.ignore_patterns = [
            # Version control
            ".git",
            # Python
            "__pycache__",
            "*.pyc",
            ".pytest_cache",
            ".venv",
            "venv",
            "*.egg-info",
            ".mypy_cache",
            ".ruff_cache",
            # JavaScript/TypeScript
            "node_modules",
            ".next",
            ".turbo",
            "out",
            "build",
            "dist",
            ".vercel",
            "*.tsbuildinfo",
            # Test coverage
            "coverage",
            ".nyc_output",
            # Caches
            ".cache",
            # OS
            ".DS_Store",
            # Temp/logs
            "*.log",
            "*.tmp",
            "*.backup",
            # SDD
            ".session",
        ]

    def generate_tree(self) -> str:
        """Generate tree using tree command."""
        try:
            # Build ignore arguments
            ignore_args = []
            for pattern in self.ignore_patterns:
                ignore_args.extend(["-I", pattern])

            result = self.runner.run(["tree", "-a", "--dirsfirst"] + ignore_args)

            if result.success:
                return result.stdout
            else:
                return self._generate_tree_fallback()

        except Exception:
            # tree command not available, use fallback
            return self._generate_tree_fallback()

    def _generate_tree_fallback(self) -> str:
        """Fallback tree generation without tree command."""
        lines = [str(self.project_root.name) + "/"]

        def should_ignore(path: Path) -> bool:
            for pattern in self.ignore_patterns:
                if pattern.startswith("*"):
                    if path.name.endswith(pattern[1:]):
                        return True
                elif pattern in path.parts:
                    return True
            return False

        def add_tree(path: Path, prefix: str = "", is_last: bool = True):
            if should_ignore(path):
                return

            connector = "└── " if is_last else "├── "
            lines.append(prefix + connector + path.name)

            if path.is_dir():
                children = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
                children = [c for c in children if not should_ignore(c)]

                for i, child in enumerate(children):
                    is_last_child = i == len(children) - 1
                    extension = "    " if is_last else "│   "
                    add_tree(child, prefix + extension, is_last_child)

        # Generate tree
        children = sorted(self.project_root.iterdir(), key=lambda p: (not p.is_dir(), p.name))
        children = [c for c in children if not should_ignore(c)]

        for i, child in enumerate(children):
            add_tree(child, "", i == len(children) - 1)

        return "\n".join(lines)

    def detect_changes(self, old_tree: str, new_tree: str) -> list[dict]:
        """Detect structural changes between trees."""
        old_lines = set(old_tree.split("\n"))
        new_lines = set(new_tree.split("\n"))

        added = new_lines - old_lines
        removed = old_lines - new_lines

        changes = []

        # Categorize changes
        for line in added:
            if "/" in line or line.strip().endswith("/"):
                changes.append({"type": "directory_added", "path": line.strip()})
            elif line.strip():
                changes.append({"type": "file_added", "path": line.strip()})

        for line in removed:
            if "/" in line or line.strip().endswith("/"):
                changes.append({"type": "directory_removed", "path": line.strip()})
            elif line.strip():
                changes.append({"type": "file_removed", "path": line.strip()})

        return changes

    def update_tree(self, session_num: int = None, non_interactive: bool = False):
        """Generate/update tree.txt and detect changes.

        Args:
            session_num: Current session number
            non_interactive: If True, skip interactive reasoning prompts
        """
        # Generate new tree
        new_tree = self.generate_tree()

        # Load old tree if exists
        old_tree = ""
        if self.tree_file.exists():
            old_tree = self.tree_file.read_text()

        # Detect changes
        changes = self.detect_changes(old_tree, new_tree)

        # Filter out minor changes (just ordering, etc.)
        significant_changes = [
            c
            for c in changes
            if c["type"] in ["directory_added", "directory_removed"]
            or len(changes) < 20  # If few changes, they're probably significant
        ]

        # Save new tree
        self.tree_file.parent.mkdir(parents=True, exist_ok=True)
        self.tree_file.write_text(new_tree)

        # If significant changes detected, prompt for reasoning (unless non-interactive)
        if significant_changes and session_num:
            print(f"\n{'=' * 50}")
            print("Structural Changes Detected")
            print("=" * 50)

            for change in significant_changes[:10]:  # Show first 10
                print(f"  {change['type'].upper()}: {change['path']}")

            if len(significant_changes) > 10:
                print(f"  ... and {len(significant_changes) - 10} more changes")

            if non_interactive:
                reasoning = "Automated update during session completion"
                print("\n(Non-interactive mode: recording changes without manual reasoning)")
            else:
                print("\nPlease provide reasoning for these structural changes:")
                reasoning = input("> ")

            # Update tree_updates.json
            self._record_tree_update(session_num, significant_changes, reasoning)

        return changes

    def _record_tree_update(self, session_num: int, changes: list[dict], reasoning: str):
        """Record tree update in tree_updates.json."""
        updates = {"updates": []}

        if self.updates_file.exists():
            try:
                updates = json.loads(self.updates_file.read_text())
            except:  # noqa: E722
                pass

        update_entry = {
            "timestamp": datetime.now().isoformat(),
            "session": session_num,
            "changes": changes,
            "reasoning": reasoning,
            "architecture_impact": "",  # Could prompt for this too
        }

        updates["updates"].append(update_entry)

        self.updates_file.write_text(json.dumps(updates, indent=2))


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate project tree documentation")
    parser.add_argument("--session", type=int, help="Current session number")
    parser.add_argument("--show-changes", action="store_true", help="Show changes from last run")
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Skip interactive prompts (use automated reasoning)",
    )
    args = parser.parse_args()

    generator = TreeGenerator()

    if args.show_changes:
        if generator.updates_file.exists():
            updates = json.loads(generator.updates_file.read_text())
            print("Recent structural changes:")
            for update in updates["updates"][-5:]:
                print(f"\nSession {update['session']} ({update['timestamp']})")
                print(f"Reasoning: {update['reasoning']}")
                print(f"Changes: {len(update['changes'])}")
        else:
            print("No tree updates recorded yet")
    else:
        changes = generator.update_tree(
            session_num=args.session, non_interactive=args.non_interactive
        )

        if changes:
            print(f"\n✓ Tree updated with {len(changes)} changes")
        else:
            print("\n✓ Tree generated (no changes)")

        print(f"✓ Saved to: {generator.tree_file}")


if __name__ == "__main__":
    main()
