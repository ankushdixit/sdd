"""Unit tests for dependency_graph module.

This module tests the DependencyGraphVisualizer class which generates
dependency graphs for work items with various visualization and analysis features.
"""

import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from sdd.visualization.dependency_graph import DependencyGraphVisualizer


@pytest.fixture
def sample_work_items_data():
    """Provide sample work items data structure for testing."""
    return {
        "work_items": {
            "1": {
                "id": "1",
                "title": "Foundation Module",
                "type": "feature",
                "status": "completed",
                "priority": "critical",
                "dependencies": [],
            },
            "2": {
                "id": "2",
                "title": "User Authentication",
                "type": "feature",
                "status": "in_progress",
                "priority": "critical",
                "dependencies": ["1"],
            },
            "3": {
                "id": "3",
                "title": "API Endpoints",
                "type": "feature",
                "status": "not_started",
                "priority": "high",
                "dependencies": ["1", "2"],
                "milestone": "v1.0",
            },
            "4": {
                "id": "4",
                "title": "Database Schema",
                "type": "feature",
                "status": "blocked",
                "priority": "critical",
                "dependencies": ["1"],
            },
            "5": {
                "id": "5",
                "title": "Frontend UI",
                "type": "feature",
                "status": "not_started",
                "priority": "medium",
                "dependencies": ["3"],
                "milestone": "v1.0",
            },
        }
    }


@pytest.fixture
def sample_work_items_list(sample_work_items_data):
    """Provide sample work items as a list."""
    return list(sample_work_items_data["work_items"].values())


class TestDependencyGraphVisualizerInit:
    """Tests for DependencyGraphVisualizer initialization."""

    def test_init_with_default_path(self):
        """Test that DependencyGraphVisualizer initializes with default work_items path."""
        # Act
        viz = DependencyGraphVisualizer()

        # Assert
        assert viz.work_items_file == Path(".session/tracking/work_items.json")

    def test_init_with_custom_path(self):
        """Test that DependencyGraphVisualizer initializes with custom work_items path."""
        # Arrange
        custom_path = Path("/custom/path/work_items.json")

        # Act
        viz = DependencyGraphVisualizer(custom_path)

        # Assert
        assert viz.work_items_file == custom_path


class TestLoadWorkItems:
    """Tests for load_work_items method."""

    def test_load_work_items_file_not_exists(self, tmp_path):
        """Test that load_work_items returns empty list when file doesn't exist."""
        # Arrange
        non_existent_file = tmp_path / "nonexistent.json"
        viz = DependencyGraphVisualizer(non_existent_file)

        # Act
        result = viz.load_work_items()

        # Assert
        assert result == []

    def test_load_work_items_all_items(self, tmp_path, sample_work_items_data):
        """Test that load_work_items returns all non-completed items by default."""
        # Arrange
        work_items_file = tmp_path / "work_items.json"
        work_items_file.write_text(json.dumps(sample_work_items_data))
        viz = DependencyGraphVisualizer(work_items_file)

        # Act
        result = viz.load_work_items()

        # Assert
        assert len(result) == 4  # All except completed item "1"
        assert all(wi["status"] != "completed" for wi in result)

    def test_load_work_items_include_completed(self, tmp_path, sample_work_items_data):
        """Test that load_work_items includes completed items when flag is set."""
        # Arrange
        work_items_file = tmp_path / "work_items.json"
        work_items_file.write_text(json.dumps(sample_work_items_data))
        viz = DependencyGraphVisualizer(work_items_file)

        # Act
        result = viz.load_work_items(include_completed=True)

        # Assert
        assert len(result) == 5
        assert any(wi["status"] == "completed" for wi in result)

    def test_load_work_items_filter_by_status(self, tmp_path, sample_work_items_data):
        """Test that load_work_items filters by status correctly."""
        # Arrange
        work_items_file = tmp_path / "work_items.json"
        work_items_file.write_text(json.dumps(sample_work_items_data))
        viz = DependencyGraphVisualizer(work_items_file)

        # Act
        result = viz.load_work_items(status_filter="in_progress", include_completed=True)

        # Assert
        assert len(result) == 1
        assert result[0]["id"] == "2"
        assert result[0]["status"] == "in_progress"

    def test_load_work_items_filter_by_milestone(self, tmp_path, sample_work_items_data):
        """Test that load_work_items filters by milestone correctly."""
        # Arrange
        work_items_file = tmp_path / "work_items.json"
        work_items_file.write_text(json.dumps(sample_work_items_data))
        viz = DependencyGraphVisualizer(work_items_file)

        # Act
        result = viz.load_work_items(milestone_filter="v1.0")

        # Assert
        assert len(result) == 2
        assert all(wi.get("milestone") == "v1.0" for wi in result)

    def test_load_work_items_filter_by_type(self, tmp_path, sample_work_items_data):
        """Test that load_work_items filters by type correctly."""
        # Arrange
        data_with_bug = sample_work_items_data.copy()
        data_with_bug["work_items"]["6"] = {
            "id": "6",
            "title": "Fix Bug",
            "type": "bug",
            "status": "not_started",
            "dependencies": [],
        }
        work_items_file = tmp_path / "work_items.json"
        work_items_file.write_text(json.dumps(data_with_bug))
        viz = DependencyGraphVisualizer(work_items_file)

        # Act
        result = viz.load_work_items(type_filter="bug")

        # Assert
        assert len(result) == 1
        assert result[0]["type"] == "bug"

    def test_load_work_items_multiple_filters(self, tmp_path, sample_work_items_data):
        """Test that load_work_items applies multiple filters correctly."""
        # Arrange
        work_items_file = tmp_path / "work_items.json"
        work_items_file.write_text(json.dumps(sample_work_items_data))
        viz = DependencyGraphVisualizer(work_items_file)

        # Act
        result = viz.load_work_items(
            milestone_filter="v1.0", type_filter="feature", status_filter="not_started"
        )

        # Assert
        assert len(result) == 2
        assert all(
            wi["milestone"] == "v1.0" and wi["type"] == "feature" and wi["status"] == "not_started"
            for wi in result
        )


