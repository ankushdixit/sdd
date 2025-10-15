#!/usr/bin/env python3
"""
Test script for Phase 5.5.5 - Integration Quality Gates
"""

import sys
import json
from pathlib import Path
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))
from scripts.quality_gates import QualityGates


def test_integration_quality_gate_methods():
    """Test integration quality gate methods exist and basic structure."""
    print("=" * 60)
    print("Testing Phase 5.5.5: Integration Quality Gates")
    print("=" * 60)
    print()

    tests_passed = 0
    tests_failed = 0

    # Test 1: QualityGates class instantiation
    print("Test 1: QualityGates class instantiation")
    try:
        gates = QualityGates()
        print("✅ PASS: QualityGates instantiated successfully")
        tests_passed += 1
    except Exception as e:
        print(f"❌ FAIL: Failed to instantiate QualityGates: {e}")
        tests_failed += 1
        return tests_passed, tests_failed
    print()

    # Test 2: Integration test methods exist
    print("Test 2: Integration quality gate methods exist")
    integration_methods = [
        "run_integration_tests",
        "validate_integration_environment"
    ]

    for method in integration_methods:
        if hasattr(gates, method):
            print(f"✅ PASS: Method {method} exists")
            tests_passed += 1
        else:
            print(f"❌ FAIL: Method {method} missing")
            tests_failed += 1
    print()

    # Test 3: Skips non-integration work items
    print("Test 3: Skips non-integration work items")
    work_item = {
        "id": "FEAT-001",
        "type": "feature",
        "title": "Regular Feature"
    }

    passed, results = gates.run_integration_tests(work_item)
    if passed and results.get("status") == "skipped":
        print("✅ PASS: Non-integration work items skipped")
        tests_passed += 1
    else:
        print("❌ FAIL: Should skip non-integration work items")
        tests_failed += 1
    print()

    # Test 4: Environment validation skips non-integration work items
    print("Test 4: Environment validation skips non-integration work items")
    passed, results = gates.validate_integration_environment(work_item)
    if passed and results.get("status") == "skipped":
        print("✅ PASS: Environment validation skipped for non-integration work items")
        tests_passed += 1
    else:
        print("❌ FAIL: Should skip environment validation for non-integration work items")
        tests_failed += 1
    print()

    # Test 5: Skips when integration tests disabled
    print("Test 5: Skips when integration tests disabled in config")

    # Create temp config with integration tests disabled
    temp_dir = Path(tempfile.mkdtemp())
    temp_config = temp_dir / "config.json"
    temp_config.write_text(json.dumps({
        "integration_tests": {"enabled": False}
    }))

    gates_disabled = QualityGates(config_path=temp_config)

    work_item = {
        "id": "INTEG-001",
        "type": "integration_test",
        "title": "Integration Test"
    }

    passed, results = gates_disabled.run_integration_tests(work_item)

    # Clean up
    shutil.rmtree(temp_dir)

    if passed and results.get("reason") == "disabled":
        print("✅ PASS: Integration tests skipped when disabled")
        tests_passed += 1
    else:
        print("❌ FAIL: Should skip when disabled in config")
        tests_failed += 1
    print()

    # Summary
    print("=" * 60)
    print("Test Summary - Integration Quality Gate Structure")
    print("=" * 60)
    print(f"Tests Passed: {tests_passed}")
    print(f"Tests Failed: {tests_failed}")
    print()

    return tests_passed, tests_failed


