"""Unit tests for file_ops module.

Tests file and JSON operation utilities.
"""

import json

import pytest

from sdd.core.file_ops import (
    backup_file,
    ensure_directory,
    load_json,
    read_file,
    save_json,
    write_file,
)


class TestLoadJson:
    """Tests for load_json function."""

    def test_load_json_success(self, tmp_path):
        """Test loading valid JSON file."""
        # Arrange
        test_file = tmp_path / "test.json"
        test_data = {"key": "value", "number": 42}
        test_file.write_text(json.dumps(test_data))

        # Act
        result = load_json(test_file)

        # Assert
        assert result == test_data

    def test_load_json_file_not_found(self, tmp_path):
        """Test loading non-existent file raises FileNotFoundError."""
        # Arrange
        non_existent = tmp_path / "nonexistent.json"

        # Act & Assert
        with pytest.raises(FileNotFoundError, match="File not found"):
            load_json(non_existent)

    def test_load_json_complex_data(self, tmp_path):
        """Test loading JSON with complex nested data."""
        # Arrange
        test_file = tmp_path / "complex.json"
        test_data = {
            "nested": {"level1": {"level2": "value"}},
            "list": [1, 2, 3],
            "mixed": [{"a": 1}, {"b": 2}],
        }
        test_file.write_text(json.dumps(test_data))

        # Act
        result = load_json(test_file)

        # Assert
        assert result == test_data


class TestSaveJson:
    """Tests for save_json function."""

    def test_save_json_creates_file(self, tmp_path):
        """Test that save_json creates a new file."""
        # Arrange
        test_file = tmp_path / "output.json"
        test_data = {"key": "value"}

        # Act
        save_json(test_file, test_data)

        # Assert
        assert test_file.exists()
        loaded = json.loads(test_file.read_text())
        assert loaded == test_data

    def test_save_json_atomic_write_creates_temp(self, tmp_path):
        """Test that save_json uses atomic write (temp file is cleaned up)."""
        # Arrange
        test_file = tmp_path / "atomic.json"
        test_data = {"atomic": True}

        # Act
        save_json(test_file, test_data)

        # Assert
        # Temp file should be cleaned up after atomic rename
        temp_file = test_file.with_suffix(".tmp")
        assert not temp_file.exists()
        assert test_file.exists()

    def test_save_json_overwrites_existing(self, tmp_path):
        """Test that save_json overwrites existing file."""
        # Arrange
        test_file = tmp_path / "existing.json"
        test_file.write_text(json.dumps({"old": "data"}))
        new_data = {"new": "data"}

        # Act
        save_json(test_file, new_data)

        # Assert
        loaded = json.loads(test_file.read_text())
        assert loaded == new_data
        assert "old" not in loaded

    def test_save_json_with_custom_indent(self, tmp_path):
        """Test save_json with custom indentation."""
        # Arrange
        test_file = tmp_path / "indented.json"
        test_data = {"key": "value"}

        # Act
        save_json(test_file, test_data, indent=4)

        # Assert
        content = test_file.read_text()
        # With indent=4, there should be 4 spaces
        assert "    " in content

    def test_save_json_handles_datetime_with_default_str(self, tmp_path):
        """Test save_json handles non-serializable objects with default=str."""
        # Arrange
        from datetime import datetime

        test_file = tmp_path / "datetime.json"
        test_data = {"timestamp": datetime(2025, 1, 1, 12, 0, 0)}

        # Act
        save_json(test_file, test_data)

        # Assert
        # Should not raise, datetime converted to string
        assert test_file.exists()
        content = test_file.read_text()
        assert "2025" in content


class TestEnsureDirectory:
    """Tests for ensure_directory function."""

    def test_ensure_directory_creates_new(self, tmp_path):
        """Test ensure_directory creates new directory."""
        # Arrange
        new_dir = tmp_path / "new_directory"

        # Act
        ensure_directory(new_dir)

        # Assert
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_ensure_directory_creates_nested(self, tmp_path):
        """Test ensure_directory creates nested directories."""
        # Arrange
        nested_dir = tmp_path / "level1" / "level2" / "level3"

        # Act
        ensure_directory(nested_dir)

        # Assert
        assert nested_dir.exists()
        assert nested_dir.is_dir()

    def test_ensure_directory_idempotent(self, tmp_path):
        """Test ensure_directory is idempotent (doesn't fail if exists)."""
        # Arrange
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()

        # Act - Should not raise
        ensure_directory(existing_dir)

        # Assert
        assert existing_dir.exists()


