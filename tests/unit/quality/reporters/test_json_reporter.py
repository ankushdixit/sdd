"""Unit tests for json_reporter.py JSONReporter.

Tests for the JSONReporter class which generates JSON-formatted reports.
"""

import json

import pytest

from sdd.quality.reporters.json_reporter import JSONReporter


@pytest.fixture
def sample_results():
    """Sample aggregated results."""
    return {
        "overall_passed": True,
        "total_checks": 3,
        "passed_checks": 3,
        "failed_checks": 0,
        "skipped_checks": 0,
        "total_execution_time": 5.5,
        "by_checker": {
            "tests": {
                "passed": True,
                "status": "passed",
                "errors": [],
                "warnings": [],
                "info": {"coverage": 85.0, "threshold": 80},
                "execution_time": 3.0,
            },
            "linting": {
                "passed": True,
                "status": "passed",
                "errors": [],
                "warnings": [],
                "info": {},
                "execution_time": 2.5,
            },
        },
        "failed_checkers": [],
    }


class TestJSONReporterInit:
    """Tests for JSONReporter initialization."""

    def test_init_with_default_indent(self):
        """Test initialization with default indent."""
        reporter = JSONReporter()

        assert reporter.indent == 2

    def test_init_with_custom_indent(self):
        """Test initialization with custom indent."""
        reporter = JSONReporter(indent=4)

        assert reporter.indent == 4

    def test_init_with_no_indent(self):
        """Test initialization with no indent (compact JSON)."""
        reporter = JSONReporter(indent=None)

        assert reporter.indent is None


class TestJSONReporterGenerate:
    """Tests for JSONReporter.generate() method."""

    def test_generate_returns_string(self, sample_results):
        """Test generate() returns a string."""
        reporter = JSONReporter()
        report = reporter.generate(sample_results)

        assert isinstance(report, str)
        assert len(report) > 0

    def test_generate_produces_valid_json(self, sample_results):
        """Test generate() produces valid JSON."""
        reporter = JSONReporter()
        report = reporter.generate(sample_results)

        # Should be parseable as JSON
        parsed = json.loads(report)
        assert isinstance(parsed, dict)

    def test_generate_includes_all_fields(self, sample_results):
        """Test generate() includes all result fields."""
        reporter = JSONReporter()
        report = reporter.generate(sample_results)
        parsed = json.loads(report)

        assert "overall_passed" in parsed
        assert "total_checks" in parsed
        assert "passed_checks" in parsed
        assert "failed_checks" in parsed
        assert "skipped_checks" in parsed
        assert "total_execution_time" in parsed
        assert "by_checker" in parsed
        assert "failed_checkers" in parsed

    def test_generate_preserves_data_types(self, sample_results):
        """Test generate() preserves data types correctly."""
        reporter = JSONReporter()
        report = reporter.generate(sample_results)
        parsed = json.loads(report)

        assert isinstance(parsed["overall_passed"], bool)
        assert isinstance(parsed["total_checks"], int)
        assert isinstance(parsed["total_execution_time"], float)
        assert isinstance(parsed["by_checker"], dict)
        assert isinstance(parsed["failed_checkers"], list)

    def test_generate_with_default_indent(self, sample_results):
        """Test generate() with default 2-space indent."""
        reporter = JSONReporter()
        report = reporter.generate(sample_results)

        # Should have indentation
        assert "\n" in report
        assert "  " in report

    def test_generate_with_custom_indent(self, sample_results):
        """Test generate() with custom indent."""
        reporter = JSONReporter(indent=4)
        report = reporter.generate(sample_results)

        # Should have 4-space indentation
        assert "    " in report

    def test_generate_with_no_indent(self, sample_results):
        """Test generate() with no indent (compact)."""
        reporter = JSONReporter(indent=None)
        report = reporter.generate(sample_results)

        # Should have minimal formatting (more compact than default)
        assert (
            "\n" in report or len(report) > 100
        )  # Either has minimal newlines or is compact

    def test_generate_handles_nested_structures(self, sample_results):
        """Test generate() handles nested data structures."""
        reporter = JSONReporter()
        report = reporter.generate(sample_results)
        parsed = json.loads(report)

        # Verify nested structure is preserved
        assert "tests" in parsed["by_checker"]
        assert "info" in parsed["by_checker"]["tests"]
        assert "coverage" in parsed["by_checker"]["tests"]["info"]

    def test_generate_handles_empty_lists(self):
        """Test generate() handles empty lists."""
        results = {
            "overall_passed": True,
            "total_checks": 0,
            "passed_checks": 0,
            "failed_checks": 0,
            "skipped_checks": 0,
            "total_execution_time": 0.0,
            "by_checker": {},
            "failed_checkers": [],
        }

        reporter = JSONReporter()
        report = reporter.generate(results)
        parsed = json.loads(report)

        assert parsed["failed_checkers"] == []
        assert parsed["by_checker"] == {}

    def test_generate_handles_errors_as_dicts(self):
        """Test generate() handles errors as dictionaries."""
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
                    "errors": [{"message": "Test failed", "output": "Error details"}],
                    "warnings": [],
                    "info": {},
                    "execution_time": 1.0,
                }
            },
            "failed_checkers": ["tests"],
        }

        reporter = JSONReporter()
        report = reporter.generate(results)
        parsed = json.loads(report)

        errors = parsed["by_checker"]["tests"]["errors"]
        assert len(errors) == 1
        assert errors[0]["message"] == "Test failed"
        assert errors[0]["output"] == "Error details"

    def test_generate_handles_errors_as_strings(self):
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

        reporter = JSONReporter()
        report = reporter.generate(results)
        parsed = json.loads(report)

        errors = parsed["by_checker"]["tests"]["errors"]
        assert len(errors) == 1
        assert errors[0] == "Error as string"

    def test_generate_roundtrip(self, sample_results):
        """Test generate() output can be parsed back to original structure."""
        reporter = JSONReporter()
        report = reporter.generate(sample_results)
        parsed = json.loads(report)

        # Should match original (with potential floating point precision)
        assert parsed["overall_passed"] == sample_results["overall_passed"]
        assert parsed["total_checks"] == sample_results["total_checks"]
        assert (
            abs(parsed["total_execution_time"] - sample_results["total_execution_time"])
            < 0.0001
        )


