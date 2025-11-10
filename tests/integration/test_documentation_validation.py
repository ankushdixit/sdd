"""Integration tests for integration documentation validation.

This module tests the QualityGates validate_integration_documentation method which
validates documentation requirements for integration test work items including
architecture diagrams, sequence diagrams, API contracts, and performance baselines.
"""

import json
from pathlib import Path
from unittest.mock import patch

from solokit.quality.gates import QualityGates


class TestDocumentationValidationBasics:
    """Tests for basic integration documentation validation functionality."""

    def test_validate_method_exists(self):
        """Test that validate_integration_documentation method exists."""
        # Arrange
        gates = QualityGates()

        # Act & Assert
        assert hasattr(gates, "validate_integration_documentation")
        assert callable(gates.validate_integration_documentation)

    def test_validate_skips_non_integration_work_items(self):
        """Test that validation skips non-integration work items."""
        # Arrange
        gates = QualityGates()
        work_item = {"id": "FEAT-001", "type": "feature", "title": "Regular Feature"}

        # Act
        passed, results = gates.validate_integration_documentation(work_item)

        # Assert
        assert passed is True
        assert results.get("status") == "skipped"

    def test_validate_skips_bug_work_items(self):
        """Test that validation skips bug work items."""
        # Arrange
        gates = QualityGates()
        work_item = {"id": "BUG-001", "type": "bug", "title": "Fix Bug"}

        # Act
        passed, results = gates.validate_integration_documentation(work_item)

        # Assert
        assert passed is True
        assert results.get("status") == "skipped"

    @patch("solokit.quality.checkers.integration.spec_parser.parse_spec_file")
    def test_validate_results_structure(self, mock_parse):
        """Test that validate_integration_documentation returns correct structure."""
        # Arrange
        mock_parse.return_value = {
            "scope": "Test scope with detailed description",
            "test_scenarios": [],
        }
        gates = QualityGates()
        work_item = {
            "id": "INTEG-001",
            "type": "integration_test",
            "title": "Integration Test",
        }

        # Act
        passed, results = gates.validate_integration_documentation(work_item)

        # Assert
        expected_keys = ["checks", "missing", "passed", "summary"]
        for key in expected_keys:
            assert key in results

    @patch("solokit.quality.checkers.integration.spec_parser.parse_spec_file")
    def test_validate_summary_format(self, mock_parse):
        """Test that summary shows X/Y format."""
        # Arrange
        mock_parse.return_value = {
            "scope": "Test scope with detailed description",
            "test_scenarios": [],
        }
        gates = QualityGates()
        work_item = {
            "id": "INTEG-001",
            "type": "integration_test",
            "title": "Integration Test",
        }

        # Act
        passed, results = gates.validate_integration_documentation(work_item)

        # Assert
        assert "/" in results.get("summary", "")
        assert "documentation requirements met" in results.get("summary", "")

    @patch("solokit.quality.checkers.integration.spec_parser.parse_spec_file")
    def test_validate_skips_when_disabled(self, mock_parse, temp_dir):
        """Test that validation skips when disabled in config."""
        # Arrange
        config_file = temp_dir / "config.json"
        config = {
            "quality_gates": {},
            "integration_tests": {"documentation": {"enabled": False}},
        }
        config_file.write_text(json.dumps(config))
        gates = QualityGates(config_path=config_file)

        work_item = {"id": "INTEG-001", "type": "integration_test"}

        # Act
        passed, results = gates.validate_integration_documentation(work_item)

        # Assert
        assert passed is True
        assert results.get("status") == "skipped"


