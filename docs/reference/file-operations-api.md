# File Operations API Reference

## Overview

The `sdd.core.file_ops` module provides centralized JSON file I/O operations with consistent error handling, atomic writes, and validation hooks. This eliminates code duplication and ensures uniform behavior across the entire codebase.

## Core Components

### `FileOperationError`

Custom exception class for all file operation errors.

```python
from sdd.core.file_ops import FileOperationError

try:
    data = load_json(path)
except FileOperationError as e:
    logger.error(f"Failed to load file: {e}")
```

### `JSONFileOperations`

Main class providing enhanced JSON file operations.

## API Reference

### JSONFileOperations.load_json()

Load JSON file with optional default and validation.

**Signature:**
```python
@staticmethod
def load_json(
    file_path: Path,
    default: dict[str, Any] | None = None,
    validator: Callable[[dict], bool] | None = None,
) -> dict[str, Any]
```

**Parameters:**
- `file_path` (Path): Path to JSON file
- `default` (dict | None): Default value if file doesn't exist (None raises error)
- `validator` (Callable | None): Optional validation function that returns True if data is valid

**Returns:**
- `dict[str, Any]`: Loaded JSON data

**Raises:**
- `FileOperationError`: If file not found and no default provided
- `FileOperationError`: If JSON is invalid
- `FileOperationError`: If validation fails

**Examples:**

```python
from pathlib import Path
from sdd.core.file_ops import JSONFileOperations

# Load required file (raises if missing)
data = JSONFileOperations.load_json(Path("config.json"))

# Load with default
data = JSONFileOperations.load_json(Path("optional.json"), default={})

# Load with validation
validator = lambda d: "version" in d
data = JSONFileOperations.load_json(Path("config.json"), validator=validator)
```

### JSONFileOperations.save_json()

Save data to JSON file with atomic write option.

**Signature:**
```python
@staticmethod
def save_json(
    file_path: Path,
    data: dict[str, Any],
    indent: int = 2,
    atomic: bool = True,
    create_dirs: bool = True,
) -> None
```

**Parameters:**
- `file_path` (Path): Path to JSON file
- `data` (dict): Data to save
- `indent` (int): JSON indentation (default 2)
- `atomic` (bool): Use atomic write via temp file (default True)
- `create_dirs` (bool): Create parent directories if needed (default True)

**Raises:**
- `FileOperationError`: If save fails

**Examples:**

```python
from pathlib import Path
from sdd.core.file_ops import JSONFileOperations

# Save with atomic write (default)
JSONFileOperations.save_json(Path("data.json"), {"key": "value"})

# Save without atomic write
JSONFileOperations.save_json(Path("data.json"), data, atomic=False)

# Save with custom indent
JSONFileOperations.save_json(Path("data.json"), data, indent=4)

# Save to nested path (creates directories automatically)
JSONFileOperations.save_json(Path("deep/nested/data.json"), data)
```

### JSONFileOperations.load_json_safe()

Load JSON with guaranteed return (never raises).

**Signature:**
```python
@staticmethod
def load_json_safe(file_path: Path, default: dict[str, Any]) -> dict[str, Any]
```

**Parameters:**
- `file_path` (Path): Path to JSON file
- `default` (dict): Default value to return if load fails

**Returns:**
- `dict[str, Any]`: Loaded JSON data or default value

**Notes:**
- Logs errors but always returns a value
- Never raises exceptions
- Use for optional configuration files or when failures should be silent

**Examples:**

```python
from pathlib import Path
from sdd.core.file_ops import JSONFileOperations

# Always returns a dict, never raises
config = JSONFileOperations.load_json_safe(Path("config.json"), {})

# Use for optional settings
settings = JSONFileOperations.load_json_safe(
    Path("user_settings.json"),
    {"theme": "dark", "notifications": True}
)
```

## Backward Compatible Functions

For convenience and backward compatibility, the module provides simplified function interfaces:

### load_json()

Wrapper for `JSONFileOperations.load_json()` without optional parameters.

```python
from sdd.core.file_ops import load_json

data = load_json(Path("data.json"))  # Raises FileOperationError if not found
```

### save_json()

Wrapper for `JSONFileOperations.save_json()` with defaults.

```python
from sdd.core.file_ops import save_json

save_json(Path("data.json"), {"key": "value"})
```

## Migration Guide

### From Duplicate Internal Methods

If your code has internal `_load_json` or `_save_json` methods:

**Before:**
```python
class MyClass:
    def _load_json(self, file_path: Path) -> dict:
        with open(file_path) as f:
            return json.load(f)

    def _save_json(self, file_path: Path, data: dict) -> None:
        temp_path = file_path.with_suffix(".tmp")
        with open(temp_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        temp_path.replace(file_path)

    def load_config(self):
        return self._load_json(self.config_path)
```

**After:**
```python
from sdd.core.file_ops import load_json, save_json

class MyClass:
    def load_config(self):
        return load_json(self.config_path)
```

### Exception Handling Changes

The centralized functions raise `FileOperationError` instead of `FileNotFoundError`:

**Before:**
```python
try:
    data = self._load_json(path)
except FileNotFoundError:
    data = {}
```

**After:**
```python
from sdd.core.file_ops import JSONFileOperations

# Option 1: Use default parameter
data = JSONFileOperations.load_json(path, default={})

# Option 2: Use load_json_safe
data = JSONFileOperations.load_json_safe(path, {})

# Option 3: Catch FileOperationError
try:
    data = load_json(path)
except FileOperationError:
    data = {}
```

## Design Decisions

### Atomic Writes by Default

All saves use atomic writes (write to temp file, then rename) by default. This prevents corruption if the process crashes mid-write.

**Why atomic writes?**
- Prevents partial file writes
- Ensures data integrity
- Safe for concurrent access

**When to disable:**
```python
# For very large files where performance is critical and
# corruption risk is acceptable
JSONFileOperations.save_json(path, large_data, atomic=False)
```

### Validation Hooks

Optional validation allows enforcing data contracts:

```python
def validate_config(data: dict) -> bool:
    required_keys = {"version", "project_name", "session_dir"}
    return all(key in data for key in required_keys)

config = JSONFileOperations.load_json(
    Path("config.json"),
    validator=validate_config
)
```

### Automatic Directory Creation

Parent directories are created automatically by default:

```python
# Creates .session/data/ if it doesn't exist
JSONFileOperations.save_json(
    Path(".session/data/metrics.json"),
    metrics_data
)
```

## Best Practices

1. **Use `load_json_safe()` for optional files:**
   ```python
   # Config file might not exist yet
   config = JSONFileOperations.load_json_safe(config_path, DEFAULT_CONFIG)
   ```

2. **Use validation for critical data:**
   ```python
   # Ensure work item structure is valid
   validator = lambda d: "work_items" in d and isinstance(d["work_items"], dict)
   work_items = JSONFileOperations.load_json(path, validator=validator)
   ```

3. **Prefer centralized functions over direct JSON operations:**
   ```python
   # Good
   from sdd.core.file_ops import load_json, save_json

   # Avoid
   import json
   with open(path) as f:
       data = json.load(f)
   ```

4. **Let the module handle errors:**
   ```python
   # The module provides informative error messages
   try:
       data = load_json(path)
   except FileOperationError as e:
       logger.error(f"Configuration error: {e}")
       sys.exit(1)
   ```

## Testing

The file operations module has 97% test coverage. Key test scenarios:

- Valid file loading
- Missing file handling (with/without default)
- Invalid JSON detection
- Validation hook success/failure
- Atomic write verification
- Directory creation
- Error message clarity

See `tests/unit/test_file_ops.py` for comprehensive examples.
