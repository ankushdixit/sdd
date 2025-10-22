#!/usr/bin/env python3
"""
Session validation - pre-flight check before completion.

Validates all conditions required for successful /end without
actually making any changes.

Updated in Phase 5.7.3 to use spec_parser for checking work item completeness.
"""

import json
import subprocess
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts import spec_parser
from scripts.quality_gates import QualityGates


class SessionValidator:
    """Validate session readiness for completion."""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.session_dir = self.project_root / ".session"
        self.quality_gates = QualityGates(self.session_dir / "config.json")

    def check_git_status(self) -> dict:
        """Check git working directory status."""
        try:
            # Check if clean or has expected changes
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=5,
            )

            if result.returncode != 0:
                return {"passed": False, "message": "Not a git repository or git error"}

            # Check branch
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=5,
            )
            current_branch = branch_result.stdout.strip()

            # Get status lines
            status_lines = [line for line in result.stdout.split("\n") if line.strip()]

            # Check for tracking file changes
            tracking_changes = [line for line in status_lines if ".session/tracking/" in line]

            if tracking_changes:
                return {
                    "passed": False,
                    "message": f"Uncommitted tracking files: {len(tracking_changes)} files",
                }

            return {
                "passed": True,
                "message": f"Working directory ready, branch: {current_branch}",
                "details": {"branch": current_branch, "changes": len(status_lines)},
            }

        except Exception as e:
            return {"passed": False, "message": f"Git check failed: {e}"}

    def preview_quality_gates(self) -> dict:
        """Preview quality gate results without making changes."""
        gates = {}

        # Use QualityGates to run tests (respects config)
        test_config = self.quality_gates.config.get("test_execution", {})
        if test_config.get("enabled", True):
            test_passed, test_results = self.quality_gates.run_tests()
            # Check if tests are required
            if test_config.get("required", True):
                gates["tests"] = {
                    "passed": test_passed,
                    "message": test_results.get(
                        "reason", "Tests pass" if test_passed else "Tests fail"
                    ),
                }
            else:
                # If not required, always mark as passed but include status info
                gates["tests"] = {
                    "passed": True,
                    "message": f"Tests {test_results.get('status', 'unknown')} (not required)",
                }

        # Use QualityGates for linting (respects config)
        lint_config = self.quality_gates.config.get("linting", {})
        if lint_config.get("enabled", True):
            lint_passed, lint_results = self.quality_gates.run_linting(auto_fix=False)
            if lint_config.get("required", False):
                gates["linting"] = {
                    "passed": lint_passed,
                    "message": "No linting issues" if lint_passed else "Linting issues found",
                }
            else:
                gates["linting"] = {
                    "passed": True,
                    "message": f"Linting {lint_results.get('status', 'unknown')} (not required)",
                }

        # Use QualityGates for formatting (respects config)
        fmt_config = self.quality_gates.config.get("formatting", {})
        if fmt_config.get("enabled", True):
            fmt_passed, fmt_results = self.quality_gates.run_formatting(auto_fix=False)
            if fmt_config.get("required", False):
                gates["formatting"] = {
                    "passed": fmt_passed,
                    "message": "All files properly formatted"
                    if fmt_passed
                    else "Files need formatting",
                }
            else:
                gates["formatting"] = {
                    "passed": True,
                    "message": f"Formatting {fmt_results.get('status', 'unknown')} (not required)",
                }

        all_passed = all(g["passed"] for g in gates.values())

        return {
            "passed": all_passed,
            "message": "All quality gates pass" if all_passed else "Some quality gates fail",
            "gates": gates,
        }

    def validate_work_item_criteria(self) -> dict:
        """
        Check if work item spec is complete and valid.

        Updated in Phase 5.7.3 to check spec file completeness instead of
        deprecated implementation_paths and test_paths fields.
        """
        # Load current work item
        status_file = self.session_dir / "tracking" / "status_update.json"
        if not status_file.exists():
            return {"passed": False, "message": "No active session"}

        with open(status_file) as f:
            status = json.load(f)

        if not status.get("current_work_item"):
            return {"passed": False, "message": "No current work item"}

        # Load work items
        work_items_file = self.session_dir / "tracking" / "work_items.json"
        with open(work_items_file) as f:
            work_items_data = json.load(f)

        work_item = work_items_data["work_items"][status["current_work_item"]]
        work_id = work_item.get("id")

        # Check spec file exists and is valid
        # Use spec_file from work item configuration (supports custom filenames)
        spec_file_path = work_item.get("spec_file", f".session/specs/{work_id}.md")
        spec_file = self.project_root / spec_file_path
        if not spec_file.exists():
            return {
                "passed": False,
                "message": f"Spec file missing: {spec_file}",
            }

        # Parse spec file - pass full work_item dict to support custom spec filenames
        try:
            parsed_spec = spec_parser.parse_spec_file(work_item)
        except Exception as e:
            return {
                "passed": False,
                "message": f"Spec file invalid: {str(e)}",
            }

        # Check that spec has required sections based on work item type
        work_type = work_item.get("type")
        missing_sections = []

        # Common sections for all types
        if (
            not parsed_spec.get("acceptance_criteria")
            or len(parsed_spec.get("acceptance_criteria", [])) < 3
        ):
            missing_sections.append("Acceptance Criteria (at least 3 items)")

        # Type-specific sections
        if work_type == "feature":
            if not parsed_spec.get("overview"):
                missing_sections.append("Overview")
            if not parsed_spec.get("implementation_details"):
                missing_sections.append("Implementation Details")

        elif work_type == "bug":
            if not parsed_spec.get("description"):
                missing_sections.append("Description")
            if not parsed_spec.get("fix_approach"):
                missing_sections.append("Fix Approach")

        elif work_type == "integration_test":
            if not parsed_spec.get("scope"):
                missing_sections.append("Scope")
            if (
                not parsed_spec.get("test_scenarios")
                or len(parsed_spec.get("test_scenarios", [])) == 0
            ):
                missing_sections.append("Test Scenarios (at least 1)")

        elif work_type == "deployment":
            if not parsed_spec.get("deployment_scope"):
                missing_sections.append("Deployment Scope")
            if not parsed_spec.get("deployment_procedure"):
                missing_sections.append("Deployment Procedure")

        if missing_sections:
            return {
                "passed": False,
                "message": "Spec file incomplete",
                "missing_sections": missing_sections,
            }

        return {"passed": True, "message": "Work item spec is complete"}

    def check_tracking_updates(self) -> dict:
        """Preview tracking file updates."""
        changes = {
            "stack": self._check_stack_changes(),
            "tree": self._check_tree_changes(),
        }

        return {
            "passed": True,  # Tracking updates don't fail validation
            "message": "Tracking updates detected"
            if any(c["has_changes"] for c in changes.values())
            else "No tracking updates",
            "changes": changes,
        }

    def _check_stack_changes(self) -> dict:
        """Check if stack has changed."""
        # This would run stack detection logic
        # For now, simplified
        return {"has_changes": False, "message": "No stack changes"}

    def _check_tree_changes(self) -> dict:
        """Check if tree structure has changed."""
        # This would run tree detection logic
        return {"has_changes": False, "message": "No structural changes"}

    def validate(self) -> dict:
        """Run all validation checks."""
        print("Running session validation...\n")

        checks = {
            "git_status": self.check_git_status(),
            "quality_gates": self.preview_quality_gates(),
            "work_item_criteria": self.validate_work_item_criteria(),
            "tracking_updates": self.check_tracking_updates(),
        }

        # Display results
        for check_name, result in checks.items():
            status = "✓" if result["passed"] else "✗"
            print(f"{status} {check_name.replace('_', ' ').title()}: {result['message']}")

            # Show details for failed checks
            if not result["passed"] and check_name == "quality_gates":
                for gate_name, gate_result in result["gates"].items():
                    if not gate_result["passed"]:
                        print(f"   ✗ {gate_name}: {gate_result['message']}")
                        if "issues" in gate_result:
                            for issue in gate_result["issues"][:5]:
                                print(f"      - {issue}")

            # Show missing paths for work item criteria
            if not result["passed"] and check_name == "work_item_criteria":
                if "missing_impl" in result and result["missing_impl"]:
                    print("   Missing implementation paths:")
                    for path in result["missing_impl"]:
                        print(f"      - {path}")
                if "missing_tests" in result and result["missing_tests"]:
                    print("   Missing test paths:")
                    for path in result["missing_tests"]:
                        print(f"      - {path}")

        all_passed = all(c["passed"] for c in checks.values())

        print()
        if all_passed:
            print("✅ Session ready to complete!")
            print("Run /end to complete the session.")
        else:
            print("⚠️  Session not ready to complete")
            print("\nFix the issues above before running /end")

        return {"ready": all_passed, "checks": checks}


def main():
    """CLI entry point."""
    validator = SessionValidator()
    result = validator.validate()
    return 0 if result["ready"] else 1


if __name__ == "__main__":
    exit(main())
