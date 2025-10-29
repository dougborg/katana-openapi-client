"""Domain model for Variant entities.

This module provides a Pydantic model representing a Variant (product or material SKU)
optimized for ETL, data processing, and business logic.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from .base import KatanaBaseModel


class KatanaVariant(KatanaBaseModel):
    """Domain model for a Product or Material Variant.

    A Variant represents a specific SKU with unique pricing, configuration,
    and inventory tracking. This is a Pydantic model optimized for:
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
        variant = KatanaVariant(
            id=123,
            sku="KNF-PRO-8PC",
            sales_price=299.99,
            purchase_price=150.00,
        )

        # Business methods available
        print(variant.get_display_name())  # "Professional Knife Set / 8-Piece"

        # ETL export
        csv_row = variant.to_csv_row()
        schema = KatanaVariant.model_json_schema()
        ```
    """

    # ============ Core Fields (always present) ============

    id: int = Field(..., description="Unique variant ID")
    sku: str = Field(..., description="Stock Keeping Unit", min_length=1)

    # ============ Pricing Fields ============

    sales_price: float | None = Field(None, ge=0, description="Sales price")
    purchase_price: float | None = Field(None, ge=0, description="Purchase cost")

    # ============ Relationship Fields ============

    product_id: int | None = Field(
        None, description="ID of parent product (if product variant)"
    )
    material_id: int | None = Field(
        None, description="ID of parent material (if material variant)"
    )
    product_or_material_name: str | None = Field(
        None, description="Name of parent product or material"
    )

    # ============ Classification ============

    type_: Literal["product", "material"] | None = Field(
        None, alias="type", description="Variant type"
    )

    # ============ Inventory & Barcode Fields ============

    internal_barcode: str | None = Field(None, description="Internal barcode")
    registered_barcode: str | None = Field(None, description="Registered/UPC barcode")
    supplier_item_codes: list[str] = Field(
        default_factory=list, description="Supplier item codes"
    )

    # ============ Ordering Fields ============

    lead_time: int | None = Field(
        None, ge=0, description="Lead time in days to fulfill order"
    )
    minimum_order_quantity: float | None = Field(
        None, ge=0, description="Minimum order quantity"
    )

    # ============ Configuration & Custom Data ============

    config_attributes: list[dict[str, str]] = Field(
        default_factory=list,
        description="Configuration attributes (e.g., size, color)",
    )
    custom_fields: list[dict[str, str]] = Field(
        default_factory=list, description="Custom field values"
    )

    # ============ Business Logic Methods ============

    def get_display_name(self) -> str:
        """Get formatted display name matching Katana UI format.

        Format: "{Product/Material Name} / {Config Value 1} / {Config Value 2} / ..."

        Returns:
            Formatted variant name, or SKU if no name available

        Example:
            ```python
            variant = KatanaVariant(
                id=1,
                sku="KNF-001",
                product_or_material_name="Kitchen Knife",
                config_attributes=[
                    {"config_name": "Size", "config_value": "8-inch"},
                    {"config_name": "Color", "config_value": "Black"},
                ],
            )
            print(variant.get_display_name())
            # "Kitchen Knife / 8-inch / Black"
            ```
        """
        if not self.product_or_material_name:
            return self.sku

        parts = [self.product_or_material_name]

        # Append config attribute values
        for attr in self.config_attributes:
            if value := attr.get("config_value"):
                parts.append(value)

        return " / ".join(parts)

    def matches_search(self, query: str) -> bool:
        """Check if variant matches search query.

        Searches across:
        - SKU
        - Product/material name
        - Supplier item codes
        - Config attribute values

        Args:
            query: Search query string (case-insensitive)

        Returns:
            True if variant matches query

        Example:
            ```python
            variant = KatanaVariant(id=1, sku="FOX-FORK-160", ...)
            variant.matches_search("fox")      # True
            variant.matches_search("fork")     # True
            variant.matches_search("160")      # True
            variant.matches_search("shimano")  # False
            ```
        """
        query_lower = query.lower()

        # Check SKU
        if query_lower in self.sku.lower():
            return True

        # Check product/material name
        if (
            self.product_or_material_name
            and query_lower in self.product_or_material_name.lower()
        ):
            return True

        # Check supplier codes
        if any(query_lower in code.lower() for code in self.supplier_item_codes):
            return True

        # Check config attribute values
        for attr in self.config_attributes:
            if (value := attr.get("config_value")) and query_lower in value.lower():
                return True

        return False

    def to_csv_row(self) -> dict[str, Any]:
        """Export as CSV-friendly row.

        Returns:
            Dictionary with flattened data suitable for CSV export

        Example:
            ```python
            variant = KatanaVariant(id=1, sku="TEST", sales_price=99.99)
            row = variant.to_csv_row()
            # {
            #   "ID": 1,
            #   "SKU": "TEST",
            #   "Name": "TEST",
            #   "Sales Price": 99.99,
            #   ...
            # }
            ```
        """

        return {
            "ID": self.id,
            "SKU": self.sku,
            "Name": self.get_display_name(),
            "Type": self.type_ or "unknown",
            "Sales Price": self.sales_price or 0.0,
            "Purchase Price": self.purchase_price or 0.0,
            "Lead Time (days)": self.lead_time or 0,
            "Min Order Qty": self.minimum_order_quantity or 0,
            "Internal Barcode": self.internal_barcode or "",
            "Registered Barcode": self.registered_barcode or "",
            "Created At": self.created_at.isoformat() if self.created_at else "",
            "Updated At": self.updated_at.isoformat() if self.updated_at else "",
        }

    def get_custom_field(self, field_name: str) -> str | None:
        """Get value of a custom field by name.

        Args:
            field_name: Name of the custom field

        Returns:
            Field value or None if not found

        Example:
            ```python
            variant = KatanaVariant(
                id=1,
                sku="TEST",
                custom_fields=[
                    {"field_name": "Warranty", "field_value": "5 years"}
                ],
            )
            print(variant.get_custom_field("Warranty"))  # "5 years"
            print(variant.get_custom_field("Missing"))  # None
            ```
        """
        for field in self.custom_fields:
            if field.get("field_name") == field_name:
                return field.get("field_value")
        return None

    def get_config_value(self, config_name: str) -> str | None:
        """Get value of a configuration attribute by name.

        Args:
            config_name: Name of the configuration attribute

        Returns:
            Config value or None if not found

        Example:
            ```python
            variant = KatanaVariant(
                id=1,
                sku="TEST",
                config_attributes=[
                    {"config_name": "Size", "config_value": "Large"}
                ],
            )
            print(variant.get_config_value("Size"))  # "Large"
            print(variant.get_config_value("Color"))  # None
            ```
        """
        for attr in self.config_attributes:
            if attr.get("config_name") == config_name:
                return attr.get("config_value")
        return None


__all__ = ["KatanaVariant"]
