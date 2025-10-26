"""Unit tests for init_project module.

This module tests the project initialization functionality which creates
the SDD project structure, tracking files, and git repository.
"""

import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from sdd.project.init import (
    check_or_init_git,
    create_initial_commit,
    create_session_structure,
    create_smoke_tests,
    detect_project_type,
    ensure_config_files,
    ensure_gitignore_entries,
    ensure_package_manager_file,
    init_project,
    initialize_tracking_files,
    install_dependencies,
    install_git_hooks,
    run_initial_scans,
)


@pytest.fixture
def temp_project(tmp_path):
    """Provide a temporary project directory."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    return project_root


@pytest.fixture
def mock_template_dir(tmp_path):
    """Create a mock template directory with sample files."""
    template_dir = tmp_path / "templates"
    template_dir.mkdir()

    # Create git-hooks directory
    git_hooks_dir = template_dir / "git-hooks"
    git_hooks_dir.mkdir()
    (git_hooks_dir / "prepare-commit-msg").write_text("#!/bin/bash\necho 'hook'")

    # Create test templates
    tests_dir = template_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "sdd-setup.test.ts").write_text("test('setup', () => {});")
    (tests_dir / "sdd-setup.test.js").write_text("test('setup', () => {});")
    (tests_dir / "test_sdd_setup.py").write_text("def test_setup(): pass")

    # Create config templates
    (template_dir / "package.json.template").write_text('{"name": "{project_name}"}')
    (template_dir / "pyproject.toml.template").write_text('[project]\nname = "{project_name}"')
    (template_dir / "CHANGELOG.md").write_text("# Changelog\n")
    (template_dir / ".eslintrc.json").write_text('{"rules": {}}')
    (template_dir / ".prettierrc.json").write_text('{"semi": true}')
    (template_dir / ".prettierignore").write_text("node_modules/")
    (template_dir / "jest.config.js").write_text("module.exports = {};")
    (template_dir / "jest.config.js.javascript").write_text("module.exports = {};")
    (template_dir / "tsconfig.json").write_text('{"compilerOptions": {}}')
    (template_dir / "config.schema.json").write_text('{"type": "object"}')

    # Create tracking file templates
    (template_dir / "work_items.json").write_text('{"work_items": []}')
    (template_dir / "learnings.json").write_text('{"learnings": []}')
    (template_dir / "status_update.json").write_text('{"status": "ready"}')

    return template_dir


class TestCheckOrInitGit:
    """Tests for check_or_init_git function."""

    def test_git_already_initialized(self, temp_project, capsys):
        """Test when git is already initialized."""
        # Arrange
        git_dir = temp_project / ".git"
        git_dir.mkdir()

        # Act
        result = check_or_init_git(temp_project)
        captured = capsys.readouterr()

        # Assert
        assert result is True
        assert "Git repository already initialized" in captured.out

    @patch("subprocess.run")
    def test_git_initialization_success(self, mock_run, temp_project, capsys):
        """Test successful git initialization."""
        # Arrange
        mock_run.return_value = Mock(returncode=0)

        # Act
        result = check_or_init_git(temp_project)
        captured = capsys.readouterr()

        # Assert
        assert result is True
        assert "Initialized git repository" in captured.out
        assert "Set default branch to 'main'" in captured.out
        assert mock_run.call_count == 2

        # Verify git init was called
        init_call = mock_run.call_args_list[0]
        assert init_call[0][0] == ["git", "init"]
        assert init_call[1]["cwd"] == temp_project

        # Verify git branch was called
        branch_call = mock_run.call_args_list[1]
        assert branch_call[0][0] == ["git", "branch", "-m", "main"]

    @patch("subprocess.run")
    def test_git_initialization_failure(self, mock_run, temp_project, capsys):
        """Test git initialization failure."""
        # Arrange
        mock_run.side_effect = subprocess.CalledProcessError(1, "git init")

        # Act
        result = check_or_init_git(temp_project)
        captured = capsys.readouterr()

        # Assert
        assert result is False
        assert "Failed to initialize git" in captured.out

    def test_git_init_default_path(self, capsys):
        """Test git initialization with default path (cwd)."""
        # Arrange
        git_dir = Path.cwd() / ".git"
        already_exists = git_dir.exists()

        # Act
        result = check_or_init_git()
        captured = capsys.readouterr()

        # Assert
        if already_exists:
            assert result is True
            assert "Git repository already initialized" in captured.out
        else:
            # Can't test initialization without mocking since it would modify real repo
            pass


class TestInstallGitHooks:
    """Tests for install_git_hooks function."""

    def test_git_hooks_dir_not_found(self, temp_project, capsys):
        """Test when .git/hooks directory doesn't exist."""
        # Act
        result = install_git_hooks(temp_project)
        captured = capsys.readouterr()

        # Assert
        assert result is False
        assert ".git/hooks directory not found" in captured.out

    @patch("shutil.copy")
    def test_install_hooks_copy_failure(self, mock_copy, temp_project, mock_template_dir, capsys):
        """Test hook installation when copy fails."""
        # Arrange
        git_hooks_dir = temp_project / ".git" / "hooks"
        git_hooks_dir.mkdir(parents=True)
        mock_copy.side_effect = OSError("Permission denied")

        # Mock the template path to exist
        with patch.object(Path, "exists", return_value=True):
            with patch("sdd.project.init.Path") as mock_path:
                # Setup mock to return our template dir
                mock_file = Mock()
                mock_file.parent.parent = mock_template_dir.parent
                mock_path.return_value = mock_file

                # Act
                result = install_git_hooks(temp_project)
                captured = capsys.readouterr()

        # Assert
        assert result is False
        assert "Failed to install git hook" in captured.out