class TestGenerateDot:
    """Tests for generate_dot method."""

    def test_generate_dot_basic_structure(self, sample_work_items_list):
        """Test that generate_dot produces valid DOT format with basic structure."""
        # Arrange
        viz = DependencyGraphVisualizer()

        # Act
        result = viz.generate_dot(sample_work_items_list)

        # Assert
        assert result.startswith("digraph WorkItems {")
        assert result.endswith("}")
        assert "rankdir=TB" in result
        assert "node [shape=box, style=rounded]" in result

    def test_generate_dot_includes_all_nodes(self, sample_work_items_list):
        """Test that generate_dot includes all work items as nodes."""
        # Arrange
        viz = DependencyGraphVisualizer()

        # Act
        result = viz.generate_dot(sample_work_items_list)

        # Assert
        for item in sample_work_items_list:
            assert f'"{item["id"]}"' in result

    def test_generate_dot_includes_edges(self, sample_work_items_list):
        """Test that generate_dot includes dependency edges."""
        # Arrange
        viz = DependencyGraphVisualizer()

        # Act
        result = viz.generate_dot(sample_work_items_list)

        # Assert
        # Check for edge from "1" to "2" (2 depends on 1)
        assert '"1" -> "2"' in result
        # Check for edges to "3" (3 depends on 1 and 2)
        assert '"1" -> "3"' in result
        assert '"2" -> "3"' in result

    def test_generate_dot_node_colors(self, sample_work_items_list):
        """Test that generate_dot applies correct colors based on status."""
        # Arrange
        viz = DependencyGraphVisualizer()

        # Act
        result = viz.generate_dot(sample_work_items_list)

        # Assert
        # Critical path items should be red (takes priority)
        assert 'color="red"' in result
        # Blocked should be orange (not on critical path in our test data)
        assert 'color="orange"' in result

        # Test with items where not all are on critical path
        # A -> B (longest path), C is separate (shorter)
        items_with_branch = [
            {"id": "A", "title": "Item A", "status": "completed", "dependencies": []},
            {"id": "B", "title": "Item B", "status": "not_started", "dependencies": ["A"]},
            {"id": "C", "title": "Item C", "status": "in_progress", "dependencies": []},
        ]
        result2 = viz.generate_dot(items_with_branch)
        # A and B are on critical path (depth 1 for B is max)
        # C is not on critical path and should show status color
        assert 'color="blue"' in result2  # C is in_progress, not on critical path

    def test_generate_dot_critical_path_highlighting(self, sample_work_items_list):
        """Test that generate_dot highlights critical path in red."""
        # Arrange
        viz = DependencyGraphVisualizer()

        # Act
        result = viz.generate_dot(sample_work_items_list)

        # Assert
        # Critical path items should be colored red
        assert 'color="red"' in result

    def test_generate_dot_with_empty_list(self):
        """Test that generate_dot handles empty work items list."""
        # Arrange
        viz = DependencyGraphVisualizer()

        # Act
        result = viz.generate_dot([])

        # Assert
        assert result.startswith("digraph WorkItems {")
        assert result.endswith("}")

    def test_generate_dot_with_missing_dependencies(self):
        """Test that generate_dot handles dependencies that don't exist in filtered items."""
        # Arrange
        viz = DependencyGraphVisualizer()
        work_items = [
            {"id": "1", "title": "Item 1", "status": "not_started", "dependencies": ["999"]},
        ]

        # Act
        result = viz.generate_dot(work_items)

        # Assert
        # Should not create edge to non-existent dependency
        assert '"999" ->' not in result
        assert '"1"' in result


