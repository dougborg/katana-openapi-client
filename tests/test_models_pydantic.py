"""Tests for auto-generated Pydantic models.

These tests verify:
1. Models are properly generated from OpenAPI spec
2. attrs↔pydantic conversion works correctly
3. Model coverage (~287 models generated)
4. Immutability (frozen=True)
5. Registry mappings work correctly
"""

from __future__ import annotations

from datetime import UTC

import pytest


class TestModelsGenerated:
    """Tests for model generation verification."""

    def test_pydantic_models_importable(self) -> None:
        """Test that pydantic models can be imported."""
        from katana_public_api_client.models_pydantic._generated import (
            Customer,
            ManufacturingOrder,
            Material,
            Product,
            RegularPurchaseOrder,
            SalesOrder,
        )

        assert Product is not None
        assert Material is not None
        assert Customer is not None
        assert SalesOrder is not None
        assert RegularPurchaseOrder is not None
        assert ManufacturingOrder is not None

    def test_model_count_minimum(self) -> None:
        """Test that we have at least 280 models generated."""
        from katana_public_api_client.models_pydantic._generated import __all__

        # We should have at least 280 models (287 classes + 4 aliases = 291 total)
        assert len(__all__) >= 280, f"Expected at least 280 models, got {len(__all__)}"

    def test_base_entity_hierarchy(self) -> None:
        """Test that entity hierarchy is correct."""
        from katana_public_api_client.models_pydantic._base import KatanaPydanticBase
        from katana_public_api_client.models_pydantic._generated import (
            ArchivableEntity,
            BaseEntity,
            DeletableEntity,
            UpdatableEntity,
        )

        assert issubclass(BaseEntity, KatanaPydanticBase)
        assert issubclass(UpdatableEntity, BaseEntity)
        assert issubclass(DeletableEntity, BaseEntity)
        assert issubclass(ArchivableEntity, BaseEntity)


class TestDomainGrouping:
    """Tests for domain-based file organization."""

    def test_inventory_models_in_inventory_module(self) -> None:
        """Test that inventory models are in the inventory module."""
        from katana_public_api_client.models_pydantic._generated import inventory

        assert hasattr(inventory, "Product")
        assert hasattr(inventory, "Material")
        assert hasattr(inventory, "Variant")

    def test_contacts_models_in_contacts_module(self) -> None:
        """Test that contact models are in the contacts module."""
        from katana_public_api_client.models_pydantic._generated import contacts

        assert hasattr(contacts, "Customer")
        assert hasattr(contacts, "Supplier")

    def test_webhooks_models_in_webhooks_module(self) -> None:
        """Test that webhook models are in the webhooks module."""
        from katana_public_api_client.models_pydantic._generated import webhooks

        assert hasattr(webhooks, "Webhook")
        assert hasattr(webhooks, "WebhookEvent")

    def test_error_models_in_errors_module(self) -> None:
        """Test that error models are in the errors module."""
        from katana_public_api_client.models_pydantic._generated import errors

        assert hasattr(errors, "ErrorResponse")
        assert hasattr(errors, "BaseValidationError")


