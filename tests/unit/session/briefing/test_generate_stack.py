"""Unit tests for generate_stack module.

This module tests the stack generation functionality which creates
a markdown file showing the current technology stack of a project.
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from solokit.core.exceptions import FileOperationError
from solokit.project.stack import StackGenerator


@pytest.fixture
def temp_project(tmp_path):
    """Provide a temporary project directory."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    return project_root


@pytest.fixture
def stack_generator(temp_project):
    """Provide a StackGenerator instance with temp directory."""
    return StackGenerator(project_root=temp_project)


class TestStackGeneratorInit:
    """Tests for StackGenerator initialization."""

    def test_init_with_default_path(self):
        """Test initialization with default path uses cwd."""
        # Act
        generator = StackGenerator()

        # Assert
        assert generator.project_root == Path.cwd()
        assert generator.stack_file.name == "stack.txt"
        assert generator.updates_file.name == "stack_updates.json"

    def test_init_with_custom_path(self, temp_project):
        """Test initialization with custom path."""
        # Act
        generator = StackGenerator(project_root=temp_project)

        # Assert
        assert generator.project_root == temp_project
        assert str(temp_project) in str(generator.stack_file)

    def test_init_creates_correct_file_paths(self, stack_generator, temp_project):
        """Test initialization creates correct file paths."""
        # Assert
        expected_stack = temp_project / ".session" / "tracking" / "stack.txt"
        expected_updates = temp_project / ".session" / "tracking" / "stack_updates.json"
        assert stack_generator.stack_file == expected_stack
        assert stack_generator.updates_file == expected_updates


class TestDetectLanguages:
    """Tests for language detection."""

    def test_detect_languages_python(self, stack_generator, temp_project):
        """Test detecting Python files."""
        # Arrange
        (temp_project / "main.py").touch()
        (temp_project / "utils.py").touch()

        # Act
        with patch.object(stack_generator, "_detect_language_version", return_value="3.9.0"):
            languages = stack_generator.detect_languages()

        # Assert
        assert "Python" in languages
        assert languages["Python"] == "3.9.0"

    def test_detect_languages_multiple(self, stack_generator, temp_project):
        """Test detecting multiple languages."""
        # Arrange
        (temp_project / "main.py").touch()
        (temp_project / "app.js").touch()
        (temp_project / "server.rs").touch()

        # Act
        with patch.object(stack_generator, "_detect_language_version", return_value=""):
            languages = stack_generator.detect_languages()

        # Assert
        assert "Python" in languages
        assert "JavaScript" in languages
        assert "Rust" in languages

    def test_detect_languages_excludes_venv(self, stack_generator, temp_project):
        """Test language detection excludes venv directories."""
        # Arrange
        venv_dir = temp_project / "venv" / "lib"
        venv_dir.mkdir(parents=True)
        (venv_dir / "script.py").touch()
        (temp_project / "main.py").touch()

        # Act
        with patch.object(stack_generator, "_detect_language_version", return_value=""):
            languages = stack_generator.detect_languages()

        # Assert
        assert "Python" in languages
        # Should detect main.py but not venv/lib/script.py

    def test_detect_languages_empty_project(self, stack_generator):
        """Test language detection on empty project."""
        # Act
        languages = stack_generator.detect_languages()

        # Assert
        assert languages == {}

    def test_detect_languages_no_version(self, stack_generator, temp_project):
        """Test language detection when version unavailable."""
        # Arrange
        (temp_project / "main.py").touch()

        # Act
        with patch.object(stack_generator, "_detect_language_version", return_value=""):
            languages = stack_generator.detect_languages()

        # Assert
        assert languages["Python"] == "detected"


