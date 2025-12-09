"""Domain model for Material entities.

This module provides a Pydantic model representing a Material (raw material or component)
optimized for ETL, data processing, and business logic.

The domain model uses composition with the auto-generated Pydantic model from OpenAPI,
leveraging its `from_attrs()` conversion while adding business-specific methods.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from pydantic import AwareDatetime, Field

from .base import KatanaBaseModel

if TYPE_CHECKING:
    from ..models.material import Material as AttrsMaterial
    from ..models_pydantic._generated.inventory import Material as GeneratedMaterial


class KatanaMaterial(KatanaBaseModel):
    """Domain model for a Material.

    A Material represents raw materials and components used in manufacturing, including
    inventory tracking, supplier information, and batch management. This is a Pydantic
    model optimized for:
    - ETL and data processing
    - Business logic
    - Data validation
    - JSON schema generation

    This model uses composition with the auto-generated Pydantic model,
    exposing a curated subset of fields with business methods.

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
        None,
        max_length=7,
        description="Purchase unit of measure (if different from base UOM)",
    )
    purchase_uom_conversion_rate: float | None = Field(
        None,
        ge=0,
        le=1_000_000_000_000,
        description="Conversion rate from purchase UOM to base UOM",
    )

    # ============ Additional Info ============

    additional_info: str | None = Field(None, description="Additional notes/info")
    custom_field_collection_id: int | None = Field(
        None, description="Custom field collection ID"
    )
    archived_at: AwareDatetime | None = Field(
        None, description="Timestamp when material was archived"
    )

    # ============ Nested Data ============

    variant_count: int = Field(
        0, ge=0, description="Number of variants for this material"
    )
    config_count: int = Field(0, ge=0, description="Number of configuration attributes")

    # ============ Factory Methods ============

    @classmethod
    def from_generated(cls, generated: GeneratedMaterial) -> KatanaMaterial:
        """Create a KatanaMaterial from a generated Pydantic Material model.

        This method extracts the curated subset of fields from the generated model.

        Args:
            generated: The auto-generated Pydantic Material model.

        Returns:
            A new KatanaMaterial instance with business methods.

        Example:
            ```python
            from katana_public_api_client.models_pydantic import Material

            # Convert from generated pydantic model
            generated = Material.from_attrs(attrs_material)
            domain = KatanaMaterial.from_generated(generated)
            ```
        """
        # Count nested collections
        variant_count = len(generated.variants) if generated.variants else 0
        config_count = len(generated.configs) if generated.configs else 0

        return cls(
            id=generated.id,
            name=generated.name,
            type="material",
            uom=generated.uom,
            category_name=generated.category_name,
            is_sellable=generated.is_sellable,
            batch_tracked=generated.batch_tracked,
            default_supplier_id=generated.default_supplier_id,
            purchase_uom=generated.purchase_uom,
            purchase_uom_conversion_rate=generated.purchase_uom_conversion_rate,
            additional_info=generated.additional_info,
            custom_field_collection_id=generated.custom_field_collection_id,
            archived_at=generated.archived_at,
            variant_count=variant_count,
            config_count=config_count,
            created_at=generated.created_at,
            updated_at=generated.updated_at,
            deleted_at=None,  # Material uses archived_at, not deleted_at
        )

    @classmethod
    def from_attrs(cls, attrs_material: AttrsMaterial) -> KatanaMaterial:
        """Create a KatanaMaterial from an attrs Material model (API response).

        This method leverages the generated Pydantic model's `from_attrs()` method
        to handle UNSET sentinel conversion, then creates the domain model.

        Args:
            attrs_material: The attrs Material model from API response.

        Returns:
            A new KatanaMaterial instance with business methods.

        Example:
            ```python
            from katana_public_api_client.api.material import get_material
            from katana_public_api_client.utils import unwrap

            response = await get_material.asyncio_detailed(client=client, id=123)
            attrs_material = unwrap(response)
            domain = KatanaMaterial.from_attrs(attrs_material)
            ```
        """
        from ..models_pydantic._generated.inventory import Material as GeneratedMaterial

        # Use generated model's from_attrs() to handle UNSET conversion
        generated = GeneratedMaterial.from_attrs(attrs_material)
        return cls.from_generated(generated)

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
            "Archived At": self.archived_at.isoformat() if self.archived_at else "",
        }


__all__ = ["KatanaMaterial"]
