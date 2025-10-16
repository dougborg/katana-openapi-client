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
poetry run poe docs-build

# Serve documentation locally with live reload
poetry run poe docs-serve
```

The docs will be available at http://127.0.0.1:8000/

### Clean Build Artifacts

```bash
poetry run poe docs-clean
```

## Documentation Structure

```
docs/
├── index.md                      # Home page
├── KATANA_CLIENT_GUIDE.md        # Main user guide
├── CONTRIBUTING.md               # Contributing guidelines
├── TESTING_GUIDE.md              # Testing documentation
├── CHANGELOG.md                  # Release notes
├── openapi-docs.md               # OpenAPI spec viewer
├── gen_ref_pages.py              # API reference generator
├── katana-api-comprehensive/     # External Katana API docs (248 files)
└── reference/                    # Auto-generated API docs (built at runtime)
```

## Configuration

- **mkdocs.yml**: Main configuration file in project root
- **Material Theme**: Modern, responsive theme with dark mode support
- **mkdocstrings**: Auto-generates API reference from Python docstrings
- **swagger-ui-tag**: Renders interactive OpenAPI documentation

## Deployment

Documentation is deployed automatically via `.github/workflows/release.yml`:

1. Triggered on release (semantic-release creates tags)
1. Builds docs with `poetry run poe docs-build`
1. Deploys to `gh-pages` branch using peaceiris/actions-gh-pages
1. Available at GitHub Pages URL

### Manual Deployment

If needed, you can manually deploy docs:

```bash
# Build the docs
poetry run poe docs-build

# Deploy to gh-pages branch (requires push access)
poetry run mkdocs gh-deploy
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
