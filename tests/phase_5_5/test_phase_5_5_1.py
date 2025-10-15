#!/usr/bin/env python3
"""
Test script for Phase 5.5.1 - Enhanced Integration Test Work Item Type
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))
from scripts.work_item_manager import WorkItemManager


def test_integration_test_validation():
    """Test the validate_integration_test method."""
    manager = WorkItemManager()

    print("=" * 60)
    print("Testing Phase 5.5.1: Enhanced Integration Test Work Item Type")
    print("=" * 60)
    print()

    tests_passed = 0
    tests_failed = 0

    # Test 1: Valid integration test work item
    print("Test 1: Valid integration test work item")
    valid_work_item = {
        "id": "INTEG-001",
        "type": "integration_test",
        "title": "Test Service A to B Integration",
        "scope": "Service A to Service B API integration",
        "test_scenarios": [
            {
                "name": "Happy path",
                "setup": "Services running",
                "actions": ["Send request", "Verify response"],
                "expected_results": "HTTP 200",
            }
        ],
        "performance_benchmarks": {
            "response_time": {"p50": 100, "p95": 500},
            "throughput": {"min": 100, "target": 500},
        },
        "api_contracts": [
            {"contract_file": "contracts/service-a-to-b.yaml", "version": "1.0.0"}
        ],
        "environment_requirements": {
            "services_required": ["service-a", "service-b", "postgres"]
        },
        "dependencies": ["FEAT-001", "FEAT-002"],
    }

    is_valid, errors = manager.validate_integration_test(valid_work_item)
    if is_valid:
        print("✅ PASS: Valid work item accepted")
        tests_passed += 1
    else:
        print(f"❌ FAIL: Valid work item rejected: {errors}")
        tests_failed += 1
    print()

    # Test 2: Missing scope
    print("Test 2: Missing scope")
    invalid_item = valid_work_item.copy()
    del invalid_item["scope"]
    is_valid, errors = manager.validate_integration_test(invalid_item)
    if not is_valid and any("scope" in e.lower() for e in errors):
        print("✅ PASS: Missing scope detected")
        tests_passed += 1
    else:
        print("❌ FAIL: Missing scope not detected")
        tests_failed += 1
    print()

    # Test 3: Missing test scenarios
    print("Test 3: Missing test scenarios")
    invalid_item = valid_work_item.copy()
    invalid_item["test_scenarios"] = []
    is_valid, errors = manager.validate_integration_test(invalid_item)
    if not is_valid and any("scenario" in e.lower() for e in errors):
        print("✅ PASS: Missing test scenarios detected")
        tests_passed += 1
    else:
        print("❌ FAIL: Missing test scenarios not detected")
        tests_failed += 1
    print()

    # Test 4: Missing performance benchmarks
    print("Test 4: Missing performance benchmarks")
    invalid_item = valid_work_item.copy()
    del invalid_item["performance_benchmarks"]
    is_valid, errors = manager.validate_integration_test(invalid_item)
    if not is_valid and any("performance" in e.lower() for e in errors):
        print("✅ PASS: Missing performance benchmarks detected")
        tests_passed += 1
    else:
        print("❌ FAIL: Missing performance benchmarks not detected")
        tests_failed += 1
    print()

    # Test 5: Missing API contracts
    print("Test 5: Missing API contracts")
    invalid_item = valid_work_item.copy()
    invalid_item["api_contracts"] = []
    is_valid, errors = manager.validate_integration_test(invalid_item)
    if not is_valid and any("contract" in e.lower() for e in errors):
        print("✅ PASS: Missing API contracts detected")
        tests_passed += 1
    else:
        print("❌ FAIL: Missing API contracts not detected")
        tests_failed += 1
    print()

    # Test 6: Missing environment requirements
    print("Test 6: Missing environment requirements")
    invalid_item = valid_work_item.copy()
    del invalid_item["environment_requirements"]
    is_valid, errors = manager.validate_integration_test(invalid_item)
    if not is_valid and any("environment" in e.lower() for e in errors):
        print("✅ PASS: Missing environment requirements detected")
        tests_passed += 1
    else:
        print("❌ FAIL: Missing environment requirements not detected")
        tests_failed += 1
    print()

    # Test 7: Scenario missing setup
    print("Test 7: Scenario missing setup")
    invalid_item = valid_work_item.copy()
    invalid_item["test_scenarios"] = [{"actions": ["test"], "expected_results": "pass"}]
    is_valid, errors = manager.validate_integration_test(invalid_item)
    if not is_valid and any("setup" in e.lower() for e in errors):
        print("✅ PASS: Missing setup in scenario detected")
        tests_passed += 1
    else:
        print("❌ FAIL: Missing setup in scenario not detected")
        tests_failed += 1
    print()

    # Test 8: Scenario missing actions
    print("Test 8: Scenario missing actions")
    invalid_item = valid_work_item.copy()
    invalid_item["test_scenarios"] = [{"setup": "test", "expected_results": "pass"}]
    is_valid, errors = manager.validate_integration_test(invalid_item)
    if not is_valid and any("actions" in e.lower() for e in errors):
        print("✅ PASS: Missing actions in scenario detected")
        tests_passed += 1
    else:
        print("❌ FAIL: Missing actions in scenario not detected")
        tests_failed += 1
    print()

    # Test 9: Scenario missing expected results
    print("Test 9: Scenario missing expected results")
    invalid_item = valid_work_item.copy()
    invalid_item["test_scenarios"] = [{"setup": "test", "actions": ["action"]}]
    is_valid, errors = manager.validate_integration_test(invalid_item)
    if not is_valid and any("expected" in e.lower() for e in errors):
        print("✅ PASS: Missing expected results in scenario detected")
        tests_passed += 1
    else:
        print("❌ FAIL: Missing expected results in scenario not detected")
        tests_failed += 1
    print()

    # Test 10: Performance benchmarks missing response time
    print("Test 10: Performance benchmarks missing response time")
    invalid_item = valid_work_item.copy()
    invalid_item["performance_benchmarks"] = {"throughput": {"min": 100}}
    is_valid, errors = manager.validate_integration_test(invalid_item)
    if not is_valid and any("response" in e.lower() for e in errors):
        print("✅ PASS: Missing response time in benchmarks detected")
        tests_passed += 1
    else:
        print("❌ FAIL: Missing response time in benchmarks not detected")
        tests_failed += 1
    print()

    # Test 11: Performance benchmarks missing throughput
    print("Test 11: Performance benchmarks missing throughput")
    invalid_item = valid_work_item.copy()
    invalid_item["performance_benchmarks"] = {"response_time": {"p50": 100}}
    is_valid, errors = manager.validate_integration_test(invalid_item)
    if not is_valid and any("throughput" in e.lower() for e in errors):
        print("✅ PASS: Missing throughput in benchmarks detected")
        tests_passed += 1
    else:
        print("❌ FAIL: Missing throughput in benchmarks not detected")
        tests_failed += 1
    print()

    # Test 12: API contract missing contract file
    print("Test 12: API contract missing contract file")
    invalid_item = valid_work_item.copy()
    invalid_item["api_contracts"] = [{"version": "1.0.0"}]
    is_valid, errors = manager.validate_integration_test(invalid_item)
    if not is_valid and any("contract_file" in e.lower() for e in errors):
        print("✅ PASS: Missing contract file detected")
        tests_passed += 1
    else:
        print("❌ FAIL: Missing contract file not detected")
        tests_failed += 1
    print()

    # Test 13: API contract missing version
    print("Test 13: API contract missing version")
    invalid_item = valid_work_item.copy()
    invalid_item["api_contracts"] = [{"contract_file": "contract.yaml"}]
    is_valid, errors = manager.validate_integration_test(invalid_item)
    if not is_valid and any("version" in e.lower() for e in errors):
        print("✅ PASS: Missing version detected")
        tests_passed += 1
    else:
        print("❌ FAIL: Missing version not detected")
        tests_failed += 1
    print()

    # Test 14: Missing services_required in environment
    print("Test 14: Missing services_required in environment")
    invalid_item = valid_work_item.copy()
    invalid_item["environment_requirements"] = {}
    is_valid, errors = manager.validate_integration_test(invalid_item)
    if not is_valid and any("services" in e.lower() for e in errors):
        print("✅ PASS: Missing services_required detected")
        tests_passed += 1
    else:
        print("❌ FAIL: Missing services_required not detected")
        tests_failed += 1
    print()

    # Test 15: Missing dependencies
    print("Test 15: Missing dependencies")
    invalid_item = valid_work_item.copy()
    invalid_item["dependencies"] = []
    is_valid, errors = manager.validate_integration_test(invalid_item)
    if not is_valid and any("dependencies" in e.lower() for e in errors):
        print("✅ PASS: Missing dependencies detected")
        tests_passed += 1
    else:
        print("❌ FAIL: Missing dependencies not detected")
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


def test_template_enhanced():
    """Test that the template file has all required sections."""
    print("=" * 60)
    print("Testing Integration Test Template")
    print("=" * 60)
    print()

    template_path = Path("templates/integration_test_spec.md")
    if not template_path.exists():
        print("❌ FAIL: Template file not found")
        return 1

    template_content = template_path.read_text()

    required_sections = [
        "## Scope",
        "**Components:**",
        "**Integration Points:**",
        "## Test Scenarios",
        "### Scenario 1:",
        "**Setup:**",
        "**Actions:**",
        "**Expected Results:**",
        "## Performance Benchmarks",
        "**Response Time Requirements:**",
        "**Throughput Requirements:**",
        "**Resource Limits:**",
        "**Load Test Duration:**",
        "## API Contracts",
        "## Environment Requirements",
        "**Services Required:**",
        "**Configuration:**",
        "**Infrastructure:**",
        "## Dependencies",
        "**Work Item Dependencies:**",
        "**Service Dependencies:**",
        "## Acceptance Criteria",
        "**Functional:**",
        "**Performance:**",
        "**Contracts:**",
        "**Documentation:**",
    ]

    tests_passed = 0
    tests_failed = 0

    for section in required_sections:
        if section in template_content:
            print(f"✅ Found: {section}")
            tests_passed += 1
        else:
            print(f"❌ Missing: {section}")
            tests_failed += 1

    print()
    print(f"Template sections found: {tests_passed}/{len(required_sections)}")
    print()

    if tests_failed == 0:
        print("✅ Template has all required sections!")
        return 0
    else:
        print(f"❌ Template missing {tests_failed} section(s)")
        return 1


def test_config_integration():
    """Test that config template includes integration_tests section."""
    print("=" * 60)
    print("Testing Config Integration")
    print("=" * 60)
    print()

    # Read init_project.py to verify config structure
    init_script = Path("scripts/init_project.py")
    if not init_script.exists():
        print("❌ FAIL: init_project.py not found")
        return 1

    content = init_script.read_text()

    required_config_keys = [
        '"integration_tests"',
        '"docker_compose_file"',
        '"environment_validation"',
        '"health_check_timeout"',
        '"performance_benchmarks"',
        '"api_contracts"',
        '"regression_threshold"',
        '"breaking_change_detection"',
    ]

    tests_passed = 0
    tests_failed = 0

    for key in required_config_keys:
        if key in content:
            print(f"✅ Found config key: {key}")
            tests_passed += 1
        else:
            print(f"❌ Missing config key: {key}")
            tests_failed += 1

    print()
    print(f"Config keys found: {tests_passed}/{len(required_config_keys)}")
    print()

    if tests_failed == 0:
        print("✅ Config has all required integration_tests keys!")
        return 0
    else:
        print(f"❌ Config missing {tests_failed} key(s)")
        return 1


if __name__ == "__main__":
    print()
    print("#" * 60)
    print("# Phase 5.5.1 Test Suite")
    print("# Enhanced Integration Test Work Item Type")
    print("#" * 60)
    print()

    result1 = test_template_enhanced()
    print()

    result2 = test_config_integration()
    print()

    result3 = test_integration_test_validation()
    print()

    if result1 == 0 and result2 == 0 and result3 == 0:
        print("=" * 60)
        print("✅ Phase 5.5.1 - ALL TESTS PASSED")
        print("=" * 60)
        sys.exit(0)
    else:
        print("=" * 60)
        print("❌ Phase 5.5.1 - SOME TESTS FAILED")
        print("=" * 60)
        sys.exit(1)