class TestDetectProjectType:
    """Tests for detect_project_type function."""

    def test_detect_typescript_project(self, temp_project, monkeypatch):
        """Test detecting TypeScript project."""
        # Arrange
        monkeypatch.chdir(temp_project)
        (temp_project / "package.json").write_text("{}")
        (temp_project / "tsconfig.json").write_text("{}")

        # Act
        result = detect_project_type()

        # Assert
        assert result == "typescript"

    def test_detect_javascript_project(self, temp_project, monkeypatch):
        """Test detecting JavaScript project."""
        # Arrange
        monkeypatch.chdir(temp_project)
        (temp_project / "package.json").write_text("{}")

        # Act
        result = detect_project_type()

        # Assert
        assert result == "javascript"

    def test_detect_python_project_pyproject(self, temp_project, monkeypatch):
        """Test detecting Python project with pyproject.toml."""
        # Arrange
        monkeypatch.chdir(temp_project)
        (temp_project / "pyproject.toml").write_text("")

        # Act
        result = detect_project_type()

        # Assert
        assert result == "python"

    def test_detect_python_project_setup_py(self, temp_project, monkeypatch):
        """Test detecting Python project with setup.py."""
        # Arrange
        monkeypatch.chdir(temp_project)
        (temp_project / "setup.py").write_text("")

        # Act
        result = detect_project_type()

        # Assert
        assert result == "python"

    @patch("builtins.input", return_value="1")
    @patch("sys.stdin.isatty", return_value=True)
    def test_detect_unknown_project_user_choice_typescript(
        self, mock_isatty, mock_input, temp_project, monkeypatch, capsys
    ):
        """Test detecting unknown project with user choosing TypeScript."""
        # Arrange
        monkeypatch.chdir(temp_project)

        # Act
        result = detect_project_type()
        captured = capsys.readouterr()

        # Assert
        assert result == "typescript"
        assert "No project files detected" in captured.out

    @patch("builtins.input", return_value="2")
    @patch("sys.stdin.isatty", return_value=True)
    def test_detect_unknown_project_user_choice_javascript(
        self, mock_isatty, mock_input, temp_project, monkeypatch
    ):
        """Test detecting unknown project with user choosing JavaScript."""
        # Arrange
        monkeypatch.chdir(temp_project)

        # Act
        result = detect_project_type()

        # Assert
        assert result == "javascript"

    @patch("builtins.input", return_value="3")
    @patch("sys.stdin.isatty", return_value=True)
    def test_detect_unknown_project_user_choice_python(
        self, mock_isatty, mock_input, temp_project, monkeypatch
    ):
        """Test detecting unknown project with user choosing Python."""
        # Arrange
        monkeypatch.chdir(temp_project)

        # Act
        result = detect_project_type()

        # Assert
        assert result == "python"

    @patch("builtins.input", return_value="invalid")
    @patch("sys.stdin.isatty", return_value=True)
    def test_detect_unknown_project_invalid_choice(
        self, mock_isatty, mock_input, temp_project, monkeypatch
    ):
        """Test detecting unknown project with invalid choice defaults to TypeScript."""
        # Arrange
        monkeypatch.chdir(temp_project)

        # Act
        result = detect_project_type()

        # Assert
        assert result == "typescript"

    @patch("sys.stdin.isatty", return_value=False)
    def test_detect_unknown_project_non_interactive(
        self, mock_isatty, temp_project, monkeypatch, capsys
    ):
        """Test detecting unknown project in non-interactive mode."""
        # Arrange
        monkeypatch.chdir(temp_project)

        # Act
        result = detect_project_type()
        captured = capsys.readouterr()

        # Assert
        assert result == "typescript"
        assert "Non-interactive mode: defaulting to TypeScript" in captured.out


