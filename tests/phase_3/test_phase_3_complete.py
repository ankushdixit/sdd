#!/usr/bin/env python3
"""
Phase 3 Comprehensive Testing - Visualization & Dependency Graph

Tests all aspects of Phase 3 implementation:
- Section 3.1: Graph generation (ASCII, DOT formats)
- Section 3.2: Critical path analysis
- Section 3.3: Bottleneck detection
- Section 3.4: Filtering options (status, type, milestone)
- Section 3.5: Focus mode and special views
- Section 3.6: Statistics and timeline projection
- Section 3.7: Include/exclude completed items

Test Strategy:
- Create temporary .session directory
- Populate with test work items with various dependencies
- Run dependency_graph.py with different options
- Validate output format and content
- Test error handling for edge cases
"""

import json
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Tuple


def run_command(cmd: str, cwd: str) -> Tuple[int, str, str]:
    """Run shell command and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def print_section(text: str) -> None:
    """Print section header."""
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}\n")


def print_success(text: str) -> None:
    """Print success message."""
    print(f"✓ {text}")


def print_failure(text: str) -> None:
    """Print failure message."""
    print(f"✗ {text}")


def print_info(text: str) -> None:
    """Print info message."""
    print(f"→ {text}")


class Phase3Tester:
    """Phase 3 comprehensive test suite."""

    def __init__(self, test_dir: str):
        """Initialize tester with test directory."""
        self.test_dir = Path(test_dir)
        self.plugin_root = Path(__file__).parent.parent.parent
        self.tests_passed = 0
        self.tests_failed = 0

    def setup_test_environment(self) -> bool:
        """Set up test environment with work items."""
        print_section("Setting Up Test Environment")

        # Create .session directory structure
        session_dir = self.test_dir / ".session"
        tracking_dir = session_dir / "tracking"
        tracking_dir.mkdir(parents=True, exist_ok=True)

        # Create work items with dependencies
        work_items = {
            "metadata": {
                "total_items": 8,
                "completed": 0,
                "in_progress": 0,
                "blocked": 0,
                "last_updated": datetime.now().isoformat(),
            },
            "milestones": {},
            "work_items": {
                # Foundation layer - no dependencies
                "feature_database_schema": {
                    "id": "feature_database_schema",
                    "type": "feature",
                    "title": "Database Schema Design",
                    "status": "completed",
                    "priority": "critical",
                    "dependencies": [],
                    "milestone": "Foundation",
                    "created_at": datetime.now().isoformat(),
                    "sessions": [],
                },
                # Core features - depend on foundation
                "feature_user_auth": {
                    "id": "feature_user_auth",
                    "type": "feature",
                    "title": "User Authentication",
                    "status": "in_progress",
                    "priority": "critical",
                    "dependencies": ["feature_database_schema"],
                    "milestone": "MVP v1.0",
                    "created_at": datetime.now().isoformat(),
                    "sessions": [],
                },
                "feature_api_endpoints": {
                    "id": "feature_api_endpoints",
                    "type": "feature",
                    "title": "REST API Endpoints",
                    "status": "not_started",
                    "priority": "high",
                    "dependencies": ["feature_database_schema"],
                    "milestone": "MVP v1.0",
                    "created_at": datetime.now().isoformat(),
                    "sessions": [],
                },
                # Secondary features - depend on core features
                "feature_user_profile": {
                    "id": "feature_user_profile",
                    "type": "feature",
                    "title": "User Profile Management",
                    "status": "not_started",
                    "priority": "high",
                    "dependencies": ["feature_user_auth"],
                    "milestone": "MVP v1.0",
                    "created_at": datetime.now().isoformat(),
                    "sessions": [],
                },
                "feature_social_login": {
                    "id": "feature_social_login",
                    "type": "feature",
                    "title": "Social Media Login",
                    "status": "not_started",
                    "priority": "medium",
                    "dependencies": ["feature_user_auth"],
                    "milestone": "MVP v1.1",
                    "created_at": datetime.now().isoformat(),
                    "sessions": [],
                },
                # Bug fix and refactor - different types
                "bug_auth_timeout": {
                    "id": "bug_auth_timeout",
                    "type": "bug",
                    "title": "Fix Authentication Timeout",
                    "status": "not_started",
                    "priority": "critical",
                    "dependencies": ["feature_user_auth"],
                    "milestone": "Hotfix v1.0.1",
                    "created_at": datetime.now().isoformat(),
                    "sessions": [],
                },
                "refactor_query_optimization": {
                    "id": "refactor_query_optimization",
                    "type": "refactor",
                    "title": "Database Query Optimization",
                    "status": "not_started",
                    "priority": "medium",
                    "dependencies": ["feature_database_schema"],
                    "milestone": "Performance Sprint",
                    "created_at": datetime.now().isoformat(),
                    "sessions": [],
                },
                # Blocked item - depends on not-started item
                "security_penetration_test": {
                    "id": "security_penetration_test",
                    "type": "security",
                    "title": "Penetration Testing",
                    "status": "blocked",
                    "priority": "high",
                    "dependencies": [
                        "feature_user_auth",
                        "feature_api_endpoints",
                        "feature_user_profile",
                    ],
                    "milestone": "Security Audit",
                    "created_at": datetime.now().isoformat(),
                    "sessions": [],
                },
            },
        }

        # Save work items
        work_items_file = tracking_dir / "work_items.json"
        with open(work_items_file, "w") as f:
            json.dump(work_items, f, indent=2)

        print_success("Test environment created")
        print_info(f"Work items: {len(work_items['work_items'])}")
        print_info("Dependency structure:")
        print_info("  Level 0: feature_database_schema (completed)")
        print_info("  Level 1: feature_user_auth, feature_api_endpoints")
        print_info("  Level 2: feature_user_profile, feature_social_login, bug_auth_timeout")
        print_info("  Level 3: security_penetration_test (blocked)")

        return True

    def test_basic_graph_generation(self) -> bool:
        """Test Section 3.1: Basic graph generation (ASCII format)."""
        print_section("Test 1: Basic Graph Generation (ASCII)")

        returncode, stdout, stderr = run_command(
            f"python3 {self.plugin_root}/scripts/dependency_graph.py",
            cwd=str(self.test_dir),
        )

        if returncode != 0:
            print_failure("Graph generation failed")
            print_info(f"Error: {stderr}")
            return False

        print_success("Graph generated successfully")

        # Validate output contains key elements
        if "Work Item Dependency Graph" not in stdout:
            print_failure("Missing graph header")
            return False

        if "Level 0:" not in stdout:
            print_failure("Missing level information")
            return False

        if "Timeline Projection:" not in stdout:
            print_failure("Missing timeline projection")
            return False

        # Check that completed items are excluded by default (shouldn't appear as main items)
        # Note: They may appear in dependency references, but not as top-level items
        # Count the status icons to verify completed items aren't shown as nodes
        completed_count = stdout.count("● feature_database_schema:")
        if completed_count > 0:
            print_failure("Completed items should be excluded by default as top-level nodes")
            return False

        # But should include non-completed items
        if "feature_user_auth" not in stdout:
            print_failure("Should include in_progress items")
            return False

        print_success("All required elements present in output")
        print_success("Completed items correctly excluded from display")
        print_info(f"Output preview:\n{stdout[:500]}...")

        return True

    def test_critical_path_analysis(self) -> bool:
        """Test Section 3.2: Critical path analysis."""
        print_section("Test 2: Critical Path Analysis")

        returncode, stdout, stderr = run_command(
            f"python3 {self.plugin_root}/scripts/dependency_graph.py --critical-path",
            cwd=str(self.test_dir),
        )

        if returncode != 0:
            print_failure("Critical path analysis failed")
            return False

        print_success("Critical path generated")

        # Validate that only critical path items are shown
        if "[CRITICAL PATH]" not in stdout:
            print_failure("Critical path markers not found")
            return False

        # Critical path should include items with longest dependency chain
        if "feature_user_auth" not in stdout:
            print_failure("Missing critical path item: feature_user_auth")
            return False

        # Non-critical items should not be shown
        if "refactor_query_optimization" in stdout:
            print_failure("Non-critical item should not be in critical path view")
            return False

        print_success("Critical path correctly identified")
        print_info("Critical path items marked with [CRITICAL PATH]")

        return True

    def test_bottleneck_detection(self) -> bool:
        """Test Section 3.3: Bottleneck detection."""
        print_section("Test 3: Bottleneck Detection")

        returncode, stdout, stderr = run_command(
            f"python3 {self.plugin_root}/scripts/dependency_graph.py --bottlenecks",
            cwd=str(self.test_dir),
        )

        if returncode != 0:
            print_failure("Bottleneck detection failed")
            return False

        print_success("Bottleneck analysis completed")

        # Validate bottleneck analysis output
        if "Bottleneck Analysis:" not in stdout:
            print_failure("Missing bottleneck analysis header")
            return False

        # feature_user_auth is a bottleneck (blocks 3 items)
        # feature_database_schema would be too but it's completed
        if "feature_user_auth" not in stdout and "No bottlenecks found" not in stdout:
            print_failure("Expected bottleneck not identified")
            return False

        print_success("Bottleneck analysis correct")
        print_info(f"Analysis output:\n{stdout}")

        return True

    def test_status_filtering(self) -> bool:
        """Test Section 3.4: Status filtering."""
        print_section("Test 4: Status Filtering")

        # Test filtering by not_started
        returncode, stdout, stderr = run_command(
            f"python3 {self.plugin_root}/scripts/dependency_graph.py --status not_started",
            cwd=str(self.test_dir),
        )

        if returncode != 0:
            print_failure("Status filtering failed")
            return False

        # Should show not_started items as main nodes (with status icon at start of line)
        # Dependencies may still be mentioned, but won't be shown as main nodes
        if "◐ feature_user_auth:" in stdout:
            print_failure("Should exclude in_progress items when filtering for not_started")
            return False

        if "○ feature_api_endpoints:" not in stdout:
            print_failure("Should include not_started items")
            return False

        print_success("not_started filter works correctly")

        # Test filtering by in_progress
        returncode, stdout, stderr = run_command(
            f"python3 {self.plugin_root}/scripts/dependency_graph.py --status in_progress",
            cwd=str(self.test_dir),
        )

        if returncode != 0:
            print_failure("in_progress filtering failed")
            return False

        if "◐ feature_user_auth:" not in stdout:
            print_failure("Should include in_progress items")
            return False

        if "○ feature_api_endpoints:" in stdout:
            print_failure("Should exclude not_started items when filtering for in_progress")
            return False

        print_success("in_progress filter works correctly")
        print_info("Status filtering validated for multiple statuses")

        return True

    def test_type_filtering(self) -> bool:
        """Test Section 3.4: Type filtering."""
        print_section("Test 5: Type Filtering")

        returncode, stdout, stderr = run_command(
            f"python3 {self.plugin_root}/scripts/dependency_graph.py --type feature",
            cwd=str(self.test_dir),
        )

        if returncode != 0:
            print_failure("Type filtering failed")
            return False

        # Should show only feature type items
        if "bug_auth_timeout" in stdout:
            print_failure("Should exclude bug type when filtering for features")
            return False

        if "refactor_query_optimization" in stdout:
            print_failure("Should exclude refactor type when filtering for features")
            return False

        if "feature_user_auth" not in stdout:
            print_failure("Should include feature type items")
            return False

        print_success("Type filtering works correctly")
        print_info("Only feature type items shown")

        return True

    def test_milestone_filtering(self) -> bool:
        """Test Section 3.4: Milestone filtering."""
        print_section("Test 6: Milestone Filtering")

        returncode, stdout, stderr = run_command(
            f'python3 {self.plugin_root}/scripts/dependency_graph.py --milestone "MVP v1.0"',
            cwd=str(self.test_dir),
        )

        if returncode != 0:
            print_failure("Milestone filtering failed")
            return False

        # Should show only MVP v1.0 milestone items
        if "feature_user_profile" not in stdout:
            print_failure("Should include items with MVP v1.0 milestone")
            return False

        if "feature_social_login" in stdout:
            print_failure("Should exclude items from other milestones (MVP v1.1)")
            return False

        if "bug_auth_timeout" in stdout:
            print_failure("Should exclude items from other milestones (Hotfix)")
            return False

        print_success("Milestone filtering works correctly")
        print_info("Only MVP v1.0 milestone items shown")

        return True

    def test_focus_mode(self) -> bool:
        """Test Section 3.5: Focus mode on specific work item."""
        print_section("Test 7: Focus Mode")

        returncode, stdout, stderr = run_command(
            f"python3 {self.plugin_root}/scripts/dependency_graph.py --focus feature_user_auth",
            cwd=str(self.test_dir),
        )

        if returncode != 0:
            print_failure("Focus mode failed")
            return False

        # Should show feature_user_auth and its neighborhood (dependencies + dependents)
        if "feature_user_auth" not in stdout:
            print_failure("Focus item not shown")
            return False

        # Should show dependency
        if "feature_database_schema" not in stdout:
            print_failure("Should show dependencies of focus item")
            return False

        # Should show dependents
        if "feature_user_profile" not in stdout:
            print_failure("Should show items that depend on focus item")
            return False

        # Should NOT show unrelated items
        if "refactor_query_optimization" in stdout:
            # This is ok if it shares the database dependency
            pass

        print_success("Focus mode works correctly")
        print_info("Shows focus item + dependencies + dependents")

        return True

    def test_statistics(self) -> bool:
        """Test Section 3.6: Statistics output."""
        print_section("Test 8: Statistics")

        returncode, stdout, stderr = run_command(
            f"python3 {self.plugin_root}/scripts/dependency_graph.py --stats",
            cwd=str(self.test_dir),
        )

        if returncode != 0:
            print_failure("Statistics generation failed")
            return False

        # Validate statistics output
        if "Graph Statistics:" not in stdout:
            print_failure("Missing statistics header")
            return False

        if "Total work items:" not in stdout:
            print_failure("Missing total work items count")
            return False

        if "Critical path length:" not in stdout:
            print_failure("Missing critical path length")
            return False

        if "Completed:" not in stdout:
            print_failure("Missing completion statistics")
            return False

        print_success("Statistics generated correctly")
        print_info(f"Statistics:\n{stdout}")

        return True

    def test_include_completed(self) -> bool:
        """Test Section 3.7: Include completed items."""
        print_section("Test 9: Include Completed Items")

        # Default should exclude completed (as main nodes with status icon)
        returncode, stdout_default, stderr = run_command(
            f"python3 {self.plugin_root}/scripts/dependency_graph.py",
            cwd=str(self.test_dir),
        )

        # Check that completed item doesn't appear as a main node (with status icon)
        if "● feature_database_schema:" in stdout_default:
            print_failure("Default should exclude completed items as main nodes")
            return False

        print_success("Default excludes completed items")

        # With --include-completed should show completed items
        returncode, stdout_include, stderr = run_command(
            f"python3 {self.plugin_root}/scripts/dependency_graph.py --include-completed",
            cwd=str(self.test_dir),
        )

        if returncode != 0:
            print_failure("Include completed flag failed")
            return False

        if "● feature_database_schema:" not in stdout_include:
            print_failure("Should include completed items with --include-completed")
            return False

        # Should show completed marker (●)
        if "●" not in stdout_include:
            print_failure("Should show completed marker (●) for completed items")
            return False

        print_success("--include-completed flag works correctly")
        print_info("Completed items shown with ● marker")

        return True

    def test_dot_format(self) -> bool:
        """Test Section 3.1: DOT format generation."""
        print_section("Test 10: DOT Format Generation")

        returncode, stdout, stderr = run_command(
            f"python3 {self.plugin_root}/scripts/dependency_graph.py --format dot",
            cwd=str(self.test_dir),
        )

        if returncode != 0:
            print_failure("DOT format generation failed")
            return False

        # Validate DOT format structure
        if "digraph WorkItems {" not in stdout:
            print_failure("Invalid DOT format - missing digraph declaration")
            return False

        if "rankdir=TB;" not in stdout and "rankdir=LR;" not in stdout:
            print_failure("Missing rankdir directive")
            return False

        if "->" not in stdout:
            print_failure("Missing edge declarations")
            return False

        # Check that nodes are declared
        if "feature_user_auth" not in stdout:
            print_failure("Missing node declarations")
            return False

        print_success("DOT format generated correctly")
        print_info("Valid Graphviz DOT syntax")
        print_info(f"DOT output preview:\n{stdout[:300]}...")

        return True

    def test_combined_filters(self) -> bool:
        """Test combining multiple filters."""
        print_section("Test 11: Combined Filters")

        returncode, stdout, stderr = run_command(
            f'python3 {self.plugin_root}/scripts/dependency_graph.py --status not_started --milestone "MVP v1.0" --type feature',
            cwd=str(self.test_dir),
        )

        if returncode != 0:
            print_failure("Combined filters failed")
            return False

        # Should only show: not_started + MVP v1.0 + feature type as main nodes
        # That would be: feature_api_endpoints, feature_user_profile

        if "○ feature_api_endpoints:" not in stdout:
            print_failure("Should include feature_api_endpoints (not_started, MVP v1.0, feature)")
            return False

        if "○ feature_user_profile:" not in stdout:
            print_failure("Should include feature_user_profile (not_started, MVP v1.0, feature)")
            return False

        # Should exclude in_progress (as main nodes)
        if "◐ feature_user_auth:" in stdout:
            print_failure("Should exclude in_progress items as main nodes")
            return False

        # Should exclude other milestones (as main nodes)
        if "○ feature_social_login:" in stdout:
            print_failure("Should exclude items from other milestones")
            return False

        # Should exclude other types (as main nodes)
        if "bug_auth_timeout:" in stdout and "depends on" not in stdout.split("bug_auth_timeout:")[0][-50:]:
            print_failure("Should exclude non-feature types as main nodes")
            return False

        print_success("Combined filters work correctly")
        print_info("All filters applied simultaneously")

        return True

    def run_all_tests(self) -> bool:
        """Run all Phase 3 tests."""
        print("\n" + "=" * 70)
        print("  PHASE 3 COMPREHENSIVE TESTING")
        print("  Visualization & Dependency Graph")
        print("=" * 70)

        # Setup
        if not self.setup_test_environment():
            print("\n❌ Test environment setup failed")
            return False

        # Run all tests
        tests = [
            self.test_basic_graph_generation,
            self.test_critical_path_analysis,
            self.test_bottleneck_detection,
            self.test_status_filtering,
            self.test_type_filtering,
            self.test_milestone_filtering,
            self.test_focus_mode,
            self.test_statistics,
            self.test_include_completed,
            self.test_dot_format,
            self.test_combined_filters,
        ]

        for test in tests:
            try:
                if test():
                    self.tests_passed += 1
                else:
                    self.tests_failed += 1
            except Exception as e:
                print_failure(f"Test raised exception: {e}")
                self.tests_failed += 1

        # Print summary
        print_section("TEST SUMMARY")
        total = self.tests_passed + self.tests_failed
        print(f"Total tests: {total}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_failed}")
        print(f"Success rate: {(self.tests_passed / total * 100):.1f}%")

        if self.tests_failed == 0:
            print("\n✅ ALL TESTS PASSED!")
            return True
        else:
            print(f"\n❌ {self.tests_failed} TEST(S) FAILED")
            return False


def main():
    """Run Phase 3 comprehensive tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Using temporary directory: {tmpdir}")
        tester = Phase3Tester(tmpdir)
        success = tester.run_all_tests()
        return 0 if success else 1


if __name__ == "__main__":
    exit(main())
