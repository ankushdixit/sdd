#!/usr/bin/env python3
"""
Initialize .session directory structure in current project.
Enhanced with documentation checks and initial scans.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path


def check_documentation():
    """Check for project documentation."""
    docs_dir = Path("docs")

    if not docs_dir.exists():
        print("⚠️  No docs/ directory found")
        print("   Recommendation: Create at least docs/vision.md and docs/prd.md")
        # Auto-continue in non-interactive mode (for testing)
        if not sys.stdin.isatty():
            print("   (Non-interactive mode: continuing anyway)")
            return True
        response = input("Continue anyway? (y/n): ")
        if response.lower() != "y":
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

    # Create config.json with default settings
    config_data = {
        "curation": {
            "auto_curate": True,
            "frequency": 5,
            "dry_run": False,
            "similarity_threshold": 0.7,
            "categories": [
                "architecture_patterns",
                "gotchas",
                "best_practices",
                "technical_debt",
                "performance_insights",
                "security",
            ],
        },
        "quality_gates": {
            "test_execution": {
                "enabled": True,
                "required": True,
                "coverage_threshold": 80,
                "commands": {
                    "python": "pytest --cov --cov-report=json",
                    "javascript": "npm test -- --coverage",
                    "typescript": "npm test -- --coverage",
                },
            },
            "linting": {
                "enabled": True,
                "required": False,
                "auto_fix": True,
                "commands": {
                    "python": "ruff check .",
                    "javascript": "eslint .",
                    "typescript": "eslint .",
                },
            },
            "formatting": {
                "enabled": True,
                "required": False,
                "auto_fix": True,
                "commands": {
                    "python": "ruff format .",
                    "javascript": "prettier --write .",
                    "typescript": "prettier --write .",
                },
            },
            "security": {"enabled": True, "required": True, "fail_on": "high"},
            "documentation": {
                "enabled": True,
                "required": False,
                "check_changelog": True,
                "check_docstrings": True,
                "check_readme": False,
            },
            "context7": {
                "enabled": False,
                "required": False,
                "important_libraries": [],
            },
            "custom_validations": {"rules": []},
        },
        "integration_tests": {
            "enabled": True,
            "docker_compose_file": "docker-compose.integration.yml",
            "environment_validation": True,
            "health_check_timeout": 300,
            "test_data_fixtures": True,
            "parallel_execution": True,
            "performance_benchmarks": {
                "enabled": True,
                "required": True,
                "regression_threshold": 0.10,
                "baseline_storage": ".session/tracking/performance_baselines.json",
                "load_test_tool": "wrk",
                "metrics": ["response_time", "throughput", "resource_usage"],
            },
            "api_contracts": {
                "enabled": True,
                "required": True,
                "contract_format": "openapi",
                "breaking_change_detection": True,
                "version_storage": ".session/tracking/api_contracts/",
                "fail_on_breaking_changes": True,
            },
            "documentation": {
                "architecture_diagrams": True,
                "sequence_diagrams": True,
                "contract_documentation": True,
                "performance_baseline_docs": True,
            },
        },
        "git_workflow": {
            "mode": "pr",
            "auto_push": True,
            "auto_create_pr": True,
            "delete_branch_after_merge": True,
            "pr_title_template": "{type}: {title}",
            "pr_body_template": "## Summary\n\n{description}\n\n## Work Item\n- ID: {work_item_id}\n- Type: {type}\n- Session: {session_num}\n\n## Changes\n{commit_messages}\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>",
        },
    }
    (session_dir / "config.json").write_text(json.dumps(config_data, indent=2))
    print("✓ Created config.json")

    # Copy config schema file
    schema_source = Path(__file__).parent.parent / "templates" / "config.schema.json"
    schema_dest = session_dir / "config.schema.json"

    if schema_source.exists() and not schema_dest.exists():
        shutil.copy(schema_source, schema_dest)
        print("✓ Created config.schema.json")
    elif not schema_source.exists():
        print(
            "⚠️  config.schema.json not found in repository, skipping (validation will be disabled)"
        )

    return True


def run_initial_scans():
    """Run initial stack and tree scans."""
    print("\nRunning initial scans...")

    # Run generate_stack.py
    try:
        subprocess.run(["python", "scripts/generate_stack.py"], check=True, capture_output=True)
        print("✓ Generated stack.txt")
    except subprocess.CalledProcessError:
        print("⚠️  Could not generate stack.txt (will be generated on first session)")

    # Run generate_tree.py
    try:
        subprocess.run(["python", "scripts/generate_tree.py"], check=True, capture_output=True)
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

    print("\n" + "=" * 50)
    print("Session-Driven Development initialized successfully!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Create work items: /work-new")
    print("2. Start first session: /start")
    print()

    return 0


if __name__ == "__main__":
    exit(init_project())