class TestDetectLanguageVersion:
    """Tests for language version detection."""

    def test_detect_language_version_python_success(self, stack_generator):
        """Test successful Python version detection."""
        # Arrange
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Python 3.9.7"

        # Act
        with patch("subprocess.run", return_value=mock_result):
            version = stack_generator._detect_language_version("python")

        # Assert
        assert version == "3.9.7"

    def test_detect_language_version_no_match(self, stack_generator):
        """Test version detection with no version match."""
        # Arrange
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Some output without version"

        # Act
        with patch("subprocess.run", return_value=mock_result):
            version = stack_generator._detect_language_version("python")

        # Assert
        assert version == ""

    def test_detect_language_version_subprocess_error(self, stack_generator):
        """Test version detection handles subprocess errors."""
        # Act
        with patch("subprocess.run", side_effect=Exception("Command failed")):
            version = stack_generator._detect_language_version("python")

        # Assert
        assert version == ""

    def test_detect_language_version_unknown_language(self, stack_generator):
        """Test version detection for unknown language."""
        # Act
        version = stack_generator._detect_language_version("unknown")

        # Assert
        assert version == ""

    def test_detect_language_version_timeout(self, stack_generator):
        """Test version detection timeout is handled."""
        # Arrange
        import subprocess

        # Act
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 2)):
            version = stack_generator._detect_language_version("python")

        # Assert
        assert version == ""


class TestDetectFrameworks:
    """Tests for framework detection."""

    def test_detect_frameworks_python_backend(self, stack_generator, temp_project):
        """Test detecting Python backend frameworks."""
        # Arrange
        requirements = "fastapi==0.95.0\ndjango>=4.0.0\n"
        (temp_project / "requirements.txt").write_text(requirements)

        # Act
        frameworks = stack_generator.detect_frameworks()

        # Assert
        assert "backend" in frameworks
        assert any("FastAPI" in fw for fw in frameworks["backend"])
        assert any("Django" in fw for fw in frameworks["backend"])

    def test_detect_frameworks_python_testing(self, stack_generator, temp_project):
        """Test detecting Python testing frameworks."""
        # Arrange
        requirements = "pytest==7.0.0\n"
        (temp_project / "requirements.txt").write_text(requirements)

        # Act
        frameworks = stack_generator.detect_frameworks()

        # Assert
        assert "testing" in frameworks
        assert "pytest" in frameworks["testing"]

    def test_detect_frameworks_javascript_frontend(self, stack_generator, temp_project):
        """Test detecting JavaScript frontend frameworks."""
        # Arrange
        package_json = {
            "dependencies": {"react": "^18.0.0", "next": "^13.0.0"},
            "devDependencies": {"jest": "^29.0.0"},
        }
        (temp_project / "package.json").write_text(json.dumps(package_json))

        # Act
        frameworks = stack_generator.detect_frameworks()

        # Assert
        assert "frontend" in frameworks
        assert any("React" in fw for fw in frameworks["frontend"])
        assert any("Next.js" in fw for fw in frameworks["frontend"])
        assert "testing" in frameworks
        assert "Jest" in frameworks["testing"]

    def test_detect_frameworks_empty(self, stack_generator):
        """Test framework detection on project without dependencies."""
        # Act
        frameworks = stack_generator.detect_frameworks()

        # Assert
        assert frameworks == {}

    def test_detect_frameworks_invalid_json(self, stack_generator, temp_project):
        """Test framework detection handles invalid JSON gracefully."""
        # Arrange
        (temp_project / "package.json").write_text("invalid json {")

        # Act - should not raise exception due to safe_execute
        frameworks = stack_generator.detect_frameworks()

        # Assert - returns empty dict
        assert isinstance(frameworks, dict)

    def test_detect_frameworks_database(self, stack_generator, temp_project):
        """Test detecting database frameworks."""
        # Arrange
        requirements = "sqlalchemy==2.0.0\n"
        (temp_project / "requirements.txt").write_text(requirements)

        # Act
        frameworks = stack_generator.detect_frameworks()

        # Assert
        assert "database" in frameworks
        assert any("SQLAlchemy" in fw for fw in frameworks["database"])


class TestExtractVersion:
    """Tests for version extraction."""

    def test_extract_version_found_equals(self, stack_generator):
        """Test extracting version with equals operator."""
        # Arrange
        requirements = "fastapi==0.95.0\nother-package==1.0.0"

        # Act
        version = stack_generator._extract_version(requirements, "fastapi")

        # Assert
        assert version == "0.95.0"

    def test_extract_version_not_found(self, stack_generator):
        """Test extracting version for non-existent package."""
        # Arrange
        requirements = "fastapi==0.95.0"

        # Act
        version = stack_generator._extract_version(requirements, "django")

        # Assert
        assert version == ""

    def test_extract_version_different_operators(self, stack_generator):
        """Test extracting version with different operators."""
        # Arrange
        requirements_gte = "django>=4.0.0"
        requirements_tilde = "flask~=2.0.0"

        # Act
        version_gte = stack_generator._extract_version(requirements_gte, "django")
        version_tilde = stack_generator._extract_version(requirements_tilde, "flask")

        # Assert
        assert version_gte == "4.0.0"
        assert version_tilde == "2.0.0"


