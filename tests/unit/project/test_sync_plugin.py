"""Unit tests for sync_plugin module.

Tests plugin sync operations between main SDD repo and claude-plugins marketplace.
"""

import json
from unittest.mock import patch

import pytest

from sdd.core.exceptions import (
    FileNotFoundError as SDDFileNotFoundError,
)
from sdd.core.exceptions import (
    FileOperationError,
    ValidationError,
)
from sdd.project.sync_plugin import PluginSyncer


class TestPluginSyncerInit:
    """Tests for PluginSyncer initialization."""

    def test_init_with_defaults(self, tmp_path):
        """Test initialization with default values."""
        # Arrange
        main_repo = tmp_path / "main"
        plugin_repo = tmp_path / "plugin"
        main_repo.mkdir()
        plugin_repo.mkdir()

        # Act
        syncer = PluginSyncer(main_repo, plugin_repo)

        # Assert
        assert syncer.main_repo == main_repo.resolve()
        assert syncer.plugin_repo == plugin_repo.resolve()
        assert syncer.dry_run is False
        assert syncer.changes == []

    def test_init_with_dry_run(self, tmp_path):
        """Test initialization with dry_run enabled."""
        # Arrange
        main_repo = tmp_path / "main"
        plugin_repo = tmp_path / "plugin"
        main_repo.mkdir()
        plugin_repo.mkdir()

        # Act
        syncer = PluginSyncer(main_repo, plugin_repo, dry_run=True)

        # Assert
        assert syncer.dry_run is True


class TestValidateRepos:
    """Tests for validate_repos method."""

    def test_validate_repos_success(self, tmp_path):
        """Test successful repository validation."""
        # Arrange
        main_repo = tmp_path / "main"
        plugin_repo = tmp_path / "plugin"

        # Create main repo structure
        (main_repo / "src/sdd").mkdir(parents=True)
        (main_repo / "src/sdd/cli.py").touch()
        (main_repo / "pyproject.toml").touch()
        (main_repo / ".claude/commands").mkdir(parents=True)

        # Create plugin repo structure
        (plugin_repo / "sdd/.claude-plugin").mkdir(parents=True)
        (plugin_repo / "sdd/.claude-plugin/plugin.json").touch()

        syncer = PluginSyncer(main_repo, plugin_repo)

        # Act & Assert - should not raise
        syncer.validate_repos()

    def test_validate_repos_main_not_found(self, tmp_path):
        """Test validation fails when main repo doesn't exist."""
        # Arrange
        main_repo = tmp_path / "main"
        plugin_repo = tmp_path / "plugin"
        plugin_repo.mkdir()

        syncer = PluginSyncer(main_repo, plugin_repo)

        # Act & Assert
        with pytest.raises(SDDFileNotFoundError) as exc_info:
            syncer.validate_repos()

        assert str(main_repo) in exc_info.value.context["file_path"]
        assert exc_info.value.context["file_type"] == "main repository"

    def test_validate_repos_plugin_not_found(self, tmp_path):
        """Test validation fails when plugin repo doesn't exist."""
        # Arrange
        main_repo = tmp_path / "main"
        plugin_repo = tmp_path / "plugin"
        main_repo.mkdir()

        # Create main repo structure
        (main_repo / "src/sdd").mkdir(parents=True)
        (main_repo / "src/sdd/cli.py").touch()
        (main_repo / "pyproject.toml").touch()
        (main_repo / ".claude/commands").mkdir(parents=True)

        syncer = PluginSyncer(main_repo, plugin_repo)

        # Act & Assert
        with pytest.raises(SDDFileNotFoundError) as exc_info:
            syncer.validate_repos()

        assert str(plugin_repo) in exc_info.value.context["file_path"]
        assert exc_info.value.context["file_type"] == "plugin repository"

    def test_validate_repos_missing_main_marker(self, tmp_path):
        """Test validation fails when main repo missing expected file."""
        # Arrange
        main_repo = tmp_path / "main"
        plugin_repo = tmp_path / "plugin"
        main_repo.mkdir()

        # Create incomplete main repo structure (missing cli.py)
        (main_repo / "src/sdd").mkdir(parents=True)
        (main_repo / "pyproject.toml").touch()
        (main_repo / ".claude/commands").mkdir(parents=True)

        (plugin_repo / "sdd/.claude-plugin").mkdir(parents=True)
        (plugin_repo / "sdd/.claude-plugin/plugin.json").touch()

        syncer = PluginSyncer(main_repo, plugin_repo)

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            syncer.validate_repos()

        assert "src/sdd/cli.py" in exc_info.value.message
        assert exc_info.value.context["missing_marker"] == "src/sdd/cli.py"
        assert str(main_repo) in exc_info.value.context["repository"]

    def test_validate_repos_missing_plugin_marker(self, tmp_path):
        """Test validation fails when plugin repo missing expected file."""
        # Arrange
        main_repo = tmp_path / "main"
        plugin_repo = tmp_path / "plugin"

        # Create complete main repo structure
        (main_repo / "src/sdd").mkdir(parents=True)
        (main_repo / "src/sdd/cli.py").touch()
        (main_repo / "pyproject.toml").touch()
        (main_repo / ".claude/commands").mkdir(parents=True)

        # Create incomplete plugin repo structure (missing plugin.json)
        (plugin_repo / "sdd").mkdir(parents=True)

        syncer = PluginSyncer(main_repo, plugin_repo)

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            syncer.validate_repos()

        assert "sdd/.claude-plugin/plugin.json" in exc_info.value.message
        assert exc_info.value.context["missing_marker"] == "sdd/.claude-plugin/plugin.json"
        assert str(plugin_repo) in exc_info.value.context["repository"]


