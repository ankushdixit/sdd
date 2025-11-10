"""
Argparse helpers for improved error messages and user experience.

This module provides custom argparse classes that enhance the default
error handling with better messaging, examples, and next steps.
"""

from __future__ import annotations

import argparse
import sys
from typing import NoReturn


class HelpfulArgumentParser(argparse.ArgumentParser):
    """
        Custom ArgumentParser that provides helpful error messages.

        This parser extends the default argparse.ArgumentParser to show:
        - Friendly error messages with emoji
        - Full help text when errors occur
        - Better formatting for terminal usage

        Example:
            parser = HelpfulArgumentParser(
                description="Create a new work item",
                epilog='''
    Examples:
      sk work-new --type feature --title "Add auth" --priority high
      sk work-new -t bug -T "Fix login" -p critical

    Valid types: feature, bug, refactor, security
                '''
            )
    """

    def error(self, message: str) -> NoReturn:
        """
        Override error handling to provide helpful messages.

        Args:
            message: Error message from argparse

        Exits with code 2 after printing error and help.
        """
        sys.stderr.write(f"❌ Error: {message}\n\n")
        self.print_help(sys.stderr)
        sys.exit(2)
