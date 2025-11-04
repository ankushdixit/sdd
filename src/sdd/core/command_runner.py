"""Centralized command execution with consistent error handling.

This module provides a unified interface for running subprocess commands
with standardized timeout handling, error handling, logging, and retry logic.
"""

import json
import logging
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class CommandResult:
    """Result of a command execution."""

    returncode: int
    stdout: str
    stderr: str
    command: list[str]
    duration_seconds: float
    timed_out: bool = False

    @property
    def success(self) -> bool:
        """Whether command succeeded."""
        return self.returncode == 0 and not self.timed_out

    @property
    def output(self) -> str:
        """Get stdout or stderr if stdout empty."""
        return self.stdout.strip() if self.stdout else self.stderr.strip()


class CommandExecutionError(Exception):
    """Raised when command execution fails."""

    def __init__(self, message: str, result: Optional[CommandResult] = None):
        """Initialize error with message and optional result."""
        super().__init__(message)
        self.result = result


class CommandRunner:
    """Centralized command execution with consistent error handling."""

    DEFAULT_TIMEOUT = 30  # seconds

    def __init__(
        self,
        default_timeout: float = DEFAULT_TIMEOUT,
        working_dir: Optional[Path] = None,
        raise_on_error: bool = False,
    ):
        """Initialize command runner.

        Args:
            default_timeout: Default timeout in seconds
            working_dir: Working directory for commands (None = current)
            raise_on_error: Whether to raise exception on non-zero exit
        """
        self.default_timeout = default_timeout
        self.working_dir = working_dir
        self.raise_on_error = raise_on_error

    def run(
        self,
        command: Union[str, list[str]],
        timeout: Optional[float] = None,
        check: Optional[bool] = None,
        working_dir: Optional[Path] = None,
        retry_count: int = 0,
        retry_delay: float = 1.0,
        env: Optional[dict] = None,
    ) -> CommandResult:
        """Run a command with consistent error handling.

        Args:
            command: Command to run (string or list)
            timeout: Timeout in seconds (None = use default)
            check: Raise exception on non-zero exit (None = use instance setting)
            working_dir: Working directory (None = use instance setting)
            retry_count: Number of retries on failure
            retry_delay: Delay between retries in seconds
            env: Environment variables

        Returns:
            CommandResult with output and status

        Raises:
            CommandExecutionError: If check=True and command fails
        """
        if isinstance(command, str):
            command = command.split()

        timeout = timeout if timeout is not None else self.default_timeout
        check = check if check is not None else self.raise_on_error
        cwd = working_dir or self.working_dir

        attempt = 0
        max_attempts = retry_count + 1

        while attempt < max_attempts:
            try:
                start_time = time.time()

                logger.debug(
                    f"Running command: {' '.join(command)} "
                    f"(timeout={timeout}s, cwd={cwd}, attempt={attempt + 1}/{max_attempts})"
                )

                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    check=False,  # We handle errors ourselves
                    cwd=cwd,
                    env=env,
                )

                duration = time.time() - start_time

                cmd_result = CommandResult(
                    returncode=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    command=command,
                    duration_seconds=duration,
                )

                if cmd_result.success:
                    logger.debug(f"Command succeeded in {duration:.2f}s")
                    return cmd_result

                # Command failed
                logger.warning(
                    f"Command failed with exit code {result.returncode}: "
                    f"{' '.join(command)}\nstderr: {result.stderr[:200]}"
                )

                if check:
                    raise CommandExecutionError(
                        f"Command failed with exit code {result.returncode}: "
                        f"{' '.join(command)}\nstderr: {result.stderr}",
                        result=cmd_result,
                    )

                # Retry if configured
                if attempt < max_attempts - 1:
                    logger.info(f"Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    attempt += 1
                    continue

                return cmd_result

            except subprocess.TimeoutExpired as e:
                duration = time.time() - start_time

                logger.error(f"Command timed out after {timeout}s: {' '.join(command)}")

                cmd_result = CommandResult(
                    returncode=-1,
                    stdout=e.stdout or "",
                    stderr=e.stderr or "",
                    command=command,
                    duration_seconds=duration,
                    timed_out=True,
                )

                if check:
                    raise CommandExecutionError(
                        f"Command timed out after {timeout}s: {' '.join(command)}",
                        result=cmd_result,
                    ) from e

                # Retry if configured
                if attempt < max_attempts - 1:
                    logger.info(f"Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    attempt += 1
                    continue

                return cmd_result

            except CommandExecutionError:
                # Re-raise CommandExecutionError as-is (don't catch and re-wrap)
                raise
            except Exception as e:
                logger.error(f"Unexpected error running command: {e}")

                if check:
                    raise CommandExecutionError(f"Unexpected error running command: {e}") from e

                # Don't retry on unexpected errors
                return CommandResult(
                    returncode=-1,
                    stdout="",
                    stderr=str(e),
                    command=command,
                    duration_seconds=time.time() - start_time,
                )

        # Should never reach here
        raise RuntimeError("Retry logic error")

    def run_json(self, command: Union[str, list[str]], **kwargs) -> Optional[dict]:
        """Run command and parse JSON output.

        Returns:
            Parsed JSON dict or None if parse fails
        """
        result = self.run(command, **kwargs)
        if not result.success:
            return None

        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON output: {e}")
            return None

    def run_lines(self, command: Union[str, list[str]], **kwargs) -> list[str]:
        """Run command and return output as lines.

        Returns:
            List of non-empty lines
        """
        result = self.run(command, **kwargs)
        if not result.success:
            return []

        return [line.strip() for line in result.stdout.split("\n") if line.strip()]


# Global instance for convenience
_default_runner = CommandRunner()


def run_command(command: Union[str, list[str]], **kwargs) -> CommandResult:
    """Convenience function to run command with default runner."""
    return _default_runner.run(command, **kwargs)
