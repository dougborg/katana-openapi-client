"""Domain model for Product entities.

This module provides a Pydantic model representing a Product (finished good or component)
optimized for ETL, data processing, and business logic.

The domain model uses composition with the auto-generated Pydantic model from OpenAPI,
leveraging its `from_attrs()` conversion while adding business-specific methods.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from pydantic import AwareDatetime, Field

from .base import KatanaBaseModel

if TYPE_CHECKING:
    from ..models.product import Product as AttrsProduct
    from ..models_pydantic._generated.inventory import Product as GeneratedProduct


class KatanaProduct(KatanaBaseModel):
    """Domain model for a Product.

    A Product represents a finished good or component that can be sold, manufactured,
    or purchased, with support for variants and configurations. This is a Pydantic model
    optimized for:
    - ETL and data processing
    - Business logic
    - Data validation
    - JSON schema generation

    This model uses composition with the auto-generated Pydantic model,
    exposing a curated subset of fields with business methods.

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
    archived_at: AwareDatetime | None = Field(
        None, description="Timestamp when product was archived"
    )

    # ============ Nested Data ============

    variant_count: int = Field(
        0, ge=0, description="Number of variants for this product"
    )
    config_count: int = Field(0, ge=0, description="Number of configuration attributes")

    # ============ Factory Methods ============

    @classmethod
    def from_generated(cls, generated: GeneratedProduct) -> KatanaProduct:
        """Create a KatanaProduct from a generated Pydantic Product model.

        This method extracts the curated subset of fields from the generated model.

        Args:
            generated: The auto-generated Pydantic Product model.

        Returns:
            A new KatanaProduct instance with business methods.

        Example:
            ```python
            from katana_public_api_client.models_pydantic import Product

            # Convert from generated pydantic model
            generated = Product.from_attrs(attrs_product)
            domain = KatanaProduct.from_generated(generated)
            ```
        """
        # Count nested collections
        variant_count = len(generated.variants) if generated.variants else 0
        config_count = len(generated.configs) if generated.configs else 0

        return cls(
            id=generated.id,
            name=generated.name,
            type="product",
            uom=generated.uom,
            category_name=generated.category_name,
            is_sellable=generated.is_sellable,
            is_producible=generated.is_producible,
            is_purchasable=generated.is_purchasable,
            is_auto_assembly=generated.is_auto_assembly,
            batch_tracked=generated.batch_tracked,
            serial_tracked=generated.serial_tracked,
            operations_in_sequence=generated.operations_in_sequence,
            default_supplier_id=generated.default_supplier_id,
            lead_time=generated.lead_time,
            minimum_order_quantity=generated.minimum_order_quantity,
            purchase_uom=generated.purchase_uom,
            purchase_uom_conversion_rate=generated.purchase_uom_conversion_rate,
            additional_info=generated.additional_info,
            custom_field_collection_id=generated.custom_field_collection_id,
            archived_at=generated.archived_at,
            variant_count=variant_count,
            config_count=config_count,
            created_at=generated.created_at,
            updated_at=generated.updated_at,
            deleted_at=None,  # Product uses archived_at, not deleted_at
        )

    @classmethod
    def from_attrs(cls, attrs_product: AttrsProduct) -> KatanaProduct:
        """Create a KatanaProduct from an attrs Product model (API response).

        This method leverages the generated Pydantic model's `from_attrs()` method
        to handle UNSET sentinel conversion, then creates the domain model.

        Args:
            attrs_product: The attrs Product model from API response.

        Returns:
            A new KatanaProduct instance with business methods.

        Example:
            ```python
            from katana_public_api_client.api.product import get_product
            from katana_public_api_client.utils import unwrap

            response = await get_product.asyncio_detailed(client=client, id=123)
            attrs_product = unwrap(response)
            domain = KatanaProduct.from_attrs(attrs_product)
            ```
        """
        from ..models_pydantic._generated.inventory import Product as GeneratedProduct

        # Use generated model's from_attrs() to handle UNSET conversion
        generated = GeneratedProduct.from_attrs(attrs_product)
        return cls.from_generated(generated)

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
            "Archived At": self.archived_at.isoformat() if self.archived_at else "",
        }


__all__ = ["KatanaProduct"]
