"""Unit tests for results.py ResultAggregator.

Tests for the ResultAggregator class which combines results from multiple checkers.
"""

import pytest

from solokit.quality.checkers.base import CheckResult
from solokit.quality.results import ResultAggregator


@pytest.fixture
def aggregator():
    """Create a ResultAggregator instance."""
    return ResultAggregator()


@pytest.fixture
def passing_check_result():
    """Create a passing CheckResult."""
    return CheckResult(
        checker_name="tests",
        passed=True,
        status="passed",
        errors=[],
        warnings=[],
        info={"coverage": 85.0},
        execution_time=5.2,
    )


@pytest.fixture
def failing_check_result():
    """Create a failing CheckResult."""
    return CheckResult(
        checker_name="linting",
        passed=False,
        status="failed",
        errors=[{"message": "Linting issues found"}],
        warnings=[],
        info={},
        execution_time=2.3,
    )


@pytest.fixture
def skipped_check_result():
    """Create a skipped CheckResult."""
    return CheckResult(
        checker_name="security",
        passed=True,
        status="skipped",
        errors=[],
        warnings=[],
        info={"reason": "tool not available"},
        execution_time=0.0,
    )


class TestResultAggregatorAggregate:
    """Tests for ResultAggregator.aggregate() method."""

    def test_aggregate_empty_results(self, aggregator):
        """Test aggregate() with empty results list."""
        result = aggregator.aggregate([])

        assert result["overall_passed"] is True
        assert result["total_checks"] == 0
        assert result["passed_checks"] == 0
        assert result["failed_checks"] == 0
        assert result["skipped_checks"] == 0
        assert result["by_checker"] == {}
        assert result["failed_checkers"] == []
        assert result["total_execution_time"] == 0.0

    def test_aggregate_single_passing_result(self, aggregator, passing_check_result):
        """Test aggregate() with single passing result."""
        result = aggregator.aggregate([passing_check_result])

        assert result["overall_passed"] is True
        assert result["total_checks"] == 1
        assert result["passed_checks"] == 1
        assert result["failed_checks"] == 0
        assert result["skipped_checks"] == 0
        assert len(result["failed_checkers"]) == 0

    def test_aggregate_single_failing_result(self, aggregator, failing_check_result):
        """Test aggregate() with single failing result."""
        result = aggregator.aggregate([failing_check_result])

        assert result["overall_passed"] is False
        assert result["total_checks"] == 1
        assert result["passed_checks"] == 0
        assert result["failed_checks"] == 1
        assert result["skipped_checks"] == 0
        assert "linting" in result["failed_checkers"]

    def test_aggregate_single_skipped_result(self, aggregator, skipped_check_result):
        """Test aggregate() with single skipped result."""
        result = aggregator.aggregate([skipped_check_result])

        assert result["overall_passed"] is True
        assert result["total_checks"] == 1
        assert result["passed_checks"] == 0
        assert result["failed_checks"] == 0
        assert result["skipped_checks"] == 1
        assert len(result["failed_checkers"]) == 0

    def test_aggregate_mixed_results(
        self,
        aggregator,
        passing_check_result,
        failing_check_result,
        skipped_check_result,
    ):
        """Test aggregate() with mixed results."""
        results = [passing_check_result, failing_check_result, skipped_check_result]

        result = aggregator.aggregate(results)

        assert result["overall_passed"] is False
        assert result["total_checks"] == 3
        assert result["passed_checks"] == 1
        assert result["failed_checks"] == 1
        assert result["skipped_checks"] == 1
        assert "linting" in result["failed_checkers"]

    def test_aggregate_multiple_passing_results(self, aggregator):
        """Test aggregate() with multiple passing results."""
        results = [
            CheckResult("tests", True, "passed", [], [], {}, 5.0),
            CheckResult("linting", True, "passed", [], [], {}, 2.0),
            CheckResult("formatting", True, "passed", [], [], {}, 3.0),
        ]

        result = aggregator.aggregate(results)

        assert result["overall_passed"] is True
        assert result["total_checks"] == 3
        assert result["passed_checks"] == 3
        assert result["failed_checks"] == 0

    def test_aggregate_multiple_failing_results(self, aggregator):
        """Test aggregate() with multiple failing results."""
        results = [
            CheckResult("tests", False, "failed", [{"message": "Tests failed"}], [], {}, 5.0),
            CheckResult("linting", False, "failed", [{"message": "Linting failed"}], [], {}, 2.0),
        ]

        result = aggregator.aggregate(results)

        assert result["overall_passed"] is False
        assert result["total_checks"] == 2
        assert result["passed_checks"] == 0
        assert result["failed_checks"] == 2
        assert len(result["failed_checkers"]) == 2
        assert "tests" in result["failed_checkers"]
        assert "linting" in result["failed_checkers"]


