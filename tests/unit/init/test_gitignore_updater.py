"""
Tests for gitignore_updater module.

Validates .gitignore updating with stack-specific patterns.

Run tests:
    pytest tests/unit/init/test_gitignore_updater.py -v

Target: 90%+ coverage
"""

from sdd.init.gitignore_updater import (
    get_os_specific_gitignore_entries,
    get_stack_specific_gitignore_entries,
    update_gitignore,
)


class TestGetStackSpecificGitignoreEntries:
    """Tests for get_stack_specific_gitignore_entries()."""

    def test_saas_t3_entries(self):
        """Test entries for SaaS T3 stack."""
        entries = get_stack_specific_gitignore_entries("saas_t3")

        assert "node_modules/" in entries
        assert ".next/" in entries
        assert ".env" in entries

    def test_ml_ai_fastapi_entries(self):
        """Test entries for ML/AI FastAPI stack."""
        entries = get_stack_specific_gitignore_entries("ml_ai_fastapi")

        assert "venv/" in entries
        assert "*.pyc" in entries
        assert "__pycache__/" in entries

    def test_common_entries_in_all(self):
        """Test that common entries appear in all stacks."""
        for template_id in ["saas_t3", "ml_ai_fastapi"]:
            entries = get_stack_specific_gitignore_entries(template_id)

            assert ".session/briefings/" in entries
            assert "coverage/" in entries

    def test_unknown_template(self):
        """Test that unknown template returns common entries only."""
        entries = get_stack_specific_gitignore_entries("unknown")

        assert ".session/briefings/" in entries
        assert len(entries) >= 1


class TestGetOsSpecificGitignoreEntries:
    """Tests for get_os_specific_gitignore_entries()."""

    def test_contains_macos_entries(self):
        """Test that macOS entries are included."""
        entries = get_os_specific_gitignore_entries()

        entries_str = "\n".join(entries)
        assert ".DS_Store" in entries_str
        assert "._*" in entries_str

    def test_contains_windows_entries(self):
        """Test that Windows entries are included."""
        entries = get_os_specific_gitignore_entries()

        entries_str = "\n".join(entries)
        assert "Thumbs.db" in entries_str
        assert "Desktop.ini" in entries_str

    def test_contains_linux_entries(self):
        """Test that Linux entries are included."""
        entries = get_os_specific_gitignore_entries()

        entries_str = "\n".join(entries)
        assert "*~" in entries_str


class TestUpdateGitignore:
    """Tests for update_gitignore()."""

    def test_create_new_gitignore(self, tmp_path):
        """Test creating new .gitignore file."""
        gitignore = update_gitignore("saas_t3", tmp_path)

        assert gitignore.exists()
        content = gitignore.read_text()
        assert "node_modules/" in content
        assert ".session/briefings/" in content

    def test_append_to_existing_gitignore(self, tmp_path):
        """Test appending to existing .gitignore."""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("# Existing content\n*.log\n")

        update_gitignore("saas_t3", tmp_path)

        content = gitignore.read_text()
        assert "*.log" in content
        assert "node_modules/" in content

    def test_skip_duplicate_entries(self, tmp_path):
        """Test that duplicate entries are not added."""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("node_modules/\n.next/\n")

        update_gitignore("saas_t3", tmp_path)

        content = gitignore.read_text()
        # Count occurrences - should be 1 each
        assert content.count("node_modules/") == 1
        assert content.count(".next/") == 1

    def test_add_os_specific_entries(self, tmp_path):
        """Test adding OS-specific entries."""
        gitignore = update_gitignore("saas_t3", tmp_path)

        content = gitignore.read_text()
        assert ".DS_Store" in content
        assert "Thumbs.db" in content

    def test_skip_os_entries_if_exist(self, tmp_path):
        """Test skipping OS entries if they already exist."""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text(".DS_Store\nThumbs.db\n")

        update_gitignore("saas_t3", tmp_path)

        content = gitignore.read_text()
        assert content.count(".DS_Store") == 1
        assert content.count("Thumbs.db") == 1
