"""
Integration tests for briefing generation functionality.

Tests the briefing_generator.py module including:
- Argument parsing and work item selection
- Integration test briefing generation
- Integration test summary generation
- Pre-session checks and utility functions
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Import functions under test
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.briefing_generator import (
    check_command_exists,
    generate_integration_test_briefing,
    main,
)
from scripts.session_complete import generate_integration_test_summary


@pytest.fixture
def mock_session_env(tmp_path):
    """Create a mock .session environment with test work items.

    Returns:
        Path: Root directory containing .session structure with work items,
            learnings, specs, and tracking files.
    """
    # Create directory structure
    session_dir = tmp_path / ".session"
    tracking_dir = session_dir / "tracking"
    specs_dir = session_dir / "specs"
    briefings_dir = session_dir / "briefings"

    session_dir.mkdir()
    tracking_dir.mkdir()
    specs_dir.mkdir()
    briefings_dir.mkdir()

    # Create mock work items with various states
    work_items = {
        "work_items": {
            "item_in_progress": {
                "id": "item_in_progress",
                "title": "In Progress Item",
                "type": "feature",
                "status": "in_progress",
                "priority": "high",
                "dependencies": [],
                "sessions": [{"session_num": 1, "started_at": "2025-01-01T00:00:00"}],
            },
            "item_not_started": {
                "id": "item_not_started",
                "title": "Not Started Item",
                "type": "bug",
                "status": "not_started",
                "priority": "medium",
                "dependencies": [],
            },
            "item_with_deps": {
                "id": "item_with_deps",
                "title": "Item With Dependencies",
                "type": "feature",
                "status": "not_started",
                "priority": "high",
                "dependencies": ["item_not_started"],
            },
            "item_completed": {
                "id": "item_completed",
                "title": "Completed Item",
                "type": "bug",
                "status": "completed",
                "priority": "low",
                "dependencies": [],
            },
        },
        "metadata": {
            "total_items": 4,
            "completed": 1,
            "in_progress": 1,
            "blocked": 0,
        },
    }

    work_items_file = tracking_dir / "work_items.json"
    with open(work_items_file, "w") as f:
        json.dump(work_items, f, indent=2)

    # Create mock learnings
    learnings = {"learnings": []}
    learnings_file = tracking_dir / "learnings.json"
    with open(learnings_file, "w") as f:
        json.dump(learnings, f, indent=2)

    # Create mock status
    status = {
        "current_session": 1,
        "current_work_item": "item_in_progress",
        "status": "in_progress",
    }
    status_file = tracking_dir / "status_update.json"
    with open(status_file, "w") as f:
        json.dump(status, f, indent=2)

    # Create mock stack and tree files
    (tracking_dir / "stack.txt").write_text("Test Stack")
    (tracking_dir / "tree.txt").write_text("Test Tree")

    # Create spec files for all work items
    for item_id in work_items["work_items"].keys():
        spec_file = specs_dir / f"{item_id}.md"
        spec_file.write_text(f"# {item_id}\n\nTest specification")

    return tmp_path


# ============================================================================
# Argument Parsing and Work Item Selection Tests
# ============================================================================


class TestBriefingGeneratorArgumentParsing:
    """Test argument parsing and work item selection in briefing generator."""

    def test_invalid_work_item_id_shows_error_and_available_items(
        self, mock_session_env, capsys, monkeypatch
    ):
        """Test that invalid work item ID shows error with available items list.

        When a non-existent work item ID is provided, the generator should:
        1. Exit with error code 1
        2. Display an error message about the invalid ID
        3. Show a list of available work items
        """
        # Arrange
        monkeypatch.chdir(mock_session_env)

        # Act
        with patch.object(sys, "argv", ["briefing_generator.py", "invalid_item_id"]):
            result = main()

        # Assert
        assert result == 1
        captured = capsys.readouterr()
        assert "Error: Work item 'invalid_item_id' not found" in captured.out
        assert "Available work items:" in captured.out

    def test_in_progress_conflict_prevents_starting_different_item(
        self, mock_session_env, capsys, monkeypatch
    ):
        """Test that starting different work item shows warning when another is in-progress.

        When attempting to start a different work item while one is already
        in-progress, the generator should:
        1. Exit with error code 1
        2. Show warning about the in-progress item
        3. Suggest completing current item or using --force flag
        """
        # Arrange
        monkeypatch.chdir(mock_session_env)

        # Act - Try to start item_not_started while item_in_progress is active
        with patch.object(sys, "argv", ["briefing_generator.py", "item_not_started"]):
            result = main()

        # Assert
        assert result == 1
        captured = capsys.readouterr()
        assert "Warning: Work item 'item_in_progress' is currently in-progress" in captured.out
        assert "Complete current work item first: /end" in captured.out
        assert "Force start new work item: sdd start item_not_started --force" in captured.out

    def test_unmet_dependencies_prevent_work_item_start(
        self, mock_session_env, capsys, monkeypatch
    ):
        """Test that work items with unmet dependencies cannot be started.

        When attempting to start a work item with incomplete dependencies:
        1. Exit with error code 1
        2. Show error about unmet dependencies
        3. List the specific dependencies that need completion
        """
        # Arrange
        monkeypatch.chdir(mock_session_env)

        # Set item_in_progress to not_started to avoid conflict
        work_items_file = mock_session_env / ".session" / "tracking" / "work_items.json"
        with open(work_items_file) as f:
            data = json.load(f)
        data["work_items"]["item_in_progress"]["status"] = "not_started"
        with open(work_items_file, "w") as f:
            json.dump(data, f)

        # Act - Try to start item_with_deps (depends on item_not_started which is not completed)
        with patch.object(sys, "argv", ["briefing_generator.py", "item_with_deps"]):
            result = main()

        # Assert
        assert result == 1
        captured = capsys.readouterr()
        assert "has unmet dependencies" in captured.out
        assert "item_not_started" in captured.out


# ============================================================================
# Integration Test Briefing Generation Tests
# ============================================================================


class TestIntegrationTestBriefing:
    """Test integration test briefing generation functionality."""

    def test_non_integration_work_item_returns_empty_briefing(self):
        """Test that non-integration work items return empty briefing.

        Regular work items (feature, bug, etc.) should not generate
        integration test briefing sections.
        """
        # Arrange
        work_item = {"id": "FEAT-001", "type": "feature", "title": "Regular Feature"}

        # Act
        briefing = generate_integration_test_briefing(work_item)

        # Assert
        assert briefing == ""

    def test_integration_work_item_generates_briefing_with_context(self):
        """Test that integration work items generate briefing with proper sections.

        Integration test work items should generate a briefing containing:
        1. Integration Test Context section header
        2. Scope information
        3. Required services list
        4. Test scenarios
        5. Performance requirements
        6. API contracts
        7. Pre-session checks
        """
        # Arrange
        work_item = {
            "id": "INTEG-001",
            "type": "integration_test",
            "title": "Test API Integration",
            "scope": "Testing the integration between Service A and Service B components",
            "environment_requirements": {
                "services_required": ["service-a", "service-b", "postgres"],
                "compose_file": "docker-compose.integration.yml",
            },
            "test_scenarios": [
                {
                    "name": "Happy path scenario",
                    "description": "Test successful integration",
                },
                {"name": "Error handling", "description": "Test error scenarios"},
            ],
            "performance_benchmarks": {
                "response_time": {"p95": 500},
                "throughput": {"minimum": 100},
            },
            "api_contracts": [{"contract_file": "contracts/api-v1.yaml", "version": "1.0.0"}],
        }

        # Act
        briefing = generate_integration_test_briefing(work_item)

        # Assert
        assert "## Integration Test Context" in briefing
        assert "Integration Scope" in briefing
        assert "Service A and Service B" in briefing
        assert "Required Services" in briefing
        assert "service-a" in briefing
        assert "Test Scenarios (2 total)" in briefing
        assert "Performance Requirements" in briefing
        assert "p95 < 500ms" in briefing
        assert "API Contracts (1 contracts)" in briefing
        assert "Pre-Session Checks" in briefing
        assert "Docker:" in briefing

    @pytest.mark.parametrize(
        "section,value,expected",
        [
            ("scope", "Testing the integration", "Testing the integration"),
            ("services_required", ["api", "db"], "api"),
            ("test_scenarios", [{"name": "Test1"}], "Test Scenarios"),
            ("performance_benchmarks", {"latency": {"p50": 100}}, "Performance Requirements"),
            ("api_contracts", [{"contract_file": "test.yaml"}], "API Contracts"),
        ],
    )
    def test_integration_briefing_includes_all_sections(self, section, value, expected):
        """Test that integration briefing includes various configuration sections.

        Verifies that different integration test configurations are properly
        included in the generated briefing.
        """
        # Arrange
        work_item = {"id": "INTEG-001", "type": "integration_test", "title": "Test Integration"}

        if section == "scope":
            work_item["scope"] = value
        elif section == "services_required":
            work_item["environment_requirements"] = {"services_required": value}
        elif section == "test_scenarios":
            work_item["test_scenarios"] = value
        elif section == "performance_benchmarks":
            work_item["performance_benchmarks"] = value
        elif section == "api_contracts":
            work_item["api_contracts"] = value

        # Act
        briefing = generate_integration_test_briefing(work_item)

        # Assert
        assert expected in briefing


class TestCheckCommandExists:
    """Test check_command_exists utility function."""

    def test_check_command_exists_returns_boolean(self):
        """Test that check_command_exists returns a boolean value.

        The utility should return True/False indicating whether a command
        is available in the system PATH.
        """
        # Act - Test with a command that likely exists
        python_exists = check_command_exists("python3") or check_command_exists("python")

        # Assert
        assert isinstance(python_exists, bool)

    def test_check_command_exists_returns_true_for_valid_command(self):
        """Test that check_command_exists returns True for valid commands.

        At least one Python command should exist in the test environment.
        """
        # Act
        result = check_command_exists("python3") or check_command_exists("python")

        # Assert
        assert result is True

    def test_check_command_exists_returns_false_for_invalid_command(self):
        """Test that check_command_exists returns False for non-existent commands.

        Commands that don't exist should return False.
        """
        # Act
        result = check_command_exists("this_command_definitely_does_not_exist_12345")

        # Assert
        assert result is False


# ============================================================================
# Integration Test Summary Generation Tests
# ============================================================================


class TestIntegrationTestSummary:
    """Test integration test summary generation functionality."""

    def test_non_integration_work_item_returns_empty_summary(self):
        """Test that non-integration work items return empty summary.

        Regular work items should not generate integration test summary sections.
        """
        # Arrange
        work_item = {"id": "FEAT-001", "type": "feature", "title": "Regular Feature"}
        gate_results = {}

        # Act
        summary = generate_integration_test_summary(work_item, gate_results)

        # Assert
        assert summary == ""

    def test_integration_work_item_generates_summary_with_test_results(self):
        """Test that integration work items generate summary with test results.

        Integration test summaries should include:
        1. Test results section header
        2. Test counts (passed, failed, skipped)
        3. Performance benchmarks
        4. API contract validation results
        """
        # Arrange
        work_item = {
            "id": "INTEG-001",
            "type": "integration_test",
            "title": "Test API Integration",
        }
        gate_results = {
            "integration_tests": {
                "integration_tests": {
                    "passed": 10,
                    "failed": 1,
                    "skipped": 2,
                    "total_duration": 45.5,
                },
                "performance_benchmarks": {
                    "load_test": {
                        "latency": {"p50": 80, "p95": 450, "p99": 900},
                        "throughput": {"requests_per_sec": 150},
                    },
                    "regression_detected": False,
                },
                "api_contracts": {"contracts_validated": 2, "breaking_changes": []},
            }
        }

        # Act
        summary = generate_integration_test_summary(work_item, gate_results)

        # Assert
        assert "## Integration Test Results" in summary
        assert "Passed: 10" in summary
        assert "Failed: 1" in summary
        assert "Performance Benchmarks" in summary
        assert "p50 latency: 80ms" in summary
        assert "API Contract Validation" in summary
        assert "Contracts validated: 2" in summary

    def test_summary_shows_no_breaking_changes_when_none_detected(self):
        """Test that summary correctly reports when no breaking changes detected.

        When API contract validation finds no breaking changes, the summary
        should explicitly state this.
        """
        # Arrange
        work_item = {"id": "INTEG-001", "type": "integration_test", "title": "Test Integration"}
        gate_results = {
            "integration_tests": {
                "integration_tests": {},
                "performance_benchmarks": {},
                "api_contracts": {"contracts_validated": 2, "breaking_changes": []},
            }
        }

        # Act
        summary = generate_integration_test_summary(work_item, gate_results)

        # Assert
        assert "No breaking changes" in summary

    def test_summary_highlights_breaking_changes_when_detected(self):
        """Test that summary highlights API breaking changes when detected.

        When breaking changes are found in API contracts, they should be
        prominently displayed in the summary with count and details.
        """
        # Arrange
        work_item = {"id": "INTEG-001", "type": "integration_test", "title": "Test Integration"}
        gate_results = {
            "integration_tests": {
                "integration_tests": {},
                "performance_benchmarks": {},
                "api_contracts": {
                    "contracts_validated": 2,
                    "breaking_changes": [
                        {"message": "Endpoint removed: /users"},
                        {"message": "Required parameter added: email"},
                    ],
                },
            }
        }

        # Act
        summary = generate_integration_test_summary(work_item, gate_results)

        # Assert
        assert "Breaking changes detected: 2" in summary

    def test_summary_highlights_performance_regression_when_detected(self):
        """Test that summary highlights performance regression when detected.

        When performance benchmarks indicate regression, this should be
        clearly indicated in the summary.
        """
        # Arrange
        work_item = {"id": "INTEG-001", "type": "integration_test", "title": "Test Integration"}
        gate_results = {
            "integration_tests": {
                "integration_tests": {},
                "performance_benchmarks": {
                    "load_test": {"latency": {"p50": 150}, "throughput": {}},
                    "regression_detected": True,
                },
                "api_contracts": {},
            }
        }

        # Act
        summary = generate_integration_test_summary(work_item, gate_results)

        # Assert
        assert "Performance regression detected" in summary

    @pytest.mark.parametrize(
        "passed,failed,skipped",
        [
            (10, 0, 0),
            (8, 2, 1),
            (0, 5, 0),
            (15, 1, 3),
        ],
    )
    def test_summary_includes_various_test_count_combinations(self, passed, failed, skipped):
        """Test that summary correctly formats various test count combinations.

        The summary should handle different test result distributions and
        display them correctly.
        """
        # Arrange
        work_item = {"id": "INTEG-001", "type": "integration_test", "title": "Test Integration"}
        gate_results = {
            "integration_tests": {
                "integration_tests": {
                    "passed": passed,
                    "failed": failed,
                    "skipped": skipped,
                    "total_duration": 30.0,
                },
                "performance_benchmarks": {},
                "api_contracts": {},
            }
        }

        # Act
        summary = generate_integration_test_summary(work_item, gate_results)

        # Assert
        assert f"Passed: {passed}" in summary
        if failed > 0:
            assert f"Failed: {failed}" in summary
        if skipped > 0:
            assert f"Skipped: {skipped}" in summary


# ============================================================================
# File Enhancement Verification Tests
# ============================================================================


class TestBriefingGeneratorFileStructure:
    """Test that briefing_generator.py file has required functions."""

    def test_briefing_generator_has_integration_briefing_function(self):
        """Test that briefing_generator.py contains integration briefing function.

        The module should export generate_integration_test_briefing function.
        """
        # Arrange
        briefing_file = Path("scripts/briefing_generator.py")

        # Act
        content = briefing_file.read_text()

        # Assert
        assert briefing_file.exists()
        assert "def generate_integration_test_briefing" in content

    def test_briefing_generator_has_check_command_exists_function(self):
        """Test that briefing_generator.py contains check_command_exists utility.

        The module should export check_command_exists function for checking
        if required commands are available.
        """
        # Arrange
        briefing_file = Path("scripts/briefing_generator.py")

        # Act
        content = briefing_file.read_text()

        # Assert
        assert "def check_command_exists" in content

    def test_briefing_generator_function_is_importable(self):
        """Test that integration briefing function is importable and callable.

        The generate_integration_test_briefing function should be properly
        defined and importable from the briefing_generator module.
        """
        # Arrange & Act - Already imported at module level
        from scripts.briefing_generator import generate_integration_test_briefing

        # Assert - Function is callable
        assert callable(generate_integration_test_briefing)


class TestSessionCompleteFileStructure:
    """Test that session_complete.py file has required functions."""

    def test_session_complete_has_integration_summary_function(self):
        """Test that session_complete.py contains integration summary function.

        The module should export generate_integration_test_summary function.
        """
        # Arrange
        session_file = Path("scripts/session_complete.py")

        # Act
        assert session_file.exists()
        content = session_file.read_text()

        # Assert
        assert "def generate_integration_test_summary" in content

    def test_session_complete_calls_integration_summary(self):
        """Test that session_complete.py integrates integration summary call.

        The session completion workflow should call the integration test
        summary function when appropriate.
        """
        # Arrange
        session_file = Path("scripts/session_complete.py")

        # Act
        content = session_file.read_text()

        # Assert
        assert "generate_integration_test_summary(work_item, gate_results)" in content
