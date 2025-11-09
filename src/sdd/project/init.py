#!/usr/bin/env python3
"""
Deterministic SDD initialization - transforms any project into working SDD project.
Philosophy: Don't check and warn - CREATE and FIX.
"""

from __future__ import annotations

import json
import logging
import shutil
import sys
from pathlib import Path

from sdd.core.command_runner import CommandRunner
from sdd.core.constants import GIT_QUICK_TIMEOUT, GIT_STANDARD_TIMEOUT
from sdd.core.exceptions import (
    DirectoryNotEmptyError,
    ErrorCode,
    FileOperationError,
    GitError,
    NotAGitRepoError,
    TemplateNotFoundError,
    ValidationError,
)

logger = logging.getLogger(__name__)


# ============================================================================
# LEGACY INIT FUNCTIONS
# These functions are kept for backward compatibility with init_project()
# New template-based init uses modules in src/sdd/init/ instead
# ============================================================================


def check_or_init_git(project_root: Path | None = None) -> bool:
    """
    Check if git is initialized, if not initialize it.

    Args:
        project_root: Root directory of the project. Defaults to current working directory.

    Returns:
        True if git repository exists or was successfully initialized.

    Raises:
        GitError: If git initialization or branch configuration fails.

    Note:
        This function prints success messages but does not print errors - it raises exceptions instead.
    """
    if project_root is None:
        project_root = Path.cwd()

    git_dir = project_root / ".git"

    if git_dir.exists():
        logger.info("Git repository already initialized")
        return True

    runner = CommandRunner(default_timeout=GIT_QUICK_TIMEOUT, working_dir=project_root)

    # Initialize git
    result = runner.run(["git", "init"], check=True)
    if not result.success:
        raise GitError(
            message="Failed to initialize git repository",
            code=ErrorCode.GIT_COMMAND_FAILED,
            context={"stderr": result.stderr, "command": "git init"},
            remediation="Ensure git is installed and you have write permissions in the directory",
        )
    logger.info("Initialized git repository")

    # Set default branch to main (modern convention)
    result = runner.run(["git", "branch", "-m", "main"], check=True)
    if not result.success:
        raise GitError(
            message="Failed to set default branch to 'main'",
            code=ErrorCode.GIT_COMMAND_FAILED,
            context={"stderr": result.stderr, "command": "git branch -m main"},
            remediation="Manually run 'git branch -m main' in the repository",
        )
    logger.info("Set default branch to 'main'")

    return True


