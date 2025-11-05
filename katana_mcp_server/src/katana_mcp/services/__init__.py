"""Services layer for dependency injection in MCP tools.

This module provides clean dependency injection patterns for accessing
the KatanaClient and other services from MCP tool contexts.
"""

from .dependencies import Services, get_services

__all__ = [
    "Services",
    "get_services",
]
