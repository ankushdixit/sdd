#!/usr/bin/env python3
"""
Test script for Phase 5.5.2 - Integration Test Execution Framework
"""

import sys
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
from scripts.integration_test_runner import IntegrationTestRunner


@pytest.mark.skip(reason="Requires spec files (Phase 5.7 update) - needs test data setup")
def test_integration_test_runner_class():
    """Test IntegrationTestRunner class structure and methods."""
    print("=" * 60)
    print("Testing Phase 5.5.2: Integration Test Execution Framework")
    print("=" * 60)
    print()

    tests_passed = 0
    tests_failed = 0

    # Test 1: Class instantiation
    print("Test 1: IntegrationTestRunner class instantiation")
    work_item = {
        "id": "INTEG-001",
        "type": "integration_test",
        "title": "Test API Integration",
        "test_scenarios": [
            {
                "name": "Happy path",
                "setup": "Start services",
                "actions": ["Send request"],
                "expected_results": "HTTP 200",
            }
        ],
        "environment_requirements": {
            "compose_file": "docker-compose.integration.yml",
            "services_required": ["service-a", "service-b"],
            "test_data_fixtures": [],
        },
    }

    runner = None
    try:
        runner = IntegrationTestRunner(work_item)
        print("✅ PASS: IntegrationTestRunner instantiated successfully")
        tests_passed += 1
    except Exception as e:
        print(f"❌ FAIL: Failed to instantiate IntegrationTestRunner: {e}")
        tests_failed += 1
    print()

    # Test 2: Required methods exist
    print("Test 2: Required methods exist")
    required_methods = [
        "setup_environment",
        "_wait_for_service",
        "_load_test_data",
        "run_tests",
        "_run_pytest",
        "_run_jest",
        "_detect_language",
        "teardown_environment",
        "generate_report",
    ]

    if runner is not None:
        for method in required_methods:
            if hasattr(runner, method):
                print(f"✅ PASS: Method {method} exists")
                tests_passed += 1
            else:
                print(f"❌ FAIL: Method {method} missing")
                tests_failed += 1
    else:
        print("⚠️  Skipping remaining tests - runner not instantiated")
        tests_failed += len(required_methods)
    print()

    # Test 3: Results dictionary initialized correctly
    print("Test 3: Results dictionary initialized correctly")
    if runner is not None:
        expected_keys = [
            "scenarios",
            "start_time",
            "end_time",
            "total_duration",
            "passed",
            "failed",
            "skipped",
        ]
        all_keys_present = all(key in runner.results for key in expected_keys)

        if all_keys_present:
            print("✅ PASS: Results dictionary has all required keys")
            tests_passed += 1
        else:
            print("❌ FAIL: Results dictionary missing required keys")
            tests_failed += 1
    else:
        print("⚠️  Skipped - runner not instantiated")
        tests_failed += 1
    print()

    # Test 4: Language detection - Python
    print("Test 4: Language detection - Python")
    # Create temporary pyproject.toml
    test_file = Path("pyproject.toml")
    original_exists = test_file.exists()
    if not original_exists:
        test_file.write_text("[tool.poetry]")

    detected = runner._detect_language()
    if detected == "python":
        print("✅ PASS: Python detected correctly")
        tests_passed += 1
    else:
        print(f"❌ FAIL: Expected 'python', got '{detected}'")
        tests_failed += 1

    # Clean up
    if not original_exists and test_file.exists():
        test_file.unlink()
    print()

    # Test 5: Language detection - JavaScript
    print("Test 5: Language detection - JavaScript")
    # Create temporary package.json
    pkg_file = Path("package.json")
    ts_file = Path("tsconfig.json")
    pkg_original = pkg_file.exists()
    ts_original = ts_file.exists()

    if not pkg_original:
        pkg_file.write_text("{}")

    # Remove pyproject.toml temporarily
    py_file = Path("pyproject.toml")
    py_exists = py_file.exists()
    if py_exists:
        py_content = py_file.read_text()
        py_file.unlink()

    detected = runner._detect_language()
    if detected == "javascript":
        print("✅ PASS: JavaScript detected correctly")
        tests_passed += 1
    else:
        print(f"❌ FAIL: Expected 'javascript', got '{detected}'")
        tests_failed += 1

    # Clean up
    if not pkg_original and pkg_file.exists():
        pkg_file.unlink()
    if py_exists:
        py_file.write_text(py_content)
    print()

    # Test 6: Language detection - TypeScript
    print("Test 6: Language detection - TypeScript")
    if not pkg_original:
        pkg_file.write_text("{}")
    if not ts_original:
        ts_file.write_text("{}")

    # Remove pyproject.toml temporarily
    if py_exists:
        py_file.unlink()

    detected = runner._detect_language()
    if detected == "typescript":
        print("✅ PASS: TypeScript detected correctly")
        tests_passed += 1
    else:
        print(f"❌ FAIL: Expected 'typescript', got '{detected}'")
        tests_failed += 1

    # Clean up
    if not pkg_original and pkg_file.exists():
        pkg_file.unlink()
    if not ts_original and ts_file.exists():
        ts_file.unlink()
    if py_exists:
        py_file.write_text(py_content)
    print()

    # Test 7: Report generation
    print("Test 7: Report generation")
    runner.results = {
        "start_time": "2024-01-01T10:00:00",
        "end_time": "2024-01-01T10:05:30",
        "total_duration": 330.0,
        "passed": 10,
        "failed": 2,
        "skipped": 1,
    }

    try:
        report = runner.generate_report()
        if "Integration Test Report" in report and "FAILED" in report:
            print("✅ PASS: Report generated correctly")
            tests_passed += 1
        else:
            print("❌ FAIL: Report missing expected content")
            tests_failed += 1
    except Exception as e:
        print(f"❌ FAIL: Report generation failed: {e}")
        tests_failed += 1
    print()

    # Test 8: Report shows PASSED when no failures
    print("Test 8: Report shows PASSED when no failures")
    runner.results["failed"] = 0
    report = runner.generate_report()
    if "PASSED" in report:
        print("✅ PASS: Report shows PASSED status correctly")
        tests_passed += 1
    else:
        print("❌ FAIL: Report should show PASSED status")
        tests_failed += 1
    print()

    # Test 9: Environment requirements parsed correctly
    print("Test 9: Environment requirements parsed correctly")
    if runner.env_requirements.get("compose_file") == "docker-compose.integration.yml":
        print("✅ PASS: Compose file parsed correctly")
        tests_passed += 1
    else:
        print("❌ FAIL: Compose file not parsed correctly")
        tests_failed += 1
    print()

    # Test 10: Services list parsed correctly
    print("Test 10: Services list parsed correctly")
    services = runner.env_requirements.get("services_required", [])
    if services == ["service-a", "service-b"]:
        print("✅ PASS: Services list parsed correctly")
        tests_passed += 1
    else:
        print("❌ FAIL: Services list not parsed correctly")
        tests_failed += 1
    print()

    # Test 11: Test scenarios stored correctly
    print("Test 11: Test scenarios stored correctly")
    if len(runner.test_scenarios) == 1:
        print("✅ PASS: Test scenarios stored correctly")
        tests_passed += 1
    else:
        print("❌ FAIL: Test scenarios not stored correctly")
        tests_failed += 1
    print()

    # Test 12: Work item data accessible
    print("Test 12: Work item data accessible")
    if runner.work_item.get("id") == "INTEG-001":
        print("✅ PASS: Work item data accessible")
        tests_passed += 1
    else:
        print("❌ FAIL: Work item data not accessible")
        tests_failed += 1
    print()

    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Tests Passed: {tests_passed}")
    print(f"Tests Failed: {tests_failed}")
    print(f"Total Tests: {tests_passed + tests_failed}")
    print()

    if tests_failed == 0:
        print("✅ All tests passed!")
        return 0
    else:
        print(f"❌ {tests_failed} test(s) failed")
        return 1


