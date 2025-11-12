"""
Unit tests for project/init.py module.

Tests interactive initialization prompts and main CLI entry point.

Run tests:
    pytest tests/unit/project/test_init.py -v

Target: 90%+ coverage
"""

from unittest.mock import patch

from solokit.project.init import (
    main,
    prompt_additional_options,
    prompt_coverage_target,
    prompt_quality_tier,
    prompt_template_selection,
)


class TestPromptTemplateSelection:
    """Tests for prompt_template_selection function."""

    def test_prompt_template_selection_saas_t3(self):
        """Test selecting SaaS T3 template."""
        with patch("solokit.project.init.select_from_list") as mock_select:
            mock_select.return_value = (
                "SaaS Application (T3 Stack) - Next.js 16, React 19, tRPC, Prisma"
            )
            result = prompt_template_selection()
            assert result == "saas_t3"

    def test_prompt_template_selection_ml_ai(self):
        """Test selecting ML/AI FastAPI template."""
        with patch("solokit.project.init.select_from_list") as mock_select:
            mock_select.return_value = (
                "ML/AI Tooling (FastAPI) - FastAPI, SQLModel, Pydantic, Alembic"
            )
            result = prompt_template_selection()
            assert result == "ml_ai_fastapi"

    def test_prompt_template_selection_dashboard(self):
        """Test selecting dashboard template."""
        with patch("solokit.project.init.select_from_list") as mock_select:
            mock_select.return_value = "Internal Dashboard (Refine) - Refine, Next.js 16, shadcn/ui"
            result = prompt_template_selection()
            assert result == "dashboard_refine"

    def test_prompt_template_selection_fullstack(self):
        """Test selecting fullstack Next.js template."""
        with patch("solokit.project.init.select_from_list") as mock_select:
            mock_select.return_value = (
                "Full-Stack Product (Next.js) - Next.js 16, Prisma, Zod, Tailwind"
            )
            result = prompt_template_selection()
            assert result == "fullstack_nextjs"

    def test_prompt_template_selection_default_on_unknown(self):
        """Test that unknown selection defaults to saas_t3."""
        with patch("solokit.project.init.select_from_list") as mock_select:
            mock_select.return_value = "Unknown Template"
            result = prompt_template_selection()
            assert result == "saas_t3"


class TestPromptQualityTier:
    """Tests for prompt_quality_tier function."""

    def test_prompt_quality_tier_essential(self):
        """Test selecting essential tier."""
        with patch("solokit.project.init.select_from_list") as mock_select:
            mock_select.return_value = "Essential - Linting, formatting, type-check, basic tests"
            result = prompt_quality_tier()
            assert result == "tier-1-essential"

    def test_prompt_quality_tier_standard(self):
        """Test selecting standard tier."""
        with patch("solokit.project.init.select_from_list") as mock_select:
            mock_select.return_value = (
                "Standard - Essential + Pre-commit hooks + Security foundation"
            )
            result = prompt_quality_tier()
            assert result == "tier-2-standard"

    def test_prompt_quality_tier_comprehensive(self):
        """Test selecting comprehensive tier."""
        with patch("solokit.project.init.select_from_list") as mock_select:
            mock_select.return_value = "Comprehensive - Standard + Advanced quality + Testing"
            result = prompt_quality_tier()
            assert result == "tier-3-comprehensive"

    def test_prompt_quality_tier_production(self):
        """Test selecting production tier."""
        with patch("solokit.project.init.select_from_list") as mock_select:
            mock_select.return_value = "Production-Ready - Comprehensive + Operations + Deployment"
            result = prompt_quality_tier()
            assert result == "tier-4-production"

    def test_prompt_quality_tier_default_on_unknown(self):
        """Test that unknown selection defaults to tier-2-standard."""
        with patch("solokit.project.init.select_from_list") as mock_select:
            mock_select.return_value = "Unknown Tier"
            result = prompt_quality_tier()
            assert result == "tier-2-standard"