class TestGetVersionFromMain:
    """Tests for get_version_from_main method."""

    def test_get_version_success(self, tmp_path):
        """Test successfully extracting version from pyproject.toml."""
        # Arrange
        main_repo = tmp_path / "main"
        plugin_repo = tmp_path / "plugin"
        main_repo.mkdir()
        plugin_repo.mkdir()

        pyproject = main_repo / "pyproject.toml"
        pyproject.write_text('[tool.poetry]\nname = "sdd"\nversion = "0.5.7"\n')

        syncer = PluginSyncer(main_repo, plugin_repo)

        # Act
        version = syncer.get_version_from_main()

        # Assert
        assert version == "0.5.7"

    def test_get_version_pyproject_not_found(self, tmp_path):
        """Test error when pyproject.toml doesn't exist."""
        # Arrange
        main_repo = tmp_path / "main"
        plugin_repo = tmp_path / "plugin"
        main_repo.mkdir()
        plugin_repo.mkdir()

        syncer = PluginSyncer(main_repo, plugin_repo)

        # Act & Assert
        with pytest.raises(SDDFileNotFoundError) as exc_info:
            syncer.get_version_from_main()

        assert "pyproject.toml" in exc_info.value.context["file_path"]
        assert exc_info.value.context["file_type"] == "pyproject.toml"

    def test_get_version_not_found_in_file(self, tmp_path):
        """Test error when version field not found in pyproject.toml."""
        # Arrange
        main_repo = tmp_path / "main"
        plugin_repo = tmp_path / "plugin"
        main_repo.mkdir()
        plugin_repo.mkdir()

        pyproject = main_repo / "pyproject.toml"
        pyproject.write_text('[tool.poetry]\nname = "sdd"\n')

        syncer = PluginSyncer(main_repo, plugin_repo)

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            syncer.get_version_from_main()

        assert "Version not found" in exc_info.value.message
        assert exc_info.value.context["expected_field"] == "version"

    def test_get_version_read_error(self, tmp_path):
        """Test error handling when file cannot be read."""
        # Arrange
        main_repo = tmp_path / "main"
        plugin_repo = tmp_path / "plugin"
        main_repo.mkdir()
        plugin_repo.mkdir()

        pyproject = main_repo / "pyproject.toml"
        pyproject.write_text('version = "1.0.0"')

        syncer = PluginSyncer(main_repo, plugin_repo)

        # Act & Assert
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            with pytest.raises(FileOperationError) as exc_info:
                syncer.get_version_from_main()

            assert exc_info.value.context["operation"] == "read"
            assert "Permission denied" in exc_info.value.context["details"]


