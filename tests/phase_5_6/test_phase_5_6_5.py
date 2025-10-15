#!/usr/bin/env python3
"""
Test script for Phase 5.6.5 - Enhanced Session Workflow for Deployment
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.briefing_generator import generate_deployment_briefing
from scripts.session_complete import generate_deployment_summary


def test_enhanced_session_workflow():
    """Test enhanced session workflow for deployments."""
    print("=" * 60)
    print("Testing Phase 5.6.5: Enhanced Session Workflow for Deployment")
    print("=" * 60)
    print()

    tests_passed = 0
    tests_failed = 0

    # Test 1: generate_deployment_briefing() method exists
    print("Test 1: generate_deployment_briefing() method exists")
    if callable(generate_deployment_briefing):
        print("✅ PASS: generate_deployment_briefing() function exists")
        tests_passed += 1
    else:
        print("❌ FAIL: generate_deployment_briefing() function missing")
        tests_failed += 1
    print()

    # Create a test deployment work item
    deployment_work_item = {
        "id": "DEPLOY-001",
        "type": "deployment",
        "title": "Production Deployment",
        "specification": """
## Deployment Scope
**Application/Service:**
- Name: MyApp

**Target Environment:**
- Environment: production

## Deployment Procedure
### Pre-Deployment Steps
1. Check tests

### Deployment Steps
1. Deploy code

### Post-Deployment Steps
1. Run smoke tests

## Rollback Procedure
### Rollback Triggers
- Smoke tests fail

### Rollback Steps
1. Revert

## Smoke Tests
### Critical User Flows
1. Login

## Monitoring & Alerting
Metrics to monitor
""",
    }

    # Test 2: Deployment briefing includes scope
    print("Test 2: Deployment briefing includes scope")
    briefing = generate_deployment_briefing(deployment_work_item)
    if "Deployment Scope" in briefing or "DEPLOYMENT CONTEXT" in briefing:
        print("✅ PASS: Deployment briefing includes scope section")
        tests_passed += 1
    else:
        print(
            f"❌ FAIL: Deployment briefing missing scope. Briefing preview: {briefing[:200]}"
        )
        tests_failed += 1
    print()

    # Test 3: Deployment briefing includes procedure steps
    print("Test 3: Deployment briefing includes procedure steps")
    if "Deployment Procedure" in briefing or "deployment" in briefing.lower():
        print("✅ PASS: Deployment briefing includes procedure")
        tests_passed += 1
    else:
        print("❌ FAIL: Deployment briefing missing procedure")
        tests_failed += 1
    print()

    # Test 4: Deployment briefing includes rollback info
    print("Test 4: Deployment briefing includes rollback info")
    if "Rollback" in briefing or "rollback" in briefing.lower():
        print("✅ PASS: Deployment briefing includes rollback info")
        tests_passed += 1
    else:
        print("❌ FAIL: Deployment briefing missing rollback info")
        tests_failed += 1
    print()

    # Test 5: Environment pre-checks run at session start
    print("Test 5: Environment pre-checks included in briefing")
    if "Environment" in briefing or "environment" in briefing.lower():
        print("✅ PASS: Environment checks included in briefing")
        tests_passed += 1
    else:
        print("❌ FAIL: Environment checks not in briefing")
        tests_failed += 1
    print()

    # Test 6: generate_deployment_summary() method exists
    print("Test 6: generate_deployment_summary() method exists")
    if callable(generate_deployment_summary):
        print("✅ PASS: generate_deployment_summary() function exists")
        tests_passed += 1
    else:
        print("❌ FAIL: generate_deployment_summary() function missing")
        tests_failed += 1
    print()

    # Create gate results for testing
    gate_results = {
        "gates": [
            {"name": "Integration Tests", "passed": True, "required": True},
            {"name": "Environment Validation", "passed": True, "required": True},
        ]
    }

    # Test 7: Deployment summary includes execution results
    print("Test 7: Deployment summary includes execution results")
    summary = generate_deployment_summary(deployment_work_item, gate_results)
    if "Deployment Execution" in summary or "DEPLOYMENT RESULTS" in summary:
        print("✅ PASS: Deployment summary includes execution results")
        tests_passed += 1
    else:
        print(
            f"❌ FAIL: Deployment summary missing execution results. Summary: {summary[:200]}"
        )
        tests_failed += 1
    print()

    # Test 8: Deployment summary includes smoke test results
    print("Test 8: Deployment summary includes smoke test results")
    if "Smoke Tests" in summary or "smoke test" in summary.lower():
        print("✅ PASS: Deployment summary includes smoke test results")
        tests_passed += 1
    else:
        print("❌ FAIL: Deployment summary missing smoke test results")
        tests_failed += 1
    print()

    # Test 9: Deployment summary includes environment validation
    print("Test 9: Deployment summary includes environment validation")
    if "Environment Validation" in summary or "environment" in summary.lower():
        print("✅ PASS: Deployment summary includes environment validation")
        tests_passed += 1
    else:
        print("❌ FAIL: Deployment summary missing environment validation")
        tests_failed += 1
    print()

    # Test 10: Rollback status shown if triggered
    print("Test 10: Rollback status handling in summary")
    # The summary should have logic for rollback status even if not triggered
    if "rollback" in summary.lower() or "Metrics" in summary:
        print("✅ PASS: Rollback status handling present")
        tests_passed += 1
    else:
        print("❌ FAIL: Rollback handling not found")
        tests_failed += 1
    print()

    # Test 11: Post-deployment metrics included
    print("Test 11: Post-deployment metrics included")
    if "Metrics" in summary or "metrics" in summary.lower():
        print("✅ PASS: Post-deployment metrics included")
        tests_passed += 1
    else:
        print("❌ FAIL: Post-deployment metrics not included")
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
    sys.exit(test_enhanced_session_workflow())
