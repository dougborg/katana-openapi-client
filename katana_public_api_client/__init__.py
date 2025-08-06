"""A client library for accessing Katana Public API"""

__version__ = "0.3.2"

# Re-export generated modules for direct access
from .generated import api, models
from .generated.api_client import ApiClient
from .generated.configuration import Configuration
from .katana_client import KatanaClient, ResilientAsyncTransport
from .log_setup import get_logger, setup_logging

# Remove all old openapi-python-client backward compatibility
# The new KatanaClient is the only supported interface
__all__ = (
    "ApiClient",
    "Configuration",
    "KatanaClient",
    "ResilientAsyncTransport",
    "__version__",
    "api",
    "get_logger",
    "models",
    "setup_logging",
)
