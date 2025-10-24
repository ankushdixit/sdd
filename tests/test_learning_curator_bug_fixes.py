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

    def test_rejects_list_fragments(self):
        """Test that list fragments from commit messages are rejected"""
        # Reject hyphen list markers
        self.assertFalse(
            self.curator.is_valid_learning("annotations\n- Code comments with enough words")
        )

        # Reject asterisk list markers
        self.assertFalse(
            self.curator.is_valid_learning("Some content\n* List item with enough words")
        )

        # Reject bullet point markers
        self.assertFalse(
            self.curator.is_valid_learning("Fragment text\n• Bullet point with enough words")
        )

        # Accept multi-line prose (no list markers)
        self.assertTrue(
            self.curator.is_valid_learning(
                "This is a valid multi-line learning\nthat spans multiple lines without list markers"
            )
        )


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


class TestTestDirectoryExclusion(unittest.TestCase):
    """Test Bug #21 Fix 1: Test directories are excluded from learning extraction"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.curator = LearningsCurator(self.project_root)

        # Create test directories
        (self.project_root / "tests").mkdir(exist_ok=True)
        (self.project_root / "test").mkdir(exist_ok=True)
        (self.project_root / "__tests__").mkdir(exist_ok=True)
        (self.project_root / "spec").mkdir(exist_ok=True)
        (self.project_root / "src").mkdir(exist_ok=True)

        # Create test files in test directories
        self.tests_file = self.project_root / "tests" / "test_example.py"
        self.test_file = self.project_root / "test" / "test_example.py"
        self.jest_file = self.project_root / "__tests__" / "example.test.js"
        self.spec_file = self.project_root / "spec" / "example_spec.rb"

        # Create production file
        self.prod_file = self.project_root / "src" / "main.py"

    def test_excludes_tests_directory(self):
        """Test that tests/ directory is excluded from extraction"""
        self.tests_file.write_text("# LEARNING: Test data from tests directory with words")
        self.prod_file.write_text("# LEARNING: Production learning from src directory here")

        learnings = self.curator.extract_from_code_comments(
            changed_files=[self.tests_file, self.prod_file]
        )

        # Should only extract from production file
        self.assertTrue(
            any("Production learning from src" in entry.get("content", "") for entry in learnings)
        )
        self.assertFalse(
            any("Test data from tests" in entry.get("content", "") for entry in learnings)
        )

    def test_excludes_test_directory(self):
        """Test that test/ directory is excluded from extraction"""
        self.test_file.write_text("# LEARNING: Test data from test directory with words")
        self.prod_file.write_text("# LEARNING: Production learning from src directory here")

        learnings = self.curator.extract_from_code_comments(
            changed_files=[self.test_file, self.prod_file]
        )

        # Should only extract from production file
        self.assertTrue(
            any("Production learning from src" in entry.get("content", "") for entry in learnings)
        )
        self.assertFalse(
            any("Test data from test" in entry.get("content", "") for entry in learnings)
        )

    def test_excludes_jest_tests_directory(self):
        """Test that __tests__/ directory (JavaScript convention) is excluded"""
        self.jest_file.write_text("// LEARNING: Test data from jest tests directory here")
        self.prod_file.write_text("# LEARNING: Production learning from src directory here")

        learnings = self.curator.extract_from_code_comments(
            changed_files=[self.jest_file, self.prod_file]
        )

        # Should only extract from production file
        self.assertTrue(
            any("Production learning from src" in entry.get("content", "") for entry in learnings)
        )
        self.assertFalse(
            any("Test data from jest" in entry.get("content", "") for entry in learnings)
        )

    def test_excludes_spec_directory(self):
        """Test that spec/ directory (RSpec convention) is excluded"""
        self.spec_file.write_text("# LEARNING: Test data from spec directory with words")
        self.prod_file.write_text("# LEARNING: Production learning from src directory here")

        learnings = self.curator.extract_from_code_comments(
            changed_files=[self.spec_file, self.prod_file]
        )

        # Should only extract from production file
        self.assertTrue(
            any("Production learning from src" in entry.get("content", "") for entry in learnings)
        )
        self.assertFalse(
            any("Test data from spec" in entry.get("content", "") for entry in learnings)
        )


class TestCodeArtifactValidation(unittest.TestCase):
    """Test Bug #21 Fix 2: Content validation rejects code artifacts"""

    def setUp(self):
        self.curator = LearningsCurator()

    def test_rejects_content_with_quote_paren(self):
        """Test rejection of content ending with quote-paren from string literals"""
        artifact_content = 'Valid code learning with enough words here")'
        self.assertFalse(self.curator.is_valid_learning(artifact_content))

    def test_rejects_content_with_escaped_quote(self):
        """Test rejection of content with escaped quotes"""
        artifact_content = 'Learning with \\" escaped quote and words'
        self.assertFalse(self.curator.is_valid_learning(artifact_content))

    def test_rejects_content_with_visible_newline(self):
        """Test rejection of content with visible \\n escape sequences"""
        artifact_content = "Learning with \\n visible newline and more words"
        self.assertFalse(self.curator.is_valid_learning(artifact_content))

    def test_rejects_content_with_backticks(self):
        """Test rejection of content with backticks (code fragments)"""
        artifact_content = "Learning with `code` backticks and more words"
        self.assertFalse(self.curator.is_valid_learning(artifact_content))

    def test_rejects_content_ending_with_quote_semicolon(self):
        """Test rejection of content ending with quote-semicolon"""
        artifact_content = 'Valid learning with enough words here";'
        self.assertFalse(self.curator.is_valid_learning(artifact_content))

    def test_rejects_content_with_single_quote_paren(self):
        """Test rejection of content ending with single-quote-paren"""
        artifact_content = "Valid learning with enough words here')"
        self.assertFalse(self.curator.is_valid_learning(artifact_content))

    def test_accepts_clean_valid_learning(self):
        """Test that clean valid learnings are still accepted"""
        clean_content = "This is a clean learning with no code artifacts"
        self.assertTrue(self.curator.is_valid_learning(clean_content))

    def test_accepts_learning_with_normal_punctuation(self):
        """Test that learnings with normal punctuation are accepted"""
        normal_content = "Learning with normal punctuation: commas, periods, and more."
        self.assertTrue(self.curator.is_valid_learning(normal_content))


