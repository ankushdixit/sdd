#!/usr/bin/env python3
"""
API contract validation for integration tests.

Supports:
- OpenAPI/Swagger specification validation
- Breaking change detection
- Contract testing
- Version compatibility checking
"""

import json
import logging
from pathlib import Path
from typing import Any

import yaml

from solokit.core.error_handlers import convert_file_errors, log_errors
from solokit.core.exceptions import (
    BreakingChangeError,
    FileOperationError,
    InvalidOpenAPISpecError,
    SchemaValidationError,
    WorkItemNotFoundError,
)
from solokit.core.exceptions import (
    FileNotFoundError as SolokitFileNotFoundError,
)
from solokit.core.file_ops import load_json
from solokit.core.output import get_output

output = get_output()
logger = logging.getLogger(__name__)


class APIContractValidator:
    """Validate API contracts for integration tests."""

    def __init__(self, work_item: dict):
        """
        Initialize API contract validator.

        Args:
            work_item: Integration test work item with contract specifications
        """
        self.work_item = work_item
        self.contracts = work_item.get("api_contracts", [])
        self.results: dict[str, Any] = {
            "contracts_validated": 0,
            "breaking_changes": [],
            "warnings": [],
            "passed": False,
        }

    @log_errors()
    def validate_contracts(self) -> tuple[bool, dict[str, Any]]:
        """
        Validate all API contracts.

        Returns:
            (passed: bool, results: dict)

        Raises:
            SchemaValidationError: If contract file validation fails
            InvalidOpenAPISpecError: If OpenAPI/Swagger spec is invalid
            BreakingChangeError: If breaking changes detected and not allowed
            FileNotFoundError: If contract file not found
        """
        logger.info(f"Validating {len(self.contracts)} API contracts...")

        all_passed = True

        for contract in self.contracts:
            contract_file = contract.get("contract_file")
            if not contract_file:
                continue

            # Validate contract file exists and is valid
            try:
                self._validate_contract_file(contract_file)
            except (
                SchemaValidationError,
                InvalidOpenAPISpecError,
                SolokitFileNotFoundError,
            ) as e:
                logger.error(f"Contract validation failed for {contract_file}: {e.message}")
                all_passed = False
                continue

            # Check for breaking changes if previous version exists
            previous_version = contract.get("previous_version")
            if previous_version:
                try:
                    breaking_changes = self._detect_breaking_changes(
                        contract_file, previous_version
                    )
                    if breaking_changes:
                        self.results["breaking_changes"].extend(breaking_changes)
                        if not contract.get("allow_breaking_changes", False):
                            all_passed = False
                except BreakingChangeError as e:
                    logger.error(f"Breaking change detection failed: {e.message}")
                    all_passed = False
                    continue

            self.results["contracts_validated"] += 1

        self.results["passed"] = all_passed
        return all_passed, self.results

    @log_errors()
    def _validate_contract_file(self, contract_file: str) -> None:
        """
        Validate OpenAPI/Swagger contract file.

        Args:
            contract_file: Path to contract file

        Raises:
            FileNotFoundError: If contract file not found
            SchemaValidationError: If contract parsing fails
            InvalidOpenAPISpecError: If not a valid OpenAPI/Swagger spec
        """
        contract_path = Path(contract_file)

        if not contract_path.exists():
            raise SolokitFileNotFoundError(file_path=contract_file, file_type="API contract")

        # Load contract
        try:
            if contract_file.endswith(".yaml") or contract_file.endswith(".yml"):
                with open(contract_path) as f:
                    spec = yaml.safe_load(f)
            else:
                with open(contract_path) as f:
                    spec = json.load(f)
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            raise SchemaValidationError(
                contract_file=contract_file,
                details=f"Failed to parse contract file: {e}",
            ) from e
        except OSError as e:
            raise FileOperationError(
                operation="read", file_path=contract_file, details=str(e), cause=e
            ) from e

        # Validate OpenAPI structure
        if "openapi" not in spec and "swagger" not in spec:
            raise InvalidOpenAPISpecError(
                contract_file=contract_file,
                details="Missing 'openapi' or 'swagger' field",
            )

        # Validate required fields
        if "paths" not in spec:
            raise SchemaValidationError(
                contract_file=contract_file, details="Missing 'paths' field"
            )

        logger.info(f"Contract valid: {contract_file}")

    @log_errors()
    def _detect_breaking_changes(self, current_file: str, previous_file: str) -> list[dict]:
        """
        Detect breaking changes between contract versions.

        Args:
            current_file: Path to current contract
            previous_file: Path to previous contract version

        Returns:
            List of breaking changes

        Raises:
            FileNotFoundError: If contract file not found
            SchemaValidationError: If contract parsing fails
            BreakingChangeError: If breaking changes detected and not allowed
        """
        breaking_changes = []

        # Load both versions
        try:
            current_spec = self._load_spec(current_file)
            previous_spec = self._load_spec(previous_file)
        except (SolokitFileNotFoundError, SchemaValidationError, FileOperationError) as e:
            logger.error(f"Failed to load contract specs: {e.message}")
            return [{"type": "load_error", "message": str(e)}]

        # Check for removed endpoints
        previous_paths = set(previous_spec.get("paths", {}).keys())
        current_paths = set(current_spec.get("paths", {}).keys())

        removed_paths = previous_paths - current_paths
        for path in removed_paths:
            breaking_changes.append(
                {
                    "type": "removed_endpoint",
                    "path": path,
                    "severity": "high",
                    "message": f"Endpoint removed: {path}",
                }
            )

        # Check for modified endpoints
        for path in previous_paths & current_paths:
            endpoint_changes = self._check_endpoint_changes(
                path, previous_spec["paths"][path], current_spec["paths"][path]
            )
            breaking_changes.extend(endpoint_changes)

        if breaking_changes:
            logger.warning(f"{len(breaking_changes)} breaking changes detected")
            for change in breaking_changes:
                logger.warning(f"  - {change['type']}: {change['message']}")
        else:
            logger.info("No breaking changes detected")

        return breaking_changes

    @convert_file_errors
    def _load_spec(self, file_path: str) -> dict[str, Any]:
        """
        Load OpenAPI/Swagger spec from file.

        Args:
            file_path: Path to spec file

        Returns:
            Parsed spec dictionary

        Raises:
            FileNotFoundError: If file not found
            SchemaValidationError: If parsing fails
        """
        path = Path(file_path)

        if not path.exists():
            raise SolokitFileNotFoundError(file_path=file_path, file_type="API contract")

        try:
            if file_path.endswith(".yaml") or file_path.endswith(".yml"):
                with open(path) as f:
                    return yaml.safe_load(f)  # type: ignore[no-any-return]
            else:
                with open(path) as f:
                    return json.load(f)  # type: ignore[no-any-return]
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            raise SchemaValidationError(
                contract_file=file_path, details=f"Failed to parse contract file: {e}"
            ) from e

    def _check_endpoint_changes(self, path: str, previous: dict, current: dict) -> list[dict]:
        """
        Check for breaking changes in a specific endpoint.

        Args:
            path: Endpoint path
            previous: Previous endpoint definition
            current: Current endpoint definition

        Returns:
            List of breaking changes
        """
        changes = []

        # Check HTTP methods
        previous_methods = set(previous.keys())
        current_methods = set(current.keys())

        removed_methods = previous_methods - current_methods
        for method in removed_methods:
            changes.append(
                {
                    "type": "removed_method",
                    "path": path,
                    "method": method.upper(),
                    "severity": "high",
                    "message": f"HTTP method removed: {method.upper()} {path}",
                }
            )

        # Check parameters for common methods
        for method in previous_methods & current_methods:
            if method in ["get", "post", "put", "patch", "delete"]:
                param_changes = self._check_parameter_changes(
                    path, method, previous.get(method, {}), current.get(method, {})
                )
                changes.extend(param_changes)

        return changes

    def _check_parameter_changes(
        self, path: str, method: str, previous: dict, current: dict
    ) -> list[dict]:
        """
        Check for breaking changes in endpoint parameters.

        Args:
            path: Endpoint path
            method: HTTP method
            previous: Previous endpoint definition
            current: Current endpoint definition

        Returns:
            List of breaking changes
        """
        changes = []

        previous_params = {p["name"]: p for p in previous.get("parameters", [])}
        current_params = {p["name"]: p for p in current.get("parameters", [])}

        # Check for removed required parameters
        for param_name, param in previous_params.items():
            if param.get("required", False):
                if param_name not in current_params:
                    changes.append(
                        {
                            "type": "removed_required_parameter",
                            "path": path,
                            "method": method.upper(),
                            "parameter": param_name,
                            "severity": "high",
                            "message": f"Required parameter removed: {param_name} from {method.upper()} {path}",
                        }
                    )

        # Check for newly required parameters (breaking change)
        for param_name, param in current_params.items():
            if param.get("required", False):
                if param_name not in previous_params:
                    changes.append(
                        {
                            "type": "added_required_parameter",
                            "path": path,
                            "method": method.upper(),
                            "parameter": param_name,
                            "severity": "high",
                            "message": f"New required parameter: {param_name} in {method.upper()} {path}",
                        }
                    )
                elif not previous_params[param_name].get("required", False):
                    changes.append(
                        {
                            "type": "parameter_now_required",
                            "path": path,
                            "method": method.upper(),
                            "parameter": param_name,
                            "severity": "high",
                            "message": f"Parameter became required: {param_name} in {method.upper()} {path}",
                        }
                    )

        return changes

    def generate_report(self) -> str:
        """
        Generate API contract validation report.

        Returns:
            Formatted report string
        """
        report = f"""
API Contract Validation Report
{"=" * 80}

Contracts Validated: {self.results["contracts_validated"]}

Breaking Changes: {len(self.results["breaking_changes"])}
"""

        if self.results["breaking_changes"]:
            report += "\nBreaking Changes Detected:\n"
            for change in self.results["breaking_changes"]:
                report += f"  • [{change['severity'].upper()}] {change['message']}\n"

        if self.results["warnings"]:
            report += "\nWarnings:\n"
            for warning in self.results["warnings"]:
                report += f"  • {warning}\n"

        report += f"\nStatus: {'PASSED' if self.results['passed'] else 'FAILED'}\n"

        return report


@log_errors()
def main() -> None:
    """
    CLI entry point.

    Raises:
        WorkItemNotFoundError: If work item not found
        Various validation errors from APIContractValidator
    """
    import sys

    if len(sys.argv) < 2:
        logger.error("Usage: python api_contract_validator.py <work_item_id>")
        sys.exit(1)

    work_item_id = sys.argv[1]

    # Load work item
    work_items_file = Path(".session/tracking/work_items.json")
    data = load_json(work_items_file)
    work_item = data["work_items"].get(work_item_id)

    if not work_item:
        raise WorkItemNotFoundError(work_item_id)

    # Validate contracts
    validator = APIContractValidator(work_item)
    try:
        passed, results = validator.validate_contracts()
        output.info(validator.generate_report())
        sys.exit(0 if passed else 1)
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise


if __name__ == "__main__":
    main()
