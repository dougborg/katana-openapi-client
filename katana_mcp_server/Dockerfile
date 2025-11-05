# Katana MCP Server Docker Image
# Provides an isolated, secure environment for running the Katana Manufacturing ERP MCP server
# Compatible with Docker MCP Catalog and Toolkit

FROM python:3.14-slim

# Metadata
LABEL org.opencontainers.image.title="Katana MCP Server"
LABEL org.opencontainers.image.description="Model Context Protocol server for Katana Manufacturing ERP"
LABEL org.opencontainers.image.version="0.1.0"
LABEL org.opencontainers.image.vendor="Doug Borg"
LABEL org.opencontainers.image.source="https://github.com/dougborg/katana-openapi-client"
LABEL org.opencontainers.image.licenses="MIT"

# Set working directory
WORKDIR /app

# Install uv for fast dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files and source code
COPY pyproject.toml /app/
COPY src/ /app/src/
COPY README.md /app/

# Install package
RUN uv pip install --system --no-cache .

# Create non-root user for security
RUN useradd -m -u 1000 mcp && \
    chown -R mcp:mcp /app
USER mcp

# Environment variables (can be overridden at runtime)
ENV KATANA_BASE_URL="https://api.katanamrp.com/v1"

# Expose MCP server (stdio-based, no network port needed)
# The server uses stdio for communication with Claude Desktop

# Run the MCP server
ENTRYPOINT ["python", "-m", "katana_mcp"]
