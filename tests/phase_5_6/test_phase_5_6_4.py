#!/usr/bin/env python3
"""
Test script for Phase 5.6.4 - Deployment Quality Gates
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.quality_gates import QualityGates


def test_deployment_quality_gates():
    """Test deployment quality gates functionality."""
    print("=" * 60)
    print("Testing Phase 5.6.4: Deployment Quality Gates")
    print("=" * 60)
    print()

    tests_passed = 0
    tests_failed = 0

    # Test 1: run_deployment_gates() method exists
    print("Test 1: run_deployment_gates() method exists")
    gates = QualityGates()
    if hasattr(gates, "run_deployment_gates"):
        print("✅ PASS: run_deployment_gates() method exists")
        tests_passed += 1
    else:
        print("❌ FAIL: run_deployment_gates() method missing")
        tests_failed += 1
    print()

    # Create a test work item with complete deployment spec
    work_item = {
        "id": "DEPLOY-001",
        "type": "deployment",
        "title": "Production Deployment",
        "specification": """
## Deployment Procedure
### Deployment Steps
1. Deploy

## Rollback Procedure
### Rollback Steps
1. Rollback

## Smoke Tests
### Critical User Flows
1. Login

## Monitoring & Alerting
Metrics to monitor
""",
    }

    # Test 2: Integration tests gate exists
    print("Test 2: Integration tests gate works")
    passed, results = gates.run_deployment_gates(work_item)
    integration_gate = next(
        (g for g in results["gates"] if g["name"] == "Integration Tests"), None
    )
    if integration_gate:
        print("✅ PASS: Integration tests gate found")
        tests_passed += 1
    else:
        print(
            f"❌ FAIL: Integration tests gate not found. Gates: {[g['name'] for g in results['gates']]}"
        )
        tests_failed += 1
    print()

    # Test 3: Security scans gate exists
    print("Test 3: Security scans gate works")
    security_gate = next(
        (g for g in results["gates"] if g["name"] == "Security Scans"), None
    )
    if security_gate:
        print("✅ PASS: Security scans gate found")
        tests_passed += 1
    else:
        print(
            f"❌ FAIL: Security scans gate not found. Gates: {[g['name'] for g in results['gates']]}"
        )
        tests_failed += 1
    print()

    # Test 4: Environment validation gate exists
    print("Test 4: Environment validation gate works")
    env_gate = next(
        (g for g in results["gates"] if g["name"] == "Environment Validation"), None
    )
    if env_gate:
        print("✅ PASS: Environment validation gate found")
        tests_passed += 1
    else:
        print(
            f"❌ FAIL: Environment validation gate not found. Gates: {[g['name'] for g in results['gates']]}"
        )
        tests_failed += 1
    print()

    # Test 5: Deployment documentation gate exists
    print("Test 5: Deployment documentation gate works")
    docs_gate = next(
        (g for g in results["gates"] if g["name"] == "Deployment Documentation"), None
    )
    if docs_gate:
        print("✅ PASS: Deployment documentation gate found")
        tests_passed += 1
    else:
        print(
            f"❌ FAIL: Deployment documentation gate not found. Gates: {[g['name'] for g in results['gates']]}"
        )
        tests_failed += 1
    print()

    # Test 6: Rollback tested gate exists
    print("Test 6: Rollback tested gate works")
    rollback_gate = next(
        (g for g in results["gates"] if g["name"] == "Rollback Tested"), None
    )
    if rollback_gate:
        print("✅ PASS: Rollback tested gate found")
        tests_passed += 1
    else:
        print(
            f"❌ FAIL: Rollback tested gate not found. Gates: {[g['name'] for g in results['gates']]}"
        )
        tests_failed += 1
    print()

    # Test 7: All gates must pass for deployment
    print("Test 7: All gates are marked as required")
    all_required = all(g["required"] for g in results["gates"])
    if all_required:
        print("✅ PASS: All deployment gates are required")
        tests_passed += 1
    else:
        optional_gates = [g["name"] for g in results["gates"] if not g["required"]]
        print(f"❌ FAIL: Some gates are not required: {optional_gates}")
        tests_failed += 1
    print()

    # Test 8: Gate results formatted clearly
    print("Test 8: Gate results formatted clearly")
    required_keys = ["gates", "passed"]
    has_keys = all(key in results for key in required_keys)

    gate_has_structure = all(
        all(k in gate for k in ["name", "required", "passed"])
        for gate in results.get("gates", [])
    )

    if has_keys and gate_has_structure:
        print("✅ PASS: Gate results have clear structure")
        tests_passed += 1
    else:
        print(f"❌ FAIL: Gate results missing structure. Keys: {results.keys()}")
        if results.get("gates"):
            print(f"  Gate keys: {results['gates'][0].keys()}")
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
    sys.exit(test_deployment_quality_gates())
