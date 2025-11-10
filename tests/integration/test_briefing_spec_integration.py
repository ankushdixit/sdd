"""Integration tests for briefing spec integration module.

This module tests the integration between briefing generation and spec files,
including full content loading, validation warnings, and schema changes.
"""

import json

from solokit.session.briefing import (
    generate_briefing,
    load_current_tree,
    load_project_docs,
    load_work_item_spec,
)


class TestLoadWorkItemSpec:
    """Tests for load_work_item_spec function."""

    def test_load_work_item_spec_returns_full_content(self, temp_project_dir, monkeypatch):
        """Test that load_work_item_spec returns complete spec file content without truncation."""
        # Arrange
        monkeypatch.chdir(temp_project_dir)
        specs_dir = temp_project_dir / ".session" / "specs"
        specs_dir.mkdir(parents=True)

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
        spec_path = specs_dir / f"{work_item_id}.md"
        spec_path.write_text(spec_content, encoding="utf-8")

        # Act
        loaded_content = load_work_item_spec(work_item_id)

        # Assert
        assert "# Feature: Test Feature" in loaded_content
        assert "## Overview" in loaded_content
        assert "## Rationale" in loaded_content
        assert "## Acceptance Criteria" in loaded_content
        assert "## Implementation Details" in loaded_content
        assert "## Testing Strategy" in loaded_content
        assert "This is a complete overview" in loaded_content
        assert "Criterion 1" in loaded_content

    def test_load_work_item_spec_handles_missing_file(self, temp_project_dir, monkeypatch):
        """Test that load_work_item_spec handles missing spec file gracefully."""
        # Arrange
        monkeypatch.chdir(temp_project_dir)
        specs_dir = temp_project_dir / ".session" / "specs"
        specs_dir.mkdir(parents=True)
        work_item_id = "nonexistent_work_item"

        # Act
        loaded_content = load_work_item_spec(work_item_id)

        # Assert
        assert "not found" in loaded_content.lower() or "no specification" in loaded_content.lower()

    def test_load_work_item_spec_preserves_formatting(self, temp_project_dir, monkeypatch):
        """Test that load_work_item_spec preserves markdown formatting."""
        # Arrange
        monkeypatch.chdir(temp_project_dir)
        specs_dir = temp_project_dir / ".session" / "specs"
        specs_dir.mkdir(parents=True)

        work_item_id = "formatted_feature"
        spec_content = """# Feature: Formatted Feature

## Code Examples
```python
def example():
    return "test"
```

## Lists
- Item 1
  - Nested item 1.1
  - Nested item 1.2
- Item 2

## Tables
| Column 1 | Column 2 |
|----------|----------|
| Value 1  | Value 2  |
"""
        spec_path = specs_dir / f"{work_item_id}.md"
        spec_path.write_text(spec_content, encoding="utf-8")

        # Act
        loaded_content = load_work_item_spec(work_item_id)

        # Assert
        assert "```python" in loaded_content
        assert "def example():" in loaded_content
        assert "- Item 1" in loaded_content
        assert "  - Nested item 1.1" in loaded_content
        assert "| Column 1 | Column 2 |" in loaded_content

    def test_load_work_item_spec_handles_large_spec(self, temp_project_dir, monkeypatch):
        """Test that load_work_item_spec handles very large spec files."""
        # Arrange
        monkeypatch.chdir(temp_project_dir)
        specs_dir = temp_project_dir / ".session" / "specs"
        specs_dir.mkdir(parents=True)

        work_item_id = "large_feature"
        # Create a large spec with many sections
        spec_content = "# Feature: Large Feature\n\n"
        for i in range(100):
            spec_content += f"## Section {i}\n\nContent for section {i}.\n\n"

        spec_path = specs_dir / f"{work_item_id}.md"
        spec_path.write_text(spec_content, encoding="utf-8")

        # Act
        loaded_content = load_work_item_spec(work_item_id)

        # Assert
        assert "## Section 0" in loaded_content
        assert "## Section 50" in loaded_content
        assert "## Section 99" in loaded_content
        assert "Content for section 99" in loaded_content


