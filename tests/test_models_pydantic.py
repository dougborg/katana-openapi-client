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
        """Test that models use extra='forbid' to catch typos."""
        from katana_public_api_client.models_pydantic._base import KatanaPydanticBase

        assert KatanaPydanticBase.model_config.get("extra") == "forbid"

    def test_models_validate_assignment(self) -> None:
        """Test that models validate on assignment."""
        from katana_public_api_client.models_pydantic._base import KatanaPydanticBase

        assert KatanaPydanticBase.model_config.get("validate_assignment") is True


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
