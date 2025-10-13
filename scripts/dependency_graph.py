#!/usr/bin/env python3
"""
Dependency graph visualization for work items

Generates visual dependency graphs with critical path analysis and work item timeline projection.
Supports DOT format, SVG, and ASCII art output.
"""

import json
from pathlib import Path
from typing import Optional


class DependencyGraphVisualizer:
    """Visualizes work item dependency graphs"""

    def __init__(self, work_items_file: Path = None):
        """
        Initialize visualizer.

        Args:
            work_items_file: Path to work_items.json (default: .session/tracking/work_items.json)
        """
        if work_items_file is None:
            work_items_file = Path(".session/tracking/work_items.json")
        self.work_items_file = work_items_file

    def load_work_items(self):
        """Load work items from JSON file."""
        if not self.work_items_file.exists():
            return []

        with open(self.work_items_file) as f:
            data = json.load(f)

        return list(data.get("work_items", {}).values())

    def generate_dot(self, include_completed: bool = False) -> str:
        """Generate DOT format graph

        Args:
            include_completed: Include completed work items in the graph

        Returns:
            DOT format string
        """
        work_items = self.load_work_items()

        if not include_completed:
            work_items = [
                item for item in work_items if item.get("status") != "completed"
            ]

        # Calculate critical path
        critical_items = self._calculate_critical_path(work_items)

        # Start DOT graph
        lines = [
            "digraph WorkItems {",
            "  rankdir=TB;",
            "  node [shape=box, style=rounded];",
            "",
        ]

        # Add nodes
        for item in work_items:
            # Determine node styling based on status and critical path
            color = self._get_node_color(item, critical_items)
            style = self._get_node_style(item)

            label = self._format_node_label(item)

            lines.append(
                f'  "{item["id"]}" [label="{label}", color="{color}", style="{style}"];'
            )

        lines.append("")

        # Add edges
        for item in work_items:
            for dep_id in item.get("dependencies", []):
                # Check if dependency exists in filtered items
                if any(wi["id"] == dep_id for wi in work_items):
                    edge_style = (
                        "bold, color=red"
                        if item["id"] in critical_items and dep_id in critical_items
                        else ""
                    )
                    if edge_style:
                        lines.append(f'  "{dep_id}" -> "{item["id"]}" [{edge_style}];')
                    else:
                        lines.append(f'  "{dep_id}" -> "{item["id"]}";')

        lines.append("}")
        return "\n".join(lines)

    def generate_ascii(self, include_completed: bool = False) -> str:
        """Generate ASCII art graph

        Args:
            include_completed: Include completed work items in the graph

        Returns:
            ASCII art string
        """
        work_items = self.load_work_items()

        if not include_completed:
            work_items = [
                item for item in work_items if item.get("status") != "completed"
            ]

        # Calculate critical path
        critical_items = self._calculate_critical_path(work_items)

        # Build dependency tree
        lines = ["Work Item Dependency Graph", "=" * 50, ""]

        # Group items by dependency level
        levels = self._group_by_dependency_level(work_items)

        for level_num, level_items in enumerate(levels):
            lines.append(f"Level {level_num}:")
            for item in level_items:
                status_icon = self._get_status_icon(item)
                critical_marker = (
                    " [CRITICAL PATH]" if item["id"] in critical_items else ""
                )
                lines.append(
                    f"  {status_icon} {item['id']}: {item['title']}{critical_marker}"
                )

                # Show dependencies
                if item.get("dependencies"):
                    for dep_id in item["dependencies"]:
                        lines.append(f"      └─ depends on: {dep_id}")

            lines.append("")

        # Add timeline projection
        timeline = self._generate_timeline_projection(work_items)
        if timeline:
            lines.append("Timeline Projection:")
            lines.append("-" * 50)
            lines.extend(timeline)

        return "\n".join(lines)

    def generate_svg(
        self, output_path: Optional[Path] = None, include_completed: bool = False
    ) -> Optional[str]:
        """Generate SVG graph using Graphviz

        Args:
            output_path: Optional path to save SVG file
            include_completed: Include completed work items in the graph

        Returns:
            SVG content if output_path is None, otherwise None
        """
        try:
            import graphviz
        except ImportError:
            raise ImportError(
                "graphviz package required for SVG generation. "
                "Install with: pip install graphviz"
            )

        dot_content = self.generate_dot(include_completed=include_completed)

        # Create graphviz graph
        graph = graphviz.Source(dot_content)

        if output_path:
            # Save to file
            graph.render(output_path.with_suffix(""), format="svg", cleanup=True)
            return None
        else:
            # Return SVG content
            return graph.pipe(format="svg").decode("utf-8")

    def _calculate_critical_path(self, work_items: list[dict]) -> set[str]:
        """Calculate critical path through work items

        The critical path is the longest chain of dependencies.

        Args:
            work_items: List of work items to analyze

        Returns:
            Set of work item IDs on the critical path
        """
        # Build dependency graph
        item_dict = {item["id"]: item for item in work_items}

        # Calculate depth for each item
        depths = {}

        def calculate_depth(item_id: str, visited: set[str]) -> int:
            if item_id in depths:
                return depths[item_id]

            if item_id in visited:
                # Circular dependency
                return 0

            if item_id not in item_dict:
                return 0

            item = item_dict[item_id]
            if not item.get("dependencies"):
                depths[item_id] = 0
                return 0

            visited.add(item_id)
            max_depth = 0

            for dep_id in item.get("dependencies", []):
                dep_depth = calculate_depth(dep_id, visited.copy())
                max_depth = max(max_depth, dep_depth + 1)

            depths[item_id] = max_depth
            return max_depth

        # Calculate depths for all items
        for item in work_items:
            calculate_depth(item["id"], set())

        # Find maximum depth
        if not depths:
            return set()

        max_depth = max(depths.values())

        # Trace critical path
        critical_items = set()

        def trace_critical_path(item_id: str, current_depth: int) -> None:
            if current_depth == 0:
                critical_items.add(item_id)
                return

            if item_id not in item_dict:
                return

            item = item_dict[item_id]
            critical_items.add(item_id)

            for dep_id in item.get("dependencies", []):
                if dep_id in depths and depths[dep_id] == current_depth - 1:
                    trace_critical_path(dep_id, current_depth - 1)

        # Find items at max depth
        for item_id, depth in depths.items():
            if depth == max_depth:
                trace_critical_path(item_id, max_depth)

        return critical_items

    def _get_node_color(self, item: dict, critical_items: set[str]) -> str:
        """Get node color based on status and critical path"""
        if item["id"] in critical_items:
            return "red"
        elif item.get("status") == "completed":
            return "green"
        elif item.get("status") == "in_progress":
            return "blue"
        elif item.get("status") == "blocked":
            return "orange"
        else:
            return "black"

    def _get_node_style(self, item: dict) -> str:
        """Get node style based on status"""
        if item.get("status") == "completed":
            return "rounded,filled"
        elif item.get("status") == "in_progress":
            return "rounded,bold"
        else:
            return "rounded"

    def _format_node_label(self, item: dict) -> str:
        """Format node label with work item details"""
        # Escape special characters for DOT
        title = item["title"].replace('"', '\\"')

        # Truncate long titles
        if len(title) > 30:
            title = title[:27] + "..."

        status = item.get("status", "not_started")
        return f"{item['id']}\\n{title}\\n[{status}]"

    def _get_status_icon(self, item: dict) -> str:
        """Get ASCII icon for work item status"""
        icons = {
            "not_started": "○",
            "in_progress": "◐",
            "completed": "●",
            "blocked": "✗",
        }
        return icons.get(item.get("status"), "○")

    def _group_by_dependency_level(self, work_items: list[dict]) -> list[list[dict]]:
        """Group work items by dependency level

        Level 0 = no dependencies
        Level 1 = depends only on level 0
        etc.
        """
        item_dict = {item["id"]: item for item in work_items}
        levels: list[list[dict]] = []
        assigned = set()

        def get_item_level(item: dict) -> int:
            if not item.get("dependencies"):
                return 0

            max_dep_level = -1
            for dep_id in item.get("dependencies", []):
                if dep_id in item_dict:
                    dep_item = item_dict[dep_id]
                    dep_level = get_item_level(dep_item)
                    max_dep_level = max(max_dep_level, dep_level)

            return max_dep_level + 1

        # Assign items to levels
        for item in work_items:
            level = get_item_level(item)

            # Ensure we have enough levels
            while len(levels) <= level:
                levels.append([])

            levels[level].append(item)
            assigned.add(item["id"])

        return levels

    def _generate_timeline_projection(self, work_items: list[dict]) -> list[str]:
        """Generate timeline projection based on work items

        Note: This is a simplified projection assuming each item takes 1 time unit.
        In practice, you'd use time_estimate from metadata.
        """
        lines = []

        # Group by dependency level
        levels = self._group_by_dependency_level(work_items)

        total_time = 0
        for level_num, level_items in enumerate(levels):
            # Assume each level can be done in parallel
            # Time for this level is the max time of any item in the level
            # For now, assume each item takes 1 unit
            level_time = 1 if level_items else 0

            if level_items:
                completed_count = sum(
                    1 for item in level_items if item.get("status") == "completed"
                )
                in_progress_count = sum(
                    1 for item in level_items if item.get("status") == "in_progress"
                )
                not_started_count = sum(
                    1 for item in level_items if item.get("status") == "not_started"
                )

                lines.append(
                    f"  Level {level_num}: {len(level_items)} items "
                    f"(✓{completed_count} ◐{in_progress_count} ○{not_started_count})"
                )

                total_time += level_time

        lines.append("")
        lines.append(f"Estimated remaining levels: {len(levels)}")
        lines.append(
            "Note: Timeline assumes items can be completed in parallel within each level"
        )

        return lines


def main():
    """CLI entry point for graph generation."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Generate work item dependency graphs")
    parser.add_argument(
        "--format",
        choices=["ascii", "dot", "svg"],
        default="ascii",
        help="Output format",
    )
    parser.add_argument("--output", type=Path, help="Output file path (for svg format)")
    parser.add_argument(
        "--include-completed", action="store_true", help="Include completed work items"
    )
    parser.add_argument(
        "--work-items-file",
        type=Path,
        help="Path to work_items.json (default: .session/tracking/work_items.json)",
    )

    args = parser.parse_args()

    visualizer = DependencyGraphVisualizer(args.work_items_file)

    try:
        if args.format == "ascii":
            output = visualizer.generate_ascii(include_completed=args.include_completed)
            print(output)
        elif args.format == "dot":
            output = visualizer.generate_dot(include_completed=args.include_completed)
            print(output)
        elif args.format == "svg":
            if not args.output:
                print("Error: --output required for SVG format", file=sys.stderr)
                return 1
            visualizer.generate_svg(
                output_path=args.output, include_completed=args.include_completed
            )
            print(f"SVG saved to {args.output}.svg")
    except Exception as e:
        print(f"Error generating graph: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
