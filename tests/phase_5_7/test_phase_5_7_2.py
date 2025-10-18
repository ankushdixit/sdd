#!/usr/bin/env python3
"""
Test script for Phase 5.7.2 - Spec Markdown Parsing Module

Tests the spec_parser.py module's ability to extract structured data
from work item specification markdown files.
"""

import sys
from pathlib import Path
import tempfile
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts import spec_parser


def test_strip_html_comments():
    """Test 1: HTML comment stripping"""
    print("\n" + "=" * 60)
    print("Test 1: Strip HTML Comments")
    print("=" * 60)

    content = """# Feature: Test
<!-- This is a comment -->
## Overview
This is content.
<!-- Another comment
spanning multiple lines -->
More content."""

    result = spec_parser.strip_html_comments(content)

    # Check that comments are removed
    assert "<!--" not in result
    assert "-->" not in result
    assert "This is content." in result
    assert "More content." in result

    print("✓ HTML comments stripped correctly")
    return True


def test_parse_section():
    """Test 2: Section extraction"""
    print("\n" + "=" * 60)
    print("Test 2: Parse Section")
    print("=" * 60)

    content = """# Feature: Test

## Overview
This is the overview section.
It has multiple lines.

## Rationale
This is the rationale section.

## Implementation Details
This is implementation."""

    overview = spec_parser.parse_section(content, 'Overview')
    rationale = spec_parser.parse_section(content, 'Rationale')
    missing = spec_parser.parse_section(content, 'NonExistent')

    assert overview == "This is the overview section.\nIt has multiple lines."
    assert rationale == "This is the rationale section."
    assert missing is None

    print("✓ Sections extracted correctly")
    print(f"  Overview: {len(overview)} chars")
    print(f"  Rationale: {len(rationale)} chars")
    print(f"  Missing section returns None: {missing is None}")
    return True


def test_extract_subsection():
    """Test 3: Subsection extraction"""
    print("\n" + "=" * 60)
    print("Test 3: Extract Subsection")
    print("=" * 60)

    section_content = """### Approach
Use WebSockets for real-time updates.

### Components Affected
- Frontend
- Backend

### API Changes
New endpoints here."""

    approach = spec_parser.extract_subsection(section_content, 'Approach')
    components = spec_parser.extract_subsection(section_content, 'Components Affected')
    missing = spec_parser.extract_subsection(section_content, 'NonExistent')

    assert "WebSockets" in approach
    assert "Frontend" in components
    assert missing is None

    print("✓ Subsections extracted correctly")
    return True


def test_extract_checklist():
    """Test 4: Checklist extraction"""
    print("\n" + "=" * 60)
    print("Test 4: Extract Checklist")
    print("=" * 60)

    content = """## Acceptance Criteria

- [ ] First item unchecked
- [x] Second item checked
- [ ] Third item unchecked
- [X] Fourth item checked (uppercase)

Some other text."""

    checklist = spec_parser.extract_checklist(content)

    assert len(checklist) == 4
    assert checklist[0] == {"text": "First item unchecked", "checked": False}
    assert checklist[1] == {"text": "Second item checked", "checked": True}
    assert checklist[2] == {"text": "Third item unchecked", "checked": False}
    assert checklist[3] == {"text": "Fourth item checked (uppercase)", "checked": True}

    print("✓ Checklist extracted correctly")
    print(f"  Found {len(checklist)} items")
    print(f"  Checked count: {sum(1 for item in checklist if item['checked'])}")
    return True


