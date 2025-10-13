"""Tests for auth module."""

from test_auth import UserAuth


def test_register():
    """Test user registration."""
    auth = UserAuth()
    success, msg = auth.register("test@example.com", "password123")
    assert success is True
    assert "success" in msg.lower()


def test_login():
    """Test user login."""
    auth = UserAuth()
    auth.register("test@example.com", "password123")
    success, msg = auth.login("test@example.com", "password123")
    assert success is True
    assert "success" in msg.lower()


def test_login_invalid_password():
    """Test login with invalid password."""
    auth = UserAuth()
    auth.register("test@example.com", "password123")
    success, msg = auth.login("test@example.com", "wrongpassword")
    assert success is False
    assert "password" in msg.lower()