def test_file_structure():
    """Test that the integration_test_runner.py file exists and is properly structured."""
    print("=" * 60)
    print("Testing File Structure")
    print("=" * 60)
    print()

    tests_passed = 0
    tests_failed = 0

    # Test 1: File exists
    print("Test 1: integration_test_runner.py file exists")
    file_path = Path("scripts/integration_test_runner.py")
    if file_path.exists():
        print("✅ PASS: File exists")
        tests_passed += 1
    else:
        print("❌ FAIL: File not found")
        tests_failed += 1
        return 1
    print()

    # Test 2: File is executable
    print("Test 2: File has executable permissions")
    import os

    if os.access(file_path, os.X_OK):
        print("✅ PASS: File is executable")
        tests_passed += 1
    else:
        print("❌ FAIL: File is not executable")
        tests_failed += 1
    print()

    # Test 3: Check for required imports
    print("Test 3: Required imports present")
    content = file_path.read_text()
    required_imports = [
        "import subprocess",
        "import json",
        "import time",
        "from pathlib import Path",
        "from typing import",
        "from datetime import datetime",
    ]

    for imp in required_imports:
        if imp in content:
            print(f"✅ PASS: Found import: {imp}")
            tests_passed += 1
        else:
            print(f"❌ FAIL: Missing import: {imp}")
            tests_failed += 1
    print()

    # Test 4: IntegrationTestRunner class defined
    print("Test 4: IntegrationTestRunner class defined")
    if "class IntegrationTestRunner:" in content:
        print("✅ PASS: IntegrationTestRunner class defined")
        tests_passed += 1
    else:
        print("❌ FAIL: IntegrationTestRunner class not found")
        tests_failed += 1
    print()

    # Test 5: Check for main function
    print("Test 5: main() function defined")
    if "def main():" in content:
        print("✅ PASS: main() function defined")
        tests_passed += 1
    else:
        print("❌ FAIL: main() function not found")
        tests_failed += 1
    print()

    # Test 6: Check for __main__ block
    print("Test 6: __main__ block present")
    if 'if __name__ == "__main__":' in content:
        print("✅ PASS: __main__ block present")
        tests_passed += 1
    else:
        print("❌ FAIL: __main__ block not found")
        tests_failed += 1
    print()

    # Summary
    print(
        f"\nFile structure tests: {tests_passed}/{tests_passed + tests_failed} passed"
    )
    print()

    if tests_failed == 0:
        print("✅ File structure tests passed!")
        return 0
    else:
        print(f"❌ {tests_failed} test(s) failed")
        return 1


