"""User profile model - Session 2: Adding CRUD operations."""


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

    def update_bio(self, bio):
        """Update user bio."""
        self.bio = bio
        return True

    def set_avatar(self, url):
        """Set avatar URL."""
        self.avatar_url = url
        return True

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "bio": self.bio,
            "avatar_url": self.avatar_url,
        }
