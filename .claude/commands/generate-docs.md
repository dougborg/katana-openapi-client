# Generate Documentation

Generate or update documentation for the specified code, feature, or architectural
decision. If no target is specified, identify documentation gaps and address them.

## Documentation Types

### 1. Docstrings (Google Style)

Required for all public functions, classes, and modules:

```python
def unwrap_as(response: Response, expected_type: type[T]) -> T:
    """Extract and validate a parsed response as the expected type.

    Args:
        response: The HTTP response to unwrap.
        expected_type: The type to validate the parsed response against.

    Returns:
        The parsed response cast to the expected type.

    Raises:
        AuthenticationError: If the response is 401 Unauthorized.
        ValidationError: If the response is 422 Unprocessable Entity.
        APIError: For other non-success status codes.
    """
```

### 2. Architecture Decision Records (ADRs)

For architectural decisions, create an ADR in `docs/adr/`:

- Numbering: 4-digit sequential (`0001`, `0002`, etc.)
- Find next number: `ls docs/adr/*.md | grep -o '[0-9]\{4\}' | sort -n | tail -1`
- Use the template at `docs/adr/template.md`
- Update `docs/adr/README.md` index after creating

### 3. README Structure Template

When creating a new README or major documentation page:

```markdown
# Project/Package Name

Brief description of what this does and why it exists.

## Installation

How to install or set up.

## Quick Start

Minimal working example to get started fast.

## Usage

Detailed usage patterns with examples.

## API Reference

Key functions/classes with signatures and descriptions.

## Configuration

Environment variables, config files, options.

## Contributing

How to contribute (or link to CONTRIBUTING.md).
```

### 4. Cookbook Recipes

For new usage patterns, add to `docs/COOKBOOK.md`:

```markdown
### Recipe: [What You Want to Do]

**When to use**: [Scenario description]

\`\`\`python
# Working, tested code example
\`\`\`

**Notes**: [Gotchas, alternatives, related recipes]
```

### 5. User Guides

For complex features, create or update guides in `docs/`:

- Step-by-step instructions
- Working code examples (tested)
- Common pitfalls and solutions
- Links to related documentation

## Standards

See CLAUDE.md's "Detailed Documentation" table for project doc structure. Format
markdown with `uv run poe format` (88 char line length, ATX headers).

## Process

1. Read the target code or feature thoroughly
1. Identify which documentation type(s) are needed
1. Write documentation following the templates above
1. Verify all code examples are correct and tested
1. Run `uv run poe format` to format markdown
1. If updating MkDocs content, run `uv run poe docs-build` to verify

## Self-Improvement

If you notice that existing documentation is wrong, incomplete, or misleading while
generating new docs, fix it. Don't just document new things - improve what's already
there.
