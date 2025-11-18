"""
Tests for claude_commands_installer module.

Validates Claude Code slash commands installation to user projects.

Run tests:
    pytest tests/unit/init/test_claude_commands_installer.py -v

Target: 90%+ coverage
"""

from unittest.mock import Mock, patch

import pytest
from solokit.core.exceptions import FileOperationError, TemplateNotFoundError
from solokit.init.claude_commands_installer import install_claude_commands


class TestInstallClaudeCommands:
    """Tests for install_claude_commands()."""

    def test_install_commands_success(self, tmp_path):
        """Test successful Claude commands installation."""
        # Setup: Create mock template commands directory
        package_dir = tmp_path / "package"
        commands_source = package_dir / "templates" / ".claude" / "commands"
        commands_source.mkdir(parents=True)

        # Create sample command files
        (commands_source / "start.md").write_text("# Start Command")
        (commands_source / "end.md").write_text("# End Command")
        (commands_source / "work-new.md").write_text("# Work New Command")

        # Setup: Create project directory
        project_root = tmp_path / "project"
        project_root.mkdir()

        # Mock the package directory path
        with patch("solokit.init.claude_commands_installer.Path") as mock_path_class:
            mock_file = Mock()
            mock_file.parent.parent = package_dir
            mock_path_class.return_value = mock_file

            # Execute
            installed = install_claude_commands(project_root)

            # Assert
            assert len(installed) == 3
            assert (project_root / ".claude" / "commands" / "start.md").exists()
            assert (project_root / ".claude" / "commands" / "end.md").exists()
            assert (project_root / ".claude" / "commands" / "work-new.md").exists()

    def test_install_commands_creates_directory(self, tmp_path):
        """Test that .claude/commands directory is created if it doesn't exist."""
        # Setup
        package_dir = tmp_path / "package"
        commands_source = package_dir / "templates" / ".claude" / "commands"
        commands_source.mkdir(parents=True)
        (commands_source / "test.md").write_text("# Test")

        project_root = tmp_path / "project"
        project_root.mkdir()

        # Mock package path
        with patch("solokit.init.claude_commands_installer.Path") as mock_path_class:
            mock_file = Mock()
            mock_file.parent.parent = package_dir
            mock_path_class.return_value = mock_file

            # Execute
            install_claude_commands(project_root)

            # Assert directory was created
            assert (project_root / ".claude" / "commands").exists()
            assert (project_root / ".claude" / "commands").is_dir()

    def test_template_not_found_error(self, tmp_path):
        """Test error when .claude/commands template directory doesn't exist."""
        # Setup: Package without commands
        package_dir = tmp_path / "package"
        package_dir.mkdir()

        project_root = tmp_path / "project"
        project_root.mkdir()

        # Mock package path
        with patch("solokit.init.claude_commands_installer.Path") as mock_path_class:
            mock_file = Mock()
            mock_file.parent.parent = package_dir
            mock_path_class.return_value = mock_file

            # Execute & Assert
            with pytest.raises(TemplateNotFoundError) as exc_info:
                install_claude_commands(project_root)

            assert ".claude/commands" in str(exc_info.value)

    def test_no_command_files_warning(self, tmp_path, caplog):
        """Test warning logged when commands directory exists but has no .md files."""
        # Setup: Empty commands directory
        package_dir = tmp_path / "package"
        commands_source = package_dir / "templates" / ".claude" / "commands"
        commands_source.mkdir(parents=True)
        # Create a non-.md file
        (commands_source / "README.txt").write_text("Not a command")

        project_root = tmp_path / "project"
        project_root.mkdir()

        # Mock package path
        with patch("solokit.init.claude_commands_installer.Path") as mock_path_class:
            mock_file = Mock()
            mock_file.parent.parent = package_dir
            mock_path_class.return_value = mock_file

            # Execute
            with caplog.at_level("WARNING"):
                installed = install_claude_commands(project_root)

            # Assert
            assert len(installed) == 0
            assert "No .md files found" in caplog.text

    def test_file_operation_error(self, tmp_path):
        """Test FileOperationError when file copy fails."""
        # Setup
        package_dir = tmp_path / "package"
        commands_source = package_dir / "templates" / ".claude" / "commands"
        commands_source.mkdir(parents=True)
        (commands_source / "test.md").write_text("# Test")

        project_root = tmp_path / "project"
        project_root.mkdir()

        # Mock package path and force copy to fail
        with patch("solokit.init.claude_commands_installer.Path") as mock_path_class:
            mock_file = Mock()
            mock_file.parent.parent = package_dir
            mock_path_class.return_value = mock_file

            with patch("solokit.init.claude_commands_installer.shutil.copy2") as mock_copy:
                mock_copy.side_effect = OSError("Permission denied")

                # Execute & Assert
                with pytest.raises(FileOperationError) as exc_info:
                    install_claude_commands(project_root)

                assert "Failed to install Claude Code commands" in str(exc_info.value)

    def test_install_all_16_commands(self, tmp_path):
        """Test that all 16 slash commands are installed correctly."""
        # Setup: Create all 16 command files
        package_dir = tmp_path / "package"
        commands_source = package_dir / "templates" / ".claude" / "commands"
        commands_source.mkdir(parents=True)

        command_files = [
            "init.md",
            "start.md",
            "end.md",
            "status.md",
            "validate.md",
            "work-new.md",
            "work-list.md",
            "work-show.md",
            "work-update.md",
            "work-next.md",
            "work-graph.md",
            "work-delete.md",
            "learn.md",
            "learn-show.md",
            "learn-search.md",
            "learn-curate.md",
        ]

        for cmd_file in command_files:
            (commands_source / cmd_file).write_text(f"# {cmd_file}")

        project_root = tmp_path / "project"
        project_root.mkdir()

        # Mock package path
        with patch("solokit.init.claude_commands_installer.Path") as mock_path_class:
            mock_file = Mock()
            mock_file.parent.parent = package_dir
            mock_path_class.return_value = mock_file

            # Execute
            installed = install_claude_commands(project_root)

            # Assert
            assert len(installed) == 16
            for cmd_file in command_files:
                assert (project_root / ".claude" / "commands" / cmd_file).exists()

    def test_file_contents_preserved(self, tmp_path):
        """Test that file contents are correctly copied."""
        # Setup
        package_dir = tmp_path / "package"
        commands_source = package_dir / "templates" / ".claude" / "commands"
        commands_source.mkdir(parents=True)

        original_content = """# Start Command

This is the start command for Solokit.

Usage: /start [work_item_id]
"""
        (commands_source / "start.md").write_text(original_content)

        project_root = tmp_path / "project"
        project_root.mkdir()

        # Mock package path
        with patch("solokit.init.claude_commands_installer.Path") as mock_path_class:
            mock_file = Mock()
            mock_file.parent.parent = package_dir
            mock_path_class.return_value = mock_file

            # Execute
            install_claude_commands(project_root)

            # Assert
            installed_file = project_root / ".claude" / "commands" / "start.md"
            assert installed_file.read_text() == original_content

    def test_uses_current_directory_when_no_root_specified(self, tmp_path):
        """Test that current directory is used when project_root is None."""
        # Setup
        package_dir = tmp_path / "package"
        commands_source = package_dir / "templates" / ".claude" / "commands"
        commands_source.mkdir(parents=True)
        (commands_source / "test.md").write_text("# Test")

        # Mock both package path and cwd
        with patch("solokit.init.claude_commands_installer.Path") as mock_path_class:
            mock_file = Mock()
            mock_file.parent.parent = package_dir
            mock_path_class.return_value = mock_file
            mock_path_class.cwd.return_value = tmp_path

            # Execute with project_root=None
            install_claude_commands(project_root=None)

            # Assert - should use cwd
            mock_path_class.cwd.assert_called_once()

    def test_logging_messages(self, tmp_path, caplog):
        """Test that appropriate logging messages are generated."""
        # Setup
        package_dir = tmp_path / "package"
        commands_source = package_dir / "templates" / ".claude" / "commands"
        commands_source.mkdir(parents=True)
        (commands_source / "start.md").write_text("# Start")
        (commands_source / "end.md").write_text("# End")

        project_root = tmp_path / "project"
        project_root.mkdir()

        # Mock package path
        with patch("solokit.init.claude_commands_installer.Path") as mock_path_class:
            mock_file = Mock()
            mock_file.parent.parent = package_dir
            mock_path_class.return_value = mock_file

            # Execute
            with caplog.at_level("INFO"):
                install_claude_commands(project_root)

            # Assert logging
            assert "Installed 2 Claude Code slash commands" in caplog.text
            assert "You can now use slash commands" in caplog.text