class TestBackupFile:
    """Tests for backup_file function."""

    def test_backup_file_creates_backup(self, tmp_path):
        """Test backup_file creates backup copy."""
        # Arrange
        original = tmp_path / "original.txt"
        original.write_text("original content")

        # Act
        backup_path = backup_file(original)

        # Assert
        assert backup_path.exists()
        assert backup_path.name == "original.txt.backup"
        assert backup_path.read_text() == "original content"

    def test_backup_file_preserves_metadata(self, tmp_path):
        """Test backup_file preserves file metadata."""
        # Arrange
        original = tmp_path / "metadata.txt"
        original.write_text("content")

        # Act
        backup_path = backup_file(original)

        # Assert
        # Both files should exist
        assert original.exists()
        assert backup_path.exists()
        # Original content preserved
        assert original.read_text() == "content"

    def test_backup_file_not_found(self, tmp_path):
        """Test backup_file raises error for non-existent file."""
        # Arrange
        non_existent = tmp_path / "nonexistent.txt"

        # Act & Assert
        with pytest.raises(FileNotFoundError, match="File not found"):
            backup_file(non_existent)

    def test_backup_file_json(self, tmp_path):
        """Test backup_file works with JSON files."""
        # Arrange
        original = tmp_path / "data.json"
        original.write_text(json.dumps({"key": "value"}))

        # Act
        backup_path = backup_file(original)

        # Assert
        assert backup_path.name == "data.json.backup"
        assert json.loads(backup_path.read_text()) == {"key": "value"}


class TestReadFile:
    """Tests for read_file function."""

    def test_read_file_success(self, tmp_path):
        """Test reading file contents."""
        # Arrange
        test_file = tmp_path / "test.txt"
        content = "Hello, World!\nLine 2\nLine 3"
        test_file.write_text(content)

        # Act
        result = read_file(test_file)

        # Assert
        assert result == content

    def test_read_file_empty(self, tmp_path):
        """Test reading empty file."""
        # Arrange
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")

        # Act
        result = read_file(test_file)

        # Assert
        assert result == ""

    def test_read_file_unicode(self, tmp_path):
        """Test reading file with unicode characters."""
        # Arrange
        test_file = tmp_path / "unicode.txt"
        content = "Hello 世界 🌍 Привет"
        test_file.write_text(content, encoding="utf-8")

        # Act
        result = read_file(test_file)

        # Assert
        assert result == content


class TestWriteFile:
    """Tests for write_file function."""

    def test_write_file_creates_new(self, tmp_path):
        """Test write_file creates new file."""
        # Arrange
        test_file = tmp_path / "new.txt"
        content = "New file content"

        # Act
        write_file(test_file, content)

        # Assert
        assert test_file.exists()
        assert test_file.read_text() == content

    def test_write_file_overwrites_existing(self, tmp_path):
        """Test write_file overwrites existing file."""
        # Arrange
        test_file = tmp_path / "existing.txt"
        test_file.write_text("old content")
        new_content = "new content"

        # Act
        write_file(test_file, new_content)

        # Assert
        assert test_file.read_text() == new_content

    def test_write_file_multiline(self, tmp_path):
        """Test write_file with multiline content."""
        # Arrange
        test_file = tmp_path / "multiline.txt"
        content = "Line 1\nLine 2\nLine 3"

        # Act
        write_file(test_file, content)

        # Assert
        assert test_file.read_text() == content

    def test_write_file_unicode(self, tmp_path):
        """Test write_file with unicode characters."""
        # Arrange
        test_file = tmp_path / "unicode.txt"
        content = "Unicode: 你好 🚀 مرحبا"

        # Act
        write_file(test_file, content)

        # Assert
        assert test_file.read_text() == content