class TestModelConfiguration:
    """Tests for Pydantic model configuration."""

    def test_models_use_frozen_config(self) -> None:
        """Test that models use frozen=True for immutability."""
        from katana_public_api_client.models_pydantic._base import KatanaPydanticBase

        assert KatanaPydanticBase.model_config.get("frozen") is True

    def test_models_use_extra_forbid(self) -> None:
        """Test that base models use extra='forbid' to catch typos in request data."""
        from katana_public_api_client.models_pydantic._base import KatanaPydanticBase

        assert KatanaPydanticBase.model_config.get("extra") == "forbid"

    def test_base_entity_uses_extra_ignore(self) -> None:
        """Test that response models tolerate extra fields from the API (#295)."""
        from katana_public_api_client.models_pydantic._generated import BaseEntity

        assert BaseEntity.model_config.get("extra") == "ignore"

    def test_response_model_tolerates_extra_fields(self) -> None:
        """Test that a concrete response model accepts unknown fields (#295)."""
        from katana_public_api_client.models_pydantic._generated import Product

        # Simulate Katana returning an unexpected field
        product = Product.model_validate(
            {
                "id": 1,
                "name": "Widget",
                "type": "product",
                "unexpected_new_field": "should not raise",
            }
        )
        assert product.id == 1

    def test_models_validate_assignment(self) -> None:
        """Test that models validate on assignment."""
        from katana_public_api_client.models_pydantic._base import KatanaPydanticBase

        assert KatanaPydanticBase.model_config.get("validate_assignment") is True

    def test_base_extends_sqlmodel(self) -> None:
        """Canary: KatanaPydanticBase must stay rooted in SQLModel (#342)."""
        from sqlmodel import SQLModel

        from katana_public_api_client.models_pydantic._base import KatanaPydanticBase

        assert issubclass(KatanaPydanticBase, SQLModel)

    def test_generated_classes_extend_sqlmodel(self) -> None:
        """Generated entities inherit SQLModel-ness via KatanaPydanticBase."""
        from sqlmodel import SQLModel

        from katana_public_api_client.models_pydantic._generated import (
            Product,
            SalesOrder,
            Variant,
        )

        for cls in (Product, Variant, SalesOrder):
            assert issubclass(cls, SQLModel), f"{cls.__name__} is not a SQLModel"

    def test_cache_tables_are_sqlmodel_tables(self) -> None:
        """Cache-target classes register tables with snake_case names and `id` PKs.

        Sanity-check the #342 generator pipeline: ``SalesOrder`` and
        ``SalesOrderRow`` opt into SQLModel table mode via ``table=True``.
        Verified via ``SQLModel.metadata.tables`` (the typed public view of
        the same table objects the classes' ``__table__`` attributes point
        at) — importing the module triggers table registration; a
        ``KeyError`` on lookup would mean a cache-target class silently
        failed to register.
        """
        import importlib

        from sqlmodel import SQLModel

        # importlib triggers module load (registering the tables with
        # SQLModel.metadata) without a named binding the linter will flag
        # as unused.
        importlib.import_module(
            "katana_public_api_client.models_pydantic._generated.sales_orders"
        )

        so_table = SQLModel.metadata.tables["sales_order"]
        sor_table = SQLModel.metadata.tables["sales_order_row"]
        assert so_table.name == "sales_order"
        assert sor_table.name == "sales_order_row"
        assert [c.name for c in so_table.primary_key.columns] == ["id"]
        assert [c.name for c in sor_table.primary_key.columns] == ["id"]

    def test_cache_table_foreign_keys(self) -> None:
        """SalesOrderRow must declare a FK back to sales_order.id."""
        import importlib

        from sqlmodel import SQLModel

        importlib.import_module(
            "katana_public_api_client.models_pydantic._generated.sales_orders"
        )
        table = SQLModel.metadata.tables["sales_order_row"]
        fks = {fk.target_fullname for fk in table.foreign_keys}
        assert "sales_order.id" in fks

    def test_cache_table_relationship_roundtrip(self) -> None:
        """Full ORM roundtrip on the SQLModel cache tables.

        Catches regressions in the generator's relationship injection step:
        parent ↔ child back-references must resolve so we can insert, query,
        and traverse both directions.
        """
        from sqlmodel import Session, SQLModel, create_engine, select

        from katana_public_api_client.models_pydantic._generated import (
            CachedSalesOrder,
            CachedSalesOrderRow,
            SalesOrderStatus,
        )

        engine = create_engine("sqlite://")
        SQLModel.metadata.create_all(engine)

        with Session(engine) as session:
            order = CachedSalesOrder(
                id=1,
                customer_id=42,
                location_id=1,
                order_no="SO-001",
                status=SalesOrderStatus.not_shipped,
            )
            row = CachedSalesOrderRow(
                id=1, sales_order_id=1, variant_id=100, quantity=5.0
            )
            session.add(order)
            session.add(row)
            session.commit()

            fetched = session.exec(select(CachedSalesOrder)).one()
            assert fetched.order_no == "SO-001"
            assert len(fetched.sales_order_rows) == 1
            assert fetched.sales_order_rows[0].variant_id == 100
            # Back-reference must resolve in the other direction too. Narrow
            # the Optional type before accessing the parent's attributes.
            parent = fetched.sales_order_rows[0].sales_order
            assert parent is not None
            assert parent.order_no == "SO-001"