class TestEnsurePackageManagerFile:
    """Tests for ensure_package_manager_file function."""

    def test_update_existing_package_json_add_scripts(self, temp_project, monkeypatch, capsys):
        """Test updating existing package.json to add missing scripts."""
        # Arrange
        monkeypatch.chdir(temp_project)
        package_json = temp_project / "package.json"
        package_json.write_text('{"name": "test", "scripts": {}}')

        # Act
        ensure_package_manager_file("typescript")
        captured = capsys.readouterr()

        # Assert
        assert "Found package.json" in captured.out
        assert "Added script: test" in captured.out

        data = json.loads(package_json.read_text())
        assert "test" in data["scripts"]
        assert "lint" in data["scripts"]
        assert "format" in data["scripts"]
        assert "build" in data["scripts"]  # TypeScript should have build

    def test_update_existing_package_json_add_dev_dependencies(
        self, temp_project, monkeypatch, capsys
    ):
        """Test updating existing package.json to add missing devDependencies."""
        # Arrange
        monkeypatch.chdir(temp_project)
        package_json = temp_project / "package.json"
        package_json.write_text(
            '{"name": "test", "scripts": {"test": "jest"}, "devDependencies": {}}'
        )

        # Act
        ensure_package_manager_file("typescript")
        captured = capsys.readouterr()

        # Assert
        assert "Added devDependency: jest" in captured.out

        data = json.loads(package_json.read_text())
        assert "jest" in data["devDependencies"]
        assert "typescript" in data["devDependencies"]
        assert "@types/jest" in data["devDependencies"]

    def test_package_json_no_modification_needed(self, temp_project, monkeypatch, capsys):
        """Test when package.json already has all required fields."""
        # Arrange
        monkeypatch.chdir(temp_project)
        package_json = temp_project / "package.json"
        complete_data = {
            "name": "test",
            "scripts": {"test": "jest", "lint": "eslint .", "format": "prettier .", "build": "tsc"},
            "devDependencies": {
                "jest": "^29.5.0",
                "prettier": "^3.0.0",
                "eslint": "^8.40.0",
                "@types/jest": "^29.5.0",
                "@types/node": "^20.0.0",
                "@typescript-eslint/eslint-plugin": "^6.0.0",
                "@typescript-eslint/parser": "^6.0.0",
                "ts-jest": "^29.1.0",
                "typescript": "^5.0.0",
            },
        }
        package_json.write_text(json.dumps(complete_data))

        # Act
        ensure_package_manager_file("typescript")
        captured = capsys.readouterr()

        # Assert
        assert "Found package.json" in captured.out
        assert "Added script:" not in captured.out
        assert "Added devDependency:" not in captured.out

    def test_existing_pyproject_toml_with_dev_deps(self, temp_project, monkeypatch, capsys):
        """Test when pyproject.toml exists with dev dependencies."""
        # Arrange
        monkeypatch.chdir(temp_project)
        pyproject = temp_project / "pyproject.toml"
        pyproject.write_text('[project.optional-dependencies]\ndev = ["pytest"]')

        # Act
        ensure_package_manager_file("python")
        captured = capsys.readouterr()

        # Assert
        assert "Found pyproject.toml" in captured.out
        assert "Add [project.optional-dependencies]" not in captured.out

    def test_existing_pyproject_toml_without_dev_deps(self, temp_project, monkeypatch, capsys):
        """Test when pyproject.toml exists without dev dependencies."""
        # Arrange
        monkeypatch.chdir(temp_project)
        pyproject = temp_project / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test"')

        # Act
        ensure_package_manager_file("python")
        captured = capsys.readouterr()

        # Assert
        assert "Found pyproject.toml" in captured.out
        assert "Add [project.optional-dependencies]" in captured.out


