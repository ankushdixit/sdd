"""Unit tests for api_contract_validator module.

This module tests the APIContractValidator class which validates OpenAPI/Swagger
specifications and detects breaking changes between contract versions.
"""

import json
from pathlib import Path

from scripts.api_contract_validator import APIContractValidator


class TestAPIContractValidatorInit:
    """Tests for APIContractValidator initialization."""

    def test_init_with_api_contracts(self):
        """Test that APIContractValidator initializes with valid work item containing contracts."""
        # Arrange
        work_item = {
            "id": "INTEG-001",
            "type": "integration_test",
            "title": "API Contract Test",
            "api_contracts": [{"contract_file": "contracts/api-v1.yaml", "version": "1.0.0"}],
        }

        # Act
        validator = APIContractValidator(work_item)

        # Assert
        assert validator.work_item == work_item
        assert len(validator.contracts) == 1
        assert validator.contracts[0]["version"] == "1.0.0"
        assert validator.results["contracts_validated"] == 0
        assert validator.results["passed"] is False
        assert validator.results["breaking_changes"] == []
        assert validator.results["warnings"] == []

    def test_init_without_api_contracts(self):
        """Test that initialization works when work item has no api_contracts."""
        # Arrange
        work_item = {"id": "INTEG-002", "type": "integration_test"}

        # Act
        validator = APIContractValidator(work_item)

        # Assert
        assert validator.contracts == []

    def test_init_results_dictionary_initialized(self):
        """Test that results dictionary is initialized with all required keys."""
        # Arrange
        work_item = {"id": "INTEG-003"}

        # Act
        validator = APIContractValidator(work_item)

        # Assert
        expected_keys = ["contracts_validated", "breaking_changes", "warnings", "passed"]
        assert all(key in validator.results for key in expected_keys)


class TestContractFileValidation:
    """Tests for OpenAPI/Swagger contract file validation."""

    def test_validate_contract_file_missing_file(self):
        """Test validation fails when contract file does not exist."""
        # Arrange
        work_item = {"id": "INTEG-004"}
        validator = APIContractValidator(work_item)

        # Act
        result = validator._validate_contract_file("/nonexistent/contract.yaml")

        # Assert
        assert result is False

    def test_validate_contract_file_valid_yaml(self, tmp_path):
        """Test validation passes for valid OpenAPI YAML file."""
        # Arrange
        work_item = {"id": "INTEG-005"}
        validator = APIContractValidator(work_item)

        valid_yaml = tmp_path / "valid-api.yaml"
        valid_yaml.write_text("""
openapi: 3.0.0
info:
  title: Test API
  version: 1.0.0
paths:
  /users:
    get:
      summary: Get users
      responses:
        '200':
          description: Success
""")

        # Act
        result = validator._validate_contract_file(str(valid_yaml))

        # Assert
        assert result is True

    def test_validate_contract_file_valid_json(self, tmp_path):
        """Test validation passes for valid OpenAPI JSON file."""
        # Arrange
        work_item = {"id": "INTEG-006"}
        validator = APIContractValidator(work_item)

        valid_json = tmp_path / "valid-api.json"
        valid_json.write_text(
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
                }
            )
        )

        # Act
        result = validator._validate_contract_file(str(valid_json))

        # Assert
        assert result is True

    def test_validate_contract_file_missing_paths(self, tmp_path):
        """Test validation fails when contract is missing required 'paths' field."""
        # Arrange
        work_item = {"id": "INTEG-007"}
        validator = APIContractValidator(work_item)

        invalid_yaml = tmp_path / "invalid-api.yaml"
        invalid_yaml.write_text("""
openapi: 3.0.0
info:
  title: Test API
  version: 1.0.0
""")

        # Act
        result = validator._validate_contract_file(str(invalid_yaml))

        # Assert
        assert result is False

    def test_validate_contract_file_invalid_yaml_syntax(self, tmp_path):
        """Test validation fails for invalid YAML syntax."""
        # Arrange
        work_item = {"id": "INTEG-008"}
        validator = APIContractValidator(work_item)

        invalid_yaml = tmp_path / "invalid-syntax.yaml"
        invalid_yaml.write_text("not: valid: yaml: [unclosed")

        # Act
        result = validator._validate_contract_file(str(invalid_yaml))

        # Assert
        assert result is False

    def test_validate_contract_file_missing_openapi_field(self, tmp_path):
        """Test validation fails when missing both 'openapi' and 'swagger' fields."""
        # Arrange
        work_item = {"id": "INTEG-009"}
        validator = APIContractValidator(work_item)

        invalid_yaml = tmp_path / "no-openapi.yaml"
        invalid_yaml.write_text("""
info:
  title: Test API
  version: 1.0.0
paths:
  /users:
    get:
      summary: Get users
""")

        # Act
        result = validator._validate_contract_file(str(invalid_yaml))

        # Assert
        assert result is False


