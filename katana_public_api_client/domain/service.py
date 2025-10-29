"""Domain model for Service entities.

This module provides a Pydantic model representing a Service (external service)
optimized for ETL, data processing, and business logic.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from .base import KatanaBaseModel


class KatanaService(KatanaBaseModel):
    """Domain model for a Service.

    A Service represents an external service that can be used as part of manufacturing
    operations or business processes. This is a Pydantic model optimized for:
    - ETL and data processing
    - Business logic
    - Data validation
    - JSON schema generation

    Unlike the generated attrs model, this model:
    - Has no Unset sentinel values
    - Provides ETL-friendly methods
    - Is immutable by default
    - Clean Optional types

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
    archived_at: str | None = Field(
        None, description="Timestamp when service was archived (ISO string)"
    )

    # ============ Nested Data ============

    variant_count: int = Field(
        0, ge=0, description="Number of variants for this service"
    )

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
            "Archived At": self.archived_at or "",
            "Deleted At": self.deleted_at or "",
        }


__all__ = ["KatanaService"]