class TestEnsureConfigFiles:
    """Tests for ensure_config_files function."""

    def test_existing_config_files_not_overwritten(self, temp_project, monkeypatch, capsys):
        """Test that existing config files are not overwritten."""
        # Arrange
        monkeypatch.chdir(temp_project)
        existing_changelog = temp_project / "CHANGELOG.md"
        existing_changelog.write_text("# My Custom Changelog")

        # Act
        ensure_config_files("typescript")
        captured = capsys.readouterr()

        # Assert
        assert "Found CHANGELOG.md" in captured.out
        assert "Created CHANGELOG.md" not in captured.out
        assert existing_changelog.read_text() == "# My Custom Changelog"


class TestInstallDependencies:
    """Tests for install_dependencies function."""

    @patch("subprocess.run")
    def test_install_npm_dependencies_success(self, mock_run, temp_project, monkeypatch, capsys):
        """Test successful npm dependency installation."""
        # Arrange
        monkeypatch.chdir(temp_project)
        mock_run.return_value = Mock(returncode=0)

        # Act
        install_dependencies("typescript")
        captured = capsys.readouterr()

        # Assert
        assert "Installing npm dependencies" in captured.out
        assert "Dependencies installed" in captured.out
        mock_run.assert_called_once_with(["npm", "install"], check=True)

    @patch("subprocess.run")
    def test_install_npm_dependencies_failure(self, mock_run, temp_project, monkeypatch, capsys):
        """Test npm dependency installation failure."""
        # Arrange
        monkeypatch.chdir(temp_project)
        mock_run.side_effect = subprocess.CalledProcessError(1, "npm install")

        # Act
        install_dependencies("javascript")
        captured = capsys.readouterr()

        # Assert
        assert "npm install failed" in captured.out

    @patch("subprocess.run")
    def test_install_python_dependencies_create_venv(
        self, mock_run, temp_project, monkeypatch, capsys
    ):
        """Test creating Python venv and installing dependencies."""
        # Arrange
        monkeypatch.chdir(temp_project)
        venv_dir = temp_project / "venv"
        pip_path = venv_dir / "bin" / "pip"

        def run_side_effect(cmd, **kwargs):
            if "venv" in cmd:
                # Simulate venv creation
                venv_dir.mkdir()
                pip_path.parent.mkdir(parents=True)
                pip_path.write_text("#!/usr/bin/env python")
                return Mock(returncode=0)
            return Mock(returncode=0)

        mock_run.side_effect = run_side_effect

        # Act
        install_dependencies("python")
        captured = capsys.readouterr()

        # Assert
        assert "Creating Python virtual environment" in captured.out
        assert "Created venv/" in captured.out
        assert "Installing Python dependencies" in captured.out

    @patch("subprocess.run")
    def test_install_python_dependencies_venv_exists(
        self, mock_run, temp_project, monkeypatch, capsys
    ):
        """Test installing Python dependencies when venv already exists."""
        # Arrange
        monkeypatch.chdir(temp_project)
        venv_dir = temp_project / "venv"
        venv_dir.mkdir()
        pip_path = venv_dir / "bin" / "pip"
        pip_path.parent.mkdir(parents=True)
        pip_path.write_text("#!/usr/bin/env python")
        mock_run.return_value = Mock(returncode=0)

        # Act
        install_dependencies("python")
        captured = capsys.readouterr()

        # Assert
        assert "Installing Python dependencies" in captured.out
        assert "Creating Python virtual environment" not in captured.out

    @patch("subprocess.run")
    def test_install_python_dependencies_venv_creation_failure(
        self, mock_run, temp_project, monkeypatch, capsys
    ):
        """Test Python venv creation failure."""
        # Arrange
        monkeypatch.chdir(temp_project)
        mock_run.side_effect = subprocess.CalledProcessError(1, "venv")

        # Act
        install_dependencies("python")
        captured = capsys.readouterr()

        # Assert
        assert "venv creation failed" in captured.out


