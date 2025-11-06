"""Katana Public API Client - Python client for Katana Manufacturing ERP."""

__version__ = "0.30.0"

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
    # Exceptions
    "APIError",
    # Client classes
    "AuthenticatedClient",
    "AuthenticationError",
    "Client",
    "KatanaClient",
    "RateLimitError",
    "ServerError",
    "ValidationError",
    # Utility functions
    "get_error_message",
    "get_variant_display_name",
    "handle_response",
    "is_error",
    "is_success",
    "unwrap",
    "unwrap_data",
]