def test_extract_code_blocks():
    """Test 5: Code block extraction"""
    print("\n" + "=" * 60)
    print("Test 5: Extract Code Blocks")
    print("=" * 60)

    content = """## Implementation

```typescript
interface User {
  id: string;
  name: string;
}
```

Some text here.

```bash
npm install
npm test
```

```
Plain code block
```
"""

    code_blocks = spec_parser.extract_code_blocks(content)

    assert len(code_blocks) == 3
    assert code_blocks[0]["language"] == "typescript"
    assert "interface User" in code_blocks[0]["code"]
    assert code_blocks[1]["language"] == "bash"
    assert "npm install" in code_blocks[1]["code"]
    assert code_blocks[2]["language"] == "text"  # No language specified

    print("✓ Code blocks extracted correctly")
    print(f"  Found {len(code_blocks)} code blocks")
    for i, block in enumerate(code_blocks):
        print(f"  Block {i + 1}: {block['language']} ({len(block['code'])} chars)")
    return True


def test_extract_list_items():
    """Test 6: List item extraction"""
    print("\n" + "=" * 60)
    print("Test 6: Extract List Items")
    print("=" * 60)

    content = """## Components

- Frontend module
- Backend API
* Database schema
+ Configuration

1. First step
2. Second step
3. Third step
"""

    items = spec_parser.extract_list_items(content)

    assert len(items) == 7
    assert "Frontend module" in items
    assert "Backend API" in items
    assert "First step" in items
    assert "Third step" in items

    print("✓ List items extracted correctly")
    print(f"  Found {len(items)} items")
    return True


def test_parse_feature_spec():
    """Test 7: Parse feature specification"""
    print("\n" + "=" * 60)
    print("Test 7: Parse Feature Spec")
    print("=" * 60)

    content = """# Feature: Real-time Notifications

## Overview
Add real-time notifications to the dashboard.

## User Story
As a user, I want real-time notifications so that I stay updated.

## Rationale
Users need immediate feedback.

## Acceptance Criteria

- [ ] Notifications appear in real-time
- [ ] Users can dismiss notifications
- [x] Tests pass

## Implementation Details

### Approach
Use WebSockets for bidirectional communication.

### API Changes

```typescript
interface Notification {
  id: string;
  message: string;
}
```

## Testing Strategy
Write integration tests for WebSocket connections.

## Dependencies
Requires Socket.IO library.

## Estimated Effort
2 sessions
"""

    result = spec_parser.parse_feature_spec(content)

    assert result['overview'] == "Add real-time notifications to the dashboard."
    assert "real-time notifications" in result['user_story']
    assert "immediate feedback" in result['rationale']
    assert len(result['acceptance_criteria']) == 3
    assert result['acceptance_criteria'][0]['checked'] == False
    assert result['acceptance_criteria'][2]['checked'] == True
    assert result['implementation_details'] is not None
    assert "WebSockets" in result['implementation_details']['approach']
    assert len(result['implementation_details']['code_blocks']) == 1
    assert result['implementation_details']['code_blocks'][0]['language'] == 'typescript'
    assert "WebSocket" in result['testing_strategy']
    assert "Socket.IO" in result['dependencies']
    assert "2 sessions" in result['estimated_effort']

    print("✓ Feature spec parsed correctly")
    print(f"  Overview: {len(result['overview'])} chars")
    print(f"  Acceptance criteria: {len(result['acceptance_criteria'])} items")
    print(f"  Code blocks: {len(result['implementation_details']['code_blocks'])}")
    return True


