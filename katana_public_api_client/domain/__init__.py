"""Pydantic domain models for Katana entities.

This package provides clean, ergonomic Pydantic models representing business
entities from the Katana Manufacturing ERP system.

Domain models are separate from the generated API request/response models and
are optimized for:
- ETL and data processing
- Business logic
- Data validation
- JSON schema generation

Example:
    ```python
    from katana_public_api_client import KatanaClient
    from katana_public_api_client.domain import KatanaVariant

    async with KatanaClient() as client:
        # Helpers return domain models
        variants = await client.variants.search("fox fork", limit=10)

        # Use business methods
        for v in variants:
            print(f"{v.get_display_name()}: ${v.sales_price}")

        # Easy ETL export
        csv_rows = [v.to_csv_row() for v in variants]

        # JSON schema generation
        schema = KatanaVariant.model_json_schema()
    ```
"""

from .base import KatanaBaseModel
from .converters import unwrap_unset, variant_to_katana, variants_to_katana
from .variant import KatanaVariant

__all__ = [
    "KatanaBaseModel",
    "KatanaVariant",
    "unwrap_unset",
    "variant_to_katana",
    "variants_to_katana",
]
