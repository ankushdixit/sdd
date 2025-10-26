#!/usr/bin/env python3
"""
Complete current session with quality gates and summary generation.
Enhanced with full tracking updates and git workflow.

Updated in Phase 5.7.3 to use spec_parser for reading work item rationale.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Add scripts directory to path for imports
from sdd.quality.gates import QualityGates
from sdd.work_items.spec_parser import parse_spec_file


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
    if not passed and gates.config.get("linting", {}).get("required", True):
        all_passed = False
        failed_gates.append("linting")

    # Run formatting
    passed, formatting_results = gates.run_formatting()
    all_results["formatting"] = formatting_results
    if not passed and gates.config.get("formatting", {}).get("required", True):
        all_passed = False
        failed_gates.append("formatting")

    # Validate documentation
    passed, doc_results = gates.validate_documentation(work_item)
    all_results["documentation"] = doc_results
    if not passed and gates.config.get("documentation", {}).get("required", True):
        all_passed = False
        failed_gates.append("documentation")

    # Verify Context7 libraries
    passed, context7_results = gates.verify_context7_libraries()
    all_results["context7"] = context7_results
    if not passed and gates.config.get("context7", {}).get("required", True):
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

    # Get SDD installation directory for absolute path resolution
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent / "project"

    # Update stack
    try:
        result = subprocess.run(
            [
                "python",
                str(project_dir / "stack.py"),
                "--session",
                str(session_num),
                "--non-interactive",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            print("✓ Stack updated")
            # Print output if there were changes
            if result.stdout.strip():
                for line in result.stdout.strip().split("\n"):
                    if line.strip():
                        print(f"  {line}")
        else:
            print(f"⚠️  Stack update failed (exit code {result.returncode})")
            if result.stderr:
                print(f"  Error: {result.stderr}")
    except Exception as e:
        print(f"⚠️  Stack update failed: {e}")

    # Update tree
    try:
        result = subprocess.run(
            [
                "python",
                str(project_dir / "tree.py"),
                "--session",
                str(session_num),
                "--non-interactive",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            print("✓ Tree updated")
            # Print output if there were changes
            if result.stdout.strip():
                for line in result.stdout.strip().split("\n"):
                    if line.strip():
                        print(f"  {line}")
        else:
            print(f"⚠️  Tree update failed (exit code {result.returncode})")
            if result.stderr:
                print(f"  Error: {result.stderr}")
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
        from sdd.learning.curator import LearningsCurator

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


def extract_learnings_from_session(learnings_file=None):
    """Extract learnings from work done in session (manual input or file).

    Args:
        learnings_file: Path to file containing learnings (one per line)
    """
    # If learnings file provided, read from it
    if learnings_file:
        try:
            learnings_path = Path(learnings_file)
            if learnings_path.exists():
                print(f"\nReading learnings from {learnings_file}...")
                with open(learnings_path) as f:
                    learnings = [line.strip() for line in f if line.strip()]
                print(f"✓ Loaded {len(learnings)} learnings from file")
                # Clean up temp file
                learnings_path.unlink()
                return learnings
            else:
                print(f"⚠️  Learnings file not found: {learnings_file}")
        except Exception as e:
            print(f"⚠️  Failed to read learnings file: {e}")

    # Skip manual input in non-interactive mode (e.g., when run by Claude Code)
    if not sys.stdin.isatty():
        print("\nSkipping manual learning extraction (non-interactive mode)")
        return []

    print("\nCapture additional learnings manually...")
    print("(Type each learning, or 'done' to finish, or 'skip' to skip):")

    learnings = []
    while True:
        try:
            learning = input("> ")
            if learning.lower() == "done":
                break
            if learning.lower() == "skip":
                return []
            if learning:
                learnings.append(learning)
        except EOFError:
            # Handle EOF gracefully in case stdin is closed
            break

    return learnings


def complete_git_workflow(work_item_id, commit_message, session_num):
    """Complete git workflow (commit, push, optionally merge or create PR)."""
    try:
        # Import git workflow from new location
        from sdd.git.integration import GitWorkflow

        workflow = GitWorkflow()

        # Load work items to check status
        with open(".session/tracking/work_items.json") as f:
            data = json.load(f)

        work_item = data["work_items"][work_item_id]
        should_merge = work_item["status"] == "completed"

        # Complete work item in git (with session_num for PR creation)
        result = workflow.complete_work_item(
            work_item_id, commit_message, merge=should_merge, session_num=session_num
        )

        return result
    except Exception as e:
        return {"success": False, "message": f"Git workflow error: {e}"}


def record_session_commits(work_item_id):
    """Record commits made during session to work item tracking (Bug #15 fix)."""
    try:
        work_items_file = Path(".session/tracking/work_items.json")
        with open(work_items_file) as f:
            data = json.load(f)

        work_item = data["work_items"][work_item_id]
        git_info = work_item.get("git", {})

        # Get branch information
        branch_name = git_info.get("branch")
        parent_branch = git_info.get("parent_branch", "main")

        if not branch_name:
            # No git branch tracking for this work item
            return

        # Get commits on session branch that aren't in parent branch
        result = subprocess.run(
            ["git", "log", "--pretty=format:%H|%s|%ai", f"{parent_branch}..{branch_name}"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            # Branch might not exist or other git error - skip silently
            return

        commits = []
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split("|", 2)
                if len(parts) == 3:
                    sha, message, timestamp = parts
                    commits.append({"sha": sha, "message": message, "timestamp": timestamp})

        # Update work_items.json with commits
        if commits:
            data["work_items"][work_item_id]["git"]["commits"] = commits
            with open(work_items_file, "w") as f:
                json.dump(data, f, indent=2)

    except Exception:
        # Silently skip if there's any error - this is non-critical tracking
        pass


def generate_commit_message(status, work_item):
    """
    Generate standardized commit message.

    Updated in Phase 5.7.3 to read rationale from spec file instead of
    deprecated JSON field.
    """
    session_num = status["current_session"]
    work_type = work_item["type"]
    title = work_item["title"]

    message = f"Session {session_num:03d}: {work_type.title()} - {title}\n\n"

    # Get rationale from spec file
    try:
        parsed_spec = parse_spec_file(work_item)
        rationale = parsed_spec.get("rationale")

        if rationale and rationale.strip():
            # Trim to first paragraph if too long
            first_para = rationale.split("\n\n")[0]
            if len(first_para) > 200:
                first_para = first_para[:197] + "..."
            message += f"{first_para}\n\n"
    except Exception:
        # If spec file not found or invalid, continue without rationale
        pass

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

"""

    # Add commit details with file stats (Enhancement #11 Phase 1)
    commits = work_item.get("git", {}).get("commits", [])
    if commits:
        summary += "## Commits Made\n\n"
        for commit in commits:
            # Show short SHA and first line of commit message
            message_lines = commit["message"].split("\n")
            first_line = message_lines[0] if message_lines else ""
            summary += f"**{commit['sha'][:7]}** - {first_line}\n"

            # Show full message if multi-line
            if len(message_lines) > 1:
                remaining_lines = "\n".join(message_lines[1:]).strip()
                if remaining_lines:
                    summary += "\n```\n"
                    summary += remaining_lines
                    summary += "\n```\n\n"

            # Get file stats using git diff
            try:
                result = subprocess.run(
                    ["git", "diff", "--stat", f"{commit['sha']}^..{commit['sha']}"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0 and result.stdout.strip():
                    summary += "\nFiles changed:\n```\n"
                    summary += result.stdout
                    summary += "```\n\n"
            except Exception:
                # Silently skip if git diff fails
                pass

        summary += "\n"

    summary += "## Quality Gates\n"

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
            summary += "**Integration Tests:**\n"
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
    # NOTE: Framework stub - Parse actual results from deployment_executor
    # When implemented, extract from DeploymentExecutor.get_deployment_log()
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
    # NOTE: Framework stub - Check deployment results for rollback trigger
    # When implemented, check DeploymentExecutor results for rollback_triggered flag
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


def check_uncommitted_changes() -> bool:
    """Check for uncommitted changes and guide user to commit first."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )

        uncommitted = [line for line in result.stdout.split("\n") if line.strip()]

        # Filter out .session/tracking files (they're updated by sdd end)
        user_changes = [
            line
            for line in uncommitted
            if ".session/tracking/" not in line and ".session/briefings/" not in line
        ]

        if not user_changes:
            return True  # All good

        # Display uncommitted changes
        print("\n" + "=" * 60)
        print("⚠️  UNCOMMITTED CHANGES DETECTED")
        print("=" * 60)
        print("\nYou have uncommitted changes:")
        print()

        for line in user_changes[:15]:  # Show first 15
            print(f"   {line}")

        if len(user_changes) > 15:
            print(f"   ... and {len(user_changes) - 15} more")

        print("\n" + "=" * 60)
        print("📋 REQUIRED STEPS BEFORE /sdd:end:")
        print("=" * 60)
        print()
        print("1. Review your changes:")
        print("   git status")
        print()
        print("2. Update CHANGELOG.md with session changes:")
        print("   ## [Unreleased]")
        print("   ### Added")
        print("   - Your feature or change")
        print()
        print("3. Commit everything:")
        print("   git add -A")
        print("   git commit -m 'Implement feature X")
        print()
        print("   LEARNING: Key insight from implementation")
        print()
        print("   🤖 Generated with [Claude Code](https://claude.com/claude-code)")
        print("   Co-Authored-By: Claude <noreply@anthropic.com>'")
        print()
        print("4. Then run:")
        print("   sdd end")
        print()
        print("=" * 60)

        # In interactive mode, allow override
        if sys.stdin.isatty():
            print()
            response = input("Continue anyway? (y/n): ")
            return response.lower() == "y"
        else:
            print("\nNon-interactive mode: exiting")
            print("Please commit your changes and run 'sdd end' again.")
            return False

    except Exception as e:
        print(f"Warning: Could not check git status: {e}")
        return True  # Don't block on errors


def prompt_work_item_completion(work_item_title: str, non_interactive: bool = False) -> bool | None:
    """
    Prompt user to mark work item as complete or in-progress.

    Args:
        work_item_title: Title of the work item to display in prompt
        non_interactive: If True, skip interactive prompt (defaults to incomplete for safety)

    Returns:
        True if work item should be marked complete
        False if work item should remain in-progress
        None if user cancelled (should abort session end)
    """
    if non_interactive:
        # In non-interactive mode, default to incomplete for safety
        return False

    print(f'\nWork item: "{work_item_title}"\n')
    print("Is this work item complete?")
    print("1. Yes - Mark as completed")
    print("2. No - Keep as in-progress (will resume in next session)")
    print("3. Cancel - Don't end session")
    print()

    while True:
        choice = input("Choice [1]: ").strip() or "1"

        if choice == "1":
            return True  # Mark complete
        elif choice == "2":
            return False  # Keep in-progress
        elif choice == "3":
            print("\nSession end cancelled")
            return None  # Cancel operation
        else:
            print("Invalid choice. Enter 1, 2, or 3.")


def main():
    """Enhanced main entry point with full tracking updates."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Complete SDD session")
    parser.add_argument(
        "--learnings-file",
        type=str,
        help="Path to file containing learnings (one per line)",
    )
    parser.add_argument(
        "--complete",
        action="store_true",
        help="Mark work item as complete",
    )
    parser.add_argument(
        "--incomplete",
        action="store_true",
        help="Keep work item as in-progress",
    )
    args = parser.parse_args()

    # Load current status
    status = load_status()
    if not status:
        print("Error: No active session found")
        return 1

    work_items_data = load_work_items()
    work_item_id = status["current_work_item"]
    session_num = status["current_session"]
    work_item = work_items_data["work_items"][work_item_id]

    # Pre-flight check - ensure changes are committed
    if not check_uncommitted_changes():
        print("\n❌ Session completion aborted")
        print("Commit your changes and try again.\n")
        return 1

    print("Completing session...\n")
    print("Running comprehensive quality gates...\n")

    # Run quality gates with work item context
    gate_results, all_passed, failed_gates = run_quality_gates(work_item)

    if not all_passed:
        print("\n❌ Required quality gates failed. Fix issues before completing session.")
        print(f"Failed gates: {', '.join(failed_gates)}")
        return 1

    print("\n✓ All required quality gates PASSED\n")

    # Update all tracking (stack, tree)
    update_all_tracking(session_num)

    # Trigger curation if needed (every N sessions)
    trigger_curation_if_needed(session_num)

    # Extract learnings manually or from file
    learnings = extract_learnings_from_session(args.learnings_file)

    # Process learnings with learning_curator if available
    if learnings:
        print(f"\nProcessing {len(learnings)} learnings...")
        try:
            from sdd.learning.curator import LearningsCurator

            curator = LearningsCurator()
            added_count = 0
            for learning in learnings:
                # Use standardized entry creator for consistent metadata structure
                # This ensures both 'learned_in' and 'context' fields are present
                source_type = "temp_file" if args.learnings_file else "manual"
                context = (
                    f"Temp file: {args.learnings_file}" if args.learnings_file else "Manual entry"
                )

                learning_dict = curator.create_learning_entry(
                    content=learning,
                    source=source_type,
                    session_id=f"session_{session_num:03d}",
                    context=context,
                )

                if curator.add_learning_if_new(learning_dict):
                    added_count += 1
                    print(f"  ✓ Added: {learning}")
                else:
                    print(f"  ⊘ Duplicate: {learning}")

            if added_count > 0:
                print(f"\n✓ Added {added_count} new learning(s) to learnings.json")
            else:
                print("\n⊘ No new learnings added (all were duplicates)")
        except Exception as e:
            print(f"⚠️  Failed to process learnings: {e}")

    # Determine work item completion status
    work_item_title = work_items_data["work_items"][work_item_id]["title"]

    if args.complete:
        print(f"\n✓ Marking work item '{work_item_title}' as complete (--complete flag)")
        is_complete = True
    elif args.incomplete:
        print(f"\n✓ Keeping work item '{work_item_title}' as in-progress (--incomplete flag)")
        is_complete = False
    else:
        # Determine if non-interactive
        non_interactive = not sys.stdin.isatty()

        # Use new prompt function
        completion_result = prompt_work_item_completion(work_item_title, non_interactive)

        if completion_result is None:
            # User cancelled - abort session end
            print("\n❌ Session completion aborted by user")
            return 1

        is_complete = completion_result

        # Print completion decision message (for interactive mode)
        if is_complete:
            print(f"\n✓ Marking work item '{work_item_title}' as complete")
        else:
            print(
                f"\n✓ Keeping work item '{work_item_title}' as in-progress (will resume in next session)"
            )

    # Track changes for update_history
    changes = []
    previous_status = work_items_data["work_items"][work_item_id]["status"]

    # Update work item status
    if is_complete:
        new_status = "completed"
        work_items_data["work_items"][work_item_id]["status"] = new_status
        if "metadata" not in work_items_data["work_items"][work_item_id]:
            work_items_data["work_items"][work_item_id]["metadata"] = {}
        work_items_data["work_items"][work_item_id]["metadata"]["completed_at"] = (
            datetime.now().isoformat()
        )

        # Record changes
        if previous_status != new_status:
            changes.append(f"  status: {previous_status} → {new_status}")
        changes.append(f"  metadata.completed_at: {datetime.now().isoformat()}")
    else:
        new_status = "in_progress"
        work_items_data["work_items"][work_item_id]["status"] = new_status

        # Record changes
        if previous_status != new_status:
            changes.append(f"  status: {previous_status} → {new_status}")

    # Add update_history entry if changes were made
    if changes:
        if "update_history" not in work_items_data["work_items"][work_item_id]:
            work_items_data["work_items"][work_item_id]["update_history"] = []

        work_items_data["work_items"][work_item_id]["update_history"].append(
            {"timestamp": datetime.now().isoformat(), "changes": changes}
        )

    # Update metadata counters
    work_items = work_items_data.get("work_items", {})
    work_items_data["metadata"]["total_items"] = len(work_items)
    work_items_data["metadata"]["completed"] = sum(
        1 for item in work_items.values() if item["status"] == "completed"
    )
    work_items_data["metadata"]["in_progress"] = sum(
        1 for item in work_items.values() if item["status"] == "in_progress"
    )
    work_items_data["metadata"]["blocked"] = sum(
        1 for item in work_items.values() if item["status"] == "blocked"
    )
    work_items_data["metadata"]["last_updated"] = datetime.now().isoformat()

    # Save updated work items
    with open(".session/tracking/work_items.json", "w") as f:
        json.dump(work_items_data, f, indent=2)

    # Generate commit message
    commit_message = generate_commit_message(status, work_item)

    # Complete git workflow (commit, push, optionally merge or create PR)
    print("\nCompleting git workflow...")
    git_result = complete_git_workflow(work_item_id, commit_message, session_num)

    if git_result.get("success"):
        print(f"✓ Git: {git_result.get('message', 'Success')}")
    else:
        print(f"⚠️  Git: {git_result.get('message', 'Failed')}")

    # Record commits to work item tracking (Bug #15 fix)
    record_session_commits(work_item_id)

    # Generate comprehensive summary
    summary = generate_summary(status, work_items_data, gate_results, learnings)

    # Save summary
    history_dir = Path(".session/history")
    history_dir.mkdir(exist_ok=True)
    summary_file = history_dir / f"session_{session_num:03d}_summary.md"
    with open(summary_file, "w") as f:
        f.write(summary)

    # Auto-extract learnings from session artifacts (Bug #16 fix)
    # Now that commit and summary are created, we can extract from them
    auto_extract_learnings(session_num)

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
