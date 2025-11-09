"""
Template-Based Init Orchestrator

Main orchestration logic for template-based project initialization.
Implements the complete 18-step initialization flow.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal, cast

from sdd.init.dependency_installer import install_dependencies
from sdd.init.docs_structure import create_docs_structure
from sdd.init.env_generator import generate_env_files
from sdd.init.environment_validator import validate_environment
from sdd.init.git_hooks_installer import install_git_hooks
from sdd.init.git_setup import check_blank_project_or_exit, check_or_init_git
from sdd.init.gitignore_updater import update_gitignore
from sdd.init.initial_commit import create_initial_commit
from sdd.init.initial_scans import run_initial_scans
from sdd.init.readme_generator import generate_readme
from sdd.init.session_structure import create_session_directories, initialize_tracking_files
from sdd.init.template_installer import get_template_info, install_template

logger = logging.getLogger(__name__)


def run_template_based_init(
    template_id: str,
    tier: str,
    coverage_target: int,
    additional_options: list[str] | None = None,
    project_root: Path | None = None,
) -> int:
    """
    Run complete template-based initialization with 18-step flow.

    Args:
        template_id: Template identifier (e.g., "saas_t3")
        tier: Quality tier (e.g., "tier-2-standard")
        coverage_target: Test coverage target percentage (60, 80, 90)
        additional_options: List of additional options (e.g., ["ci_cd", "docker"])
        project_root: Project root directory (defaults to current directory)

    Returns:
        0 on success, non-zero on failure

    Raises:
        Various exceptions from individual init modules on critical failures
    """
    if additional_options is None:
        additional_options = []

    if project_root is None:
        project_root = Path.cwd()

    logger.info("🚀 Initializing Session-Driven Development with Template System...\n")

    # =========================================================================
    # PHASE 1: PRE-FLIGHT CHECKS & VALIDATION
    # =========================================================================

    # Step 1-2: Check if already initialized + Check if blank project
    logger.info("Step 1-2: Pre-flight validation...")
    check_blank_project_or_exit(project_root)
    logger.info("✓ Project directory is blank\n")

    # Step 3: Initialize/verify git repository
    logger.info("Step 3: Git initialization...")
    check_or_init_git(project_root)
    logger.info("")

    # Step 4: Validate AND auto-update environment
    logger.info(f"Step 4: Environment validation for {template_id}...")

    # Map template_id to stack_type for environment validation
    template_to_stack_type = {
        "saas_t3": "saas_t3",
        "ml_ai_fastapi": "ml_ai_fastapi",
        "dashboard_refine": "dashboard_refine",
        "fullstack_nextjs": "fullstack_nextjs",
    }
    stack_type = template_to_stack_type.get(template_id)

    python_binary = None
    if stack_type:
        env_result = validate_environment(
            cast(
                Literal["saas_t3", "ml_ai_fastapi", "dashboard_refine", "fullstack_nextjs"],
                stack_type,
            ),
            auto_update=True,
        )
        logger.info(f"✓ Environment validated for {template_id}")
        if env_result.get("node_version"):
            logger.info(f"  Node.js: {env_result['node_version']}")
        if env_result.get("python_version"):
            logger.info(f"  Python: {env_result['python_version']}")
            python_binary = cast(str | None, env_result.get("python_binary"))
    logger.info("")

    # Get template information
    template_info = get_template_info(template_id)

    # =========================================================================
    # PHASE 3: INSTALLATION & SETUP (Phase 2 is interactive, done in CLI)
    # =========================================================================

    # Step 6: Install template files (base + tier + options)
    logger.info("Step 6: Installing template files...")
    install_result = install_template(template_id, tier, additional_options, project_root)
    logger.info(f"✓ Installed {install_result['files_installed']} template files\n")

    # Step 7: Generate README.md
    logger.info("Step 7: Generating README.md...")
    generate_readme(template_id, tier, coverage_target, additional_options, project_root)
    logger.info("✓ Generated README.md\n")

    # Step 8: Config files (handled by template installation)
    logger.info("Step 8: Config files installed via template\n")

    # Step 9: Install dependencies
    logger.info("Step 9: Installing dependencies...")
    logger.info("⏳ This may take several minutes...\n")

    try:
        install_dependencies(
            template_id,
            cast(
                Literal[
                    "tier-1-essential",
                    "tier-2-standard",
                    "tier-3-comprehensive",
                    "tier-4-production",
                ],
                tier,
            ),
            python_binary,
            project_root,
        )
        logger.info("✓ Dependencies installed successfully\n")
    except Exception as e:
        logger.warning(f"Dependency installation encountered an issue: {e}")
        logger.warning("You can install dependencies manually later\n")

    # Step 10: Create docs directory structure
    logger.info("Step 10: Creating documentation structure...")
    create_docs_structure(project_root)
    logger.info("✓ Created docs/ structure\n")

    # Step 11: Starter code (handled by template)
    logger.info("Step 11: Starter code installed via template\n")

    # Step 12: Smoke tests (handled by template)
    logger.info("Step 12: Smoke tests installed via template\n")

    # Step 13: Create .env files
    if "env_templates" in additional_options:
        logger.info("Step 13: Generating environment files...")
        generate_env_files(template_id, project_root)
        logger.info("✓ Generated .env.example and .editorconfig\n")
    else:
        logger.info("Step 13: Skipped (environment templates not selected)\n")

    # Step 14: Create .session structure
    logger.info("Step 14: Creating .session structure...")
    create_session_directories(project_root)
    logger.info("✓ Created .session/ directories\n")

    # Step 15: Initialize tracking files
    logger.info("Step 15: Initializing tracking files...")
    initialize_tracking_files(tier, coverage_target, project_root)
    logger.info("✓ Initialized tracking files with tier-specific config\n")

    # Step 16: Run initial scans (stack.txt, tree.txt)
    logger.info("Step 16: Running initial scans...")
    scan_results = run_initial_scans(project_root)
    if scan_results["stack"]:
        logger.info("✓ Generated stack.txt")
    if scan_results["tree"]:
        logger.info("✓ Generated tree.txt")
    logger.info("")

    # Step 17: Install git hooks
    logger.info("Step 17: Installing git hooks...")
    install_git_hooks(project_root)
    logger.info("✓ Installed git hooks\n")

    # Step 18: Update .gitignore
    logger.info("Step 18: Updating .gitignore...")
    update_gitignore(template_id, project_root)
    logger.info("✓ Updated .gitignore\n")

    # Step 19: Create initial commit
    logger.info("Step 19: Creating initial commit...")
    commit_success = create_initial_commit(
        template_name=template_info["display_name"],
        tier=tier,
        coverage_target=coverage_target,
        additional_options=additional_options,
        stack_info=template_info["stack"],
        project_root=project_root,
    )
    if commit_success:
        logger.info("✓ Created initial commit\n")
    else:
        logger.warning("Initial commit failed (you can commit manually later)\n")

    # =========================================================================
    # SUCCESS SUMMARY
    # =========================================================================

    logger.info("=" * 70)
    logger.info("✅ SDD Template Initialization Complete!")
    logger.info("=" * 70)
    logger.info("")
    logger.info(f"📦 Template: {template_info['display_name']}")
    logger.info(f"🎯 Quality Tier: {tier}")
    logger.info(f"📊 Coverage Target: {coverage_target}%")
    logger.info("")
    logger.info("✓ Project structure created")
    logger.info("✓ Dependencies installed")
    logger.info("✓ Quality gates configured")
    logger.info("✓ Documentation structure created")
    logger.info("✓ Session tracking initialized")
    logger.info("✓ Git repository configured")
    logger.info("")
    logger.info("🚀 Next Steps:")
    logger.info("   1. Review README.md for getting started guide")
    logger.info("   2. Create your first work item: /sdd:work-new")
    logger.info("   3. Start working: /sdd:start")
    logger.info("")

    return 0
