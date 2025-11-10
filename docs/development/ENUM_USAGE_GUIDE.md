# Enum Usage Guide for Solokit

This guide explains how to use type-safe enums throughout the Solokit codebase, replacing magic strings.

## Available Enums

All enums are defined in `src/solokit/core/types.py` and inherit from `str` for JSON serialization compatibility.

### WorkItemType

Valid work item types:
```python
from solokit.core.types import WorkItemType

WorkItemType.FEATURE          # "feature"
WorkItemType.BUG              # "bug"
WorkItemType.REFACTOR         # "refactor"
WorkItemType.SECURITY         # "security"
WorkItemType.INTEGRATION_TEST # "integration_test"
WorkItemType.DEPLOYMENT       # "deployment"
```

### WorkItemStatus

Valid work item statuses:
```python
from solokit.core.types import WorkItemStatus

WorkItemStatus.NOT_STARTED  # "not_started"
WorkItemStatus.IN_PROGRESS  # "in_progress"
WorkItemStatus.BLOCKED      # "blocked"
WorkItemStatus.COMPLETED    # "completed"
```

### Priority

Valid priority levels (with comparison support):
```python
from solokit.core.types import Priority

Priority.CRITICAL  # "critical"
Priority.HIGH      # "high"
Priority.MEDIUM    # "medium"
Priority.LOW       # "low"

# Priorities support comparison operations:
assert Priority.CRITICAL < Priority.HIGH  # True (higher priority = lower value)
```

### GitStatus

Valid git workflow statuses for work item branches:
```python
from solokit.core.types import GitStatus

GitStatus.IN_PROGRESS     # "in_progress"
GitStatus.READY_TO_MERGE  # "ready_to_merge"
GitStatus.READY_FOR_PR    # "ready_for_pr"
GitStatus.PR_CREATED      # "pr_created"
GitStatus.MERGED          # "merged"
```

These track the git workflow state of work item branches through their lifecycle:
- `IN_PROGRESS`: Work is actively being done on the branch
- `READY_TO_MERGE`: Branch is complete and ready for local merge
- `READY_FOR_PR`: Branch is complete and ready for pull request creation
- `PR_CREATED`: Pull request has been created
- `MERGED`: Branch has been merged (either locally or via PR)

## Usage Patterns

### 1. Comparisons

Always use `.value` when comparing with data from JSON files:

```python
# ✅ Correct
if item["status"] == WorkItemStatus.COMPLETED.value:
    process_completed_item(item)

# ❌ Incorrect (compares enum object, not string)
if item["status"] == WorkItemStatus.COMPLETED:
    process_completed_item(item)
```

### 2. Assignments

Use `.value` when assigning to dictionary or JSON data:

```python
# ✅ Correct
work_item["status"] = WorkItemStatus.IN_PROGRESS.value

# ❌ Incorrect (assigns enum object, not string)
work_item["status"] = WorkItemStatus.IN_PROGRESS
```

### 3. Dictionary Keys

Use `.value` as dict keys when dict is used for lookups:

```python
# ✅ Correct
parsers = {
    WorkItemType.FEATURE.value: parse_feature_spec,
    WorkItemType.BUG.value: parse_bug_spec,
}

# ✅ Also correct for icon/emoji mappings
status_icons = {
    WorkItemStatus.NOT_STARTED.value: "○",
    WorkItemStatus.IN_PROGRESS.value: "◐",
    WorkItemStatus.COMPLETED.value: "✓",
}
```

### 4. Default Values

Use `.value` when providing default values:

```python
# ✅ Correct
work_type = item.get("type", WorkItemType.FEATURE.value)
priority = item.get("priority", Priority.MEDIUM.value)

# ❌ Incorrect
work_type = item.get("type", "feature")
```

### 5. Getting All Valid Values

Each enum has a `values()` class method:

```python
# Get all valid work item types
all_types = WorkItemType.values()
# Returns: ["feature", "bug", "refactor", "security", "integration_test", "deployment"]

# Use for validation
if work_type not in WorkItemType.values():
    raise ValueError(f"Invalid work type: {work_type}")
```

### 6. Priority Comparisons

The `Priority` enum supports comparison operations:

```python
# Priorities can be compared directly
if task_priority < Priority.HIGH:
    print("This is critical priority")

# Sort items by priority
items.sort(key=lambda x: Priority(x["priority"]))
```

### 7. String Conversion

