# Documentation Structure

This directory contains the source files for the project documentation, built with
MkDocs and deployed to GitHub Pages.

## Documentation Site

**Live Site**: https://dougborg.github.io/katana-openapi-client/

The documentation is automatically built and deployed on every release via GitHub
Actions.

## Local Development

### Build Documentation

```bash
# Build documentation (outputs to ./site)
uv run poe docs-build

# Serve documentation locally with live reload
uv run poe docs-serve
```

The docs will be available at http://127.0.0.1:8000/

### Clean Build Artifacts

```bash
uv run poe docs-clean
```

## Documentation Structure

This is a monorepo with module-local documentation. Each package has its own `docs/`
directory:

```
docs/                                # Shared/monorepo documentation
├── index.md                         # Home page
├── CONTRIBUTING.md                  # Contributing guidelines
├── CODE_OF_CONDUCT.md              # Code of conduct
├── MONOREPO_SEMANTIC_RELEASE.md    # Semantic release guide
├── UV_USAGE.md                     # uv package manager guide
├── PYPI_SETUP.md                   # PyPI publishing setup
├── RELEASE.md                      # Release documentation
├── openapi-docs.md                 # OpenAPI spec viewer
├── gen_ref_pages.py                # API reference generator
├── client/                         # Symlink → katana_public_api_client/docs
├── mcp-server/                     # Symlink → katana_mcp_server/docs
├── adr/                            # Shared/monorepo ADRs
│   └── 0009-migrate-from-poetry-to-uv.md
└── reference/                      # Auto-generated API docs (built at runtime)

katana_public_api_client/docs/       # Python client documentation
├── README.md                        # Client docs index
├── guide.md                         # Client user guide
├── cookbook.md                      # Usage recipes
├── testing.md                       # Testing documentation
├── CHANGELOG.md                     # Client changelog
└── adr/                            # Client ADRs (001-008, 011-012)

katana_mcp_server/docs/              # MCP server documentation
├── README.md                        # MCP docs index
├── architecture.md                  # MCP architecture design
├── development.md                   # Development guide
├── deployment.md                    # Deployment guide
├── docker.md                        # Docker deployment
├── implementation-plan.md           # Implementation roadmap
├── stocktrim-migration.md           # StockTrim migration plan
└── adr/                            # MCP ADRs (010)

packages/katana-client/docs/         # TypeScript client documentation
├── guide.md                         # TypeScript usage guide
├── cookbook.md                      # Usage recipes
├── testing.md                       # Testing documentation
└── adr/                            # TypeScript ADRs (001-003)
```

## Configuration

- **mkdocs.yml**: Main configuration file in project root
- **Material Theme**: Modern, responsive theme with dark mode support
- **mkdocstrings**: Auto-generates API reference from Python docstrings
- **swagger-ui-tag**: Renders interactive OpenAPI documentation

## Deployment

Documentation is deployed automatically via `.github/workflows/release.yml`:

1. Triggered on release (semantic-release creates tags)
1. Builds docs with `uv run poe docs-build`
1. Deploys to `gh-pages` branch using peaceiris/actions-gh-pages
1. Available at GitHub Pages URL

### Manual Deployment

If needed, you can manually deploy docs:

```bash
# Build the docs
uv run poe docs-build

# Deploy to gh-pages branch (requires push access)
uv run mkdocs gh-deploy
```

## Improvements Needed

### High Priority

- [ ] Configure custom domain DNS (katana-openapi-client.dougborg.org)
- [ ] Add version information to docs (currently using mike but not configured)
- [ ] Consider removing or consolidating 248 katana-api-comprehensive files

### Medium Priority

- [ ] Add search optimization
- [ ] Add more code examples to API reference
- [ ] Add diagrams for architecture explanation

### Low Priority

- [ ] Add social media cards (og:image)
- [ ] Add analytics (if desired)
- [ ] Add "Edit this page" links (already configured in theme)
