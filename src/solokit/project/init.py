#!/usr/bin/env python3
"""
Interactive Solokit Initialization

Provides both command-line argument and interactive modes for project initialization.
All initialization flows through the template-based system with quality tiers.
"""

from __future__ import annotations

import argparse
import logging
import sys

logger = logging.getLogger(__name__)


def prompt_template_selection() -> str:
    """
    Interactively prompt user to select a project template.

    Returns:
        Selected template ID (e.g., "saas_t3")
    """
    print("\n📋 Select your project template:\n")
    print("1. SaaS Application (T3 Stack)")
    print("   Next.js 16, React 19, tRPC, Prisma, Tailwind")
    print("   Best for: Multi-tenant SaaS products\n")

    print("2. ML/AI Tooling (FastAPI)")
    print("   FastAPI, SQLModel, Pydantic, Alembic")
    print("   Best for: ML APIs, data pipelines, model serving\n")

    print("3. Internal Dashboard (Refine)")
    print("   Refine, Next.js 16, shadcn/ui, React Hook Form")
    print("   Best for: Admin panels, analytics dashboards\n")

    print("4. Full-Stack Product (Next.js)")
    print("   Next.js 16, Prisma, Zod, Tailwind")
    print("   Best for: General purpose web applications\n")

    template_map = {
        "1": "saas_t3",
        "2": "ml_ai_fastapi",
        "3": "dashboard_refine",
        "4": "fullstack_nextjs",
    }

    while True:
        if not sys.stdin.isatty():
            # Non-interactive mode - default to saas_t3
            logger.info("Non-interactive mode: defaulting to SaaS Application (T3 Stack)")
            return "saas_t3"

        choice = input("Enter choice (1-4): ").strip()
        if choice in template_map:
            return template_map[choice]
        print("❌ Invalid choice. Please enter 1-4.")


def prompt_quality_tier() -> str:
    """
    Interactively prompt user to select quality tier.

    Returns:
        Selected tier ID (e.g., "tier-2-standard")
    """
    print("\n🎯 Select quality tier:\n")
    print("1. Essential - Linting, formatting, type-check, basic tests")
    print("   Best for: Prototypes, MVPs, small internal tools\n")

    print("2. Standard - Essential + Pre-commit hooks + Security foundation")
    print("   Best for: Production apps, funded startups, small teams\n")

    print("3. Comprehensive - Standard + Advanced quality + Testing")
    print("   Best for: Production SaaS, growing teams, mission-critical apps\n")

    print("4. Production-Ready - Comprehensive + Operations + Deployment")
    print("   Best for: Enterprise apps, regulated industries, high-scale\n")

    tier_map = {
        "1": "tier-1-essential",
        "2": "tier-2-standard",
        "3": "tier-3-comprehensive",
        "4": "tier-4-production",
    }

    while True:
        if not sys.stdin.isatty():
            # Non-interactive mode - default to tier-2
            logger.info("Non-interactive mode: defaulting to Standard tier")
            return "tier-2-standard"

        choice = input("Enter choice (1-4): ").strip()
        if choice in tier_map:
            return tier_map[choice]
        print("❌ Invalid choice. Please enter 1-4.")


def prompt_coverage_target() -> int:
    """
    Interactively prompt user to select coverage target.

    Returns:
        Coverage target percentage (60, 80, or 90)
    """
    print("\n📊 Select test coverage target:\n")
    print("1. 60% - Light coverage, fast iteration")
    print("2. 80% - Balanced coverage (recommended)")
    print("3. 90% - High coverage, maximum confidence\n")

    coverage_map = {"1": 60, "2": 80, "3": 90}

    while True:
        if not sys.stdin.isatty():
            # Non-interactive mode - default to 80%
            logger.info("Non-interactive mode: defaulting to 80% coverage")
            return 80

        choice = input("Enter choice (1-3): ").strip()
        if choice in coverage_map:
            return coverage_map[choice]
        print("❌ Invalid choice. Please enter 1-3.")


