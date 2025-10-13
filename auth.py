"""Simple authentication module for testing."""


class Auth:
    """Basic authentication handler."""

    def __init__(self):
        self.users = {}

    def register(self, username, password):
        """Register a new user."""
        if username in self.users:
            return False
        self.users[username] = password
        return True

    def login(self, username, password):
        """Authenticate user."""
        return self.users.get(username) == password