def test_parse_bug_spec():
    """Test 8: Parse bug specification"""
    print("\n" + "=" * 60)
    print("Test 8: Parse Bug Spec")
    print("=" * 60)

    content = """# Bug: Session Timeout

## Description
Users are logged out unexpectedly.

## Steps to Reproduce
1. Login to the application
2. Wait 5 minutes
3. Try to perform an action

## Expected Behavior
Session should remain active.

## Actual Behavior
User is logged out after 5 minutes.

## Impact
**Severity:** High

## Root Cause Analysis

### Investigation
Reviewed session management code.

### Root Cause
Session timeout is set to 5 minutes instead of 30.

### Why It Happened
Configuration error during deployment.

## Fix Approach
Update session timeout configuration to 30 minutes.

## Prevention
Add configuration validation tests.

## Testing Strategy
Test session timeout with various durations.

## Dependencies
None

## Estimated Effort
1 session
"""

    result = spec_parser.parse_bug_spec(content)

    assert "logged out unexpectedly" in result['description']
    assert "Wait 5 minutes" in result['steps_to_reproduce']
    assert "remain active" in result['expected_behavior']
    assert "logged out after 5 minutes" in result['actual_behavior']
    assert "High" in result['impact']
    assert result['root_cause_analysis'] is not None
    assert "session management" in result['root_cause_analysis']['investigation']
    assert "5 minutes instead of 30" in result['root_cause_analysis']['root_cause']
    assert "Configuration error" in result['root_cause_analysis']['why_it_happened']
    assert "30 minutes" in result['fix_approach']
    assert "validation tests" in result['prevention']

    print("✓ Bug spec parsed correctly")
    print(f"  Description: {len(result['description'])} chars")
    print(f"  Root cause analysis sections: {len([k for k, v in result['root_cause_analysis'].items() if v])}")
    return True


def test_parse_refactor_spec():
    """Test 9: Parse refactor specification"""
    print("\n" + "=" * 60)
    print("Test 9: Parse Refactor Spec")
    print("=" * 60)

    content = """# Refactor: Dependency Injection

## Overview
Refactor service instantiation to use dependency injection.

## Current State
Services are instantiated with `new` keyword throughout the codebase.

## Problems with Current Approach
- Hard to test
- Tight coupling
- No lifecycle management

## Proposed Refactor

### New Approach
Use a DI container to manage service instances.

### Benefits
- Easier testing with mocks
- Loose coupling
- Better lifecycle control

### Trade-offs
- Additional complexity
- Learning curve

## Implementation Plan
1. Install DI library
2. Create container configuration
3. Refactor services one by one

## Scope

### In Scope
- User service
- Auth service
- Database service

### Out of Scope
- UI components
- External libraries

## Risk Assessment
**Risk Level:** Medium

## Success Criteria
- [ ] All services use DI
- [ ] Tests pass
- [x] Documentation updated

## Testing Strategy
Mock services in unit tests.

## Dependencies
Requires DI library installation.

## Estimated Effort
3 sessions
"""

    result = spec_parser.parse_refactor_spec(content)

    assert "dependency injection" in result['overview']
    assert "new` keyword" in result['current_state']
    assert "Hard to test" in result['problems']
    assert result['proposed_refactor'] is not None
    assert "DI container" in result['proposed_refactor']['new_approach']
    assert "Easier testing" in result['proposed_refactor']['benefits']
    assert "complexity" in result['proposed_refactor']['trade_offs']
    assert "Install DI library" in result['implementation_plan']
    assert result['scope'] is not None
    assert "User service" in result['scope']['in_scope']
    assert "UI components" in result['scope']['out_of_scope']
    assert "Medium" in result['risk_assessment']
    assert len(result['success_criteria']) == 3
    assert "Mock services" in result['testing_strategy']

    print("✓ Refactor spec parsed correctly")
    print(f"  Success criteria: {len(result['success_criteria'])} items")
    return True