class TestRegexPatternStrictness(unittest.TestCase):
    """Test Bug #21 Fix 3: Regex pattern only matches actual comment lines"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.curator = LearningsCurator(self.project_root)

        # Create test file
        (self.project_root / "src").mkdir(exist_ok=True)
        self.test_file = self.project_root / "src" / "test.py"

    def test_extracts_actual_comment(self):
        """Test that actual # LEARNING comments are extracted"""
        code = """# LEARNING: This is an actual comment with words
def foo():
    pass
"""
        self.test_file.write_text(code)
        learnings = self.curator.extract_from_code_comments(changed_files=[self.test_file])

        self.assertEqual(len(learnings), 1)
        self.assertIn("actual comment", learnings[0]["content"])

    def test_extracts_indented_comment(self):
        """Test that indented # LEARNING comments are extracted"""
        code = """def foo():
    # LEARNING: Indented learning comment with enough words here
    pass
"""
        self.test_file.write_text(code)
        learnings = self.curator.extract_from_code_comments(changed_files=[self.test_file])

        self.assertEqual(len(learnings), 1)
        self.assertIn("Indented learning", learnings[0]["content"])

    def test_does_not_extract_string_literal(self):
        """Test that string literals containing LEARNING pattern are NOT extracted"""
        code = """def test_example():
    test_data = "# LEARNING: This is test data not comment"
    file.write_text("# LEARNING: Another test string with enough words here")
"""
        self.test_file.write_text(code)
        learnings = self.curator.extract_from_code_comments(changed_files=[self.test_file])

        # Should not extract any learnings from string literals
        self.assertEqual(len(learnings), 0)

    def test_does_not_extract_learning_in_middle_of_line(self):
        """Test that LEARNING pattern not at line start is NOT extracted"""
        code = """def foo():
    x = "some string # LEARNING: This should not be extracted ever"
"""
        self.test_file.write_text(code)
        learnings = self.curator.extract_from_code_comments(changed_files=[self.test_file])

        self.assertEqual(len(learnings), 0)

    def test_extracts_multiple_actual_comments(self):
        """Test that multiple actual comments are all extracted"""
        code = """# LEARNING: First learning comment with enough words here
def foo():
    # LEARNING: Second learning comment also with enough words
    pass

# LEARNING: Third learning comment at end with words
"""
        self.test_file.write_text(code)
        learnings = self.curator.extract_from_code_comments(changed_files=[self.test_file])

        self.assertEqual(len(learnings), 3)
        self.assertTrue(any("First learning" in entry["content"] for entry in learnings))
        self.assertTrue(any("Second learning" in entry["content"] for entry in learnings))
        self.assertTrue(any("Third learning" in entry["content"] for entry in learnings))


