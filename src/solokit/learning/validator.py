"""Learning validation module"""

from __future__ import annotations

import hashlib
from datetime import datetime

import jsonschema

from solokit.core.logging_config import get_logger

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


class LearningValidator:
    """Validates learning entries and creates standardized learning objects"""

    def is_valid_learning(self, content: str) -> bool:
        """
        Check if extracted content is a valid learning (not placeholder/garbage)

        Args:
            content: Content string to validate

        Returns:
            True if content appears to be a valid learning
        """
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
    ) -> dict[str, str]:
        """
        Create a standardized learning entry with all required fields

        Ensures consistent metadata structure across all extraction methods.
        All entries will have both 'learned_in' and 'context' fields.

        Args:
            content: Learning content text
            source: Source of the learning (git_commit, session_summary, etc.)
            session_id: Optional session ID
            context: Optional context string
            timestamp: Optional timestamp (ISO format)
            learning_id: Optional learning ID

        Returns:
            Standardized learning dictionary
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
        """
        Validate learning entry against JSON schema

        Args:
            learning: Learning dictionary to validate

        Returns:
            True if valid, False otherwise (logs warnings for invalid entries)
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