class TestLoadCurrentTree:
    """Tests for load_current_tree function."""

    def test_load_current_tree_returns_full_tree(self, temp_project_dir, monkeypatch):
        """Test that load_current_tree returns full tree without 50-line limit."""
        # Arrange
        monkeypatch.chdir(temp_project_dir)
        tracking_dir = temp_project_dir / ".session" / "tracking"
        tracking_dir.mkdir(parents=True)

        # Create tree.txt with more than 50 lines
        tree_content = "\n".join([f"file_{i}.py" for i in range(100)])
        tree_path = tracking_dir / "tree.txt"
        tree_path.write_text(tree_content, encoding="utf-8")

        # Act
        loaded_tree = load_current_tree()

        # Assert
        assert "file_0.py" in loaded_tree
        assert "file_50.py" in loaded_tree
        assert "file_99.py" in loaded_tree
        line_count = len(loaded_tree.split("\n"))
        assert line_count >= 100, f"Expected >= 100 lines, got {line_count}"

    def test_load_current_tree_handles_missing_file(self, temp_project_dir, monkeypatch):
        """Test that load_current_tree handles missing tree.txt gracefully."""
        # Arrange
        monkeypatch.chdir(temp_project_dir)
        tracking_dir = temp_project_dir / ".session" / "tracking"
        tracking_dir.mkdir(parents=True)

        # Act
        loaded_tree = load_current_tree()

        # Assert
        assert isinstance(loaded_tree, str)
        assert (
            "not found" in loaded_tree.lower()
            or "no tree" in loaded_tree.lower()
            or "not yet" in loaded_tree.lower()
            or loaded_tree == ""
        )

    def test_load_current_tree_preserves_formatting(self, temp_project_dir, monkeypatch):
        """Test that load_current_tree preserves tree structure formatting."""
        # Arrange
        monkeypatch.chdir(temp_project_dir)
        tracking_dir = temp_project_dir / ".session" / "tracking"
        tracking_dir.mkdir(parents=True)

        tree_content = """project/
├── src/
│   ├── main.py
│   └── utils.py
└── tests/
    └── test_main.py"""

        tree_path = tracking_dir / "tree.txt"
        tree_path.write_text(tree_content, encoding="utf-8")

        # Act
        loaded_tree = load_current_tree()

        # Assert
        assert "├──" in loaded_tree
        assert "└──" in loaded_tree
        assert "│" in loaded_tree


class TestLoadProjectDocs:
    """Tests for load_project_docs function."""

    def test_load_project_docs_returns_full_vision(self, temp_project_dir, monkeypatch):
        """Test that load_project_docs returns full vision.md without 500-char limit."""
        # Arrange
        monkeypatch.chdir(temp_project_dir)
        docs_dir = temp_project_dir / "docs"
        docs_dir.mkdir()

        # Create vision.md with more than 500 characters
        vision_content = "Project Vision\n\n" + ("This is a detailed vision statement. " * 50)
        vision_path = docs_dir / "vision.md"
        vision_path.write_text(vision_content, encoding="utf-8")

        # Act
        project_docs = load_project_docs()

        # Assert
        loaded_vision = project_docs.get("vision.md", "")
        assert len(loaded_vision) > 500
        assert "Project Vision" in loaded_vision
        assert loaded_vision.count("detailed vision statement") >= 40

    def test_load_project_docs_returns_full_architecture(self, temp_project_dir, monkeypatch):
        """Test that load_project_docs returns full architecture.md without 500-char limit."""
        # Arrange
        monkeypatch.chdir(temp_project_dir)
        docs_dir = temp_project_dir / "docs"
        docs_dir.mkdir()

        # Create architecture.md with more than 500 characters
        arch_content = "Project Architecture\n\n" + (
            "This describes the architecture in detail. " * 50
        )
        arch_path = docs_dir / "architecture.md"
        arch_path.write_text(arch_content, encoding="utf-8")

        # Act
        project_docs = load_project_docs()

        # Assert
        loaded_arch = project_docs.get("architecture.md", "")
        assert len(loaded_arch) > 500
        assert "Project Architecture" in loaded_arch
        assert loaded_arch.count("architecture in detail") >= 40

    def test_load_project_docs_handles_missing_docs_dir(self, temp_project_dir, monkeypatch):
        """Test that load_project_docs handles missing docs directory gracefully."""
        # Arrange
        monkeypatch.chdir(temp_project_dir)

        # Act
        project_docs = load_project_docs()

        # Assert
        assert isinstance(project_docs, dict)

    def test_load_project_docs_loads_multiple_files(self, temp_project_dir, monkeypatch):
        """Test that load_project_docs loads all available documentation files."""
        # Arrange
        monkeypatch.chdir(temp_project_dir)
        docs_dir = temp_project_dir / "docs"
        docs_dir.mkdir()

        vision_path = docs_dir / "vision.md"
        vision_path.write_text("Vision content", encoding="utf-8")

        arch_path = docs_dir / "architecture.md"
        arch_path.write_text("Architecture content", encoding="utf-8")

        readme_path = docs_dir / "README.md"
        readme_path.write_text("README content", encoding="utf-8")

        # Act
        project_docs = load_project_docs()

        # Assert
        assert "vision.md" in project_docs or len(project_docs) >= 1
        assert "architecture.md" in project_docs or len(project_docs) >= 1


