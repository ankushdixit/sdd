"""
Tests for initial_scans module.

Validates initial stack and tree scan execution.

Run tests:
    pytest tests/unit/init/test_initial_scans.py -v

Target: 90%+ coverage
"""

from unittest.mock import Mock, patch

from solokit.init.initial_scans import run_initial_scans, run_stack_scan, run_tree_scan


class TestRunStackScan:
    """Tests for run_stack_scan()."""

    def test_stack_scan_success(self, tmp_path):
        """Test successful stack scan."""
        with patch("solokit.init.initial_scans.CommandRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            mock_runner.run.return_value = Mock(success=True)

            result = run_stack_scan(tmp_path)

            assert result is True

    def test_stack_scan_failure(self, tmp_path):
        """Test stack scan failure."""
        with patch("solokit.init.initial_scans.CommandRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            mock_runner.run.return_value = Mock(success=False, stderr="Error")

            result = run_stack_scan(tmp_path)

            assert result is False

    def test_stack_script_not_found(self, tmp_path):
        """Test when stack.py script doesn't exist."""
        # Mock __file__ at module level to point to a fake location
        import solokit.init.initial_scans as initial_scans_module

        with patch.object(initial_scans_module, "__file__", "/fake/solokit/init/initial_scans.py"):
            # Now Path(__file__).parent.parent / "project" / "stack.py" will be /fake/solokit/project/stack.py
            # which doesn't exist
            result = run_stack_scan(tmp_path)

            assert result is False


class TestRunTreeScan:
    """Tests for run_tree_scan()."""

    def test_tree_scan_success(self, tmp_path):
        """Test successful tree scan."""
        with patch("solokit.init.initial_scans.CommandRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            mock_runner.run.return_value = Mock(success=True)

            result = run_tree_scan(tmp_path)

            assert result is True

    def test_tree_scan_failure(self, tmp_path):
        """Test tree scan failure."""
        with patch("solokit.init.initial_scans.CommandRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            mock_runner.run.return_value = Mock(success=False)

            result = run_tree_scan(tmp_path)

            assert result is False


class TestRunInitialScans:
    """Tests for run_initial_scans()."""

    def test_run_both_scans(self, tmp_path):
        """Test running both stack and tree scans."""
        with patch("solokit.init.initial_scans.run_stack_scan") as mock_stack:
            with patch("solokit.init.initial_scans.run_tree_scan") as mock_tree:
                mock_stack.return_value = True
                mock_tree.return_value = True

                results = run_initial_scans(tmp_path)

                assert results["stack"] is True
                assert results["tree"] is True
                mock_stack.assert_called_once()
                mock_tree.assert_called_once()

    def test_partial_success(self, tmp_path):
        """Test when only one scan succeeds."""
        with patch("solokit.init.initial_scans.run_stack_scan") as mock_stack:
            with patch("solokit.init.initial_scans.run_tree_scan") as mock_tree:
                mock_stack.return_value = True
                mock_tree.return_value = False

                results = run_initial_scans(tmp_path)

                assert results["stack"] is True
                assert results["tree"] is False

    def test_both_scans_fail(self, tmp_path):
        """Test when both scans fail."""
        with patch("solokit.init.initial_scans.run_stack_scan") as mock_stack:
            with patch("solokit.init.initial_scans.run_tree_scan") as mock_tree:
                mock_stack.return_value = False
                mock_tree.return_value = False

                results = run_initial_scans(tmp_path)

                assert results["stack"] is False
                assert results["tree"] is False

    def test_default_project_root(self):
        """Test run_initial_scans with default project root."""
        with patch("solokit.init.initial_scans.run_stack_scan") as mock_stack:
            with patch("solokit.init.initial_scans.run_tree_scan") as mock_tree:
                mock_stack.return_value = True
                mock_tree.return_value = True

                results = run_initial_scans()

                assert results["stack"] is True
                assert results["tree"] is True


class TestRunStackScanEdgeCases:
    """Additional edge case tests for run_stack_scan."""

    def test_stack_scan_exception(self, tmp_path):
        """Test stack scan handles exception gracefully."""
        with patch("solokit.init.initial_scans.CommandRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            mock_runner.run.side_effect = Exception("Unexpected error")

            result = run_stack_scan(tmp_path)

            assert result is False

    def test_stack_scan_with_stderr_message(self, tmp_path):
        """Test stack scan logs stderr when command fails."""
        with patch("solokit.init.initial_scans.CommandRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            mock_runner.run.return_value = Mock(success=False, stderr="Stack generation error")

            result = run_stack_scan(tmp_path)

            assert result is False

    def test_stack_scan_default_project_root(self):
        """Test stack scan with default project root (None)."""
        with patch("solokit.init.initial_scans.CommandRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            mock_runner.run.return_value = Mock(success=True)

            result = run_stack_scan(None)

            assert result is True

    def test_stack_scan_command_runner_check_flag(self, tmp_path):
        """Test stack scan uses check=True flag."""
        with patch("solokit.init.initial_scans.CommandRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            mock_runner.run.return_value = Mock(success=True)

            run_stack_scan(tmp_path)

            # Verify check=True was passed
            call_args = mock_runner.run.call_args
            assert call_args[1]["check"] is True


class TestRunTreeScanEdgeCases:
    """Additional edge case tests for run_tree_scan."""

    def test_tree_scan_exception(self, tmp_path):
        """Test tree scan handles exception gracefully."""
        with patch("solokit.init.initial_scans.CommandRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            mock_runner.run.side_effect = Exception("Unexpected error")

            result = run_tree_scan(tmp_path)

            assert result is False

    def test_tree_scan_with_stderr_message(self, tmp_path):
        """Test tree scan logs stderr when command fails."""
        with patch("solokit.init.initial_scans.CommandRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            mock_runner.run.return_value = Mock(success=False, stderr="Tree generation error")

            result = run_tree_scan(tmp_path)

            assert result is False

    def test_tree_scan_default_project_root(self):
        """Test tree scan with default project root (None)."""
        with patch("solokit.init.initial_scans.CommandRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            mock_runner.run.return_value = Mock(success=True)

            result = run_tree_scan(None)

            assert result is True

    def test_tree_script_not_found(self, tmp_path):
        """Test when tree.py script doesn't exist."""
        import solokit.init.initial_scans as initial_scans_module

        with patch.object(initial_scans_module, "__file__", "/fake/solokit/init/initial_scans.py"):
            result = run_tree_scan(tmp_path)

            assert result is False

    def test_tree_scan_command_runner_check_flag(self, tmp_path):
        """Test tree scan uses check=True flag."""
        with patch("solokit.init.initial_scans.CommandRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            mock_runner.run.return_value = Mock(success=True)

            run_tree_scan(tmp_path)

            # Verify check=True was passed
            call_args = mock_runner.run.call_args
            assert call_args[1]["check"] is True


class TestCommandRunnerIntegration:
    """Test CommandRunner integration with scans."""

    def test_stack_scan_uses_correct_timeout(self, tmp_path):
        """Test stack scan initializes CommandRunner with correct timeout."""
        with patch("solokit.init.initial_scans.CommandRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            mock_runner.run.return_value = Mock(success=True)

            run_stack_scan(tmp_path)

            # Verify CommandRunner was initialized with GIT_STANDARD_TIMEOUT
            from solokit.core.constants import GIT_STANDARD_TIMEOUT

            mock_runner_class.assert_called_once()
            call_kwargs = mock_runner_class.call_args[1]
            assert call_kwargs["default_timeout"] == GIT_STANDARD_TIMEOUT
            assert call_kwargs["working_dir"] == tmp_path

    def test_tree_scan_uses_correct_timeout(self, tmp_path):
        """Test tree scan initializes CommandRunner with correct timeout."""
        with patch("solokit.init.initial_scans.CommandRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            mock_runner.run.return_value = Mock(success=True)

            run_tree_scan(tmp_path)

            # Verify CommandRunner was initialized with GIT_STANDARD_TIMEOUT
            from solokit.core.constants import GIT_STANDARD_TIMEOUT

            mock_runner_class.assert_called_once()
            call_kwargs = mock_runner_class.call_args[1]
            assert call_kwargs["default_timeout"] == GIT_STANDARD_TIMEOUT
            assert call_kwargs["working_dir"] == tmp_path

    def test_stack_scan_uses_sys_executable(self, tmp_path):
        """Test stack scan uses sys.executable for Python interpreter."""
        import sys

        with patch("solokit.init.initial_scans.CommandRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            mock_runner.run.return_value = Mock(success=True)

            run_stack_scan(tmp_path)

            # Verify sys.executable was used in the command
            call_args = mock_runner.run.call_args[0][0]
            assert call_args[0] == sys.executable

    def test_tree_scan_uses_sys_executable(self, tmp_path):
        """Test tree scan uses sys.executable for Python interpreter."""
        import sys

        with patch("solokit.init.initial_scans.CommandRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner_class.return_value = mock_runner
            mock_runner.run.return_value = Mock(success=True)

            run_tree_scan(tmp_path)

            # Verify sys.executable was used in the command
            call_args = mock_runner.run.call_args[0][0]
            assert call_args[0] == sys.executable