class TestDetectLibraries:
    """Tests for library detection."""

    def test_detect_libraries_from_requirements(self, stack_generator, temp_project):
        """Test detecting libraries from requirements.txt."""
        # Arrange
        requirements = "fastapi==0.95.0\nrequests>=2.28.0\npydantic~=1.10.0\n"
        (temp_project / "requirements.txt").write_text(requirements)

        # Act
        libraries = stack_generator.detect_libraries()

        # Assert
        assert len(libraries) == 3
        assert "fastapi==0.95.0" in libraries
        assert any("requests" in lib for lib in libraries)

    def test_detect_libraries_empty(self, stack_generator):
        """Test library detection with no requirements file."""
        # Act
        libraries = stack_generator.detect_libraries()

        # Assert
        assert libraries == []

    def test_detect_libraries_limits_to_20(self, stack_generator, temp_project):
        """Test library detection limits output to 20 items."""
        # Arrange
        requirements = "\n".join([f"package{i}==1.0.0" for i in range(30)])
        (temp_project / "requirements.txt").write_text(requirements)

        # Act
        libraries = stack_generator.detect_libraries()

        # Assert
        assert len(libraries) == 20

    def test_detect_libraries_ignores_comments(self, stack_generator, temp_project):
        """Test library detection ignores comments."""
        # Arrange
        requirements = "# This is a comment\nfastapi==0.95.0\n# Another comment\nrequests>=2.28.0\n"
        (temp_project / "requirements.txt").write_text(requirements)

        # Act
        libraries = stack_generator.detect_libraries()

        # Assert
        assert len(libraries) == 2
        assert all(not lib.startswith("#") for lib in libraries)


class TestDetectMCPServers:
    """Tests for MCP server detection."""

    def test_detect_mcp_servers_found(self, stack_generator, temp_project):
        """Test detecting MCP servers in code."""
        # Arrange
        py_file = temp_project / "main.py"
        py_file.write_text("import context7\nfrom mcp__context7 import get_docs")

        # Act
        mcp_servers = stack_generator.detect_mcp_servers()

        # Assert
        assert len(mcp_servers) == 1
        assert "Context7" in mcp_servers[0]

    def test_detect_mcp_servers_not_found(self, stack_generator, temp_project):
        """Test MCP server detection when none present."""
        # Arrange
        py_file = temp_project / "main.py"
        py_file.write_text("import requests\nfrom fastapi import FastAPI")

        # Act
        mcp_servers = stack_generator.detect_mcp_servers()

        # Assert
        assert mcp_servers == []

    def test_detect_mcp_servers_read_error(self, stack_generator, temp_project):
        """Test MCP server detection handles read errors gracefully."""
        # Arrange
        py_file = temp_project / "main.py"
        py_file.touch()

        # Act
        with patch.object(Path, "read_text", side_effect=Exception("Read error")):
            mcp_servers = stack_generator.detect_mcp_servers()

        # Assert - should not raise exception
        assert isinstance(mcp_servers, list)


