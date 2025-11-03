"""Tests for centralized configuration management."""

import json

import pytest

from sdd.core.config import (
    ConfigManager,
    CurationConfig,
    DocumentationConfig,
    FormattingConfig,
    GitWorkflowConfig,
    LintingConfig,
    QualityGatesConfig,
    SDDConfig,
    SecurityConfig,
    SpecCompletenessConfig,
    TestExecutionConfig,
    get_config_manager,
)


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary config directory."""
    config_dir = tmp_path / ".session"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def config_file(temp_config_dir):
    """Path to config file."""
    return temp_config_dir / "config.json"


@pytest.fixture
def valid_config_data():
    """Valid configuration data."""
    return {
        "quality_gates": {
            "test_execution": {
                "enabled": True,
                "required": True,
                "coverage_threshold": 90,
                "commands": {
                    "python": "pytest --cov",
                },
            },
            "linting": {
                "enabled": False,
                "required": False,
                "auto_fix": False,
            },
            "security": {
                "enabled": True,
                "required": True,
                "fail_on": "critical",
            },
        },
        "git_workflow": {
            "mode": "direct",
            "auto_push": False,
            "auto_create_pr": False,
            "delete_branch_after_merge": False,
        },
        "curation": {
            "auto_curate": True,
            "frequency": 10,
            "dry_run": True,
            "similarity_threshold": 0.8,
        },
    }


@pytest.fixture(autouse=True)
def reset_config_manager():
    """Reset ConfigManager singleton before each test."""
    # Reset the singleton instance
    ConfigManager._instance = None
    ConfigManager._config = None
    ConfigManager._config_path = None
    yield
    # Clean up after test
    ConfigManager._instance = None
    ConfigManager._config = None
    ConfigManager._config_path = None


class TestConfigManager:
    """Test ConfigManager class."""

    def test_singleton_behavior(self):
        """Test that ConfigManager implements singleton pattern."""
        manager1 = ConfigManager()
        manager2 = ConfigManager()
        assert manager1 is manager2

    def test_get_config_manager_returns_singleton(self):
        """Test that get_config_manager returns the same instance."""
        manager1 = get_config_manager()
        manager2 = get_config_manager()
        assert manager1 is manager2

    def test_default_config_on_init(self):
        """Test that ConfigManager initializes with default config."""
        manager = ConfigManager()
        config = manager.get_config()

        assert isinstance(config, SDDConfig)
        assert isinstance(config.quality_gates, QualityGatesConfig)
        assert isinstance(config.git_workflow, GitWorkflowConfig)
        assert isinstance(config.curation, CurationConfig)

    def test_load_valid_config(self, config_file, valid_config_data):
        """Test loading a valid config file."""
        # Write valid config
        with open(config_file, "w") as f:
            json.dump(valid_config_data, f)

        manager = ConfigManager()
        manager.load_config(config_file)

        # Check quality gates
        assert manager.quality_gates.test_execution.coverage_threshold == 90
        assert manager.quality_gates.linting.enabled is False
        assert manager.quality_gates.security.fail_on == "critical"

        # Check git workflow
        assert manager.git_workflow.mode == "direct"
        assert manager.git_workflow.auto_push is False

        # Check curation
        assert manager.curation.auto_curate is True
        assert manager.curation.frequency == 10
        assert manager.curation.similarity_threshold == 0.8

    def test_load_missing_config_file(self, config_file):
        """Test loading when config file doesn't exist."""
        manager = ConfigManager()
        manager.load_config(config_file)

        # Should use defaults
        config = manager.get_config()
        assert config.quality_gates.test_execution.coverage_threshold == 80
        assert config.git_workflow.mode == "pr"
        assert config.curation.frequency == 5

    def test_load_invalid_json(self, config_file):
        """Test loading with invalid JSON."""
        # Write invalid JSON
        with open(config_file, "w") as f:
            f.write("{invalid json}")

        manager = ConfigManager()
        manager.load_config(config_file)

        # Should use defaults
        config = manager.get_config()
        assert isinstance(config, SDDConfig)
        assert config.quality_gates.test_execution.coverage_threshold == 80

    def test_load_invalid_structure(self, config_file):
        """Test loading with invalid config structure."""
        # Write config with invalid structure
        invalid_data = {
            "quality_gates": {
                "test_execution": {
                    "coverage_threshold": "not_a_number",  # Invalid type
                }
            }
        }
        with open(config_file, "w") as f:
            json.dump(invalid_data, f)

        manager = ConfigManager()
        manager.load_config(config_file)

        # Should use defaults
        config = manager.get_config()
        assert isinstance(config, SDDConfig)

    def test_caching_behavior(self, config_file, valid_config_data):
        """Test that config is cached and not re-read."""
        # Write initial config
        with open(config_file, "w") as f:
            json.dump(valid_config_data, f)

        manager = ConfigManager()
        manager.load_config(config_file)
        initial_threshold = manager.quality_gates.test_execution.coverage_threshold
        assert initial_threshold == 90

        # Modify file
        valid_config_data["quality_gates"]["test_execution"]["coverage_threshold"] = 95
        with open(config_file, "w") as f:
            json.dump(valid_config_data, f)

        # Load again without force_reload - should use cache
        manager.load_config(config_file)
        assert manager.quality_gates.test_execution.coverage_threshold == 90

    def test_force_reload(self, config_file, valid_config_data):
        """Test force_reload parameter."""
        # Write initial config
        with open(config_file, "w") as f:
            json.dump(valid_config_data, f)

        manager = ConfigManager()
        manager.load_config(config_file)
        assert manager.quality_gates.test_execution.coverage_threshold == 90

        # Modify file
        valid_config_data["quality_gates"]["test_execution"]["coverage_threshold"] = 95
        with open(config_file, "w") as f:
            json.dump(valid_config_data, f)

        # Force reload
        manager.load_config(config_file, force_reload=True)
        assert manager.quality_gates.test_execution.coverage_threshold == 95

    def test_invalidate_cache(self, config_file, valid_config_data):
        """Test invalidate_cache method."""
        # Write initial config
        with open(config_file, "w") as f:
            json.dump(valid_config_data, f)

        manager = ConfigManager()
        manager.load_config(config_file)
        assert manager.quality_gates.test_execution.coverage_threshold == 90

        # Invalidate cache
        manager.invalidate_cache()

        # Modify file
        valid_config_data["quality_gates"]["test_execution"]["coverage_threshold"] = 95
        with open(config_file, "w") as f:
            json.dump(valid_config_data, f)

        # Load again - should reload from disk
        manager.load_config(config_file)
        assert manager.quality_gates.test_execution.coverage_threshold == 95

    def test_partial_config(self, config_file):
        """Test config with only some sections defined."""
        # Config with only git_workflow
        partial_data = {
            "git_workflow": {
                "mode": "direct",
                "auto_push": False,
            }
        }
        with open(config_file, "w") as f:
            json.dump(partial_data, f)

        manager = ConfigManager()
        manager.load_config(config_file)

        # Should use defaults for missing sections
        assert manager.git_workflow.mode == "direct"
        assert manager.quality_gates.test_execution.coverage_threshold == 80
        assert manager.curation.frequency == 5

    def test_property_access(self, config_file, valid_config_data):
        """Test property access for config sections."""
        with open(config_file, "w") as f:
            json.dump(valid_config_data, f)

        manager = ConfigManager()
        manager.load_config(config_file)

        # Test property access
        quality_gates = manager.quality_gates
        assert isinstance(quality_gates, QualityGatesConfig)

        git_workflow = manager.git_workflow
        assert isinstance(git_workflow, GitWorkflowConfig)

        curation = manager.curation
        assert isinstance(curation, CurationConfig)

    def test_nested_dataclass_defaults(self):
        """Test that nested dataclasses get proper defaults."""
        manager = ConfigManager()
        config = manager.get_config()

        # Test quality gates nested configs
        assert isinstance(config.quality_gates.test_execution, TestExecutionConfig)
        assert isinstance(config.quality_gates.linting, LintingConfig)
        assert isinstance(config.quality_gates.formatting, FormattingConfig)
        assert isinstance(config.quality_gates.security, SecurityConfig)
        assert isinstance(config.quality_gates.documentation, DocumentationConfig)
        assert isinstance(config.quality_gates.spec_completeness, SpecCompletenessConfig)

        # Test default values
        assert config.quality_gates.test_execution.enabled is True
        assert config.quality_gates.test_execution.coverage_threshold == 80
        assert config.quality_gates.security.fail_on == "high"

    def test_commands_dict_defaults(self):
        """Test that command dicts have proper defaults."""
        manager = ConfigManager()
        config = manager.get_config()

        # Test execution commands
        test_commands = config.quality_gates.test_execution.commands
        assert "python" in test_commands
        assert "javascript" in test_commands
        assert "typescript" in test_commands

        # Linting commands
        lint_commands = config.quality_gates.linting.commands
        assert "python" in lint_commands
        assert lint_commands["python"] == "ruff check ."

        # Formatting commands
        format_commands = config.quality_gates.formatting.commands
        assert "python" in format_commands
        assert format_commands["python"] == "ruff format ."

    def test_multiple_modules_share_instance(self, config_file, valid_config_data):
        """Test that multiple modules can share the ConfigManager instance."""
        with open(config_file, "w") as f:
            json.dump(valid_config_data, f)

        # Simulate multiple modules getting config manager
        manager1 = get_config_manager()
        manager1.load_config(config_file)

        manager2 = get_config_manager()

        # Should be same instance with same config
        assert manager1 is manager2
        assert (
            manager1.quality_gates.test_execution.coverage_threshold
            == manager2.quality_gates.test_execution.coverage_threshold
        )

    def test_empty_sections_use_defaults(self, config_file):
        """Test that empty config sections use default values."""
        empty_data = {"quality_gates": {}, "git_workflow": {}, "curation": {}}
        with open(config_file, "w") as f:
            json.dump(empty_data, f)

        manager = ConfigManager()
        manager.load_config(config_file)

        # Should use all defaults
        assert manager.quality_gates.test_execution.coverage_threshold == 80
        assert manager.git_workflow.mode == "pr"
        assert manager.curation.frequency == 5

    def test_load_with_file_permission_error(self, config_file, monkeypatch):
        """Test loading config when file cannot be read."""
        # Create file
        with open(config_file, "w") as f:
            json.dump({}, f)

        # Mock open to raise PermissionError
        def mock_open(*args, **kwargs):
            raise PermissionError("Permission denied")

        monkeypatch.setattr("builtins.open", mock_open)

        manager = ConfigManager()
        manager.load_config(config_file)

        # Should use defaults
        config = manager.get_config()
        assert isinstance(config, SDDConfig)
        assert config.quality_gates.test_execution.coverage_threshold == 80


class TestDataclassDefaults:
    """Test dataclass default values."""

    def test_quality_gates_config_defaults(self):
        """Test QualityGatesConfig default values."""
        config = QualityGatesConfig()
        assert config.test_execution.enabled is True
        assert config.test_execution.required is True
        assert config.test_execution.coverage_threshold == 80
        assert config.linting.enabled is True
        assert config.security.fail_on == "high"

    def test_git_workflow_config_defaults(self):
        """Test GitWorkflowConfig default values."""
        config = GitWorkflowConfig()
        assert config.mode == "pr"
        assert config.auto_push is True
        assert config.auto_create_pr is True
        assert config.delete_branch_after_merge is True

    def test_curation_config_defaults(self):
        """Test CurationConfig default values."""
        config = CurationConfig()
        assert config.auto_curate is False
        assert config.frequency == 5
        assert config.dry_run is False
        assert config.similarity_threshold == 0.7

    def test_sdd_config_defaults(self):
        """Test SDDConfig creates nested configs with defaults."""
        config = SDDConfig()
        assert isinstance(config.quality_gates, QualityGatesConfig)
        assert isinstance(config.git_workflow, GitWorkflowConfig)
        assert isinstance(config.curation, CurationConfig)