class TestResultAggregatorByChecker:
    """Tests for by_checker mapping."""

    def test_aggregate_creates_by_checker_mapping(self, aggregator, passing_check_result):
        """Test aggregate() creates by_checker mapping."""
        result = aggregator.aggregate([passing_check_result])

        assert "tests" in result["by_checker"]
        checker_result = result["by_checker"]["tests"]
        assert checker_result["passed"] is True
        assert checker_result["status"] == "passed"

    def test_aggregate_includes_all_result_fields(self, aggregator, passing_check_result):
        """Test aggregate() includes all CheckResult fields in by_checker."""
        result = aggregator.aggregate([passing_check_result])

        checker_result = result["by_checker"]["tests"]
        assert "passed" in checker_result
        assert "status" in checker_result
        assert "errors" in checker_result
        assert "warnings" in checker_result
        assert "info" in checker_result
        assert "execution_time" in checker_result

    def test_aggregate_preserves_errors_list(self, aggregator, failing_check_result):
        """Test aggregate() preserves errors list."""
        result = aggregator.aggregate([failing_check_result])

        checker_result = result["by_checker"]["linting"]
        assert len(checker_result["errors"]) == 1
        assert checker_result["errors"][0]["message"] == "Linting issues found"

    def test_aggregate_preserves_warnings_list(self, aggregator):
        """Test aggregate() preserves warnings list."""
        check_result = CheckResult(
            "custom",
            True,
            "passed",
            [],
            [{"message": "Optional check failed"}],
            {},
            1.0,
        )

        result = aggregator.aggregate([check_result])

        checker_result = result["by_checker"]["custom"]
        assert len(checker_result["warnings"]) == 1
        assert checker_result["warnings"][0]["message"] == "Optional check failed"

    def test_aggregate_preserves_info_dict(self, aggregator, passing_check_result):
        """Test aggregate() preserves info dictionary."""
        result = aggregator.aggregate([passing_check_result])

        checker_result = result["by_checker"]["tests"]
        assert "coverage" in checker_result["info"]
        assert checker_result["info"]["coverage"] == 85.0

    def test_aggregate_handles_multiple_checkers(self, aggregator):
        """Test aggregate() handles multiple different checkers."""
        results = [
            CheckResult("tests", True, "passed", [], [], {}, 5.0),
            CheckResult("linting", True, "passed", [], [], {}, 2.0),
            CheckResult("security", True, "passed", [], [], {}, 3.0),
        ]

        result = aggregator.aggregate(results)

        assert len(result["by_checker"]) == 3
        assert "tests" in result["by_checker"]
        assert "linting" in result["by_checker"]
        assert "security" in result["by_checker"]


class TestResultAggregatorExecutionTime:
    """Tests for execution time aggregation."""

    def test_aggregate_sums_execution_times(self, aggregator):
        """Test aggregate() sums execution times."""
        results = [
            CheckResult("tests", True, "passed", [], [], {}, 5.2),
            CheckResult("linting", True, "passed", [], [], {}, 2.3),
            CheckResult("security", True, "passed", [], [], {}, 3.1),
        ]

        result = aggregator.aggregate(results)

        expected_time = 5.2 + 2.3 + 3.1
        assert abs(result["total_execution_time"] - expected_time) < 0.0001

    def test_aggregate_includes_individual_execution_times(self, aggregator):
        """Test aggregate() includes individual execution times."""
        results = [
            CheckResult("tests", True, "passed", [], [], {}, 5.2),
            CheckResult("linting", True, "passed", [], [], {}, 2.3),
        ]

        result = aggregator.aggregate(results)

        assert result["by_checker"]["tests"]["execution_time"] == 5.2
        assert result["by_checker"]["linting"]["execution_time"] == 2.3

    def test_aggregate_handles_zero_execution_time(self, aggregator, skipped_check_result):
        """Test aggregate() handles zero execution time."""
        result = aggregator.aggregate([skipped_check_result])

        assert result["total_execution_time"] == 0.0
        assert result["by_checker"]["security"]["execution_time"] == 0.0


