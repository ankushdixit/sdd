"""
Test authentication module for Phase 1 testing.
This simulates work being done during a session.
"""


class UserAuth:
    """Basic user authentication."""

    def __init__(self):
        self.users = {}

    def register(self, email, password):
        """Register a new user."""
        if email in self.users:
            return False, "User already exists"
        self.users[email] = password
        return True, "User registered successfully"

    def login(self, email, password):
        """Login user."""
        if email not in self.users:
            return False, "User not found"
        if self.users[email] != password:
            return False, "Invalid password"
        return True, "Login successful"
