"""Unit tests for console.py ConsoleReporter.

Tests for the ConsoleReporter class which generates human-readable console reports.
"""

import pytest

from solokit.quality.reporters.console import ConsoleReporter


@pytest.fixture
def reporter():
    """Create a ConsoleReporter instance."""
    return ConsoleReporter()


@pytest.fixture
def passing_results():
    """Sample passing aggregated results."""
    return {
        "overall_passed": True,
        "total_checks": 5,
        "passed_checks": 5,
        "failed_checks": 0,
        "skipped_checks": 0,
        "total_execution_time": 10.5,
        "by_checker": {
            "tests": {
                "passed": True,
                "status": "passed",
                "errors": [],
                "warnings": [],
                "info": {"coverage": 85.5, "threshold": 80},
                "execution_time": 5.2,
            },
            "linting": {
                "passed": True,
                "status": "passed",
                "errors": [],
                "warnings": [],
                "info": {},
                "execution_time": 2.3,
            },
            "security": {
                "passed": True,
                "status": "passed",
                "errors": [],
                "warnings": [],
                "info": {"by_severity": {}},
                "execution_time": 3.0,
            },
        },
        "failed_checkers": [],
    }


@pytest.fixture
def failing_results():
    """Sample failing aggregated results."""
    return {
        "overall_passed": False,
        "total_checks": 5,
        "passed_checks": 3,
        "failed_checks": 2,
        "skipped_checks": 0,
        "total_execution_time": 12.3,
        "by_checker": {
            "tests": {
                "passed": False,
                "status": "failed",
                "errors": [
                    {"message": "Tests failed with exit code 1"},
                    {"message": "Coverage 75% below threshold 80%"},
                ],
                "warnings": [],
                "info": {"coverage": 75.0, "threshold": 80},
                "execution_time": 6.1,
            },
            "linting": {
                "passed": False,
                "status": "failed",
                "errors": [
                    {
                        "message": "Linting found 5 issue(s)",
                        "output": "file1.py:10: E501 line too long",
                    }
                ],
                "warnings": [],
                "info": {},
                "execution_time": 3.2,
            },
            "formatting": {
                "passed": True,
                "status": "passed",
                "errors": [],
                "warnings": [],
                "info": {},
                "execution_time": 3.0,
            },
        },
        "failed_checkers": ["tests", "linting"],
    }


@pytest.fixture
def skipped_results():
    """Sample results with skipped checks."""
    return {
        "overall_passed": True,
        "total_checks": 3,
        "passed_checks": 2,
        "failed_checks": 0,
        "skipped_checks": 1,
        "total_execution_time": 5.0,
        "by_checker": {
            "tests": {
                "passed": True,
                "status": "passed",
                "errors": [],
                "warnings": [],
                "info": {},
                "execution_time": 3.0,
            },
            "linting": {
                "passed": True,
                "status": "skipped",
                "errors": [],
                "warnings": [],
                "info": {"reason": "linting tool not available"},
                "execution_time": 0.0,
            },
            "formatting": {
                "passed": True,
                "status": "passed",
                "errors": [],
                "warnings": [],
                "info": {},
                "execution_time": 2.0,
            },
        },
        "failed_checkers": [],
    }


class TestConsoleReporterGenerate:
    """Tests for ConsoleReporter.generate() method."""

    def test_generate_returns_string(self, reporter, passing_results):
        """Test generate() returns a string."""
        report = reporter.generate(passing_results)

        assert isinstance(report, str)
        assert len(report) > 0

    def test_generate_includes_header(self, reporter, passing_results):
        """Test generate() includes report header."""
        report = reporter.generate(passing_results)

        assert "QUALITY GATE RESULTS" in report
        assert "=" in report

    def test_generate_shows_overall_passed(self, reporter, passing_results):
        """Test generate() shows overall passed status."""
        report = reporter.generate(passing_results)

        assert "ALL CHECKS PASSED" in report

    def test_generate_shows_overall_failed(self, reporter, failing_results):
        """Test generate() shows overall failed status."""
        report = reporter.generate(failing_results)

        assert "SOME CHECKS FAILED" in report

    def test_generate_includes_summary_counts(self, reporter, passing_results):
        """Test generate() includes summary counts."""
        report = reporter.generate(passing_results)

        assert "Total Checks: 5" in report
        assert "Passed: 5" in report
        assert "Failed: 0" in report
        assert "Skipped: 0" in report

    def test_generate_includes_execution_time(self, reporter, passing_results):
        """Test generate() includes total execution time."""
        report = reporter.generate(passing_results)

        assert "Execution Time: 10.50s" in report

    def test_generate_includes_individual_checker_results(self, reporter, passing_results):
        """Test generate() includes individual checker results."""
        report = reporter.generate(passing_results)

        assert "INDIVIDUAL CHECKER RESULTS" in report
        assert "TESTS" in report
        assert "LINTING" in report
        assert "SECURITY" in report


class TestConsoleReporterCheckerStatus:
    """Tests for checker status display."""

    def test_generate_shows_passed_symbol(self, reporter, passing_results):
        """Test generate() shows checkmark for passed checks."""
        report = reporter.generate(passing_results)

        # Should have checkmarks for passed tests
        assert "✓" in report

    def test_generate_shows_failed_symbol(self, reporter, failing_results):
        """Test generate() shows X for failed checks."""
        report = reporter.generate(failing_results)

        # Should have X marks for failed tests
        assert "✗" in report

    def test_generate_shows_skipped_symbol(self, reporter, skipped_results):
        """Test generate() shows special symbol for skipped checks."""
        report = reporter.generate(skipped_results)

        # Should have skip symbol for skipped tests
        assert "⊘" in report

    def test_generate_includes_checker_execution_time(self, reporter, passing_results):
        """Test generate() includes individual checker execution times."""
        report = reporter.generate(passing_results)

        assert "Execution time: 5.20s" in report  # tests
        assert "Execution time: 2.30s" in report  # linting