def install_git_hooks(project_root: Path | None = None) -> bool:
    """
    Install git hooks from templates.

    Args:
        project_root: Root directory of the project. Defaults to current working directory.

    Returns:
        True if git hooks were successfully installed.

    Raises:
        NotAGitRepoError: If .git/hooks directory doesn't exist (git not initialized).
        TemplateNotFoundError: If hook template file is not found.
        FileOperationError: If hook installation or permission setting fails.
    """
    if project_root is None:
        project_root = Path.cwd()

    git_hooks_dir = project_root / ".git" / "hooks"

    # Check if .git/hooks exists
    if not git_hooks_dir.exists():
        raise NotAGitRepoError(str(project_root))

    # Get template directory
    template_dir = Path(__file__).parent.parent / "templates" / "git-hooks"

    # Install prepare-commit-msg hook
    hook_template = template_dir / "prepare-commit-msg"
    hook_dest = git_hooks_dir / "prepare-commit-msg"

    if not hook_template.exists():
        raise TemplateNotFoundError(
            template_name="prepare-commit-msg", template_path=str(template_dir)
        )

    try:
        shutil.copy(hook_template, hook_dest)
        # Make executable (chmod +x)
        import stat

        hook_dest.chmod(hook_dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        logger.info("Installed git prepare-commit-msg hook")
        return True
    except Exception as e:
        raise FileOperationError(
            operation="install",
            file_path=str(hook_dest),
            details=f"Failed to copy or set permissions: {str(e)}",
            cause=e,
        )


def detect_project_type() -> str:
    """Detect project type from existing files."""
    if Path("package.json").exists():
        if Path("tsconfig.json").exists():
            return "typescript"
        return "javascript"
    elif Path("pyproject.toml").exists() or Path("setup.py").exists():
        return "python"
    else:
        # No project files found - ask user
        logger.info("\nNo project files detected. What type of project is this?")
        logger.info("1. TypeScript")
        logger.info("2. JavaScript")
        logger.info("3. Python")

        if not sys.stdin.isatty():
            # Non-interactive mode - default to TypeScript
            logger.info("Non-interactive mode: defaulting to TypeScript")
            return "typescript"

        choice = input("Enter choice (1-3): ").strip()
        return {"1": "typescript", "2": "javascript", "3": "python"}.get(choice, "typescript")


def ensure_package_manager_file(project_type: str) -> None:
    """
    Create or update package manager file with required dependencies.

    Args:
        project_type: Type of project (typescript, javascript, or python).

    Raises:
        ValidationError: If project_type is invalid.
        TemplateNotFoundError: If required template file is not found.
        FileOperationError: If file read/write operations fail.

    Note:
        Prints informational messages about created/updated files but raises exceptions on errors.
    """
    if project_type not in ["typescript", "javascript", "python"]:
        raise ValidationError(
            message=f"Invalid project type: {project_type}",
            code=ErrorCode.INVALID_WORK_ITEM_TYPE,
            context={"project_type": project_type},
            remediation="Use 'typescript', 'javascript', or 'python'",
        )

    template_dir = Path(__file__).parent.parent / "templates"

    if project_type in ["typescript", "javascript"]:
        package_json = Path("package.json")

        if not package_json.exists():
            logger.info("Creating package.json...")
            # Get project name from directory
            project_name = Path.cwd().name
            project_desc = f"A {project_type} project with Session-Driven Development"

            # Load template and replace placeholders
            template_path = template_dir / "package.json.template"
            if not template_path.exists():
                raise TemplateNotFoundError(
                    template_name="package.json.template", template_path=str(template_dir)
                )

            try:
                template_content = template_path.read_text()
                content = template_content.replace("{project_name}", project_name)
                content = content.replace("{project_description}", project_desc)
                package_json.write_text(content)
                logger.info(f"Created package.json for {project_name}")
            except Exception as e:
                raise FileOperationError(
                    operation="create",
                    file_path=str(package_json),
                    details=f"Failed to create package.json from template: {str(e)}",
                    cause=e,
                )
        else:
            logger.info("Found package.json")
            # Ensure required scripts and devDependencies exist
            try:
                with open(package_json) as f:
                    data = json.load(f)
            except json.JSONDecodeError as e:
                raise FileOperationError(
                    operation="parse",
                    file_path=str(package_json),
                    details=f"Invalid JSON in package.json: {str(e)}",
                    cause=e,
                )

            # Ensure scripts
            required_scripts = {
                "test": "jest",
                "lint": "eslint src tests --ext .ts,.tsx,.js,.jsx"
                if project_type == "typescript"
                else "eslint src tests --ext .js,.jsx",
                "format": 'prettier --write "src/**/*" "tests/**/*"',
            }
            if project_type == "typescript":
                required_scripts["build"] = "tsc"

            if "scripts" not in data:
                data["scripts"] = {}

            scripts_modified = False
            for script, cmd in required_scripts.items():
                if script not in data["scripts"]:
                    data["scripts"][script] = cmd
                    logger.info(f"Added script: {script}")
                    scripts_modified = True

            # Ensure devDependencies
            if "devDependencies" not in data:
                data["devDependencies"] = {}

            # Common dependencies for all JS/TS projects
            required_deps = {
                "jest": "^29.5.0",
                "prettier": "^3.0.0",
                "eslint": "^8.40.0",
                "@types/jest": "^29.5.0",
                "@types/node": "^20.0.0",
            }

            # TypeScript-specific dependencies
            if project_type == "typescript":
                required_deps.update(
                    {
                        "@typescript-eslint/eslint-plugin": "^6.0.0",
                        "@typescript-eslint/parser": "^6.0.0",
                        "ts-jest": "^29.1.0",
                        "typescript": "^5.0.0",
                    }
                )

            deps_modified = False
            for pkg, version in required_deps.items():
                if pkg not in data["devDependencies"]:
                    data["devDependencies"][pkg] = version
                    logger.info(f"Added devDependency: {pkg}")
                    deps_modified = True

            # Save back only if modified
            if scripts_modified or deps_modified:
                try:
                    with open(package_json, "w") as f:
                        json.dump(data, f, indent=2)
                    if deps_modified:
                        logger.info("Run 'npm install' to install new dependencies")
                except Exception as e:
                    raise FileOperationError(
                        operation="write",
                        file_path=str(package_json),
                        details=f"Failed to save package.json: {str(e)}",
                        cause=e,
                    )

    elif project_type == "python":
        pyproject = Path("pyproject.toml")

        if not pyproject.exists():
            logger.info("Creating pyproject.toml...")
            project_name = Path.cwd().name.replace("-", "_")
            project_desc = "A Python project with Session-Driven Development"

            template_path = template_dir / "pyproject.toml.template"
            if not template_path.exists():
                raise TemplateNotFoundError(
                    template_name="pyproject.toml.template", template_path=str(template_dir)
                )

            try:
                template_content = template_path.read_text()
                content = template_content.replace("{project_name}", project_name)
                content = template_content.replace("{project_description}", project_desc)
                pyproject.write_text(content)
                logger.info(f"Created pyproject.toml for {project_name}")
            except Exception as e:
                raise FileOperationError(
                    operation="create",
                    file_path=str(pyproject),
                    details=f"Failed to create pyproject.toml from template: {str(e)}",
                    cause=e,
                )
        else:
            logger.info("Found pyproject.toml")
            # Check if it has dev dependencies section
            try:
                content = pyproject.read_text()
                if "[project.optional-dependencies]" not in content and "dev" not in content:
                    logger.info(
                        "Note: Add [project.optional-dependencies] section with pytest, pytest-cov, ruff"
                    )
                    logger.info("Or install manually: pip install pytest pytest-cov ruff")
            except Exception as e:
                raise FileOperationError(
                    operation="read",
                    file_path=str(pyproject),
                    details=f"Failed to read pyproject.toml: {str(e)}",
                    cause=e,
                )


def ensure_config_files(project_type: str) -> None:
    """
    Create all required config files from templates.

    Args:
        project_type: Type of project (typescript, javascript, or python).

    Raises:
        FileOperationError: If file copy operation fails.

    Note:
        Prints informational messages about created/found files.
        Missing templates are silently skipped (no error raised).
    """
    template_dir = Path(__file__).parent.parent / "templates"

    # Common configs
    configs_to_create = [
        ("CHANGELOG.md", "CHANGELOG.md"),
    ]

    if project_type in ["typescript", "javascript"]:
        configs_to_create.extend(
            [
                (".eslintrc.json", ".eslintrc.json"),
                (".prettierrc.json", ".prettierrc.json"),
                (".prettierignore", ".prettierignore"),
            ]
        )

        # Use correct jest config based on project type
        if project_type == "typescript":
            configs_to_create.append(("jest.config.js", "jest.config.js"))
            configs_to_create.append(("tsconfig.json", "tsconfig.json"))
        else:  # javascript
            configs_to_create.append(("jest.config.js.javascript", "jest.config.js"))

    for template_name, dest_name in configs_to_create:
        dest_path = Path(dest_name)
        if not dest_path.exists():
            template_path = template_dir / template_name
            if template_path.exists():
                try:
                    shutil.copy(template_path, dest_path)
                    logger.info(f"Created {dest_name}")
                except Exception as e:
                    raise FileOperationError(
                        operation="copy",
                        file_path=str(dest_path),
                        details=f"Failed to copy config file: {str(e)}",
                        cause=e,
                    )
        else:
            logger.info(f"Found {dest_name}")


def install_dependencies(project_type: str) -> None:
    """
    Install project dependencies.

    Args:
        project_type: Type of project (typescript, javascript, or python).

    Raises:
        CommandExecutionError: If dependency installation command fails critically.

    Note:
        Prints informational messages. Some failures are logged as warnings rather than exceptions
        to allow the initialization to continue (user can manually install dependencies later).
    """
    if project_type in ["typescript", "javascript"]:
        # Always run npm install to ensure new devDependencies are installed
        logger.info("\nInstalling npm dependencies...")
        try:
            runner = CommandRunner(default_timeout=300)
            result = runner.run(["npm", "install"], check=True)
            if result.success:
                logger.info("Dependencies installed")
            else:
                logger.warning("npm install failed - you may need to run it manually")
        except Exception as e:
            logger.warning(f"npm install failed: {e} - you may need to run it manually")

    elif project_type == "python":
        # Check if we're in a venv, if not create one
        if not (Path("venv").exists() or Path(".venv").exists()):
            logger.info("\nCreating Python virtual environment...")
            try:
                runner = CommandRunner(default_timeout=60)
                result = runner.run([sys.executable, "-m", "venv", "venv"], check=True)
                if result.success:
                    logger.info("Created venv/")
                    logger.info(
                        "Activate with: source venv/bin/activate (Unix) or venv\\Scripts\\activate (Windows)"
                    )
                else:
                    logger.warning("venv creation failed")
                    return
            except Exception as e:
                logger.warning(f"venv creation failed: {e}")
                return

        # Try to install dev dependencies
        logger.info("\nInstalling Python dependencies...")
        pip_cmd = "venv/bin/pip" if Path("venv").exists() else ".venv/bin/pip"
        if Path(pip_cmd).exists():
            try:
                runner = CommandRunner(default_timeout=300)
                result = runner.run([pip_cmd, "install", "-e", ".[dev]"], check=True)
                if result.success:
                    logger.info("Dependencies installed")
                else:
                    logger.warning(
                        "pip install failed - you may need to activate venv and install manually"
                    )
            except Exception as e:
                logger.warning(
                    f"pip install failed: {e} - you may need to activate venv and install manually"
                )
        else:
            logger.warning("Please activate virtual environment and run: pip install -e .[dev]")


def create_smoke_tests(project_type: str) -> None:
    """
    Create initial smoke tests that validate SDD setup.

    Args:
        project_type: Type of project (typescript, javascript, or python).

    Raises:
        FileOperationError: If test directory creation or file copy fails.

    Note:
        Prints informational messages about created/found test files.
        Missing templates are silently skipped (no error raised).
    """
    template_dir = Path(__file__).parent.parent / "templates" / "tests"
    test_dir = Path("tests")

    try:
        test_dir.mkdir(exist_ok=True)
    except Exception as e:
        raise FileOperationError(
            operation="create",
            file_path=str(test_dir),
            details=f"Failed to create tests directory: {str(e)}",
            cause=e,
        )

    if project_type == "typescript":
        test_file = test_dir / "sdd-setup.test.ts"
        template_name = "sdd-setup.test.ts"
        if not test_file.exists():
            template_file = template_dir / template_name
            if template_file.exists():
                try:
                    shutil.copy(template_file, test_file)
                    logger.info(f"Created smoke tests: {test_file}")
                except Exception as e:
                    raise FileOperationError(
                        operation="copy",
                        file_path=str(test_file),
                        details=f"Failed to copy smoke test template: {str(e)}",
                        cause=e,
                    )
        else:
            logger.info(f"Found {test_file}")

    elif project_type == "javascript":
        test_file = test_dir / "sdd-setup.test.js"
        template_name = "sdd-setup.test.js"
        if not test_file.exists():
            template_file = template_dir / template_name
            if template_file.exists():
                try:
                    shutil.copy(template_file, test_file)
                    logger.info(f"Created smoke tests: {test_file}")
                except Exception as e:
                    raise FileOperationError(
                        operation="copy",
                        file_path=str(test_file),
                        details=f"Failed to copy smoke test template: {str(e)}",
                        cause=e,
                    )
        else:
            logger.info(f"Found {test_file}")

    elif project_type == "python":
        test_file = test_dir / "test_sdd_setup.py"
        if not test_file.exists():
            template_file = template_dir / "test_sdd_setup.py"
            if template_file.exists():
                try:
                    shutil.copy(template_file, test_file)
                    logger.info(f"Created smoke tests: {test_file}")
                except Exception as e:
                    raise FileOperationError(
                        operation="copy",
                        file_path=str(test_file),
                        details=f"Failed to copy smoke test template: {str(e)}",
                        cause=e,
                    )
        else:
            logger.info(f"Found {test_file}")


def create_session_structure() -> None:
    """
    Create .session directory structure.

    Raises:
        FileOperationError: If directory creation fails.

    Note:
        Prints informational messages about created directories.
    """
    session_dir = Path(".session")

    logger.info("\nCreating .session/ structure...")

    # Create directories
    try:
        (session_dir / "tracking").mkdir(parents=True)
        (session_dir / "briefings").mkdir(parents=True)
        (session_dir / "history").mkdir(parents=True)
        (session_dir / "specs").mkdir(parents=True)
    except Exception as e:
        raise FileOperationError(
            operation="create",
            file_path=str(session_dir),
            details=f"Failed to create .session directory structure: {str(e)}",
            cause=e,
        )

    logger.info("Created .session/tracking/")
    logger.info("Created .session/briefings/")
    logger.info("Created .session/history/")
    logger.info("Created .session/specs/")


def initialize_tracking_files() -> None:
    """
    Initialize tracking files from templates.

    Raises:
        FileOperationError: If file operations fail.
        TemplateNotFoundError: If required template files are missing.

    Note:
        Creates tracking files, config.json, and schema files in .session directory.
    """
    session_dir = Path(".session")
    template_dir = Path(__file__).parent.parent / "templates"

    logger.info("\nInitializing tracking files...")

    # Copy templates
    tracking_files = [
        ("work_items.json", "tracking/work_items.json"),
        ("learnings.json", "tracking/learnings.json"),
        ("status_update.json", "tracking/status_update.json"),
    ]

    for src, dst in tracking_files:
        src_path = template_dir / src
        dst_path = session_dir / dst
        if src_path.exists():
            try:
                shutil.copy(src_path, dst_path)
                logger.info(f"Created {dst}")
            except Exception as e:
                raise FileOperationError(
                    operation="copy",
                    file_path=str(dst_path),
                    details=f"Failed to copy tracking file template: {str(e)}",
                    cause=e,
                )

    # Create empty files for stack and tree tracking
    try:
        (session_dir / "tracking" / "stack_updates.json").write_text(
            json.dumps({"updates": []}, indent=2)
        )
        logger.info("Created stack_updates.json")

        (session_dir / "tracking" / "tree_updates.json").write_text(
            json.dumps({"updates": []}, indent=2)
        )
        logger.info("Created tree_updates.json")
    except Exception as e:
        raise FileOperationError(
            operation="create",
            file_path=str(session_dir / "tracking"),
            details=f"Failed to create tracking files: {str(e)}",
            cause=e,
        )

    # Create config.json with default settings
    config_data = {
        "curation": {
            "auto_curate": True,
            "frequency": 5,
            "dry_run": False,
            "similarity_threshold": 0.7,
            "categories": [
                "architecture_patterns",
                "gotchas",
                "best_practices",
                "technical_debt",
                "performance_insights",
                "security",
            ],
        },
        "quality_gates": {
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
                "required": True,
                "auto_fix": True,
                "commands": {
                    "python": "ruff check .",
                    "javascript": "npx eslint . --ext .js,.jsx",
                    "typescript": "npx eslint . --ext .ts,.tsx",
                },
            },
            "formatting": {
                "enabled": True,
                "required": True,
                "auto_fix": True,
                "commands": {
                    "python": "ruff format .",
                    "javascript": "npx prettier .",
                    "typescript": "npx prettier .",
                },
            },
            "security": {"enabled": True, "required": True, "fail_on": "high"},
            "documentation": {
                "enabled": True,
                "required": True,
                "check_changelog": True,
                "check_docstrings": True,
                "check_readme": False,
            },
            "context7": {
                "enabled": False,
                "required": True,
                "important_libraries": [],
            },
            "custom_validations": {"rules": []},
        },
        "integration_tests": {
            "enabled": True,
            "docker_compose_file": "docker-compose.integration.yml",
            "environment_validation": True,
            "health_check_timeout": 300,
            "test_data_fixtures": True,
            "parallel_execution": True,
            "performance_benchmarks": {
                "enabled": True,
                "required": True,
                "regression_threshold": 0.10,
                "baseline_storage": ".session/tracking/performance_baselines.json",
                "load_test_tool": "wrk",
                "metrics": ["response_time", "throughput", "resource_usage"],
            },
            "api_contracts": {
                "enabled": True,
                "required": True,
                "contract_format": "openapi",
                "breaking_change_detection": True,
                "version_storage": ".session/tracking/api_contracts/",
                "fail_on_breaking_changes": True,
            },
            "documentation": {
                "architecture_diagrams": True,
                "sequence_diagrams": True,
                "contract_documentation": True,
                "performance_baseline_docs": True,
            },
        },
        "git_workflow": {
            "mode": "pr",
            "auto_push": True,
            "auto_create_pr": True,
            "delete_branch_after_merge": True,
            "pr_title_template": "{type}: {title}",
            "pr_body_template": "## Summary\n\n{description}\n\n## Work Item\n- ID: {work_item_id}\n- Type: {type}\n- Session: {session_num}\n\n## Changes\n{commit_messages}\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>",
        },
    }
    try:
        (session_dir / "config.json").write_text(json.dumps(config_data, indent=2))
        logger.info("Created config.json")
    except Exception as e:
        raise FileOperationError(
            operation="create",
            file_path=str(session_dir / "config.json"),
            details=f"Failed to create config.json: {str(e)}",
            cause=e,
        )

    # Copy config schema file
    schema_source = Path(__file__).parent.parent / "templates" / "config.schema.json"
    schema_dest = session_dir / "config.schema.json"

    if schema_source.exists() and not schema_dest.exists():
        try:
            shutil.copy(schema_source, schema_dest)
            logger.info("Created config.schema.json")
        except Exception as e:
            raise FileOperationError(
                operation="copy",
                file_path=str(schema_dest),
                details=f"Failed to copy config schema: {str(e)}",
                cause=e,
            )


