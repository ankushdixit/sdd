"""Profile model - Session 1."""


class Profile:
    """User profile model."""

    def __init__(self, user_id, name, email):
        self.user_id = user_id
        self.name = name
        self.email = email

    def __repr__(self):
        return f"Profile(id={self.user_id}, name={self.name})"
