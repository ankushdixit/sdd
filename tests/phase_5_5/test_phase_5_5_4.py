#!/usr/bin/env python3
"""
Test script for Phase 5.5.4 - API Contract Validation
"""

import sys
import json
from pathlib import Path
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Check if PyYAML is available
try:
    import yaml  # noqa: F401

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    print("⚠️  PyYAML not available - some tests will be skipped")

from scripts.api_contract_validator import APIContractValidator


def test_api_contract_validator_class():
    """Test APIContractValidator class structure and methods."""
    print("=" * 60)
    print("Testing Phase 5.5.4: API Contract Validation")
    print("=" * 60)
    print()

    tests_passed = 0
    tests_failed = 0

    # Test 1: Class instantiation
    print("Test 1: APIContractValidator class instantiation")
    work_item = {
        "id": "INTEG-001",
        "type": "integration_test",
        "title": "API Contract Test",
        "api_contracts": [
            {"contract_file": "contracts/api-v1.yaml", "version": "1.0.0"}
        ],
    }

    try:
        validator = APIContractValidator(work_item)
        print("✅ PASS: APIContractValidator instantiated successfully")
        tests_passed += 1
    except Exception as e:
        print(f"❌ FAIL: Failed to instantiate APIContractValidator: {e}")
        tests_failed += 1
    print()

    # Test 2: Required methods exist
    print("Test 2: Required methods exist")
    required_methods = [
        "validate_contracts",
        "_validate_contract_file",
        "_detect_breaking_changes",
        "_load_spec",
        "_check_endpoint_changes",
        "_check_parameter_changes",
        "generate_report",
    ]

    for method in required_methods:
        if hasattr(validator, method):
            print(f"✅ PASS: Method {method} exists")
            tests_passed += 1
        else:
            print(f"❌ FAIL: Method {method} missing")
            tests_failed += 1
    print()

    # Test 3: Contracts configuration parsed
    print("Test 3: Contracts configuration parsed")
    if len(validator.contracts) == 1 and validator.contracts[0]["version"] == "1.0.0":
        print("✅ PASS: Contracts parsed correctly")
        tests_passed += 1
    else:
        print("❌ FAIL: Contracts not parsed correctly")
        tests_failed += 1
    print()

    # Test 4: Results dictionary initialized
    print("Test 4: Results dictionary initialized")
    expected_keys = ["contracts_validated", "breaking_changes", "warnings", "passed"]
    all_keys_present = all(key in validator.results for key in expected_keys)
    if all_keys_present:
        print("✅ PASS: Results dictionary has all required keys")
        tests_passed += 1
    else:
        print("❌ FAIL: Results dictionary missing required keys")
        tests_failed += 1
    print()

    # Summary
    print("=" * 60)
    print("Test Summary - Basic Structure")
    print("=" * 60)
    print(f"Tests Passed: {tests_passed}")
    print(f"Tests Failed: {tests_failed}")
    print()

    return tests_passed, tests_failed