def run_initial_scans() -> None:
    """
    Run initial stack and tree scans with FIXED path resolution (Bug #12).

    Raises:
        None - failures are logged as warnings to allow initialization to continue.

    Note:
        Uses absolute paths to stack.py and tree.py scripts.
        Failures don't block initialization - user can generate these later.
    """
    logger.info("\nGenerating project context...")

    # Get SDD installation directory
    script_dir = Path(__file__).parent
    runner = CommandRunner(default_timeout=GIT_STANDARD_TIMEOUT)

    # Run stack.py with absolute path
    try:
        result = runner.run(["python", str(script_dir / "stack.py")], check=True)
        if result.success:
            logger.info("Generated stack.txt")
        else:
            logger.warning("Could not generate stack.txt")
            if result.stderr:
                logger.warning(f"Error: {result.stderr.strip()}")
    except Exception as e:
        logger.warning(f"Stack generation failed: {e}")

    # Run tree.py with absolute path
    try:
        result = runner.run(["python", str(script_dir / "tree.py")], check=True)
        if result.success:
            logger.info("Generated tree.txt")
        else:
            logger.warning("Could not generate tree.txt")
            if result.stderr:
                logger.warning(f"Error: {result.stderr.strip()}")
    except Exception as e:
        logger.warning(f"Tree generation failed: {e}")


