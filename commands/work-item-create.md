---
description: Create a new work item interactively
---

# Work Item Create

Guide the user through creating a new work item by asking for the following information:

## Questions to Ask

1. **Work Item Type** - Ask: "What type of work item is this?"
   - Options: feature, bug, refactor, security, integration_test, deployment
   - Explain each briefly if needed

2. **Title** - Ask: "What is the title/brief description?"
   - Should be concise and descriptive

3. **Priority** - Ask: "What is the priority level?"
   - Options: critical, high, medium, low
   - Default to "high" if user doesn't specify

4. **Dependencies** - Ask: "Are there any dependencies? (work item IDs, comma-separated, or 'none')"
   - Optional, can be empty

## After Collecting Information

Once you have all the information, create the work item by running:

```bash
python3 scripts/work_item_manager.py --type TYPE --title "TITLE" --priority PRIORITY --dependencies "DEP_IDS"
```

Replace:
- `TYPE` with the work item type
- `TITLE` with the title (use quotes if it contains spaces)
- `PRIORITY` with the priority level
- `DEP_IDS` with comma-separated dependency IDs (or omit `--dependencies` if none)

The script will:
- Generate a unique work item ID
- Create a specification file from the appropriate template
- Update work_items.json tracking file
- Display the created work item details and next steps

Show all output to the user including the work item ID and specification file path.
