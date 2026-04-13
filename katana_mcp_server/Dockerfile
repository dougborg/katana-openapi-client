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

# Set working directory
WORKDIR /app

# Install uv for fast dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files and source code
COPY pyproject.toml /app/
COPY src/ /app/src/
COPY README.md /app/

# Install package (--no-sources skips workspace reference, resolves from PyPI)
RUN uv pip install --system --no-cache --no-sources .

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
