#!/usr/bin/env python3
"""
Initialize .session directory structure in current project.
"""

import json
import shutil
from pathlib import Path


def init_project():
    """Create .session directory structure."""
    session_dir = Path(".session")

    if session_dir.exists():
        print("⚠️  .session directory already exists")
        return

    print("Initializing Session-Driven Development structure...\n")

    # Create directories
    (session_dir / "tracking").mkdir(parents=True)
    (session_dir / "briefings").mkdir(parents=True)
    (session_dir / "history").mkdir(parents=True)
    (session_dir / "specs").mkdir(parents=True)

    # Copy templates
    template_dir = Path(__file__).parent.parent / "templates"

    shutil.copy(
        template_dir / "work_items.json",
        session_dir / "tracking" / "work_items.json"
    )
    shutil.copy(
        template_dir / "learnings.json",
        session_dir / "tracking" / "learnings.json"
    )
    shutil.copy(
        template_dir / "status_update.json",
        session_dir / "tracking" / "status_update.json"
    )

    print("✓ Created .session/tracking/")
    print("✓ Created .session/briefings/")
    print("✓ Created .session/history/")
    print("✓ Created .session/specs/")
    print("✓ Initialized tracking files\n")

    print("Session-Driven Development initialized!")
    print("\nNext steps:")
    print("1. Create your first work item")
    print("2. Run /session-start to begin")


if __name__ == "__main__":
    init_project()