class TestRegistry:
    """Tests for attrs↔pydantic registry."""

    def test_registry_has_mappings(self) -> None:
        """Test that registry has model mappings."""
        from katana_public_api_client.models_pydantic._registry import (
            get_registration_stats,
        )

        stats = get_registration_stats()
        # We should have at least 200 mappings (210 expected)
        assert stats["total_pairs"] >= 200

    def test_lookup_pydantic_class_by_attrs(self) -> None:
        """Test looking up pydantic class from attrs class."""
        from katana_public_api_client.models import Product as AttrsProduct
        from katana_public_api_client.models_pydantic._generated import (
            Product as PydanticProduct,
        )
        from katana_public_api_client.models_pydantic._registry import (
            get_pydantic_class,
        )

        result = get_pydantic_class(AttrsProduct)
        assert result is PydanticProduct

    def test_lookup_attrs_class_by_pydantic(self) -> None:
        """Test looking up attrs class from pydantic class."""
        from katana_public_api_client.models import Product as AttrsProduct
        from katana_public_api_client.models_pydantic._generated import (
            Product as PydanticProduct,
        )
        from katana_public_api_client.models_pydantic._registry import (
            get_attrs_class,
        )

        result = get_attrs_class(PydanticProduct)
        assert result is AttrsProduct

    def test_is_registered(self) -> None:
        """Test checking if a class is registered."""
        from katana_public_api_client.models import Product as AttrsProduct
        from katana_public_api_client.models_pydantic._generated import (
            Product as PydanticProduct,
        )
        from katana_public_api_client.models_pydantic._registry import is_registered

        assert is_registered(AttrsProduct) is True
        assert is_registered(PydanticProduct) is True


class TestModelInstantiation:
    """Tests for creating model instances."""

    def test_create_simple_model(self) -> None:
        """Test creating a simple model instance."""
        from katana_public_api_client.models_pydantic._generated import BaseEntity

        entity = BaseEntity(id=123)
        assert entity.id == 123

    def test_create_product_model(self) -> None:
        """Test creating a Product model instance."""
        from katana_public_api_client.models_pydantic._generated import Product

        product = Product(
            id=1,
            name="Test Product",
            uom="pcs",
            type="product",
        )
        assert product.id == 1
        assert product.name == "Test Product"
        assert product.uom == "pcs"
        assert product.type == "product"

    def test_model_validation_fails_for_missing_required(self) -> None:
        """Test that validation fails for missing required fields."""
        from typing import Any

        from pydantic import ValidationError

        from katana_public_api_client.models_pydantic._generated import Product

        # Test that Product requires name, uom, type (id is required too)
        # We pass incomplete kwargs to trigger validation error
        # Type annotation allows the type checker to accept any dict values
        incomplete_kwargs: dict[str, Any] = {"id": 1}  # Missing name, uom, type
        with pytest.raises(ValidationError):
            Product(**incomplete_kwargs)


class TestVariantNullSku:
    """Variant.sku must accept None — Katana lets users create variants without one.

    Pinning the wire-contract relaxation that ships in this PR: the spec previously
    declared ``sku: type: string`` (non-nullable), but Katana actually emits
    ``sku: null`` for variants created without one. The bug surfaced as a typed-cache
    sync crash because ``get_all_variants(extend=PRODUCT_OR_MATERIAL)`` nests each
    parent's full ``variants[]`` array, and ``Variant.from_attrs`` recursively
    validated each nested variant — one null-sku sibling killed the whole batch.
    """

    def test_variant_accepts_null_sku(self) -> None:
        from katana_public_api_client.models_pydantic._generated import Variant

        variant = Variant(id=33351828, sku=None)
        assert variant.sku is None

    def test_variant_response_accepts_null_sku(self) -> None:
        from katana_public_api_client.models_pydantic._generated import VariantResponse

        response = VariantResponse(id=33351828, sku=None)
        assert response.sku is None

    def test_variant_from_attrs_with_null_sku(self) -> None:
        """The crash path: ``Variant.from_attrs(attrs_with_null_sku)`` must succeed."""
        from katana_public_api_client.models import Variant as AttrsVariant
        from katana_public_api_client.models_pydantic._generated import Variant

        attrs_variant = AttrsVariant.from_dict({"id": 33351828, "sku": None})
        pydantic_variant = Variant.from_attrs(attrs_variant)
        assert pydantic_variant.sku is None
        assert pydantic_variant.id == 33351828

    def test_product_with_null_sku_nested_variant(self) -> None:
        """Recursive conversion crash path: a parent product whose nested
        ``variants[]`` array contains a null-sku variant must round-trip cleanly.

        This is the exact shape Katana returns when ``get_all_variants`` is called
        with ``extend=PRODUCT_OR_MATERIAL`` — every parent embeds its full variant
        list, and previously a single null-sku sibling raised before any row landed
        in the cache.
        """
        from katana_public_api_client.models import Product as AttrsProduct
        from katana_public_api_client.models_pydantic._generated import Product

        attrs_product = AttrsProduct.from_dict(
            {
                "id": 101,
                "name": "Legacy NetSuite Import",
                "type": "product",
                "variants": [
                    {"id": 1, "sku": "VALID-SKU"},
                    {"id": 2, "sku": None},
                ],
            }
        )
        pydantic_product = Product.from_attrs(attrs_product)
        assert pydantic_product.variants is not None
        assert len(pydantic_product.variants) == 2
        assert pydantic_product.variants[0].sku == "VALID-SKU"
        assert pydantic_product.variants[1].sku is None


