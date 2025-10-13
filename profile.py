"""User profile model - Session 1 partial work."""


class UserProfile:
    """User profile model."""

    def __init__(self, user_id, name, email):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.bio = ""
        self.avatar_url = None

    def __repr__(self):
        return f"UserProfile(id={self.user_id}, name={self.name})"