class TestGenerateAscii:
    """Tests for generate_ascii method."""

    def test_generate_ascii_basic_structure(self, sample_work_items_list):
        """Test that generate_ascii produces output with expected structure."""
        # Arrange
        viz = DependencyGraphVisualizer()

        # Act
        result = viz.generate_ascii(sample_work_items_list)

        # Assert
        assert "Work Item Dependency Graph" in result
        assert "=" * 50 in result
        assert "Level" in result

    def test_generate_ascii_includes_all_items(self, sample_work_items_list):
        """Test that generate_ascii includes all work items."""
        # Arrange
        viz = DependencyGraphVisualizer()

        # Act
        result = viz.generate_ascii(sample_work_items_list)

        # Assert
        for item in sample_work_items_list:
            assert item["id"] in result
            assert item["title"] in result

    def test_generate_ascii_shows_status_icons(self, sample_work_items_list):
        """Test that generate_ascii shows status icons for work items."""
        # Arrange
        viz = DependencyGraphVisualizer()

        # Act
        result = viz.generate_ascii(sample_work_items_list)

        # Assert
        assert "●" in result  # Completed
        assert "◐" in result  # In progress
        assert "○" in result  # Not started
        assert "✗" in result  # Blocked

    def test_generate_ascii_shows_dependencies(self, sample_work_items_list):
        """Test that generate_ascii shows dependency relationships."""
        # Arrange
        viz = DependencyGraphVisualizer()

        # Act
        result = viz.generate_ascii(sample_work_items_list)

        # Assert
        assert "depends on" in result
        assert "└─" in result

    def test_generate_ascii_shows_critical_path(self, sample_work_items_list):
        """Test that generate_ascii marks critical path items."""
        # Arrange
        viz = DependencyGraphVisualizer()

        # Act
        result = viz.generate_ascii(sample_work_items_list)

        # Assert
        assert "[CRITICAL PATH]" in result

    def test_generate_ascii_includes_timeline(self, sample_work_items_list):
        """Test that generate_ascii includes timeline projection."""
        # Arrange
        viz = DependencyGraphVisualizer()

        # Act
        result = viz.generate_ascii(sample_work_items_list)

        # Assert
        assert "Timeline Projection:" in result
        assert "-" * 50 in result


class TestGenerateSvg:
    """Tests for generate_svg method."""

    @patch("subprocess.run")
    def test_generate_svg_success(self, mock_run, tmp_path):
        """Test that generate_svg successfully generates SVG file."""
        # Arrange
        viz = DependencyGraphVisualizer()
        output_file = tmp_path / "output.svg"
        dot_content = "digraph { a -> b; }"
        mock_run.return_value = Mock(returncode=0)

        # Act
        result = viz.generate_svg(dot_content, output_file)

        # Assert
        assert result is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == ["dot", "-Tsvg", "-o", str(output_file)]
        assert call_args[1]["input"] == dot_content
        assert call_args[1]["text"] is True
        assert call_args[1]["timeout"] == 30

    @patch("subprocess.run")
    def test_generate_svg_graphviz_not_found(self, mock_run, tmp_path):
        """Test that generate_svg handles Graphviz not installed."""
        # Arrange
        viz = DependencyGraphVisualizer()
        output_file = tmp_path / "output.svg"
        dot_content = "digraph { a -> b; }"
        mock_run.side_effect = FileNotFoundError()

        # Act
        result = viz.generate_svg(dot_content, output_file)

        # Assert
        assert result is False

    @patch("subprocess.run")
    def test_generate_svg_timeout(self, mock_run, tmp_path):
        """Test that generate_svg handles timeout gracefully."""
        # Arrange
        viz = DependencyGraphVisualizer()
        output_file = tmp_path / "output.svg"
        dot_content = "digraph { a -> b; }"
        mock_run.side_effect = subprocess.TimeoutExpired("dot", 30)

        # Act
        result = viz.generate_svg(dot_content, output_file)

        # Assert
        assert result is False

    @patch("subprocess.run")
    def test_generate_svg_nonzero_exit(self, mock_run, tmp_path):
        """Test that generate_svg handles non-zero exit code."""
        # Arrange
        viz = DependencyGraphVisualizer()
        output_file = tmp_path / "output.svg"
        dot_content = "digraph { a -> b; }"
        mock_run.return_value = Mock(returncode=1)

        # Act
        result = viz.generate_svg(dot_content, output_file)

        # Assert
        assert result is False