class TestServiceVariantNullSku:
    """ServiceVariant.sku must accept None — Katana lets users create services without one.

    Mirrors TestVariantNullSku for the service vertical. The spec previously declared
    ``ServiceVariant.sku: type: string`` (non-nullable, and listed in ``required``),
    but Katana actually emits ``sku: null`` for services created without one — the
    nullable-SKU relaxation that shipped for ``Variant`` was never applied here. The
    bug surfaced as a typed-cache sync crash in ``search_items``: ``get_all_services``
    nests each service's full ``variants[]`` array, and ``Service.from_attrs``
    recursively validated each nested ``ServiceVariant`` through pydantic — one
    null-sku variant killed the whole sync, leaving the catalog cache empty so every
    ``search_items`` call failed. Live-reproduced on the test tenant. Pinned here so a
    future regen can't silently revert the spec relaxation.
    """

    def test_service_variant_accepts_null_sku(self) -> None:
        from katana_public_api_client.models_pydantic._generated import ServiceVariant

        variant = ServiceVariant(id=40757631, sku=None, service_id=401)
        assert variant.sku is None

    def test_service_variant_from_attrs_with_null_sku(self) -> None:
        """The crash path: ``ServiceVariant.from_attrs(attrs_with_null_sku)``."""
        from katana_public_api_client.models import (
            ServiceVariant as AttrsServiceVariant,
        )
        from katana_public_api_client.models_pydantic._generated import ServiceVariant

        attrs_variant = AttrsServiceVariant.from_dict(
            {"id": 40757631, "sku": None, "service_id": 401}
        )
        pydantic_variant = ServiceVariant.from_attrs(attrs_variant)
        assert pydantic_variant.sku is None
        assert pydantic_variant.service_id == 401

    def test_service_with_null_sku_nested_variant(self) -> None:
        """The ``search_items`` crash path: a service whose nested ``variants[]``
        array contains a null-sku variant must round-trip cleanly — the exact
        shape ``get_all_services`` returns and the typed-cache sync validates
        per row.
        """
        from katana_public_api_client.models import Service as AttrsService
        from katana_public_api_client.models_pydantic._generated import Service

        attrs_service = AttrsService.from_dict(
            {
                "id": 401,
                "name": "Assembly Service",
                "type": "service",
                "variants": [
                    {"id": 1, "sku": "SVC-001", "service_id": 401},
                    {"id": 2, "sku": None, "service_id": 401},
                ],
            }
        )
        pydantic_service = Service.from_attrs(attrs_service)
        assert pydantic_service.variants is not None
        assert len(pydantic_service.variants) == 2
        assert pydantic_service.variants[0].sku == "SVC-001"
        assert pydantic_service.variants[1].sku is None