class TestUpdatePluginVersion:
    """Tests for update_plugin_version method."""

    def test_update_version_success(self, tmp_path):
        """Test successfully updating version in plugin.json."""
        # Arrange
        main_repo = tmp_path / "main"
        plugin_repo = tmp_path / "plugin"
        main_repo.mkdir()

        plugin_json_dir = plugin_repo / "sdd/.claude-plugin"
        plugin_json_dir.mkdir(parents=True)
        plugin_json_path = plugin_json_dir / "plugin.json"

        initial_data = {"name": "sdd", "version": "0.5.0"}
        plugin_json_path.write_text(json.dumps(initial_data, indent=2))

        syncer = PluginSyncer(main_repo, plugin_repo)

        # Act
        syncer.update_plugin_version("0.5.7")

        # Assert
        updated_data = json.loads(plugin_json_path.read_text())
        assert updated_data["version"] == "0.5.7"
        assert updated_data["name"] == "sdd"
        assert "0.5.0 → 0.5.7" in syncer.changes[0]

    def test_update_version_dry_run(self, tmp_path):
        """Test dry run mode doesn't actually update file."""
        # Arrange
        main_repo = tmp_path / "main"
        plugin_repo = tmp_path / "plugin"
        main_repo.mkdir()

        plugin_json_dir = plugin_repo / "sdd/.claude-plugin"
        plugin_json_dir.mkdir(parents=True)
        plugin_json_path = plugin_json_dir / "plugin.json"

        initial_data = {"name": "sdd", "version": "0.5.0"}
        plugin_json_path.write_text(json.dumps(initial_data, indent=2))

        syncer = PluginSyncer(main_repo, plugin_repo, dry_run=True)

        # Act
        syncer.update_plugin_version("0.5.7")

        # Assert
        # File should be unchanged
        updated_data = json.loads(plugin_json_path.read_text())
        assert updated_data["version"] == "0.5.0"

        # Change should be recorded
        assert any("0.5.7" in change for change in syncer.changes)

    def test_update_version_invalid_json(self, tmp_path):
        """Test error when plugin.json contains invalid JSON."""
        # Arrange
        main_repo = tmp_path / "main"
        plugin_repo = tmp_path / "plugin"
        main_repo.mkdir()

        plugin_json_dir = plugin_repo / "sdd/.claude-plugin"
        plugin_json_dir.mkdir(parents=True)
        plugin_json_path = plugin_json_dir / "plugin.json"

        # Write invalid JSON
        plugin_json_path.write_text("{invalid json}")

        syncer = PluginSyncer(main_repo, plugin_repo)

        # Act & Assert
        with pytest.raises(FileOperationError) as exc_info:
            syncer.update_plugin_version("0.5.7")

        assert exc_info.value.context["operation"] == "parse"
        assert "Invalid JSON" in exc_info.value.context["details"]

    def test_update_version_write_error(self, tmp_path):
        """Test error handling when file cannot be written."""
        # Arrange
        main_repo = tmp_path / "main"
        plugin_repo = tmp_path / "plugin"
        main_repo.mkdir()

        plugin_json_dir = plugin_repo / "sdd/.claude-plugin"
        plugin_json_dir.mkdir(parents=True)
        plugin_json_path = plugin_json_dir / "plugin.json"

        initial_data = {"name": "sdd", "version": "0.5.0"}
        plugin_json_path.write_text(json.dumps(initial_data, indent=2))

        syncer = PluginSyncer(main_repo, plugin_repo)

        # Act & Assert
        with patch("builtins.open", side_effect=OSError("Disk full")):
            with pytest.raises(FileOperationError) as exc_info:
                syncer.update_plugin_version("0.5.7")

            # Should fail on read, not write, but same error type
            assert exc_info.value.context["operation"] in ["read", "write"]


