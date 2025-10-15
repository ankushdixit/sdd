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

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from quality_gates import QualityGates


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


def run_quality_gates(work_item=None):
    """
    Run comprehensive quality gates using QualityGates class.
    Returns dict with results from all gates.
    """
    gates = QualityGates()
    all_results = {}
    all_passed = True
    failed_gates = []

    # Run tests
    passed, test_results = gates.run_tests()
    all_results["tests"] = test_results
    if not passed and gates.config.get("test_execution", {}).get("required", True):
        all_passed = False
        failed_gates.append("tests")

    # Run security scanning
    passed, security_results = gates.run_security_scan()
    all_results["security"] = security_results
    if not passed and gates.config.get("security", {}).get("required", True):
        all_passed = False
        failed_gates.append("security")

    # Run linting
    passed, linting_results = gates.run_linting()
    all_results["linting"] = linting_results
    if not passed and gates.config.get("linting", {}).get("required", False):
        all_passed = False
        failed_gates.append("linting")

    # Run formatting
    passed, formatting_results = gates.run_formatting()
    all_results["formatting"] = formatting_results
    if not passed and gates.config.get("formatting", {}).get("required", False):
        all_passed = False
        failed_gates.append("formatting")

    # Validate documentation
    passed, doc_results = gates.validate_documentation(work_item)
    all_results["documentation"] = doc_results
    if not passed and gates.config.get("documentation", {}).get("required", False):
        all_passed = False
        failed_gates.append("documentation")

    # Verify Context7 libraries
    passed, context7_results = gates.verify_context7_libraries()
    all_results["context7"] = context7_results
    if not passed and gates.config.get("context7", {}).get("required", False):
        all_passed = False
        failed_gates.append("context7")

    # Run custom validations
    if work_item:
        passed, custom_results = gates.run_custom_validations(work_item)
        all_results["custom"] = custom_results
        if not passed:
            all_passed = False
            failed_gates.append("custom")

    # Generate and print report
    report = gates.generate_report(all_results)
    print("\n" + report)

    # Print remediation guidance if any gates failed
    if failed_gates:
        guidance = gates.get_remediation_guidance(failed_gates)
        print(guidance)

    return all_results, all_passed, failed_gates


def update_all_tracking(session_num):
    """Update stack, tree, and other tracking files."""
    print("\nUpdating tracking files...")

    # Update stack
    try:
        result = subprocess.run(
            ["python", "scripts/generate_stack.py", "--session", str(session_num)],
            capture_output=True,
            text=True,
            timeout=30,
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
            timeout=30,
        )
        if result.returncode == 0:
            print("✓ Tree updated")
        else:
            print("⚠️  Tree update skipped")
    except Exception as e:
        print(f"⚠️  Tree update failed: {e}")

    return True


def load_curation_config():
    """Load curation configuration from config.json"""
    config_path = Path(".session/config.json")
    if not config_path.exists():
        return {"auto_curate": False, "frequency": 5, "dry_run": False}

    try:
        with open(config_path) as f:
            config = json.load(f)
            return config.get("curation", {})
    except Exception:
        return {"auto_curate": False, "frequency": 5, "dry_run": False}