def test_contract_file_validation():
    """Test contract file validation with actual files."""
    print("=" * 60)
    print("Testing Contract File Validation")
    print("=" * 60)
    print()

    if not YAML_AVAILABLE:
        print("⚠️  Skipping YAML tests - PyYAML not available")
        return 0, 0

    tests_passed = 0
    tests_failed = 0

    # Create temporary directory for test contracts
    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Test 1: Valid OpenAPI YAML file
        print("Test 1: Valid OpenAPI YAML file")
        valid_yaml_contract = temp_dir / "valid-api.yaml"
        valid_yaml_contract.write_text("""
openapi: 3.0.0
info:
  title: Test API
  version: 1.0.0
paths:
  /users:
    get:
      summary: Get users
      parameters:
        - name: limit
          in: query
          required: false
          schema:
            type: integer
      responses:
        '200':
          description: Success
""")

        work_item = {
            "id": "TEST-001",
            "api_contracts": [{"contract_file": str(valid_yaml_contract)}],
        }
        validator = APIContractValidator(work_item)

        if validator._validate_contract_file(str(valid_yaml_contract)):
            print("✅ PASS: Valid YAML contract accepted")
            tests_passed += 1
        else:
            print("❌ FAIL: Valid YAML contract rejected")
            tests_failed += 1
        print()

        # Test 2: Valid OpenAPI JSON file
        print("Test 2: Valid OpenAPI JSON file")
        valid_json_contract = temp_dir / "valid-api.json"
        valid_json_contract.write_text(
            json.dumps(
                {
                    "openapi": "3.0.0",
                    "info": {"title": "Test API", "version": "1.0.0"},
                    "paths": {
                        "/users": {
                            "get": {
                                "summary": "Get users",
                                "responses": {"200": {"description": "Success"}},
                            }
                        }
                    },
                },
                indent=2,
            )
        )

        if validator._validate_contract_file(str(valid_json_contract)):
            print("✅ PASS: Valid JSON contract accepted")
            tests_passed += 1
        else:
            print("❌ FAIL: Valid JSON contract rejected")
            tests_failed += 1
        print()

        # Test 3: Invalid contract - missing paths
        print("Test 3: Invalid contract - missing paths")
        invalid_contract = temp_dir / "invalid-api.yaml"
        invalid_contract.write_text("""
openapi: 3.0.0
info:
  title: Test API
  version: 1.0.0
""")

        if not validator._validate_contract_file(str(invalid_contract)):
            print("✅ PASS: Invalid contract (missing paths) rejected")
            tests_passed += 1
        else:
            print("❌ FAIL: Invalid contract should have been rejected")
            tests_failed += 1
        print()

        # Test 4: Missing contract file
        print("Test 4: Missing contract file")
        if not validator._validate_contract_file("nonexistent-file.yaml"):
            print("✅ PASS: Missing file detected")
            tests_passed += 1
        else:
            print("❌ FAIL: Missing file should have been detected")
            tests_failed += 1
        print()

        # Test 5: Invalid YAML syntax
        print("Test 5: Invalid YAML syntax")
        invalid_yaml = temp_dir / "invalid-syntax.yaml"
        invalid_yaml.write_text("not: valid: yaml: [unclosed")

        if not validator._validate_contract_file(str(invalid_yaml)):
            print("✅ PASS: Invalid YAML syntax detected")
            tests_passed += 1
        else:
            print("❌ FAIL: Invalid YAML syntax should have been detected")
            tests_failed += 1
        print()

    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir)

    print(
        f"Contract validation tests: {tests_passed}/{tests_passed + tests_failed} passed"
    )
    print()

    return tests_passed, tests_failed


