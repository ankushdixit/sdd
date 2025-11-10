"""Learning extraction module for various sources"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from solokit.core.command_runner import CommandRunner
from solokit.core.constants import GIT_STANDARD_TIMEOUT
from solokit.core.error_handlers import log_errors
from solokit.core.exceptions import FileOperationError
from solokit.core.file_ops import load_json
from solokit.core.logging_config import get_logger

logger = get_logger(__name__)


class LearningExtractor:
    """Extracts learnings from various sources (sessions, git commits, code comments)"""

    def __init__(self, session_dir: Path, project_root: Path | None = None):
        """
        Initialize learning extractor

        Args:
            session_dir: Path to .session directory
            project_root: Path to project root (for git operations)
        """
        self.session_dir = session_dir
        self.project_root = project_root or Path.cwd()
        self.runner = CommandRunner(
            default_timeout=GIT_STANDARD_TIMEOUT, working_dir=self.project_root
        )

    def extract_from_sessions(self) -> list[dict[str, Any]]:
        """
        Extract learnings from session summary JSON files

        Returns:
            List of learning dictionaries
        """
        learnings: list[dict[str, Any]] = []
        summaries_dir = self.session_dir / "summaries"

        if not summaries_dir.exists():
            return learnings

        # Look for session summary files
        for summary_file in summaries_dir.glob("session_*.json"):
            try:
                summary_data = load_json(summary_file)

                # Extract learnings from various fields
                session_id = summary_file.stem.replace("session_", "")

                # Check for explicit learnings field
                if "learnings" in summary_data:
                    for learning_text in summary_data["learnings"]:
                        learnings.append(
                            {
                                "content": learning_text,
                                "learned_in": session_id,
                                "timestamp": summary_data.get("timestamp", ""),
                            }
                        )

                # Extract from challenges as potential gotchas
                if "challenges_encountered" in summary_data:
                    for challenge in summary_data["challenges_encountered"]:
                        learnings.append(
                            {
                                "content": f"Challenge: {challenge}",
                                "learned_in": session_id,
                                "timestamp": summary_data.get("timestamp", ""),
                                "suggested_type": "gotcha",
                            }
                        )

            except (ValueError, KeyError, FileOperationError) as e:
                # Skip invalid summary files
                logger.warning(f"Failed to extract learnings from {summary_file}: {e}")
                continue

        logger.info(f"Extracted {len(learnings)} learnings from session summaries")
        return learnings

    @log_errors()
    def extract_from_session_summary(
        self, session_file: Path, validator: Any = None
    ) -> list[dict[str, Any]]:
        """
        Extract learnings from a session summary markdown file

        Args:
            session_file: Path to session summary markdown file
            validator: Optional validator instance with create_learning_entry and validate_learning methods

        Returns:
            List of learning dictionaries extracted from the file
        """
        if not session_file.exists():
            return []

        try:
            with open(session_file) as f:
                content = f.read()
        except (OSError, Exception) as e:
            logger.warning(f"Failed to read session summary {session_file}: {e}")
            return []

        learnings = []

        # Extract session number from filename (e.g., session_005_summary.md)
        session_match = re.search(r"session_(\d+)", session_file.name)
        session_num = int(session_match.group(1)) if session_match else 0

        # Look for "Challenges Encountered" or "Learnings Captured" sections
        patterns = [
            r"##\s*Challenges?\s*Encountered\s*\n(.*?)(?=\n##|\Z)",
            r"##\s*Learnings?\s*Captured\s*\n(.*?)(?=\n##|\Z)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                # Each bullet point is a potential learning
                for line in match.split("\n"):
                    line = line.strip()
                    if line.startswith("-") or line.startswith("*"):
                        learning_text = line.lstrip("-*").strip()
                        # Basic validation
                        if learning_text and self._is_valid_content(learning_text):
                            if validator:
                                # Use validator for standardized entry creation
                                entry = validator.create_learning_entry(
                                    content=learning_text,
                                    source="session_summary",
                                    session_id=f"session_{session_num:03d}",
                                    context=f"Session summary file: {session_file.name}",
                                )
                                if validator.validate_learning(entry):
                                    learnings.append(entry)
                            else:
                                # Simple entry without validation
                                learnings.append(
                                    {
                                        "content": learning_text,
                                        "learned_in": f"session_{session_num:03d}",
                                        "source": "session_summary",
                                        "context": f"Session summary file: {session_file.name}",
                                    }
                                )

        logger.info(f"Extracted {len(learnings)} learnings from {session_file.name}")
        return learnings

    @log_errors()
    def extract_from_git_commits(
        self, since_session: int = 0, session_id: str | None = None, validator: Any = None
    ) -> list[dict[str, Any]]:
        """
        Extract learnings from git commit messages with LEARNING: annotations

        Args:
            since_session: Extract only commits after this session number
            session_id: Session ID to tag learnings with
            validator: Optional validator instance

        Returns:
            List of learning dictionaries extracted from commit messages
        """
        try:
            # Get recent commits
            result = self.runner.run(["git", "log", "--format=%H|||%B", "-n", "100"])

            if not result.success:
                return []

            learnings = []
            # Updated regex to capture multi-line LEARNING statements
            # Captures until: double newline (blank line) OR end of string
            learning_pattern = r"LEARNING:\s*([\s\S]+?)(?=\n\n|\Z)"

            # Parse commit messages
            commits_raw = result.stdout.strip()
            if not commits_raw:
                return []

            # Each commit starts with hash|||, split on newline followed by hash pattern
            commit_blocks = re.split(r"\n(?=[a-f0-9]{40}\|\|\|)", commits_raw)

            for commit_block in commit_blocks:
                if "|||" not in commit_block:
                    continue

                commit_hash, message = commit_block.split("|||", 1)

                # Find LEARNING: annotations
                for match in re.finditer(learning_pattern, message, re.MULTILINE):
                    learning_text = match.group(1).strip()
                    # Basic validation
                    if learning_text and self._is_valid_content(learning_text):
                        if validator:
                            # Use validator for standardized entry creation
                            entry = validator.create_learning_entry(
                                content=learning_text,
                                source="git_commit",
                                session_id=session_id,
                                context=f"Commit {commit_hash[:8]}",
                            )
                            if validator.validate_learning(entry):
                                learnings.append(entry)
                        else:
                            # Simple entry without validation
                            learnings.append(
                                {
                                    "content": learning_text,
                                    "learned_in": session_id or "unknown",
                                    "source": "git_commit",
                                    "context": f"Commit {commit_hash[:8]}",
                                }
                            )

            logger.info(f"Extracted {len(learnings)} learnings from git commits")
            return learnings

        except Exception as e:
            logger.warning(f"Failed to extract learnings from git commits: {e}")
            return []

    @log_errors()
    def extract_from_code_comments(
        self,
        changed_files: list[Path] | None = None,
        session_id: str | None = None,
        validator: Any = None,
    ) -> list[dict[str, Any]]:
        """
        Extract learnings from inline code comments (not documentation)

        Args:
            changed_files: List of file paths to scan (or None to auto-detect from git)
            session_id: Session ID to tag learnings with
            validator: Optional validator instance

        Returns:
            List of learning dictionaries extracted from code comments
        """
        if changed_files is None:
            # Get recently changed files from git
            try:
                result = self.runner.run(["git", "diff", "--name-only", "HEAD~5", "HEAD"])

                if result.success:
                    changed_files = [
                        self.project_root / f.strip()
                        for f in result.stdout.split("\n")
                        if f.strip()
                    ]
                else:
                    changed_files = []
            except Exception as e:
                logger.warning(f"Failed to get changed files from git: {e}")
                changed_files = []

        learnings = []
        # Pattern must match actual comment lines (starting with #), not string literals
        learning_pattern = r"^\s*#\s*LEARNING:\s*(.+?)$"

        # Only scan actual code files, not documentation
        code_extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs"}
        doc_extensions = {".md", ".txt", ".rst"}
        excluded_dirs = {"examples", "templates", "tests", "test", "__tests__", "spec"}

        for file_path in changed_files:
            if not file_path.exists() or not file_path.is_file():
                continue

            # Skip documentation files
            if file_path.suffix in doc_extensions:
                continue

            # Skip example/template/test directories
            if any(excluded_dir in file_path.parts for excluded_dir in excluded_dirs):
                continue

            # Only process code files
            if file_path.suffix not in code_extensions:
                continue

            # Skip binary files and large files
            if file_path.stat().st_size > 1_000_000:
                continue

            try:
                with open(file_path, encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        match = re.search(learning_pattern, line)
                        if match:
                            learning_text = match.group(1).strip()
                            # Basic validation
                            if learning_text and self._is_valid_content(learning_text):
                                if validator:
                                    # Use validator for standardized entry creation
                                    entry = validator.create_learning_entry(
                                        content=learning_text,
                                        source="inline_comment",
                                        session_id=session_id,
                                        context=f"{file_path.name}:{line_num}",
                                    )
                                    if validator.validate_learning(entry):
                                        learnings.append(entry)
                                else:
                                    # Simple entry without validation
                                    learnings.append(
                                        {
                                            "content": learning_text,
                                            "learned_in": session_id or "unknown",
                                            "source": "inline_comment",
                                            "context": f"{file_path.name}:{line_num}",
                                        }
                                    )
            except (OSError, UnicodeDecodeError) as e:
                logger.warning(f"Failed to read file {file_path}: {e}")
                continue

        logger.info(f"Extracted {len(learnings)} learnings from code comments")
        return learnings

    def _is_valid_content(self, content: str) -> bool:
        """
        Basic validation for learning content

        Args:
            content: Content to validate

        Returns:
            True if content appears valid
        """
        if not content or not isinstance(content, str):
            return False

        # Skip placeholders and examples
        if "<" in content or ">" in content:
            return False

        # Must have substance (more than just a few words)
        if len(content.split()) < 5:
            return False

        return True
