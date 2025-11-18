---
description: Get the next recommended work item to start based on dependencies and priority
---

# Work Item Next

Get an intelligent recommendation for the next work item to start:

```bash
sk work-next
```

The recommendation algorithm analyzes:

- **Available Work Items**: All items with `not_started` status
- **Dependency Blocking**: Filters out items blocked by incomplete dependencies
- **Priority Sorting**: Ranks by priority (critical > high > medium > low)
- **Smart Selection**: Recommends the highest priority unblocked item

Display to the user:

- **Recommended Work Item**: Full details (ID, title, type, priority)
- **Selection Rationale**: Why this item was chosen
- **Dependency Status**: Confirmation that all dependencies are satisfied
- **Context**: Overview of other waiting items (both blocked and ready)

This helps maintain efficient workflow by always suggesting the most important work that can be started immediately.