class TestBreakingChangeDetection:
    """Tests for detecting breaking changes between contract versions."""

    def test_detect_breaking_changes_removed_endpoint(self, tmp_path):
        """Test that removed endpoints are detected as breaking changes."""
        # Arrange
        work_item = {"id": "INTEG-010"}
        validator = APIContractValidator(work_item)

        v1_contract = tmp_path / "api-v1.yaml"
        v1_contract.write_text("""
openapi: 3.0.0
info:
  version: 1.0.0
paths:
  /users:
    get:
      responses:
        '200':
          description: Success
  /posts:
    get:
      responses:
        '200':
          description: Success
""")

        v2_contract = tmp_path / "api-v2.yaml"
        v2_contract.write_text("""
openapi: 3.0.0
info:
  version: 2.0.0
paths:
  /users:
    get:
      responses:
        '200':
          description: Success
""")

        # Act
        changes = validator._detect_breaking_changes(str(v2_contract), str(v1_contract))

        # Assert
        assert len(changes) == 1
        assert changes[0]["type"] == "removed_endpoint"
        assert changes[0]["path"] == "/posts"
        assert changes[0]["severity"] == "high"

    def test_detect_breaking_changes_removed_http_method(self, tmp_path):
        """Test that removed HTTP methods are detected as breaking changes."""
        # Arrange
        work_item = {"id": "INTEG-011"}
        validator = APIContractValidator(work_item)

        v1_contract = tmp_path / "api-v1.yaml"
        v1_contract.write_text("""
openapi: 3.0.0
paths:
  /users:
    get:
      responses:
        '200':
          description: Success
    post:
      responses:
        '201':
          description: Created
""")

        v2_contract = tmp_path / "api-v2.yaml"
        v2_contract.write_text("""
openapi: 3.0.0
paths:
  /users:
    get:
      responses:
        '200':
          description: Success
""")

        # Act
        changes = validator._detect_breaking_changes(str(v2_contract), str(v1_contract))

        # Assert
        assert len(changes) == 1
        assert changes[0]["type"] == "removed_method"
        assert changes[0]["method"] == "POST"
        assert changes[0]["path"] == "/users"

    def test_detect_breaking_changes_removed_required_parameter(self, tmp_path):
        """Test that removed required parameters are detected as breaking changes."""
        # Arrange
        work_item = {"id": "INTEG-012"}
        validator = APIContractValidator(work_item)

        v1_contract = tmp_path / "api-v1.yaml"
        v1_contract.write_text("""
openapi: 3.0.0
paths:
  /users:
    get:
      parameters:
        - name: id
          required: true
          in: query
      responses:
        '200':
          description: Success
""")

        v2_contract = tmp_path / "api-v2.yaml"
        v2_contract.write_text("""
openapi: 3.0.0
paths:
  /users:
    get:
      parameters: []
      responses:
        '200':
          description: Success
""")

        # Act
        changes = validator._detect_breaking_changes(str(v2_contract), str(v1_contract))

        # Assert
        assert len(changes) == 1
        assert changes[0]["type"] == "removed_required_parameter"
        assert changes[0]["parameter"] == "id"

    def test_detect_breaking_changes_added_required_parameter(self, tmp_path):
        """Test that new required parameters are detected as breaking changes."""
        # Arrange
        work_item = {"id": "INTEG-013"}
        validator = APIContractValidator(work_item)

        v1_contract = tmp_path / "api-v1.yaml"
        v1_contract.write_text("""
openapi: 3.0.0
paths:
  /users:
    get:
      parameters: []
      responses:
        '200':
          description: Success
""")

        v2_contract = tmp_path / "api-v2.yaml"
        v2_contract.write_text("""
openapi: 3.0.0
paths:
  /users:
    get:
      parameters:
        - name: token
          required: true
          in: header
      responses:
        '200':
          description: Success
""")

        # Act
        changes = validator._detect_breaking_changes(str(v2_contract), str(v1_contract))

        # Assert
        assert len(changes) == 1
        assert changes[0]["type"] == "added_required_parameter"
        assert changes[0]["parameter"] == "token"

    def test_detect_breaking_changes_parameter_became_required(self, tmp_path):
        """Test that optional parameters becoming required are detected as breaking changes."""
        # Arrange
        work_item = {"id": "INTEG-014"}
        validator = APIContractValidator(work_item)

        v1_contract = tmp_path / "api-v1.yaml"
        v1_contract.write_text("""
openapi: 3.0.0
paths:
  /users:
    get:
      parameters:
        - name: limit
          required: false
          in: query
      responses:
        '200':
          description: Success
""")

        v2_contract = tmp_path / "api-v2.yaml"
        v2_contract.write_text("""
openapi: 3.0.0
paths:
  /users:
    get:
      parameters:
        - name: limit
          required: true
          in: query
      responses:
        '200':
          description: Success
""")

        # Act
        changes = validator._detect_breaking_changes(str(v2_contract), str(v1_contract))

        # Assert
        assert len(changes) == 1
        assert changes[0]["type"] == "parameter_now_required"
        assert changes[0]["parameter"] == "limit"

    def test_detect_breaking_changes_no_changes(self, tmp_path):
        """Test that no breaking changes are detected for identical contracts."""
        # Arrange
        work_item = {"id": "INTEG-015"}
        validator = APIContractValidator(work_item)

        contract = tmp_path / "api.yaml"
        contract.write_text("""
openapi: 3.0.0
paths:
  /users:
    get:
      responses:
        '200':
          description: Success
""")

        # Act
        changes = validator._detect_breaking_changes(str(contract), str(contract))

        # Assert
        assert len(changes) == 0


