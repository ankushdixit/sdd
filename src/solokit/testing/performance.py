#!/usr/bin/env python3
"""
Performance benchmarking system for integration tests.

Tracks:
- Response times (p50, p95, p99)
- Throughput (requests/second)
- Resource utilization (CPU, memory)
- Regression detection
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from solokit.core.command_runner import CommandRunner
from solokit.core.constants import (
    GIT_QUICK_TIMEOUT,
    HTTP_REQUEST_TIMEOUT,
    PERFORMANCE_REGRESSION_THRESHOLD,
    PERFORMANCE_TEST_TIMEOUT,
)
from solokit.core.error_handlers import convert_subprocess_errors, log_errors
from solokit.core.exceptions import (
    BenchmarkFailedError,
    LoadTestFailedError,
    PerformanceRegressionError,
    PerformanceTestError,
    ValidationError,
    WorkItemNotFoundError,
)
from solokit.core.file_ops import load_json, save_json
from solokit.core.output import get_output

logger = logging.getLogger(__name__)
output = get_output()


class PerformanceBenchmark:
    """Performance benchmarking for integration tests."""

    def __init__(self, work_item: dict):
        """
        Initialize performance benchmark.

        Args:
            work_item: Integration test work item with performance requirements

        Raises:
            ValidationError: If work_item is invalid or missing required fields
        """
        if not work_item:
            raise ValidationError(
                message="Work item cannot be None or empty",
                context={"work_item": work_item},
                remediation="Provide a valid work item dictionary",
            )

        self.work_item = work_item
        self.benchmarks = work_item.get("performance_benchmarks", {})
        self.baselines_file = Path(".session/tracking/performance_baselines.json")
        self.results: dict[str, Any] = {}
        self.runner = CommandRunner(default_timeout=300)  # Long timeout for perf tests

    @log_errors()
    def run_benchmarks(self, test_endpoint: str | None = None) -> tuple[bool, dict[str, Any]]:
        """
        Run performance benchmarks.

        Args:
            test_endpoint: Endpoint to benchmark (if None, uses work item config)

        Returns:
            (passed: bool, results: dict)

        Raises:
            LoadTestFailedError: If load test fails
            PerformanceTestError: If benchmark execution fails
            BenchmarkFailedError: If benchmarks don't meet requirements
            PerformanceRegressionError: If regression is detected
        """
        logger.info("Running performance benchmarks...")

        if test_endpoint is None:
            test_endpoint = self.benchmarks.get("endpoint", "http://localhost:8000/health")

        # Run load test
        load_test_results = self._run_load_test(test_endpoint)
        self.results["load_test"] = load_test_results

        # Measure resource utilization
        resource_usage = self._measure_resource_usage()
        self.results["resource_usage"] = resource_usage

        # Compare against baselines
        passed = self._check_against_requirements()
        regression_detected = self._check_for_regression()

        self.results["passed"] = passed
        self.results["regression_detected"] = regression_detected

        # Store as new baseline if passed
        if passed and not regression_detected:
            self._store_baseline()

        return passed and not regression_detected, self.results

    @log_errors()
    @convert_subprocess_errors
    def _run_load_test(self, endpoint: str) -> dict[str, Any]:
        """
        Run load test using wrk or similar tool.

        Args:
            endpoint: URL to test

        Returns:
            Load test results dict

        Raises:
            LoadTestFailedError: If load test fails
            ValidationError: If endpoint is invalid
        """
        if not endpoint:
            raise ValidationError(
                message="Endpoint cannot be empty",
                context={"endpoint": endpoint},
                remediation="Provide a valid endpoint URL",
            )

        duration = self.benchmarks.get("load_test_duration", 60)
        threads = self.benchmarks.get("threads", 4)
        connections = self.benchmarks.get("connections", 100)

        try:
            # Using wrk for load testing
            result = self.runner.run(
                [
                    "wrk",
                    "-t",
                    str(threads),
                    "-c",
                    str(connections),
                    "-d",
                    f"{duration}s",
                    "--latency",
                    endpoint,
                ],
                timeout=duration + 30,
            )

            if result.success:
                # Parse wrk output
                return self._parse_wrk_output(result.stdout)
            else:
                # wrk not installed, try using Python requests as fallback
                logger.info("wrk not available, using fallback load test")
                return self._run_simple_load_test(endpoint, duration)

        except Exception as e:
            raise LoadTestFailedError(
                endpoint=endpoint,
                details=str(e),
                context={"duration": duration, "threads": threads, "connections": connections},
            ) from e

    def _parse_wrk_output(self, output: str) -> dict[str, Any]:
        """
        Parse wrk output to extract metrics.

        Args:
            output: Raw wrk output

        Returns:
            Parsed metrics dictionary

        Raises:
            PerformanceTestError: If parsing fails
        """
        results: dict[str, Any] = {"latency": {}, "throughput": {}}

        try:
            lines = output.split("\n")

            for line in lines:
                # Match percentile lines more precisely - look for lines starting with whitespace + percentage
                line_stripped = line.strip()
                if line_stripped.startswith("50.000%") or line_stripped.startswith("50%"):
                    # p50 latency
                    parts = line.split()
                    results["latency"]["p50"] = self._parse_latency(parts[-1])
                elif line_stripped.startswith("75.000%") or line_stripped.startswith("75%"):
                    results["latency"]["p75"] = self._parse_latency(parts[-1])
                elif line_stripped.startswith("90.000%") or line_stripped.startswith("90%"):
                    results["latency"]["p90"] = self._parse_latency(parts[-1])
                elif line_stripped.startswith("99.000%") or line_stripped.startswith("99%"):
                    results["latency"]["p99"] = self._parse_latency(parts[-1])
                elif "Requests/sec:" in line:
                    parts = line.split()
                    results["throughput"]["requests_per_sec"] = float(parts[1])
                elif "Transfer/sec:" in line:
                    parts = line.split()
                    results["throughput"]["transfer_per_sec"] = parts[1]

            return results
        except (IndexError, ValueError) as e:
            raise PerformanceTestError(
                message="Failed to parse wrk output",
                context={"output": output[:500], "error": str(e)},
                remediation="Verify wrk is producing expected output format",
            ) from e

    def _parse_latency(self, latency_str: str) -> float:
        """
        Convert latency string (e.g., '1.23ms') to milliseconds.

        Args:
            latency_str: Latency string from wrk

        Returns:
            Latency in milliseconds

        Raises:
            PerformanceTestError: If parsing fails
        """
        try:
            latency_str = latency_str.strip()
            if "ms" in latency_str:  # milliseconds
                return float(latency_str.rstrip("ms"))
            elif "s" in latency_str:  # seconds
                return float(latency_str.rstrip("s")) * 1000
            return 0.0
        except (ValueError, AttributeError) as e:
            raise PerformanceTestError(
                message=f"Failed to parse latency value: {latency_str}",
                context={"latency_str": latency_str},
                remediation="Check wrk output format",
            ) from e

    def _run_simple_load_test(self, endpoint: str, duration: int) -> dict[str, Any]:
        """
        Fallback load test using Python requests.

        Args:
            endpoint: URL to test
            duration: Test duration in seconds

        Returns:
            Load test results dictionary

        Raises:
            LoadTestFailedError: If load test fails
        """
        import time

        import requests  # type: ignore[import-untyped]

        latencies = []
        start_time = time.time()
        request_count = 0

        logger.info("Using simple load test (wrk not available)...")

        try:
            while time.time() - start_time < duration:
                req_start = time.time()
                try:
                    requests.get(endpoint, timeout=HTTP_REQUEST_TIMEOUT)
                    latency = (time.time() - req_start) * 1000  # Convert to ms
                    latencies.append(latency)
                    request_count += 1
                except Exception:
                    # Individual request failures are logged but don't stop the test
                    logger.debug(f"Request to {endpoint} failed, continuing test")
                    pass

            total_duration = time.time() - start_time

            if not latencies:
                raise LoadTestFailedError(
                    endpoint=endpoint,
                    details="No successful requests during load test",
                    context={"duration": duration, "request_count": request_count},
                )

            latencies.sort()

            return {
                "latency": {
                    "p50": latencies[int(len(latencies) * 0.50)],
                    "p75": latencies[int(len(latencies) * 0.75)],
                    "p90": latencies[int(len(latencies) * 0.90)],
                    "p95": latencies[int(len(latencies) * 0.95)],
                    "p99": latencies[int(len(latencies) * 0.99)],
                },
                "throughput": {"requests_per_sec": request_count / total_duration},
            }
        except LoadTestFailedError:
            raise
        except Exception as e:
            raise LoadTestFailedError(
                endpoint=endpoint,
                details=f"Load test execution failed: {str(e)}",
                context={"duration": duration},
            ) from e

    @log_errors()
    @convert_subprocess_errors
    def _measure_resource_usage(self) -> dict[str, Any]:
        """
        Measure CPU and memory usage of services.

        Returns:
            Resource usage dictionary

        Raises:
            PerformanceTestError: If resource measurement fails
        """
        services = self.work_item.get("environment_requirements", {}).get("services_required", [])

        resource_usage = {}

        for service in services:
            try:
                # Get container ID
                result = self.runner.run(
                    ["docker-compose", "ps", "-q", service], timeout=GIT_QUICK_TIMEOUT
                )

                container_id = result.stdout.strip()
                if not container_id:
                    logger.warning(f"No container found for service: {service}")
                    continue

                # Get resource stats
                stats_result = self.runner.run(
                    [
                        "docker",
                        "stats",
                        container_id,
                        "--no-stream",
                        "--format",
                        "{{.CPUPerc}},{{.MemUsage}}",
                    ],
                    timeout=PERFORMANCE_TEST_TIMEOUT,
                )

                if stats_result.success:
                    parts = stats_result.stdout.strip().split(",")
                    resource_usage[service] = {
                        "cpu_percent": parts[0].rstrip("%"),
                        "memory_usage": parts[1],
                    }
                else:
                    logger.warning(
                        f"Failed to get stats for service {service}: {stats_result.stderr}"
                    )

            except Exception as e:
                logger.warning(f"Error measuring resource usage for {service}: {e}")
                resource_usage[service] = {"error": str(e)}

        return resource_usage

    def _check_against_requirements(self) -> bool:
        """
        Check if benchmarks meet requirements.

        Returns:
            True if all requirements met, False otherwise

        Raises:
            BenchmarkFailedError: If benchmarks fail to meet requirements
        """
        requirements = self.benchmarks.get("response_time", {})
        load_test = self.results.get("load_test", {})
        latency = load_test.get("latency", {})

        failed_benchmarks = []

        # Check response time requirements
        if "p50" in requirements:
            actual = latency.get("p50", float("inf"))
            expected = requirements["p50"]
            if actual > expected:
                logger.warning(f"p50 latency {actual}ms exceeds requirement {expected}ms")
                failed_benchmarks.append(
                    BenchmarkFailedError(metric="p50_latency", actual=actual, expected=expected)
                )

        if "p95" in requirements:
            actual = latency.get("p95", float("inf"))
            expected = requirements["p95"]
            if actual > expected:
                logger.warning(f"p95 latency {actual}ms exceeds requirement {expected}ms")
                failed_benchmarks.append(
                    BenchmarkFailedError(metric="p95_latency", actual=actual, expected=expected)
                )

        if "p99" in requirements:
            actual = latency.get("p99", float("inf"))
            expected = requirements["p99"]
            if actual > expected:
                logger.warning(f"p99 latency {actual}ms exceeds requirement {expected}ms")
                failed_benchmarks.append(
                    BenchmarkFailedError(metric="p99_latency", actual=actual, expected=expected)
                )

        # Check throughput requirements
        throughput_req = self.benchmarks.get("throughput", {})
        throughput = load_test.get("throughput", {})

        if "minimum" in throughput_req:
            actual_rps = throughput.get("requests_per_sec", 0)
            expected_rps = throughput_req["minimum"]
            if actual_rps < expected_rps:
                logger.warning(f"Throughput {actual_rps} req/s below minimum {expected_rps} req/s")
                failed_benchmarks.append(
                    BenchmarkFailedError(
                        metric="throughput", actual=actual_rps, expected=expected_rps, unit="req/s"
                    )
                )

        # If any benchmarks failed, raise the first one
        if failed_benchmarks:
            raise failed_benchmarks[0]

        return True

    def _check_for_regression(self) -> bool:
        """
        Check for performance regression against baseline.

        Returns:
            True if regression detected, False otherwise

        Raises:
            PerformanceRegressionError: If regression is detected
        """
        if not self.baselines_file.exists():
            logger.info("No baseline found, skipping regression check")
            return False

        try:
            baselines = load_json(self.baselines_file)
        except Exception as e:
            logger.warning(f"Failed to load baselines: {e}")
            return False

        work_item_id = self.work_item.get("id")
        if not work_item_id:
            logger.info("Work item has no id, skipping regression check")
            return False

        baseline = baselines.get(work_item_id)

        if not baseline:
            logger.info(f"No baseline for work item {work_item_id}")
            return False

        load_test = self.results.get("load_test", {})
        latency = load_test.get("latency", {})
        baseline_latency = baseline.get("latency", {})

        # Check for latency regression
        for percentile in ["p50", "p95", "p99"]:
            current = latency.get(percentile, 0)
            baseline_val = baseline_latency.get(percentile, 0)

            if baseline_val > 0 and current > baseline_val * PERFORMANCE_REGRESSION_THRESHOLD:
                regression_percent = (current / baseline_val - 1) * 100
                logger.warning(
                    f"Performance regression detected: {percentile} increased from "
                    f"{baseline_val}ms to {current}ms ({regression_percent:.1f}% slower)"
                )
                raise PerformanceRegressionError(
                    metric=percentile,
                    current=current,
                    baseline=baseline_val,
                    threshold_percent=(PERFORMANCE_REGRESSION_THRESHOLD - 1) * 100,
                )

        return False

    @log_errors()
    def _store_baseline(self) -> None:
        """
        Store current results as baseline.

        Raises:
            PerformanceTestError: If baseline storage fails
        """
        try:
            if not self.baselines_file.exists():
                baselines = {}
            else:
                baselines = load_json(self.baselines_file)

            work_item_id = self.work_item.get("id")
            if not work_item_id:
                raise PerformanceTestError(
                    message="Work item has no id, cannot store baseline",
                    context={"work_item": self.work_item},
                    remediation="Ensure work item has an 'id' field",
                )

            baselines[work_item_id] = {
                "latency": self.results.get("load_test", {}).get("latency", {}),
                "throughput": self.results.get("load_test", {}).get("throughput", {}),
                "resource_usage": self.results.get("resource_usage", {}),
                "timestamp": datetime.now().isoformat(),
                "session": self._get_current_session(),
            }

            save_json(self.baselines_file, baselines)
            logger.info(f"Baseline stored for work item {work_item_id}")
        except Exception as e:
            raise PerformanceTestError(
                message=f"Failed to store baseline for work item {work_item_id}",
                context={"work_item_id": work_item_id, "error": str(e)},
                remediation="Check file permissions and disk space",
            ) from e

    def _get_current_session(self) -> int:
        """
        Get current session number.

        Returns:
            Current session number or 0 if not found
        """
        status_file = Path(".session/tracking/status_update.json")
        if status_file.exists():
            try:
                status = load_json(status_file)
                session_num = status.get("session_number", 0)
                return int(session_num) if session_num is not None else 0
            except Exception as e:
                logger.warning(f"Failed to load session status: {e}")
                return 0
        return 0

    def generate_report(self) -> str:
        """
        Generate performance benchmark report.

        Returns:
            Formatted report string
        """
        load_test = self.results.get("load_test", {})
        latency = load_test.get("latency", {})
        throughput = load_test.get("throughput", {})

        report = f"""
