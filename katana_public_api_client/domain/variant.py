"""Domain model for Variant entities.

This module provides a Pydantic model representing a Variant (product, material, or service SKU)
optimized for ETL, data processing, and business logic.

The domain model uses composition with the auto-generated Pydantic model from OpenAPI,
leveraging its `from_attrs()` conversion while adding business-specific methods.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Literal

from pydantic import Field

from .base import KatanaBaseModel
from .converters import unwrap_unset

if TYPE_CHECKING:
    from ..models.variant import Variant as AttrsVariant
    from ..models_pydantic._generated.inventory import Variant as GeneratedVariant


def build_variant_display_name(
    parent_name: str | None,
    config_attributes: Iterable[Any] | None,
    fallback_sku: str | None = None,
) -> str:
    """Build a variant's display name in Katana UI format.

    Format: ``"{parent_name} / {config_value_1} / {config_value_2} / ..."``.
    Falls back to ``fallback_sku`` when ``parent_name`` is empty (a
    defensive case — Katana always returns a non-empty parent name in
    practice, but the legacy cache handled the empty case so we
    preserve it).

    Accepts ``config_attributes`` as an iterable of either dicts
    (domain models, MCP response dicts) or attrs objects (raw API
    objects via ``?extend=`` responses). Both routes converge on a
    ``config_value`` field — the helper reads via ``dict.get`` for the
    former and ``getattr`` + ``unwrap_unset`` for the latter. This is
    the single source of truth for the formula; consumers in the
    ``KatanaVariant`` domain class, the typed-cache postprocess hook,
    and the MCP variant-details response all delegate to this function
    so the rendered name stays consistent across the codebase.

    Args:
        parent_name: The parent Product or Material's ``name``. ``None``
            or empty triggers the SKU fallback.
        config_attributes: Iterable of variant config attribute records
            (e.g. ``{"config_name": "Size", "config_value": "Large"}``).
            Empty or ``None`` is fine — yields just the parent name.
        fallback_sku: Returned (or empty string) when ``parent_name``
            is empty.

    Returns:
        The formatted display name, or ``fallback_sku`` (or ``""``) on
        the empty-parent path.

    Example:
        >>> build_variant_display_name(
        ...     "Kitchen Knife",
        ...     [
        ...         {"config_name": "Size", "config_value": "8-inch"},
        ...         {"config_name": "Color", "config_value": "Black"},
        ...     ],
        ... )
        'Kitchen Knife / 8-inch / Black'
        >>> build_variant_display_name(None, [], fallback_sku="KNF-001")
        'KNF-001'
    """
    if not parent_name:
        return fallback_sku or ""
    parts: list[str] = [parent_name]
    for attr in config_attributes or []:
        # Dict shape (domain class, MCP response): direct .get.
        # Attrs-object shape (raw API): getattr + unwrap_unset to strip
        # the UNSET sentinel (which itself handles ``None`` and
        # ``Unset`` uniformly via its default). Both yield ``str | None``.
        if isinstance(attr, dict):
            value = attr.get("config_value")
        else:
            value = unwrap_unset(getattr(attr, "config_value", None), None)
        if isinstance(value, str) and value:
            parts.append(value)
    return " / ".join(parts)


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

    # ============ Core Fields (key always present, value may be null) ============

    id: int = Field(..., description="Unique variant ID")
    sku: str | None = Field(
        ...,
        description=(
            "Stock Keeping Unit. Katana allows variants to be created without "
            "a SKU; nullable to match the wire contract. The field is always "
            "present in API responses but may be ``None`` for variants created "
            "without a SKU (e.g., legacy NetSuite imports)."
        ),
    )

    # ============ Pricing Fields ============

    sales_price: float | None = Field(
        default=None, ge=0, le=100_000_000_000, description="Sales price"
    )
    purchase_price: float | None = Field(
        default=None, ge=0, le=100_000_000_000, description="Purchase cost"
    )

    # ============ Relationship Fields ============

    product_id: int | None = Field(
        default=None, description="ID of parent product (if product variant)"
    )
    material_id: int | None = Field(
        default=None, description="ID of parent material (if material variant)"
    )
    product_or_material_name: str | None = Field(
        default=None, description="Name of parent product or material"
    )

    # ============ Classification ============

    type_: Literal["product", "material", "service"] | None = Field(
        default=None,
        alias="type",
        description="Variant type (product, material, or service)",
    )

    # ============ Inventory & Barcode Fields ============

    internal_barcode: str | None = Field(default=None, description="Internal barcode")
    registered_barcode: str | None = Field(
        default=None, description="Registered/UPC barcode"
    )
    supplier_item_codes: list[str] = Field(
        default_factory=list, description="Supplier item codes"
    )

    # ============ Ordering Fields ============

    lead_time: int | None = Field(
        default=None, ge=0, le=999, description="Lead time in days to fulfill order"
    )
    minimum_order_quantity: float | None = Field(
        default=None, ge=0, le=999_999_999, description="Minimum order quantity"
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
        type_value: Literal["product", "material", "service"] | None = None
        if generated.type is not None:
            raw_type = (
                generated.type.value
                if hasattr(generated.type, "value")
                else generated.type
            )
            # Per-branch narrowing satisfies both pyright and ty:
            # ``raw_type`` is ``VariantType | str``; pyright doesn't
            # narrow membership-against-literals, and ty calls a wrapping
            # cast redundant. Direct equality on each literal narrows
            # cleanly under both checkers.
            if raw_type == "product":
                type_value = "product"
            elif raw_type == "material":
                type_value = "material"
            elif raw_type == "service":
                type_value = "service"

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

            # Attribute exists per ``hasattr`` but isn't on the static
            # ``Variant`` shape (it comes in via ``?extend=`` API
            # responses) — read via ``getattr`` to satisfy the checker.
            pom = getattr(attrs_variant, "product_or_material", None)
            if pom is not UNSET and pom is not None and hasattr(pom, "name"):
                name = pom.name
                if name is not UNSET and isinstance(name, str):
                    product_or_material_name = name

        return cls.from_generated(generated, product_or_material_name)

    # ============ Business Logic Methods ============

    def get_display_name(self) -> str:
        """Get formatted display name matching Katana UI format.

        Delegates to :func:`build_variant_display_name` so the formula
        stays consistent across the domain class, the typed-cache
        postprocess hook, and the MCP variant-details response.

        Returns:
            Formatted variant name, or SKU if no parent name available.

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
        return build_variant_display_name(
            self.product_or_material_name,
            self.config_attributes,
            self.sku,
        )

    def matches_search(self, query: str) -> bool:
        """Check if variant matches search query with tokenization and fuzzy matching.

        Searches across SKU, product/material name, supplier codes, and config
        attributes. Supports multi-word queries (all tokens must match) and
        tolerates typos via fuzzy matching.

        Args:
            query: Search query string (case-insensitive, multi-word supported)

        Returns:
            True if variant matches query

        Example:
            ```python
            variant = KatanaVariant(id=1, sku="FOX-FORK-160", ...)
            variant.matches_search("fox")        # True
            variant.matches_search("fork 160")   # True (multi-word)
            variant.matches_search("forks")      # True (fuzzy)
            variant.matches_search("shimano")    # False
            ```
        """
        from katana_public_api_client.helpers.search import score_match

        # Build searchable fields with supplier codes and config values
        extra_text_parts = list(self.supplier_item_codes)
        for attr in self.config_attributes:
            if value := attr.get("config_value"):
                extra_text_parts.append(value)
        extra_text = " ".join(extra_text_parts)

        return (
            score_match(
                query=query,
                fields={
                    "sku": (self.sku or "", 100),
                    "name": (self.product_or_material_name or "", 30),
                    "extra": (extra_text, 10),
                },
            )
            > 0
        )

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
