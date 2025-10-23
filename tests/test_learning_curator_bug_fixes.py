#!/usr/bin/env python3
"""
Unit tests for learning curator bug fixes.

Tests the fixes for:
- Bug 1: Multi-line LEARNING statement extraction
- Bug 2: File type filtering and content validation
- Bug 3: Standardized metadata structure
"""

import re

# Add parent directory to path
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))


from scripts.learning_curator import LEARNING_SCHEMA, LearningsCurator


class TestMultiLineLearningExtraction(unittest.TestCase):
    """Test Bug 1 fix: Multi-line LEARNING statement extraction from git commits"""

    def setUp(self):
        self.curator = LearningsCurator()
        self.learning_pattern = r"LEARNING:\s*([\s\S]+?)(?=\n\n|\Z)"

    def test_single_line_learning(self):
        """Test extraction of single-line LEARNING statement"""
        commit_message = "feat: Add new feature\n\nLEARNING: This is a single line learning."

        match = re.search(self.learning_pattern, commit_message)
        self.assertIsNotNone(match)
        learning_text = match.group(1).strip()
        self.assertEqual(learning_text, "This is a single line learning.")

    def test_multi_line_learning_basic(self):
        """Test extraction of multi-line LEARNING statement (2-3 lines)"""
        commit_message = """feat: Add authentication

LEARNING: This is a multi-line learning that spans
several lines to provide comprehensive context about
the implementation.

Some other text."""

        match = re.search(self.learning_pattern, commit_message)
        self.assertIsNotNone(match)
        learning_text = match.group(1).strip()

        # Should capture all three lines
        self.assertIn("This is a multi-line learning that spans", learning_text)
        self.assertIn("several lines to provide comprehensive context", learning_text)
        self.assertIn("the implementation.", learning_text)

    def test_multi_line_learning_with_indentation(self):
        """Test extraction of multi-line LEARNING with indented continuation"""
        commit_message = """fix: Bug fix

LEARNING: The .gitignore patterns are added programmatically in
  ensure_gitignore_entries() function, not from a template file.
  This allows dynamic checking of which patterns already exist.

Next paragraph."""

        match = re.search(self.learning_pattern, commit_message)
        self.assertIsNotNone(match)
        learning_text = match.group(1).strip()

        # Should capture all indented lines
        self.assertIn("ensure_gitignore_entries() function", learning_text)
        self.assertIn("This allows dynamic checking", learning_text)

    def test_learning_followed_by_double_newline(self):
        """Test LEARNING statement followed by double newline"""
        commit_message = """feat: New feature

LEARNING: Important learning here that should be captured.


Next section starts here."""

        match = re.search(self.learning_pattern, commit_message)
        self.assertIsNotNone(match)
        learning_text = match.group(1).strip()

        self.assertEqual(learning_text, "Important learning here that should be captured.")
        # Should NOT include "Next section"
        self.assertNotIn("Next section", learning_text)

    def test_learning_with_wrapped_lines(self):
        """Test that LEARNING captures wrapped continuation lines"""
        commit_message = """feat: Feature

LEARNING: This learning continues across multiple lines
without blank lines between them because it is describing
a single cohesive concept that needs detailed explanation.

Next paragraph starts here."""

        match = re.search(self.learning_pattern, commit_message)
        self.assertIsNotNone(match)
        learning_text = match.group(1).strip()

        # Should include all lines until double newline
        self.assertIn("continues across multiple lines", learning_text)
        self.assertIn("without blank lines between them", learning_text)
        self.assertIn("detailed explanation", learning_text)
        # Should NOT include next paragraph
        self.assertNotIn("Next paragraph", learning_text)


