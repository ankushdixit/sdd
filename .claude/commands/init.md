---
description: Initialize a new Session-Driven Development project
---

# Session Init

Run the initialization command:

```bash
sdd init
```

**What it does (automatically):**
1. Detects project type (TypeScript/JavaScript/Python)
2. Creates/updates package manager files (package.json or pyproject.toml)
3. Creates all required config files from templates (.eslintrc, .prettierrc, jest.config, etc.)
4. Installs dependencies (npm install or pip install)
5. Creates smoke tests that validate SDD setup
6. Creates .session/ directory structure with tracking files
7. Generates project context files (stack.txt, tree.txt)
8. Updates .gitignore with SDD patterns

**Result:** Fully working SDD project, ready for first session.

**Only fails if:** `.session/` already exists (project already initialized)

---

## After Successful Init

Show the user the success output from the script, which includes:
- ✅ Summary of what was created/updated
- 🚀 Next step: `/sdd:work-new`

Explain briefly:

"Your project is now set up with Session-Driven Development! The next step is to create your first work item using `/sdd:work-new`. This will interactively guide you through defining what you want to build."

That's it! No manual setup steps, no config tweaking needed. Just works.
