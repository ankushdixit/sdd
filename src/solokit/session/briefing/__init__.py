#!/usr/bin/env python3
"""
Session briefing package.

This package provides modular components for generating comprehensive session briefings.
The package is organized into focused, single-responsibility modules.

Public API exports maintain backward compatibility with the original briefing.py module.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from solokit.core.logging_config import get_logger

from .documentation_loader import DocumentationLoader
from .formatter import BriefingFormatter
from .git_context import GitContext
from .learning_loader import LearningLoader
from .milestone_builder import MilestoneBuilder
from .orchestrator import SessionBriefing
from .stack_detector import StackDetector
from .tree_generator import TreeGenerator
from .work_item_loader import WorkItemLoader

# Package-level logger for backward compatibility
logger = get_logger(__name__)

# Get the parent module (solokit.session)
_parent_module_path = Path(__file__).parent.parent
if str(_parent_module_path) not in sys.path:
    sys.path.insert(0, str(_parent_module_path))


# Import main from the briefing.py module (not package)
# This is a bit tricky since briefing is now a package, but main() is in briefing.py
# We need to import the actual module file, not the package
def _get_briefing_module() -> Any:
    """Get the briefing module (not package) for accessing main() and _cli_main()."""
    # Import the briefing module file (not the package) using importlib
    import importlib.util
    import sys
    from pathlib import Path

    # Get the path to briefing.py (the module file, not the package)
    module_path = Path(__file__).parent.parent / "briefing.py"

    # Load the module directly from the file
    spec = importlib.util.spec_from_file_location("solokit.session._briefing_module", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load briefing module from {module_path}")
    briefing_module = importlib.util.module_from_spec(spec)
    sys.modules["solokit.session._briefing_module"] = briefing_module
    spec.loader.exec_module(briefing_module)

    return briefing_module


def main() -> int:
    """Main entry point - delegates to briefing.py main()."""
    briefing_module = _get_briefing_module()
    # Call the main function from the loaded module
    return briefing_module.main()  # type: ignore[no-any-return]


def _cli_main() -> int:
    """CLI wrapper for main() - delegates to briefing.py _cli_main()."""
    briefing_module = _get_briefing_module()
    # Call the _cli_main function from the loaded module
    return briefing_module._cli_main()  # type: ignore[no-any-return]


# Export commonly used functions for backward compatibility
# These maintain the original module-level function API

__all__ = [
    # Classes
    "SessionBriefing",
    "WorkItemLoader",
    "LearningLoader",
    "DocumentationLoader",
    "StackDetector",
    "TreeGenerator",
    "GitContext",
    "MilestoneBuilder",
    "BriefingFormatter",
    # Functions (for backward compatibility with old code that imports functions)
    "load_work_items",
    "load_learnings",
    "get_next_work_item",
    "get_relevant_learnings",
    "load_milestone_context",
    "load_project_docs",
    "load_current_stack",
    "load_current_tree",
    "load_work_item_spec",
    "shift_heading_levels",
    "extract_section",
    "generate_previous_work_section",
    "extract_keywords",
    "calculate_days_ago",
    "validate_environment",
    "check_git_status",
    "generate_briefing",
    "check_command_exists",
    "generate_integration_test_briefing",
    "generate_deployment_briefing",
    "determine_git_branch_final_status",
    "finalize_previous_work_item_git_status",
    "main",  # Add main to exports
    "_cli_main",  # Add _cli_main to exports (for testing)
]


# Backward compatibility: Module-level function wrappers


def load_work_items() -> dict[str, Any]:
    """Load work items from tracking file (backward compatibility wrapper)."""
    from pathlib import Path

    work_items_file = Path(".session/tracking/work_items.json")
    logger.debug("Loading work items from: %s", work_items_file)

    loader = WorkItemLoader()
    return loader.load_work_items()


def load_learnings() -> dict[str, Any]:
    """Load learnings from tracking file (backward compatibility wrapper)."""
    loader = LearningLoader()
    return loader.load_learnings()


def get_next_work_item(work_items_data: dict) -> tuple[str | None, dict | None]:
    """Find next available work item (backward compatibility wrapper)."""
    loader = WorkItemLoader()
    return loader.get_next_work_item(work_items_data)


def get_relevant_learnings(
    learnings_data: dict, work_item: dict, spec_content: str = ""
) -> list[dict]:
    """Get relevant learnings (backward compatibility wrapper)."""
    loader = LearningLoader()
    return loader.get_relevant_learnings(learnings_data, work_item, spec_content)


def load_milestone_context(work_item: dict) -> dict | None:
    """Load milestone context (backward compatibility wrapper)."""
    builder = MilestoneBuilder()
    return builder.load_milestone_context(work_item)


def load_project_docs() -> dict[str, str]:
    """Load project documentation (backward compatibility wrapper)."""
    loader = DocumentationLoader()
    return loader.load_project_docs()


def load_current_stack() -> str:
    """Load current technology stack (backward compatibility wrapper)."""
    detector = StackDetector()
    return detector.load_current_stack()


def load_current_tree() -> str:
    """Load current project structure (backward compatibility wrapper)."""
    generator = TreeGenerator()
    return generator.load_current_tree()


def load_work_item_spec(work_item: str | dict[str, Any]) -> str:
    """Load work item specification file (backward compatibility wrapper)."""
    loader = WorkItemLoader()
    return loader.load_work_item_spec(work_item)


def shift_heading_levels(markdown_content: str, shift: int) -> str:
    """Shift markdown heading levels (backward compatibility wrapper)."""
    formatter = BriefingFormatter()
    return formatter.shift_heading_levels(markdown_content, shift)


def extract_section(markdown: str, heading: str) -> str:
    """Extract section from markdown (backward compatibility wrapper)."""
    formatter = BriefingFormatter()
    return formatter.extract_section(markdown, heading)


def generate_previous_work_section(item_id: str, item: dict) -> str:
    """Generate previous work context (backward compatibility wrapper)."""
    formatter = BriefingFormatter()
    return formatter.generate_previous_work_section(item_id, item)


def extract_keywords(text: str) -> set[str]:
    """Extract meaningful keywords from text (backward compatibility wrapper)."""
    loader = LearningLoader()
    return loader._extract_keywords(text)


def calculate_days_ago(timestamp: str) -> int:
    """Calculate days since timestamp (backward compatibility wrapper)."""
    loader = LearningLoader()
    return loader._calculate_days_ago(timestamp)


def validate_environment() -> list[str]:
    """Validate development environment (backward compatibility wrapper)."""
    formatter = BriefingFormatter()
    return formatter.validate_environment()


def check_git_status() -> dict[str, Any]:
    """Check git status for session start (backward compatibility wrapper)."""
    context = GitContext()
    return context.check_git_status()


def generate_briefing(item_id: str, item: dict, learnings_data: dict) -> str:
    """Generate comprehensive markdown briefing (backward compatibility wrapper)."""
    briefing = SessionBriefing()
    return briefing.generate_briefing(item_id, item, learnings_data)


def check_command_exists(command: str) -> bool:
    """Check if a command is available (backward compatibility wrapper)."""
    formatter = BriefingFormatter()
    return formatter.check_command_exists(command)


def generate_integration_test_briefing(work_item: dict) -> str:
    """Generate integration test briefing (backward compatibility wrapper)."""
    formatter = BriefingFormatter()
    return formatter.generate_integration_test_briefing(work_item)


def generate_deployment_briefing(work_item: dict) -> str:
    """Generate deployment briefing (backward compatibility wrapper)."""
    formatter = BriefingFormatter()
    return formatter.generate_deployment_briefing(work_item)


def determine_git_branch_final_status(branch_name: str, git_info: dict) -> str:
    """Determine final git branch status (backward compatibility wrapper)."""
    context = GitContext()
    return context.determine_git_branch_final_status(branch_name, git_info)


def finalize_previous_work_item_git_status(
    work_items_data: dict, current_work_item_id: str
) -> str | None:
    """Finalize git status for previous work item (backward compatibility wrapper)."""
    context = GitContext()
    return context.finalize_previous_work_item_git_status(work_items_data, current_work_item_id)