def ensure_gitignore_entries() -> None:
    """
    Add .session patterns and OS-specific files to .gitignore.

    Raises:
        FileOperationError: If .gitignore read/write operations fail.

    Note:
        Prints informational messages about updated .gitignore.
    """
    gitignore = Path(".gitignore")

    required_entries = [
        ".session/briefings/",
        ".session/history/",
        "coverage/",
        "coverage.json",
        "node_modules/",
        "dist/",
        "venv/",
        ".venv/",
        "*.pyc",
        "__pycache__/",
    ]

    # OS-specific files
    os_specific_entries = [
        ".DS_Store           # macOS",
        ".DS_Store?          # macOS",
        "._*                 # macOS resource forks",
        ".Spotlight-V100     # macOS",
        ".Trashes            # macOS",
        "Thumbs.db           # Windows",
        "ehthumbs.db         # Windows",
        "Desktop.ini         # Windows",
        "$RECYCLE.BIN/       # Windows",
        "*~                  # Linux backup files",
    ]

    try:
        existing_content = gitignore.read_text() if gitignore.exists() else ""
    except Exception as e:
        raise FileOperationError(
            operation="read",
            file_path=str(gitignore),
            details=f"Failed to read .gitignore: {str(e)}",
            cause=e,
        )

    entries_to_add = []
    for entry in required_entries:
        if entry not in existing_content:
            entries_to_add.append(entry)

    # First pass: check which patterns need to be added
    os_patterns_needed = []
    for entry in os_specific_entries:
        # Skip comment-only lines in first pass
        pattern = entry.split("#")[0].strip()
        if pattern and pattern not in existing_content:
            os_patterns_needed.append(entry)

    # If we need to add any OS patterns, include the header
    os_entries_to_add = []
    if os_patterns_needed:
        # Add the section header first
        os_entries_to_add.append("# OS-specific files")
        # Then add all the patterns
        os_entries_to_add.extend(os_patterns_needed)

    if entries_to_add or os_entries_to_add:
        logger.info("\nUpdating .gitignore...")
        try:
            with open(gitignore, "a") as f:
                if existing_content and not existing_content.endswith("\n"):
                    f.write("\n")

                if entries_to_add:
                    f.write("\n# SDD-related patterns\n")
                    for entry in entries_to_add:
                        f.write(f"{entry}\n")

                if os_entries_to_add:
                    f.write("\n")
                    for entry in os_entries_to_add:
                        f.write(f"{entry}\n")

            total_added = len(entries_to_add) + len(
                [e for e in os_entries_to_add if not e.startswith("#")]
            )
            logger.info(f"Added {total_added} entries to .gitignore")
        except Exception as e:
            raise FileOperationError(
                operation="write",
                file_path=str(gitignore),
                details=f"Failed to update .gitignore: {str(e)}",
                cause=e,
            )
    else:
        logger.info(".gitignore already up to date")


