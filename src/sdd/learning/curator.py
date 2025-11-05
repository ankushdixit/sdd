#!/usr/bin/env python3
"""
Learning curation script

Curates and organizes accumulated learnings:
1. Loads raw learnings from session summaries
2. Categorizes learnings
3. Merges similar/duplicate learnings
4. Archives obsolete learnings
5. Generates learning summary reports
"""

from __future__ import annotations

import argparse
import hashlib
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import jsonschema

from sdd.core.command_runner import CommandRunner
from sdd.core.config import get_config_manager
from sdd.core.error_handlers import log_errors
from sdd.core.exceptions import (
    FileNotFoundError as SDDFileNotFoundError,
)
from sdd.core.exceptions import (
    FileOperationError,
    ValidationError,
)
from sdd.core.file_ops import load_json, save_json
from sdd.core.logging_config import get_logger

logger = get_logger(__name__)

# JSON Schema for learning entry validation
LEARNING_SCHEMA = {
    "type": "object",
    "required": ["content", "learned_in", "source", "context", "timestamp", "id"],
    "properties": {
        "content": {"type": "string", "minLength": 10},
        "learned_in": {"type": "string"},
        "source": {
            "type": "string",
            "enum": ["git_commit", "temp_file", "inline_comment", "session_summary"],
        },
        "context": {"type": "string"},
        "timestamp": {"type": "string"},
        "id": {"type": "string"},
    },
}


