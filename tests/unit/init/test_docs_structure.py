"""
Tests for docs_structure module.

Validates documentation directory creation.

Run tests:
    pytest tests/unit/init/test_docs_structure.py -v

Target: 90%+ coverage
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from solokit.core.exceptions import FileOperationError
from solokit.init.docs_structure import create_docs_structure


class TestCreateDocsStructure:
    """Tests for create_docs_structure()."""

    def test_create_basic_structure(self, tmp_path):
        """Test creating basic docs structure."""
        dirs = create_docs_structure(tmp_path)

        assert len(dirs) >= 3
        assert (tmp_path / "docs" / "architecture").exists()
        assert (tmp_path / "docs" / "api").exists()
        assert (tmp_path / "docs" / "guides").exists()

    def test_creates_readme_files(self, tmp_path):
        """Test that placeholder README files are created."""
        create_docs_structure(tmp_path)

        assert (tmp_path / "docs" / "architecture" / "README.md").exists()
        assert (tmp_path / "docs" / "api" / "README.md").exists()

    def test_creates_guide_files(self, tmp_path):
        """Test that guide files are created."""
        create_docs_structure(tmp_path)

        assert (tmp_path / "docs" / "guides" / "development.md").exists()
        assert (tmp_path / "docs" / "guides" / "deployment.md").exists()

    def test_creates_security_file(self, tmp_path):
        """Test that SECURITY.md is created."""
        create_docs_structure(tmp_path)

        security = tmp_path / "docs" / "SECURITY.md"
        assert security.exists()
        content = security.read_text()
        assert "Security Policy" in content

    def test_error_handling(self, tmp_path):
        """Test error handling when directory creation fails."""
        with patch.object(Path, "mkdir", side_effect=PermissionError("Access denied")):
            with pytest.raises(FileOperationError) as exc:
                create_docs_structure(tmp_path)

            assert exc.value.operation == "create"