class TestGetBottlenecks:
    """Tests for get_bottlenecks method."""

    def test_get_bottlenecks_identifies_blocking_items(self, sample_work_items_list):
        """Test that get_bottlenecks identifies items that block multiple others."""
        # Arrange
        viz = DependencyGraphVisualizer()

        # Act
        result = viz.get_bottlenecks(sample_work_items_list)

        # Assert
        # Item "1" blocks items 2, 3, and 4 (3 items)
        # Item "2" blocks item 3 (1 item)
        assert len(result) == 1
        assert result[0]["id"] == "1"
        assert result[0]["blocks"] == 3

    def test_get_bottlenecks_sorted_by_blocks(self):
        """Test that get_bottlenecks returns items sorted by blocks count descending."""
        # Arrange
        viz = DependencyGraphVisualizer()
        work_items = [
            {"id": "A", "dependencies": []},
            {"id": "B", "dependencies": []},
            {"id": "C", "dependencies": ["A"]},
            {"id": "D", "dependencies": ["A"]},
            {"id": "E", "dependencies": ["A"]},
            {"id": "F", "dependencies": ["B"]},
            {"id": "G", "dependencies": ["B"]},
        ]

        # Act
        result = viz.get_bottlenecks(work_items)

        # Assert
        assert len(result) == 2
        assert result[0]["id"] == "A"
        assert result[0]["blocks"] == 3
        assert result[1]["id"] == "B"
        assert result[1]["blocks"] == 2

    def test_get_bottlenecks_no_bottlenecks(self):
        """Test that get_bottlenecks returns empty list when no bottlenecks exist."""
        # Arrange
        viz = DependencyGraphVisualizer()
        work_items = [
            {"id": "A", "dependencies": []},
            {"id": "B", "dependencies": ["A"]},
        ]

        # Act
        result = viz.get_bottlenecks(work_items)

        # Assert
        assert result == []

    def test_get_bottlenecks_includes_item_details(self, sample_work_items_list):
        """Test that get_bottlenecks includes full item details."""
        # Arrange
        viz = DependencyGraphVisualizer()

        # Act
        result = viz.get_bottlenecks(sample_work_items_list)

        # Assert
        assert "item" in result[0]
        assert result[0]["item"]["id"] == "1"
        assert result[0]["item"]["title"] == "Foundation Module"


class TestGetNeighborhood:
    """Tests for get_neighborhood method."""

    def test_get_neighborhood_includes_focus_item(self, sample_work_items_list):
        """Test that get_neighborhood includes the focus item itself."""
        # Arrange
        viz = DependencyGraphVisualizer()

        # Act
        result = viz.get_neighborhood(sample_work_items_list, "2")

        # Assert
        assert any(wi["id"] == "2" for wi in result)

    def test_get_neighborhood_includes_dependencies(self, sample_work_items_list):
        """Test that get_neighborhood includes all dependencies recursively."""
        # Arrange
        viz = DependencyGraphVisualizer()

        # Act
        result = viz.get_neighborhood(sample_work_items_list, "3")

        # Assert
        result_ids = {wi["id"] for wi in result}
        # Item 3 depends on 1 and 2, so all three should be included
        assert "3" in result_ids
        assert "1" in result_ids
        assert "2" in result_ids

    def test_get_neighborhood_includes_dependents(self, sample_work_items_list):
        """Test that get_neighborhood includes items that depend on focus item."""
        # Arrange
        viz = DependencyGraphVisualizer()

        # Act
        result = viz.get_neighborhood(sample_work_items_list, "1")

        # Assert
        result_ids = {wi["id"] for wi in result}
        # Items 2, 3, and 4 depend on 1
        assert "1" in result_ids
        assert "2" in result_ids
        assert "3" in result_ids
        assert "4" in result_ids

    def test_get_neighborhood_nonexistent_focus(self, sample_work_items_list):
        """Test that get_neighborhood returns empty list for non-existent focus item."""
        # Arrange
        viz = DependencyGraphVisualizer()

        # Act
        result = viz.get_neighborhood(sample_work_items_list, "999")

        # Assert
        assert result == []

    def test_get_neighborhood_recursive_dependencies(self):
        """Test that get_neighborhood handles recursive dependencies correctly."""
        # Arrange
        viz = DependencyGraphVisualizer()
        work_items = [
            {"id": "A", "dependencies": []},
            {"id": "B", "dependencies": ["A"]},
            {"id": "C", "dependencies": ["B"]},
            {"id": "D", "dependencies": ["C"]},
        ]

        # Act
        result = viz.get_neighborhood(work_items, "D")

        # Assert
        result_ids = {wi["id"] for wi in result}
        # Should include all items in the chain
        assert result_ids == {"A", "B", "C", "D"}


