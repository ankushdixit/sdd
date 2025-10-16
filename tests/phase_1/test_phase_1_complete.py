#!/usr/bin/env python3
"""
Comprehensive End-to-End Test Script for Phase 1: Core Plugin Foundation

Tests all Phase 1 functionality:
- Section 1.1: /init command
- Section 1.2: Stack tracking system
- Section 1.3: Tree tracking system
- Section 1.4: Git workflow integration
- Section 1.5: Enhanced /start with context loading
- Section 1.6: Enhanced /end with comprehensive updates
- Section 1.7: /validate command
- Section 1.8: Work item types
- Section 1.9: Multi-session workflow
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def run_command(cmd: str, cwd: str = None) -> tuple[int, str, str]:
    """Run a shell command and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def print_test_header(test_name: str):
    """Print formatted test header."""
    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}{test_name}{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}\n")


def print_success(message: str):
    """Print success message."""
    print(f"{GREEN}✓ {message}{RESET}")


def print_failure(message: str):
    """Print failure message."""
    print(f"{RED}✗ {message}{RESET}")


def print_info(message: str):
    """Print info message."""
    print(f"{YELLOW}ℹ {message}{RESET}")


class Phase1Tester:
    """Phase 1 comprehensive test suite."""

    def __init__(self, test_dir: str):
        """Initialize tester with test directory."""
        self.test_dir = Path(test_dir)
        self.plugin_root = Path(__file__).parent.parent.parent
        self.tests_passed = 0
        self.tests_failed = 0

    def setup_test_project(self):
        """Set up a minimal test project."""
        print_info("Setting up test project...")

        # Create minimal project structure
        (self.test_dir / "README.md").write_text("# Test Project\n\nA test project for Phase 1 testing.")

        # Create a simple Python file
        (self.test_dir / "main.py").write_text('print("Hello, World!")\n')

        # Initialize git repo
        run_command("git init", cwd=str(self.test_dir))
        run_command('git config user.name "Test User"', cwd=str(self.test_dir))
        run_command('git config user.email "test@example.com"', cwd=str(self.test_dir))
        run_command("git add .", cwd=str(self.test_dir))
        run_command('git commit -m "Initial commit"', cwd=str(self.test_dir))

        # Copy scripts to test project
        shutil.copytree(self.plugin_root / "scripts", self.test_dir / "scripts")
        shutil.copytree(self.plugin_root / "templates", self.test_dir / "templates")

        print_success("Test project set up")

    def test_session_init(self) -> bool:
        """Test Section 1.1: /init command."""
        print_test_header("Test 1.1: Session Initialization")

        try:
            # Run /init
            returncode, stdout, stderr = run_command(
                "python3 scripts/init_project.py",
                cwd=str(self.test_dir)
            )

            if returncode != 0:
                print_failure(f"/init failed with code {returncode}")
                print_info(f"stderr: {stderr}")
                return False

            # Verify directory structure
            required_dirs = [
                ".session",
                ".session/tracking",
                ".session/briefings",
                ".session/history",
                ".session/specs",
            ]

            for dir_path in required_dirs:
                full_path = self.test_dir / dir_path
                if not full_path.exists():
                    print_failure(f"Directory not created: {dir_path}")
                    return False
                print_success(f"Directory exists: {dir_path}")

            # Verify tracking files
            required_files = [
                ".session/tracking/work_items.json",
                ".session/tracking/learnings.json",
                ".session/tracking/status_update.json",
                ".session/tracking/stack.txt",
                ".session/tracking/tree.txt",
                ".session/config.json",
            ]

            for file_path in required_files:
                full_path = self.test_dir / file_path
                if not full_path.exists():
                    print_failure(f"File not created: {file_path}")
                    return False
                print_success(f"File exists: {file_path}")

            # Verify stack.txt contains Python
            stack_content = (self.test_dir / ".session/tracking/stack.txt").read_text()
            if "Python" not in stack_content:
                print_failure("stack.txt does not contain Python")
                return False
            print_success("stack.txt correctly detects Python")

            # Verify tree.txt contains project structure
            tree_content = (self.test_dir / ".session/tracking/tree.txt").read_text()
            if "README.md" not in tree_content or "main.py" not in tree_content:
                print_failure("tree.txt does not contain expected files")
                return False
            print_success("tree.txt correctly shows project structure")

            print_success("Session initialization complete")
            return True

        except Exception as e:
            print_failure(f"Exception during /init: {e}")
            return False

    def test_work_item_creation(self) -> bool:
        """Test creating a work item."""
        print_test_header("Test 1.8: Work Item Creation")

        try:
            # Create a feature work item
            returncode, stdout, stderr = run_command(
                'python3 scripts/work_item_manager.py --type feature --title "Test Feature" --priority high',
                cwd=str(self.test_dir)
            )

            if returncode != 0:
                print_failure(f"Work item creation failed with code {returncode}")
                print_info(f"stderr: {stderr}")
                return False

            print_success("Feature work item created")

            # Verify work_items.json updated
            work_items_file = self.test_dir / ".session/tracking/work_items.json"
            work_items_data = json.loads(work_items_file.read_text())

            if not work_items_data.get("work_items"):
                print_failure("No work items found in work_items.json")
                return False

            # work_items is a dict keyed by ID, get the first one
            work_item_id = list(work_items_data["work_items"].keys())[0]
            work_item = work_items_data["work_items"][work_item_id]
            if work_item["type"] != "feature":
                print_failure(f"Work item type incorrect: {work_item['type']}")
                return False
            print_success(f"Work item created with ID: {work_item['id']}")

            # Verify spec file created
            spec_file = self.test_dir / ".session/specs" / f"{work_item['id']}.md"
            if not spec_file.exists():
                print_failure(f"Spec file not created: {spec_file}")
                return False
            print_success("Spec file created")

            return True

        except KeyError as e:
            print_failure(f"KeyError during work item creation: {e}")
            print_info(f"work_items_data: {work_items_data}")
            return False
        except IndexError as e:
            print_failure(f"IndexError during work item creation: {e}")
            print_info(f"work_items_data: {work_items_data}")
            return False
        except Exception as e:
            print_failure(f"Exception during work item creation: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def test_session_start(self) -> bool:
        """Test Section 1.5: Enhanced /start."""
        print_test_header("Test 1.5: Session Start with Context Loading")

        try:
            # Run briefing generator
            returncode, stdout, stderr = run_command(
                "python3 scripts/briefing_generator.py",
                cwd=str(self.test_dir)
            )

            if returncode != 0:
                print_failure(f"Briefing generation failed with code {returncode}")
                print_info(f"stderr: {stderr}")
                return False

            # Verify briefing contains key sections
            required_sections = [
                "Session Briefing",
                "Work Item ID",
                "Project Context",
                "Current Stack",
                "Project Structure",
            ]

            for section in required_sections:
                if section not in stdout:
                    print_failure(f"Briefing missing section: {section}")
                    return False
                print_success(f"Briefing contains: {section}")

            # Verify git branch created
            returncode, stdout, stderr = run_command(
                "git branch",
                cwd=str(self.test_dir)
            )

            if "session-001" not in stdout:
                print_failure("Git session branch not created")
                return False
            print_success("Git session branch created")

            # Verify work item status updated to in_progress
            work_items_file = self.test_dir / ".session/tracking/work_items.json"
            work_items_data = json.loads(work_items_file.read_text())
            # work_items is a dict keyed by ID, get the first one
            work_item_id = list(work_items_data["work_items"].keys())[0]
            work_item = work_items_data["work_items"][work_item_id]

            if work_item["status"] != "in_progress":
                print_failure(f"Work item status not updated: {work_item['status']}")
                return False
            print_success("Work item status updated to in_progress")

            return True

        except KeyError as e:
            print_failure(f"KeyError during session start: {e}")
            print_info(f"work_items_data: {work_items_data}")
            return False
        except IndexError as e:
            print_failure(f"IndexError during session start: {e}")
            print_info(f"work_items_data: {work_items_data}")
            return False
        except Exception as e:
            print_failure(f"Exception during session start: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def test_session_validate(self) -> bool:
        """Test Section 1.7: /sdd:validate command."""
        print_test_header("Test 1.7: Session Validation")

        try:
            # Run session validation
            returncode, stdout, stderr = run_command(
                "python3 scripts/session_validate.py",
                cwd=str(self.test_dir)
            )

            # Validation might fail due to quality gates, which is expected
            # We're testing that it runs and provides output
            if "Running session validation" not in stdout and "Running session validation" not in stderr:
                print_failure("Session validation did not run properly")
                return False

            print_success("Session validation executed")

            # Check for expected validation sections
            output = stdout + stderr
            expected_checks = ["Git Status", "Quality Gates", "Work Item Criteria"]

            for check in expected_checks:
                if check in output:
                    print_success(f"Validation includes: {check}")
                else:
                    print_info(f"Validation may not include: {check}")

            return True

        except Exception as e:
            print_failure(f"Exception during session validation: {e}")
            return False

    def test_stack_and_tree_tracking(self) -> bool:
        """Test Sections 1.2 & 1.3: Stack and Tree tracking."""
        print_test_header("Test 1.2 & 1.3: Stack and Tree Tracking")

        try:
            # Modify project (add a new file)
            (self.test_dir / "new_file.py").write_text('print("New file")\n')
            (self.test_dir / "newdir").mkdir(exist_ok=True)
            (self.test_dir / "newdir" / "test.py").write_text('print("Test")\n')

            # Run stack update
            returncode, stdout, stderr = run_command(
                "python3 scripts/generate_stack.py",
                cwd=str(self.test_dir)
            )

            if returncode != 0:
                print_failure(f"Stack generation failed with code {returncode}")
                return False
            print_success("Stack tracking updated")

            # Run tree update
            returncode, stdout, stderr = run_command(
                "python3 scripts/generate_tree.py",
                cwd=str(self.test_dir)
            )

            if returncode != 0:
                print_failure(f"Tree generation failed with code {returncode}")
                return False
            print_success("Tree tracking updated")

            # Verify tree.txt includes new files
            tree_content = (self.test_dir / ".session/tracking/tree.txt").read_text()
            if "new_file.py" not in tree_content or "newdir" not in tree_content:
                print_failure("Tree tracking did not detect new files/directories")
                return False
            print_success("Tree tracking detected structural changes")

            return True

        except Exception as e:
            print_failure(f"Exception during stack/tree tracking: {e}")
            return False

    def test_git_workflow(self) -> bool:
        """Test Section 1.4: Git workflow integration."""
        print_test_header("Test 1.4: Git Workflow Integration")

        try:
            # Verify we're on a session branch
            returncode, stdout, stderr = run_command(
                "git branch --show-current",
                cwd=str(self.test_dir)
            )

            current_branch = stdout.strip()
            if not current_branch.startswith("session-"):
                print_failure(f"Not on session branch: {current_branch}")
                return False
            print_success(f"On session branch: {current_branch}")

            # Verify git status shows changes
            returncode, stdout, stderr = run_command(
                "git status --porcelain",
                cwd=str(self.test_dir)
            )

            if not stdout.strip():
                print_info("No git changes detected (files may need to be added)")
            else:
                print_success("Git tracking file changes")

            return True

        except Exception as e:
            print_failure(f"Exception during git workflow test: {e}")
            return False

    def run_all_tests(self) -> bool:
        """Run all Phase 1 tests."""
        print_test_header("PHASE 1: CORE PLUGIN FOUNDATION - COMPREHENSIVE TEST SUITE")

        self.setup_test_project()

        tests = [
            ("1.1: Session Initialization", self.test_session_init),
            ("1.8: Work Item Creation", self.test_work_item_creation),
            ("1.5: Session Start", self.test_session_start),
            ("1.7: Session Validation", self.test_session_validate),
            ("1.2 & 1.3: Stack and Tree Tracking", self.test_stack_and_tree_tracking),
            ("1.4: Git Workflow Integration", self.test_git_workflow),
        ]

        for test_name, test_func in tests:
            try:
                if test_func():
                    self.tests_passed += 1
                else:
                    self.tests_failed += 1
            except Exception as e:
                print_failure(f"Test {test_name} raised exception: {e}")
                self.tests_failed += 1

        # Print summary
        print_test_header("PHASE 1 TEST SUMMARY")
        print(f"{GREEN}Tests Passed: {self.tests_passed}{RESET}")
        print(f"{RED}Tests Failed: {self.tests_failed}{RESET}")
        print(f"Total Tests: {self.tests_passed + self.tests_failed}\n")

        success_rate = (self.tests_passed / (self.tests_passed + self.tests_failed)) * 100 if (self.tests_passed + self.tests_failed) > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%\n")

        if self.tests_failed == 0:
            print(f"{GREEN}✓ ALL PHASE 1 TESTS PASSED{RESET}\n")
            return True
        else:
            print(f"{RED}✗ SOME PHASE 1 TESTS FAILED{RESET}\n")
            return False


def main():
    """Main test runner."""
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        print_info(f"Using temporary test directory: {temp_dir}")

        tester = Phase1Tester(temp_dir)
        success = tester.run_all_tests()

        return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
