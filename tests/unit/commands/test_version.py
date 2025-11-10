"""Unit tests for version command."""

import platform
import sys

from solokit.__version__ import __version__
from solokit.commands.version import show_version


def test_version_shows_version_number(capsys):
    """Test that version command displays the version number."""
    result = show_version()

    captured = capsys.readouterr()
    assert f"solokit version {__version__}" in captured.out
    assert result == 0


def test_version_shows_python_version(capsys):
    """Test that version command displays Python version."""
    result = show_version()

    captured = capsys.readouterr()
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    assert f"Python {python_version}" in captured.out
    assert result == 0


def test_version_shows_platform(capsys):
    """Test that version command displays platform information."""
    result = show_version()

    captured = capsys.readouterr()
    platform_name = platform.system()
    assert platform_name in captured.out
    assert result == 0


def test_version_returns_success_code():
    """Test that version command returns exit code 0."""
    result = show_version()
    assert result == 0
