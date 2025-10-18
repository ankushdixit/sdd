# Spec Template Structure Conventions

**Document Purpose:** Define the standardized structure and conventions used in all work item specification templates. This document serves as the specification for the `spec_parser.py` module.

**Version:** 1.0.0
**Last Updated:** October 18, 2025

---

## Overview

All spec templates in `templates/*_spec.md` follow a standardized markdown structure with:
- **Consistent heading hierarchy** (H1 for title, H2 for main sections, H3 for subsections)
- **HTML comments** for inline guidance (stripped during parsing)
- **Code blocks** with language identifiers for syntax highlighting
- **Checklists** using markdown task list syntax (`- [ ]`)
- **Mermaid diagrams** for visualizations (sequence diagrams, flowcharts)
- **Standardized section names** that parsers can reliably match

---

## Common Structure (All Templates)

### Title (H1)
```markdown
# [Work Item Type]: [Name]
```
- **Examples:** `# Feature: Real-time Notifications`, `# Bug: Session Timeout`, `# Deployment: Order API v2.5.0`
- **Parsing:** Extract work item type and name from H1

### Template Instructions (HTML Comment)
```markdown
<!--
TEMPLATE INSTRUCTIONS:
- Guidance for filling out the template
- Remove these instructions before finalizing
-->
```
- **Parsing:** Strip all HTML comments during parsing
- **Purpose:** User guidance only, not part of spec content

### Section Structure
- **H2 (`##`):** Main sections (e.g., `## Overview`, `## Testing Strategy`)
- **H3 (`###`):** Subsections (e.g., `### Approach`, `### Benefits`)
- **Inline comments:** `<!-- Explanation of what goes in this section -->`

---

## Section Naming Conventions

### Standardized Sections (Across All Templates)

These sections appear in multiple templates with consistent naming:

| Section Name | Templates | Content Type | Parseable Elements |
|--------------|-----------|--------------|-------------------|
| `## Overview` | feature, refactor | Paragraph | Text description |
| `## Rationale` | feature | Paragraph | Bullet points, text |
| `## Acceptance Criteria` | feature, security | Checklist | Task list items |
| `## Testing Strategy` | feature, bug, refactor | Mixed | Subsections, checklists |
| `## Dependencies` | All templates | List | Work item IDs, bullet points |
| `## Estimated Effort` | All templates | Text | Number + "sessions" |

### Work Item Type-Specific Sections

#### Feature Template

| Section | Subsections | Content |
|---------|-------------|---------|
| `## User Story` | None | "As a ... I want ... so that ..." |
| `## Implementation Details` | `### Approach`, `### LLM/Processing Configuration`, `### Components Affected`, `### API Changes`, `### Database Changes` | Code blocks, lists |
| `## Documentation Updates` | None | Checklist |

#### Bug Template

| Section | Subsections | Content |
|---------|-------------|---------|
| `## Description` | None | Paragraph |
| `## Steps to Reproduce` | None | Numbered list, code block |
| `## Expected Behavior` | None | Paragraph |
| `## Actual Behavior` | None | Paragraph, code block (error logs) |
| `## Impact` | None | Severity field, bullet points |
| `## Root Cause Analysis` | `### Investigation`, `### Root Cause`, `### Why It Happened` | Paragraphs, code blocks |
| `## Fix Approach` | None | Paragraph, code blocks |
| `## Prevention` | None | Bullet points |

#### Refactor Template

| Section | Subsections | Content |
|---------|-------------|---------|
| `## Current State` | None | Paragraph, code block (before) |
| `## Problems with Current Approach` | None | Bullet points |
| `## Proposed Refactor` | `### New Approach`, `### Benefits`, `### Trade-offs` | Code blocks (after), lists |
| `## Implementation Plan` | None | Numbered list with phases |
| `## Scope` | `### In Scope`, `### Out of Scope` | Bullet points |
| `## Risk Assessment` | None | Risk level, mitigation strategies |
| `## Success Criteria` | None | Checklist |

