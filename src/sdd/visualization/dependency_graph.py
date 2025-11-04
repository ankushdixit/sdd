#!/usr/bin/env python3
"""
Dependency graph visualization for work items

Generates visual dependency graphs with critical path analysis and work item timeline projection.
Supports DOT format, SVG, and ASCII art output.
"""

import argparse
import json
from pathlib import Path
from typing import Optional

from sdd.core.command_runner import CommandRunner
from sdd.core.types import WorkItemStatus


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
        self.runner = CommandRunner(default_timeout=30)

    def load_work_items(
        self,
        status_filter: Optional[str] = None,
        milestone_filter: Optional[str] = None,
        type_filter: Optional[str] = None,
        include_completed: bool = False,
    ) -> list[dict]:
        """Load and filter work items from JSON file.

        Args:
            status_filter: Filter by status (not_started, in_progress, completed, blocked)
            milestone_filter: Filter by milestone name
            type_filter: Filter by work item type
            include_completed: Include completed items (default: False)

        Returns:
            List of filtered work items
        """
        if not self.work_items_file.exists():
            return []

        with open(self.work_items_file) as f:
            data = json.load(f)

        work_items = list(data.get("work_items", {}).values())

        # Apply filters
        if not include_completed:
            work_items = [
                wi for wi in work_items if wi.get("status") != WorkItemStatus.COMPLETED.value
            ]

        if status_filter:
            work_items = [wi for wi in work_items if wi.get("status") == status_filter]

        if milestone_filter:
            work_items = [wi for wi in work_items if wi.get("milestone") == milestone_filter]

        if type_filter:
            work_items = [wi for wi in work_items if wi.get("type") == type_filter]

        return work_items

    def generate_dot(self, work_items: list[dict]) -> str:
        """Generate DOT format graph

        Args:
            work_items: List of work items to include in graph

        Returns:
            DOT format string
        """

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

            lines.append(f'  "{item["id"]}" [label="{label}", color="{color}", style="{style}"];')

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

    def generate_ascii(self, work_items: list[dict]) -> str:
        """Generate ASCII art graph

        Args:
            work_items: List of work items to include in graph

        Returns:
            ASCII art string
        """

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
                critical_marker = " [CRITICAL PATH]" if item["id"] in critical_items else ""
                lines.append(f"  {status_icon} {item['id']}: {item['title']}{critical_marker}")

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

    def generate_svg(self, dot_content: str, output_file: Path) -> bool:
        """Generate SVG from DOT using Graphviz.

        Args:
            dot_content: DOT format string
            output_file: Path to save SVG file

        Returns:
            True if successful, False otherwise
        """
        # Use stdin input via temporary file approach since CommandRunner doesn't support stdin input directly
        import tempfile

        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".dot", delete=False) as f:
                f.write(dot_content)
                temp_file = f.name

            result = self.runner.run(["dot", "-Tsvg", temp_file, "-o", str(output_file)])

            # Clean up temp file
            Path(temp_file).unlink()

            return result.success
        except Exception:
            return False

    def get_bottlenecks(self, work_items: list[dict]) -> list[dict]:
        """Identify bottleneck work items (items that block many others).

        Args:
            work_items: List of work items to analyze

        Returns:
            List of bottleneck info dicts with id, blocks count, and item details
        """
        # Count how many items each work item blocks
        blocking_count = {}
        for wi in work_items:
            blocking_count[wi["id"]] = 0

        for wi in work_items:
            for dep_id in wi.get("dependencies", []):
                if dep_id in blocking_count:
                    blocking_count[dep_id] += 1

        # Return items that block 2+ other items
        bottlenecks = [
            {
                "id": wid,
                "blocks": count,
                "item": next(wi for wi in work_items if wi["id"] == wid),
            }
            for wid, count in blocking_count.items()
            if count >= 2
        ]

        return sorted(bottlenecks, key=lambda x: x["blocks"], reverse=True)

    def get_neighborhood(self, work_items: list[dict], focus_id: str) -> list[dict]:
        """Get work items in neighborhood of focus item (dependencies and dependents).

        Args:
            work_items: List of work items
            focus_id: ID of focus work item

        Returns:
            List of work items in neighborhood
        """
        # Find focus item
        focus_item = next((wi for wi in work_items if wi["id"] == focus_id), None)
        if not focus_item:
            return []

        # Get all dependencies (recursive)
        neighborhood_ids = {focus_id}
        to_check = set(focus_item.get("dependencies", []))

        while to_check:
            dep_id = to_check.pop()
            if dep_id not in neighborhood_ids:
                neighborhood_ids.add(dep_id)
                dep_item = next((wi for wi in work_items if wi["id"] == dep_id), None)
                if dep_item:
                    to_check.update(dep_item.get("dependencies", []))

        # Get all dependents (items that depend on any item in neighborhood)
        for wi in work_items:
            if any(dep_id in neighborhood_ids for dep_id in wi.get("dependencies", [])):
                neighborhood_ids.add(wi["id"])

        return [wi for wi in work_items if wi["id"] in neighborhood_ids]

    def generate_stats(self, work_items: list[dict], critical_path: set[str]) -> dict:
        """Generate graph statistics.

        Args:
            work_items: List of work items
            critical_path: Set of work item IDs on critical path

        Returns:
            Dictionary with statistics
        """
        total = len(work_items)
        completed = len(
            [wi for wi in work_items if wi.get("status") == WorkItemStatus.COMPLETED.value]
        )
        in_progress = len(
            [wi for wi in work_items if wi.get("status") == WorkItemStatus.IN_PROGRESS.value]
        )
        not_started = len(
            [wi for wi in work_items if wi.get("status") == WorkItemStatus.NOT_STARTED.value]
        )

        return {
            "total_items": total,
            "completed": completed,
            "in_progress": in_progress,
            "not_started": not_started,
            "completion_pct": round(completed / total * 100, 1) if total > 0 else 0,
            "critical_path_length": len(critical_path),
            "critical_items": list(critical_path),
        }

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
        elif item.get("status") == WorkItemStatus.COMPLETED.value:
            return "green"
        elif item.get("status") == WorkItemStatus.IN_PROGRESS.value:
            return "blue"
        elif item.get("status") == WorkItemStatus.BLOCKED.value:
            return "orange"
        else:
            return "black"

    def _get_node_style(self, item: dict) -> str:
        """Get node style based on status"""
        if item.get("status") == WorkItemStatus.COMPLETED.value:
            return "rounded,filled"
        elif item.get("status") == WorkItemStatus.IN_PROGRESS.value:
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

        status = item.get("status", WorkItemStatus.NOT_STARTED.value)
        return f"{item['id']}\\n{title}\\n[{status}]"

    def _get_status_icon(self, item: dict) -> str:
        """Get ASCII icon for work item status"""
        icons = {
            WorkItemStatus.NOT_STARTED.value: "○",
            WorkItemStatus.IN_PROGRESS.value: "◐",
            WorkItemStatus.COMPLETED.value: "●",
            WorkItemStatus.BLOCKED.value: "✗",
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
                    1
                    for item in level_items
                    if item.get("status") == WorkItemStatus.COMPLETED.value
                )
                in_progress_count = sum(
                    1
                    for item in level_items
                    if item.get("status") == WorkItemStatus.IN_PROGRESS.value
                )
                not_started_count = sum(
                    1
                    for item in level_items
                    if item.get("status") == WorkItemStatus.NOT_STARTED.value
                )

                lines.append(
                    f"  Level {level_num}: {len(level_items)} items "
                    f"(✓{completed_count} ◐{in_progress_count} ○{not_started_count})"
                )

                total_time += level_time

        lines.append("")
        lines.append(f"Estimated remaining levels: {len(levels)}")
        lines.append("Note: Timeline assumes items can be completed in parallel within each level")

        return lines


