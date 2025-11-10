#!/usr/bin/env python3
"""Configuration validation using JSON schema."""

import json
import logging
from pathlib import Path
from typing import Any

from solokit.core.error_handlers import log_errors
from solokit.core.exceptions import (
    ConfigurationError,
    ConfigValidationError,
    ErrorCode,
    ValidationError,
)
from solokit.core.exceptions import (
    FileNotFoundError as SolokitFileNotFoundError,
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
            raise SolokitFileNotFoundError(str(config_path), file_type="config")
        try:
            with open(config_path) as f:
                config: dict[str, Any] = json.load(f)
                return config
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
        raise SolokitFileNotFoundError(str(config_path), file_type="config")

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
        config_dict: dict[str, Any] = config
        return config_dict

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
        validated_config: dict[str, Any] = config
        return validated_config
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


def main() -> None:
    """
    CLI entry point for manual validation.

    Exits with 0 on success, non-zero on error.

    Raises:
        SystemExit: Always exits with status code
    """
    import sys

    from solokit.core.exceptions import SolokitError
    from solokit.core.output import get_output

    output = get_output()

    if len(sys.argv) < 2:
        output.info("Usage: config_validator.py <config_path> [schema_path]")
        output.info("\nValidate Solokit configuration against JSON schema.")
        output.info("\nExample:")
        output.info("  python3 config_validator.py .session/config.json")
        output.info(
            "  python3 config_validator.py .session/config.json .session/config.schema.json"
        )
        sys.exit(1)

    config_path = Path(sys.argv[1])

    # Default schema path
    if len(sys.argv) >= 3:
        schema_path = Path(sys.argv[2])
    else:
        # Assume schema is in same directory as config
        schema_path = config_path.parent / "config.schema.json"

    output.info(f"Validating: {config_path}")
    output.info(f"Against schema: {schema_path}\n")

    try:
        validate_config(config_path, schema_path)
        output.success("Configuration is valid!")
        sys.exit(0)
    except SolokitError as e:
        output.info("✗ Configuration validation failed!\n")
        output.info(f"Error: {e.message}")
        if e.context:
            output.info(f"Context: {e.context}")
        if e.remediation:
            output.info(f"\nRemediation: {e.remediation}")
        output.info("\nSee docs/configuration.md for configuration reference.")
        sys.exit(e.exit_code)
    except Exception as e:
        output.info("✗ Unexpected error during validation!\n")
        output.info(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