class LearningsCurator:
    """Curates project learnings"""

    def __init__(self, project_root: Path | None = None):
        """Initialize LearningsCurator with project root path."""
        if project_root is None:
            project_root = Path.cwd()
        self.project_root = project_root
        self.session_dir = project_root / ".session"
        self.learnings_path = self.session_dir / "tracking" / "learnings.json"

        # Use ConfigManager for centralized config management
        config_path = self.session_dir / "config.json"
        config_manager = get_config_manager()
        config_manager.load_config(config_path)
        self.config = config_manager.curation

        # Initialize CommandRunner
        self.runner = CommandRunner(default_timeout=10, working_dir=self.project_root)

    @log_errors()
    def curate(self, dry_run: bool = False) -> None:
        """Curate learnings

        Raises:
            FileOperationError: If reading/writing learnings file fails
            ValidationError: If learning data is invalid
        """
        logger.info("Starting learning curation (dry_run=%s)", dry_run)
        print("\n=== Learning Curation ===\n")

        # Load existing learnings
        learnings = self._load_learnings()

        # Statistics
        initial_count = self._count_all_learnings(learnings)
        logger.info("Initial learnings count: %d", initial_count)
        print(f"Initial learnings: {initial_count}\n")

        # Categorize uncategorized learnings
        categorized = self._categorize_learnings(learnings)
        logger.info("Categorized %d learnings", categorized)
        print(f"✓ Categorized {categorized} learnings")

        # Merge similar learnings
        merged = self._merge_similar_learnings(learnings)
        logger.info("Merged %d similar learnings", merged)
        print(f"✓ Merged {merged} duplicate learnings")

        # Archive old learnings
        archived = self._archive_old_learnings(learnings)
        print(f"✓ Archived {archived} old learnings")

        # Update metadata
        learnings["last_curated"] = datetime.now().isoformat()
        learnings["curator"] = "session_curator"

        # Update total_learnings counter
        self._update_total_learnings(learnings)

        final_count = self._count_all_learnings(learnings)

        print(f"\nFinal learnings: {final_count}\n")

        if not dry_run:
            save_json(self.learnings_path, learnings)
            print("✓ Learnings saved\n")
        else:
            print("Dry run - no changes saved\n")

    def _load_learnings(self) -> dict:
        """Load learnings file"""
        if self.learnings_path.exists():
            data = load_json(self.learnings_path)
            # Ensure metadata exists
            if "metadata" not in data:
                data["metadata"] = {
                    "total_learnings": self._count_all_learnings(data),
                    "last_curated": data.get("last_curated"),
                }
            return data
        else:
            # Create default structure
            return {
                "metadata": {
                    "total_learnings": 0,
                    "last_curated": None,
                },
                "last_curated": None,
                "curator": "session_curator",
                "categories": {
                    "architecture_patterns": [],
                    "gotchas": [],
                    "best_practices": [],
                    "technical_debt": [],
                    "performance_insights": [],
                },
                "archived": [],
            }

    def _count_all_learnings(self, learnings: dict) -> int:
        """Count all learnings"""
        count = 0
        categories = learnings.get("categories", {})

        for category in categories.values():
            count += len(category)

        count += len(learnings.get("archived", []))

        return count

    def _update_total_learnings(self, learnings: dict) -> None:
        """Update total_learnings metadata counter"""
        if "metadata" not in learnings:
            learnings["metadata"] = {}
        learnings["metadata"]["total_learnings"] = self._count_all_learnings(learnings)

    def _categorize_learnings(self, learnings: dict) -> int:
        """Categorize uncategorized learnings using AI-powered analysis"""
        categorized_count = 0

        # Extract learnings from session summaries
        new_learnings = self._extract_learnings_from_sessions()

        for learning in new_learnings:
            # Use AI-powered categorization (rule-based with keyword analysis)
            category = self._auto_categorize_learning(learning)

            # Add to appropriate category
            categories = learnings.setdefault("categories", {})
            if category not in categories:
                categories[category] = []

            # Check if already exists
            if not self._learning_exists(categories[category], learning):
                categories[category].append(learning)
                categorized_count += 1

        return categorized_count

    def _extract_learnings_from_sessions(self) -> list[dict]:
        """Extract learnings from session summary files"""
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

            except (FileOperationError, ValidationError, ValueError, KeyError) as e:
                # Skip invalid summary files
                logger.warning(f"Failed to extract learnings from {summary_file}: {e}")
                continue

        return learnings

    def _auto_categorize_learning(self, learning: dict) -> str:
        """Automatically categorize a learning using keyword analysis"""
        content = learning.get("content", "").lower()

        # Check for suggested type first
        if "suggested_type" in learning:
            suggested = learning["suggested_type"]
            if suggested in [
                "architecture_pattern",
                "gotcha",
                "best_practice",
                "technical_debt",
                "performance_insight",
            ]:
                return f"{suggested}s"  # Pluralize

        # Keyword-based categorization
        architecture_keywords = [
            "architecture",
            "design",
            "pattern",
            "structure",
            "component",
            "module",
            "layer",
            "service",
        ]
        gotcha_keywords = [
            "gotcha",
            "trap",
            "pitfall",
            "mistake",
            "error",
            "bug",
            "issue",
            "problem",
            "challenge",
            "warning",
        ]
        practice_keywords = [
            "best practice",
            "convention",
            "standard",
            "guideline",
            "recommendation",
            "should",
            "always",
            "never",
        ]
        debt_keywords = [
            "technical debt",
            "refactor",
            "cleanup",
            "legacy",
            "deprecated",
            "workaround",
            "hack",
            "todo",
        ]
        performance_keywords = [
            "performance",
            "optimization",
            "speed",
            "slow",
            "fast",
            "efficient",
            "memory",
            "cpu",
            "benchmark",
        ]

        # Score each category
        scores = {
            "architecture_patterns": self._keyword_score(content, architecture_keywords),
            "gotchas": self._keyword_score(content, gotcha_keywords),
            "best_practices": self._keyword_score(content, practice_keywords),
            "technical_debt": self._keyword_score(content, debt_keywords),
            "performance_insights": self._keyword_score(content, performance_keywords),
        }

        # Return category with highest score, default to best_practices
        max_category = max(scores.items(), key=lambda x: x[1])
        return max_category[0] if max_category[1] > 0 else "best_practices"

    def _keyword_score(self, text: str, keywords: list[str]) -> int:
        """Calculate keyword match score"""
        score = 0
        for keyword in keywords:
            if keyword in text:
                score += 1
        return score

    def _learning_exists(self, category_learnings: list, new_learning: dict) -> bool:
        """Check if a similar learning already exists"""
        for existing in category_learnings:
            if self._are_similar(existing, new_learning):
                return True
        return False

    def _merge_similar_learnings(self, learnings: dict) -> int:
        """Merge similar learnings"""
        merged_count = 0
        categories = learnings.get("categories", {})

        for category_name, category_learnings in categories.items():
            # Group by similarity (simple keyword matching for now)
            to_remove = []

            for i, learning_a in enumerate(category_learnings):
                if i in to_remove:
                    continue

                for j in range(i + 1, len(category_learnings)):
                    if j in to_remove:
                        continue

                    learning_b = category_learnings[j]

                    # Simple similarity check
                    if self._are_similar(learning_a, learning_b):
                        # Merge into first learning
                        self._merge_learning(learning_a, learning_b)
                        to_remove.append(j)
                        merged_count += 1

            # Remove merged learnings
            for idx in sorted(to_remove, reverse=True):
                category_learnings.pop(idx)

        return merged_count

    def _are_similar(self, learning_a: dict, learning_b: dict) -> bool:
        """Check if two learnings are similar using enhanced semantic comparison"""
        content_a = learning_a.get("content", "").lower()
        content_b = learning_b.get("content", "").lower()

        # Exact match
        if content_a == content_b:
            return True

        # Remove common stopwords for better comparison
        stopwords = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "should",
            "could",
            "may",
            "might",
        }

        words_a = set(w for w in content_a.split() if w not in stopwords)
        words_b = set(w for w in content_b.split() if w not in stopwords)

        if len(words_a) == 0 or len(words_b) == 0:
            return False

        # Jaccard similarity (overlap coefficient)
        overlap = len(words_a & words_b)
        total = len(words_a | words_b)
        jaccard = overlap / total if total > 0 else 0

        # Containment similarity (one learning contains the other)
        min_size = min(len(words_a), len(words_b))
        containment = overlap / min_size if min_size > 0 else 0

        # Consider similar if high Jaccard OR high containment
        return jaccard > 0.6 or containment > 0.8

    def _merge_learning(self, target: dict, source: dict) -> None:
        """Merge source learning into target"""
        # Merge applies_to
        target_applies = set(target.get("applies_to", []))
        source_applies = set(source.get("applies_to", []))
        target["applies_to"] = list(target_applies | source_applies)

        # Add note about merge
        if "merged_from" not in target:
            target["merged_from"] = []
        target["merged_from"].append(source.get("learned_in", "unknown"))

    def _archive_old_learnings(self, learnings: dict, max_age_sessions: int = 50) -> int:
        """Archive old, unreferenced learnings"""
        archived_count = 0
        categories = learnings.get("categories", {})

        # Get current session number from tracking
        current_session = self._get_current_session_number()

        for category_name, category_learnings in categories.items():
            to_archive = []

            for i, learning in enumerate(category_learnings):
                # Extract session number from learned_in field
                session_num = self._extract_session_number(learning.get("learned_in", ""))

                # Archive if too old
                if (
                    session_num
                    and current_session > 0
                    and current_session - session_num > max_age_sessions
                ):
                    to_archive.append(i)

            # Move to archive
            archived = learnings.setdefault("archived", [])
            for idx in sorted(to_archive, reverse=True):
                learning = category_learnings.pop(idx)
                learning["archived_from"] = category_name
                learning["archived_at"] = datetime.now().isoformat()
                archived.append(learning)
                archived_count += 1

        return archived_count

    def _get_current_session_number(self) -> int:
        """Get the current session number from work items"""
        try:
            work_items_path = self.session_dir / "tracking" / "work_items.json"
            if work_items_path.exists():
                data = load_json(work_items_path)
                # Find max session number across all work items
                max_session = 0
                for item in data.get("work_items", {}).values():
                    sessions = item.get("sessions", [])
                    if sessions and isinstance(sessions, list):
                        max_session = max(max_session, max(sessions))
                return max_session
        except (FileOperationError, ValidationError, ValueError, KeyError, TypeError) as e:
            logger.warning(f"Failed to get current session number: {e}")
            return 0
        return 0

    def _extract_session_number(self, session_id: str) -> int:
        """Extract numeric session number from session ID"""
        try:
            # Handle formats like "session_001", "001", "1", etc.
            match = re.search(r"\d+", session_id)
            if match:
                return int(match.group())
        except (ValueError, AttributeError) as e:
            logger.debug(f"Failed to extract session number from '{session_id}': {e}")
            return 0
        return 0

    def auto_curate_if_needed(self) -> bool:
        """Auto-curate based on configuration and last curation time"""
        if not self.config.auto_curate:
            return False

        learnings = self._load_learnings()
        last_curated = learnings.get("last_curated")

        if not last_curated:
            # Never curated, do it now
            print("Auto-curating (first time)...\n")
            self.curate(dry_run=False)
            return True

        # Check frequency
        last_date = datetime.fromisoformat(last_curated)
        days_since = (datetime.now() - last_date).days

        frequency_days = self.config.frequency

        if days_since >= frequency_days:
            print(f"Auto-curating (last curated {days_since} days ago)...\n")
            self.curate(dry_run=False)
            return True

        return False

    @log_errors()
    def extract_from_session_summary(self, session_file: Path) -> list[dict]:
        """Extract learnings from session summary file

        Args:
            session_file: Path to session summary markdown file

        Returns:
            List of learning dictionaries extracted from the file

        Raises:
            FileOperationError: If file cannot be read
            ValidationError: If learning data is invalid
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
                        # Validate learning content before adding
                        if learning_text and self.is_valid_learning(learning_text):
                            # Use standardized entry creator for consistent metadata
                            entry = self.create_learning_entry(
                                content=learning_text,
                                source="session_summary",
                                session_id=f"session_{session_num:03d}",
                                context=f"Session summary file: {session_file.name}",
                            )
                            # Validate schema before adding
                            if self.validate_learning(entry):
                                learnings.append(entry)

        return learnings

    @log_errors()
    def extract_from_git_commits(
        self, since_session: int = 0, session_id: str | None = None
    ) -> list[dict]:
        """Extract learnings from git commit messages with standardized metadata

        Args:
            since_session: Extract only commits after this session number
            session_id: Session ID to tag learnings with

        Returns:
            List of learning dictionaries extracted from commit messages

        Raises:
            FileOperationError: If git command fails
            ValidationError: If learning data is invalid
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
            # Split by commit hash pattern (40-char hex at line start followed by |||)
            # This preserves multi-paragraph commit messages
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
                    # Validate learning content before adding
                    if learning_text and self.is_valid_learning(learning_text):
                        # Use standardized entry creator for consistent metadata
                        entry = self.create_learning_entry(
                            content=learning_text,
                            source="git_commit",
                            session_id=session_id,
                            context=f"Commit {commit_hash[:8]}",
                        )
                        # Validate schema before adding
                        if self.validate_learning(entry):
                            learnings.append(entry)

            return learnings

        except (FileOperationError, ValidationError) as e:
            logger.warning(f"Failed to extract learnings from git commits: {e}")
            return []

    @log_errors()
    def extract_from_code_comments(
        self, changed_files: list[Path] | None = None, session_id: str | None = None
    ) -> list[dict]:
        """Extract learnings from inline code comments (not documentation) with standardized metadata

        Args:
            changed_files: List of file paths to scan (or None to auto-detect from git)
            session_id: Session ID to tag learnings with

        Returns:
            List of learning dictionaries extracted from code comments

        Raises:
            FileOperationError: If file reading fails
            ValidationError: If learning data is invalid
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
            except (FileOperationError, ValidationError) as e:
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
                            # Validate learning content before adding
                            if learning_text and self.is_valid_learning(learning_text):
                                # Use standardized entry creator for consistent metadata
                                entry = self.create_learning_entry(
                                    content=learning_text,
                                    source="inline_comment",
                                    session_id=session_id,
                                    context=f"{file_path.name}:{line_num}",
                                )
                                # Validate schema before adding
                                if self.validate_learning(entry):
                                    learnings.append(entry)
            except (OSError, UnicodeDecodeError) as e:
                logger.warning(f"Failed to read file {file_path}: {e}")
                continue

        return learnings

    def is_valid_learning(self, content: str) -> bool:
        """Check if extracted content is a valid learning (not placeholder/garbage)."""
        if not content or not isinstance(content, str):
            return False

        # Skip placeholders and examples (content with angle brackets)
        if "<" in content or ">" in content:
            return False

        # Skip content with code syntax artifacts (from string literals or code fragments)
        code_artifacts = ['")', '\\"', "\\n", "`", "')", "');", '");', "`,"]
        if any(artifact in content for artifact in code_artifacts):
            return False

        # Skip if content ends with code syntax patterns
        content_stripped = content.strip()
        if content_stripped.endswith(('")', '";', "`,", "')", "';", "`)", "`,")):
            return False

        # Skip list fragments from commit messages (newline followed by list marker)
        if "\n- " in content or "\n* " in content or "\n• " in content:
            return False

        # Skip known placeholder text
        content_lower = content.lower().strip()
        placeholders = ["your learning here", "example learning", "todo", "tbd", "placeholder"]
        if content_lower in placeholders:
            return False

        # Must have substance (more than just a few words)
        if len(content.split()) < 5:
            return False

        return True

    def create_learning_entry(
        self,
        content: str,
        source: str,
        session_id: str | None = None,
        context: str | None = None,
        timestamp: str | None = None,
        learning_id: str | None = None,
    ) -> dict:
        """Create a standardized learning entry with all required fields.

        Ensures consistent metadata structure across all extraction methods.
        All entries will have both 'learned_in' and 'context' fields.
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        if learning_id is None:
            # MD5 used only for ID generation, not security
            learning_id = hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()[:8]

        # Both learned_in and context are required for consistency
        if session_id is None:
            session_id = "unknown"
        if context is None:
            context = "No context provided"

        return {
            "content": content,
            "learned_in": session_id,
            "source": source,
            "context": context,
            "timestamp": timestamp,
            "id": learning_id,
        }

    def validate_learning(self, learning: dict) -> bool:
        """Validate learning entry against JSON schema.

        Returns True if valid, False otherwise.
        Logs warnings for invalid entries.
        """
        try:
            jsonschema.validate(learning, LEARNING_SCHEMA)
            return True
        except jsonschema.ValidationError as e:
            logger.warning(f"Invalid learning entry: {e.message}")
            logger.debug(f"Invalid learning data: {learning}")
            return False
        except (TypeError, KeyError) as e:
            logger.warning(f"Invalid learning structure: {e}")
            return False

    def add_learning_if_new(self, learning_dict: dict) -> bool:
        """Add learning if it doesn't already exist (based on similarity)"""
        learnings = self._load_learnings()
        categories = learnings.get("categories", {})

        # Check against all existing learnings
        for category_learnings in categories.values():
            for existing in category_learnings:
                if self._are_similar(existing, learning_dict):
                    return False  # Skip, already exists

        # Auto-categorize if needed
        category = learning_dict.get("category")
        if not category:
            category = self._auto_categorize_learning(learning_dict)

        # Add to category
        if category not in categories:
            categories[category] = []

        # Generate ID if missing
        if "id" not in learning_dict:
            learning_dict["id"] = str(uuid.uuid4())[:8]

        categories[category].append(learning_dict)

        # Update total_learnings counter
        self._update_total_learnings(learnings)

        # Save
        save_json(self.learnings_path, learnings)

        return True  # Successfully added

    def generate_report(self) -> None:
        """Generate learning summary report"""
        print("\n=== Learning Summary Report ===\n")

        learnings = self._load_learnings()

        # Create table
        print("Learnings by Category:")
        print("-" * 40)

        categories = learnings.get("categories", {})
        total = 0

        for category_name, category_learnings in categories.items():
            count = len(category_learnings)
            total += count
            formatted_name = category_name.replace("_", " ").title()
            print(f"{formatted_name:<30} {count:>5}")

        # Add archived
        archived_count = len(learnings.get("archived", []))
        if archived_count > 0:
            print(f"{'Archived':<30} {archived_count:>5}")

        # Add total
        print("-" * 40)
        print(f"{'Total':<30} {total:>5}")
        print()

        # Show last curated
        last_curated = learnings.get("last_curated")
        if last_curated:
            print(f"Last curated: {last_curated}\n")
        else:
            print("Never curated\n")

    @log_errors()
    def add_learning(
        self,
        content: str,
        category: str,
        session: int | None = None,
        tags: list | None = None,
        context: str | None = None,
    ) -> str:
        """Add a new learning

        Args:
            content: Learning content text
            category: Category to add learning to
            session: Optional session number
            tags: Optional list of tags
            context: Optional context string

        Returns:
            Learning ID of the created learning

        Raises:
            FileOperationError: If saving learnings fails
            ValidationError: If learning data is invalid
        """
        learnings = self._load_learnings()

        # Generate unique ID
        learning_id = str(uuid.uuid4())[:8]

        # Create learning object
        learning: dict[str, Any] = {
            "id": learning_id,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "learned_in": f"session_{session:03d}" if session else "unknown",
        }

        if tags:
            learning["tags"] = tags if isinstance(tags, list) else [tags]

        if context:
            learning["context"] = context

        # Add to category
        categories = learnings.setdefault("categories", {})
        if category not in categories:
            categories[category] = []

        categories[category].append(learning)

        # Update total_learnings counter
        self._update_total_learnings(learnings)

        # Save
        save_json(self.learnings_path, learnings)

        print("\n✓ Learning captured!")
        print(f"  ID: {learning_id}")
        print(f"  Category: {category}")
        if tags:
            print(f"  Tags: {', '.join(learning['tags'])}")
        print("\nIt will be auto-categorized and curated.\n")

        return learning_id

    def search_learnings(self, query: str) -> None:
        """Search learnings by keyword"""
        learnings = self._load_learnings()
        categories = learnings.get("categories", {})

        query_lower = query.lower()
        matches = []

        # Search through all learnings
        for category_name, category_learnings in categories.items():
            for learning in category_learnings:
                # Search in content
                content = learning.get("content", "").lower()
                tags = learning.get("tags", [])
                context = learning.get("context", "").lower()

                if (
                    query_lower in content
                    or query_lower in context
                    or any(query_lower in tag.lower() for tag in tags)
                ):
                    matches.append({**learning, "category": category_name})

        # Display results
        if not matches:
            print(f"\nNo learnings found matching '{query}'\n")
            return

        print(f"\n=== Search Results for '{query}' ===\n")
        print(f"Found {len(matches)} matching learning(s):\n")

        for i, learning in enumerate(matches, 1):
            print(f"{i}. [{learning['category'].replace('_', ' ').title()}]")
            print(f"   {learning['content']}")

            if "tags" in learning:
                print(f"   Tags: {', '.join(learning['tags'])}")

            print(f"   Session: {learning.get('learned_in', 'unknown')}")
            print(f"   ID: {learning.get('id', 'N/A')}")
            print()

    def show_learnings(
        self,
        category: str | None = None,
        tag: str | None = None,
        session: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        include_archived: bool = False,
    ) -> None:
        """Show learnings with optional filters"""
        learnings = self._load_learnings()
        categories = learnings.get("categories", {})

        # Apply filters
        filtered = []
        for category_name, category_learnings in categories.items():
            # Category filter
            if category and category_name != category:
                continue

            for learning in category_learnings:
                # Tag filter
                if tag and tag not in learning.get("tags", []):
                    continue

                # Session filter
                if session:
                    learned_in = learning.get("learned_in", "")
                    session_num = self._extract_session_number(learned_in)
                    if session_num != session:
                        continue

                # Date range filter
                if date_from or date_to:
                    learning_date = learning.get("timestamp", "")
                    if date_from and learning_date < date_from:
                        continue
                    if date_to and learning_date > date_to:
                        continue

                filtered.append({**learning, "category": category_name})

        # Display results
        if not filtered:
            print("\nNo learnings found matching the filters\n")
            return

        if category:
            # Show specific category
            print(f"\n{category.replace('_', ' ').title()}\n")
            print("=" * 50)

            for i, learning in enumerate(filtered, 1):
                print(f"\n{i}. {learning.get('content', 'N/A')}")
                if "tags" in learning:
                    print(f"   Tags: {', '.join(learning['tags'])}")
                if "learned_in" in learning:
                    print(f"   Learned in: {learning['learned_in']}")
                if "timestamp" in learning:
                    print(f"   Date: {learning['timestamp']}")
                print(f"   ID: {learning.get('id', 'N/A')}")
        else:
            # Show all categories
            grouped: dict[str, list[Any]] = {}
            for learning in filtered:
                cat = learning["category"]
                if cat not in grouped:
                    grouped[cat] = []
                grouped[cat].append(learning)

            for category_name, category_learnings in grouped.items():
                print(f"\n{category_name.replace('_', ' ').title()}")
                print(f"Count: {len(category_learnings)}\n")

                # Show first 3
                for learning in category_learnings[:3]:
                    print(f"  • {learning.get('content', 'N/A')}")
                    if "tags" in learning:
                        print(f"    Tags: {', '.join(learning['tags'])}")

                if len(category_learnings) > 3:
                    print(f"  ... and {len(category_learnings) - 3} more")

                print()

    def get_related_learnings(self, learning_id: str, limit: int = 5) -> list[dict]:
        """Get similar learnings using similarity algorithms"""
        learnings = self._load_learnings()
        categories = learnings.get("categories", {})

        # Find target learning
        target = None
        for category_learnings in categories.values():
            for learning in category_learnings:
                if learning.get("id") == learning_id:
                    target = learning
                    break
            if target:
                break

        if not target:
            return []

        # Calculate similarity scores
        similarities = []
        for category_name, category_learnings in categories.items():
            for learning in category_learnings:
                if learning.get("id") == learning_id:
                    continue

                # Use existing similarity algorithm
                if self._are_similar(target, learning):
                    # Calculate a simple similarity score (0-100)
                    # Based on word overlap
                    target_words = set(target.get("content", "").lower().split())
                    learning_words = set(learning.get("content", "").lower().split())
                    overlap = len(target_words & learning_words)
                    total = len(target_words | learning_words)
                    score = int(overlap / total * 100) if total > 0 else 0

                    similarities.append((score, {**learning, "category": category_name}))

        # Sort by score and return top N
        similarities.sort(reverse=True, key=lambda x: x[0])
        return [learning for _, learning in similarities[:limit]]

    def generate_statistics(self) -> dict:
        """Generate learning statistics"""
        learnings = self._load_learnings()
        categories = learnings.get("categories", {})

        stats: dict[str, Any] = {
            "total": 0,
            "by_category": {},
            "by_tag": {},
            "top_tags": [],
            "by_session": {},
        }

        # Count by category
        for cat, items in categories.items():
            count = len(items)
            stats["by_category"][cat] = count
            stats["total"] += count

        # Count by tag and session
        tag_counts: dict[str, int] = {}
        session_counts: dict[int, int] = {}

        for items in categories.values():
            for learning in items:
                # Tag counts
                for tag in learning.get("tags", []):
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

                # Session counts
                learned_in = learning.get("learned_in", "unknown")
                session_num = self._extract_session_number(learned_in)
                if session_num > 0:
                    session_counts[session_num] = session_counts.get(session_num, 0) + 1

        # Top tags
        stats["top_tags"] = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        stats["by_tag"] = tag_counts
        stats["by_session"] = session_counts

        return stats

    def show_statistics(self) -> None:
        """Display learning statistics"""
        stats = self.generate_statistics()

        print("\n=== Learning Statistics ===\n")

        # Total
        print(f"Total learnings: {stats['total']}\n")

        # By category
        print("By Category:")
        print("-" * 40)
        for cat, count in stats["by_category"].items():
            cat_name = cat.replace("_", " ").title()
            print(f"  {cat_name:<30} {count:>5}")

        # Top tags
        if stats["top_tags"]:
            print("\nTop Tags:")
            print("-" * 40)
            for tag, count in stats["top_tags"]:
                print(f"  {tag:<30} {count:>5}")

        # Sessions with most learnings
        if stats["by_session"]:
            top_sessions = sorted(stats["by_session"].items(), key=lambda x: x[1], reverse=True)[:5]
            print("\nSessions with Most Learnings:")
            print("-" * 40)
            for session_num, count in top_sessions:
                print(f"  Session {session_num:<22} {count:>5}")

        print()

    def show_timeline(self, sessions: int = 10) -> None:
        """Show learning timeline for recent sessions"""
        learnings = self._load_learnings()
        categories = learnings.get("categories", {})

        # Group by session
        by_session: dict[int, list[Any]] = {}
        for items in categories.values():
            for learning in items:
                learned_in = learning.get("learned_in", "unknown")
                session = self._extract_session_number(learned_in)
                if session > 0:
                    if session not in by_session:
                        by_session[session] = []
                    by_session[session].append(learning)

        if not by_session:
            print("\nNo session timeline available\n")
            return

        # Display recent sessions
        recent = sorted(by_session.keys(), reverse=True)[:sessions]

        print(f"\n=== Learning Timeline (Last {min(len(recent), sessions)} Sessions) ===\n")

        for session in recent:
            session_learnings = by_session[session]
            count = len(session_learnings)

            print(f"Session {session:03d}: {count} learning(s)")

            # Show first 3 learnings
            for learning in session_learnings[:3]:
                content = learning.get("content", "")
                # Truncate long learnings
                if len(content) > 60:
                    content = content[:57] + "..."
                print(f"  - {content}")

            if len(session_learnings) > 3:
                print(f"  ... and {len(session_learnings) - 3} more")

            print()