class TestArchitectureDiagramValidation:
    """Tests for integration architecture diagram validation."""

    @patch("solokit.quality.checkers.integration.spec_parser.parse_spec_file")
    def test_detects_missing_architecture_diagram(self, mock_parse):
        """Test that validation detects missing architecture diagram."""
        # Arrange
        mock_parse.return_value = {
            "scope": "Test scope with sufficient detail",
            "test_scenarios": [],
        }
        gates = QualityGates()
        work_item = {"id": "INTEG-001", "type": "integration_test", "title": "Test"}

        # Act
        passed, results = gates.validate_integration_documentation(work_item)

        # Assert
        has_arch_check = any(
            c["name"] == "Integration architecture diagram" for c in results.get("checks", [])
        )
        assert has_arch_check
        assert "Integration architecture diagram" in results.get("missing", [])

    @patch("solokit.quality.checkers.integration.spec_parser.parse_spec_file")
    def test_finds_architecture_diagram_in_docs(self, mock_parse, temp_dir, monkeypatch):
        """Test that validation finds architecture diagram in docs/ directory."""
        # Arrange
        mock_parse.return_value = {
            "scope": "Test scope with sufficient detail",
            "test_scenarios": [],
        }
        docs_dir = temp_dir / "docs"
        docs_dir.mkdir()
        arch_file = docs_dir / "integration-architecture.md"
        arch_file.write_text("# Integration Architecture\n\nDiagram content here")

        monkeypatch.chdir(temp_dir)

        gates = QualityGates()
        work_item = {"id": "INTEG-001", "type": "integration_test"}

        # Act
        passed, results = gates.validate_integration_documentation(work_item)

        # Assert
        arch_check = next(
            (
                c
                for c in results.get("checks", [])
                if c["name"] == "Integration architecture diagram"
            ),
            None,
        )
        assert arch_check is not None
        assert arch_check["passed"] is True

    @patch("solokit.quality.checkers.integration.spec_parser.parse_spec_file")
    def test_finds_architecture_diagram_in_architecture_subdir(
        self, mock_parse, temp_dir, monkeypatch
    ):
        """Test that validation finds architecture diagram in docs/architecture/ directory."""
        # Arrange
        mock_parse.return_value = {
            "scope": "Test scope with sufficient detail",
            "test_scenarios": [],
        }
        arch_dir = temp_dir / "docs" / "architecture"
        arch_dir.mkdir(parents=True)
        arch_file = arch_dir / "integration-architecture.md"
        arch_file.write_text("# Integration Architecture\n\nDiagram content")

        monkeypatch.chdir(temp_dir)

        gates = QualityGates()
        work_item = {"id": "INTEG-001", "type": "integration_test"}

        # Act
        passed, results = gates.validate_integration_documentation(work_item)

        # Assert
        arch_check = next(
            (
                c
                for c in results.get("checks", [])
                if c["name"] == "Integration architecture diagram"
            ),
            None,
        )
        assert arch_check["passed"] is True

    @patch("solokit.quality.checkers.integration.spec_parser.parse_spec_file")
    def test_finds_architecture_diagram_in_session_specs(self, mock_parse, temp_dir, monkeypatch):
        """Test that validation finds architecture diagram in .session/specs/ directory."""
        # Arrange
        mock_parse.return_value = {
            "scope": "Test scope with sufficient detail",
            "test_scenarios": [],
        }
        specs_dir = temp_dir / ".session" / "specs"
        specs_dir.mkdir(parents=True)
        arch_file = specs_dir / "integration-architecture.md"
        arch_file.write_text("# Integration Architecture\n\nDiagram")

        monkeypatch.chdir(temp_dir)

        gates = QualityGates()
        work_item = {"id": "INTEG-001", "type": "integration_test"}

        # Act
        passed, results = gates.validate_integration_documentation(work_item)

        # Assert
        arch_check = next(
            (
                c
                for c in results.get("checks", [])
                if c["name"] == "Integration architecture diagram"
            ),
            None,
        )
        assert arch_check["passed"] is True

    @patch("solokit.quality.checkers.integration.spec_parser.parse_spec_file")
    def test_architecture_diagram_disabled_in_config(self, mock_parse, temp_dir):
        """Test that architecture diagram check can be disabled in config."""
        # Arrange
        mock_parse.return_value = {"scope": "Test", "test_scenarios": []}
        config_file = temp_dir / "config.json"
        config = {
            "quality_gates": {},
            "integration_tests": {
                "documentation": {"enabled": True, "architecture_diagrams": False}
            },
        }
        config_file.write_text(json.dumps(config))

        gates = QualityGates(config_path=config_file)
        work_item = {"id": "INTEG-001", "type": "integration_test"}

        # Act
        passed, results = gates.validate_integration_documentation(work_item)

        # Assert
        has_arch_check = any(
            c["name"] == "Integration architecture diagram" for c in results.get("checks", [])
        )
        assert has_arch_check is False