def trigger_curation_if_needed(session_num):
    """Check if curation should run and trigger it"""
    config = load_curation_config()

    if not config.get("auto_curate", False):
        return

    frequency = config.get("frequency", 5)

    # Run curation every N sessions
    if session_num % frequency == 0:
        print(f"\n{'=' * 50}")
        print(f"Running automatic learning curation (session {session_num})...")
        print(f"{'=' * 50}\n")

        try:
            result = subprocess.run(
                ["python3", "scripts/learning_curator.py", "curate"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                print(result.stdout)
                print("✓ Learning curation completed\n")
            else:
                print("⚠️  Learning curation encountered issues")
                if result.stderr:
                    print(result.stderr)
        except Exception as e:
            print(f"⚠️  Learning curation failed: {e}\n")


def auto_extract_learnings(session_num):
    """Auto-extract learnings from session artifacts"""
    print("\nAuto-extracting learnings from session artifacts...")

    try:
        # Import learning curator
        from learning_curator import LearningsCurator

        curator = LearningsCurator()

        total_extracted = 0

        # Extract from session summary (if it exists)
        summary_file = Path(f".session/history/session_{session_num:03d}_summary.md")
        if summary_file.exists():
            from_summary = curator.extract_from_session_summary(summary_file)
            for learning in from_summary:
                if curator.add_learning_if_new(learning):
                    total_extracted += 1

        # Extract from git commits
        from_commits = curator.extract_from_git_commits()
        for learning in from_commits:
            if curator.add_learning_if_new(learning):
                total_extracted += 1

        # Extract from inline code comments
        from_code = curator.extract_from_code_comments()
        for learning in from_code:
            if curator.add_learning_if_new(learning):
                total_extracted += 1

        if total_extracted > 0:
            print(f"✓ Auto-extracted {total_extracted} new learning(s)\n")
        else:
            print("No new learnings extracted\n")

        return total_extracted

    except Exception as e:
        print(f"⚠️  Auto-extraction failed: {e}\n")
        return 0


def extract_learnings_from_session():
    """Extract learnings from work done in session (manual input)."""
    print("\nCapture additional learnings manually...")
    print("(Type each learning, or 'done' to finish, or 'skip' to skip):")

    learnings = []
    while True:
        learning = input("> ")
        if learning.lower() == "done":
            break
        if learning.lower() == "skip":
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

        spec = importlib.util.spec_from_file_location(
            "git_integration", git_module_path
        )
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
            work_item_id, commit_message, merge=should_merge
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

    summary = f"""# Session {status["current_session"]} Summary

{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Work Items
- **{work_item_id}**: {work_item["title"]} ({work_item["status"]})

## Quality Gates
"""

    # Add results for each gate
    for gate_name, gate_result in gate_results.items():
        status_text = gate_result.get("status", "unknown")
        if status_text == "skipped":
            summary += f"- {gate_name.title()}: ⊘ SKIPPED\n"
        elif status_text == "passed":
            summary += f"- {gate_name.title()}: ✓ PASSED\n"
        else:
            summary += f"- {gate_name.title()}: ✗ FAILED\n"

        # Add coverage for tests
        if gate_name == "tests" and gate_result.get("coverage"):
            summary += f"  - Coverage: {gate_result['coverage']}%\n"

        # Add severity counts for security
        if gate_name == "security" and gate_result.get("by_severity"):
            for severity, count in gate_result["by_severity"].items():
                summary += f"  - {severity}: {count}\n"

    if learnings:
        summary += "\n## Learnings Captured\n"
        for learning in learnings:
            summary += f"- {learning}\n"

    summary += "\n## Next Session\nTo be determined\n"

    # Add integration test summary if applicable
    integration_summary = generate_integration_test_summary(work_item, gate_results)
    if integration_summary:
        summary += integration_summary

    # Add deployment summary if applicable
    deployment_summary = generate_deployment_summary(work_item, gate_results)
    if deployment_summary:
        summary += deployment_summary

    return summary


def generate_integration_test_summary(work_item: dict, gate_results: dict) -> str:
    """
    Generate integration test summary for session completion.

    Args:
        work_item: Integration test work item
        gate_results: Results from quality gates

    Returns:
        Integration test summary section
    """
    if work_item.get("type") != "integration_test":
        return ""

    summary = "\n## Integration Test Results\n\n"

    # Integration test execution results
    integration_results = gate_results.get("integration_tests", {})

    if integration_results:
        test_results = integration_results.get("integration_tests", {})

        if test_results:
            summary += f"**Integration Tests:**\n"
            summary += f"- Passed: {test_results.get('passed', 0)}\n"
            summary += f"- Failed: {test_results.get('failed', 0)}\n"
            summary += f"- Skipped: {test_results.get('skipped', 0)}\n"
            summary += f"- Duration: {test_results.get('total_duration', 0):.2f}s\n\n"

        # Performance benchmarks
        perf_results = integration_results.get("performance_benchmarks", {})
        if perf_results:
            summary += "**Performance Benchmarks:**\n"

            latency = perf_results.get("load_test", {}).get("latency", {})
            if latency:
                summary += f"- p50 latency: {latency.get('p50', 'N/A')}ms\n"
                summary += f"- p95 latency: {latency.get('p95', 'N/A')}ms\n"
                summary += f"- p99 latency: {latency.get('p99', 'N/A')}ms\n"

            throughput = perf_results.get("load_test", {}).get("throughput", {})
            if throughput:
                summary += f"- Throughput: {throughput.get('requests_per_sec', 'N/A')} req/s\n"

            if perf_results.get("regression_detected"):
                summary += "- ⚠️  Performance regression detected!\n"

            summary += "\n"

        # API contracts
        contract_results = integration_results.get("api_contracts", {})
        if contract_results:
            summary += "**API Contract Validation:**\n"
            summary += f"- Contracts validated: {contract_results.get('contracts_validated', 0)}\n"

            breaking_changes = contract_results.get("breaking_changes", [])
            if breaking_changes:
                summary += f"- ⚠️  Breaking changes detected: {len(breaking_changes)}\n"
                for change in breaking_changes[:3]:  # Show first 3
                    summary += f"  - {change.get('message', 'Unknown')}\n"
            else:
                summary += "- ✓ No breaking changes\n"

            summary += "\n"

    return summary


def generate_deployment_summary(work_item: dict, gate_results: dict) -> str:
    """
    Generate deployment-specific summary section.

    Args:
        work_item: Deployment work item
        gate_results: Results from deployment quality gates

    Returns:
        Deployment summary text
    """
    if work_item.get("type") != "deployment":
        return ""

    summary = []
    summary.append("\n" + "=" * 60)
    summary.append("DEPLOYMENT RESULTS")
    summary.append("=" * 60)

    # Deployment execution results
    # TODO: Parse from deployment_executor results
    summary.append("\n**Deployment Execution:**")
    summary.append("  Status: [Success/Failed]")
    summary.append("  Steps completed: [X/Y]")
    summary.append("  Duration: [X minutes]")

    # Smoke test results
    summary.append("\n**Smoke Tests:**")
    summary.append("  Passed: [X]")
    summary.append("  Failed: [Y]")
    summary.append("  Skipped: [Z]")

    # Environment validation
    summary.append("\n**Environment Validation:**")
    for gate in gate_results.get("gates", []):
        if gate.get("name") == "Environment Validation":
            status = "✓ PASSED" if gate.get("passed") else "✗ FAILED"
            summary.append(f"  {status}")

    # Rollback status (if applicable)
    # TODO: Check if rollback was triggered
    rollback_triggered = False
    if rollback_triggered:
        summary.append("\n⚠️  ROLLBACK TRIGGERED")
        summary.append("  Reason: [smoke test failure / error threshold]")
        summary.append("  Rollback status: [Success/Failed]")

    # Post-deployment metrics
    summary.append("\n**Post-Deployment Metrics:**")
    summary.append("  Error rate: [X%]")
    summary.append("  Response time p99: [X ms]")
    summary.append("  Active alerts: [X]")

    summary.append("\n" + "=" * 60)

    return "\n".join(summary)


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
    work_item = work_items_data["work_items"][work_item_id]

    print("Completing session...\n")
    print("Running comprehensive quality gates...\n")

    # Run quality gates with work item context
    gate_results, all_passed, failed_gates = run_quality_gates(work_item)

    if not all_passed:
        print(
            "\n❌ Required quality gates failed. Fix issues before completing session."
        )
        print(f"Failed gates: {', '.join(failed_gates)}")
        return 1

    print("\n✓ All required quality gates PASSED\n")

    # Update all tracking (stack, tree)
    update_all_tracking(session_num)

    # Trigger curation if needed (every N sessions)
    trigger_curation_if_needed(session_num)

    # Auto-extract learnings from session artifacts
    auto_extract_learnings(session_num)

    # Extract learnings manually
    learnings = extract_learnings_from_session()

    # Process learnings with learning_curator if available
    if learnings:
        print("\nProcessing learnings...")
        # Learning curation will be handled by learning_curator.py

    # Ask about work item completion status
    print(
        f"\nIs work item '{work_items_data['work_items'][work_item_id]['title']}' complete? (y/n): "
    )
    is_complete = input("> ").lower() == "y"

    # Update work item status
    if is_complete:
        work_items_data["work_items"][work_item_id]["status"] = "completed"
        if "metadata" not in work_items_data["work_items"][work_item_id]:
            work_items_data["work_items"][work_item_id]["metadata"] = {}
        work_items_data["work_items"][work_item_id]["metadata"]["completed_at"] = (
            datetime.now().isoformat()
        )
    else:
        work_items_data["work_items"][work_item_id]["status"] = "in_progress"

    # Save updated work items
    with open(".session/tracking/work_items.json", "w") as f:
        json.dump(work_items_data, f, indent=2)

    # Generate commit message
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
    print("\n" + "=" * 50)
    print(summary)
    print("=" * 50)

    # Update status
    status["status"] = "completed"
    status["completed_at"] = datetime.now().isoformat()
    with open(".session/tracking/status_update.json", "w") as f:
        json.dump(status, f, indent=2)

    print("\n✓ Session completed successfully")
    return 0


if __name__ == "__main__":
    exit(main())
