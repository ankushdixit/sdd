"""
Config command for Solokit CLI.

Displays and manages Solokit configuration with validation status.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from solokit.core.config import ConfigManager
from solokit.core.constants import SESSION_DIR_NAME
from solokit.core.output import get_output

output = get_output()


def format_config_yaml_style(config_dict: dict, indent: int = 0) -> str:
    """
    Format configuration in YAML-style for human readability.

    Args:
        config_dict: Configuration dictionary
        indent: Current indentation level

    Returns:
        Formatted configuration string
    """
    lines = []
    indent_str = "  " * indent

    for key, value in config_dict.items():
        if isinstance(value, dict):
            lines.append(f"{indent_str}{key}:")
            lines.append(format_config_yaml_style(value, indent + 1))
        elif isinstance(value, list):
            lines.append(f"{indent_str}{key}:")
            for item in value:
                if isinstance(item, dict):
                    lines.append(format_config_yaml_style(item, indent + 1))
                else:
                    lines.append(f"{indent_str}  - {item}")
        else:
            lines.append(f"{indent_str}{key}: {value}")

    return "\n".join(lines)


def show_config(as_json: bool = False) -> int:
    """
    Display current configuration.

    Args:
        as_json: Whether to output as JSON (vs human-readable format)

    Returns:
        Exit code (0 for success, 1 for errors)
    """
    config_path = Path.cwd() / SESSION_DIR_NAME / "config.json"

    output.info(f"Configuration from: {config_path}")
    output.info("")

    # Check if config file exists
    if not config_path.exists():
        output.info("⚠ Config file not found - using default configuration")
        output.info("")
        output.info("To create a config file:")
        output.info("  1. Run 'sk init' to initialize a project")
        output.info(f"  2. Or manually create {config_path}")
        output.info("")
        return 1

    # Try to load and display config
    try:
        with open(config_path) as f:
            config_data = json.load(f)

        if as_json:
            # Output as formatted JSON
            output.info(json.dumps(config_data, indent=2))
        else:
            # Output in human-readable YAML-style format
            formatted = format_config_yaml_style(config_data)
            output.info(formatted)

        output.info("")

        # Validate configuration
        try:
            config_manager = ConfigManager()
            config_manager.load_config(config_path, force_reload=True)
            output.info("✓ Configuration is valid")
            return 0
        except Exception as e:
            output.error(f"✗ Configuration has errors: {str(e)}")
            output.error("")
            output.error("Suggestions:")
            output.error("  - Check JSON syntax")
            output.error("  - Verify all required fields are present")
            output.error("  - Compare with documentation or run 'sk init' for a fresh config")
            return 1

    except json.JSONDecodeError as e:
        output.error(f"✗ Configuration has invalid JSON: {str(e)}")
        output.error("")
        output.error("Fix JSON syntax errors in config.json")
        return 1
    except Exception as e:
        output.error(f"✗ Error reading configuration: {str(e)}")
        return 1


def main() -> int:
    """Main entry point for config show command."""
    parser = argparse.ArgumentParser(description="Display configuration")
    parser.add_argument(
        "subcommand",
        nargs="?",
        default="show",
        help="Subcommand (currently only 'show' is supported)",
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.subcommand != "show":
        output.error(f"Unknown subcommand: {args.subcommand}")
        output.error("Currently only 'sk config show' is supported")
        return 1

    return show_config(as_json=args.json)


if __name__ == "__main__":
    sys.exit(main())
