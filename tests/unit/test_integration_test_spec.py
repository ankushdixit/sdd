"""
Unit tests for integration test specification functionality.

Tests the work_item_manager.py module's integration test validation including:
- Integration test template structure
- Spec validation for integration tests
- Required section checking
"""

from pathlib import Path

import pytest

from sdd.work_items.manager import WorkItemManager


@pytest.fixture
def project_root():
    """Get the project root directory.

    Returns:
        Path: Absolute path to project root directory.
    """
    return Path(__file__).parent.parent.parent


@pytest.fixture
def temp_session_env(tmp_path, monkeypatch):
    """Create a temporary session environment for testing.

    Args:
        tmp_path: Pytest temporary directory fixture.
        monkeypatch: Pytest monkeypatch fixture for changing directory.

    Returns:
        Path: Root of temporary session environment with .session structure.
    """
    # Change to temp directory
    monkeypatch.chdir(tmp_path)

    # Create directory structure
    session_dir = tmp_path / ".session"
    specs_dir = session_dir / "specs"
    tracking_dir = session_dir / "tracking"

    specs_dir.mkdir(parents=True)
    tracking_dir.mkdir(parents=True)

    return tmp_path


@pytest.fixture
def work_item_manager(temp_session_env):
    """Create a WorkItemManager instance for testing.

    Args:
        temp_session_env: Temporary session environment fixture.

    Returns:
        WorkItemManager: Initialized manager instance.
    """
    return WorkItemManager(project_root=temp_session_env)


def create_spec_file(temp_session_env: Path, work_item_id: str, content: str):
    """Helper function to create a spec file.

    Args:
        temp_session_env: Path to temporary session environment.
        work_item_id: ID of the work item.
        content: Markdown content for the spec file.
    """
    spec_path = temp_session_env / ".session" / "specs" / f"{work_item_id}.md"
    spec_path.write_text(content, encoding="utf-8")


# ============================================================================
# Integration Test Template Tests
# ============================================================================


class TestIntegrationTestTemplate:
    """Test integration test template structure and completeness."""

    def test_template_file_exists(self, project_root):
        """Test that integration test template file exists.

        The template file should be present at templates/integration_test_spec.md.
        """
        # Arrange
        template_path = project_root / "src" / "sdd" / "templates" / "integration_test_spec.md"

        # Assert
        assert template_path.exists(), "integration_test_spec.md template not found"

    def test_template_has_all_required_sections(self, project_root):
        """Test that integration test template has all required sections.

        The template must include sections for:
        - Scope
        - Test Scenarios
        - Performance Benchmarks
        - API Contracts
        - Environment Requirements
        - Dependencies
        - Acceptance Criteria
        """
        # Arrange
        template_path = project_root / "src" / "sdd" / "templates" / "integration_test_spec.md"
        required_sections = [
            "## Scope",
            "## Test Scenarios",
            "## Performance Benchmarks",
            "## API Contracts",
            "## Environment Requirements",
            "## Dependencies",
            "## Acceptance Criteria",
        ]

        # Act
        template_content = template_path.read_text()

        # Assert - Check each required section
        for section in required_sections:
            assert section in template_content, f"Missing required section: {section}"

    @pytest.mark.parametrize(
        "section",
        [
            "## Scope",
            "## Test Scenarios",
            "## Performance Benchmarks",
            "## API Contracts",
            "## Environment Requirements",
            "## Dependencies",
            "## Acceptance Criteria",
        ],
    )
    def test_template_includes_specific_section(self, project_root, section):
        """Test that integration test template includes specific section.

        Parametrized test to verify each required section individually.
        """
        # Arrange
        template_path = project_root / "src" / "sdd" / "templates" / "integration_test_spec.md"

        # Act
        template_content = template_path.read_text()

        # Assert
        assert section in template_content, f"Missing section: {section}"


# ============================================================================
# Integration Test Validation Tests
# ============================================================================


