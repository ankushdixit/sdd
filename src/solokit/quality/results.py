#!/usr/bin/env python3
"""
Result aggregation for quality gates.

Combines results from multiple checkers into a comprehensive report.
"""

from __future__ import annotations

from typing import Any

from solokit.quality.checkers.base import CheckResult


class ResultAggregator:
    """Aggregates results from multiple quality checkers."""

    def aggregate(self, results: list[CheckResult]) -> dict[str, Any]:
        """Aggregate multiple check results into a summary.

        Args:
            results: List of CheckResult objects from various checkers

        Returns:
            Dictionary containing aggregated results with:
                - overall_passed: Whether all checks passed
                - total_checks: Number of checks run
                - passed_checks: Number of checks that passed
                - failed_checks: Number of checks that failed
                - skipped_checks: Number of checks that were skipped
                - by_checker: Results organized by checker name
                - failed_checkers: List of checker names that failed
        """
        aggregated: dict[str, Any] = {
            "overall_passed": True,
            "total_checks": len(results),
            "passed_checks": 0,
            "failed_checks": 0,
            "skipped_checks": 0,
            "by_checker": {},
            "failed_checkers": [],
            "total_execution_time": 0.0,
        }

        for result in results:
            # Add to by_checker mapping
            aggregated["by_checker"][result.checker_name] = {
                "passed": result.passed,
                "status": result.status,
                "errors": result.errors,
                "warnings": result.warnings,
                "info": result.info,
                "execution_time": result.execution_time,
            }

            # Update counters
            if result.status == "skipped":
                aggregated["skipped_checks"] += 1
            elif result.passed:
                aggregated["passed_checks"] += 1
            else:
                aggregated["failed_checks"] += 1
                aggregated["overall_passed"] = False
                aggregated["failed_checkers"].append(result.checker_name)

            # Add execution time
            aggregated["total_execution_time"] += result.execution_time

        return aggregated

    def get_summary_text(self, aggregated: dict[str, Any]) -> str:
        """Generate a text summary of aggregated results.

        Args:
            aggregated: Aggregated results dictionary

        Returns:
            Human-readable summary string
        """
        total = aggregated["total_checks"]
        passed = aggregated["passed_checks"]
        failed = aggregated["failed_checks"]
        skipped = aggregated["skipped_checks"]
        exec_time = aggregated["total_execution_time"]

        summary = []
        summary.append(f"Total Checks: {total}")
        summary.append(f"Passed: {passed}")
        summary.append(f"Failed: {failed}")
        summary.append(f"Skipped: {skipped}")
        summary.append(f"Execution Time: {exec_time:.2f}s")

        if aggregated["overall_passed"]:
            summary.append("\n✓ All quality checks passed")
        else:
            summary.append(f"\n✗ Quality checks failed: {', '.join(aggregated['failed_checkers'])}")

        return "\n".join(summary)
