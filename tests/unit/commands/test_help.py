"""Unit tests for help command."""

from solokit.commands.help import show_command_help, show_help


def test_help_shows_usage(capsys):
    """Test that help command displays usage information."""
    result = show_help()

    captured = capsys.readouterr()
    assert "Usage: sk" in captured.out
    assert result == 0


def test_help_shows_global_flags(capsys):
    """Test that help command displays global flags."""
    result = show_help()

    captured = capsys.readouterr()
    assert "--verbose" in captured.out
    assert "--log-file" in captured.out
    assert "--version" in captured.out
    assert "--help" in captured.out
    assert result == 0


def test_help_shows_work_items_commands(capsys):
    """Test that help command displays work items commands."""
    result = show_help()

    captured = capsys.readouterr()
    assert "work-list" in captured.out
    assert "work-show" in captured.out
    assert "work-new" in captured.out
    assert "work-update" in captured.out
    assert "work-delete" in captured.out
    assert "work-next" in captured.out
    assert "work-graph" in captured.out
    assert result == 0


def test_help_shows_session_commands(capsys):
    """Test that help command displays session management commands."""
    result = show_help()

    captured = capsys.readouterr()
    assert "start" in captured.out
    assert "end" in captured.out
    assert "status" in captured.out
    assert "validate" in captured.out
    assert result == 0


def test_help_shows_learning_commands(capsys):
    """Test that help command displays learning system commands."""
    result = show_help()

    captured = capsys.readouterr()
    assert "learn" in captured.out
    assert "learn-show" in captured.out
    assert "learn-search" in captured.out
    assert "learn-curate" in captured.out
    assert result == 0


def test_help_shows_utility_commands(capsys):
    """Test that help command displays utility commands."""
    result = show_help()

    captured = capsys.readouterr()
    assert "help" in captured.out
    assert "version" in captured.out
    assert "doctor" in captured.out
    assert "config" in captured.out
    assert result == 0


def test_help_shows_categories(capsys):
    """Test that help command organizes commands by category."""
    result = show_help()

    captured = capsys.readouterr()
    assert "Work Items Management:" in captured.out
    assert "Session Management:" in captured.out
    assert "Learning System:" in captured.out
    assert "Utilities:" in captured.out
    assert result == 0


def test_command_specific_help_version(capsys):
    """Test command-specific help for version command."""
    result = show_command_help("version")

    captured = capsys.readouterr()
    assert "Command: sk version" in captured.out
    assert "Description:" in captured.out
    assert "Usage:" in captured.out
    assert "Examples:" in captured.out
    assert result == 0


def test_command_specific_help_work_new(capsys):
    """Test command-specific help for work-new command."""
    result = show_command_help("work-new")

    captured = capsys.readouterr()
    assert "Command: sk work-new" in captured.out
    assert "Options:" in captured.out
    assert "--type" in captured.out
    assert "--title" in captured.out
    assert "--priority" in captured.out
    assert result == 0


def test_command_specific_help_invalid_command(capsys):
    """Test command-specific help with invalid command name."""
    result = show_command_help("invalid-command")

    captured = capsys.readouterr()
    # Error messages go to stderr
    assert "Unknown command: invalid-command" in captured.err
    assert result == 1


def test_help_returns_success_code():
    """Test that help command returns exit code 0."""
    result = show_help()
    assert result == 0