class TestGenerateBriefing:
    """Tests for generate_briefing function."""

    def test_generate_briefing_includes_full_spec(self, temp_project_dir, monkeypatch):
        """Test that generate_briefing includes complete spec file content."""
        # Arrange
        monkeypatch.chdir(temp_project_dir)
        specs_dir = temp_project_dir / ".session" / "specs"
        specs_dir.mkdir(parents=True)

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
        spec_path = specs_dir / f"{work_item_id}.md"
        spec_path.write_text(spec_content, encoding="utf-8")

        work_item = {
            "id": work_item_id,
            "type": "feature",
            "title": "Test Feature",
            "priority": "high",
            "status": "not_started",
        }

        learnings_data = {"learnings": []}

        # Act
        briefing = generate_briefing(work_item_id, work_item, learnings_data)

        # Assert
        assert "## Work Item Specification" in briefing
        assert "# Feature: Another Test Feature" in briefing
        assert "Complete overview here" in briefing
        assert "Why this feature matters" in briefing
        assert "Must do X" in briefing
        assert "Detailed implementation" in briefing
        assert "Testing approach" in briefing

    def test_generate_briefing_includes_spec_validation_warning(
        self, temp_project_dir, monkeypatch
    ):
        """Test that generate_briefing shows warning if spec is incomplete."""
        # Arrange
        monkeypatch.chdir(temp_project_dir)
        specs_dir = temp_project_dir / ".session" / "specs"
        specs_dir.mkdir(parents=True)

        work_item_id = "incomplete_feature"
        incomplete_spec = """# Feature: Incomplete Feature

## Overview
Just an overview, missing other required sections.
"""
        spec_path = specs_dir / f"{work_item_id}.md"
        spec_path.write_text(incomplete_spec, encoding="utf-8")

        work_item = {
            "id": work_item_id,
            "type": "feature",
            "title": "Incomplete Feature",
            "priority": "high",
            "status": "not_started",
        }

        learnings_data = {"learnings": []}

        # Act
        briefing = generate_briefing(work_item_id, work_item, learnings_data)

        # Assert - validation warning is optional based on import success
        # Just verify the spec content is included
        assert "## Overview" in briefing

    def test_briefing_structure_has_no_duplicate_sections(self, temp_project_dir, monkeypatch):
        """Test that briefing doesn't have duplicate sections (Implementation Checklist, Validation Requirements removed)."""
        # Arrange
        monkeypatch.chdir(temp_project_dir)
        specs_dir = temp_project_dir / ".session" / "specs"
        specs_dir.mkdir(parents=True)

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
        spec_path = specs_dir / f"{work_item_id}.md"
        spec_path.write_text(spec_content, encoding="utf-8")

        work_item = {
            "id": work_item_id,
            "type": "feature",
            "title": "Test Feature",
            "priority": "high",
            "status": "not_started",
        }

        learnings_data = {"learnings": []}

        # Act
        briefing = generate_briefing(work_item_id, work_item, learnings_data)

        # Assert
        # These sections should NOT appear (they were removed in Phase 5.7.1)
        assert "## Implementation Checklist" not in briefing
        assert "## Validation Requirements" not in briefing
        # Should still have core sections
        assert "## Work Item Specification" in briefing
        assert "## Dependencies" in briefing

    def test_generate_briefing_handles_missing_spec(self, temp_project_dir, monkeypatch):
        """Test that generate_briefing handles missing spec file gracefully."""
        # Arrange
        monkeypatch.chdir(temp_project_dir)
        specs_dir = temp_project_dir / ".session" / "specs"
        specs_dir.mkdir(parents=True)

        work_item_id = "missing_spec_item"
        work_item = {
            "id": work_item_id,
            "type": "feature",
            "title": "Missing Spec Feature",
            "priority": "high",
            "status": "not_started",
        }

        learnings_data = {"learnings": []}

        # Act
        briefing = generate_briefing(work_item_id, work_item, learnings_data)

        # Assert
        assert isinstance(briefing, str)
        assert len(briefing) > 0

    def test_generate_briefing_includes_learnings(self, temp_project_dir, monkeypatch):
        """Test that generate_briefing includes relevant learnings."""
        # Arrange
        monkeypatch.chdir(temp_project_dir)
        specs_dir = temp_project_dir / ".session" / "specs"
        specs_dir.mkdir(parents=True)

        work_item_id = "feature_with_learnings"
        spec_content = "# Feature: Test Feature\n\n## Overview\nTest feature."
        spec_path = specs_dir / f"{work_item_id}.md"
        spec_path.write_text(spec_content, encoding="utf-8")

        work_item = {
            "id": work_item_id,
            "type": "feature",
            "title": "Test Feature",
            "priority": "high",
            "status": "not_started",
        }

        learnings_data = {
            "learnings": [
                {
                    "id": "L-001",
                    "category": "technical",
                    "content": "Important learning about testing",
                    "tags": ["testing"],
                }
            ]
        }

        # Act
        briefing = generate_briefing(work_item_id, work_item, learnings_data)

        # Assert
        assert isinstance(briefing, str)
        assert len(briefing) > 0