def main():
    """CLI entry point for graph generation."""
    import sys

    parser = argparse.ArgumentParser(description="Generate work item dependency graphs")

    # Output format
    parser.add_argument(
        "--format",
        choices=["ascii", "dot", "svg"],
        default="ascii",
        help="Output format (default: ascii)",
    )
    parser.add_argument("--output", help="Output file (for dot/svg formats)")

    # Filters
    parser.add_argument(
        "--status",
        choices=WorkItemStatus.values(),
        help="Filter by status",
    )
    parser.add_argument("--milestone", help="Filter by milestone")
    parser.add_argument("--type", help="Filter by work item type")
    parser.add_argument(
        "--include-completed",
        action="store_true",
        help="Include completed items (default: hide)",
    )

    # Special views
    parser.add_argument("--critical-path", action="store_true", help="Show only critical path")
    parser.add_argument("--bottlenecks", action="store_true", help="Show bottleneck analysis")
    parser.add_argument("--stats", action="store_true", help="Show graph statistics")
    parser.add_argument("--focus", help="Focus on neighborhood of specific work item")

    # Work items file
    parser.add_argument(
        "--work-items-file",
        type=Path,
        help="Path to work_items.json (default: .session/tracking/work_items.json)",
    )

    args = parser.parse_args()

    # Initialize visualizer
    viz = DependencyGraphVisualizer(args.work_items_file)

    # Load work items with filters
    work_items = viz.load_work_items(
        status_filter=args.status,
        milestone_filter=args.milestone,
        type_filter=args.type,
        include_completed=args.include_completed,
    )

    if not work_items:
        print("No work items found matching criteria.")
        return 1

    # Apply special filters
    if args.focus:
        work_items = viz.get_neighborhood(work_items, args.focus)
        if not work_items:
            print(f"Work item '{args.focus}' not found.", file=sys.stderr)
            return 1

    critical_path = viz._calculate_critical_path(work_items)

    if args.critical_path:
        work_items = [wi for wi in work_items if wi["id"] in critical_path]

    # Handle special views
    if args.stats:
        stats = viz.generate_stats(work_items, critical_path)
        print("Graph Statistics:")
        print("=" * 50)
        print(f"Total work items: {stats['total_items']}")
        print(f"Completed: {stats['completed']} ({stats['completion_pct']}%)")
        print(f"In progress: {stats['in_progress']}")
        print(f"Not started: {stats['not_started']}")
        print(f"Critical path length: {stats['critical_path_length']}")
        if stats["critical_items"]:
            print(f"Critical items: {', '.join(stats['critical_items'])}")
        return 0

    if args.bottlenecks:
        bottlenecks = viz.get_bottlenecks(work_items)
        print("Bottleneck Analysis:")
        print("=" * 50)
        if bottlenecks:
            for bn in bottlenecks:
                item = bn["item"]
                print(f"{bn['id']} - {item.get('title', 'N/A')} (blocks {bn['blocks']} items)")
        else:
            print("No bottlenecks found (no items block 2+ other items).")
        return 0

    # Generate graph
    try:
        if args.format == "ascii":
            output = viz.generate_ascii(work_items)
            print(output)

        elif args.format == "dot":
            output = viz.generate_dot(work_items)
            if args.output:
                Path(args.output).write_text(output)
                print(f"DOT graph saved to {args.output}")
            else:
                print(output)

        elif args.format == "svg":
            dot_output = viz.generate_dot(work_items)
            output_file = Path(args.output) if args.output else Path("dependency_graph.svg")
            if viz.generate_svg(dot_output, output_file):
                print(f"SVG graph saved to {output_file}")
            else:
                print(
                    "Error: Graphviz not installed or DOT conversion failed",
                    file=sys.stderr,
                )
                return 1

    except Exception as e:
        print(f"Error generating graph: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
