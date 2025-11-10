"""Unit tests for context7.py Context7Checker.

Tests for the Context7Checker class which verifies important libraries
via Context7 MCP integration by parsing stack.txt and querying Context7.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from solokit.core.command_runner import CommandRunner
from solokit.core.exceptions import FileOperationError
from solokit.quality.checkers.context7 import Context7Checker


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project directory."""
    # Create .session/tracking directory
    session_dir = tmp_path / ".session" / "tracking"
    session_dir.mkdir(parents=True)
    return tmp_path


@pytest.fixture
def mock_runner():
    """Create a mock CommandRunner."""
    return Mock(spec=CommandRunner)


@pytest.fixture
def basic_config():
    """Basic Context7 config."""
    return {
        "enabled": True,
    }


@pytest.fixture
def config_with_important_libs():
    """Config with important libraries list."""
    return {
        "enabled": True,
        "important_libraries": ["pytest", "numpy", "pandas"],
    }


@pytest.fixture
def disabled_config():
    """Disabled Context7 config."""
    return {
        "enabled": False,
    }


class TestContext7CheckerInit:
    """Tests for Context7Checker initialization."""

    def test_init_with_defaults(self, basic_config, temp_project_dir):
        """Test initialization with default parameters."""
        checker = Context7Checker(basic_config, temp_project_dir)

        assert checker.config == basic_config
        assert checker.project_root == temp_project_dir
        assert checker.runner is not None
        assert isinstance(checker.runner, CommandRunner)

    def test_init_with_custom_runner(self, basic_config, temp_project_dir, mock_runner):
        """Test initialization with custom runner."""
        checker = Context7Checker(basic_config, temp_project_dir, runner=mock_runner)

        assert checker.runner is mock_runner

    def test_init_with_no_project_root(self, basic_config):
        """Test initialization with no project root defaults to cwd."""
        checker = Context7Checker(basic_config)

        assert checker.project_root == Path.cwd()


class TestContext7CheckerInterface:
    """Tests for Context7Checker interface methods."""

    def test_name_returns_context7(self, basic_config, temp_project_dir):
        """Test name() returns 'context7'."""
        checker = Context7Checker(basic_config, temp_project_dir)

        assert checker.name() == "context7"

    def test_is_enabled_returns_false_by_default(self, temp_project_dir):
        """Test is_enabled() returns False by default."""
        config = {}
        checker = Context7Checker(config, temp_project_dir)

        assert checker.is_enabled() is False

    def test_is_enabled_returns_config_value(self, temp_project_dir):
        """Test is_enabled() returns config value."""
        config = {"enabled": True}
        checker = Context7Checker(config, temp_project_dir)

        assert checker.is_enabled() is True


