"""
Tests for orchestrator module.

Validates complete 18-step initialization flow.

Run tests:
    pytest tests/unit/init/test_orchestrator.py -v

Target: 90%+ coverage
"""

from unittest.mock import patch

from solokit.init.orchestrator import run_template_based_init


class TestRunTemplateBasedInit:
    """Tests for run_template_based_init()."""

    def test_complete_initialization_flow(self, tmp_path, mock_template_registry):
        """Test complete initialization flow executes all steps."""
        with patch("solokit.init.orchestrator.check_blank_project_or_exit"):
            with patch("solokit.init.orchestrator.check_or_init_git"):
                with patch("solokit.init.orchestrator.validate_environment") as mock_env:
                    mock_env.return_value = {
                        "node_ok": True,
                        "node_version": "v20.0.0",
                        "python_ok": True,
                        "python_version": None,
                        "python_binary": None,
                    }

                    with patch("solokit.init.orchestrator.get_template_info") as mock_info:
                        mock_info.return_value = mock_template_registry["templates"]["saas_t3"]

                        with patch("solokit.init.orchestrator.install_template") as mock_install:
                            mock_install.return_value = {"files_installed": 42}

                            with patch("solokit.init.orchestrator.generate_readme"):
                                with patch("solokit.init.orchestrator.install_dependencies"):
                                    with patch("solokit.init.orchestrator.create_docs_structure"):
                                        with patch("solokit.init.orchestrator.generate_env_files"):
                                            with patch(
                                                "solokit.init.orchestrator.create_session_directories"
                                            ):
                                                with patch(
                                                    "solokit.init.orchestrator.initialize_tracking_files"
                                                ):
                                                    with patch(
                                                        "solokit.init.orchestrator.run_initial_scans"
                                                    ) as mock_scans:
                                                        mock_scans.return_value = {
                                                            "stack": True,
                                                            "tree": True,
                                                        }

                                                        with patch(
                                                            "solokit.init.orchestrator.install_git_hooks"
                                                        ):
                                                            with patch(
                                                                "solokit.init.orchestrator.update_gitignore"
                                                            ):
                                                                with patch(
                                                                    "solokit.init.orchestrator.create_initial_commit"
                                                                ) as mock_commit:
                                                                    mock_commit.return_value = True

                                                                    result = (
                                                                        run_template_based_init(
                                                                            "saas_t3",
                                                                            "tier-2-standard",
                                                                            80,
                                                                            ["ci_cd"],
                                                                            tmp_path,
                                                                        )
                                                                    )

                                                                    assert result == 0

    def test_validation_checks_performed(self, tmp_path):
        """Test that pre-flight validations are performed."""
        with patch("solokit.init.orchestrator.check_blank_project_or_exit") as mock_blank:
            with patch("solokit.init.orchestrator.check_or_init_git"):
                with patch("solokit.init.orchestrator.validate_environment"):
                    with patch("solokit.init.orchestrator.get_template_info"):
                        with patch("solokit.init.orchestrator.install_template"):
                            # Patch all other dependencies
                            with patch("solokit.init.orchestrator.generate_readme"):
                                with patch("solokit.init.orchestrator.install_dependencies"):
                                    with patch("solokit.init.orchestrator.create_docs_structure"):
                                        with patch(
                                            "solokit.init.orchestrator.create_session_directories"
                                        ):
                                            with patch(
                                                "solokit.init.orchestrator.initialize_tracking_files"
                                            ):
                                                with patch(
                                                    "solokit.init.orchestrator.run_initial_scans"
                                                ) as mock_scans:
                                                    mock_scans.return_value = {
                                                        "stack": True,
                                                        "tree": True,
                                                    }
                                                    with patch(
                                                        "solokit.init.orchestrator.install_git_hooks"
                                                    ):
                                                        with patch(
                                                            "solokit.init.orchestrator.update_gitignore"
                                                        ):
                                                            with patch(
                                                                "solokit.init.orchestrator.create_initial_commit"
                                                            ):
                                                                run_template_based_init(
                                                                    "saas_t3",
                                                                    "tier-1-essential",
                                                                    60,
                                                                    [],
                                                                    tmp_path,
                                                                )

                                                                mock_blank.assert_called_once_with(
                                                                    tmp_path
                                                                )

    def test_defaults_additional_options_to_empty_list(self, tmp_path):
        """Test that additional_options defaults to empty list."""
        with patch("solokit.init.orchestrator.check_blank_project_or_exit"):
            with patch("solokit.init.orchestrator.check_or_init_git"):
                with patch("solokit.init.orchestrator.validate_environment"):
                    with patch("solokit.init.orchestrator.get_template_info"):
                        with patch("solokit.init.orchestrator.install_template") as mock_install:
                            mock_install.return_value = {"files_installed": 1}
                            # Patch rest
                            with patch("solokit.init.orchestrator.generate_readme"):
                                with patch("solokit.init.orchestrator.install_dependencies"):
                                    with patch("solokit.init.orchestrator.create_docs_structure"):
                                        with patch(
                                            "solokit.init.orchestrator.create_session_directories"
                                        ):
                                            with patch(
                                                "solokit.init.orchestrator.initialize_tracking_files"
                                            ):
                                                with patch(
                                                    "solokit.init.orchestrator.run_initial_scans"
                                                ) as mock_scans:
                                                    mock_scans.return_value = {
                                                        "stack": True,
                                                        "tree": True,
                                                    }
                                                    with patch(
                                                        "solokit.init.orchestrator.install_git_hooks"
                                                    ):
                                                        with patch(
                                                            "solokit.init.orchestrator.update_gitignore"
                                                        ):
                                                            with patch(
                                                                "solokit.init.orchestrator.create_initial_commit"
                                                            ):
                                                                run_template_based_init(
                                                                    "saas_t3",
                                                                    "tier-1-essential",
                                                                    60,
                                                                    None,
                                                                    tmp_path,
                                                                )

                                                                # Verify empty list was passed
                                                                call_args = mock_install.call_args
                                                                assert call_args[0][2] == []

    def test_dependency_installation_continues_on_warning(self, tmp_path):
        """Test that init continues when dependency installation fails (warning, not error)."""
        with patch("solokit.init.orchestrator.check_blank_project_or_exit"):
            with patch("solokit.init.orchestrator.check_or_init_git"):
                with patch("solokit.init.orchestrator.validate_environment"):
                    with patch("solokit.init.orchestrator.get_template_info"):
                        with patch("solokit.init.orchestrator.install_template") as mock_install:
                            mock_install.return_value = {"files_installed": 1}

                            with patch("solokit.init.orchestrator.generate_readme"):
                                with patch(
                                    "solokit.init.orchestrator.install_dependencies",
                                    side_effect=Exception("Dep failed"),
                                ):
                                    with patch("solokit.init.orchestrator.create_docs_structure"):
                                        with patch(
                                            "solokit.init.orchestrator.create_session_directories"
                                        ):
                                            with patch(
                                                "solokit.init.orchestrator.initialize_tracking_files"
                                            ):
                                                with patch(
                                                    "solokit.init.orchestrator.run_initial_scans"
                                                ) as mock_scans:
                                                    mock_scans.return_value = {
                                                        "stack": True,
                                                        "tree": True,
                                                    }
                                                    with patch(
                                                        "solokit.init.orchestrator.install_git_hooks"
                                                    ):
                                                        with patch(
                                                            "solokit.init.orchestrator.update_gitignore"
                                                        ):
                                                            with patch(
                                                                "solokit.init.orchestrator.create_initial_commit"
                                                            ):
                                                                # Should not raise, returns 0
                                                                result = run_template_based_init(
                                                                    "saas_t3",
                                                                    "tier-1-essential",
                                                                    60,
                                                                    [],
                                                                    tmp_path,
                                                                )

                                                                assert result == 0
