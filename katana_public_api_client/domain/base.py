"""Base domain model for Katana entities.

This module provides the foundation for Pydantic domain models that represent
business entities from the Katana Manufacturing ERP system.

Domain models are separate from the generated API request/response models and
are optimized for:
- ETL and data processing
- Business logic
- Data validation
- JSON schema generation
- Clean, ergonomic APIs
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field


class KatanaBaseModel(BaseModel):
    """Base class for all Pydantic domain models.

    Provides:
    - Immutability by default (frozen=True)
    - Automatic validation
    - JSON schema generation
    - Easy serialization for ETL
    - Common timestamp fields

    Example:
        ```python
        class ProductDomain(KatanaBaseModel):
            id: int
            name: str
            sku: str

            @computed_field
            @property
            def display_name(self) -> str:
                return f"{self.name} ({self.sku})"
        ```
    """

    model_config = ConfigDict(
        frozen=True,  # Immutable by default
        validate_assignment=True,  # Validate on updates (if unfrozen)
        arbitrary_types_allowed=True,  # Allow datetime, etc.
        str_strip_whitespace=True,  # Clean string inputs
        json_schema_extra={
            "source": "Katana Manufacturing ERP",
            "version": "v1",
        },
    )

    # Metadata about the source model
    _source_model: ClassVar[str] = "attrs"
    _api_version: ClassVar[str] = "v1"

    # Common timestamp fields (most Katana entities have these)
    created_at: datetime | None = Field(
        None, description="Timestamp when entity was created"
    )
    updated_at: datetime | None = Field(
        None, description="Timestamp when entity was last updated"
    )
    deleted_at: datetime | None = Field(
        None, description="Timestamp when entity was soft-deleted (if applicable)"
    )

    def model_dump_for_etl(self) -> dict[str, Any]:
        """Export to ETL-friendly format.

        Removes None values and uses field aliases for cleaner output.

        Returns:
            Dictionary with all non-None fields

        Example:
            ```python
            variant = KatanaVariant(id=123, sku="ABC-001", sales_price=99.99)
            data = variant.model_dump_for_etl()
            # {"id": 123, "sku": "ABC-001", "sales_price": 99.99}
            ```
        """
        return self.model_dump(exclude_none=True, by_alias=True)

    def to_warehouse_json(self) -> str:
        """Export as JSON for data warehouse.

        Returns:
            JSON string with all non-None fields

        Example:
            ```python
            variant = KatanaVariant(id=123, sku="ABC-001")
            json_str = variant.to_warehouse_json()
            # '{"id":123,"sku":"ABC-001"}'
            ```
        """
        return self.model_dump_json(exclude_none=True, by_alias=True)

    def to_dict_with_computed(self) -> dict[str, Any]:
        """Export including computed fields.

        Unlike model_dump(), this includes @computed_field properties.

        Returns:
            Dictionary with all fields including computed ones
        """
        # Pydantic v2 automatically includes computed fields in model_dump
        return self.model_dump(mode="python", exclude_none=True)


__all__ = ["KatanaBaseModel"]
