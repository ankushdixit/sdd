#!/usr/bin/env python3
"""
Test script for Phase 5.5.6 - Integration Documentation Validation
"""

import sys
import json
from pathlib import Path
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))
from scripts.quality_gates import QualityGates  # noqa: E402


def test_integration_documentation_validation():
    """Test integration documentation validation method."""
    print("=" * 60)
    print("Testing Phase 5.5.6: Integration Documentation Validation")
    print("=" * 60)
    print()

    tests_passed = 0
    tests_failed = 0

    # Test 1: Method exists
    print("Test 1: validate_integration_documentation method exists")
    gates = QualityGates()
    if hasattr(gates, "validate_integration_documentation"):
        print("✅ PASS: Method exists")
        tests_passed += 1
    else:
        print("❌ FAIL: Method not found")
        tests_failed += 1
        return tests_passed, tests_failed
    print()

    # Test 2: Skips non-integration work items
    print("Test 2: Skips non-integration work items")
    work_item = {"id": "FEAT-001", "type": "feature", "title": "Regular Feature"}

    passed, results = gates.validate_integration_documentation(work_item)
    if passed and results.get("status") == "skipped":
        print("✅ PASS: Non-integration work items skipped")
        tests_passed += 1
    else:
        print("❌ FAIL: Should skip non-integration work items")
        tests_failed += 1
    print()

    # Test 3: Results structure
    print("Test 3: Results dictionary has correct structure")
    work_item = {
        "id": "INTEG-001",
        "type": "integration_test",
        "title": "Integration Test",
        "scope": "Test scope description with sufficient detail",
        "test_scenarios": [],
    }

    passed, results = gates.validate_integration_documentation(work_item)
    expected_keys = ["checks", "missing", "passed", "summary"]

    all_keys_present = all(key in results for key in expected_keys)
    if all_keys_present:
        print("✅ PASS: Results dictionary has all required keys")
        tests_passed += 1
    else:
        print("❌ FAIL: Results dictionary missing required keys")
        tests_failed += 1
    print()

    # Test 4: Summary format
    print("Test 4: Summary shows X/Y format")
    if "/" in results.get("summary", ""):
        print(f"  Summary: {results['summary']}")
        print("✅ PASS: Summary format correct")
        tests_passed += 1
    else:
        print("❌ FAIL: Summary format incorrect")
        tests_failed += 1
    print()

    print(f"Basic tests: {tests_passed}/{tests_passed + tests_failed} passed")
    print()

    return tests_passed, tests_failed


def test_architecture_diagram_validation():
    """Test architecture diagram validation."""
    print("=" * 60)
    print("Testing Architecture Diagram Validation")
    print("=" * 60)
    print()

    tests_passed = 0
    tests_failed = 0

    # Create temporary directories
    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Create config
        config_file = temp_dir / "config.json"
        config_data = {
            "integration_tests": {
                "documentation": {
                    "enabled": True,
                    "architecture_diagrams": True,
                    "sequence_diagrams": False,
                    "contract_documentation": False,
                    "performance_baseline_docs": False,
                }
            }
        }
        config_file.write_text(json.dumps(config_data, indent=2))

        gates = QualityGates(config_path=config_file)

        # Test 1: Missing architecture diagram
        print("Test 1: Detects missing architecture diagram")
        work_item = {
            "id": "INTEG-001",
            "type": "integration_test",
            "title": "Test",
            "scope": "Test scope with sufficient detail here",
            "test_scenarios": [],
        }

        passed, results = gates.validate_integration_documentation(work_item)

        has_arch_check = any(
            c["name"] == "Integration architecture diagram"
            for c in results.get("checks", [])
        )
        if has_arch_check and "Integration architecture diagram" in results.get(
            "missing", []
        ):
            print("✅ PASS: Missing architecture diagram detected")
            tests_passed += 1
        else:
            print("❌ FAIL: Should detect missing architecture diagram")
            tests_failed += 1
        print()

        # Test 2: Finds architecture diagram in docs/
        print("Test 2: Finds architecture diagram in docs/")
        docs_dir = temp_dir / "docs"
        docs_dir.mkdir()
        arch_file = docs_dir / "integration-architecture.md"
        arch_file.write_text("# Integration Architecture\n\nDiagram content here")

        # Change to temp directory for test
        import os

        original_dir = os.getcwd()
        os.chdir(temp_dir)

        passed, results = gates.validate_integration_documentation(work_item)

        os.chdir(original_dir)

        arch_check = next(
            (
                c
                for c in results.get("checks", [])
                if c["name"] == "Integration architecture diagram"
            ),
            None,
        )
        if arch_check and arch_check["passed"]:
            print("✅ PASS: Architecture diagram found in docs/")
            tests_passed += 1
        else:
            print("❌ FAIL: Should find architecture diagram")
            tests_failed += 1
        print()

    finally:
        shutil.rmtree(temp_dir)

    print(
        f"Architecture diagram tests: {tests_passed}/{tests_passed + tests_failed} passed"
    )
    print()

    return tests_passed, tests_failed