class TestContext7CheckerRun:
    """Tests for Context7Checker.run() method."""

    def test_run_returns_skipped_when_disabled(self, disabled_config, temp_project_dir):
        """Test run() returns skipped result when disabled."""
        checker = Context7Checker(disabled_config, temp_project_dir)

        result = checker.run()

        assert result.checker_name == "context7"
        assert result.passed is True
        assert result.status == "skipped"
        assert result.info["reason"] == "not enabled"

    def test_run_returns_skipped_when_no_stack_txt(self, basic_config, temp_project_dir):
        """Test run() returns skipped when stack.txt doesn't exist."""
        # Don't create stack.txt
        checker = Context7Checker(basic_config, temp_project_dir)

        result = checker.run()

        assert result.checker_name == "context7"
        assert result.passed is True
        assert result.status == "skipped"
        assert result.info["reason"] == "no stack.txt"

    def test_run_passes_with_no_libraries(self, basic_config, temp_project_dir):
        """Test run() passes when stack.txt is empty."""
        stack_file = temp_project_dir / ".session" / "tracking" / "stack.txt"
        stack_file.write_text("")

        checker = Context7Checker(basic_config, temp_project_dir)

        result = checker.run()

        assert result.checker_name == "context7"
        assert result.passed is True
        assert result.status == "passed"
        assert result.info["total_libraries"] == 0
        assert result.info["verified"] == 0
        assert result.info["failed"] == 0

    def test_run_passes_with_all_libraries_verified(
        self, basic_config, temp_project_dir, mock_runner
    ):
        """Test run() passes when all libraries are verified."""
        stack_file = temp_project_dir / ".session" / "tracking" / "stack.txt"
        stack_file.write_text("pytest 7.4.0\nnumpy 1.24.0\npandas 2.0.0\n")

        checker = Context7Checker(basic_config, temp_project_dir, runner=mock_runner)

        # Mock _query_context7 to return True
        with patch.object(checker, "_query_context7", return_value=True):
            result = checker.run()

        assert result.passed is True
        assert result.status == "passed"
        assert result.info["total_libraries"] == 3
        assert result.info["verified"] == 3
        assert result.info["failed"] == 0
        assert len(result.errors) == 0

    def test_run_fails_with_some_libraries_unverified(
        self, basic_config, temp_project_dir, mock_runner
    ):
        """Test run() fails when some libraries fail verification."""
        stack_file = temp_project_dir / ".session" / "tracking" / "stack.txt"
        stack_file.write_text("pytest 7.4.0\nnumpy 1.24.0\npandas 2.0.0\n")

        checker = Context7Checker(basic_config, temp_project_dir, runner=mock_runner)

        # Mock _query_context7 to return False for numpy
        def mock_query(lib):
            return lib["name"] != "numpy"

        with patch.object(checker, "_query_context7", side_effect=mock_query):
            result = checker.run()

        assert result.passed is False
        assert result.status == "failed"
        assert result.info["total_libraries"] == 3
        assert result.info["verified"] == 2
        assert result.info["failed"] == 1
        assert len(result.errors) == 1
        assert result.errors[0]["library"] == "numpy"

    def test_run_filters_by_important_libraries(
        self, config_with_important_libs, temp_project_dir, mock_runner
    ):
        """Test run() only verifies important libraries when configured."""
        stack_file = temp_project_dir / ".session" / "tracking" / "stack.txt"
        stack_file.write_text("pytest 7.4.0\nnumpy 1.24.0\nrequests 2.31.0\n")

        checker = Context7Checker(config_with_important_libs, temp_project_dir, runner=mock_runner)

        with patch.object(checker, "_query_context7", return_value=True):
            result = checker.run()

        # Only pytest and numpy should be verified (not requests)
        assert result.info["total_libraries"] == 2
        library_names = [lib["name"] for lib in result.info["libraries"]]
        assert "pytest" in library_names
        assert "numpy" in library_names
        assert "requests" not in library_names

    def test_run_includes_execution_time(self, basic_config, temp_project_dir):
        """Test run() includes execution time in result."""
        stack_file = temp_project_dir / ".session" / "tracking" / "stack.txt"
        stack_file.write_text("pytest 7.4.0\n")

        checker = Context7Checker(basic_config, temp_project_dir)

        result = checker.run()

        assert result.execution_time > 0

    def test_run_handles_file_operation_error(self, basic_config, temp_project_dir, mock_runner):
        """Test run() handles file operation errors gracefully."""
        stack_file = temp_project_dir / ".session" / "tracking" / "stack.txt"
        stack_file.write_text("pytest 7.4.0\n")

        checker = Context7Checker(basic_config, temp_project_dir, runner=mock_runner)

        # Mock _parse_libraries_from_stack to raise FileOperationError
        with patch.object(
            checker,
            "_parse_libraries_from_stack",
            side_effect=FileOperationError(
                operation="read",
                file_path=str(stack_file),
                details="Mock error",
            ),
        ):
            result = checker.run()

        assert result.passed is False
        assert result.status == "failed"
        assert len(result.errors) == 1
        assert "Failed to read stack.txt" in result.errors[0]["message"]
        assert result.info["reason"] == "stack file read error"