def test_parse_security_spec():
    """Test 10: Parse security specification"""
    print("\n" + "=" * 60)
    print("Test 10: Parse Security Spec")
    print("=" * 60)

    content = """# Security: SQL Injection Vulnerability

## Security Issue
SQL injection vulnerability in user search endpoint.

## Severity
**CVSS Score:** 8.5 (High)

- [x] Critical
- [ ] High
- [ ] Medium

## Affected Components
- User API v2.1.0
- Database layer

## Threat Model

### Assets at Risk
- User database
- Personal information

### Threat Actors
- External attackers
- Malicious users

### Attack Scenarios
SQL injection through search parameter.

## Attack Vector
Unsanitized input in SQL query.

## Mitigation Strategy
Use parameterized queries for all database operations.

## Security Testing

### Automated Security Testing
Run SQL injection scanners.

### Manual Security Testing
Attempt injection attacks manually.

### Test Cases
- [ ] Test with malicious SQL
- [ ] Test with special characters
- [x] Verify parameterized queries

## Compliance
- [ ] OWASP Top 10
- [x] CWE-89
- [ ] PCI DSS

## Acceptance Criteria
- [ ] No SQL injection vulnerabilities
- [ ] All queries parameterized

## Post-Deployment
- [ ] Monitor for suspicious queries
- [ ] Set up alerts

## Dependencies
None

## Estimated Effort
1 session
"""

    result = spec_parser.parse_security_spec(content)

    assert "SQL injection" in result['security_issue']
    assert "8.5" in result['severity']
    assert "User API" in result['affected_components']
    assert result['threat_model'] is not None
    assert "User database" in result['threat_model']['assets_at_risk']
    assert "External attackers" in result['threat_model']['threat_actors']
    assert "search parameter" in result['threat_model']['attack_scenarios']
    assert "Unsanitized input" in result['attack_vector']
    assert "parameterized queries" in result['mitigation_strategy']
    assert result['security_testing'] is not None
    assert "SQL injection scanners" in result['security_testing']['automated']
    assert len(result['security_testing']['checklist']) == 3
    assert len(result['compliance']) >= 2
    assert len(result['acceptance_criteria']) == 2
    assert len(result['post_deployment']) == 2

    print("✓ Security spec parsed correctly")
    print(f"  Compliance items: {len(result['compliance'])}")
    print(f"  Security testing checklist: {len(result['security_testing']['checklist'])}")
    return True


def test_parse_integration_test_spec():
    """Test 11: Parse integration test specification"""
    print("\n" + "=" * 60)
    print("Test 11: Parse Integration Test Spec")
    print("=" * 60)

    content = """# Integration Test: Order Processing Flow

## Scope
Test the complete order processing workflow.

## Test Scenarios

### Scenario 1: Successful Order
User places an order and receives confirmation.

### Scenario 2: Payment Failure
User's payment fails and order is cancelled.

### Scenario 3: Inventory Check
Order fails if item is out of stock.

## Performance Benchmarks
**Response Time:** < 200ms
**Throughput:** 100 orders/second

## API Contracts
Order API v2.0 contracts.

## Environment Requirements
- PostgreSQL 14
- Redis 6.2
- Node.js 18

## Acceptance Criteria
- [ ] All scenarios pass
- [ ] Performance benchmarks met
- [x] Environment setup automated

## Dependencies
Requires order service deployment.

## Estimated Effort
2 sessions
"""

    result = spec_parser.parse_integration_test_spec(content)

    assert "order processing workflow" in result['scope']
    assert len(result['test_scenarios']) == 3
    assert result['test_scenarios'][0]['name'] == "Scenario 1: Successful Order"
    assert "confirmation" in result['test_scenarios'][0]['content']
    assert result['test_scenarios'][1]['name'] == "Scenario 2: Payment Failure"
    assert result['test_scenarios'][2]['name'] == "Scenario 3: Inventory Check"
    assert "200ms" in result['performance_benchmarks']
    assert "100 orders/second" in result['performance_benchmarks']
    assert "Order API" in result['api_contracts']
    assert "PostgreSQL" in result['environment_requirements']
    assert len(result['acceptance_criteria']) == 3

    print("✓ Integration test spec parsed correctly")
    print(f"  Test scenarios: {len(result['test_scenarios'])}")
    for scenario in result['test_scenarios']:
        print(f"    - {scenario['name']}")
    return True