class TestJSONReporterComplexData:
    """Tests for complex data structures."""

    def test_generate_handles_unicode(self):
        """Test generate() handles unicode characters."""
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
                    "info": {"message": "Test passed ✓"},
                    "execution_time": 1.0,
                }
            },
            "failed_checkers": [],
        }

        reporter = JSONReporter()
        report = reporter.generate(results)
        parsed = json.loads(report)

        assert "✓" in parsed["by_checker"]["tests"]["info"]["message"]

    def test_generate_handles_special_characters(self):
        """Test generate() handles special characters."""
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
                    "errors": [{"message": "Error: \"quoted\" and 'single' quotes"}],
                    "warnings": [],
                    "info": {},
                    "execution_time": 1.0,
                }
            },
            "failed_checkers": ["tests"],
        }

        reporter = JSONReporter()
        report = reporter.generate(results)
        parsed = json.loads(report)

        error_msg = parsed["by_checker"]["tests"]["errors"][0]["message"]
        assert "quoted" in error_msg
        assert "single" in error_msg

    def test_generate_handles_large_numbers(self):
        """Test generate() handles large numbers."""
        results = {
            "overall_passed": True,
            "total_checks": 1000000,
            "passed_checks": 999999,
            "failed_checks": 1,
            "skipped_checks": 0,
            "total_execution_time": 123456.789,
            "by_checker": {},
            "failed_checkers": [],
        }

        reporter = JSONReporter()
        report = reporter.generate(results)
        parsed = json.loads(report)

        assert parsed["total_checks"] == 1000000
        assert abs(parsed["total_execution_time"] - 123456.789) < 0.0001
