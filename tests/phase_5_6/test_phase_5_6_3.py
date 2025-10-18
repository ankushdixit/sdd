#!/usr/bin/env python3
"""
Test script for Phase 5.6.3 - Environment Validation System
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.environment_validator import EnvironmentValidator  # noqa: E402


def test_environment_validator():
    """Test EnvironmentValidator class structure and methods."""
    print("=" * 60)
    print("Testing Phase 5.6.3: Environment Validation System")
    print("=" * 60)
    print()

    tests_passed = 0
    tests_failed = 0

    # Test 1: Class instantiation
    print("Test 1: EnvironmentValidator class instantiation")
    try:
        validator = EnvironmentValidator("staging")
        print("✅ PASS: EnvironmentValidator instantiated successfully")
        tests_passed += 1
    except Exception as e:
        print(f"❌ FAIL: Failed to instantiate EnvironmentValidator: {e}")
        tests_failed += 1
    print()

    # Test 2: Connectivity validation method exists and works
    print("Test 2: Connectivity validation works")
    try:
        passed, results = validator.validate_connectivity()
        if "checks" in results and "passed" in results:
            print("✅ PASS: Connectivity validation works")
            tests_passed += 1
        else:
            print(f"❌ FAIL: Connectivity validation missing keys: {results}")
            tests_failed += 1
    except Exception as e:
        print(f"❌ FAIL: Connectivity validation failed: {e}")
        tests_failed += 1
    print()

    # Test 3: Configuration validation works
    print("Test 3: Configuration validation works with environment variables")
    # Set test environment variable
    os.environ["TEST_VAR"] = "test_value"
    passed, results = validator.validate_configuration(["TEST_VAR"])
    if passed and any(check["passed"] for check in results["checks"]):
        print("✅ PASS: Configuration validation works")
        tests_passed += 1
    else:
        print(f"❌ FAIL: Configuration validation failed: {results}")
        tests_failed += 1
    print()

    # Test 4: Configuration validation detects missing variables
    print("Test 4: Configuration validation detects missing variables")
    passed, results = validator.validate_configuration(["NONEXISTENT_VAR"])
    if not passed and any(not check["passed"] for check in results["checks"]):
        print("✅ PASS: Missing environment variable detected")
        tests_passed += 1
    else:
        print(f"❌ FAIL: Missing variable not detected: {results}")
        tests_failed += 1
    print()

    # Test 5: Dependency validation works
    print("Test 5: Dependency validation works")
    try:
        passed, results = validator.validate_dependencies()
        if "checks" in results and "passed" in results:
            print("✅ PASS: Dependency validation works")
            tests_passed += 1
        else:
            print(f"❌ FAIL: Dependency validation missing keys: {results}")
            tests_failed += 1
    except Exception as e:
        print(f"❌ FAIL: Dependency validation failed: {e}")
        tests_failed += 1
    print()

    # Test 6: Health check validation works
    print("Test 6: Health check validation works")
    try:
        passed, results = validator.validate_health_checks()
        if "checks" in results and "passed" in results:
            print("✅ PASS: Health check validation works")
            tests_passed += 1
        else:
            print(f"❌ FAIL: Health check validation missing keys: {results}")
            tests_failed += 1
    except Exception as e:
        print(f"❌ FAIL: Health check validation failed: {e}")
        tests_failed += 1
    print()

    # Test 7: Monitoring validation works
    print("Test 7: Monitoring validation works")
    try:
        passed, results = validator.validate_monitoring()
        if "checks" in results and "passed" in results:
            print("✅ PASS: Monitoring validation works")
            tests_passed += 1
        else:
            print(f"❌ FAIL: Monitoring validation missing keys: {results}")
            tests_failed += 1
    except Exception as e:
        print(f"❌ FAIL: Monitoring validation failed: {e}")
        tests_failed += 1
    print()

    # Test 8: Infrastructure validation works
    print("Test 8: Infrastructure validation works")
    try:
        passed, results = validator.validate_infrastructure()
        if "checks" in results and "passed" in results:
            print("✅ PASS: Infrastructure validation works")
            tests_passed += 1
        else:
            print(f"❌ FAIL: Infrastructure validation missing keys: {results}")
            tests_failed += 1
    except Exception as e:
        print(f"❌ FAIL: Infrastructure validation failed: {e}")
        tests_failed += 1
    print()

    # Test 9: Capacity validation works
    print("Test 9: Capacity validation works")
    try:
        passed, results = validator.validate_capacity()
        if "checks" in results and "passed" in results:
            print("✅ PASS: Capacity validation works")
            tests_passed += 1
        else:
            print(f"❌ FAIL: Capacity validation missing keys: {results}")
            tests_failed += 1
    except Exception as e:
        print(f"❌ FAIL: Capacity validation failed: {e}")
        tests_failed += 1
    print()

    # Test 10: validate_all() runs all checks
    print("Test 10: validate_all() runs all checks")
    try:
        passed, results = validator.validate_all(required_env_vars=["TEST_VAR"])
        expected_validations = [
            "Connectivity",
            "Configuration",
            "Dependencies",
            "Health Checks",
            "Monitoring",
            "Infrastructure",
            "Capacity",
        ]

        validation_names = [v["name"] for v in results.get("validations", [])]
        all_present = all(name in validation_names for name in expected_validations)

        if all_present:
            print("✅ PASS: validate_all() runs all 7 validation types")
            tests_passed += 1
        else:
            missing = [n for n in expected_validations if n not in validation_names]
            print(f"❌ FAIL: Missing validations: {missing}")
            print(f"  Found: {validation_names}")
            tests_failed += 1
    except Exception as e:
        print(f"❌ FAIL: validate_all() failed: {e}")
        tests_failed += 1
    print()

    # Cleanup
    if "TEST_VAR" in os.environ:
        del os.environ["TEST_VAR"]

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
    sys.exit(test_environment_validator())
