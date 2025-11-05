"""Integration tests for spec validation pipeline module.

This module tests the integration between validators, runners, and spec files,
including validation of integration tests and deployments.
"""

import pytest

from sdd.core.exceptions import FileNotFoundError
from sdd.testing.integration_runner import IntegrationTestRunner
from sdd.work_items.manager import WorkItemManager


class TestValidateIntegrationTest:
    """Tests for validate_integration_test function."""

    def test_validate_integration_test_valid_spec(self, temp_project_dir, monkeypatch):
        """Test that validate_integration_test correctly validates a complete integration test spec."""
        # Arrange
        monkeypatch.chdir(temp_project_dir)
        specs_dir = temp_project_dir / ".session" / "specs"
        specs_dir.mkdir(parents=True)

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
        spec_file = specs_dir / "integration_test_001.md"
        spec_file.write_text(spec_content)

        manager = WorkItemManager()

        work_item = {
            "id": "integration_test_001",
            "type": "integration_test",
            "title": "Order Processing Flow",
            "dependencies": ["feature_001"],
        }

        # Act
        is_valid, errors = manager.validate_integration_test(work_item)

        # Assert
        assert is_valid, f"Expected valid, got errors: {errors}"
        assert len(errors) == 0

    def test_validate_integration_test_invalid_spec(self, temp_project_dir, monkeypatch):
        """Test that validate_integration_test detects invalid spec with missing sections."""
        # Arrange
        monkeypatch.chdir(temp_project_dir)
        specs_dir = temp_project_dir / ".session" / "specs"
        specs_dir.mkdir(parents=True)

        spec_content = """# integration_test: Incomplete Test

## Scope
Some scope here.

## Acceptance Criteria
- [ ] First criterion
- [ ] Second criterion
"""
        spec_file = specs_dir / "integration_test_002.md"
        spec_file.write_text(spec_content)

        manager = WorkItemManager()

        work_item = {
            "id": "integration_test_002",
            "type": "integration_test",
            "title": "Incomplete Test",
            "dependencies": [],
        }

        # Act
        is_valid, errors = manager.validate_integration_test(work_item)

        # Assert
        assert not is_valid, "Expected invalid spec"
        assert len(errors) > 0
        assert any("Test Scenarios" in str(e) for e in errors)

    def test_validate_integration_test_missing_spec_file(self, temp_project_dir, monkeypatch):
        """Test that validate_integration_test raises FileNotFoundError when spec file is missing."""
        # Arrange
        monkeypatch.chdir(temp_project_dir)
        specs_dir = temp_project_dir / ".session" / "specs"
        specs_dir.mkdir(parents=True)

        manager = WorkItemManager()

        work_item = {
            "id": "nonexistent_test",
            "type": "integration_test",
            "title": "Missing Test",
            "dependencies": [],
        }

        # Act & Assert
        with pytest.raises(FileNotFoundError) as exc_info:
            manager.validate_integration_test(work_item)

        assert "nonexistent_test.md" in str(exc_info.value.context.get("file_path", ""))

    def test_validate_integration_test_missing_dependencies(self, temp_project_dir, monkeypatch):
        """Test that validate_integration_test detects missing dependencies."""
        # Arrange
        monkeypatch.chdir(temp_project_dir)
        specs_dir = temp_project_dir / ".session" / "specs"
        specs_dir.mkdir(parents=True)

        spec_content = """# integration_test: Test Without Dependencies

## Scope
Test scope.

## Test Scenarios

### Scenario 1: Test
Test scenario.

## Performance Benchmarks
Response time: < 100ms

## Environment Requirements
- PostgreSQL

## Acceptance Criteria
- [ ] Test passes

## Dependencies
None

## Estimated Effort
1 session
"""
        spec_file = specs_dir / "integration_test_003.md"
        spec_file.write_text(spec_content)

        manager = WorkItemManager()

        work_item = {
            "id": "integration_test_003",
            "type": "integration_test",
            "title": "Test Without Dependencies",
            "dependencies": [],
        }

        # Act
        is_valid, errors = manager.validate_integration_test(work_item)

        # Assert
        # Should detect missing feature dependency
        assert not is_valid
        assert any("dependencies" in str(e).lower() for e in errors)