class TestSequenceDiagramValidation:
    """Tests for sequence diagram validation."""

    @patch("solokit.quality.checkers.integration.spec_parser.parse_spec_file")
    def test_detects_missing_sequence_diagrams(self, mock_parse, temp_dir, monkeypatch):
        """Test that validation detects missing sequence diagrams."""
        # Arrange
        specs_dir = temp_dir / ".session" / "specs"
        specs_dir.mkdir(parents=True)
        spec_file = specs_dir / "INTEG-001.md"
        spec_file.write_text("# Integration Test\n\nNo diagrams here")

        mock_parse.return_value = {
            "scope": "Test scope with sufficient detail",
            "test_scenarios": [{"name": "Scenario 1", "content": "No diagrams"}],
        }

        monkeypatch.chdir(temp_dir)

        config_file = temp_dir / "config.json"
        config = {
            "quality_gates": {},
            "integration_tests": {
                "documentation": {
                    "enabled": True,
                    "architecture_diagrams": False,
                    "sequence_diagrams": True,
                }
            },
        }
        config_file.write_text(json.dumps(config))

        gates = QualityGates(config_path=config_file)
        work_item = {
            "id": "INTEG-001",
            "type": "integration_test",
            "test_scenarios": [{"name": "Scenario 1"}],
        }

        # Act
        passed, results = gates.validate_integration_documentation(work_item)

        # Assert
        assert "Sequence diagrams for test scenarios" in results.get("missing", [])

    @patch("solokit.quality.checkers.integration.spec_parser.parse_spec_file")
    def test_finds_mermaid_sequence_diagrams(self, mock_parse, temp_dir, monkeypatch):
        """Test that validation finds mermaid sequence diagrams."""
        # Arrange
        mermaid_content = """# Integration Test

## Sequence Diagrams

```mermaid
sequenceDiagram
    Client->>Service A: Request
    Service A->>Service B: Forward
    Service B-->>Service A: Response
    Service A-->>Client: Response
```
"""
        mock_parse.return_value = {
            "scope": "Test scope with sufficient detail",
            "test_scenarios": [{"name": "Scenario 1", "content": mermaid_content}],
        }

        monkeypatch.chdir(temp_dir)

        config_file = temp_dir / "config.json"
        config = {
            "quality_gates": {},
            "integration_tests": {
                "documentation": {
                    "enabled": True,
                    "architecture_diagrams": False,
                    "sequence_diagrams": True,
                }
            },
        }
        config_file.write_text(json.dumps(config))

        gates = QualityGates(config_path=config_file)
        work_item = {"id": "INTEG-001", "type": "integration_test"}

        # Act
        passed, results = gates.validate_integration_documentation(work_item)

        # Assert
        seq_check = next(
            (c for c in results.get("checks", []) if c["name"] == "Sequence diagrams"),
            None,
        )
        assert seq_check is not None
        assert seq_check["passed"] is True

    @patch("solokit.quality.checkers.integration.spec_parser.parse_spec_file")
    def test_scenario_sections_without_diagrams_fail(self, mock_parse, temp_dir, monkeypatch):
        """Test that validation fails when scenarios exist but have no diagrams."""
        # Arrange
        scenario_content = """# Integration Test

### Scenario 1: Happy Path
- Setup: Services running
- Actions: Send request
- Expected: HTTP 200
"""
        mock_parse.return_value = {
            "scope": "Test scope with sufficient detail",
            "test_scenarios": [{"name": "Scenario 1", "content": scenario_content}],
        }

        monkeypatch.chdir(temp_dir)

        config_file = temp_dir / "config.json"
        config = {
            "quality_gates": {},
            "integration_tests": {
                "documentation": {
                    "enabled": True,
                    "architecture_diagrams": False,
                    "sequence_diagrams": True,
                }
            },
        }
        config_file.write_text(json.dumps(config))

        gates = QualityGates(config_path=config_file)
        work_item = {"id": "INTEG-001", "type": "integration_test"}

        # Act
        passed, results = gates.validate_integration_documentation(work_item)

        # Assert
        seq_check = next(
            (c for c in results.get("checks", []) if c["name"] == "Sequence diagrams"),
            None,
        )
        assert seq_check is not None
        assert seq_check["passed"] is False

    @patch("solokit.quality.checkers.integration.spec_parser.parse_spec_file")
    def test_sequence_diagrams_disabled_in_config(self, mock_parse, temp_dir):
        """Test that sequence diagram check can be disabled in config."""
        # Arrange
        mock_parse.return_value = {
            "scope": "Test",
            "test_scenarios": [{"name": "S1", "content": "No diagrams"}],
        }
        config_file = temp_dir / "config.json"
        config = {
            "quality_gates": {},
            "integration_tests": {"documentation": {"enabled": True, "sequence_diagrams": False}},
        }
        config_file.write_text(json.dumps(config))

        gates = QualityGates(config_path=config_file)
        work_item = {"id": "INTEG-001", "type": "integration_test"}

        # Act
        passed, results = gates.validate_integration_documentation(work_item)

        # Assert
        has_seq_check = any(c["name"] == "Sequence diagrams" for c in results.get("checks", []))
        assert has_seq_check is False


