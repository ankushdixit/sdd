"""Unit tests for deployment specification validation.

This module tests the deployment work item type validation including:
- Deployment template structure
- Deployment spec validation through WorkItemManager
- Required sections checking
"""

import shutil
import tempfile
from pathlib import Path

from sdd.work_items.manager import WorkItemManager


class TestDeploymentTemplate:
    """Tests for deployment template structure."""

    def test_deployment_template_exists(self):
        """Test that deployment template file exists."""
        # Arrange
        project_root = Path(__file__).parent.parent.parent
        template_path = project_root / "src" / "sdd" / "templates" / "deployment_spec.md"

        # Act & Assert
        assert template_path.exists(), "Deployment template file should exist"

    def test_deployment_template_has_required_sections(self):
        """Test that deployment template contains all required sections."""
        # Arrange
        project_root = Path(__file__).parent.parent.parent
        template_path = project_root / "src" / "sdd" / "templates" / "deployment_spec.md"
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

        # Act & Assert
        for section in required_sections:
            assert section in template_content, f"Template should contain section: {section}"

    def test_deployment_template_has_environment_config(self):
        """Test that deployment template includes environment configuration section."""
        # Arrange
        project_root = Path(__file__).parent.parent.parent
        template_path = project_root / "src" / "sdd" / "templates" / "deployment_spec.md"
        template_content = template_path.read_text()

        # Act & Assert
        assert "## Environment Configuration" in template_content

    def test_deployment_template_has_monitoring_section(self):
        """Test that deployment template includes monitoring and alerting section."""
        # Arrange
        project_root = Path(__file__).parent.parent.parent
        template_path = project_root / "src" / "sdd" / "templates" / "deployment_spec.md"
        template_content = template_path.read_text()

        # Act & Assert
        assert "## Monitoring & Alerting" in template_content


class TestDeploymentValidation:
    """Tests for deployment spec validation through WorkItemManager."""

    def setup_method(self):
        """Set up test fixtures."""
        import os

        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = Path.cwd()
        os.chdir(self.temp_dir)

        # Create directory structure
        self.session_dir = Path(self.temp_dir) / ".session"
        self.specs_dir = self.session_dir / "specs"
        self.tracking_dir = self.session_dir / "tracking"

        self.specs_dir.mkdir(parents=True)
        self.tracking_dir.mkdir(parents=True)

    def teardown_method(self):
        """Clean up test fixtures."""
        import os

        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def create_spec_file(self, work_item_id: str, content: str):
        """Helper to create a spec file."""
        spec_path = self.specs_dir / f"{work_item_id}.md"
        spec_path.write_text(content, encoding="utf-8")

    def test_validate_complete_deployment_spec(self):
        """Test that a complete deployment spec validates successfully."""
        # Arrange
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

        # Act
        is_valid, errors = manager.validate_deployment(work_item)

        # Assert
        assert is_valid, f"Complete deployment spec should be valid, errors: {errors}"
        assert len(errors) == 0, "Should have no validation errors"

    def test_validate_incomplete_deployment_spec(self):
        """Test that an incomplete deployment spec fails validation."""
        # Arrange
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

        # Act
        is_valid, errors = manager.validate_deployment(work_item)

        # Assert
        assert not is_valid, "Incomplete deployment spec should fail validation"
        assert len(errors) > 0, "Should have validation errors"

    def test_validate_deployment_missing_spec_file(self):
        """Test that validation fails when spec file is missing."""
        # Arrange
        manager = WorkItemManager(project_root=Path(self.temp_dir))
        work_item = {
            "id": "DEPLOY-999",
            "type": "deployment",
            "title": "Missing Spec",
        }

        # Act
        is_valid, errors = manager.validate_deployment(work_item)

        # Assert
        assert not is_valid, "Validation should fail when spec file is missing"
        assert len(errors) > 0, "Should have error about missing spec file"
        assert any("not found" in error.lower() for error in errors)

    def test_validate_deployment_missing_deployment_scope(self):
        """Test that validation fails when deployment scope is missing."""
        # Arrange
        work_item_id = "DEPLOY-003"
        spec_content = """# Deployment: Missing Scope

## Deployment Procedure
Some procedure steps

## Environment Configuration
Some config

## Rollback Procedure
Some rollback steps

## Smoke Tests
Some tests

## Acceptance Criteria
Some criteria
"""
        self.create_spec_file(work_item_id, spec_content)
        manager = WorkItemManager(project_root=Path(self.temp_dir))
        work_item = {
            "id": work_item_id,
            "type": "deployment",
            "title": "Missing Scope",
        }

        # Act
        is_valid, errors = manager.validate_deployment(work_item)

        # Assert
        assert not is_valid, "Should fail validation without deployment scope"
        assert any("Deployment Scope" in error for error in errors)

    def test_validate_deployment_empty_section(self):
        """Test that validation fails when a required section is empty."""
        # Arrange
        work_item_id = "DEPLOY-004"
        spec_content = """# Deployment: Empty Sections

## Deployment Scope
Complete scope information here

## Deployment Procedure


## Environment Configuration
Complete config here

## Rollback Procedure
Complete rollback here

## Smoke Tests
Complete tests here

## Acceptance Criteria
Complete criteria here
"""
        self.create_spec_file(work_item_id, spec_content)
        manager = WorkItemManager(project_root=Path(self.temp_dir))
        work_item = {
            "id": work_item_id,
            "type": "deployment",
            "title": "Empty Sections",
        }

        # Act
        is_valid, errors = manager.validate_deployment(work_item)

        # Assert
        assert not is_valid, "Should fail validation with empty required section"
        assert any("empty" in error.lower() for error in errors)

    def test_validate_deployment_with_custom_spec_file(self):
        """Test that validation works with custom spec file paths."""
        # Arrange
        work_item_id = "DEPLOY-005"
        custom_spec_file = ".session/specs/custom_deploy.md"
        spec_content = """# Deployment: Custom Spec File

## Deployment Scope
Complete scope information

## Deployment Procedure

### Pre-Deployment Checklist
- [ ] Check tests

### Deployment Steps
1. Deploy code

### Post-Deployment Steps
- [ ] Verify deployment

## Environment Configuration
Complete config information

## Rollback Procedure

### Rollback Triggers
- Errors occur

### Rollback Steps
1. Revert changes

## Smoke Tests

### Test 1: Health Check
Verify health endpoint

## Acceptance Criteria
- [ ] Deployment completes
- [ ] Tests pass
- [ ] No errors
"""
        custom_spec_path = Path(self.temp_dir) / custom_spec_file
        custom_spec_path.parent.mkdir(parents=True, exist_ok=True)
        custom_spec_path.write_text(spec_content, encoding="utf-8")

        manager = WorkItemManager(project_root=Path(self.temp_dir))
        work_item = {
            "id": work_item_id,
            "type": "deployment",
            "title": "Custom Spec File",
            "spec_file": custom_spec_file,
        }

        # Act
        is_valid, errors = manager.validate_deployment(work_item)

        # Assert
        assert is_valid, f"Should validate custom spec file, errors: {errors}"
        assert len(errors) == 0
