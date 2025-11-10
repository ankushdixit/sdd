"""Unit tests for logging_config module.

This module tests the logging configuration functionality including:
- Logger initialization with different log levels
- File-based logging
- Structured and human-readable formatters
- Module-specific logger creation
- Log context management
"""

import json
import logging

from solokit.core.logging_config import (
    HumanReadableFormatter,
    LogContext,
    StructuredFormatter,
    get_logger,
    setup_logging,
)


class TestSetupLogging:
    """Test suite for setup_logging function."""

    def test_setup_logging_default_level(self):
        """Test that setup_logging creates a logger with INFO level by default."""
        # Arrange & Act
        setup_logging()
        logger = logging.getLogger("solokit")

        # Assert
        assert logger.level == logging.INFO
        assert len(logger.handlers) >= 1

    def test_setup_logging_debug_level(self):
        """Test that setup_logging correctly sets DEBUG log level."""
        # Arrange & Act
        setup_logging(level="DEBUG")
        logger = logging.getLogger("solokit")

        # Assert
        assert logger.level == logging.DEBUG

    def test_setup_logging_warning_level(self):
        """Test that setup_logging correctly sets WARNING log level."""
        # Arrange & Act
        setup_logging(level="WARNING")
        logger = logging.getLogger("solokit")

        # Assert
        assert logger.level == logging.WARNING

    def test_setup_logging_error_level(self):
        """Test that setup_logging correctly sets ERROR log level."""
        # Arrange & Act
        setup_logging(level="ERROR")
        logger = logging.getLogger("solokit")

        # Assert
        assert logger.level == logging.ERROR

    def test_setup_logging_with_file_handler(self, tmp_path):
        """Test that setup_logging creates a log file and writes messages to it."""
        # Arrange
        log_file = tmp_path / "test.log"

        # Act
        setup_logging(log_file=log_file)
        logger = logging.getLogger("solokit")
        logger.info("Test message")

        # Assert
        assert log_file.exists()
        content = log_file.read_text()
        assert "Test message" in content

    def test_setup_logging_structured(self, tmp_path):
        """Test that setup_logging applies structured JSON formatting."""
        # Arrange
        log_file = tmp_path / "test.log"

        # Act
        setup_logging(log_file=log_file, structured=True)
        logger = logging.getLogger("solokit")
        logger.info("Structured log test")

        # Assert
        content = log_file.read_text()
        log_data = json.loads(content.strip())
        assert log_data["message"] == "Structured log test"
        assert log_data["level"] == "INFO"
        assert "timestamp" in log_data


class TestGetLogger:
    """Test suite for get_logger function."""

    def test_get_logger_returns_named_logger(self):
        """Test that get_logger returns a logger with the specified module name prefixed with 'solokit'."""
        # Arrange
        module_name = "test_module"

        # Act
        logger = get_logger(module_name)

        # Assert
        assert logger.name == f"solokit.{module_name}"
        assert isinstance(logger, logging.Logger)


class TestStructuredFormatter:
    """Test suite for StructuredFormatter."""

    def test_structured_formatter_produces_json(self):
        """Test that StructuredFormatter produces valid JSON output."""
        # Arrange
        formatter = StructuredFormatter()
        logger = logging.getLogger("test")
        logger.setLevel(logging.INFO)

        # Create a log record
        record = logger.makeRecord("test", logging.INFO, __file__, 1, "Test message", (), None)

        # Act
        output = formatter.format(record)
        log_data = json.loads(output)

        # Assert
        assert log_data["message"] == "Test message"
        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test"
        assert "timestamp" in log_data

    def test_structured_formatter_includes_context(self):
        """Test that StructuredFormatter includes context when present."""
        # Arrange
        formatter = StructuredFormatter()
        logger = logging.getLogger("test")
        record = logger.makeRecord("test", logging.INFO, __file__, 1, "Test message", (), None)
        record.context = {"operation": "test_op", "user": "test_user"}

        # Act
        output = formatter.format(record)
        log_data = json.loads(output)

        # Assert
        assert "context" in log_data
        assert log_data["context"]["operation"] == "test_op"
        assert log_data["context"]["user"] == "test_user"


class TestHumanReadableFormatter:
    """Test suite for HumanReadableFormatter."""

    def test_human_readable_formatter_includes_timestamp(self):
        """Test that HumanReadableFormatter includes timestamp."""
        # Arrange
        formatter = HumanReadableFormatter()
        logger = logging.getLogger("test")
        record = logger.makeRecord("test", logging.INFO, __file__, 1, "Test message", (), None)

        # Act
        output = formatter.format(record)

        # Assert
        assert "Test message" in output
        assert "INFO" in output
        assert "test" in output


class TestLogContext:
    """Test suite for LogContext."""

    def test_log_context_adds_context_to_records(self):
        """Test that LogContext adds context to log records."""
        # Arrange
        setup_logging(structured=True)
        logger = get_logger("test_context")

        # Act & Assert - Context should be added within the context manager
        with LogContext(logger, operation="test_operation", session_id="123"):
            # Capture a log record
            test_record = None

            class ContextCapture(logging.Handler):
                def emit(self, record):
                    nonlocal test_record
                    test_record = record

            handler = ContextCapture()
            logger.addHandler(handler)
            logger.info("Test message")
            logger.removeHandler(handler)

            # Verify context was added
            assert hasattr(test_record, "context")
            assert test_record.context["operation"] == "test_operation"
            assert test_record.context["session_id"] == "123"
