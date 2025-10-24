#!/usr/bin/env python3
"""
Test Suite for Phase 5.7.6: Documentation Updates

Tests that all documentation files have been updated with spec-first workflow information.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestDocumentationUpdates:
    """Test suite for documentation updates in Phase 5.7.6."""

    def test_writing_specs_guide_exists_and_complete(self):
        """Test: docs/guides/writing-specs.md exists and contains key sections."""
        writing_specs_path = project_root / "docs" / "guides" / "writing-specs.md"

        assert writing_specs_path.exists(), "docs/writing-specs.md should exist"

        content = writing_specs_path.read_text(encoding="utf-8")

        # Check for key sections
        required_sections = [
            "# Writing Effective Specifications",
            "## Why Good Specs Matter",
            "## Spec-First Principles",
            "## General Guidelines",
            "## Work Item Type Guides",
            "### Feature Specs",
            "### Bug Specs",
            "### Refactor Specs",
            "### Security Specs",
            "### Integration Test Specs",
            "### Deployment Specs",
            "## Good vs Bad Examples",
            "## Tips and Best Practices",
            "## Common Mistakes",
            "## Validation Checklist",
        ]

        for section in required_sections:
            assert section in content, f"writing-specs.md should contain section: {section}"

        # Check for key concepts
        key_concepts = [
            "single source of truth",
            "acceptance criteria",
            "validation",
            "templates",
        ]

        for concept in key_concepts:
            assert concept.lower() in content.lower(), f"writing-specs.md should mention: {concept}"

        print("✓ Test 1: docs/writing-specs.md exists and contains all required sections")

    def test_session_driven_development_updated_with_spec_architecture(self):
        """Test: docs/architecture/session-driven-development.md includes spec architecture section."""
        sdd_doc_path = project_root / "docs" / "architecture" / "session-driven-development.md"

        assert sdd_doc_path.exists(), "docs/session-driven-development.md should exist"

        content = sdd_doc_path.read_text(encoding="utf-8")

        # Check for spec architecture section
        required_sections = [
            "### Spec File Architecture (Phase 5.7)",
            "#### Architecture Overview",
            "#### Separation of Concerns",
            "#### Why Spec-First?",
            "#### Spec File Flow",
            "#### Spec Templates",
            "#### Spec Validation",
            "#### Benefits",
        ]

        for section in required_sections:
            assert section in content, f"session-driven-development.md should contain: {section}"

        # Check for key concepts (case-insensitive search)
        key_concepts = [
            "single source of truth",
            "spec file",
            "work_items.json",
            "validation",
            "Zero Context Loss",
        ]

        content_lower = content.lower()
        for concept in key_concepts:
            assert concept.lower() in content_lower, (
                f"session-driven-development.md should mention: {concept}"
            )

        print("✓ Test 2: docs/session-driven-development.md updated with spec architecture")

    def test_command_documentation_updated_for_spec_workflow(self):
        """Test: Command documentation emphasizes spec-first workflow."""
        # Check /start command
        start_cmd_path = project_root / ".claude" / "commands" / "start.md"
        assert start_cmd_path.exists(), ".claude/commands/start.md should exist"

        start_content = start_cmd_path.read_text(encoding="utf-8")
        assert "spec file" in start_content.lower(), "start.md should mention spec file"
        assert "source of truth" in start_content.lower(), "start.md should mention source of truth"
        assert "Spec-First Architecture" in start_content, (
            "start.md should have Spec-First Architecture section"
        )

        # Check /work-new command
        work_new_cmd_path = project_root / ".claude" / "commands" / "work-new.md"
        assert work_new_cmd_path.exists(), ".claude/commands/work-new.md should exist"

        work_new_content = work_new_cmd_path.read_text(encoding="utf-8")
        assert "fill out the spec file" in work_new_content.lower(), (
            "work-new.md should mention filling out spec file"
        )
        assert "Next Step: Fill Out the Spec File" in work_new_content, (
            "work-new.md should have spec file section"
        )
        assert "writing-specs.md" in work_new_content, (
            "work-new.md should reference writing-specs.md"
        )

        print("✓ Test 3: Command documentation updated for spec-first workflow")


def run_all_tests():
    """Run all tests and report results."""
    test_instance = TestDocumentationUpdates()

    tests = [
        test_instance.test_writing_specs_guide_exists_and_complete,
        test_instance.test_session_driven_development_updated_with_spec_architecture,
        test_instance.test_command_documentation_updated_for_spec_workflow,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_func.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__} errored: {e}")
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"Test Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print(f"{'=' * 60}")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
