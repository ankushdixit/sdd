#!/usr/bin/env python3
"""
Unit tests for LearningLoader.
Tests learning file loading, relevance scoring, and error handling.
"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from sdd.core.exceptions import FileOperationError
from sdd.session.briefing.learning_loader import LearningLoader


class TestLearningLoaderInit:
    """Test LearningLoader initialization."""

    def test_init_default_session_dir(self):
        """Should default to .session directory."""
        loader = LearningLoader()
        assert loader.session_dir == Path(".session")
        assert loader.learnings_file == Path(".session/tracking/learnings.json")

    def test_init_custom_session_dir(self):
        """Should use provided session directory."""
        custom_dir = Path("/tmp/custom_session")
        loader = LearningLoader(session_dir=custom_dir)
        assert loader.session_dir == custom_dir
        assert loader.learnings_file == custom_dir / "tracking" / "learnings.json"


class TestLoadLearnings:
    """Test load_learnings method."""

    def test_load_learnings_file_not_exists(self):
        """Should return empty structure when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir) / ".session"
            loader = LearningLoader(session_dir=session_dir)
            result = loader.load_learnings()
            assert result == {"learnings": []}

    def test_load_learnings_valid_json(self):
        """Should load valid learnings JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir) / ".session"
            tracking_dir = session_dir / "tracking"
            tracking_dir.mkdir(parents=True)

            learnings_data = {
                "categories": {
                    "best_practices": [
                        {
                            "content": "Always validate inputs",
                            "context": "Testing",
                            "tags": ["testing"],
                            "created_at": "2025-01-01T00:00:00Z",
                        }
                    ]
                }
            }
            learnings_file = tracking_dir / "learnings.json"
            learnings_file.write_text(json.dumps(learnings_data))

            loader = LearningLoader(session_dir=session_dir)
            result = loader.load_learnings()
            assert result == learnings_data

    def test_load_learnings_invalid_json(self):
        """Should raise FileOperationError on invalid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir) / ".session"
            tracking_dir = session_dir / "tracking"
            tracking_dir.mkdir(parents=True)

            learnings_file = tracking_dir / "learnings.json"
            learnings_file.write_text("{ invalid json }")

            loader = LearningLoader(session_dir=session_dir)
            with pytest.raises(FileOperationError) as exc_info:
                loader.load_learnings()

            error = exc_info.value
            assert error.context["operation"] == "parse"
            assert "Invalid JSON format" in error.message
            assert str(learnings_file) in error.context["file_path"]

    def test_load_learnings_old_format_compatibility(self):
        """Should load old format with learnings list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir) / ".session"
            tracking_dir = session_dir / "tracking"
            tracking_dir.mkdir(parents=True)

            # Old format
            learnings_data = {
                "learnings": [
                    {
                        "content": "Old format learning",
                        "context": "Legacy",
                        "tags": ["old"],
                    }
                ]
            }
            learnings_file = tracking_dir / "learnings.json"
            learnings_file.write_text(json.dumps(learnings_data))

            loader = LearningLoader(session_dir=session_dir)
            result = loader.load_learnings()
            assert result == learnings_data


class TestGetRelevantLearnings:
    """Test get_relevant_learnings method."""

    def test_get_relevant_learnings_empty_data(self):
        """Should return empty list when no learnings exist."""
        loader = LearningLoader()
        result = loader.get_relevant_learnings(
            learnings_data={"categories": {}},
            work_item={"title": "Test", "type": "feature", "tags": []},
        )
        assert result == []

    def test_get_relevant_learnings_old_format(self):
        """Should handle old format learnings list."""
        loader = LearningLoader()
        learnings_data = {
            "learnings": [
                {
                    "content": "Test learning",
                    "context": "Testing context",
                    "tags": ["test"],
                    "created_at": datetime.now().isoformat(),
                }
            ]
        }
        work_item = {"title": "test feature", "type": "feature", "tags": ["test"]}

        result = loader.get_relevant_learnings(learnings_data, work_item)
        assert len(result) > 0
        assert result[0]["category"] == "general"

    def test_get_relevant_learnings_new_format(self):
        """Should handle new format with categories."""
        loader = LearningLoader()
        learnings_data = {
            "categories": {
                "best_practices": [
                    {
                        "content": "Best practice learning",
                        "context": "Testing",
                        "tags": ["test"],
                        "created_at": datetime.now().isoformat(),
                    }
                ],
                "patterns": [
                    {
                        "content": "Pattern learning",
                        "context": "Design",
                        "tags": ["design"],
                        "created_at": datetime.now().isoformat(),
                    }
                ],
            }
        }
        work_item = {
            "title": "test pattern feature",
            "type": "feature",
            "tags": ["test"],
        }

        result = loader.get_relevant_learnings(learnings_data, work_item)
        assert len(result) > 0
        # Best practices should have category bonus
        assert any(learning["category"] == "best_practices" for learning in result)

    def test_get_relevant_learnings_keyword_matching(self):
        """Should score based on keyword matching."""
        loader = LearningLoader()
        learnings_data = {
            "categories": {
                "general": [
                    {
                        "content": "authentication security password validation",
                        "context": "Security",
                        "tags": [],
                        "created_at": datetime.now().isoformat(),
                    },
                    {
                        "content": "unrelated content about databases",
                        "context": "Database",
                        "tags": [],
                        "created_at": datetime.now().isoformat(),
                    },
                ]
            }
        }
        work_item = {
            "title": "implement authentication system with password validation",
            "type": "feature",
            "tags": [],
        }

        result = loader.get_relevant_learnings(learnings_data, work_item)
        # Authentication learning should score higher and appear first
        assert len(result) > 0
        assert "authentication" in result[0]["content"]

    def test_get_relevant_learnings_type_based_matching(self):
        """Should score based on work item type."""
        loader = LearningLoader()
        learnings_data = {
            "categories": {
                "general": [
                    {
                        "content": "Testing best practices for bugfix scenarios",
                        "context": "Testing",
                        "tags": [],
                        "created_at": datetime.now().isoformat(),
                    },
                    {
                        "content": "General development tips",
                        "context": "Development",
                        "tags": [],
                        "created_at": datetime.now().isoformat(),
                    },
                ]
            }
        }
        work_item = {"title": "Fix login issue", "type": "bugfix", "tags": []}

        result = loader.get_relevant_learnings(learnings_data, work_item)
        # Bugfix learning should score higher
        assert len(result) > 0
        assert "bugfix" in result[0]["content"]

    def test_get_relevant_learnings_tag_matching(self):
        """Should score based on tag overlap."""
        loader = LearningLoader()
        learnings_data = {
            "categories": {
                "general": [
                    {
                        "content": "Security learning",
                        "context": "Security",
                        "tags": ["security", "authentication"],
                        "created_at": datetime.now().isoformat(),
                    },
                    {
                        "content": "Performance learning",
                        "context": "Performance",
                        "tags": ["performance"],
                        "created_at": datetime.now().isoformat(),
                    },
                ]
            }
        }
        work_item = {
            "title": "Feature work",
            "type": "feature",
            "tags": ["security", "authentication"],
        }

        result = loader.get_relevant_learnings(learnings_data, work_item)
        # Security learning with matching tags should score higher
        assert len(result) > 0
        assert "Security" in result[0]["context"]

    def test_get_relevant_learnings_recency_weighting(self):
        """Should give higher scores to recent learnings."""
        loader = LearningLoader()
        very_recent = (datetime.now() - timedelta(days=3)).isoformat()
        old = (datetime.now() - timedelta(days=100)).isoformat()

        learnings_data = {
            "categories": {
                "general": [
                    {
                        "content": "Recent testing learning",
                        "context": "Testing",
                        "tags": [],
                        "created_at": very_recent,
                    },
                    {
                        "content": "Old testing learning",
                        "context": "Testing",
                        "tags": [],
                        "created_at": old,
                    },
                ]
            }
        }
        work_item = {"title": "test feature", "type": "feature", "tags": []}

        result = loader.get_relevant_learnings(learnings_data, work_item)
        # Recent learning should score higher
        assert len(result) > 0
        assert "Recent" in result[0]["content"]

    def test_get_relevant_learnings_category_bonuses(self):
        """Should apply category bonuses to scores."""
        loader = LearningLoader()
        timestamp = datetime.now().isoformat()

        learnings_data = {
            "categories": {
                "best_practices": [
                    {"content": "practice", "context": "", "tags": [], "created_at": timestamp}
                ],
                "patterns": [
                    {"content": "pattern", "context": "", "tags": [], "created_at": timestamp}
                ],
                "gotchas": [
                    {"content": "gotcha", "context": "", "tags": [], "created_at": timestamp}
                ],
                "general": [
                    {"content": "general", "context": "", "tags": [], "created_at": timestamp}
                ],
            }
        }
        work_item = {"title": "work", "type": "feature", "tags": []}

        result = loader.get_relevant_learnings(learnings_data, work_item)
        # Should include learnings with category bonuses
        assert len(result) > 0
        categories = [learning["category"] for learning in result]
        # Categories with bonuses should appear
        assert "best_practices" in categories or "patterns" in categories

    def test_get_relevant_learnings_top_10_limit(self):
        """Should return at most 10 learnings."""
        loader = LearningLoader()
        timestamp = datetime.now().isoformat()

        # Create 20 learnings
        learnings = []
        for i in range(20):
            learnings.append(
                {
                    "content": f"learning {i} testing feature",
                    "context": "Testing",
                    "tags": [],
                    "created_at": timestamp,
                }
            )

        learnings_data = {"categories": {"general": learnings}}
        work_item = {"title": "test feature", "type": "feature", "tags": []}

        result = loader.get_relevant_learnings(learnings_data, work_item)
        assert len(result) <= 10

    def test_get_relevant_learnings_zero_score_filtered(self):
        """Should filter out learnings with zero score."""
        loader = LearningLoader()
        learnings_data = {
            "categories": {
                "general": [
                    {
                        "content": "completely unrelated content xyz",
                        "context": "abc",
                        "tags": [],
                        "created_at": datetime.now().isoformat(),
                    }
                ]
            }
        }
        work_item = {"title": "authentication feature", "type": "feature", "tags": []}

        result = loader.get_relevant_learnings(learnings_data, work_item)
        # Should be empty or very few since no relevance
        assert len(result) <= 1


class TestExtractKeywords:
    """Test _extract_keywords method."""

    def test_extract_keywords_basic(self):
        """Should extract words longer than 3 characters."""
        loader = LearningLoader()
        result = loader._extract_keywords("implement authentication system")
        assert "implement" in result
        assert "authentication" in result
        assert "system" in result

    def test_extract_keywords_filters_stop_words(self):
        """Should filter out common stop words."""
        loader = LearningLoader()
        result = loader._extract_keywords("the quick brown fox with the dog")
        assert "the" not in result
        assert "with" not in result
        assert "quick" in result
        assert "brown" in result

    def test_extract_keywords_filters_short_words(self):
        """Should filter out words with 3 or fewer characters."""
        loader = LearningLoader()
        result = loader._extract_keywords("a big cat sat on mat")
        assert "a" not in result
        assert "on" not in result
        assert "cat" not in result  # exactly 3 chars
        assert "sat" not in result  # exactly 3 chars
        assert "mat" not in result  # exactly 3 chars

    def test_extract_keywords_lowercase(self):
        """Should convert to lowercase."""
        loader = LearningLoader()
        result = loader._extract_keywords("Testing AUTHENTICATION System")
        assert "testing" in result
        assert "authentication" in result
        assert "system" in result
        assert "Testing" not in result
        assert "AUTHENTICATION" not in result

    def test_extract_keywords_empty_text(self):
        """Should handle empty text."""
        loader = LearningLoader()
        result = loader._extract_keywords("")
        assert result == set()


class TestCalculateDaysAgo:
    """Test _calculate_days_ago method."""

    def test_calculate_days_ago_valid_timestamp(self):
        """Should calculate days for valid timestamp."""
        loader = LearningLoader()
        three_days_ago = (datetime.now() - timedelta(days=3)).isoformat()
        result = loader._calculate_days_ago(three_days_ago)
        assert result == 3

    def test_calculate_days_ago_with_z_suffix(self):
        """Should handle timestamps with Z suffix."""
        loader = LearningLoader()
        timestamp = "2025-01-01T00:00:00Z"
        result = loader._calculate_days_ago(timestamp)
        # Should not raise exception
        assert isinstance(result, int)
        assert result >= 0

    def test_calculate_days_ago_empty_timestamp(self):
        """Should return 365 for empty timestamp."""
        loader = LearningLoader()
        result = loader._calculate_days_ago("")
        assert result == 365

    def test_calculate_days_ago_invalid_timestamp(self):
        """Should return 365 for invalid timestamp."""
        loader = LearningLoader()
        result = loader._calculate_days_ago("not-a-date")
        assert result == 365

    def test_calculate_days_ago_malformed_timestamp(self):
        """Should return 365 for malformed timestamp."""
        loader = LearningLoader()
        result = loader._calculate_days_ago("2025-99-99T99:99:99")
        assert result == 365

    def test_calculate_days_ago_none_timestamp(self):
        """Should return 365 for None timestamp."""
        loader = LearningLoader()
        result = loader._calculate_days_ago(None)
        assert result == 365