class TestGenerateStackTxt:
    """Tests for stack.txt generation."""

    def test_generate_stack_txt_all_sections(self, stack_generator):
        """Test generating stack.txt with all sections."""
        # Arrange
        with patch.object(stack_generator, "detect_languages", return_value={"Python": "3.9.0"}):
            with patch.object(
                stack_generator,
                "detect_frameworks",
                return_value={"backend": ["FastAPI 0.95.0"], "testing": ["pytest"]},
            ):
                with patch.object(
                    stack_generator, "detect_libraries", return_value=["requests==2.28.0"]
                ):
                    with patch.object(
                        stack_generator,
                        "detect_mcp_servers",
                        return_value=["Context7 (library documentation)"],
                    ):
                        # Act
                        content = stack_generator.generate_stack_txt()

        # Assert
        assert "# Technology Stack" in content
        assert "## Languages" in content
        assert "Python 3.9.0" in content
        assert "## Backend Framework" in content
        assert "FastAPI 0.95.0" in content
        assert "## Testing" in content
        assert "pytest" in content
        assert "## Key Libraries" in content
        assert "requests==2.28.0" in content
        assert "## MCP Servers" in content
        assert "Context7" in content
        assert "Generated:" in content

    def test_generate_stack_txt_only_languages(self, stack_generator):
        """Test generating stack.txt with only languages."""
        # Arrange
        with patch.object(stack_generator, "detect_languages", return_value={"Python": "3.9.0"}):
            with patch.object(stack_generator, "detect_frameworks", return_value={}):
                with patch.object(stack_generator, "detect_libraries", return_value=[]):
                    with patch.object(stack_generator, "detect_mcp_servers", return_value=[]):
                        # Act
                        content = stack_generator.generate_stack_txt()

        # Assert
        assert "## Languages" in content
        assert "Python 3.9.0" in content
        assert "## Backend Framework" not in content
        assert "## Key Libraries" not in content

    def test_generate_stack_txt_empty(self, stack_generator):
        """Test generating stack.txt with no detections."""
        # Arrange
        with patch.object(stack_generator, "detect_languages", return_value={}):
            with patch.object(stack_generator, "detect_frameworks", return_value={}):
                with patch.object(stack_generator, "detect_libraries", return_value=[]):
                    with patch.object(stack_generator, "detect_mcp_servers", return_value=[]):
                        # Act
                        content = stack_generator.generate_stack_txt()

        # Assert
        assert "# Technology Stack" in content
        assert "Generated:" in content

    def test_generate_stack_txt_formats_correctly(self, stack_generator):
        """Test stack.txt is formatted correctly."""
        # Arrange
        with patch.object(stack_generator, "detect_languages", return_value={"Python": "3.9.0"}):
            with patch.object(stack_generator, "detect_frameworks", return_value={}):
                with patch.object(stack_generator, "detect_libraries", return_value=[]):
                    with patch.object(stack_generator, "detect_mcp_servers", return_value=[]):
                        # Act
                        content = stack_generator.generate_stack_txt()

        # Assert
        lines = content.split("\n")
        assert lines[0] == "# Technology Stack"
        assert any(line.startswith("- Python") for line in lines)

    def test_generate_stack_txt_includes_timestamp(self, stack_generator):
        """Test stack.txt includes timestamp."""
        # Arrange
        with patch.object(stack_generator, "detect_languages", return_value={}):
            with patch.object(stack_generator, "detect_frameworks", return_value={}):
                with patch.object(stack_generator, "detect_libraries", return_value=[]):
                    with patch.object(stack_generator, "detect_mcp_servers", return_value=[]):
                        # Act
                        content = stack_generator.generate_stack_txt()

        # Assert
        assert "Generated:" in content
        # Timestamp format should be YYYY-MM-DD HH:MM:SS
        import re

        assert re.search(r"Generated: \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", content)


class TestDetectChanges:
    """Tests for change detection."""

    def test_detect_changes_additions(self, stack_generator):
        """Test detecting additions."""
        # Arrange
        old_content = "# Stack\n- Python 3.9\n"
        new_content = "# Stack\n- Python 3.9\n- JavaScript ES6\n"

        # Act
        changes = stack_generator.detect_changes(old_content, new_content)

        # Assert
        additions = [c for c in changes if c["type"] == "addition"]
        assert len(additions) == 1
        assert "JavaScript" in additions[0]["content"]

    def test_detect_changes_removals(self, stack_generator):
        """Test detecting removals."""
        # Arrange
        old_content = "# Stack\n- Python 3.9\n- JavaScript ES6\n"
        new_content = "# Stack\n- Python 3.9\n"

        # Act
        changes = stack_generator.detect_changes(old_content, new_content)

        # Assert
        removals = [c for c in changes if c["type"] == "removal"]
        assert len(removals) == 1
        assert "JavaScript" in removals[0]["content"]

    def test_detect_changes_both(self, stack_generator):
        """Test detecting both additions and removals."""
        # Arrange
        old_content = "# Stack\n- Python 3.9\n- Go 1.18\n"
        new_content = "# Stack\n- Python 3.9\n- Rust 1.70\n"

        # Act
        changes = stack_generator.detect_changes(old_content, new_content)

        # Assert
        assert len(changes) >= 2
        types = [c["type"] for c in changes]
        assert "addition" in types
        assert "removal" in types

    def test_detect_changes_none(self, stack_generator):
        """Test no changes detected when content is identical."""
        # Arrange
        content = "# Stack\n- Python 3.9\n"

        # Act
        changes = stack_generator.detect_changes(content, content)

        # Assert
        assert len(changes) == 0

    def test_detect_changes_ignores_timestamps(self, stack_generator):
        """Test change detection ignores timestamp lines."""
        # Arrange
        old_content = "# Stack\n- Python 3.9\nGenerated: 2024-01-01 10:00:00"
        new_content = "# Stack\n- Python 3.9\nGenerated: 2024-01-02 11:00:00"

        # Act
        changes = stack_generator.detect_changes(old_content, new_content)

        # Assert
        assert len(changes) == 0


