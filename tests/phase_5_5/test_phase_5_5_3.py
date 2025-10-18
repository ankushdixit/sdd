#!/usr/bin/env python3
"""
Test script for Phase 5.5.3 - Performance Benchmarking System
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))
from scripts.performance_benchmark import PerformanceBenchmark  # noqa: E402


def test_performance_benchmark_class():
    """Test PerformanceBenchmark class structure and methods."""
    print("=" * 60)
    print("Testing Phase 5.5.3: Performance Benchmarking System")
    print("=" * 60)
    print()

    tests_passed = 0
    tests_failed = 0

    # Test 1: Class instantiation
    print("Test 1: PerformanceBenchmark class instantiation")
    work_item = {
        "id": "INTEG-001",
        "type": "integration_test",
        "title": "Performance Test",
        "performance_benchmarks": {
            "endpoint": "http://localhost:8000/api",
            "response_time": {"p50": 100, "p95": 500, "p99": 1000},
            "throughput": {"minimum": 100, "target": 500},
            "load_test_duration": 30,
            "threads": 4,
            "connections": 100,
        },
        "environment_requirements": {"services_required": ["api", "db"]},
    }

    try:
        benchmark = PerformanceBenchmark(work_item)
        print("✅ PASS: PerformanceBenchmark instantiated successfully")
        tests_passed += 1
    except Exception as e:
        print(f"❌ FAIL: Failed to instantiate PerformanceBenchmark: {e}")
        tests_failed += 1
    print()

    # Test 2: Required methods exist
    print("Test 2: Required methods exist")
    required_methods = [
        "run_benchmarks",
        "_run_load_test",
        "_parse_wrk_output",
        "_parse_latency",
        "_run_simple_load_test",
        "_measure_resource_usage",
        "_check_against_requirements",
        "_check_for_regression",
        "_store_baseline",
        "_get_current_session",
        "generate_report",
    ]

    for method in required_methods:
        if hasattr(benchmark, method):
            print(f"✅ PASS: Method {method} exists")
            tests_passed += 1
        else:
            print(f"❌ FAIL: Method {method} missing")
            tests_failed += 1
    print()

    # Test 3: Benchmarks configuration parsed
    print("Test 3: Benchmarks configuration parsed")
    if benchmark.benchmarks.get("endpoint") == "http://localhost:8000/api":
        print("✅ PASS: Endpoint configured correctly")
        tests_passed += 1
    else:
        print("❌ FAIL: Endpoint not configured correctly")
        tests_failed += 1
    print()

    # Test 4: Response time requirements parsed
    print("Test 4: Response time requirements parsed")
    response_time = benchmark.benchmarks.get("response_time", {})
    if response_time.get("p50") == 100 and response_time.get("p95") == 500:
        print("✅ PASS: Response time requirements parsed")
        tests_passed += 1
    else:
        print("❌ FAIL: Response time requirements not parsed correctly")
        tests_failed += 1
    print()

    # Test 5: Throughput requirements parsed
    print("Test 5: Throughput requirements parsed")
    throughput = benchmark.benchmarks.get("throughput", {})
    if throughput.get("minimum") == 100 and throughput.get("target") == 500:
        print("✅ PASS: Throughput requirements parsed")
        tests_passed += 1
    else:
        print("❌ FAIL: Throughput requirements not parsed correctly")
        tests_failed += 1
    print()

    # Test 6: Baselines file path configured
    print("Test 6: Baselines file path configured")
    if str(benchmark.baselines_file) == ".session/tracking/performance_baselines.json":
        print("✅ PASS: Baselines file path configured")
        tests_passed += 1
    else:
        print("❌ FAIL: Baselines file path not configured correctly")
        tests_failed += 1
    print()

    # Test 7: Parse latency - milliseconds
    print("Test 7: Parse latency - milliseconds")
    latency_ms = benchmark._parse_latency("123.45ms")
    if latency_ms == 123.45:
        print("✅ PASS: Milliseconds parsed correctly")
        tests_passed += 1
    else:
        print(f"❌ FAIL: Expected 123.45, got {latency_ms}")
        tests_failed += 1
    print()

    # Test 8: Parse latency - seconds
    print("Test 8: Parse latency - seconds")
    latency_s = benchmark._parse_latency("1.5s")
    if latency_s == 1500.0:
        print("✅ PASS: Seconds parsed correctly")
        tests_passed += 1
    else:
        print(f"❌ FAIL: Expected 1500.0, got {latency_s}")
        tests_failed += 1
    print()

    # Test 9: Check against requirements - passing
    print("Test 9: Check against requirements - passing")
    benchmark.results = {
        "load_test": {
            "latency": {"p50": 80, "p95": 400, "p99": 900},
            "throughput": {"requests_per_sec": 150},
        }
    }
    passed = benchmark._check_against_requirements()
    if passed:
        print("✅ PASS: Requirements check passed correctly")
        tests_passed += 1
    else:
        print("❌ FAIL: Requirements check should have passed")
        tests_failed += 1
    print()

    # Test 10: Check against requirements - failing p50
    print("Test 10: Check against requirements - failing p50")
    benchmark.results = {
        "load_test": {
            "latency": {"p50": 150, "p95": 400, "p99": 900},
            "throughput": {"requests_per_sec": 150},
        }
    }
    passed = benchmark._check_against_requirements()
    if not passed:
        print("✅ PASS: Requirements check failed correctly (p50 exceeded)")
        tests_passed += 1
    else:
        print("❌ FAIL: Requirements check should have failed (p50 exceeded)")
        tests_failed += 1
    print()

    # Test 11: Check against requirements - failing throughput
    print("Test 11: Check against requirements - failing throughput")
    benchmark.results = {
        "load_test": {
            "latency": {"p50": 80, "p95": 400, "p99": 900},
            "throughput": {"requests_per_sec": 50},
        }
    }
    passed = benchmark._check_against_requirements()
    if not passed:
        print("✅ PASS: Requirements check failed correctly (throughput below minimum)")
        tests_passed += 1
    else:
        print(
            "❌ FAIL: Requirements check should have failed (throughput below minimum)"
        )
        tests_failed += 1
    print()

    # Test 12: Regression detection - no baseline
    print("Test 12: Regression detection - no baseline")
    # Clean up any existing baseline
    if benchmark.baselines_file.exists():
        baseline_backup = benchmark.baselines_file.read_text()
        benchmark.baselines_file.unlink()
    else:
        baseline_backup = None

    benchmark.results = {"load_test": {"latency": {"p50": 80, "p95": 400, "p99": 900}}}
    regression = benchmark._check_for_regression()
    if not regression:
        print("✅ PASS: No regression when no baseline exists")
        tests_passed += 1
    else:
        print("❌ FAIL: Should not detect regression without baseline")
        tests_failed += 1

    # Restore baseline if it existed
    if baseline_backup:
        benchmark.baselines_file.write_text(baseline_backup)
    print()

    # Test 13: Regression detection - with regression
    print("Test 13: Regression detection - with regression")
    # Create baseline
    baseline_data = {
        "INTEG-001": {
            "latency": {"p50": 80, "p95": 400, "p99": 900},
            "timestamp": "2024-01-01T10:00:00",
        }
    }
    benchmark.baselines_file.parent.mkdir(parents=True, exist_ok=True)
    benchmark.baselines_file.write_text(json.dumps(baseline_data, indent=2))

    # Set current results with regression
    benchmark.results = {
        "load_test": {"latency": {"p50": 100, "p95": 500, "p99": 1100}}
    }
    regression = benchmark._check_for_regression()
    if regression:
        print("✅ PASS: Regression detected correctly")
        tests_passed += 1
    else:
        print("❌ FAIL: Should detect regression (>10% increase)")
        tests_failed += 1

    # Clean up
    if benchmark.baselines_file.exists():
        benchmark.baselines_file.unlink()
    print()

    # Test 14: Regression detection - no regression
    print("Test 14: Regression detection - no regression")
    # Create baseline
    benchmark.baselines_file.write_text(json.dumps(baseline_data, indent=2))

    # Set current results without regression
    benchmark.results = {"load_test": {"latency": {"p50": 85, "p95": 420, "p99": 950}}}
    regression = benchmark._check_for_regression()
    if not regression:
        print("✅ PASS: No regression when within threshold")
        tests_passed += 1
    else:
        print("❌ FAIL: Should not detect regression (<10% increase)")
        tests_failed += 1

    # Clean up
    if benchmark.baselines_file.exists():
        benchmark.baselines_file.unlink()
    print()

    # Test 15: Report generation
    print("Test 15: Report generation")
    benchmark.results = {
        "load_test": {
            "latency": {"p50": 80, "p75": 150, "p90": 300, "p95": 400, "p99": 900},
            "throughput": {"requests_per_sec": 150},
        },
        "resource_usage": {
            "api": {"cpu_percent": "45%", "memory_usage": "512MB"},
            "db": {"cpu_percent": "30%", "memory_usage": "1GB"},
        },
        "passed": True,
        "regression_detected": False,
    }

    report = benchmark.generate_report()
    if (
        "Performance Benchmark Report" in report
        and "PASSED" in report
        and "p50: 80" in report
    ):
        print("✅ PASS: Report generated correctly")
        tests_passed += 1
    else:
        print("❌ FAIL: Report missing expected content")
        tests_failed += 1
    print()

    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Tests Passed: {tests_passed}")
    print(f"Tests Failed: {tests_failed}")
    print(f"Total Tests: {tests_passed + tests_failed}")
    print()

    if tests_failed == 0:
        print("✅ All tests passed!")
        return 0
    else:
        print(f"❌ {tests_failed} test(s) failed")
        return 1


def test_file_structure():
    """Test that the performance_benchmark.py file exists and is properly structured."""
    print("=" * 60)
    print("Testing File Structure")
    print("=" * 60)
    print()

    tests_passed = 0
    tests_failed = 0

    # Test 1: File exists
    print("Test 1: performance_benchmark.py file exists")
    file_path = Path("scripts/performance_benchmark.py")
    if file_path.exists():
        print("✅ PASS: File exists")
        tests_passed += 1
    else:
        print("❌ FAIL: File not found")
        tests_failed += 1
        return 1
    print()

    # Test 2: File is executable
    print("Test 2: File has executable permissions")
    import os

    if os.access(file_path, os.X_OK):
        print("✅ PASS: File is executable")
        tests_passed += 1
    else:
        print("❌ FAIL: File is not executable")
        tests_failed += 1
    print()

    # Test 3: Check for required imports
    print("Test 3: Required imports present")
    content = file_path.read_text()
    required_imports = [
        "import subprocess",
        "import json",
        "from pathlib import Path",
        "from typing import",
        "from datetime import datetime",
        "from scripts.file_ops import",
    ]

    for imp in required_imports:
        if imp in content:
            print(f"✅ PASS: Found import: {imp}")
            tests_passed += 1
        else:
            print(f"❌ FAIL: Missing import: {imp}")
            tests_failed += 1
    print()

    # Test 4: PerformanceBenchmark class defined
    print("Test 4: PerformanceBenchmark class defined")
    if "class PerformanceBenchmark:" in content:
        print("✅ PASS: PerformanceBenchmark class defined")
        tests_passed += 1
    else:
        print("❌ FAIL: PerformanceBenchmark class not found")
        tests_failed += 1
    print()

    # Test 5: Check for regression threshold
    print("Test 5: Regression threshold defined (10%)")
    if "regression_threshold = 1.1" in content:
        print("✅ PASS: 10% regression threshold defined")
        tests_passed += 1
    else:
        print("❌ FAIL: Regression threshold not found or incorrect")
        tests_failed += 1
    print()

    # Test 6: Check for main function
    print("Test 6: main() function defined")
    if "def main():" in content:
        print("✅ PASS: main() function defined")
        tests_passed += 1
    else:
        print("❌ FAIL: main() function not found")
        tests_failed += 1
    print()

    # Summary
    print(
        f"\nFile structure tests: {tests_passed}/{tests_passed + tests_failed} passed"
    )
    print()

    if tests_failed == 0:
        print("✅ File structure tests passed!")
        return 0
    else:
        print(f"❌ {tests_failed} test(s) failed")
        return 1


def test_wrk_fallback():
    """Test wrk fallback logic."""
    print("=" * 60)
    print("Testing wrk Fallback Logic")
    print("=" * 60)
    print()

    tests_passed = 0
    tests_failed = 0

    work_item = {
        "id": "INTEG-002",
        "type": "integration_test",
        "title": "Fallback Test",
        "performance_benchmarks": {
            "load_test_duration": 5,  # Short duration for testing
            "threads": 2,
            "connections": 10,
        },
        "environment_requirements": {"services_required": []},
    }

    benchmark = PerformanceBenchmark(work_item)

    # Test 1: Parse wrk output
    print("Test 1: Parse wrk output")
    wrk_output = """Running 60s test @ http://localhost:8000
  4 threads and 100 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency    45.23ms   12.34ms  123.45ms   75.00%
    Req/Sec   567.89    123.45     890.12    80.00%
  Latency Distribution
     50%   45.23ms
     75%   52.34ms
     90%   65.67ms
     99%   89.12ms
  136789 requests in 60.00s, 45.67MB read
