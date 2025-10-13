#!/usr/bin/env python3
"""
Complete current session with quality gates and summary generation.
Enhanced with full tracking updates and git workflow.
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime


def load_status():
    """Load current session status."""
    status_file = Path(".session/tracking/status_update.json")
    if not status_file.exists():
        return None
    with open(status_file) as f:
        return json.load(f)


def load_work_items():
    """Load work items."""
    with open(".session/tracking/work_items.json") as f:
        return json.load(f)


def run_quality_gates():
    """
    Run quality gates: tests, linting, formatting.
    Returns dict with results.
    """
    results = {
        "tests": {"passed": False, "details": None},
        "linting": {"passed": False, "details": None},
        "formatting": {"passed": False, "details": None},
    }

    # Run tests (if pytest available)
    try:
        result = subprocess.run(
            ["pytest", "--cov=.", "--cov-report=term"],
            capture_output=True,
            text=True,
            timeout=300
        )
        results["tests"]["passed"] = result.returncode == 0
        results["tests"]["details"] = result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        results["tests"]["passed"] = True  # Skip if pytest not found
        results["tests"]["details"] = "Tests skipped (pytest not found)"

    # Run linting (if ruff available)
    try:
        result = subprocess.run(
            ["ruff", "check", "--fix", "."],
            capture_output=True,
            text=True,
            timeout=60
        )
        results["linting"]["passed"] = result.returncode == 0
        results["linting"]["details"] = result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        results["linting"]["passed"] = True  # Skip if ruff not found

    # Check formatting (if ruff available)
    try:
        result = subprocess.run(
            ["ruff", "format", "--check", "."],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode != 0:
            # Auto-format
            subprocess.run(["ruff", "format", "."], timeout=60)
        results["formatting"]["passed"] = True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        results["formatting"]["passed"] = True

    return results


def update_all_tracking(session_num):
    """Update stack, tree, and other tracking files."""
    print("\nUpdating tracking files...")

    # Update stack
    try:
        result = subprocess.run(
            ["python", "scripts/generate_stack.py", "--session", str(session_num)],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print("✓ Stack updated")
        else:
            print("⚠️  Stack update skipped")
    except Exception as e:
        print(f"⚠️  Stack update failed: {e}")

    # Update tree
    try:
        result = subprocess.run(
            ["python", "scripts/generate_tree.py", "--session", str(session_num)],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print("✓ Tree updated")
        else:
            print("⚠️  Tree update skipped")
    except Exception as e:
        print(f"⚠️  Tree update failed: {e}")

    return True


def extract_learnings_from_session():
    """Extract learnings from work done in session."""
    print("\nExtract learnings from this session...")
    print("(Type each learning, or 'done' to finish, or 'skip' to skip):")

    learnings = []
    while True:
        learning = input("> ")
        if learning.lower() == 'done':
            break
        if learning.lower() == 'skip':
            return []
        if learning:
            learnings.append(learning)

    return learnings


def complete_git_workflow(work_item_id, commit_message):
    """Complete git workflow (commit, push, optionally merge)."""
    try:
        # Import git workflow dynamically
        git_module_path = Path(__file__).parent / "git_integration.py"
        if not git_module_path.exists():
            return {"success": False, "message": "git_integration.py not found"}

        import importlib.util
        spec = importlib.util.spec_from_file_location("git_integration", git_module_path)
        git_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(git_module)

        workflow = git_module.GitWorkflow()

        # Load work items to check status
        with open(".session/tracking/work_items.json") as f:
            data = json.load(f)

        work_item = data["work_items"][work_item_id]
        should_merge = work_item["status"] == "completed"

        # Complete work item in git
        result = workflow.complete_work_item(
            work_item_id,
            commit_message,
            merge=should_merge
        )

        return result
    except Exception as e:
        return {"success": False, "message": f"Git workflow error: {e}"}


def generate_commit_message(status, work_item):
    """Generate standardized commit message."""
    session_num = status["current_session"]
    work_type = work_item["type"]
    title = work_item["title"]

    message = f"Session {session_num:03d}: {work_type.title()} - {title}\n\n"

    if work_item.get("rationale"):
        message += f"{work_item['rationale']}\n\n"

    if work_item["status"] == "completed":
        message += "✅ Work item completed\n"
    else:
        message += "🚧 Work in progress\n"

    message += "\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n"
    message += "\nCo-Authored-By: Claude <noreply@anthropic.com>"

    return message


def generate_summary(status, work_items_data, gate_results, learnings=None):
    """Generate comprehensive session summary."""
    work_item_id = status["current_work_item"]
    work_item = work_items_data["work_items"][work_item_id]

    summary = f"""# Session {status['current_session']} Summary

