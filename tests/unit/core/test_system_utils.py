"""Unit tests for system_utils module.

This module tests cross-platform system utilities including:
- Python binary detection (python vs python3)
- Python command formatting
- Platform-specific behavior
"""

import sys
from unittest.mock import patch

from solokit.core.system_utils import format_python_command, get_python_binary


class TestGetPythonBinary:
    """Test suite for get_python_binary function."""

    @patch("shutil.which")
    def test_get_python_binary_prefers_python3(self, mock_which):
        """Test that get_python_binary returns 'python3' when available."""

        # Arrange
        def which_side_effect(binary):
            return "/usr/bin/python3" if binary == "python3" else None

        mock_which.side_effect = which_side_effect

        # Act
        result = get_python_binary()

        # Assert
        assert result == "python3"
        # Verify python3 was checked first
        mock_which.assert_called_with("python3")

    @patch("shutil.which")
    def test_get_python_binary_falls_back_to_python(self, mock_which):
        """Test that get_python_binary returns 'python' when python3 is not available."""

        # Arrange
        def which_side_effect(binary):
            return "/usr/bin/python" if binary == "python" else None

        mock_which.side_effect = which_side_effect

        # Act
        result = get_python_binary()

        # Assert
        assert result == "python"
        # Verify both binaries were checked
        assert mock_which.call_count == 2
        mock_which.assert_any_call("python3")
        mock_which.assert_any_call("python")

    @patch("shutil.which")
    def test_get_python_binary_uses_sys_executable_as_last_resort(self, mock_which):
        """Test that get_python_binary returns sys.executable when neither python3 nor python are found."""
        # Arrange
        mock_which.return_value = None  # Neither python3 nor python found

        # Act
        result = get_python_binary()

        # Assert
        assert result == sys.executable
        assert mock_which.call_count == 2
        mock_which.assert_any_call("python3")
        mock_which.assert_any_call("python")

    @patch("shutil.which")
    def test_get_python_binary_both_available_prefers_python3(self, mock_which):
        """Test that python3 is preferred when both python3 and python are available."""
        # Arrange - both binaries available
        mock_which.return_value = "/usr/bin/python3"

        # Act
        result = get_python_binary()

        # Assert
        assert result == "python3"
        # Should only check python3, not python since python3 is found first
        mock_which.assert_called_once_with("python3")

    @patch("shutil.which")
    def test_get_python_binary_with_full_path_python3(self, mock_which):
        """Test get_python_binary with full path to python3 binary."""
        # Arrange
        mock_which.side_effect = lambda x: ("/usr/local/bin/python3" if x == "python3" else None)

        # Act
        result = get_python_binary()

        # Assert
        assert result == "python3"

    @patch("shutil.which")
    def test_get_python_binary_with_full_path_python(self, mock_which):
        """Test get_python_binary with full path to python binary."""
        # Arrange
        mock_which.side_effect = lambda x: ("/usr/local/bin/python" if x == "python" else None)

        # Act
        result = get_python_binary()

        # Assert
        assert result == "python"

    @patch("shutil.which")
    def test_get_python_binary_sys_executable_fallback_with_path(self, mock_which):
        """Test that sys.executable fallback preserves the full path."""
        # Arrange
        mock_which.return_value = None
        original_executable = sys.executable

        # Act
        result = get_python_binary()

        # Assert
        assert result == original_executable
        # Verify it returns actual executable path
        assert len(result) > 0


