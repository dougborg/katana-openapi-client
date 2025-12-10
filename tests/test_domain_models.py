"""Tests for domain model factory methods.

These tests verify:
1. from_attrs() factory method correctly converts attrs models
2. from_generated() factory method correctly converts generated pydantic models
3. UNSET handling is correct
4. Nested object conversion (config_attributes, custom_fields)
5. Type consistency between attrs, generated pydantic, and domain models
"""

from __future__ import annotations

from datetime import UTC, datetime


class TestKatanaVariantFactoryMethods:
    """Tests for KatanaVariant.from_attrs() and from_generated()."""

    def test_from_generated_with_all_fields(self) -> None:
        """Test converting a fully-populated generated Variant."""
        from katana_public_api_client.domain.variant import KatanaVariant
        from katana_public_api_client.models_pydantic._generated.common import Type
        from katana_public_api_client.models_pydantic._generated.inventory import (
            Variant as GeneratedVariant,
        )

        # Create a generated variant with all fields
        generated = GeneratedVariant(
            id=123,
            sku="TEST-SKU-001",
            sales_price=99.99,
            purchase_price=49.99,
            product_id=456,
            material_id=None,
            type=Type.product,
            internal_barcode="INT-123",
            registered_barcode="UPC-456",
            supplier_item_codes=["SUP-001", "SUP-002"],
            lead_time=7,
            minimum_order_quantity=10.0,
            config_attributes=None,
            custom_fields=None,
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            updated_at=datetime(2024, 6, 1, 14, 30, 0, tzinfo=UTC),
            deleted_at=None,
        )

        domain = KatanaVariant.from_generated(generated, "Test Product")

        assert domain.id == 123
        assert domain.sku == "TEST-SKU-001"
        assert domain.sales_price == 99.99
        assert domain.purchase_price == 49.99
        assert domain.product_id == 456
        assert domain.material_id is None
        assert domain.type_ == "product"
        assert domain.product_or_material_name == "Test Product"
        assert domain.internal_barcode == "INT-123"
        assert domain.registered_barcode == "UPC-456"
        assert domain.supplier_item_codes == ["SUP-001", "SUP-002"]
        assert domain.lead_time == 7
        assert domain.minimum_order_quantity == 10.0
        assert domain.created_at == datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        assert domain.updated_at == datetime(2024, 6, 1, 14, 30, 0, tzinfo=UTC)
        assert domain.deleted_at is None

    def test_from_generated_with_minimal_fields(self) -> None:
        """Test converting a variant with only required fields."""
        from katana_public_api_client.domain.variant import KatanaVariant
        from katana_public_api_client.models_pydantic._generated.inventory import (
            Variant as GeneratedVariant,
        )

        generated = GeneratedVariant(id=1, sku="MIN-001")

        domain = KatanaVariant.from_generated(generated)

        assert domain.id == 1
        assert domain.sku == "MIN-001"
        assert domain.sales_price is None
        assert domain.purchase_price is None
        assert domain.type_ is None
        assert domain.product_or_material_name is None

    def test_from_generated_with_config_attributes(self) -> None:
        """Test converting config_attributes from nested objects to dicts."""
        from katana_public_api_client.domain.variant import KatanaVariant
        from katana_public_api_client.models_pydantic._generated.inventory import (
            ConfigAttribute2,
            Variant as GeneratedVariant,
        )

        config1 = ConfigAttribute2(config_name="Size", config_value="Large")
        config2 = ConfigAttribute2(config_name="Color", config_value="Blue")

        generated = GeneratedVariant(
            id=1,
            sku="CFG-001",
            config_attributes=[config1, config2],
        )

        domain = KatanaVariant.from_generated(generated)

        assert len(domain.config_attributes) == 2
        assert domain.config_attributes[0] == {
            "config_name": "Size",
            "config_value": "Large",
        }
        assert domain.config_attributes[1] == {
            "config_name": "Color",
            "config_value": "Blue",
        }

    def test_from_generated_with_custom_fields(self) -> None:
        """Test converting custom_fields from nested objects to dicts."""
        from katana_public_api_client.domain.variant import KatanaVariant
        from katana_public_api_client.models_pydantic._generated.inventory import (
            CustomField3,
            Variant as GeneratedVariant,
        )

        field1 = CustomField3(field_name="Warranty", field_value="1 year")
        field2 = CustomField3(field_name="Origin", field_value="USA")

        generated = GeneratedVariant(
            id=1,
            sku="CUS-001",
            custom_fields=[field1, field2],
        )

        domain = KatanaVariant.from_generated(generated)

        assert len(domain.custom_fields) == 2
        assert domain.custom_fields[0] == {
            "field_name": "Warranty",
            "field_value": "1 year",
        }
        assert domain.custom_fields[1] == {
            "field_name": "Origin",
            "field_value": "USA",
        }

    def test_from_generated_type_filtering(self) -> None:
        """Test that only 'product' and 'material' types are accepted."""
        from katana_public_api_client.domain.variant import KatanaVariant
        from katana_public_api_client.models_pydantic._generated.common import Type
        from katana_public_api_client.models_pydantic._generated.inventory import (
            Variant as GeneratedVariant,
        )

        # Test product type
        gen_product = GeneratedVariant(id=1, sku="P-001", type=Type.product)
        domain_product = KatanaVariant.from_generated(gen_product)
        assert domain_product.type_ == "product"

        # Test material type
        gen_material = GeneratedVariant(id=2, sku="M-001", type=Type.material)
        domain_material = KatanaVariant.from_generated(gen_material)
        assert domain_material.type_ == "material"

        # Test None type
        gen_none = GeneratedVariant(id=3, sku="N-001", type=None)
        domain_none = KatanaVariant.from_generated(gen_none)
        assert domain_none.type_ is None

    def test_from_attrs_delegates_to_generated(self) -> None:
        """Test that from_attrs() uses generated model's from_attrs()."""
        from katana_public_api_client.domain.variant import KatanaVariant
        from katana_public_api_client.models.variant import Variant as AttrsVariant

        # Create attrs variant with minimal fields
        attrs_variant = AttrsVariant(id=999, sku="ATTRS-001")

        domain = KatanaVariant.from_attrs(attrs_variant)

        assert domain.id == 999
        assert domain.sku == "ATTRS-001"


