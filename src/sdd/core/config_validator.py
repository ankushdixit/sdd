#!/usr/bin/env python3
"""Configuration validation using JSON schema."""

import json
import logging
from pathlib import Path
from typing import Any

from sdd.core.error_handlers import log_errors
from sdd.core.exceptions import (
    ConfigurationError,
    ConfigValidationError,
    ErrorCode,
    ValidationError,
)
from sdd.core.exceptions import (
    FileNotFoundError as SDDFileNotFoundError,
)

logger = logging.getLogger(__name__)


@log_errors()
def validate_config(config_path: Path, schema_path: Path) -> dict[str, Any]:
    """
    Validate configuration against JSON schema.

    Args:
        config_path: Path to config.json
        schema_path: Path to config.schema.json

    Returns:
        Validated configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValidationError: If config JSON is malformed
        ConfigurationError: If schema is invalid or malformed
        ConfigValidationError: If config fails schema validation
    """
    try:
        import jsonschema
    except ImportError:
        # If jsonschema not installed, skip validation but warn
        logger.warning("jsonschema not installed, skipping validation")
        # Still try to load and return config
        if not config_path.exists():
            raise SDDFileNotFoundError(str(config_path), file_type="config")
        try:
            with open(config_path) as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValidationError(
                message=f"Invalid JSON in config file: {config_path}",
                code=ErrorCode.INVALID_JSON,
                context={"file_path": str(config_path), "error": str(e)},
                remediation="Fix JSON syntax errors in config file",
                cause=e,
            ) from e

    # Load config
    if not config_path.exists():
        raise SDDFileNotFoundError(str(config_path), file_type="config")

    try:
        with open(config_path) as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        raise ValidationError(
            message=f"Invalid JSON in config file: {config_path}",
            code=ErrorCode.INVALID_JSON,
            context={"file_path": str(config_path), "error": str(e)},
            remediation="Fix JSON syntax errors in config file",
            cause=e,
        ) from e

    # Load schema
    if not schema_path.exists():
        # Schema missing is a warning, not an error - allow validation to be skipped
        logger.warning(f"Schema file not found: {schema_path}, skipping validation")
        return config

    try:
        with open(schema_path) as f:
            schema = json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigurationError(
            message=f"Invalid JSON in schema file: {schema_path}",
            code=ErrorCode.INVALID_CONFIG_VALUE,
            context={"file_path": str(schema_path), "error": str(e)},
            remediation="Fix JSON syntax errors in schema file",
            cause=e,
        ) from e

    # Validate
    try:
        jsonschema.validate(instance=config, schema=schema)
        return config
    except jsonschema.ValidationError as e:
        error_msg = _format_validation_error(e)
        raise ConfigValidationError(config_path=str(config_path), errors=[error_msg]) from e
    except jsonschema.SchemaError as e:
        raise ConfigurationError(
            message=f"Invalid schema structure: {schema_path}",
            code=ErrorCode.INVALID_CONFIG_VALUE,
            context={"file_path": str(schema_path), "error": e.message},
            remediation="Fix schema structure errors in schema file",
            cause=e,
        ) from e


def _format_validation_error(error: Any) -> str:
    """Format validation error for user-friendly display."""
    path = " -> ".join(str(p) for p in error.path) if error.path else "root"
    return f"Validation error at '{path}': {error.message}"


@log_errors()
def load_and_validate_config(config_path: Path, schema_path: Path) -> dict[str, Any]:
    """
    Load and validate configuration.

    This is a convenience function that wraps validate_config.
    Use validate_config directly for better error handling.

    Args:
        config_path: Path to config.json
        schema_path: Path to config.schema.json

    Returns:
        Loaded and validated configuration

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValidationError: If config JSON is malformed
        ConfigurationError: If schema is invalid or malformed
        ConfigValidationError: If config fails schema validation
    """
    # validate_config now loads and validates in one step
    return validate_config(config_path, schema_path)


def main():
    """
    CLI entry point for manual validation.

    Exits with 0 on success, non-zero on error.

    Raises:
        SystemExit: Always exits with status code
    """
    import sys

    from sdd.core.exceptions import SDDError

    if len(sys.argv) < 2:
        print("Usage: config_validator.py <config_path> [schema_path]")
        print("\nValidate SDD configuration against JSON schema.")
        print("\nExample:")
        print("  python3 config_validator.py .session/config.json")
        print("  python3 config_validator.py .session/config.json .session/config.schema.json")
        sys.exit(1)

    config_path = Path(sys.argv[1])

    # Default schema path
    if len(sys.argv) >= 3:
        schema_path = Path(sys.argv[2])
    else:
        # Assume schema is in same directory as config
        schema_path = config_path.parent / "config.schema.json"

    print(f"Validating: {config_path}")
    print(f"Against schema: {schema_path}\n")

    try:
        validate_config(config_path, schema_path)
        print("✓ Configuration is valid!")
        sys.exit(0)
    except SDDError as e:
        print("✗ Configuration validation failed!\n")
        print(f"Error: {e.message}")
        if e.context:
            print(f"Context: {e.context}")
        if e.remediation:
            print(f"\nRemediation: {e.remediation}")
        print("\nSee docs/configuration.md for configuration reference.")
        sys.exit(e.exit_code)
    except Exception as e:
        print("✗ Unexpected error during validation!\n")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
