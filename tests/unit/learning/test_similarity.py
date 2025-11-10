"""Unit tests for learning similarity engine"""

from solokit.learning.similarity import (
    ENGLISH_STOPWORDS,
    JaccardContainmentSimilarity,
    LearningSimilarityEngine,
)


class TestJaccardContainmentSimilarity:
    """Test Jaccard + Containment similarity algorithm"""

    def test_exact_match_returns_one(self) -> None:
        """Test that identical texts return similarity of 1.0"""
        algo = JaccardContainmentSimilarity()
        text = "This is a test learning about Python"

        assert algo.compute_similarity(text, text) == 1.0

    def test_case_insensitive(self) -> None:
        """Test that similarity is case-insensitive"""
        algo = JaccardContainmentSimilarity()
        text1 = "Python is great"
        text2 = "PYTHON IS GREAT"

        assert algo.compute_similarity(text1, text2) == 1.0

    def test_stopwords_filtered(self) -> None:
        """Test that stopwords are filtered out"""
        algo = JaccardContainmentSimilarity()

        # These should be similar after removing stopwords
        text1 = "Python is a great language"
        text2 = "Python great language"

        score = algo.compute_similarity(text1, text2)
        assert score > 0.9  # Should be very similar after stopword removal

    def test_custom_stopwords(self) -> None:
        """Test using custom stopword set"""
        custom_stopwords = {"custom", "words"}
        algo = JaccardContainmentSimilarity(stopwords=custom_stopwords)

        text1 = "custom words test"
        text2 = "test"

        score = algo.compute_similarity(text1, text2)
        assert score == 1.0  # "custom" and "words" filtered out

    def test_empty_after_stopword_removal(self) -> None:
        """Test texts that become empty after stopword removal"""
        algo = JaccardContainmentSimilarity()

        text1 = "the a an"
        text2 = "is are was"

        score = algo.compute_similarity(text1, text2)
        assert score == 0.0

    def test_high_jaccard_similarity(self) -> None:
        """Test texts with high Jaccard similarity"""
        algo = JaccardContainmentSimilarity()

        text1 = "Python Django Flask frameworks"
        text2 = "Python Django frameworks"

        # Jaccard = 3/4 = 0.75 > 0.6 threshold
        assert algo.are_similar(text1, text2)

    def test_high_containment_similarity(self) -> None:
        """Test texts with high containment similarity"""
        algo = JaccardContainmentSimilarity()

        text1 = "Use dependency injection for better testability"
        text2 = "dependency injection testability"

        # Short text mostly contained in longer text
        assert algo.are_similar(text1, text2)

    def test_not_similar_different_content(self) -> None:
        """Test texts that are not similar"""
        algo = JaccardContainmentSimilarity()

        text1 = "Python programming language"
        text2 = "JavaScript frontend development"

        assert not algo.are_similar(text1, text2)

    def test_custom_thresholds(self) -> None:
        """Test custom similarity thresholds"""
        # Very strict thresholds that require near-perfect match
        algo = JaccardContainmentSimilarity(jaccard_threshold=0.95, containment_threshold=1.0)

        text1 = "Python Django Flask FastAPI"
        text2 = "Python Django"

        # Would be similar with default thresholds, not with very strict ones
        # Jaccard = 2/4 = 0.5, Containment = 2/2 = 1.0 (but we set containment threshold to 1.0 exactly)
        # Since one needs strict match, this should fail
        assert not algo.are_similar(text1, text2)

    def test_jaccard_similarity_calculation(self) -> None:
        """Test Jaccard similarity calculation directly"""
        algo = JaccardContainmentSimilarity()

        words_a = {"python", "django", "flask"}
        words_b = {"python", "django", "fastapi"}

        # Overlap: {python, django} = 2
        # Union: {python, django, flask, fastapi} = 4
        # Jaccard = 2/4 = 0.5
        score = algo._jaccard_similarity(words_a, words_b)
        assert score == 0.5

    def test_containment_similarity_calculation(self) -> None:
        """Test containment similarity calculation directly"""
        algo = JaccardContainmentSimilarity()

        words_a = {"python", "django"}
        words_b = {"python", "django", "flask", "fastapi"}

        # Overlap: {python, django} = 2
        # Min size: 2
        # Containment = 2/2 = 1.0
        score = algo._containment_similarity(words_a, words_b)
        assert score == 1.0