class TestKatanaProductFactoryMethods:
    """Tests for KatanaProduct.from_attrs() and from_generated()."""

    def test_from_generated_with_all_fields(self) -> None:
        """Test converting a fully-populated generated Product."""
        from katana_public_api_client.domain.product import KatanaProduct
        from katana_public_api_client.models_pydantic._generated.inventory import (
            Product as GeneratedProduct,
        )

        generated = GeneratedProduct(
            id=1,
            name="Test Product",
            type="product",
            uom="pcs",
            category_name="Electronics",
            is_sellable=True,
            is_producible=True,
            is_purchasable=True,
            is_auto_assembly=False,
            batch_tracked=True,
            serial_tracked=False,
            operations_in_sequence=True,
            default_supplier_id=100,
            lead_time=14,
            minimum_order_quantity=5.0,
            purchase_uom="box",
            purchase_uom_conversion_rate=10.0,
            additional_info="Test notes",
            custom_field_collection_id=200,
            archived_at=datetime(2024, 12, 1, 0, 0, 0, tzinfo=UTC),
            variants=None,
            configs=None,
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            updated_at=datetime(2024, 6, 1, 14, 30, 0, tzinfo=UTC),
        )

        domain = KatanaProduct.from_generated(generated)

        assert domain.id == 1
        assert domain.name == "Test Product"
        assert domain.type_ == "product"
        assert domain.uom == "pcs"
        assert domain.category_name == "Electronics"
        assert domain.is_sellable is True
        assert domain.is_producible is True
        assert domain.is_purchasable is True
        assert domain.is_auto_assembly is False
        assert domain.batch_tracked is True
        assert domain.serial_tracked is False
        assert domain.operations_in_sequence is True
        assert domain.default_supplier_id == 100
        assert domain.lead_time == 14
        assert domain.minimum_order_quantity == 5.0
        assert domain.purchase_uom == "box"
        assert domain.purchase_uom_conversion_rate == 10.0
        assert domain.additional_info == "Test notes"
        assert domain.custom_field_collection_id == 200
        assert domain.archived_at == datetime(2024, 12, 1, 0, 0, 0, tzinfo=UTC)
        assert domain.deleted_at is None  # Product uses archived_at, not deleted_at

    def test_from_generated_counts_variants_and_configs(self) -> None:
        """Test that variant_count and config_count are computed correctly."""
        from katana_public_api_client.domain.product import KatanaProduct
        from katana_public_api_client.models_pydantic._generated.inventory import (
            ItemConfig,
            Product as GeneratedProduct,
            Variant,
        )

        variants = [
            Variant(id=1, sku="V-001"),
            Variant(id=2, sku="V-002"),
            Variant(id=3, sku="V-003"),
        ]
        configs = [
            ItemConfig(id=1, name="Size", values=["S", "M", "L"]),
            ItemConfig(id=2, name="Color", values=["Red", "Blue"]),
        ]

        generated = GeneratedProduct(
            id=1,
            name="Multi-Variant Product",
            type="product",
            uom="pcs",
            variants=variants,
            configs=configs,
        )

        domain = KatanaProduct.from_generated(generated)

        assert domain.variant_count == 3
        assert domain.config_count == 2

    def test_from_attrs_delegates_to_generated(self) -> None:
        """Test that from_attrs() uses generated model's from_attrs()."""
        from katana_public_api_client.domain.product import KatanaProduct
        from katana_public_api_client.models.product import Product as AttrsProduct
        from katana_public_api_client.models.product_type import ProductType

        attrs_product = AttrsProduct(
            id=888, name="Attrs Product", type_=ProductType.PRODUCT
        )

        domain = KatanaProduct.from_attrs(attrs_product)

        assert domain.id == 888
        assert domain.name == "Attrs Product"
        assert domain.type_ == "product"


