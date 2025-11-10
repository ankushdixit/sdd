"""Unit tests for config command."""

import json

from solokit.commands.config import format_config_yaml_style, show_config


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