class TestLearningSimilarityEngine:
    """Test main similarity engine"""

    def test_initialization_default_algorithm(self) -> None:
        """Test engine initializes with default algorithm"""
        engine = LearningSimilarityEngine()
        assert isinstance(engine.algorithm, JaccardContainmentSimilarity)

    def test_initialization_custom_algorithm(self) -> None:
        """Test engine initializes with custom algorithm"""
        custom_algo = JaccardContainmentSimilarity(jaccard_threshold=0.7)
        engine = LearningSimilarityEngine(algorithm=custom_algo)
        assert engine.algorithm is custom_algo

    def test_are_similar_basic(self) -> None:
        """Test basic similarity check between learnings"""
        engine = LearningSimilarityEngine()

        learning_a = {"content": "Always use type hints in Python code"}
        learning_b = {"content": "Use type hints in Python for better code quality"}

        assert engine.are_similar(learning_a, learning_b)

    def test_are_similar_different(self) -> None:
        """Test dissimilar learnings are not marked as similar"""
        engine = LearningSimilarityEngine()

        learning_a = {"content": "Always use type hints in Python code"}
        learning_b = {"content": "JavaScript async/await best practices"}

        assert not engine.are_similar(learning_a, learning_b)

    def test_get_similarity_score(self) -> None:
        """Test getting numeric similarity score"""
        engine = LearningSimilarityEngine()

        learning_a = {"content": "Python Django REST framework"}
        learning_b = {"content": "Python Django"}

        score = engine.get_similarity_score(learning_a, learning_b)
        assert 0.0 <= score <= 1.0
        assert score > 0.7  # Should be fairly similar

    def test_similarity_score_caching(self) -> None:
        """Test that similarity scores are cached"""
        engine = LearningSimilarityEngine()

        learning_a = {"content": "Python programming"}
        learning_b = {"content": "Python development"}

        # First call - compute
        score1 = engine.get_similarity_score(learning_a, learning_b)

        # Second call - from cache
        score2 = engine.get_similarity_score(learning_a, learning_b)

        assert score1 == score2
        assert len(engine._cache) > 0

    def test_cache_is_order_independent(self) -> None:
        """Test that cache works regardless of argument order"""
        engine = LearningSimilarityEngine()

        learning_a = {"content": "Python programming"}
        learning_b = {"content": "Python development"}

        # Compute in both orders
        score1 = engine.get_similarity_score(learning_a, learning_b)
        score2 = engine.get_similarity_score(learning_b, learning_a)

        assert score1 == score2
        # Should use same cache entry
        assert len(engine._cache) == 1

    def test_clear_cache(self) -> None:
        """Test clearing the similarity cache"""
        engine = LearningSimilarityEngine()

        learning_a = {"content": "Python programming"}
        learning_b = {"content": "Python development"}

        engine.get_similarity_score(learning_a, learning_b)
        assert len(engine._cache) > 0

        engine.clear_cache()
        assert len(engine._cache) == 0
        assert len(engine._word_cache) == 0

    def test_word_cache_cleared_per_category(self) -> None:
        """Test that word cache is cleared between categories during merge"""
        engine = LearningSimilarityEngine()

        learnings = {
            "categories": {
                "category1": [
                    {"id": "1", "content": "Python Django Flask", "applies_to": []},
                    {"id": "2", "content": "Python Django", "applies_to": []},
                ],
                "category2": [
                    {"id": "3", "content": "JavaScript React Vue", "applies_to": []},
                    {"id": "4", "content": "JavaScript React", "applies_to": []},
                ],
            }
        }

        # Merge should process both categories successfully
        merged_count = engine.merge_similar_learnings(learnings)
        assert merged_count == 2  # One merge per category

    def test_merge_similar_learnings(self) -> None:
        """Test merging similar learnings within categories"""
        engine = LearningSimilarityEngine()

        learnings = {
            "categories": {
                "best_practices": [
                    {
                        "id": "1",
                        "content": "type hints python programming code",
                        "applies_to": ["python"],
                    },
                    {
                        "id": "2",
                        "content": "type hints python programming",
                        "applies_to": ["code_quality"],
                    },
                    {"id": "3", "content": "JavaScript async patterns", "applies_to": ["js"]},
                ]
            }
        }

        merged_count = engine.merge_similar_learnings(learnings)

        # Should merge first two (similar) but not third (different)
        assert merged_count == 1
        assert len(learnings["categories"]["best_practices"]) == 2

        # Check that merged learning combines applies_to
        merged_learning = learnings["categories"]["best_practices"][0]
        assert "python" in merged_learning.get("applies_to", [])
        assert "code_quality" in merged_learning.get("applies_to", [])

    def test_merge_preserves_longer_content(self) -> None:
        """Test that merging preserves the longer content"""
        engine = LearningSimilarityEngine()

        learnings = {
            "categories": {
                "best_practices": [
                    {"id": "1", "content": "python code test", "applies_to": []},
                    {
                        "id": "2",
                        "content": "python code test with much longer content and more details",
                        "applies_to": [],
                    },
                ]
            }
        }

        engine.merge_similar_learnings(learnings)

        # Should keep the longer content
        remaining = learnings["categories"]["best_practices"][0]
        assert "longer" in remaining["content"]

    def test_merge_combines_tags(self) -> None:
        """Test that merging combines tags from both learnings"""
        engine = LearningSimilarityEngine()

        learnings = {
            "categories": {
                "best_practices": [
                    {
                        "id": "1",
                        "content": "type hints python programming quality",
                        "tags": ["python", "typing"],
                        "applies_to": [],
                    },
                    {
                        "id": "2",
                        "content": "type hints python programming",
                        "tags": ["best_practice", "python"],
                        "applies_to": [],
                    },
                ]
            }
        }

        engine.merge_similar_learnings(learnings)

        merged = learnings["categories"]["best_practices"][0]
        tags = set(merged.get("tags", []))
        assert "python" in tags
        assert "typing" in tags
        assert "best_practice" in tags

    def test_get_related_learnings(self) -> None:
        """Test finding related learnings"""
        engine = LearningSimilarityEngine()

        learnings = {
            "categories": {
                "best_practices": [
                    {
                        "id": "target",
                        "content": "python type hints programming code quality",
                        "applies_to": [],
                    },
                    {
                        "id": "related1",
                        "content": "type hints python code quality",
                        "applies_to": [],
                    },
                    {
                        "id": "related2",
                        "content": "python programming type hints",
                        "applies_to": [],
                    },
                    {
                        "id": "unrelated",
                        "content": "JavaScript async patterns",
                        "applies_to": [],
                    },
                ]
            }
        }

        related = engine.get_related_learnings(learnings, "target", limit=5)

        # Should find related Python/typing learnings but not JavaScript
        assert len(related) >= 2
        related_ids = [r["id"] for r in related]
        assert "related1" in related_ids
        assert "related2" in related_ids
        assert "unrelated" not in related_ids

    def test_get_related_learnings_with_similarity_scores(self) -> None:
        """Test that related learnings include similarity scores"""
        engine = LearningSimilarityEngine()

        learnings = {
            "categories": {
                "best_practices": [
                    {"id": "target", "content": "Python type hints", "applies_to": []},
                    {"id": "related", "content": "Type hints Python", "applies_to": []},
                ]
            }
        }

        related = engine.get_related_learnings(learnings, "target", limit=5)

        assert len(related) == 1
        assert "similarity_score" in related[0]
        assert 0.0 <= related[0]["similarity_score"] <= 1.0

    def test_get_related_learnings_respects_limit(self) -> None:
        """Test that related learnings respects the limit parameter"""
        engine = LearningSimilarityEngine()

        learnings = {
            "categories": {
                "best_practices": [
                    {"id": "target", "content": "Python Django", "applies_to": []},
                    {"id": "r1", "content": "Python Django REST", "applies_to": []},
                    {"id": "r2", "content": "Django Python web", "applies_to": []},
                    {"id": "r3", "content": "Python web Django", "applies_to": []},
                    {"id": "r4", "content": "Django REST Python", "applies_to": []},
                ]
            }
        }

        related = engine.get_related_learnings(learnings, "target", limit=2)

        assert len(related) <= 2

    def test_get_related_learnings_nonexistent_id(self) -> None:
        """Test getting related learnings for non-existent ID"""
        engine = LearningSimilarityEngine()

        learnings = {
            "categories": {
                "best_practices": [{"id": "existing", "content": "Some content", "applies_to": []}]
            }
        }

        related = engine.get_related_learnings(learnings, "nonexistent", limit=5)

        assert related == []

    def test_find_learning_by_id(self) -> None:
        """Test finding a learning by its ID"""
        engine = LearningSimilarityEngine()

        learnings = {
            "categories": {
                "best_practices": [{"id": "test123", "content": "Test content"}],
                "gotchas": [{"id": "test456", "content": "Gotcha content"}],
            }
        }

        # Find in first category
        found = engine._find_learning_by_id(learnings, "test123")
        assert found is not None
        assert found["id"] == "test123"

        # Find in second category
        found = engine._find_learning_by_id(learnings, "test456")
        assert found is not None
        assert found["id"] == "test456"

        # Not found
        found = engine._find_learning_by_id(learnings, "nonexistent")
        assert found is None

    def test_merge_learning_helper(self) -> None:
        """Test the _merge_learning helper method"""
        engine = LearningSimilarityEngine()

        target = {
            "id": "1",
            "content": "Short",
            "applies_to": ["python"],
            "tags": ["type1"],
        }

        source = {
            "id": "2",
            "content": "Much longer content",
            "applies_to": ["django"],
            "tags": ["type2"],
        }

        engine._merge_learning(target, source)

        # Should combine applies_to
        assert set(target["applies_to"]) == {"python", "django"}

        # Should combine tags
        assert set(target["tags"]) == {"type1", "type2"}

        # Should use longer content
        assert target["content"] == "Much longer content"

    def test_english_stopwords_constant(self) -> None:
        """Test that ENGLISH_STOPWORDS is properly defined"""
        assert isinstance(ENGLISH_STOPWORDS, set)
        assert "the" in ENGLISH_STOPWORDS
        assert "a" in ENGLISH_STOPWORDS
        assert "and" in ENGLISH_STOPWORDS
        assert len(ENGLISH_STOPWORDS) > 20  # Should have substantial list


class TestSimilarityEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_content(self) -> None:
        """Test similarity with empty content"""
        engine = LearningSimilarityEngine()

        learning_a = {"content": ""}
        learning_b = {"content": "Some content"}

        score = engine.get_similarity_score(learning_a, learning_b)
        assert score == 0.0

    def test_missing_content_key(self) -> None:
        """Test similarity with missing content key"""
        engine = LearningSimilarityEngine()

        learning_a = {}
        learning_b = {"content": "Some content"}

        score = engine.get_similarity_score(learning_a, learning_b)
        assert score == 0.0

    def test_whitespace_only_content(self) -> None:
        """Test similarity with whitespace-only content"""
        algo = JaccardContainmentSimilarity()

        text1 = "   "
        text2 = "Some content"

        score = algo.compute_similarity(text1, text2)
        assert score == 0.0

    def test_special_characters(self) -> None:
        """Test similarity handles special characters"""
        algo = JaccardContainmentSimilarity()

        text1 = "Use @decorators in Python!"
        text2 = "Python @decorators usage!"

        # Should handle special chars gracefully
        score = algo.compute_similarity(text1, text2)
        assert score > 0.0

    def test_unicode_content(self) -> None:
        """Test similarity with Unicode content"""
        algo = JaccardContainmentSimilarity()

        text1 = "Python 编程最佳实践"
        text2 = "Python 编程实践"

        # Should handle Unicode
        score = algo.compute_similarity(text1, text2)
        assert score > 0.0

    def test_very_long_content(self) -> None:
        """Test similarity with very long content"""
        algo = JaccardContainmentSimilarity()

        text1 = " ".join(["word"] * 1000)
        text2 = " ".join(["word"] * 1000)

        # Should handle long content efficiently
        score = algo.compute_similarity(text1, text2)
        assert score == 1.0
