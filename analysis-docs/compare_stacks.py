#!/usr/bin/env python3
"""
Template Stack Comparison Tool

Compares files across saas_t3, dashboard_refine, and fullstack_nextjs templates
to identify content differences and ensure consistency.

Usage:
    # Generate CSV report of all files
    python compare_stacks.py --output report.csv

    # Generate markdown report
    python compare_stacks.py --output report.md

    # Generate markdown with detailed diffs
    python compare_stacks.py --output report.md --show-diffs

    # Compare a single file across all stacks (quick check)
    python compare_stacks.py --file tier-4-production/k6/load-test.js

    # Compare single file and save to file
    python compare_stacks.py --file tier-3-comprehensive/.axe-config.json --output axe.md
"""

import argparse
import csv
import difflib
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass
from enum import Enum


class DiffSeverity(Enum):
    """Severity levels for file differences"""
    CRITICAL = "🔴 CRITICAL"  # Must be identical (workflows, quality configs)
    HIGH = "🟡 HIGH"  # Should be very similar (package.json scripts)
    MEDIUM = "🟠 MEDIUM"  # May differ but check (ESLint rules)
    LOW = "🟢 LOW"  # Expected to differ (base code, tests)
    INFO = "ℹ️ INFO"  # Informational only


@dataclass
class FileDiff:
    """Represents a difference between files"""
    relative_path: str
    severity: DiffSeverity
    stacks_present: Set[str]
    differences: Dict[Tuple[str, str], List[str]]  # (stack1, stack2) -> diff lines
    reason: str


@dataclass
class FileComparison:
    """Represents a complete comparison of a file across stacks"""
    relative_path: str
    stacks_present: Set[str]
    file_paths: Dict[str, Path]  # stack -> full path
    is_identical: bool
    severity: DiffSeverity
    differences: Dict[Tuple[str, str], List[str]]
    reason: str


