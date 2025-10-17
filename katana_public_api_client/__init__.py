"""Katana Public API Client - Python client for Katana Manufacturing ERP."""

from .client import AuthenticatedClient, Client
from .katana_client import KatanaClient
from .utils import (
    APIError,
    AuthenticationError,
    RateLimitError,
    ServerError,
    ValidationError,
    get_error_message,
    handle_response,
    is_error,
    is_success,
    unwrap,
    unwrap_data,
)

__all__ = [
    # Exceptions
    "APIError",
    "AuthenticatedClient",
    "AuthenticationError",
    "Client",
    "KatanaClient",
    "RateLimitError",
    "ServerError",
    "ValidationError",
    "get_error_message",
    "handle_response",
    "is_error",
    "is_success",
    # Utilities
    "unwrap",
    "unwrap_data",
]
