"""User output handler separate from diagnostic logging."""

import sys


class OutputHandler:
    """Handle user-facing output separate from logs."""

    def __init__(self, quiet: bool = False):
        """
        Initialize output handler.

        Args:
            quiet: Suppress all non-error output
        """
        self.quiet = quiet

    def info(self, message: str) -> None:
        """
        Display info message to user.

        Args:
            message: Message to display
        """
        if not self.quiet:
            print(message)

    def success(self, message: str) -> None:
        """
        Display success message to user.

        Args:
            message: Success message to display
        """
        if not self.quiet:
            print(f"✅ {message}")

    def warning(self, message: str) -> None:
        """
        Display warning message to user.

        Args:
            message: Warning message to display
        """
        if not self.quiet:
            print(f"⚠️  {message}")

    def error(self, message: str) -> None:
        """
        Display error message to user.

        Args:
            message: Error message to display
        """
        print(f"❌ {message}", file=sys.stderr)

    def progress(self, message: str) -> None:
        """
        Display progress message to user.

        Args:
            message: Progress message to display
        """
        if not self.quiet:
            print(f"⏳ {message}")

    def section(self, title: str) -> None:
        """
        Display section header.

        Args:
            title: Section title
        """
        if not self.quiet:
            print(f"\n=== {title} ===\n")


# Global output handler
_output_handler = OutputHandler()


def get_output() -> OutputHandler:
    """
    Get the global output handler.

    Returns:
        Global OutputHandler instance
    """
    return _output_handler


def set_quiet(quiet: bool) -> None:
    """
    Set quiet mode for output handler.

    Args:
        quiet: True to suppress output, False to enable
    """
    _output_handler.quiet = quiet