class TestManufacturingOrderNullDeadline:
    """ManufacturingOrder.production_deadline_date must accept None.

    Pinning the wire-contract relaxation in this PR: the spec previously declared
    ``production_deadline_date: type: string`` (non-nullable), so the generated
    ``ManufacturingOrder.from_dict`` parsed it with a bare ``isoparse(value)`` that
    only guarded ``Unset`` — an API ``null`` (key present, value None) raised
    ``TypeError: object of type 'NoneType' has no len()`` inside ``isoparse``.
    ``POST /manufacturing_order_make_to_order`` returns exactly that shape (an MO
    with no deadline), which crashed any typed read of the response (get / list /
    make_to_order). Spec corrected to ``[string, "null"]``; pinned here so a
    future regen can't silently revert it.
    """

    def test_attrs_from_dict_accepts_null_deadline(self) -> None:
        """The crash path: ``ManufacturingOrder.from_dict`` with a null deadline."""
        from katana_public_api_client.models import ManufacturingOrder

        mo = ManufacturingOrder.from_dict(
            {"id": 16920725, "production_deadline_date": None}
        )
        assert mo.production_deadline_date is None
        assert mo.id == 16920725

    def test_pydantic_accepts_null_deadline(self) -> None:
        from katana_public_api_client.models_pydantic._generated import (
            ManufacturingOrder,
        )

        mo = ManufacturingOrder(id=16920725, production_deadline_date=None)
        assert mo.production_deadline_date is None

    def test_from_attrs_with_null_deadline(self) -> None:
        from katana_public_api_client.models import (
            ManufacturingOrder as AttrsManufacturingOrder,
        )
        from katana_public_api_client.models_pydantic._generated import (
            ManufacturingOrder,
        )

        attrs_mo = AttrsManufacturingOrder.from_dict(
            {"id": 16920725, "production_deadline_date": None}
        )
        pydantic_mo = ManufacturingOrder.from_attrs(attrs_mo)
        assert pydantic_mo.production_deadline_date is None
        assert pydantic_mo.id == 16920725


class TestProductionSerialNumbers:
    """Wire-shape pin for ``CreateManufacturingOrderProductionRequest.serial_numbers``.

    Spec drift fix in #790: Katana's `POST /manufacturing_order_productions`
    schema previously declared ``serial_numbers: array<string>`` but the live
    API rejects strings with HTTP 422 ("must be of type: number") and accepts
    only integer ``SerialNumber.id`` values. The spec was corrected to
    ``array<integer>`` in this PR; this test pins the regenerated wire shape
    so a future spec-regen can't silently revert it.

    Worse, when an unknown integer ID was passed (e.g., from a future-mint
    flow that handed the production POST an unminted ID), Katana would
    return HTTP 200 with ``serial_numbers: []`` — a silent drop. Catching
    that footgun lives in the MCP tool layer (``_fulfill_manufacturing_order``);
    this test only pins the wire-type contract.
    """

    def test_serial_numbers_is_list_of_int(self) -> None:
        from katana_public_api_client.models_pydantic._generated import (
            CreateManufacturingOrderProductionRequest,
        )

        # Integer IDs round-trip cleanly.
        req = CreateManufacturingOrderProductionRequest(
            manufacturing_order_id=3001,
            completed_quantity=25,
            serial_numbers=[101, 102, 103],
        )
        assert req.serial_numbers == [101, 102, 103]

    def test_serial_numbers_rejects_string_values(self) -> None:
        from pydantic import ValidationError

        from katana_public_api_client.models_pydantic._generated import (
            CreateManufacturingOrderProductionRequest,
        )

        # Strings (the pre-#790 wrong type) now raise at the model boundary.
        # Routes through ``model_validate`` so the test stays type-clean —
        # raw string values are a wire-layer concern (MCP clients pass JSON),
        # not a static-type one.
        with pytest.raises(ValidationError):
            CreateManufacturingOrderProductionRequest.model_validate(
                {
                    "manufacturing_order_id": 3001,
                    "completed_quantity": 25,
                    "serial_numbers": ["SN-001", "SN-002"],
                }
            )