def create_initial_commit(project_root: Path | None = None) -> bool:
    """
    Create initial commit after project initialization.

    Args:
        project_root: Root directory of the project. Defaults to current working directory.

    Returns:
        True if initial commit was created or already exists.

    Raises:
        GitError: If git add or commit operations fail critically.

    Note:
        Prints informational messages. Some failures are logged as warnings to allow
        the initialization to complete (user can commit manually later).
    """
    if project_root is None:
        project_root = Path.cwd()

    runner = CommandRunner(default_timeout=GIT_STANDARD_TIMEOUT, working_dir=project_root)

    try:
        # Check if repository has any commits by trying to count them
        # This will fail gracefully if no commits exist yet
        result = runner.run(["git", "rev-list", "--count", "--all"], check=False)

        if result.success and result.stdout.strip() and int(result.stdout.strip()) > 0:
            logger.info("Git repository already has commits, skipping initial commit")
            return True

    except Exception:
        # If command fails (e.g., no commits yet), continue to create initial commit
        pass

    try:
        # Stage all initialized files
        result = runner.run(["git", "add", "-A"], check=True)
        if not result.success:
            logger.warning(f"Git add failed: {result.stderr}")
            logger.warning("You may need to commit manually before starting sessions")
            return False

        # Create initial commit
        commit_message = """chore: Initialize project with Session-Driven Development

Project initialized with SDD framework including:
- Project structure and configuration files
- Quality gates and testing setup
- Session tracking infrastructure
- Documentation templates

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"""

        result = runner.run(["git", "commit", "-m", commit_message], check=True)
        if not result.success:
            logger.warning(f"Git commit failed: {result.stderr}")
            logger.warning("You may need to commit manually before starting sessions")
            return False

        logger.info("Created initial commit on main branch")
        return True

    except Exception as e:
        logger.warning(f"Failed to create initial commit: {e}")
        logger.warning("You may need to commit manually before starting sessions")
        return False