class TestKatanaMaterialFactoryMethods:
    """Tests for KatanaMaterial.from_attrs() and from_generated()."""

    def test_from_generated_with_all_fields(self) -> None:
        """Test converting a fully-populated generated Material."""
        from katana_public_api_client.domain.material import KatanaMaterial
        from katana_public_api_client.models_pydantic._generated.inventory import (
            Material as GeneratedMaterial,
        )

        generated = GeneratedMaterial(
            id=1,
            name="Raw Steel",
            type="material",
            uom="kg",
            category_name="Metals",
            is_sellable=False,
            batch_tracked=True,
            default_supplier_id=50,
            purchase_uom="ton",
            purchase_uom_conversion_rate=1000.0,
            additional_info="High-grade steel",
            custom_field_collection_id=300,
            archived_at=None,
            variants=None,
            configs=None,
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            updated_at=datetime(2024, 6, 1, 14, 30, 0, tzinfo=UTC),
        )

        domain = KatanaMaterial.from_generated(generated)

        assert domain.id == 1
        assert domain.name == "Raw Steel"
        assert domain.type_ == "material"
        assert domain.uom == "kg"
        assert domain.category_name == "Metals"
        assert domain.is_sellable is False
        assert domain.batch_tracked is True
        assert domain.default_supplier_id == 50
        assert domain.purchase_uom == "ton"
        assert domain.purchase_uom_conversion_rate == 1000.0
        assert domain.additional_info == "High-grade steel"
        assert domain.deleted_at is None  # Material uses archived_at, not deleted_at

    def test_from_attrs_delegates_to_generated(self) -> None:
        """Test that from_attrs() uses generated model's from_attrs()."""
        from katana_public_api_client.domain.material import KatanaMaterial
        from katana_public_api_client.models.material import Material as AttrsMaterial
        from katana_public_api_client.models.material_type import MaterialType

        attrs_material = AttrsMaterial(
            id=777, name="Test Material", type_=MaterialType.MATERIAL
        )

        domain = KatanaMaterial.from_attrs(attrs_material)

        assert domain.id == 777
        assert domain.name == "Test Material"
        assert domain.type_ == "material"


