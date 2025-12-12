"""Entry point for running Katana MCP Server as a module.

Usage:
    python -m katana_mcp [--transport stdio|sse|http] [--host HOST] [--port PORT]

Examples:
    # Run with stdio (default, for Claude Desktop/CLI)
    python -m katana_mcp

    # Run with SSE transport for development
    python -m katana_mcp --transport sse --port 8765

    # Run with HTTP transport
    python -m katana_mcp --transport http --port 8765
"""

import argparse

from katana_mcp.server import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Katana MCP Server - Manufacturing ERP tools for AI assistants"
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "http"],
        default="stdio",
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to for HTTP/SSE (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port to bind to for HTTP/SSE (default: 8765)",
    )
    args = parser.parse_args()
    main(transport=args.transport, host=args.host, port=args.port)
