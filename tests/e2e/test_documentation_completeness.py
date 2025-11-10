"""End-to-end tests for documentation completeness.

This module tests that all documentation files have been updated with spec-first workflow information.
"""

from pathlib import Path

# Get project root
project_root = Path(__file__).parent.parent.parent


class TestDocumentationUpdates:
    """Tests for documentation updates in Phase 5.7.6."""

    def test_writing_specs_guide_exists_and_complete(self):
        """Test that docs/guides/writing-specs.md exists and contains all required sections."""
        # Arrange
        writing_specs_path = project_root / "docs" / "guides" / "writing-specs.md"

        # Assert file exists
        assert writing_specs_path.exists(), "docs/guides/writing-specs.md should exist"

        # Act
        content = writing_specs_path.read_text(encoding="utf-8")

        # Assert - check for key sections
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

        # Assert - check for key concepts
        key_concepts = [
            "single source of truth",
            "acceptance criteria",
            "validation",
            "templates",
        ]

        for concept in key_concepts:
            assert concept.lower() in content.lower(), f"writing-specs.md should mention: {concept}"

    def test_session_driven_development_updated_with_spec_architecture(self):
        """Test that docs/architecture/solokit-methodology.md includes spec architecture section."""
        # Arrange
        sdd_doc_path = project_root / "docs" / "architecture" / "solokit-methodology.md"

        # Assert file exists
        assert sdd_doc_path.exists(), "docs/architecture/solokit-methodology.md should exist"

        # Act
        content = sdd_doc_path.read_text(encoding="utf-8")

        # Assert - check for spec architecture section
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
            assert section in content, f"solokit-methodology.md should contain: {section}"

        # Assert - check for key concepts (case-insensitive search)
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
                f"solokit-methodology.md should mention: {concept}"
            )

    def test_command_documentation_updated_for_spec_workflow(self):
        """Test that command documentation emphasizes spec-first workflow."""
        # Arrange & Act - Check /start command
        start_cmd_path = project_root / ".claude" / "commands" / "start.md"
        assert start_cmd_path.exists(), ".claude/commands/start.md should exist"

        start_content = start_cmd_path.read_text(encoding="utf-8")

        # Assert - /start command mentions spec-first workflow
        assert "spec file" in start_content.lower(), "start.md should mention spec file"
        assert "source of truth" in start_content.lower(), "start.md should mention source of truth"
        assert "Spec-First Architecture" in start_content, (
            "start.md should have Spec-First Architecture section"
        )

        # Arrange & Act - Check /work-new command
        work_new_cmd_path = project_root / ".claude" / "commands" / "work-new.md"
        assert work_new_cmd_path.exists(), ".claude/commands/work-new.md should exist"

        work_new_content = work_new_cmd_path.read_text(encoding="utf-8")

        # Assert - /work-new command mentions spec file workflow
        assert "fill out the spec file" in work_new_content.lower(), (
            "work-new.md should mention filling out spec file"
        )
        assert "Next Step: Fill Out the Spec File" in work_new_content, (
            "work-new.md should have spec file section"
        )
        assert "writing-specs.md" in work_new_content, (
            "work-new.md should reference writing-specs.md"
        )

    def test_readme_mentions_spec_architecture(self):
        """Test that README.md mentions the spec-first architecture."""
        # Arrange
        readme_path = project_root / "README.md"

        # Assert file exists
        assert readme_path.exists(), "README.md should exist"

        # Act
        content = readme_path.read_text(encoding="utf-8")

        # Assert - README mentions spec files
        content_lower = content.lower()
        assert "spec" in content_lower or "specification" in content_lower, (
            "README.md should mention specs or specifications"
        )