class TestFormatPythonCommand:
    """Test suite for format_python_command function."""

    @patch("solokit.core.system_utils.get_python_binary")
    def test_format_python_command_basic_module_path(self, mock_get_binary):
        """Test format_python_command with basic module path and no args."""
        # Arrange
        mock_get_binary.return_value = "python3"

        # Act
        result = format_python_command("solokit.work_items.get_metadata")

        # Assert
        assert result == "python3 -m solokit.work_items.get_metadata"
        mock_get_binary.assert_called_once()

    @patch("solokit.core.system_utils.get_python_binary")
    def test_format_python_command_with_arguments(self, mock_get_binary):
        """Test format_python_command with module path and arguments."""
        # Arrange
        mock_get_binary.return_value = "python3"

        # Act
        result = format_python_command("solokit.work_items.get_metadata", "feat_001 --with-deps")

        # Assert
        assert result == "python3 -m solokit.work_items.get_metadata feat_001 --with-deps"
        mock_get_binary.assert_called_once()

    @patch("solokit.core.system_utils.get_python_binary")
    def test_format_python_command_with_empty_args(self, mock_get_binary):
        """Test format_python_command with empty string arguments."""
        # Arrange
        mock_get_binary.return_value = "python3"

        # Act
        result = format_python_command("solokit.module", "")

        # Assert
        # Empty string args should result in no args being added
        assert result == "python3 -m solokit.module"

    @patch("solokit.core.system_utils.get_python_binary")
    def test_format_python_command_uses_python_fallback(self, mock_get_binary):
        """Test format_python_command when get_python_binary returns 'python'."""
        # Arrange
        mock_get_binary.return_value = "python"

        # Act
        result = format_python_command("mymodule")

        # Assert
        assert result == "python -m mymodule"
        assert result.startswith("python -m")

    @patch("solokit.core.system_utils.get_python_binary")
    def test_format_python_command_uses_sys_executable(self, mock_get_binary):
        """Test format_python_command when get_python_binary returns sys.executable."""
        # Arrange
        mock_get_binary.return_value = sys.executable

        # Act
        result = format_python_command("test.module")

        # Assert
        assert result == f"{sys.executable} -m test.module"

    @patch("solokit.core.system_utils.get_python_binary")
    def test_format_python_command_with_complex_arguments(self, mock_get_binary):
        """Test format_python_command with complex arguments including flags and values."""
        # Arrange
        mock_get_binary.return_value = "python3"

        # Act
        result = format_python_command(
            "solokit.cli.main",
            "--verbose --config config.yaml --items feat_001 feat_002",
        )

        # Assert
        assert result == (
            "python3 -m solokit.cli.main --verbose --config config.yaml --items feat_001 feat_002"
        )

    @patch("solokit.core.system_utils.get_python_binary")
    def test_format_python_command_with_single_arg(self, mock_get_binary):
        """Test format_python_command with a single argument."""
        # Arrange
        mock_get_binary.return_value = "python3"

        # Act
        result = format_python_command("solokit.commands.status", "--json")

        # Assert
        assert result == "python3 -m solokit.commands.status --json"

    @patch("solokit.core.system_utils.get_python_binary")
    def test_format_python_command_preserves_argument_spacing(self, mock_get_binary):
        """Test that format_python_command preserves spacing in arguments."""
        # Arrange
        mock_get_binary.return_value = "python3"

        # Act
        result = format_python_command("mymodule", "arg1    arg2")

        # Assert
        # Should preserve the extra spaces in arguments
        assert result == "python3 -m mymodule arg1    arg2"

    @patch("solokit.core.system_utils.get_python_binary")
    def test_format_python_command_with_quoted_arguments(self, mock_get_binary):
        """Test format_python_command with quoted arguments."""
        # Arrange
        mock_get_binary.return_value = "python3"

        # Act
        result = format_python_command(
            "solokit.module", '--message "Hello World" --name "Test User"'
        )

        # Assert
        assert result == 'python3 -m solokit.module --message "Hello World" --name "Test User"'

    @patch("solokit.core.system_utils.get_python_binary")
    def test_format_python_command_with_nested_module_path(self, mock_get_binary):
        """Test format_python_command with deeply nested module path."""
        # Arrange
        mock_get_binary.return_value = "python3"

        # Act
        result = format_python_command("pkg.subpkg.subsubpkg.module", "arg")

        # Assert
        assert result == "python3 -m pkg.subpkg.subsubpkg.module arg"

    @patch("solokit.core.system_utils.get_python_binary")
    def test_format_python_command_multiple_calls_same_module(self, mock_get_binary):
        """Test multiple calls to format_python_command with same module."""
        # Arrange
        mock_get_binary.return_value = "python3"

        # Act
        result1 = format_python_command("module", "arg1")
        result2 = format_python_command("module", "arg2")

        # Assert
        assert result1 == "python3 -m module arg1"
        assert result2 == "python3 -m module arg2"
        assert mock_get_binary.call_count == 2

    @patch("solokit.core.system_utils.get_python_binary")
    def test_format_python_command_with_numeric_arguments(self, mock_get_binary):
        """Test format_python_command with numeric arguments."""
        # Arrange
        mock_get_binary.return_value = "python3"

        # Act
        result = format_python_command("module", "123 456 789")

        # Assert
        assert result == "python3 -m module 123 456 789"

    @patch("solokit.core.system_utils.get_python_binary")
    def test_format_python_command_with_special_characters_in_args(self, mock_get_binary):
        """Test format_python_command with special characters in arguments."""
        # Arrange
        mock_get_binary.return_value = "python3"

        # Act
        result = format_python_command("module", "--pattern *.py --exclude __pycache__")

        # Assert
        assert result == "python3 -m module --pattern *.py --exclude __pycache__"


class TestSystemUtilsIntegration:
    """Integration tests for system_utils module."""

    def test_get_python_binary_returns_valid_binary(self):
        """Test that get_python_binary returns a valid Python binary (integration test)."""
        # Act
        result = get_python_binary()

        # Assert
        # Should return one of the expected values
        assert result in ["python3", "python"] or result == sys.executable
        # Should not be empty
        assert len(result) > 0

    def test_format_python_command_produces_executable_command(self):
        """Test that format_python_command produces a valid command format."""
        # Act
        result = format_python_command("test.module", "--help")

        # Assert
        # Should contain -m flag
        assert " -m " in result
        # Should contain module path
        assert "test.module" in result
        # Should contain arguments
        assert "--help" in result
        # Should start with a python binary name or path
        assert (
            result.startswith("python3 ")
            or result.startswith("python ")
            or result.startswith(sys.executable + " ")
        )

    def test_command_formatting_consistency(self):
        """Test that multiple calls produce consistent command format."""
        # Act
        cmd1 = format_python_command("module1")
        cmd2 = format_python_command("module2")

        # Assert
        # Both should use same python binary
        binary1 = cmd1.split(" ")[0]
        binary2 = cmd2.split(" ")[0]
        assert binary1 == binary2

    @patch("solokit.core.system_utils.get_python_binary")
    def test_edge_case_module_path_starting_with_dash(self, mock_get_binary):
        """Test format_python_command with edge case module path."""
        # Arrange
        mock_get_binary.return_value = "python3"

        # Act
        result = format_python_command("-m", "args")

        # Assert
        # Should still format correctly even with unusual module name
        assert result == "python3 -m -m args"

    @patch("solokit.core.system_utils.get_python_binary")
    def test_empty_module_path(self, mock_get_binary):
        """Test format_python_command with empty module path."""
        # Arrange
        mock_get_binary.return_value = "python3"

        # Act
        result = format_python_command("")

        # Assert
        assert result == "python3 -m "

    @patch("solokit.core.system_utils.get_python_binary")
    def test_whitespace_handling_in_module_path(self, mock_get_binary):
        """Test format_python_command with whitespace in module path."""
        # Arrange
        mock_get_binary.return_value = "python3"

        # Act
        result = format_python_command("module name with spaces")

        # Assert
        # Function doesn't validate module path, just formats it
        assert result == "python3 -m module name with spaces"