def test_parse_deployment_spec():
    """Test 12: Parse deployment specification"""
    print("\n" + "=" * 60)
    print("Test 12: Parse Deployment Spec")
    print("=" * 60)

    content = """# Deployment: Production Release v2.0

## Deployment Scope
**Application:** Order API
**Version:** 2.0.0
**Environment:** Production

## Deployment Procedure

### Pre-Deployment Checklist
- [ ] Backup database
- [ ] Notify stakeholders

### Deployment Steps
1. Pull latest code
2. Build Docker image
3. Deploy to production

### Post-Deployment Steps
1. Run smoke tests
2. Verify metrics

## Environment Configuration
**Database URL:** postgresql://prod.example.com
**Redis URL:** redis://prod-cache.example.com

## Rollback Procedure

### Rollback Triggers
- Critical bugs detected
- Performance degradation

### Rollback Steps
1. Revert to previous Docker image
2. Clear cache
3. Verify rollback successful

## Smoke Tests

### Test 1: Health Check
Check /health endpoint returns 200.

### Test 2: Order Creation
Create a test order and verify response.

## Monitoring & Alerting
**Dashboard:** https://grafana.example.com/dashboard
**Alerts:** PagerDuty

## Post-Deployment Monitoring Period
**Soak Time:** 24 hours

## Acceptance Criteria
- [ ] All smoke tests pass
- [ ] No critical errors in logs
- [x] Monitoring configured

## Dependencies
None

## Estimated Effort
1 session
"""

    result = spec_parser.parse_deployment_spec(content)

    assert "Order API" in result['deployment_scope']
    assert result['deployment_procedure'] is not None
    assert "Backup database" in result['deployment_procedure']['pre_deployment']
    assert "Pull latest code" in result['deployment_procedure']['deployment_steps']
    assert "Run smoke tests" in result['deployment_procedure']['post_deployment']
    assert "postgresql://" in result['environment_configuration']
    assert result['rollback_procedure'] is not None
    assert "Critical bugs" in result['rollback_procedure']['triggers']
    assert "Revert to previous" in result['rollback_procedure']['steps']
    assert len(result['smoke_tests']) == 2
    assert result['smoke_tests'][0]['name'] == "Test 1: Health Check"
    assert "/health" in result['smoke_tests'][0]['content']
    assert "grafana" in result['monitoring']
    assert "24 hours" in result['monitoring_period']
    assert len(result['acceptance_criteria']) == 3

    print("✓ Deployment spec parsed correctly")
    print(f"  Smoke tests: {len(result['smoke_tests'])}")
    for test in result['smoke_tests']:
        print(f"    - {test['name']}")
    return True


def test_parse_spec_file_feature():
    """Test 13: Parse spec file (feature) - end-to-end"""
    print("\n" + "=" * 60)
    print("Test 13: Parse Spec File (Feature) - End-to-End")
    print("=" * 60)

    # Create a temporary spec file
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create .session/specs/ directory structure
        specs_dir = Path(tmpdir) / ".session" / "specs"
        specs_dir.mkdir(parents=True)

        spec_content = """# Feature: Test Feature

<!-- Template instructions here -->

## Overview
This is a test feature.

## Acceptance Criteria
- [ ] First criterion
- [ ] Second criterion

## Dependencies
None
"""

        spec_file = specs_dir / "feature_test.md"
        spec_file.write_text(spec_content)

        # Change to temp directory and parse
        original_dir = os.getcwd()
        try:
            os.chdir(tmpdir)
            result = spec_parser.parse_spec_file("feature_test")

            assert result['_meta']['work_item_id'] == "feature_test"
            assert result['_meta']['work_type'] == "feature"
            assert result['_meta']['name'] == "Test Feature"
            assert result['overview'] == "This is a test feature."
            assert len(result['acceptance_criteria']) == 2
            assert result['dependencies'] == "None"

            print("✓ Spec file parsed end-to-end successfully")
            print(f"  Work item ID: {result['_meta']['work_item_id']}")
            print(f"  Work type: {result['_meta']['work_type']}")
            print(f"  Name: {result['_meta']['name']}")
            return True
        finally:
            os.chdir(original_dir)


