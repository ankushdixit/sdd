#!/usr/bin/env python3
"""
Initialize .session directory structure in current project.
Enhanced with documentation checks and initial scans.
"""

import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime


def check_documentation():
    """Check for project documentation."""
    docs_dir = Path("docs")

    if not docs_dir.exists():
        print("⚠️  No docs/ directory found")
        print("   Recommendation: Create at least docs/vision.md and docs/prd.md")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return False

    # Check for common doc files
    found_docs = []
    for doc_file in ["vision.md", "prd.md", "architecture.md", "README.md"]:
        if (docs_dir / doc_file).exists() or Path(doc_file).exists():
            found_docs.append(doc_file)
            print(f"✓ Found {doc_file}")

    if found_docs:
        print(f"\n✓ Project documentation found ({len(found_docs)} files)")
    else:
        print("\n⚠️  No standard documentation files found")

    return True


def create_directory_structure():
    """Create .session directory structure."""
    session_dir = Path(".session")

    if session_dir.exists():
        print("❌ Error: .session directory already exists")
        print("   Project already initialized")
        return False

    print("\nCreating .session/ structure...")

    # Create directories
    (session_dir / "tracking").mkdir(parents=True)
    (session_dir / "briefings").mkdir(parents=True)
    (session_dir / "history").mkdir(parents=True)
    (session_dir / "specs").mkdir(parents=True)

    print("✓ Created .session/tracking/")
    print("✓ Created .session/briefings/")
    print("✓ Created .session/history/")
    print("✓ Created .session/specs/")

    return True


def initialize_tracking_files():
    """Initialize tracking files from templates."""
    session_dir = Path(".session")
    template_dir = Path(__file__).parent.parent / "templates"

    print("\nInitializing tracking files...")

    # Copy templates
    tracking_files = [
        ("work_items.json", "tracking/work_items.json"),
        ("learnings.json", "tracking/learnings.json"),
        ("status_update.json", "tracking/status_update.json"),
    ]

    for src, dst in tracking_files:
        src_path = template_dir / src
        dst_path = session_dir / dst
        if src_path.exists():
            shutil.copy(src_path, dst_path)
            print(f"✓ Created {dst}")

    # Create empty files for stack and tree tracking
    (session_dir / "tracking" / "stack_updates.json").write_text(
        json.dumps({"updates": []}, indent=2)
    )
    print("✓ Created stack_updates.json")

    (session_dir / "tracking" / "tree_updates.json").write_text(
        json.dumps({"updates": []}, indent=2)
    )
    print("✓ Created tree_updates.json")

    return True


def run_initial_scans():
    """Run initial stack and tree scans."""
    print("\nRunning initial scans...")

    # Run generate_stack.py
    try:
        subprocess.run(
            ["python", "scripts/generate_stack.py"],
            check=True,
            capture_output=True
        )
        print("✓ Generated stack.txt")
    except subprocess.CalledProcessError:
        print("⚠️  Could not generate stack.txt (will be generated on first session)")

    # Run generate_tree.py
    try:
        subprocess.run(
            ["python", "scripts/generate_tree.py"],
            check=True,
            capture_output=True
        )
        print("✓ Generated tree.txt")
    except subprocess.CalledProcessError:
        print("⚠️  Could not generate tree.txt (will be generated on first session)")

    return True


def init_project():
    """Main initialization function."""
    print("Initializing Session-Driven Development...\n")

    # Check documentation
    if not check_documentation():
        return 1

    # Create directory structure
    if not create_directory_structure():
        return 1

    # Initialize tracking files
    if not initialize_tracking_files():
        return 1

    # Run initial scans
    run_initial_scans()

    print("\n" + "="*50)
    print("Session-Driven Development initialized successfully!")
    print("="*50)
    print("\nNext steps:")
    print("1. Create work items: /work-item create")
    print("2. Start first session: /session-start")
    print()

    return 0


if __name__ == "__main__":
    exit(init_project())