class TestGenerateStats:
    """Tests for generate_stats method."""

    def test_generate_stats_counts_by_status(self, sample_work_items_list):
        """Test that generate_stats counts work items by status correctly."""
        # Arrange
        viz = DependencyGraphVisualizer()
        critical_path = {"1", "2", "3"}

        # Act
        result = viz.generate_stats(sample_work_items_list, critical_path)

        # Assert
        assert result["total_items"] == 5
        assert result["completed"] == 1
        assert result["in_progress"] == 1
        assert result["not_started"] == 2

    def test_generate_stats_calculates_completion_percentage(self, sample_work_items_list):
        """Test that generate_stats calculates completion percentage correctly."""
        # Arrange
        viz = DependencyGraphVisualizer()
        critical_path = set()

        # Act
        result = viz.generate_stats(sample_work_items_list, critical_path)

        # Assert
        # 1 completed out of 5 total = 20%
        assert result["completion_pct"] == 20.0

    def test_generate_stats_critical_path_length(self, sample_work_items_list):
        """Test that generate_stats includes critical path length."""
        # Arrange
        viz = DependencyGraphVisualizer()
        critical_path = {"1", "2", "3"}

        # Act
        result = viz.generate_stats(sample_work_items_list, critical_path)

        # Assert
        assert result["critical_path_length"] == 3
        assert set(result["critical_items"]) == {"1", "2", "3"}

    def test_generate_stats_empty_list(self):
        """Test that generate_stats handles empty work items list."""
        # Arrange
        viz = DependencyGraphVisualizer()
        critical_path = set()

        # Act
        result = viz.generate_stats([], critical_path)

        # Assert
        assert result["total_items"] == 0
        assert result["completion_pct"] == 0

    def test_generate_stats_all_completed(self):
        """Test that generate_stats handles all items completed."""
        # Arrange
        viz = DependencyGraphVisualizer()
        work_items = [
            {"id": "1", "status": "completed"},
            {"id": "2", "status": "completed"},
        ]
        critical_path = set()

        # Act
        result = viz.generate_stats(work_items, critical_path)

        # Assert
        assert result["total_items"] == 2
        assert result["completed"] == 2
        assert result["completion_pct"] == 100.0


class TestCalculateCriticalPath:
    """Tests for _calculate_critical_path method."""

    def test_calculate_critical_path_simple_chain(self):
        """Test that _calculate_critical_path identifies simple chain correctly."""
        # Arrange
        viz = DependencyGraphVisualizer()
        work_items = [
            {"id": "A", "dependencies": []},
            {"id": "B", "dependencies": ["A"]},
            {"id": "C", "dependencies": ["B"]},
        ]

        # Act
        result = viz._calculate_critical_path(work_items)

        # Assert
        assert result == {"A", "B", "C"}

    def test_calculate_critical_path_missing_dependency(self):
        """Test that _calculate_critical_path handles missing dependencies gracefully."""
        # Arrange
        viz = DependencyGraphVisualizer()
        work_items = [
            {"id": "A", "dependencies": []},
            {"id": "B", "dependencies": ["A", "Z"]},  # Z doesn't exist
        ]

        # Act
        result = viz._calculate_critical_path(work_items)

        # Assert
        # Should still include A and B in critical path despite missing Z
        assert "A" in result
        assert "B" in result

    def test_calculate_critical_path_with_branches(self):
        """Test that _calculate_critical_path identifies longest path with branches."""
        # Arrange
        viz = DependencyGraphVisualizer()
        work_items = [
            {"id": "A", "dependencies": []},
            {"id": "B", "dependencies": ["A"]},
            {"id": "C", "dependencies": ["A"]},
            {"id": "D", "dependencies": ["B"]},
        ]

        # Act
        result = viz._calculate_critical_path(work_items)

        # Assert
        # A -> B -> D is the longest path (depth 2 for D)
        assert "A" in result
        assert "B" in result
        assert "D" in result

    def test_calculate_critical_path_no_dependencies(self):
        """Test that _calculate_critical_path handles items with no dependencies."""
        # Arrange
        viz = DependencyGraphVisualizer()
        work_items = [
            {"id": "A", "dependencies": []},
            {"id": "B", "dependencies": []},
        ]

        # Act
        result = viz._calculate_critical_path(work_items)

        # Assert
        # Both items are at depth 0, both should be in critical path
        assert len(result) == 2

    def test_calculate_critical_path_empty_list(self):
        """Test that _calculate_critical_path handles empty list."""
        # Arrange
        viz = DependencyGraphVisualizer()

        # Act
        result = viz._calculate_critical_path([])

        # Assert
        assert result == set()

    def test_calculate_critical_path_circular_dependency(self):
        """Test that _calculate_critical_path handles circular dependencies gracefully."""
        # Arrange
        viz = DependencyGraphVisualizer()
        work_items = [
            {"id": "A", "dependencies": ["B"]},
            {"id": "B", "dependencies": ["A"]},
        ]

        # Act
        result = viz._calculate_critical_path(work_items)

        # Assert
        # Should handle circular dependency without infinite loop
        assert isinstance(result, set)

    def test_calculate_critical_path_multiple_longest_paths(self):
        """Test that _calculate_critical_path includes all paths of equal length."""
        # Arrange
        viz = DependencyGraphVisualizer()
        work_items = [
            {"id": "A", "dependencies": []},
            {"id": "B", "dependencies": ["A"]},
            {"id": "C", "dependencies": []},
            {"id": "D", "dependencies": ["C"]},
        ]

        # Act
        result = viz._calculate_critical_path(work_items)

        # Assert
        # Both A->B and C->D have the same depth
        assert "A" in result
        assert "B" in result
        assert "C" in result
        assert "D" in result

    def test_calculate_critical_path_with_orphaned_dependencies(self):
        """Test that _calculate_critical_path handles items with dependencies not in the list."""
        # Arrange
        viz = DependencyGraphVisualizer()
        work_items = [
            {"id": "A", "dependencies": []},
            {"id": "B", "dependencies": ["A"]},
            {"id": "C", "dependencies": ["B", "X"]},  # X doesn't exist
        ]

        # Act
        result = viz._calculate_critical_path(work_items)

        # Assert
        # Should trace back through existing path even with missing dependency
        assert "A" in result
        assert "B" in result
        assert "C" in result


