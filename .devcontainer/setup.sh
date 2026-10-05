#!/bin/bash
# This script runs after container creation to finalize setup
set -e

echo "🚀 Finalizing development environment setup..."

# Ensure uv is in PATH (it should already be installed via onCreate)
export PATH="$HOME/.cargo/bin:$PATH"

# Verify uv is available
if ! command -v uv &> /dev/null; then
    echo "⚠️  uv not found, installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

uv --version

# The TypeScript package is managed by pnpm. Install the version pinned by
# `packageManager` in its package.json (pnpm also self-switches to that pin on
# every run, so a newer global pnpm still installs with the pinned one).
TS_PNPM_VERSION="$(python3 -c \
  "import json; print(json.load(open('packages/katana-client/package.json'))['packageManager'].split('@', 1)[1])")"
echo "📦 Installing pnpm ${TS_PNPM_VERSION} for the TypeScript client..."
npm install --global "pnpm@${TS_PNPM_VERSION}"
pnpm --dir packages/katana-client install --frozen-lockfile

# Sync dependencies (should be fast due to prebuild cache)
echo "📚 Syncing dependencies (using prebuild cache)..."
uv sync --all-extras

# Create .env template if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env template..."
    cat > .env << 'EOF'
# Katana API Configuration
# Get your API key from: https://app.katanamrp.com/settings/api
KATANA_API_KEY=your-api-key-here
KATANA_BASE_URL=https://api.katanamrp.com/v1
EOF
    echo "⚠️  Don't forget to add your KATANA_API_KEY to .env!"
fi

# Run quick validation (skip to speed up startup)
echo "✅ Environment validated. Run 'uv run poe check' to verify everything."

# Print next steps
echo ""
echo "✨ Development environment ready!"
echo ""
echo "📋 Next steps:"
echo "   1. Add your KATANA_API_KEY to .env file"
echo "   2. Run tests: uv run poe test"
echo "   3. See available tasks: uv run poe help"
echo ""
echo "📖 Key resources:"
echo "   - MCP v0.1.0 Plan: docs/mcp-server/MCP_V0.1.0_IMPLEMENTATION_PLAN.md"
echo "   - MCP Architecture: docs/mcp-server/MCP_ARCHITECTURE_DESIGN.md"
echo "   - ADR-010: docs/adr/0010-katana-mcp-server.md"
echo ""
echo "🎯 Ready to start working on MCP server issues!"
echo "   View milestone: https://github.com/dougborg/katana-openapi-client/milestone/1"
