"""
Comprehensive exception hierarchy for SDD.

Provides structured exceptions with error codes, categories, and context.
All business logic should raise these exceptions rather than returning error tuples.

Usage:
    from sdd.core.exceptions import WorkItemNotFoundError

    def get_work_item(item_id: str) -> WorkItem:
        if item_id not in work_items:
            raise WorkItemNotFoundError(item_id)
        return work_items[item_id]

    # CLI layer catches and formats
    try:
        item = get_work_item("invalid")
    except WorkItemNotFoundError as e:
        print(f"Error: {e}")
        print(f"Remediation: {e.remediation}")
        sys.exit(e.exit_code)
"""

from __future__ import annotations
from typing import Any, Optional
from enum import Enum


class ErrorCategory(Enum):
    """Error categories for classification and handling"""
    VALIDATION = "validation"
    NOT_FOUND = "not_found"
    ALREADY_EXISTS = "already_exists"
    CONFIGURATION = "configuration"
    SYSTEM = "system"
    GIT = "git"
    DEPENDENCY = "dependency"
    SECURITY = "security"
    TIMEOUT = "timeout"
    PERMISSION = "permission"


class ErrorCode(Enum):
    """Specific error codes for programmatic handling"""
    # Validation errors (1000-1999)
    INVALID_WORK_ITEM_ID = 1001
    INVALID_WORK_ITEM_TYPE = 1002
    MISSING_REQUIRED_FIELD = 1003
    INVALID_JSON = 1004
    SPEC_VALIDATION_FAILED = 1005
    INVALID_STATUS = 1006
    INVALID_PRIORITY = 1007
    INVALID_COMMAND = 1008

    # Not found errors (2000-2999)
    WORK_ITEM_NOT_FOUND = 2001
    FILE_NOT_FOUND = 2002
    SESSION_NOT_FOUND = 2003
    LEARNING_NOT_FOUND = 2004
    CONFIG_NOT_FOUND = 2005

    # Already exists errors (3000-3999)
    WORK_ITEM_ALREADY_EXISTS = 3001
    FILE_ALREADY_EXISTS = 3002
    SESSION_ALREADY_ACTIVE = 3003

    # Configuration errors (4000-4999)
    CONFIG_FILE_MISSING = 4001
    CONFIG_VALIDATION_FAILED = 4002
    SCHEMA_MISSING = 4003
    INVALID_CONFIG_VALUE = 4004

    # System errors (5000-5999)
    FILE_OPERATION_FAILED = 5001
    SUBPROCESS_FAILED = 5002
    IMPORT_FAILED = 5003
    COMMAND_FAILED = 5004
    MODULE_NOT_FOUND = 5005
    FUNCTION_NOT_FOUND = 5006

    # Git errors (6000-6999)
    NOT_A_GIT_REPO = 6001
    GIT_NOT_FOUND = 6002
    WORKING_DIR_NOT_CLEAN = 6003
    GIT_COMMAND_FAILED = 6004
    BRANCH_NOT_FOUND = 6005
    BRANCH_ALREADY_EXISTS = 6006

    # Dependency errors (7000-7999)
    CIRCULAR_DEPENDENCY = 7001
    UNMET_DEPENDENCY = 7002

    # Security errors (8000-8999)
    SECURITY_SCAN_FAILED = 8001
    VULNERABILITY_FOUND = 8002

    # Timeout errors (9000-9999)
    OPERATION_TIMEOUT = 9001
    SUBPROCESS_TIMEOUT = 9002

    # Quality gate errors (10000-10999)
    TEST_FAILED = 10001
    LINT_FAILED = 10002
    COVERAGE_BELOW_THRESHOLD = 10003
    QUALITY_GATE_FAILED = 10004


