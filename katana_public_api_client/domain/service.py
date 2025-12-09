"""Domain model for Service entities.

This module provides a Pydantic model representing a Service (external service)
optimized for ETL, data processing, and business logic.

The domain model uses composition with the auto-generated Pydantic model from OpenAPI,
leveraging its `from_attrs()` conversion while adding business-specific methods.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal

from pydantic import Field

from .base import KatanaBaseModel

if TYPE_CHECKING:
    from ..models.service import Service as AttrsService
    from ..models_pydantic._generated.inventory import Service as GeneratedService


class KatanaService(KatanaBaseModel):
    """Domain model for a Service.

    A Service represents an external service that can be used as part of manufacturing
    operations or business processes. This is a Pydantic model optimized for:
    - ETL and data processing
    - Business logic
    - Data validation
    - JSON schema generation

    This model uses composition with the auto-generated Pydantic model,
    exposing a curated subset of fields with business methods.

    Example:
        ```python
        service = KatanaService(
            id=1,
            name="External Assembly Service",
            type="service",
            uom="pcs",
            category_name="Assembly",
            is_sellable=True,
        )

        # Business methods available
        print(service.get_display_name())  # "External Assembly Service"

        # ETL export
        csv_row = service.to_csv_row()
        schema = KatanaService.model_json_schema()
        ```
    """

    # ============ Core Fields (always present) ============

    id: int = Field(..., description="Unique service ID")
    name: str | None = Field(None, description="Service name")
    type_: Literal["service"] | None = Field(
        None, alias="type", description="Entity type"
    )

    # ============ Classification & Units ============

    uom: str | None = Field(None, description="Unit of measure (e.g., 'pcs', 'hours')")
    category_name: str | None = Field(None, description="Service category name")

    # ============ Capabilities ============

    is_sellable: bool | None = Field(None, description="Can be sold to customers")

    # ============ Additional Info ============

    additional_info: str | None = Field(None, description="Additional notes/info")
    custom_field_collection_id: int | None = Field(
        None, description="Custom field collection ID"
    )
    archived_at: datetime | None = Field(
        None, description="Timestamp when service was archived"
    )

    # ============ Nested Data ============

    variant_count: int = Field(
        0, ge=0, description="Number of variants for this service"
    )

    # ============ Factory Methods ============

    @classmethod
    def from_generated(cls, generated: GeneratedService) -> KatanaService:
        """Create a KatanaService from a generated Pydantic Service model.

        This method extracts the curated subset of fields from the generated model.

        Args:
            generated: The auto-generated Pydantic Service model.

        Returns:
            A new KatanaService instance with business methods.

        Example:
            ```python
            from katana_public_api_client.models_pydantic import Service

            # Convert from generated pydantic model
            generated = Service.from_attrs(attrs_service)
            domain = KatanaService.from_generated(generated)
            ```
        """
        # Count nested collections
        variant_count = len(generated.variants) if generated.variants else 0

        # Extract type value from enum if present
        type_value: Literal["service"] | None = None
        if generated.type is not None:
            type_value = (
                generated.type.value
                if hasattr(generated.type, "value")
                else generated.type
            )

        return cls(
            id=generated.id,
            name=generated.name,
            type=type_value,
            uom=generated.uom,
            category_name=generated.category_name,
            is_sellable=generated.is_sellable,
            additional_info=generated.additional_info,
            custom_field_collection_id=generated.custom_field_collection_id,
            archived_at=generated.archived_at,
            variant_count=variant_count,
            created_at=generated.created_at,
            updated_at=generated.updated_at,
            deleted_at=generated.deleted_at,
        )

    @classmethod
    def from_attrs(cls, attrs_service: AttrsService) -> KatanaService:
        """Create a KatanaService from an attrs Service model (API response).

        This method leverages the generated Pydantic model's `from_attrs()` method
        to handle UNSET sentinel conversion, then creates the domain model.

        Args:
            attrs_service: The attrs Service model from API response.

        Returns:
            A new KatanaService instance with business methods.

        Example:
            ```python
            from katana_public_api_client.api.service import get_service
            from katana_public_api_client.utils import unwrap

            response = await get_service.asyncio_detailed(client=client, id=123)
            attrs_service = unwrap(response)
            domain = KatanaService.from_attrs(attrs_service)
            ```
        """
        from ..models_pydantic._generated.inventory import Service as GeneratedService

        # Use generated model's from_attrs() to handle UNSET conversion
        generated = GeneratedService.from_attrs(attrs_service)
        return cls.from_generated(generated)

    # ============ Business Logic Methods ============

    def get_display_name(self) -> str:
        """Get formatted display name.

        Returns:
            Service name, or "Unnamed Service {id}" if no name

        Example:
            ```python
            service = KatanaService(id=1, name="Assembly Service")
            print(service.get_display_name())  # "Assembly Service"
            ```
        """
        return self.name or f"Unnamed Service {self.id}"

    def matches_search(self, query: str) -> bool:
        """Check if service matches search query.

        Searches across:
        - Service name
        - Category name

        Args:
            query: Search query string (case-insensitive)

        Returns:
            True if service matches query

        Example:
            ```python
            service = KatanaService(
                id=1, name="Assembly Service", category_name="Manufacturing"
            )
            service.matches_search("assembly")  # True
            service.matches_search("manufacturing")  # True
            service.matches_search("packaging")  # False
            ```
        """
        query_lower = query.lower()

        # Check name
        if self.name and query_lower in self.name.lower():
            return True

        # Check category
        return bool(self.category_name and query_lower in self.category_name.lower())

    def to_csv_row(self) -> dict[str, Any]:
        """Export as CSV-friendly row.

        Returns:
            Dictionary with flattened data suitable for CSV export

        Example:
            ```python
            service = KatanaService(id=1, name="Test Service", is_sellable=True)
            row = service.to_csv_row()
            # {
            #   "ID": 1,
            #   "Name": "Test Service",
            #   "Type": "service",
            #   "Category": "",
            #   ...
            # }
            ```
        """
        return {
            "ID": self.id,
            "Name": self.get_display_name(),
            "Type": self.type_ or "service",
            "Category": self.category_name or "",
            "UOM": self.uom or "",
            "Is Sellable": self.is_sellable or False,
            "Variant Count": self.variant_count,
            "Created At": self.created_at.isoformat() if self.created_at else "",
            "Updated At": self.updated_at.isoformat() if self.updated_at else "",
            "Archived At": self.archived_at.isoformat() if self.archived_at else "",
            "Deleted At": self.deleted_at.isoformat() if self.deleted_at else "",
        }


__all__ = ["KatanaService"]