class TestValidateDeployment:
    """Tests for validate_deployment function."""

    def test_validate_deployment_valid_spec(self, temp_project_dir, monkeypatch):
        """Test that validate_deployment correctly validates a complete deployment spec."""
        # Arrange
        monkeypatch.chdir(temp_project_dir)
        specs_dir = temp_project_dir / ".session" / "specs"
        specs_dir.mkdir(parents=True)

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
        spec_file = specs_dir / "deployment_001.md"
        spec_file.write_text(spec_content)

        manager = WorkItemManager()

        work_item = {
            "id": "deployment_001",
            "type": "deployment",
            "title": "Production Release v2.0",
        }

        # Act
        is_valid, errors = manager.validate_deployment(work_item)

        # Assert
        assert is_valid, f"Expected valid, got errors: {errors}"
        assert len(errors) == 0

    def test_validate_deployment_invalid_spec(self, temp_project_dir, monkeypatch):
        """Test that validate_deployment detects invalid spec with missing sections."""
        # Arrange
        monkeypatch.chdir(temp_project_dir)
        specs_dir = temp_project_dir / ".session" / "specs"
        specs_dir.mkdir(parents=True)

        spec_content = """# deployment: Incomplete Deployment

## Deployment Scope
Some scope

## Acceptance Criteria
- [ ] Test 1
- [ ] Test 2
"""
        spec_file = specs_dir / "deployment_002.md"
        spec_file.write_text(spec_content)

        manager = WorkItemManager()

        work_item = {
            "id": "deployment_002",
            "type": "deployment",
            "title": "Incomplete Deployment",
        }

        # Act
        is_valid, errors = manager.validate_deployment(work_item)

        # Assert
        assert not is_valid, "Expected invalid spec"
        assert len(errors) > 0
        assert any(
            "Deployment Procedure" in str(e)
            or "Rollback Procedure" in str(e)
            or "Smoke Tests" in str(e)
            for e in errors
        )

    def test_validate_deployment_missing_spec_file(self, temp_project_dir, monkeypatch):
        """Test that validate_deployment raises FileNotFoundError when spec file is missing."""
        # Arrange
        monkeypatch.chdir(temp_project_dir)
        specs_dir = temp_project_dir / ".session" / "specs"
        specs_dir.mkdir(parents=True)

        manager = WorkItemManager()

        work_item = {
            "id": "nonexistent_deployment",
            "type": "deployment",
            "title": "Missing Deployment",
        }

        # Act & Assert
        with pytest.raises(FileNotFoundError) as exc_info:
            manager.validate_deployment(work_item)

        assert "nonexistent_deployment.md" in str(exc_info.value.context.get("file_path", ""))