def init_project() -> int:
    """
    LEGACY: Basic initialization function without templates.

    This function is deprecated in favor of template-based initialization.
    Use `sdd init --template=<template> --tier=<tier> --coverage=<coverage>` instead.

    Returns:
        0 on success, 1 if already initialized, or raises exception on critical errors.

    Raises:
        DirectoryNotEmptyError: If .session directory already exists.
        GitError: If git operations fail critically.
        FileOperationError: If file operations fail critically.
        ValidationError: If configuration or validation fails.

    Note:
        Some non-critical failures (like dependency installation) are logged as warnings
        and don't stop the initialization process. The user can fix these manually.
        All output is now through logger instead of print().
    """
    logger.warning("⚠️  Using legacy initialization mode")
    logger.warning("⚠️  Consider using template-based init for better experience")
    logger.warning("")
    logger.info("🚀 Initializing Session-Driven Development...\n")

    # 1. Check if already initialized
    if Path(".session").exists():
        raise DirectoryNotEmptyError(".session")

    # 2. Check or initialize git repository
    check_or_init_git()

    # 3. Install git hooks
    install_git_hooks()
    logger.info("")

    # 4. Detect project type
    project_type = detect_project_type()
    logger.info(f"\n📦 Project type: {project_type}\n")

    # 5. Ensure package manager file (create/update)
    ensure_package_manager_file(project_type)

    # 6. Ensure all config files (create from templates)
    logger.info("")
    ensure_config_files(project_type)

    # 7. Install dependencies
    logger.info("")
    install_dependencies(project_type)

    # 8. Create smoke tests
    logger.info("")
    create_smoke_tests(project_type)

    # 9. Create .session structure
    create_session_structure()

    # 10. Initialize tracking files
    initialize_tracking_files()

    # 11. Generate project context (stack/tree)
    run_initial_scans()

    # 12. Update .gitignore
    logger.info("")
    ensure_gitignore_entries()

    # 13. Create initial commit
    logger.info("")
    create_initial_commit()

    # Success summary
    logger.info("\n" + "=" * 60)
    logger.info("✅ SDD Initialized Successfully!")
    logger.info("=" * 60)

    logger.info("\n📦 What was created/updated:")
    logger.info("  ✓ Git repository initialized with initial commit")
    logger.info("  ✓ Git hooks (prepare-commit-msg with CHANGELOG/LEARNING reminders)")
    logger.info("  ✓ Config files (.eslintrc, .prettierrc, jest.config, etc.)")
    logger.info("  ✓ Dependencies installed")
    logger.info("  ✓ Smoke tests created")
    logger.info("  ✓ .session/ structure with tracking files")
    logger.info("  ✓ Project context (stack.txt, tree.txt)")
    logger.info("  ✓ .gitignore updated")

    logger.info("\n🚀 Next Step:")
    logger.info("  /sdd:work-new")
    logger.info("")

    return 0


