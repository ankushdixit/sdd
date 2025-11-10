"""Unit tests for cli_prompts module.

This module tests the interactive CLI prompt utilities including:
- Confirmation prompts
- Single-select lists
- Multi-select checkbox lists
- Text input with validation
- Non-interactive fallback behavior
"""

from unittest.mock import MagicMock, patch

from solokit.core.cli_prompts import (
    confirm_action,
    multi_select_list,
    select_from_list,
    text_input,
)


class TestConfirmAction:
    """Test suite for confirm_action function."""

    @patch("sys.stdin.isatty", return_value=True)
    @patch("questionary.confirm")
    def test_confirm_action_returns_true_when_confirmed(self, mock_confirm, mock_isatty):
        """Test that confirm_action returns True when user confirms."""
        # Arrange
        mock_result = MagicMock()
        mock_result.ask.return_value = True
        mock_confirm.return_value = mock_result

        # Act
        result = confirm_action("Confirm action?")

        # Assert
        assert result is True
        mock_confirm.assert_called_once_with("Confirm action?", default=False)

    @patch("sys.stdin.isatty", return_value=True)
    @patch("questionary.confirm")
    def test_confirm_action_returns_false_when_declined(self, mock_confirm, mock_isatty):
        """Test that confirm_action returns False when user declines."""
        # Arrange
        mock_result = MagicMock()
        mock_result.ask.return_value = False
        mock_confirm.return_value = mock_result

        # Act
        result = confirm_action("Confirm action?")

        # Assert
        assert result is False

    @patch("sys.stdin.isatty", return_value=True)
    @patch("questionary.confirm")
    def test_confirm_action_uses_custom_default(self, mock_confirm, mock_isatty):
        """Test that confirm_action respects custom default value."""
        # Arrange
        mock_result = MagicMock()
        mock_result.ask.return_value = True
        mock_confirm.return_value = mock_result

        # Act
        confirm_action("Confirm action?", default=True)

        # Assert
        mock_confirm.assert_called_once_with("Confirm action?", default=True)

    @patch("sys.stdin.isatty", return_value=False)
    def test_confirm_action_non_interactive_uses_default(self, mock_isatty):
        """Test that confirm_action returns default in non-interactive mode."""
        # Act
        result_false = confirm_action("Confirm?", default=False)
        result_true = confirm_action("Confirm?", default=True)

        # Assert
        assert result_false is False
        assert result_true is True

    @patch("sys.stdin.isatty", return_value=True)
    @patch("questionary.confirm")
    def test_confirm_action_handles_none_response(self, mock_confirm, mock_isatty):
        """Test that confirm_action handles None response gracefully."""
        # Arrange
        mock_result = MagicMock()
        mock_result.ask.return_value = None
        mock_confirm.return_value = mock_result

        # Act
        result = confirm_action("Confirm?", default=True)

        # Assert
        assert result is True


class TestSelectFromList:
    """Test suite for select_from_list function."""

    @patch("sys.stdin.isatty", return_value=True)
    @patch("questionary.select")
    def test_select_from_list_returns_selected_choice(self, mock_select, mock_isatty):
        """Test that select_from_list returns the user's selection."""
        # Arrange
        choices = ["option1", "option2", "option3"]
        mock_result = MagicMock()
        mock_result.ask.return_value = "option2"
        mock_select.return_value = mock_result

        # Act
        result = select_from_list("Select one:", choices)

        # Assert
        assert result == "option2"
        mock_select.assert_called_once_with("Select one:", choices=choices)

    @patch("sys.stdin.isatty", return_value=False)
    def test_select_from_list_non_interactive_returns_first(self, mock_isatty):
        """Test that select_from_list returns first choice in non-interactive mode."""
        # Arrange
        choices = ["option1", "option2", "option3"]

        # Act
        result = select_from_list("Select one:", choices)

        # Assert
        assert result == "option1"

    @patch("sys.stdin.isatty", return_value=False)
    def test_select_from_list_non_interactive_uses_default(self, mock_isatty):
        """Test that select_from_list returns custom default in non-interactive mode."""
        # Arrange
        choices = ["option1", "option2", "option3"]

        # Act
        result = select_from_list("Select one:", choices, default="option2")

        # Assert
        assert result == "option2"

    def test_select_from_list_empty_choices_returns_empty_string(self):
        """Test that select_from_list returns empty string for empty choices."""
        # Act
        result = select_from_list("Select one:", [])

        # Assert
        assert result == ""

    @patch("sys.stdin.isatty", return_value=True)
    @patch("questionary.select")
    def test_select_from_list_handles_none_response(self, mock_select, mock_isatty):
        """Test that select_from_list handles None response gracefully."""
        # Arrange
        choices = ["option1", "option2"]
        mock_result = MagicMock()
        mock_result.ask.return_value = None
        mock_select.return_value = mock_result

        # Act
        result = select_from_list("Select one:", choices)

        # Assert
        assert result == "option1"