class TestReportGeneration:
    """Tests for API contract validation report generation."""

    def test_generate_report_with_breaking_changes(self):
        """Test report generation when breaking changes are detected."""
        # Arrange
        work_item = {"id": "INTEG-016"}
        validator = APIContractValidator(work_item)
        validator.results = {
            "contracts_validated": 2,
            "breaking_changes": [
                {
                    "type": "removed_endpoint",
                    "path": "/old-endpoint",
                    "severity": "high",
                    "message": "Endpoint removed: /old-endpoint",
                }
            ],
            "warnings": [],
            "passed": False,
        }

        # Act
        report = validator.generate_report()

        # Assert
        assert "API Contract Validation Report" in report
        assert "Contracts Validated: 2" in report
        assert "Breaking Changes: 1" in report
        assert "Endpoint removed: /old-endpoint" in report
        assert "FAILED" in report

    def test_generate_report_with_warnings(self):
        """Test report generation with warnings."""
        # Arrange
        work_item = {"id": "INTEG-017"}
        validator = APIContractValidator(work_item)
        validator.results = {
            "contracts_validated": 1,
            "breaking_changes": [],
            "warnings": ["Deprecated endpoint usage detected"],
            "passed": True,
        }

        # Act
        report = validator.generate_report()

        # Assert
        assert "Warnings:" in report
        assert "Deprecated endpoint usage detected" in report
        assert "PASSED" in report

    def test_generate_report_no_issues(self):
        """Test report generation when all contracts pass."""
        # Arrange
        work_item = {"id": "INTEG-018"}
        validator = APIContractValidator(work_item)
        validator.results = {
            "contracts_validated": 3,
            "breaking_changes": [],
            "warnings": [],
            "passed": True,
        }

        # Act
        report = validator.generate_report()

        # Assert
        assert "Contracts Validated: 3" in report
        assert "Breaking Changes: 0" in report
        assert "PASSED" in report


