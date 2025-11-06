"""Unit tests for output module.

This module tests the user output functionality including:
- OutputHandler methods
- Quiet mode
- Output formatting
"""

from sdd.core.output import OutputHandler, get_output, set_quiet


class TestOutputHandler:
    """Test suite for OutputHandler class."""

    def test_info_displays_message(self, capsys):
        """Test that info() displays a plain message."""
        # Arrange
        handler = OutputHandler()

        # Act
        handler.info("Test info message")
        captured = capsys.readouterr()

        # Assert
        assert "Test info message" in captured.out

    def test_success_displays_with_emoji(self, capsys):
        """Test that success() displays message with checkmark emoji."""
        # Arrange
        handler = OutputHandler()

        # Act
        handler.success("Operation completed")
        captured = capsys.readouterr()

        # Assert
        assert "✅ Operation completed" in captured.out

    def test_warning_displays_with_emoji(self, capsys):
        """Test that warning() displays message with warning emoji."""
        # Arrange
        handler = OutputHandler()

        # Act
        handler.warning("This is a warning")
        captured = capsys.readouterr()

        # Assert
        assert "⚠️  This is a warning" in captured.out

    def test_error_displays_with_emoji_to_stderr(self, capsys):
        """Test that error() displays message with error emoji to stderr."""
        # Arrange
        handler = OutputHandler()

        # Act
        handler.error("Error occurred")
        captured = capsys.readouterr()

        # Assert
        assert "❌ Error occurred" in captured.err

    def test_progress_displays_with_emoji(self, capsys):
        """Test that progress() displays message with progress emoji."""
        # Arrange
        handler = OutputHandler()

        # Act
        handler.progress("Processing...")
        captured = capsys.readouterr()

        # Assert
        assert "⏳ Processing..." in captured.out

    def test_section_displays_formatted_header(self, capsys):
        """Test that section() displays a formatted section header."""
        # Arrange
        handler = OutputHandler()

        # Act
        handler.section("Test Section")
        captured = capsys.readouterr()

        # Assert
        assert "=== Test Section ===" in captured.out

    def test_quiet_mode_suppresses_info(self, capsys):
        """Test that quiet mode suppresses info messages."""
        # Arrange
        handler = OutputHandler(quiet=True)

        # Act
        handler.info("This should be suppressed")
        captured = capsys.readouterr()

        # Assert
        assert captured.out == ""

    def test_quiet_mode_suppresses_success(self, capsys):
        """Test that quiet mode suppresses success messages."""
        # Arrange
        handler = OutputHandler(quiet=True)

        # Act
        handler.success("This should be suppressed")
        captured = capsys.readouterr()

        # Assert
        assert captured.out == ""

    def test_quiet_mode_does_not_suppress_errors(self, capsys):
        """Test that quiet mode does NOT suppress error messages."""
        # Arrange
        handler = OutputHandler(quiet=True)

        # Act
        handler.error("This should still appear")
        captured = capsys.readouterr()

        # Assert
        assert "❌ This should still appear" in captured.err


class TestGlobalOutputHandler:
    """Test suite for global output handler functions."""

    def test_get_output_returns_same_instance(self):
        """Test that get_output() returns the same instance."""
        # Act
        handler1 = get_output()
        handler2 = get_output()

        # Assert
        assert handler1 is handler2

    def test_set_quiet_affects_global_handler(self, capsys):
        """Test that set_quiet() affects the global output handler."""
        # Arrange
        set_quiet(False)
        handler = get_output()

        # Act - First test with quiet=False
        handler.info("Should appear")
        captured1 = capsys.readouterr()

        # Set quiet mode
        set_quiet(True)
        handler.info("Should not appear")
        captured2 = capsys.readouterr()

        # Reset quiet mode
        set_quiet(False)

        # Assert
        assert "Should appear" in captured1.out
        assert captured2.out == ""
