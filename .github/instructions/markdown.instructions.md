______________________________________________________________________

## description: 'Markdown formatting standards for documentation' applyTo: '\*\*/\*.md'

# Markdown Documentation Standards

## Formatting Tool

- **Always use mdformat** for consistency
- Run `uv run poe format` to format all markdown files
- Run `uv run poe format-check` to verify formatting

## Line Length

- **88 characters maximum** (matches ruff for code)
- mdformat handles wrapping automatically

## Headers

```markdown
# Top Level (Document Title)

## Second Level (Major Sections)

### Third Level (Subsections)

#### Fourth Level (Details)
```

- Use ATX style (`# Header`) not underline style
- Don't skip header levels
- One blank line before and after headers

## Lists

### Unordered Lists

```markdown
- Item 1
- Item 2
  - Nested item
  - Another nested item
- Item 3
```

- Use `-` (hyphen) consistently, not `*` or `+`
- Indent nested items with 2 spaces

### Ordered Lists

```markdown
1. Step 1
2. Step 2
3. Step 3
```

- Use `1.` numbering (mdformat handles sequential)
- Don't manually number (mdformat fixes)

### Task Lists

```markdown
- [x] Completed task
- [ ] Pending task
- [ ] Another pending task
```

## Code Blocks

**Always specify language:**

````markdown
```python
def example():
    return "code"
```

```bash
uv run poe test
```

```yaml
key: value
```
````

- Never use unlabeled code blocks
- Use appropriate language for syntax highlighting

## Emphasis

```markdown
**Bold** for strong emphasis and UI elements
*Italic* for terminology on first use
`Code` for code elements, commands, file paths
```

## Links

```markdown
[Inline link](https://example.com)

[Reference link][ref]

[ref]: https://example.com "Optional title"

[Internal link](../path/to/file.md)
```

- Use reference-style for repeated links
- Verify all links work (internal and external)

## Tables

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
| Value 4  | Value 5  | Value 6  |
```

- Use mdformat to align columns automatically
- Include header separator row

## Images

```markdown
![Alt text](path/to/image.png)

![Alt text with title](path/to/image.png "Image title")
```

- Always include descriptive alt text
- Use relative paths for local images

## Code Examples

Include working, tested examples:

````markdown
```python
from katana_public_api_client import KatanaClient

async with KatanaClient() as client:
    response = await get_products.asyncio_detailed(client=client)
    print(f"Found {len(response.parsed.data)} products")
````

````

## Blockquotes

```markdown
> This is a quoted section.
> It can span multiple lines.
````

## Horizontal Rules

```markdown
---
```

- Use `---` (three hyphens)
- One blank line before and after

## ADR-Specific Standards

For Architecture Decision Records:

```markdown
# ADR-NNNN: Title in Title Case

## Status

[Proposed | Accepted | Deprecated | Superseded by ADR-XXXX]

Date: YYYY-MM-DD

## Context

[Problem description...]

## Decision

[What was decided...]

## Consequences

### Positive
- Benefit 1

### Negative
- Tradeoff 1

## Alternatives Considered

### Alternative 1: Name

**Pros:**
- Pro 1

**Cons:**
- Con 1

**Why not chosen:**
- Reason

## References

- Link 1
- Link 2
```

## Critical Reminders

1. **Always format with mdformat** - Run before committing
1. **Test code examples** - Ensure they actually work
1. **Verify links** - Broken links frustrate users
1. **Specify code block language** - Required for syntax highlighting
1. **Use reference links** - For repeated URLs
1. **Keep line length** - 88 characters maximum
1. **One blank line** - Before/after headers, code blocks, lists
