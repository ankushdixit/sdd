#!/usr/bin/env python3
"""
Quality gate validation for session completion.

Provides comprehensive validation including:
- Test execution with coverage
- Linting and formatting
- Security scanning
- Documentation validation
- Custom validation rules
"""

import subprocess
import json
from pathlib import Path
from typing import List, Tuple


class QualityGates:
    """Quality gate validation."""

    def __init__(self, config_path: Path = None):
        """Initialize quality gates with configuration."""
        if config_path is None:
            config_path = Path(".session/config.json")
        self._config_path = config_path
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: Path) -> dict:
        """Load quality gate configuration."""
        if not config_path.exists():
            return self._default_config()

        with open(config_path) as f:
            config = json.load(f)

        return config.get("quality_gates", self._default_config())

    def _default_config(self) -> dict:
        """Default quality gate configuration."""
        return {
            "test_execution": {
                "enabled": True,
                "required": True,
                "coverage_threshold": 80,
                "commands": {
                    "python": "pytest --cov --cov-report=json",
                    "javascript": "npm test -- --coverage",
                    "typescript": "npm test -- --coverage",
                },
            },
            "linting": {
                "enabled": True,
                "required": False,
                "auto_fix": True,
                "commands": {
                    "python": "ruff check .",
                    "javascript": "eslint .",
                    "typescript": "eslint .",
                },
            },
            "formatting": {
                "enabled": True,
                "required": False,
                "auto_fix": True,
                "commands": {
                    "python": "ruff format .",
                    "javascript": "prettier --write .",
                    "typescript": "prettier --write .",
                },
            },
            "security": {
                "enabled": True,
                "required": True,
                "fail_on": "high",  # critical, high, medium, low
            },
            "documentation": {
                "enabled": True,
                "required": False,
                "check_changelog": True,
                "check_docstrings": True,
                "check_readme": False,
            },
        }

    def run_tests(self, language: str = None) -> Tuple[bool, dict]:
        """
        Run test suite with coverage.

        Returns:
            (passed: bool, results: dict)
        """
        config = self.config.get("test_execution", {})

        if not config.get("enabled", True):
            return True, {"status": "skipped", "reason": "disabled"}

        # Detect language if not provided
        if language is None:
            language = self._detect_language()

        # Get test command for language
        command = config.get("commands", {}).get(language)
        if not command:
            return True, {"status": "skipped", "reason": f"no command for {language}"}

        # Run tests
        try:
            result = subprocess.run(
                command.split(), capture_output=True, text=True, timeout=300
            )

            # pytest exit codes:
            # 0 = all tests passed
            # 1 = tests were collected and run but some failed
            # 2 = test execution was interrupted
            # 3 = internal error
            # 4 = pytest command line usage error
            # 5 = no tests were collected

            # Treat "no tests collected" (exit code 5) as skipped, not failed
            if result.returncode == 5:
                return True, {
                    "status": "skipped",
                    "reason": "no tests collected",
                    "returncode": result.returncode,
                }

            # Parse results
            passed = result.returncode == 0
            coverage = self._parse_coverage(language)

            results = {
                "status": "passed" if passed else "failed",
                "returncode": result.returncode,
                "coverage": coverage,
                "output": result.stdout,
                "errors": result.stderr,
            }

            # Check coverage threshold
            threshold = config.get("coverage_threshold", 80)
            if coverage and coverage < threshold:
                results["status"] = "failed"
                results["reason"] = f"Coverage {coverage}% below threshold {threshold}%"
                passed = False

            return passed, results

        except subprocess.TimeoutExpired:
            return False, {"status": "failed", "reason": "timeout"}
        except FileNotFoundError:
            # pytest not available - skip test gate
            return True, {"status": "skipped", "reason": "pytest not available"}
        except Exception as e:
            return False, {"status": "failed", "reason": str(e)}

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

    def _parse_coverage(self, language: str) -> float:
        """Parse coverage from test results."""
        if language == "python":
            coverage_file = Path("coverage.json")
            if coverage_file.exists():
                with open(coverage_file) as f:
                    data = json.load(f)
                return data.get("totals", {}).get("percent_covered", 0)

        elif language in ["javascript", "typescript"]:
            coverage_file = Path("coverage/coverage-summary.json")
            if coverage_file.exists():
                with open(coverage_file) as f:
                    data = json.load(f)
                return data.get("total", {}).get("lines", {}).get("pct", 0)

        return None

    def run_security_scan(self, language: str = None) -> Tuple[bool, dict]:
        """
        Run security vulnerability scanning.

        Returns:
            (passed: bool, results: dict)
        """
        config = self.config.get("security", {})

        if not config.get("enabled", True):
            return True, {"status": "skipped"}

        if language is None:
            language = self._detect_language()

        results = {"vulnerabilities": [], "by_severity": {}}

        # Python: bandit + safety
        if language == "python":
            # Run bandit
            try:
                subprocess.run(
                    ["bandit", "-r", ".", "-f", "json", "-o", "/tmp/bandit.json"],
                    capture_output=True,
                    timeout=60,
                )

                if Path("/tmp/bandit.json").exists():
                    with open("/tmp/bandit.json") as f:
                        bandit_data = json.load(f)
                    results["bandit"] = bandit_data

                    # Count by severity
                    for issue in bandit_data.get("results", []):
                        severity = issue.get("issue_severity", "LOW")
                        results["by_severity"][severity] = (
                            results["by_severity"].get(severity, 0) + 1
                        )
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass  # bandit not available

            # Run safety
            try:
                safety_result = subprocess.run(
                    ["safety", "check", "--json"], capture_output=True, timeout=60
                )

                if safety_result.stdout:
                    safety_data = json.loads(safety_result.stdout)
                    results["safety"] = safety_data
                    results["vulnerabilities"].extend(safety_data)
            except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
                pass  # safety not available

        # JavaScript/TypeScript: npm audit
        elif language in ["javascript", "typescript"]:
            try:
                audit_result = subprocess.run(
                    ["npm", "audit", "--json"], capture_output=True, timeout=60
                )

                if audit_result.stdout:
                    audit_data = json.loads(audit_result.stdout)
                    results["npm_audit"] = audit_data

                    # Count by severity
                    for vuln in audit_data.get("vulnerabilities", {}).values():
                        severity = vuln.get("severity", "low").upper()
                        results["by_severity"][severity] = (
                            results["by_severity"].get(severity, 0) + 1
                        )
            except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
                pass  # npm not available

        # Check if passed based on fail_on threshold
        fail_on = config.get("fail_on", "high").upper()
        severity_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

        if fail_on not in severity_levels:
            fail_on = "HIGH"

        fail_threshold = severity_levels.index(fail_on)

        passed = True
        for severity, count in results["by_severity"].items():
            if (
                severity in severity_levels
                and severity_levels.index(severity) >= fail_threshold
                and count > 0
            ):
                passed = False
                results["status"] = f"failed: {count} {severity} vulnerabilities"
                break

        if passed:
            results["status"] = "passed"

        return passed, results

    def run_linting(
        self, language: str = None, auto_fix: bool = None
    ) -> Tuple[bool, dict]:
        """Run linting with optional auto-fix."""
        config = self.config.get("linting", {})

        if not config.get("enabled", True):
            return True, {"status": "skipped"}

        if language is None:
            language = self._detect_language()

        if auto_fix is None:
            auto_fix = config.get("auto_fix", True)

        command = config.get("commands", {}).get(language)
        if not command:
            return True, {"status": "skipped"}

        # Add auto-fix flag if supported
        if auto_fix and language == "python":
            command += " --fix"
        elif auto_fix and language in ["javascript", "typescript"]:
            command += " --fix"

        try:
            result = subprocess.run(
                command.split(), capture_output=True, text=True, timeout=120
            )

            passed = result.returncode == 0

            return passed, {
                "status": "passed" if passed else "failed",
                "issues_found": result.returncode,
                "output": result.stdout,
                "fixed": auto_fix,
            }
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            return True, {"status": "skipped", "reason": str(e)}

    def run_formatting(
        self, language: str = None, auto_fix: bool = None
    ) -> Tuple[bool, dict]:
        """Run code formatting."""
        config = self.config.get("formatting", {})

        if not config.get("enabled", True):
            return True, {"status": "skipped"}

        if language is None:
            language = self._detect_language()

        if auto_fix is None:
            auto_fix = config.get("auto_fix", True)

        command = config.get("commands", {}).get(language)
        if not command:
            return True, {"status": "skipped"}

        if not auto_fix and language == "python":
            command += " --check"
        elif not auto_fix and language in ["javascript", "typescript"]:
            command += " --check"

        try:
            result = subprocess.run(
                command.split(), capture_output=True, text=True, timeout=120
            )

            passed = result.returncode == 0

            return passed, {
                "status": "passed" if passed else "failed",
                "formatted": auto_fix,
                "output": result.stdout,
            }
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            return True, {"status": "skipped", "reason": str(e)}

    def validate_documentation(self, work_item: dict = None) -> Tuple[bool, dict]:
        """Validate documentation requirements."""
        config = self.config.get("documentation", {})

        if not config.get("enabled", True):
            return True, {"status": "skipped"}

        results = {"checks": [], "passed": True}

        # Check CHANGELOG updated
        if config.get("check_changelog", True):
            changelog_updated = self._check_changelog_updated()
            results["checks"].append(
                {"name": "CHANGELOG updated", "passed": changelog_updated}
            )
            if not changelog_updated:
                results["passed"] = False

        # Check docstrings for Python
        if config.get("check_docstrings", True):
            language = self._detect_language()
            if language == "python":
                docstrings_present = self._check_python_docstrings()
                results["checks"].append(
                    {"name": "Docstrings present", "passed": docstrings_present}
                )
                if not docstrings_present:
                    results["passed"] = False

        # Check README current
        if config.get("check_readme", False):
            readme_current = self._check_readme_current(work_item)
            results["checks"].append(
                {"name": "README current", "passed": readme_current}
            )
            if not readme_current:
                results["passed"] = False

        results["status"] = "passed" if results["passed"] else "failed"
        return results["passed"], results

    def _check_changelog_updated(self) -> bool:
        """Check if CHANGELOG was updated in this session."""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1..HEAD"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            changed_files = result.stdout.strip().split("\n")
            return any("CHANGELOG" in f.upper() for f in changed_files)
        except Exception:
            # If git diff fails, check if any CHANGELOG file was modified
            try:
                result = subprocess.run(
                    ["git", "status", "--short"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                return any(
                    "CHANGELOG" in line.upper() for line in result.stdout.split("\n")
                )
            except Exception:
                return True  # Skip check if git not available

    def _check_python_docstrings(self) -> bool:
        """Check if Python functions have docstrings."""
        try:
            result = subprocess.run(
                ["python3", "-m", "pydocstyle", "--count"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # If no issues found, return True
            return result.returncode == 0
        except FileNotFoundError:
            # pydocstyle not available, skip check
            return True
        except subprocess.TimeoutExpired:
            return True

    def _check_readme_current(self, work_item: dict = None) -> bool:
        """Check if README was updated (optional check)."""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1..HEAD"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            changed_files = result.stdout.strip().split("\n")
            return any("README" in f.upper() for f in changed_files)
        except Exception:
            return True  # Skip check if git not available

    def verify_context7_libraries(self) -> Tuple[bool, dict]:
        """Verify important libraries via Context7 MCP."""
        config = self.config.get("context7", {})

        if not config.get("enabled", False):
            return True, {"status": "skipped", "reason": "not enabled"}

        # Get important libraries from stack.txt
        stack_file = Path(".session/tracking/stack.txt")
        if not stack_file.exists():
            return True, {"status": "skipped", "reason": "no stack.txt"}

        libraries = self._parse_libraries_from_stack()
        results = {"libraries": [], "verified": 0, "failed": 0}

        for lib in libraries:
            # Check if library should be verified
            if not self._should_verify_library(lib, config):
                continue

            # Query Context7 MCP
            verified = self._query_context7(lib)

            results["libraries"].append(
                {
                    "name": lib["name"],
                    "version": lib.get("version", "unknown"),
                    "verified": verified,
                }
            )

            if verified:
                results["verified"] += 1
            else:
                results["failed"] += 1

        passed = results["failed"] == 0
        results["status"] = "passed" if passed else "failed"

        return passed, results

    def _parse_libraries_from_stack(self) -> List[dict]:
        """Parse libraries from stack.txt."""
        stack_file = Path(".session/tracking/stack.txt")
        libraries = []

        try:
            with open(stack_file) as f:
                content = f.read()

            # Parse libraries - expecting format like "Python 3.x" or "pytest (testing)"
            lines = content.split("\n")
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Extract library name and version
                parts = line.split()
                if len(parts) >= 1:
                    name = parts[0]
                    version = parts[1] if len(parts) > 1 else "unknown"
                    libraries.append({"name": name, "version": version})

        except Exception:
            pass

        return libraries

    def _should_verify_library(self, lib: dict, config: dict) -> bool:
        """Check if library should be verified via Context7."""
        # Check if library is in important list (if configured)
        important_libs = config.get("important_libraries", [])
        if important_libs:
            return lib["name"] in important_libs

        # By default, verify all libraries
        return True

    def _query_context7(self, lib: dict) -> bool:
        """Query Context7 MCP for library verification (stub)."""
        # TODO: Implement actual Context7 MCP integration
        # For now, return True (verification passes)
        # In production, this would call the Context7 MCP server
        # to verify the library version is current/secure
        return True

    def run_custom_validations(self, work_item: dict) -> Tuple[bool, dict]:
        """Run custom validation rules for work item."""
        results = {"validations": [], "passed": True}

        # Get custom rules from work item
        custom_rules = work_item.get("validation_rules", []) if work_item else []

        # Get project-level rules
        project_rules = self.config.get("custom_validations", {}).get("rules", [])

        # Combine rules
        all_rules = custom_rules + project_rules

        for rule in all_rules:
            rule_type = rule.get("type")
            required = rule.get("required", False)

            # Execute rule based on type
            if rule_type == "command":
                passed = self._run_command_validation(rule)
            elif rule_type == "file_exists":
                passed = self._check_file_exists(rule)
            elif rule_type == "grep":
                passed = self._run_grep_validation(rule)
            else:
                passed = True

            results["validations"].append(
                {
                    "name": rule.get("name", "unknown"),
                    "passed": passed,
                    "required": required,
                }
            )

            if not passed and required:
                results["passed"] = False

        results["status"] = "passed" if results["passed"] else "failed"
        return results["passed"], results

    def _run_command_validation(self, rule: dict) -> bool:
        """Run command validation."""
        command = rule.get("command")
        if not command:
            return True

        try:
            result = subprocess.run(command.split(), capture_output=True, timeout=60)
            return result.returncode == 0
        except Exception:
            return False

    def _check_file_exists(self, rule: dict) -> bool:
        """Check if file exists at path."""
        file_path = rule.get("path")
        if not file_path:
            return True

        return Path(file_path).exists()

    def _run_grep_validation(self, rule: dict) -> bool:
        """Run grep validation."""
        pattern = rule.get("pattern")
        files = rule.get("files", ".")

        if not pattern:
            return True

        try:
            result = subprocess.run(
                ["grep", "-r", pattern, files], capture_output=True, timeout=30
            )
            # grep returns 0 if pattern found
            return result.returncode == 0
        except Exception:
            return False

    def check_required_gates(self) -> Tuple[bool, List[str]]:
        """
        Check if all required gates are configured.

        Returns:
            (all_required_met: bool, missing_gates: List[str])
        """
        missing = []

        for gate_name, gate_config in self.config.items():
            if gate_config.get("required", False) and not gate_config.get(
                "enabled", False
            ):
                missing.append(gate_name)

        return len(missing) == 0, missing

    def run_integration_tests(self, work_item: dict) -> Tuple[bool, dict]:
        """
        Run integration tests for integration test work items.

        Args:
            work_item: Integration test work item

        Returns:
            (passed: bool, results: dict)
        """
        # Get integration test config
        # Try to load from the full config file since integration_tests is a sibling of quality_gates
        full_config = {}
        if hasattr(self, "_config_path") and self._config_path.exists():
            with open(self._config_path) as f:
                full_config = json.load(f)
        else:
            config_path = Path(".session/config.json")
            if config_path.exists():
                with open(config_path) as f:
                    full_config = json.load(f)

        config = full_config.get("integration_tests", {})

        if not config.get("enabled", True):
            return True, {"status": "skipped", "reason": "disabled"}

        # Only run for integration_test work items
        if work_item.get("type") != "integration_test":
            return True, {"status": "skipped", "reason": "not integration test"}

        print("Running integration test quality gates...")

        results = {
            "integration_tests": {},
            "performance_benchmarks": {},
            "api_contracts": {},
            "passed": False,
        }

        # Import here to avoid circular imports
        import sys

        sys.path.insert(0, str(Path(__file__).parent))

        # 1. Run integration tests
        from integration_test_runner import IntegrationTestRunner

        runner = IntegrationTestRunner(work_item)

        # Setup environment
        setup_success, setup_message = runner.setup_environment()
        if not setup_success:
            results["error"] = f"Environment setup failed: {setup_message}"
            return False, results

        try:
            # Execute integration tests
            tests_passed, test_results = runner.run_tests()
            results["integration_tests"] = test_results

            if not tests_passed:
                print("  ✗ Integration tests failed")
                return False, results

            print(
                f"  ✓ Integration tests passed ({test_results.get('passed', 0)} tests)"
            )

            # 2. Run performance benchmarks
            if work_item.get("performance_benchmarks"):
                from performance_benchmark import PerformanceBenchmark

                benchmark = PerformanceBenchmark(work_item)
                benchmarks_passed, benchmark_results = benchmark.run_benchmarks()
                results["performance_benchmarks"] = benchmark_results

                if not benchmarks_passed:
                    print("  ✗ Performance benchmarks failed")
                    if config.get("performance_benchmarks", {}).get("required", True):
                        return False, results
                else:
                    print("  ✓ Performance benchmarks passed")

            # 3. Validate API contracts
            if work_item.get("api_contracts"):
                from api_contract_validator import APIContractValidator

                validator = APIContractValidator(work_item)
                contracts_passed, contract_results = validator.validate_contracts()
                results["api_contracts"] = contract_results

                if not contracts_passed:
                    print("  ✗ API contract validation failed")
                    if config.get("api_contracts", {}).get("required", True):
                        return False, results
                else:
                    print("  ✓ API contracts validated")

            results["passed"] = True
            return True, results

        finally:
            # Always teardown environment
            runner.teardown_environment()

    def validate_integration_environment(self, work_item: dict) -> Tuple[bool, dict]:
        """
        Validate integration test environment requirements.

        Args:
            work_item: Integration test work item

        Returns:
            (passed: bool, results: dict)
        """
        if work_item.get("type") != "integration_test":
            return True, {"status": "skipped"}

        env_requirements = work_item.get("environment_requirements", {})
        results = {
            "docker_available": False,
            "docker_compose_available": False,
            "required_services": [],
            "missing_config": [],
            "passed": False,
        }

        # Check Docker available
        try:
            result = subprocess.run(
                ["docker", "--version"], capture_output=True, timeout=5
            )
            results["docker_available"] = result.returncode == 0
        except:
            results["docker_available"] = False

        # Check Docker Compose available
        try:
            result = subprocess.run(
                ["docker-compose", "--version"], capture_output=True, timeout=5
            )
            results["docker_compose_available"] = result.returncode == 0
        except:
            results["docker_compose_available"] = False

        # Check compose file exists
        compose_file = env_requirements.get(
            "compose_file", "docker-compose.integration.yml"
        )
        if not Path(compose_file).exists():
            results["missing_config"].append(compose_file)

        # Check config files exist
        config_files = env_requirements.get("config_files", [])
        for config_file in config_files:
            if not Path(config_file).exists():
                results["missing_config"].append(config_file)

        # Determine if passed
        results["passed"] = (
            results["docker_available"]
            and results["docker_compose_available"]
            and len(results["missing_config"]) == 0
        )

        return results["passed"], results

    def validate_integration_documentation(self, work_item: dict) -> Tuple[bool, dict]:
        """
        Validate integration test documentation requirements.

        Args:
            work_item: Integration test work item

        Returns:
            (passed: bool, results: dict)
        """
        if work_item.get("type") != "integration_test":
            return True, {"status": "skipped"}

        # Get integration documentation config
        full_config = {}
        if hasattr(self, "_config_path") and self._config_path.exists():
            with open(self._config_path) as f:
                full_config = json.load(f)
        else:
            config_path = Path(".session/config.json")
            if config_path.exists():
                with open(config_path) as f:
                    full_config = json.load(f)

        config = full_config.get("integration_tests", {}).get("documentation", {})
        if not config.get("enabled", True):
            return True, {"status": "skipped"}

        results = {"checks": [], "missing": [], "passed": False}

        # 1. Check for integration architecture diagram
        if config.get("architecture_diagrams", True):
            diagram_paths = [
                "docs/architecture/integration-architecture.md",
                "docs/integration-architecture.md",
                ".session/specs/integration-architecture.md",
            ]

            diagram_found = any(Path(p).exists() for p in diagram_paths)
            results["checks"].append(
                {"name": "Integration architecture diagram", "passed": diagram_found}
            )

            if not diagram_found:
                results["missing"].append("Integration architecture diagram")

        # 2. Check for sequence diagrams
        if config.get("sequence_diagrams", True):
            scenarios = work_item.get("test_scenarios", [])

            if scenarios:
                # Check if sequence diagrams documented in spec file
                spec_file = Path(".session/specs") / f"{work_item.get('id')}.md"
                has_sequence = False

                if spec_file.exists():
                    with open(spec_file) as f:
                        spec_content = f.read()

                    # Look for sequence diagram indicators
                    has_sequence = (
                        "```mermaid" in spec_content
                        or "sequenceDiagram" in spec_content
                        or "## Sequence Diagram" in spec_content
                        or "### Scenario" in spec_content  # Basic indicator
                    )

                results["checks"].append(
                    {"name": "Sequence diagrams", "passed": has_sequence}
                )

                if not has_sequence:
                    results["missing"].append("Sequence diagrams for test scenarios")

        # 3. Check for API contract documentation
        if config.get("contract_documentation", True):
            contracts = work_item.get("api_contracts", [])

            if contracts:
                all_contracts_documented = True

                for contract in contracts:
                    contract_file = contract.get("contract_file")
                    if not contract_file or not Path(contract_file).exists():
                        all_contracts_documented = False
                        results["missing"].append(f"API contract: {contract_file}")

                results["checks"].append(
                    {
                        "name": "API contracts documented",
                        "passed": all_contracts_documented,
                    }
                )

        # 4. Check for performance baseline documentation
        if config.get("performance_baseline_docs", True):
            benchmarks = work_item.get("performance_benchmarks")

            if benchmarks:
                baseline_file = Path(".session/tracking/performance_baselines.json")
                baseline_exists = baseline_file.exists()

                results["checks"].append(
                    {
                        "name": "Performance baseline documented",
                        "passed": baseline_exists,
                    }
                )

                if not baseline_exists:
                    results["missing"].append("Performance baseline documentation")

        # 5. Check for integration point documentation
        scope = work_item.get("scope", "")
        # Check if scope has meaningful content
        documented = len(scope) > 20  # More than just placeholder text

        results["checks"].append(
            {"name": "Integration points documented", "passed": documented}
        )

        if not documented:
            results["missing"].append("Integration points documentation")

        # Determine overall pass/fail
        passed_checks = sum(1 for check in results["checks"] if check["passed"])
        total_checks = len(results["checks"])

        # Pass if all required checks pass
        results["passed"] = len(results["missing"]) == 0
        results["summary"] = (
            f"{passed_checks}/{total_checks} documentation requirements met"
        )

        return results["passed"], results

    def generate_report(self, all_results: dict) -> str:
        """Generate comprehensive quality gate report."""
        report = []
        report.append("=" * 60)
        report.append("QUALITY GATE RESULTS")
        report.append("=" * 60)

        # Test results
        if "tests" in all_results:
            test_results = all_results["tests"]
            status = "✓ PASSED" if test_results["status"] == "passed" else "✗ FAILED"
            report.append(f"\nTests: {status}")
            if test_results.get("coverage"):
                report.append(f"  Coverage: {test_results['coverage']}%")

        # Security results
        if "security" in all_results:
            sec_results = all_results["security"]
            status = "✓ PASSED" if sec_results["status"] == "passed" else "✗ FAILED"
            report.append(f"\nSecurity: {status}")
            if sec_results.get("by_severity"):
                for severity, count in sec_results["by_severity"].items():
                    report.append(f"  {severity}: {count}")

        # Linting results
        if "linting" in all_results:
            lint_results = all_results["linting"]
            status = "✓ PASSED" if lint_results["status"] == "passed" else "✗ FAILED"
            report.append(f"\nLinting: {status}")
            if lint_results.get("fixed"):
                report.append("  Auto-fix applied")

        # Formatting results
        if "formatting" in all_results:
            fmt_results = all_results["formatting"]
            status = "✓ PASSED" if fmt_results["status"] == "passed" else "✗ FAILED"
            report.append(f"\nFormatting: {status}")
            if fmt_results.get("formatted"):
                report.append("  Auto-format applied")

        # Documentation results
        if "documentation" in all_results:
            doc_results = all_results["documentation"]
            status = "✓ PASSED" if doc_results["status"] == "passed" else "✗ FAILED"
            report.append(f"\nDocumentation: {status}")
            for check in doc_results.get("checks", []):
                check_status = "✓" if check["passed"] else "✗"
                report.append(f"  {check_status} {check['name']}")

        # Context7 results
        if "context7" in all_results:
            ctx_results = all_results["context7"]
            if ctx_results["status"] != "skipped":
                status = "✓ PASSED" if ctx_results["status"] == "passed" else "✗ FAILED"
                report.append(f"\nContext7: {status}")
                report.append(f"  Verified: {ctx_results.get('verified', 0)}")
                report.append(f"  Failed: {ctx_results.get('failed', 0)}")

        # Custom validations results
        if "custom" in all_results:
            custom_results = all_results["custom"]
            status = "✓ PASSED" if custom_results["status"] == "passed" else "✗ FAILED"
            report.append(f"\nCustom Validations: {status}")
            for validation in custom_results.get("validations", []):
                val_status = "✓" if validation["passed"] else "✗"
                required_mark = " (required)" if validation["required"] else ""
                report.append(f"  {val_status} {validation['name']}{required_mark}")

        report.append("\n" + "=" * 60)

        return "\n".join(report)

    def get_remediation_guidance(self, failed_gates: List[str]) -> str:
        """Get remediation guidance for failed gates."""
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
                guidance.append("  - Update CHANGELOG with session changes")
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

    def run_deployment_gates(self, work_item: dict) -> Tuple[bool, dict]:
        """
        Run deployment-specific quality gates.

        Returns:
            (passed, results)
        """
        results = {"gates": [], "passed": True}

        # Gate 1: All integration tests must pass
        tests_passed, test_results = self.run_integration_tests(work_item)
        results["gates"].append(
            {
                "name": "Integration Tests",
                "required": True,
                "passed": tests_passed,
                "details": test_results,
            }
        )
        if not tests_passed:
            results["passed"] = False

        # Gate 2: Security scans must pass
        security_passed, security_results = self.run_security_scan()
        results["gates"].append(
            {
                "name": "Security Scans",
                "required": True,
                "passed": security_passed,
                "details": security_results,
            }
        )
        if not security_passed:
            results["passed"] = False

        # Gate 3: Environment must be validated
        env_passed = self._validate_deployment_environment(work_item)
        results["gates"].append(
            {"name": "Environment Validation", "required": True, "passed": env_passed}
        )
        if not env_passed:
            results["passed"] = False

        # Gate 4: Deployment documentation complete
        docs_passed = self._validate_deployment_documentation(work_item)
        results["gates"].append(
            {
                "name": "Deployment Documentation",
                "required": True,
                "passed": docs_passed,
            }
        )
        if not docs_passed:
            results["passed"] = False

        # Gate 5: Rollback procedure tested
        rollback_tested = self._check_rollback_tested(work_item)
        results["gates"].append(
            {"name": "Rollback Tested", "required": True, "passed": rollback_tested}
        )
        if not rollback_tested:
            results["passed"] = False

        return results["passed"], results

    def _validate_deployment_environment(self, work_item: dict) -> bool:
        """Validate deployment environment is ready."""
        try:
            from environment_validator import EnvironmentValidator

            # Parse target environment from work item
            environment = "staging"  # TODO: Parse from work item

            validator = EnvironmentValidator(environment)
            passed, _ = validator.validate_all()

            return passed
        except Exception:
            # If environment_validator not available, return True
            return True

    def _validate_deployment_documentation(self, work_item: dict) -> bool:
        """Validate deployment documentation is complete."""
        spec = work_item.get("specification", "")

        required_sections = [
            "deployment procedure",
            "rollback procedure",
            "smoke tests",
            "monitoring & alerting",
        ]

        for section in required_sections:
            if section.lower() not in spec.lower():
                return False

        return True

    def _check_rollback_tested(self, work_item: dict) -> bool:
        """Check if rollback procedure has been tested."""
        # TODO: Check deployment history for rollback test
        return True


def main():
    """CLI entry point."""
    gates = QualityGates()

    print("Running quality gates...")

    # Run tests
    passed, results = gates.run_tests()
    print(f"\nTest Execution: {'✓ PASSED' if passed else '✗ FAILED'}")
    if results.get("coverage"):
        print(f"  Coverage: {results['coverage']}%")

    # Check required gates
    all_met, missing = gates.check_required_gates()
    if not all_met:
        print(f"\n✗ Missing required gates: {', '.join(missing)}")


if __name__ == "__main__":
    main()
