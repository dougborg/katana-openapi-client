"""Katana Public API Client - Python client for Katana Manufacturing ERP."""

from ._logging import Logger
from .client import AuthenticatedClient, Client
from .katana_client import KatanaClient
from .utils import (
    APIError,
    AuthenticationError,
    RateLimitError,
    ServerError,
    ValidationError,
    get_error_message,
    get_variant_display_name,
    handle_response,
    is_error,
    is_success,
    unwrap,
    unwrap_data,
)

__all__ = [
    "APIError",
    "AuthenticatedClient",
    "AuthenticationError",
    "Client",
    "KatanaClient",
    "Logger",
    "RateLimitError",
    "ServerError",
    "ValidationError",
    "get_error_message",
    "get_variant_display_name",
    "handle_response",
    "is_error",
    "is_success",
    "unwrap",
    "unwrap_data",
]
