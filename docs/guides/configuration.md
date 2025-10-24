# SDD Configuration

SDD uses JSON-based configuration stored in `.session/config.json`. The configuration is automatically validated against a JSON schema to catch errors early.

## Configuration Schema

Configuration is validated against `.session/config.schema.json` to catch errors early with helpful error messages.

## Configuration Structure

The configuration file is organized into several top-level sections:

### Quality Gates

Controls which quality gates are enforced during session completion.

```json
{
  "quality_gates": {
    "test": {
      "required": true,
      "command": "pytest tests/",
      "timeout": 300
    },
    "lint": {
      "required": false,
      "command": "ruff check .",
      "timeout": 60
    },
    "security": {
      "required": true,
      "severity": "high",
      "timeout": 120
    },
    "format": {
      "required": false,
      "auto_fix": true,
      "command": "ruff format .",
      "timeout": 60
    },
    "documentation": {
      "required": false,
      "check_changelog": true,
      "check_docstrings": true
    },
    "spec_completeness": {
      "required": true
    }
  }
}
```

**Field Descriptions:**
- `required` (boolean): If true, session cannot complete if this gate fails
- `command` (string): Command to execute for this gate
- `timeout` (integer): Timeout in seconds (minimum 1)
- `severity` (string): For security gates, one of: "critical", "high", "medium", "low"
- `auto_fix` (boolean): For format gates, automatically fix issues
- `check_changelog` (boolean): Validate CHANGELOG.md was updated
- `check_docstrings` (boolean): Check Python docstrings with pydocstyle

### Learning System

Controls learning capture and curation behavior.

```json
{
  "learning": {
    "auto_curate_frequency": 5,
    "similarity_threshold": 0.7,
    "containment_threshold": 0.8
  }
}
```

**Field Descriptions:**
- `auto_curate_frequency` (integer): Auto-curate every N sessions (minimum 1)
- `similarity_threshold` (number): Jaccard similarity threshold for duplicate detection (0.0-1.0)
- `containment_threshold` (number): Containment similarity threshold for duplicate detection (0.0-1.0)

### Session Management

Controls session workflow behavior.

```json
{
  "session": {
    "auto_commit": false,
    "require_work_item": true
  }
}
```

**Field Descriptions:**
- `auto_commit` (boolean): Automatically commit changes on session end
- `require_work_item` (boolean): Require work item for session start

### Deployment

Controls deployment workflow and validation.

```json
{
  "deployment": {
    "pre_deployment_checks": {
      "integration_tests": true,
      "security_scans": true,
      "environment_validation": true
    },
    "smoke_tests": {
      "enabled": true,
      "timeout": 300,
      "retry_count": 3
    },
    "rollback": {
      "automatic": true,
      "on_smoke_test_failure": true,
      "on_error_threshold": true,
      "error_threshold_percent": 5
    },
    "environments": {
      "staging": {
        "auto_deploy": true,
        "require_approval": false
      },
      "production": {
        "auto_deploy": false,
        "require_approval": true
      }
    }
  }
}
```

**Field Descriptions:**
- `pre_deployment_checks`: Validation before deployment execution
  - `integration_tests` (boolean): Run integration tests before deploying
  - `security_scans` (boolean): Run security scans before deploying
  - `environment_validation` (boolean): Validate environment readiness
- `smoke_tests`: Post-deployment validation
  - `enabled` (boolean): Run smoke tests after deployment
  - `timeout` (integer): Smoke test timeout in seconds
  - `retry_count` (integer): Number of retries for failed smoke tests (minimum 0)
- `rollback`: Automatic rollback configuration
  - `automatic` (boolean): Enable automatic rollback
  - `on_smoke_test_failure` (boolean): Rollback if smoke tests fail
  - `on_error_threshold` (boolean): Rollback if error rate exceeds threshold
  - `error_threshold_percent` (integer): Error rate percentage threshold (0-100)
- `environments`: Per-environment deployment settings
  - `auto_deploy` (boolean): Automatically deploy to this environment
  - `require_approval` (boolean): Require manual approval before deployment

## Example Configuration

Here's a complete example configuration file:

```json
{
  "quality_gates": {
    "test": {
      "required": true,
      "command": "pytest tests/ -v",
      "timeout": 300
    },
    "lint": {
      "required": false,
      "command": "ruff check scripts/ tests/",
      "timeout": 60
    },
    "security": {
      "required": true,
      "severity": "high",
      "timeout": 120
    },
    "format": {
      "required": false,
      "auto_fix": true,
      "command": "ruff format scripts/ tests/",
      "timeout": 60
    },
    "documentation": {
      "required": false,
      "check_changelog": true,
      "check_docstrings": false
    },
    "spec_completeness": {
      "required": true
    }
  },
  "learning": {
    "auto_curate_frequency": 5,
    "similarity_threshold": 0.7,
    "containment_threshold": 0.8
  },
  "session": {
    "auto_commit": false,
    "require_work_item": true
  },
  "deployment": {
    "pre_deployment_checks": {
      "integration_tests": true,
      "security_scans": true,
      "environment_validation": true
    },
    "smoke_tests": {
      "enabled": true,
      "timeout": 300,
      "retry_count": 3
    },
    "rollback": {
      "automatic": true,
      "on_smoke_test_failure": true,
      "on_error_threshold": true,
      "error_threshold_percent": 5
    },
    "environments": {
      "staging": {
        "auto_deploy": true,
        "require_approval": false
      },
      "production": {
        "auto_deploy": false,
        "require_approval": true
      }
    }
  }
}
```

