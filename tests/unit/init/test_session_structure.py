"""
Tests for session_structure module.

Validates .session directory and tracking files creation.

Run tests:
    pytest tests/unit/init/test_session_structure.py -v

Target: 90%+ coverage
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from sdd.core.exceptions import FileOperationError
from sdd.init.session_structure import (
    create_session_directories,
    initialize_tracking_files,
)


class TestCreateSessionDirectories:
    """Tests for create_session_directories()."""

    def test_create_directories(self, tmp_path):
        """Test creating .session directory structure."""
        dirs = create_session_directories(tmp_path)

        assert len(dirs) >= 4
        assert (tmp_path / ".session" / "tracking").exists()
        assert (tmp_path / ".session" / "briefings").exists()
        assert (tmp_path / ".session" / "history").exists()
        assert (tmp_path / ".session" / "specs").exists()

    def test_directories_already_exist(self, tmp_path):
        """Test when directories already exist."""
        (tmp_path / ".session" / "tracking").mkdir(parents=True)

        dirs = create_session_directories(tmp_path)

        assert len(dirs) >= 4

    def test_error_handling(self, tmp_path):
        """Test error when directory creation fails."""
        with patch.object(Path, "mkdir", side_effect=PermissionError("Access denied")):
            with pytest.raises(FileOperationError):
                create_session_directories(tmp_path)

    def test_default_project_root(self):
        """Test using default project root (Path.cwd())."""
        with patch("sdd.init.session_structure.Path") as mock_path:
            mock_cwd = Mock()
            mock_cwd.cwd.return_value = Path("/fake/cwd")
            mock_path.cwd.return_value = Path("/fake/cwd")

            # Mock mkdir to not actually create directories
            with patch.object(Path, "mkdir"):
                create_session_directories()

            # Verify cwd was called
            mock_path.cwd.assert_called_once()


class TestInitializeTrackingFiles:
    """Tests for initialize_tracking_files()."""

    def test_create_tracking_files(self, tmp_path, tracking_template_files):
        """Test creating tracking files from templates."""
        (tmp_path / ".session" / "tracking").mkdir(parents=True)

        # Mock __file__ to point to a fake location so template_dir points to our test templates
        import sdd.init.session_structure as session_structure_module

        # Create a fake module structure: fake_sdd/init/session_structure.py
        # So Path(__file__).parent.parent / "templates" = fake_sdd/templates
        fake_sdd_dir = tmp_path / "fake_sdd"
        fake_init_dir = fake_sdd_dir / "init"
        fake_init_dir.mkdir(parents=True)

        # Copy template files to fake_sdd/templates
        fake_templates = fake_sdd_dir / "templates"
        fake_templates.mkdir()

        import shutil

        for item in tracking_template_files.iterdir():
            if item.is_file():
                shutil.copy(item, fake_templates / item.name)

        # Set __file__ to fake_sdd/init/session_structure.py
        fake_file = str(fake_init_dir / "session_structure.py")

        with patch.object(session_structure_module, "__file__", fake_file):
            files = initialize_tracking_files("tier-2-standard", 80, tmp_path)

            assert len(files) >= 2
            assert (tmp_path / ".session" / "config.json").exists()

    def test_config_json_has_tier_settings(self, tmp_path, tracking_template_files):
        """Test that config.json includes tier-specific settings."""
        (tmp_path / ".session" / "tracking").mkdir(parents=True)

        import shutil

        import sdd.init.session_structure as session_structure_module

        # Create a fake module structure: fake_sdd/init/session_structure.py
        fake_sdd_dir = tmp_path / "fake_sdd"
        fake_init_dir = fake_sdd_dir / "init"
        fake_init_dir.mkdir(parents=True)

        # Copy template files to fake_sdd/templates
        fake_templates = fake_sdd_dir / "templates"
        fake_templates.mkdir()

        for item in tracking_template_files.iterdir():
            if item.is_file():
                shutil.copy(item, fake_templates / item.name)

        fake_file = str(fake_init_dir / "session_structure.py")

        with patch.object(session_structure_module, "__file__", fake_file):
            initialize_tracking_files("tier-3-comprehensive", 90, tmp_path)

            config = json.loads((tmp_path / ".session" / "config.json").read_text())
            assert config["quality_gates"]["tier"] == "tier-3-comprehensive"
            assert config["quality_gates"]["coverage_threshold"] == 90

    def test_creates_update_tracking_files(self, tmp_path, tracking_template_files):
        """Test creating empty update tracking files."""
        (tmp_path / ".session" / "tracking").mkdir(parents=True)

        import shutil

        import sdd.init.session_structure as session_structure_module

        # Create a fake module structure: fake_sdd/init/session_structure.py
        fake_sdd_dir = tmp_path / "fake_sdd"
        fake_init_dir = fake_sdd_dir / "init"
        fake_init_dir.mkdir(parents=True)

        # Copy template files to fake_sdd/templates
        fake_templates = fake_sdd_dir / "templates"
        fake_templates.mkdir()

        for item in tracking_template_files.iterdir():
            if item.is_file():
                shutil.copy(item, fake_templates / item.name)

        fake_file = str(fake_init_dir / "session_structure.py")

        with patch.object(session_structure_module, "__file__", fake_file):
            initialize_tracking_files("tier-1-essential", 60, tmp_path)

            assert (tmp_path / ".session" / "tracking" / "stack_updates.json").exists()
            assert (tmp_path / ".session" / "tracking" / "tree_updates.json").exists()

    def test_default_project_root(self, tracking_template_files):
        """Test using default project root (Path.cwd())."""
        import shutil

        # Use a real tmp directory for the test
        import tempfile

        import sdd.init.session_structure as session_structure_module

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create .session/tracking directory
            (tmp_path / ".session" / "tracking").mkdir(parents=True)

            # Set up fake module structure
            fake_sdd_dir = tmp_path / "fake_sdd"
            fake_init_dir = fake_sdd_dir / "init"
            fake_init_dir.mkdir(parents=True)

            fake_templates = fake_sdd_dir / "templates"
            fake_templates.mkdir()

            for item in tracking_template_files.iterdir():
                if item.is_file():
                    shutil.copy(item, fake_templates / item.name)

            fake_file = str(fake_init_dir / "session_structure.py")

            # Mock Path.cwd() to return our tmp directory
            with patch("sdd.init.session_structure.Path.cwd", return_value=tmp_path):
                with patch.object(session_structure_module, "__file__", fake_file):
                    # Call without project_root to trigger Path.cwd()
                    files = initialize_tracking_files("tier-1-essential", 80)

                    assert len(files) >= 2

    def test_copy_error_handling(self, tmp_path, tracking_template_files):
        """Test error handling when file copy fails."""
        import shutil

        import sdd.init.session_structure as session_structure_module

        (tmp_path / ".session" / "tracking").mkdir(parents=True)

        # Set up fake module structure
        fake_sdd_dir = tmp_path / "fake_sdd"
        fake_init_dir = fake_sdd_dir / "init"
        fake_init_dir.mkdir(parents=True)

        fake_templates = fake_sdd_dir / "templates"
        fake_templates.mkdir()

        for item in tracking_template_files.iterdir():
            if item.is_file():
                shutil.copy(item, fake_templates / item.name)

        fake_file = str(fake_init_dir / "session_structure.py")

        with patch.object(session_structure_module, "__file__", fake_file):
            # Mock shutil.copy to raise an error
            with patch("shutil.copy", side_effect=PermissionError("Cannot copy")):
                with pytest.raises(FileOperationError) as exc:
                    initialize_tracking_files("tier-1-essential", 80, tmp_path)

                assert "Failed to copy tracking file template" in exc.value.details

    def test_update_tracking_creation_error(self, tmp_path, tracking_template_files):
        """Test error handling when creating update tracking files fails."""
        import shutil

        import sdd.init.session_structure as session_structure_module

        (tmp_path / ".session" / "tracking").mkdir(parents=True)

        # Set up fake module structure
        fake_sdd_dir = tmp_path / "fake_sdd"
        fake_init_dir = fake_sdd_dir / "init"
        fake_init_dir.mkdir(parents=True)

        fake_templates = fake_sdd_dir / "templates"
        fake_templates.mkdir()

        for item in tracking_template_files.iterdir():
            if item.is_file():
                shutil.copy(item, fake_templates / item.name)

        fake_file = str(fake_init_dir / "session_structure.py")

        with patch.object(session_structure_module, "__file__", fake_file):
            # Mock Path.write_text to raise an error
            with patch.object(Path, "write_text", side_effect=PermissionError("Cannot write")):
                with pytest.raises(FileOperationError) as exc:
                    initialize_tracking_files("tier-1-essential", 80, tmp_path)

                assert "Failed to create" in exc.value.details

    def test_config_schema_copy_error(self, tmp_path, tracking_template_files):
        """Test error handling when copying config schema fails."""
        import shutil

        import sdd.init.session_structure as session_structure_module

        (tmp_path / ".session" / "tracking").mkdir(parents=True)

        # Set up fake module structure
        fake_sdd_dir = tmp_path / "fake_sdd"
        fake_init_dir = fake_sdd_dir / "init"
        fake_init_dir.mkdir(parents=True)

        fake_templates = fake_sdd_dir / "templates"
        fake_templates.mkdir()

        for item in tracking_template_files.iterdir():
            if item.is_file():
                shutil.copy(item, fake_templates / item.name)

        fake_file = str(fake_init_dir / "session_structure.py")

        # Create a scenario where config.schema.json copy fails
        def mock_copy_side_effect(src, dst):
            # Only fail on config.schema.json
            if "config.schema.json" in str(dst):
                raise PermissionError("Cannot copy schema")
            # Otherwise do the real copy
            return shutil.copy2(src, dst)

        with patch.object(session_structure_module, "__file__", fake_file):
            with patch("shutil.copy", side_effect=mock_copy_side_effect):
                with pytest.raises(FileOperationError) as exc:
                    initialize_tracking_files("tier-1-essential", 80, tmp_path)

                assert "Failed to copy config schema" in exc.value.details