class TestSyncFile:
    """Tests for sync_file method."""

    def test_sync_file_success(self, tmp_path):
        """Test successfully syncing a single file."""
        # Arrange
        main_repo = tmp_path / "main"
        plugin_repo = tmp_path / "plugin"
        main_repo.mkdir()
        plugin_repo.mkdir()

        src_file = main_repo / "test.txt"
        src_file.write_text("test content")

        dest_file = plugin_repo / "test.txt"

        syncer = PluginSyncer(main_repo, plugin_repo)

        # Act
        syncer.sync_file(src_file, dest_file)

        # Assert
        assert dest_file.exists()
        assert dest_file.read_text() == "test content"
        assert len(syncer.changes) == 1

    def test_sync_file_creates_parent_dirs(self, tmp_path):
        """Test that sync_file creates parent directories."""
        # Arrange
        main_repo = tmp_path / "main"
        plugin_repo = tmp_path / "plugin"
        main_repo.mkdir()
        plugin_repo.mkdir()

        src_file = main_repo / "test.txt"
        src_file.write_text("test content")

        dest_file = plugin_repo / "subdir/nested/test.txt"

        syncer = PluginSyncer(main_repo, plugin_repo)

        # Act
        syncer.sync_file(src_file, dest_file)

        # Assert
        assert dest_file.exists()
        assert dest_file.parent.exists()

    def test_sync_file_dry_run(self, tmp_path):
        """Test dry run mode doesn't actually copy file."""
        # Arrange
        main_repo = tmp_path / "main"
        plugin_repo = tmp_path / "plugin"
        main_repo.mkdir()
        plugin_repo.mkdir()

        src_file = main_repo / "test.txt"
        src_file.write_text("test content")

        dest_file = plugin_repo / "test.txt"

        syncer = PluginSyncer(main_repo, plugin_repo, dry_run=True)

        # Act
        syncer.sync_file(src_file, dest_file)

        # Assert
        assert not dest_file.exists()
        assert len(syncer.changes) == 1

    def test_sync_file_copy_error(self, tmp_path):
        """Test error handling when file copy fails."""
        # Arrange
        main_repo = tmp_path / "main"
        plugin_repo = tmp_path / "plugin"
        main_repo.mkdir()
        plugin_repo.mkdir()

        src_file = main_repo / "test.txt"
        src_file.write_text("test content")

        dest_file = plugin_repo / "test.txt"

        syncer = PluginSyncer(main_repo, plugin_repo)

        # Act & Assert
        with patch("shutil.copy2", side_effect=OSError("Copy failed")):
            with pytest.raises(FileOperationError) as exc_info:
                syncer.sync_file(src_file, dest_file)

            assert exc_info.value.context["operation"] == "copy"
            assert "Copy failed" in exc_info.value.context["details"]