class TestKatanaServiceFactoryMethods:
    """Tests for KatanaService.from_attrs() and from_generated()."""

    def test_from_generated_with_all_fields(self) -> None:
        """Test converting a fully-populated generated Service."""
        from katana_public_api_client.domain.service import KatanaService
        from katana_public_api_client.models_pydantic._generated.common import Type1
        from katana_public_api_client.models_pydantic._generated.inventory import (
            Service as GeneratedService,
        )

        generated = GeneratedService(
            id=1,
            name="Assembly Service",
            type=Type1.service,
            uom="hours",
            category_name="Manufacturing",
            is_sellable=True,
            additional_info="External assembly",
            custom_field_collection_id=400,
            archived_at=datetime(2024, 11, 1, 0, 0, 0, tzinfo=UTC),
            variants=None,
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            updated_at=datetime(2024, 6, 1, 14, 30, 0, tzinfo=UTC),
            deleted_at=datetime(2024, 12, 1, 0, 0, 0, tzinfo=UTC),
        )

        domain = KatanaService.from_generated(generated)

        assert domain.id == 1
        assert domain.name == "Assembly Service"
        assert domain.type_ == "service"  # Always "service"
        assert domain.uom == "hours"
        assert domain.category_name == "Manufacturing"
        assert domain.is_sellable is True
        assert domain.additional_info == "External assembly"
        assert domain.archived_at == datetime(2024, 11, 1, 0, 0, 0, tzinfo=UTC)
        # Service has both archived_at and deleted_at
        assert domain.deleted_at == datetime(2024, 12, 1, 0, 0, 0, tzinfo=UTC)

    def test_from_generated_type_always_service(self) -> None:
        """Test that type is always 'service' regardless of input."""
        from katana_public_api_client.domain.service import KatanaService
        from katana_public_api_client.models_pydantic._generated.inventory import (
            Service as GeneratedService,
        )

        # Even with type=None in generated, domain should have type="service"
        generated = GeneratedService(id=1, name="Test", type=None)

        domain = KatanaService.from_generated(generated)

        assert domain.type_ == "service"

    def test_from_attrs_delegates_to_generated(self) -> None:
        """Test that from_attrs() uses generated model's from_attrs()."""
        from katana_public_api_client.domain.service import KatanaService
        from katana_public_api_client.models.service import Service as AttrsService

        attrs_service = AttrsService(id=666)

        domain = KatanaService.from_attrs(attrs_service)

        assert domain.id == 666
        assert domain.type_ == "service"