class TestWireNullTolerance:
    """Generated ``from_dict`` parsers must tolerate ``null`` for spec-nullable fields.

    Pins the wire-vs-spec gaps fixed for #727, one case per affected field:
    ``Variant`` / ``VariantResponse`` ``custom_fields`` and
    ``config_attributes``, ``Variant.internal_barcode``,
    ``Inventory.default_storage_bin`` and ``quantity_potential``, and
    ``Factory.default_so_delivery_time`` / ``default_po_lead_time`` (the
    latter also covering the non-datetime ``"14"`` opaque-string shape).
    Each one was a live-API payload shape that crashed our generated
    client because the OpenAPI spec declared the field as non-nullable
    but Katana's actual API returns ``null`` (often unconditionally).
    The test inputs mirror real responses captured against the live API
    on 2026-05-14; if a future spec regen re-tightens these to
    non-nullable, the relevant ``from_dict`` will raise
    ``TypeError: 'NoneType' object is not iterable`` (or
    ``has no len()``) and the test will fail.
    """

    def test_variant_from_dict_with_null_custom_fields(self) -> None:
        """``Variant.custom_fields = null`` (observed on 100% of variants).

        Crash site: ``for custom_fields_item_data in _custom_fields`` in the
        generated parser, when the wire delivers ``null`` instead of ``[]``
        or omission.
        """
        from katana_public_api_client.models import Variant as AttrsVariant

        attrs_variant = AttrsVariant.from_dict(
            {"id": 1, "sku": "TEST-SKU", "custom_fields": None}
        )
        # ``UNSET`` and ``None`` both mean "no custom fields"; the parser
        # must accept the wire's literal null without raising.
        assert attrs_variant.id == 1

    def test_variant_from_dict_with_null_config_attributes(self) -> None:
        """``Variant.config_attributes = null`` — defensive sibling case."""
        from katana_public_api_client.models import Variant as AttrsVariant

        attrs_variant = AttrsVariant.from_dict(
            {"id": 1, "sku": "TEST-SKU", "config_attributes": None}
        )
        assert attrs_variant.id == 1

    def test_service_variant_from_dict_with_null_custom_fields(self) -> None:
        """``ServiceVariant.custom_fields = null`` (observed on every create_service).

        Pre-fix this broke ``create_item(type="service")`` end-to-end:
        the API returns ``custom_fields: null`` on the nested variant and
        the parser tried to iterate it. Live-API shape captured 2026-05-26
        via ``scripts/probe_create_service_response.py``.
        """
        from katana_public_api_client.models import (
            ServiceVariant as AttrsServiceVariant,
        )

        attrs_variant = AttrsServiceVariant.from_dict(
            {
                "id": 1,
                "sku": "SVC-TEST",
                "service_id": 100,
                "custom_fields": None,
            }
        )
        assert attrs_variant.id == 1
        assert attrs_variant.custom_fields is None

    def test_variant_response_from_dict_with_null_custom_fields(self) -> None:
        """``VariantResponse.custom_fields = null`` (single-variant endpoint)."""
        from katana_public_api_client.models import VariantResponse as AttrsVR

        attrs_variant = AttrsVR.from_dict(
            {"id": 1, "sku": "TEST-SKU", "custom_fields": None}
        )
        assert attrs_variant.id == 1

    def test_variant_from_dict_with_null_internal_barcode(self) -> None:
        """``Variant.internal_barcode = null`` (observed on 41/50 variants)."""
        from katana_public_api_client.models import Variant as AttrsVariant

        attrs_variant = AttrsVariant.from_dict(
            {"id": 1, "sku": "TEST-SKU", "internal_barcode": None}
        )
        assert attrs_variant.id == 1

    def test_inventory_from_dict_with_null_default_storage_bin(self) -> None:
        """``Inventory.default_storage_bin = null`` (observed on 100% of rows).

        Crash site: ``VariantDefaultStorageBinLinkResponse.from_dict(None)``
        → ``dict(None)`` in the generated parser. The wire delivers ``null``
        whenever no bin has been linked (the typical case).
        """
        from katana_public_api_client.models import Inventory as AttrsInventory

        attrs_inv = AttrsInventory.from_dict(
            {
                "variant_id": 1,
                "location_id": 1,
                "safety_stock_level": "0",
                "reorder_point": 0,
                "average_cost": 0,
                "value_in_stock": 0,
                "quantity_in_stock": "0",
                "quantity_committed": "0",
                "quantity_expected": "0",
                "quantity_missing_or_excess": "0",
                # ``quantity_potential`` is required on the wire (Katana always
                # ships the key) and may be ``null`` — see the sibling
                # ``test_inventory_quantity_potential_nullable`` case.
                "quantity_potential": None,
                "default_storage_bin": None,
            }
        )
        assert attrs_inv.variant_id == 1

    def test_inventory_quantity_potential_nullable(self) -> None:
        """``Inventory.quantity_potential = null`` (observed on 100% of rows).

        Spec quirk: the field stays in ``required`` because Katana always
        ships the key, but the value is ``null`` on the typical row. The
        generated parser must accept ``null`` without raising.
        """
        from katana_public_api_client.models import Inventory as AttrsInventory

        attrs_inv = AttrsInventory.from_dict(
            {
                "variant_id": 1,
                "location_id": 1,
                "safety_stock_level": "0",
                "reorder_point": 0,
                "average_cost": 0,
                "value_in_stock": 0,
                "quantity_in_stock": "0",
                "quantity_committed": "0",
                "quantity_expected": "0",
                "quantity_missing_or_excess": "0",
                "quantity_potential": None,
            }
        )
        assert attrs_inv.variant_id == 1
        assert attrs_inv.quantity_potential is None

    def test_factory_from_dict_with_null_default_so_delivery_time(self) -> None:
        """``Factory.default_so_delivery_time = null`` (live wire ships null).

        Crash site: ``isoparse(_default_so_delivery_time)`` →
        ``len(None)`` inside dateutil. Schema gap with Katana's upstream
        spec, which documents the field as ``date-time`` (their example
        shows a valid datetime) but the live wire delivers ``null`` or an
        opaque short string. See #727.
        """
        from katana_public_api_client.models import Factory as AttrsFactory

        attrs_factory = AttrsFactory.from_dict(
            {
                "display_name": "Test Factory",
                "base_currency_code": "USD",
                "default_so_delivery_time": None,
                "default_po_lead_time": None,
            }
        )
        assert attrs_factory.display_name == "Test Factory"

    def test_factory_from_dict_with_opaque_po_lead_time(self) -> None:
        """``Factory.default_po_lead_time = "14"`` (live wire ships opaque short string).

        Sibling of the null case — the field is declared as a plain string
        (no ``format: date-time``) because the wire actually delivers
        days-as-string ("14") rather than a datetime, contrary to Katana's
        upstream example.
        """
        from katana_public_api_client.models import Factory as AttrsFactory

        attrs_factory = AttrsFactory.from_dict(
            {
                "display_name": "Test Factory",
                "base_currency_code": "USD",
                "default_po_lead_time": "14",
            }
        )
        assert attrs_factory.display_name == "Test Factory"
        # The parser keeps the opaque string verbatim — it's the caller's
        # job to interpret the format.
        assert attrs_factory.default_po_lead_time == "14"


