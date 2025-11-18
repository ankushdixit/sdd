"""Unit tests for stack_detector.py module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from solokit.core.exceptions import FileOperationError
from solokit.session.briefing.stack_detector import StackDetector


@pytest.fixture
def temp_session_dir():
    """Create a temporary .session directory structure."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        session_dir = temp_path / ".session"
        session_dir.mkdir()
        (session_dir / "tracking").mkdir()
        yield session_dir


class TestStackDetector:
    """Tests for StackDetector class."""

    def test_init_with_default_session_dir(self):
        """Test StackDetector initialization with default session directory."""
        detector = StackDetector()
        assert detector.session_dir == Path(".session")
        assert detector.stack_file == Path(".session/tracking/stack.txt")

    def test_init_with_custom_session_dir(self):
        """Test StackDetector initialization with custom session directory."""
        custom_dir = Path("/custom/session")
        detector = StackDetector(session_dir=custom_dir)
        assert detector.session_dir == custom_dir
        assert detector.stack_file == custom_dir / "tracking" / "stack.txt"

    def test_load_current_stack_success(self, temp_session_dir):
        """Test load_current_stack successfully loads stack file."""
        # Arrange
        stack_file = temp_session_dir / "tracking" / "stack.txt"
        stack_content = "Python 3.11\nDjango 4.2\nPostgreSQL 15"
        stack_file.write_text(stack_content)
        detector = StackDetector(session_dir=temp_session_dir)

        # Act
        result = detector.load_current_stack()

        # Assert
        assert result == stack_content

    def test_load_current_stack_file_not_found(self, temp_session_dir):
        """Test load_current_stack returns default message when file doesn't exist."""
        # Arrange
        detector = StackDetector(session_dir=temp_session_dir)
        # File doesn't exist

        # Act
        result = detector.load_current_stack()

        # Assert
        assert result == "Stack not yet generated"

    def test_load_current_stack_raises_error_on_read_failure(self, temp_session_dir):
        """Test load_current_stack raises FileOperationError when file exists but cannot be read."""
        # Arrange
        stack_file = temp_session_dir / "tracking" / "stack.txt"
        stack_file.write_text("Python 3.11")
        detector = StackDetector(session_dir=temp_session_dir)

        # Mock Path.read_text to raise an exception
        with patch.object(Path, "read_text", side_effect=PermissionError("Permission denied")):
            # Act & Assert
            with pytest.raises(FileOperationError) as exc_info:
                detector.load_current_stack()

            error = exc_info.value
            assert error.context["operation"] == "read"
            assert error.context["file_path"] == str(stack_file)
            assert "Failed to read stack file" in error.context["details"]
            assert isinstance(error.cause, PermissionError)

    def test_load_current_stack_empty_file(self, temp_session_dir):
        """Test load_current_stack handles empty stack file."""
        # Arrange
        stack_file = temp_session_dir / "tracking" / "stack.txt"
        stack_file.write_text("")
        detector = StackDetector(session_dir=temp_session_dir)

        # Act
        result = detector.load_current_stack()

        # Assert
        assert result == ""

    def test_load_current_stack_multiline_content(self, temp_session_dir):
        """Test load_current_stack preserves multiline content."""
        # Arrange
        stack_content = """Python 3.11
Django 4.2
PostgreSQL 15
Redis 7.0"""
        stack_file = temp_session_dir / "tracking" / "stack.txt"
        stack_file.write_text(stack_content)
        detector = StackDetector(session_dir=temp_session_dir)

        # Act
        result = detector.load_current_stack()

        # Assert
        assert result == stack_content
        assert result.count("\n") == 3