class TestCreateSmokeTests:
    """Tests for create_smoke_tests function."""

    def test_existing_smoke_test_not_overwritten(self, temp_project, monkeypatch, capsys):
        """Test that existing smoke test is not overwritten."""
        # Arrange
        monkeypatch.chdir(temp_project)
        test_dir = temp_project / "tests"
        test_dir.mkdir()
        test_file = test_dir / "sdd-setup.test.ts"
        test_file.write_text("// My custom test")

        # Act
        create_smoke_tests("typescript")
        captured = capsys.readouterr()

        # Assert
        assert "Found" in captured.out
        assert test_file.read_text() == "// My custom test"


class TestCreateSessionStructure:
    """Tests for create_session_structure function."""

    def test_create_session_directories(self, temp_project, monkeypatch, capsys):
        """Test creating .session directory structure."""
        # Arrange
        monkeypatch.chdir(temp_project)

        # Act
        create_session_structure()
        captured = capsys.readouterr()

        # Assert
        assert (temp_project / ".session" / "tracking").exists()
        assert (temp_project / ".session" / "briefings").exists()
        assert (temp_project / ".session" / "history").exists()
        assert (temp_project / ".session" / "specs").exists()
        assert "Created .session/tracking/" in captured.out
        assert "Created .session/briefings/" in captured.out
        assert "Created .session/history/" in captured.out
        assert "Created .session/specs/" in captured.out


class TestInitializeTrackingFiles:
    """Tests for initialize_tracking_files function."""

    def test_initialize_config_json_structure(self, temp_project, monkeypatch):
        """Test config.json has correct structure."""
        # Arrange
        monkeypatch.chdir(temp_project)
        session_dir = temp_project / ".session"
        (session_dir / "tracking").mkdir(parents=True)

        # Act
        initialize_tracking_files()

        # Assert
        config_file = session_dir / "config.json"
        config = json.loads(config_file.read_text())
        assert "curation" in config
        assert "quality_gates" in config
        assert "integration_tests" in config
        assert "git_workflow" in config
        assert config["curation"]["auto_curate"] is True
        assert config["quality_gates"]["test_execution"]["coverage_threshold"] == 80

    def test_initialize_stack_updates_json(self, temp_project, monkeypatch):
        """Test stack_updates.json is created with correct structure."""
        # Arrange
        monkeypatch.chdir(temp_project)
        session_dir = temp_project / ".session"
        (session_dir / "tracking").mkdir(parents=True)

        # Act
        initialize_tracking_files()

        # Assert
        stack_file = session_dir / "tracking" / "stack_updates.json"
        stack_data = json.loads(stack_file.read_text())
        assert "updates" in stack_data
        assert isinstance(stack_data["updates"], list)


