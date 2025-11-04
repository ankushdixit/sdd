#!/usr/bin/env python3
"""
Performance benchmarking system for integration tests.

Tracks:
- Response times (p50, p95, p99)
- Throughput (requests/second)
- Resource utilization (CPU, memory)
- Regression detection
"""

import sys
from datetime import datetime
from pathlib import Path

from sdd.core.command_runner import CommandRunner
from sdd.core.file_ops import load_json, save_json


class PerformanceBenchmark:
    """Performance benchmarking for integration tests."""

    def __init__(self, work_item: dict):
        """
        Initialize performance benchmark.

        Args:
            work_item: Integration test work item with performance requirements
        """
        self.work_item = work_item
        self.benchmarks = work_item.get("performance_benchmarks", {})
        self.baselines_file = Path(".session/tracking/performance_baselines.json")
        self.results = {}
        self.runner = CommandRunner(default_timeout=300)

    def run_benchmarks(self, test_endpoint: str = None) -> tuple[bool, dict]:
        """
        Run performance benchmarks.

        Args:
            test_endpoint: Endpoint to benchmark (if None, uses work item config)

        Returns:
            (passed: bool, results: dict)
        """
        print("Running performance benchmarks...")

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

    def _run_load_test(self, endpoint: str) -> dict:
        """
        Run load test using wrk or similar tool.

        Args:
            endpoint: URL to test

        Returns:
            Load test results dict
        """
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
                return self._run_simple_load_test(endpoint, duration)

        except Exception as e:
            return {"error": str(e)}

    def _parse_wrk_output(self, output: str) -> dict:
        """Parse wrk output to extract metrics."""
        results = {"latency": {}, "throughput": {}}

        lines = output.split("\n")

        for line in lines:
            if "50.000%" in line or "50%" in line:
                # p50 latency
                parts = line.split()
                results["latency"]["p50"] = self._parse_latency(parts[-1])
            elif "75.000%" in line or "75%" in line:
                results["latency"]["p75"] = self._parse_latency(parts[-1])
            elif "90.000%" in line or "90%" in line:
                results["latency"]["p90"] = self._parse_latency(parts[-1])
            elif "99.000%" in line or "99%" in line:
                results["latency"]["p99"] = self._parse_latency(parts[-1])
            elif "Requests/sec:" in line:
                parts = line.split()
                results["throughput"]["requests_per_sec"] = float(parts[1])
            elif "Transfer/sec:" in line:
                parts = line.split()
                results["throughput"]["transfer_per_sec"] = parts[1]

        return results

    def _parse_latency(self, latency_str: str) -> float:
        """Convert latency string (e.g., '1.23ms') to milliseconds."""
        latency_str = latency_str.strip()
        if "ms" in latency_str:  # milliseconds
            return float(latency_str.rstrip("ms"))
        elif "s" in latency_str:  # seconds
            return float(latency_str.rstrip("s")) * 1000
        return 0.0

    def _run_simple_load_test(self, endpoint: str, duration: int) -> dict:
        """Fallback load test using Python requests."""
        import time

        import requests

        latencies = []
        start_time = time.time()
        request_count = 0

        print("  Using simple load test (wrk not available)...")

        while time.time() - start_time < duration:
            req_start = time.time()
            try:
                requests.get(endpoint, timeout=5)
                latency = (time.time() - req_start) * 1000  # Convert to ms
                latencies.append(latency)
                request_count += 1
            except Exception:
                pass

        total_duration = time.time() - start_time

        if not latencies:
            return {"error": "No successful requests"}

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

    def _measure_resource_usage(self) -> dict:
        """Measure CPU and memory usage of services."""
        services = self.work_item.get("environment_requirements", {}).get("services_required", [])

        resource_usage = {}

        for service in services:
            try:
                # Get container ID
                result = self.runner.run(["docker-compose", "ps", "-q", service], timeout=5)

                container_id = result.stdout.strip()
                if not container_id:
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
                    timeout=10,
                )

                if stats_result.success:
                    parts = stats_result.stdout.strip().split(",")
                    resource_usage[service] = {
                        "cpu_percent": parts[0].rstrip("%"),
                        "memory_usage": parts[1],
                    }

            except Exception as e:
                resource_usage[service] = {"error": str(e)}

        return resource_usage

    def _check_against_requirements(self) -> bool:
        """Check if benchmarks meet requirements."""
        requirements = self.benchmarks.get("response_time", {})
        load_test = self.results.get("load_test", {})
        latency = load_test.get("latency", {})

        passed = True

        # Check response time requirements
        if "p50" in requirements:
            if latency.get("p50", float("inf")) > requirements["p50"]:
                print(
                    f"  ✗ p50 latency {latency.get('p50')}ms exceeds requirement {requirements['p50']}ms"
                )
                passed = False

        if "p95" in requirements:
            if latency.get("p95", float("inf")) > requirements["p95"]:
                print(
                    f"  ✗ p95 latency {latency.get('p95')}ms exceeds requirement {requirements['p95']}ms"
                )
                passed = False

        if "p99" in requirements:
            if latency.get("p99", float("inf")) > requirements["p99"]:
                print(
                    f"  ✗ p99 latency {latency.get('p99')}ms exceeds requirement {requirements['p99']}ms"
                )
                passed = False

        # Check throughput requirements
        throughput_req = self.benchmarks.get("throughput", {})
        throughput = load_test.get("throughput", {})

        if "minimum" in throughput_req:
            actual_rps = throughput.get("requests_per_sec", 0)
            if actual_rps < throughput_req["minimum"]:
                print(
                    f"  ✗ Throughput {actual_rps} req/s below minimum {throughput_req['minimum']} req/s"
                )
                passed = False

        return passed

    def _check_for_regression(self) -> bool:
        """Check for performance regression against baseline."""
        if not self.baselines_file.exists():
            print("  ℹ️  No baseline found, skipping regression check")
            return False

        baselines = load_json(self.baselines_file)
        work_item_id = self.work_item.get("id")
        baseline = baselines.get(work_item_id)

        if not baseline:
            print(f"  ℹ️  No baseline for work item {work_item_id}")
            return False

        load_test = self.results.get("load_test", {})
        latency = load_test.get("latency", {})
        baseline_latency = baseline.get("latency", {})

        regression_threshold = 1.1  # 10% regression threshold

        # Check for latency regression
        for percentile in ["p50", "p95", "p99"]:
            current = latency.get(percentile, 0)
            baseline_val = baseline_latency.get(percentile, 0)

            if baseline_val > 0 and current > baseline_val * regression_threshold:
                print(
                    f"  ⚠️  Performance regression detected: {percentile} increased from "
                    f"{baseline_val}ms to {current}ms ({((current / baseline_val - 1) * 100):.1f}% slower)"
                )
                return True

        return False

    def _store_baseline(self):
        """Store current results as baseline."""
        if not self.baselines_file.exists():
            baselines = {}
        else:
            baselines = load_json(self.baselines_file)

        work_item_id = self.work_item.get("id")
        baselines[work_item_id] = {
            "latency": self.results.get("load_test", {}).get("latency", {}),
            "throughput": self.results.get("load_test", {}).get("throughput", {}),
            "resource_usage": self.results.get("resource_usage", {}),
            "timestamp": datetime.now().isoformat(),
            "session": self._get_current_session(),
        }

        save_json(self.baselines_file, baselines)
        print(f"  ✓ Baseline stored for work item {work_item_id}")

    def _get_current_session(self) -> int:
        """Get current session number."""
        status_file = Path(".session/tracking/status_update.json")
        if status_file.exists():
            status = load_json(status_file)
            return status.get("session_number", 0)
        return 0

    def generate_report(self) -> str:
        """Generate performance benchmark report."""
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
            report += "⚠️  Performance regression detected!\n"

        return report


def main():
    """CLI entry point."""

    if len(sys.argv) < 2:
        print("Usage: python performance_benchmark.py <work_item_id>")
        sys.exit(1)

    work_item_id = sys.argv[1]

    # Load work item
    work_items_file = Path(".session/tracking/work_items.json")
    data = load_json(work_items_file)
    work_item = data["work_items"].get(work_item_id)

    if not work_item:
        print(f"Work item not found: {work_item_id}")
        sys.exit(1)

    # Run benchmarks
    benchmark = PerformanceBenchmark(work_item)
    passed, results = benchmark.run_benchmarks()

    print(benchmark.generate_report())

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
