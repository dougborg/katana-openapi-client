"""Domain model for Variant entities.

This module provides a Pydantic model representing a Variant (product or material SKU)
optimized for ETL, data processing, and business logic.

The domain model uses composition with the auto-generated Pydantic model from OpenAPI,
leveraging its `from_attrs()` conversion while adding business-specific methods.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from pydantic import Field

from .base import KatanaBaseModel

if TYPE_CHECKING:
    from ..models.variant import Variant as AttrsVariant
    from ..models_pydantic._generated.inventory import Variant as GeneratedVariant


class KatanaVariant(KatanaBaseModel):
    """Domain model for a Product or Material Variant.

    A Variant represents a specific SKU with unique pricing, configuration,
    and inventory tracking. This is a Pydantic model optimized for:
    - ETL and data processing
    - Business logic
    - Data validation
    - JSON schema generation

    This model uses composition with the auto-generated Pydantic model,
    exposing a curated subset of fields with business methods.

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
    sku: str = Field(..., description="Stock Keeping Unit")

    # ============ Pricing Fields ============

    sales_price: float | None = Field(
        None, ge=0, le=100_000_000_000, description="Sales price"
    )
    purchase_price: float | None = Field(
        None, ge=0, le=100_000_000_000, description="Purchase cost"
    )

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

    # Note: OpenAPI spec only allows "product" or "material" for variants
    type_: Literal["product", "material"] | None = Field(
        None, alias="type", description="Variant type (product or material)"
    )

    # ============ Inventory & Barcode Fields ============

    internal_barcode: str | None = Field(None, description="Internal barcode")
    registered_barcode: str | None = Field(None, description="Registered/UPC barcode")
    supplier_item_codes: list[str] = Field(
        default_factory=list, description="Supplier item codes"
    )

    # ============ Ordering Fields ============

    lead_time: int | None = Field(
        None, ge=0, le=999, description="Lead time in days to fulfill order"
    )
    minimum_order_quantity: float | None = Field(
        None, ge=0, le=999_999_999, description="Minimum order quantity"
    )

    # ============ Configuration & Custom Data ============

    config_attributes: list[dict[str, str]] = Field(
        default_factory=list,
        description="Configuration attributes (e.g., size, color)",
    )
    custom_fields: list[dict[str, str]] = Field(
        default_factory=list, description="Custom field values"
    )

    # ============ Factory Methods ============

    @classmethod
    def from_generated(
        cls,
        generated: GeneratedVariant,
        product_or_material_name: str | None = None,
    ) -> KatanaVariant:
        """Create a KatanaVariant from a generated Pydantic Variant model.

        This method extracts the curated subset of fields from the generated model
        and converts nested objects (config_attributes, custom_fields) to simple dicts.

        Args:
            generated: The auto-generated Pydantic Variant model.
            product_or_material_name: Optional name of parent product/material
                (must be provided separately as it comes from extend query).

        Returns:
            A new KatanaVariant instance with business methods.

        Example:
            ```python
            from katana_public_api_client.models_pydantic import Variant

            # Convert from generated pydantic model
            generated = Variant.from_attrs(attrs_variant)
            domain = KatanaVariant.from_generated(generated)
            ```
        """
        # Convert config attributes to simple dicts
        config_attrs: list[dict[str, str]] = []
        if generated.config_attributes:
            for attr in generated.config_attributes:
                config_attrs.append(
                    {
                        "config_name": getattr(attr, "config_name", "") or "",
                        "config_value": getattr(attr, "config_value", "") or "",
                    }
                )

        # Convert custom fields to simple dicts
        custom: list[dict[str, str]] = []
        if generated.custom_fields:
            for field in generated.custom_fields:
                custom.append(
                    {
                        "field_name": getattr(field, "field_name", "") or "",
                        "field_value": getattr(field, "field_value", "") or "",
                    }
                )

        # Extract type value from enum if present
        # Only "product" or "material" are valid per OpenAPI spec
        type_value: Literal["product", "material"] | None = None
        if generated.type is not None:
            raw_type = (
                generated.type.value
                if hasattr(generated.type, "value")
                else generated.type
            )
            if raw_type in ("product", "material"):
                type_value = raw_type

        return cls(
            id=generated.id,
            sku=generated.sku,
            sales_price=generated.sales_price,
            purchase_price=generated.purchase_price,
            product_id=generated.product_id,
            material_id=generated.material_id,
            product_or_material_name=product_or_material_name,
            type=type_value,
            internal_barcode=generated.internal_barcode,
            registered_barcode=generated.registered_barcode,
            supplier_item_codes=generated.supplier_item_codes or [],
            lead_time=generated.lead_time,
            minimum_order_quantity=generated.minimum_order_quantity,
            config_attributes=config_attrs,
            custom_fields=custom,
            created_at=generated.created_at,
            updated_at=generated.updated_at,
            deleted_at=generated.deleted_at,
        )

    @classmethod
    def from_attrs(
        cls,
        attrs_variant: AttrsVariant,
        product_or_material_name: str | None = None,
    ) -> KatanaVariant:
        """Create a KatanaVariant from an attrs Variant model (API response).

        This method leverages the generated Pydantic model's `from_attrs()` method
        to handle UNSET sentinel conversion, then creates the domain model.

        Args:
            attrs_variant: The attrs Variant model from API response.
            product_or_material_name: Optional name of parent product/material
                (must be provided separately as it comes from extend query).

        Returns:
            A new KatanaVariant instance with business methods.

        Example:
            ```python
            from katana_public_api_client.api.variant import get_variant
            from katana_public_api_client.utils import unwrap

            response = await get_variant.asyncio_detailed(client=client, id=123)
            attrs_variant = unwrap(response)
            domain = KatanaVariant.from_attrs(attrs_variant)
            ```
        """
        from ..models_pydantic._generated.inventory import Variant as GeneratedVariant

        # Use generated model's from_attrs() to handle UNSET conversion
        generated = GeneratedVariant.from_attrs(attrs_variant)

        # Extract product_or_material_name from extended data if not provided
        if product_or_material_name is None and hasattr(
            attrs_variant, "product_or_material"
        ):
            from ..client_types import UNSET

            pom = attrs_variant.product_or_material
            if pom is not UNSET and pom is not None and hasattr(pom, "name"):
                name = pom.name
                if name is not UNSET and isinstance(name, str):
                    product_or_material_name = name

        return cls.from_generated(generated, product_or_material_name)

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
