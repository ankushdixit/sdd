"""Unit tests for performance module"""

import time
from unittest.mock import patch

import pytest
from solokit.core.performance import Timer, measure_time


class TestMeasureTime:
    """Test cases for measure_time decorator"""

    def test_measure_time_default_name(self):
        """Test measure_time with default operation name"""

        @measure_time()
        def sample_function():
            return "result"

        with patch("solokit.core.performance.logger") as mock_logger:
            result = sample_function()
            assert result == "result"
            # Should not log for fast operations
            mock_logger.info.assert_not_called()
            mock_logger.warning.assert_not_called()

    def test_measure_time_custom_name(self):
        """Test measure_time with custom operation name"""

        @measure_time(operation="custom_operation")
        def sample_function():
            return "result"

        with patch("solokit.core.performance.logger"):
            result = sample_function()
            assert result == "result"

    def test_measure_time_slow_operation(self):
        """Test measure_time logs slow operations"""

        @measure_time(operation="slow_operation")
        def slow_function():
            time.sleep(0.15)  # Slightly over 100ms threshold
            return "result"

        with patch("solokit.core.performance.logger") as mock_logger:
            result = slow_function()
            assert result == "result"
            # Should log info for operations > 100ms
            assert mock_logger.info.called or mock_logger.warning.called

    def test_measure_time_very_slow_operation(self):
        """Test measure_time warns for very slow operations"""

        @measure_time(operation="very_slow_operation")
        def very_slow_function():
            time.sleep(1.1)  # Over 1s threshold
            return "result"

        with patch("solokit.core.performance.logger") as mock_logger:
            result = very_slow_function()
            assert result == "result"
            # Should log warning for operations > 1s
            mock_logger.warning.assert_called()

    def test_measure_time_with_exception(self):
        """Test measure_time still logs when exception is raised"""

        @measure_time(operation="failing_operation")
        def failing_function():
            time.sleep(0.15)
            raise ValueError("Test error")

        with patch("solokit.core.performance.logger") as mock_logger:
            with pytest.raises(ValueError, match="Test error"):
                failing_function()
            # Should still log performance even when exception occurs
            assert mock_logger.info.called or mock_logger.warning.called

    def test_measure_time_preserves_function_metadata(self):
        """Test that decorator preserves function metadata"""

        @measure_time()
        def sample_function():
            """Sample docstring"""
            return "result"

        assert sample_function.__name__ == "sample_function"
        assert sample_function.__doc__ == "Sample docstring"

    def test_measure_time_with_arguments(self):
        """Test measure_time works with function arguments"""

        @measure_time()
        def function_with_args(a, b, c=None):
            return (a, b, c)

        result = function_with_args(1, 2, c=3)
        assert result == (1, 2, 3)


class TestTimer:
    """Test cases for Timer context manager"""

    def test_timer_context_manager(self):
        """Test Timer as context manager"""
        with Timer("test_operation") as timer:
            time.sleep(0.01)

        assert timer.duration is not None
        assert timer.duration >= 0.01
        assert timer.start is not None

    def test_timer_logs_slow_operations(self):
        """Test Timer logs operations > 100ms"""
        with patch("solokit.core.performance.logger") as mock_logger:
            with Timer("slow_operation"):
                time.sleep(0.15)

            mock_logger.info.assert_called()

    def test_timer_does_not_log_fast_operations(self):
        """Test Timer doesn't log operations < 100ms"""
        with patch("solokit.core.performance.logger") as mock_logger:
            with Timer("fast_operation"):
                time.sleep(0.01)

            mock_logger.info.assert_not_called()

    def test_timer_name(self):
        """Test Timer stores operation name"""
        timer = Timer("my_operation")
        assert timer.name == "my_operation"

    def test_timer_duration_available_after_exit(self):
        """Test timer duration is available after context exit"""
        with Timer("test_operation") as timer:
            time.sleep(0.01)

        # Duration should be set after exiting context
        assert timer.duration is not None
        assert timer.duration >= 0.01

    def test_timer_with_exception(self):
        """Test Timer still measures time when exception occurs"""
        with patch("solokit.core.performance.logger") as mock_logger:
            try:
                with Timer("failing_operation") as timer:
                    time.sleep(0.15)
                    raise ValueError("Test error")
            except ValueError:
                pass

            # Duration should still be recorded
            assert timer.duration is not None
            assert timer.duration >= 0.15
            # Should still log
            mock_logger.info.assert_called()