class TestConverterFunctions:
    """Tests for the converter functions in converters.py."""

    def test_variant_to_katana(self) -> None:
        """Test variant_to_katana converter function."""
        from katana_public_api_client.domain.converters import variant_to_katana
        from katana_public_api_client.models.variant import Variant as AttrsVariant

        attrs_variant = AttrsVariant(id=100, sku="CONV-001")

        domain = variant_to_katana(attrs_variant)

        assert domain.id == 100
        assert domain.sku == "CONV-001"

    def test_variants_to_katana_batch(self) -> None:
        """Test batch conversion of variants."""
        from katana_public_api_client.domain.converters import variants_to_katana
        from katana_public_api_client.models.variant import Variant as AttrsVariant

        attrs_variants = [
            AttrsVariant(id=1, sku="BATCH-001"),
            AttrsVariant(id=2, sku="BATCH-002"),
            AttrsVariant(id=3, sku="BATCH-003"),
        ]

        domains = variants_to_katana(attrs_variants)

        assert len(domains) == 3
        assert domains[0].sku == "BATCH-001"
        assert domains[1].sku == "BATCH-002"
        assert domains[2].sku == "BATCH-003"

    def test_product_to_katana(self) -> None:
        """Test product_to_katana converter function."""
        from katana_public_api_client.domain.converters import product_to_katana
        from katana_public_api_client.models.product import Product as AttrsProduct
        from katana_public_api_client.models.product_type import ProductType

        attrs_product = AttrsProduct(
            id=200, name="Converted Product", type_=ProductType.PRODUCT
        )

        domain = product_to_katana(attrs_product)

        assert domain.id == 200
        assert domain.name == "Converted Product"

    def test_material_to_katana(self) -> None:
        """Test material_to_katana converter function."""
        from katana_public_api_client.domain.converters import material_to_katana
        from katana_public_api_client.models.material import Material as AttrsMaterial
        from katana_public_api_client.models.material_type import MaterialType

        attrs_material = AttrsMaterial(
            id=300, name="Converted Material", type_=MaterialType.MATERIAL
        )

        domain = material_to_katana(attrs_material)

        assert domain.id == 300
        assert domain.name == "Converted Material"

    def test_service_to_katana(self) -> None:
        """Test service_to_katana converter function."""
        from katana_public_api_client.domain.converters import service_to_katana
        from katana_public_api_client.models.service import Service as AttrsService

        attrs_service = AttrsService(id=400)

        domain = service_to_katana(attrs_service)

        assert domain.id == 400
        assert domain.type_ == "service"


class TestDomainModelBusinessMethods:
    """Tests for domain model business methods."""

    def test_variant_get_display_name_with_configs(self) -> None:
        """Test KatanaVariant.get_display_name() with config attributes."""
        from katana_public_api_client.domain.variant import KatanaVariant

        variant = KatanaVariant(
            id=1,
            sku="DISP-001",
            product_or_material_name="Kitchen Knife",
            config_attributes=[
                {"config_name": "Size", "config_value": "8-inch"},
                {"config_name": "Handle", "config_value": "Wood"},
            ],
        )

        display_name = variant.get_display_name()

        assert display_name == "Kitchen Knife / 8-inch / Wood"

    def test_variant_get_display_name_no_name_uses_sku(self) -> None:
        """Test KatanaVariant.get_display_name() falls back to SKU."""
        from katana_public_api_client.domain.variant import KatanaVariant

        variant = KatanaVariant(
            id=1,
            sku="FALLBACK-SKU",
            product_or_material_name=None,
        )

        display_name = variant.get_display_name()

        assert display_name == "FALLBACK-SKU"

    def test_variant_matches_search(self) -> None:
        """Test KatanaVariant.matches_search()."""
        from katana_public_api_client.domain.variant import KatanaVariant

        variant = KatanaVariant(
            id=1,
            sku="FOX-FORK-160",
            product_or_material_name="Fox 36 Fork",
            supplier_item_codes=["SUPP-FOX-001"],
            config_attributes=[{"config_name": "Travel", "config_value": "160mm"}],
        )

        # Should match SKU
        assert variant.matches_search("fox") is True
        assert variant.matches_search("FORK") is True

        # Should match product name
        assert variant.matches_search("36") is True

        # Should match supplier codes
        assert variant.matches_search("supp") is True

        # Should match config values
        assert variant.matches_search("160") is True

        # Should not match
        assert variant.matches_search("shimano") is False

    def test_product_to_csv_row(self) -> None:
        """Test KatanaProduct.to_csv_row()."""
        from katana_public_api_client.domain.product import KatanaProduct

        product = KatanaProduct(
            id=1,
            name="CSV Product",
            type="product",
            category_name="Test Category",
            uom="pcs",
            is_sellable=True,
            is_producible=False,
            variant_count=5,
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        )

        row = product.to_csv_row()

        assert row["ID"] == 1
        assert row["Name"] == "CSV Product"
        assert row["Type"] == "product"
        assert row["Category"] == "Test Category"
        assert row["Is Sellable"] is True
        assert row["Variant Count"] == 5
        assert row["Created At"] == "2024-01-01T12:00:00+00:00"
