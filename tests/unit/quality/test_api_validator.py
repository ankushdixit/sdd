#!/usr/bin/env python3
"""
Unit tests for APIContractValidator.

Tests API contract validation, OpenAPI/Swagger spec parsing,
breaking change detection, and report generation.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from solokit.core.exceptions import (
    FileNotFoundError as SolokitFileNotFoundError,
)
from solokit.core.exceptions import (
    FileOperationError,
    InvalidOpenAPISpecError,
    SchemaValidationError,
    WorkItemNotFoundError,
)
from solokit.quality.api_validator import APIContractValidator, main


class TestAPIContractValidatorInit:
    """Test APIContractValidator initialization."""

    def test_init_with_valid_work_item(self):
        """Should initialize with valid work item."""
        work_item = {"id": "WI-001", "api_contracts": []}
        validator = APIContractValidator(work_item)

        assert validator.work_item == work_item
        assert validator.contracts == []
        assert validator.results["contracts_validated"] == 0
        assert validator.results["breaking_changes"] == []
        assert validator.results["warnings"] == []
        assert validator.results["passed"] is False

    def test_init_with_contracts(self):
        """Should extract contracts from work item."""
        work_item = {
            "api_contracts": [{"contract_file": "api.yaml"}, {"contract_file": "openapi.json"}]
        }
        validator = APIContractValidator(work_item)

        assert len(validator.contracts) == 2
        assert validator.contracts[0]["contract_file"] == "api.yaml"

    def test_init_without_contracts(self):
        """Should handle work item without api_contracts field."""
        work_item = {"id": "WI-001"}
        validator = APIContractValidator(work_item)

        assert validator.contracts == []


class TestValidateContractFile:
    """Test contract file validation."""

    def test_validate_openapi_yaml_file(self):
        """Should validate OpenAPI YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_file = Path(tmpdir) / "api.yaml"
            contract_data = {
                "openapi": "3.0.0",
                "info": {"title": "Test API", "version": "1.0.0"},
                "paths": {"/users": {"get": {"summary": "Get users"}}},
            }
            contract_file.write_text(yaml.dump(contract_data))

            work_item = {"api_contracts": []}
            validator = APIContractValidator(work_item)

            # Should not raise exception
            validator._validate_contract_file(str(contract_file))

    def test_validate_swagger_json_file(self):
        """Should validate Swagger JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_file = Path(tmpdir) / "api.json"
            contract_data = {
                "swagger": "2.0",
                "info": {"title": "Test API", "version": "1.0.0"},
                "paths": {"/users": {"get": {"summary": "Get users"}}},
            }
            contract_file.write_text(json.dumps(contract_data))

            work_item = {"api_contracts": []}
            validator = APIContractValidator(work_item)

            # Should not raise exception
            validator._validate_contract_file(str(contract_file))

    def test_validate_contract_file_not_found(self):
        """Should raise FileNotFoundError if contract file doesn't exist."""
        work_item = {"api_contracts": []}
        validator = APIContractValidator(work_item)

        with pytest.raises(SolokitFileNotFoundError) as exc_info:
            validator._validate_contract_file("/nonexistent/api.yaml")

        assert "api.yaml" in str(exc_info.value)
        assert exc_info.value.context["file_type"] == "API contract"

    def test_validate_contract_invalid_json(self):
        """Should raise SchemaValidationError for invalid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_file = Path(tmpdir) / "api.json"
            contract_file.write_text("{ invalid json }")

            work_item = {"api_contracts": []}
            validator = APIContractValidator(work_item)

            with pytest.raises(SchemaValidationError) as exc_info:
                validator._validate_contract_file(str(contract_file))

            assert "Failed to parse contract file" in exc_info.value.context["details"]

    def test_validate_contract_invalid_yaml(self):
        """Should raise SchemaValidationError for invalid YAML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_file = Path(tmpdir) / "api.yaml"
            contract_file.write_text("invalid: yaml: content:")

            work_item = {"api_contracts": []}
            validator = APIContractValidator(work_item)

            with pytest.raises(SchemaValidationError):
                validator._validate_contract_file(str(contract_file))

    def test_validate_contract_missing_openapi_field(self):
        """Should raise InvalidOpenAPISpecError if openapi/swagger field missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_file = Path(tmpdir) / "api.yaml"
            contract_data = {"info": {"title": "Test API"}, "paths": {}}
            contract_file.write_text(yaml.dump(contract_data))

            work_item = {"api_contracts": []}
            validator = APIContractValidator(work_item)

            with pytest.raises(InvalidOpenAPISpecError) as exc_info:
                validator._validate_contract_file(str(contract_file))

            assert "Missing 'openapi' or 'swagger' field" in exc_info.value.context["details"]

    def test_validate_contract_missing_paths_field(self):
        """Should raise SchemaValidationError if paths field missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_file = Path(tmpdir) / "api.yaml"
            contract_data = {"openapi": "3.0.0", "info": {"title": "Test API"}}
            contract_file.write_text(yaml.dump(contract_data))

            work_item = {"api_contracts": []}
            validator = APIContractValidator(work_item)

            with pytest.raises(SchemaValidationError) as exc_info:
                validator._validate_contract_file(str(contract_file))

            assert "Missing 'paths' field" in exc_info.value.context["details"]

    def test_validate_contract_file_read_error(self):
        """Should raise FileOperationError on file read error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_file = Path(tmpdir) / "api.json"
            contract_file.write_text('{"openapi": "3.0.0", "paths": {}}')

            work_item = {"api_contracts": []}
            validator = APIContractValidator(work_item)

            with patch("builtins.open", side_effect=OSError("Permission denied")):
                with pytest.raises(FileOperationError) as exc_info:
                    validator._validate_contract_file(str(contract_file))

                assert exc_info.value.context["operation"] == "read"


class TestValidateContracts:
    """Test validate_contracts method."""

    def test_validate_contracts_empty_list(self):
        """Should pass with no contracts."""
        work_item = {"api_contracts": []}
        validator = APIContractValidator(work_item)

        passed, results = validator.validate_contracts()

        assert passed is True
        assert results["contracts_validated"] == 0
        assert results["breaking_changes"] == []

    def test_validate_contracts_single_valid_contract(self):
        """Should validate single valid contract."""
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_file = Path(tmpdir) / "api.yaml"
            contract_data = {
                "openapi": "3.0.0",
                "info": {"title": "Test API", "version": "1.0.0"},
                "paths": {"/users": {"get": {"summary": "Get users"}}},
            }
            contract_file.write_text(yaml.dump(contract_data))

            work_item = {"api_contracts": [{"contract_file": str(contract_file)}]}
            validator = APIContractValidator(work_item)

            passed, results = validator.validate_contracts()

            assert passed is True
            assert results["contracts_validated"] == 1

    def test_validate_contracts_multiple_contracts(self):
        """Should validate multiple contracts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            contract1 = Path(tmpdir) / "api1.yaml"
            contract2 = Path(tmpdir) / "api2.json"

            contract_data1 = {
                "openapi": "3.0.0",
                "info": {"title": "API 1"},
                "paths": {"/users": {}},
            }
            contract_data2 = {
                "swagger": "2.0",
                "info": {"title": "API 2"},
                "paths": {"/products": {}},
            }

            contract1.write_text(yaml.dump(contract_data1))
            contract2.write_text(json.dumps(contract_data2))

            work_item = {
                "api_contracts": [
                    {"contract_file": str(contract1)},
                    {"contract_file": str(contract2)},
                ]
            }
            validator = APIContractValidator(work_item)

            passed, results = validator.validate_contracts()

            assert passed is True
            assert results["contracts_validated"] == 2

    def test_validate_contracts_with_validation_error(self):
        """Should fail if contract validation fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_file = Path(tmpdir) / "api.yaml"
            # Missing paths field
            contract_data = {"openapi": "3.0.0", "info": {"title": "Test API"}}
            contract_file.write_text(yaml.dump(contract_data))

            work_item = {"api_contracts": [{"contract_file": str(contract_file)}]}
            validator = APIContractValidator(work_item)

            passed, results = validator.validate_contracts()

            assert passed is False
            assert results["contracts_validated"] == 0

    def test_validate_contracts_skips_missing_contract_file(self):
        """Should skip contracts without contract_file field."""
        work_item = {
            "api_contracts": [
                {},  # No contract_file
                {"name": "API Contract"},  # No contract_file
            ]
        }
        validator = APIContractValidator(work_item)

        passed, results = validator.validate_contracts()

        assert passed is True
        assert results["contracts_validated"] == 0


class TestDetectBreakingChanges:
    """Test breaking change detection."""

    def test_detect_removed_endpoint(self):
        """Should detect removed endpoints as breaking changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            previous_file = Path(tmpdir) / "previous.yaml"
            current_file = Path(tmpdir) / "current.yaml"

            previous_data = {
                "openapi": "3.0.0",
                "paths": {"/users": {"get": {}}, "/products": {"get": {}}},
            }
            current_data = {"openapi": "3.0.0", "paths": {"/users": {"get": {}}}}

            previous_file.write_text(yaml.dump(previous_data))
            current_file.write_text(yaml.dump(current_data))

            work_item = {"api_contracts": []}
            validator = APIContractValidator(work_item)

            changes = validator._detect_breaking_changes(str(current_file), str(previous_file))

            assert len(changes) > 0
            assert any(c["type"] == "removed_endpoint" for c in changes)
            assert any("/products" in c["path"] for c in changes)

    def test_detect_removed_http_method(self):
        """Should detect removed HTTP methods as breaking changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            previous_file = Path(tmpdir) / "previous.yaml"
            current_file = Path(tmpdir) / "current.yaml"

            previous_data = {
                "openapi": "3.0.0",
                "paths": {
                    "/users": {"get": {"summary": "Get users"}, "post": {"summary": "Create user"}}
                },
            }
            current_data = {
                "openapi": "3.0.0",
                "paths": {"/users": {"get": {"summary": "Get users"}}},
            }

            previous_file.write_text(yaml.dump(previous_data))
            current_file.write_text(yaml.dump(current_data))

            work_item = {"api_contracts": []}
            validator = APIContractValidator(work_item)

            changes = validator._detect_breaking_changes(str(current_file), str(previous_file))

            assert len(changes) > 0
            assert any(c["type"] == "removed_method" for c in changes)
            assert any(c["method"] == "POST" for c in changes)

    def test_detect_removed_required_parameter(self):
        """Should detect removed required parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            previous_file = Path(tmpdir) / "previous.yaml"
            current_file = Path(tmpdir) / "current.yaml"

            previous_data = {
                "openapi": "3.0.0",
                "paths": {"/users": {"get": {"parameters": [{"name": "id", "required": True}]}}},
            }
            current_data = {"openapi": "3.0.0", "paths": {"/users": {"get": {"parameters": []}}}}

            previous_file.write_text(yaml.dump(previous_data))
            current_file.write_text(yaml.dump(current_data))

            work_item = {"api_contracts": []}
            validator = APIContractValidator(work_item)

            changes = validator._detect_breaking_changes(str(current_file), str(previous_file))

            assert len(changes) > 0
            assert any(c["type"] == "removed_required_parameter" for c in changes)
            assert any(c["parameter"] == "id" for c in changes)

    def test_detect_added_required_parameter(self):
        """Should detect added required parameters as breaking changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            previous_file = Path(tmpdir) / "previous.yaml"
            current_file = Path(tmpdir) / "current.yaml"

            previous_data = {"openapi": "3.0.0", "paths": {"/users": {"get": {"parameters": []}}}}
            current_data = {
                "openapi": "3.0.0",
                "paths": {"/users": {"get": {"parameters": [{"name": "token", "required": True}]}}},
            }

            previous_file.write_text(yaml.dump(previous_data))
            current_file.write_text(yaml.dump(current_data))

            work_item = {"api_contracts": []}
            validator = APIContractValidator(work_item)

            changes = validator._detect_breaking_changes(str(current_file), str(previous_file))

            assert len(changes) > 0
            assert any(c["type"] == "added_required_parameter" for c in changes)
            assert any(c["parameter"] == "token" for c in changes)

    def test_detect_parameter_became_required(self):
        """Should detect when optional parameter becomes required."""
        with tempfile.TemporaryDirectory() as tmpdir:
            previous_file = Path(tmpdir) / "previous.yaml"
            current_file = Path(tmpdir) / "current.yaml"

            previous_data = {
                "openapi": "3.0.0",
                "paths": {
                    "/users": {"get": {"parameters": [{"name": "limit", "required": False}]}}
                },
            }
            current_data = {
                "openapi": "3.0.0",
                "paths": {"/users": {"get": {"parameters": [{"name": "limit", "required": True}]}}},
            }

            previous_file.write_text(yaml.dump(previous_data))
            current_file.write_text(yaml.dump(current_data))

            work_item = {"api_contracts": []}
            validator = APIContractValidator(work_item)

            changes = validator._detect_breaking_changes(str(current_file), str(previous_file))

            assert len(changes) > 0
            assert any(c["type"] == "parameter_now_required" for c in changes)

    def test_detect_no_breaking_changes(self):
        """Should return empty list when no breaking changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            previous_file = Path(tmpdir) / "previous.yaml"
            current_file = Path(tmpdir) / "current.yaml"

            data = {"openapi": "3.0.0", "paths": {"/users": {"get": {}}}}

            previous_file.write_text(yaml.dump(data))
            current_file.write_text(yaml.dump(data))

            work_item = {"api_contracts": []}
            validator = APIContractValidator(work_item)

            changes = validator._detect_breaking_changes(str(current_file), str(previous_file))

            assert len(changes) == 0

    def test_detect_breaking_changes_file_load_error(self):
        """Should handle file load errors gracefully."""
        work_item = {"api_contracts": []}
        validator = APIContractValidator(work_item)

        changes = validator._detect_breaking_changes(
            "/nonexistent/current.yaml", "/nonexistent/previous.yaml"
        )

        assert len(changes) > 0
        assert changes[0]["type"] == "load_error"


