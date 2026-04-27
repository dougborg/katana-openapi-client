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
