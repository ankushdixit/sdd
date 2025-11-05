"""Unit tests for core type definitions."""

import json

import pytest

from sdd.core.types import GitStatus, Priority, WorkItemStatus, WorkItemType
from sdd.core.exceptions import ValidationError, ErrorCode


class TestWorkItemType:
    """Test WorkItemType enum."""

    def test_enum_members(self):
        """Test all enum members are defined."""
        assert WorkItemType.FEATURE.value == "feature"
        assert WorkItemType.BUG.value == "bug"
        assert WorkItemType.REFACTOR.value == "refactor"
        assert WorkItemType.SECURITY.value == "security"
        assert WorkItemType.INTEGRATION_TEST.value == "integration_test"
        assert WorkItemType.DEPLOYMENT.value == "deployment"

    def test_enum_count(self):
        """Test correct number of enum members."""
        assert len(WorkItemType) == 6

    def test_string_representation(self):
        """Test string conversion."""
        assert str(WorkItemType.FEATURE) == "feature"
        assert str(WorkItemType.BUG) == "bug"

    def test_value_validation_valid(self):
        """Test valid value conversion."""
        assert WorkItemType("feature") == WorkItemType.FEATURE
        assert WorkItemType("bug") == WorkItemType.BUG
        assert WorkItemType("refactor") == WorkItemType.REFACTOR

    def test_value_validation_invalid(self):
        """Test invalid value raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            WorkItemType("invalid")
        assert exc_info.value.code == ErrorCode.INVALID_WORK_ITEM_TYPE
        assert "work_item_type" in exc_info.value.context
        assert exc_info.value.context["work_item_type"] == "invalid"
        assert "valid_types" in exc_info.value.context
        assert exc_info.value.remediation is not None

        with pytest.raises(ValidationError) as exc_info:
            WorkItemType("features")
        assert exc_info.value.code == ErrorCode.INVALID_WORK_ITEM_TYPE

        with pytest.raises(ValidationError) as exc_info:
            WorkItemType("")
        assert exc_info.value.code == ErrorCode.INVALID_WORK_ITEM_TYPE

    def test_values_method(self):
        """Test values() returns all valid values."""
        values = WorkItemType.values()
        assert len(values) == 6
        assert "feature" in values
        assert "bug" in values
        assert "refactor" in values
        assert "security" in values
        assert "integration_test" in values
        assert "deployment" in values

    def test_json_serialization(self):
        """Test JSON serialization."""
        data = {"type": WorkItemType.FEATURE.value}
        json_str = json.dumps(data)
        assert json_str == '{"type": "feature"}'

    def test_json_deserialization(self):
        """Test JSON deserialization."""
        json_str = '{"type": "bug"}'
        data = json.loads(json_str)
        work_type = WorkItemType(data["type"])
        assert work_type == WorkItemType.BUG

    def test_enum_iteration(self):
        """Test enum iteration."""
        types = list(WorkItemType)
        assert len(types) == 6
        assert WorkItemType.FEATURE in types
        assert WorkItemType.DEPLOYMENT in types

    def test_enum_equality(self):
        """Test enum equality."""
        assert WorkItemType.FEATURE == WorkItemType.FEATURE
        assert WorkItemType.FEATURE != WorkItemType.BUG
        assert WorkItemType("feature") == WorkItemType.FEATURE


class TestWorkItemStatus:
    """Test WorkItemStatus enum."""

    def test_enum_members(self):
        """Test all enum members are defined."""
        assert WorkItemStatus.NOT_STARTED.value == "not_started"
        assert WorkItemStatus.IN_PROGRESS.value == "in_progress"
        assert WorkItemStatus.BLOCKED.value == "blocked"
        assert WorkItemStatus.COMPLETED.value == "completed"

    def test_enum_count(self):
        """Test correct number of enum members."""
        assert len(WorkItemStatus) == 4

    def test_string_representation(self):
        """Test string conversion."""
        assert str(WorkItemStatus.NOT_STARTED) == "not_started"
        assert str(WorkItemStatus.IN_PROGRESS) == "in_progress"

    def test_value_validation_valid(self):
        """Test valid value conversion."""
        assert WorkItemStatus("not_started") == WorkItemStatus.NOT_STARTED
        assert WorkItemStatus("in_progress") == WorkItemStatus.IN_PROGRESS
        assert WorkItemStatus("blocked") == WorkItemStatus.BLOCKED
        assert WorkItemStatus("completed") == WorkItemStatus.COMPLETED

    def test_value_validation_invalid(self):
        """Test invalid value raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            WorkItemStatus("invalid")
        assert exc_info.value.code == ErrorCode.INVALID_STATUS
        assert "status" in exc_info.value.context
        assert exc_info.value.context["status"] == "invalid"
        assert "valid_statuses" in exc_info.value.context
        assert exc_info.value.remediation is not None

        with pytest.raises(ValidationError) as exc_info:
            WorkItemStatus("done")
        assert exc_info.value.code == ErrorCode.INVALID_STATUS

        with pytest.raises(ValidationError) as exc_info:
            WorkItemStatus("")
        assert exc_info.value.code == ErrorCode.INVALID_STATUS

    def test_values_method(self):
        """Test values() returns all valid values."""
        values = WorkItemStatus.values()
        assert len(values) == 4
        assert "not_started" in values
        assert "in_progress" in values
        assert "blocked" in values
        assert "completed" in values

    def test_json_serialization(self):
        """Test JSON serialization."""
        data = {"status": WorkItemStatus.IN_PROGRESS.value}
        json_str = json.dumps(data)
        assert json_str == '{"status": "in_progress"}'

    def test_json_deserialization(self):
        """Test JSON deserialization."""
        json_str = '{"status": "completed"}'
        data = json.loads(json_str)
        status = WorkItemStatus(data["status"])
        assert status == WorkItemStatus.COMPLETED

    def test_enum_iteration(self):
        """Test enum iteration."""
        statuses = list(WorkItemStatus)
        assert len(statuses) == 4
        assert WorkItemStatus.NOT_STARTED in statuses
        assert WorkItemStatus.COMPLETED in statuses

    def test_enum_equality(self):
        """Test enum equality."""
        assert WorkItemStatus.IN_PROGRESS == WorkItemStatus.IN_PROGRESS
        assert WorkItemStatus.IN_PROGRESS != WorkItemStatus.COMPLETED
        assert WorkItemStatus("in_progress") == WorkItemStatus.IN_PROGRESS


