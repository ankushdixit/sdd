#!/usr/bin/env python3
"""
Spec Markdown Parsing Module

Parses work item specification files from .session/specs/ directory.
Extracts structured data from markdown for use by validators, runners, and quality gates.

Part of Phase 5.7.2: Spec File First Architecture
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from solokit.core.error_handlers import log_errors
from solokit.core.exceptions import (
    ErrorCode,
    ValidationError,
)
from solokit.core.exceptions import (
    FileNotFoundError as SolokitFileNotFoundError,
)
from solokit.core.logging_config import get_logger
from solokit.core.output import get_output
from solokit.core.types import WorkItemType

logger = get_logger(__name__)
output = get_output()


def strip_html_comments(content: str) -> str:
    """
    Remove all HTML comments from content.

    Args:
        content: Markdown content with possible HTML comments

    Returns:
        Content with all <!-- ... --> comments removed
    """
    # Remove HTML comments (including multiline)
    return re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)


def parse_section(content: str, section_name: str) -> str | None:
    """
    Extract content between '## SectionName' and next '##' heading.

    Args:
        content: Full markdown content (should have HTML comments stripped first)
        section_name: Name of section to extract (case-insensitive)

    Returns:
        Section content (excluding heading) or None if not found
    """
    lines = content.split("\n")
    in_section = False
    section_content = []

    for line in lines:
        # Check if this is an H2 heading
        if line.startswith("## "):
            heading = line[3:].strip()

            # Found our target section
            if heading.lower() == section_name.lower():
                in_section = True
                continue
            # Found next section, stop collecting
            elif in_section:
                break

        # Collect lines while in target section
        if in_section:
            section_content.append(line)

    # Return None if section not found
    if not section_content:
        return None

    # Return trimmed content
    return "\n".join(section_content).strip()


def extract_subsection(section_content: str, subsection_name: str) -> str | None:
    """
    Extract content under '### SubsectionName' within a section.

    Args:
        section_content: Content of a section (from parse_section)
        subsection_name: Name of subsection to extract (case-insensitive)

    Returns:
        Subsection content (excluding heading) or None if not found
    """
    if not section_content:
        return None

    lines = section_content.split("\n")
    in_subsection = False
    subsection_content = []

    for line in lines:
        # Check if this is an H3 heading
        if line.startswith("### "):
            heading = line[4:].strip()

            # Found our target subsection
            if heading.lower() == subsection_name.lower():
                in_subsection = True
                continue
            # Found next subsection, stop collecting
            elif in_subsection:
                break
        # H2 heading means we've left the parent section
        elif line.startswith("## ") and in_subsection:
            break

        # Collect lines while in target subsection
        if in_subsection:
            subsection_content.append(line)

    # Return None if subsection not found
    if not subsection_content:
        return None

    # Return trimmed content
    return "\n".join(subsection_content).strip()


def extract_checklist(content: str) -> list[dict[str, Any]]:
    """
    Extract checklist items from markdown.

    Args:
        content: Markdown content containing checklist items

    Returns:
        List of dicts with 'text' and 'checked' keys:
        [
            {"text": "Item text", "checked": False},
            {"text": "Checked item", "checked": True},
            ...
        ]
    """
    if not content:
        return []

    checklist = []
    for line in content.split("\n"):
        # Match checklist pattern: - [ ] or - [x]
        match = re.match(r"-\s+\[([ xX])\]\s+(.+)", line.strip())
        if match:
            checked = match.group(1).lower() == "x"
            text = match.group(2).strip()
            checklist.append({"text": text, "checked": checked})

    return checklist


def extract_code_blocks(content: str) -> list[dict[str, str]]:
    """
    Extract all code blocks from content.

    Args:
        content: Markdown content with code blocks

    Returns:
        List of dicts with 'language' and 'code' keys:
        [
            {"language": "typescript", "code": "..."},
            {"language": "bash", "code": "..."},
            ...
        ]
    """
    if not content:
        return []

    code_blocks = []

    # Pattern to match ```language\n...\n```
    pattern = r"```(\w+)?\n(.*?)```"
    matches = re.finditer(pattern, content, flags=re.DOTALL)

    for match in matches:
        language = match.group(1) or "text"  # Default to 'text' if no language specified
        code = match.group(2).strip()
        code_blocks.append({"language": language, "code": code})

    return code_blocks


def extract_list_items(content: str) -> list[str]:
    """
    Extract bullet point or numbered list items from content.

    Args:
        content: Markdown content with list items

    Returns:
        List of item text (without bullets/numbers)
    """
    if not content:
        return []

    items = []
    for line in content.split("\n"):
        # Match bullet points (-, *, +) or numbered lists (1., 2., etc.)
        match = re.match(r"^[\s]*(?:[-*+]|\d+\.)\s+(.+)", line)
        if match:
            items.append(match.group(1).strip())

    return items


# ============================================================================
# Work Item Type-Specific Parsers
# ============================================================================


def parse_feature_spec(content: str) -> dict[str, Any]:
    """
    Parse feature specification.

    Sections:
    - Overview
    - User Story
    - Rationale
    - Acceptance Criteria
    - Implementation Details (with subsections: Approach, Components Affected, API Changes, Database Changes)
    - Testing Strategy
    - Documentation Updates
    - Dependencies
    - Estimated Effort
    """
    # Strip HTML comments first
    content = strip_html_comments(content)

    result: dict[str, Any] = {}

    # Extract main sections
    result["overview"] = parse_section(content, "Overview")
    result["user_story"] = parse_section(content, "User Story")
    result["rationale"] = parse_section(content, "Rationale")

    # Acceptance Criteria - extract as checklist
    ac_section = parse_section(content, "Acceptance Criteria")
    result["acceptance_criteria"] = extract_checklist(ac_section) if ac_section else []

    # Implementation Details with subsections
    impl_section = parse_section(content, "Implementation Details")
    if impl_section:
        result["implementation_details"] = {
            "approach": extract_subsection(impl_section, "Approach"),
            "llm_processing_config": extract_subsection(
                impl_section, "LLM/Processing Configuration"
            ),
            "components_affected": extract_subsection(impl_section, "Components Affected"),
            "api_changes": extract_subsection(impl_section, "API Changes"),
            "database_changes": extract_subsection(impl_section, "Database Changes"),
            "code_blocks": extract_code_blocks(impl_section),
        }
    else:
        result["implementation_details"] = None

    # Testing Strategy
    result["testing_strategy"] = parse_section(content, "Testing Strategy")

    # Documentation Updates - extract as checklist
    doc_section = parse_section(content, "Documentation Updates")
    result["documentation_updates"] = extract_checklist(doc_section) if doc_section else []

    # Dependencies
    result["dependencies"] = parse_section(content, "Dependencies")

    # Estimated Effort
    result["estimated_effort"] = parse_section(content, "Estimated Effort")

    return result


def parse_bug_spec(content: str) -> dict[str, Any]:
    """
    Parse bug specification.

    Sections:
    - Description
    - Steps to Reproduce
    - Expected Behavior
    - Actual Behavior
    - Impact
    - Root Cause Analysis (with subsections: Investigation, Root Cause, Why It Happened)
    - Fix Approach
    - Prevention
    - Testing Strategy
    - Dependencies
    - Estimated Effort
    """
    # Strip HTML comments first
    content = strip_html_comments(content)

    result: dict[str, Any] = {}

    # Extract main sections
    result["description"] = parse_section(content, "Description")
    result["steps_to_reproduce"] = parse_section(content, "Steps to Reproduce")
    result["expected_behavior"] = parse_section(content, "Expected Behavior")
    result["actual_behavior"] = parse_section(content, "Actual Behavior")
    result["impact"] = parse_section(content, "Impact")

    # Root Cause Analysis with subsections
    rca_section = parse_section(content, "Root Cause Analysis")
    if rca_section:
        result["root_cause_analysis"] = {
            "investigation": extract_subsection(rca_section, "Investigation"),
            "root_cause": extract_subsection(rca_section, "Root Cause"),
            "why_it_happened": extract_subsection(rca_section, "Why It Happened"),
            "code_blocks": extract_code_blocks(rca_section),
        }
    else:
        result["root_cause_analysis"] = None

    # Fix Approach
    result["fix_approach"] = parse_section(content, "Fix Approach")

    # Prevention
    result["prevention"] = parse_section(content, "Prevention")

    # Testing Strategy
    result["testing_strategy"] = parse_section(content, "Testing Strategy")

    # Acceptance Criteria - extract as checklist
    ac_section = parse_section(content, "Acceptance Criteria")
    result["acceptance_criteria"] = extract_checklist(ac_section) if ac_section else []

    # Dependencies
    result["dependencies"] = parse_section(content, "Dependencies")

    # Estimated Effort
    result["estimated_effort"] = parse_section(content, "Estimated Effort")

    return result


def parse_refactor_spec(content: str) -> dict[str, Any]:
    """
    Parse refactor specification.

    Sections:
    - Overview
    - Current State
    - Problems with Current Approach
    - Proposed Refactor (with subsections: New Approach, Benefits, Trade-offs)
    - Implementation Plan
    - Scope (with subsections: In Scope, Out of Scope)
    - Risk Assessment
    - Acceptance Criteria
    - Testing Strategy
    - Dependencies
    - Estimated Effort
    """
    # Strip HTML comments first
    content = strip_html_comments(content)

    result: dict[str, Any] = {}

    # Extract main sections
    result["overview"] = parse_section(content, "Overview")
    result["current_state"] = parse_section(content, "Current State")
    result["problems"] = parse_section(content, "Problems with Current Approach")

    # Proposed Refactor with subsections
    refactor_section = parse_section(content, "Proposed Refactor")
    if refactor_section:
        result["proposed_refactor"] = {
            "new_approach": extract_subsection(refactor_section, "New Approach"),
            "benefits": extract_subsection(refactor_section, "Benefits"),
            "trade_offs": extract_subsection(refactor_section, "Trade-offs"),
            "code_blocks": extract_code_blocks(refactor_section),
        }
    else:
        result["proposed_refactor"] = None

    # Implementation Plan
    result["implementation_plan"] = parse_section(content, "Implementation Plan")

    # Scope with subsections
    scope_section = parse_section(content, "Scope")
    if scope_section:
        result["scope"] = {
            "in_scope": extract_subsection(scope_section, "In Scope"),
            "out_of_scope": extract_subsection(scope_section, "Out of Scope"),
        }
    else:
        result["scope"] = None

    # Risk Assessment
    result["risk_assessment"] = parse_section(content, "Risk Assessment")

    # Acceptance Criteria - extract as checklist
    ac_section = parse_section(content, "Acceptance Criteria")
    result["acceptance_criteria"] = extract_checklist(ac_section) if ac_section else []

    # Testing Strategy
    result["testing_strategy"] = parse_section(content, "Testing Strategy")

    # Dependencies
    result["dependencies"] = parse_section(content, "Dependencies")

    # Estimated Effort
    result["estimated_effort"] = parse_section(content, "Estimated Effort")

    return result


def parse_security_spec(content: str) -> dict[str, Any]:
    """
    Parse security specification.

    Sections:
    - Security Issue
    - Severity
    - Affected Components
    - Threat Model (with subsections: Assets at Risk, Threat Actors, Attack Scenarios)
    - Attack Vector
    - Mitigation Strategy
    - Security Testing (with subsections: Automated Security Testing, Manual Security Testing, Test Cases)
    - Compliance
    - Acceptance Criteria
    - Post-Deployment
    - Dependencies
    - Estimated Effort
    """
    # Strip HTML comments first
    content = strip_html_comments(content)

    result: dict[str, Any] = {}

    # Extract main sections
    result["security_issue"] = parse_section(content, "Security Issue")
    result["severity"] = parse_section(content, "Severity")
    result["affected_components"] = parse_section(content, "Affected Components")

    # Threat Model with subsections
    threat_section = parse_section(content, "Threat Model")
    if threat_section:
        result["threat_model"] = {
            "assets_at_risk": extract_subsection(threat_section, "Assets at Risk"),
            "threat_actors": extract_subsection(threat_section, "Threat Actors"),
            "attack_scenarios": extract_subsection(threat_section, "Attack Scenarios"),
            "code_blocks": extract_code_blocks(threat_section),
        }
    else:
        result["threat_model"] = None

    # Attack Vector
    result["attack_vector"] = parse_section(content, "Attack Vector")

    # Mitigation Strategy
    result["mitigation_strategy"] = parse_section(content, "Mitigation Strategy")

    # Security Testing with subsections
    testing_section = parse_section(content, "Security Testing")
    if testing_section:
        result["security_testing"] = {
            "automated": extract_subsection(testing_section, "Automated Security Testing"),
            "manual": extract_subsection(testing_section, "Manual Security Testing"),
            "test_cases": extract_subsection(testing_section, "Test Cases"),
            "checklist": extract_checklist(testing_section),
        }
    else:
        result["security_testing"] = None

    # Compliance - extract as checklist
    compliance_section = parse_section(content, "Compliance")
    result["compliance"] = extract_checklist(compliance_section) if compliance_section else []

    # Acceptance Criteria - extract as checklist
    ac_section = parse_section(content, "Acceptance Criteria")
    result["acceptance_criteria"] = extract_checklist(ac_section) if ac_section else []

    # Post-Deployment
    post_section = parse_section(content, "Post-Deployment")
    result["post_deployment"] = extract_checklist(post_section) if post_section else []

    # Dependencies
    result["dependencies"] = parse_section(content, "Dependencies")

    # Estimated Effort
    result["estimated_effort"] = parse_section(content, "Estimated Effort")

    return result


def parse_integration_test_spec(content: str) -> dict[str, Any]:
    """
    Parse integration test specification.

    Sections:
    - Scope
    - Test Scenarios (multiple subsections: Scenario 1, Scenario 2, etc.)
    - Performance Benchmarks
    - API Contracts
    - Environment Requirements
    - Acceptance Criteria
    - Dependencies
    - Estimated Effort
    """
    # Strip HTML comments first
    content = strip_html_comments(content)

    result: dict[str, Any] = {}

    # Extract main sections
    result["scope"] = parse_section(content, "Scope")

    # Test Scenarios - extract all scenarios
    scenarios_section = parse_section(content, "Test Scenarios")
    if scenarios_section:
        # Find all subsections that start with "Scenario"
        scenarios = []
        lines = scenarios_section.split("\n")
        current_scenario: str | None = None
        current_content: list[str] = []

        for line in lines:
            if line.startswith("### Scenario"):
                # Save previous scenario if exists
                if current_scenario is not None:
                    scenarios.append(
                        {
                            "name": current_scenario,
                            "content": "\n".join(current_content).strip(),
                        }
                    )
                # Start new scenario
                current_scenario = line[4:].strip()  # Remove '### '
                current_content = []
            elif current_scenario:
                current_content.append(line)

        # Save last scenario
        if current_scenario is not None:
            scenarios.append(
                {
                    "name": current_scenario,
                    "content": "\n".join(current_content).strip(),
                }
            )

        result["test_scenarios"] = scenarios
    else:
        result["test_scenarios"] = []

    # Performance Benchmarks
    result["performance_benchmarks"] = parse_section(content, "Performance Benchmarks")

    # API Contracts
    result["api_contracts"] = parse_section(content, "API Contracts")

    # Environment Requirements
    result["environment_requirements"] = parse_section(content, "Environment Requirements")

    # Acceptance Criteria - extract as checklist
    ac_section = parse_section(content, "Acceptance Criteria")
    result["acceptance_criteria"] = extract_checklist(ac_section) if ac_section else []

    # Dependencies
    result["dependencies"] = parse_section(content, "Dependencies")

    # Estimated Effort
    result["estimated_effort"] = parse_section(content, "Estimated Effort")

    return result


def parse_deployment_spec(content: str) -> dict[str, Any]:
    """
    Parse deployment specification.

    Sections:
    - Deployment Scope
    - Deployment Procedure (with subsections: Pre-Deployment Checklist, Deployment Steps, Post-Deployment Steps)
    - Environment Configuration
    - Rollback Procedure (with subsections: Rollback Triggers, Rollback Steps)
    - Smoke Tests (multiple subsections: Test 1, Test 2, etc.)
    - Monitoring & Alerting
    - Post-Deployment Monitoring Period
    - Acceptance Criteria
    - Dependencies
    - Estimated Effort
    """
    # Strip HTML comments first
    content = strip_html_comments(content)

    result: dict[str, Any] = {}

    # Extract main sections
    result["deployment_scope"] = parse_section(content, "Deployment Scope")

    # Deployment Procedure with subsections
    procedure_section = parse_section(content, "Deployment Procedure")
    if procedure_section:
        result["deployment_procedure"] = {
            "pre_deployment": extract_subsection(procedure_section, "Pre-Deployment Checklist"),
            "deployment_steps": extract_subsection(procedure_section, "Deployment Steps"),
            "post_deployment": extract_subsection(procedure_section, "Post-Deployment Steps"),
            "code_blocks": extract_code_blocks(procedure_section),
            "checklist": extract_checklist(procedure_section),
        }
    else:
        result["deployment_procedure"] = None

    # Environment Configuration
    result["environment_configuration"] = parse_section(content, "Environment Configuration")

    # Rollback Procedure with subsections
    rollback_section = parse_section(content, "Rollback Procedure")
    if rollback_section:
        result["rollback_procedure"] = {
            "triggers": extract_subsection(rollback_section, "Rollback Triggers"),
            "steps": extract_subsection(rollback_section, "Rollback Steps"),
            "code_blocks": extract_code_blocks(rollback_section),
        }
    else:
        result["rollback_procedure"] = None

    # Smoke Tests - extract all tests
    smoke_section = parse_section(content, "Smoke Tests")
    if smoke_section:
        # Find all subsections that start with "Test"
        tests = []
        lines = smoke_section.split("\n")
        current_test: str | None = None
        current_content: list[str] = []

        for line in lines:
            if line.startswith("### Test"):
                # Save previous test if exists
                if current_test is not None:
                    tests.append(
                        {
                            "name": current_test,
                            "content": "\n".join(current_content).strip(),
                        }
                    )
                # Start new test
                current_test = line[4:].strip()  # Remove '### '
                current_content = []
            elif current_test:
                current_content.append(line)

        # Save last test
        if current_test is not None:
            tests.append({"name": current_test, "content": "\n".join(current_content).strip()})

        result["smoke_tests"] = tests
    else:
        result["smoke_tests"] = []

    # Monitoring & Alerting
    result["monitoring"] = parse_section(content, "Monitoring & Alerting")

    # Post-Deployment Monitoring Period
    result["monitoring_period"] = parse_section(content, "Post-Deployment Monitoring Period")

    # Acceptance Criteria - extract as checklist
    ac_section = parse_section(content, "Acceptance Criteria")
    result["acceptance_criteria"] = extract_checklist(ac_section) if ac_section else []

    # Dependencies
    result["dependencies"] = parse_section(content, "Dependencies")

    # Estimated Effort
    result["estimated_effort"] = parse_section(content, "Estimated Effort")

    return result


# ============================================================================
# Main Entry Point
# ============================================================================


@log_errors()
def parse_spec_file(work_item: str | dict[str, Any]) -> dict[str, Any]:
    """
    Parse a work item specification file.

    Args:
        work_item: Either a work item dict with 'spec_file' and 'id' fields,
                  or a string work_item_id (for backwards compatibility)

    Returns:
        Parsed specification as structured dict

    Raises:
        FileNotFoundError: If spec file doesn't exist
        ValidationError: If work item type cannot be determined or spec format is invalid
        SpecValidationError: If spec file structure is invalid
    """
    # Handle backwards compatibility: accept both dict and string
    if isinstance(work_item, str):
        # Legacy call with just work_item_id string
        work_item_id: str | Any | None = work_item
        spec_path = Path(f".session/specs/{work_item_id}.md")
        logger.debug("Parsing spec file for work item (legacy): %s", work_item_id)
    else:
        # New call with work item dict
        work_item_id = work_item.get("id")
        # Use spec_file from work item if available, otherwise fallback to ID-based pattern
        spec_file_path = work_item.get("spec_file")
        if spec_file_path:
            spec_path = Path(spec_file_path)
            logger.debug("Parsing spec file from work_item.spec_file: %s", spec_path)
        else:
            # Fallback to legacy pattern for backwards compatibility
            spec_path = Path(f".session/specs/{work_item_id}.md")
            logger.debug("Parsing spec file (fallback to ID pattern): %s", spec_path)

    if not spec_path.exists():
        logger.error("Spec file not found: %s", spec_path)
        raise SolokitFileNotFoundError(file_path=str(spec_path), file_type="spec")

    try:
        with open(spec_path, encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        logger.error("Failed to read spec file: %s", spec_path)
        raise ValidationError(
            message=f"Failed to read spec file: {spec_path}",
            code=ErrorCode.FILE_OPERATION_FAILED,
            context={"file_path": str(spec_path)},
            remediation="Check file permissions and try again",
            cause=e,
        )

    # Determine work item type from first line (H1 heading)
    first_line = content.split("\n")[0].strip()
    if not first_line.startswith("# "):
        logger.error("Invalid spec file: Missing H1 heading in %s", spec_path)
        raise ValidationError(
            message=f"Invalid spec file: Missing H1 heading in {spec_path}",
            code=ErrorCode.SPEC_VALIDATION_FAILED,
            context={"file_path": str(spec_path), "first_line": first_line},
            remediation="Spec file must start with '# Type: Name' heading",
        )

    # Extract type from "# Type: Name" pattern
    heading_match = re.match(r"#\s*(\w+):\s*(.+)", first_line)
    if not heading_match:
        logger.error("Invalid spec file: H1 heading doesn't match pattern in %s", spec_path)
        raise ValidationError(
            message=f"Invalid spec file: H1 heading doesn't match 'Type: Name' pattern in {spec_path}",
            code=ErrorCode.SPEC_VALIDATION_FAILED,
            context={"file_path": str(spec_path), "heading": first_line},
            remediation="Use format: '# Type: Name' (e.g., '# Feature: My Feature')",
        )

    work_type = heading_match.group(1).lower()
    work_name = heading_match.group(2).strip()
    logger.debug("Detected work type: %s, name: %s", work_type, work_name)

    # Parse based on work item type
    parsers = {
        WorkItemType.FEATURE.value: parse_feature_spec,
        WorkItemType.BUG.value: parse_bug_spec,
        WorkItemType.REFACTOR.value: parse_refactor_spec,
        WorkItemType.SECURITY.value: parse_security_spec,
        WorkItemType.INTEGRATION_TEST.value: parse_integration_test_spec,
        WorkItemType.DEPLOYMENT.value: parse_deployment_spec,
    }

    parser = parsers.get(work_type)
    if not parser:
        valid_types = ", ".join(parsers.keys())
        raise ValidationError(
            message=f"Unknown work item type: {work_type}",
            code=ErrorCode.INVALID_WORK_ITEM_TYPE,
            context={
                "work_type": work_type,
                "valid_types": list(parsers.keys()),
                "file_path": str(spec_path),
            },
            remediation=f"Use one of: {valid_types}",
        )

    # Parse the spec
    try:
        parsed = parser(content)
        parsed["_meta"] = {
            "work_item_id": work_item_id,
            "work_type": work_type,
            "name": work_name,
            "spec_path": str(spec_path),
        }
        return parsed
    except ValidationError:
        # Re-raise ValidationError as-is
        raise
    except Exception as e:
        # Wrap unexpected errors in ValidationError
        logger.error("Error parsing spec file %s: %s", spec_path, str(e))
        raise ValidationError(
            message=f"Error parsing spec file {spec_path}",
            code=ErrorCode.SPEC_VALIDATION_FAILED,
            context={"file_path": str(spec_path), "work_type": work_type, "error": str(e)},
            remediation="Check spec file format and content",
            cause=e,
        )


# ============================================================================
# CLI Interface for Testing
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        output.info("Usage: spec_parser.py <work_item_id>")
        output.info("Example: spec_parser.py feature_001")
        sys.exit(1)

    work_item_id = sys.argv[1]

    try:
        logger.info("Parsing spec file for work item: %s", work_item_id)
        result = parse_spec_file(work_item_id)
        output.info(json.dumps(result, indent=2))
    except Exception as e:
        logger.error("Failed to parse spec file", exc_info=True)
        output.error(f"Error: {e}")
        sys.exit(1)