class SDDError(Exception):
    """
    Base exception for all SDD errors.

    Attributes:
        message: Human-readable error message
        code: ErrorCode enum for programmatic handling
        category: ErrorCategory enum for classification
        context: Additional context data (file paths, IDs, etc.)
        remediation: Suggested fix for the user
        cause: Original exception if wrapping another error
        exit_code: Suggested exit code for CLI

    Example:
        >>> error = SDDError(
        ...     message="Something went wrong",
        ...     code=ErrorCode.FILE_OPERATION_FAILED,
        ...     category=ErrorCategory.SYSTEM,
        ...     context={"file": "/path/to/file"},
        ...     remediation="Check file permissions"
        ... )
        >>> print(error.to_dict())
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode,
        category: ErrorCategory,
        context: Optional[dict[str, Any]] = None,
        remediation: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.category = category
        self.context = context or {}
        self.remediation = remediation
        self.cause = cause

    @property
    def exit_code(self) -> int:
        """Get CLI exit code based on error category"""
        exit_codes = {
            ErrorCategory.VALIDATION: 2,
            ErrorCategory.NOT_FOUND: 3,
            ErrorCategory.CONFIGURATION: 4,
            ErrorCategory.SYSTEM: 5,
            ErrorCategory.GIT: 6,
            ErrorCategory.DEPENDENCY: 7,
            ErrorCategory.SECURITY: 8,
            ErrorCategory.TIMEOUT: 9,
            ErrorCategory.ALREADY_EXISTS: 10,
            ErrorCategory.PERMISSION: 11,
        }
        return exit_codes.get(self.category, 1)

    def __str__(self) -> str:
        """Format error for display"""
        parts = [self.message]
        if self.remediation:
            parts.append(f"Remediation: {self.remediation}")
        return "\n".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for structured logging"""
        return {
            "message": self.message,
            "code": self.code.value,
            "code_name": self.code.name,
            "category": self.category.value,
            "context": self.context,
            "remediation": self.remediation,
            "cause": str(self.cause) if self.cause else None,
            "exit_code": self.exit_code
        }


# ============================================================================
# Validation Errors
# ============================================================================

class ValidationError(SDDError):
    """
    Raised when validation fails.

    Example:
        >>> raise ValidationError(
        ...     message="Invalid work item ID format",
        ...     code=ErrorCode.INVALID_WORK_ITEM_ID,
        ...     context={"work_item_id": "bad-id!"},
        ...     remediation="Use alphanumeric characters and underscores only"
        ... )
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.MISSING_REQUIRED_FIELD,
        context: Optional[dict[str, Any]] = None,
        remediation: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.VALIDATION,
            context=context,
            remediation=remediation,
            cause=cause
        )


class SpecValidationError(ValidationError):
    """
    Raised when spec file validation fails.

    Example:
        >>> raise SpecValidationError(
        ...     work_item_id="my_feature",
        ...     errors=["Missing Overview section", "Missing acceptance criteria"]
        ... )
    """

    def __init__(
        self,
        work_item_id: str,
        errors: list[str],
        remediation: Optional[str] = None
    ):
        message = f"Spec validation failed for '{work_item_id}'"
        context = {
            "work_item_id": work_item_id,
            "validation_errors": errors,
            "error_count": len(errors)
        }
        super().__init__(
            message=message,
            code=ErrorCode.SPEC_VALIDATION_FAILED,
            context=context,
            remediation=remediation or f"Edit .session/specs/{work_item_id}.md to fix validation errors"
        )


# ============================================================================
# Not Found Errors
# ============================================================================

class NotFoundError(SDDError):
    """
    Raised when a resource is not found.

    Example:
        >>> raise NotFoundError(
        ...     message="Configuration file not found",
        ...     code=ErrorCode.CONFIG_NOT_FOUND,
        ...     context={"path": ".session/config.json"}
        ... )
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode,
        context: Optional[dict[str, Any]] = None,
        remediation: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.NOT_FOUND,
            context=context,
            remediation=remediation,
            cause=cause
        )


class WorkItemNotFoundError(NotFoundError):
    """
    Raised when work item doesn't exist.

    Example:
        >>> raise WorkItemNotFoundError("nonexistent_feature")
    """

    def __init__(self, work_item_id: str):
        super().__init__(
            message=f"Work item '{work_item_id}' not found",
            code=ErrorCode.WORK_ITEM_NOT_FOUND,
            context={"work_item_id": work_item_id},
            remediation="Use 'sdd work-list' to see available work items"
        )


