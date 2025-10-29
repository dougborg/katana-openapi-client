"""Domain model for Product entities.

This module provides a Pydantic model representing a Product (finished good or component)
optimized for ETL, data processing, and business logic.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from .base import KatanaBaseModel


class KatanaProduct(KatanaBaseModel):
    """Domain model for a Product.

    A Product represents a finished good or component that can be sold, manufactured,
    or purchased, with support for variants and configurations. This is a Pydantic model
    optimized for:
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
        product = KatanaProduct(
            id=1,
            name="Standard-hilt lightsaber",
            type="product",
            uom="pcs",
            category_name="lightsaber",
            is_sellable=True,
            is_producible=True,
            is_purchasable=True,
        )

        # Business methods available
        print(product.get_display_name())  # "Standard-hilt lightsaber"

        # ETL export
        csv_row = product.to_csv_row()
        schema = KatanaProduct.model_json_schema()
        ```
    """

    # ============ Core Fields (always present) ============

    id: int = Field(..., description="Unique product ID")
    name: str = Field(..., description="Product name", min_length=1)
    type_: Literal["product"] = Field(
        "product", alias="type", description="Entity type"
    )

    # ============ Classification & Units ============

    uom: str | None = Field(None, description="Unit of measure (e.g., 'pcs', 'kg')")
    category_name: str | None = Field(None, description="Product category name")

    # ============ Capabilities ============

    is_sellable: bool | None = Field(None, description="Can be sold to customers")
    is_producible: bool | None = Field(None, description="Can be manufactured in-house")
    is_purchasable: bool | None = Field(
        None, description="Can be purchased from suppliers"
    )
    is_auto_assembly: bool | None = Field(
        None, description="Automatically assemble when components available"
    )

    # ============ Tracking Features ============

    batch_tracked: bool | None = Field(None, description="Track by batch/lot numbers")
    serial_tracked: bool | None = Field(None, description="Track by serial numbers")
    operations_in_sequence: bool | None = Field(
        None, description="Manufacturing operations must be done in sequence"
    )

    # ============ Supplier & Ordering ============

    default_supplier_id: int | None = Field(None, description="Default supplier ID")
    lead_time: int | None = Field(
        None, ge=0, description="Lead time in days to fulfill order"
    )
    minimum_order_quantity: float | None = Field(
        None, ge=0, description="Minimum order quantity"
    )

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
        None, description="Timestamp when product was archived (ISO string)"
    )

    # ============ Nested Data ============

    variant_count: int = Field(
        0, ge=0, description="Number of variants for this product"
    )
    config_count: int = Field(0, ge=0, description="Number of configuration attributes")

    # ============ Business Logic Methods ============

    def get_display_name(self) -> str:
        """Get formatted display name.

        Returns:
            Product name, or "Unnamed Product {id}" if no name

        Example:
            ```python
            product = KatanaProduct(id=1, name="Kitchen Knife")
            print(product.get_display_name())  # "Kitchen Knife"
            ```
        """
        return self.name or f"Unnamed Product {self.id}"

    def matches_search(self, query: str) -> bool:
        """Check if product matches search query.

        Searches across:
        - Product name
        - Category name

        Args:
            query: Search query string (case-insensitive)

        Returns:
            True if product matches query

        Example:
            ```python
            product = KatanaProduct(
                id=1, name="Kitchen Knife", category_name="Cutlery"
            )
            product.matches_search("knife")  # True
            product.matches_search("cutlery")  # True
            product.matches_search("fork")  # False
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
            product = KatanaProduct(id=1, name="Test Product", is_sellable=True)
            row = product.to_csv_row()
            # {
            #   "ID": 1,
            #   "Name": "Test Product",
            #   "Type": "product",
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
            "Is Producible": self.is_producible or False,
            "Is Purchasable": self.is_purchasable or False,
            "Batch Tracked": self.batch_tracked or False,
            "Serial Tracked": self.serial_tracked or False,
            "Lead Time (days)": self.lead_time or 0,
            "Min Order Qty": self.minimum_order_quantity or 0,
            "Variant Count": self.variant_count,
            "Config Count": self.config_count,
            "Created At": self.created_at.isoformat() if self.created_at else "",
            "Updated At": self.updated_at.isoformat() if self.updated_at else "",
            "Archived At": self.archived_at or "",
        }


__all__ = ["KatanaProduct"]
