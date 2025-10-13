# Work Item Types

This document defines the work item types supported by the Session-Driven Development plugin.

## Standard Work Item Types

### feature
Standard feature development work items.
- **Template:** Feature specification
- **Typical sessions:** 2-4
- **Validation:** Tests pass, linting pass, documentation updated

### bug
Bug fix work items.
- **Template:** Bug report
- **Typical sessions:** 1-2
- **Validation:** Tests pass, regression tests added, root cause documented

### refactor
Code refactoring work items.
- **Template:** Refactor plan
- **Typical sessions:** 1-3
- **Validation:** Tests pass, no functionality changes, code quality improved

## Integration & Deployment Types (Phase 1.8)

### integration_test
Integration testing work items that validate multiple components working together.
- **Template:** `templates/integration_test_spec.md`
- **Typical sessions:** 1-2
- **Validation:**
  - Integration tests pass
  - End-to-end tests pass
  - Performance benchmarks met
  - API contracts validated
- **Dependencies:** Required (must specify what components are being integrated)

**Usage:**
```json
{
  "type": "integration_test",
  "title": "Test OAuth + User Profile Integration",
  "dependencies": ["feature_oauth", "feature_profile"],
  "validation_criteria": {
    "integration_tests_pass": true,
    "e2e_tests_pass": true,
    "performance_benchmarks_met": true,
    "api_contracts_validated": true
  }
}
```

### deployment
Deployment work items for releasing code to environments.
- **Template:** `templates/deployment_spec.md`
- **Typical sessions:** 1
- **Validation:**
  - Deployment successful
  - Smoke tests pass
  - Monitoring operational
  - Rollback tested
  - Documentation updated
- **Dependencies:** Required (must specify what features/fixes are being deployed)

**Usage:**
```json
{
  "type": "deployment",
  "title": "Deploy v1.2.0 to Production",
  "dependencies": ["feature_oauth", "feature_profile", "integration_test_auth"],
  "validation_criteria": {
    "deployment_successful": true,
    "smoke_tests_pass": true,
    "monitoring_operational": true,
    "rollback_tested": true,
    "documentation_updated": true
  }
}
```

## Validation Rules

### All Types
- Must have a title
- Must have a type from the list above
- Must have a status (not_started, in_progress, completed)
- Must have a priority (critical, high, medium, low)

### integration_test and deployment
- **Must have dependencies** - Cannot be created without specifying dependencies
- **Phase-specific validation** - Additional validation criteria enforced
- **Typical workflow:**
  1. Complete all dependent work items
  2. Create integration_test to validate integration
  3. Complete integration tests
  4. Create deployment to deploy to environment
  5. Complete deployment with smoke tests

## Work Item Lifecycle

```
not_started → in_progress → completed
     ↓              ↓
  blocked      blocked
```

**Status definitions:**
- `not_started` - Ready to begin, dependencies satisfied
- `in_progress` - Currently being worked on
- `blocked` - Waiting on dependency or external factor
- `completed` - Work finished and validated
