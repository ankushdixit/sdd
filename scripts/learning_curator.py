#!/usr/bin/env python3
"""
Learning curation script

Curates and organizes accumulated learnings:
1. Loads raw learnings from session summaries
2. Categorizes learnings
3. Merges similar/duplicate learnings
4. Archives obsolete learnings
5. Generates learning summary reports
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path


class LearningsCurator:
    """Curates project learnings"""

    def __init__(self, project_root: Path = None):
        if project_root is None:
            project_root = Path.cwd()
        self.project_root = project_root
        self.session_dir = project_root / ".session"
        self.learnings_path = self.session_dir / "tracking" / "learnings.json"

    def curate(self, dry_run: bool = False) -> None:
        """Curate learnings"""
        print("\n=== Learning Curation ===\n")

        # Load existing learnings
        learnings = self._load_learnings()

        # Statistics
        initial_count = self._count_all_learnings(learnings)
        print(f"Initial learnings: {initial_count}\n")

        # Categorize uncategorized learnings
        categorized = self._categorize_learnings(learnings)
        print(f"✓ Categorized {categorized} learnings")

        # Merge similar learnings
        merged = self._merge_similar_learnings(learnings)
        print(f"✓ Merged {merged} duplicate learnings")

        # Archive old learnings
        archived = self._archive_old_learnings(learnings)
        print(f"✓ Archived {archived} old learnings")

        # Update metadata
        learnings["last_curated"] = datetime.now().isoformat()
        learnings["curator"] = "session_curator"

        final_count = self._count_all_learnings(learnings)

        print(f"\nFinal learnings: {final_count}\n")

        if not dry_run:
            self._save_json(self.learnings_path, learnings)
            print("✓ Learnings saved\n")
        else:
            print("Dry run - no changes saved\n")

    def _load_learnings(self) -> dict:
        """Load learnings file"""
        if self.learnings_path.exists():
            return self._load_json(self.learnings_path)
        else:
            # Create default structure
            return {
                "last_curated": None,
                "curator": "session_curator",
                "categories": {
                    "architecture_patterns": [],
                    "gotchas": [],
                    "best_practices": [],
                    "technical_debt": [],
                    "performance_insights": [],
                },
                "archived": [],
            }

    def _count_all_learnings(self, learnings: dict) -> int:
        """Count all learnings"""
        count = 0
        categories = learnings.get("categories", {})

        for category in categories.values():
            count += len(category)

        count += len(learnings.get("archived", []))

        return count

    def _categorize_learnings(self, learnings: dict) -> int:
        """Categorize uncategorized learnings using AI-powered analysis"""
        categorized_count = 0

        # Extract learnings from session summaries
        new_learnings = self._extract_learnings_from_sessions()

        for learning in new_learnings:
            # Use AI-powered categorization (rule-based with keyword analysis)
            category = self._auto_categorize_learning(learning)

            # Add to appropriate category
            categories = learnings.setdefault("categories", {})
            if category not in categories:
                categories[category] = []

            # Check if already exists
            if not self._learning_exists(categories[category], learning):
                categories[category].append(learning)
                categorized_count += 1

        return categorized_count

    def _extract_learnings_from_sessions(self) -> list[dict]:
        """Extract learnings from session summary files"""
        learnings = []
        summaries_dir = self.session_dir / "summaries"

        if not summaries_dir.exists():
            return learnings

        # Look for session summary files
        for summary_file in summaries_dir.glob("session_*.json"):
            try:
                summary_data = self._load_json(summary_file)

                # Extract learnings from various fields
                session_id = summary_file.stem.replace("session_", "")

                # Check for explicit learnings field
                if "learnings" in summary_data:
                    for learning_text in summary_data["learnings"]:
                        learnings.append(
                            {
                                "content": learning_text,
                                "learned_in": session_id,
                                "timestamp": summary_data.get("timestamp", ""),
                            }
                        )

                # Extract from challenges as potential gotchas
                if "challenges_encountered" in summary_data:
                    for challenge in summary_data["challenges_encountered"]:
                        learnings.append(
                            {
                                "content": f"Challenge: {challenge}",
                                "learned_in": session_id,
                                "timestamp": summary_data.get("timestamp", ""),
                                "suggested_type": "gotcha",
                            }
                        )

            except Exception:
                # Skip invalid summary files
                continue

        return learnings

    def _auto_categorize_learning(self, learning: dict) -> str:
        """Automatically categorize a learning using keyword analysis"""
        content = learning.get("content", "").lower()

        # Check for suggested type first
        if "suggested_type" in learning:
            suggested = learning["suggested_type"]
            if suggested in [
                "architecture_pattern",
                "gotcha",
                "best_practice",
                "technical_debt",
                "performance_insight",
            ]:
                return f"{suggested}s"  # Pluralize

        # Keyword-based categorization
        architecture_keywords = [
            "architecture",
            "design",
            "pattern",
            "structure",
            "component",
            "module",
            "layer",
            "service",
        ]
        gotcha_keywords = [
            "gotcha",
            "trap",
            "pitfall",
            "mistake",
            "error",
            "bug",
            "issue",
            "problem",
            "challenge",
            "warning",
        ]
        practice_keywords = [
            "best practice",
            "convention",
            "standard",
            "guideline",
            "recommendation",
            "should",
            "always",
            "never",
        ]
        debt_keywords = [
            "technical debt",
            "refactor",
            "cleanup",
            "legacy",
            "deprecated",
            "workaround",
            "hack",
            "todo",
        ]
        performance_keywords = [
            "performance",
            "optimization",
            "speed",
            "slow",
            "fast",
            "efficient",
            "memory",
            "cpu",
            "benchmark",
        ]

        # Score each category
        scores = {
            "architecture_patterns": self._keyword_score(
                content, architecture_keywords
            ),
            "gotchas": self._keyword_score(content, gotcha_keywords),
            "best_practices": self._keyword_score(content, practice_keywords),
            "technical_debt": self._keyword_score(content, debt_keywords),
            "performance_insights": self._keyword_score(content, performance_keywords),
        }

        # Return category with highest score, default to best_practices
        max_category = max(scores.items(), key=lambda x: x[1])
        return max_category[0] if max_category[1] > 0 else "best_practices"

    def _keyword_score(self, text: str, keywords: list[str]) -> int:
        """Calculate keyword match score"""
        score = 0
        for keyword in keywords:
            if keyword in text:
                score += 1
        return score

    def _learning_exists(self, category_learnings: list, new_learning: dict) -> bool:
        """Check if a similar learning already exists"""
        for existing in category_learnings:
            if self._are_similar(existing, new_learning):
                return True
        return False

    def _merge_similar_learnings(self, learnings: dict) -> int:
        """Merge similar learnings"""
        merged_count = 0
        categories = learnings.get("categories", {})

        for category_name, category_learnings in categories.items():
            # Group by similarity (simple keyword matching for now)
            to_remove = []

            for i, learning_a in enumerate(category_learnings):
                if i in to_remove:
                    continue

                for j in range(i + 1, len(category_learnings)):
                    if j in to_remove:
                        continue

                    learning_b = category_learnings[j]

                    # Simple similarity check
                    if self._are_similar(learning_a, learning_b):
                        # Merge into first learning
                        self._merge_learning(learning_a, learning_b)
                        to_remove.append(j)
                        merged_count += 1

            # Remove merged learnings
            for idx in sorted(to_remove, reverse=True):
                category_learnings.pop(idx)

        return merged_count

    def _are_similar(self, learning_a: dict, learning_b: dict) -> bool:
        """Check if two learnings are similar using enhanced semantic comparison"""
        content_a = learning_a.get("content", "").lower()
        content_b = learning_b.get("content", "").lower()

        # Exact match
        if content_a == content_b:
            return True

        # Remove common stopwords for better comparison
        stopwords = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "should",
            "could",
            "may",
            "might",
        }

        words_a = set(w for w in content_a.split() if w not in stopwords)
        words_b = set(w for w in content_b.split() if w not in stopwords)

        if len(words_a) == 0 or len(words_b) == 0:
            return False

        # Jaccard similarity (overlap coefficient)
        overlap = len(words_a & words_b)
        total = len(words_a | words_b)
        jaccard = overlap / total if total > 0 else 0

        # Containment similarity (one learning contains the other)
        min_size = min(len(words_a), len(words_b))
        containment = overlap / min_size if min_size > 0 else 0

        # Consider similar if high Jaccard OR high containment
        return jaccard > 0.6 or containment > 0.8

    def _merge_learning(self, target: dict, source: dict) -> None:
        """Merge source learning into target"""
        # Merge applies_to
        target_applies = set(target.get("applies_to", []))
        source_applies = set(source.get("applies_to", []))
        target["applies_to"] = list(target_applies | source_applies)

        # Add note about merge
        if "merged_from" not in target:
            target["merged_from"] = []
        target["merged_from"].append(source.get("learned_in", "unknown"))

    def _archive_old_learnings(
        self, learnings: dict, max_age_sessions: int = 50
    ) -> int:
        """Archive old, unreferenced learnings"""
        archived_count = 0
        categories = learnings.get("categories", {})

        # Get current session number from tracking
        current_session = self._get_current_session_number()

        for category_name, category_learnings in categories.items():
            to_archive = []

            for i, learning in enumerate(category_learnings):
                # Extract session number from learned_in field
                session_num = self._extract_session_number(
                    learning.get("learned_in", "")
                )

                # Archive if too old
                if session_num and current_session - session_num > max_age_sessions:
                    to_archive.append(i)

            # Move to archive
            archived = learnings.setdefault("archived", [])
            for idx in sorted(to_archive, reverse=True):
                learning = category_learnings.pop(idx)
                learning["archived_from"] = category_name
                learning["archived_at"] = datetime.now().isoformat()
                archived.append(learning)
                archived_count += 1

        return archived_count

    def _get_current_session_number(self) -> int:
        """Get the current session number from work items"""
        try:
            work_items_path = self.session_dir / "tracking" / "work_items.json"
            if work_items_path.exists():
                data = self._load_json(work_items_path)
                # Find max session number across all work items
                max_session = 0
                for item in data.get("work_items", {}).values():
                    sessions = item.get("sessions", [])
                    if sessions:
                        max_session = max(max_session, max(sessions))
                return max_session
        except Exception:
            pass
        return 0

    def _extract_session_number(self, session_id: str) -> int:
        """Extract numeric session number from session ID"""
        try:
            # Handle formats like "session_001", "001", "1", etc.
            match = re.search(r"\d+", session_id)
            if match:
                return int(match.group())
        except Exception:
            pass
        return 0

    def auto_curate_if_needed(self) -> bool:
        """Auto-curate based on configuration and last curation time"""
        config = self._load_curation_config()

        if not config.get("auto_curate_enabled", False):
            return False

        learnings = self._load_learnings()
        last_curated = learnings.get("last_curated")

        if not last_curated:
            # Never curated, do it now
            print("Auto-curating (first time)...\n")
            self.curate(dry_run=False)
            return True

        # Check frequency
        last_date = datetime.fromisoformat(last_curated)
        days_since = (datetime.now() - last_date).days

        frequency_days = config.get("auto_curate_frequency_days", 7)

        if days_since >= frequency_days:
            print(f"Auto-curating (last curated {days_since} days ago)...\n")
            self.curate(dry_run=False)
            return True

        return False

    def _load_curation_config(self) -> dict:
        """Load curation configuration from .sessionrc.json"""
        config_path = self.project_root / ".sessionrc.json"

        if config_path.exists():
            try:
                config = self._load_json(config_path)
                return config.get("learning_curation", {})
            except Exception:
                pass

        # Return defaults
        return {
            "auto_curate_enabled": False,
            "auto_curate_frequency_days": 7,
            "similarity_threshold": 0.6,
            "archive_after_sessions": 50,
        }

    def generate_report(self) -> None:
        """Generate learning summary report"""
        print("\n=== Learning Summary Report ===\n")

        learnings = self._load_learnings()

        # Create table
        print("Learnings by Category:")
        print("-" * 40)

        categories = learnings.get("categories", {})
        total = 0

        for category_name, category_learnings in categories.items():
            count = len(category_learnings)
            total += count
            formatted_name = category_name.replace("_", " ").title()
            print(f"{formatted_name:<30} {count:>5}")

        # Add archived
        archived_count = len(learnings.get("archived", []))
        if archived_count > 0:
            print(f"{'Archived':<30} {archived_count:>5}")

        # Add total
        print("-" * 40)
        print(f"{'Total':<30} {total:>5}")
        print()

        # Show last curated
        last_curated = learnings.get("last_curated")
        if last_curated:
            print(f"Last curated: {last_curated}\n")
        else:
            print("Never curated\n")

    def show_learnings(self, category: str = None) -> None:
        """Show learnings by category"""
        learnings = self._load_learnings()
        categories = learnings.get("categories", {})

        if category:
            # Show specific category
            if category not in categories:
                print(f"Category not found: {category}\n")
                return

            print(f"\n{category.replace('_', ' ').title()}\n")
            print("=" * 50)

            for i, learning in enumerate(categories[category], 1):
                print(f"\n{i}. {learning.get('content', 'N/A')}")
                if "learned_in" in learning:
                    print(f"   Learned in: {learning['learned_in']}")
                if "timestamp" in learning:
                    print(f"   Date: {learning['timestamp']}")
        else:
            # Show all categories
            for category_name, category_learnings in categories.items():
                if not category_learnings:
                    continue

                print(f"\n{category_name.replace('_', ' ').title()}")
                print(f"Count: {len(category_learnings)}\n")

                # Show first 3
                for learning in category_learnings[:3]:
                    print(f"  • {learning.get('content', 'N/A')}")

                if len(category_learnings) > 3:
                    print(f"  ... and {len(category_learnings) - 3} more")

                print()

    def _load_json(self, file_path: Path) -> dict:
        """Load JSON file"""
        with open(file_path) as f:
            return json.load(f)

    def _save_json(self, file_path: Path, data: dict, indent: int = 2) -> None:
        """Save data to JSON file with atomic write"""
        # Write to temp file first
        temp_path = file_path.with_suffix(".tmp")

        with open(temp_path, "w") as f:
            json.dump(data, f, indent=indent, default=str)

        # Atomic rename
        temp_path.replace(file_path)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Curate project learnings")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show changes without saving"
    )
    parser.add_argument("--report", action="store_true", help="Generate summary report")
    parser.add_argument("--show", type=str, help="Show learnings by category")
    parser.add_argument(
        "--recategorize-all", action="store_true", help="Recategorize all learnings"
    )

    args = parser.parse_args()

    project_root = Path.cwd()
    session_dir = project_root / ".session"

    if not session_dir.exists():
        print("Error: .session directory not found", file=sys.stderr)
        print("Run /session-start to initialize the project first\n")
        sys.exit(1)

    curator = LearningsCurator(project_root)

    if args.report:
        curator.generate_report()
    elif args.show:
        curator.show_learnings(category=args.show)
    else:
        curator.curate(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