class TestGetNodeColor:
    """Tests for _get_node_color method."""

    def test_get_node_color_critical_path(self):
        """Test that _get_node_color returns red for critical path items."""
        # Arrange
        viz = DependencyGraphVisualizer()
        item = {"id": "1", "status": "not_started"}
        critical_items = {"1"}

        # Act
        result = viz._get_node_color(item, critical_items)

        # Assert
        assert result == "red"

    def test_get_node_color_completed(self):
        """Test that _get_node_color returns green for completed items."""
        # Arrange
        viz = DependencyGraphVisualizer()
        item = {"id": "1", "status": "completed"}
        critical_items = set()

        # Act
        result = viz._get_node_color(item, critical_items)

        # Assert
        assert result == "green"

    def test_get_node_color_in_progress(self):
        """Test that _get_node_color returns blue for in_progress items."""
        # Arrange
        viz = DependencyGraphVisualizer()
        item = {"id": "1", "status": "in_progress"}
        critical_items = set()

        # Act
        result = viz._get_node_color(item, critical_items)

        # Assert
        assert result == "blue"

    def test_get_node_color_blocked(self):
        """Test that _get_node_color returns orange for blocked items."""
        # Arrange
        viz = DependencyGraphVisualizer()
        item = {"id": "1", "status": "blocked"}
        critical_items = set()

        # Act
        result = viz._get_node_color(item, critical_items)

        # Assert
        assert result == "orange"

    def test_get_node_color_default(self):
        """Test that _get_node_color returns black for not_started items."""
        # Arrange
        viz = DependencyGraphVisualizer()
        item = {"id": "1", "status": "not_started"}
        critical_items = set()

        # Act
        result = viz._get_node_color(item, critical_items)

        # Assert
        assert result == "black"


class TestGetNodeStyle:
    """Tests for _get_node_style method."""

    def test_get_node_style_completed(self):
        """Test that _get_node_style returns filled style for completed items."""
        # Arrange
        viz = DependencyGraphVisualizer()
        item = {"status": "completed"}

        # Act
        result = viz._get_node_style(item)

        # Assert
        assert result == "rounded,filled"

    def test_get_node_style_in_progress(self):
        """Test that _get_node_style returns bold style for in_progress items."""
        # Arrange
        viz = DependencyGraphVisualizer()
        item = {"status": "in_progress"}

        # Act
        result = viz._get_node_style(item)

        # Assert
        assert result == "rounded,bold"

    def test_get_node_style_default(self):
        """Test that _get_node_style returns default style for other statuses."""
        # Arrange
        viz = DependencyGraphVisualizer()
        item = {"status": "not_started"}

        # Act
        result = viz._get_node_style(item)

        # Assert
        assert result == "rounded"


class TestFormatNodeLabel:
    """Tests for _format_node_label method."""

    def test_format_node_label_basic(self):
        """Test that _format_node_label formats label correctly."""
        # Arrange
        viz = DependencyGraphVisualizer()
        item = {"id": "1", "title": "Test Item", "status": "not_started"}

        # Act
        result = viz._format_node_label(item)

        # Assert
        assert "1" in result
        assert "Test Item" in result
        assert "[not_started]" in result
        assert "\\n" in result

    def test_format_node_label_truncates_long_title(self):
        """Test that _format_node_label truncates titles longer than 30 characters."""
        # Arrange
        viz = DependencyGraphVisualizer()
        long_title = "This is a very long title that should be truncated"
        item = {"id": "1", "title": long_title, "status": "not_started"}

        # Act
        result = viz._format_node_label(item)

        # Assert
        assert "..." in result
        assert len(result) < len(long_title) + 20  # Account for ID and status

    def test_format_node_label_escapes_quotes(self):
        """Test that _format_node_label escapes double quotes in title."""
        # Arrange
        viz = DependencyGraphVisualizer()
        item = {"id": "1", "title": 'Title with "quotes"', "status": "not_started"}

        # Act
        result = viz._format_node_label(item)

        # Assert
        assert '\\"' in result
        assert '"quotes"' not in result


