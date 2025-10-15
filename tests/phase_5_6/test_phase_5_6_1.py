#!/usr/bin/env python3
"""
Test script for Phase 5.6.1 - Enhanced Deployment Work Item Type
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.work_item_manager import WorkItemManager


def test_deployment_validation():
    """Test the validate_deployment method."""
    manager = WorkItemManager()

    print("=" * 60)
    print("Testing Phase 5.6.1: Enhanced Deployment Work Item Type")
    print("=" * 60)
    print()

    tests_passed = 0
    tests_failed = 0

    # Test 1: Valid deployment work item
    print("Test 1: Valid deployment work item")
    valid_spec = """
# Deployment: Production Release

## Deployment Scope
**Application/Service:**
- Name: MyApp
- Version: 2.0.0

**Target Environment:**
- Environment: production
- Cloud Provider: AWS

## Deployment Procedure

### Pre-Deployment Steps
1. Verify all integration tests passed
2. Verify security scans passed

### Deployment Steps
1. Pull latest code
2. Build artifacts

### Post-Deployment Steps
1. Run smoke tests
2. Verify monitoring

## Environment Configuration
**Required Environment Variables:**
DATABASE_URL=postgresql://...

## Rollback Procedure

### Rollback Triggers
- Smoke tests fail
- Error rate exceeds 5%

### Rollback Steps
1. Stop deployment
2. Revert to previous version

## Smoke Tests

### Critical User Flows
1. User Login

### Health Checks
- Application health: GET /health
"""

    valid_work_item = {
        "id": "DEPLOY-001",
        "type": "deployment",
        "title": "Production Deployment v2.0",
        "specification": valid_spec
    }

    is_valid, errors = manager.validate_deployment(valid_work_item)
    if is_valid:
        print("✅ PASS: Valid deployment work item accepted")
        tests_passed += 1
    else:
        print(f"❌ FAIL: Valid deployment rejected: {errors}")
        tests_failed += 1
    print()

    # Test 2: Missing deployment scope
    print("Test 2: Missing deployment scope")
    spec_no_scope = valid_spec.replace("## Deployment Scope", "## Scope")
    item = {"id": "DEPLOY-002", "type": "deployment", "specification": spec_no_scope}
    is_valid, errors = manager.validate_deployment(item)
    if not is_valid and any("deployment scope" in e.lower() for e in errors):
        print("✅ PASS: Missing deployment scope detected")
        tests_passed += 1
    else:
        print(f"❌ FAIL: Missing deployment scope not detected. Errors: {errors}")
        tests_failed += 1
    print()

    # Test 3: Missing deployment procedure
    print("Test 3: Missing deployment procedure")
    spec_no_procedure = valid_spec.replace("## Deployment Procedure", "## Procedure")
    item = {"id": "DEPLOY-003", "type": "deployment", "specification": spec_no_procedure}
    is_valid, errors = manager.validate_deployment(item)
    if not is_valid and any("deployment procedure" in e.lower() for e in errors):
        print("✅ PASS: Missing deployment procedure detected")
        tests_passed += 1
    else:
        print(f"❌ FAIL: Missing deployment procedure not detected. Errors: {errors}")
        tests_failed += 1
    print()

    # Test 4: Missing pre-deployment steps
    print("Test 4: Missing pre-deployment steps")
    spec_no_pre = valid_spec.replace("### Pre-Deployment Steps", "### Pre Steps")
    item = {"id": "DEPLOY-004", "type": "deployment", "specification": spec_no_pre}
    is_valid, errors = manager.validate_deployment(item)
    if not is_valid and any("pre-deployment steps" in e.lower() for e in errors):
        print("✅ PASS: Missing pre-deployment steps detected")
        tests_passed += 1
    else:
        print(f"❌ FAIL: Missing pre-deployment steps not detected. Errors: {errors}")
        tests_failed += 1
    print()

    # Test 5: Missing deployment steps
    print("Test 5: Missing deployment steps")
    spec_no_deploy = valid_spec.replace("### Deployment Steps\n1. Pull latest code\n2. Build artifacts", "")
    item = {"id": "DEPLOY-005", "type": "deployment", "specification": spec_no_deploy}
    is_valid, errors = manager.validate_deployment(item)
    if not is_valid and any("deployment steps" in e.lower() for e in errors):
        print("✅ PASS: Missing deployment steps detected")
        tests_passed += 1
    else:
        print(f"❌ FAIL: Missing deployment steps not detected. Errors: {errors}")
        tests_failed += 1
    print()

    # Test 6: Missing post-deployment steps
    print("Test 6: Missing post-deployment steps")
    spec_no_post = valid_spec.replace("### Post-Deployment Steps", "### Post Steps")
    item = {"id": "DEPLOY-006", "type": "deployment", "specification": spec_no_post}
    is_valid, errors = manager.validate_deployment(item)
    if not is_valid and any("post-deployment steps" in e.lower() for e in errors):
        print("✅ PASS: Missing post-deployment steps detected")
        tests_passed += 1
    else:
        print(f"❌ FAIL: Missing post-deployment steps not detected. Errors: {errors}")
        tests_failed += 1
    print()

    # Test 7: Missing rollback procedure
    print("Test 7: Missing rollback procedure")
    spec_no_rollback = valid_spec.replace("## Rollback Procedure", "## Rollback")
    item = {"id": "DEPLOY-007", "type": "deployment", "specification": spec_no_rollback}
    is_valid, errors = manager.validate_deployment(item)
    if not is_valid and any("rollback procedure" in e.lower() for e in errors):
        print("✅ PASS: Missing rollback procedure detected")
        tests_passed += 1
    else:
        print(f"❌ FAIL: Missing rollback procedure not detected. Errors: {errors}")
        tests_failed += 1
    print()

    # Test 8: Missing rollback triggers
    print("Test 8: Missing rollback triggers")
    spec_no_triggers = valid_spec.replace("### Rollback Triggers", "### Triggers")
    item = {"id": "DEPLOY-008", "type": "deployment", "specification": spec_no_triggers}
    is_valid, errors = manager.validate_deployment(item)
    if not is_valid and any("rollback triggers" in e.lower() for e in errors):
        print("✅ PASS: Missing rollback triggers detected")
        tests_passed += 1
    else:
        print(f"❌ FAIL: Missing rollback triggers not detected. Errors: {errors}")
        tests_failed += 1
    print()

    # Test 9: Missing smoke tests
    print("Test 9: Missing smoke tests")
    # Remove the entire smoke tests section
    smoke_section = """## Smoke Tests

### Critical User Flows
1. User Login

### Health Checks
- Application health: GET /health"""
    spec_no_smoke = valid_spec.replace(smoke_section, "")
    item = {"id": "DEPLOY-009", "type": "deployment", "specification": spec_no_smoke}
    is_valid, errors = manager.validate_deployment(item)
    if not is_valid and any("smoke test" in e.lower() for e in errors):
        print("✅ PASS: Missing smoke tests detected")
        tests_passed += 1
    else:
        print(f"❌ FAIL: Missing smoke tests not detected. Errors: {errors}")
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
    sys.exit(test_deployment_validation())
