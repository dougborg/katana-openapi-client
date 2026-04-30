"""FastMCP boundary middlewares for the Katana MCP server.

Custom middlewares plugged into the FastMCP server's call-tool pipeline. Layer
generic harness-compatibility fixes here rather than scattering them across
per-tool model annotations.
"""

from __future__ import annotations

from katana_mcp.middleware.json_string_coercion import JsonStringCoercionMiddleware

__all__ = ["JsonStringCoercionMiddleware"]