def main() -> None:
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Learning curation and management")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Curate command
    curate_parser = subparsers.add_parser("curate", help="Run curation process")
    curate_parser.add_argument("--dry-run", action="store_true", help="Show changes without saving")

    # Show learnings command
    show_parser = subparsers.add_parser("show-learnings", help="Show learnings")
    show_parser.add_argument("--category", type=str, help="Filter by category")
    show_parser.add_argument("--tag", type=str, help="Filter by tag")
    show_parser.add_argument("--session", type=int, help="Filter by session number")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search learnings")
    search_parser.add_argument("query", type=str, help="Search query")

    # Add learning command
    add_parser = subparsers.add_parser("add-learning", help="Add a new learning")
    add_parser.add_argument("--content", type=str, required=True, help="Learning content")
    add_parser.add_argument(
        "--category",
        type=str,
        required=True,
        choices=[
            "architecture_patterns",
            "gotchas",
            "best_practices",
            "technical_debt",
            "performance_insights",
            "security",
        ],
        help="Learning category",
    )
    add_parser.add_argument("--session", type=int, help="Session number")
    add_parser.add_argument("--tags", type=str, help="Comma-separated tags")
    add_parser.add_argument("--context", type=str, help="Additional context")

    # Report command (legacy)
    subparsers.add_parser("report", help="Generate summary report")

    # Statistics command
    subparsers.add_parser("statistics", help="Show learning statistics")

    # Timeline command
    timeline_parser = subparsers.add_parser("timeline", help="Show learning timeline")
    timeline_parser.add_argument(
        "--sessions", type=int, default=10, help="Number of recent sessions to show"
    )

    args = parser.parse_args()

    project_root = Path.cwd()
    session_dir = project_root / ".session"

    if not session_dir.exists():
        raise SDDFileNotFoundError(file_path=str(session_dir), file_type="session directory")

    curator = LearningsCurator(project_root)

    if args.command == "curate":
        curator.curate(dry_run=args.dry_run)
    elif args.command == "show-learnings":
        curator.show_learnings(category=args.category, tag=args.tag, session=args.session)
    elif args.command == "search":
        curator.search_learnings(args.query)
    elif args.command == "add-learning":
        tags = args.tags.split(",") if args.tags else None
        curator.add_learning(
            content=args.content,
            category=args.category,
            session=args.session,
            tags=tags,
            context=args.context,
        )
    elif args.command == "report":
        curator.generate_report()
    elif args.command == "statistics":
        curator.show_statistics()
    elif args.command == "timeline":
        curator.show_timeline(sessions=args.sessions)
    else:
        # Default to report if no command specified
        curator.generate_report()


if __name__ == "__main__":
    main()
