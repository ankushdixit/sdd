"""Profile model - Session 3: Complete with validation."""

import re


class Profile:
    """User profile model."""

    def __init__(self, user_id, name, email):
        if not self._validate_email(email):
            raise ValueError("Invalid email")
        self.user_id = user_id
        self.name = name
        self.email = email
        self.bio = ""

    @staticmethod
    def _validate_email(email):
        """Validate email format."""
        return (
            re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email)
            is not None
        )

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
