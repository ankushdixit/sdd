# Installation Test Findings - Fresh macOS

**Test Date:** 2025-11-10
**Test Environment:** Fresh MacBook with no development tools installed
**Tester:** New user simulation (non-technical)

## Critical Issues Found

### Issue #1: README Uses Wrong pip Command ⚠️
**Problem:** README says `pip install solokit` but fresh macOS only has `pip3`
**User Impact:** First command in installation instructions fails
**Error Message:** `zsh: command not found: pip`
**Fix Required:** Update README to use `pip3 install solokit`

---

### Issue #2: Missing Command Line Tools Warning ⚠️
**Problem:** README doesn't mention macOS Command Line Tools requirement
**User Impact:**
- Unexpected 5-10 minute delay when tools install
- User sees popup asking for permission to install developer tools
- User doesn't know if this is normal or an error

**What Happened:**
```
xcode-select: note: No developer tools were found, requesting install
```

**Fix Required:** Add prerequisite section warning about:
- Command Line Tools installation (automatic on first pip3 use)
- Expected 5-10 minute delay
- This is normal macOS behavior

---

### Issue #3: PATH Issue Not Documented ⚠️
**Problem:** After `pip3 install solokit`, the `sk` command doesn't work
**User Impact:** Users think installation failed
**Error Message:**
```
WARNING: The script sk is installed in '/Users/username/Library/Python/3.9/bin' which is not on PATH.
```

**Fix Required:** Add post-installation PATH setup instructions:
```bash
echo 'export PATH="$HOME/Library/Python/3.9/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

---

### Issue #4: PyPI Package Completely Broken 🚨 **CRITICAL**
**Problem:** PyPI package missing ALL Python submodules
**Root Cause:** `pyproject.toml` line 62 only included top-level package:
```toml
packages = ["solokit"]  # WRONG - missing all subpackages
```

**User Impact:**
- Package only 13 KB instead of ~500 KB
- Software completely unusable
- Error on first run:
```
ModuleNotFoundError: No module named 'solokit.core'
```

**Fix Applied:** ✅
- Changed to `[tool.setuptools.packages.find]` to auto-discover all packages
- Package now 441 KB with all modules included

---

### Issue #5: Missing Claude Code Slash Commands 🚨 **CRITICAL**
**Problem:** `.claude/commands/` not included in PyPI package
**User Impact:**
- Users who install via PyPI can't use slash commands
- No `/start`, `/end`, `/work-new`, etc. in their projects
- Missing core feature mentioned in README

**Fix Applied:** ✅
- Copied `.claude/commands/` to `src/solokit/templates/.claude/commands/`
- Created `claude_commands_installer.py` module
- Updated `sk init` to copy commands to user projects
- Excluded developer docs (COMMANDS_README.md, COMMAND_FORMAT.md)

---

### Issue #6: Old pip Warning (Minor) ⚠️
**Message:**
```
WARNING: You are using pip version 21.2.4; however, version 25.3 is available.
```

**User Impact:** Minor - confusing but doesn't break functionality
**Fix Required:** Optional - could add note that this warning is safe to ignore

---

## Summary Statistics

| Metric | Before | After |
|--------|--------|-------|
| **Package Size (wheel)** | 13 KB | 441 KB |
| **Included Modules** | 1 | 15+ |
| **Command Files** | 0 | 16 |
| **Functionality** | ❌ Broken | ✅ Working |

---

## Recommended README Updates

### 1. Update Installation Section

**Old:**
```bash
pip install solokit
```

**New:**
```bash
# Install Solokit
pip3 install solokit

# Add sk command to PATH (macOS/Linux)
echo 'export PATH="$HOME/Library/Python/3.9/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Verify installation
sk status
```

### 2. Add Prerequisites Section

```markdown
### Prerequisites & Setup

**First-time macOS users:** When you run `pip3` for the first time, macOS will prompt you to install Command Line Tools. This is normal and required. The installation takes 5-10 minutes.

**After installation:** You may need to add Solokit to your PATH:
\`\`\`bash
echo 'export PATH="$HOME/Library/Python/3.9/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
\`\`\`

Then verify:
\`\`\`bash
sk status
\`\`\`
```

### 3. Add Troubleshooting Section

```markdown
### Troubleshooting

**"command not found: sk"**
- Solution: Add `$HOME/Library/Python/3.9/bin` to your PATH (see Prerequisites)

**"command not found: pip"**
- Solution: Use `pip3` instead of `pip` on macOS

**"xcode-select: note: No developer tools were found"**
- This is normal on fresh macOS - allow the installation to complete
```

---

## Files Changed in Fix

1. `pyproject.toml` - Fixed package discovery and data files
2. `src/solokit/init/claude_commands_installer.py` - New module to install commands
3. `src/solokit/init/orchestrator.py` - Added Step 17.5 to install commands
4. `src/solokit/templates/.claude/commands/` - Added 16 command files for packaging

---

## Testing Checklist for Next Release

- [ ] Build package: `python3 -m build`
- [ ] Verify size: `ls -lh dist/` (should be ~440 KB)
- [ ] Check contents: `unzip -l dist/*.whl | grep "solokit/core"`
- [ ] Check commands: `unzip -l dist/*.whl | grep "templates/.claude/commands" | wc -l` (should be 16)
- [ ] Test installation in clean virtualenv
- [ ] Test `sk status` works immediately after install
- [ ] Test `sk init` creates `.claude/commands/` in user project

---

## Lessons Learned

1. **Always test on clean environment** - Developer machines hide dependency issues
2. **PyPI package verification is critical** - Check tarball AND wheel contents
3. **PATH issues are common** - Need explicit documentation
4. **macOS-specific quirks** - Command Line Tools, pip vs pip3
5. **Package size is a red flag** - 13 KB was a clear indicator something was wrong