#### Security Template

| Section | Subsections | Content |
|---------|-------------|---------|
| `## Security Issue` | None | Paragraph, CVSS score |
| `## Severity` | None | Checklist (single selection), Impact assessment |
| `## Affected Components` | None | Bullet points with versions |
| `## Threat Model` | `### Assets at Risk`, `### Threat Actors`, `### Attack Scenarios` | Lists, code blocks (PoC) |
| `## Attack Vector` | None | Paragraph, code blocks |
| `## Mitigation Strategy` | None | Code blocks (before/after), lists |
| `## Security Testing` | `### Automated Security Testing`, `### Manual Security Testing`, `### Test Cases` | Checklists, code blocks |
| `## Compliance` | None | Checklist (standards: OWASP, CWE, PCI DSS, etc.) |
| `## Post-Deployment` | None | Checklist |

#### Integration Test Template

| Section | Subsections | Content |
|---------|-------------|---------|
| `## Scope` | None | Components list, integration points |
| `## Test Scenarios` | `### Scenario N: [Name]` | Description, mermaid diagram, setup, actions, expected results |
| `## Performance Benchmarks` | None | Response time, throughput, resource limits, load test config |
| `## API Contracts` | None | Contract files, example requests/responses (JSON) |
| `## Environment Requirements` | None | Services list, configuration (bash), infrastructure (YAML) |

#### Deployment Template

| Section | Subsections | Content |
|---------|-------------|---------|
| `## Deployment Scope` | None | Application details, target environment, scope of changes |
| `## Deployment Procedure` | `### Pre-Deployment Checklist`, `### Deployment Steps`, `### Post-Deployment Steps` | Checklists, bash code blocks |
| `## Environment Configuration` | None | Environment variables (bash), secrets list, infrastructure |
| `## Rollback Procedure` | `### Rollback Triggers`, `### Rollback Steps` | Lists, bash code blocks |
| `## Smoke Tests` | `### Test N: [Name]` | Bash code blocks with expected output |
| `## Monitoring & Alerting` | None | Dashboard URL, metrics list, alerts |
| `## Post-Deployment Monitoring Period` | None | Soak time checklist |

---

## Content Formatting Conventions

### 1. Code Blocks

**Syntax:**
```markdown
\```language
code here
\```
```

**Common Languages:**
- `typescript` / `javascript` - Source code
- `json` - API requests/responses, configuration
- `sql` - Database queries, schema
- `bash` - Commands, scripts
- `yaml` - Configuration files, docker-compose
- `mermaid` - Diagrams (sequence, flowcharts)

**Example:**
```markdown
\```typescript
async function example(): Promise<void> {
  // Code
}
\```
```

### 2. Checklists

**Syntax:**
```markdown
- [ ] Unchecked item
- [x] Checked item
```

**Parsing:**
- Extract checklist items as list of strings
- Preserve checked/unchecked state if present
- Items can span multiple lines with indentation

**Example:**
```markdown
- [ ] All tests pass
- [ ] Code review approved
- [x] Documentation updated
```

### 3. Lists

**Bulleted Lists:**
```markdown
- Item 1
- Item 2
  - Nested item
```

**Numbered Lists:**
```markdown
1. Step 1
2. Step 2
3. Step 3
```

**Parsing:** Extract list items, preserve nesting

### 4. Mermaid Diagrams

**Syntax:**
```markdown
\```mermaid
sequenceDiagram
    participant A
    participant B
    A->>B: Message
    B-->>A: Response
\```
```

**Usage:** Integration test scenarios, deployment flows, architecture

**Parsing:** Extract as raw mermaid source, don't render

### 5. Tables

**Syntax:**
```markdown
| Column 1 | Column 2 |
|----------|----------|
| Value 1  | Value 2  |
```

**Usage:** Performance benchmarks, configuration, comparisons

**Parsing:** Extract as structured data (list of dicts)

### 6. Inline Formatting

- **Bold:** `**text**` or `__text__`
- **Italic:** `*text*` or `_text_`
- **Code:** `` `code` ``
- **Links:** `[text](url)`