class TestResultAggregatorGetSummaryText:
    """Tests for ResultAggregator.get_summary_text() method."""

    def test_get_summary_text_returns_string(self, aggregator):
        """Test get_summary_text() returns a string."""
        aggregated = {
            "overall_passed": True,
            "total_checks": 3,
            "passed_checks": 3,
            "failed_checks": 0,
            "skipped_checks": 0,
            "total_execution_time": 10.5,
            "by_checker": {},
            "failed_checkers": [],
        }

        summary = aggregator.get_summary_text(aggregated)

        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_get_summary_text_includes_counts(self, aggregator):
        """Test get_summary_text() includes all counts."""
        aggregated = {
            "overall_passed": True,
            "total_checks": 5,
            "passed_checks": 4,
            "failed_checks": 0,
            "skipped_checks": 1,
            "total_execution_time": 10.5,
            "by_checker": {},
            "failed_checkers": [],
        }

        summary = aggregator.get_summary_text(aggregated)

        assert "Total Checks: 5" in summary
        assert "Passed: 4" in summary
        assert "Failed: 0" in summary
        assert "Skipped: 1" in summary

    def test_get_summary_text_includes_execution_time(self, aggregator):
        """Test get_summary_text() includes execution time."""
        aggregated = {
            "overall_passed": True,
            "total_checks": 3,
            "passed_checks": 3,
            "failed_checks": 0,
            "skipped_checks": 0,
            "total_execution_time": 12.34,
            "by_checker": {},
            "failed_checkers": [],
        }

        summary = aggregator.get_summary_text(aggregated)

        assert "Execution Time: 12.34s" in summary

    def test_get_summary_text_shows_passed_message(self, aggregator):
        """Test get_summary_text() shows passed message."""
        aggregated = {
            "overall_passed": True,
            "total_checks": 3,
            "passed_checks": 3,
            "failed_checks": 0,
            "skipped_checks": 0,
            "total_execution_time": 10.5,
            "by_checker": {},
            "failed_checkers": [],
        }

        summary = aggregator.get_summary_text(aggregated)

        assert "All quality checks passed" in summary

    def test_get_summary_text_shows_failed_message(self, aggregator):
        """Test get_summary_text() shows failed message with checker names."""
        aggregated = {
            "overall_passed": False,
            "total_checks": 3,
            "passed_checks": 1,
            "failed_checks": 2,
            "skipped_checks": 0,
            "total_execution_time": 10.5,
            "by_checker": {},
            "failed_checkers": ["tests", "linting"],
        }

        summary = aggregator.get_summary_text(aggregated)

        assert "Quality checks failed" in summary
        assert "tests" in summary
        assert "linting" in summary

    def test_get_summary_text_multiline_format(self, aggregator):
        """Test get_summary_text() uses multiline format."""
        aggregated = {
            "overall_passed": True,
            "total_checks": 3,
            "passed_checks": 3,
            "failed_checks": 0,
            "skipped_checks": 0,
            "total_execution_time": 10.5,
            "by_checker": {},
            "failed_checkers": [],
        }

        summary = aggregator.get_summary_text(aggregated)

        lines = summary.split("\n")
        assert len(lines) >= 5  # Should have multiple lines


class TestResultAggregatorEdgeCases:
    """Tests for edge cases."""

    def test_aggregate_handles_empty_errors_list(self, aggregator):
        """Test aggregate() handles empty errors list."""
        result_with_no_errors = CheckResult("tests", True, "passed", [], [], {}, 5.0)

        result = aggregator.aggregate([result_with_no_errors])

        assert result["by_checker"]["tests"]["errors"] == []

    def test_aggregate_handles_empty_warnings_list(self, aggregator):
        """Test aggregate() handles empty warnings list."""
        result_with_no_warnings = CheckResult("tests", True, "passed", [], [], {}, 5.0)

        result = aggregator.aggregate([result_with_no_warnings])

        assert result["by_checker"]["tests"]["warnings"] == []

    def test_aggregate_handles_empty_info_dict(self, aggregator):
        """Test aggregate() handles empty info dict."""
        result_with_no_info = CheckResult("tests", True, "passed", [], [], {}, 5.0)

        result = aggregator.aggregate([result_with_no_info])

        assert result["by_checker"]["tests"]["info"] == {}

    def test_aggregate_handles_string_errors(self, aggregator):
        """Test aggregate() handles errors as strings."""
        result_with_string_errors = CheckResult(
            "tests", False, "failed", ["Error message"], [], {}, 5.0
        )

        result = aggregator.aggregate([result_with_string_errors])

        assert result["by_checker"]["tests"]["errors"] == ["Error message"]

    def test_aggregate_handles_dict_errors(self, aggregator):
        """Test aggregate() handles errors as dictionaries."""
        result_with_dict_errors = CheckResult(
            "tests",
            False,
            "failed",
            [{"message": "Error", "details": "More info"}],
            [],
            {},
            5.0,
        )

        result = aggregator.aggregate([result_with_dict_errors])

        errors = result["by_checker"]["tests"]["errors"]
        assert len(errors) == 1
        assert errors[0]["message"] == "Error"
        assert errors[0]["details"] == "More info"
