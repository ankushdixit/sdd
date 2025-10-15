#!/usr/bin/env python3
"""
Test script for Phase 5.5.7 - Enhanced Session Workflow
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))
from scripts.briefing_generator import generate_integration_test_briefing, check_command_exists
from scripts.session_complete import generate_integration_test_summary


def test_integration_briefing():
    """Test integration test briefing generation."""
    print("=" * 60)
    print("Testing Phase 5.5.7: Enhanced Session Workflow - Briefing")
    print("=" * 60)
    print()

    tests_passed = 0
    tests_failed = 0

    # Test 1: Non-integration work item returns empty
    print("Test 1: Non-integration work item returns empty briefing")
    work_item = {
        "id": "FEAT-001",
        "type": "feature",
        "title": "Regular Feature"
    }

    briefing = generate_integration_test_briefing(work_item)
    if briefing == "":
        print("✅ PASS: Empty briefing for non-integration work item")
        tests_passed += 1
    else:
        print("❌ FAIL: Should return empty briefing")
        tests_failed += 1
    print()

    # Test 2: Integration work item generates briefing
    print("Test 2: Integration work item generates briefing")
    work_item = {
        "id": "INTEG-001",
        "type": "integration_test",
        "title": "Test API Integration",
        "scope": "Testing the integration between Service A and Service B components",
        "environment_requirements": {
            "services_required": ["service-a", "service-b", "postgres"],
            "compose_file": "docker-compose.integration.yml"
        },
        "test_scenarios": [
            {"name": "Happy path scenario", "description": "Test successful integration"},
            {"name": "Error handling", "description": "Test error scenarios"}
        ],
        "performance_benchmarks": {
            "response_time": {"p95": 500},
            "throughput": {"minimum": 100}
        },
        "api_contracts": [
            {"contract_file": "contracts/api-v1.yaml", "version": "1.0.0"}
        ]
    }

    briefing = generate_integration_test_briefing(work_item)

    if "## Integration Test Context" in briefing:
        print("✅ PASS: Integration briefing contains context section")
        tests_passed += 1
    else:
        print("❌ FAIL: Missing Integration Test Context section")
        tests_failed += 1
    print()

    # Test 3: Briefing includes scope
    print("Test 3: Briefing includes integration scope")
    if "Integration Scope" in briefing and "Service A and Service B" in briefing:
        print("✅ PASS: Briefing includes scope")
        tests_passed += 1
    else:
        print("❌ FAIL: Briefing should include scope")
        tests_failed += 1
    print()

    # Test 4: Briefing includes required services
    print("Test 4: Briefing includes required services")
    if "Required Services" in briefing and "service-a" in briefing:
        print("✅ PASS: Briefing includes required services")
        tests_passed += 1
    else:
        print("❌ FAIL: Briefing should include required services")
        tests_failed += 1
    print()

    # Test 5: Briefing includes test scenarios
    print("Test 5: Briefing includes test scenarios")
    if "Test Scenarios (2 total)" in briefing:
        print("✅ PASS: Briefing includes test scenarios count")
        tests_passed += 1
    else:
        print("❌ FAIL: Briefing should include test scenarios")
        tests_failed += 1
    print()

    # Test 6: Briefing includes performance requirements
    print("Test 6: Briefing includes performance requirements")
    if "Performance Requirements" in briefing and "p95 < 500ms" in briefing:
        print("✅ PASS: Briefing includes performance requirements")
        tests_passed += 1
    else:
        print("❌ FAIL: Briefing should include performance requirements")
        tests_failed += 1
    print()

    # Test 7: Briefing includes API contracts
    print("Test 7: Briefing includes API contracts")
    if "API Contracts (1 contracts)" in briefing:
        print("✅ PASS: Briefing includes API contracts")
        tests_passed += 1
    else:
        print("❌ FAIL: Briefing should include API contracts")
        tests_failed += 1
    print()

    # Test 8: Briefing includes pre-session checks
    print("Test 8: Briefing includes pre-session checks")
    if "Pre-Session Checks" in briefing and "Docker:" in briefing:
        print("✅ PASS: Briefing includes pre-session checks")
        tests_passed += 1
    else:
        print("❌ FAIL: Briefing should include pre-session checks")
        tests_failed += 1
    print()

    # Test 9: Check command exists utility
    print("Test 9: check_command_exists utility works")
    # Test with a command that likely exists
    python_exists = check_command_exists("python3") or check_command_exists("python")
    if isinstance(python_exists, bool):
        print("✅ PASS: check_command_exists returns boolean")
        tests_passed += 1
    else:
        print("❌ FAIL: check_command_exists should return boolean")
        tests_failed += 1
    print()

    print(f"Briefing tests: {tests_passed}/{tests_passed + tests_failed} passed")
    print()

    return tests_passed, tests_failed


def test_integration_summary():
    """Test integration test summary generation."""
    print("=" * 60)
    print("Testing Phase 5.5.7: Enhanced Session Workflow - Summary")
    print("=" * 60)
    print()

    tests_passed = 0
    tests_failed = 0

    # Test 1: Non-integration work item returns empty
    print("Test 1: Non-integration work item returns empty summary")
    work_item = {
        "id": "FEAT-001",
        "type": "feature",
        "title": "Regular Feature"
    }

    gate_results = {}
    summary = generate_integration_test_summary(work_item, gate_results)

    if summary == "":
        print("✅ PASS: Empty summary for non-integration work item")
        tests_passed += 1
    else:
        print("❌ FAIL: Should return empty summary")
        tests_failed += 1
    print()

    # Test 2: Integration work item generates summary
    print("Test 2: Integration work item generates summary")
    work_item = {
        "id": "INTEG-001",
        "type": "integration_test",
        "title": "Test API Integration"
    }

    gate_results = {
        "integration_tests": {
            "integration_tests": {
                "passed": 10,
                "failed": 1,
                "skipped": 2,
                "total_duration": 45.5
            },
            "performance_benchmarks": {
                "load_test": {
                    "latency": {
                        "p50": 80,
                        "p95": 450,
                        "p99": 900
                    },
                    "throughput": {
                        "requests_per_sec": 150
                    }
                },
                "regression_detected": False
            },
            "api_contracts": {
                "contracts_validated": 2,
                "breaking_changes": []
            }
        }
    }

    summary = generate_integration_test_summary(work_item, gate_results)

    if "## Integration Test Results" in summary:
        print("✅ PASS: Summary contains integration test results section")
        tests_passed += 1
    else:
        print("❌ FAIL: Missing Integration Test Results section")
        tests_failed += 1
    print()

    # Test 3: Summary includes test counts
    print("Test 3: Summary includes test counts")
    if "Passed: 10" in summary and "Failed: 1" in summary:
        print("✅ PASS: Summary includes test counts")
        tests_passed += 1
    else:
        print("❌ FAIL: Summary should include test counts")
        tests_failed += 1
    print()

    # Test 4: Summary includes performance metrics
    print("Test 4: Summary includes performance metrics")
    if "Performance Benchmarks" in summary and "p50 latency: 80ms" in summary:
        print("✅ PASS: Summary includes performance metrics")
        tests_passed += 1
    else:
        print("❌ FAIL: Summary should include performance metrics")
        tests_failed += 1
    print()

    # Test 5: Summary includes API contract validation
    print("Test 5: Summary includes API contract validation")
    if "API Contract Validation" in summary and "Contracts validated: 2" in summary:
        print("✅ PASS: Summary includes API contract validation")
        tests_passed += 1
    else:
        print("❌ FAIL: Summary should include API contract validation")
        tests_failed += 1
    print()

    # Test 6: Summary shows no breaking changes
    print("Test 6: Summary shows no breaking changes")
    if "No breaking changes" in summary:
        print("✅ PASS: Summary shows no breaking changes")
        tests_passed += 1
    else:
        print("❌ FAIL: Summary should show no breaking changes")
        tests_failed += 1
    print()

    # Test 7: Summary with breaking changes
    print("Test 7: Summary highlights breaking changes")
    gate_results_with_breaks = {
        "integration_tests": {
            "integration_tests": {},
            "performance_benchmarks": {},
            "api_contracts": {
                "contracts_validated": 2,
                "breaking_changes": [
                    {"message": "Endpoint removed: /users"},
                    {"message": "Required parameter added: email"}
                ]
            }
        }
    }

    summary_breaks = generate_integration_test_summary(work_item, gate_results_with_breaks)
    if "Breaking changes detected: 2" in summary_breaks:
        print("✅ PASS: Summary highlights breaking changes")
        tests_passed += 1
    else:
        print("❌ FAIL: Summary should highlight breaking changes")
        tests_failed += 1
    print()

    # Test 8: Summary with performance regression
    print("Test 8: Summary highlights performance regression")
    gate_results_regression = {
        "integration_tests": {
            "integration_tests": {},
            "performance_benchmarks": {
                "load_test": {
                    "latency": {"p50": 150},
                    "throughput": {}
                },
                "regression_detected": True
            },
            "api_contracts": {}
        }
    }

    summary_regression = generate_integration_test_summary(work_item, gate_results_regression)
    if "Performance regression detected" in summary_regression:
        print("✅ PASS: Summary highlights performance regression")
        tests_passed += 1
    else:
        print("❌ FAIL: Summary should highlight performance regression")
        tests_failed += 1
    print()

    print(f"Summary tests: {tests_passed}/{tests_passed + tests_failed} passed")
    print()

    return tests_passed, tests_failed


def test_file_enhancements():
    """Test that files were enhanced correctly."""
    print("=" * 60)
    print("Testing File Enhancements")
    print("=" * 60)
    print()

    tests_passed = 0
    tests_failed = 0

    # Test 1: briefing_generator.py has integration function
    print("Test 1: briefing_generator.py has integration function")
    briefing_file = Path("scripts/briefing_generator.py")
    if briefing_file.exists():
        content = briefing_file.read_text()
        if "def generate_integration_test_briefing" in content:
            print("✅ PASS: Integration briefing function exists")
            tests_passed += 1
        else:
            print("❌ FAIL: Integration briefing function not found")
            tests_failed += 1
    else:
        print("❌ FAIL: briefing_generator.py not found")
        tests_failed += 1
    print()

    # Test 2: briefing_generator.py has check_command_exists
    print("Test 2: briefing_generator.py has check_command_exists")
    if "def check_command_exists" in content:
        print("✅ PASS: check_command_exists function exists")
        tests_passed += 1
    else:
        print("❌ FAIL: check_command_exists function not found")
        tests_failed += 1
    print()

    # Test 3: briefing_generator.py calls integration briefing
    print("Test 3: briefing_generator.py calls integration briefing")
    if "generate_integration_test_briefing(item)" in content:
        print("✅ PASS: Integration briefing is called")
        tests_passed += 1
    else:
        print("❌ FAIL: Integration briefing not called in generate_briefing")
        tests_failed += 1
    print()

    # Test 4: session_complete.py has integration summary function
    print("Test 4: session_complete.py has integration summary function")
    session_file = Path("scripts/session_complete.py")
    if session_file.exists():
        content = session_file.read_text()
        if "def generate_integration_test_summary" in content:
            print("✅ PASS: Integration summary function exists")
            tests_passed += 1
        else:
            print("❌ FAIL: Integration summary function not found")
            tests_failed += 1
    else:
        print("❌ FAIL: session_complete.py not found")
        tests_failed += 1
    print()

    # Test 5: session_complete.py calls integration summary
    print("Test 5: session_complete.py calls integration summary")
    if "generate_integration_test_summary(work_item, gate_results)" in content:
        print("✅ PASS: Integration summary is called")
        tests_passed += 1
    else:
        print("❌ FAIL: Integration summary not called in generate_summary")
        tests_failed += 1
    print()

    print(f"File enhancement tests: {tests_passed}/{tests_passed + tests_failed} passed")
    print()

    return tests_passed, tests_failed


if __name__ == "__main__":
    print()
    print("#" * 60)
    print("# Phase 5.5.7 Test Suite")
    print("# Enhanced Session Workflow")
    print("#" * 60)
    print()

    total_passed = 0
    total_failed = 0

    # File enhancement tests
    passed, failed = test_file_enhancements()
    total_passed += passed
    total_failed += failed
    print()

    # Integration briefing tests
    passed, failed = test_integration_briefing()
    total_passed += passed
    total_failed += failed
    print()

    # Integration summary tests
    passed, failed = test_integration_summary()
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
        print("✅ Phase 5.5.7 - ALL TESTS PASSED")
        print("=" * 60)
        sys.exit(0)
    else:
        print("=" * 60)
        print("❌ Phase 5.5.7 - SOME TESTS FAILED")
        print("=" * 60)
        sys.exit(1)