def test_sequence_diagram_validation():
    """Test sequence diagram validation."""
    print("=" * 60)
    print("Testing Sequence Diagram Validation")
    print("=" * 60)
    print()

    tests_passed = 0
    tests_failed = 0

    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Create config
        config_file = temp_dir / "config.json"
        config_data = {
            "integration_tests": {
                "documentation": {
                    "enabled": True,
                    "architecture_diagrams": False,
                    "sequence_diagrams": True,
                    "contract_documentation": False,
                    "performance_baseline_docs": False,
                }
            }
        }
        config_file.write_text(json.dumps(config_data, indent=2))

        gates = QualityGates(config_path=config_file)

        # Create .session/specs directory
        specs_dir = temp_dir / ".session" / "specs"
        specs_dir.mkdir(parents=True)

        # Test 1: Missing sequence diagrams
        print("Test 1: Detects missing sequence diagrams")
        work_item = {
            "id": "INTEG-001",
            "type": "integration_test",
            "title": "Test",
            "scope": "Test scope with sufficient detail here",
            "test_scenarios": [{"name": "Scenario 1"}],
        }

        spec_file = specs_dir / "INTEG-001.md"
        spec_file.write_text("# Integration Test\n\nNo diagrams here")

        import os

        original_dir = os.getcwd()
        os.chdir(temp_dir)

        passed, results = gates.validate_integration_documentation(work_item)

        os.chdir(original_dir)

        # Debug: print what we got
        # print(f"  DEBUG - Missing: {results.get('missing', [])}")
        # print(f"  DEBUG - Checks: {results.get('checks', [])}")

        if "Sequence diagrams for test scenarios" in results.get("missing", []):
            print("✅ PASS: Missing sequence diagrams detected")
            tests_passed += 1
        else:
            print("❌ FAIL: Should detect missing sequence diagrams")
            print(f"  Missing list: {results.get('missing', [])}")
            tests_failed += 1
        print()

        # Test 2: Finds mermaid sequence diagrams
        print("Test 2: Finds mermaid sequence diagrams")
        spec_file.write_text("""# Integration Test

## Sequence Diagrams

```mermaid
sequenceDiagram
    Client->>Service A: Request
    Service A->>Service B: Forward
    Service B-->>Service A: Response
    Service A-->>Client: Response
```
""")

        os.chdir(temp_dir)
        passed, results = gates.validate_integration_documentation(work_item)
        os.chdir(original_dir)

        seq_check = next(
            (c for c in results.get("checks", []) if c["name"] == "Sequence diagrams"),
            None,
        )
        if seq_check and seq_check["passed"]:
            print("✅ PASS: Mermaid sequence diagram found")
            tests_passed += 1
        else:
            print("❌ FAIL: Should find mermaid diagram")
            tests_failed += 1
        print()

        # Test 3: Finds scenario sections
        print("Test 3: Finds scenario sections")
        spec_file.write_text("""# Integration Test

### Scenario 1: Happy Path
- Setup: Services running
- Actions: Send request
- Expected: HTTP 200
""")

        os.chdir(temp_dir)
        passed, results = gates.validate_integration_documentation(work_item)
        os.chdir(original_dir)

        seq_check = next(
            (c for c in results.get("checks", []) if c["name"] == "Sequence diagrams"),
            None,
        )
        if seq_check and seq_check["passed"]:
            print("✅ PASS: Scenario sections found")
            tests_passed += 1
        else:
            print("❌ FAIL: Should find scenario sections")
            tests_failed += 1
        print()

    finally:
        shutil.rmtree(temp_dir)

    print(
        f"Sequence diagram tests: {tests_passed}/{tests_passed + tests_failed} passed"
    )
    print()

    return tests_passed, tests_failed