**Parsing:** Preserve or strip based on use case

---

## Parsing Guidelines for spec_parser.py

### General Principles

1. **Heading-Based Parsing:** Use H2 (`##`) headings as section delimiters
2. **Subsection Awareness:** Use H3 (`###`) headings for subsection content
3. **Flexible Matching:** Match section names case-insensitively, ignore extra whitespace
4. **Graceful Degradation:** If section not found, return `None` or empty, don't error
5. **Strip Comments:** Remove all HTML comments (`<!-- -->`) during parsing
6. **Preserve Code Blocks:** Keep code blocks intact with language identifier
7. **Extract Checklists:** Parse task lists into structured format

### Section Extraction Algorithm

**Pseudocode:**
```python
def extract_section(content: str, section_name: str) -> str:
    """
    Extract content between '## SectionName' and next '##' heading.

    Args:
        content: Full markdown content
        section_name: Name of section to extract (case-insensitive)

    Returns:
        Section content (excluding heading) or None if not found
    """
    lines = content.split('\n')
    in_section = False
    section_content = []

    for line in lines:
        if line.startswith('## '):
            heading = line[3:].strip()
            if heading.lower() == section_name.lower():
                in_section = True
                continue
            elif in_section:
                break  # Next section found, stop

        if in_section:
            section_content.append(line)

    if not section_content:
        return None

    return '\n'.join(section_content).strip()
```

### Subsection Extraction

**For subsections within a section:**
```python
def extract_subsection(section_content: str, subsection_name: str) -> str:
    """Extract content under '### SubsectionName'."""
    # Similar algorithm, but match '###' instead of '##'
```

### Checklist Extraction

```python
def extract_checklist(content: str) -> List[Dict[str, Any]]:
    """
    Extract checklist items from markdown.

    Returns:
        [
            {"text": "Item text", "checked": False},
            {"text": "Checked item", "checked": True},
            ...
        ]
    """
    checklist = []
    for line in content.split('\n'):
        match = re.match(r'-\s+\[([ x])\]\s+(.+)', line.strip())
        if match:
            checked = match.group(1) == 'x'
            text = match.group(2)
            checklist.append({"text": text, "checked": checked})
    return checklist
```

### Code Block Extraction

```python
def extract_code_blocks(content: str) -> List[Dict[str, str]]:
    """
    Extract all code blocks from content.

    Returns:
        [
            {"language": "typescript", "code": "..."},
            {"language": "bash", "code": "..."},
            ...
        ]
    """
    # Match ```language\n...\n``` pattern
    # Return list of code blocks with language and content
```

---

## Special Subsections

### LLM/Processing Configuration (Feature Template)

The `### LLM/Processing Configuration` subsection within "Implementation Details" documents how a feature processes data, particularly when LLM-based processing, deterministic algorithms, or external API integrations are involved.

**Usage Patterns:**

1. **LLM-based Features** - For features using LLMs (e.g., DSPy framework):
   ```markdown
   **Type:** LLM-based (DSPy)

   **DSPy Signature:**
   ```python
   class ExampleSignature(dspy.Signature):
       """Description."""
       input_field = dspy.InputField(desc="...")
       output_field = dspy.OutputField(desc="...")
   ```

   **LLM Provider:** Google AI Studio (Gemini 2.5 Flash)

   **LLM Usage:**
   - How the LLM is used
   - Fallback strategy
   ```

2. **Deterministic Features** - For features using traditional algorithms:
   ```markdown
   **Type:** Deterministic (No LLM)

   **Processing Type:**
   - Algorithm details
   - Data transformations
   ```

3. **External API Integrations** - For features calling external services:
   ```markdown
   **Type:** External API Integration (No LLM)

   **API Provider:** [Name]
   **Processing Type:**
   - API call patterns
   - Response handling

   **Rate Limits:** [Details]
   ```