class TestPromptCoverageTarget:
    """Tests for prompt_coverage_target function."""

    def test_prompt_coverage_target_60(self):
        """Test selecting 60% coverage."""
        with patch("solokit.project.init.select_from_list") as mock_select:
            mock_select.return_value = "60% - Light coverage, fast iteration"
            result = prompt_coverage_target()
            assert result == 60

    def test_prompt_coverage_target_80(self):
        """Test selecting 80% coverage."""
        with patch("solokit.project.init.select_from_list") as mock_select:
            mock_select.return_value = "80% - Balanced coverage (recommended)"
            result = prompt_coverage_target()
            assert result == 80

    def test_prompt_coverage_target_90(self):
        """Test selecting 90% coverage."""
        with patch("solokit.project.init.select_from_list") as mock_select:
            mock_select.return_value = "90% - High coverage, maximum confidence"
            result = prompt_coverage_target()
            assert result == 90

    def test_prompt_coverage_target_default_on_unknown(self):
        """Test that unknown selection defaults to 80."""
        with patch("solokit.project.init.select_from_list") as mock_select:
            mock_select.return_value = "Unknown Coverage"
            result = prompt_coverage_target()
            assert result == 80


class TestPromptAdditionalOptions:
    """Tests for prompt_additional_options function."""

    def test_prompt_additional_options_all_selected(self):
        """Test selecting all additional options."""
        with patch("solokit.project.init.multi_select_list") as mock_select:
            mock_select.return_value = [
                "CI/CD - GitHub Actions workflows",
                "Docker - Container support with docker-compose",
                "Pre-commit - Automated quality checks before commits",
                "Env Templates - .env files and .editorconfig",
            ]
            result = prompt_additional_options()
            assert result == ["ci_cd", "docker", "pre_commit", "env_templates"]

    def test_prompt_additional_options_partial_selected(self):
        """Test selecting some additional options."""
        with patch("solokit.project.init.multi_select_list") as mock_select:
            mock_select.return_value = [
                "CI/CD - GitHub Actions workflows",
                "Docker - Container support with docker-compose",
            ]
            result = prompt_additional_options()
            assert result == ["ci_cd", "docker"]

    def test_prompt_additional_options_none_selected(self):
        """Test selecting no additional options."""
        with patch("solokit.project.init.multi_select_list") as mock_select:
            mock_select.return_value = []
            result = prompt_additional_options()
            assert result == []

    def test_prompt_additional_options_unknown_ignored(self):
        """Test that unknown options are ignored."""
        with patch("solokit.project.init.multi_select_list") as mock_select:
            mock_select.return_value = [
                "CI/CD - GitHub Actions workflows",
                "Unknown Option",
            ]
            result = prompt_additional_options()
            assert result == ["ci_cd"]