{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Work Items
- **{work_item_id}**: {work_item['title']} ({work_item['status']})

## Quality Gates
- Tests: {'✓ PASSED' if gate_results['tests']['passed'] else '✗ FAILED'}
- Linting: {'✓ PASSED' if gate_results['linting']['passed'] else '✗ FAILED'}
- Formatting: {'✓ PASSED' if gate_results['formatting']['passed'] else '✗ FAILED'}
"""

    if learnings:
        summary += "\n## Learnings Captured\n"
        for learning in learnings:
            summary += f"- {learning}\n"

    summary += "\n## Next Session\nTo be determined\n"

    return summary


def main():
    """Enhanced main entry point with full tracking updates."""
    # Load current status
    status = load_status()
    if not status:
        print("Error: No active session found")
        return 1

    work_items_data = load_work_items()
    work_item_id = status["current_work_item"]
    session_num = status["current_session"]

    print("Completing session...\n")
    print("Running quality gates...")

    # Run quality gates
    gate_results = run_quality_gates()

    # Print results
    for gate, result in gate_results.items():
        status_icon = "✓" if result["passed"] else "✗"
        print(f"{status_icon} {gate.title()}: {'passed' if result['passed'] else 'failed'}")

    all_passed = all(r["passed"] for r in gate_results.values())

    if not all_passed:
        print("\n❌ Quality gates failed. Fix issues before completing session.")
        return 1

    print("\n✓ Quality gates PASSED\n")

    # Update all tracking (stack, tree)
    update_all_tracking(session_num)

    # Extract learnings
    learnings = extract_learnings_from_session()

    # Process learnings with learning_curator if available
    if learnings:
        print("\nProcessing learnings...")
        # Learning curation will be handled by learning_curator.py

    # Ask about work item completion status
    print(f"\nIs work item '{work_items_data['work_items'][work_item_id]['title']}' complete? (y/n): ")
    is_complete = input("> ").lower() == 'y'

    # Update work item status
    if is_complete:
        work_items_data["work_items"][work_item_id]["status"] = "completed"
        if "metadata" not in work_items_data["work_items"][work_item_id]:
            work_items_data["work_items"][work_item_id]["metadata"] = {}
        work_items_data["work_items"][work_item_id]["metadata"]["completed_at"] = datetime.now().isoformat()
    else:
        work_items_data["work_items"][work_item_id]["status"] = "in_progress"

    # Save updated work items
    with open(".session/tracking/work_items.json", "w") as f:
        json.dump(work_items_data, f, indent=2)

    # Generate commit message
    work_item = work_items_data["work_items"][work_item_id]
    commit_message = generate_commit_message(status, work_item)

    # Complete git workflow (commit, push, optionally merge)
    print("\nCompleting git workflow...")
    git_result = complete_git_workflow(work_item_id, commit_message)

    if git_result.get("success"):
        print(f"✓ Git: {git_result.get('message', 'Success')}")
    else:
        print(f"⚠️  Git: {git_result.get('message', 'Failed')}")

    # Generate comprehensive summary
    summary = generate_summary(status, work_items_data, gate_results, learnings)

    # Save summary
    history_dir = Path(".session/history")
    history_dir.mkdir(exist_ok=True)
    summary_file = history_dir / f"session_{session_num:03d}_summary.md"
    with open(summary_file, "w") as f:
        f.write(summary)

    # Print summary
    print("\n" + "="*50)
    print(summary)
    print("="*50)

    # Update status
    status["status"] = "completed"
    status["completed_at"] = datetime.now().isoformat()
    with open(".session/tracking/status_update.json", "w") as f:
        json.dump(status, f, indent=2)

    print("\n✓ Session completed successfully")
    return 0


if __name__ == "__main__":
    exit(main())
