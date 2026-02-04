# ADR-0013: Module-Local Documentation Structure

## Status

Accepted

Date: 2025-11-05

## Context

The monorepo had inconsistent documentation organization that made it difficult for
contributors to find relevant information and didn't align with modern Python monorepo
best practices.

### Problems with Previous Structure

1. **Documentation scattered across multiple locations**:

   - Client docs at root `docs/` (8 guides + 8 ADRs)
   - MCP docs split between `docs/mcp-server/` (5 files) and `katana_mcp_server/` (2
     files)
   - No clear module boundaries

1. **ADRs mixed by scope**:

   - Root `docs/adr/` contained client ADRs (001-008, 011-012), MCP ADR (010), and
     shared ADR (009)
   - Made it unclear which ADRs applied to which package

1. **Examples not organized by module**:

   - All examples in flat `examples/` directory
   - No separation between client and MCP examples

1. **Difficult to extract packages**:

   - Package-specific docs didn't travel with the package
   - Would need extensive refactoring to split packages into separate repos

1. **Questions about organization**:

   - "Where are the client docs?" → Unclear (some in root docs/, some might be
     elsewhere)
   - "Where are the MCP docs?" → Very unclear (split across 3 locations)
   - "Which ADRs apply to the client?" → Required reading all ADRs to determine

## Decision

We will reorganize documentation into a **module-local structure** where each package
has its own `docs/` subdirectory containing all module-specific documentation, including
ADRs.

### New Structure

```
katana-openapi-client/
│
├── katana_public_api_client/          # CLIENT PACKAGE
│   ├── [source code...]
│   └── docs/                          # Client-specific docs
│       ├── README.md                  # Navigation/index
│       ├── guide.md                   # User guide
│       ├── testing.md                 # Testing strategy
│       ├── cookbook.md                # Usage recipes
│       ├── CHANGELOG.md               # Release notes
│       └── adr/                       # Client ADRs (001-008, 011-012)
│
├── katana_mcp_server/                 # MCP PACKAGE
│   ├── [source code...]
│   └── docs/                          # MCP-specific docs
│       ├── README.md                  # Navigation/index
│       ├── architecture.md            # MCP architecture
│       ├── development.md             # Development guide
│       ├── deployment.md              # Deployment guide
│       ├── docker.md                  # Docker guide
│       ├── implementation-plan.md     # Implementation roadmap
│       └── adr/                       # MCP ADRs (010)
│
├── docs/                              # SHARED MONOREPO DOCS
│   ├── index.md                       # Landing page
│   ├── CONTRIBUTING.md                # Shared contribution guide
│   ├── CODE_OF_CONDUCT.md             # Code of conduct
│   ├── MONOREPO_SEMANTIC_RELEASE.md   # Shared release guide
│   ├── UV_USAGE.md                    # Shared tooling
│   ├── PYPI_SETUP.md                  # PyPI publishing
│   ├── RELEASE.md                     # Release process
│   ├── client/                        # Symlink → ../katana_public_api_client/docs
│   ├── mcp-server/                    # Symlink → ../katana_mcp_server/docs
│   └── adr/                           # Shared/monorepo ADRs (009, 013)
│
└── examples/                          # EXAMPLES
    ├── README.md                      # Examples index
    ├── client/                        # Client examples
    └── mcp-server/                    # MCP examples (placeholder)
```

### Implementation

1. Created `katana_public_api_client/docs/` and `katana_mcp_server/docs/` directories
1. Moved client docs and ADRs to client package
1. Moved MCP docs and ADRs to MCP package
1. Reorganized examples by module
1. Created symlinks from `docs/client/` and `docs/mcp-server/` to module docs
1. Updated all internal links and references
1. Updated `mkdocs.yml` navigation structure

## Consequences

### Positive Consequences

1. **Clear Module Boundaries**: Each package has complete, self-contained documentation
1. **Improved Discoverability**: Easy to find docs - client docs in client package, MCP
   docs in MCP package
1. **Better ADR Organization**: ADRs organized by scope (client/MCP/shared)
1. **Package Extractability**: Documentation travels with the package - could extract to
   separate repo without refactoring
1. **Consistent with Modern Practices**: Aligns with Python monorepo best practices
1. **Better mkdocs Integration**: Root `docs/` aggregates everything via symlinks
1. **Easier Navigation**: Clear navigation structure by module in documentation site

### Negative Consequences

1. **More Complex Directory Structure**: More directories to navigate (though better
   organized)
1. **Symlinks Required**: CI/CD must handle symlinks or copy files for documentation
   builds
1. **Cross-References**: Some documentation cross-references require relative paths
   (e.g., `../../`)

### Neutral Consequences

1. **Documentation Paths Changed**: All documentation paths updated - old
   bookmarks/links will break
1. **Git History**: File moves preserved in git history but may complicate some git
   operations

## Alternatives Considered

### Alternative 1: Keep Flat Structure

- **Description**: Keep all docs in root `docs/` directory with subdirectories for
  different topics
- **Pros**: Simpler structure, easier to browse all docs at once
- **Cons**: Doesn't scale to multiple packages, unclear ownership, difficult to extract
  packages
- **Why rejected**: Doesn't support monorepo evolution and package independence

### Alternative 2: Duplicate Documentation

- **Description**: Keep docs in both root `docs/` and package directories
- **Pros**: Easy to find docs in either location
- **Cons**: Synchronization nightmare, source-of-truth unclear, duplicated maintenance
- **Why rejected**: Unsustainable maintenance burden

### Alternative 3: Documentation in Separate Repo

- **Description**: Move all documentation to a separate repository
- **Pros**: Clean separation, focused documentation repo
- **Cons**: Docs far from code, version synchronization issues, harder to keep docs
  updated
- **Why rejected**: Best practice is to keep docs with code

## References

- Issue: dougborg/katana-openapi-client#118 - Documentation reorganization
- [Python Packaging Guide](https://packaging.python.org/) - Modern Python packaging
  practices
- [Monorepo Best Practices](https://monorepo.tools/) - Monorepo organization patterns
- [ADR-009: Migrate to uv](0009-migrate-from-poetry-to-uv.md) - Related monorepo
  decision
- [ADR-010: Katana MCP Server](../../katana_mcp_server/docs/adr/0010-katana-mcp-server.md)
  \- MCP server architecture
