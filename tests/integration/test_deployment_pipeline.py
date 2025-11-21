"""Integration tests for deployment quality gates pipeline.

This module tests the integration of quality gates for deployment work items:
- Deployment gate orchestration through QualityGates
- Integration tests gate
- Security scans gate
- Environment validation gate
- Deployment documentation gate
- Rollback tested gate
"""

import pytest

from solokit.quality.gates import QualityGates


@pytest.fixture
def deployment_work_item():
    """Create a deployment work item with complete spec."""
    return {
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


class TestDeploymentQualityGatesMethod:
    """Tests for deployment quality gates method existence."""

    def test_run_deployment_gates_method_exists(self):
        """Test that QualityGates has run_deployment_gates method."""
        # Arrange
        gates = QualityGates()

        # Act & Assert
        assert hasattr(gates, "run_deployment_gates")
        assert callable(gates.run_deployment_gates)


class TestDeploymentQualityGates:
    """Tests for deployment quality gates execution."""

    def test_run_deployment_gates_returns_correct_structure(self, deployment_work_item):
        """Test that run_deployment_gates returns results with correct structure."""
        # Arrange
        gates = QualityGates()

        # Act
        passed, results = gates.run_deployment_gates(deployment_work_item)

        # Assert
        assert isinstance(passed, bool)
        assert isinstance(results, dict)
        assert "gates" in results
        assert isinstance(results["gates"], list)

    def test_integration_tests_gate_included(self, deployment_work_item):
        """Test that integration tests gate is included in deployment gates."""
        # Arrange
        gates = QualityGates()

        # Act
        passed, results = gates.run_deployment_gates(deployment_work_item)

        # Assert
        gate_names = [gate["name"] for gate in results["gates"]]
        assert "Integration Tests" in gate_names

    def test_security_scans_gate_included(self, deployment_work_item):
        """Test that security scans gate is included in deployment gates."""
        # Arrange
        gates = QualityGates()

        # Act
        passed, results = gates.run_deployment_gates(deployment_work_item)

        # Assert
        gate_names = [gate["name"] for gate in results["gates"]]
        assert "Security Scans" in gate_names

    def test_environment_validation_gate_included(self, deployment_work_item):
        """Test that environment validation gate is included in deployment gates."""
        # Arrange
        gates = QualityGates()

        # Act
        passed, results = gates.run_deployment_gates(deployment_work_item)

        # Assert
        gate_names = [gate["name"] for gate in results["gates"]]
        assert "Environment Validation" in gate_names

    def test_deployment_documentation_gate_included(self, deployment_work_item):
        """Test that deployment documentation gate is included in deployment gates."""
        # Arrange
        gates = QualityGates()

        # Act
        passed, results = gates.run_deployment_gates(deployment_work_item)

        # Assert
        gate_names = [gate["name"] for gate in results["gates"]]
        assert "Deployment Documentation" in gate_names

    def test_rollback_tested_gate_included(self, deployment_work_item):
        """Test that rollback tested gate is included in deployment gates."""
        # Arrange
        gates = QualityGates()

        # Act
        passed, results = gates.run_deployment_gates(deployment_work_item)

        # Assert
        gate_names = [gate["name"] for gate in results["gates"]]
        assert "Rollback Tested" in gate_names


class TestDeploymentGateRequirements:
    """Tests for deployment gate requirements and structure."""

    def test_all_deployment_gates_marked_as_required(self, deployment_work_item):
        """Test that all deployment gates are marked as required."""
        # Arrange
        gates = QualityGates()

        # Act
        passed, results = gates.run_deployment_gates(deployment_work_item)

        # Assert
        all_required = all(gate["required"] for gate in results["gates"])
        assert all_required, "All deployment gates should be required"

    def test_gate_results_have_complete_structure(self, deployment_work_item):
        """Test that each gate result has complete structure with required fields."""
        # Arrange
        gates = QualityGates()

        # Act
        passed, results = gates.run_deployment_gates(deployment_work_item)

        # Assert
        required_keys = ["name", "required", "passed"]
        for gate in results["gates"]:
            for key in required_keys:
                assert key in gate, f"Gate should have '{key}' field"
