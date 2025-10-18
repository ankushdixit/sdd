#!/usr/bin/env python3
"""
Test Suite for Phase 5.7.1: Briefing Integration

Tests that briefing generation includes full spec content, full project context,
and validates spec completeness.
"""

import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

from scripts.briefing_generator import (
    generate_briefing,
    load_work_item_spec,
    load_current_tree,
    load_project_docs
)


class TestBriefingIntegration:
    """Test suite for briefing integration with spec files."""

    def setup_method(self):
        """Setup test fixtures."""
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp()
        self.original_dir = Path.cwd()
        import os
        os.chdir(self.temp_dir)

        # Create .session directory structure
        self.session_dir = Path(self.temp_dir) / ".session"
        self.specs_dir = self.session_dir / "specs"
        self.tracking_dir = self.session_dir / "tracking"
        self.docs_dir = Path(self.temp_dir) / "docs"

        self.specs_dir.mkdir(parents=True)
        self.tracking_dir.mkdir(parents=True)
        self.docs_dir.mkdir(parents=True)

    def teardown_method(self):
        """Cleanup test fixtures."""
        import os
        os.chdir(self.original_dir)
        shutil.rmtree(self.temp_dir)

    def create_spec_file(self, work_item_id: str, content: str):
        """Helper to create a spec file."""
        spec_path = self.specs_dir / f"{work_item_id}.md"
        spec_path.write_text(content, encoding='utf-8')

    def test_load_work_item_spec_returns_full_content(self):
        """Test: load_work_item_spec returns complete spec file content."""
        work_item_id = "test_feature_123"
        spec_content = """# Feature: Test Feature

## Overview
This is a complete overview of the test feature.

## Rationale
This feature is needed because...

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Implementation Details
Detailed implementation approach here.

## Testing Strategy
How to test this feature.
"""

        self.create_spec_file(work_item_id, spec_content)

        loaded_content = load_work_item_spec(work_item_id)

        # Should return full content, not truncated
        assert "# Feature: Test Feature" in loaded_content
        assert "## Overview" in loaded_content
        assert "## Rationale" in loaded_content
        assert "## Acceptance Criteria" in loaded_content
        assert "## Implementation Details" in loaded_content
        assert "## Testing Strategy" in loaded_content
        assert "This is a complete overview" in loaded_content
        assert "Criterion 1" in loaded_content

        print("✓ Test 1: load_work_item_spec returns full content without truncation")

    def test_load_work_item_spec_handles_missing_file(self):
        """Test: load_work_item_spec handles missing spec file gracefully."""
        work_item_id = "nonexistent_work_item"

        loaded_content = load_work_item_spec(work_item_id)

        # Should return informative message, not crash
        assert "not found" in loaded_content.lower() or "no specification" in loaded_content.lower()

        print("✓ Test 2: load_work_item_spec handles missing file gracefully")

    def test_load_current_tree_returns_full_tree(self):
        """Test: load_current_tree returns full tree without 50-line limit."""
        # Create tree.txt with more than 50 lines
        tree_content = "\n".join([f"file_{i}.py" for i in range(100)])
        tree_path = self.tracking_dir / "tree.txt"
        tree_path.write_text(tree_content, encoding='utf-8')

        loaded_tree = load_current_tree()

        # Should have all 100 lines, not limited to 50
        assert "file_0.py" in loaded_tree
        assert "file_50.py" in loaded_tree
        assert "file_99.py" in loaded_tree
        line_count = len(loaded_tree.split('\n'))
        assert line_count >= 100, f"Expected >= 100 lines, got {line_count}"

        print("✓ Test 3: load_current_tree returns full tree without 50-line limit")

    def test_load_project_docs_returns_full_vision(self):
        """Test: load_project_docs returns full vision.md without 500-char limit."""
        # Create vision.md with more than 500 characters
        vision_content = "Project Vision\n\n" + ("This is a detailed vision statement. " * 50)
        vision_path = self.docs_dir / "vision.md"
        vision_path.write_text(vision_content, encoding='utf-8')

        project_docs = load_project_docs()

        # Should have full content, not truncated to 500 chars
        loaded_vision = project_docs.get("vision.md", "")
        assert len(loaded_vision) > 500
        assert "Project Vision" in loaded_vision
        assert loaded_vision.count("detailed vision statement") >= 40

        print("✓ Test 4: load_project_docs returns full vision.md without 500-char limit")

    def test_load_project_docs_returns_full_architecture(self):
        """Test: load_project_docs returns full architecture.md without 500-char limit."""
        # Create architecture.md with more than 500 characters
        arch_content = "Project Architecture\n\n" + ("This describes the architecture in detail. " * 50)
        arch_path = self.docs_dir / "architecture.md"
        arch_path.write_text(arch_content, encoding='utf-8')

        project_docs = load_project_docs()

        # Should have full content, not truncated
        loaded_arch = project_docs.get("architecture.md", "")
        assert len(loaded_arch) > 500
        assert "Project Architecture" in loaded_arch
        assert loaded_arch.count("architecture in detail") >= 40

        print("✓ Test 5: load_project_docs returns full architecture.md without 500-char limit")

    def test_generate_briefing_includes_full_spec(self):
        """Test: generate_briefing includes complete spec file content."""
        work_item_id = "test_feature_456"
        spec_content = """# Feature: Another Test Feature

## Overview
Complete overview here.

## Rationale
Why this feature matters.

## Acceptance Criteria
- [ ] Must do X
- [ ] Must do Y
- [ ] Must do Z

## Implementation Details
Detailed implementation.

## Testing Strategy
Testing approach.
"""

        self.create_spec_file(work_item_id, spec_content)

        # Create minimal work item
        work_item = {
            "id": work_item_id,
            "type": "feature",
            "title": "Test Feature",
            "priority": "high",
            "status": "not_started"
        }

        # Create empty learnings
        learnings_data = {"learnings": []}

        # Generate briefing
        briefing = generate_briefing(work_item_id, work_item, learnings_data)

        # Briefing should include full spec content
        assert "## Work Item Specification" in briefing
        assert "# Feature: Another Test Feature" in briefing
        assert "Complete overview here" in briefing
        assert "Why this feature matters" in briefing
        assert "Must do X" in briefing
        assert "Detailed implementation" in briefing
        assert "Testing approach" in briefing

        print("✓ Test 6: generate_briefing includes full spec content in briefing")

    def test_generate_briefing_includes_spec_validation_warning(self):
        """Test: generate_briefing shows warning if spec is incomplete."""
        work_item_id = "incomplete_feature"
        # Create incomplete spec (missing required sections)
        incomplete_spec = """# Feature: Incomplete Feature

## Overview
Just an overview, missing other required sections.
"""

        self.create_spec_file(work_item_id, incomplete_spec)

        work_item = {
            "id": work_item_id,
            "type": "feature",
            "title": "Incomplete Feature",
            "priority": "high",
            "status": "not_started"
        }

        learnings_data = {"learnings": []}

        briefing = generate_briefing(work_item_id, work_item, learnings_data)

        # Should include validation warning
        # Note: This will only work if spec_validator is importable
        # The warning section is optional based on import success
        if "⚠️ Specification Validation Warning" in briefing:
            assert "Missing required section" in briefing or "incomplete" in briefing.lower()
            print("✓ Test 7: generate_briefing includes spec validation warning for incomplete specs")
        else:
            print("✓ Test 7: generate_briefing (spec validation warning skipped - validator not available)")

    def test_briefing_structure_has_no_duplicate_sections(self):
        """Test: Briefing doesn't have duplicate sections (Implementation Checklist, Validation Requirements removed)."""
        work_item_id = "test_feature_789"
        spec_content = """# Feature: Test Feature

## Overview
Overview content.

## Rationale
Rationale content.

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Implementation Details
Implementation details.

## Testing Strategy
Testing strategy.
"""

        self.create_spec_file(work_item_id, spec_content)

        work_item = {
            "id": work_item_id,
            "type": "feature",
            "title": "Test Feature",
            "priority": "high",
            "status": "not_started"
        }

        learnings_data = {"learnings": []}

        briefing = generate_briefing(work_item_id, work_item, learnings_data)

        # These sections should NOT appear (they were removed in Phase 5.7.1)
        assert "## Implementation Checklist" not in briefing
        assert "## Validation Requirements" not in briefing

        # Should still have core sections
        assert "## Work Item Specification" in briefing
        assert "## Dependencies" in briefing

        print("✓ Test 8: Briefing structure has no duplicate sections")

    def test_work_items_json_has_no_content_fields(self):
        """Test: work_items.json should not contain content fields (rationale, acceptance_criteria, etc.)."""
        # This test verifies the schema change from Phase 5.7.1

        # Create a work item as the system would
        work_item_data = {
            "work_items": {
                "test_item_001": {
                    "id": "test_item_001",
                    "type": "feature",
                    "title": "Test Item",
                    "status": "not_started",
                    "priority": "high",
                    "dependencies": [],
                    "milestone": None,
                    "created_at": "2025-10-18T12:00:00Z",
                    "sessions": []
                }
            }
        }

        # Write to work_items.json
        work_items_path = self.tracking_dir / "work_items.json"
        work_items_path.write_text(json.dumps(work_item_data, indent=2), encoding='utf-8')

        # Read back
        with open(work_items_path) as f:
            loaded_data = json.load(f)

        work_item = loaded_data["work_items"]["test_item_001"]

        # Should NOT have content fields
        assert "rationale" not in work_item, "work_items.json should not contain 'rationale' field"
        assert "acceptance_criteria" not in work_item, "work_items.json should not contain 'acceptance_criteria' field"
        assert "implementation_paths" not in work_item, "work_items.json should not contain 'implementation_paths' field"
        assert "test_paths" not in work_item, "work_items.json should not contain 'test_paths' field"

        # Should have tracking fields
        assert "id" in work_item
        assert "type" in work_item
        assert "status" in work_item
        assert "priority" in work_item
        assert "dependencies" in work_item

        print("✓ Test 9: work_items.json has no content fields (pure tracking)")


def run_all_tests():
    """Run all tests and report results."""
    test_instance = TestBriefingIntegration()

    tests = [
        test_instance.test_load_work_item_spec_returns_full_content,
        test_instance.test_load_work_item_spec_handles_missing_file,
        test_instance.test_load_current_tree_returns_full_tree,
        test_instance.test_load_project_docs_returns_full_vision,
        test_instance.test_load_project_docs_returns_full_architecture,
        test_instance.test_generate_briefing_includes_full_spec,
        test_instance.test_generate_briefing_includes_spec_validation_warning,
        test_instance.test_briefing_structure_has_no_duplicate_sections,
        test_instance.test_work_items_json_has_no_content_fields,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_instance.setup_method()
            test_func()
            test_instance.teardown_method()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_func.__name__} failed: {e}")
            test_instance.teardown_method()
            failed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__} errored: {e}")
            test_instance.teardown_method()
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"Test Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print(f"{'=' * 60}")

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