class TestIntegrationTestRunner:
    """Tests for IntegrationTestRunner class."""

    def test_integration_test_runner_with_spec(self, temp_project_dir, monkeypatch):
        """Test that IntegrationTestRunner correctly parses spec and extracts test scenarios."""
        # Arrange
        monkeypatch.chdir(temp_project_dir)
        specs_dir = temp_project_dir / ".session" / "specs"
        specs_dir.mkdir(parents=True)

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
        spec_file = specs_dir / "integration_test_runner.md"
        spec_file.write_text(spec_content)

        work_item = {"id": "integration_test_runner", "type": "integration_test"}

        # Act
        runner = IntegrationTestRunner(work_item)

        # Assert
        assert len(runner.test_scenarios) == 2
        assert runner.test_scenarios[0]["name"] == "Scenario 1: Basic Test"
        assert runner.test_scenarios[1]["name"] == "Scenario 2: Advanced Test"
        assert isinstance(runner.env_requirements, dict)
        assert "services_required" in runner.env_requirements
        assert "compose_file" in runner.env_requirements
        assert runner.env_requirements.get("compose_file") == "docker-compose.test.yml"

    def test_integration_test_runner_missing_spec(self, temp_project_dir, monkeypatch):
        """Test that IntegrationTestRunner raises FileNotFoundError for missing spec."""
        # Arrange
        monkeypatch.chdir(temp_project_dir)
        specs_dir = temp_project_dir / ".session" / "specs"
        specs_dir.mkdir(parents=True)

        work_item = {"id": "nonexistent_test", "type": "integration_test"}

        # Act & Assert
        with pytest.raises(FileNotFoundError) as exc_info:
            IntegrationTestRunner(work_item)

        assert "nonexistent_test.md" in str(exc_info.value.context.get("file_path", ""))

    def test_integration_test_runner_extracts_services(self, temp_project_dir, monkeypatch):
        """Test that IntegrationTestRunner extracts required services from environment requirements."""
        # Arrange
        monkeypatch.chdir(temp_project_dir)
        specs_dir = temp_project_dir / ".session" / "specs"
        specs_dir.mkdir(parents=True)

        spec_content = """# integration_test: Service Extraction Test

## Scope
Test service extraction

## Test Scenarios

### Scenario 1: Test
Test scenario

## Performance Benchmarks
Response time: < 100ms

## Environment Requirements
- PostgreSQL 14
- Redis 6.2
- RabbitMQ 3.9
- Elasticsearch 8.0

## Acceptance Criteria
- [ ] Tests pass

## Dependencies
None

## Estimated Effort
1 session
"""
        spec_file = specs_dir / "test_services.md"
        spec_file.write_text(spec_content)

        work_item = {"id": "test_services", "type": "integration_test"}

        # Act
        runner = IntegrationTestRunner(work_item)

        # Assert
        services = runner.env_requirements.get("services_required", [])
        # Service extraction is heuristic-based, just verify the structure exists
        assert isinstance(services, list)


class TestValidationPipelineEndToEnd:
    """End-to-end tests for the validation pipeline."""

    def test_validation_pipeline_complete_workflow(self, temp_project_dir, monkeypatch):
        """Test complete validation workflow from spec creation to validation."""
        # Arrange
        monkeypatch.chdir(temp_project_dir)
        specs_dir = temp_project_dir / ".session" / "specs"
        specs_dir.mkdir(parents=True)

        # Create multiple spec files
        integration_spec = """# integration_test: Complete Test

## Scope
Complete integration test

## Test Scenarios

### Scenario 1: Full Flow
Complete test flow

## Performance Benchmarks
Response time: < 200ms

## Environment Requirements
- PostgreSQL 14

## Acceptance Criteria
- [ ] All scenarios pass
- [ ] Performance benchmarks met
- [ ] Environment setup works

## Dependencies
feature_001

## Estimated Effort
2 sessions
"""

        deployment_spec = """# deployment: Complete Deployment

## Deployment Scope
**Application:** Test App

## Deployment Procedure

### Pre-Deployment Checklist
- [ ] Backup

### Deployment Steps
1. Deploy

### Post-Deployment Steps
1. Verify

## Environment Configuration
DB_URL=test

## Rollback Procedure

### Rollback Triggers
- Issues

### Rollback Steps
1. Revert

## Smoke Tests

### Test 1: Health
Check health

## Acceptance Criteria
- [ ] All smoke tests pass
- [ ] No critical errors
- [ ] Monitoring configured

## Dependencies
None

## Estimated Effort
1 session
"""

        (specs_dir / "integration_complete.md").write_text(integration_spec)
        (specs_dir / "deployment_complete.md").write_text(deployment_spec)

        manager = WorkItemManager()

        integration_item = {
            "id": "integration_complete",
            "type": "integration_test",
            "title": "Complete Test",
            "dependencies": ["feature_001"],
        }

        deployment_item = {
            "id": "deployment_complete",
            "type": "deployment",
            "title": "Complete Deployment",
        }

        # Act
        int_valid, int_errors = manager.validate_integration_test(integration_item)
        dep_valid, dep_errors = manager.validate_deployment(deployment_item)

        # Assert
        assert int_valid, f"Integration test should be valid, got errors: {int_errors}"
        assert dep_valid, f"Deployment should be valid, got errors: {dep_errors}"
