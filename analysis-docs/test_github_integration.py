#!/usr/bin/env python3
"""
GitHub Integration Test for Solokit Templates

This script validates that generated templates actually pass CI/CD checks on GitHub
by creating a real test repository, pushing to it, creating a PR, and waiting for
CI/CD checks to complete.

Prerequisites:
1. GitHub CLI (gh) installed and authenticated
2. A GitHub organization or personal account with permissions to create repos
3. GITHUB_TOKEN environment variable set (optional, gh CLI uses its own auth)

Usage:
    # Test a single template
    python test_github_integration.py --stack saas_t3 --tier tier-1-essential

    # Test multiple templates
    python test_github_integration.py --stack saas_t3 --tier tier-2-standard --tier tier-3-comprehensive

    # Use a specific GitHub org
    python test_github_integration.py --org my-test-org --stack saas_t3 --tier tier-1-essential

    # Keep the test repo after completion (for debugging)
    python test_github_integration.py --no-cleanup --stack saas_t3 --tier tier-1-essential
"""

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any


@dataclass
class GitHubTestResult:
    """Result of a GitHub integration test"""
    test_id: str
    stack: str
    tier: str
    options: List[str]
    success: bool
    duration_seconds: float
    repo_url: Optional[str]
    pr_url: Optional[str]
    ci_checks_passed: bool
    failed_checks: List[str]
    errors: List[str]
    timestamp: str


