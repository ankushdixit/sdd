"""Unit tests for doctor command."""

import pytest

from solokit.commands.doctor import (
    check_python_version,
    parse_version,
    run_diagnostics,
)


def test_parse_version_standard():
    """Test parsing standard version string."""
    assert parse_version("3.11.7") == (3, 11, 7)
    assert parse_version("2.45.0") == (2, 45, 0)


def test_parse_version_with_v_prefix():
    """Test parsing version string with 'v' prefix."""
    assert parse_version("v3.11.7") == (3, 11, 7)
    assert parse_version("v2.45.0") == (2, 45, 0)


def test_parse_version_without_patch():
    """Test parsing version string without patch version."""
    assert parse_version("3.11") == (3, 11, 0)


def test_parse_version_invalid():
    """Test parsing invalid version string."""
    with pytest.raises(ValueError):
        parse_version("invalid")


def test_check_python_version_passes():
    """Test that Python version check passes for current Python."""
    result = check_python_version()
    # Current Python should meet minimum requirements (3.9+)
    assert result.passed is True
    assert "Python" in result.message
    assert result.name == "Python Version"


def test_run_diagnostics_returns_exit_code(capsys):
    """Test that run_diagnostics returns appropriate exit code."""
    result = run_diagnostics(verbose=False)
    # Result should be 0 or 1
    assert result in [0, 1]

    captured = capsys.readouterr()
    assert "Running system diagnostics" in captured.out
    assert "checks passed" in captured.out
