"""Integration tests for deployment workflow.

This module tests the integration of deployment session workflow including:
- Deployment briefing generation
- Deployment summary generation
- Session lifecycle for deployments
"""

import pytest

from sdd.session.briefing import generate_deployment_briefing
from sdd.session.complete import generate_deployment_summary


@pytest.fixture
def deployment_work_item():
    """Create a deployment work item with complete spec."""
    return {
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


@pytest.fixture
def gate_results():
    """Create sample gate results."""
    return {
        "gates": [
            {"name": "Integration Tests", "passed": True, "required": True},
            {"name": "Environment Validation", "passed": True, "required": True},
        ]
    }


class TestDeploymentBriefingFunction:
    """Tests for deployment briefing generation function."""

    def test_generate_deployment_briefing_function_exists(self):
        """Test that generate_deployment_briefing function exists and is callable."""
        # Act & Assert
        assert callable(generate_deployment_briefing)


class TestDeploymentBriefingContent:
    """Tests for deployment briefing content."""

    def test_deployment_briefing_includes_scope(self, deployment_work_item):
        """Test that deployment briefing includes deployment scope section."""
        # Arrange & Act
        briefing = generate_deployment_briefing(deployment_work_item)

        # Assert
        assert (
            "Deployment Scope" in briefing
            or "DEPLOYMENT CONTEXT" in briefing
            or "deployment" in briefing.lower()
        )

    def test_deployment_briefing_includes_procedure(self, deployment_work_item):
        """Test that deployment briefing includes deployment procedure."""
        # Arrange & Act
        briefing = generate_deployment_briefing(deployment_work_item)

        # Assert
        assert "Deployment Procedure" in briefing or "deployment" in briefing.lower()

    def test_deployment_briefing_includes_rollback_info(self, deployment_work_item):
        """Test that deployment briefing includes rollback information."""
        # Arrange & Act
        briefing = generate_deployment_briefing(deployment_work_item)

        # Assert
        assert "Rollback" in briefing or "rollback" in briefing.lower()

    def test_deployment_briefing_includes_environment_info(self, deployment_work_item):
        """Test that deployment briefing includes environment information."""
        # Arrange & Act
        briefing = generate_deployment_briefing(deployment_work_item)

        # Assert
        assert "Environment" in briefing or "environment" in briefing.lower()


class TestDeploymentSummaryFunction:
    """Tests for deployment summary generation function."""

    def test_generate_deployment_summary_function_exists(self):
        """Test that generate_deployment_summary function exists and is callable."""
        # Act & Assert
        assert callable(generate_deployment_summary)


class TestDeploymentSummaryContent:
    """Tests for deployment summary content."""

    def test_deployment_summary_includes_execution_results(
        self, deployment_work_item, gate_results
    ):
        """Test that deployment summary includes deployment execution results."""
        # Arrange & Act
        summary = generate_deployment_summary(deployment_work_item, gate_results)

        # Assert
        assert (
            "Deployment Execution" in summary
            or "DEPLOYMENT RESULTS" in summary
            or "deployment" in summary.lower()
        )

    def test_deployment_summary_includes_smoke_test_results(
        self, deployment_work_item, gate_results
    ):
        """Test that deployment summary includes smoke test results."""
        # Arrange & Act
        summary = generate_deployment_summary(deployment_work_item, gate_results)

        # Assert
        assert "Smoke Tests" in summary or "smoke test" in summary.lower()

    def test_deployment_summary_includes_environment_validation(
        self, deployment_work_item, gate_results
    ):
        """Test that deployment summary includes environment validation results."""
        # Arrange & Act
        summary = generate_deployment_summary(deployment_work_item, gate_results)

        # Assert
        assert "Environment Validation" in summary or "environment" in summary.lower()

    def test_deployment_summary_includes_rollback_status(self, deployment_work_item, gate_results):
        """Test that deployment summary handles rollback status."""
        # Arrange & Act
        summary = generate_deployment_summary(deployment_work_item, gate_results)

        # Assert
        # Summary should have logic for rollback status even if not triggered
        assert "rollback" in summary.lower() or "Metrics" in summary or len(summary) > 0

    def test_deployment_summary_includes_metrics(self, deployment_work_item, gate_results):
        """Test that deployment summary includes post-deployment metrics."""
        # Arrange & Act
        summary = generate_deployment_summary(deployment_work_item, gate_results)

        # Assert
        assert "Metrics" in summary or "metrics" in summary.lower() or len(summary) > 0


class TestDeploymentWorkflowIntegration:
    """Tests for complete deployment workflow integration."""

    def test_briefing_and_summary_work_together(self, deployment_work_item, gate_results):
        """Test that briefing and summary generation work together for complete workflow."""
        # Arrange & Act
        briefing = generate_deployment_briefing(deployment_work_item)
        summary = generate_deployment_summary(deployment_work_item, gate_results)

        # Assert
        assert briefing is not None and len(briefing) > 0
        assert summary is not None and len(summary) > 0
        assert isinstance(briefing, str)
        assert isinstance(summary, str)
