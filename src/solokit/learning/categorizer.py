"""Learning categorization module"""

from __future__ import annotations

from typing import Any

from solokit.core.logging_config import get_logger

logger = get_logger(__name__)


class LearningCategorizer:
    """Handles automatic categorization of learnings based on content analysis"""

    # Keyword sets for each category
    ARCHITECTURE_KEYWORDS = [
        "architecture",
        "design",
        "pattern",
        "structure",
        "component",
        "module",
        "layer",
        "service",
    ]

    GOTCHA_KEYWORDS = [
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

    PRACTICE_KEYWORDS = [
        "best practice",
        "convention",
        "standard",
        "guideline",
        "recommendation",
        "should",
        "always",
        "never",
    ]

    DEBT_KEYWORDS = [
        "technical debt",
        "refactor",
        "cleanup",
        "legacy",
        "deprecated",
        "workaround",
        "hack",
        "todo",
    ]

    PERFORMANCE_KEYWORDS = [
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

    def categorize_learning(self, learning: dict[str, Any]) -> str:
        """
        Automatically categorize a single learning based on content analysis

        Args:
            learning: Learning dict with 'content' field

        Returns:
            Category name string
        """
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

        # Score each category based on keywords
        scores = {
            "architecture_patterns": self._keyword_score(content, self.ARCHITECTURE_KEYWORDS),
            "gotchas": self._keyword_score(content, self.GOTCHA_KEYWORDS),
            "best_practices": self._keyword_score(content, self.PRACTICE_KEYWORDS),
            "technical_debt": self._keyword_score(content, self.DEBT_KEYWORDS),
            "performance_insights": self._keyword_score(content, self.PERFORMANCE_KEYWORDS),
        }

        # Return category with highest score, default to best_practices
        max_category = max(scores.items(), key=lambda x: x[1])
        return max_category[0] if max_category[1] > 0 else "best_practices"

    def _keyword_score(self, text: str, keywords: list[str]) -> int:
        """
        Calculate keyword match score for text

        Args:
            text: Text to analyze (should be lowercased)
            keywords: List of keywords to search for

        Returns:
            Number of keyword matches found
        """
        score = 0
        for keyword in keywords:
            if keyword in text:
                score += 1
        return score