class TestSyncDirectory:
    """Tests for sync_directory method."""

    def test_sync_directory_success(self, tmp_path):
        """Test successfully syncing a directory."""
        # Arrange
        main_repo = tmp_path / "main"
        plugin_repo = tmp_path / "plugin"
        main_repo.mkdir()
        plugin_repo.mkdir()

        # Create source directory with files
        src_dir = main_repo / "src"
        src_dir.mkdir()
        (src_dir / "file1.txt").write_text("content1")
        (src_dir / "file2.txt").write_text("content2")
        (src_dir / "subdir").mkdir()
        (src_dir / "subdir/file3.txt").write_text("content3")

        dest_dir = plugin_repo / "src"

        syncer = PluginSyncer(main_repo, plugin_repo)

        # Act
        syncer.sync_directory(src_dir, dest_dir)

        # Assert
        assert dest_dir.exists()
        assert (dest_dir / "file1.txt").read_text() == "content1"
        assert (dest_dir / "file2.txt").read_text() == "content2"
        assert (dest_dir / "subdir/file3.txt").read_text() == "content3"
        assert len(syncer.changes) == 1
        assert "3 files" in syncer.changes[0]

    def test_sync_directory_replaces_existing(self, tmp_path):
        """Test that sync_directory replaces existing directory."""
        # Arrange
        main_repo = tmp_path / "main"
        plugin_repo = tmp_path / "plugin"
        main_repo.mkdir()
        plugin_repo.mkdir()

        # Create source directory
        src_dir = main_repo / "src"
        src_dir.mkdir()
        (src_dir / "new_file.txt").write_text("new content")

        # Create existing destination directory with old file
        dest_dir = plugin_repo / "src"
        dest_dir.mkdir()
        (dest_dir / "old_file.txt").write_text("old content")

        syncer = PluginSyncer(main_repo, plugin_repo)

        # Act
        syncer.sync_directory(src_dir, dest_dir)

        # Assert
        assert dest_dir.exists()
        assert (dest_dir / "new_file.txt").exists()
        assert not (dest_dir / "old_file.txt").exists()

    def test_sync_directory_dry_run(self, tmp_path):
        """Test dry run mode doesn't actually sync directory."""
        # Arrange
        main_repo = tmp_path / "main"
        plugin_repo = tmp_path / "plugin"
        main_repo.mkdir()
        plugin_repo.mkdir()

        src_dir = main_repo / "src"
        src_dir.mkdir()
        (src_dir / "file1.txt").write_text("content1")

        dest_dir = plugin_repo / "src"

        syncer = PluginSyncer(main_repo, plugin_repo, dry_run=True)

        # Act
        syncer.sync_directory(src_dir, dest_dir)

        # Assert
        assert not dest_dir.exists()
        assert len(syncer.changes) == 1
        assert "1 files" in syncer.changes[0]

    def test_sync_directory_error(self, tmp_path):
        """Test error handling when directory sync fails."""
        # Arrange
        main_repo = tmp_path / "main"
        plugin_repo = tmp_path / "plugin"
        main_repo.mkdir()
        plugin_repo.mkdir()

        src_dir = main_repo / "src"
        src_dir.mkdir()
        (src_dir / "file.txt").write_text("content")

        dest_dir = plugin_repo / "src"

        syncer = PluginSyncer(main_repo, plugin_repo)

        # Act & Assert
        with patch("shutil.copytree", side_effect=OSError("Sync failed")):
            with pytest.raises(FileOperationError) as exc_info:
                syncer.sync_directory(src_dir, dest_dir)

            assert exc_info.value.context["operation"] == "sync_directory"
            assert "Sync failed" in exc_info.value.context["details"]


class TestSyncAllFiles:
    """Tests for sync_all_files method."""

    def test_sync_all_files_success(self, tmp_path):
        """Test successfully syncing all mapped files."""
        # Arrange
        main_repo = tmp_path / "main"
        plugin_repo = tmp_path / "plugin"

        # Create main repo structure
        (main_repo / "src/sdd").mkdir(parents=True)
        (main_repo / "src/sdd/cli.py").write_text("cli code")
        (main_repo / ".claude/commands").mkdir(parents=True)
        (main_repo / ".claude/commands/cmd.py").write_text("command code")
        (main_repo / "pyproject.toml").write_text("project config")

        plugin_repo.mkdir()

        syncer = PluginSyncer(main_repo, plugin_repo)

        # Act
        syncer.sync_all_files()

        # Assert
        assert (plugin_repo / "sdd/src/sdd/cli.py").exists()
        assert (plugin_repo / "sdd/commands/cmd.py").exists()
        assert (plugin_repo / "sdd/pyproject.toml").exists()
        assert len(syncer.changes) == 3

    def test_sync_all_files_skips_missing(self, tmp_path, caplog):
        """Test that missing source files are logged as warnings and skipped."""
        # Arrange
        main_repo = tmp_path / "main"
        plugin_repo = tmp_path / "plugin"

        # Create only partial main repo structure
        main_repo.mkdir()
        (main_repo / "pyproject.toml").write_text("project config")

        plugin_repo.mkdir()

        syncer = PluginSyncer(main_repo, plugin_repo)

        # Act
        syncer.sync_all_files()

        # Assert
        assert (plugin_repo / "sdd/pyproject.toml").exists()
        # Only one file should be synced
        assert len(syncer.changes) == 1


