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
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.file_ops import load_json


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
        self.results = {
            "contracts_validated": 0,
            "breaking_changes": [],
            "warnings": [],
            "passed": False
        }

    def validate_contracts(self) -> Tuple[bool, dict]:
        """
        Validate all API contracts.

        Returns:
            (passed: bool, results: dict)
        """
        print(f"Validating {len(self.contracts)} API contracts...")

        all_passed = True

        for contract in self.contracts:
            contract_file = contract.get("contract_file")
            if not contract_file:
                continue

            # Validate contract file exists and is valid
            is_valid = self._validate_contract_file(contract_file)
            if not is_valid:
                all_passed = False
                continue

            # Check for breaking changes if previous version exists
            previous_version = contract.get("previous_version")
            if previous_version:
                breaking_changes = self._detect_breaking_changes(
                    contract_file,
                    previous_version
                )
                if breaking_changes:
                    self.results["breaking_changes"].extend(breaking_changes)
                    if contract.get("allow_breaking_changes", False) == False:
                        all_passed = False

            self.results["contracts_validated"] += 1

        self.results["passed"] = all_passed
        return all_passed, self.results

    def _validate_contract_file(self, contract_file: str) -> bool:
        """
        Validate OpenAPI/Swagger contract file.

        Args:
            contract_file: Path to contract file

        Returns:
            True if valid, False otherwise
        """
        contract_path = Path(contract_file)

        if not contract_path.exists():
            print(f"  ✗ Contract file not found: {contract_file}")
            return False

        # Load contract
        try:
            if contract_file.endswith('.yaml') or contract_file.endswith('.yml'):
                with open(contract_path) as f:
                    spec = yaml.safe_load(f)
            else:
                with open(contract_path) as f:
                    spec = json.load(f)
        except Exception as e:
            print(f"  ✗ Failed to parse contract file {contract_file}: {e}")
            return False

        # Validate OpenAPI structure
        if "openapi" not in spec and "swagger" not in spec:
            print(f"  ✗ Invalid OpenAPI/Swagger spec: {contract_file}")
            return False

        # Validate required fields
        if "paths" not in spec:
            print(f"  ✗ Missing 'paths' in contract: {contract_file}")
            return False

        print(f"  ✓ Contract valid: {contract_file}")
        return True

    def _detect_breaking_changes(self, current_file: str, previous_file: str) -> List[dict]:
        """
        Detect breaking changes between contract versions.

        Args:
            current_file: Path to current contract
            previous_file: Path to previous contract version

        Returns:
            List of breaking changes
        """
        breaking_changes = []

        # Load both versions
        try:
            current_spec = self._load_spec(current_file)
            previous_spec = self._load_spec(previous_file)
        except Exception as e:
            return [{"type": "load_error", "message": str(e)}]

        # Check for removed endpoints
        previous_paths = set(previous_spec.get("paths", {}).keys())
        current_paths = set(current_spec.get("paths", {}).keys())

        removed_paths = previous_paths - current_paths
        for path in removed_paths:
            breaking_changes.append({
                "type": "removed_endpoint",
                "path": path,
                "severity": "high",
                "message": f"Endpoint removed: {path}"
            })

        # Check for modified endpoints
        for path in previous_paths & current_paths:
            endpoint_changes = self._check_endpoint_changes(
                path,
                previous_spec["paths"][path],
                current_spec["paths"][path]
            )
            breaking_changes.extend(endpoint_changes)

        if breaking_changes:
            print(f"  ⚠️  {len(breaking_changes)} breaking changes detected")
            for change in breaking_changes:
                print(f"     - {change['type']}: {change['message']}")
        else:
            print(f"  ✓ No breaking changes detected")

        return breaking_changes

    def _load_spec(self, file_path: str) -> dict:
        """Load OpenAPI/Swagger spec from file."""
        path = Path(file_path)

        if file_path.endswith('.yaml') or file_path.endswith('.yml'):
            with open(path) as f:
                return yaml.safe_load(f)
        else:
            with open(path) as f:
                return json.load(f)

    def _check_endpoint_changes(self, path: str, previous: dict, current: dict) -> List[dict]:
        """Check for breaking changes in a specific endpoint."""
        changes = []

        # Check HTTP methods
        previous_methods = set(previous.keys())
        current_methods = set(current.keys())

        removed_methods = previous_methods - current_methods
        for method in removed_methods:
            changes.append({
                "type": "removed_method",
                "path": path,
                "method": method.upper(),
                "severity": "high",
                "message": f"HTTP method removed: {method.upper()} {path}"
            })

        # Check parameters for common methods
        for method in previous_methods & current_methods:
            if method in ["get", "post", "put", "patch", "delete"]:
                param_changes = self._check_parameter_changes(
                    path,
                    method,
                    previous.get(method, {}),
                    current.get(method, {})
                )
                changes.extend(param_changes)

        return changes

    def _check_parameter_changes(self, path: str, method: str,
                                 previous: dict, current: dict) -> List[dict]:
        """Check for breaking changes in endpoint parameters."""
        changes = []

        previous_params = {p["name"]: p for p in previous.get("parameters", [])}
        current_params = {p["name"]: p for p in current.get("parameters", [])}

        # Check for removed required parameters
        for param_name, param in previous_params.items():
            if param.get("required", False):
                if param_name not in current_params:
                    changes.append({
                        "type": "removed_required_parameter",
                        "path": path,
                        "method": method.upper(),
                        "parameter": param_name,
                        "severity": "high",
                        "message": f"Required parameter removed: {param_name} from {method.upper()} {path}"
                    })

        # Check for newly required parameters (breaking change)
        for param_name, param in current_params.items():
            if param.get("required", False):
                if param_name not in previous_params:
                    changes.append({
                        "type": "added_required_parameter",
                        "path": path,
                        "method": method.upper(),
                        "parameter": param_name,
                        "severity": "high",
                        "message": f"New required parameter: {param_name} in {method.upper()} {path}"
                    })
                elif not previous_params[param_name].get("required", False):
                    changes.append({
                        "type": "parameter_now_required",
                        "path": path,
                        "method": method.upper(),
                        "parameter": param_name,
                        "severity": "high",
                        "message": f"Parameter became required: {param_name} in {method.upper()} {path}"
                    })

        return changes

    def generate_report(self) -> str:
        """Generate API contract validation report."""
        report = f"""
API Contract Validation Report
{'='*80}

Contracts Validated: {self.results['contracts_validated']}

Breaking Changes: {len(self.results['breaking_changes'])}
"""

        if self.results['breaking_changes']:
            report += "\nBreaking Changes Detected:\n"
            for change in self.results['breaking_changes']:
                report += f"  • [{change['severity'].upper()}] {change['message']}\n"

        if self.results['warnings']:
            report += "\nWarnings:\n"
            for warning in self.results['warnings']:
                report += f"  • {warning}\n"

        report += f"\nStatus: {'PASSED' if self.results['passed'] else 'FAILED'}\n"

        return report


def main():
    """CLI entry point."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python api_contract_validator.py <work_item_id>")
        sys.exit(1)

    work_item_id = sys.argv[1]

    # Load work item
    work_items_file = Path(".session/tracking/work_items.json")
    data = load_json(work_items_file)
    work_item = data["work_items"].get(work_item_id)

    if not work_item:
        print(f"Work item not found: {work_item_id}")
        sys.exit(1)

    # Validate contracts
    validator = APIContractValidator(work_item)
    passed, results = validator.validate_contracts()

    print(validator.generate_report())

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