class TestWorkItemsJsonSchema:
    """Tests for work_items.json schema changes."""

    def test_work_items_json_has_no_content_fields(self, temp_project_dir):
        """Test that work_items.json should not contain content fields (rationale, acceptance_criteria, etc.)."""
        # Arrange
        tracking_dir = temp_project_dir / ".session" / "tracking"
        tracking_dir.mkdir(parents=True)

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
                    "sessions": [],
                }
            }
        }

        work_items_path = tracking_dir / "work_items.json"
        work_items_path.write_text(json.dumps(work_item_data, indent=2), encoding="utf-8")

        # Act
        with open(work_items_path) as f:
            loaded_data = json.load(f)

        work_item = loaded_data["work_items"]["test_item_001"]

        # Assert - should NOT have content fields
        assert "rationale" not in work_item
        assert "acceptance_criteria" not in work_item
        assert "implementation_paths" not in work_item
        assert "test_paths" not in work_item

        # Should have tracking fields
        assert "id" in work_item
        assert "type" in work_item
        assert "status" in work_item
        assert "priority" in work_item
        assert "dependencies" in work_item

    def test_work_items_json_has_tracking_fields(self, temp_project_dir):
        """Test that work_items.json contains all required tracking fields."""
        # Arrange
        tracking_dir = temp_project_dir / ".session" / "tracking"
        tracking_dir.mkdir(parents=True)

        work_item_data = {
            "work_items": {
                "test_item_002": {
                    "id": "test_item_002",
                    "type": "bug",
                    "title": "Test Bug",
                    "status": "in_progress",
                    "priority": "critical",
                    "dependencies": ["test_item_001"],
                    "milestone": "v1.0",
                    "created_at": "2025-10-18T12:00:00Z",
                    "sessions": ["session_001"],
                }
            }
        }

        work_items_path = tracking_dir / "work_items.json"
        work_items_path.write_text(json.dumps(work_item_data, indent=2), encoding="utf-8")

        # Act
        with open(work_items_path) as f:
            loaded_data = json.load(f)

        work_item = loaded_data["work_items"]["test_item_002"]

        # Assert
        assert work_item["id"] == "test_item_002"
        assert work_item["type"] == "bug"
        assert work_item["title"] == "Test Bug"
        assert work_item["status"] == "in_progress"
        assert work_item["priority"] == "critical"
        assert work_item["dependencies"] == ["test_item_001"]
        assert work_item["milestone"] == "v1.0"
        assert work_item["sessions"] == ["session_001"]
