#!/usr/bin/env python3
"""
Test Results Analysis Script

Analyzes the JSON results from template testing and generates:
- Summary report
- Failure analysis
- Performance metrics
- Recommendations

Usage:
    python analyze_test_results.py test_results/test_results_20250117_143022.json
    python analyze_test_results.py --latest
    python analyze_test_results.py --all
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict


class TestResultsAnalyzer:
    """Analyzes test results and generates reports"""

    def __init__(self, results_file: Path):
        self.results_file = results_file
        self.data = self._load_results()

    def _load_results(self) -> Dict[str, Any]:
        """Load test results from JSON file"""
        try:
            with open(self.results_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading results file: {e}")
            sys.exit(1)

    def print_summary(self):
        """Print high-level summary"""
        total = self.data['total_tests']
        passed = self.data['passed']
        failed = self.data['failed']
        duration = self.data['total_duration_seconds']

        print("\n" + "="*80)
        print("TEST RESULTS SUMMARY")
        print("="*80)
        print(f"Timestamp: {self.data['timestamp']}")
        print(f"Results File: {self.results_file}")
        print("-"*80)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ({100*passed//total if total > 0 else 0}%)")
        print(f"Failed: {failed} ({100*failed//total if total > 0 else 0}%)")
        print(f"Total Duration: {self._format_duration(duration)}")
        print(f"Average Duration: {self._format_duration(duration/total if total > 0 else 0)}")
        print("="*80 + "\n")

    def print_failures(self):
        """Print detailed failure analysis"""
        failures = [r for r in self.data['results'] if not r['success']]

        if not failures:
            print("✓ No failures! All tests passed.")
            return

        print("\n" + "="*80)
        print("FAILURE ANALYSIS")
        print("="*80)

        for i, failure in enumerate(failures, 1):
            print(f"\n{i}. Test ID: {failure['test_id']}")
            print(f"   Stack: {failure['stack']}")
            print(f"   Tier: {failure['tier']}")
            print(f"   Options: {', '.join(failure['options']) if failure['options'] else 'None'}")
            print(f"   Duration: {self._format_duration(failure['duration_seconds'])}")
            print(f"   Steps Completed: {', '.join(failure['steps_completed'])}")

            if failure['errors']:
                print(f"   Errors:")
                for error in failure['errors']:
                    print(f"     - {error}")

            if failure['warnings']:
                print(f"   Warnings:")
                for warning in failure['warnings']:
                    print(f"     - {warning}")

            if failure.get('project_path'):
                print(f"   Project Path: {failure['project_path']}")

        print("\n" + "="*80 + "\n")

    def print_stack_analysis(self):
        """Analyze results by stack"""
        stack_results = defaultdict(lambda: {'total': 0, 'passed': 0, 'failed': 0, 'duration': 0})

        for result in self.data['results']:
            stack = result['stack']
            stack_results[stack]['total'] += 1
            stack_results[stack]['duration'] += result['duration_seconds']

            if result['success']:
                stack_results[stack]['passed'] += 1
            else:
                stack_results[stack]['failed'] += 1

        print("\n" + "="*80)
        print("RESULTS BY STACK")
        print("="*80)

        for stack in sorted(stack_results.keys()):
            stats = stack_results[stack]
            success_rate = 100 * stats['passed'] // stats['total'] if stats['total'] > 0 else 0

            print(f"\n{stack}:")
            print(f"  Total: {stats['total']}")
            print(f"  Passed: {stats['passed']}")
            print(f"  Failed: {stats['failed']}")
            print(f"  Success Rate: {success_rate}%")
            print(f"  Total Duration: {self._format_duration(stats['duration'])}")
            print(f"  Avg Duration: {self._format_duration(stats['duration']/stats['total'])}")

        print("\n" + "="*80 + "\n")

    def print_tier_analysis(self):
        """Analyze results by tier"""
        tier_results = defaultdict(lambda: {'total': 0, 'passed': 0, 'failed': 0, 'duration': 0})

        for result in self.data['results']:
            tier = result['tier']
            tier_results[tier]['total'] += 1
            tier_results[tier]['duration'] += result['duration_seconds']

            if result['success']:
                tier_results[tier]['passed'] += 1
            else:
                tier_results[tier]['failed'] += 1

        print("\n" + "="*80)
        print("RESULTS BY TIER")
        print("="*80)

        tier_order = ['tier-1-essential', 'tier-2-standard', 'tier-3-comprehensive', 'tier-4-production']

        for tier in tier_order:
            if tier not in tier_results:
                continue

            stats = tier_results[tier]
            success_rate = 100 * stats['passed'] // stats['total'] if stats['total'] > 0 else 0

            print(f"\n{tier}:")
            print(f"  Total: {stats['total']}")
            print(f"  Passed: {stats['passed']}")
            print(f"  Failed: {stats['failed']}")
            print(f"  Success Rate: {success_rate}%")
            print(f"  Total Duration: {self._format_duration(stats['duration'])}")
            print(f"  Avg Duration: {self._format_duration(stats['duration']/stats['total'])}")

        print("\n" + "="*80 + "\n")

    def print_options_analysis(self):
        """Analyze results by options"""
        option_results = {
            'no_options': {'total': 0, 'passed': 0, 'failed': 0, 'duration': 0},
            'ci_cd': {'total': 0, 'passed': 0, 'failed': 0, 'duration': 0},
            'docker': {'total': 0, 'passed': 0, 'failed': 0, 'duration': 0},
            'env_templates': {'total': 0, 'passed': 0, 'failed': 0, 'duration': 0},
            'all_options': {'total': 0, 'passed': 0, 'failed': 0, 'duration': 0},
        }

        for result in self.data['results']:
            options = result['options']

            if not options:
                key = 'no_options'
            elif len(options) == 3:
                key = 'all_options'
            elif 'ci_cd' in options and len(options) == 1:
                key = 'ci_cd'
            elif 'docker' in options and len(options) == 1:
                key = 'docker'
            elif 'env_templates' in options and len(options) == 1:
                key = 'env_templates'
            else:
                continue  # Skip combinations for now

            option_results[key]['total'] += 1
            option_results[key]['duration'] += result['duration_seconds']

            if result['success']:
                option_results[key]['passed'] += 1
            else:
                option_results[key]['failed'] += 1

        print("\n" + "="*80)
        print("RESULTS BY OPTIONS")
        print("="*80)

        for option, stats in option_results.items():
            if stats['total'] == 0:
                continue

            success_rate = 100 * stats['passed'] // stats['total'] if stats['total'] > 0 else 0

            print(f"\n{option}:")
            print(f"  Total: {stats['total']}")
            print(f"  Passed: {stats['passed']}")
            print(f"  Failed: {stats['failed']}")
            print(f"  Success Rate: {success_rate}%")
            print(f"  Total Duration: {self._format_duration(stats['duration'])}")
            if stats['total'] > 0:
                print(f"  Avg Duration: {self._format_duration(stats['duration']/stats['total'])}")

        print("\n" + "="*80 + "\n")

    def print_step_analysis(self):
        """Analyze which steps fail most often"""
        all_steps = [
            'create_directory',
            'initialize',
            'verify_installation',
            'install_dependencies',
            'create_work_item',
            'start_session',
            'create_code',
            'validate_session',
            'end_session',
            'push_to_remote'
        ]

        step_stats = defaultdict(lambda: {'success': 0, 'failure': 0})

        for result in self.data['results']:
            completed_steps = set(result['steps_completed'])

            for step in all_steps:
                if step in completed_steps:
                    step_stats[step]['success'] += 1
                else:
                    if not result['success']:
                        step_stats[step]['failure'] += 1

        print("\n" + "="*80)
        print("STEP COMPLETION ANALYSIS")
        print("="*80)

        print("\nStep Success Rates:")
        for step in all_steps:
            stats = step_stats[step]
            total = stats['success'] + stats['failure']
            if total == 0:
                continue

            success_rate = 100 * stats['success'] // total
            print(f"  {step:25s}: {stats['success']:3d}/{total:3d} ({success_rate:3d}%)")

        # Find most problematic steps
        failures = [(step, stats['failure']) for step, stats in step_stats.items() if stats['failure'] > 0]
        failures.sort(key=lambda x: x[1], reverse=True)

        if failures:
            print("\nMost Problematic Steps:")
            for step, count in failures[:5]:
                print(f"  {step:25s}: {count} failures")

        print("\n" + "="*80 + "\n")

    def print_performance_analysis(self):
        """Analyze performance metrics"""
        durations = [(r['test_id'], r['duration_seconds']) for r in self.data['results']]
        durations.sort(key=lambda x: x[1], reverse=True)

        print("\n" + "="*80)
        print("PERFORMANCE ANALYSIS")
        print("="*80)

        print("\nSlowest Tests:")
        for test_id, duration in durations[:10]:
            print(f"  {test_id:40s}: {self._format_duration(duration)}")

        print("\nFastest Tests:")
        for test_id, duration in durations[-10:]:
            print(f"  {test_id:40s}: {self._format_duration(duration)}")

        # Calculate percentiles
        sorted_durations = sorted([r['duration_seconds'] for r in self.data['results']])
        if sorted_durations:
            p50 = sorted_durations[len(sorted_durations)//2]
            p90 = sorted_durations[int(len(sorted_durations)*0.9)]
            p95 = sorted_durations[int(len(sorted_durations)*0.95)]

            print("\nDuration Percentiles:")
            print(f"  P50 (median): {self._format_duration(p50)}")
            print(f"  P90:          {self._format_duration(p90)}")
            print(f"  P95:          {self._format_duration(p95)}")

        print("\n" + "="*80 + "\n")

    def print_recommendations(self):
        """Generate recommendations based on results"""
        print("\n" + "="*80)
        print("RECOMMENDATIONS")
        print("="*80 + "\n")

        failures = [r for r in self.data['results'] if not r['success']]

        if not failures:
            print("✓ All tests passed! Consider:")
            print("  - Running additional edge case tests")
            print("  - Testing with different environment configurations")
            print("  - Adding performance regression tests")
            print("  - Updating documentation with findings")
        else:
            # Analyze failure patterns
            failure_stacks = defaultdict(int)
            failure_tiers = defaultdict(int)
            failure_steps = defaultdict(int)

            for failure in failures:
                failure_stacks[failure['stack']] += 1
                failure_tiers[failure['tier']] += 1

                all_steps = ['create_directory', 'initialize', 'verify_installation',
                            'install_dependencies', 'create_work_item', 'start_session',
                            'create_code', 'validate_session', 'end_session', 'push_to_remote']

                completed = set(failure['steps_completed'])
                for step in all_steps:
                    if step not in completed:
                        failure_steps[step] += 1
                        break  # Only count first failure

            print("Priority Actions:\n")

            # Stack-specific issues
            if failure_stacks:
                most_problematic_stack = max(failure_stacks.items(), key=lambda x: x[1])
                print(f"1. Fix {most_problematic_stack[0]} stack issues")
                print(f"   - {most_problematic_stack[1]} failures detected")
                print(f"   - Review template files in templates/{most_problematic_stack[0]}/")
                print()

            # Tier-specific issues
            if failure_tiers:
                most_problematic_tier = max(failure_tiers.items(), key=lambda x: x[1])
                print(f"2. Fix {most_problematic_tier[0]} tier issues")
                print(f"   - {most_problematic_tier[1]} failures detected")
                print(f"   - Check tier-specific dependencies and configurations")
                print()

            # Step-specific issues
            if failure_steps:
                most_problematic_step = max(failure_steps.items(), key=lambda x: x[1])
                print(f"3. Fix {most_problematic_step[0]} step")
                print(f"   - {most_problematic_step[1]} failures at this step")
                print(f"   - Review implementation in test script and templates")
                print()

            print("General Recommendations:")
            print("  - Review error messages in the results JSON file")
            print("  - Inspect failed project directories (kept for debugging)")
            print("  - Run failed tests individually for detailed debugging")
            print("  - Check system requirements (Node.js, Python versions)")
            print("  - Verify network connectivity for dependency installation")

        print("\n" + "="*80 + "\n")

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.1f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"

    def generate_markdown_report(self, output_file: Path):
        """Generate a markdown report"""
        with open(output_file, 'w') as f:
            f.write(f"# Test Results Report\n\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Results File**: {self.results_file}\n")
            f.write(f"**Test Run**: {self.data['timestamp']}\n\n")

            # Summary
            f.write("## Summary\n\n")
            f.write(f"- **Total Tests**: {self.data['total_tests']}\n")
            f.write(f"- **Passed**: {self.data['passed']}\n")
            f.write(f"- **Failed**: {self.data['failed']}\n")
            f.write(f"- **Success Rate**: {100*self.data['passed']//self.data['total_tests']}%\n")
            f.write(f"- **Total Duration**: {self._format_duration(self.data['total_duration_seconds'])}\n\n")

            # Failures
            failures = [r for r in self.data['results'] if not r['success']]
            if failures:
                f.write("## Failures\n\n")
                for failure in failures:
                    f.write(f"### {failure['test_id']}\n\n")
                    f.write(f"- **Stack**: {failure['stack']}\n")
                    f.write(f"- **Tier**: {failure['tier']}\n")
                    f.write(f"- **Options**: {', '.join(failure['options']) if failure['options'] else 'None'}\n")
                    f.write(f"- **Duration**: {self._format_duration(failure['duration_seconds'])}\n")
                    f.write(f"- **Steps Completed**: {', '.join(failure['steps_completed'])}\n\n")

                    if failure['errors']:
                        f.write("**Errors**:\n")
                        for error in failure['errors']:
                            f.write(f"- {error}\n")
                        f.write("\n")

            # All results table
            f.write("## All Results\n\n")
            f.write("| Test ID | Stack | Tier | Options | Status | Duration |\n")
            f.write("|---------|-------|------|---------|--------|----------|\n")

            for result in self.data['results']:
                status = "✅" if result['success'] else "❌"
                options = ', '.join(result['options']) if result['options'] else 'None'
                duration = self._format_duration(result['duration_seconds'])
                f.write(f"| {result['test_id']} | {result['stack']} | {result['tier']} | {options} | {status} | {duration} |\n")

        print(f"\n✓ Markdown report saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Analyze solokit test results")
    parser.add_argument('results_file', nargs='?', help="Path to results JSON file")
    parser.add_argument('--latest', action='store_true', help="Analyze most recent results")
    parser.add_argument('--all', action='store_true', help="Show all analysis sections")
    parser.add_argument('--summary', action='store_true', help="Show summary only")
    parser.add_argument('--failures', action='store_true', help="Show failures only")
    parser.add_argument('--stacks', action='store_true', help="Show stack analysis")
    parser.add_argument('--tiers', action='store_true', help="Show tier analysis")
    parser.add_argument('--options', action='store_true', help="Show options analysis")
    parser.add_argument('--steps', action='store_true', help="Show step analysis")
    parser.add_argument('--performance', action='store_true', help="Show performance analysis")
    parser.add_argument('--recommendations', action='store_true', help="Show recommendations")
    parser.add_argument('--markdown', type=str, help="Generate markdown report to file")

    args = parser.parse_args()

    results_dir = Path(__file__).parent / "test_results"

    # Determine which results file to use
    if args.latest:
        results_files = sorted(results_dir.glob("test_results_*.json"), reverse=True)
        if not results_files:
            print("No results files found in test_results/")
            sys.exit(1)
        results_file = results_files[0]
    elif args.results_file:
        results_file = Path(args.results_file)
    else:
        parser.print_help()
        sys.exit(1)

    if not results_file.exists():
        print(f"Results file not found: {results_file}")
        sys.exit(1)

    # Initialize analyzer
    analyzer = TestResultsAnalyzer(results_file)

    # Determine what to show
    show_all = args.all or not any([
        args.summary, args.failures, args.stacks, args.tiers,
        args.options, args.steps, args.performance, args.recommendations
    ])

    # Generate reports
    if show_all or args.summary:
        analyzer.print_summary()

    if show_all or args.failures:
        analyzer.print_failures()

    if show_all or args.stacks:
        analyzer.print_stack_analysis()

    if show_all or args.tiers:
        analyzer.print_tier_analysis()

    if show_all or args.options:
        analyzer.print_options_analysis()

    if show_all or args.steps:
        analyzer.print_step_analysis()

    if show_all or args.performance:
        analyzer.print_performance_analysis()

    if show_all or args.recommendations:
        analyzer.print_recommendations()

    # Generate markdown report if requested
    if args.markdown:
        markdown_file = Path(args.markdown)
        analyzer.generate_markdown_report(markdown_file)


if __name__ == "__main__":
    main()