class TestPriority:
    """Test Priority enum."""

    def test_enum_members(self):
        """Test all enum members are defined."""
        assert Priority.CRITICAL.value == "critical"
        assert Priority.HIGH.value == "high"
        assert Priority.MEDIUM.value == "medium"
        assert Priority.LOW.value == "low"

    def test_enum_count(self):
        """Test correct number of enum members."""
        assert len(Priority) == 4

    def test_string_representation(self):
        """Test string conversion."""
        assert str(Priority.CRITICAL) == "critical"
        assert str(Priority.HIGH) == "high"

    def test_value_validation_valid(self):
        """Test valid value conversion."""
        assert Priority("critical") == Priority.CRITICAL
        assert Priority("high") == Priority.HIGH
        assert Priority("medium") == Priority.MEDIUM
        assert Priority("low") == Priority.LOW

    def test_value_validation_invalid(self):
        """Test invalid value raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Priority("invalid")
        assert exc_info.value.code == ErrorCode.INVALID_PRIORITY
        assert "priority" in exc_info.value.context
        assert exc_info.value.context["priority"] == "invalid"
        assert "valid_priorities" in exc_info.value.context
        assert exc_info.value.remediation is not None

        with pytest.raises(ValidationError) as exc_info:
            Priority("urgent")
        assert exc_info.value.code == ErrorCode.INVALID_PRIORITY

        with pytest.raises(ValidationError) as exc_info:
            Priority("")
        assert exc_info.value.code == ErrorCode.INVALID_PRIORITY

    def test_values_method(self):
        """Test values() returns all valid values."""
        values = Priority.values()
        assert len(values) == 4
        assert "critical" in values
        assert "high" in values
        assert "medium" in values
        assert "low" in values

    def test_priority_comparison_less_than(self):
        """Test priority less-than comparison."""
        # Lower numeric order = higher priority
        assert Priority.CRITICAL < Priority.HIGH
        assert Priority.HIGH < Priority.MEDIUM
        assert Priority.MEDIUM < Priority.LOW

        # Not less than
        assert not (Priority.HIGH < Priority.CRITICAL)
        assert not (Priority.LOW < Priority.MEDIUM)
        assert not (Priority.CRITICAL < Priority.CRITICAL)

    def test_priority_comparison_less_than_or_equal(self):
        """Test priority less-than-or-equal comparison."""
        assert Priority.CRITICAL <= Priority.HIGH
        assert Priority.CRITICAL <= Priority.CRITICAL
        assert Priority.HIGH <= Priority.MEDIUM

        # Not less than or equal
        assert not (Priority.HIGH <= Priority.CRITICAL)
        assert not (Priority.LOW <= Priority.MEDIUM)

    def test_priority_comparison_greater_than(self):
        """Test priority greater-than comparison."""
        assert Priority.HIGH > Priority.CRITICAL
        assert Priority.MEDIUM > Priority.HIGH
        assert Priority.LOW > Priority.MEDIUM

        # Not greater than
        assert not (Priority.CRITICAL > Priority.HIGH)
        assert not (Priority.MEDIUM > Priority.LOW)
        assert not (Priority.CRITICAL > Priority.CRITICAL)

    def test_priority_comparison_greater_than_or_equal(self):
        """Test priority greater-than-or-equal comparison."""
        assert Priority.HIGH >= Priority.CRITICAL
        assert Priority.HIGH >= Priority.HIGH
        assert Priority.MEDIUM >= Priority.HIGH

        # Not greater than or equal
        assert not (Priority.CRITICAL >= Priority.HIGH)
        assert not (Priority.MEDIUM >= Priority.LOW)

    def test_priority_comparison_invalid_type(self):
        """Test priority comparison with invalid type raises TypeError."""
        with pytest.raises(TypeError):
            Priority.HIGH < "high"
        with pytest.raises(TypeError):
            Priority.HIGH <= 1
        with pytest.raises(TypeError):
            Priority.HIGH > "low"
        with pytest.raises(TypeError):
            Priority.HIGH >= None

    def test_priority_sorting(self):
        """Test priority can be used for sorting."""
        priorities = [Priority.LOW, Priority.CRITICAL, Priority.MEDIUM, Priority.HIGH]
        sorted_priorities = sorted(priorities)
        assert sorted_priorities == [
            Priority.CRITICAL,
            Priority.HIGH,
            Priority.MEDIUM,
            Priority.LOW,
        ]

    def test_json_serialization(self):
        """Test JSON serialization."""
        data = {"priority": Priority.HIGH.value}
        json_str = json.dumps(data)
        assert json_str == '{"priority": "high"}'

    def test_json_deserialization(self):
        """Test JSON deserialization."""
        json_str = '{"priority": "critical"}'
        data = json.loads(json_str)
        priority = Priority(data["priority"])
        assert priority == Priority.CRITICAL

    def test_enum_iteration(self):
        """Test enum iteration."""
        priorities = list(Priority)
        assert len(priorities) == 4
        assert Priority.CRITICAL in priorities
        assert Priority.LOW in priorities

    def test_enum_equality(self):
        """Test enum equality."""
        assert Priority.HIGH == Priority.HIGH
        assert Priority.HIGH != Priority.LOW
        assert Priority("high") == Priority.HIGH


class TestGitStatus:
    """Test GitStatus enum."""

    def test_enum_members(self):
        """Test all enum members are defined."""
        assert GitStatus.IN_PROGRESS.value == "in_progress"
        assert GitStatus.READY_TO_MERGE.value == "ready_to_merge"
        assert GitStatus.READY_FOR_PR.value == "ready_for_pr"
        assert GitStatus.PR_CREATED.value == "pr_created"
        assert GitStatus.PR_CLOSED.value == "pr_closed"
        assert GitStatus.MERGED.value == "merged"
        assert GitStatus.DELETED.value == "deleted"

    def test_enum_count(self):
        """Test correct number of enum members."""
        assert len(GitStatus) == 7

    def test_string_representation(self):
        """Test string conversion."""
        assert str(GitStatus.IN_PROGRESS) == "in_progress"
        assert str(GitStatus.MERGED) == "merged"

    def test_value_validation_valid(self):
        """Test valid value conversion."""
        assert GitStatus("in_progress") == GitStatus.IN_PROGRESS
        assert GitStatus("ready_to_merge") == GitStatus.READY_TO_MERGE
        assert GitStatus("ready_for_pr") == GitStatus.READY_FOR_PR
        assert GitStatus("pr_created") == GitStatus.PR_CREATED
        assert GitStatus("pr_closed") == GitStatus.PR_CLOSED
        assert GitStatus("merged") == GitStatus.MERGED
        assert GitStatus("deleted") == GitStatus.DELETED

    def test_value_validation_invalid(self):
        """Test invalid value raises ValueError."""
        with pytest.raises(ValueError):
            GitStatus("invalid")
        with pytest.raises(ValueError):
            GitStatus("committed")
        with pytest.raises(ValueError):
            GitStatus("")

    def test_values_method(self):
        """Test values() returns all valid values."""
        values = GitStatus.values()
        assert len(values) == 7
        assert "in_progress" in values
        assert "ready_to_merge" in values
        assert "ready_for_pr" in values
        assert "pr_created" in values
        assert "pr_closed" in values
        assert "merged" in values
        assert "deleted" in values

    def test_json_serialization(self):
        """Test JSON serialization."""
        data = {"git_status": GitStatus.PR_CREATED.value}
        json_str = json.dumps(data)
        assert json_str == '{"git_status": "pr_created"}'

    def test_json_deserialization(self):
        """Test JSON deserialization."""
        json_str = '{"git_status": "merged"}'
        data = json.loads(json_str)
        git_status = GitStatus(data["git_status"])
        assert git_status == GitStatus.MERGED

    def test_enum_iteration(self):
        """Test enum iteration."""
        statuses = list(GitStatus)
        assert len(statuses) == 7
        assert GitStatus.IN_PROGRESS in statuses
        assert GitStatus.PR_CLOSED in statuses
        assert GitStatus.MERGED in statuses
        assert GitStatus.DELETED in statuses

    def test_enum_equality(self):
        """Test enum equality."""
        assert GitStatus.READY_TO_MERGE == GitStatus.READY_TO_MERGE
        assert GitStatus.READY_TO_MERGE != GitStatus.MERGED
        assert GitStatus("ready_to_merge") == GitStatus.READY_TO_MERGE