class GitHubIntegrationTester:
    """Tests templates by pushing to real GitHub repos and validating CI/CD"""

    def __init__(
        self,
        workspace: Path,
        github_org: Optional[str] = None,
        cleanup: bool = True,
        wait_timeout: int = 1800  # 30 minutes
    ):
        self.workspace = workspace
        self.github_org = github_org
        self.cleanup = cleanup
        self.wait_timeout = wait_timeout
        self.results: List[GitHubTestResult] = []

        # Verify gh CLI is installed and authenticated
        self._verify_gh_cli()

        # Create workspace
        self.workspace.mkdir(parents=True, exist_ok=True)

    def _verify_gh_cli(self):
        """Verify GitHub CLI is installed and authenticated"""
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                print("❌ GitHub CLI not authenticated. Run: gh auth login")
                sys.exit(1)
            print("✓ GitHub CLI authenticated")
        except FileNotFoundError:
            print("❌ GitHub CLI (gh) not found. Install from: https://cli.github.com/")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error verifying GitHub CLI: {e}")
            sys.exit(1)

    def _run_command(
        self,
        cmd: List[str],
        cwd: Path,
        timeout: int = 300,
        check: bool = False
    ) -> tuple[bool, str, str]:
        """Run a shell command"""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=check
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout}s"
        except subprocess.CalledProcessError as e:
            return False, e.stdout, e.stderr
        except Exception as e:
            return False, "", str(e)

    def test_template(
        self,
        stack: str,
        tier: str,
        options: List[str] = None
    ) -> GitHubTestResult:
        """
        Test a template by:
        1. Creating a local project with sk init
        2. Creating a GitHub repository
        3. Pushing the code
        4. Creating a PR
        5. Waiting for CI/CD checks
        6. Validating all checks pass
        """
        if options is None:
            options = []

        test_id = f"gh_{stack}_{tier}_{'_'.join(options) if options else 'base'}"
        repo_name = f"solokit-test-{test_id}-{int(time.time())}"

        print(f"\n{'='*80}")
        print(f"GitHub Integration Test: {test_id}")
        print(f"Stack: {stack}, Tier: {tier}, Options: {options}")
        print(f"{'='*80}\n")

        start_time = time.time()
        errors = []
        repo_url = None
        pr_url = None
        ci_checks_passed = False
        failed_checks = []

        project_path = None

        try:
            # Step 1: Create local project
            print("→ Step 1: Creating local project with sk init...")
            project_path = self.workspace / repo_name
            project_path.mkdir(parents=True, exist_ok=True)

            cmd = ["sk", "init", "--template", stack, "--tier", tier, "--coverage", "80"]
            if options:
                cmd.extend(["--options", ",".join(options)])

            success, stdout, stderr = self._run_command(cmd, project_path, timeout=600)
            if not success:
                raise Exception(f"sk init failed: {stderr}")

            print("✓ Project created locally")

            # Step 2: Install dependencies
            print("\n→ Step 2: Installing dependencies...")
            if stack == "ml_ai_fastapi":
                cmd = ["pip", "install", "-e", ".", "--quiet"]
            else:
                cmd = ["npm", "install", "--silent"]

            success, stdout, stderr = self._run_command(cmd, project_path, timeout=900)
            if not success:
                errors.append(f"Dependency installation failed: {stderr}")
                # Continue anyway - CI might handle this differently

            print("✓ Dependencies installed")

            # Step 3: Create sample code (similar to local test)
            print("\n→ Step 3: Creating sample code...")
            self._create_sample_code(project_path, stack)
            print("✓ Sample code created")

            # Step 4: Commit changes
            print("\n→ Step 4: Committing changes...")
            self._run_command(["git", "add", "-A"], project_path)
            self._run_command(
                ["git", "commit", "-m", "feat: initial template validation\n\nGenerated by solokit GitHub integration test"],
                project_path
            )
            print("✓ Changes committed")

            # Step 5: Create GitHub repository
            print("\n→ Step 5: Creating GitHub repository...")
            repo_url, create_errors = self._create_github_repo(repo_name)
            if not repo_url:
                raise Exception(f"Failed to create GitHub repo: {create_errors}")

            print(f"✓ Repository created: {repo_url}")

            # Step 6: Push to main branch
            print("\n→ Step 6: Pushing to main branch...")
            self._run_command(["git", "remote", "add", "origin", repo_url], project_path)
            success, stdout, stderr = self._run_command(
                ["git", "push", "-u", "origin", "main"],
                project_path,
                timeout=120
            )
            if not success:
                # Try master branch
                success, stdout, stderr = self._run_command(
                    ["git", "push", "-u", "origin", "master"],
                    project_path,
                    timeout=120
                )
                if not success:
                    raise Exception(f"Failed to push: {stderr}")

            print("✓ Code pushed to GitHub")

            # Step 7: Create a test branch for PR
            print("\n→ Step 7: Creating PR branch...")
            self._run_command(["git", "checkout", "-b", "test/ci-validation"], project_path)

            # Make a small change to trigger CI
            readme_path = project_path / "README.md"
            if readme_path.exists():
                content = readme_path.read_text()
                readme_path.write_text(content + "\n\n<!-- CI validation test -->")
                self._run_command(["git", "add", "README.md"], project_path)
                self._run_command(
                    ["git", "commit", "-m", "test: trigger CI validation"],
                    project_path
                )
                self._run_command(
                    ["git", "push", "-u", "origin", "test/ci-validation"],
                    project_path,
                    timeout=120
                )

            print("✓ PR branch created and pushed")

            # Step 8: Create pull request
            print("\n→ Step 8: Creating pull request...")
            pr_url, pr_errors = self._create_pull_request(project_path, repo_name)
            if not pr_url:
                raise Exception(f"Failed to create PR: {pr_errors}")

            print(f"✓ Pull request created: {pr_url}")

            # Step 9: Wait for CI checks to complete
            print("\n→ Step 9: Waiting for CI/CD checks to complete...")
            print(f"  (timeout: {self.wait_timeout}s = {self.wait_timeout // 60} minutes)")

            ci_checks_passed, failed_checks = self._wait_for_ci_checks(
                project_path,
                repo_name,
                timeout=self.wait_timeout
            )

            if ci_checks_passed:
                print("✓ All CI/CD checks passed!")
            else:
                print(f"✗ CI/CD checks failed:")
                for check in failed_checks:
                    print(f"  - {check}")
                errors.append(f"CI checks failed: {', '.join(failed_checks)}")

            # Test successful if CI checks passed
            success = ci_checks_passed

        except Exception as e:
            print(f"\n✗ Test failed: {str(e)}")
            errors.append(str(e))
            success = False

        finally:
            duration = time.time() - start_time

            # Cleanup
            if self.cleanup and project_path and project_path.exists():
                print("\n→ Cleaning up local directory...")
                import shutil
                shutil.rmtree(project_path, ignore_errors=True)

            if self.cleanup and repo_url:
                print("→ Deleting GitHub repository...")
                self._delete_github_repo(repo_name)

            # Create result
            result = GitHubTestResult(
                test_id=test_id,
                stack=stack,
                tier=tier,
                options=options,
                success=success,
                duration_seconds=round(duration, 2),
                repo_url=repo_url,
                pr_url=pr_url,
                ci_checks_passed=ci_checks_passed,
                failed_checks=failed_checks,
                errors=errors,
                timestamp=datetime.now().isoformat()
            )

            self.results.append(result)

            if success:
                print(f"\n{'='*80}")
                print(f"✓ PASSED: {test_id}")
                print(f"{'='*80}")
            else:
                print(f"\n{'='*80}")
                print(f"✗ FAILED: {test_id}")
                print(f"{'='*80}")

            return result

    def _create_sample_code(self, project_path: Path, stack: str):
        """Create minimal sample code for testing"""
        if stack == "ml_ai_fastapi":
            code_file = project_path / "src" / "test_feature.py"
            code_file.parent.mkdir(parents=True, exist_ok=True)
            code_file.write_text("""
def add(a: int, b: int) -> int:
    \"\"\"Add two numbers\"\"\"
    return a + b
""")

            test_file = project_path / "tests" / "test_feature.py"
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text("""
from src.test_feature import add

def test_add():
    assert add(2, 3) == 5
    assert add(0, 0) == 0
    assert add(-1, 1) == 0
""")
        else:
            code_file = project_path / "lib" / "test-feature.ts"
            code_file.parent.mkdir(parents=True, exist_ok=True)
            code_file.write_text("""
export function add(a: number, b: number): number {
  return a + b;
}
""")

            test_file = project_path / "tests" / "test-feature.test.ts"
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text("""
import { add } from '../lib/test-feature';

describe('add', () => {
  it('should add two numbers', () => {
    expect(add(2, 3)).toBe(5);
    expect(add(0, 0)).toBe(0);
    expect(add(-1, 1)).toBe(0);
  });
});
""")

    def _create_github_repo(self, repo_name: str) -> tuple[Optional[str], List[str]]:
        """Create a GitHub repository using gh CLI"""
        errors = []

        try:
            cmd = ["gh", "repo", "create", repo_name, "--public", "--confirm"]
            if self.github_org:
                cmd = ["gh", "repo", "create", f"{self.github_org}/{repo_name}", "--public", "--confirm"]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                # Parse repo URL from output
                repo_url = result.stdout.strip().split()[-1] if result.stdout else None
                if not repo_url:
                    # Construct URL manually
                    if self.github_org:
                        repo_url = f"https://github.com/{self.github_org}/{repo_name}.git"
                    else:
                        # Get current user
                        user_result = subprocess.run(
                            ["gh", "api", "user", "--jq", ".login"],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        username = user_result.stdout.strip()
                        repo_url = f"https://github.com/{username}/{repo_name}.git"

                return repo_url, []
            else:
                errors.append(f"gh repo create failed: {result.stderr}")
                return None, errors

        except Exception as e:
            errors.append(f"Exception creating repo: {str(e)}")
            return None, errors

    def _create_pull_request(self, project_path: Path, repo_name: str) -> tuple[Optional[str], List[str]]:
        """Create a pull request using gh CLI"""
        errors = []

        try:
            cmd = [
                "gh", "pr", "create",
                "--title", "CI/CD Validation Test",
                "--body", "Automated test to validate template CI/CD configuration",
                "--base", "main",
                "--head", "test/ci-validation"
            ]

            result = subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                pr_url = result.stdout.strip()
                return pr_url, []
            else:
                errors.append(f"gh pr create failed: {result.stderr}")
                return None, errors

        except Exception as e:
            errors.append(f"Exception creating PR: {str(e)}")
            return None, errors

    def _wait_for_ci_checks(
        self,
        project_path: Path,
        repo_name: str,
        timeout: int
    ) -> tuple[bool, List[str]]:
        """
        Wait for CI checks to complete and return success status.

        Returns:
            (all_passed, failed_check_names)
        """
        start_time = time.time()
        check_interval = 30  # Check every 30 seconds

        while (time.time() - start_time) < timeout:
            # Get PR checks status
            result = subprocess.run(
                ["gh", "pr", "checks", "--json", "name,status,conclusion"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                print(f"  ⚠ Failed to get PR checks: {result.stderr}")
                time.sleep(check_interval)
                continue

            try:
                checks = json.loads(result.stdout)

                # Count statuses
                pending = sum(1 for c in checks if c.get("status") == "in_progress" or c.get("status") == "queued")
                completed = sum(1 for c in checks if c.get("status") == "completed")
                total = len(checks)

                # Get failed checks
                failed = [
                    c["name"] for c in checks
                    if c.get("status") == "completed" and c.get("conclusion") not in ["success", "neutral", "skipped"]
                ]

                print(f"  [{int(time.time() - start_time)}s] Checks: {completed}/{total} complete, {pending} pending, {len(failed)} failed")

                # All checks completed
                if pending == 0 and total > 0:
                    if len(failed) == 0:
                        return True, []
                    else:
                        return False, failed

                # No checks have started yet
                if total == 0:
                    print(f"  ⚠ No CI checks found yet, waiting...")

            except json.JSONDecodeError:
                print(f"  ⚠ Failed to parse checks JSON")

            time.sleep(check_interval)

        # Timeout reached
        return False, ["Timeout waiting for CI checks"]

    def _delete_github_repo(self, repo_name: str):
        """Delete a GitHub repository"""
        try:
            cmd = ["gh", "repo", "delete", repo_name, "--yes"]
            if self.github_org:
                cmd = ["gh", "repo", "delete", f"{self.github_org}/{repo_name}", "--yes"]

            subprocess.run(cmd, capture_output=True, timeout=30)
        except Exception:
            pass  # Ignore cleanup errors

    def save_results(self, output_file: Path):
        """Save test results to JSON"""
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(self.results),
            "passed": sum(1 for r in self.results if r.success),
            "failed": sum(1 for r in self.results if not r.success),
            "results": [asdict(r) for r in self.results]
        }

        output_file.write_text(json.dumps(results_data, indent=2))
        print(f"\n✓ Results saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="GitHub Integration Test for Solokit Templates"
    )

    parser.add_argument("--stack", required=True, help="Template stack to test")
    parser.add_argument("--tier", required=True, help="Template tier to test")
    parser.add_argument("--options", help="Comma-separated options (ci_cd,docker,env_templates)")
    parser.add_argument("--org", help="GitHub organization (uses personal account if not specified)")
    parser.add_argument("--no-cleanup", action="store_true", help="Keep test repos after completion")
    parser.add_argument("--workspace", default="/tmp/solokit_gh_test", help="Local workspace directory")
    parser.add_argument("--timeout", type=int, default=1800, help="CI check timeout in seconds (default: 1800 = 30 min)")

    args = parser.parse_args()

    workspace = Path(args.workspace)
    options = args.options.split(",") if args.options else []

    # Initialize tester
    tester = GitHubIntegrationTester(
        workspace=workspace,
        github_org=args.org,
        cleanup=not args.no_cleanup,
        wait_timeout=args.timeout
    )

    # Run test
    result = tester.test_template(
        stack=args.stack,
        tier=args.tier,
        options=options
    )

    # Save results
    results_dir = Path(__file__).parent / "test_results"
    results_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = results_dir / f"github_integration_{timestamp}.json"
    tester.save_results(results_file)

    # Exit with appropriate code
    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