Requests/sec:   2279.82
Transfer/sec:      0.76MB
"""

    result = benchmark._parse_wrk_output(wrk_output)
    if (
        result.get("latency", {}).get("p50")
        and result.get("throughput", {}).get("requests_per_sec") == 2279.82
    ):
        print("✅ PASS: wrk output parsed correctly")
        tests_passed += 1
    else:
        print("❌ FAIL: wrk output parsing failed")
        tests_failed += 1
    print()

    # Test 2: Latency parsing - various formats
    print("Test 2: Latency parsing - various formats")
    test_cases = [
        ("50.5ms", 50.5),
        ("1.5s", 1500.0),
        ("100ms", 100.0),
    ]

    for input_val, expected in test_cases:
        result = benchmark._parse_latency(input_val)
        if result == expected:
            print(f"✅ PASS: '{input_val}' -> {result}ms")
            tests_passed += 1
        else:
            print(f"❌ FAIL: '{input_val}' expected {expected}, got {result}")
            tests_failed += 1
    print()

    # Summary
    print(f"\nwrk fallback tests: {tests_passed}/{tests_passed + tests_failed} passed")
    print()

    if tests_failed == 0:
        print("✅ wrk fallback tests passed!")
        return 0
    else:
        print(f"❌ {tests_failed} test(s) failed")
        return 1


if __name__ == "__main__":
    print()
    print("#" * 60)
    print("# Phase 5.5.3 Test Suite")
    print("# Performance Benchmarking System")
    print("#" * 60)
    print()

    result1 = test_file_structure()
    print()

    result2 = test_performance_benchmark_class()
    print()

    result3 = test_wrk_fallback()
    print()

    if result1 == 0 and result2 == 0 and result3 == 0:
        print("=" * 60)
        print("✅ Phase 5.5.3 - ALL TESTS PASSED")
        print("=" * 60)
        sys.exit(0)
    else:
        print("=" * 60)
        print("❌ Phase 5.5.3 - SOME TESTS FAILED")
        print("=" * 60)
        sys.exit(1)
