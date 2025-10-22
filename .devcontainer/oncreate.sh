#!/bin/bash
# This script runs during Codespaces prebuild to cache dependencies
set -e

echo "🔨 Running onCreate (prebuild) setup..."

# Install uv (this gets cached in the prebuild)
echo "📦 Installing uv package manager..."
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"

# Verify uv installation
uv --version

# Sync all dependencies (this gets cached!)
echo "📚 Syncing project dependencies (will be cached)..."
uv sync --all-extras

# Install pre-commit hooks
echo "🪝 Installing pre-commit hooks..."
uv run pre-commit install
uv run pre-commit install-hooks

echo "✅ onCreate setup complete - dependencies cached for fast startup!"
