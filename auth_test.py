"""Tests for auth module."""

from auth import Auth


def test_register():
    """Test user registration."""
    auth = Auth()
    assert auth.register("user1", "pass123") is True
    assert auth.register("user1", "pass456") is False


def test_login():
    """Test user login."""
    auth = Auth()
    auth.register("user1", "pass123")
    assert auth.login("user1", "pass123") is True
    assert auth.login("user1", "wrongpass") is False
    assert auth.login("nonexistent", "pass") is False