class TestUpdateStack:
    """Tests for stack update functionality."""

    def test_update_stack_no_changes(self, stack_generator, temp_project):
        """Test updating stack when no changes detected."""
        # Arrange
        stack_content = "# Stack\n- Python 3.9\n"
        stack_generator.stack_file.parent.mkdir(parents=True, exist_ok=True)
        stack_generator.stack_file.write_text(stack_content)

        # Act
        with patch.object(stack_generator, "generate_stack_txt", return_value=stack_content):
            changes = stack_generator.update_stack(session_num=1, non_interactive=True)

        # Assert
        assert len(changes) == 0

    def test_update_stack_with_changes_non_interactive(self, stack_generator, temp_project, capsys):
        """Test updating stack with changes in non-interactive mode."""
        # Arrange
        old_content = "# Stack\n- Python 3.9\n"
        new_content = "# Stack\n- Python 3.9\n- JavaScript ES6\n"
        stack_generator.stack_file.parent.mkdir(parents=True, exist_ok=True)
        stack_generator.stack_file.write_text(old_content)

        # Act
        with patch.object(stack_generator, "generate_stack_txt", return_value=new_content):
            with patch.object(stack_generator, "_record_stack_update"):
                changes = stack_generator.update_stack(session_num=1, non_interactive=True)

        # Assert
        assert len(changes) > 0
        captured = capsys.readouterr()
        assert "Stack Changes Detected" in captured.out
        assert "Non-interactive mode" in captured.out

    def test_update_stack_with_changes_interactive(self, stack_generator, temp_project):
        """Test updating stack with changes in interactive mode."""
        # Arrange
        old_content = "# Stack\n- Python 3.9\n"
        new_content = "# Stack\n- Python 3.9\n- JavaScript ES6\n"
        stack_generator.stack_file.parent.mkdir(parents=True, exist_ok=True)
        stack_generator.stack_file.write_text(old_content)

        # Act
        with patch.object(stack_generator, "generate_stack_txt", return_value=new_content):
            with patch("builtins.input", return_value="Added JavaScript support"):
                with patch.object(stack_generator, "_record_stack_update") as mock_record:
                    changes = stack_generator.update_stack(session_num=1, non_interactive=False)

        # Assert
        assert len(changes) > 0
        mock_record.assert_called_once()

    def test_update_stack_first_time(self, stack_generator, temp_project):
        """Test updating stack for the first time (no existing file)."""
        # Arrange
        new_content = "# Stack\n- Python 3.9\n"

        # Act
        with patch.object(stack_generator, "generate_stack_txt", return_value=new_content):
            _changes = stack_generator.update_stack(session_num=1, non_interactive=True)

        # Assert
        assert stack_generator.stack_file.exists()
        assert stack_generator.stack_file.read_text() == new_content

    def test_update_stack_creates_directory(self, stack_generator, temp_project):
        """Test updating stack creates parent directory if needed."""
        # Arrange
        new_content = "# Stack\n- Python 3.9\n"

        # Act
        with patch.object(stack_generator, "generate_stack_txt", return_value=new_content):
            stack_generator.update_stack(session_num=1, non_interactive=True)

        # Assert
        assert stack_generator.stack_file.parent.exists()

    def test_update_stack_no_session_num(self, stack_generator, temp_project):
        """Test updating stack without session number."""
        # Arrange
        old_content = "# Stack\n- Python 3.9\n"
        new_content = "# Stack\n- Python 3.9\n- JavaScript ES6\n"
        stack_generator.stack_file.parent.mkdir(parents=True, exist_ok=True)
        stack_generator.stack_file.write_text(old_content)

        # Act
        with patch.object(stack_generator, "generate_stack_txt", return_value=new_content):
            with patch.object(stack_generator, "_record_stack_update") as mock_record:
                changes = stack_generator.update_stack(session_num=None, non_interactive=True)

        # Assert
        assert len(changes) > 0
        mock_record.assert_not_called()