class TestContext7CheckerParseLibraries:
    """Tests for _parse_libraries_from_stack method."""

    def test_parse_libraries_with_version(self, basic_config, temp_project_dir):
        """Test parsing libraries with version numbers."""
        stack_file = temp_project_dir / ".session" / "tracking" / "stack.txt"
        stack_file.write_text("pytest 7.4.0\nnumpy 1.24.0\npandas 2.0.0\n")

        checker = Context7Checker(basic_config, temp_project_dir)

        libraries = checker._parse_libraries_from_stack(stack_file)

        assert len(libraries) == 3
        assert libraries[0] == {"name": "pytest", "version": "7.4.0"}
        assert libraries[1] == {"name": "numpy", "version": "1.24.0"}
        assert libraries[2] == {"name": "pandas", "version": "2.0.0"}

    def test_parse_libraries_without_version(self, basic_config, temp_project_dir):
        """Test parsing libraries without version numbers."""
        stack_file = temp_project_dir / ".session" / "tracking" / "stack.txt"
        stack_file.write_text("pytest\nnumpy\npandas\n")

        checker = Context7Checker(basic_config, temp_project_dir)

        libraries = checker._parse_libraries_from_stack(stack_file)

        assert len(libraries) == 3
        assert libraries[0] == {"name": "pytest", "version": "unknown"}
        assert libraries[1] == {"name": "numpy", "version": "unknown"}
        assert libraries[2] == {"name": "pandas", "version": "unknown"}

    def test_parse_libraries_ignores_empty_lines(self, basic_config, temp_project_dir):
        """Test parsing ignores empty lines."""
        stack_file = temp_project_dir / ".session" / "tracking" / "stack.txt"
        stack_file.write_text("pytest 7.4.0\n\n\nnumpy 1.24.0\n\n")

        checker = Context7Checker(basic_config, temp_project_dir)

        libraries = checker._parse_libraries_from_stack(stack_file)

        assert len(libraries) == 2
        assert libraries[0] == {"name": "pytest", "version": "7.4.0"}
        assert libraries[1] == {"name": "numpy", "version": "1.24.0"}

    def test_parse_libraries_ignores_comments(self, basic_config, temp_project_dir):
        """Test parsing ignores comment lines."""
        stack_file = temp_project_dir / ".session" / "tracking" / "stack.txt"
        stack_file.write_text("# Core libraries\npytest 7.4.0\n# Data libraries\nnumpy 1.24.0\n")

        checker = Context7Checker(basic_config, temp_project_dir)

        libraries = checker._parse_libraries_from_stack(stack_file)

        assert len(libraries) == 2
        assert libraries[0] == {"name": "pytest", "version": "7.4.0"}
        assert libraries[1] == {"name": "numpy", "version": "1.24.0"}

    def test_parse_libraries_handles_extra_whitespace(self, basic_config, temp_project_dir):
        """Test parsing handles extra whitespace."""
        stack_file = temp_project_dir / ".session" / "tracking" / "stack.txt"
        stack_file.write_text("  pytest  7.4.0  \n  numpy  1.24.0  \n")

        checker = Context7Checker(basic_config, temp_project_dir)

        libraries = checker._parse_libraries_from_stack(stack_file)

        assert len(libraries) == 2
        assert libraries[0] == {"name": "pytest", "version": "7.4.0"}
        assert libraries[1] == {"name": "numpy", "version": "1.24.0"}

    def test_parse_libraries_handles_parenthetical_info(self, basic_config, temp_project_dir):
        """Test parsing handles parenthetical information."""
        stack_file = temp_project_dir / ".session" / "tracking" / "stack.txt"
        stack_file.write_text("pytest (testing)\nnumpy (data)\n")

        checker = Context7Checker(basic_config, temp_project_dir)

        libraries = checker._parse_libraries_from_stack(stack_file)

        assert len(libraries) == 2
        assert libraries[0] == {"name": "pytest", "version": "(testing)"}
        assert libraries[1] == {"name": "numpy", "version": "(data)"}

    def test_parse_libraries_raises_on_file_not_found(self, basic_config, temp_project_dir):
        """Test parsing raises FileOperationError when file not found."""
        stack_file = temp_project_dir / ".session" / "tracking" / "nonexistent.txt"

        checker = Context7Checker(basic_config, temp_project_dir)

        with pytest.raises(FileOperationError) as exc_info:
            checker._parse_libraries_from_stack(stack_file)

        assert exc_info.value.context["operation"] == "read"
        assert "nonexistent.txt" in exc_info.value.context["file_path"]
        assert "Failed to read stack.txt file" in exc_info.value.context["details"]

    def test_parse_libraries_raises_on_permission_error(self, basic_config, temp_project_dir):
        """Test parsing raises FileOperationError on permission error."""
        stack_file = temp_project_dir / ".session" / "tracking" / "stack.txt"
        stack_file.write_text("pytest 7.4.0\n")

        checker = Context7Checker(basic_config, temp_project_dir)

        # Mock open() to raise PermissionError
        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            with pytest.raises(FileOperationError) as exc_info:
                checker._parse_libraries_from_stack(stack_file)

        assert exc_info.value.context["operation"] == "read"
        assert "stack.txt" in exc_info.value.context["file_path"]
        assert "Failed to read stack.txt file" in exc_info.value.context["details"]

    def test_parse_libraries_empty_file(self, basic_config, temp_project_dir):
        """Test parsing empty file returns empty list."""
        stack_file = temp_project_dir / ".session" / "tracking" / "stack.txt"
        stack_file.write_text("")

        checker = Context7Checker(basic_config, temp_project_dir)

        libraries = checker._parse_libraries_from_stack(stack_file)

        assert len(libraries) == 0


