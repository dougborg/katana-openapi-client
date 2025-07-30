"""A client library for accessing Katana Public API"""

__version__ = "0.2.2"

# Re-export generated modules for backward compatibility
from .generated import api, models
from .generated.client import AuthenticatedClient, Client
from .katana_client import KatanaClient
from .log_setup import get_logger, setup_logging

__all__ = (
    "AuthenticatedClient",
    "Client",
    "KatanaClient",
    "__version__",
    "api",
    "get_logger",
    "models",
    "setup_logging",
)
