#!/usr/bin/env python3
"""
Test script for Phase 5.6.1 - Enhanced Deployment Work Item Type

Updated for Phase 5.7 spec-first architecture.
"""

import shutil
import sys
import tempfile
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

from scripts.work_item_manager import WorkItemManager  # noqa: E402


class TestPhase5_6_1:
    """Test suite for Phase 5.6.1."""

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

    def test_deployment_template(self):
        """Test: Deployment template has all required sections."""
        template_path = project_root / "templates" / "deployment_spec.md"

        if not template_path.exists():
            print("❌ Template file not found")
            return False

        template_content = template_path.read_text()

        required_sections = [
            "## Deployment Scope",
            "## Deployment Procedure",
            "### Pre-Deployment Checklist",
            "### Deployment Steps",
            "### Post-Deployment Steps",
            "## Rollback Procedure",
            "### Rollback Triggers",
            "## Smoke Tests",
            "## Acceptance Criteria",
        ]

        print("=" * 60)
        print("Testing Deployment Template")
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
            print(f"❌ Template missing {len(required_sections) - sections_found} section(s)")
            return False

    def test_valid_deployment(self):
        """Test: Valid deployment spec validates successfully."""
        work_item_id = "DEPLOY-001"
        spec_content = """# Deployment: Production Release v2.0

## Deployment Scope

**Application/Service:**
- Name: MyApp
- Version: 2.0.0

**Target Environment:**
- Environment: production
- Cloud Provider: AWS

## Deployment Procedure

### Pre-Deployment Checklist
- [ ] Verify all integration tests passed
- [ ] Verify security scans passed
- [ ] Backup database

### Deployment Steps
1. Pull latest code from main branch
2. Build artifacts using CI/CD
3. Deploy to production environment
4. Run database migrations

### Post-Deployment Steps
- [ ] Run smoke tests
- [ ] Verify monitoring dashboards
- [ ] Update deployment log

## Environment Configuration

**Required Environment Variables:**
- DATABASE_URL=postgresql://prod.example.com/db
- API_KEY=<secure>

## Rollback Procedure

### Rollback Triggers
- Smoke tests fail
- Error rate exceeds 5%
- Critical functionality broken

### Rollback Steps
1. Stop current deployment
2. Revert to previous version
3. Verify rollback successful
4. Investigate issues

## Smoke Tests

### Test 1: Health Check
```bash
curl https://api.example.com/health
# Expected: {"status": "ok"}
```

### Test 2: User Login
```bash
curl -X POST https://api.example.com/auth/login
# Expected: 200 OK
```

## Monitoring & Alerting
- Monitor error rates
- Set up alerts for failures

## Acceptance Criteria
- [ ] Deployment completes successfully
- [ ] All smoke tests pass
- [ ] No increase in error rate
- [ ] Rollback procedure tested
"""

        self.create_spec_file(work_item_id, spec_content)

        manager = WorkItemManager(project_root=Path(self.temp_dir))

        work_item = {
            "id": work_item_id,
            "type": "deployment",
            "title": "Production Deployment v2.0",
        }

        is_valid, errors = manager.validate_deployment(work_item)

        if is_valid:
            print("✅ PASS: Valid deployment spec accepted")
            return True
        else:
            print(f"❌ FAIL: Valid spec rejected: {errors}")
            return False

    def test_incomplete_deployment(self):
        """Test: Incomplete deployment spec fails validation."""
        work_item_id = "DEPLOY-002"
        spec_content = """# Deployment: Incomplete Deployment

## Deployment Scope
Just a scope, missing other required sections.
"""

        self.create_spec_file(work_item_id, spec_content)

        manager = WorkItemManager(project_root=Path(self.temp_dir))

        work_item = {
            "id": work_item_id,
            "type": "deployment",
            "title": "Incomplete Deployment",
        }

        is_valid, errors = manager.validate_deployment(work_item)

        if not is_valid and len(errors) > 0:
            print(f"✅ PASS: Incomplete spec rejected with {len(errors)} errors")
            return True
        else:
            print("❌ FAIL: Incomplete spec should fail validation")
            return False


def run_all_tests():
    """Run all tests and report results."""
    test_instance = TestPhase5_6_1()

    print("=" * 60)
    print("Testing Phase 5.6.1: Enhanced Deployment Work Item Type")
    print("=" * 60)
    print()

    tests = [
        test_instance.test_deployment_template,
        test_instance.test_valid_deployment,
        test_instance.test_incomplete_deployment,
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
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests passed: {passed}")
    print(f"Tests failed: {failed}")
    print(f"Total tests: {len(tests)}")
    print()

    if failed == 0:
        print("✅ All tests passed!")
        return True
    else:
        print(f"❌ {failed} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
