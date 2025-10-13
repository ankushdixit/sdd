"""Tests for profile module."""

from profile import Profile


def test_profile_creation():
    """Test profile creation."""
    profile = Profile(1, "Test User", "test@example.com")
    assert profile.user_id == 1
    assert profile.name == "Test User"