class TestMainFunction:
    """Tests for main CLI entry point."""

    def test_main_argument_mode_success(self):
        """Test main with all required arguments provided."""
        args = [
            "init.py",
            "--template",
            "saas_t3",
            "--tier",
            "tier-2-standard",
            "--coverage",
            "80",
        ]

        with patch("sys.argv", args):
            with patch("solokit.init.orchestrator.run_template_based_init") as mock_init:
                mock_init.return_value = 0
                exit_code = main()

                assert exit_code == 0
                mock_init.assert_called_once_with(
                    template_id="saas_t3",
                    tier="tier-2-standard",
                    coverage_target=80,
                    additional_options=[],
                )

    def test_main_argument_mode_with_options(self):
        """Test main with all arguments including options."""
        args = [
            "init.py",
            "--template",
            "ml_ai_fastapi",
            "--tier",
            "tier-3-comprehensive",
            "--coverage",
            "90",
            "--options",
            "ci_cd,docker",
        ]

        with patch("sys.argv", args):
            with patch("solokit.init.orchestrator.run_template_based_init") as mock_init:
                mock_init.return_value = 0
                exit_code = main()

                assert exit_code == 0
                mock_init.assert_called_once_with(
                    template_id="ml_ai_fastapi",
                    tier="tier-3-comprehensive",
                    coverage_target=90,
                    additional_options=["ci_cd", "docker"],
                )

    def test_main_argument_mode_partial_args_error(self, caplog):
        """Test main with partial arguments returns error."""
        args = [
            "init.py",
            "--template",
            "saas_t3",
            "--tier",
            "tier-2-standard",
            # Missing --coverage
        ]

        with patch("sys.argv", args):
            exit_code = main()

            assert exit_code == 1
            assert "all required" in caplog.text.lower()

    def test_main_argument_mode_only_template_error(self, caplog):
        """Test main with only template argument returns error."""
        args = [
            "init.py",
            "--template",
            "saas_t3",
        ]

        with patch("sys.argv", args):
            exit_code = main()

            assert exit_code == 1
            assert "all required" in caplog.text.lower()

    def test_main_interactive_mode_success(self, capsys):
        """Test main in interactive mode with user confirmation."""
        args = ["init.py"]

        with patch("sys.argv", args):
            with patch("solokit.project.init.prompt_template_selection") as mock_template:
                with patch("solokit.project.init.prompt_quality_tier") as mock_tier:
                    with patch("solokit.project.init.prompt_coverage_target") as mock_coverage:
                        with patch(
                            "solokit.project.init.prompt_additional_options"
                        ) as mock_options:
                            with patch("solokit.project.init.confirm_action") as mock_confirm:
                                with patch(
                                    "solokit.init.orchestrator.run_template_based_init"
                                ) as mock_init:
                                    mock_template.return_value = "saas_t3"
                                    mock_tier.return_value = "tier-2-standard"
                                    mock_coverage.return_value = 80
                                    mock_options.return_value = ["ci_cd"]
                                    mock_confirm.return_value = True
                                    mock_init.return_value = 0

                                    exit_code = main()

                                    assert exit_code == 0
                                    mock_init.assert_called_once_with(
                                        template_id="saas_t3",
                                        tier="tier-2-standard",
                                        coverage_target=80,
                                        additional_options=["ci_cd"],
                                    )

    def test_main_interactive_mode_user_cancels(self, capsys):
        """Test main in interactive mode when user cancels."""
        args = ["init.py"]

        with patch("sys.argv", args):
            with patch("solokit.project.init.prompt_template_selection") as mock_template:
                with patch("solokit.project.init.prompt_quality_tier") as mock_tier:
                    with patch("solokit.project.init.prompt_coverage_target") as mock_coverage:
                        with patch(
                            "solokit.project.init.prompt_additional_options"
                        ) as mock_options:
                            with patch("solokit.project.init.confirm_action") as mock_confirm:
                                mock_template.return_value = "saas_t3"
                                mock_tier.return_value = "tier-2-standard"
                                mock_coverage.return_value = 80
                                mock_options.return_value = []
                                mock_confirm.return_value = False

                                exit_code = main()

                                assert exit_code == 1
                                captured = capsys.readouterr()
                                assert "cancelled" in captured.out.lower()

    def test_main_interactive_mode_no_additional_options(self, capsys):
        """Test main in interactive mode with no additional options."""
        args = ["init.py"]

        with patch("sys.argv", args):
            with patch("solokit.project.init.prompt_template_selection") as mock_template:
                with patch("solokit.project.init.prompt_quality_tier") as mock_tier:
                    with patch("solokit.project.init.prompt_coverage_target") as mock_coverage:
                        with patch(
                            "solokit.project.init.prompt_additional_options"
                        ) as mock_options:
                            with patch("solokit.project.init.confirm_action") as mock_confirm:
                                with patch(
                                    "solokit.init.orchestrator.run_template_based_init"
                                ) as mock_init:
                                    mock_template.return_value = "dashboard_refine"
                                    mock_tier.return_value = "tier-3-comprehensive"
                                    mock_coverage.return_value = 90
                                    mock_options.return_value = []
                                    mock_confirm.return_value = True
                                    mock_init.return_value = 0

                                    exit_code = main()

                                    assert exit_code == 0
                                    captured = capsys.readouterr()
                                    assert "Additional:       None" in captured.out

    def test_main_interactive_mode_displays_summary(self, capsys):
        """Test main displays configuration summary in interactive mode."""
        args = ["init.py"]

        with patch("sys.argv", args):
            with patch("solokit.project.init.prompt_template_selection") as mock_template:
                with patch("solokit.project.init.prompt_quality_tier") as mock_tier:
                    with patch("solokit.project.init.prompt_coverage_target") as mock_coverage:
                        with patch(
                            "solokit.project.init.prompt_additional_options"
                        ) as mock_options:
                            with patch("solokit.project.init.confirm_action") as mock_confirm:
                                with patch(
                                    "solokit.init.orchestrator.run_template_based_init"
                                ) as mock_init:
                                    mock_template.return_value = "fullstack_nextjs"
                                    mock_tier.return_value = "tier-4-production"
                                    mock_coverage.return_value = 60
                                    mock_options.return_value = ["docker", "pre_commit"]
                                    mock_confirm.return_value = True
                                    mock_init.return_value = 0

                                    exit_code = main()

                                    assert exit_code == 0
                                    captured = capsys.readouterr()
                                    assert "Configuration Summary" in captured.out
                                    assert "fullstack_nextjs" in captured.out
                                    assert "tier-4-production" in captured.out
                                    assert "60%" in captured.out
                                    assert "docker, pre_commit" in captured.out

    def test_main_init_orchestrator_returns_error(self):
        """Test main propagates error from init orchestrator."""
        args = [
            "init.py",
            "--template",
            "saas_t3",
            "--tier",
            "tier-2-standard",
            "--coverage",
            "80",
        ]

        with patch("sys.argv", args):
            with patch("solokit.init.orchestrator.run_template_based_init") as mock_init:
                mock_init.return_value = 1  # Error

                exit_code = main()

                assert exit_code == 1

    def test_main_options_with_spaces(self):
        """Test main handles options with spaces in CSV."""
        args = [
            "init.py",
            "--template",
            "saas_t3",
            "--tier",
            "tier-2-standard",
            "--coverage",
            "80",
            "--options",
            "ci_cd, docker, pre_commit",
        ]

        with patch("sys.argv", args):
            with patch("solokit.init.orchestrator.run_template_based_init") as mock_init:
                mock_init.return_value = 0
                exit_code = main()

                assert exit_code == 0
                # Check that spaces are stripped
                mock_init.assert_called_once()
                call_args = mock_init.call_args[1]
                assert call_args["additional_options"] == ["ci_cd", "docker", "pre_commit"]

    def test_main_welcome_message_interactive(self, capsys):
        """Test main displays welcome message in interactive mode."""
        args = ["init.py"]

        with patch("sys.argv", args):
            with patch("solokit.project.init.prompt_template_selection") as mock_template:
                with patch("solokit.project.init.prompt_quality_tier") as mock_tier:
                    with patch("solokit.project.init.prompt_coverage_target") as mock_coverage:
                        with patch(
                            "solokit.project.init.prompt_additional_options"
                        ) as mock_options:
                            with patch("solokit.project.init.confirm_action") as mock_confirm:
                                with patch(
                                    "solokit.init.orchestrator.run_template_based_init"
                                ) as mock_init:
                                    mock_template.return_value = "saas_t3"
                                    mock_tier.return_value = "tier-2-standard"
                                    mock_coverage.return_value = 80
                                    mock_options.return_value = []
                                    mock_confirm.return_value = True
                                    mock_init.return_value = 0

                                    exit_code = main()
                                    assert exit_code == 0

                                    captured = capsys.readouterr()
                                    assert (
                                        "Welcome to Solokit Project Initialization" in captured.out
                                    )
                                    assert "Modern development stack" in captured.out
                                    assert "Claude Code integration" in captured.out