# ============================================================================
# NEW TEMPLATE-BASED INIT (PRIMARY ENTRY POINT)
# ============================================================================


def main() -> int:
    """
    Main entry point for init command with template-based initialization.

    Handles CLI argument parsing and routes to appropriate init function:
    - With arguments (--template, --tier, etc.): Template-based init
    - Without arguments (legacy): Basic init (deprecated)

    Returns:
        0 on success, non-zero on failure
    """
    import argparse

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
        help="Test coverage target percentage (e.g., 60, 80, 90)",
    )
    parser.add_argument(
        "--options",
        help="Comma-separated list of additional options (ci_cd,docker,pre_commit,env_templates)",
    )

    args = parser.parse_args()

    # Check if template-based init is requested
    if args.template:
        # Template-based initialization (new flow)
        from sdd.init.orchestrator import run_template_based_init

        # Validate required arguments
        if not args.tier:
            logger.error("--tier is required when using --template")
            return 1
        if not args.coverage:
            logger.error("--coverage is required when using --template")
            return 1

        # Parse additional options
        additional_options = []
        if args.options:
            additional_options = [opt.strip() for opt in args.options.split(",")]

        # Run template-based init
        return run_template_based_init(
            template_id=args.template,
            tier=args.tier,
            coverage_target=args.coverage,
            additional_options=additional_options,
        )
    else:
        # Legacy init (basic initialization without templates)
        # The deprecation warning is shown in init_project() itself
        return init_project()


if __name__ == "__main__":
    exit(main())
