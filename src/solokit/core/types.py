"""Type definitions for Solokit work items.

This module provides type-safe enums for work item properties, replacing
magic strings throughout the codebase. All enums inherit from str for
JSON serialization compatibility.

It also provides TypedDict definitions for structured data and type aliases
for improved code clarity.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, TypedDict

from solokit.core.exceptions import ErrorCode, ValidationError


class WorkItemType(str, Enum):
    """Work item types.

    Defines all valid work item types in the Solokit system.
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

    @classmethod
    def _missing_(cls, value: object) -> WorkItemType:
        """Handle invalid work item types with ValidationError."""
        valid_types = ", ".join(cls.values())
        raise ValidationError(
            message=f"Invalid work item type '{value}'. Valid types: {valid_types}",
            code=ErrorCode.INVALID_WORK_ITEM_TYPE,
            context={"work_item_type": value, "valid_types": cls.values()},
            remediation=f"Choose one of the valid work item types: {valid_types}",
        )


class WorkItemStatus(str, Enum):
    """Work item statuses.

    Defines all valid work item statuses in the Solokit system.
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

    @classmethod
    def _missing_(cls, value: object) -> WorkItemStatus:
        """Handle invalid work item status with ValidationError."""
        valid_statuses = ", ".join(cls.values())
        raise ValidationError(
            message=f"Invalid status '{value}'. Valid statuses: {valid_statuses}",
            code=ErrorCode.INVALID_STATUS,
            context={"status": value, "valid_statuses": cls.values()},
            remediation=f"Choose one of the valid statuses: {valid_statuses}",
        )


class Priority(str, Enum):
    """Priority levels.

    Defines all valid priority levels in the Solokit system.
    Supports comparison operations for ordering.
    """

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    def __str__(self) -> str:
        """Return the string value of the enum."""
        return self.value

    def __lt__(self, other: object) -> bool:
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

    def __le__(self, other: object) -> bool:
        """Enable priority less-than-or-equal comparison."""
        if not isinstance(other, Priority):
            raise TypeError(f"Cannot compare Priority with {type(other)}")
        return self == other or self < other

    def __gt__(self, other: object) -> bool:
        """Enable priority greater-than comparison."""
        if not isinstance(other, Priority):
            raise TypeError(f"Cannot compare Priority with {type(other)}")
        return not self <= other

    def __ge__(self, other: object) -> bool:
        """Enable priority greater-than-or-equal comparison."""
        if not isinstance(other, Priority):
            raise TypeError(f"Cannot compare Priority with {type(other)}")
        return not self < other

    @classmethod
    def values(cls) -> list[str]:
        """Return list of all valid priority values."""
        return [item.value for item in cls]

    @classmethod
    def _missing_(cls, value: object) -> Priority:
        """Handle invalid priority with ValidationError."""
        valid_priorities = ", ".join(cls.values())
        raise ValidationError(
            message=f"Invalid priority '{value}'. Valid priorities: {valid_priorities}",
            code=ErrorCode.INVALID_PRIORITY,
            context={"priority": value, "valid_priorities": cls.values()},
            remediation=f"Choose one of the valid priorities: {valid_priorities}",
        )


class GitStatus(str, Enum):
    """Git workflow statuses for work items.

    Tracks the git workflow state of work item branches through their lifecycle.
    """

    IN_PROGRESS = "in_progress"
    READY_TO_MERGE = "ready_to_merge"
    READY_FOR_PR = "ready_for_pr"
    PR_CREATED = "pr_created"
    PR_CLOSED = "pr_closed"
    MERGED = "merged"
    DELETED = "deleted"

    def __str__(self) -> str:
        """Return the string value of the enum."""
        return self.value

    @classmethod
    def values(cls) -> list[str]:
        """Return list of all valid git status values."""
        return [item.value for item in cls]


# Type Aliases
WorkItemID = str
"""Type alias for work item identifiers."""

MilestoneID = str
"""Type alias for milestone identifiers."""

SessionID = int
"""Type alias for session identifiers."""


# TypedDict Definitions
class WorkItemDict(TypedDict, total=False):
    """Typed dictionary for work item data structure.

    Attributes:
        id: Unique work item identifier
        type: Type of work item (feature, bug, etc.)
        title: Human-readable title
        status: Current status (not_started, in_progress, etc.)
        priority: Priority level (critical, high, medium, low)
        urgent: Whether this item requires immediate attention (only one can be urgent at a time)
        description: Detailed description
        dependencies: List of work item IDs this depends on
        milestone: Optional milestone this belongs to
        created_at: ISO format timestamp of creation
        updated_at: ISO format timestamp of last update
        spec_file: Path to specification file
        git_status: Git workflow status
        git_branch: Git branch name
    """

    id: WorkItemID
    type: str
    title: str
    status: str
    priority: str
    urgent: bool
    description: str
    dependencies: list[WorkItemID]
    milestone: str
    created_at: str
    updated_at: str
    spec_file: str
    git_status: str
    git_branch: str


class WorkItemsData(TypedDict):
    """Typed dictionary for work_items.json file structure.

    Attributes:
        work_items: Dictionary mapping work item IDs to work item data
        metadata: Additional metadata about the work items collection
    """

    work_items: dict[WorkItemID, WorkItemDict]
    metadata: dict[str, Any]


class LearningDict(TypedDict, total=False):
    """Typed dictionary for learning entry data structure.

    Attributes:
        id: Unique learning identifier
        session_id: Session where learning was captured
        work_item_id: Work item associated with learning
        category: Learning category (best_practices, gotcha, etc.)
        content: Learning content/description
        tags: List of tags for categorization
        created_at: ISO format timestamp
        context: Additional context information
    """

    id: str
    session_id: SessionID
    work_item_id: WorkItemID
    category: str
    content: str
    tags: list[str]
    created_at: str
    context: dict[str, Any]


class MilestoneDict(TypedDict, total=False):
    """Typed dictionary for milestone data structure.

    Attributes:
        id: Unique milestone identifier
        title: Milestone title
        description: Milestone description
        target_date: Target completion date
        status: Milestone status
        work_items: List of work item IDs in this milestone
    """

    id: MilestoneID
    title: str
    description: str
    target_date: str
    status: str
    work_items: list[WorkItemID]


class ConfigDict(TypedDict, total=False):
    """Typed dictionary for Solokit configuration structure.

    Attributes:
        project_name: Name of the project
        version: Configuration version
        quality_gates: Quality gate configuration
        learning: Learning system configuration
        git: Git integration configuration
    """

    project_name: str
    version: str
    quality_gates: dict[str, Any]
    learning: dict[str, Any]
    git: dict[str, Any]


class QualityGateResult(TypedDict):
    """Typed dictionary for quality gate results.

    Attributes:
        passed: Whether the quality gate passed
        message: Result message
        details: Additional details about the result
    """

    passed: bool
    message: str
    details: dict[str, Any]