class TestRunInitialScans:
    """Tests for run_initial_scans function."""

    @patch("subprocess.run")
    def test_run_initial_scans_success(self, mock_run, temp_project, monkeypatch, capsys):
        """Test successful initial scans."""
        # Arrange
        monkeypatch.chdir(temp_project)
        mock_run.return_value = Mock(returncode=0, stderr="")

        # Act
        run_initial_scans()
        captured = capsys.readouterr()

        # Assert
        assert "Generated stack.txt" in captured.out
        assert "Generated tree.txt" in captured.out
        assert mock_run.call_count == 2

    @patch("subprocess.run")
    def test_run_initial_scans_stack_failure(self, mock_run, temp_project, monkeypatch, capsys):
        """Test when stack generation fails."""
        # Arrange
        monkeypatch.chdir(temp_project)
        mock_run.side_effect = [
            subprocess.CalledProcessError(1, "generate_stack.py", stderr="Error"),
            Mock(returncode=0),
        ]

        # Act
        run_initial_scans()
        captured = capsys.readouterr()

        # Assert
        assert "Could not generate stack.txt" in captured.out

    @patch("subprocess.run")
    def test_run_initial_scans_timeout(self, mock_run, temp_project, monkeypatch, capsys):
        """Test when scans timeout."""
        # Arrange
        monkeypatch.chdir(temp_project)
        mock_run.side_effect = subprocess.TimeoutExpired("generate_stack.py", 30)

        # Act
        run_initial_scans()
        captured = capsys.readouterr()

        # Assert
        assert "Stack generation timed out" in captured.out


class TestEnsureGitignoreEntries:
    """Tests for ensure_gitignore_entries function."""

    def test_create_gitignore_from_scratch(self, temp_project, monkeypatch, capsys):
        """Test creating .gitignore from scratch."""
        # Arrange
        monkeypatch.chdir(temp_project)

        # Act
        ensure_gitignore_entries()
        captured = capsys.readouterr()

        # Assert
        gitignore = temp_project / ".gitignore"
        assert gitignore.exists()
        content = gitignore.read_text()
        assert ".session/briefings/" in content
        assert "coverage/" in content
        assert ".DS_Store" in content
        assert "Thumbs.db" in content
        assert "*~" in content
        assert "Added" in captured.out and "entries to .gitignore" in captured.out

    def test_update_existing_gitignore(self, temp_project, monkeypatch, capsys):
        """Test updating existing .gitignore."""
        # Arrange
        monkeypatch.chdir(temp_project)
        gitignore = temp_project / ".gitignore"
        gitignore.write_text("node_modules/\n")

        # Act
        ensure_gitignore_entries()
        captured = capsys.readouterr()

        # Assert
        content = gitignore.read_text()
        assert "node_modules/" in content
        assert ".session/briefings/" in content
        assert "Added" in captured.out

    def test_gitignore_already_complete(self, temp_project, monkeypatch, capsys):
        """Test when .gitignore already has all entries."""
        # Arrange
        monkeypatch.chdir(temp_project)
        gitignore = temp_project / ".gitignore"
        complete_content = """
.session/briefings/
.session/history/
coverage/
coverage.json
node_modules/
dist/
venv/
.venv/
*.pyc
__pycache__/
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
Thumbs.db
ehthumbs.db
Desktop.ini
$RECYCLE.BIN/
*~
"""
        gitignore.write_text(complete_content)

        # Act
        ensure_gitignore_entries()
        captured = capsys.readouterr()

        # Assert
        assert ".gitignore already up to date" in captured.out

    def test_gitignore_os_patterns_section(self, temp_project, monkeypatch, capsys):
        """Test OS-specific patterns section is added."""
        # Arrange
        monkeypatch.chdir(temp_project)

        # Act
        ensure_gitignore_entries()

        # Assert
        gitignore = temp_project / ".gitignore"
        content = gitignore.read_text()
        assert "# OS-specific files" in content
        assert ".DS_Store" in content and "# macOS" in content
        assert "Thumbs.db" in content and "# Windows" in content
        assert "*~" in content and "# Linux backup files" in content


