#!/usr/bin/env python3
"""
Console reporter for quality gate results.
"""

from __future__ import annotations

from typing import Any

from solokit.quality.reporters.base import Reporter


class ConsoleReporter(Reporter):
    """Generates human-readable console reports."""

    def generate(self, aggregated_results: dict[str, Any]) -> str:
        """Generate a console-friendly report.

        Args:
            aggregated_results: Aggregated results from ResultAggregator

        Returns:
            Formatted console report
        """
        report = []
        report.append("=" * 60)
        report.append("QUALITY GATE RESULTS")
        report.append("=" * 60)

        # Overall summary
        if aggregated_results["overall_passed"]:
            report.append("\n✓ ALL CHECKS PASSED")
        else:
            report.append("\n✗ SOME CHECKS FAILED")

        report.append(f"\nTotal Checks: {aggregated_results['total_checks']}")
        report.append(f"Passed: {aggregated_results['passed_checks']}")
        report.append(f"Failed: {aggregated_results['failed_checks']}")
        report.append(f"Skipped: {aggregated_results['skipped_checks']}")
        report.append(f"Execution Time: {aggregated_results['total_execution_time']:.2f}s")

        # Individual checker results
        report.append("\n" + "-" * 60)
        report.append("INDIVIDUAL CHECKER RESULTS")
        report.append("-" * 60)

        for checker_name, result in aggregated_results["by_checker"].items():
            status = result["status"]
            if status == "passed":
                status_symbol = "✓"
            elif status == "skipped":
                status_symbol = "⊘"
            else:
                status_symbol = "✗"

            report.append(f"\n{status_symbol} {checker_name.upper()}: {status.upper()}")

            # Add execution time
            if result.get("execution_time", 0) > 0:
                report.append(f"  Execution time: {result['execution_time']:.2f}s")

            # Show errors
            if result.get("errors"):
                report.append("  Errors:")
                for error in result["errors"][:5]:  # Limit to first 5
                    if isinstance(error, dict):
                        error_msg = error.get("message", str(error))
                    else:
                        error_msg = str(error)
                    report.append(f"    - {error_msg}")
                if len(result["errors"]) > 5:
                    report.append(f"    ... and {len(result['errors']) - 5} more")

            # Show warnings
            if result.get("warnings"):
                report.append("  Warnings:")
                for warning in result["warnings"][:3]:  # Limit to first 3
                    if isinstance(warning, dict):
                        warning_msg = warning.get("message", str(warning))
                    else:
                        warning_msg = str(warning)
                    report.append(f"    - {warning_msg}")
                if len(result["warnings"]) > 3:
                    report.append(f"    ... and {len(result['warnings']) - 3} more")

            # Show key info
            if result.get("info"):
                info = result["info"]
                # Show coverage if present
                if "coverage" in info:
                    report.append(f"  Coverage: {info['coverage']}%")
                # Show reason for skipped
                if "reason" in info and status == "skipped":
                    report.append(f"  Reason: {info['reason']}")

        report.append("\n" + "=" * 60)

        return "\n".join(report)