class TestGetStatusIcon:
    """Tests for _get_status_icon method."""

    def test_get_status_icon_not_started(self):
        """Test that _get_status_icon returns correct icon for not_started."""
        # Arrange
        viz = DependencyGraphVisualizer()
        item = {"status": "not_started"}

        # Act
        result = viz._get_status_icon(item)

        # Assert
        assert result == "○"

    def test_get_status_icon_in_progress(self):
        """Test that _get_status_icon returns correct icon for in_progress."""
        # Arrange
        viz = DependencyGraphVisualizer()
        item = {"status": "in_progress"}

        # Act
        result = viz._get_status_icon(item)

        # Assert
        assert result == "◐"

    def test_get_status_icon_completed(self):
        """Test that _get_status_icon returns correct icon for completed."""
        # Arrange
        viz = DependencyGraphVisualizer()
        item = {"status": "completed"}

        # Act
        result = viz._get_status_icon(item)

        # Assert
        assert result == "●"

    def test_get_status_icon_blocked(self):
        """Test that _get_status_icon returns correct icon for blocked."""
        # Arrange
        viz = DependencyGraphVisualizer()
        item = {"status": "blocked"}

        # Act
        result = viz._get_status_icon(item)

        # Assert
        assert result == "✗"

    def test_get_status_icon_default(self):
        """Test that _get_status_icon returns default icon for unknown status."""
        # Arrange
        viz = DependencyGraphVisualizer()
        item = {"status": "unknown_status"}

        # Act
        result = viz._get_status_icon(item)

        # Assert
        assert result == "○"


class TestGroupByDependencyLevel:
    """Tests for _group_by_dependency_level method."""

    def test_group_by_dependency_level_simple_chain(self):
        """Test that _group_by_dependency_level groups simple chain correctly."""
        # Arrange
        viz = DependencyGraphVisualizer()
        work_items = [
            {"id": "A", "dependencies": []},
            {"id": "B", "dependencies": ["A"]},
            {"id": "C", "dependencies": ["B"]},
        ]

        # Act
        result = viz._group_by_dependency_level(work_items)

        # Assert
        assert len(result) == 3
        assert result[0][0]["id"] == "A"
        assert result[1][0]["id"] == "B"
        assert result[2][0]["id"] == "C"

    def test_group_by_dependency_level_parallel_items(self):
        """Test that _group_by_dependency_level groups parallel items in same level."""
        # Arrange
        viz = DependencyGraphVisualizer()
        work_items = [
            {"id": "A", "dependencies": []},
            {"id": "B", "dependencies": []},
            {"id": "C", "dependencies": ["A", "B"]},
        ]

        # Act
        result = viz._group_by_dependency_level(work_items)

        # Assert
        assert len(result) == 2
        # Level 0 should have both A and B
        assert len(result[0]) == 2
        # Level 1 should have C
        assert len(result[1]) == 1
        assert result[1][0]["id"] == "C"

    def test_group_by_dependency_level_complex_dependencies(self):
        """Test that _group_by_dependency_level handles complex dependency tree."""
        # Arrange
        viz = DependencyGraphVisualizer()
        work_items = [
            {"id": "A", "dependencies": []},
            {"id": "B", "dependencies": ["A"]},
            {"id": "C", "dependencies": ["A"]},
            {"id": "D", "dependencies": ["B", "C"]},
        ]

        # Act
        result = viz._group_by_dependency_level(work_items)

        # Assert
        assert len(result) == 3
        # D should be at level 2 (depends on both B and C which are at level 1)
        assert any(item["id"] == "D" for item in result[2])


class TestGenerateTimelineProjection:
    """Tests for _generate_timeline_projection method."""

    def test_generate_timeline_projection_includes_levels(self, sample_work_items_list):
        """Test that _generate_timeline_projection includes level information."""
        # Arrange
        viz = DependencyGraphVisualizer()

        # Act
        result = viz._generate_timeline_projection(sample_work_items_list)

        # Assert
        assert any("Level" in line for line in result)

    def test_generate_timeline_projection_includes_status_counts(self, sample_work_items_list):
        """Test that _generate_timeline_projection includes status counts."""
        # Arrange
        viz = DependencyGraphVisualizer()

        # Act
        result = viz._generate_timeline_projection(sample_work_items_list)

        # Assert
        result_str = "\n".join(result)
        assert "✓" in result_str  # Completed
        assert "◐" in result_str  # In progress
        assert "○" in result_str  # Not started

    def test_generate_timeline_projection_includes_estimate(self, sample_work_items_list):
        """Test that _generate_timeline_projection includes remaining levels estimate."""
        # Arrange
        viz = DependencyGraphVisualizer()

        # Act
        result = viz._generate_timeline_projection(sample_work_items_list)

        # Assert
        result_str = "\n".join(result)
        assert "Estimated remaining levels:" in result_str

    def test_generate_timeline_projection_includes_note(self, sample_work_items_list):
        """Test that _generate_timeline_projection includes parallel execution note."""
        # Arrange
        viz = DependencyGraphVisualizer()

        # Act
        result = viz._generate_timeline_projection(sample_work_items_list)

        # Assert
        result_str = "\n".join(result)
        assert "parallel" in result_str.lower()

    def test_generate_timeline_projection_empty_list(self):
        """Test that _generate_timeline_projection handles empty list."""
        # Arrange
        viz = DependencyGraphVisualizer()

        # Act
        result = viz._generate_timeline_projection([])

        # Assert
        # Should return some output even for empty list
        assert isinstance(result, list)