Performance Benchmark Report
{"=" * 80}

Latency:
  p50: {latency.get("p50", "N/A")} ms
  p75: {latency.get("p75", "N/A")} ms
  p90: {latency.get("p90", "N/A")} ms
  p95: {latency.get("p95", "N/A")} ms
  p99: {latency.get("p99", "N/A")} ms

Throughput:
  Requests/sec: {throughput.get("requests_per_sec", "N/A")}

Resource Usage:
"""

        for service, usage in self.results.get("resource_usage", {}).items():
            report += f"  {service}:\n"
            report += f"    CPU: {usage.get('cpu_percent', 'N/A')}\n"
            report += f"    Memory: {usage.get('memory_usage', 'N/A')}\n"

        report += f"\nStatus: {'PASSED' if self.results.get('passed') else 'FAILED'}\n"

        if self.results.get("regression_detected"):
            report += "WARNING: Performance regression detected!\n"

        return report


@log_errors()
def main() -> None:
    """
    CLI entry point.

    Raises:
        ValidationError: If command line arguments are invalid
        WorkItemNotFoundError: If work item doesn't exist
        PerformanceTestError: If benchmarks fail
    """
    import sys

    if len(sys.argv) < 2:
        raise ValidationError(
            message="Missing required argument: work_item_id",
            context={"usage": "python performance_benchmark.py <work_item_id>"},
            remediation="Provide a work item ID as the first argument",
        )

    work_item_id = sys.argv[1]

    # Load work item
    work_items_file = Path(".session/tracking/work_items.json")
    try:
        data = load_json(work_items_file)
        work_item = data["work_items"].get(work_item_id)

        if not work_item:
            raise WorkItemNotFoundError(work_item_id)

        # Run benchmarks
        benchmark = PerformanceBenchmark(work_item)
        passed, results = benchmark.run_benchmarks()

        output.info(benchmark.generate_report())

        sys.exit(0 if passed else 1)

    except (BenchmarkFailedError, PerformanceRegressionError, LoadTestFailedError) as e:
        logger.error(f"Performance test failed: {e.message}")
        output.info(f"\nERROR: {e.message}")
        if e.remediation:
            output.info(f"REMEDIATION: {e.remediation}")
        sys.exit(e.exit_code)
    except Exception as e:
        logger.exception("Unexpected error during performance benchmarking")
        output.info(f"\nERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