class FileNotFoundError(NotFoundError):
    """
    Raised when a required file doesn't exist.

    Note: This shadows the built-in FileNotFoundError, but provides
    more structured error information.

    Example:
        >>> raise FileNotFoundError(
        ...     file_path=".session/specs/my_feature.md",
        ...     file_type="spec"
        ... )
    """

    def __init__(self, file_path: str, file_type: Optional[str] = None):
        context = {"file_path": file_path}
        if file_type:
            context["file_type"] = file_type

        remediation_msg = None
        if file_type:
            remediation_msg = f"Create the missing {file_type} file: {file_path}"

        super().__init__(
            message=f"File not found: {file_path}",
            code=ErrorCode.FILE_NOT_FOUND,
            context=context,
            remediation=remediation_msg
        )


class SessionNotFoundError(NotFoundError):
    """
    Raised when no active session exists.

    Example:
        >>> raise SessionNotFoundError()
    """

    def __init__(self):
        super().__init__(
            message="No active session found",
            code=ErrorCode.SESSION_NOT_FOUND,
            remediation="Start a session with 'sdd start' or 'sdd start <work_item_id>'"
        )


# ============================================================================
# Configuration Errors
# ============================================================================

class ConfigurationError(SDDError):
    """
    Raised when configuration is invalid.

    Example:
        >>> raise ConfigurationError(
        ...     message="Invalid configuration value",
        ...     code=ErrorCode.INVALID_CONFIG_VALUE,
        ...     context={"key": "test_command", "value": None}
        ... )
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.CONFIG_VALIDATION_FAILED,
        context: Optional[dict[str, Any]] = None,
        remediation: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.CONFIGURATION,
            context=context,
            remediation=remediation,
            cause=cause
        )


class ConfigValidationError(ConfigurationError):
    """
    Raised when config fails schema validation.

    Example:
        >>> raise ConfigValidationError(
        ...     config_path=".session/config.json",
        ...     errors=["Missing 'project_name' field"]
        ... )
    """

    def __init__(self, config_path: str, errors: list[str]):
        message = f"Configuration validation failed: {config_path}"
        context = {
            "config_path": config_path,
            "validation_errors": errors,
            "error_count": len(errors)
        }
        super().__init__(
            message=message,
            code=ErrorCode.CONFIG_VALIDATION_FAILED,
            context=context,
            remediation="Check docs/guides/configuration.md for valid configuration options"
        )


# ============================================================================
# Git Errors
# ============================================================================

class GitError(SDDError):
    """
    Raised for git-related errors.

    Example:
        >>> raise GitError(
        ...     message="Git command failed",
        ...     code=ErrorCode.GIT_COMMAND_FAILED,
        ...     context={"command": "git status"}
        ... )
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode,
        context: Optional[dict[str, Any]] = None,
        remediation: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.GIT,
            context=context,
            remediation=remediation,
            cause=cause
        )


class NotAGitRepoError(GitError):
    """
    Raised when operation requires git repo but not in one.

    Example:
        >>> raise NotAGitRepoError()
    """

    def __init__(self, path: Optional[str] = None):
        context = {"path": path} if path else {}
        super().__init__(
            message="Not a git repository",
            code=ErrorCode.NOT_A_GIT_REPO,
            context=context,
            remediation="Run 'git init' to initialize a repository"
        )


class WorkingDirNotCleanError(GitError):
    """
    Raised when working directory has uncommitted changes.

    Example:
        >>> raise WorkingDirNotCleanError(
        ...     changes=["M src/file.py", "?? new_file.py"]
        ... )
    """

    def __init__(self, changes: Optional[list[str]] = None):
        context = {"uncommitted_changes": changes} if changes else {}
        super().__init__(
            message="Working directory not clean (uncommitted changes)",
            code=ErrorCode.WORKING_DIR_NOT_CLEAN,
            context=context,
            remediation="Commit or stash changes before proceeding"
        )


class BranchNotFoundError(GitError):
    """
    Raised when git branch doesn't exist.

    Example:
        >>> raise BranchNotFoundError("feature-branch")
    """

    def __init__(self, branch_name: str):
        super().__init__(
            message=f"Branch '{branch_name}' not found",
            code=ErrorCode.BRANCH_NOT_FOUND,
            context={"branch_name": branch_name},
            remediation="Check branch name or create it with 'git checkout -b <branch>'"
        )


