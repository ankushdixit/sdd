---
description: Search learnings by keyword
argument-hint: <query>
---

# Search Learnings

Full-text search across all learning content, tags, and context.

## Usage

Extract the search query from $ARGUMENTS and run:

```bash
sk learn-search "$@"
```

### How Search Works

The search looks for matches in:

- Learning content (main text)
- Tags
- Context/notes
- Category names

Search is case-insensitive and finds partial matches.

### Examples

Search for "CORS":

```bash
sk learn-search "CORS"
```

Search for "FastAPI middleware":

```bash
sk learn-search "FastAPI middleware"
```

Search for "authentication":

```bash
sk learn-search "authentication"
```

## Display Format

Show matching learnings with:

- Learning content with matched text highlighted
- Category and tags
- Session where captured
- Relevance score or match indicator
- Learning ID

Present results in order of relevance, grouped by category.

## Tips for Users

Suggest to users:

- Use specific keywords for better results
- Try tag names if searching by topic
- Use category names to narrow results
- Combine with `/learn-show --category` for focused browsing
