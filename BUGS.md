# SDD Bug Tracker

This document tracks bugs discovered during development and testing.

## Status Legend
- 🔴 CRITICAL - Blocks core functionality
- 🟠 HIGH - Significant impact on user experience
- 🟡 MEDIUM - Noticeable but has workarounds
- 🟢 LOW - Minor issue or cosmetic
- ✅ FIXED - Bug has been resolved

---

## Bug #20: Learning Curator Extracts Incomplete and Example Learnings

**Status:** 🟠 HIGH

**Discovered:** 2025-10-22 (During Session 1 - Enhancement #4 dogfooding)

### Problem

The learning curator has two bugs when extracting learnings during `/sdd:end`:

1. **Truncated learnings** - Multi-line LEARNING statements in commit messages are cut off at the first newline
2. **Extracts documentation examples** - Pulls example LEARNING statements from ENHANCEMENTS.md and other docs as if they were real learnings

### Current Behavior

When running `/sdd:end`, learnings.json contains:

**Truncated Learnings:**
```json
{
  "content": "The .gitignore patterns are added programmatically in",
  "source": "git_commit"
}
```

**Expected:**
```json
{
  "content": "The .gitignore patterns are added programmatically in ensure_gitignore_entries() function, not from a template file. This allows dynamic checking of which patterns already exist.",
  "source": "git_commit"
}
```

**Garbage from Examples:**
```json
{
  "content": "<your learning here>",
  "source": "inline_comment",
  "context": "ENHANCEMENTS.md:123"
}
```

### Root Cause

**Bug 1 - Truncated Learnings (scripts/learning_curator.py:570)**
```python
learning_pattern = r"LEARNING:\s*(.+?)(?=\n|$)"
```
This regex only captures to the first newline, stopping at line breaks even if the LEARNING statement continues.

**Bug 2 - Extracting from Documentation (extract_from_code_comments)**
The `extract_from_code_comments()` function scans ALL files including documentation (.md files) that contain example LEARNING statements for teaching purposes. These examples get extracted as real learnings.

### Impact

- **User Confusion**: Learnings database fills with incomplete/garbage entries
- **Loss of Context**: Truncated learnings lose valuable information
- **Data Quality**: Examples pollute the real learnings database
- **Curation Overhead**: Manual cleanup required after every session

### Expected Behavior

1. **Multi-line capture**: LEARNING statements should be captured completely, including line breaks within the statement
2. **Source filtering**: Only extract from actual source code files (.py, .js, .ts), not documentation files (.md)
3. **Validation**: Skip obvious garbage like placeholders ("<your learning here>")

### Proposed Solution

#### Fix 1: Multi-line Learning Capture
Update regex to capture until the next blank line or end of message:

```python
# Before
learning_pattern = r"LEARNING:\s*(.+?)(?=\n|$)"

# After
learning_pattern = r"LEARNING:\s*(.+?)(?=\n\n|\Z)"  # Capture until double newline or end
```

Or handle multi-line in a different way:
```python
learning_pattern = r"LEARNING:\s*(.+?)(?=(?:\n(?![ \t]))|$)"  # Capture until unindented line
```

#### Fix 2: Filter Documentation Files
Update `extract_from_code_comments()` to skip documentation:

```python
def extract_from_code_comments(self):
    """Extract learnings from code comments (not documentation)."""
    learnings = []

    # Only scan actual code files
    code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs'}
    doc_extensions = {'.md', '.txt', '.rst'}

    for file_path in self._get_project_files():
        # Skip documentation files
        if file_path.suffix in doc_extensions:
            continue

        # Skip example/template directories
        if 'examples' in file_path.parts or 'templates' in file_path.parts:
            continue

        if file_path.suffix in code_extensions:
            # ... extract from this file
```

#### Fix 3: Validate Content
Add validation to skip garbage:

```python
def is_valid_learning(content: str) -> bool:
    """Check if extracted content is a valid learning."""
    # Skip placeholders and examples
    if '<' in content or '>' in content:
        return False
    if content in ['your learning here', 'example learning']:
        return False
    # Must have substance (more than just a few words)
    if len(content.split()) < 5:
        return False
    return True
```

### Reproduction Steps

1. Run `sdd init` in a project
2. Create a work item and start a session
3. Make commits with multi-line LEARNING statements:
   ```
   LEARNING: This is a multi-line learning that spans
   several lines to provide comprehensive context about
   the implementation.
   ```
4. Run `/sdd:end`
5. Check `.session/tracking/learnings.json`
6. Observe truncated learnings and documentation examples

### Workaround

Manually edit `.session/tracking/learnings.json` to:
1. Remove garbage entries (examples, placeholders)
2. Complete truncated learnings by checking git commit messages

### Related Issues

- Discovered during dogfooding Enhancement #4
- Session 1 generated 12 learnings, only 3 were valid

### Files Affected

- `scripts/learning_curator.py:570` - Regex pattern
- `scripts/learning_curator.py` - `extract_from_code_comments()` method
- `.session/tracking/learnings.json` - Affected by bug

---

## Bug Template

```markdown
## Bug #XX: [Title]

**Status:** 🔴/🟠/🟡/🟢/✅

**Discovered:** YYYY-MM-DD

### Problem
Brief description of the bug

### Current Behavior
What happens now

### Expected Behavior
What should happen

### Root Cause
Why this happens

### Impact
Effect on users/system

### Proposed Solution
How to fix it

### Reproduction Steps
1. Step 1
2. Step 2
3. Observe issue

### Workaround
Temporary fix if available

### Related Issues
Links or references

### Files Affected
- file1.py
- file2.py
```
