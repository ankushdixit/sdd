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
from typing import Dict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts import spec_parser


class SessionValidator:
    """Validate session readiness for completion."""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.session_dir = self.project_root / ".session"

    def check_git_status(self) -> Dict:
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
            tracking_changes = [
                line for line in status_lines if ".session/tracking/" in line
            ]

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

    def preview_quality_gates(self) -> Dict:
        """Preview quality gate results without making changes."""
        gates = {
            "tests": self._preview_tests(),
            "linting": self._preview_linting(),
            "formatting": self._preview_formatting(),
        }

        all_passed = all(g["passed"] for g in gates.values())

        return {
            "passed": all_passed,
            "message": "All quality gates pass"
            if all_passed
            else "Some quality gates fail",
            "gates": gates,
        }

    def _preview_tests(self) -> Dict:
        """Preview test results."""
        try:
            result = subprocess.run(
                ["pytest", "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=300,
            )

            # Parse output for counts
            output = result.stdout + result.stderr

            passed = result.returncode == 0

            return {
                "passed": passed,
                "message": "Tests pass" if passed else "Tests fail",
                "output_preview": output[-500:] if not passed else None,
            }

        except FileNotFoundError:
            return {"passed": True, "message": "pytest not found (skipped)"}
        except subprocess.TimeoutExpired:
            return {"passed": False, "message": "Tests timed out (>5 minutes)"}

    def _preview_linting(self) -> Dict:
        """Preview linting results."""
        try:
            result = subprocess.run(
                ["ruff", "check", "."], capture_output=True, text=True, timeout=60
            )

            passed = result.returncode == 0

            if not passed:
                # Parse issues
                issues = result.stdout.strip().split("\n")
                issue_count = len([i for i in issues if i.strip()])

                return {
                    "passed": False,
                    "message": f"{issue_count} linting issues found",
                    "issues": issues[:10],  # First 10 issues
                    "fixable": "--fix" in result.stderr or "fixable" in result.stdout,
                }

            return {"passed": True, "message": "No linting issues"}

        except FileNotFoundError:
            return {"passed": True, "message": "ruff not found (skipped)"}
        except subprocess.TimeoutExpired:
            return {"passed": False, "message": "Linting timed out"}

    def _preview_formatting(self) -> Dict:
        """Preview formatting check."""
        try:
            result = subprocess.run(
                ["ruff", "format", "--check", "."],
                capture_output=True,
                text=True,
                timeout=60,
            )

            passed = result.returncode == 0

            if not passed:
                unformatted = result.stdout.strip().split("\n")
                file_count = len([f for f in unformatted if f.strip()])

                return {
                    "passed": False,
                    "message": f"{file_count} files need formatting",
                    "files": unformatted[:5],
                }

            return {"passed": True, "message": "All files properly formatted"}

        except FileNotFoundError:
            return {"passed": True, "message": "ruff not found (skipped)"}

    def validate_work_item_criteria(self) -> Dict:
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
        spec_file = self.session_dir / "specs" / f"{work_id}.md"
        if not spec_file.exists():
            return {
                "passed": False,
                "message": f"Spec file missing: {spec_file}",
            }

        # Parse spec file
        try:
            parsed_spec = spec_parser.parse_spec_file(work_id)
        except Exception as e:
            return {
                "passed": False,
                "message": f"Spec file invalid: {str(e)}",
            }

        # Check that spec has required sections based on work item type
        work_type = work_item.get("type")
        missing_sections = []

        # Common sections for all types
        if not parsed_spec.get("acceptance_criteria") or len(parsed_spec.get("acceptance_criteria", [])) < 3:
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
            if not parsed_spec.get("test_scenarios") or len(parsed_spec.get("test_scenarios", [])) == 0:
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

    def check_tracking_updates(self) -> Dict:
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

    def _check_stack_changes(self) -> Dict:
        """Check if stack has changed."""
        # This would run stack detection logic
        # For now, simplified
        return {"has_changes": False, "message": "No stack changes"}

    def _check_tree_changes(self) -> Dict:
        """Check if tree structure has changed."""
        # This would run tree detection logic
        return {"has_changes": False, "message": "No structural changes"}

    def validate(self) -> Dict:
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
            print(
                f"{status} {check_name.replace('_', ' ').title()}: {result['message']}"
            )

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