def test_parse_spec_file_errors():
    """Test 14: Error handling for invalid specs"""
    print("\n" + "=" * 60)
    print("Test 14: Error Handling")
    print("=" * 60)

    # Test 1: File not found
    try:
        spec_parser.parse_spec_file("nonexistent_file")
        print("✗ Should have raised FileNotFoundError")
        return False
    except FileNotFoundError as e:
        print(f"✓ FileNotFoundError raised correctly: {e}")

    # Test 2: Invalid heading format
    with tempfile.TemporaryDirectory() as tmpdir:
        specs_dir = Path(tmpdir) / ".session" / "specs"
        specs_dir.mkdir(parents=True)

        spec_file = specs_dir / "invalid_test.md"
        spec_file.write_text("Invalid content without proper heading")

        original_dir = os.getcwd()
        try:
            os.chdir(tmpdir)
            try:
                spec_parser.parse_spec_file("invalid_test")
                print("✗ Should have raised ValueError")
                return False
            except ValueError as e:
                print(f"✓ ValueError raised for invalid heading: {e}")
        finally:
            os.chdir(original_dir)

    # Test 3: Unknown work item type
    with tempfile.TemporaryDirectory() as tmpdir:
        specs_dir = Path(tmpdir) / ".session" / "specs"
        specs_dir.mkdir(parents=True)

        spec_file = specs_dir / "unknown_test.md"
        spec_file.write_text("# UnknownType: Test\n\nSome content")

        original_dir = os.getcwd()
        try:
            os.chdir(tmpdir)
            try:
                spec_parser.parse_spec_file("unknown_test")
                print("✗ Should have raised ValueError")
                return False
            except ValueError as e:
                print(f"✓ ValueError raised for unknown type: {e}")
        finally:
            os.chdir(original_dir)

    return True


def test_missing_sections_return_none():
    """Test 15: Missing sections return None gracefully"""
    print("\n" + "=" * 60)
    print("Test 15: Missing Sections Return None")
    print("=" * 60)

    # Feature spec with minimal content
    content = """# Feature: Minimal Feature

## Overview
Just an overview.

## Acceptance Criteria
- [ ] One criterion
"""

    result = spec_parser.parse_feature_spec(content)

    # Check that missing sections return None or empty
    assert result['overview'] == "Just an overview."
    assert result['user_story'] is None  # Not present
    assert result['rationale'] is None  # Not present
    assert len(result['acceptance_criteria']) == 1
    assert result['implementation_details'] is None  # Not present
    assert result['testing_strategy'] is None  # Not present
    assert result['documentation_updates'] == []  # Empty list for missing checklist
    assert result['dependencies'] is None  # Not present
    assert result['estimated_effort'] is None  # Not present

    print("✓ Missing sections handled gracefully")
    print("  Present sections: overview, acceptance_criteria")
    print("  Missing sections return None or empty")
    return True


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "=" * 80)
    print("PHASE 5.7.2 - SPEC MARKDOWN PARSING MODULE - TEST SUITE")
    print("=" * 80)

    tests = [
        test_strip_html_comments,
        test_parse_section,
        test_extract_subsection,
        test_extract_checklist,
        test_extract_code_blocks,
        test_extract_list_items,
        test_parse_feature_spec,
        test_parse_bug_spec,
        test_parse_refactor_spec,
        test_parse_security_spec,
        test_parse_integration_test_spec,
        test_parse_deployment_spec,
        test_parse_spec_file_feature,
        test_parse_spec_file_errors,
        test_missing_sections_return_none,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
                print(f"✗ {test.__name__} failed")
        except Exception as e:
            failed += 1
            print(f"✗ {test.__name__} raised exception: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed} ✓")
    print(f"Failed: {failed} ✗")
    print(f"Success rate: {(passed / len(tests) * 100):.1f}%")
    print("=" * 80)

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
