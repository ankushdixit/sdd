#!/usr/bin/env python3
"""
Test script for Phase 5.5.1 - Enhanced Integration Test Work Item Type

Updated for Phase 5.7 spec-first architecture.
"""

import sys
import tempfile
import shutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

from scripts.work_item_manager import WorkItemManager  # noqa: E402


class TestPhase5_5_1:
    """Test suite for Phase 5.5.1."""

    def setup_method(self):
        """Setup test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_dir = Path.cwd()
        import os

        os.chdir(self.temp_dir)

        # Create directory structure
        self.session_dir = Path(self.temp_dir) / ".session"
        self.specs_dir = self.session_dir / "specs"
        self.tracking_dir = self.session_dir / "tracking"

        self.specs_dir.mkdir(parents=True)
        self.tracking_dir.mkdir(parents=True)

    def teardown_method(self):
        """Cleanup test fixtures."""
        import os

        os.chdir(self.original_dir)
        shutil.rmtree(self.temp_dir)

    def create_spec_file(self, work_item_id: str, content: str):
        """Helper to create a spec file."""
        spec_path = self.specs_dir / f"{work_item_id}.md"
        spec_path.write_text(content, encoding="utf-8")

    def test_integration_test_template(self):
        """Test: Integration test template has all required sections."""
        template_path = project_root / "templates" / "integration_test_spec.md"

        if not template_path.exists():
            print("❌ Template file not found")
            return False

        template_content = template_path.read_text()

        required_sections = [
            "## Scope",
            "## Test Scenarios",
            "## Performance Benchmarks",
            "## API Contracts",
            "## Environment Requirements",
            "## Dependencies",
            "## Acceptance Criteria",
        ]

        print("=" * 60)
        print("Testing Integration Test Template")
        print("=" * 60)
        print()

        sections_found = 0
        for section in required_sections:
            if section in template_content:
                print(f"✅ Found: {section}")
                sections_found += 1
            else:
                print(f"❌ Missing: {section}")

        print()
        print(f"Template sections found: {sections_found}/{len(required_sections)}")
        print()

        if sections_found == len(required_sections):
            print("✅ Template has all required sections!")
            return True
        else:
            print(
                f"❌ Template missing {len(required_sections) - sections_found} section(s)"
            )
            return False

    def test_valid_integration_test(self):
        """Test: Valid integration test spec validates successfully."""
        work_item_id = "INTEG-001"
        spec_content = """# Integration_Test: Test Service A to B Integration

## Scope
Test the integration between Service A and Service B API.

**Components:**
- Service A
- Service B

**Integration Points:**
- REST API endpoints
- Message queue

## Test Scenarios

### Scenario 1: Happy path
**Setup:**
- Services running
- Database seeded

**Actions:**
1. Send request to Service A
2. Verify response from Service B

**Expected Results:**
- HTTP 200
- Correct data returned

## Performance Benchmarks

**Response Time Requirements:**
- P50: < 100ms
- P95: < 500ms

**Throughput Requirements:**
- Min: 100 req/s
- Target: 500 req/s

## API Contracts
- contracts/service-a-to-b.yaml (v1.0.0)

## Environment Requirements

**Services Required:**
- service-a
- service-b
- postgres

**Configuration:**
- DATABASE_URL=postgres://localhost/test

## Dependencies

**Work Item Dependencies:**
- FEAT-001
- FEAT-002

## Acceptance Criteria
- [ ] All test scenarios pass
- [ ] Performance benchmarks met
- [ ] API contracts validated
"""

        self.create_spec_file(work_item_id, spec_content)

        manager = WorkItemManager(project_root=Path(self.temp_dir))

        work_item = {
            "id": work_item_id,
            "type": "integration_test",
            "title": "Test Service A to B Integration",
            "dependencies": [
                "FEAT-001",
                "FEAT-002",
            ],  # Integration tests need component dependencies
        }

        is_valid, errors = manager.validate_integration_test(work_item)

        if is_valid:
            print("✅ PASS: Valid integration test spec accepted")
            return True
        else:
            print(f"❌ FAIL: Valid spec rejected: {errors}")
            return False

    def test_incomplete_integration_test(self):
        """Test: Incomplete integration test spec fails validation."""
        work_item_id = "INTEG-002"
        spec_content = """# Integration_Test: Incomplete Test

## Scope
Just a scope, missing other sections.
"""

        self.create_spec_file(work_item_id, spec_content)

        manager = WorkItemManager(project_root=Path(self.temp_dir))

        work_item = {
            "id": work_item_id,
            "type": "integration_test",
            "title": "Incomplete Test",
        }

        is_valid, errors = manager.validate_integration_test(work_item)

        if not is_valid and len(errors) > 0:
            print(f"✅ PASS: Incomplete spec rejected with {len(errors)} errors")
            return True
        else:
            print("❌ FAIL: Incomplete spec should fail validation")
            return False


def run_all_tests():
    """Run all tests and report results."""
    test_instance = TestPhase5_5_1()

    print("=" * 60)
    print("Testing Phase 5.5.1: Enhanced Integration Test Work Item Type")
    print("=" * 60)
    print()

    tests = [
        test_instance.test_integration_test_template,
        test_instance.test_valid_integration_test,
        test_instance.test_incomplete_integration_test,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_instance.setup_method()
            if test_func():
                passed += 1
            else:
                failed += 1
            test_instance.teardown_method()
        except Exception as e:
            print(f"❌ {test_func.__name__} errored: {e}")
            import traceback

            traceback.print_exc()
            test_instance.teardown_method()
            failed += 1
        print()

    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Tests Passed: {passed}")
    print(f"Tests Failed: {failed}")
    print(f"Total Tests: {len(tests)}")
    print()

    if failed == 0:
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        return True
    else:
        print(f"❌ {failed} TEST(S) FAILED")
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
