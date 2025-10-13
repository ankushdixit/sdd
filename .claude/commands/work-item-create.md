---
description: Create a new work item interactively
---

# Work Item Create

Start the interactive work item creation process:

```bash
python3 scripts/work_item_manager.py
```

The script will guide you through prompts for:
- **Work Item Type**: Choose from 6 types (feature, bug, refactor, security, integration_test, deployment)
- **Title**: Brief description of the work item
- **Priority**: Set priority level (critical, high, medium, low)
- **Dependencies**: Optional comma-separated list of work item IDs this depends on

The script automatically:
- Generates a unique work item ID
- Creates a specification file from the appropriate template
- Updates the work_items.json tracking file
- Shows suggested next steps

Guide the user through each prompt and display the results, including the generated work item ID and the path to the specification file.
