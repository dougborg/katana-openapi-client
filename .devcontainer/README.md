# Development Container Configuration

This directory contains the configuration for the VS Code development container for the
Katana OpenAPI Client and MCP Server project.

## What's Included

### Base Image

- **Python 3.13** (official Microsoft Python devcontainer)
- **Git** pre-installed
- **GitHub CLI** (gh) for issue management
- **Node.js LTS** (for OpenAPI client generation with npx)

### Python Tools

- **uv** - Fast Python package manager
- **ruff** - Fast Python linter and formatter
- **mypy** - Static type checking
- **pytest** - Test framework
- **pre-commit** - Git hook framework

### VS Code Extensions

**Python Development**:

- Python extension with Pylance
- Ruff for linting and formatting

**Documentation**:

- Markdown All in One
- Markdown lint
- Better TOML support

**AI Assistance**:

- GitHub Copilot
- GitHub Copilot Chat

**DevOps**:

- Docker extension
- YAML support

## Quick Start

### Using VS Code

1. **Open in Container**:

   - Open this repository in VS Code
   - Click the green button in the lower-left corner
   - Select "Reopen in Container"

1. **Wait for Setup**:

   - The container will build and run `setup.sh`
   - This installs uv, syncs dependencies, and sets up pre-commit hooks
   - First build takes ~2-5 minutes

1. **Configure Environment**:

   ```bash
   # Edit .env file
   nano .env

   # Add your Katana API key
   KATANA_API_KEY=your-actual-key-here
   ```

1. **Verify Setup**:

   ```bash
   # Check all tools work
   uv run poe help

   # Run tests
   uv run poe test
   ```

### Manual Setup (Outside Container)

If you prefer to develop locally without the container:

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies
uv sync --all-extras

# Install pre-commit hooks
uv run pre-commit install

# Create .env file
cp .env.example .env  # Then edit with your API key
```

## Features

### Automatic Formatting

Files are formatted on save using Ruff:

- Import sorting
- Code style fixes
- Docstring formatting

### Integrated Testing

Run tests from VS Code:

- Click the testing icon in the sidebar
- Or use `uv run poe test` in the terminal

### GitHub Integration

GitHub CLI is pre-installed:

```bash
# View issues
gh issue list --label "mcp-server"

# View milestone
gh issue list --milestone "MCP Server v0.1.0 MVP"

# Claim an issue
gh issue comment 32 --body "Starting work on this"
```

## Port Forwarding

Port 8000 is automatically forwarded for:

- Running MCP server locally
- Testing HTTP endpoints
- Development servers

## Environment Variables

The container preserves your Git configuration from the host machine.

To add project-specific environment variables, edit `.env`:

- `KATANA_API_KEY` - Your Katana API key (required for integration tests)
- `KATANA_BASE_URL` - API base URL (defaults to production)

## Customization

To customize the container:

1. **Add VS Code extensions**: Edit `devcontainer.json` →
   `customizations.vscode.extensions`

1. **Change Python version**: Edit `devcontainer.json` → `image` to use different Python
   version

1. **Add system packages**: Create `.devcontainer/Dockerfile` and reference it instead
   of direct image

1. **Modify setup**: Edit `.devcontainer/setup.sh` to change post-create behavior

## Troubleshooting

### Container won't start

- Check Docker is running
- Try "Rebuild Container" from VS Code
- Check Docker logs: `docker logs <container-id>`

### uv not found

- The setup script should install uv automatically
- If not, run manually: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Reload the shell: `source ~/.bashrc`

### Tests fail with API errors

- Make sure `KATANA_API_KEY` is set in `.env`
- Integration tests require a valid API key
- Unit tests should work without API key

### Pre-commit hooks fail

- Run `uv run pre-commit run --all-files` to see errors
- Fix issues with `uv run poe format` and `uv run poe fix`

## Resources

- [VS Code Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers)
- [uv Documentation](https://docs.astral.sh/uv/)
- [MCP v0.1.0 Implementation Plan](../docs/mcp-server/MCP_V0.1.0_IMPLEMENTATION_PLAN.md)
- [MCP Architecture Design](../docs/mcp-server/MCP_ARCHITECTURE_DESIGN.md)
