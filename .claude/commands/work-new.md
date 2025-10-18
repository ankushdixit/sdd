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
python3 scripts/../sdd_cli.py work-new
```

The CLI will interactively prompt the user for:
- Work item type
- Title
- Priority
- Dependencies

This provides a guided experience for creating work items.

The script will:
- Generate a unique work item ID
- Create a specification file from the appropriate template at `.session/specs/{work_item_id}.md`
- Update work_items.json tracking file (metadata only)
- Display the created work item details and next steps

Show all output to the user including the work item ID and specification file path.

## Next Step: Fill Out the Spec File

**IMPORTANT:** After creating the work item, you must fill out the specification file:

1. Open `.session/specs/{work_item_id}.md` in your editor
2. Follow the template structure and inline guidance comments
3. Complete all required sections for the work item type
4. Remove HTML comment instructions when done

The spec file is the **single source of truth** for work item content. All implementation details, acceptance criteria, and testing strategies should be documented in the spec file, not in `work_items.json`.

For guidance on writing effective specs, see:
- `docs/writing-specs.md` - Best practices and examples
- `docs/spec-template-structure.md` - Template structure reference
- `templates/{type}_spec.md` - Template examples for each work item type
