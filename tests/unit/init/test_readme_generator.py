"""
Tests for readme_generator module.

Validates README.md generation with stack-specific information.

Run tests:
    pytest tests/unit/init/test_readme_generator.py -v

Run with coverage:
    pytest tests/unit/init/test_readme_generator.py --cov=sdd.init.readme_generator --cov-report=term-missing

Target: 90%+ coverage
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from sdd.core.exceptions import FileOperationError
from sdd.init.readme_generator import generate_readme


class TestGenerateReadme:
    """Tests for generate_readme()."""

    def test_generate_readme_for_saas_t3(self, tmp_path, mock_template_registry):
        """Test generating README for SaaS T3 template."""
        with patch("sdd.init.readme_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["saas_t3"]

            with patch(
                "sdd.init.readme_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                readme_path = generate_readme("saas_t3", "tier-2-standard", 80, ["ci_cd"], tmp_path)

                assert readme_path.exists()
                content = readme_path.read_text()
                assert "SaaS T3" in content
                assert "80%" in content
                assert "Next.js" in content

    def test_readme_includes_tech_stack(self, tmp_path, mock_template_registry):
        """Test that README includes complete tech stack."""
        with patch("sdd.init.readme_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["saas_t3"]

            with patch(
                "sdd.init.readme_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                readme_path = generate_readme("saas_t3", "tier-1-essential", 60, [], tmp_path)

                content = readme_path.read_text()
                assert "Next.js 16.0.1" in content
                assert "tRPC 11.0.0" in content
                assert "PostgreSQL 16.2" in content

    def test_readme_includes_npm_commands(self, tmp_path, mock_template_registry):
        """Test that README includes npm commands for Node.js stacks."""
        with patch("sdd.init.readme_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["saas_t3"]

            with patch(
                "sdd.init.readme_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                readme_path = generate_readme("saas_t3", "tier-1-essential", 60, [], tmp_path)

                content = readme_path.read_text()
                assert "npm install" in content
                assert "npm run dev" in content
                assert "npm test" in content

    def test_readme_includes_python_commands(self, tmp_path, mock_template_registry):
        """Test that README includes Python commands for Python stacks."""
        with patch("sdd.init.readme_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["ml_ai_fastapi"]

            with patch(
                "sdd.init.readme_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                readme_path = generate_readme("ml_ai_fastapi", "tier-1-essential", 60, [], tmp_path)

                content = readme_path.read_text()
                assert "source venv/bin/activate" in content
                assert "pytest" in content
                assert "uvicorn" in content

    def test_readme_includes_additional_options(self, tmp_path, mock_template_registry):
        """Test that README includes additional options."""
        with patch("sdd.init.readme_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["saas_t3"]

            with patch(
                "sdd.init.readme_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                readme_path = generate_readme(
                    "saas_t3", "tier-1-essential", 60, ["ci_cd", "docker"], tmp_path
                )

                content = readme_path.read_text()
                assert "Additional Features" in content
                assert "Ci Cd" in content or "CI/CD" in content.upper()
                assert "Docker" in content

    def test_readme_uses_project_name(self, tmp_path, mock_template_registry):
        """Test that README uses project directory name."""
        project = tmp_path / "my-awesome-project"
        project.mkdir()

        with patch("sdd.init.readme_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["saas_t3"]

            with patch(
                "sdd.init.readme_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                readme_path = generate_readme("saas_t3", "tier-1-essential", 60, [], project)

                content = readme_path.read_text()
                assert "my-awesome-project" in content

    def test_readme_includes_sdd_commands(self, tmp_path, mock_template_registry):
        """Test that README includes SDD workflow commands."""
        with patch("sdd.init.readme_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["saas_t3"]

            with patch(
                "sdd.init.readme_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                readme_path = generate_readme("saas_t3", "tier-1-essential", 60, [], tmp_path)

                content = readme_path.read_text()
                assert "/sdd:work-new" in content
                assert "/sdd:start" in content
                assert "/sdd:end" in content

    def test_error_handling_on_write_failure(self, tmp_path, mock_template_registry):
        """Test error handling when README write fails."""
        with patch("sdd.init.readme_generator.get_template_info") as mock_info:
            mock_info.return_value = mock_template_registry["templates"]["saas_t3"]

            with patch(
                "sdd.init.readme_generator.load_template_registry",
                return_value=mock_template_registry,
            ):
                with patch.object(Path, "write_text", side_effect=PermissionError("Access denied")):
                    with pytest.raises(FileOperationError) as exc:
                        generate_readme("saas_t3", "tier-1-essential", 60, [], tmp_path)

                    assert exc.value.operation == "write"
                    assert "README.md" in exc.value.file_path