class TestValidateContractsWithBreakingChanges:
    """Test validate_contracts with breaking change detection."""

    def test_validate_with_breaking_changes_not_allowed(self):
        """Should fail when breaking changes detected and not allowed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            previous_file = Path(tmpdir) / "previous.yaml"
            current_file = Path(tmpdir) / "current.yaml"

            previous_data = {
                "openapi": "3.0.0",
                "paths": {"/users": {"get": {}}, "/products": {"get": {}}},
            }
            current_data = {"openapi": "3.0.0", "paths": {"/users": {"get": {}}}}

            previous_file.write_text(yaml.dump(previous_data))
            current_file.write_text(yaml.dump(current_data))

            work_item = {
                "api_contracts": [
                    {
                        "contract_file": str(current_file),
                        "previous_version": str(previous_file),
                        "allow_breaking_changes": False,
                    }
                ]
            }
            validator = APIContractValidator(work_item)

            passed, results = validator.validate_contracts()

            assert passed is False
            assert len(results["breaking_changes"]) > 0

    def test_validate_with_breaking_changes_allowed(self):
        """Should pass when breaking changes detected but allowed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            previous_file = Path(tmpdir) / "previous.yaml"
            current_file = Path(tmpdir) / "current.yaml"

            previous_data = {
                "openapi": "3.0.0",
                "paths": {"/users": {"get": {}}, "/products": {"get": {}}},
            }
            current_data = {"openapi": "3.0.0", "paths": {"/users": {"get": {}}}}

            previous_file.write_text(yaml.dump(previous_data))
            current_file.write_text(yaml.dump(current_data))

            work_item = {
                "api_contracts": [
                    {
                        "contract_file": str(current_file),
                        "previous_version": str(previous_file),
                        "allow_breaking_changes": True,
                    }
                ]
            }
            validator = APIContractValidator(work_item)

            passed, results = validator.validate_contracts()

            assert passed is True
            assert len(results["breaking_changes"]) > 0


