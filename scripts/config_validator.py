#!/usr/bin/env python3
"""Configuration validation using JSON schema."""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


def validate_config(config_path: Path, schema_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate configuration against JSON schema.

    Args:
        config_path: Path to config.json
        schema_path: Path to config.schema.json

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    try:
        import jsonschema
    except ImportError:
        # If jsonschema not installed, skip validation
        return True, ["Warning: jsonschema not installed, skipping validation"]

    # Load config
    if not config_path.exists():
        return False, [f"Config file not found: {config_path}"]

    try:
        with open(config_path) as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON in config file: {e}"]

    # Load schema
    if not schema_path.exists():
        return True, [f"Warning: Schema file not found: {schema_path}"]

    try:
        with open(schema_path) as f:
            schema = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON in schema file: {e}"]

    # Validate
    try:
        jsonschema.validate(instance=config, schema=schema)
        return True, []
    except jsonschema.ValidationError as e:
        error_msg = _format_validation_error(e)
        return False, [error_msg]
    except jsonschema.SchemaError as e:
        return False, [f"Invalid schema: {e.message}"]


def _format_validation_error(error: Any) -> str:
    """Format validation error for user-friendly display."""
    path = " -> ".join(str(p) for p in error.path) if error.path else "root"
    return f"Validation error at '{path}': {error.message}"


def load_and_validate_config(config_path: Path, schema_path: Path) -> Dict[str, Any]:
    """
    Load and validate configuration.

    Args:
        config_path: Path to config.json
        schema_path: Path to config.schema.json

    Returns:
        Loaded configuration

    Raises:
        ValueError: If configuration is invalid
    """
    is_valid, errors = validate_config(config_path, schema_path)

    if not is_valid:
        error_msg = "Configuration validation failed:\n" + "\n".join(errors)
        raise ValueError(error_msg)

    # Load and return config
    with open(config_path) as f:
        return json.load(f)


def main():
    """CLI entry point for manual validation."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: config_validator.py <config_path> [schema_path]")
        print("\nValidate SDD configuration against JSON schema.")
        print("\nExample:")
        print("  python3 config_validator.py .session/config.json")
        print(
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

    print(f"Validating: {config_path}")
    print(f"Against schema: {schema_path}\n")

    is_valid, errors = validate_config(config_path, schema_path)

    if is_valid:
        print("✓ Configuration is valid!")
        if errors:  # Warnings
            print("\nWarnings:")
            for error in errors:
                print(f"  - {error}")
        sys.exit(0)
    else:
        print("✗ Configuration validation failed!\n")
        print("Errors:")
        for error in errors:
            print(f"  - {error}")
        print("\nPlease fix the configuration errors and try again.")
        print("See docs/configuration.md for configuration reference.")
        sys.exit(1)


if __name__ == "__main__":
    main()