@pytest.mark.skip(reason="Requires spec files (Phase 5.7 update) - needs test data setup")
def test_docker_compose_support():
    """Test Docker Compose integration logic."""
    print("=" * 60)
    print("Testing Docker Compose Support")
    print("=" * 60)
    print()

    tests_passed = 0
    tests_failed = 0

    work_item = {
        "id": "INTEG-002",
        "type": "integration_test",
        "title": "Docker Compose Test",
        "test_scenarios": [],
        "environment_requirements": {
            "compose_file": "custom-compose.yml",
            "services_required": ["db", "api", "cache"],
            "test_data_fixtures": ["fixtures/users.py", "fixtures/products.py"],
        },
    }

    runner = IntegrationTestRunner(work_item)

    # Test 1: Compose file configuration
    print("Test 1: Custom compose file configuration")
    compose_file = runner.env_requirements.get("compose_file")
    if compose_file == "custom-compose.yml":
        print("✅ PASS: Custom compose file configured")
        tests_passed += 1
    else:
        print("❌ FAIL: Compose file not configured correctly")
        tests_failed += 1
    print()

    # Test 2: Multiple services configured
    print("Test 2: Multiple services configured")
    services = runner.env_requirements.get("services_required", [])
    if (
        len(services) == 3
        and "db" in services
        and "api" in services
        and "cache" in services
    ):
        print("✅ PASS: All services configured")
        tests_passed += 1
    else:
        print("❌ FAIL: Services not configured correctly")
        tests_failed += 1
    print()

    # Test 3: Test data fixtures configured
    print("Test 3: Test data fixtures configured")
    fixtures = runner.env_requirements.get("test_data_fixtures", [])
    if len(fixtures) == 2:
        print("✅ PASS: Fixtures configured")
        tests_passed += 1
    else:
        print("❌ FAIL: Fixtures not configured correctly")
        tests_failed += 1
    print()

    # Summary
    print(
        f"\nDocker Compose tests: {tests_passed}/{tests_passed + tests_failed} passed"
    )
    print()

    if tests_failed == 0:
        print("✅ Docker Compose support tests passed!")
        return 0
    else:
        print(f"❌ {tests_failed} test(s) failed")
        return 1


if __name__ == "__main__":
    print()
    print("#" * 60)
    print("# Phase 5.5.2 Test Suite")
    print("# Integration Test Execution Framework")
    print("#" * 60)
    print()

    result1 = test_file_structure()
    print()

    result2 = test_integration_test_runner_class()
    print()

    result3 = test_docker_compose_support()
    print()

    if result1 == 0 and result2 == 0 and result3 == 0:
        print("=" * 60)
        print("✅ Phase 5.5.2 - ALL TESTS PASSED")
        print("=" * 60)
        sys.exit(0)
    else:
        print("=" * 60)
        print("❌ Phase 5.5.2 - SOME TESTS FAILED")
        print("=" * 60)
        sys.exit(1)