def prompt_additional_options() -> list[str]:
    """
    Interactively prompt user to select additional options.

    Returns:
        List of selected option IDs (e.g., ["ci_cd", "docker"])
    """
    print("\n⚙️  Select additional options (comma-separated, or press Enter to skip):\n")
    print("1. CI/CD - GitHub Actions workflows")
    print("2. Docker - Container support with docker-compose")
    print("3. Pre-commit - Automated quality checks before commits")
    print("4. Env Templates - .env files and .editorconfig\n")
    print("Examples: '1,2' for CI/CD+Docker, '1,2,3,4' for all, or Enter for none\n")

    option_map = {
        "1": "ci_cd",
        "2": "docker",
        "3": "pre_commit",
        "4": "env_templates",
    }

    if not sys.stdin.isatty():
        # Non-interactive mode - default to all options
        logger.info("Non-interactive mode: enabling all additional options")
        return ["ci_cd", "docker", "pre_commit", "env_templates"]

    while True:
        choice = input("Enter choices (e.g., '1,2' or Enter to skip): ").strip()

        # Allow empty input (skip all options)
        if not choice:
            return []

        # Parse comma-separated choices
        selected = []
        choices = [c.strip() for c in choice.split(",")]
        valid = True

        for c in choices:
            if c not in option_map:
                print(f"❌ Invalid choice: {c}. Please use 1-4.")
                valid = False
                break
            selected.append(option_map[c])

        if valid:
            return selected


def main() -> int:
    """
    Main entry point for init command with interactive mode support.

    Supports both argument-based and interactive modes:
    - With arguments: Direct initialization
    - Without arguments: Interactive prompts

    Returns:
        0 on success, non-zero on failure
    """
    parser = argparse.ArgumentParser(description="Initialize Session-Driven Development project")
    parser.add_argument(
        "--template",
        choices=["saas_t3", "ml_ai_fastapi", "dashboard_refine", "fullstack_nextjs"],
        help="Template to use for initialization",
    )
    parser.add_argument(
        "--tier",
        choices=[
            "tier-1-essential",
            "tier-2-standard",
            "tier-3-comprehensive",
            "tier-4-production",
        ],
        help="Quality gates tier",
    )
    parser.add_argument(
        "--coverage",
        type=int,
        choices=[60, 80, 90],
        help="Test coverage target percentage",
    )
    parser.add_argument(
        "--options",
        help="Comma-separated list of additional options (ci_cd,docker,pre_commit,env_templates)",
    )

    args = parser.parse_args()

    # Import here to avoid circular imports
    from solokit.init.orchestrator import run_template_based_init

    # Determine if we're in argument mode or interactive mode
    if args.template and args.tier and args.coverage:
        # Argument mode - all required params provided
        template_id = args.template
        tier = args.tier
        coverage_target = args.coverage
        additional_options = []
        if args.options:
            additional_options = [opt.strip() for opt in args.options.split(",")]

    elif args.template or args.tier or args.coverage:
        # Partial arguments provided - error
        logger.error("❌ When using arguments, --template, --tier, and --coverage are all required")
        logger.error("\nUsage:")
        logger.error("  sk init --template=saas_t3 --tier=tier-2-standard --coverage=80")
        logger.error(
            "  sk init --template=ml_ai_fastapi --tier=tier-3-comprehensive --coverage=90 --options=ci_cd,docker"
        )
        logger.error("\nOr run without arguments for interactive mode:")
        logger.error("  sk init")
        return 1

    else:
        # Interactive mode
        print("🚀 Welcome to Solokit Project Initialization!\n")
        print("This wizard will help you set up a new project with:")
        print("  • Modern development stack")
        print("  • Quality automation")
        print("  • Session-driven workflow")
        print("  • Claude Code integration")

        template_id = prompt_template_selection()
        tier = prompt_quality_tier()
        coverage_target = prompt_coverage_target()
        additional_options = prompt_additional_options()

        # Show summary
        print("\n" + "=" * 60)
        print("📋 Configuration Summary")
        print("=" * 60)
        print(f"Template:         {template_id}")
        print(f"Quality Tier:     {tier}")
        print(f"Coverage Target:  {coverage_target}%")
        if additional_options:
            print(f"Additional:       {', '.join(additional_options)}")
        else:
            print("Additional:       None")
        print("=" * 60 + "\n")

        if sys.stdin.isatty():
            confirm = input("Proceed with initialization? (y/N): ").strip().lower()
            if confirm not in ["y", "yes"]:
                print("\n❌ Initialization cancelled")
                return 1

    # Run template-based init
    return run_template_based_init(
        template_id=template_id,
        tier=tier,
        coverage_target=coverage_target,
        additional_options=additional_options,
    )


if __name__ == "__main__":
    exit(main())
