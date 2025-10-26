"""Unit tests for logging_config module.

This module tests the logging configuration functionality including:
- Logger initialization with different log levels
- File-based logging
- Custom format strings
- Module-specific logger creation
"""

import logging

from sdd.core.logging_config import get_logger, setup_logging


class TestSetupLogging:
    """Test suite for setup_logging function."""

    def test_setup_logging_default_level(self):
        """Test that setup_logging creates a logger with INFO level by default."""
        # Arrange & Act
        logger = setup_logging()

        # Assert
        assert logger.level == logging.INFO
        assert len(logger.handlers) >= 1

    def test_setup_logging_debug_level(self):
        """Test that setup_logging correctly sets DEBUG log level."""
        # Arrange & Act
        logger = setup_logging(level="DEBUG")

        # Assert
        assert logger.level == logging.DEBUG

    def test_setup_logging_warning_level(self):
        """Test that setup_logging correctly sets WARNING log level."""
        # Arrange & Act
        logger = setup_logging(level="WARNING")

        # Assert
        assert logger.level == logging.WARNING

    def test_setup_logging_error_level(self):
        """Test that setup_logging correctly sets ERROR log level."""
        # Arrange & Act
        logger = setup_logging(level="ERROR")

        # Assert
        assert logger.level == logging.ERROR

    def test_setup_logging_with_file_handler(self, tmp_path):
        """Test that setup_logging creates a log file and writes messages to it."""
        # Arrange
        log_file = tmp_path / "test.log"

        # Act
        logger = setup_logging(log_file=log_file)
        logger.info("Test message")

        # Assert
        assert log_file.exists()
        content = log_file.read_text()
        assert "Test message" in content

    def test_setup_logging_custom_format_string(self, tmp_path):
        """Test that setup_logging applies custom format string to log messages."""
        # Arrange
        log_file = tmp_path / "test.log"
        custom_format = "%(levelname)s - %(message)s"

        # Act
        logger = setup_logging(log_file=log_file, format_string=custom_format)
        logger.info("Custom format test")

        # Assert
        content = log_file.read_text()
        assert "INFO - Custom format test" in content
        # Verify that custom format excludes timestamp (not in format string)
        assert "test_logging" not in content


class TestGetLogger:
    """Test suite for get_logger function."""

    def test_get_logger_returns_named_logger(self):
        """Test that get_logger returns a logger with the specified module name."""
        # Arrange
        module_name = "test_module"

        # Act
        logger = get_logger(module_name)

        # Assert
        assert logger.name == module_name
        assert isinstance(logger, logging.Logger)