def test_breaking_change_detection():
    """Test breaking change detection."""
    print("=" * 60)
    print("Testing Breaking Change Detection")
    print("=" * 60)
    print()

    if not YAML_AVAILABLE:
        print("⚠️  Skipping breaking change tests - PyYAML not available")
        return 0, 0

    tests_passed = 0
    tests_failed = 0

    # Create temporary directory for test contracts
    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Create v1 contract
        v1_contract = temp_dir / "api-v1.yaml"
        v1_contract.write_text("""
openapi: 3.0.0
info:
  title: Test API
  version: 1.0.0
paths:
  /users:
    get:
      summary: Get users
      parameters:
        - name: id
          in: query
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: Success
    post:
      summary: Create user
      parameters:
        - name: name
          in: body
          required: true
          schema:
            type: string
      responses:
        '201':
          description: Created
  /posts:
    get:
      summary: Get posts
      responses:
        '200':
          description: Success
""")

        # Test 1: Removed endpoint detection
        print("Test 1: Removed endpoint detection")
        v2_removed_endpoint = temp_dir / "api-v2-removed-endpoint.yaml"
        v2_removed_endpoint.write_text("""
openapi: 3.0.0
info:
  title: Test API
  version: 2.0.0
paths:
  /users:
    get:
      summary: Get users
      parameters:
        - name: id
          in: query
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: Success
""")

        work_item = {"id": "TEST-001", "api_contracts": []}
        validator = APIContractValidator(work_item)

        changes = validator._detect_breaking_changes(
            str(v2_removed_endpoint), str(v1_contract)
        )

        removed_endpoint = any(
            c["type"] == "removed_endpoint" and "/posts" in c["path"] for c in changes
        )
        if removed_endpoint:
            print("✅ PASS: Removed endpoint detected")
            tests_passed += 1
        else:
            print("❌ FAIL: Removed endpoint not detected")
            tests_failed += 1
        print()

        # Test 2: Removed HTTP method detection
        print("Test 2: Removed HTTP method detection")
        v2_removed_method = temp_dir / "api-v2-removed-method.yaml"
        v2_removed_method.write_text("""
openapi: 3.0.0
info:
  title: Test API
  version: 2.0.0
paths:
  /users:
    get:
      summary: Get users
      parameters:
        - name: id
          in: query
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: Success
  /posts:
    get:
      summary: Get posts
      responses:
        '200':
          description: Success
""")

        changes = validator._detect_breaking_changes(
            str(v2_removed_method), str(v1_contract)
        )

        removed_method = any(
            c["type"] == "removed_method"
            and c["method"] == "POST"
            and "/users" in c["path"]
            for c in changes
        )
        if removed_method:
            print("✅ PASS: Removed HTTP method detected")
            tests_passed += 1
        else:
            print("❌ FAIL: Removed HTTP method not detected")
            tests_failed += 1
        print()

        # Test 3: Removed required parameter detection
        print("Test 3: Removed required parameter detection")
        v2_removed_param = temp_dir / "api-v2-removed-param.yaml"
        v2_removed_param.write_text("""
openapi: 3.0.0
info:
  title: Test API
  version: 2.0.0
paths:
  /users:
    get:
      summary: Get users
      parameters: []
      responses:
        '200':
          description: Success
    post:
      summary: Create user
      parameters:
        - name: name
          in: body
          required: true
          schema:
            type: string
      responses:
        '201':
          description: Created
  /posts:
    get:
      summary: Get posts
      responses:
        '200':
          description: Success
""")

        changes = validator._detect_breaking_changes(
            str(v2_removed_param), str(v1_contract)
        )

        removed_param = any(
            c["type"] == "removed_required_parameter" and c["parameter"] == "id"
            for c in changes
        )
        if removed_param:
            print("✅ PASS: Removed required parameter detected")
            tests_passed += 1
        else:
            print("❌ FAIL: Removed required parameter not detected")
            tests_failed += 1
        print()

        # Test 4: Added required parameter detection
        print("Test 4: Added required parameter detection")
        v2_added_param = temp_dir / "api-v2-added-param.yaml"
        v2_added_param.write_text("""
openapi: 3.0.0
info:
  title: Test API
  version: 2.0.0
paths:
  /users:
    get:
      summary: Get users
      parameters:
        - name: id
          in: query
          required: true
          schema:
            type: integer
        - name: email
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Success
    post:
      summary: Create user
      parameters:
        - name: name
          in: body
          required: true
          schema:
            type: string
      responses:
        '201':
          description: Created
  /posts:
    get:
      summary: Get posts
      responses:
        '200':
          description: Success
""")

        changes = validator._detect_breaking_changes(
            str(v2_added_param), str(v1_contract)
        )

        added_param = any(
            c["type"] == "added_required_parameter" and c["parameter"] == "email"
            for c in changes
        )
        if added_param:
            print("✅ PASS: Added required parameter detected")
            tests_passed += 1
        else:
            print("❌ FAIL: Added required parameter not detected")
            tests_failed += 1
        print()

        # Test 5: No breaking changes
        print("Test 5: No breaking changes (backward compatible)")
        v2_compatible = temp_dir / "api-v2-compatible.yaml"
        v2_compatible.write_text("""
openapi: 3.0.0
info:
  title: Test API
  version: 2.0.0
paths:
  /users:
    get:
      summary: Get users
      parameters:
        - name: id
          in: query
          required: true
          schema:
            type: integer
        - name: email
          in: query
          required: false
          schema:
            type: string
      responses:
        '200':
          description: Success
    post:
      summary: Create user
      parameters:
        - name: name
          in: body
          required: true
          schema:
            type: string
      responses:
        '201':
          description: Created
  /posts:
    get:
      summary: Get posts
      responses:
        '200':
          description: Success
  /comments:
    get:
      summary: Get comments
      responses:
        '200':
          description: Success
""")

        changes = validator._detect_breaking_changes(
            str(v2_compatible), str(v1_contract)
        )

        if len(changes) == 0:
            print("✅ PASS: No breaking changes detected for backward compatible API")
            tests_passed += 1
        else:
            print(f"❌ FAIL: Should not detect breaking changes, found {len(changes)}")
            tests_failed += 1
        print()

    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir)

    print(
        f"Breaking change detection tests: {tests_passed}/{tests_passed + tests_failed} passed"
    )
    print()

    return tests_passed, tests_failed


