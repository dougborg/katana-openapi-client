"""A client library for accessing Katana Public API"""

__version__ = "0.3.2"

# Re-export generated modules for direct access
from .generated import api, models
from .generated import ApiClient, Configuration
from .katana_client import KatanaClient
from .log_setup import get_logger, setup_logging

__all__ = (
    "ApiClient",
    "Configuration", 
    "KatanaClient",
    "__version__",
    "api",
    "get_logger",
    "models", 
    "setup_logging",
)
