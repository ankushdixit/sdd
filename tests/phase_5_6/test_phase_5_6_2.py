#!/usr/bin/env python3
"""
Test script for Phase 5.6.2 - Deployment Execution Framework
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.deployment_executor import DeploymentExecutor


def test_deployment_executor():
    """Test DeploymentExecutor class structure and methods."""
    print("=" * 60)
    print("Testing Phase 5.6.2: Deployment Execution Framework")
    print("=" * 60)
    print()

    tests_passed = 0
    tests_failed = 0

    # Test 1: Class instantiation
    print("Test 1: DeploymentExecutor class instantiation")
    work_item = {
        "id": "DEPLOY-001",
        "type": "deployment",
        "title": "Production Deployment",
        "specification": """
## Deployment Procedure
### Deployment Steps
1. Pull code
2. Build
"""
    }

    try:
        executor = DeploymentExecutor(work_item)
        print("✅ PASS: DeploymentExecutor instantiated successfully")
        tests_passed += 1
    except Exception as e:
        print(f"❌ FAIL: Failed to instantiate DeploymentExecutor: {e}")
        tests_failed += 1
    print()

    # Test 2: Required methods exist
    print("Test 2: Required methods exist")
    required_methods = [
        "pre_deployment_validation",
        "execute_deployment",
        "run_smoke_tests",
        "rollback",
        "_check_integration_tests",
        "_check_security_scans",
        "_check_environment_readiness",
        "_parse_deployment_steps",
        "_execute_deployment_step",
        "_parse_smoke_tests",
        "_execute_smoke_test",
        "_parse_rollback_steps",
        "_execute_rollback_step",
        "get_deployment_log"
    ]

    for method in required_methods:
        if hasattr(executor, method):
            print(f"✅ PASS: Method {method} exists")
            tests_passed += 1
        else:
            print(f"❌ FAIL: Method {method} missing")
            tests_failed += 1
    print()

    # Test 3: Configuration loaded
    print("Test 3: Configuration loaded from default config")
    if executor.config:
        print("✅ PASS: Configuration loaded")
        tests_passed += 1
    else:
        print("❌ FAIL: Configuration not loaded")
        tests_failed += 1
    print()

    # Test 4: Default configuration structure
    print("Test 4: Default configuration has required keys")
    required_keys = [
        "pre_deployment_checks",
        "smoke_tests",
        "rollback",
        "environments"
    ]

    all_keys_present = all(key in executor.config for key in required_keys)
    if all_keys_present:
        print("✅ PASS: Default configuration has all required keys")
        tests_passed += 1
    else:
        missing = [k for k in required_keys if k not in executor.config]
        print(f"❌ FAIL: Missing configuration keys: {missing}")
        tests_failed += 1
    print()

    # Test 5: Pre-deployment validation checks integration tests
    print("Test 5: Pre-deployment validation checks integration tests")
    executor.config["pre_deployment_checks"]["integration_tests"] = True
    passed, results = executor.pre_deployment_validation()
    integration_check = any(
        check["name"] == "Integration Tests"
        for check in results.get("checks", [])
    )
    if integration_check:
        print("✅ PASS: Integration tests check included")
        tests_passed += 1
    else:
        print(f"❌ FAIL: Integration tests check not found. Checks: {results.get('checks')}")
        tests_failed += 1
    print()

    # Test 6: Pre-deployment validation checks security scans
    print("Test 6: Pre-deployment validation checks security scans")
    security_check = any(
        check["name"] == "Security Scans"
        for check in results.get("checks", [])
    )
    if security_check:
        print("✅ PASS: Security scans check included")
        tests_passed += 1
    else:
        print(f"❌ FAIL: Security scans check not found. Checks: {results.get('checks')}")
        tests_failed += 1
    print()

    # Test 7: Pre-deployment validation checks environment readiness
    print("Test 7: Pre-deployment validation checks environment readiness")
    env_check = any(
        check["name"] == "Environment Readiness"
        for check in results.get("checks", [])
    )
    if env_check:
        print("✅ PASS: Environment readiness check included")
        tests_passed += 1
    else:
        print(f"❌ FAIL: Environment readiness check not found. Checks: {results.get('checks')}")
        tests_failed += 1
    print()

    # Test 8: Deployment execution returns results
    print("Test 8: Deployment execution returns results")
    success, results = executor.execute_deployment(dry_run=True)
    if "started_at" in results and "completed_at" in results:
        print("✅ PASS: Deployment execution returns timestamped results")
        tests_passed += 1
    else:
        print(f"❌ FAIL: Missing timestamps in results: {results}")
        tests_failed += 1
    print()

    # Test 9: Deployment logging works
    print("Test 9: Deployment logging works")
    log = executor.get_deployment_log()
    if log and len(log) > 0:
        print(f"✅ PASS: Deployment logging works ({len(log)} log entries)")
        tests_passed += 1
    else:
        print("❌ FAIL: Deployment logging not working")
        tests_failed += 1
    print()

    # Test 10: Smoke tests can be executed
    print("Test 10: Smoke tests execute")
    passed, results = executor.run_smoke_tests()
    if "tests" in results or "status" in results:
        print("✅ PASS: Smoke tests execute")
        tests_passed += 1
    else:
        print(f"❌ FAIL: Smoke tests execution failed: {results}")
        tests_failed += 1
    print()

    # Test 11: Smoke test configuration used
    print("Test 11: Smoke test configuration used")
    if executor.config["smoke_tests"].get("enabled") is not None:
        print("✅ PASS: Smoke test configuration loaded")
        tests_passed += 1
    else:
        print("❌ FAIL: Smoke test configuration not loaded")
        tests_failed += 1
    print()

    # Test 12: Rollback can be executed
    print("Test 12: Rollback execution works")
    success, results = executor.rollback()
    if "started_at" in results and "completed_at" in results:
        print("✅ PASS: Rollback executes with timestamps")
        tests_passed += 1
    else:
        print(f"❌ FAIL: Rollback execution failed: {results}")
        tests_failed += 1
    print()

    # Test 13: Rollback steps tracked
    print("Test 13: Rollback steps tracked")
    if "steps" in results:
        print("✅ PASS: Rollback steps tracked")
        tests_passed += 1
    else:
        print(f"❌ FAIL: Rollback steps not tracked: {results}")
        tests_failed += 1
    print()

    # Test 14: Dry-run mode works
    print("Test 14: Dry-run mode works")
    success, results = executor.execute_deployment(dry_run=True)
    if success:
        print("✅ PASS: Dry-run mode executes successfully")
        tests_passed += 1
    else:
        print(f"❌ FAIL: Dry-run mode failed: {results}")
        tests_failed += 1
    print()

    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests passed: {tests_passed}")
    print(f"Tests failed: {tests_failed}")
    print(f"Total tests: {tests_passed + tests_failed}")
    print()

    if tests_failed == 0:
        print("✅ All tests passed!")
        return 0
    else:
        print(f"❌ {tests_failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(test_deployment_executor())