def test_api_contract_documentation():
    """Test API contract documentation validation."""
    print("=" * 60)
    print("Testing API Contract Documentation")
    print("=" * 60)
    print()

    tests_passed = 0
    tests_failed = 0

    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Create config
        config_file = temp_dir / "config.json"
        config_data = {
            "integration_tests": {
                "documentation": {
                    "enabled": True,
                    "architecture_diagrams": False,
                    "sequence_diagrams": False,
                    "contract_documentation": True,
                    "performance_baseline_docs": False,
                }
            }
        }
        config_file.write_text(json.dumps(config_data, indent=2))

        gates = QualityGates(config_path=config_file)

        # Test 1: Missing contract files
        print("Test 1: Detects missing contract files")
        work_item = {
            "id": "INTEG-001",
            "type": "integration_test",
            "title": "Test",
            "scope": "Test scope with sufficient detail here",
            "api_contracts": [
                {"contract_file": "contracts/api-v1.yaml"},
                {"contract_file": "contracts/api-v2.json"},
            ],
        }

        passed, results = gates.validate_integration_documentation(work_item)

        missing_contracts = [
            m for m in results.get("missing", []) if "contract" in m.lower()
        ]
        if len(missing_contracts) == 2:
            print("✅ PASS: Missing contract files detected")
            tests_passed += 1
        else:
            print(
                f"❌ FAIL: Should detect 2 missing contracts, found {len(missing_contracts)}"
            )
            tests_failed += 1
        print()

        # Test 2: Existing contract files pass
        print("Test 2: Existing contract files pass")
        contracts_dir = temp_dir / "contracts"
        contracts_dir.mkdir()
        (contracts_dir / "api-v1.yaml").write_text("openapi: 3.0.0")
        (contracts_dir / "api-v2.json").write_text('{"openapi": "3.0.0"}')

        import os

        original_dir = os.getcwd()
        os.chdir(temp_dir)

        passed, results = gates.validate_integration_documentation(work_item)

        os.chdir(original_dir)

        contract_check = next(
            (
                c
                for c in results.get("checks", [])
                if c["name"] == "API contracts documented"
            ),
            None,
        )
        if contract_check and contract_check["passed"]:
            print("✅ PASS: Existing contract files validated")
            tests_passed += 1
        else:
            print("❌ FAIL: Should validate existing contracts")
            tests_failed += 1
        print()

    finally:
        shutil.rmtree(temp_dir)

    print(f"API contract tests: {tests_passed}/{tests_passed + tests_failed} passed")
    print()

    return tests_passed, tests_failed


def test_performance_baseline_documentation():
    """Test performance baseline documentation validation."""
    print("=" * 60)
    print("Testing Performance Baseline Documentation")
    print("=" * 60)
    print()

    tests_passed = 0
    tests_failed = 0

    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Create config
        config_file = temp_dir / "config.json"
        config_data = {
            "integration_tests": {
                "documentation": {
                    "enabled": True,
                    "architecture_diagrams": False,
                    "sequence_diagrams": False,
                    "contract_documentation": False,
                    "performance_baseline_docs": True,
                }
            }
        }
        config_file.write_text(json.dumps(config_data, indent=2))

        gates = QualityGates(config_path=config_file)

        # Test 1: Missing baseline file
        print("Test 1: Detects missing baseline file")
        work_item = {
            "id": "INTEG-001",
            "type": "integration_test",
            "title": "Test",
            "scope": "Test scope with sufficient detail here",
            "performance_benchmarks": {"p50": 100},
        }

        passed, results = gates.validate_integration_documentation(work_item)

        if "Performance baseline documentation" in results.get("missing", []):
            print("✅ PASS: Missing baseline file detected")
            tests_passed += 1
        else:
            print("❌ FAIL: Should detect missing baseline file")
            tests_failed += 1
        print()

        # Test 2: Existing baseline file passes
        print("Test 2: Existing baseline file passes")
        baseline_dir = temp_dir / ".session" / "tracking"
        baseline_dir.mkdir(parents=True)
        baseline_file = baseline_dir / "performance_baselines.json"
        baseline_file.write_text('{"INTEG-001": {"p50": 80}}')

        import os

        original_dir = os.getcwd()
        os.chdir(temp_dir)

        passed, results = gates.validate_integration_documentation(work_item)

        os.chdir(original_dir)

        baseline_check = next(
            (
                c
                for c in results.get("checks", [])
                if c["name"] == "Performance baseline documented"
            ),
            None,
        )
        if baseline_check and baseline_check["passed"]:
            print("✅ PASS: Existing baseline file validated")
            tests_passed += 1
        else:
            print("❌ FAIL: Should validate existing baseline")
            tests_failed += 1
        print()

    finally:
        shutil.rmtree(temp_dir)

    print(
        f"Performance baseline tests: {tests_passed}/{tests_passed + tests_failed} passed"
    )
    print()

    return tests_passed, tests_failed


