"""
Solokit Init Module

This module contains deterministic scripts for template-based project initialization.
Each script handles a specific phase of the initialization process.

Module Organization:
- git_setup.py: Git initialization and verification
- environment_validator.py: Environment validation with auto-update (pyenv, nvm)
- template_installer.py: Template file copying and installation
- readme_generator.py: README.md generation
- config_generator.py: Config file generation (.eslintrc, .prettierrc, etc.)
- dependency_installer.py: Dependency installation (npm/pip)
- docs_structure.py: Documentation directory creation
- code_generator.py: Minimal code generation
- test_generator.py: Smoke test generation
- env_generator.py: Environment file generation (.env.example)
- session_structure.py: Session structure initialization
- initial_scans.py: Initial scans (stack.txt, tree.txt)
- git_hooks.py: Git hooks installation
- gitignore_updater.py: .gitignore updates
- initial_commit.py: Initial commit creation
"""

__all__ = [
    "git_setup",
    "environment_validator",
    "template_installer",
    "readme_generator",
    "config_generator",
    "dependency_installer",
    "docs_structure",
    "code_generator",
    "test_generator",
    "env_generator",
    "session_structure",
    "initial_scans",
    "git_hooks",
    "gitignore_updater",
    "initial_commit",
]