class TestConsoleReporterErrors:
    """Tests for error display."""

    def test_generate_shows_errors(self, reporter, failing_results):
        """Test generate() shows error messages."""
        report = reporter.generate(failing_results)

        assert "Errors:" in report
        assert "Tests failed with exit code 1" in report
        assert "Coverage 75% below threshold 80%" in report

    def test_generate_limits_error_count(self, reporter):
        """Test generate() limits number of errors displayed."""
        results = {
            "overall_passed": False,
            "total_checks": 1,
            "passed_checks": 0,
            "failed_checks": 1,
            "skipped_checks": 0,
            "total_execution_time": 1.0,
            "by_checker": {
                "tests": {
                    "passed": False,
                    "status": "failed",
                    "errors": [{"message": f"Error {i}"} for i in range(10)],
                    "warnings": [],
                    "info": {},
                    "execution_time": 1.0,
                }
            },
            "failed_checkers": ["tests"],
        }

        report = reporter.generate(results)

        # Should show first 5 errors plus "... and N more"
        assert "... and 5 more" in report

    def test_generate_handles_string_errors(self, reporter):
        """Test generate() handles errors as strings."""
        results = {
            "overall_passed": False,
            "total_checks": 1,
            "passed_checks": 0,
            "failed_checks": 1,
            "skipped_checks": 0,
            "total_execution_time": 1.0,
            "by_checker": {
                "tests": {
                    "passed": False,
                    "status": "failed",
                    "errors": ["Error as string"],
                    "warnings": [],
                    "info": {},
                    "execution_time": 1.0,
                }
            },
            "failed_checkers": ["tests"],
        }

        report = reporter.generate(results)

        assert "Error as string" in report


class TestConsoleReporterWarnings:
    """Tests for warning display."""

    def test_generate_shows_warnings(self, reporter):
        """Test generate() shows warning messages."""
        results = {
            "overall_passed": True,
            "total_checks": 1,
            "passed_checks": 1,
            "failed_checks": 0,
            "skipped_checks": 0,
            "total_execution_time": 1.0,
            "by_checker": {
                "custom": {
                    "passed": True,
                    "status": "passed",
                    "errors": [],
                    "warnings": [{"message": "Optional validation failed"}],
                    "info": {},
                    "execution_time": 1.0,
                }
            },
            "failed_checkers": [],
        }

        report = reporter.generate(results)

        assert "Warnings:" in report
        assert "Optional validation failed" in report

    def test_generate_limits_warning_count(self, reporter):
        """Test generate() limits number of warnings displayed."""
        results = {
            "overall_passed": True,
            "total_checks": 1,
            "passed_checks": 1,
            "failed_checks": 0,
            "skipped_checks": 0,
            "total_execution_time": 1.0,
            "by_checker": {
                "custom": {
                    "passed": True,
                    "status": "passed",
                    "errors": [],
                    "warnings": [{"message": f"Warning {i}"} for i in range(10)],
                    "info": {},
                    "execution_time": 1.0,
                }
            },
            "failed_checkers": [],
        }

        report = reporter.generate(results)

        # Should show first 3 warnings plus "... and N more"
        assert "... and 7 more" in report


class TestConsoleReporterInfo:
    """Tests for info display."""

    def test_generate_shows_coverage_info(self, reporter, passing_results):
        """Test generate() shows coverage percentage."""
        report = reporter.generate(passing_results)

        assert "Coverage: 85.5%" in report

    def test_generate_shows_skip_reason(self, reporter, skipped_results):
        """Test generate() shows reason for skipped checks."""
        report = reporter.generate(skipped_results)

        assert "Reason: linting tool not available" in report

    def test_generate_handles_missing_info_fields(self, reporter):
        """Test generate() handles missing info fields gracefully."""
        results = {
            "overall_passed": True,
            "total_checks": 1,
            "passed_checks": 1,
            "failed_checks": 0,
            "skipped_checks": 0,
            "total_execution_time": 1.0,
            "by_checker": {
                "tests": {
                    "passed": True,
                    "status": "passed",
                    "errors": [],
                    "warnings": [],
                    "info": {},  # No coverage info
                    "execution_time": 1.0,
                }
            },
            "failed_checkers": [],
        }

        # Should not raise an exception
        report = reporter.generate(results)

        assert isinstance(report, str)


class TestConsoleReporterFormatting:
    """Tests for report formatting."""

    def test_generate_uses_consistent_dividers(self, reporter, passing_results):
        """Test generate() uses consistent dividers."""
        report = reporter.generate(passing_results)

        # Should have main dividers
        assert "=" * 60 in report
        assert "-" * 60 in report

    def test_generate_formats_multiline_output(self, reporter, passing_results):
        """Test generate() formats output correctly."""
        report = reporter.generate(passing_results)

        lines = report.split("\n")
        # Should have multiple lines
        assert len(lines) > 10

    def test_generate_indents_details(self, reporter, failing_results):
        """Test generate() indents checker details."""
        report = reporter.generate(failing_results)

        # Error details should be indented
        assert "  Errors:" in report or "    -" in report
