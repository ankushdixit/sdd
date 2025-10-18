#!/usr/bin/env python3
"""
Test script for Phase 5.7.3 - Update Validators & Runners

Tests updated validators, runners, quality gates, and session tools
that now use spec_parser instead of deprecated JSON fields.
"""

import sys
from pathlib import Path
import tempfile
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.work_item_manager import WorkItemManager # noqa: E402
from scripts.integration_test_runner import IntegrationTestRunner # noqa: E402


def create_test_spec_file(spec_dir, work_id, spec_type, content):
    """Helper to create a test spec file."""
    spec_file = spec_dir / f"{work_id}.md"
    spec_file.write_text(content)
    return spec_file


def test_validate_integration_test_valid():
    """Test 1: validate_integration_test() with valid spec"""
    print("\n" + "=" * 60)
    print("Test 1: validate_integration_test() - Valid Spec")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        specs_dir = Path(tmpdir) / ".session" / "specs"
        specs_dir.mkdir(parents=True)

        # Create valid integration test spec
        spec_content = """# integration_test: Order Processing Flow

## Scope
Test the complete order processing workflow from creation to completion.

## Test Scenarios

### Scenario 1: Successful Order
User places an order and receives confirmation.

### Scenario 2: Payment Failure
User's payment fails and order is cancelled.

## Performance Benchmarks
- Response Time: < 200ms
- Throughput: 100 orders/second

## API Contracts
Order API v2.0 contracts documented in docs/api-contracts/

## Environment Requirements
- PostgreSQL 14
- Redis 6.2
- Node.js 18

## Acceptance Criteria
- [ ] All scenarios pass
- [ ] Performance benchmarks met
- [ ] Integration points documented

## Dependencies
feature_001

## Estimated Effort
2 sessions
"""
        create_test_spec_file(
            specs_dir, "integration_test_001", "integration_test", spec_content
        )

        original_dir = os.getcwd()
        try:
            os.chdir(tmpdir)
            manager = WorkItemManager()

            work_item = {
                "id": "integration_test_001",
                "type": "integration_test",
                "title": "Order Processing Flow",
                "dependencies": ["feature_001"],
            }

            is_valid, errors = manager.validate_integration_test(work_item)

            assert is_valid, f"Expected valid, got errors: {errors}"
            assert len(errors) == 0

            print("✓ Valid integration test spec validated successfully")
            return True
        finally:
            os.chdir(original_dir)


def test_validate_integration_test_invalid():
    """Test 2: validate_integration_test() with invalid spec"""
    print("\n" + "=" * 60)
    print("Test 2: validate_integration_test() - Invalid Spec")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        specs_dir = Path(tmpdir) / ".session" / "specs"
        specs_dir.mkdir(parents=True)

        # Create invalid integration test spec (missing sections)
        spec_content = """# integration_test: Incomplete Test

## Scope
Some scope here.

## Acceptance Criteria
- [ ] First criterion
- [ ] Second criterion
"""
        create_test_spec_file(
            specs_dir, "integration_test_002", "integration_test", spec_content
        )

        original_dir = os.getcwd()
        try:
            os.chdir(tmpdir)
            manager = WorkItemManager()

            work_item = {
                "id": "integration_test_002",
                "type": "integration_test",
                "title": "Incomplete Test",
                "dependencies": [],
            }

            is_valid, errors = manager.validate_integration_test(work_item)

            assert not is_valid, "Expected invalid spec"
            assert len(errors) > 0
            # Should have errors for missing sections and dependencies
            assert any("Test Scenarios" in str(e) for e in errors)

            print(f"✓ Invalid spec detected with {len(errors)} errors")
            return True
        finally:
            os.chdir(original_dir)


def test_validate_deployment_valid():
    """Test 3: validate_deployment() with valid spec"""
    print("\n" + "=" * 60)
    print("Test 3: validate_deployment() - Valid Spec")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        specs_dir = Path(tmpdir) / ".session" / "specs"
        specs_dir.mkdir(parents=True)

        # Create valid deployment spec
        spec_content = """# deployment: Production Release v2.0

## Deployment Scope
**Application:** Order API
**Version:** 2.0.0

## Deployment Procedure

### Pre-Deployment Checklist
- [ ] Backup database
- [ ] Notify stakeholders

### Deployment Steps
1. Pull latest code
2. Deploy to production

### Post-Deployment Steps
1. Run smoke tests
2. Verify metrics

## Environment Configuration
DATABASE_URL=postgresql://prod.db
REDIS_URL=redis://cache

## Rollback Procedure

### Rollback Triggers
- Critical bugs detected
- Performance degradation

### Rollback Steps
1. Revert to previous version
2. Verify rollback successful

## Smoke Tests

### Test 1: Health Check
Check /health endpoint returns 200.

## Acceptance Criteria
- [ ] All smoke tests pass
- [ ] No critical errors
- [ ] Monitoring configured

## Dependencies
None

## Estimated Effort
1 session
"""
        create_test_spec_file(specs_dir, "deployment_001", "deployment", spec_content)

        original_dir = os.getcwd()
        try:
            os.chdir(tmpdir)
            manager = WorkItemManager()

            work_item = {
                "id": "deployment_001",
                "type": "deployment",
                "title": "Production Release v2.0",
            }

            is_valid, errors = manager.validate_deployment(work_item)

            assert is_valid, f"Expected valid, got errors: {errors}"
            assert len(errors) == 0

            print("✓ Valid deployment spec validated successfully")
            return True
        finally:
            os.chdir(original_dir)