## Validation

Configuration is automatically validated when loaded. If validation fails:

1. Error messages show exactly what's wrong
2. System falls back to default configuration
3. Session continues (graceful degradation)

### Running Manual Validation

You can manually validate your configuration:

```bash
# Validate with automatic schema detection
python3 scripts/config_validator.py .session/config.json

# Validate with explicit schema path
python3 scripts/config_validator.py .session/config.json .session/config.schema.json
```

### Common Validation Errors

**Wrong type**:
```
Validation error at 'quality_gates -> test -> required': 'true' is not of type 'boolean'
```
**Fix**: Change `"required": "true"` to `"required": true` (remove quotes)

**Invalid value**:
```
Validation error at 'learning -> similarity_threshold': 1.5 is greater than the maximum of 1
```
**Fix**: Use value between 0.0 and 1.0

**Invalid enum value**:
```
Validation error at 'quality_gates -> security -> severity': 'critical+' is not one of ['critical', 'high', 'medium', 'low']
```
**Fix**: Use one of the valid severity levels

**Missing required field**:
```
Validation error at 'quality_gates -> test': 'required' is a required property
```
**Fix**: Add `"required": true` or `"required": false`

**Invalid number**:
```
Validation error at 'quality_gates -> test -> timeout': 0 is less than the minimum of 1
```
**Fix**: Use timeout value of at least 1 second

## Default Configuration

If `.session/config.json` doesn't exist or validation fails, SDD uses these defaults:

```json
{
  "quality_gates": {
    "test_execution": {
      "enabled": true,
      "required": true,
      "command": "pytest tests/ -v",
      "timeout": 300
    },
    "lint": {
      "enabled": true,
      "required": false,
      "command": "ruff check scripts/ tests/",
      "timeout": 60
    },
    "security_scan": {
      "enabled": true,
      "required": true,
      "severity": "high",
      "timeout": 120
    },
    "format_check": {
      "enabled": true,
      "required": false,
      "auto_fix": false,
      "command": "ruff format --check scripts/ tests/",
      "timeout": 60
    },
    "spec_completeness": {
      "enabled": true,
      "required": true
    }
  },
  "learning": {
    "auto_curate_frequency": 5,
    "similarity_threshold": 0.7,
    "containment_threshold": 0.8
  }
}
```

## Modifying Configuration

To modify configuration:

1. Edit `.session/config.json` directly
2. Validate using `python3 scripts/config_validator.py .session/config.json`
3. Fix any validation errors
4. Re-run your session commands

**Note**: Configuration changes take effect immediately on the next command that loads configuration (typically `/start` or `/end`).

## Schema Reference

The complete JSON schema is available at `.session/config.schema.json`. The schema defines:

- Required vs optional fields
- Valid data types for each field
- Minimum/maximum values for numbers
- Enumerated values for strings (e.g., severity levels)
- Default values and descriptions

## Best Practices

1. **Start with defaults**: Use the default configuration created by `/init` and customize as needed
2. **Validate early**: Run `config_validator.py` after making changes
3. **Required gates**: Keep critical gates (tests, security, spec_completeness) as required
4. **Optional gates**: Make formatting and linting optional to avoid blocking development
5. **Auto-fix**: Enable `auto_fix` for formatting to automatically fix issues
6. **Timeouts**: Set realistic timeouts based on your project size
7. **Thresholds**: Adjust similarity thresholds (0.6-0.8 typical) based on learning deduplication needs

## Troubleshooting

### Configuration not loading

**Symptom**: Default configuration used despite having `.session/config.json`

**Possible causes**:
1. Invalid JSON syntax - check for missing commas, quotes
2. Validation errors - run `config_validator.py` to see errors
3. File permissions - ensure file is readable

**Solution**:
```bash
# Check JSON syntax
python3 -m json.tool .session/config.json

# Validate against schema
python3 scripts/config_validator.py .session/config.json
```

### jsonschema not installed

**Symptom**: Warning message "jsonschema not installed, skipping validation"

**Solution**:
```bash
pip install -r requirements.txt
```

### Schema file missing

**Symptom**: Warning message "Schema file not found"

**Solution**: Re-run `/init` to recreate schema file, or copy from repository:
```bash
cp templates/config.schema.json path/to/your/project/.session/
```

## Related Documentation

- [Session-Driven Development Methodology](./session-driven-development.md)
- [Quality Gates](../scripts/quality_gates.py)
- [Learning System](./learning-system.md)
- [Writing Specs](./writing-specs.md)
