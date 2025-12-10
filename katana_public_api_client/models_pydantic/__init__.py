"""Pydantic v2 models for Katana API.

This module provides Pydantic v2 models that mirror the attrs models
in the main `models/` package. These models offer:

- **Strong validation**: Pydantic's validation ensures data integrity
- **Immutability**: All models are frozen to prevent accidental modification
- **Serialization**: Easy conversion to/from JSON and dictionaries
- **IDE support**: Full type hints and autocomplete

## Usage

### Converting from API Responses

```python
from katana_public_api_client import KatanaClient
from katana_public_api_client.api.product import get_all_products
from katana_public_api_client.models_pydantic import Product
from katana_public_api_client.models_pydantic.converters import (
    convert_response,
)

async with KatanaClient() as client:
    response = await get_all_products.asyncio_detailed(client=client)
    products: list[Product] = convert_response(response, Product)

    for product in products:
        print(f"{product.name}: {product.id}")
```

### Converting Individual Objects

```python
from katana_public_api_client.models_pydantic import Product
from katana_public_api_client.models_pydantic.converters import (
    to_pydantic,
    to_attrs,
)

# Convert attrs -> pydantic
pydantic_product = Product.from_attrs(attrs_product)

# Or use the convenience function
pydantic_product = to_pydantic(attrs_product)

# Convert back to attrs for API calls
attrs_product = pydantic_product.to_attrs()
```

## Model Layers

This package contains three distinct model layers:

1. **`models/`** (attrs): Auto-generated from OpenAPI, used by API transport
2. **`models_pydantic/`** (pydantic): Auto-generated from OpenAPI, user-facing
3. **`domain/`** (hand-written): Custom business logic models (e.g., ItemSearchResult)

The Pydantic models here are designed for user-facing operations while the attrs
models handle API communication internally.
"""

# Import generated models (populated by generation script)
# This will be updated by the generate_pydantic_models.py script
import logging

from ._base import KatanaPydanticBase
from ._registry import (
    get_attrs_class,
    get_attrs_class_by_name,
    get_pydantic_class,
    get_pydantic_class_by_name,
    get_registration_stats,
    is_registered,
    list_registered_models,
    register,
)

_logger = logging.getLogger(__name__)

# Try to import generated models
try:
    from ._generated import *  # noqa: F403

    _GENERATED_MODELS_AVAILABLE = True
except ImportError as e:
    # Generated models not yet created - this is expected before running
    # the generation script for the first time
    _GENERATED_MODELS_AVAILABLE = False
    _logger.debug(
        "Pydantic models not yet generated. Run 'uv run poe generate-pydantic' "
        "to generate them. Import error: %s",
        e,
    )

# Import auto-registration (populated by generation script)
try:
    from ._auto_registry import register_all_models as _register_all

    _register_all()
    _REGISTRY_AVAILABLE = True
except ImportError as e:
    # Auto-registry not yet created - this is expected before generation
    _REGISTRY_AVAILABLE = False
    _logger.debug(
        "Auto-registry not yet generated. Run 'uv run poe generate-pydantic' "
        "to generate it. Import error: %s",
        e,
    )

__all__ = [
    # Base class
    "KatanaPydanticBase",
    "get_attrs_class",
    "get_attrs_class_by_name",
    "get_pydantic_class",
    "get_pydantic_class_by_name",
    "get_registration_stats",
    "is_registered",
    "list_registered_models",
    # Registry functions
    "register",
]