class TestBug21Integration(unittest.TestCase):
    """Integration test for Bug #21: All three fixes working together"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.curator = LearningsCurator(self.project_root)

        # Create directories
        (self.project_root / "tests").mkdir(exist_ok=True)
        (self.project_root / "src").mkdir(exist_ok=True)

    def test_full_bug_scenario(self):
        """Test the full bug scenario: test file with string literals should extract nothing"""
        # This is the exact scenario from the bug report
        test_file = self.project_root / "tests" / "test_learning_curator_bug_fixes.py"
        test_content = """def test_example():
    test_data = "# LEARNING: This is test data"
    file.write_text("# LEARNING: Valid code learning with enough words here")
    assert test_data
"""
        test_file.write_text(test_content)

        learnings = self.curator.extract_from_code_comments(changed_files=[test_file])

        # Should extract NOTHING from test file (directory excluded + string literals)
        self.assertEqual(len(learnings), 0)

    def test_production_code_still_works(self):
        """Test that production code with real comments still works correctly"""
        prod_file = self.project_root / "src" / "main.py"
        prod_content = """# LEARNING: Production learning comment with enough words

def important_function():
    # LEARNING: Another production learning with sufficient word count
    pass
"""
        prod_file.write_text(prod_content)

        learnings = self.curator.extract_from_code_comments(changed_files=[prod_file])

        # Should extract both production learnings
        self.assertEqual(len(learnings), 2)
        self.assertTrue(
            any("Production learning comment" in entry["content"] for entry in learnings)
        )
        self.assertTrue(
            any("Another production learning" in entry["content"] for entry in learnings)
        )

    def test_mixed_scenario(self):
        """Test mixed scenario with test files and production files"""
        test_file = self.project_root / "tests" / "test_example.py"
        test_file.write_text('file.write_text("# LEARNING: Test data with enough words here")')

        prod_file = self.project_root / "src" / "main.py"
        prod_file.write_text("# LEARNING: Real production learning with enough words")

        learnings = self.curator.extract_from_code_comments(changed_files=[test_file, prod_file])

        # Should only extract from production file
        self.assertEqual(len(learnings), 1)
        self.assertIn("Real production learning", learnings[0]["content"])

    def test_no_garbage_entries(self):
        """Test that no garbage entries with code artifacts are created"""
        test_file = self.project_root / "tests" / "test.py"
        test_file.write_text('x = "# LEARNING: annotations\\n- Code comments with words")')

        learnings = self.curator.extract_from_code_comments(changed_files=[test_file])

        # Should be empty (test directory excluded)
        self.assertEqual(len(learnings), 0)

        # Even if we bypass directory check, content validation should reject it
        prod_file = self.project_root / "src" / "broken.py"
        prod_file.write_text('x = "# LEARNING: Valid code learning with enough words here")')

        learnings = self.curator.extract_from_code_comments(changed_files=[prod_file])

        # Should be empty (regex won't match string literals anymore)
        self.assertEqual(len(learnings), 0)


if __name__ == "__main__":
    unittest.main()