class TestContext7CheckerShouldVerify:
    """Tests for _should_verify_library method."""

    def test_should_verify_all_when_no_important_list(self, basic_config, temp_project_dir):
        """Test all libraries are verified when no important list configured."""
        checker = Context7Checker(basic_config, temp_project_dir)

        assert checker._should_verify_library({"name": "pytest", "version": "7.4.0"}) is True
        assert checker._should_verify_library({"name": "numpy", "version": "1.24.0"}) is True
        assert checker._should_verify_library({"name": "requests", "version": "2.31.0"}) is True

    def test_should_verify_only_important_when_list_configured(
        self, config_with_important_libs, temp_project_dir
    ):
        """Test only important libraries are verified when list configured."""
        checker = Context7Checker(config_with_important_libs, temp_project_dir)

        assert checker._should_verify_library({"name": "pytest", "version": "7.4.0"}) is True
        assert checker._should_verify_library({"name": "numpy", "version": "1.24.0"}) is True
        assert checker._should_verify_library({"name": "pandas", "version": "2.0.0"}) is True
        assert checker._should_verify_library({"name": "requests", "version": "2.31.0"}) is False
        assert checker._should_verify_library({"name": "django", "version": "4.2.0"}) is False

    def test_should_verify_empty_important_list(self, temp_project_dir):
        """Test behavior with empty important libraries list."""
        config = {"enabled": True, "important_libraries": []}
        checker = Context7Checker(config, temp_project_dir)

        # Empty list means verify all (no filtering)
        assert checker._should_verify_library({"name": "pytest", "version": "7.4.0"}) is True
        assert checker._should_verify_library({"name": "numpy", "version": "1.24.0"}) is True


class TestContext7CheckerQueryContext7:
    """Tests for _query_context7 method."""

    def test_query_context7_returns_true_by_default(self, basic_config, temp_project_dir):
        """Test _query_context7 returns True by default (stub implementation)."""
        checker = Context7Checker(basic_config, temp_project_dir)

        result = checker._query_context7({"name": "pytest", "version": "7.4.0"})

        assert result is True

    def test_query_context7_stub_for_all_libraries(self, basic_config, temp_project_dir):
        """Test _query_context7 stub works for all library types."""
        checker = Context7Checker(basic_config, temp_project_dir)

        assert checker._query_context7({"name": "pytest", "version": "7.4.0"}) is True
        assert checker._query_context7({"name": "numpy", "version": "1.24.0"}) is True
        assert checker._query_context7({"name": "pandas", "version": "unknown"}) is True


