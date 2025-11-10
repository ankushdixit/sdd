#!/usr/bin/env python3
"""
Generate and update technology stack documentation.

Detects:
- Languages (from file extensions)
- Frameworks (from imports and config files)
- Libraries (from requirements.txt, package.json, etc.)
- Databases (from connection strings, imports)
- MCP Servers (from context7 usage, etc.)
- External APIs (from code inspection)
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from solokit.core.error_handlers import log_errors
from solokit.core.exceptions import FileOperationError
from solokit.core.output import get_output

output = get_output()


class StackGenerator:
    """Generate technology stack documentation."""

    def __init__(self, project_root: Path | None = None):
        """Initialize StackGenerator with project root path."""
        self.project_root = project_root or Path.cwd()
        self.stack_file = self.project_root / ".session" / "tracking" / "stack.txt"
        self.updates_file = self.project_root / ".session" / "tracking" / "stack_updates.json"

    def detect_languages(self) -> dict[str, str]:
        """Detect programming languages from file extensions."""
        languages = {}

        # Count files by extension
        extensions = {
            ".py": ("Python", "python"),
            ".js": ("JavaScript", "javascript"),
            ".ts": ("TypeScript", "typescript"),
            ".rs": ("Rust", "rust"),
            ".go": ("Go", "go"),
            ".java": ("Java", "java"),
            ".cpp": ("C++", "cpp"),
            ".c": ("C", "c"),
        }

        for ext, (name, key) in extensions.items():
            files = list(self.project_root.rglob(f"*{ext}"))
            # Exclude common non-source directories
            files = [
                f
                for f in files
                if not any(
                    part in f.parts
                    for part in [
                        "node_modules",
                        "venv",
                        ".venv",
                        "build",
                        "dist",
                        "__pycache__",
                    ]
                )
            ]

            if files:
                # Try to detect version
                version = self._detect_language_version(key)
                languages[name] = version or "detected"

        return languages

    def _detect_language_version(self, language: str) -> str:
        """Detect language version from environment."""
        import shutil

        from solokit.core.command_runner import CommandRunner
        from solokit.core.constants import STACK_DETECTION_TIMEOUT
        from solokit.core.error_handlers import safe_execute

        version_commands = {
            "python": ["python3", "--version"],  # macOS has python3, not python
            "node": ["node", "--version"],
            "rust": ["rustc", "--version"],
            "go": ["go", "version"],
        }

        if language in version_commands:
            # For Python, try python3 first, fall back to python
            if language == "python":
                python_cmd = shutil.which("python3") or shutil.which("python")
                if not python_cmd:
                    return ""
                version_commands["python"] = [python_cmd, "--version"]

            def detect_version() -> str:
                runner = CommandRunner(default_timeout=STACK_DETECTION_TIMEOUT)
                result = runner.run(version_commands[language])
                if result.success:
                    # Extract version number
                    version_match = re.search(r"(\d+\.\d+(?:\.\d+)?)", result.stdout)
                    if version_match:
                        return version_match.group(1)
                return ""

            result = safe_execute(detect_version, default="", log_errors=False)
            return result or ""

        return ""

    def detect_frameworks(self) -> dict[str, list[str]]:
        """Detect frameworks from imports and config files."""
        from solokit.core.error_handlers import safe_execute

        frameworks: dict[str, list[str]] = {
            "backend": [],
            "frontend": [],
            "testing": [],
            "database": [],
        }

        # Check Python imports
        if (self.project_root / "requirements.txt").exists():
            try:
                requirements = (self.project_root / "requirements.txt").read_text()
                if "fastapi" in requirements.lower():
                    version = self._extract_version(requirements, "fastapi")
                    frameworks["backend"].append(f"FastAPI {version}")
                if "django" in requirements.lower():
                    version = self._extract_version(requirements, "django")
                    frameworks["backend"].append(f"Django {version}")
                if "flask" in requirements.lower():
                    version = self._extract_version(requirements, "flask")
                    frameworks["backend"].append(f"Flask {version}")
                if "sqlalchemy" in requirements.lower():
                    version = self._extract_version(requirements, "sqlalchemy")
                    frameworks["database"].append(f"SQLAlchemy {version}")
                if "pytest" in requirements.lower():
                    frameworks["testing"].append("pytest")
            except OSError as e:
                raise FileOperationError(
                    operation="read",
                    file_path=str(self.project_root / "requirements.txt"),
                    details=str(e),
                    cause=e,
                )

        # Check JavaScript/TypeScript frameworks
        if (self.project_root / "package.json").exists():

            def parse_package_json() -> None:
                try:
                    content = (self.project_root / "package.json").read_text()
                    package = json.loads(content)
                    deps = {
                        **package.get("dependencies", {}),
                        **package.get("devDependencies", {}),
                    }

                    if "react" in deps:
                        frameworks["frontend"].append(f"React {deps['react']}")
                    if "vue" in deps:
                        frameworks["frontend"].append(f"Vue {deps['vue']}")
                    if "next" in deps:
                        frameworks["frontend"].append(f"Next.js {deps['next']}")
                    if "jest" in deps:
                        frameworks["testing"].append("Jest")
                except json.JSONDecodeError as e:
                    raise FileOperationError(
                        operation="parse",
                        file_path=str(self.project_root / "package.json"),
                        details=f"Invalid JSON: {e}",
                        cause=e,
                    )

            safe_execute(parse_package_json, default=None, log_errors=False)

        return {k: v for k, v in frameworks.items() if v}

    def _extract_version(self, requirements: str, package: str) -> str:
        """Extract version from requirements file."""
        pattern = rf"{package}\s*[>=<~]+\s*([0-9.]+)"
        match = re.search(pattern, requirements, re.IGNORECASE)
        if match:
            return match.group(1)
        return ""

    def detect_libraries(self) -> list[str]:
        """Detect libraries from dependency files."""
        libraries = []

        # Python libraries
        if (self.project_root / "requirements.txt").exists():
            try:
                requirements = (self.project_root / "requirements.txt").read_text()
                for line in requirements.split("\n"):
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Extract package name and version
                        match = re.match(r"([a-zA-Z0-9_-]+)([>=<~]+.*)?", line)
                        if match:
                            libraries.append(line)
            except OSError as e:
                raise FileOperationError(
                    operation="read",
                    file_path=str(self.project_root / "requirements.txt"),
                    details=str(e),
                    cause=e,
                )

        return libraries[:20]  # Limit to top 20

    def detect_mcp_servers(self) -> list[str]:
        """Detect MCP servers in use."""
        from solokit.core.error_handlers import safe_execute

        mcp_servers = []

        # Check for context7 usage in code
        for py_file in self.project_root.rglob("*.py"):

            def read_py_file() -> bool:
                content = py_file.read_text()
                if "context7" in content.lower() or "mcp__context7" in content:
                    if "Context7 (library documentation)" not in mcp_servers:
                        mcp_servers.append("Context7 (library documentation)")
                        return True
                return False

            if safe_execute(read_py_file, default=False, log_errors=False):
                break  # Found it, no need to continue

        return mcp_servers

    def generate_stack_txt(self) -> str:
        """Generate stack.txt content."""
        languages = self.detect_languages()
        frameworks = self.detect_frameworks()
        libraries = self.detect_libraries()
        mcp_servers = self.detect_mcp_servers()

        lines = ["# Technology Stack\n"]

        if languages:
            lines.append("## Languages")
            for name, version in languages.items():
                lines.append(f"- {name} {version}")
            lines.append("")

        if frameworks.get("backend"):
            lines.append("## Backend Framework")
            for fw in frameworks["backend"]:
                lines.append(f"- {fw}")
            lines.append("")

        if frameworks.get("frontend"):
            lines.append("## Frontend Framework")
            for fw in frameworks["frontend"]:
                lines.append(f"- {fw}")
            lines.append("")

        if frameworks.get("database"):
            lines.append("## Database")
            for db in frameworks["database"]:
                lines.append(f"- {db}")
            lines.append("")

        if mcp_servers:
            lines.append("## MCP Servers")
            for mcp in mcp_servers:
                lines.append(f"- {mcp}")
            lines.append("")

        if frameworks.get("testing"):
            lines.append("## Testing")
            for test in frameworks["testing"]:
                lines.append(f"- {test}")
            lines.append("")

        if libraries:
            lines.append("## Key Libraries")
            for lib in libraries:
                lines.append(f"- {lib}")
            lines.append("")

        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return "\n".join(lines)

    def detect_changes(self, old_content: str, new_content: str) -> list[dict]:
        """Detect changes between old and new stack."""
        old_lines = set(old_content.split("\n"))
        new_lines = set(new_content.split("\n"))

        added = new_lines - old_lines
        removed = old_lines - new_lines

        changes = []
        for line in added:
            if line.strip() and not line.startswith("#") and not line.startswith("Generated:"):
                changes.append({"type": "addition", "content": line.strip()})

        for line in removed:
            if line.strip() and not line.startswith("#") and not line.startswith("Generated:"):
                changes.append({"type": "removal", "content": line.strip()})

        return changes

    @log_errors()
    def update_stack(
        self, session_num: int | None = None, non_interactive: bool = False
    ) -> list[dict[str, str]]:
        """Generate/update stack.txt and detect changes.

        Args:
            session_num: Current session number
            non_interactive: If True, skip interactive reasoning prompts
        """
        # Generate new stack content
        new_content = self.generate_stack_txt()

        # Load old content if exists
        old_content = ""
        if self.stack_file.exists():
            try:
                old_content = self.stack_file.read_text()
            except OSError as e:
                raise FileOperationError(
                    operation="read", file_path=str(self.stack_file), details=str(e), cause=e
                )

        # Detect changes
        changes = self.detect_changes(old_content, new_content)

        # Save new stack
        try:
            self.stack_file.parent.mkdir(parents=True, exist_ok=True)
            self.stack_file.write_text(new_content)
        except OSError as e:
            raise FileOperationError(
                operation="write", file_path=str(self.stack_file), details=str(e), cause=e
            )

        # If changes detected, prompt for reasoning (unless non-interactive)
        if changes and session_num:
            output.info(f"\n{'=' * 50}")
            output.info("Stack Changes Detected")
            output.info("=" * 50)

            for change in changes:
                output.info(f"  {change['type'].upper()}: {change['content']}")

            if non_interactive:
                reasoning = "Automated update during session completion"
                output.info("\n(Non-interactive mode: recording changes without manual reasoning)")
            else:
                output.info("\nPlease provide reasoning for these changes:")
                reasoning = input("> ")

            # Update stack_updates.json
            self._record_stack_update(session_num, changes, reasoning)

        return changes

    def _record_stack_update(
        self, session_num: int, changes: list[dict[str, Any]], reasoning: str
    ) -> None:
        """Record stack update in stack_updates.json."""
        from solokit.core.error_handlers import safe_execute

        updates: dict[str, Any] = {"updates": []}

        if self.updates_file.exists():

            def load_updates() -> dict[str, Any]:
                try:
                    content = self.updates_file.read_text()
                    return json.loads(content)  # type: ignore[no-any-return]
                except json.JSONDecodeError as e:
                    raise FileOperationError(
                        operation="parse",
                        file_path=str(self.updates_file),
                        details=f"Invalid JSON: {e}",
                        cause=e,
                    )

            loaded_updates = safe_execute(load_updates, default=None, log_errors=False)
            if loaded_updates:
                updates = loaded_updates

        update_entry = {
            "timestamp": datetime.now().isoformat(),
            "session": session_num,
            "changes": changes,
            "reasoning": reasoning,
        }

        updates["updates"].append(update_entry)

        try:
            self.updates_file.write_text(json.dumps(updates, indent=2))
        except OSError as e:
            raise FileOperationError(
                operation="write", file_path=str(self.updates_file), details=str(e), cause=e
            )


def main() -> None:
    """CLI entry point."""
    import argparse

    from solokit.core.output import get_output

    output = get_output()

    parser = argparse.ArgumentParser(description="Generate technology stack documentation")
    parser.add_argument("--session", type=int, help="Current session number")
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Skip interactive prompts (use automated reasoning)",
    )
    args = parser.parse_args()

    generator = StackGenerator()
    changes = generator.update_stack(session_num=args.session, non_interactive=args.non_interactive)

    if changes:
        output.info(f"\n✓ Stack updated with {len(changes)} changes")
    else:
        output.info("\n✓ Stack generated (no changes)")

    output.info(f"✓ Saved to: {generator.stack_file}")


if __name__ == "__main__":
    main()
