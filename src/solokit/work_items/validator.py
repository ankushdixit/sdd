#!/usr/bin/env python3
"""
Work Item Validator - Validation logic for work items.

Handles spec validation for integration_test and deployment work items.
"""

from __future__ import annotations

from solokit.core.error_handlers import log_errors
from solokit.core.exceptions import (
    ErrorCode,
    FileOperationError,
    SpecValidationError,
    ValidationError,
)
from solokit.core.logging_config import get_logger
from solokit.work_items import spec_parser

logger = get_logger(__name__)


class WorkItemValidator:
    """Validates work item specifications and constraints"""

    @log_errors()
    def validate_integration_test(self, work_item: dict) -> None:
        """Validate integration test work item by parsing spec file

        Args:
            work_item: Work item dictionary to validate

        Raises:
            FileOperationError: If spec file not found
            ValidationError: If spec validation fails (with validation errors in context)
        """
        errors = []
        work_id: str = str(work_item.get("id", ""))

        # Parse spec file - pass full work_item dict to support custom spec filenames
        try:
            parsed_spec = spec_parser.parse_spec_file(work_item)
        except FileNotFoundError:
            spec_file = work_item.get("spec_file", f".session/specs/{work_id}.md")
            raise FileOperationError(
                operation="read",
                file_path=spec_file,
                details="Spec file not found",
            )
        except ValueError as e:
            raise ValidationError(
                message=f"Invalid spec file: {str(e)}",
                code=ErrorCode.SPEC_VALIDATION_FAILED,
                context={"work_item_id": work_id},
                remediation=f"Fix spec file validation errors for {work_id}",
                cause=e,
            )

        # Validate required sections exist and are not empty
        required_sections = {
            "scope": "Scope",
            "test_scenarios": "Test Scenarios",
            "performance_benchmarks": "Performance Benchmarks",
            "environment_requirements": "Environment Requirements",
            "acceptance_criteria": "Acceptance Criteria",
        }

        for field_name, section_name in required_sections.items():
            value = parsed_spec.get(field_name)
            if value is None or (isinstance(value, str) and not value.strip()):
                errors.append(f"Missing required section: {section_name}")
            elif isinstance(value, list) and len(value) == 0:
                errors.append(f"Section '{section_name}' is empty")

        # Validate test scenarios - must have at least 1 scenario
        test_scenarios = parsed_spec.get("test_scenarios", [])
        if len(test_scenarios) == 0:
            errors.append("At least one test scenario required")
        else:
            # Check that each scenario has content
            for i, scenario in enumerate(test_scenarios):
                if not scenario.get("content") or not scenario.get("content").strip():
                    scenario_name = scenario.get("name", f"Scenario {i + 1}")
                    errors.append(f"{scenario_name}: Missing scenario content")

        # Validate acceptance criteria - should have at least 3 items (per spec validation rules)
        acceptance_criteria = parsed_spec.get("acceptance_criteria", [])
        if len(acceptance_criteria) < 3:
            errors.append(
                f"Acceptance criteria should have at least 3 items (found {len(acceptance_criteria)})"
            )

        # Check for work item dependencies
        dependencies = work_item.get("dependencies", [])
        if not dependencies:
            errors.append("Integration tests must have dependencies (component implementations)")

        # If errors found, raise ValidationError with all errors in context
        if errors:
            raise SpecValidationError(
                work_item_id=work_id,
                errors=errors,
                remediation=f"Fix validation errors in {work_id} spec file",
            )

    @log_errors()
    def validate_deployment(self, work_item: dict) -> None:
        """Validate deployment work item by parsing spec file

        Args:
            work_item: Work item dictionary to validate

        Raises:
            FileOperationError: If spec file not found
            ValidationError: If spec validation fails (with validation errors in context)
        """
        errors = []
        work_id: str = str(work_item.get("id", ""))

        # Parse spec file - pass full work_item dict to support custom spec filenames
        try:
            parsed_spec = spec_parser.parse_spec_file(work_item)
        except FileNotFoundError:
            spec_file = work_item.get("spec_file", f".session/specs/{work_id}.md")
            raise FileOperationError(
                operation="read",
                file_path=spec_file,
                details="Spec file not found",
            )
        except ValueError as e:
            raise ValidationError(
                message=f"Invalid spec file: {str(e)}",
                code=ErrorCode.SPEC_VALIDATION_FAILED,
                context={"work_item_id": work_id},
                remediation=f"Fix spec file validation errors for {work_id}",
                cause=e,
            )

        # Validate required sections exist and are not empty
        required_sections = {
            "deployment_scope": "Deployment Scope",
            "deployment_procedure": "Deployment Procedure",
            "environment_configuration": "Environment Configuration",
            "rollback_procedure": "Rollback Procedure",
            "smoke_tests": "Smoke Tests",
            "acceptance_criteria": "Acceptance Criteria",
        }

        for field_name, section_name in required_sections.items():
            value = parsed_spec.get(field_name)
            if value is None:
                errors.append(f"Missing required section: {section_name}")
            elif isinstance(value, str) and not value.strip():
                errors.append(f"Section '{section_name}' is empty")
            elif isinstance(value, list) and len(value) == 0:
                errors.append(f"Section '{section_name}' is empty")
            elif isinstance(value, dict) and not any(value.values()):
                errors.append(f"Section '{section_name}' is empty")

        # Validate deployment procedure subsections
        deployment_proc = parsed_spec.get("deployment_procedure")
        if deployment_proc:
            if (
                not deployment_proc.get("pre_deployment")
                or not deployment_proc.get("pre_deployment").strip()
            ):
                errors.append("Missing pre-deployment checklist/steps")
            if (
                not deployment_proc.get("deployment_steps")
                or not deployment_proc.get("deployment_steps").strip()
            ):
                errors.append("Missing deployment steps")
            if (
                not deployment_proc.get("post_deployment")
                or not deployment_proc.get("post_deployment").strip()
            ):
                errors.append("Missing post-deployment steps")

        # Validate rollback procedure subsections
        rollback_proc = parsed_spec.get("rollback_procedure")
        if rollback_proc:
            if not rollback_proc.get("triggers") or not rollback_proc.get("triggers").strip():
                errors.append("Missing rollback triggers")
            if not rollback_proc.get("steps") or not rollback_proc.get("steps").strip():
                errors.append("Missing rollback steps")

        # Validate smoke tests - must have at least 1 test
        smoke_tests = parsed_spec.get("smoke_tests", [])
        if len(smoke_tests) == 0:
            errors.append("At least one smoke test required")

        # Validate acceptance criteria - should have at least 3 items
        acceptance_criteria = parsed_spec.get("acceptance_criteria", [])
        if len(acceptance_criteria) < 3:
            errors.append(
                f"Acceptance criteria should have at least 3 items (found {len(acceptance_criteria)})"
            )

        # If errors found, raise ValidationError with all errors in context
        if errors:
            raise SpecValidationError(
                work_item_id=work_id,
                errors=errors,
                remediation=f"Fix validation errors in {work_id} spec file",
            )