class TestRecordStackUpdate:
    """Tests for recording stack updates."""

    def test_record_stack_update_new_file(self, stack_generator, temp_project):
        """Test recording stack update to new file."""
        # Arrange
        stack_generator.updates_file.parent.mkdir(parents=True, exist_ok=True)
        session_num = 1
        changes = [{"type": "addition", "content": "- JavaScript ES6"}]
        reasoning = "Added JavaScript support"

        # Act
        with patch("solokit.project.stack.datetime") as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T10:00:00"
            stack_generator._record_stack_update(session_num, changes, reasoning)

        # Assert
        assert stack_generator.updates_file.exists()
        data = json.loads(stack_generator.updates_file.read_text())
        assert "updates" in data
        assert len(data["updates"]) == 1
        assert data["updates"][0]["session"] == 1
        assert data["updates"][0]["reasoning"] == reasoning

    def test_record_stack_update_append_to_existing(self, stack_generator, temp_project):
        """Test appending stack update to existing file."""
        # Arrange
        stack_generator.updates_file.parent.mkdir(parents=True, exist_ok=True)
        existing_data = {
            "updates": [
                {
                    "timestamp": "2024-01-01T09:00:00",
                    "session": 0,
                    "changes": [],
                    "reasoning": "Initial",
                }
            ]
        }
        stack_generator.updates_file.write_text(json.dumps(existing_data))
        session_num = 1
        changes = [{"type": "addition", "content": "- JavaScript ES6"}]
        reasoning = "Added JavaScript support"

        # Act
        with patch("solokit.project.stack.datetime") as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T10:00:00"
            stack_generator._record_stack_update(session_num, changes, reasoning)

        # Assert
        data = json.loads(stack_generator.updates_file.read_text())
        assert len(data["updates"]) == 2
        assert data["updates"][1]["session"] == 1

    def test_record_stack_update_invalid_existing(self, stack_generator, temp_project):
        """Test recording update when existing file is invalid JSON."""
        # Arrange
        stack_generator.updates_file.parent.mkdir(parents=True, exist_ok=True)
        stack_generator.updates_file.write_text("invalid json {")
        session_num = 1
        changes = [{"type": "addition", "content": "- JavaScript ES6"}]
        reasoning = "Added JavaScript support"

        # Act
        with patch("solokit.project.stack.datetime") as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T10:00:00"
            stack_generator._record_stack_update(session_num, changes, reasoning)

        # Assert
        data = json.loads(stack_generator.updates_file.read_text())
        assert len(data["updates"]) == 1