4. **Standard Features** - For typical application logic:
   ```markdown
   Not Applicable - Standard application logic without LLM or special processing requirements.
   ```

**When to Use:**
- Feature involves LLM processing (especially DSPy-based agents)
- Feature uses non-trivial data processing algorithms
- Feature integrates with external APIs
- Otherwise: state "Not Applicable"

**Parser Field:** `implementation_details.llm_processing_config`

---

## Validation Rules

### Required Sections by Work Item Type

**Feature:**
- ✅ Required: Overview, Rationale, Acceptance Criteria, Implementation Details, Testing Strategy, Dependencies
- ⚠️ Optional: User Story, Documentation Updates

**Bug:**
- ✅ Required: Description, Steps to Reproduce, Expected Behavior, Actual Behavior, Impact, Root Cause Analysis, Fix Approach, Testing Strategy
- ⚠️ Optional: Prevention

**Refactor:**
- ✅ Required: Overview, Current State, Problems with Current Approach, Proposed Refactor, Scope, Testing Strategy
- ⚠️ Optional: Risk Assessment, Success Criteria

**Security:**
- ✅ Required: Security Issue, Severity, Affected Components, Threat Model, Attack Vector, Mitigation Strategy, Security Testing, Compliance
- ⚠️ Optional: Post-Deployment

**Integration Test:**
- ✅ Required: Scope, Test Scenarios (at least 1), Performance Benchmarks, Environment Requirements, Acceptance Criteria
- ⚠️ Optional: API Contracts

**Deployment:**
- ✅ Required: Deployment Scope, Deployment Procedure, Environment Configuration, Rollback Procedure, Smoke Tests, Acceptance Criteria
- ⚠️ Optional: Monitoring & Alerting, Post-Deployment Monitoring Period

### Content Validation

1. **Acceptance Criteria:** Must have at least 3 checklist items
2. **Test Scenarios:** Must include at least 1 scenario with setup, actions, expected results
3. **Code Blocks:** Must have language identifier
4. **Severity (security):** Must have exactly 1 checked severity level
5. **Dependencies:** Must be parseable as list of work item IDs

---

## Example Parsed Output

**Input (feature_spec.md):**
```markdown
## Acceptance Criteria

- [ ] Users can see notifications in real-time
- [ ] Notifications are displayed non-intrusively
- [ ] All tests pass

## Implementation Details

### API Changes

\```typescript
interface Notification {
  id: string;
  message: string;
}
\```
```

**Output (parsed structure):**
```python
{
    "acceptance_criteria": [
        {"text": "Users can see notifications in real-time", "checked": False},
        {"text": "Notifications are displayed non-intrusively", "checked": False},
        {"text": "All tests pass", "checked": False}
    ],
    "implementation_details": {
        "api_changes": [
            {
                "language": "typescript",
                "code": "interface Notification {\n  id: string;\n  message: string;\n}"
            }
        ]
    }
}
```

---

## Future Enhancements

1. **Schema Validation:** JSON schema for parsed output
2. **Type Inference:** Detect work item type from spec content
3. **Link Resolution:** Parse and validate work item ID references
4. **Diagram Validation:** Validate mermaid syntax
5. **Template Versioning:** Support multiple template versions

---

## Parser Implementation Checklist

When implementing `spec_parser.py`, ensure:

- [ ] Parse all 6 work item types (feature, bug, refactor, security, integration_test, deployment)
- [ ] Extract common sections (overview, dependencies, estimated effort)
- [ ] Extract work-type-specific sections
- [ ] Handle missing sections gracefully (return None or empty)
- [ ] Strip HTML comments
- [ ] Preserve code blocks with language identifiers
- [ ] Extract checklists with checked status
- [ ] Extract lists (bulleted and numbered)
- [ ] Extract mermaid diagrams
- [ ] Handle malformed markdown without crashing
- [ ] Provide detailed error messages for validation failures
- [ ] Include line numbers in error messages (if possible)
- [ ] Support both file path and string content as input

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-18 | Initial documentation based on Phase 5.7.4 template enhancements |