def test_report_generation():
    """Test report generation."""
    print("=" * 60)
    print("Testing Report Generation")
    print("=" * 60)
    print()

    tests_passed = 0
    tests_failed = 0

    # Test 1: Report with breaking changes
    print("Test 1: Report with breaking changes")
    work_item = {"id": "TEST-001", "api_contracts": []}
    validator = APIContractValidator(work_item)

    validator.results = {
        "contracts_validated": 2,
        "breaking_changes": [
            {
                "type": "removed_endpoint",
                "path": "/users",
                "severity": "high",
                "message": "Endpoint removed: /users",
            }
        ],
        "warnings": [],
        "passed": False,
    }

    report = validator.generate_report()
    if (
        "Contracts Validated: 2" in report
        and "Breaking Changes: 1" in report
        and "FAILED" in report
    ):
        print("✅ PASS: Report with breaking changes generated correctly")
        tests_passed += 1
    else:
        print("❌ FAIL: Report missing expected content")
        tests_failed += 1
    print()

    # Test 2: Report with no breaking changes
    print("Test 2: Report with no breaking changes")
    validator.results = {
        "contracts_validated": 3,
        "breaking_changes": [],
        "warnings": ["Optional parameter added"],
        "passed": True,
    }

    report = validator.generate_report()
    if (
        "Contracts Validated: 3" in report
        and "Breaking Changes: 0" in report
        and "PASSED" in report
    ):
        print("✅ PASS: Report with no breaking changes generated correctly")
        tests_passed += 1
    else:
        print("❌ FAIL: Report missing expected content")
        tests_failed += 1
    print()

    print(
        f"Report generation tests: {tests_passed}/{tests_passed + tests_failed} passed"
    )
    print()

    return tests_passed, tests_failed


def test_file_structure():
    """Test that the api_contract_validator.py file exists and is properly structured."""
    print("=" * 60)
    print("Testing File Structure")
    print("=" * 60)
    print()

    tests_passed = 0
    tests_failed = 0

    # Test 1: File exists
    print("Test 1: api_contract_validator.py file exists")
    file_path = Path("scripts/api_contract_validator.py")
    if file_path.exists():
        print("✅ PASS: File exists")
        tests_passed += 1
    else:
        print("❌ FAIL: File not found")
        tests_failed += 1
        return tests_passed, tests_failed
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
        "import json",
        "import yaml",
        "from pathlib import Path",
        "from typing import",
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

    # Test 4: APIContractValidator class defined
    print("Test 4: APIContractValidator class defined")
    if "class APIContractValidator:" in content:
        print("✅ PASS: APIContractValidator class defined")
        tests_passed += 1
    else:
        print("❌ FAIL: APIContractValidator class not found")
        tests_failed += 1
    print()

    # Test 5: Check for main function
    print("Test 5: main() function defined")
    if "def main():" in content:
        print("✅ PASS: main() function defined")
        tests_passed += 1
    else:
        print("❌ FAIL: main() function not found")
        tests_failed += 1
    print()

    print(f"File structure tests: {tests_passed}/{tests_passed + tests_failed} passed")
    print()

    return tests_passed, tests_failed


if __name__ == "__main__":
    print()
    print("#" * 60)
    print("# Phase 5.5.4 Test Suite")
    print("# API Contract Validation")
    print("#" * 60)
    print()

    total_passed = 0
    total_failed = 0

    # File structure tests
    passed, failed = test_file_structure()
    total_passed += passed
    total_failed += failed
    print()

    # Basic class tests
    passed, failed = test_api_contract_validator_class()
    total_passed += passed
    total_failed += failed
    print()

    # Contract file validation tests
    passed, failed = test_contract_file_validation()
    total_passed += passed
    total_failed += failed
    print()

    # Breaking change detection tests
    passed, failed = test_breaking_change_detection()
    total_passed += passed
    total_failed += failed
    print()

    # Report generation tests
    passed, failed = test_report_generation()
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
        print("✅ Phase 5.5.4 - ALL TESTS PASSED")
        print("=" * 60)
        sys.exit(0)
    else:
        print("=" * 60)
        print("❌ Phase 5.5.4 - SOME TESTS FAILED")
        print("=" * 60)
        sys.exit(1)