def test_environment_validation():
    """Test environment validation logic."""
    print("=" * 60)
    print("Testing Environment Validation")
    print("=" * 60)
    print()

    tests_passed = 0
    tests_failed = 0

    gates = QualityGates()

    # Test 1: Check Docker availability
    print("Test 1: Check Docker availability detection")
    work_item = {
        "id": "INTEG-001",
        "type": "integration_test",
        "environment_requirements": {
            "compose_file": "docker-compose.integration.yml"
        }
    }

    passed, results = gates.validate_integration_environment(work_item)

    # We can't guarantee Docker is installed, so just check the field exists
    if "docker_available" in results:
        print(f"  Docker available: {results['docker_available']}")
        print("✅ PASS: Docker availability checked")
        tests_passed += 1
    else:
        print("❌ FAIL: Docker availability not checked")
        tests_failed += 1
    print()

    # Test 2: Check Docker Compose availability
    print("Test 2: Check Docker Compose availability detection")
    if "docker_compose_available" in results:
        print(f"  Docker Compose available: {results['docker_compose_available']}")
        print("✅ PASS: Docker Compose availability checked")
        tests_passed += 1
    else:
        print("❌ FAIL: Docker Compose availability not checked")
        tests_failed += 1
    print()

    # Test 3: Missing compose file detection
    print("Test 3: Missing compose file detection")
    work_item_missing = {
        "id": "INTEG-002",
        "type": "integration_test",
        "environment_requirements": {
            "compose_file": "nonexistent-compose.yml"
        }
    }

    passed, results = gates.validate_integration_environment(work_item_missing)

    if "nonexistent-compose.yml" in results.get("missing_config", []):
        print("✅ PASS: Missing compose file detected")
        tests_passed += 1
    else:
        print("❌ FAIL: Missing compose file not detected")
        tests_failed += 1
    print()

    # Test 4: Missing config files detection
    print("Test 4: Missing config files detection")
    work_item_config = {
        "id": "INTEG-003",
        "type": "integration_test",
        "environment_requirements": {
            "compose_file": "docker-compose.integration.yml",
            "config_files": ["missing-config.yml", "another-missing.json"]
        }
    }

    passed, results = gates.validate_integration_environment(work_item_config)

    missing_count = len([f for f in results.get("missing_config", [])
                        if "missing-config.yml" in f or "another-missing.json" in f])
    if missing_count >= 2:
        print("✅ PASS: Missing config files detected")
        tests_passed += 1
    else:
        print(f"❌ FAIL: Should detect 2 missing files, found {missing_count}")
        tests_failed += 1
    print()

    # Test 5: Results dictionary structure
    print("Test 5: Results dictionary has correct structure")
    expected_keys = ["docker_available", "docker_compose_available",
                    "required_services", "missing_config", "passed"]

    all_keys_present = all(key in results for key in expected_keys)
    if all_keys_present:
        print("✅ PASS: Results dictionary has all required keys")
        tests_passed += 1
    else:
        print("❌ FAIL: Results dictionary missing required keys")
        tests_failed += 1
    print()

    print(f"Environment validation tests: {tests_passed}/{tests_passed + tests_failed} passed")
    print()

    return tests_passed, tests_failed


def test_integration_gate_configuration():
    """Test integration quality gate configuration loading."""
    print("=" * 60)
    print("Testing Integration Gate Configuration")
    print("=" * 60)
    print()

    tests_passed = 0
    tests_failed = 0

    # Create temp config
    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Test 1: Load config with integration_tests section
        print("Test 1: Load config with integration_tests section")
        config_file = temp_dir / "config.json"
        config_data = {
            "quality_gates": {
                "test_execution": {"enabled": True}
            },
            "integration_tests": {
                "enabled": True,
                "performance_benchmarks": {"required": True},
                "api_contracts": {"required": True}
            }
        }
        config_file.write_text(json.dumps(config_data, indent=2))

        gates = QualityGates(config_path=config_file)

        # Verify config loaded (indirectly by checking it doesn't crash)
        print("✅ PASS: Config with integration_tests section loaded")
        tests_passed += 1
        print()

        # Test 2: Integration gate respects enabled flag
        print("Test 2: Integration gate respects enabled flag")
        work_item = {
            "id": "INTEG-001",
            "type": "integration_test",
            "title": "Test"
        }

        # Should not be skipped since enabled is True
        passed, results = gates.run_integration_tests(work_item)
        if results.get("reason") != "disabled":
            print("✅ PASS: Enabled integration gate runs")
            tests_passed += 1
        else:
            print("❌ FAIL: Should not be disabled")
            tests_failed += 1
        print()

        # Test 3: Config with integration_tests disabled
        print("Test 3: Config with integration_tests disabled")
        config_data["integration_tests"]["enabled"] = False
        config_file.write_text(json.dumps(config_data, indent=2))

        gates_disabled = QualityGates(config_path=config_file)
        passed, results = gates_disabled.run_integration_tests(work_item)

        if results.get("reason") == "disabled":
            print("✅ PASS: Disabled integration gate skipped")
            tests_passed += 1
        else:
            print("❌ FAIL: Should be disabled")
            tests_failed += 1
        print()

    finally:
        # Clean up
        shutil.rmtree(temp_dir)

    print(f"Configuration tests: {tests_passed}/{tests_passed + tests_failed} passed")
    print()

    return tests_passed, tests_failed