class StackComparator:
    """Compares template files across multiple stacks"""

    TEMPLATES_DIR = Path("/Users/ankushdixit/Projects/solokit/src/solokit/templates")
    STACKS = ["saas_t3", "dashboard_refine", "fullstack_nextjs"]

    # Files that MUST be identical
    CRITICAL_FILES = {
        # CI/CD workflows
        ".github/workflows/build.yml",
        ".github/workflows/quality-check.yml",
        ".github/workflows/security.yml",
        ".github/workflows/test.yml",
        ".github/workflows/a11y.yml",

        # Quality configs - Tier 1
        "jest.config.ts",
        "jest.setup.ts",
        ".prettierignore",
        ".prettierrc",

        # Quality configs - Tier 2
        ".git-secrets",
        ".husky/pre-commit",
        ".lintstagedrc.json",
        ".npmrc",

        # Quality configs - Tier 3
        ".axe-config.json",
        ".jscpd.json",
        "playwright.config.ts",
        "stryker.conf.json",
        "type-coverage.json",
        "jest.config.ts.tier3.template",

        # Quality configs - Tier 4
        ".lighthouserc.json",
        "jest.config.ts.tier4.template",

        # Sentry configs (structure should match)
        "sentry.client.config.ts",
        "sentry.edge.config.ts",
        "sentry.server.config.ts",
        "instrumentation.ts",
    }

    # Files that should have similar structure but may differ
    HIGH_PRIORITY_FILES = {
        "package.json.tier1.template",
        "package.json.tier2.template",
        "package.json.tier3.template",
        "package.json.tier4.template",
        "eslint.config.mjs",  # May have stack-specific rules
    }

    # Files expected to differ
    EXPECTED_DIFFERENCES = {
        # Base application code
        "app/", "components/", "lib/", "prisma/",
        "next.config.ts", "tailwind.config.ts", "tsconfig.json",
        "package.json.template",  # Base package.json expected to differ

        # Tests are stack-specific
        "tests/unit/example.test.tsx",
        "tests/integration/",
        "tests/e2e/",
        "tests/api/",

        # Load tests
        "k6/",

        # Environment templates
        ".env.example", ".env.local.example", ".env.production.example",

        # Docker configs may differ
        "Dockerfile", "docker-compose.yml", "docker-compose.prod.yml",

        # Deployment configs
        ".github/workflows/deploy.yml",
        "vercel.json",  # Known to be only in saas_t3
    }

    def __init__(self, show_diffs: bool = False, single_file: str = None):
        self.show_diffs = show_diffs
        self.single_file = single_file
        self.file_map: Dict[str, Dict[str, Path]] = {}  # relative_path -> {stack: full_path}
        self.diffs: List[FileDiff] = []
        self.all_comparisons: List[FileComparison] = []  # Complete comparison list

    def scan_stacks(self):
        """Scan all stacks and build file map"""
        if self.single_file:
            print(f"📁 Scanning for single file: {self.single_file}...")
            for stack in self.STACKS:
                stack_path = self.TEMPLATES_DIR / stack
                file_path = stack_path / self.single_file
                if file_path.exists() and file_path.is_file():
                    if self.single_file not in self.file_map:
                        self.file_map[self.single_file] = {}
                    self.file_map[self.single_file][stack] = file_path

            if not self.file_map:
                print(f"  ⚠️  File '{self.single_file}' not found in any stack!")
            else:
                stacks_found = list(self.file_map[self.single_file].keys())
                print(f"  ✓ Found in: {', '.join(stacks_found)}\n")
        else:
            print("📁 Scanning template directories...")

            for stack in self.STACKS:
                stack_path = self.TEMPLATES_DIR / stack
                if not stack_path.exists():
                    print(f"  ⚠️  Warning: {stack} not found")
                    continue

                # Scan all files in the stack
                for file_path in stack_path.rglob("*"):
                    if file_path.is_file() and not self._should_skip(file_path):
                        relative = file_path.relative_to(stack_path)
                        relative_str = str(relative)

                        if relative_str not in self.file_map:
                            self.file_map[relative_str] = {}
                        self.file_map[relative_str][stack] = file_path

            print(f"  ✓ Found {len(self.file_map)} unique file paths across {len(self.STACKS)} stacks\n")

    def _should_skip(self, path: Path) -> bool:
        """Check if file should be skipped"""
        skip_patterns = [
            ".DS_Store",
            "__pycache__",
            "node_modules",
            ".ruff_cache",
            "*.pyc",
            ".gitkeep",
        ]

        path_str = str(path)

        # Skip .git directory but NOT .github
        if "/.git/" in path_str or path_str.endswith("/.git"):
            return True

        for pattern in skip_patterns:
            if pattern in path_str:
                return True
        return False

    def compare_files(self):
        """Compare files across stacks"""
        print("🔍 Comparing files across stacks...\n")

        # Compare ALL files, including those in only one stack
        for relative_path, stack_files in sorted(self.file_map.items()):
            stacks_present = set(stack_files.keys())
            severity = self._determine_severity(relative_path, stacks_present)

            # Compare all pairs (if more than one stack has this file)
            differences = {}
            is_identical = True

            if len(stack_files) >= 2:
                stacks = sorted(stack_files.keys())

                for i in range(len(stacks)):
                    for j in range(i + 1, len(stacks)):
                        stack1, stack2 = stacks[i], stacks[j]
                        file1, file2 = stack_files[stack1], stack_files[stack2]

                        diff = self._compare_file_pair(file1, file2, relative_path)
                        if diff:
                            differences[(stack1, stack2)] = diff
                            is_identical = False

            reason = self._get_diff_reason(relative_path, stacks_present) if differences or len(stacks_present) < len(self.STACKS) else "Identical across all stacks"

            # Add to complete comparisons list
            self.all_comparisons.append(FileComparison(
                relative_path=relative_path,
                stacks_present=stacks_present,
                file_paths=stack_files,
                is_identical=is_identical and len(stacks_present) == len(self.STACKS),
                severity=severity,
                differences=differences,
                reason=reason
            ))

            # Add to diffs list if there are differences
            if differences or len(stacks_present) < len(self.STACKS):
                self.diffs.append(FileDiff(
                    relative_path=relative_path,
                    severity=severity,
                    stacks_present=stacks_present,
                    differences=differences,
                    reason=reason
                ))

    def _compare_file_pair(self, file1: Path, file2: Path, relative_path: str) -> List[str]:
        """Compare two files and return diff if different"""
        try:
            content1 = self._normalize_content(file1.read_text(), relative_path)
            content2 = self._normalize_content(file2.read_text(), relative_path)

            if content1 == content2:
                return []

            # Generate unified diff
            diff = list(difflib.unified_diff(
                content1.splitlines(keepends=True),
                content2.splitlines(keepends=True),
                fromfile=str(file1.name),
                tofile=str(file2.name),
                lineterm=""
            ))

            return diff

        except Exception as e:
            return [f"Error comparing files: {e}"]

    def _normalize_content(self, content: str, relative_path: str) -> str:
        """Normalize content for comparison"""
        # For template files, normalize common template variables
        if ".template" in relative_path or "example" in relative_path:
            # Normalize project name placeholders
            content = re.sub(r'\{project_name\}|\{PROJECT_NAME\}', 'PROJECT_NAME', content)
            content = re.sub(r'\{project-name\}', 'project-name', content)

        # Normalize line endings
        content = content.replace('\r\n', '\n')

        # For package.json, normalize version numbers to compare structure
        if "package.json" in relative_path:
            # Don't normalize - we want to see version differences
            pass

        return content

    def _determine_severity(self, relative_path: str, stacks_present: Set[str]) -> DiffSeverity:
        """Determine severity level for a file difference"""
        # File missing from some stacks
        if len(stacks_present) < len(self.STACKS):
            if any(critical in relative_path for critical in self.CRITICAL_FILES):
                return DiffSeverity.CRITICAL
            elif any(high in relative_path for high in self.HIGH_PRIORITY_FILES):
                return DiffSeverity.HIGH
            else:
                return DiffSeverity.MEDIUM

        # File present in all stacks - check if it should be identical
        if any(relative_path.endswith(critical) or critical in relative_path
               for critical in self.CRITICAL_FILES):
            return DiffSeverity.CRITICAL

        if any(relative_path.endswith(high) for high in self.HIGH_PRIORITY_FILES):
            return DiffSeverity.HIGH

        if any(expected in relative_path for expected in self.EXPECTED_DIFFERENCES):
            return DiffSeverity.LOW

        return DiffSeverity.MEDIUM

    def _get_diff_reason(self, relative_path: str, stacks_present: Set[str]) -> str:
        """Get reason for the difference"""
        missing = set(self.STACKS) - stacks_present

        if missing:
            return f"Missing from: {', '.join(sorted(missing))}"

        if "package.json" in relative_path:
            return "Check scripts match, dependencies may differ"

        if "eslint.config.mjs" in relative_path:
            return "Verify stack-specific rules are appropriate"

        if any(test in relative_path for test in ["tests/", "spec.ts", "test.ts"]):
            return "Stack-specific tests - verify appropriate coverage"

        if "sentry" in relative_path.lower() or "instrumentation" in relative_path:
            return "Verify structure/pattern matches, values will differ"

        return "Content differs - verify if intentional"

    def generate_report(self, output_path: Path = None):
        """Generate markdown report"""
        identical_count = sum(1 for c in self.all_comparisons if c.is_identical)

        lines = [
            "# Template Stack Comparison Report\n",
            f"**Comparing**: {', '.join(self.STACKS)}",
            f"**Total files scanned**: {len(self.file_map)}",
            f"**Files identical across all stacks**: {identical_count}",
            f"**Files with differences**: {len(self.diffs)}\n",
            "---\n",
        ]

        # Section 1: Complete File List
        lines.append("\n## Complete File Comparison\n")
        lines.append("This section shows ALL files found in the templates with their paths and status.\n")

        # Group files by directory for better organization
        by_directory = {}
        for comp in self.all_comparisons:
            dir_name = str(Path(comp.relative_path).parent)
            if dir_name == '.':
                dir_name = 'root'
            if dir_name not in by_directory:
                by_directory[dir_name] = []
            by_directory[dir_name].append(comp)

        for dir_name in sorted(by_directory.keys()):
            comparisons = sorted(by_directory[dir_name], key=lambda c: c.relative_path)
            lines.append(f"\n### Directory: `{dir_name}`\n")
            lines.append("| File | saas_t3 | dashboard_refine | fullstack_nextjs | Status |")
            lines.append("|------|---------|------------------|------------------|--------|")

            for comp in comparisons:
                file_name = Path(comp.relative_path).name

                # Check presence in each stack
                s3_present = "✅" if "saas_t3" in comp.stacks_present else "❌"
                dr_present = "✅" if "dashboard_refine" in comp.stacks_present else "❌"
                fn_present = "✅" if "fullstack_nextjs" in comp.stacks_present else "❌"

                # Status icon
                if comp.is_identical:
                    status = "✅ Identical"
                elif len(comp.stacks_present) < len(self.STACKS):
                    missing = set(self.STACKS) - comp.stacks_present
                    status = f"⚠️ Missing from {', '.join(missing)}"
                else:
                    status = f"{comp.severity.value.split()[0]} Different"

                lines.append(f"| `{file_name}` | {s3_present} | {dr_present} | {fn_present} | {status} |")

        lines.append("\n---\n")

        # Section 2: Differences by Severity
        lines.append("\n## Differences by Severity\n")
        lines.append("This section shows only files that differ or are missing from some stacks.\n")

        # Group by severity
        by_severity = {}
        for diff in self.diffs:
            if diff.severity not in by_severity:
                by_severity[diff.severity] = []
            by_severity[diff.severity].append(diff)

        # Report each severity level
        for severity in [DiffSeverity.CRITICAL, DiffSeverity.HIGH, DiffSeverity.MEDIUM,
                        DiffSeverity.LOW, DiffSeverity.INFO]:
            if severity not in by_severity:
                continue

            diffs = by_severity[severity]
            lines.append(f"\n## {severity.value} - {len(diffs)} files\n")

            for diff in sorted(diffs, key=lambda d: d.relative_path):
                lines.append(f"\n### `{diff.relative_path}`\n")
                lines.append(f"**Stacks present**: {', '.join(sorted(diff.stacks_present))}")
                lines.append(f"**Status**: {diff.reason}\n")

                # Show full paths for each stack
                lines.append("\n**File paths**:")
                comp = next((c for c in self.all_comparisons if c.relative_path == diff.relative_path), None)
                if comp:
                    for stack in self.STACKS:
                        if stack in comp.file_paths:
                            lines.append(f"- `{stack}`: {comp.file_paths[stack]}")
                        else:
                            lines.append(f"- `{stack}`: ❌ Missing")
                lines.append("")

                if self.show_diffs and diff.differences:
                    for (stack1, stack2), diff_lines in diff.differences.items():
                        lines.append(f"\n**Diff ({stack1} vs {stack2})**:\n")
                        lines.append("```diff")
                        # Show first 50 lines of diff
                        for line in diff_lines[:50]:
                            lines.append(line.rstrip())
                        if len(diff_lines) > 50:
                            lines.append(f"... ({len(diff_lines) - 50} more lines)")
                        lines.append("```\n")

                lines.append("---")

        # Summary statistics
        lines.append("\n## Summary\n")
        lines.append("| Severity | Count |")
        lines.append("|----------|-------|")
        for severity in [DiffSeverity.CRITICAL, DiffSeverity.HIGH, DiffSeverity.MEDIUM,
                        DiffSeverity.LOW, DiffSeverity.INFO]:
            count = len(by_severity.get(severity, []))
            if count > 0:
                lines.append(f"| {severity.value} | {count} |")

        report = "\n".join(lines)

        if output_path:
            output_path.write_text(report)
            print(f"📄 Report written to: {output_path}")

        return report

    def generate_csv(self, output_path: Path):
        """Generate CSV report"""
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)

            # Header
            writer.writerow([
                'Relative Path',
                'Directory',
                'File Name',
                'saas_t3',
                'dashboard_refine',
                'fullstack_nextjs',
                'saas_t3 Full Path',
                'dashboard_refine Full Path',
                'fullstack_nextjs Full Path',
                'Status',
                'Severity',
                'Reason'
            ])

            # Data rows
            for comp in sorted(self.all_comparisons, key=lambda c: c.relative_path):
                dir_name = str(Path(comp.relative_path).parent)
                file_name = Path(comp.relative_path).name

                # Presence indicators
                s3_present = "Yes" if "saas_t3" in comp.stacks_present else "No"
                dr_present = "Yes" if "dashboard_refine" in comp.stacks_present else "No"
                fn_present = "Yes" if "fullstack_nextjs" in comp.stacks_present else "No"

                # Full paths
                s3_path = str(comp.file_paths.get("saas_t3", "")) if "saas_t3" in comp.file_paths else ""
                dr_path = str(comp.file_paths.get("dashboard_refine", "")) if "dashboard_refine" in comp.file_paths else ""
                fn_path = str(comp.file_paths.get("fullstack_nextjs", "")) if "fullstack_nextjs" in comp.file_paths else ""

                # Status
                if comp.is_identical:
                    status = "Identical"
                elif len(comp.stacks_present) < len(self.STACKS):
                    missing = set(self.STACKS) - comp.stacks_present
                    status = f"Missing from {', '.join(sorted(missing))}"
                else:
                    status = "Different"

                # Severity (without emoji)
                severity = comp.severity.value.split()[1] if len(comp.severity.value.split()) > 1 else comp.severity.value

                writer.writerow([
                    comp.relative_path,
                    dir_name,
                    file_name,
                    s3_present,
                    dr_present,
                    fn_present,
                    s3_path,
                    dr_path,
                    fn_path,
                    status,
                    severity,
                    comp.reason
                ])

        print(f"📊 CSV report written to: {output_path}")

    def print_single_file_comparison(self):
        """Print detailed comparison for a single file"""
        if not self.single_file or self.single_file not in self.file_map:
            return

        print("\n" + "="*80)
        print(f"SINGLE FILE COMPARISON: {self.single_file}")
        print("="*80 + "\n")

        stack_files = self.file_map[self.single_file]
        stacks_present = set(stack_files.keys())
        missing = set(self.STACKS) - stacks_present

        # Show presence
        print("📍 File Presence:")
        for stack in self.STACKS:
            if stack in stack_files:
                print(f"  ✅ {stack}: {stack_files[stack]}")
            else:
                print(f"  ❌ {stack}: Missing")

        if missing:
            print(f"\n⚠️  File is missing from: {', '.join(sorted(missing))}")
            return

        # Compare all pairs
        print("\n🔍 Content Comparison:\n")
        stacks = sorted(stack_files.keys())
        all_identical = True

        for i in range(len(stacks)):
            for j in range(i + 1, len(stacks)):
                stack1, stack2 = stacks[i], stacks[j]
                file1, file2 = stack_files[stack1], stack_files[stack2]

                diff = self._compare_file_pair(file1, file2, self.single_file)

                print(f"\n{'='*80}")
                print(f"Comparing: {stack1} vs {stack2}")
                print('='*80)

                if not diff:
                    print("✅ Files are IDENTICAL")
                else:
                    all_identical = False
                    print(f"❌ Files DIFFER ({len(diff)} diff lines)\n")
                    print("Diff:")
                    print("-" * 80)
                    for line in diff[:100]:  # Show first 100 lines
                        print(line.rstrip())
                    if len(diff) > 100:
                        print(f"\n... ({len(diff) - 100} more lines)")
                    print("-" * 80)

        print("\n" + "="*80)
        if all_identical:
            print("✅ RESULT: File is IDENTICAL across all stacks")
        else:
            print("❌ RESULT: File has DIFFERENCES across stacks")
        print("="*80 + "\n")

    def print_summary(self):
        """Print summary to console"""
        print("\n" + "="*80)
        print("COMPARISON SUMMARY")
        print("="*80 + "\n")

        by_severity = {}
        for diff in self.diffs:
            if diff.severity not in by_severity:
                by_severity[diff.severity] = []
            by_severity[diff.severity].append(diff)

        for severity in [DiffSeverity.CRITICAL, DiffSeverity.HIGH, DiffSeverity.MEDIUM]:
            if severity not in by_severity:
                continue

            diffs = by_severity[severity]
            print(f"\n{severity.value} ({len(diffs)} files):")
            print("-" * 80)

            for diff in sorted(diffs, key=lambda d: d.relative_path)[:10]:  # Show first 10
                stacks = ', '.join(sorted(diff.stacks_present))
                print(f"  • {diff.relative_path}")
                print(f"    Stacks: {stacks}")
                print(f"    {diff.reason}")

            if len(diffs) > 10:
                print(f"  ... and {len(diffs) - 10} more")

        print("\n" + "="*80)
        print(f"Total differences: {len(self.diffs)}")
        print("="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Compare template stacks for consistency",
        epilog="""
Examples:
  # Compare all files and generate CSV
  python compare_stacks.py --output report.csv

  # Compare a single file across all stacks
  python compare_stacks.py --file tier-4-production/k6/load-test.js

  # Compare single file with output to file
  python compare_stacks.py --file tier-3-comprehensive/.axe-config.json --output axe-comparison.md
        """
    )
    parser.add_argument("--output", type=Path,
                       help="Output file for the report (extension determines format: .csv or .md)")
    parser.add_argument("--format", choices=["csv", "markdown"],
                       help="Output format (default: auto-detect from output file extension)")
    parser.add_argument("--show-diffs", action="store_true",
                       help="Include detailed diffs in markdown report (ignored for CSV)")
    parser.add_argument("--file", type=str,
                       help="Compare only a single file across all stacks (relative path from stack root)")

    args = parser.parse_args()

    # Single file mode
    if args.file:
        comparator = StackComparator(show_diffs=True, single_file=args.file)
        comparator.scan_stacks()

        if not comparator.file_map:
            print(f"\n❌ File '{args.file}' not found in any stack!")
            return 1

        comparator.compare_files()
        comparator.print_single_file_comparison()

        # Optionally save to file
        if args.output:
            if args.output.suffix == ".csv":
                comparator.generate_csv(args.output)
            else:
                comparator.generate_report(args.output)

        # Return error code if file differs
        if comparator.diffs:
            return 1
        return 0

    # Full comparison mode
    # Determine output format
    if args.format:
        output_format = args.format
    elif args.output:
        output_format = "csv" if args.output.suffix == ".csv" else "markdown"
    else:
        output_format = "markdown"

    # Default output path based on format
    if not args.output:
        args.output = Path(f"analysis-docs/stack_comparison_report.{'csv' if output_format == 'csv' else 'md'}")

    comparator = StackComparator(show_diffs=args.show_diffs)
    comparator.scan_stacks()
    comparator.compare_files()
    comparator.print_summary()

    # Generate output in requested format
    if output_format == "csv":
        comparator.generate_csv(args.output)
    else:
        comparator.generate_report(args.output)

    # Exit with error code if critical issues found
    critical_count = sum(1 for d in comparator.diffs if d.severity == DiffSeverity.CRITICAL)
    if critical_count > 0:
        print(f"\n⚠️  Found {critical_count} CRITICAL differences that must be fixed!")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
