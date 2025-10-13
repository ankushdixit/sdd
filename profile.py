"""User profile model - Session 3: Complete with validation."""

import re


class UserProfile:
    """User profile model."""

    def __init__(self, user_id, name, email):
        if not self._validate_email(email):
            raise ValueError("Invalid email format")
        self.user_id = user_id
        self.name = name
        self.email = email
        self.bio = ""
        self.avatar_url = None

    @staticmethod
    def _validate_email(email):
        """Validate email format."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

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
