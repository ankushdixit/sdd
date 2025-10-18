#!/usr/bin/env python3
"""
Spec File Validation Module

Validates work item specification files for completeness and correctness.
Ensures specs have all required sections and meet quality standards.

Part of Phase 5.7.5: Spec File Validation System
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from spec_parser import (
    extract_checklist,
    extract_subsection,
    parse_section,
    strip_html_comments,
)


def get_validation_rules(work_item_type: str) -> Dict[str, Any]:
    """
    Get validation rules for a specific work item type.

    Args:
        work_item_type: Type of work item (feature, bug, refactor, security, integration_test, deployment)

    Returns:
        Dictionary with required_sections, optional_sections, and special_requirements
    """
    rules = {
        "feature": {
            "required_sections": [
                "Overview",
                "Rationale",
                "Acceptance Criteria",
                "Implementation Details",
                "Testing Strategy",
            ],
            "optional_sections": [
                "User Story",
                "Documentation Updates",
                "Dependencies",
                "Estimated Effort",
            ],
            "special_requirements": {"acceptance_criteria_min_items": 3},
        },
        "bug": {
            "required_sections": [
                "Description",
                "Steps to Reproduce",
                "Root Cause Analysis",
                "Fix Approach",
            ],
            "optional_sections": [
                "Expected Behavior",
                "Actual Behavior",
                "Impact",
                "Testing Strategy",
                "Prevention",
                "Dependencies",
                "Estimated Effort",
            ],
            "special_requirements": {},
        },
        "refactor": {
            "required_sections": [
                "Overview",
                "Current State",
                "Proposed Refactor",
                "Scope",
            ],
            "optional_sections": [
                "Problems with Current Approach",
                "Implementation Plan",
                "Risk Assessment",
                "Success Criteria",
                "Testing Strategy",
                "Dependencies",
                "Estimated Effort",
            ],
            "special_requirements": {},
        },
        "security": {
            "required_sections": [
                "Security Issue",
                "Threat Model",
                "Attack Vector",
                "Mitigation Strategy",
                "Compliance",
            ],
            "optional_sections": [
                "Severity",
                "Affected Components",
                "Security Testing",
                "Post-Deployment",
                "Testing Strategy",
                "Acceptance Criteria",
                "Dependencies",
                "Estimated Effort",
            ],
            "special_requirements": {},
        },
        "integration_test": {
            "required_sections": [
                "Scope",
                "Test Scenarios",
                "Performance Benchmarks",
                "Environment Requirements",
                "Acceptance Criteria",
            ],
            "optional_sections": ["API Contracts", "Dependencies", "Estimated Effort"],
            "special_requirements": {
                "test_scenarios_min": 1,
                "acceptance_criteria_min_items": 3,
            },
        },
        "deployment": {
            "required_sections": [
                "Deployment Scope",
                "Deployment Procedure",
                "Rollback Procedure",
                "Smoke Tests",
                "Acceptance Criteria",
            ],
            "optional_sections": [
                "Environment Configuration",
                "Monitoring & Alerting",
                "Post-Deployment Monitoring Period",
                "Dependencies",
                "Estimated Effort",
            ],
            "special_requirements": {
                "deployment_procedure_subsections": [
                    "Pre-Deployment Checklist",
                    "Deployment Steps",
                    "Post-Deployment Steps",
                ],
                "rollback_procedure_subsections": [
                    "Rollback Triggers",
                    "Rollback Steps",
                ],
                "smoke_tests_min": 1,
                "acceptance_criteria_min_items": 3,
            },
        },
    }

    return rules.get(
        work_item_type,
        {"required_sections": [], "optional_sections": [], "special_requirements": {}},
    )


def check_required_sections(spec_content: str, work_item_type: str) -> List[str]:
    """
    Check if all required sections are present and non-empty.

    Args:
        spec_content: Full spec file content
        work_item_type: Type of work item

    Returns:
        List of error messages (empty if all checks pass)
    """
    errors = []
    rules = get_validation_rules(work_item_type)
    required_sections = rules.get("required_sections", [])

    # Strip HTML comments before parsing
    clean_content = strip_html_comments(spec_content)

    for section_name in required_sections:
        section_content = parse_section(clean_content, section_name)

        if section_content is None:
            errors.append(f"Missing required section: '{section_name}'")
        elif not section_content.strip():
            errors.append(f"Required section '{section_name}' is empty")

    return errors


def check_acceptance_criteria(spec_content: str, min_items: int = 3) -> Optional[str]:
    """
    Check if Acceptance Criteria section has enough items.

    Args:
        spec_content: Full spec file content
        min_items: Minimum number of acceptance criteria items required (default: 3)

    Returns:
        Error message if validation fails, None otherwise
    """
    clean_content = strip_html_comments(spec_content)
    ac_section = parse_section(clean_content, "Acceptance Criteria")

    if ac_section is None:
        return None  # Section doesn't exist, will be caught by check_required_sections

    checklist = extract_checklist(ac_section)

    if len(checklist) < min_items:
        return f"Acceptance Criteria must have at least {min_items} items (found {len(checklist)})"

    return None


def check_test_scenarios(spec_content: str, min_scenarios: int = 1) -> Optional[str]:
    """
    Check if Test Scenarios section has enough scenarios.

    Args:
        spec_content: Full spec file content
        min_scenarios: Minimum number of test scenarios required (default: 1)

    Returns:
        Error message if validation fails, None otherwise
    """
    clean_content = strip_html_comments(spec_content)
    scenarios_section = parse_section(clean_content, "Test Scenarios")

    if scenarios_section is None:
        return None  # Will be caught by check_required_sections

    # Count H3 headings that match "Scenario N:" pattern
    scenario_count = len(re.findall(r"###\s+Scenario\s+\d+:", scenarios_section, re.IGNORECASE))

    if scenario_count < min_scenarios:
        return f"Test Scenarios must have at least {min_scenarios} scenario(s) (found {scenario_count})"

    return None


def check_smoke_tests(spec_content: str, min_tests: int = 1) -> Optional[str]:
    """
    Check if Smoke Tests section has enough test cases.

    Args:
        spec_content: Full spec file content
        min_tests: Minimum number of smoke tests required (default: 1)

    Returns:
        Error message if validation fails, None otherwise
    """
    clean_content = strip_html_comments(spec_content)
    smoke_tests_section = parse_section(clean_content, "Smoke Tests")

    if smoke_tests_section is None:
        return None  # Will be caught by check_required_sections

    # Count H3 headings that match "Test N:" pattern
    test_count = len(re.findall(r"###\s+Test\s+\d+:", smoke_tests_section, re.IGNORECASE))

    if test_count < min_tests:
        return f"Smoke Tests must have at least {min_tests} test(s) (found {test_count})"

    return None


def check_deployment_subsections(spec_content: str) -> List[str]:
    """
    Check if Deployment Procedure has all required subsections.

    Args:
        spec_content: Full spec file content

    Returns:
        List of error messages (empty if all checks pass)
    """
    errors = []
    clean_content = strip_html_comments(spec_content)
    deployment_section = parse_section(clean_content, "Deployment Procedure")

    if deployment_section is None:
        return []  # Will be caught by check_required_sections

    required_subsections = [
        "Pre-Deployment Checklist",
        "Deployment Steps",
        "Post-Deployment Steps",
    ]

    for subsection_name in required_subsections:
        subsection_content = extract_subsection(deployment_section, subsection_name)
        if subsection_content is None:
            errors.append(f"Deployment Procedure missing required subsection: '{subsection_name}'")
        elif not subsection_content.strip():
            errors.append(f"Deployment Procedure subsection '{subsection_name}' is empty")

    return errors


def check_rollback_subsections(spec_content: str) -> List[str]:
    """
    Check if Rollback Procedure has all required subsections.

    Args:
        spec_content: Full spec file content

    Returns:
        List of error messages (empty if all checks pass)
    """
    errors = []
    clean_content = strip_html_comments(spec_content)
    rollback_section = parse_section(clean_content, "Rollback Procedure")

    if rollback_section is None:
        return []  # Will be caught by check_required_sections

    required_subsections = ["Rollback Triggers", "Rollback Steps"]

    for subsection_name in required_subsections:
        subsection_content = extract_subsection(rollback_section, subsection_name)
        if subsection_content is None:
            errors.append(f"Rollback Procedure missing required subsection: '{subsection_name}'")
        elif not subsection_content.strip():
            errors.append(f"Rollback Procedure subsection '{subsection_name}' is empty")

    return errors


def validate_spec_file(work_item_id: str, work_item_type: str) -> Tuple[bool, List[str]]:
    """
    Validate a work item specification file for completeness and correctness.

    Args:
        work_item_id: ID of the work item
        work_item_type: Type of work item (feature, bug, refactor, security, integration_test, deployment)

    Returns:
        Tuple of (is_valid, error_messages)
        - is_valid: True if spec passes all validation checks
        - error_messages: List of validation errors (empty if valid)
    """
    # Locate spec file
    spec_path = Path(".session/specs") / f"{work_item_id}.md"

    if not spec_path.exists():
        return False, [f"Spec file not found: {spec_path}"]

    # Read spec content
    try:
        spec_content = spec_path.read_text(encoding="utf-8")
    except Exception as e:
        return False, [f"Error reading spec file: {str(e)}"]

    # Collect all errors
    errors = []

    # Check required sections
    errors.extend(check_required_sections(spec_content, work_item_type))

    # Get special requirements for this work item type
    rules = get_validation_rules(work_item_type)
    special_requirements = rules.get("special_requirements", {})

    # Check acceptance criteria (if required)
    if "acceptance_criteria_min_items" in special_requirements:
        min_items = special_requirements["acceptance_criteria_min_items"]
        ac_error = check_acceptance_criteria(spec_content, min_items)
        if ac_error:
            errors.append(ac_error)

    # Check test scenarios (for integration_test)
    if "test_scenarios_min" in special_requirements:
        min_scenarios = special_requirements["test_scenarios_min"]
        scenarios_error = check_test_scenarios(spec_content, min_scenarios)
        if scenarios_error:
            errors.append(scenarios_error)

    # Check smoke tests (for deployment)
    if "smoke_tests_min" in special_requirements:
        min_tests = special_requirements["smoke_tests_min"]
        smoke_error = check_smoke_tests(spec_content, min_tests)
        if smoke_error:
            errors.append(smoke_error)

    # Check deployment subsections (for deployment)
    if "deployment_procedure_subsections" in special_requirements:
        errors.extend(check_deployment_subsections(spec_content))

    # Check rollback subsections (for deployment)
    if "rollback_procedure_subsections" in special_requirements:
        errors.extend(check_rollback_subsections(spec_content))

    # Return validation result
    is_valid = len(errors) == 0
    return is_valid, errors


def format_validation_report(work_item_id: str, work_item_type: str, errors: List[str]) -> str:
    """
    Format validation errors into a human-readable report.

    Args:
        work_item_id: ID of the work item
        work_item_type: Type of work item
        errors: List of validation error messages

    Returns:
        Formatted validation report
    """
    if not errors:
        return f"✅ Spec file for '{work_item_id}' ({work_item_type}) is valid"

    report = f"❌ Spec file for '{work_item_id}' ({work_item_type}) has validation errors:\n\n"

    for i, error in enumerate(errors, 1):
        report += f"{i}. {error}\n"

    report += "\n💡 Suggestions:\n"
    report += f"- Review the template at templates/{work_item_type}_spec.md\n"
    report += "- Check docs/spec-template-structure.md for section requirements\n"
    report += f"- Edit .session/specs/{work_item_id}.md to add missing sections\n"

    return report


# CLI interface for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python3 spec_validator.py <work_item_id> <work_item_type>")
        print("Example: python3 spec_validator.py feature_websocket_notifications feature")
        sys.exit(1)

    work_item_id = sys.argv[1]
    work_item_type = sys.argv[2]

    is_valid, errors = validate_spec_file(work_item_id, work_item_type)
    report = format_validation_report(work_item_id, work_item_type, errors)

    print(report)
    sys.exit(0 if is_valid else 1)
