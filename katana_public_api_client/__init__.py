"""A client library for accessing Katana Public API"""

__version__ = "0.3.2"

# Re-export generated modules for direct access
from .generated import api, models
from .generated import ApiClient, Configuration
from .katana_client import KatanaClient
from .log_setup import get_logger, setup_logging

# Backward compatibility aliases for the old openapi-python-client approach
# The old AuthenticatedClient is now replaced by the new KatanaClient approach
# but we provide aliases for backward compatibility
AuthenticatedClient = ApiClient  # For backward compatibility  
Client = ApiClient  # For backward compatibility

__all__ = (
    "ApiClient",
    "AuthenticatedClient",  # Backward compatibility
    "Client",  # Backward compatibility
    "Configuration", 
    "KatanaClient",
    "__version__",
    "api",
    "get_logger",
    "models", 
    "setup_logging",
)