class TestAPIContractDocumentation:
    """Tests for API contract documentation validation."""

    @patch("solokit.quality.checkers.integration.spec_parser.parse_spec_file")
    def test_detects_missing_api_contracts(self, mock_parse):
        """Test that validation detects missing API contract documentation."""
        # Arrange
        mock_parse.return_value = {"scope": "Test scope", "api_contracts": ""}
        config_file = Path("/tmp/config.json")
        config = {
            "quality_gates": {},
            "integration_tests": {
                "documentation": {
                    "enabled": True,
                    "architecture_diagrams": False,
                    "contract_documentation": True,
                }
            },
        }

        gates = QualityGates()
        work_item = {"id": "INTEG-001", "type": "integration_test"}

        # Act
        with patch.object(gates, "_config_path", config_file):
            with patch("builtins.open", create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(config)
                passed, results = gates.validate_integration_documentation(work_item)

        # Assert
        has_contract_check = any(
            c["name"] == "API contracts documented" for c in results.get("checks", [])
        )
        assert has_contract_check
        assert "API contract documentation" in results.get("missing", [])

    @patch("solokit.quality.checkers.integration.spec_parser.parse_spec_file")
    def test_finds_api_contract_documentation(self, mock_parse, temp_dir):
        """Test that validation finds API contract documentation."""
        # Arrange
        mock_parse.return_value = {
            "scope": "Test scope",
            "api_contracts": "OpenAPI 3.0 specification with detailed endpoints",
        }
        config_file = temp_dir / "config.json"
        config = {
            "quality_gates": {},
            "integration_tests": {
                "documentation": {
                    "enabled": True,
                    "architecture_diagrams": False,
                    "contract_documentation": True,
                }
            },
        }
        config_file.write_text(json.dumps(config))

        gates = QualityGates(config_path=config_file)
        work_item = {"id": "INTEG-001", "type": "integration_test"}

        # Act
        passed, results = gates.validate_integration_documentation(work_item)

        # Assert
        contract_check = next(
            (c for c in results.get("checks", []) if c["name"] == "API contracts documented"),
            None,
        )
        assert contract_check is not None
        assert contract_check["passed"] is True

    @patch("solokit.quality.checkers.integration.spec_parser.parse_spec_file")
    def test_api_contracts_require_minimum_length(self, mock_parse, temp_dir):
        """Test that API contracts must have meaningful content (not just a few chars)."""
        # Arrange
        mock_parse.return_value = {"scope": "Test scope", "api_contracts": "Short"}
        config_file = temp_dir / "config.json"
        config = {
            "quality_gates": {},
            "integration_tests": {
                "documentation": {
                    "enabled": True,
                    "architecture_diagrams": False,
                    "contract_documentation": True,
                }
            },
        }
        config_file.write_text(json.dumps(config))

        gates = QualityGates(config_path=config_file)
        work_item = {"id": "INTEG-001", "type": "integration_test"}

        # Act
        passed, results = gates.validate_integration_documentation(work_item)

        # Assert
        contract_check = next(
            (c for c in results.get("checks", []) if c["name"] == "API contracts documented"),
            None,
        )
        assert contract_check["passed"] is False


class TestPerformanceBaselineDocumentation:
    """Tests for performance baseline documentation validation."""

    @patch("solokit.quality.checkers.integration.spec_parser.parse_spec_file")
    def test_detects_missing_baseline_file(self, mock_parse, temp_dir, monkeypatch):
        """Test that validation detects missing baseline file."""
        # Arrange
        mock_parse.return_value = {
            "scope": "Test scope",
            "performance_benchmarks": "p50: 100ms, p95: 200ms, p99: 300ms",
        }
        monkeypatch.chdir(temp_dir)

        config_file = temp_dir / "config.json"
        config = {
            "quality_gates": {},
            "integration_tests": {
                "documentation": {
                    "enabled": True,
                    "architecture_diagrams": False,
                    "performance_baseline_docs": True,
                }
            },
        }
        config_file.write_text(json.dumps(config))

        gates = QualityGates(config_path=config_file)
        work_item = {"id": "INTEG-001", "type": "integration_test"}

        # Act
        passed, results = gates.validate_integration_documentation(work_item)

        # Assert
        assert "Performance baseline documentation" in results.get("missing", [])

    @patch("solokit.quality.checkers.integration.spec_parser.parse_spec_file")
    def test_finds_baseline_file(self, mock_parse, temp_dir, monkeypatch):
        """Test that validation finds existing baseline file."""
        # Arrange
        mock_parse.return_value = {
            "scope": "Test scope",
            "performance_benchmarks": "p50: 100ms, p95: 200ms, p99: 300ms",
        }
        baseline_dir = temp_dir / ".session" / "tracking"
        baseline_dir.mkdir(parents=True)
        baseline_file = baseline_dir / "performance_baselines.json"
        baseline_file.write_text('{"INTEG-001": {"p50": 80}}')

        monkeypatch.chdir(temp_dir)

        config_file = temp_dir / "config.json"
        config = {
            "quality_gates": {},
            "integration_tests": {
                "documentation": {
                    "enabled": True,
                    "architecture_diagrams": False,
                    "performance_baseline_docs": True,
                }
            },
        }
        config_file.write_text(json.dumps(config))

        gates = QualityGates(config_path=config_file)
        work_item = {"id": "INTEG-001", "type": "integration_test"}

        # Act
        passed, results = gates.validate_integration_documentation(work_item)

        # Assert
        baseline_check = next(
            (
                c
                for c in results.get("checks", [])
                if c["name"] == "Performance baseline documented"
            ),
            None,
        )
        assert baseline_check is not None
        assert baseline_check["passed"] is True

    @patch("solokit.quality.checkers.integration.spec_parser.parse_spec_file")
    def test_skips_baseline_check_when_no_benchmarks(self, mock_parse, temp_dir):
        """Test that validation skips baseline check when no performance benchmarks defined."""
        # Arrange
        mock_parse.return_value = {"scope": "Test scope", "performance_benchmarks": ""}
        config_file = temp_dir / "config.json"
        config = {
            "quality_gates": {},
            "integration_tests": {
                "documentation": {"enabled": True, "performance_baseline_docs": True}
            },
        }
        config_file.write_text(json.dumps(config))

        gates = QualityGates(config_path=config_file)
        work_item = {"id": "INTEG-001", "type": "integration_test"}

        # Act
        passed, results = gates.validate_integration_documentation(work_item)

        # Assert
        has_baseline_check = any(
            c["name"] == "Performance baseline documented" for c in results.get("checks", [])
        )
        assert has_baseline_check is False


class TestIntegrationPointsDocumentation:
    """Tests for integration points documentation validation."""

    @patch("solokit.quality.checkers.integration.spec_parser.parse_spec_file")
    def test_detects_missing_integration_points_short_scope(self, mock_parse):
        """Test that validation detects missing integration points when scope is too short."""
        # Arrange
        mock_parse.return_value = {"scope": "Short", "test_scenarios": []}
        gates = QualityGates()
        work_item = {"id": "INTEG-001", "type": "integration_test"}

        # Act
        passed, results = gates.validate_integration_documentation(work_item)

        # Assert
        assert "Integration points documentation" in results.get("missing", [])

    @patch("solokit.quality.checkers.integration.spec_parser.parse_spec_file")
    def test_finds_integration_points_detailed_scope(self, mock_parse):
        """Test that validation finds integration points when scope is detailed."""
        # Arrange
        mock_parse.return_value = {
            "scope": "This is a detailed scope describing the integration between Service A and Service B with sufficient detail",
            "test_scenarios": [],
        }
        gates = QualityGates()
        work_item = {"id": "INTEG-001", "type": "integration_test"}

        # Act
        passed, results = gates.validate_integration_documentation(work_item)

        # Assert
        points_check = next(
            (c for c in results.get("checks", []) if c["name"] == "Integration points documented"),
            None,
        )
        assert points_check is not None
        assert points_check["passed"] is True

    @patch("solokit.quality.checkers.integration.spec_parser.parse_spec_file")
    def test_integration_points_require_minimum_length(self, mock_parse):
        """Test that integration points require meaningful content (more than 20 chars)."""
        # Arrange
        mock_parse.return_value = {"scope": "Brief", "test_scenarios": []}
        gates = QualityGates()
        work_item = {"id": "INTEG-001", "type": "integration_test"}

        # Act
        passed, results = gates.validate_integration_documentation(work_item)

        # Assert
        points_check = next(
            (c for c in results.get("checks", []) if c["name"] == "Integration points documented"),
            None,
        )
        assert points_check["passed"] is False

    @patch("solokit.quality.checkers.integration.spec_parser.parse_spec_file")
    def test_handles_spec_parse_error_gracefully(self, mock_parse):
        """Test that validation handles spec parse errors gracefully."""
        # Arrange
        # Use OSError which is caught by the exception handler
        mock_parse.side_effect = OSError("Spec file not found")
        gates = QualityGates()
        work_item = {"id": "INTEG-001", "type": "integration_test"}

        # Act
        passed, results = gates.validate_integration_documentation(work_item)

        # Assert
        points_check = next(
            (c for c in results.get("checks", []) if c["name"] == "Integration points documented"),
            None,
        )
        assert points_check is not None
        assert points_check["passed"] is False


class TestOverallValidation:
    """Tests for overall documentation validation logic."""

    @patch("solokit.quality.checkers.integration.spec_parser.parse_spec_file")
    def test_passes_when_all_requirements_met(self, mock_parse, temp_dir, monkeypatch):
        """Test that validation passes when all documentation requirements are met."""
        # Arrange
        mock_parse.return_value = {
            "scope": "This is a detailed scope with sufficient information about the integration",
            "test_scenarios": [],
        }

        docs_dir = temp_dir / "docs"
        docs_dir.mkdir()
        (docs_dir / "integration-architecture.md").write_text("# Architecture")

        monkeypatch.chdir(temp_dir)

        config_file = temp_dir / "config.json"
        config = {
            "quality_gates": {},
            "integration_tests": {
                "documentation": {
                    "enabled": True,
                    "architecture_diagrams": True,
                    "sequence_diagrams": False,
                    "contract_documentation": False,
                    "performance_baseline_docs": False,
                }
            },
        }
        config_file.write_text(json.dumps(config))

        gates = QualityGates(config_path=config_file)
        work_item = {"id": "INTEG-001", "type": "integration_test"}

        # Act
        passed, results = gates.validate_integration_documentation(work_item)

        # Assert
        assert passed is True
        assert results["passed"] is True
        assert len(results["missing"]) == 0

    @patch("solokit.quality.checkers.integration.spec_parser.parse_spec_file")
    def test_fails_when_requirements_not_met(self, mock_parse):
        """Test that validation fails when documentation requirements are not met."""
        # Arrange
        mock_parse.return_value = {"scope": "Short", "test_scenarios": []}
        gates = QualityGates()
        work_item = {"id": "INTEG-001", "type": "integration_test"}

        # Act
        passed, results = gates.validate_integration_documentation(work_item)

        # Assert
        assert passed is False
        assert results["passed"] is False
        assert len(results["missing"]) > 0

    @patch("solokit.quality.checkers.integration.spec_parser.parse_spec_file")
    def test_summary_counts_passed_and_total_checks(self, mock_parse):
        """Test that summary correctly counts passed and total checks."""
        # Arrange
        mock_parse.return_value = {
            "scope": "This is a detailed scope with sufficient detail",
            "test_scenarios": [],
        }
        gates = QualityGates()
        work_item = {"id": "INTEG-001", "type": "integration_test"}

        # Act
        passed, results = gates.validate_integration_documentation(work_item)

        # Assert
        summary = results.get("summary", "")
        assert "/" in summary
        parts = summary.split("/")
        passed_count = int(parts[0].strip().split()[-1])
        total_count = int(parts[1].strip().split()[0])
        assert passed_count >= 0
        assert total_count >= 0
        assert passed_count <= total_count
