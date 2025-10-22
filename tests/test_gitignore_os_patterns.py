#!/usr/bin/env python3
"""
Test that gitignore includes OS-specific patterns after initialization.

This test verifies Enhancement #4: Add OS-specific files to .gitignore template
"""

import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.mark.skipif(
    subprocess.run(["which", "sdd"], capture_output=True).returncode != 0,
    reason="sdd command not available (not installed)",
)
def test_gitignore_os_patterns():
    """Test that sdd init adds OS-specific patterns to .gitignore."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "test_project"
        test_dir.mkdir()

        # Initialize git first (required for sdd init)
        subprocess.run(["git", "init"], cwd=test_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=test_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=test_dir,
            check=True,
            capture_output=True,
        )

        # Create minimal required docs directory
        docs_dir = test_dir / "docs"
        docs_dir.mkdir()

        # Run sdd init
        result = subprocess.run(
            ["sdd", "init"],
            cwd=test_dir,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"sdd init failed: {result.stderr}"

        # Check that .gitignore exists
        gitignore = test_dir / ".gitignore"
        assert gitignore.exists(), ".gitignore was not created"

        # Read .gitignore content
        gitignore_content = gitignore.read_text()

        # Define expected OS-specific patterns
        macos_patterns = [".DS_Store", ".DS_Store?", "._*", ".Spotlight-V100", ".Trashes"]
        windows_patterns = ["Thumbs.db", "ehthumbs.db", "Desktop.ini", "$RECYCLE.BIN/"]
        linux_patterns = ["*~"]

        all_patterns = macos_patterns + windows_patterns + linux_patterns

        # Check that all OS-specific patterns are present
        for pattern in all_patterns:
            assert pattern in gitignore_content, (
                f"Missing OS-specific pattern: {pattern}\n\n.gitignore content:\n{gitignore_content}"
            )

        # Check that comments are present
        assert "# OS-specific files" in gitignore_content, (
            "Missing OS-specific files section header"
        )
        assert "# macOS" in gitignore_content, "Missing macOS comment"
        assert "# Windows" in gitignore_content, "Missing Windows comment"
        assert "# Linux" in gitignore_content, "Missing Linux comment"

        # Verify that SDD patterns are still present
        sdd_patterns = [".session/briefings/", ".session/history/"]
        for pattern in sdd_patterns:
            assert pattern in gitignore_content, f"Missing SDD pattern: {pattern}"


if __name__ == "__main__":
    test_gitignore_os_patterns()
    print("✓ All OS-specific patterns present in .gitignore")
    print("✓ All comments present")
    print("✓ SDD patterns preserved")