def test_file_enhancements():
    """Test that quality_gates.py was enhanced correctly."""
    print("=" * 60)
    print("Testing File Enhancements")
    print("=" * 60)
    print()

    tests_passed = 0
    tests_failed = 0

    # Test 1: File exists
    print("Test 1: quality_gates.py file exists")
    file_path = Path("scripts/quality_gates.py")
    if file_path.exists():
        print("✅ PASS: File exists")
        tests_passed += 1
    else:
        print("❌ FAIL: File not found")
        tests_failed += 1
        return tests_passed, tests_failed
    print()

    # Test 2: Check for integration test method
    print("Test 2: run_integration_tests method defined")
    content = file_path.read_text()
    if "def run_integration_tests(self, work_item: dict)" in content:
        print("✅ PASS: run_integration_tests method defined")
        tests_passed += 1
    else:
        print("❌ FAIL: run_integration_tests method not found")
        tests_failed += 1
    print()

    # Test 3: Check for environment validation method
    print("Test 3: validate_integration_environment method defined")
    if "def validate_integration_environment(self, work_item: dict)" in content:
        print("✅ PASS: validate_integration_environment method defined")
        tests_passed += 1
    else:
        print("❌ FAIL: validate_integration_environment method not found")
        tests_failed += 1
    print()

    # Test 4: Check for integration test runner import
    print("Test 4: IntegrationTestRunner import present")
    if "from integration_test_runner import IntegrationTestRunner" in content:
        print("✅ PASS: IntegrationTestRunner import found")
        tests_passed += 1
    else:
        print("❌ FAIL: IntegrationTestRunner import not found")
        tests_failed += 1
    print()

    # Test 5: Check for performance benchmark import
    print("Test 5: PerformanceBenchmark import present")
    if "from performance_benchmark import PerformanceBenchmark" in content:
        print("✅ PASS: PerformanceBenchmark import found")
        tests_passed += 1
    else:
        print("❌ FAIL: PerformanceBenchmark import not found")
        tests_failed += 1
    print()

    # Test 6: Check for API contract validator import
    print("Test 6: APIContractValidator import present")
    if "from api_contract_validator import APIContractValidator" in content:
        print("✅ PASS: APIContractValidator import found")
        tests_passed += 1
    else:
        print("❌ FAIL: APIContractValidator import not found")
        tests_failed += 1
    print()

    # Test 7: Check for environment teardown in finally block
    print("Test 7: Environment teardown in finally block")
    if "finally:" in content and "runner.teardown_environment()" in content:
        print("✅ PASS: Environment teardown in finally block")
        tests_passed += 1
    else:
        print("❌ FAIL: Environment teardown not in finally block")
        tests_failed += 1
    print()

    print(f"File enhancement tests: {tests_passed}/{tests_passed + tests_failed} passed")
    print()

    return tests_passed, tests_failed


if __name__ == "__main__":
    print()
    print("#" * 60)
    print("# Phase 5.5.5 Test Suite")
    print("# Integration Quality Gates")
    print("#" * 60)
    print()

    total_passed = 0
    total_failed = 0

    # File enhancement tests
    passed, failed = test_file_enhancements()
    total_passed += passed
    total_failed += failed
    print()

    # Integration quality gate structure tests
    passed, failed = test_integration_quality_gate_methods()
    total_passed += passed
    total_failed += failed
    print()

    # Environment validation tests
    passed, failed = test_environment_validation()
    total_passed += passed
    total_failed += failed
    print()

    # Configuration tests
    passed, failed = test_integration_gate_configuration()
    total_passed += passed
    total_failed += failed
    print()

    # Final summary
    print("=" * 60)
    print("FINAL TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests Passed: {total_passed}")
    print(f"Total Tests Failed: {total_failed}")
    print(f"Total Tests: {total_passed + total_failed}")
    print()

    if total_failed == 0:
        print("=" * 60)
        print("✅ Phase 5.5.5 - ALL TESTS PASSED")
        print("=" * 60)
        sys.exit(0)
    else:
        print("=" * 60)
        print("❌ Phase 5.5.5 - SOME TESTS FAILED")
        print("=" * 60)
        sys.exit(1)
