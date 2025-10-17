---
description: Initialize a new Session-Driven Development project
---

# Session Init

Run the initialization script to set up Session-Driven Development infrastructure:

```bash
python3 scripts/../sdd_cli.py init
```

This script will create:
- `.session/` directory structure with all subdirectories
- Tracking files: `work_items.json`, `learnings.json`, `status_update.json`
- Project context files: `stack.txt` and `tree.txt`

After running the script, show the user the success message and explain the next steps for getting started with the session-driven workflow.