class TestLoadSpec:
    """Test _load_spec method."""

    def test_load_yaml_spec(self):
        """Should load YAML spec file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_file = Path(tmpdir) / "api.yaml"
            spec_data = {"openapi": "3.0.0", "paths": {}}
            spec_file.write_text(yaml.dump(spec_data))

            work_item = {"api_contracts": []}
            validator = APIContractValidator(work_item)

            result = validator._load_spec(str(spec_file))

            assert result["openapi"] == "3.0.0"
            assert "paths" in result

    def test_load_json_spec(self):
        """Should load JSON spec file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_file = Path(tmpdir) / "api.json"
            spec_data = {"swagger": "2.0", "paths": {}}
            spec_file.write_text(json.dumps(spec_data))

            work_item = {"api_contracts": []}
            validator = APIContractValidator(work_item)

            result = validator._load_spec(str(spec_file))

            assert result["swagger"] == "2.0"
            assert "paths" in result

    def test_load_spec_file_not_found(self):
        """Should raise FileNotFoundError for missing file."""
        work_item = {"api_contracts": []}
        validator = APIContractValidator(work_item)

        with pytest.raises(SolokitFileNotFoundError):
            validator._load_spec("/nonexistent/api.yaml")

    def test_load_spec_invalid_json(self):
        """Should raise SchemaValidationError for invalid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_file = Path(tmpdir) / "api.json"
            spec_file.write_text("{ invalid }")

            work_item = {"api_contracts": []}
            validator = APIContractValidator(work_item)

            with pytest.raises(SchemaValidationError):
                validator._load_spec(str(spec_file))


class TestGenerateReport:
    """Test report generation."""

    def test_generate_report_no_contracts(self):
        """Should generate report with no contracts."""
        work_item = {"api_contracts": []}
        validator = APIContractValidator(work_item)
        validator.validate_contracts()

        report = validator.generate_report()

        assert "API Contract Validation Report" in report
        assert "Contracts Validated: 0" in report
        assert "PASSED" in report

    def test_generate_report_with_validated_contracts(self):
        """Should include validated contract count."""
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_file = Path(tmpdir) / "api.yaml"
            contract_data = {"openapi": "3.0.0", "info": {"title": "Test"}, "paths": {}}
            contract_file.write_text(yaml.dump(contract_data))

            work_item = {"api_contracts": [{"contract_file": str(contract_file)}]}
            validator = APIContractValidator(work_item)
            validator.validate_contracts()

            report = validator.generate_report()

            assert "Contracts Validated: 1" in report

    def test_generate_report_with_breaking_changes(self):
        """Should list breaking changes in report."""
        work_item = {"api_contracts": []}
        validator = APIContractValidator(work_item)
        validator.results["breaking_changes"] = [
            {
                "type": "removed_endpoint",
                "path": "/users",
                "severity": "high",
                "message": "Endpoint removed: /users",
            }
        ]

        report = validator.generate_report()

        assert "Breaking Changes Detected:" in report
        assert "Endpoint removed: /users" in report
        assert "HIGH" in report

    def test_generate_report_with_warnings(self):
        """Should list warnings in report."""
        work_item = {"api_contracts": []}
        validator = APIContractValidator(work_item)
        validator.results["warnings"] = ["Warning message 1", "Warning message 2"]
        validator.results["passed"] = True

        report = validator.generate_report()

        assert "Warnings:" in report
        assert "Warning message 1" in report
        assert "Warning message 2" in report

    def test_generate_report_failed_status(self):
        """Should show FAILED status when validation fails."""
        work_item = {"api_contracts": []}
        validator = APIContractValidator(work_item)
        validator.results["passed"] = False

        report = validator.generate_report()

        assert "FAILED" in report


class TestMainFunction:
    """Test main CLI entry point."""

    def test_main_missing_work_item_id(self, capsys):
        """Should exit with error if work item ID not provided."""
        with patch("sys.argv", ["api_validator.py"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

    def test_main_work_item_not_found(self):
        """Should raise WorkItemNotFoundError if work item doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            work_items_file = Path(tmpdir) / ".session" / "tracking" / "work_items.json"
            work_items_file.parent.mkdir(parents=True)
            work_items_file.write_text(json.dumps({"work_items": {}}))

            with patch("sys.argv", ["api_validator.py", "WI-999"]):
                with patch("solokit.quality.api_validator.Path") as mock_path:
                    mock_path.return_value = work_items_file

                    with pytest.raises(WorkItemNotFoundError) as exc_info:
                        main()

                    assert "WI-999" in str(exc_info.value)

    def test_main_successful_validation(self):
        """Should exit with 0 on successful validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_file = Path(tmpdir) / "api.yaml"
            contract_data = {"openapi": "3.0.0", "info": {"title": "Test"}, "paths": {}}
            contract_file.write_text(yaml.dump(contract_data))

            work_items_data = {
                "work_items": {"WI-001": {"api_contracts": [{"contract_file": str(contract_file)}]}}
            }

            with patch("sys.argv", ["api_validator.py", "WI-001"]):
                with patch("solokit.quality.api_validator.load_json") as mock_load:
                    mock_load.return_value = work_items_data

                    with pytest.raises(SystemExit) as exc_info:
                        main()

                    assert exc_info.value.code == 0


class TestCheckEndpointChanges:
    """Test _check_endpoint_changes method."""

    def test_check_endpoint_no_changes(self):
        """Should return empty list when no changes."""
        work_item = {"api_contracts": []}
        validator = APIContractValidator(work_item)

        previous = {"get": {"summary": "Get users"}}
        current = {"get": {"summary": "Get users"}}

        changes = validator._check_endpoint_changes("/users", previous, current)

        assert len(changes) == 0

    def test_check_endpoint_method_removed(self):
        """Should detect removed HTTP methods."""
        work_item = {"api_contracts": []}
        validator = APIContractValidator(work_item)

        previous = {"get": {"summary": "Get users"}, "post": {"summary": "Create user"}}
        current = {"get": {"summary": "Get users"}}

        changes = validator._check_endpoint_changes("/users", previous, current)

        assert len(changes) > 0
        assert changes[0]["type"] == "removed_method"
        assert changes[0]["method"] == "POST"


class TestCheckParameterChanges:
    """Test _check_parameter_changes method."""

    def test_check_parameter_no_changes(self):
        """Should return empty list when parameters unchanged."""
        work_item = {"api_contracts": []}
        validator = APIContractValidator(work_item)

        previous = {"parameters": [{"name": "id", "required": True}]}
        current = {"parameters": [{"name": "id", "required": True}]}

        changes = validator._check_parameter_changes("/users", "get", previous, current)

        assert len(changes) == 0

    def test_check_parameter_optional_added(self):
        """Should not flag added optional parameters."""
        work_item = {"api_contracts": []}
        validator = APIContractValidator(work_item)

        previous = {"parameters": [{"name": "id", "required": True}]}
        current = {
            "parameters": [{"name": "id", "required": True}, {"name": "limit", "required": False}]
        }

        changes = validator._check_parameter_changes("/users", "get", previous, current)

        # Optional parameter addition is not breaking
        assert len(changes) == 0