class TestCreateInitialCommit:
    """Tests for create_initial_commit function."""

    @patch("subprocess.run")
    def test_create_initial_commit_success(self, mock_run, temp_project, capsys):
        """Test successful initial commit creation."""
        # Arrange
        # First call checks for existing commits (no commits)
        # Second call stages files
        # Third call creates commit
        mock_run.side_effect = [
            subprocess.CalledProcessError(128, "git rev-list"),  # No commits yet
            Mock(returncode=0),  # git add
            Mock(returncode=0),  # git commit
        ]

        # Act
        result = create_initial_commit(temp_project)
        captured = capsys.readouterr()

        # Assert
        assert result is True
        assert "Created initial commit" in captured.out
        assert mock_run.call_count == 3

    @patch("subprocess.run")
    def test_create_initial_commit_already_has_commits(self, mock_run, temp_project, capsys):
        """Test when repository already has commits."""
        # Arrange
        mock_run.return_value = Mock(returncode=0, stdout="5\n")

        # Act
        result = create_initial_commit(temp_project)
        captured = capsys.readouterr()

        # Assert
        assert result is True
        assert "already has commits" in captured.out
        assert "skipping initial commit" in captured.out

    @patch("subprocess.run")
    def test_create_initial_commit_failure(self, mock_run, temp_project, capsys):
        """Test initial commit creation failure."""
        # Arrange
        mock_run.side_effect = [
            subprocess.CalledProcessError(128, "git rev-list"),  # No commits
            Mock(returncode=0),  # git add succeeds
            subprocess.CalledProcessError(1, "git commit"),  # commit fails
        ]

        # Act
        result = create_initial_commit(temp_project)
        captured = capsys.readouterr()

        # Assert
        assert result is False
        assert "Failed to create initial commit" in captured.out

    @patch("subprocess.run")
    def test_create_initial_commit_message_format(self, mock_run, temp_project):
        """Test initial commit message format."""
        # Arrange
        mock_run.side_effect = [
            subprocess.CalledProcessError(128, "git rev-list"),
            Mock(returncode=0),
            Mock(returncode=0),
        ]

        # Act
        create_initial_commit(temp_project)

        # Assert
        commit_call = mock_run.call_args_list[2]
        # The commit message is the third argument (after ["git", "commit", "-m"])
        commit_args = commit_call[0][0]
        assert commit_args[0] == "git"
        assert commit_args[1] == "commit"
        assert commit_args[2] == "-m"
        commit_msg = commit_args[3]
        assert "chore: Initialize project with Session-Driven Development" in commit_msg
        assert "Co-Authored-By: Claude" in commit_msg