class TestErrorHandling:
    """Tests for error handling with standardized exceptions."""

    def test_detect_frameworks_requirements_read_error(self, stack_generator, temp_project):
        """Test framework detection raises FileOperationError on requirements.txt read failure."""
        # Arrange
        requirements_file = temp_project / "requirements.txt"
        requirements_file.touch()

        # Act & Assert
        with patch.object(Path, "read_text", side_effect=OSError("Permission denied")):
            with pytest.raises(FileOperationError) as exc_info:
                stack_generator.detect_frameworks()

            assert exc_info.value.context["operation"] == "read"
            assert "requirements.txt" in exc_info.value.context["file_path"]

    def test_detect_libraries_read_error(self, stack_generator, temp_project):
        """Test library detection raises FileOperationError on requirements.txt read failure."""
        # Arrange
        requirements_file = temp_project / "requirements.txt"
        requirements_file.touch()

        # Act & Assert
        with patch.object(Path, "read_text", side_effect=OSError("Permission denied")):
            with pytest.raises(FileOperationError) as exc_info:
                stack_generator.detect_libraries()

            assert exc_info.value.context["operation"] == "read"
            assert "requirements.txt" in exc_info.value.context["file_path"]

    def test_update_stack_read_error(self, stack_generator, temp_project):
        """Test update_stack raises FileOperationError on stack file read failure."""
        # Arrange
        stack_generator.stack_file.parent.mkdir(parents=True, exist_ok=True)
        stack_generator.stack_file.touch()

        # Mock generate_stack_txt to avoid dependencies
        with patch.object(stack_generator, "generate_stack_txt", return_value="# Stack\n"):
            # Mock read_text to raise OSError
            with patch.object(Path, "read_text", side_effect=OSError("Permission denied")):
                # Act & Assert
                with pytest.raises(FileOperationError) as exc_info:
                    stack_generator.update_stack(session_num=1, non_interactive=True)

                assert exc_info.value.context["operation"] == "read"

    def test_update_stack_write_error(self, stack_generator, temp_project):
        """Test update_stack raises FileOperationError on stack file write failure."""
        # Arrange
        with patch.object(stack_generator, "generate_stack_txt", return_value="# Stack\n"):
            # Mock write_text to raise OSError
            with patch.object(Path, "write_text", side_effect=OSError("Disk full")):
                # Act & Assert
                with pytest.raises(FileOperationError) as exc_info:
                    stack_generator.update_stack(session_num=1, non_interactive=True)

                assert exc_info.value.context["operation"] == "write"

    def test_record_stack_update_write_error(self, stack_generator, temp_project):
        """Test _record_stack_update raises FileOperationError on write failure."""
        # Arrange
        changes = [{"type": "addition", "content": "- Python 3.10"}]
        reasoning = "Added Python"

        # Mock write_text to raise OSError
        with patch.object(Path, "write_text", side_effect=OSError("Disk full")):
            # Act & Assert
            with pytest.raises(FileOperationError) as exc_info:
                stack_generator._record_stack_update(1, changes, reasoning)

            assert exc_info.value.context["operation"] == "write"
            assert "stack_updates.json" in exc_info.value.context["file_path"]


class TestMainFunction:
    """Tests for main CLI function."""

    def test_main_with_session(self, temp_project, capsys):
        """Test main function with session number."""
        # Arrange
        test_args = ["--session", "1", "--non-interactive"]

        # Act
        with patch("sys.argv", ["generate_stack.py"] + test_args):
            with patch("solokit.project.stack.StackGenerator") as mock_generator_class:
                mock_instance = Mock()
                mock_instance.update_stack.return_value = [{"type": "addition", "content": "test"}]
                mock_instance.stack_file = temp_project / "stack.txt"
                mock_generator_class.return_value = mock_instance

                from solokit.project.stack import main

                main()

        # Assert
        captured = capsys.readouterr()
        assert "Stack updated with 1 changes" in captured.out
        assert "Saved to:" in captured.out

    def test_main_non_interactive(self, temp_project, capsys):
        """Test main function in non-interactive mode."""
        # Arrange
        test_args = ["--non-interactive"]

        # Act
        with patch("sys.argv", ["generate_stack.py"] + test_args):
            with patch("solokit.project.stack.StackGenerator") as mock_generator_class:
                mock_instance = Mock()
                mock_instance.update_stack.return_value = []
                mock_instance.stack_file = temp_project / "stack.txt"
                mock_generator_class.return_value = mock_instance

                from solokit.project.stack import main

                main()

        # Assert
        captured = capsys.readouterr()
        assert "Stack generated (no changes)" in captured.out

    def test_main_no_changes(self, temp_project, capsys):
        """Test main function when no changes detected."""
        # Act
        with patch("sys.argv", ["generate_stack.py"]):
            with patch("solokit.project.stack.StackGenerator") as mock_generator_class:
                mock_instance = Mock()
                mock_instance.update_stack.return_value = []
                mock_instance.stack_file = temp_project / "stack.txt"
                mock_generator_class.return_value = mock_instance

                from solokit.project.stack import main

                main()

        # Assert
        captured = capsys.readouterr()
        assert "Stack generated (no changes)" in captured.out
        assert "Saved to:" in captured.out