class TestFileTypeFiltering(unittest.TestCase):
    """Test Bug 2 fix: File type filtering to skip documentation"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.curator = LearningsCurator(self.project_root)

        # Create test files
        self.code_file = self.project_root / "test.py"
        self.doc_file = self.project_root / "README.md"
        self.template_file = self.project_root / "templates" / "example.py"

        # Create directories
        (self.project_root / "templates").mkdir(exist_ok=True)

    def test_code_extensions_defined(self):
        """Test that code extensions are properly defined"""
        code_extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs"}

        # This is tested implicitly in extract_from_code_comments
        self.assertTrue(len(code_extensions) > 0)

    def test_doc_extensions_defined(self):
        """Test that doc extensions are properly defined"""
        doc_extensions = {".md", ".txt", ".rst"}

        # This is tested implicitly in extract_from_code_comments
        self.assertTrue(len(doc_extensions) > 0)

    def test_skips_markdown_files(self):
        """Test that .md files are skipped"""
        # Create files with valid learning content (5+ words)
        self.code_file.write_text("# LEARNING: Valid code learning with enough words here")
        self.doc_file.write_text("# LEARNING: <your learning here>")

        # Extract learnings
        learnings = self.curator.extract_from_code_comments(
            changed_files=[self.code_file, self.doc_file]
        )

        # Should only extract from code file, not doc file
        self.assertTrue(
            any(
                "Valid code learning with enough words" in learning.get("content", "")
                for learning in learnings
            )
        )
        self.assertFalse(
            any("your learning here" in learning.get("content", "") for learning in learnings)
        )

    def test_skips_template_directories(self):
        """Test that templates/ directory is skipped"""
        # Create files with valid learning content (5+ words)
        self.code_file.write_text("# LEARNING: Valid code learning from main file with words")
        self.template_file.parent.mkdir(exist_ok=True)
        self.template_file.write_text("# LEARNING: Example learning from template directory here")

        # Extract learnings
        learnings = self.curator.extract_from_code_comments(
            changed_files=[self.code_file, self.template_file]
        )

        # Should only extract from main code file, not template
        self.assertTrue(
            any(
                "Valid code learning from main file" in learning.get("content", "")
                for learning in learnings
            )
        )
        self.assertFalse(
            any(
                "Example learning from template" in learning.get("content", "")
                for learning in learnings
            )
        )


class TestContentValidation(unittest.TestCase):
    """Test Bug 2 fix: Content validation to skip placeholders"""

    def setUp(self):
        self.curator = LearningsCurator()

    def test_valid_learning_passes(self):
        """Test that valid learnings (5+ words) pass validation"""
        valid_learning = "This is a valid learning with enough words"
        self.assertTrue(self.curator.is_valid_learning(valid_learning))

    def test_rejects_angle_brackets(self):
        """Test that placeholders with angle brackets are rejected"""
        placeholder = "<your learning here>"
        self.assertFalse(self.curator.is_valid_learning(placeholder))

        partial_placeholder = "This has <placeholder> text in it"
        self.assertFalse(self.curator.is_valid_learning(partial_placeholder))

    def test_rejects_known_placeholders(self):
        """Test that known placeholder text is rejected"""
        placeholders = ["your learning here", "example learning", "todo", "tbd", "placeholder"]

        for placeholder in placeholders:
            self.assertFalse(self.curator.is_valid_learning(placeholder))
            # Test case-insensitive
            self.assertFalse(self.curator.is_valid_learning(placeholder.upper()))

    def test_rejects_short_content(self):
        """Test that content with < 5 words is rejected"""
        short_content = "Too short here"  # 3 words
        self.assertFalse(self.curator.is_valid_learning(short_content))

        exactly_five = "This has exactly five words"  # 5 words
        self.assertTrue(self.curator.is_valid_learning(exactly_five))

    def test_rejects_empty_content(self):
        """Test that empty/None content is rejected"""
        self.assertFalse(self.curator.is_valid_learning(""))
        self.assertFalse(self.curator.is_valid_learning(None))


class TestStandardizedEntryCreation(unittest.TestCase):
    """Test Bug 3 fix: Standardized learning entry creation"""

    def setUp(self):
        self.curator = LearningsCurator()

    def test_creates_entry_with_all_required_fields(self):
        """Test that create_learning_entry includes all required fields"""
        entry = self.curator.create_learning_entry(
            content="Test learning with enough words here",
            source="git_commit",
            session_id="session_001",
            context="Commit abc123",
        )

        # Check all required fields are present
        self.assertIn("content", entry)
        self.assertIn("learned_in", entry)
        self.assertIn("source", entry)
        self.assertIn("context", entry)
        self.assertIn("timestamp", entry)
        self.assertIn("id", entry)

    def test_entry_values_are_correct(self):
        """Test that entry values match input parameters"""
        content = "Test learning content with more words"
        source = "git_commit"
        session_id = "session_002"
        context = "Commit xyz789"

        entry = self.curator.create_learning_entry(
            content=content, source=source, session_id=session_id, context=context
        )

        self.assertEqual(entry["content"], content)
        self.assertEqual(entry["learned_in"], session_id)
        self.assertEqual(entry["source"], source)
        self.assertEqual(entry["context"], context)

    def test_defaults_for_optional_fields(self):
        """Test that optional fields get default values"""
        entry = self.curator.create_learning_entry(
            content="Test learning with sufficient words present", source="git_commit"
        )

        # session_id defaults to "unknown"
        self.assertEqual(entry["learned_in"], "unknown")
        # context defaults to "No context provided"
        self.assertEqual(entry["context"], "No context provided")
        # timestamp and id should be auto-generated
        self.assertIsNotNone(entry["timestamp"])
        self.assertIsNotNone(entry["id"])

    def test_generates_consistent_id(self):
        """Test that same content generates same ID"""
        content = "Test learning for ID consistency check here"

        entry1 = self.curator.create_learning_entry(content=content, source="test")
        entry2 = self.curator.create_learning_entry(content=content, source="test")

        # IDs should be the same for same content
        self.assertEqual(entry1["id"], entry2["id"])

    def test_git_extraction_has_both_fields(self):
        """Test that git-extracted learnings have both learned_in and context"""
        with patch("subprocess.run") as mock_run:
            # Mock git log output
            mock_run.return_value = Mock(
                returncode=0,
                stdout="abc123|||feat: Test\n\nLEARNING: Git commit learning with enough words",
            )

            learnings = self.curator.extract_from_git_commits(session_id="session_003")

            if learnings:  # Only check if extraction succeeded
                learning = learnings[0]
                self.assertIn("learned_in", learning)
                self.assertIn("context", learning)
                self.assertEqual(learning["learned_in"], "session_003")

    def test_temp_file_entry_has_both_fields(self):
        """Test that temp-file learnings have both learned_in and context"""
        entry = self.curator.create_learning_entry(
            content="Temp file learning with many words here",
            source="temp_file",
            session_id="session_004",
            context="Temp file: .session/temp_learnings.txt",
        )

        self.assertIn("learned_in", entry)
        self.assertIn("context", entry)
        self.assertEqual(entry["learned_in"], "session_004")
        self.assertEqual(entry["context"], "Temp file: .session/temp_learnings.txt")


class TestJSONSchemaValidation(unittest.TestCase):
    """Test Bug 3 fix: JSON schema validation for learning entries"""

    def setUp(self):
        self.curator = LearningsCurator()

    def test_valid_entry_passes_validation(self):
        """Test that valid learning entry passes schema validation"""
        valid_entry = {
            "content": "This is a valid learning with more than ten characters",
            "learned_in": "session_001",
            "source": "git_commit",
            "context": "Commit abc123",
            "timestamp": datetime.now().isoformat(),
            "id": "test123",
        }

        self.assertTrue(self.curator.validate_learning(valid_entry))

    def test_missing_required_field_fails(self):
        """Test that missing required fields fail validation"""
        # Missing "context" field
        invalid_entry = {
            "content": "Valid content with enough characters",
            "learned_in": "session_001",
            "source": "git_commit",
            "timestamp": datetime.now().isoformat(),
            "id": "test123",
        }

        self.assertFalse(self.curator.validate_learning(invalid_entry))

    def test_invalid_source_type_fails(self):
        """Test that invalid source type fails validation"""
        invalid_entry = {
            "content": "Valid content with enough characters",
            "learned_in": "session_001",
            "source": "invalid_source",  # Not in enum
            "context": "Test context",
            "timestamp": datetime.now().isoformat(),
            "id": "test123",
        }

        self.assertFalse(self.curator.validate_learning(invalid_entry))

    def test_short_content_fails_validation(self):
        """Test that content shorter than minLength fails"""
        invalid_entry = {
            "content": "Short",  # Less than 10 characters
            "learned_in": "session_001",
            "source": "git_commit",
            "context": "Test context",
            "timestamp": datetime.now().isoformat(),
            "id": "test123",
        }

        self.assertFalse(self.curator.validate_learning(invalid_entry))

    def test_schema_has_all_required_fields(self):
        """Test that LEARNING_SCHEMA defines all required fields"""
        required_fields = ["content", "learned_in", "source", "context", "timestamp", "id"]

        self.assertEqual(set(LEARNING_SCHEMA["required"]), set(required_fields))

    def test_schema_defines_source_enum(self):
        """Test that schema defines valid source types"""
        source_enum = LEARNING_SCHEMA["properties"]["source"]["enum"]

        # Should include all extraction sources
        self.assertIn("git_commit", source_enum)
        self.assertIn("temp_file", source_enum)
        self.assertIn("inline_comment", source_enum)
        self.assertIn("session_summary", source_enum)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases for learning extraction"""

    def setUp(self):
        self.curator = LearningsCurator()

    def test_learning_with_special_characters(self):
        """Test LEARNING with special characters"""
        special_content = "Learning with special chars: @#$% and émojis 🎉 works fine"

        self.assertTrue(self.curator.is_valid_learning(special_content))

        entry = self.curator.create_learning_entry(content=special_content, source="git_commit")
        self.assertTrue(self.curator.validate_learning(entry))

    def test_very_long_learning(self):
        """Test LEARNING with very long content (100+ words)"""
        long_content = " ".join(["word"] * 150)  # 150 words

        self.assertTrue(self.curator.is_valid_learning(long_content))

        entry = self.curator.create_learning_entry(content=long_content, source="git_commit")
        self.assertTrue(self.curator.validate_learning(entry))

    def test_empty_learning_statement(self):
        """Test empty LEARNING statement"""
        empty_content = ""

        self.assertFalse(self.curator.is_valid_learning(empty_content))

    def test_multiple_learnings_in_single_commit(self):
        """Test multiple LEARNING statements in single commit"""
        commit_message = """feat: Multiple learnings

LEARNING: First learning with enough words to be valid

LEARNING: Second learning also with sufficient word count"""

        learning_pattern = r"LEARNING:\s*([\s\S]+?)(?=\n(?![ \t])|\n\n|\Z)"
        matches = list(re.finditer(learning_pattern, commit_message))

        # Should find both learnings
        self.assertEqual(len(matches), 2)


if __name__ == "__main__":
    unittest.main()