class TestIntegrationTestValidation:
    """Test integration test work item validation."""

    def test_valid_integration_test_passes_validation(self, temp_session_env, work_item_manager):
        """Test that valid integration test spec passes validation.

        A complete integration test spec with all required sections should
        validate successfully.
        """
        # Arrange
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
        create_spec_file(temp_session_env, work_item_id, spec_content)

        work_item = {
            "id": work_item_id,
            "type": "integration_test",
            "title": "Test Service A to B Integration",
            "dependencies": ["FEAT-001", "FEAT-002"],
        }

        # Act
        is_valid, errors = work_item_manager.validate_integration_test(work_item)

        # Assert
        assert is_valid, f"Valid integration test spec should pass validation. Errors: {errors}"
        assert len(errors) == 0, "Valid spec should have no validation errors"

    def test_incomplete_integration_test_fails_validation(
        self, temp_session_env, work_item_manager
    ):
        """Test that incomplete integration test spec fails validation.

        An integration test spec missing required sections should fail
        validation with appropriate error messages.
        """
        # Arrange
        work_item_id = "INTEG-002"
        spec_content = """# Integration_Test: Incomplete Test

## Scope
Just a scope, missing other sections.
"""
        create_spec_file(temp_session_env, work_item_id, spec_content)

        work_item = {
            "id": work_item_id,
            "type": "integration_test",
            "title": "Incomplete Test",
        }

        # Act
        is_valid, errors = work_item_manager.validate_integration_test(work_item)

        # Assert
        assert not is_valid, "Incomplete integration test spec should fail validation"
        assert len(errors) > 0, "Incomplete spec should have validation errors"

    def test_incomplete_spec_identifies_missing_sections(self, temp_session_env, work_item_manager):
        """Test that validation identifies specific missing sections.

        The validation should report which sections are missing from an
        incomplete integration test spec.
        """
        # Arrange
        work_item_id = "INTEG-003"
        # Only has Scope and Test Scenarios, missing everything else
        spec_content = """# Integration_Test: Partial Test

## Scope
Some scope description.

## Test Scenarios
Some test scenarios.
"""
        create_spec_file(temp_session_env, work_item_id, spec_content)

        work_item = {
            "id": work_item_id,
            "type": "integration_test",
            "title": "Partial Test",
        }

        # Act
        is_valid, errors = work_item_manager.validate_integration_test(work_item)

        # Assert
        assert not is_valid, "Partial spec should fail validation"

        # Should identify multiple missing sections
        # The spec is missing: Performance Benchmarks, API Contracts,
        # Environment Requirements, Dependencies, Acceptance Criteria
        assert len(errors) >= 3, (
            f"Should identify multiple missing sections, got {len(errors)} errors: {errors}"
        )

    def test_integration_test_with_minimal_required_content(
        self, temp_session_env, work_item_manager
    ):
        """Test integration test with minimal but complete required content.

        Integration tests require:
        - Proper test scenario structure (not just bullet points)
        - At least 3 acceptance criteria
        - Work item dependencies
        """
        # Arrange
        work_item_id = "INTEG-004"
        spec_content = """# Integration_Test: Minimal Test

## Scope
Minimal scope for testing basic integration.

## Test Scenarios

### Scenario 1: Basic test
**Setup:**
- Service running

**Actions:**
1. Call endpoint

**Expected Results:**
- Success response

## Performance Benchmarks
- Response time < 100ms

## API Contracts
- contracts/api.yaml

## Environment Requirements
- service-a
- database

## Dependencies
- FEAT-001

## Acceptance Criteria
- [ ] All test scenarios pass
- [ ] Performance benchmarks met
- [ ] API contracts validated
"""
        create_spec_file(temp_session_env, work_item_id, spec_content)

        work_item = {
            "id": work_item_id,
            "type": "integration_test",
            "title": "Minimal Test",
            "dependencies": ["FEAT-001"],
        }

        # Act
        is_valid, errors = work_item_manager.validate_integration_test(work_item)

        # Assert
        assert is_valid, f"Minimal but complete spec should pass validation. Errors: {errors}"
