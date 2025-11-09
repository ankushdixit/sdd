"""
Tests for initial_scans module.

Validates initial stack and tree scan execution.

Run tests:
    pytest tests/unit/init/test_initial_scans.py -v

Target: 90%+ coverage
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from sdd.init.initial_scans import run_stack_scan, run_tree_scan, run_initial_scans


class TestRunStackScan:
    """Tests for run_stack_scan()."""

    def test_stack_scan_success(self, tmp_path):
        """Test successful stack scan."""
        with patch("sdd.init.initial_scans.CommandRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            mock_runner.run.return_value = Mock(success=True)

            result = run_stack_scan(tmp_path)

            assert result is True

    def test_stack_scan_failure(self, tmp_path):
        """Test stack scan failure."""
        with patch("sdd.init.initial_scans.CommandRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            mock_runner.run.return_value = Mock(success=False, stderr="Error")

            result = run_stack_scan(tmp_path)

            assert result is False

    def test_stack_script_not_found(self, tmp_path):
        """Test when stack.py script doesn't exist."""
        # Mock __file__ at module level to point to a fake location
        import sdd.init.initial_scans as initial_scans_module

        with patch.object(initial_scans_module, "__file__", "/fake/sdd/init/initial_scans.py"):
            # Now Path(__file__).parent.parent / "project" / "stack.py" will be /fake/sdd/project/stack.py
            # which doesn't exist
            result = run_stack_scan(tmp_path)

            assert result is False


class TestRunTreeScan:
    """Tests for run_tree_scan()."""

    def test_tree_scan_success(self, tmp_path):
        """Test successful tree scan."""
        with patch("sdd.init.initial_scans.CommandRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            mock_runner.run.return_value = Mock(success=True)

            result = run_tree_scan(tmp_path)

            assert result is True

    def test_tree_scan_failure(self, tmp_path):
        """Test tree scan failure."""
        with patch("sdd.init.initial_scans.CommandRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            mock_runner.run.return_value = Mock(success=False)

            result = run_tree_scan(tmp_path)

            assert result is False


class TestRunInitialScans:
    """Tests for run_initial_scans()."""

    def test_run_both_scans(self, tmp_path):
        """Test running both stack and tree scans."""
        with patch("sdd.init.initial_scans.run_stack_scan") as mock_stack:
            with patch("sdd.init.initial_scans.run_tree_scan") as mock_tree:
                mock_stack.return_value = True
                mock_tree.return_value = True

                results = run_initial_scans(tmp_path)

                assert results["stack"] is True
                assert results["tree"] is True
                mock_stack.assert_called_once()
                mock_tree.assert_called_once()

    def test_partial_success(self, tmp_path):
        """Test when only one scan succeeds."""
        with patch("sdd.init.initial_scans.run_stack_scan") as mock_stack:
            with patch("sdd.init.initial_scans.run_tree_scan") as mock_tree:
                mock_stack.return_value = True
                mock_tree.return_value = False

                results = run_initial_scans(tmp_path)

                assert results["stack"] is True
                assert results["tree"] is False
