"""Tests for profile module."""

from profile import UserProfile


def test_profile_creation():
    """Test profile creation."""
    profile = UserProfile(1, "Test User", "test@example.com")
    assert profile.user_id == 1
    assert profile.name == "Test User"
    assert profile.email == "test@example.com"
