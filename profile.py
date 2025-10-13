"""Profile model - Session 2: Adding CRUD operations."""


class Profile:
    """User profile model."""

    def __init__(self, user_id, name, email):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.bio = ""

    def __repr__(self):
        return f"Profile(id={self.user_id}, name={self.name})"

    def update_bio(self, bio):
        """Update profile bio."""
        self.bio = bio
        return True

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "bio": self.bio,
        }