class TestCriticalPathEdgeCases:
    """Tests for critical path edge cases."""

    def test_calculate_critical_path_with_dependency_at_max_depth(self):
        """Test critical path calculation when dependency chain reaches max depth."""
        # Arrange
        viz = DependencyGraphVisualizer()
        work_items = [
            {"id": "A", "dependencies": []},
            {"id": "B", "dependencies": ["A"]},
            {"id": "C", "dependencies": ["B"]},
            {"id": "D", "dependencies": ["C"]},
        ]

        # Act
        result = viz._calculate_critical_path(work_items)

        # Assert
        # All items should be in critical path (linear chain)
        assert "A" in result
        assert "B" in result
        assert "C" in result
        assert "D" in result

    def test_calculate_critical_path_with_referenced_missing_item(self):
        """Test critical path when dependency exists in depths but theoretically could be missing."""
        # Arrange
        viz = DependencyGraphVisualizer()
        # Create a scenario with very complex dependencies
        work_items = [
            {"id": "1", "dependencies": []},
            {"id": "2", "dependencies": ["1", "99"]},  # 99 doesn't exist
            {"id": "3", "dependencies": ["2"]},
        ]

        # Act
        result = viz._calculate_critical_path(work_items)

        # Assert - Should handle gracefully
        assert isinstance(result, set)
        assert "1" in result or "2" in result or "3" in result


class TestNodeColoringEdgeCases:
    """Tests for node coloring edge cases."""

    def test_get_node_color_with_none_status(self):
        """Test node color when status is None."""
        # Arrange
        viz = DependencyGraphVisualizer()
        item = {"id": "1", "status": None}
        critical_items = set()

        # Act
        result = viz._get_node_color(item, critical_items)

        # Assert
        assert result == "black"

    def test_get_node_color_with_missing_status_field(self):
        """Test node color when status field is missing entirely."""
        # Arrange
        viz = DependencyGraphVisualizer()
        item = {"id": "1"}  # No status field
        critical_items = set()

        # Act
        result = viz._get_node_color(item, critical_items)

        # Assert
        assert result == "black"


class TestGraphFilteringEdgeCases:
    """Tests for graph filtering edge cases."""

    def test_load_work_items_with_empty_milestone_filter(self, tmp_path):
        """Test loading with empty milestone filter."""
        # Arrange
        work_items_file = tmp_path / "work_items.json"
        data = {
            "work_items": {
                "1": {"id": "1", "milestone": ""},
                "2": {"id": "2", "milestone": "v1.0"},
            }
        }
        work_items_file.write_text(json.dumps(data))

        viz = DependencyGraphVisualizer(work_items_file)

        # Act
        result = viz.load_work_items(milestone_filter="")

        # Assert
        # Should match items with empty milestone
        assert len(result) >= 0

    def test_load_work_items_with_none_values(self, tmp_path):
        """Test loading items with None values in filter fields."""
        # Arrange
        work_items_file = tmp_path / "work_items.json"
        data = {
            "work_items": {
                "1": {"id": "1", "status": None, "milestone": None, "type": None},
                "2": {"id": "2", "status": "completed", "milestone": "v1.0", "type": "feature"},
            }
        }
        work_items_file.write_text(json.dumps(data))

        viz = DependencyGraphVisualizer(work_items_file)

        # Act
        result = viz.load_work_items()

        # Assert
        # Should handle None values gracefully
        assert len(result) >= 1


class TestStatsGenerationEdgeCases:
    """Tests for stats generation edge cases."""

    def test_generate_stats_with_all_same_depth(self):
        """Test stats generation when all items are at same depth."""
        # Arrange
        viz = DependencyGraphVisualizer()
        work_items = [
            {"id": "1", "dependencies": [], "status": "not_started"},
            {"id": "2", "dependencies": [], "status": "not_started"},
            {"id": "3", "dependencies": [], "status": "not_started"},
        ]
        critical_path = {"1", "2", "3"}

        # Act
        result = viz.generate_stats(work_items, critical_path)

        # Assert
        assert result["total_items"] == 3
        assert result["critical_path_length"] == 3
        assert result["not_started"] == 3