class TestRequestModels:
    """Tests for request model instantiation."""

    def test_create_stock_adjustment_request_valid(self) -> None:
        """Test that CreateStockAdjustmentRequest accepts current schema fields."""
        from datetime import datetime

        from katana_public_api_client.models_pydantic._generated import (
            CreateStockAdjustmentRequest,
            StockAdjustmentRow1,
        )

        # This should not raise - model accepts current fields
        request = CreateStockAdjustmentRequest(
            stock_adjustment_number="TEST-001",
            location_id=1,
            stock_adjustment_date=datetime.now(UTC),
            stock_adjustment_rows=[
                StockAdjustmentRow1(variant_id=1, quantity=10.0),
            ],
        )
        assert request.location_id == 1
        assert request.stock_adjustment_number == "TEST-001"


class TestTypeAliases:
    """Tests for type aliases."""

    def test_type_aliases_exported(self) -> None:
        """Test that type aliases are exported from the module."""
        from katana_public_api_client.models_pydantic._generated import __all__

        # ConfigAttribute2, CustomField3, Address, ManufacturingOrderType
        # are type aliases that should be in __all__
        # Let's check that we have more than just classes
        assert len(__all__) >= 287  # 287 classes + some aliases


class TestMROFix:
    """Tests for Method Resolution Order fixes."""

    def test_customer_has_correct_inheritance(self) -> None:
        """Test that Customer inherits correctly (no duplicate BaseEntity)."""
        from katana_public_api_client.models_pydantic._generated import (
            Customer,
            DeletableEntity,
        )

        # Customer should only inherit from DeletableEntity (not both BaseEntity and DeletableEntity)
        assert issubclass(Customer, DeletableEntity)

    def test_sales_order_has_correct_inheritance(self) -> None:
        """Test that SalesOrder inherits correctly."""
        from katana_public_api_client.models_pydantic._generated import (
            DeletableEntity,
            SalesOrder,
        )

        assert issubclass(SalesOrder, DeletableEntity)
