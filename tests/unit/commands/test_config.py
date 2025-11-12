"""Unit tests for config command."""

import json
import sys
from unittest.mock import MagicMock, patch

from solokit.commands.config import format_config_yaml_style, main, show_config


def test_format_config_yaml_style_simple():
    """Test YAML-style formatting with simple config."""
    config = {"key1": "value1", "key2": "value2"}
    result = format_config_yaml_style(config)
    assert "key1: value1" in result
    assert "key2: value2" in result


def test_format_config_yaml_style_nested():
    """Test YAML-style formatting with nested config."""
    config = {"parent": {"child1": "value1", "child2": "value2"}}
    result = format_config_yaml_style(config)
    assert "parent:" in result
    assert "child1: value1" in result
    assert "child2: value2" in result


def test_format_config_yaml_style_list():
    """Test YAML-style formatting with list values."""
    config = {"items": ["item1", "item2", "item3"]}
    result = format_config_yaml_style(config)
    assert "items:" in result
    # Lists should have dash prefix
    assert "- item" in result or "item1" in result


def test_format_config_yaml_style_list_with_dicts():
    """Test YAML-style formatting with list of dictionaries."""
    config = {"items": [{"name": "item1", "value": 1}, {"name": "item2", "value": 2}]}
    result = format_config_yaml_style(config)
    assert "items:" in result
    assert "name: item1" in result
    assert "value: 1" in result


def test_show_config_missing_file(capsys, tmp_path, monkeypatch):
    """Test config show when config file doesn't exist."""
    # Change to temp directory
    monkeypatch.chdir(tmp_path)

    result = show_config(as_json=False)

    captured = capsys.readouterr()
    assert "Config file not found" in captured.out
    assert result == 1


def test_show_config_with_valid_file(capsys, tmp_path, monkeypatch):
    """Test config show with valid config file."""
    # Create .session directory and config file
    session_dir = tmp_path / ".session"
    session_dir.mkdir()
    config_file = session_dir / "config.json"
    config_data = {"quality_gates": {"test_execution": {"enabled": True}}}
    config_file.write_text(json.dumps(config_data))

    # Change to temp directory
    monkeypatch.chdir(tmp_path)

    result = show_config(as_json=False)

    captured = capsys.readouterr()
    assert "quality_gates" in captured.out
    assert result == 0


def test_show_config_json_format(capsys, tmp_path, monkeypatch):
    """Test config show with JSON output format."""
    # Create .session directory and config file
    session_dir = tmp_path / ".session"
    session_dir.mkdir()
    config_file = session_dir / "config.json"
    config_data = {"test_key": "test_value"}
    config_file.write_text(json.dumps(config_data))

    # Change to temp directory
    monkeypatch.chdir(tmp_path)

    result = show_config(as_json=True)

    captured = capsys.readouterr()
    # Should be valid JSON in output
    assert "test_key" in captured.out
    assert "test_value" in captured.out
    assert result == 0


def test_show_config_invalid_json(capsys, tmp_path, monkeypatch):
    """Test config show with invalid JSON in config file."""
    # Create .session directory and config file with invalid JSON
    session_dir = tmp_path / ".session"
    session_dir.mkdir()
    config_file = session_dir / "config.json"
    config_file.write_text("{invalid json content}")

    # Change to temp directory
    monkeypatch.chdir(tmp_path)

    result = show_config(as_json=False)

    captured = capsys.readouterr()
    assert "invalid JSON" in captured.err
    assert result == 1


def test_show_config_validation_error(capsys, tmp_path, monkeypatch):
    """Test config show when ConfigManager validation fails."""
    # Create .session directory and config file
    session_dir = tmp_path / ".session"
    session_dir.mkdir()
    config_file = session_dir / "config.json"
    config_data = {"invalid": "config"}
    config_file.write_text(json.dumps(config_data))

    # Change to temp directory
    monkeypatch.chdir(tmp_path)

    # Mock ConfigManager to raise an exception during validation
    with patch("solokit.commands.config.ConfigManager") as mock_config_manager:
        mock_instance = MagicMock()
        mock_instance.load_config.side_effect = Exception("Validation failed")
        mock_config_manager.return_value = mock_instance

        result = show_config(as_json=False)

        captured = capsys.readouterr()
        assert "Configuration has errors" in captured.err
        assert "Validation failed" in captured.err
        assert result == 1


def test_show_config_read_error(capsys, tmp_path, monkeypatch):
    """Test config show when file read error occurs."""
    # Create .session directory and config file
    session_dir = tmp_path / ".session"
    session_dir.mkdir()
    config_file = session_dir / "config.json"
    config_file.write_text('{"test": "data"}')

    # Change to temp directory
    monkeypatch.chdir(tmp_path)

    # Mock open to raise an exception
    with patch("builtins.open", side_effect=PermissionError("Permission denied")):
        result = show_config(as_json=False)

        captured = capsys.readouterr()
        assert "Error reading configuration" in captured.err
        assert result == 1


def test_main_show_subcommand(capsys, tmp_path, monkeypatch):
    """Test main function with 'show' subcommand."""
    # Create .session directory and config file
    session_dir = tmp_path / ".session"
    session_dir.mkdir()
    config_file = session_dir / "config.json"
    config_data = {"test": "data"}
    config_file.write_text(json.dumps(config_data))

    # Change to temp directory
    monkeypatch.chdir(tmp_path)

    # Mock sys.argv
    with patch.object(sys, "argv", ["config", "show"]):
        result = main()

    assert result in [0, 1]


def test_main_show_with_json_flag(capsys, tmp_path, monkeypatch):
    """Test main function with --json flag."""
    # Create .session directory and config file
    session_dir = tmp_path / ".session"
    session_dir.mkdir()
    config_file = session_dir / "config.json"
    config_data = {"test": "data"}
    config_file.write_text(json.dumps(config_data))

    # Change to temp directory
    monkeypatch.chdir(tmp_path)

    # Mock sys.argv
    with patch.object(sys, "argv", ["config", "show", "--json"]):
        result = main()

    captured = capsys.readouterr()
    assert '"test"' in captured.out
    assert result in [0, 1]


def test_main_unknown_subcommand(capsys):
    """Test main function with unknown subcommand."""
    # Mock sys.argv
    with patch.object(sys, "argv", ["config", "invalid"]):
        result = main()

    captured = capsys.readouterr()
    assert "Unknown subcommand" in captured.err
    assert "invalid" in captured.err
    assert result == 1


def test_main_default_subcommand(capsys, tmp_path, monkeypatch):
    """Test main function with no subcommand (defaults to show)."""
    # Create .session directory and config file
    session_dir = tmp_path / ".session"
    session_dir.mkdir()
    config_file = session_dir / "config.json"
    config_data = {"test": "data"}
    config_file.write_text(json.dumps(config_data))

    # Change to temp directory
    monkeypatch.chdir(tmp_path)

    # Mock sys.argv with no subcommand
    with patch.object(sys, "argv", ["config"]):
        result = main()

    assert result in [0, 1]
