#!/usr/bin/env python3
"""
Deterministic SDD initialization - transforms any project into working SDD project.
Philosophy: Don't check and warn - CREATE and FIX.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path


def check_or_init_git(project_root: Path = None) -> bool:
    """Check if git is initialized, if not initialize it."""
    if project_root is None:
        project_root = Path.cwd()

    git_dir = project_root / ".git"

    if git_dir.exists():
        print("✓ Git repository already initialized")
        return True

    try:
        # Initialize git
        subprocess.run(
            ["git", "init"],
            cwd=project_root,
            check=True,
            capture_output=True,
        )
        print("✓ Initialized git repository")

        # Set default branch to main (modern convention)
        subprocess.run(
            ["git", "branch", "-m", "main"],
            cwd=project_root,
            check=True,
            capture_output=True,
        )
        print("✓ Set default branch to 'main'")

        return True
    except Exception as e:
        print(f"⚠️  Failed to initialize git: {e}")
        print("   You may need to run 'git init' manually")
        return False


def install_git_hooks(project_root: Path = None) -> bool:
    """Install git hooks from templates."""
    if project_root is None:
        project_root = Path.cwd()

    git_hooks_dir = project_root / ".git" / "hooks"

    # Check if .git/hooks exists
    if not git_hooks_dir.exists():
        print("⚠️  .git/hooks directory not found - git may not be initialized")
        return False

    # Get template directory
    template_dir = Path(__file__).parent.parent / "templates" / "git-hooks"

    # Install prepare-commit-msg hook
    hook_template = template_dir / "prepare-commit-msg"
    hook_dest = git_hooks_dir / "prepare-commit-msg"

    if hook_template.exists():
        try:
            shutil.copy(hook_template, hook_dest)
            # Make executable (chmod +x)
            import stat
            hook_dest.chmod(hook_dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            print("✓ Installed git prepare-commit-msg hook")
            return True
        except Exception as e:
            print(f"⚠️  Failed to install git hook: {e}")
            return False
    else:
        print(f"⚠️  Hook template not found: {hook_template}")
        return False


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
        print("\nNo project files detected. What type of project is this?")
        print("1. TypeScript")
        print("2. JavaScript")
        print("3. Python")

        if not sys.stdin.isatty():
            # Non-interactive mode - default to TypeScript
            print("Non-interactive mode: defaulting to TypeScript")
            return "typescript"

        choice = input("Enter choice (1-3): ").strip()
        return {"1": "typescript", "2": "javascript", "3": "python"}.get(choice, "typescript")


def ensure_package_manager_file(project_type: str):
    """Create or update package manager file with required dependencies."""
    template_dir = Path(__file__).parent.parent / "templates"

    if project_type in ["typescript", "javascript"]:
        package_json = Path("package.json")

        if not package_json.exists():
            print("Creating package.json...")
            # Get project name from directory
            project_name = Path.cwd().name
            project_desc = f"A {project_type} project with Session-Driven Development"

            # Load template and replace placeholders
            template_path = template_dir / "package.json.template"
            template_content = template_path.read_text()
            content = template_content.replace("{project_name}", project_name)
            content = content.replace("{project_description}", project_desc)

            package_json.write_text(content)
            print(f"✓ Created package.json for {project_name}")
        else:
            print("✓ Found package.json")
            # Ensure required scripts and devDependencies exist
            with open(package_json) as f:
                data = json.load(f)

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
                    print(f"  Added script: {script}")
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
                    print(f"  Added devDependency: {pkg}")
                    deps_modified = True

            # Save back only if modified
            if scripts_modified or deps_modified:
                with open(package_json, "w") as f:
                    json.dump(data, f, indent=2)
                if deps_modified:
                    print("  Run 'npm install' to install new dependencies")

    elif project_type == "python":
        pyproject = Path("pyproject.toml")

        if not pyproject.exists():
            print("Creating pyproject.toml...")
            project_name = Path.cwd().name.replace("-", "_")
            project_desc = "A Python project with Session-Driven Development"

            template_path = template_dir / "pyproject.toml.template"
            template_content = template_path.read_text()
            content = template_content.replace("{project_name}", project_name)
            content = template_content.replace("{project_description}", project_desc)

            pyproject.write_text(content)
            print(f"✓ Created pyproject.toml for {project_name}")
        else:
            print("✓ Found pyproject.toml")
            # Check if it has dev dependencies section
            content = pyproject.read_text()
            if "[project.optional-dependencies]" not in content and "dev" not in content:
                print(
                    "  Note: Add [project.optional-dependencies] section with pytest, pytest-cov, ruff"
                )
                print("  Or install manually: pip install pytest pytest-cov ruff")


def ensure_config_files(project_type: str):
    """Create all required config files from templates."""
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
                shutil.copy(template_path, dest_path)
                print(f"✓ Created {dest_name}")
        else:
            print(f"✓ Found {dest_name}")


def install_dependencies(project_type: str):
    """Install project dependencies."""
    if project_type in ["typescript", "javascript"]:
        # Always run npm install to ensure new devDependencies are installed
        print("\nInstalling npm dependencies...")
        try:
            subprocess.run(["npm", "install"], check=True)
            print("✓ Dependencies installed")
        except subprocess.CalledProcessError:
            print("⚠️  npm install failed - you may need to run it manually")

    elif project_type == "python":
        # Check if we're in a venv, if not create one
        if not (Path("venv").exists() or Path(".venv").exists()):
            print("\nCreating Python virtual environment...")
            try:
                subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
                print("✓ Created venv/")
                print(
                    "  Activate with: source venv/bin/activate (Unix) or venv\\Scripts\\activate (Windows)"
                )
            except subprocess.CalledProcessError:
                print("⚠️  venv creation failed")
                return

        # Try to install dev dependencies
        print("\nInstalling Python dependencies...")
        pip_cmd = "venv/bin/pip" if Path("venv").exists() else ".venv/bin/pip"
        if Path(pip_cmd).exists():
            try:
                subprocess.run([pip_cmd, "install", "-e", ".[dev]"], check=True)
                print("✓ Dependencies installed")
            except subprocess.CalledProcessError:
                print("⚠️  pip install failed - you may need to activate venv and install manually")
        else:
            print("⚠️  Please activate virtual environment and run: pip install -e .[dev]")


def create_smoke_tests(project_type: str):
    """Create initial smoke tests that validate SDD setup."""
    template_dir = Path(__file__).parent.parent / "templates" / "tests"
    test_dir = Path("tests")
    test_dir.mkdir(exist_ok=True)

    if project_type == "typescript":
        test_file = test_dir / "sdd-setup.test.ts"
        template_name = "sdd-setup.test.ts"
        if not test_file.exists():
            template_file = template_dir / template_name
            if template_file.exists():
                shutil.copy(template_file, test_file)
                print(f"✓ Created smoke tests: {test_file}")
        else:
            print(f"✓ Found {test_file}")

    elif project_type == "javascript":
        test_file = test_dir / "sdd-setup.test.js"
        template_name = "sdd-setup.test.js"
        if not test_file.exists():
            template_file = template_dir / template_name
            if template_file.exists():
                shutil.copy(template_file, test_file)
                print(f"✓ Created smoke tests: {test_file}")
        else:
            print(f"✓ Found {test_file}")

    elif project_type == "python":
        test_file = test_dir / "test_sdd_setup.py"
        if not test_file.exists():
            template_file = template_dir / "test_sdd_setup.py"
            if template_file.exists():
                shutil.copy(template_file, test_file)
                print(f"✓ Created smoke tests: {test_file}")
        else:
            print(f"✓ Found {test_file}")


def create_session_structure():
    """Create .session directory structure."""
    session_dir = Path(".session")

    print("\nCreating .session/ structure...")

    # Create directories
    (session_dir / "tracking").mkdir(parents=True)
    (session_dir / "briefings").mkdir(parents=True)
    (session_dir / "history").mkdir(parents=True)
    (session_dir / "specs").mkdir(parents=True)

    print("✓ Created .session/tracking/")
    print("✓ Created .session/briefings/")
    print("✓ Created .session/history/")
    print("✓ Created .session/specs/")


def initialize_tracking_files():
    """Initialize tracking files from templates."""
    session_dir = Path(".session")
    template_dir = Path(__file__).parent.parent / "templates"

    print("\nInitializing tracking files...")

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
            shutil.copy(src_path, dst_path)
            print(f"✓ Created {dst}")

    # Create empty files for stack and tree tracking
    (session_dir / "tracking" / "stack_updates.json").write_text(
        json.dumps({"updates": []}, indent=2)
    )
    print("✓ Created stack_updates.json")

    (session_dir / "tracking" / "tree_updates.json").write_text(
        json.dumps({"updates": []}, indent=2)
    )
    print("✓ Created tree_updates.json")

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
    (session_dir / "config.json").write_text(json.dumps(config_data, indent=2))
    print("✓ Created config.json")

    # Copy config schema file
    schema_source = Path(__file__).parent.parent / "templates" / "config.schema.json"
    schema_dest = session_dir / "config.schema.json"

    if schema_source.exists() and not schema_dest.exists():
        shutil.copy(schema_source, schema_dest)
        print("✓ Created config.schema.json")


def run_initial_scans():
    """Run initial stack and tree scans with FIXED path resolution (Bug #12)."""
    print("\nGenerating project context...")

    # Get SDD installation directory
    script_dir = Path(__file__).parent

    # Run generate_stack.py with absolute path
    try:
        subprocess.run(
            ["python", str(script_dir / "generate_stack.py")],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        print("✓ Generated stack.txt")
    except subprocess.CalledProcessError as e:
        print("⚠️  Could not generate stack.txt")
        if e.stderr:
            print(f"  Error: {e.stderr.strip()}")
    except subprocess.TimeoutExpired:
        print("⚠️  Stack generation timed out")

    # Run generate_tree.py with absolute path
    try:
        subprocess.run(
            ["python", str(script_dir / "generate_tree.py")],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        print("✓ Generated tree.txt")
    except subprocess.CalledProcessError as e:
        print("⚠️  Could not generate tree.txt")
        if e.stderr:
            print(f"  Error: {e.stderr.strip()}")
    except subprocess.TimeoutExpired:
        print("⚠️  Tree generation timed out")


def ensure_gitignore_entries():
    """Add .session patterns to .gitignore."""
    gitignore = Path(".gitignore")

    required_entries = [
        ".session/briefings/",
        ".session/history/",
        "coverage/",
        "node_modules/",
        "dist/",
        "venv/",
        ".venv/",
        "*.pyc",
        "__pycache__/",
    ]

    existing_content = gitignore.read_text() if gitignore.exists() else ""

    entries_to_add = []
    for entry in required_entries:
        if entry not in existing_content:
            entries_to_add.append(entry)

    if entries_to_add:
        print("\nUpdating .gitignore...")
        with open(gitignore, "a") as f:
            if existing_content and not existing_content.endswith("\n"):
                f.write("\n")
            f.write("\n# SDD-related patterns\n")
            for entry in entries_to_add:
                f.write(f"{entry}\n")
        print(f"✓ Added {len(entries_to_add)} entries to .gitignore")
    else:
        print("✓ .gitignore already up to date")


def init_project():
    """Main initialization function - deterministic setup."""
    print("🚀 Initializing Session-Driven Development...\n")

    # 1. Check if already initialized
    if Path(".session").exists():
        print("❌ Already initialized!")
        print("   .session/ directory already exists")
        print("   If you need to reinitialize, delete .session/ first")
        return 1

    # 2. Check or initialize git repository
    check_or_init_git()

    # 3. Install git hooks
    install_git_hooks()
    print()

    # 4. Detect project type
    project_type = detect_project_type()
    print(f"\n📦 Project type: {project_type}\n")

    # 5. Ensure package manager file (create/update)
    ensure_package_manager_file(project_type)

    # 6. Ensure all config files (create from templates)
    print()
    ensure_config_files(project_type)

    # 7. Install dependencies
    print()
    install_dependencies(project_type)

    # 8. Create smoke tests
    print()
    create_smoke_tests(project_type)

    # 9. Create .session structure
    create_session_structure()

    # 10. Initialize tracking files
    initialize_tracking_files()

    # 11. Generate project context (stack/tree)
    run_initial_scans()

    # 12. Update .gitignore
    print()
    ensure_gitignore_entries()

    # Success summary
    print("\n" + "=" * 60)
    print("✅ SDD Initialized Successfully!")
    print("=" * 60)

    print("\n📦 What was created/updated:")
    print("  ✓ Git hooks (prepare-commit-msg with CHANGELOG/LEARNING reminders)")
    print("  ✓ Config files (.eslintrc, .prettierrc, jest.config, etc.)")
    print("  ✓ Dependencies installed")
    print("  ✓ Smoke tests created")
    print("  ✓ .session/ structure with tracking files")
    print("  ✓ Project context (stack.txt, tree.txt)")
    print("  ✓ .gitignore updated")

    print("\n🚀 Next Step:")
    print("  /sdd:work-new")
    print()

    return 0


if __name__ == "__main__":
    exit(init_project())