class TestGenerateSummary:
    """Tests for generate_summary method."""

    def test_generate_summary_with_changes(self, tmp_path):
        """Test summary generation with changes recorded."""
        # Arrange
        main_repo = tmp_path / "main"
        plugin_repo = tmp_path / "plugin"
        main_repo.mkdir()
        plugin_repo.mkdir()

        syncer = PluginSyncer(main_repo, plugin_repo)
        syncer.changes = ["Change 1", "Change 2", "Change 3"]

        # Act
        summary = syncer.generate_summary()

        # Assert
        assert "Plugin Sync Summary" in summary
        assert str(main_repo) in summary
        assert str(plugin_repo) in summary
        assert "Change 1" in summary
        assert "Change 2" in summary
        assert "Change 3" in summary

    def test_generate_summary_no_changes(self, tmp_path):
        """Test summary generation with no changes."""
        # Arrange
        main_repo = tmp_path / "main"
        plugin_repo = tmp_path / "plugin"
        main_repo.mkdir()
        plugin_repo.mkdir()

        syncer = PluginSyncer(main_repo, plugin_repo)

        # Act
        summary = syncer.generate_summary()

        # Assert
        assert "No changes made" in summary

    def test_generate_summary_dry_run(self, tmp_path):
        """Test summary includes dry run status."""
        # Arrange
        main_repo = tmp_path / "main"
        plugin_repo = tmp_path / "plugin"
        main_repo.mkdir()
        plugin_repo.mkdir()

        syncer = PluginSyncer(main_repo, plugin_repo, dry_run=True)

        # Act
        summary = syncer.generate_summary()

        # Assert
        assert "Dry run: True" in summary


class TestSync:
    """Tests for sync method (integration)."""

    def test_sync_success(self, tmp_path):
        """Test complete sync operation."""
        # Arrange
        main_repo = tmp_path / "main"
        plugin_repo = tmp_path / "plugin"

        # Create complete main repo structure
        (main_repo / "src/sdd").mkdir(parents=True)
        (main_repo / "src/sdd/cli.py").write_text("cli code")
        (main_repo / ".claude/commands").mkdir(parents=True)
        (main_repo / "pyproject.toml").write_text('version = "0.5.7"')

        # Create plugin repo structure
        (plugin_repo / "sdd/.claude-plugin").mkdir(parents=True)
        plugin_json = plugin_repo / "sdd/.claude-plugin/plugin.json"
        plugin_json.write_text(json.dumps({"version": "0.5.0"}))

        syncer = PluginSyncer(main_repo, plugin_repo)

        # Act
        syncer.sync()

        # Assert
        # Version should be updated
        updated_data = json.loads(plugin_json.read_text())
        assert updated_data["version"] == "0.5.7"

        # Files should be synced
        assert (plugin_repo / "sdd/src/sdd/cli.py").exists()

    def test_sync_validation_error(self, tmp_path):
        """Test sync fails with validation error."""
        # Arrange
        main_repo = tmp_path / "main"
        plugin_repo = tmp_path / "plugin"
        main_repo.mkdir()
        plugin_repo.mkdir()

        # Missing expected files
        syncer = PluginSyncer(main_repo, plugin_repo)

        # Act & Assert
        with pytest.raises((SDDFileNotFoundError, ValidationError)):
            syncer.sync()

    def test_sync_dry_run(self, tmp_path):
        """Test sync in dry run mode."""
        # Arrange
        main_repo = tmp_path / "main"
        plugin_repo = tmp_path / "plugin"

        # Create complete main repo structure
        (main_repo / "src/sdd").mkdir(parents=True)
        (main_repo / "src/sdd/cli.py").write_text("cli code")
        (main_repo / ".claude/commands").mkdir(parents=True)
        (main_repo / "pyproject.toml").write_text('version = "0.5.7"')

        # Create plugin repo structure
        (plugin_repo / "sdd/.claude-plugin").mkdir(parents=True)
        plugin_json = plugin_repo / "sdd/.claude-plugin/plugin.json"
        plugin_json.write_text(json.dumps({"version": "0.5.0"}))

        syncer = PluginSyncer(main_repo, plugin_repo, dry_run=True)

        # Act
        syncer.sync()

        # Assert
        # Version should NOT be updated
        updated_data = json.loads(plugin_json.read_text())
        assert updated_data["version"] == "0.5.0"

        # Files should NOT be synced
        assert not (plugin_repo / "sdd/src/sdd/cli.py").exists()

        # But changes should be recorded
        assert len(syncer.changes) > 0
