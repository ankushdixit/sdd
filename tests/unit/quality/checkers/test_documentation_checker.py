"""Unit tests for documentation.py DocumentationChecker.

Tests for the DocumentationChecker class which validates CHANGELOG, docstrings, and README.
"""

from unittest.mock import Mock

import pytest

from sdd.core.command_runner import CommandResult, CommandRunner
from sdd.quality.checkers.documentation import DocumentationChecker


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project directory."""
    return tmp_path


@pytest.fixture
def mock_runner():
    """Create a mock CommandRunner."""
    return Mock(spec=CommandRunner)


@pytest.fixture
def doc_config():
    """Standard documentation config."""
    return {
        "enabled": True,
        "check_changelog": True,
        "check_docstrings": True,
        "check_readme": True,
    }


class TestDocumentationCheckerInit:
    """Tests for DocumentationChecker initialization."""

    def test_init_with_defaults(self, doc_config, temp_project_dir):
        """Test initialization with default parameters."""
        checker = DocumentationChecker(doc_config, temp_project_dir)

        assert checker.config == doc_config
        assert checker.project_root == temp_project_dir
        assert checker.runner is not None
        assert isinstance(checker.runner, CommandRunner)
        assert checker.work_item == {}

    def test_init_with_custom_runner(self, doc_config, temp_project_dir, mock_runner):
        """Test initialization with custom runner."""
        checker = DocumentationChecker(doc_config, temp_project_dir, runner=mock_runner)

        assert checker.runner is mock_runner

    def test_init_with_work_item(self, doc_config, temp_project_dir):
        """Test initialization with work item."""
        work_item = {"id": "WI-001", "title": "Test"}
        checker = DocumentationChecker(doc_config, temp_project_dir, work_item=work_item)

        assert checker.work_item == work_item


class TestDocumentationCheckerInterface:
    """Tests for DocumentationChecker interface methods."""

    def test_name_returns_documentation(self, doc_config, temp_project_dir):
        """Test name() returns 'documentation'."""
        checker = DocumentationChecker(doc_config, temp_project_dir)

        assert checker.name() == "documentation"

    def test_is_enabled_returns_true_by_default(self, temp_project_dir):
        """Test is_enabled() returns True by default."""
        config = {}
        checker = DocumentationChecker(config, temp_project_dir)

        assert checker.is_enabled() is True

    def test_is_enabled_returns_config_value(self, temp_project_dir):
        """Test is_enabled() returns config value."""
        config = {"enabled": False}
        checker = DocumentationChecker(config, temp_project_dir)

        assert checker.is_enabled() is False


class TestDocumentationCheckerRun:
    """Tests for DocumentationChecker.run() method."""

    def test_run_returns_skipped_when_disabled(self, temp_project_dir):
        """Test run() returns skipped result when disabled."""
        config = {"enabled": False}
        checker = DocumentationChecker(config, temp_project_dir)

        result = checker.run()

        assert result.checker_name == "documentation"
        assert result.passed is True
        assert result.status == "skipped"

    def test_run_passes_when_all_checks_disabled(self, temp_project_dir, mock_runner):
        """Test run() passes when no checks enabled."""
        config = {
            "enabled": True,
            "check_changelog": False,
            "check_docstrings": False,
            "check_readme": False,
        }
        checker = DocumentationChecker(config, temp_project_dir, runner=mock_runner)

        result = checker.run()

        assert result.passed is True
        assert result.status == "passed"
        assert len(result.info["checks"]) == 0

    def test_run_includes_execution_time(self, doc_config, temp_project_dir, mock_runner):
        """Test run() includes execution time in result."""
        checker = DocumentationChecker(doc_config, temp_project_dir, runner=mock_runner)

        # Mock all git commands to succeed
        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="main",
            stderr="",
            command=["git"],
            duration_seconds=0.1,
        )

        result = checker.run()

        assert result.execution_time > 0


class TestDocumentationCheckerChangelog:
    """Tests for CHANGELOG validation."""

    def test_check_changelog_passes_on_main_branch(self, doc_config, temp_project_dir, mock_runner):
        """Test CHANGELOG check passes on main branch."""
        checker = DocumentationChecker(doc_config, temp_project_dir, runner=mock_runner)

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="main",
            stderr="",
            command=["git"],
            duration_seconds=0.1,
        )

        result = checker._check_changelog_updated()

        assert result is True

    def test_check_changelog_passes_on_master_branch(
        self, doc_config, temp_project_dir, mock_runner
    ):
        """Test CHANGELOG check passes on master branch."""
        checker = DocumentationChecker(doc_config, temp_project_dir, runner=mock_runner)

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="master",
            stderr="",
            command=["git"],
            duration_seconds=0.1,
        )

        result = checker._check_changelog_updated()

        assert result is True

    def test_check_changelog_passes_when_changelog_modified(
        self, doc_config, temp_project_dir, mock_runner
    ):
        """Test CHANGELOG check passes when CHANGELOG.md modified."""
        checker = DocumentationChecker(doc_config, temp_project_dir, runner=mock_runner)

        mock_runner.run.side_effect = [
            CommandResult(
                returncode=0,
                stdout="feature-branch",
                stderr="",
                command=["git"],
                duration_seconds=0.1,
            ),
            CommandResult(
                returncode=0,
                stdout="CHANGELOG.md\nfile.py",
                stderr="",
                command=["git"],
                duration_seconds=0.1,
            ),
        ]

        result = checker._check_changelog_updated()

        assert result is True

    def test_check_changelog_fails_when_changelog_not_modified(
        self, doc_config, temp_project_dir, mock_runner
    ):
        """Test CHANGELOG check fails when CHANGELOG.md not modified."""
        checker = DocumentationChecker(doc_config, temp_project_dir, runner=mock_runner)

        mock_runner.run.side_effect = [
            CommandResult(
                returncode=0,
                stdout="feature-branch",
                stderr="",
                command=["git"],
                duration_seconds=0.1,
            ),
            CommandResult(
                returncode=0,
                stdout="file.py\ntest.py",
                stderr="",
                command=["git"],
                duration_seconds=0.1,
            ),
        ]

        result = checker._check_changelog_updated()

        assert result is False

    def test_check_changelog_passes_when_git_not_available(
        self, doc_config, temp_project_dir, mock_runner
    ):
        """Test CHANGELOG check passes when git not available."""
        checker = DocumentationChecker(doc_config, temp_project_dir, runner=mock_runner)

        mock_runner.run.return_value = CommandResult(
            returncode=1,
            stdout="",
            stderr="git not found",
            command=["git"],
            duration_seconds=0.1,
        )

        result = checker._check_changelog_updated()

        assert result is True


class TestDocumentationCheckerDocstrings:
    """Tests for docstring validation."""

    def test_check_docstrings_passes_when_no_issues(
        self, doc_config, temp_project_dir, mock_runner
    ):
        """Test docstring check passes when no issues found."""
        (temp_project_dir / "pyproject.toml").touch()
        checker = DocumentationChecker(doc_config, temp_project_dir, runner=mock_runner)

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="",
            stderr="",
            command=["pydocstyle"],
            duration_seconds=0.5,
        )

        result = checker._check_python_docstrings()

        assert result is True

    def test_check_docstrings_fails_when_issues_found(
        self, doc_config, temp_project_dir, mock_runner
    ):
        """Test docstring check fails when issues found."""
        (temp_project_dir / "pyproject.toml").touch()
        checker = DocumentationChecker(doc_config, temp_project_dir, runner=mock_runner)

        mock_runner.run.return_value = CommandResult(
            returncode=1,
            stdout="5 issues",
            stderr="",
            command=["pydocstyle"],
            duration_seconds=0.5,
        )

        result = checker._check_python_docstrings()

        assert result is False

    def test_check_docstrings_passes_for_non_python_project(
        self, doc_config, temp_project_dir, mock_runner
    ):
        """Test docstring check passes for non-Python project."""
        checker = DocumentationChecker(doc_config, temp_project_dir, runner=mock_runner)

        result = checker._check_python_docstrings()

        assert result is True

    def test_check_docstrings_passes_when_pydocstyle_not_available(
        self, doc_config, temp_project_dir, mock_runner
    ):
        """Test docstring check passes when pydocstyle not available."""
        (temp_project_dir / "pyproject.toml").touch()
        checker = DocumentationChecker(doc_config, temp_project_dir, runner=mock_runner)

        mock_runner.run.return_value = CommandResult(
            returncode=-1,
            stdout="",
            stderr="",
            command=["pydocstyle"],
            duration_seconds=0.1,
        )

        result = checker._check_python_docstrings()

        assert result is True

    def test_check_docstrings_passes_when_timeout(self, doc_config, temp_project_dir, mock_runner):
        """Test docstring check passes when timeout occurs."""
        (temp_project_dir / "pyproject.toml").touch()
        checker = DocumentationChecker(doc_config, temp_project_dir, runner=mock_runner)

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="",
            stderr="",
            command=["pydocstyle"],
            duration_seconds=30.0,
            timed_out=True,
        )

        result = checker._check_python_docstrings()

        assert result is True


class TestDocumentationCheckerReadme:
    """Tests for README validation."""

    def test_check_readme_passes_when_readme_updated(
        self, doc_config, temp_project_dir, mock_runner
    ):
        """Test README check passes when README updated."""
        checker = DocumentationChecker(doc_config, temp_project_dir, runner=mock_runner)

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="README.md\nfile.py",
            stderr="",
            command=["git"],
            duration_seconds=0.1,
        )

        result = checker._check_readme_current()

        assert result is True

    def test_check_readme_fails_when_readme_not_updated(
        self, doc_config, temp_project_dir, mock_runner
    ):
        """Test README check fails when README not updated."""
        checker = DocumentationChecker(doc_config, temp_project_dir, runner=mock_runner)

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="file.py\ntest.py",
            stderr="",
            command=["git"],
            duration_seconds=0.1,
        )

        result = checker._check_readme_current()

        assert result is False

    def test_check_readme_passes_when_git_not_available(
        self, doc_config, temp_project_dir, mock_runner
    ):
        """Test README check passes when git not available."""
        checker = DocumentationChecker(doc_config, temp_project_dir, runner=mock_runner)

        mock_runner.run.return_value = CommandResult(
            returncode=1,
            stdout="",
            stderr="git not found",
            command=["git"],
            duration_seconds=0.1,
        )

        result = checker._check_readme_current()

        assert result is True

    def test_check_readme_case_insensitive(self, doc_config, temp_project_dir, mock_runner):
        """Test README check is case insensitive."""
        checker = DocumentationChecker(doc_config, temp_project_dir, runner=mock_runner)

        mock_runner.run.return_value = CommandResult(
            returncode=0,
            stdout="readme.txt\nfile.py",
            stderr="",
            command=["git"],
            duration_seconds=0.1,
        )

        result = checker._check_readme_current()

        assert result is True


class TestDocumentationCheckerIntegration:
    """Integration tests for documentation checker."""

    def test_run_passes_all_checks(self, doc_config, temp_project_dir, mock_runner):
        """Test run() passes when all checks pass."""
        (temp_project_dir / "pyproject.toml").touch()
        checker = DocumentationChecker(doc_config, temp_project_dir, runner=mock_runner)

        # Mock successful responses
        mock_runner.run.side_effect = [
            # CHANGELOG check
            CommandResult(
                returncode=0,
                stdout="main",
                stderr="",
                command=["git"],
                duration_seconds=0.1,
            ),
            # Docstrings check
            CommandResult(
                returncode=0,
                stdout="",
                stderr="",
                command=["pydocstyle"],
                duration_seconds=0.5,
            ),
            # README check
            CommandResult(
                returncode=0,
                stdout="README.md",
                stderr="",
                command=["git"],
                duration_seconds=0.1,
            ),
        ]

        result = checker.run()

        assert result.passed is True
        assert result.status == "passed"
        assert len(result.info["checks"]) == 3

    def test_run_fails_when_any_check_fails(self, doc_config, temp_project_dir, mock_runner):
        """Test run() fails when any check fails."""
        (temp_project_dir / "pyproject.toml").touch()
        checker = DocumentationChecker(doc_config, temp_project_dir, runner=mock_runner)

        # Mock mixed responses
        mock_runner.run.side_effect = [
            # CHANGELOG check - passes
            CommandResult(
                returncode=0,
                stdout="main",
                stderr="",
                command=["git"],
                duration_seconds=0.1,
            ),
            # Docstrings check - fails
            CommandResult(
                returncode=1,
                stdout="issues",
                stderr="",
                command=["pydocstyle"],
                duration_seconds=0.5,
            ),
            # README check - passes
            CommandResult(
                returncode=0,
                stdout="README.md",
                stderr="",
                command=["git"],
                duration_seconds=0.1,
            ),
        ]

        result = checker.run()

        assert result.passed is False
        assert result.status == "failed"
        assert len(result.errors) > 0

    def test_run_includes_check_details(self, doc_config, temp_project_dir, mock_runner):
        """Test run() includes details for each check."""
        checker = DocumentationChecker(doc_config, temp_project_dir, runner=mock_runner)

        # Mock successful responses
        mock_runner.run.side_effect = [
            CommandResult(
                returncode=0,
                stdout="main",
                stderr="",
                command=["git"],
                duration_seconds=0.1,
            ),
            CommandResult(
                returncode=0,
                stdout="",
                stderr="",
                command=["pydocstyle"],
                duration_seconds=0.5,
            ),
            CommandResult(
                returncode=0,
                stdout="README.md",
                stderr="",
                command=["git"],
                duration_seconds=0.1,
            ),
        ]

        result = checker.run()

        checks = result.info["checks"]
        assert len(checks) == 3
        assert all("name" in check for check in checks)
        assert all("passed" in check for check in checks)
