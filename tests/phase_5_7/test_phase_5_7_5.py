#!/usr/bin/env python3
"""
Test Suite for Phase 5.7.5: Spec File Validation System

Tests the spec_validator module and its integration with briefing_generator and quality_gates.
"""

import sys
from pathlib import Path
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

from scripts.spec_validator import (  # noqa: E402
    validate_spec_file,
    check_required_sections,
    check_acceptance_criteria,
    check_test_scenarios,
    check_deployment_subsections,
    get_validation_rules,
)
from scripts.quality_gates import QualityGates  # noqa: E402


class TestSpecValidator:
    """Test suite for spec_validator.py module."""

    def setup_method(self):
        """Setup test fixtures."""
        # Create temporary .session/specs directory
        self.temp_dir = tempfile.mkdtemp()
        self.specs_dir = Path(self.temp_dir) / ".session" / "specs"
        self.specs_dir.mkdir(parents=True)

        # Change to temp directory
        self.original_dir = Path.cwd()
        import os

        os.chdir(self.temp_dir)

    def teardown_method(self):
        """Cleanup test fixtures."""
        import os

        os.chdir(self.original_dir)
        shutil.rmtree(self.temp_dir)

    def create_spec_file(self, work_item_id: str, content: str):
        """Helper to create a spec file."""
        spec_path = self.specs_dir / f"{work_item_id}.md"
        spec_path.write_text(content, encoding="utf-8")

    def test_get_validation_rules_feature(self):
        """Test: get_validation_rules returns correct rules for feature."""
        rules = get_validation_rules("feature")

        assert "required_sections" in rules
        assert "Overview" in rules["required_sections"]
        assert "Rationale" in rules["required_sections"]
        assert "Acceptance Criteria" in rules["required_sections"]
        assert "Implementation Details" in rules["required_sections"]
        assert "Testing Strategy" in rules["required_sections"]
        assert rules["special_requirements"]["acceptance_criteria_min_items"] == 3

        print("✓ Test 1: get_validation_rules returns correct rules for feature")

    def test_get_validation_rules_deployment(self):
        """Test: get_validation_rules returns correct rules for deployment."""
        rules = get_validation_rules("deployment")

        assert "required_sections" in rules
        assert "Deployment Scope" in rules["required_sections"]
        assert "Deployment Procedure" in rules["required_sections"]
        assert "Rollback Procedure" in rules["required_sections"]
        assert "Smoke Tests" in rules["required_sections"]
        assert "Acceptance Criteria" in rules["required_sections"]

        assert "deployment_procedure_subsections" in rules["special_requirements"]
        assert (
            "Pre-Deployment Checklist"
            in rules["special_requirements"]["deployment_procedure_subsections"]
        )
        assert (
            "Deployment Steps"
            in rules["special_requirements"]["deployment_procedure_subsections"]
        )
        assert (
            "Post-Deployment Steps"
            in rules["special_requirements"]["deployment_procedure_subsections"]
        )

        print("✓ Test 2: get_validation_rules returns correct rules for deployment")

    def test_check_required_sections_valid(self):
        """Test: check_required_sections passes for valid feature spec."""
        spec_content = """
# Feature: Test Feature

## Overview
This is the overview section.

## Rationale
This is the rationale.

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Implementation Details
Implementation details here.

## Testing Strategy
Testing strategy here.
"""

        errors = check_required_sections(spec_content, "feature")
        assert len(errors) == 0

        print("✓ Test 3: check_required_sections passes for valid feature spec")

    def test_check_required_sections_missing(self):
        """Test: check_required_sections detects missing sections."""
        spec_content = """
# Feature: Test Feature

## Overview
This is the overview section.

## Rationale
This is the rationale.
"""

        errors = check_required_sections(spec_content, "feature")
        assert len(errors) > 0
        assert any("Acceptance Criteria" in error for error in errors)
        assert any("Implementation Details" in error for error in errors)

        print("✓ Test 4: check_required_sections detects missing sections")

    def test_check_acceptance_criteria_valid(self):
        """Test: check_acceptance_criteria passes with 3+ items."""
        spec_content = """
## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3
"""

        error = check_acceptance_criteria(spec_content, min_items=3)
        assert error is None

        print("✓ Test 5: check_acceptance_criteria passes with 3+ items")

    def test_check_acceptance_criteria_insufficient(self):
        """Test: check_acceptance_criteria fails with < 3 items."""
        spec_content = """
## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
"""

        error = check_acceptance_criteria(spec_content, min_items=3)
        assert error is not None
        assert "at least 3 items" in error
        assert "found 2" in error

        print("✓ Test 6: check_acceptance_criteria fails with < 3 items")

    def test_check_test_scenarios_valid(self):
        """Test: check_test_scenarios passes with scenarios present."""
        spec_content = """
## Test Scenarios

### Scenario 1: User Login
Description here.

### Scenario 2: User Logout
Description here.
"""

        error = check_test_scenarios(spec_content, min_scenarios=1)
        assert error is None

        print("✓ Test 7: check_test_scenarios passes with scenarios present")

    def test_check_deployment_subsections_valid(self):
        """Test: check_deployment_subsections passes with all required subsections."""
        spec_content = """
## Deployment Procedure

### Pre-Deployment Checklist
- [ ] Check 1

### Deployment Steps
Step 1

### Post-Deployment Steps
Step 1
"""

        errors = check_deployment_subsections(spec_content)
        assert len(errors) == 0

        print(
            "✓ Test 8: check_deployment_subsections passes with all required subsections"
        )

    def test_validate_spec_file_valid_feature(self):
        """Test: validate_spec_file passes for complete feature spec."""
        work_item_id = "test_feature_123"
        spec_content = """
# Feature: Test Feature

## Overview
Complete overview of the feature.

## Rationale
Why this feature is needed.

## Acceptance Criteria
- [ ] Criterion 1: Must do X
- [ ] Criterion 2: Must do Y
- [ ] Criterion 3: Must do Z

## Implementation Details
How to implement this.

## Testing Strategy
How to test this.
"""

        self.create_spec_file(work_item_id, spec_content)

        is_valid, errors = validate_spec_file(work_item_id, "feature")
        assert is_valid
        assert len(errors) == 0

        print("✓ Test 9: validate_spec_file passes for complete feature spec")

    def test_validate_spec_file_incomplete_deployment(self):
        """Test: validate_spec_file fails for incomplete deployment spec."""
        work_item_id = "test_deployment_456"
        spec_content = """
# Deployment: Test Deployment

## Deployment Scope
Scope here.

## Deployment Procedure

### Pre-Deployment Checklist
- [ ] Check 1

### Deployment Steps
Steps here.
"""

        self.create_spec_file(work_item_id, spec_content)

        is_valid, errors = validate_spec_file(work_item_id, "deployment")
        assert not is_valid
        assert len(errors) > 0
        # Should be missing: Post-Deployment Steps, Rollback Procedure, Smoke Tests, Acceptance Criteria

        print("✓ Test 10: validate_spec_file fails for incomplete deployment spec")

    def test_quality_gates_validate_spec_completeness(self):
        """Test: QualityGates.validate_spec_completeness integration."""
        work_item_id = "test_feature_789"
        spec_content = """
# Feature: Test Feature

## Overview
Complete overview.

## Rationale
Rationale here.

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Implementation Details
Details here.

## Testing Strategy
Strategy here.
"""

        self.create_spec_file(work_item_id, spec_content)

        # Create QualityGates instance
        gates = QualityGates()

        # Test with valid spec
        work_item = {"id": work_item_id, "type": "feature"}
        passed, results = gates.validate_spec_completeness(work_item)

        assert passed
        assert results["status"] == "passed"

        print(
            "✓ Test 11 (BONUS): QualityGates.validate_spec_completeness integration works"
        )


def run_all_tests():
    """Run all tests and report results."""
    test_instance = TestSpecValidator()

    tests = [
        test_instance.test_get_validation_rules_feature,
        test_instance.test_get_validation_rules_deployment,
        test_instance.test_check_required_sections_valid,
        test_instance.test_check_required_sections_missing,
        test_instance.test_check_acceptance_criteria_valid,
        test_instance.test_check_acceptance_criteria_insufficient,
        test_instance.test_check_test_scenarios_valid,
        test_instance.test_check_deployment_subsections_valid,
        test_instance.test_validate_spec_file_valid_feature,
        test_instance.test_validate_spec_file_incomplete_deployment,
        test_instance.test_quality_gates_validate_spec_completeness,
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
            test_instance.teardown_method()
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"Test Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print(f"{'=' * 60}")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
