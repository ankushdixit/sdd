"""Type definitions for SDD work items.

This module provides type-safe enums for work item properties, replacing
magic strings throughout the codebase. All enums inherit from str for
JSON serialization compatibility.
"""

from enum import Enum


class WorkItemType(str, Enum):
    """Work item types.

    Defines all valid work item types in the SDD system.
    """

    FEATURE = "feature"
    BUG = "bug"
    REFACTOR = "refactor"
    SECURITY = "security"
    INTEGRATION_TEST = "integration_test"
    DEPLOYMENT = "deployment"

    def __str__(self) -> str:
        """Return the string value of the enum."""
        return self.value

    @classmethod
    def values(cls) -> list[str]:
        """Return list of all valid work item type values."""
        return [item.value for item in cls]


class WorkItemStatus(str, Enum):
    """Work item statuses.

    Defines all valid work item statuses in the SDD system.
    """

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"

    def __str__(self) -> str:
        """Return the string value of the enum."""
        return self.value

    @classmethod
    def values(cls) -> list[str]:
        """Return list of all valid work item status values."""
        return [item.value for item in cls]


class Priority(str, Enum):
    """Priority levels.

    Defines all valid priority levels in the SDD system.
    Supports comparison operations for ordering.
    """

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    def __str__(self) -> str:
        """Return the string value of the enum."""
        return self.value

    def __lt__(self, other: "Priority") -> bool:
        """Enable priority comparison.

        Lower numeric order = higher priority:
        CRITICAL (0) < HIGH (1) < MEDIUM (2) < LOW (3)

        Args:
            other: Another Priority enum to compare against

        Returns:
            True if this priority is higher than other

        Raises:
            TypeError: If other is not a Priority enum
        """
        if not isinstance(other, Priority):
            raise TypeError(f"Cannot compare Priority with {type(other)}")

        order = {Priority.CRITICAL: 0, Priority.HIGH: 1, Priority.MEDIUM: 2, Priority.LOW: 3}
        return order[self] < order[other]

    def __le__(self, other: "Priority") -> bool:
        """Enable priority less-than-or-equal comparison."""
        if not isinstance(other, Priority):
            raise TypeError(f"Cannot compare Priority with {type(other)}")
        return self == other or self < other

    def __gt__(self, other: "Priority") -> bool:
        """Enable priority greater-than comparison."""
        if not isinstance(other, Priority):
            raise TypeError(f"Cannot compare Priority with {type(other)}")
        return not self <= other

    def __ge__(self, other: "Priority") -> bool:
        """Enable priority greater-than-or-equal comparison."""
        if not isinstance(other, Priority):
            raise TypeError(f"Cannot compare Priority with {type(other)}")
        return not self < other

    @classmethod
    def values(cls) -> list[str]:
        """Return list of all valid priority values."""
        return [item.value for item in cls]


class GitStatus(str, Enum):
    """Git workflow statuses for work items.

    Tracks the git workflow state of work item branches through their lifecycle.
    """

    IN_PROGRESS = "in_progress"
    READY_TO_MERGE = "ready_to_merge"
    READY_FOR_PR = "ready_for_pr"
    PR_CREATED = "pr_created"
    MERGED = "merged"

    def __str__(self) -> str:
        """Return the string value of the enum."""
        return self.value

    @classmethod
    def values(cls) -> list[str]:
        """Return list of all valid git status values."""
        return [item.value for item in cls]