class TestContext7CheckerIntegration:
    """Integration tests for Context7Checker."""

    def test_full_workflow_with_mixed_results(self, basic_config, temp_project_dir, mock_runner):
        """Test full workflow with mixed verification results."""
        stack_file = temp_project_dir / ".session" / "tracking" / "stack.txt"
        stack_file.write_text("pytest 7.4.0\nnumpy 1.24.0\npandas 2.0.0\nrequests 2.31.0\n")

        checker = Context7Checker(basic_config, temp_project_dir, runner=mock_runner)

        # Mock to fail numpy and pandas
        def mock_query(lib):
            return lib["name"] in ["pytest", "requests"]

        with patch.object(checker, "_query_context7", side_effect=mock_query):
            result = checker.run()

        assert result.passed is False
        assert result.status == "failed"
        assert result.info["total_libraries"] == 4
        assert result.info["verified"] == 2
        assert result.info["failed"] == 2
        assert len(result.errors) == 2

        # Check error details
        error_libs = [err["library"] for err in result.errors]
        assert "numpy" in error_libs
        assert "pandas" in error_libs

    def test_full_workflow_with_important_libraries_filter(
        self, config_with_important_libs, temp_project_dir, mock_runner
    ):
        """Test full workflow with important libraries filtering."""
        stack_file = temp_project_dir / ".session" / "tracking" / "stack.txt"
        stack_file.write_text(
            "pytest 7.4.0\nnumpy 1.24.0\npandas 2.0.0\nrequests 2.31.0\ndjango 4.2.0\n"
        )

        checker = Context7Checker(config_with_important_libs, temp_project_dir, runner=mock_runner)

        # Mock to fail pandas
        def mock_query(lib):
            return lib["name"] != "pandas"

        with patch.object(checker, "_query_context7", side_effect=mock_query):
            result = checker.run()

        # Only pytest, numpy, pandas should be checked (not requests or django)
        assert result.info["total_libraries"] == 3
        assert result.info["verified"] == 2
        assert result.info["failed"] == 1

        library_names = [lib["name"] for lib in result.info["libraries"]]
        assert "pytest" in library_names
        assert "numpy" in library_names
        assert "pandas" in library_names
        assert "requests" not in library_names
        assert "django" not in library_names

    def test_full_workflow_with_comments_and_whitespace(self, basic_config, temp_project_dir):
        """Test full workflow handles comments and whitespace correctly."""
        stack_file = temp_project_dir / ".session" / "tracking" / "stack.txt"
        stack_file.write_text(
            "# Testing libraries\n  pytest  7.4.0  \n\n# Data science\n  numpy  1.24.0  \n\n"
        )

        checker = Context7Checker(basic_config, temp_project_dir)

        result = checker.run()

        assert result.passed is True
        assert result.info["total_libraries"] == 2
        assert result.info["verified"] == 2

    def test_result_structure_matches_checkresult_contract(self, basic_config, temp_project_dir):
        """Test result structure matches CheckResult contract."""
        stack_file = temp_project_dir / ".session" / "tracking" / "stack.txt"
        stack_file.write_text("pytest 7.4.0\n")

        checker = Context7Checker(basic_config, temp_project_dir)

        result = checker.run()

        # Verify all CheckResult fields are present and correct type
        assert isinstance(result.checker_name, str)
        assert result.checker_name == "context7"
        assert isinstance(result.passed, bool)
        assert isinstance(result.status, str)
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)
        assert isinstance(result.info, dict)
        assert isinstance(result.execution_time, float)