Enums automatically convert to strings when needed:

```python
# String representation
str(WorkItemType.FEATURE)  # Returns: "feature"

# JSON serialization (automatic via str inheritance)
json.dumps({"type": WorkItemType.FEATURE.value})  # Returns: '{"type": "feature"}'
```

## Migration from Magic Strings

When migrating code from magic strings to enums:

### Before:
```python
def process_work_item(item):
    if item["status"] == "completed":
        return

    if item["type"] == "integration_test":
        run_integration_tests(item)

    item["status"] = "in_progress"
```

### After:
```python
from solokit.core.types import WorkItemType, WorkItemStatus

def process_work_item(item):
    if item["status"] == WorkItemStatus.COMPLETED.value:
        return

    if item["type"] == WorkItemType.INTEGRATION_TEST.value:
        run_integration_tests(item)

    item["status"] = WorkItemStatus.IN_PROGRESS.value
```

## Benefits

1. **Type Safety**: IDEs provide autocomplete and catch typos at development time
2. **Refactoring**: Easy to find all usages of a specific enum value
3. **Documentation**: Enum definitions serve as single source of truth for valid values
4. **Validation**: Built-in validation when converting strings to enums
5. **Extensibility**: Easy to add new valid values in one place

## Common Pitfalls

### 1. Forgetting `.value`

```python
# ❌ WRONG - compares enum object to string
if item["status"] == WorkItemStatus.COMPLETED:
    pass

# ✅ CORRECT - compares string to string
if item["status"] == WorkItemStatus.COMPLETED.value:
    pass
```

### 2. Using magic strings in new code

```python
# ❌ WRONG - introduces magic string
work_item["type"] = "feature"

# ✅ CORRECT - uses enum
work_item["type"] = WorkItemType.FEATURE.value
```

### 3. Not importing enums

```python
# ❌ WRONG - missing import
def create_work_item():
    return {"type": WorkItemType.FEATURE.value}  # NameError!

# ✅ CORRECT - proper import
from solokit.core.types import WorkItemType

def create_work_item():
    return {"type": WorkItemType.FEATURE.value}
```

## IDE Support

Most modern IDEs provide excellent support for enums:

- **Autocomplete**: Type `WorkItemType.` and see all available options
- **Go to Definition**: Jump to enum definition to see all valid values
- **Find Usages**: Find all places where a specific enum is used
- **Refactoring**: Safely rename enum members across entire codebase

## Testing with Enums

When writing tests, use enum values for clarity:

```python
def test_work_item_completion():
    item = {
        "id": "test_001",
        "status": WorkItemStatus.IN_PROGRESS.value,
        "type": WorkItemType.FEATURE.value,
    }

    complete_work_item(item)

    assert item["status"] == WorkItemStatus.COMPLETED.value
```

## JSON Serialization

Enums serialize correctly to JSON because they inherit from `str`:

```python
work_item = {
    "type": WorkItemType.FEATURE.value,
    "status": WorkItemStatus.NOT_STARTED.value,
    "priority": Priority.HIGH.value,
}

# Serializes to: {"type": "feature", "status": "not_started", "priority": "high"}
json.dumps(work_item)
```

## Backward Compatibility

The enum refactoring maintains full backward compatibility:

- Existing JSON files work without changes
- String comparisons still work (when using `.value`)
- No changes to external APIs or data formats
- All existing tests pass without modification

## Quick Reference

| Enum | Import | Values Method | Example Usage |
|------|--------|---------------|---------------|
| `WorkItemType` | `from solokit.core.types import WorkItemType` | `WorkItemType.values()` | `WorkItemType.FEATURE.value` |
| `WorkItemStatus` | `from solokit.core.types import WorkItemStatus` | `WorkItemStatus.values()` | `WorkItemStatus.IN_PROGRESS.value` |
| `Priority` | `from solokit.core.types import Priority` | `Priority.values()` | `Priority.HIGH.value` |
| `GitStatus` | `from solokit.core.types import GitStatus` | `GitStatus.values()` | `GitStatus.IN_PROGRESS.value` |

## Questions or Issues?

If you encounter issues with enum usage:

1. Ensure you're using `.value` when comparing/assigning
2. Check that imports are correct
3. Verify enum inheritance from `str` is maintained
4. Run tests to catch any type mismatches

For more information, see `src/solokit/core/types.py` or the comprehensive unit tests in `tests/unit/test_types.py`.