class TestFileStructure:
    """Tests for file structure and presence."""

    def test_api_contract_validator_file_exists(self):
        """Test that api_contract_validator.py file exists."""
        # Arrange & Act
        file_path = Path("scripts/api_contract_validator.py")

        # Assert
        assert file_path.exists()

    def test_api_contract_validator_class_defined(self):
        """Test that APIContractValidator class is defined."""
        # Arrange
        file_path = Path("scripts/api_contract_validator.py")
        content = file_path.read_text()

        # Act & Assert
        assert "class APIContractValidator:" in content

    def test_api_contract_validator_has_required_methods(self):
        """Test that APIContractValidator class has all required methods."""
        # Arrange
        work_item = {"id": "INTEG-019"}
        validator = APIContractValidator(work_item)

        required_methods = [
            "validate_contracts",
            "_validate_contract_file",
            "_detect_breaking_changes",
            "_load_spec",
            "_check_endpoint_changes",
            "_check_parameter_changes",
            "generate_report",
        ]

        # Act & Assert
        for method in required_methods:
            assert hasattr(validator, method), f"Missing method: {method}"

    def test_api_contract_validator_has_required_imports(self):
        """Test that api_contract_validator.py has required imports."""
        # Arrange
        file_path = Path("scripts/api_contract_validator.py")
        content = file_path.read_text()

        required_imports = [
            "import json",
            "import yaml",
            "from pathlib import Path",
            "from scripts.file_ops import",
        ]

        # Act & Assert
        for imp in required_imports:
            assert imp in content, f"Missing import: {imp}"

    def test_api_contract_validator_has_main_function(self):
        """Test that api_contract_validator.py has main function."""
        # Arrange
        file_path = Path("scripts/api_contract_validator.py")
        content = file_path.read_text()

        # Act & Assert
        assert "def main():" in content


class TestContractValidation:
    """Tests for the complete contract validation workflow."""

    def test_validate_contracts_all_valid(self, tmp_path):
        """Test validation succeeds when all contracts are valid."""
        # Arrange
        contract = tmp_path / "api.yaml"
        contract.write_text("""
openapi: 3.0.0
info:
  title: Test API
  version: 1.0.0
paths:
  /test:
    get:
      responses:
        '200':
          description: Success
""")

        work_item = {"id": "INTEG-020", "api_contracts": [{"contract_file": str(contract)}]}
        validator = APIContractValidator(work_item)

        # Act
        passed, results = validator.validate_contracts()

        # Assert
        assert passed is True
        assert results["contracts_validated"] == 1
        assert results["passed"] is True

    def test_validate_contracts_with_breaking_changes_not_allowed(self, tmp_path):
        """Test validation fails when breaking changes detected and not allowed."""
        # Arrange
        v1 = tmp_path / "v1.yaml"
        v1.write_text("""
openapi: 3.0.0
paths:
  /users:
    get:
      responses:
        '200':
          description: Success
  /posts:
    get:
      responses:
        '200':
          description: Success
""")

        v2 = tmp_path / "v2.yaml"
        v2.write_text("""
openapi: 3.0.0
paths:
  /users:
    get:
      responses:
        '200':
          description: Success
""")

        work_item = {
            "id": "INTEG-021",
            "api_contracts": [
                {
                    "contract_file": str(v2),
                    "previous_version": str(v1),
                    "allow_breaking_changes": False,
                }
            ],
        }
        validator = APIContractValidator(work_item)

        # Act
        passed, results = validator.validate_contracts()

        # Assert
        assert passed is False
        assert len(results["breaking_changes"]) > 0

    def test_validate_contracts_with_breaking_changes_allowed(self, tmp_path):
        """Test validation succeeds when breaking changes allowed."""
        # Arrange
        v1 = tmp_path / "v1.yaml"
        v1.write_text("""
openapi: 3.0.0
paths:
  /users:
    get:
      responses:
        '200':
          description: Success
  /posts:
    get:
      responses:
        '200':
          description: Success
""")

        v2 = tmp_path / "v2.yaml"
        v2.write_text("""
openapi: 3.0.0
paths:
  /users:
    get:
      responses:
        '200':
          description: Success
""")

        work_item = {
            "id": "INTEG-022",
            "api_contracts": [
                {
                    "contract_file": str(v2),
                    "previous_version": str(v1),
                    "allow_breaking_changes": True,
                }
            ],
        }
        validator = APIContractValidator(work_item)

        # Act
        passed, results = validator.validate_contracts()

        # Assert
        assert passed is True
        assert len(results["breaking_changes"]) > 0  # Changes detected but allowed

    def test_validate_contracts_invalid_file(self):
        """Test validation fails when contract file is invalid."""
        # Arrange
        work_item = {
            "id": "INTEG-023",
            "api_contracts": [{"contract_file": "/nonexistent/contract.yaml"}],
        }
        validator = APIContractValidator(work_item)

        # Act
        passed, results = validator.validate_contracts()

        # Assert
        assert passed is False
        assert results["contracts_validated"] == 0
