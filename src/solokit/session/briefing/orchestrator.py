#!/usr/bin/env python3
"""
Session briefing orchestrator.
Coordinates all briefing components to generate comprehensive session briefings.
"""

from __future__ import annotations

from pathlib import Path

from solokit.core.exceptions import GitError, SystemError
from solokit.core.logging_config import get_logger

from .documentation_loader import DocumentationLoader
from .formatter import BriefingFormatter
from .git_context import GitContext
from .learning_loader import LearningLoader
from .milestone_builder import MilestoneBuilder
from .stack_detector import StackDetector
from .tree_generator import TreeGenerator
from .work_item_loader import WorkItemLoader

logger = get_logger(__name__)


class SessionBriefing:
    """Orchestrate generation of comprehensive session briefings."""

    def __init__(
        self,
        session_dir: Path | None = None,
        project_root: Path | None = None,
    ):
        """Initialize session briefing orchestrator.

        Args:
            session_dir: Path to .session directory (defaults to .session)
            project_root: Path to project root (defaults to current directory)
        """
        self.session_dir = session_dir or Path(".session")
        self.project_root = project_root or Path.cwd()

        # Initialize all component modules
        self.work_item_loader = WorkItemLoader(session_dir=self.session_dir)
        self.learning_loader = LearningLoader(session_dir=self.session_dir)
        self.doc_loader = DocumentationLoader(project_root=self.project_root)
        self.stack_detector = StackDetector(session_dir=self.session_dir)
        self.tree_generator = TreeGenerator(session_dir=self.session_dir)
        self.git_context = GitContext()
        self.milestone_builder = MilestoneBuilder(session_dir=self.session_dir)
        self.formatter = BriefingFormatter()

    def generate_briefing(self, item_id: str, item: dict, learnings_data: dict) -> str:
        """Generate comprehensive markdown briefing with full project context.

        Args:
            item_id: Work item identifier
            item: Work item dictionary
            learnings_data: Full learnings data structure

        Returns:
            Complete briefing as markdown string
        """
        # Load all context using specialized modules
        project_docs = self.doc_loader.load_project_docs()
        current_stack = self.stack_detector.load_current_stack()
        current_tree = self.tree_generator.load_current_tree()
        work_item_spec = self.work_item_loader.load_work_item_spec(item)
        env_checks = self.formatter.validate_environment()

        # Check git status - gracefully handle errors as this is informational
        try:
            git_status = self.git_context.check_git_status()
        except (GitError, SystemError) as e:
            logger.warning(f"Failed to check git status: {e.message}")
            git_status = {"clean": False, "status": f"Error: {e.message}", "branch": None}

        # Validate spec completeness
        spec_validation_warning = self._validate_spec(item_id, item["type"])

        # Get milestone context
        milestone_context = self.milestone_builder.load_milestone_context(item)

        # Get relevant learnings
        relevant_learnings = self.learning_loader.get_relevant_learnings(
            learnings_data, item, work_item_spec
        )

        # Generate briefing using formatter
        return self.formatter.generate_briefing(
            item_id=item_id,
            item=item,
            project_docs=project_docs,
            current_stack=current_stack,
            current_tree=current_tree,
            work_item_spec=work_item_spec,
            env_checks=env_checks,
            git_status=git_status,
            spec_validation_warning=spec_validation_warning,
            milestone_context=milestone_context,
            relevant_learnings=relevant_learnings,
        )

    def _validate_spec(self, item_id: str, work_item_type: str) -> str | None:
        """Validate spec completeness and return warning if incomplete.

        Args:
            item_id: Work item identifier
            work_item_type: Type of work item

        Returns:
            Validation warning string or None if valid
        """
        try:
            from solokit.core.exceptions import FileNotFoundError as SolokitFileNotFoundError
            from solokit.core.exceptions import SpecValidationError
            from solokit.work_items.spec_validator import (
                format_validation_report,
                validate_spec_file,
            )

            try:
                validate_spec_file(item_id, work_item_type)
                # If no exception, spec is valid
                return None
            except SpecValidationError as e:
                # Spec has validation errors
                return format_validation_report(item_id, work_item_type, e)
            except (SolokitFileNotFoundError, Exception):
                # Spec file doesn't exist or other error - this is not critical for briefing
                # Just return None and let the briefing proceed
                return None
        except ImportError:
            # Gracefully handle if spec_validator not available
            logger.debug("Spec validator not available")

        return None
