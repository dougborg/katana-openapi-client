# Katana MCP Server Docker Image
# Provides an isolated, secure environment for running the Katana Manufacturing ERP MCP server
# Compatible with Docker MCP Catalog and Toolkit
#
# Supports multiple transport modes via MCP_TRANSPORT env var:
#   - streamable-http (default): HTTP transport for Claude.ai co-work and remote clients
#   - stdio: Standard I/O for Claude Desktop and Claude Code
#   - sse: Server-Sent Events for Cursor IDE

FROM python:3.14-slim

# Metadata
LABEL org.opencontainers.image.title="Katana MCP Server"
LABEL org.opencontainers.image.description="Model Context Protocol server for Katana Manufacturing ERP"
LABEL org.opencontainers.image.version="0.1.0"
LABEL org.opencontainers.image.vendor="Doug Borg"
LABEL org.opencontainers.image.source="https://github.com/dougborg/katana-openapi-client"
LABEL org.opencontainers.image.licenses="MIT"

# Install uv for fast dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy the client source from the same release commit. Its wheel includes the
# OpenAPI document through Hatch's force-include configuration.
WORKDIR /client
COPY pyproject.toml README.md ./
COPY katana_public_api_client/ ./katana_public_api_client/
COPY docs/katana-openapi.yaml ./docs/katana-openapi.yaml

# Copy the MCP package.
WORKDIR /app
COPY katana_mcp_server/pyproject.toml ./pyproject.toml
COPY katana_mcp_server/README.md ./README.md
COPY katana_mcp_server/src/ ./src/

# Install both local packages together. --no-sources ignores the development
# workspace mapping while the direct /client requirement prevents a PyPI race.
RUN uv pip install --system --no-cache --no-sources /client /app

# Create non-root user for security
RUN useradd -m -u 1000 mcp && \
    chown -R mcp:mcp /app
USER mcp

# Environment variables (can be overridden at runtime)
ENV KATANA_BASE_URL="https://api.katanamrp.com/v1"
# Expose HTTP port (used by streamable-http, http, and sse transports)
EXPOSE 8765

# Run the MCP server with configurable transport
ENTRYPOINT ["python", "-m", "katana_mcp"]
CMD ["--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8765"]