# ============================================================================
# System Errors
# ============================================================================

class SystemError(SDDError):
    """
    Raised for system-level errors.

    Example:
        >>> raise SystemError(
        ...     message="Failed to write file",
        ...     code=ErrorCode.FILE_OPERATION_FAILED,
        ...     context={"path": "/tmp/file.txt"}
        ... )
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode,
        context: Optional[dict[str, Any]] = None,
        remediation: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.SYSTEM,
            context=context,
            remediation=remediation,
            cause=cause
        )


class SubprocessError(SystemError):
    """
    Raised when subprocess command fails.

    Example:
        >>> raise SubprocessError(
        ...     command="pytest tests/",
        ...     returncode=1,
        ...     stderr="FAILED tests/test_foo.py"
        ... )
    """

    def __init__(
        self,
        command: str,
        returncode: int,
        stderr: Optional[str] = None,
        stdout: Optional[str] = None
    ):
        context = {
            "command": command,
            "returncode": returncode,
            "stderr": stderr,
            "stdout": stdout
        }
        super().__init__(
            message=f"Command failed with exit code {returncode}: {command}",
            code=ErrorCode.SUBPROCESS_FAILED,
            context=context
        )


class TimeoutError(SystemError):
    """
    Raised when operation times out.

    Example:
        >>> raise TimeoutError(
        ...     operation="git fetch",
        ...     timeout_seconds=30
        ... )
    """

    def __init__(
        self,
        operation: str,
        timeout_seconds: int,
        context: Optional[dict[str, Any]] = None
    ):
        ctx = context or {}
        ctx.update({"operation": operation, "timeout_seconds": timeout_seconds})
        super().__init__(
            message=f"Operation timed out after {timeout_seconds}s: {operation}",
            code=ErrorCode.OPERATION_TIMEOUT,
            context=ctx
        )


class CommandExecutionError(SystemError):
    """
    Raised when a command execution fails.

    This wraps the CommandExecutionError from command_runner for consistency.

    Example:
        >>> raise CommandExecutionError(
        ...     command="npm test",
        ...     returncode=1,
        ...     stderr="Test failed"
        ... )
    """

    def __init__(
        self,
        command: str,
        returncode: int,
        stderr: Optional[str] = None,
        stdout: Optional[str] = None
    ):
        context = {
            "command": command,
            "returncode": returncode,
            "stderr": stderr,
            "stdout": stdout
        }
        super().__init__(
            message=f"Command execution failed: {command}",
            code=ErrorCode.COMMAND_FAILED,
            context=context
        )


# ============================================================================
# Dependency Errors
# ============================================================================

class DependencyError(SDDError):
    """
    Raised for dependency-related errors.

    Example:
        >>> raise DependencyError(
        ...     message="Dependency not met",
        ...     code=ErrorCode.UNMET_DEPENDENCY,
        ...     context={"dependency": "feature_a"}
        ... )
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode,
        context: Optional[dict[str, Any]] = None,
        remediation: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.DEPENDENCY,
            context=context,
            remediation=remediation,
            cause=cause
        )


class CircularDependencyError(DependencyError):
    """
    Raised when circular dependency detected.

    Example:
        >>> raise CircularDependencyError(["feature_a", "feature_b", "feature_a"])
    """

    def __init__(self, cycle: list[str]):
        cycle_str = " -> ".join(cycle)
        super().__init__(
            message=f"Circular dependency detected: {cycle_str}",
            code=ErrorCode.CIRCULAR_DEPENDENCY,
            context={"cycle": cycle},
            remediation="Break the dependency cycle by reordering work items"
        )


class UnmetDependencyError(DependencyError):
    """
    Raised when dependency not met.

    Example:
        >>> raise UnmetDependencyError("feature_b", "feature_a")
    """

    def __init__(self, work_item_id: str, dependency_id: str):
        super().__init__(
            message=f"Cannot start '{work_item_id}': dependency '{dependency_id}' not completed",
            code=ErrorCode.UNMET_DEPENDENCY,
            context={"work_item_id": work_item_id, "dependency_id": dependency_id},
            remediation=f"Complete '{dependency_id}' before starting '{work_item_id}'"
        )