def test_integration_points_documentation():
    """Test integration points documentation validation."""
    print("=" * 60)
    print("Testing Integration Points Documentation")
    print("=" * 60)
    print()

    tests_passed = 0
    tests_failed = 0

    gates = QualityGates()

    # Test 1: Missing integration points (short scope)
    print("Test 1: Detects missing integration points (short scope)")
    work_item = {
        "id": "INTEG-001",
        "type": "integration_test",
        "title": "Test",
        "scope": "Short",
    }

    passed, results = gates.validate_integration_documentation(work_item)

    if "Integration points documentation" in results.get("missing", []):
        print("✅ PASS: Missing integration points detected")
        tests_passed += 1
    else:
        print("❌ FAIL: Should detect missing integration points")
        tests_failed += 1
    print()

    # Test 2: Documented integration points (detailed scope)
    print("Test 2: Documented integration points (detailed scope)")
    work_item["scope"] = (
        "This is a detailed scope describing the integration between Service A and Service B with sufficient detail"
    )

    passed, results = gates.validate_integration_documentation(work_item)

    points_check = next(
        (
            c
            for c in results.get("checks", [])
            if c["name"] == "Integration points documented"
        ),
        None,
    )
    if points_check and points_check["passed"]:
        print("✅ PASS: Integration points documented")
        tests_passed += 1
    else:
        print("❌ FAIL: Should validate documented integration points")
        tests_failed += 1
    print()

    print(
        f"Integration points tests: {tests_passed}/{tests_passed + tests_failed} passed"
    )
    print()

    return tests_passed, tests_failed


if __name__ == "__main__":
    print()
    print("#" * 60)
    print("# Phase 5.5.6 Test Suite")
    print("# Integration Documentation Validation")
    print("#" * 60)
    print()

    total_passed = 0
    total_failed = 0

    # Basic tests
    passed, failed = test_integration_documentation_validation()
    total_passed += passed
    total_failed += failed
    print()

    # Architecture diagram tests
    passed, failed = test_architecture_diagram_validation()
    total_passed += passed
    total_failed += failed
    print()

    # Sequence diagram tests
    passed, failed = test_sequence_diagram_validation()
    total_passed += passed
    total_failed += failed
    print()

    # API contract tests
    passed, failed = test_api_contract_documentation()
    total_passed += passed
    total_failed += failed
    print()

    # Performance baseline tests
    passed, failed = test_performance_baseline_documentation()
    total_passed += passed
    total_failed += failed
    print()

    # Integration points tests
    passed, failed = test_integration_points_documentation()
    total_passed += passed
    total_failed += failed
    print()

    # Final summary
    print("=" * 60)
    print("FINAL TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests Passed: {total_passed}")
    print(f"Total Tests Failed: {total_failed}")
    print(f"Total Tests: {total_passed + total_failed}")
    print()

    if total_failed == 0:
        print("=" * 60)
        print("✅ Phase 5.5.6 - ALL TESTS PASSED")
        print("=" * 60)
        sys.exit(0)
    else:
        print("=" * 60)
        print("❌ Phase 5.5.6 - SOME TESTS FAILED")
        print("=" * 60)
        sys.exit(1)
