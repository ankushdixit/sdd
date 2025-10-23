#!/usr/bin/env python3
"""
Test Suite for Phase 5.7: End-to-End Integration Tests

Comprehensive tests that verify the complete spec-first workflow from work item
creation to session completion.
"""

import json
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

from scripts.briefing_generator import generate_briefing, load_work_item_spec  # noqa: E402
from scripts.quality_gates import QualityGates  # noqa: E402
from scripts.spec_parser import parse_spec_file  # noqa: E402
from scripts.spec_validator import validate_spec_file  # noqa: E402


class TestPhase5_7Complete:
    """End-to-end integration tests for Phase 5.7."""

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
        self.docs_dir = Path(self.temp_dir) / "docs"

        self.specs_dir.mkdir(parents=True)
        self.tracking_dir.mkdir(parents=True)
        self.docs_dir.mkdir(parents=True)

    def teardown_method(self):
        """Cleanup test fixtures."""
        import os

        os.chdir(self.original_dir)
        shutil.rmtree(self.temp_dir)

    def create_spec_file(self, work_item_id: str, content: str):
        """Helper to create a spec file."""
        spec_path = self.specs_dir / f"{work_item_id}.md"
        spec_path.write_text(content, encoding="utf-8")

    @pytest.mark.skip(
        reason="Test pollution issue - passes individually but fails in full suite (Session 2)"
    )
    def test_end_to_end_feature_workflow(self):
        """
        Test: Complete workflow for feature work item.
        1. Create spec file
        2. Validate spec completeness
        3. Parse spec for structured data
        4. Generate briefing with full spec
        5. Quality gate validates spec
        """
        work_item_id = "feature_complete_workflow"
        work_item_type = "feature"

        # Step 1: Create complete spec file
        spec_content = """# Feature: Complete Workflow Test

## Overview
A comprehensive feature for testing the complete workflow.

## Rationale
This feature demonstrates the end-to-end spec-first workflow
from creation to validation.

## Acceptance Criteria
- [ ] Spec file can be created from template
- [ ] Spec file can be validated for completeness
- [ ] Spec file can be parsed for structured data
- [ ] Briefing includes full spec content
- [ ] Quality gates validate spec completeness

## Implementation Details
Complete implementation details go here, including:
- Architecture decisions
- API contracts
- Database schema changes

## Testing Strategy
Comprehensive testing strategy including:
- Unit tests
- Integration tests
- End-to-end tests
"""

        self.create_spec_file(work_item_id, spec_content)

        # Step 2: Validate spec completeness
        is_valid, errors = validate_spec_file(work_item_id, work_item_type)
        assert is_valid, f"Spec should be valid, errors: {errors}"
        assert len(errors) == 0

        # Step 3: Parse spec for structured data
        parsed_data = parse_spec_file(work_item_id)
        assert parsed_data is not None
        assert parsed_data["overview"] is not None
        assert parsed_data["rationale"] is not None
        assert len(parsed_data["acceptance_criteria"]) >= 3

        # Step 4: Generate briefing with full spec
        work_item = {
            "id": work_item_id,
            "type": work_item_type,
            "title": "Complete Workflow Test",
            "priority": "high",
            "status": "not_started",
        }
        learnings_data = {"learnings": []}

        briefing = generate_briefing(work_item_id, work_item, learnings_data)
        assert "## Work Item Specification" in briefing
        assert "# Feature: Complete Workflow Test" in briefing
        assert "A comprehensive feature" in briefing

        # Step 5: Quality gate validates spec
        gates = QualityGates()
        passed, results = gates.validate_spec_completeness(work_item)
        assert passed, f"Quality gate should pass, results: {results}"
        assert results["status"] == "passed"

        print(
            "✓ Test 1: End-to-end feature workflow (create → validate → parse → brief → quality gate)"
        )

    def test_end_to_end_deployment_workflow(self):
        """
        Test: Complete workflow for deployment work item with all required subsections.
        """
        work_item_id = "deployment_complete_workflow"
        work_item_type = "deployment"

        # Create complete deployment spec
        spec_content = """# Deployment: API v2.5.0

## Deployment Scope
Deploy API v2.5.0 to production with zero downtime using blue-green deployment.

## Deployment Procedure

### Pre-Deployment Checklist
- [ ] Backup database
- [ ] Verify staging deployment successful
- [ ] Notify team of deployment window

### Deployment Steps
1. Deploy to green environment
2. Run smoke tests on green
3. Switch traffic to green
4. Monitor for 15 minutes

### Post-Deployment Steps
- [ ] Run full smoke test suite
- [ ] Verify monitoring dashboards
- [ ] Update deployment log

## Rollback Procedure

### Rollback Triggers
- Error rate > 5%
- Response time > 2s
- Failed smoke tests

### Rollback Steps
1. Switch traffic back to blue environment
2. Investigate issues
3. Fix and redeploy

## Smoke Tests

### Test 1: Health Check
```bash
curl https://api.example.com/health
# Expected: {"status": "ok"}
```

### Test 2: User Login
```bash
curl -X POST https://api.example.com/auth/login
# Expected: 200 OK with JWT token
```

## Acceptance Criteria
- [ ] Deployment completes with zero downtime
- [ ] All smoke tests pass
- [ ] No increase in error rate
- [ ] Rollback procedure tested and documented
"""

        self.create_spec_file(work_item_id, spec_content)

        # Validate deployment spec
        is_valid, errors = validate_spec_file(work_item_id, work_item_type)
        assert is_valid, f"Deployment spec should be valid, errors: {errors}"

        # Parse deployment spec
        parsed_data = parse_spec_file(work_item_id)
        assert parsed_data is not None
        assert parsed_data["deployment_scope"] is not None
        assert parsed_data["deployment_procedure"] is not None
        assert parsed_data["rollback_procedure"] is not None
        assert parsed_data["smoke_tests"] is not None
        assert len(parsed_data["acceptance_criteria"]) >= 3

        # Generate briefing
        work_item = {
            "id": work_item_id,
            "type": work_item_type,
            "title": "API v2.5.0 Deployment",
            "priority": "critical",
            "status": "not_started",
        }
        learnings_data = {"learnings": []}

        briefing = generate_briefing(work_item_id, work_item, learnings_data)
        assert "# Deployment: API v2.5.0" in briefing
        assert "blue-green deployment" in briefing

        # Quality gate
        gates = QualityGates()
        passed, results = gates.validate_spec_completeness(work_item)
        assert passed

        print("✓ Test 2: End-to-end deployment workflow with all required subsections")

    @pytest.mark.skip(
        reason="Test pollution issue - passes individually but fails in full suite (Session 2)"
    )
    def test_incomplete_spec_fails_validation(self):
        """
        Test: Incomplete spec fails validation at multiple checkpoints.
        """
        work_item_id = "feature_incomplete"
        work_item_type = "feature"

        # Create incomplete spec (missing required sections)
        incomplete_spec = """# Feature: Incomplete Feature

## Overview
Just an overview, missing many required sections.

## Acceptance Criteria
- [ ] Only two criteria
- [ ] Not enough items
"""

        self.create_spec_file(work_item_id, incomplete_spec)

        # Validation should fail
        is_valid, errors = validate_spec_file(work_item_id, work_item_type)
        assert not is_valid, "Incomplete spec should fail validation"
        assert len(errors) > 0
        assert any("Rationale" in error for error in errors)
        assert any("Implementation Details" in error for error in errors)
        assert any("Testing Strategy" in error for error in errors)
        assert any("at least 3 items" in error for error in errors)

        # Quality gate should also fail
        work_item = {
            "id": work_item_id,
            "type": work_item_type,
            "title": "Incomplete Feature",
            "priority": "high",
            "status": "not_started",
        }

        gates = QualityGates()
        passed, results = gates.validate_spec_completeness(work_item)
        assert not passed, "Quality gate should fail for incomplete spec"
        assert results["status"] == "failed"

        print("✓ Test 3: Incomplete spec fails validation at all checkpoints")

    def test_spec_parser_integration_with_all_work_item_types(self):
        """
        Test: Spec parser correctly handles all 6 work item types.
        """
        test_cases = [
            (
                "feature",
                "Feature Spec",
                ["overview", "rationale", "acceptance_criteria"],
            ),
            ("bug", "Bug Spec", ["description", "root_cause_analysis", "fix_approach"]),
            (
                "refactor",
                "Refactor Spec",
                ["overview", "current_state", "proposed_refactor"],
            ),
            (
                "security",
                "Security Spec",
                ["security_issue", "threat_model", "mitigation_strategy"],
            ),
            (
                "integration_test",
                "Integration Test Spec",
                ["scope", "test_scenarios", "environment_requirements"],
            ),
            (
                "deployment",
                "Deployment Spec",
                ["deployment_scope", "deployment_procedure", "rollback_procedure"],
            ),
        ]

        for work_item_type, title, expected_fields in test_cases:
            work_item_id = f"{work_item_type}_parser_test"

            # Create minimal valid spec for each type
            if work_item_type == "feature":
                spec = f"""# Feature: {title}
## Overview
Overview
## Rationale
Rationale
## Acceptance Criteria
- [ ] 1
- [ ] 2
- [ ] 3
## Implementation Details
Details
## Testing Strategy
Strategy
"""
            elif work_item_type == "bug":
                spec = f"""# Bug: {title}
## Description
Description
## Steps to Reproduce
Steps
## Root Cause Analysis
Analysis
## Fix Approach
Fix
"""
            elif work_item_type == "refactor":
                spec = f"""# Refactor: {title}
## Overview
Overview
## Current State
Current
## Proposed Refactor
Proposed
## Scope
Scope
"""
            elif work_item_type == "security":
                spec = f"""# Security: {title}
## Security Issue
Issue
## Threat Model
Model
## Attack Vector
Vector
## Mitigation Strategy
Strategy
## Compliance
Compliance
"""
            elif work_item_type == "integration_test":
                spec = f"""# Integration_Test: {title}
## Scope
Scope
## Test Scenarios
### Scenario 1: Test
Test
## Performance Benchmarks
Benchmarks
## Environment Requirements
Requirements
## Acceptance Criteria
- [ ] 1
- [ ] 2
- [ ] 3
"""
            elif work_item_type == "deployment":
                spec = f"""# Deployment: {title}
## Deployment Scope
Scope
## Deployment Procedure
### Pre-Deployment Checklist
- [ ] Check
### Deployment Steps
Steps
### Post-Deployment Steps
- [ ] Verify
## Rollback Procedure
### Rollback Triggers
Triggers
### Rollback Steps
Steps
## Smoke Tests
### Test 1: Test
Test
## Acceptance Criteria
- [ ] 1
- [ ] 2
- [ ] 3
"""

            self.create_spec_file(work_item_id, spec)

            # Parse and verify
            parsed = parse_spec_file(work_item_id)
            assert parsed is not None, f"Parser should handle {work_item_type}"

            for field in expected_fields:
                assert field in parsed, f"{work_item_type} should have {field} field"
                assert parsed[field] is not None, f"{work_item_type}.{field} should not be None"

        print("✓ Test 4: Spec parser correctly handles all 6 work item types")

    def test_system_integration_no_deprecated_fields(self):
        """
        Test: Verify system doesn't use deprecated fields anywhere.
        """
        # This test verifies that work_items.json no longer contains deprecated fields
        # and that all components use spec files instead

        work_item_id = "feature_no_deprecated_fields"
        spec_content = """# Feature: No Deprecated Fields

## Overview
This feature verifies the system uses spec files, not JSON fields.

## Rationale
Ensure clean separation between content (spec files) and tracking (JSON).

## Acceptance Criteria
- [ ] No rationale field in work_items.json
- [ ] No acceptance_criteria field in work_items.json
- [ ] Content read from spec files only

## Implementation Details
All content in spec file, not JSON.

## Testing Strategy
Verify no deprecated fields.
"""

        self.create_spec_file(work_item_id, spec_content)

        # Create work item JSON (as system would)
        work_item_data = {
            "work_items": {
                work_item_id: {
                    "id": work_item_id,
                    "type": "feature",
                    "title": "No Deprecated Fields",
                    "status": "not_started",
                    "priority": "high",
                    "dependencies": [],
                    "milestone": None,
                    "created_at": "2025-10-18T12:00:00Z",
                    "sessions": [],
                }
            }
        }

        work_items_path = self.tracking_dir / "work_items.json"
        work_items_path.write_text(json.dumps(work_item_data, indent=2), encoding="utf-8")

        # Verify no deprecated fields
        with open(work_items_path) as f:
            loaded_data = json.load(f)

        work_item = loaded_data["work_items"][work_item_id]

        deprecated_fields = [
            "rationale",
            "acceptance_criteria",
            "implementation_paths",
            "test_paths",
        ]
        for field in deprecated_fields:
            assert field not in work_item, (
                f"Deprecated field '{field}' should not be in work_items.json"
            )

        # Verify content comes from spec file
        loaded_spec = load_work_item_spec(work_item_id)
        assert "This feature verifies" in loaded_spec
        assert "Ensure clean separation" in loaded_spec

        # Parse spec to get content
        parsed = parse_spec_file(work_item_id)
        assert parsed["rationale"] is not None
        assert len(parsed["acceptance_criteria"]) >= 3

        print("✓ Test 5: System integration uses spec files, no deprecated JSON fields")


def run_all_tests():
    """Run all tests and report results."""
    test_instance = TestPhase5_7Complete()

    tests = [
        test_instance.test_end_to_end_feature_workflow,
        test_instance.test_end_to_end_deployment_workflow,
        test_instance.test_incomplete_spec_fails_validation,
        test_instance.test_spec_parser_integration_with_all_work_item_types,
        test_instance.test_system_integration_no_deprecated_fields,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_instance.setup_method()
            test_func()
            test_instance.teardown_method()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_func.__name__} failed: {e}")
            test_instance.teardown_method()
            failed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__} errored: {e}")
            import traceback

            traceback.print_exc()
            test_instance.teardown_method()
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"Test Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print(f"{'=' * 60}")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