class TestInitProject:
    """Tests for init_project main function."""

    def test_init_project_already_initialized(self, temp_project, monkeypatch, capsys):
        """Test when project is already initialized."""
        # Arrange
        monkeypatch.chdir(temp_project)
        (temp_project / ".session").mkdir()

        # Act
        result = init_project()
        captured = capsys.readouterr()

        # Assert
        assert result == 1
        assert "Already initialized!" in captured.out

    @patch("sdd.project.init.create_initial_commit")
    @patch("sdd.project.init.ensure_gitignore_entries")
    @patch("sdd.project.init.run_initial_scans")
    @patch("sdd.project.init.initialize_tracking_files")
    @patch("sdd.project.init.create_session_structure")
    @patch("sdd.project.init.create_smoke_tests")
    @patch("sdd.project.init.install_dependencies")
    @patch("sdd.project.init.ensure_config_files")
    @patch("sdd.project.init.ensure_package_manager_file")
    @patch("sdd.project.init.detect_project_type")
    @patch("sdd.project.init.install_git_hooks")
    @patch("sdd.project.init.check_or_init_git")
    def test_init_project_full_workflow(
        self,
        mock_git,
        mock_hooks,
        mock_detect,
        mock_package,
        mock_config,
        mock_deps,
        mock_tests,
        mock_structure,
        mock_tracking,
        mock_scans,
        mock_gitignore,
        mock_commit,
        temp_project,
        monkeypatch,
        capsys,
    ):
        """Test complete initialization workflow."""
        # Arrange
        monkeypatch.chdir(temp_project)
        mock_git.return_value = True
        mock_hooks.return_value = True
        mock_detect.return_value = "typescript"
        mock_commit.return_value = True

        # Act
        result = init_project()
        captured = capsys.readouterr()

        # Assert
        assert result == 0
        assert "SDD Initialized Successfully!" in captured.out
        mock_git.assert_called_once()
        mock_hooks.assert_called_once()
        mock_detect.assert_called_once()
        mock_package.assert_called_once_with("typescript")
        mock_config.assert_called_once_with("typescript")
        mock_deps.assert_called_once_with("typescript")
        mock_tests.assert_called_once_with("typescript")
        mock_structure.assert_called_once()
        mock_tracking.assert_called_once()
        mock_scans.assert_called_once()
        mock_gitignore.assert_called_once()
        mock_commit.assert_called_once()

    @patch("sdd.project.init.create_initial_commit")
    @patch("sdd.project.init.ensure_gitignore_entries")
    @patch("sdd.project.init.run_initial_scans")
    @patch("sdd.project.init.initialize_tracking_files")
    @patch("sdd.project.init.create_session_structure")
    @patch("sdd.project.init.create_smoke_tests")
    @patch("sdd.project.init.install_dependencies")
    @patch("sdd.project.init.ensure_config_files")
    @patch("sdd.project.init.ensure_package_manager_file")
    @patch("sdd.project.init.detect_project_type")
    @patch("sdd.project.init.install_git_hooks")
    @patch("sdd.project.init.check_or_init_git")
    def test_init_project_python_workflow(
        self,
        mock_git,
        mock_hooks,
        mock_detect,
        mock_package,
        mock_config,
        mock_deps,
        mock_tests,
        mock_structure,
        mock_tracking,
        mock_scans,
        mock_gitignore,
        mock_commit,
        temp_project,
        monkeypatch,
        capsys,
    ):
        """Test initialization workflow for Python project."""
        # Arrange
        monkeypatch.chdir(temp_project)
        mock_git.return_value = True
        mock_hooks.return_value = True
        mock_detect.return_value = "python"
        mock_commit.return_value = True

        # Act
        result = init_project()
        captured = capsys.readouterr()

        # Assert
        assert result == 0
        assert "Project type: python" in captured.out
        mock_package.assert_called_once_with("python")
        mock_config.assert_called_once_with("python")
        mock_deps.assert_called_once_with("python")
        mock_tests.assert_called_once_with("python")

    def test_init_project_success_message(self, temp_project, monkeypatch, capsys):
        """Test success message includes all created items."""
        # Arrange
        monkeypatch.chdir(temp_project)

        with patch("sdd.project.init.check_or_init_git", return_value=True):
            with patch("sdd.project.init.install_git_hooks", return_value=True):
                with patch("sdd.project.init.detect_project_type", return_value="python"):
                    with patch("sdd.project.init.ensure_package_manager_file"):
                        with patch("sdd.project.init.ensure_config_files"):
                            with patch("sdd.project.init.install_dependencies"):
                                with patch("sdd.project.init.create_smoke_tests"):
                                    with patch("sdd.project.init.create_session_structure"):
                                        with patch("sdd.project.init.initialize_tracking_files"):
                                            with patch("sdd.project.init.run_initial_scans"):
                                                with patch(
                                                    "sdd.project.init.ensure_gitignore_entries"
                                                ):
                                                    with patch(
                                                        "sdd.project.init.create_initial_commit",
                                                        return_value=True,
                                                    ):
                                                        # Act
                                                        result = init_project()
                                                        captured = capsys.readouterr()

        # Assert
        assert result == 0
        assert "Git repository initialized" in captured.out
        assert "Git hooks" in captured.out
        assert "Config files" in captured.out
        assert "Dependencies installed" in captured.out
        assert "Smoke tests created" in captured.out
        assert ".session/ structure" in captured.out
        assert "Project context" in captured.out
        assert ".gitignore updated" in captured.out
        assert "/sdd:work-new" in captured.out
