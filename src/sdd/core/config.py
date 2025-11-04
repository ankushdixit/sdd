"""Centralized configuration management with caching and validation.

This module provides a singleton ConfigManager that loads, validates, and caches
configuration from .session/config.json. It replaces the duplicated configuration
loading logic scattered across multiple modules.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ExecutionConfig:
    """Test execution configuration."""

    enabled: bool = True
    required: bool = True
    coverage_threshold: int = 80
    commands: dict[str, str] = field(
        default_factory=lambda: {
            "python": "pytest --cov=src/sdd --cov-report=json",
            "javascript": "npm test -- --coverage",
            "typescript": "npm test -- --coverage",
        }
    )


@dataclass
class LintingConfig:
    """Linting configuration."""

    enabled: bool = True
    required: bool = False
    auto_fix: bool = True
    commands: dict[str, str] = field(
        default_factory=lambda: {
            "python": "ruff check .",
            "javascript": "npx eslint .",
            "typescript": "npx eslint .",
        }
    )


@dataclass
class FormattingConfig:
    """Formatting configuration."""

    enabled: bool = True
    required: bool = False
    auto_fix: bool = True
    commands: dict[str, str] = field(
        default_factory=lambda: {
            "python": "ruff format .",
            "javascript": "npx prettier .",
            "typescript": "npx prettier .",
        }
    )


@dataclass
class SecurityConfig:
    """Security scanning configuration."""

    enabled: bool = True
    required: bool = True
    fail_on: str = "high"  # critical, high, medium, low


@dataclass
class DocumentationConfig:
    """Documentation validation configuration."""

    enabled: bool = True
    required: bool = False
    check_changelog: bool = True
    check_docstrings: bool = True
    check_readme: bool = False


@dataclass
class SpecCompletenessConfig:
    """Spec completeness validation configuration."""

    enabled: bool = True
    required: bool = True


@dataclass
class QualityGatesConfig:
    """Quality gates configuration."""

    test_execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    linting: LintingConfig = field(default_factory=LintingConfig)
    formatting: FormattingConfig = field(default_factory=FormattingConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    documentation: DocumentationConfig = field(default_factory=DocumentationConfig)
    spec_completeness: SpecCompletenessConfig = field(default_factory=SpecCompletenessConfig)


@dataclass
class GitWorkflowConfig:
    """Git workflow configuration."""

    mode: str = "pr"
    auto_push: bool = True
    auto_create_pr: bool = True
    delete_branch_after_merge: bool = True
    pr_title_template: str = "{type}: {title}"
    pr_body_template: str = "## Work Item: {work_item_id}\n\n{description}\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)"


@dataclass
class CurationConfig:
    """Learning curation configuration."""

    auto_curate: bool = False
    frequency: int = 5
    dry_run: bool = False
    similarity_threshold: float = 0.7


@dataclass
class SDDConfig:
    """Main SDD configuration."""

    quality_gates: QualityGatesConfig = field(default_factory=QualityGatesConfig)
    git_workflow: GitWorkflowConfig = field(default_factory=GitWorkflowConfig)
    curation: CurationConfig = field(default_factory=CurationConfig)


class ConfigManager:
    """Centralized configuration management with caching and validation.

    This class implements the Singleton pattern to ensure a single source of truth
    for configuration across the entire application. It loads configuration from
    .session/config.json, validates it, and caches it for performance.

    Example:
        >>> config_mgr = get_config_manager()
        >>> config_mgr.load_config(Path(".session/config.json"))
        >>> quality_config = config_mgr.quality_gates
        >>> print(quality_config.test_execution.coverage_threshold)
        80
    """

    _instance: Optional["ConfigManager"] = None
    _config: Optional[SDDConfig] = None
    _config_path: Optional[Path] = None

    def __new__(cls) -> "ConfigManager":
        """Ensure only one instance of ConfigManager exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize with default configuration if not already initialized."""
        if self._config is None:
            self._config = SDDConfig()

    def load_config(self, config_path: Path, force_reload: bool = False) -> None:
        """Load configuration from file.

        Args:
            config_path: Path to config.json file
            force_reload: Force reload even if already cached

        Note:
            If the config file doesn't exist or is invalid, default configuration
            is used and errors are logged.
        """
        # Skip if already loaded and not forcing reload
        if not force_reload and self._config_path == config_path:
            logger.debug("Config already loaded from %s, using cache", config_path)
            return

        self._config_path = config_path

        if not config_path.exists():
            logger.info("Config file not found at %s, using defaults", config_path)
            self._config = SDDConfig()
            return

        try:
            with open(config_path, encoding="utf-8") as f:
                data = json.load(f)

            # Parse config sections with defaults
            quality_gates_data = self._parse_quality_gates(data.get("quality_gates", {}))
            git_workflow_data = data.get("git_workflow", {})
            curation_data = data.get("curation", {})

            # Create config with parsed data
            self._config = SDDConfig(
                quality_gates=quality_gates_data,
                git_workflow=GitWorkflowConfig(**git_workflow_data)
                if git_workflow_data
                else GitWorkflowConfig(),
                curation=CurationConfig(**curation_data) if curation_data else CurationConfig(),
            )

            logger.info("Loaded configuration from %s", config_path)

        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in %s: %s", config_path, e)
            self._config = SDDConfig()
        except TypeError as e:
            logger.error("Invalid config structure in %s: %s", config_path, e)
            self._config = SDDConfig()
        except Exception as e:
            logger.error("Error loading config from %s: %s", config_path, e)
            self._config = SDDConfig()

    def _parse_quality_gates(self, data: dict) -> QualityGatesConfig:
        """Parse quality gates configuration with nested structures.

        Args:
            data: Raw quality gates configuration dict

        Returns:
            Validated QualityGatesConfig with defaults for missing values
        """
        try:
            # Parse nested configs
            test_exec_data = data.get("test_execution", {})
            linting_data = data.get("linting", {})
            formatting_data = data.get("formatting", {})
            security_data = data.get("security", {})
            documentation_data = data.get("documentation", {})
            spec_completeness_data = data.get("spec_completeness", {})

            return QualityGatesConfig(
                test_execution=ExecutionConfig(**test_exec_data)
                if test_exec_data
                else ExecutionConfig(),
                linting=LintingConfig(**linting_data) if linting_data else LintingConfig(),
                formatting=FormattingConfig(**formatting_data)
                if formatting_data
                else FormattingConfig(),
                security=SecurityConfig(**security_data) if security_data else SecurityConfig(),
                documentation=DocumentationConfig(**documentation_data)
                if documentation_data
                else DocumentationConfig(),
                spec_completeness=SpecCompletenessConfig(**spec_completeness_data)
                if spec_completeness_data
                else SpecCompletenessConfig(),
            )
        except TypeError as e:
            logger.warning("Invalid quality_gates structure, using defaults: %s", e)
            return QualityGatesConfig()

    @property
    def quality_gates(self) -> QualityGatesConfig:
        """Get quality gates configuration.

        Returns:
            Quality gates configuration with all sub-configurations
        """
        return self._config.quality_gates

    @property
    def git_workflow(self) -> GitWorkflowConfig:
        """Get git workflow configuration.

        Returns:
            Git workflow configuration
        """
        return self._config.git_workflow

    @property
    def curation(self) -> CurationConfig:
        """Get curation configuration.

        Returns:
            Learning curation configuration
        """
        return self._config.curation

    def get_config(self) -> SDDConfig:
        """Get full configuration.

        Returns:
            Complete SDD configuration
        """
        return self._config

    def invalidate_cache(self) -> None:
        """Invalidate cached configuration.

        Forces next load_config() call to reload from disk.
        Useful for testing and when config file changes.
        """
        self._config_path = None
        logger.debug("Configuration cache invalidated")


# Global instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get global ConfigManager instance.

    Returns:
        Singleton ConfigManager instance

    Example:
        >>> config = get_config_manager()
        >>> config.load_config(Path(".session/config.json"))
        >>> print(config.quality_gates.test_execution.enabled)
        True
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