def test_validate_deployment_invalid():
    """Test 4: validate_deployment() with invalid spec"""
    print("\n" + "=" * 60)
    print("Test 4: validate_deployment() - Invalid Spec")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        specs_dir = Path(tmpdir) / ".session" / "specs"
        specs_dir.mkdir(parents=True)

        # Create invalid deployment spec (missing sections)
        spec_content = """# deployment: Incomplete Deployment

## Deployment Scope
Some scope

## Acceptance Criteria
- [ ] Test 1
- [ ] Test 2
"""
        create_test_spec_file(specs_dir, "deployment_002", "deployment", spec_content)

        original_dir = os.getcwd()
        try:
            os.chdir(tmpdir)
            manager = WorkItemManager()

            work_item = {
                "id": "deployment_002",
                "type": "deployment",
                "title": "Incomplete Deployment",
            }

            is_valid, errors = manager.validate_deployment(work_item)

            assert not is_valid, "Expected invalid spec"
            assert len(errors) > 0
            # Should have errors for missing required sections
            assert any(
                "Deployment Procedure" in str(e)
                or "Rollback Procedure" in str(e)
                or "Smoke Tests" in str(e)
                for e in errors
            )

            print(f"✓ Invalid spec detected with {len(errors)} errors")
            return True
        finally:
            os.chdir(original_dir)


def test_integration_test_runner_with_spec():
    """Test 5: IntegrationTestRunner with spec parsing"""
    print("\n" + "=" * 60)
    print("Test 5: IntegrationTestRunner - Spec Parsing")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        specs_dir = Path(tmpdir) / ".session" / "specs"
        specs_dir.mkdir(parents=True)

        # Create integration test spec
        spec_content = """# integration_test: Runner Test

## Scope
Test runner functionality

## Test Scenarios

### Scenario 1: Basic Test
First test scenario

### Scenario 2: Advanced Test
Second test scenario

## Performance Benchmarks
Response time: < 100ms

## Environment Requirements
- PostgreSQL 14
- Redis 6.2

docker-compose.test.yml

## Acceptance Criteria
- [ ] Tests pass
- [ ] Performance met
- [ ] Environment setup works

## Dependencies
None

## Estimated Effort
1 session
"""
        create_test_spec_file(
            specs_dir, "integration_test_runner", "integration_test", spec_content
        )

        original_dir = os.getcwd()
        try:
            os.chdir(tmpdir)

            work_item = {"id": "integration_test_runner", "type": "integration_test"}

            runner = IntegrationTestRunner(work_item)

            assert len(runner.test_scenarios) == 2
            assert runner.test_scenarios[0]["name"] == "Scenario 1: Basic Test"
            assert runner.test_scenarios[1]["name"] == "Scenario 2: Advanced Test"
            # Environment requirements parsing is heuristic-based
            # Just verify it returns a dict with expected keys
            assert isinstance(runner.env_requirements, dict)
            assert "services_required" in runner.env_requirements
            assert "compose_file" in runner.env_requirements
            assert (
                runner.env_requirements.get("compose_file") == "docker-compose.test.yml"
            )

            print(f"✓ Runner parsed {len(runner.test_scenarios)} test scenarios")
            print(
                f"✓ Environment requirements structure: services_required={len(runner.env_requirements.get('services_required', []))}, compose_file={runner.env_requirements.get('compose_file')}"
            )
            return True
        finally:
            os.chdir(original_dir)


def test_integration_test_runner_missing_spec():
    """Test 6: IntegrationTestRunner with missing spec"""
    print("\n" + "=" * 60)
    print("Test 6: IntegrationTestRunner - Missing Spec")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        specs_dir = Path(tmpdir) / ".session" / "specs"
        specs_dir.mkdir(parents=True)

        original_dir = os.getcwd()
        try:
            os.chdir(tmpdir)

            work_item = {"id": "nonexistent_test", "type": "integration_test"}

            try:
                IntegrationTestRunner(work_item)
                print("✗ Should have raised ValueError for missing spec")
                return False
            except ValueError as e:
                assert "not found" in str(e).lower()
                print(f"✓ Correctly raised ValueError: {e}")
                return True
        finally:
            os.chdir(original_dir)


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "=" * 80)
    print("PHASE 5.7.3 - UPDATE VALIDATORS & RUNNERS - TEST SUITE")
    print("=" * 80)

    tests = [
        test_validate_integration_test_valid,
        test_validate_integration_test_invalid,
        test_validate_deployment_valid,
        test_validate_deployment_invalid,
        test_integration_test_runner_with_spec,
        test_integration_test_runner_missing_spec,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
                print(f"✗ {test.__name__} failed")
        except Exception as e:
            failed += 1
            print(f"✗ {test.__name__} raised exception: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed} ✓")
    print(f"Failed: {failed} ✗")
    print(f"Success rate: {(passed / len(tests) * 100):.1f}%")
    print("=" * 80)
    print("\nNOTE: Quality gates, session_validate, and session_complete tests")
    print("require more complex setup and are tested through integration tests.")
    print("=" * 80)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
