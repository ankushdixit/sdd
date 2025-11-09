"""
Tests for env_generator module.

Validates .env.example and .editorconfig generation.

Run tests:
    pytest tests/unit/init/test_env_generator.py -v

Target: 90%+ coverage
"""
import pytest
from pathlib import Path
from unittest.mock import patch

from sdd.init.env_generator import (
    generate_editorconfig,
    generate_env_example_nextjs,
    generate_env_example_python,
    generate_env_files,
)
from sdd.core.exceptions import FileOperationError


class TestGenerateEditorconfig:
    """Tests for generate_editorconfig()."""

    def test_generate_editorconfig(self, tmp_path):
        """Test generating .editorconfig."""
        path = generate_editorconfig(tmp_path)

        assert path.exists()
        content = path.read_text()
        assert "indent_style = space" in content
        assert "indent_size = 2" in content

    def test_python_specific_config(self, tmp_path):
        """Test that Python files have indent_size = 4."""
        path = generate_editorconfig(tmp_path)

        content = path.read_text()
        assert "[*.py]" in content
        assert "indent_size = 4" in content.split("[*.py]")[1].split("[")[0]


class TestGenerateEnvExampleNextjs:
    """Tests for generate_env_example_nextjs()."""

    def test_generate_nextjs_env(self, tmp_path):
        """Test generating .env.example for Next.js."""
        path = generate_env_example_nextjs(tmp_path)

        assert path.exists()
        content = path.read_text()
        assert "DATABASE_URL" in content
        assert "NEXTAUTH_SECRET" in content


class TestGenerateEnvExamplePython:
    """Tests for generate_env_example_python()."""

    def test_generate_python_env(self, tmp_path):
        """Test generating .env.example for Python."""
        path = generate_env_example_python(tmp_path)

        assert path.exists()
        content = path.read_text()
        assert "DATABASE_URL" in content
        assert "API_HOST" in content
        assert "SECRET_KEY" in content


class TestGenerateEnvFiles:
    """Tests for generate_env_files()."""

    def test_generate_for_nodejs_template(self, tmp_path):
        """Test generating env files for Node.js template."""
        files = generate_env_files("saas_t3", tmp_path)

        assert len(files) == 2
        assert (tmp_path / ".editorconfig").exists()
        assert (tmp_path / ".env.example").exists()

    def test_generate_for_python_template(self, tmp_path):
        """Test generating env files for Python template."""
        files = generate_env_files("ml_ai_fastapi", tmp_path)

        assert len(files) == 2
        assert (tmp_path / ".editorconfig").exists()
        assert (tmp_path / ".env.example").exists()