class TestMultiSelectList:
    """Test suite for multi_select_list function."""

    @patch("sys.stdin.isatty", return_value=True)
    @patch("questionary.checkbox")
    def test_multi_select_list_returns_selected_choices(self, mock_checkbox, mock_isatty):
        """Test that multi_select_list returns all selected options."""
        # Arrange
        choices = ["option1", "option2", "option3"]
        mock_result = MagicMock()
        mock_result.ask.return_value = ["option1", "option3"]
        mock_checkbox.return_value = mock_result

        # Act
        result = multi_select_list("Select multiple:", choices)

        # Assert
        assert result == ["option1", "option3"]
        mock_checkbox.assert_called_once_with("Select multiple:", choices=choices)

    @patch("sys.stdin.isatty", return_value=False)
    def test_multi_select_list_non_interactive_returns_empty(self, mock_isatty):
        """Test that multi_select_list returns empty list in non-interactive mode."""
        # Arrange
        choices = ["option1", "option2", "option3"]

        # Act
        result = multi_select_list("Select multiple:", choices)

        # Assert
        assert result == []

    @patch("sys.stdin.isatty", return_value=True)
    @patch("questionary.checkbox")
    def test_multi_select_list_handles_none_response(self, mock_checkbox, mock_isatty):
        """Test that multi_select_list handles None response gracefully."""
        # Arrange
        choices = ["option1", "option2"]
        mock_result = MagicMock()
        mock_result.ask.return_value = None
        mock_checkbox.return_value = mock_result

        # Act
        result = multi_select_list("Select multiple:", choices)

        # Assert
        assert result == []


class TestTextInput:
    """Test suite for text_input function."""

    @patch("sys.stdin.isatty", return_value=True)
    @patch("questionary.text")
    def test_text_input_returns_user_input(self, mock_text, mock_isatty):
        """Test that text_input returns the user's text."""
        # Arrange
        mock_result = MagicMock()
        mock_result.ask.return_value = "user input"
        mock_text.return_value = mock_result

        # Act
        result = text_input("Enter text:")

        # Assert
        assert result == "user input"
        mock_text.assert_called_once_with("Enter text:", validate=None)

    @patch("sys.stdin.isatty", return_value=True)
    @patch("questionary.text")
    def test_text_input_with_validation(self, mock_text, mock_isatty):
        """Test that text_input passes validation function to questionary."""
        # Arrange
        mock_result = MagicMock()
        mock_result.ask.return_value = "valid input"
        mock_text.return_value = mock_result
        validate_fn = lambda x: len(x) > 0  # noqa: E731

        # Act
        result = text_input("Enter text:", validate_fn=validate_fn)

        # Assert
        assert result == "valid input"
        mock_text.assert_called_once_with("Enter text:", validate=validate_fn)

    @patch("sys.stdin.isatty", return_value=False)
    def test_text_input_non_interactive_returns_default(self, mock_isatty):
        """Test that text_input returns default in non-interactive mode."""
        # Act
        result = text_input("Enter text:", default="default value")

        # Assert
        assert result == "default value"

    @patch("sys.stdin.isatty", return_value=True)
    @patch("questionary.text")
    def test_text_input_handles_none_response(self, mock_text, mock_isatty):
        """Test that text_input handles None response gracefully."""
        # Arrange
        mock_result = MagicMock()
        mock_result.ask.return_value = None
        mock_text.return_value = mock_result

        # Act
        result = text_input("Enter text:", default="fallback")

        # Assert
        assert result == "fallback"
