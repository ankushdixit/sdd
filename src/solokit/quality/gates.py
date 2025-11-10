#!/usr/bin/env python3
"""
Quality gate validation for session completion.

Refactored to use pluggable checker architecture for better maintainability.

Provides comprehensive validation including:
- Test execution with coverage
- Linting and formatting
- Security scanning
- Documentation validation
- Custom validation rules

Updated to use modular checker architecture while maintaining backward compatibility.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from solokit.core.command_runner import CommandRunner
from solokit.core.config import get_config_manager
from solokit.core.constants import QUALITY_CHECK_VERY_LONG_TIMEOUT
from solokit.core.error_handlers import log_errors
from solokit.core.exceptions import (
    FileOperationError,
)
from solokit.core.logging_config import get_logger
from solokit.quality.checkers import (
    CustomValidationChecker,
    DocumentationChecker,
    ExecutionChecker,
    FormattingChecker,
    LintingChecker,
    SecurityChecker,
    SpecCompletenessChecker,
)
from solokit.quality.reporters import ConsoleReporter
from solokit.quality.results import ResultAggregator

logger = get_logger(__name__)

# Import spec validator for spec completeness quality gate
try:
    from solokit.core.exceptions import SpecValidationError
    from solokit.work_items.spec_validator import validate_spec_file
except ImportError:
    validate_spec_file = None  # type: ignore[assignment]
    SpecValidationError = None  # type: ignore[assignment, misc]


class QualityGates:
    """Quality gate validation using modular checker architecture.

    This class maintains backward compatibility with the original QualityGates interface
    while delegating to specialized checker classes internally.
    """

    def __init__(self, config_path: Path | None = None):
        """Initialize quality gates with configuration."""
        if config_path is None:
            config_path = Path(".session/config.json")
        self._config_path = config_path

        # Use ConfigManager for centralized config management
        config_manager = get_config_manager()
        config_manager.load_config(config_path)
        self.config = config_manager.quality_gates  # QualityGatesConfig dataclass

        # Initialize command runner (for backward compatibility)
        self.runner = CommandRunner(default_timeout=QUALITY_CHECK_VERY_LONG_TIMEOUT)

        # Project root
        self.project_root = Path.cwd()

        # Result aggregator and reporter
        self.aggregator = ResultAggregator()
        self.reporter = ConsoleReporter()

    @log_errors()
    def _load_full_config(self) -> dict[str, Any]:
        """Load full configuration file for optional sections (context7, custom_validations, etc.)."""
        if self._config_path.exists():
            try:
                with open(self._config_path) as f:
                    return json.load(f)  # type: ignore[no-any-return]
            except OSError as e:
                raise FileOperationError(
                    operation="read",
                    file_path=str(self._config_path),
                    details="Failed to read configuration file",
                    cause=e,
                ) from e
            except json.JSONDecodeError as e:
                raise FileOperationError(
                    operation="parse",
                    file_path=str(self._config_path),
                    details="Invalid JSON in configuration file",
                    cause=e,
                ) from e
        return {}

    def _detect_language(self) -> str:
        """Detect primary project language."""
        # Check for common files
        if Path("pyproject.toml").exists() or Path("setup.py").exists():
            return "python"
        elif Path("package.json").exists():
            # Check if TypeScript
            if Path("tsconfig.json").exists():
                return "typescript"
            return "javascript"

        return "python"  # default

    def run_tests(self, language: str | None = None) -> tuple[bool, dict[str, Any]]:
        """
        Run test suite with coverage.

        Args:
            language: Programming language (optional, will be detected if not provided)

        Returns:
            (passed: bool, results: dict)
        """
        logger.info("Running test quality gate")

        # Convert config dataclass to dict for checker
        test_config = {
            "enabled": self.config.test_execution.enabled,
            "commands": self.config.test_execution.commands,
            "coverage_threshold": self.config.test_execution.coverage_threshold,
        }

        # Create and run test checker (pass runner for test compatibility)
        checker = ExecutionChecker(
            test_config, self.project_root, language=language, runner=self.runner
        )
        result = checker.run()

        # Convert CheckResult to legacy format
        # Extract reason from errors if present (for coverage failures)
        reason = result.info.get("reason")
        if not reason and result.errors:
            # Check if any error is about coverage
            for error in result.errors:
                if isinstance(error, dict):
                    msg = error.get("message", "")
                    if "coverage" in msg.lower() and "threshold" in msg.lower():
                        reason = msg
                        break

        return result.passed, {
            "status": result.status,
            "coverage": result.info.get("coverage"),
            "returncode": result.info.get("returncode", 0),
            "output": result.info.get("output", ""),
            "errors": "\n".join(str(e) for e in result.errors) if result.errors else "",
            "reason": reason,
        }

    def run_security_scan(self, language: str | None = None) -> tuple[bool, dict[str, Any]]:
        """
        Run security vulnerability scanning.

        Args:
            language: Programming language (optional, will be detected if not provided)

        Returns:
            (passed: bool, results: dict)
        """
        logger.info("Running security scan quality gate")

        # Convert config dataclass to dict for checker
        security_config = {
            "enabled": self.config.security.enabled,
            "fail_on": self.config.security.fail_on,
        }

        # Create and run security checker (pass runner for test compatibility)
        checker = SecurityChecker(
            security_config, self.project_root, language=language, runner=self.runner
        )
        result = checker.run()

        # Convert CheckResult to legacy format
        return result.passed, {
            "status": result.status,
            "vulnerabilities": result.errors,
            "by_severity": result.info.get("by_severity", {}),
        }

    def run_linting(
        self, language: str | None = None, auto_fix: bool | None = None
    ) -> tuple[bool, dict[str, Any]]:
        """Run linting with optional auto-fix.

        Args:
            language: Programming language (optional, will be detected if not provided)
            auto_fix: Whether to automatically fix issues (overrides config)

        Returns:
            (passed: bool, results: dict)
        """
        logger.info("Running linting quality gate")

        # Convert config dataclass to dict for checker
        linting_config = {
            "enabled": self.config.linting.enabled,
            "commands": self.config.linting.commands,
            "auto_fix": self.config.linting.auto_fix,
            "required": self.config.linting.required,
        }

        # Create and run linting checker (pass runner for test compatibility)
        checker = LintingChecker(
            linting_config,
            self.project_root,
            language=language,
            auto_fix=auto_fix,
            runner=self.runner,
        )
        result = checker.run()

        # Convert CheckResult to legacy format
        return result.passed, {
            "status": result.status,
            "issues_found": result.info.get("issues_found", 0),
            "output": result.info.get("output", ""),
            "fixed": result.info.get("auto_fixed", False),
            "reason": result.info.get("reason"),
        }

    def run_formatting(
        self, language: str | None = None, auto_fix: bool | None = None
    ) -> tuple[bool, dict[str, Any]]:
        """Run code formatting.

        Args:
            language: Programming language (optional, will be detected if not provided)
            auto_fix: Whether to automatically format (overrides config)

        Returns:
            (passed: bool, results: dict)
        """
        logger.info("Running formatting quality gate")

        # Convert config dataclass to dict for checker
        formatting_config = {
            "enabled": self.config.formatting.enabled,
            "commands": self.config.formatting.commands,
            "auto_fix": self.config.formatting.auto_fix,
            "required": self.config.formatting.required,
        }

        # Create and run formatting checker (pass runner for test compatibility)
        checker = FormattingChecker(
            formatting_config,
            self.project_root,
            language=language,
            auto_fix=auto_fix,
            runner=self.runner,
        )
        result = checker.run()

        # Convert CheckResult to legacy format
        return result.passed, {
            "status": result.status,
            "formatted": result.info.get("formatted", False),
            "output": result.info.get("output", ""),
        }

    def validate_documentation(self, work_item: dict | None = None) -> tuple[bool, dict[str, Any]]:
        """Validate documentation requirements.

        Args:
            work_item: Work item dictionary (optional)

        Returns:
            (passed: bool, results: dict)
        """
        logger.info("Running documentation validation quality gate")

        # Convert config dataclass to dict for checker
        doc_config = {
            "enabled": self.config.documentation.enabled,
            "check_changelog": self.config.documentation.check_changelog,
            "check_docstrings": self.config.documentation.check_docstrings,
            "check_readme": self.config.documentation.check_readme,
        }

        # Create and run documentation checker (pass runner for test compatibility)
        checker = DocumentationChecker(
            doc_config, self.project_root, work_item=work_item, runner=self.runner
        )
        result = checker.run()

        # Convert CheckResult to legacy format
        return result.passed, {
            "status": result.status,
            "checks": result.info.get("checks", []),
            "passed": result.passed,
        }

    def validate_spec_completeness(self, work_item: dict) -> tuple[bool, dict[str, Any]]:
        """
        Validate that the work item specification file is complete.

        Part of Phase 5.7.5: Spec File Validation System

        Args:
            work_item: Work item dictionary with 'id' and 'type' fields

        Returns:
            Tuple of (passed, results)
        """
        logger.info(f"Running spec completeness validation for work item: {work_item.get('id')}")

        # Convert config dataclass to dict for checker
        spec_config = {
            "enabled": self.config.spec_completeness.enabled,
        }

        # Create and run spec completeness checker
        checker = SpecCompletenessChecker(spec_config, self.project_root, work_item=work_item)
        result = checker.run()

        # Convert CheckResult to legacy format
        if result.status == "skipped":
            return True, {"status": "skipped", "reason": result.info.get("reason", "")}

        if result.passed:
            return True, {
                "status": "passed",
                "message": result.info.get("message", ""),
            }
        else:
            return False, {
                "status": "failed",
                "errors": [
                    e.get("message", str(e)) if isinstance(e, dict) else str(e)
                    for e in result.errors
                ],
                "message": result.info.get("message", ""),
                "suggestion": result.info.get("suggestion", ""),
            }

    def run_custom_validations(self, work_item: dict) -> tuple[bool, dict[str, Any]]:
        """Run custom validation rules for work item.

        Args:
            work_item: Work item dictionary

        Returns:
            (passed: bool, results: dict)
        """
        logger.info("Running custom validations quality gate")

        # Get custom rules from full config
        full_config = self._load_full_config()
        custom_config = full_config.get("custom_validations", {})

        # Create and run custom validation checker (pass runner for test compatibility)
        checker = CustomValidationChecker(
            custom_config, self.project_root, work_item=work_item, runner=self.runner
        )
        result = checker.run()

        # Convert CheckResult to legacy format
        return result.passed, {
            "status": result.status,
            "validations": result.info.get("validations", []),
            "passed": result.passed,
        }

    def check_required_gates(self) -> tuple[bool, list[str]]:
        """
        Check if all required gates are configured.

        Returns:
            (all_required_met: bool, missing_gates: List[str])
        """
        missing = []

        # Check each quality gate
        gates = {
            "test_execution": self.config.test_execution,
            "linting": self.config.linting,
            "formatting": self.config.formatting,
            "security": self.config.security,
            "documentation": self.config.documentation,
            "spec_completeness": self.config.spec_completeness,
        }

        for gate_name, gate_config in gates.items():
            if gate_config.required and not gate_config.enabled:  # type: ignore[attr-defined]
                missing.append(gate_name)

        return len(missing) == 0, missing

    # ========================================================================
    # Integration Test Gates
    # ========================================================================

    def run_integration_tests(self, work_item: dict) -> tuple[bool, dict[str, Any]]:
        """Run integration tests for integration test work items."""
        from solokit.quality.checkers.integration import IntegrationChecker

        checker = IntegrationChecker(
            work_item=work_item,
            config=self.config.integration.__dict__,
            runner=self.runner,
            config_path=self._config_path,
        )
        result = checker.run()
        return result.passed, result.details

    def validate_integration_environment(self, work_item: dict) -> tuple[bool, dict[str, Any]]:
        """Validate integration test environment requirements."""
        from solokit.quality.checkers.integration import IntegrationChecker

        checker = IntegrationChecker(
            work_item=work_item,
            config=self.config.integration.__dict__,
            runner=self.runner,
            config_path=self._config_path,
        )
        result = checker.validate_environment()
        return result.passed, result.details

    def validate_integration_documentation(self, work_item: dict) -> tuple[bool, dict[str, Any]]:
        """Validate integration test documentation requirements."""
        from solokit.quality.checkers.integration import IntegrationChecker

        checker = IntegrationChecker(
            work_item=work_item,
            config=self.config.integration.__dict__,
            runner=self.runner,
            config_path=self._config_path,
        )
        result = checker.validate_documentation()
        return result.passed, result.details

    def verify_context7_libraries(self) -> tuple[bool, dict[str, Any]]:
        """Verify important libraries via Context7 MCP."""
        from solokit.quality.checkers.context7 import Context7Checker

        checker = Context7Checker(
            config=self.config.context7.__dict__,
            project_root=self.project_root,
            runner=self.runner,
        )
        result = checker.run()
        return result.passed, result.details

    def run_deployment_gates(self, work_item: dict) -> tuple[bool, dict[str, Any]]:
        """Run deployment-specific quality gates."""
        from solokit.quality.checkers.deployment import DeploymentChecker

        checker = DeploymentChecker(
            work_item=work_item,
            config=self.config.deployment.__dict__,
            project_root=self.project_root,
            runner=self.runner,
        )
        result = checker.run()
        return result.passed, result.details

    # ========================================================================
    # Report Generation
    # ========================================================================

    def generate_report(self, all_results: dict) -> str:
        """Generate comprehensive quality gate report.

        Args:
            all_results: Dictionary of results from all quality gates

        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 60)
        report.append("QUALITY GATE RESULTS")
        report.append("=" * 60)

        # Test results
        if "tests" in all_results:
            test_results = all_results["tests"]
            status = "✓ PASSED" if test_results.get("status") == "passed" else "✗ FAILED"
            report.append(f"\nTests: {status}")
            if test_results.get("coverage"):
                report.append(f"  Coverage: {test_results['coverage']}%")

        # Security results
        if "security" in all_results:
            sec_results = all_results["security"]
            status = "✓ PASSED" if sec_results.get("status") == "passed" else "✗ FAILED"
            report.append(f"\nSecurity: {status}")
            if sec_results.get("by_severity"):
                for severity, count in sec_results["by_severity"].items():
                    report.append(f"  {severity}: {count}")

        # Linting results
        if "linting" in all_results:
            lint_results = all_results["linting"]
            if lint_results.get("status") == "passed":
                status = "✓ PASSED"
            elif lint_results.get("status") == "skipped":
                status = "⊘ SKIPPED"
            else:
                status = "✗ FAILED"
            report.append(f"\nLinting: {status}")
            if lint_results.get("fixed"):
                report.append("  Auto-fix applied")

        # Formatting results
        if "formatting" in all_results:
            fmt_results = all_results["formatting"]
            if fmt_results.get("status") == "passed":
                status = "✓ PASSED"
            elif fmt_results.get("status") == "skipped":
                status = "⊘ SKIPPED"
            else:
                status = "✗ FAILED"
            report.append(f"\nFormatting: {status}")
            if fmt_results.get("formatted"):
                report.append("  Auto-format applied")

        # Documentation results
        if "documentation" in all_results:
            doc_results = all_results["documentation"]
            status = "✓ PASSED" if doc_results.get("status") == "passed" else "✗ FAILED"
            report.append(f"\nDocumentation: {status}")
            for check in doc_results.get("checks", []):
                check_status = "✓" if check["passed"] else "✗"
                report.append(f"  {check_status} {check['name']}")

        # Context7 results
        if "context7" in all_results:
            ctx_results = all_results["context7"]
            if ctx_results.get("status") != "skipped":
                status = "✓ PASSED" if ctx_results.get("status") == "passed" else "✗ FAILED"
                report.append(f"\nContext7: {status}")
                report.append(f"  Verified: {ctx_results.get('verified', 0)}")
                report.append(f"  Failed: {ctx_results.get('failed', 0)}")

        # Custom validations results
        if "custom" in all_results:
            custom_results = all_results["custom"]
            if custom_results.get("status") == "passed":
                status = "✓ PASSED"
            elif custom_results.get("status") == "skipped":
                status = "⊘ SKIPPED"
            else:
                status = "✗ FAILED"
            report.append(f"\nCustom Validations: {status}")
            for validation in custom_results.get("validations", []):
                val_status = "✓" if validation["passed"] else "✗"
                required_mark = " (required)" if validation["required"] else ""
                report.append(f"  {val_status} {validation['name']}{required_mark}")

        report.append("\n" + "=" * 60)

        return "\n".join(report)

    def get_remediation_guidance(self, failed_gates: list[str]) -> str:
        """Get remediation guidance for failed gates.

        Args:
            failed_gates: List of failed gate names

        Returns:
            Formatted remediation guidance string
        """
        guidance = []
        guidance.append("\nREMEDIATION GUIDANCE:")
        guidance.append("-" * 60)

        for gate in failed_gates:
            if gate == "tests":
                guidance.append("\n• Tests Failed:")
                guidance.append("  - Review test output above")
                guidance.append("  - Fix failing tests")
                guidance.append("  - Improve coverage if below threshold")

            elif gate == "security":
                guidance.append("\n• Security Issues Found:")
                guidance.append("  - Review vulnerability details above")
                guidance.append("  - Update vulnerable dependencies")
                guidance.append("  - Fix high/critical issues immediately")

            elif gate == "linting":
                guidance.append("\n• Linting Issues:")
                guidance.append("  - Run with --auto-fix to fix automatically")
                guidance.append("  - Review remaining issues manually")

            elif gate == "formatting":
                guidance.append("\n• Formatting Issues:")
                guidance.append("  - Run with --auto-format to fix automatically")
                guidance.append("  - Ensure consistent code style")

            elif gate == "documentation":
                guidance.append("\n• Documentation Issues:")
                guidance.append("  Update CHANGELOG.md with your changes:")
                guidance.append("")
                guidance.append("  ## [Unreleased]")
                guidance.append("  ### Added")
                guidance.append("  - Feature: User authentication with JWT")
                guidance.append("  - Tests: Comprehensive auth endpoint tests")
                guidance.append("")
                guidance.append("  Then commit:")
                guidance.append("    git add CHANGELOG.md")
                guidance.append("    git commit -m 'docs: Update CHANGELOG'")
                guidance.append("")
                guidance.append("  - Add docstrings to new functions")
                guidance.append("  - Update README if needed")

            elif gate == "context7":
                guidance.append("\n• Context7 Library Verification Failed:")
                guidance.append("  - Review failed library versions")
                guidance.append("  - Update outdated libraries")
                guidance.append("  - Check for security updates")

            elif gate == "custom":
                guidance.append("\n• Custom Validation Failed:")
                guidance.append("  - Review failed validation rules")
                guidance.append("  - Address required validations")
                guidance.append("  - Check work item requirements")

        return "\n".join(guidance)


def main() -> None:
    """CLI entry point."""
    gates = QualityGates()

    logger.info("Running quality gates...")

    # Run tests
    passed, results = gates.run_tests()
    logger.info(f"\nTest Execution: {'✓ PASSED' if passed else '✗ FAILED'}")
    if results.get("coverage"):
        logger.info(f"  Coverage: {results['coverage']}%")

    # Check required gates
    all_met, missing = gates.check_required_gates()
    if not all_met:
        logger.error(f"\n✗ Missing required gates: {', '.join(missing)}")


if __name__ == "__main__":
    main()
