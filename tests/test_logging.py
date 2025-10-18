"""Tests for logging configuration."""

import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.logging_config import get_logger, setup_logging  # noqa: E402


def test_setup_logging_default():
    """Test default logging setup."""
    logger = setup_logging()
    assert logger.level == logging.INFO
    assert len(logger.handlers) >= 1


def test_setup_logging_debug():
    """Test DEBUG level logging."""
    logger = setup_logging(level="DEBUG")
    assert logger.level == logging.DEBUG


def test_setup_logging_with_file(tmp_path):
    """Test logging to file."""
    log_file = tmp_path / "test.log"
    logger = setup_logging(log_file=log_file)

    logger.info("Test message")

    assert log_file.exists()
    content = log_file.read_text()
    assert "Test message" in content


def test_get_logger():
    """Test getting module-specific logger."""
    logger = get_logger("test_module")
    assert logger.name == "test_module"


def test_setup_logging_custom_format(tmp_path):
    """Test custom format string."""
    log_file = tmp_path / "test.log"
    custom_format = "%(levelname)s - %(message)s"
    logger = setup_logging(log_file=log_file, format_string=custom_format)

    logger.info("Custom format test")

    content = log_file.read_text()
    assert "INFO - Custom format test" in content
    # Should not contain timestamp (not in custom format)
    assert "test_logging" not in content


def test_setup_logging_warning_level():
    """Test WARNING level logging."""
    logger = setup_logging(level="WARNING")
    assert logger.level == logging.WARNING


def test_setup_logging_error_level():
    """Test ERROR level logging."""
    logger = setup_logging(level="ERROR")
    assert logger.level == logging.ERROR