# ============================================================================
# Already Exists Errors
# ============================================================================

class AlreadyExistsError(SDDError):
    """
    Raised when resource already exists.

    Example:
        >>> raise AlreadyExistsError(
        ...     message="Work item already exists",
        ...     code=ErrorCode.WORK_ITEM_ALREADY_EXISTS,
        ...     context={"work_item_id": "my_feature"}
        ... )
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode,
        context: Optional[dict[str, Any]] = None,
        remediation: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.ALREADY_EXISTS,
            context=context,
            remediation=remediation,
            cause=cause
        )


class SessionAlreadyActiveError(AlreadyExistsError):
    """
    Raised when trying to start session while one is active.

    Example:
        >>> raise SessionAlreadyActiveError("current_feature")
    """

    def __init__(self, current_work_item_id: str):
        super().__init__(
            message=f"Session already active for '{current_work_item_id}'",
            code=ErrorCode.SESSION_ALREADY_ACTIVE,
            context={"current_work_item_id": current_work_item_id},
            remediation="Complete current session with 'sdd end' before starting a new one"
        )


class WorkItemAlreadyExistsError(AlreadyExistsError):
    """
    Raised when trying to create work item that already exists.

    Example:
        >>> raise WorkItemAlreadyExistsError("my_feature")
    """

    def __init__(self, work_item_id: str):
        super().__init__(
            message=f"Work item '{work_item_id}' already exists",
            code=ErrorCode.WORK_ITEM_ALREADY_EXISTS,
            context={"work_item_id": work_item_id},
            remediation=f"Use 'sdd work-show {work_item_id}' to view existing work item"
        )


# ============================================================================
# Quality Gate Errors
# ============================================================================

class QualityGateError(SDDError):
    """
    Raised when quality gate fails.

    Example:
        >>> raise QualityGateError(
        ...     message="Tests failed",
        ...     code=ErrorCode.TEST_FAILED,
        ...     context={"failed_tests": ["test_foo", "test_bar"]}
        ... )
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode,
        context: Optional[dict[str, Any]] = None,
        remediation: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.VALIDATION,
            context=context,
            remediation=remediation,
            cause=cause
        )


class QualityTestFailedError(QualityGateError):
    """
    Raised when quality tests fail.

    Example:
        >>> raise QualityTestFailedError(
        ...     failed_count=2,
        ...     total_count=10,
        ...     details=["test_foo failed", "test_bar failed"]
        ... )
    """

    def __init__(self, failed_count: int, total_count: int, details: Optional[list[str]] = None):
        message = f"{failed_count} of {total_count} tests failed"
        context = {
            "failed_count": failed_count,
            "total_count": total_count,
            "details": details
        }
        super().__init__(
            message=message,
            code=ErrorCode.TEST_FAILED,
            context=context,
            remediation="Fix failing tests before completing session"
        )


# ============================================================================
# File Operation Errors
# ============================================================================

class FileOperationError(SystemError):
    """
    Raised when file operations fail (read, write, parse, etc.).

    Example:
        >>> raise FileOperationError(
        ...     operation="write",
        ...     file_path="/path/to/file.json",
        ...     details="Permission denied"
        ... )
    """

    def __init__(
        self,
        operation: str,
        file_path: str,
        details: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        message = f"File {operation} operation failed: {file_path}"
        if details:
            message = f"{message} - {details}"

        context = {
            "operation": operation,
            "file_path": file_path,
            "details": details
        }
        super().__init__(
            message=message,
            code=ErrorCode.FILE_OPERATION_FAILED,
            context=context,
            cause=cause
        )


# ============================================================================
# Learning Errors
# ============================================================================

class LearningError(ValidationError):
    """
    Raised when learning operations fail (validation, storage, curation).

    Example:
        >>> raise LearningError(
        ...     message="Learning content cannot be empty",
        ...     context={"learning_id": "abc123"}
        ... )
    """

    def __init__(
        self,
        message: str,
        context: Optional[dict[str, Any]] = None,
        remediation: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            code=ErrorCode.MISSING_REQUIRED_FIELD,
            context=context,
            remediation=remediation or "Check learning content and structure",
            cause=cause
        )
