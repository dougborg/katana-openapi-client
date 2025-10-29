"""Domain model for Material entities.

This module provides a Pydantic model representing a Material (raw material or component)
optimized for ETL, data processing, and business logic.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from .base import KatanaBaseModel


class KatanaMaterial(KatanaBaseModel):
    """Domain model for a Material.

    A Material represents raw materials and components used in manufacturing, including
    inventory tracking, supplier information, and batch management. This is a Pydantic
    model optimized for:
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
        material = KatanaMaterial(
            id=3201,
            name="Stainless Steel Sheet 304",
            type="material",
            uom="m²",
            category_name="Raw Materials",
            is_sellable=False,
            batch_tracked=True,
        )

        # Business methods available
        print(material.get_display_name())  # "Stainless Steel Sheet 304"

        # ETL export
        csv_row = material.to_csv_row()
        schema = KatanaMaterial.model_json_schema()
        ```
    """

    # ============ Core Fields (always present) ============

    id: int = Field(..., description="Unique material ID")
    name: str = Field(..., description="Material name", min_length=1)
    type_: Literal["material"] = Field(
        "material", alias="type", description="Entity type"
    )

    # ============ Classification & Units ============

    uom: str | None = Field(None, description="Unit of measure (e.g., 'kg', 'm²')")
    category_name: str | None = Field(None, description="Material category name")

    # ============ Capabilities ============

    is_sellable: bool | None = Field(
        None, description="Can be sold to customers (usually False for materials)"
    )

    # ============ Tracking Features ============

    batch_tracked: bool | None = Field(None, description="Track by batch/lot numbers")

    # ============ Supplier & Ordering ============

    default_supplier_id: int | None = Field(None, description="Default supplier ID")

    # ============ Purchase Unit Conversion ============

    purchase_uom: str | None = Field(
        None, description="Purchase unit of measure (if different from base UOM)"
    )
    purchase_uom_conversion_rate: float | None = Field(
        None, ge=0, description="Conversion rate from purchase UOM to base UOM"
    )

    # ============ Additional Info ============

    additional_info: str | None = Field(None, description="Additional notes/info")
    custom_field_collection_id: int | None = Field(
        None, description="Custom field collection ID"
    )
    archived_at: str | None = Field(
        None, description="Timestamp when material was archived (ISO string)"
    )

    # ============ Nested Data ============

    variant_count: int = Field(
        0, ge=0, description="Number of variants for this material"
    )
    config_count: int = Field(0, ge=0, description="Number of configuration attributes")

    # ============ Business Logic Methods ============

    def get_display_name(self) -> str:
        """Get formatted display name.

        Returns:
            Material name, or "Unnamed Material {id}" if no name

        Example:
            ```python
            material = KatanaMaterial(id=3201, name="Steel Sheet")
            print(material.get_display_name())  # "Steel Sheet"
            ```
        """
        return self.name or f"Unnamed Material {self.id}"

    def matches_search(self, query: str) -> bool:
        """Check if material matches search query.

        Searches across:
        - Material name
        - Category name

        Args:
            query: Search query string (case-insensitive)

        Returns:
            True if material matches query

        Example:
            ```python
            material = KatanaMaterial(
                id=3201, name="Stainless Steel Sheet", category_name="Raw Materials"
            )
            material.matches_search("steel")  # True
            material.matches_search("raw")  # True
            material.matches_search("aluminum")  # False
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
            material = KatanaMaterial(
                id=3201, name="Test Material", is_sellable=False
            )
            row = material.to_csv_row()
            # {
            #   "ID": 3201,
            #   "Name": "Test Material",
            #   "Type": "material",
            #   "Category": "",
            #   ...
            # }
            ```
        """
        return {
            "ID": self.id,
            "Name": self.get_display_name(),
            "Type": self.type_,
            "Category": self.category_name or "",
            "UOM": self.uom or "",
            "Is Sellable": self.is_sellable or False,
            "Batch Tracked": self.batch_tracked or False,
            "Variant Count": self.variant_count,
            "Config Count": self.config_count,
            "Created At": self.created_at.isoformat() if self.created_at else "",
            "Updated At": self.updated_at.isoformat() if self.updated_at else "",
            "Archived At": self.archived_at or "",
        }


__all__ = ["KatanaMaterial"]
