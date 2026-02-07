"""Tests that require real API credentials (marked as integration tests)."""

import asyncio
import importlib
import inspect
import os
from pathlib import Path
from typing import Any

import pytest
import yaml
from dotenv import load_dotenv

from katana_public_api_client import AuthenticatedClient, KatanaClient
from katana_public_api_client.api.product import get_all_products
from katana_public_api_client.utils import unwrap_data

# Load environment variables from .env file
load_dotenv()


class TestRealAPIIntegration:
    """Tests that use real API credentials when available."""

    @pytest.fixture(autouse=True)
    def bypass_test_env(self, monkeypatch):
        """Bypass the test environment setup and use real environment variables."""
        # Force reload of environment variables from .env file
        load_dotenv(override=True)
        # Don't let the setup_test_env fixture override our real values
        return True

    @pytest.fixture
    def api_credentials_available(self):
        """Check if real API credentials are available."""
        api_key = os.getenv("KATANA_API_KEY")
        return api_key is not None and api_key.strip() != ""

    @pytest.fixture
    def api_key(self):
        """Get API key from environment."""
        return os.getenv("KATANA_API_KEY")

    @pytest.fixture
    def base_url(self):
        """Get base URL from environment or use default."""
        return os.getenv("KATANA_BASE_URL", "https://api.katanamrp.com/v1")

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv("KATANA_API_KEY"),
        reason="Real API credentials not available (set KATANA_API_KEY in .env file)",
    )
    async def test_real_api_connection(self, api_key, base_url):
        """Test connection to real Katana API."""
        assert api_key is not None, "API key should not be None"
        # trunk-ignore(mypy/call-arg)
        client = AuthenticatedClient(base_url=base_url, token=api_key)

        async with client:
            # Try to fetch products (should work with any valid API key)
            response = await get_all_products.asyncio_detailed(client=client, limit=1)

            # Should get a successful response or proper error
            assert response.status_code in [
                200,
                401,
                403,
            ], f"Unexpected status code: {response.status_code}"

            if response.status_code == 200:
                # If successful, should have proper structure
                assert response.parsed is not None
                assert hasattr(response.parsed, "data")

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("KATANA_API_KEY"),
        reason="Real API credentials not available (set KATANA_API_KEY in .env file)",
    )
    async def test_katana_client_with_real_api(self, api_key, base_url):
        """Test KatanaClient with real API."""
        # Test both with explicit parameters and environment variables
        async with KatanaClient(api_key=api_key, base_url=base_url) as client:
            # Direct API call - automatic resilience built-in
            response = await get_all_products.asyncio_detailed(client=client, limit=1)

            # Should get a response
            assert response.status_code in [
                200,
                401,
                403,
            ], f"Unexpected status code: {response.status_code}"

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv("KATANA_API_KEY"),
        reason="Real API credentials not available (set KATANA_API_KEY in .env file)",
    )
    async def test_katana_client_with_env_vars_only(self):
        """Test KatanaClient using only environment variables."""
        # This tests the new default behavior where base_url defaults to official URL
        async with KatanaClient() as client:
            # Should work without explicit parameters since we have .env file
            assert client.token is not None
            assert client._base_url is not None
            # Base URL should be either from .env file or the default
            expected_urls = [
                "https://api.katanamrp.com/v1",  # Default
                os.getenv("KATANA_BASE_URL"),  # From .env file
            ]
            assert client._base_url in expected_urls

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv("KATANA_API_KEY"),
        reason="Real API credentials not available (set KATANA_API_KEY in .env file)",
    )
    async def test_real_api_pagination(self, api_key, base_url):
        """Test pagination with real API."""
        async with KatanaClient(api_key=api_key, base_url=base_url) as client:
            try:

                async def test_katana_pagination():
                    from katana_public_api_client.api.product import (
                        get_all_products,
                    )

                    # Test automatic pagination (now built into transport layer)
                    response = await get_all_products.asyncio_detailed(
                        client=client,
                        limit=5,  # Small limit to test automatic pagination
                    )
                    return response

                # Test with 30 second timeout
                response = await asyncio.wait_for(
                    test_katana_pagination(), timeout=30.0
                )

                # Should get a valid response
                assert response.status_code == 200, (
                    f"Expected 200, got {response.status_code}"
                )

                # Extract products from response
                if (
                    hasattr(response, "parsed")
                    and response.parsed
                    and hasattr(response.parsed, "data")
                ):
                    products = response.parsed.data
                    if isinstance(products, list) and len(products) > 0:
                        assert len(products) > 0, "Should get at least some products"

                        # Each product should be a ProductResponse object with proper attributes
                        first_product = products[0]
                        assert hasattr(first_product, "id"), (
                            "Product should have an id attribute"
                        )
                        assert hasattr(first_product, "name"), (
                            "Product should have a name attribute"
                        )

            except TimeoutError:
                pytest.fail("Pagination test timed out after 30 seconds")
            except Exception as e:
                error_msg = str(e).lower()
                if any(
                    keyword in error_msg
                    for keyword in [
                        "rate limit",
                        "permission",
                        "forbidden",
                        "unauthorized",
                    ]
                ):
                    pytest.skip(f"API limitation: {e}")
                else:
                    raise

    def test_environment_variable_loading(self):
        """Test that environment variables are loaded correctly."""
        # Test loading from .env file if it exists
        env_file = Path(".env")

        if env_file.exists():
            # Re-load to ensure we have latest values
            load_dotenv(override=True)

            # Check that key variables can be accessed
            api_key = os.environ.get("KATANA_API_KEY")

            # If .env exists and has API_KEY, it should be loaded
            if api_key:
                assert len(api_key) > 0, "API key should not be empty"

            # Base URL is optional in .env, should default if not set
            # This test just verifies the loading mechanism works

    @pytest.mark.integration
    def test_client_creation_with_env_vars(self, api_key, base_url):
        """Test that client can be created from environment variables."""
        if api_key:
            # Should be able to create client
            # trunk-ignore(mypy/call-arg)
            client = AuthenticatedClient(base_url=base_url, token=api_key)
            assert client.token == api_key
            assert hasattr(client, "_base_url"), "Client should have base URL"
        else:
            pytest.skip("No API credentials available in environment")

    def test_katana_client_defaults_base_url(self):
        """Test that KatanaClient defaults to official Katana API URL."""
        # Test without any environment variables set
        original_key = os.environ.get("KATANA_API_KEY")
        original_url = os.environ.get("KATANA_BASE_URL")

        try:
            # Temporarily clear environment variables to test defaults
            if "KATANA_BASE_URL" in os.environ:
                del os.environ["KATANA_BASE_URL"]

            # Should still be able to create client if API key is available
            if original_key:
                client = KatanaClient(api_key=original_key)
                assert client._base_url == "https://api.katanamrp.com/v1"

        finally:
            # Restore original values
            if original_key is not None:
                os.environ["KATANA_API_KEY"] = original_key
            if original_url is not None:
                os.environ["KATANA_BASE_URL"] = original_url

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv("KATANA_API_KEY"),
        reason="Real API credentials not available (set KATANA_API_KEY in .env file)",
    )
    async def test_api_error_handling(self, api_key, base_url):
        """Test error handling with real API."""
        # Test with an invalid API key by explicitly creating a client with a bad key
        # and ensuring environment variables don't interfere
        import os

        # Store original environment values
        original_api_key = os.environ.get("KATANA_API_KEY")
        original_base_url_env = os.environ.get("KATANA_BASE_URL")

        try:
            # Clear environment variables to ensure they don't interfere
            if "KATANA_API_KEY" in os.environ:
                del os.environ["KATANA_API_KEY"]
            if "KATANA_BASE_URL" in os.environ:
                del os.environ["KATANA_BASE_URL"]

            # Create client with invalid API key explicitly
            async with KatanaClient(
                api_key="invalid-api-key-12345", base_url=base_url
            ) as client:
                from katana_public_api_client.api.product import (
                    get_all_products,
                )

                # Direct API call with invalid key - automatic resilience built-in
                response = await get_all_products.asyncio_detailed(
                    client=client, limit=1
                )
                # Should handle error gracefully - either error status or the response itself
                if hasattr(response, "status_code"):
                    # If we get a response, it should be an error status for invalid API key
                    assert response.status_code >= 400, (
                        f"Expected error status code for invalid API key, got {response.status_code}"
                    )
                else:
                    # If we get an exception, that's also fine for error handling
                    pytest.fail(
                        "Should have received a response object with error status"
                    )

        finally:
            # Restore original environment values
            if original_api_key is not None:
                os.environ["KATANA_API_KEY"] = original_api_key
            if original_base_url_env is not None:
                os.environ["KATANA_BASE_URL"] = original_base_url_env


# --- Schema Validation Integration Tests ---

# Mapping of all GET list endpoints: (api_module_path, spec_path, schema_name)
# api_module_path is relative to katana_public_api_client.api
LIST_ENDPOINTS = [
    ("additional_costs.get_additional_costs", "/additional_costs", "AdditionalCost"),
    ("bom_row.get_all_bom_rows", "/bom_rows", "BomRow"),
    ("customer.get_all_customers", "/customers", "Customer"),
    (
        "customer_address.get_all_customer_addresses",
        "/customer_addresses",
        "CustomerAddress",
    ),
    (
        "custom_fields.get_all_custom_fields_collections",
        "/custom_fields_collections",
        "CustomFieldsCollection",
    ),
    ("inventory.get_all_inventory_point", "/inventory", "Inventory"),
    ("inventory.get_all_negative_stock", "/negative_stock", "NegativeStock"),
    (
        "inventory_movements.get_all_inventory_movements",
        "/inventory_movements",
        "InventoryMovement",
    ),
    ("location.get_all_locations", "/locations", "Location"),
    (
        "manufacturing_order.get_all_manufacturing_orders",
        "/manufacturing_orders",
        "ManufacturingOrder",
    ),
    (
        "manufacturing_order.get_all_manufacturing_order_productions",
        "/manufacturing_order_productions",
        "ManufacturingOrderProduction",
    ),
    (
        "manufacturing_order_operation.get_all_manufacturing_order_operation_rows",
        "/manufacturing_order_operation_rows",
        "ManufacturingOrderOperationRow",
    ),
    (
        "manufacturing_order_recipe.get_all_manufacturing_order_recipe_rows",
        "/manufacturing_order_recipe_rows",
        "ManufacturingOrderRecipeRow",
    ),
    ("material.get_all_materials", "/materials", "Material"),
    ("operator.get_all_operators", "/operators", "Operator"),
    ("price_list.get_all_price_lists", "/price_lists", "PriceList"),
    (
        "price_list_customer.get_all_price_list_customers",
        "/price_list_customers",
        "PriceListCustomer",
    ),
    ("price_list_row.get_all_price_list_rows", "/price_list_rows", "PriceListRow"),
    ("product.get_all_products", "/products", "Product"),
    (
        "products.get_all_product_operation_rows",
        "/product_operation_rows",
        "ProductOperationRow",
    ),
    ("purchase_order.find_purchase_orders", "/purchase_orders", "PurchaseOrder"),
    (
        "purchase_order_row.get_all_purchase_order_rows",
        "/purchase_order_rows",
        "PurchaseOrderRow",
    ),
    (
        "purchase_order_accounting_metadata.get_all_purchase_order_accounting_metadata",
        "/purchase_order_accounting_metadata",
        "PurchaseOrderAccountingMetadata",
    ),
    (
        "purchase_order_additional_cost_row.get_purchase_order_additional_cost_rows",
        "/po_additional_cost_rows",
        "PurchaseOrderAdditionalCostRow",
    ),
    ("recipe.get_all_recipes", "/recipes", "Recipe"),
    ("sales_order.get_all_sales_orders", "/sales_orders", "SalesOrder"),
    ("sales_order_row.get_all_sales_order_rows", "/sales_order_rows", "SalesOrderRow"),
    (
        "sales_order_address.get_all_sales_order_addresses",
        "/sales_order_addresses",
        "SalesOrderAddress",
    ),
    (
        "sales_order_fulfillment.get_all_sales_order_fulfillments",
        "/sales_order_fulfillments",
        "SalesOrderFulfillment",
    ),
    ("sales_return.get_all_sales_returns", "/sales_returns", "SalesReturn"),
    (
        "sales_return_row.get_all_sales_return_rows",
        "/sales_return_rows",
        "SalesReturnRow",
    ),
    ("serial_number.get_all_serial_numbers", "/serial_numbers", "SerialNumber"),
    (
        "serial_number.get_all_serial_numbers_stock",
        "/serial_numbers_stock",
        "SerialNumberStock",
    ),
    ("services.get_all_services", "/services", "Service"),
    (
        "stock_adjustment.get_all_stock_adjustments",
        "/stock_adjustments",
        "StockAdjustment",
    ),
    ("stock_transfer.get_all_stock_transfers", "/stock_transfers", "StockTransfer"),
    ("stocktake.get_all_stocktakes", "/stocktakes", "Stocktake"),
    ("stocktake_row.get_all_stocktake_rows", "/stocktake_rows", "StocktakeRow"),
    ("storage_bin.get_all_storage_bins", "/bin_locations", "StorageBinResponse"),
    ("supplier.get_all_suppliers", "/suppliers", "Supplier"),
    (
        "supplier_address.get_supplier_addresses",
        "/supplier_addresses",
        "SupplierAddress",
    ),
    ("tax_rate.get_all_tax_rates", "/tax_rates", "TaxRate"),
    ("user.get_all_users", "/users", "User"),
    ("variant.get_all_variants", "/variants", "VariantResponse"),
    ("webhook.get_all_webhooks", "/webhooks", "Webhook"),
]


def _resolve_schema_properties(
    schema: dict[str, Any], components: dict[str, Any]
) -> set[str]:
    """Resolve all properties from a schema, following allOf/oneOf/$ref chains."""
    properties: set[str] = set()

    if "properties" in schema:
        properties.update(schema["properties"].keys())

    if "allOf" in schema:
        for item in schema["allOf"]:
            if "$ref" in item:
                ref_name = item["$ref"].split("/")[-1]
                ref_schema = components.get("schemas", {}).get(ref_name, {})
                properties.update(_resolve_schema_properties(ref_schema, components))
            else:
                properties.update(_resolve_schema_properties(item, components))

    # For discriminated unions (oneOf/anyOf), collect properties from all variants
    for keyword in ("oneOf", "anyOf"):
        if keyword in schema:
            for item in schema[keyword]:
                if "$ref" in item:
                    ref_name = item["$ref"].split("/")[-1]
                    ref_schema = components.get("schemas", {}).get(ref_name, {})
                    properties.update(
                        _resolve_schema_properties(ref_schema, components)
                    )
                else:
                    properties.update(_resolve_schema_properties(item, components))

    return properties


def _load_spec_schema_properties() -> dict[str, set[str]]:
    """Load all schema property sets from the OpenAPI spec."""
    spec_path = Path(__file__).parent.parent / "docs" / "katana-openapi.yaml"
    with open(spec_path, encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    components = spec.get("components", {})
    schemas = components.get("schemas", {})
    result: dict[str, set[str]] = {}

    for schema_name, schema_def in schemas.items():
        result[schema_name] = _resolve_schema_properties(schema_def, components)

    return result


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("KATANA_API_KEY"),
    reason="Real API credentials not available (set KATANA_API_KEY in .env file)",
)
class TestSchemaValidation:
    """Validate that real API responses match our OpenAPI schema definitions.

    Uses a single shared client to iterate through all list endpoints,
    fetching a small page (limit=5) from each to see objects in different states.
    Compares response fields against our OpenAPI schema and reports all gaps.
    """

    @pytest.fixture(autouse=True)
    def bypass_test_env(self, monkeypatch):
        """Bypass the test environment setup and use real environment variables."""
        load_dotenv(override=True)
        return True

    async def test_all_list_endpoint_schema_fields(self):
        """Validate that API response fields match our schema definitions."""
        api_key = os.getenv("KATANA_API_KEY")
        assert api_key, "KATANA_API_KEY must be set"
        base_url = os.getenv("KATANA_BASE_URL", "https://api.katanamrp.com/v1")
        spec_properties = _load_spec_schema_properties()

        schema_gaps: list[str] = []
        skipped: list[str] = []
        passed: list[str] = []

        # max_retries=1: avoid long exponential backoff on rate limits
        # max_pages=1: disable auto-pagination (we only need the first page)
        async with KatanaClient(
            api_key=api_key, base_url=base_url, max_retries=1, max_pages=1
        ) as client:
            for api_module_path, spec_path, schema_name in LIST_ENDPOINTS:
                module = importlib.import_module(
                    f"katana_public_api_client.api.{api_module_path}"
                )

                # Respect rate limits
                await asyncio.sleep(1.1)

                try:
                    # Some endpoints (e.g. custom_fields_collections) don't
                    # accept limit/page parameters
                    sig = inspect.signature(module.asyncio_detailed)
                    kwargs: dict[str, Any] = {"client": client}
                    if "limit" in sig.parameters:
                        kwargs["limit"] = 5
                    response = await module.asyncio_detailed(**kwargs)
                except (ValueError, KeyError, TypeError, AttributeError) as e:
                    # Parsing errors indicate schema mismatches (e.g. unknown
                    # enum values, missing required fields)
                    schema_gaps.append(f"{schema_name}({spec_path}): parse error: {e}")
                    continue
                except Exception as e:
                    error_msg = str(e).lower()
                    if any(
                        kw in error_msg
                        for kw in [
                            "rate limit",
                            "permission",
                            "forbidden",
                            "unauthorized",
                        ]
                    ):
                        skipped.append(f"{schema_name}({spec_path}): {e}")
                        continue
                    raise

                if response.status_code == 429:
                    skipped.append(f"{schema_name}({spec_path}): rate limited")
                    continue
                if response.status_code in (401, 403):
                    skipped.append(
                        f"{schema_name}({spec_path}): auth {response.status_code}"
                    )
                    continue
                if response.status_code != 200:
                    schema_gaps.append(
                        f"{schema_name}({spec_path}): HTTP {response.status_code}"
                    )
                    continue

                items = unwrap_data(response, default=[])
                if not items:
                    skipped.append(f"{schema_name}({spec_path}): empty collection")
                    continue

                # Collect field names across ALL items for better coverage.
                # to_dict() includes known fields; additional_properties captures
                # any fields the API returned that our model doesn't define.
                response_fields: set[str] = set()
                extra_api_fields: set[str] = set()
                for item in items:
                    if hasattr(item, "to_dict"):
                        response_fields.update(item.to_dict().keys())
                    if hasattr(item, "additional_properties"):
                        extra_api_fields.update(item.additional_properties.keys())

                if not response_fields:
                    skipped.append(f"{schema_name}({spec_path}): no to_dict()")
                    continue

                expected_fields = spec_properties.get(schema_name, set())
                if not expected_fields:
                    schema_gaps.append(
                        f"{schema_name}({spec_path}): schema not found in spec"
                    )
                    continue

                # Fields in the API response but NOT in our schema
                unexpected = (response_fields | extra_api_fields) - expected_fields
                unexpected.discard("additional_properties")

                if unexpected:
                    schema_gaps.append(
                        f"{schema_name}({spec_path}): {len(items)} items, "
                        f"undocumented fields: {sorted(unexpected)}"
                    )
                else:
                    passed.append(f"{schema_name}({spec_path})")

        # Report results
        print("\n  Schema Validation Results:")
        print(f"  Passed: {len(passed)}/{len(LIST_ENDPOINTS)}")
        print(f"  Skipped: {len(skipped)}")
        if skipped:
            for s in skipped:
                print(f"    - {s}")
        if schema_gaps:
            print(f"  Gaps: {len(schema_gaps)}")
            for gap in schema_gaps:
                print(f"    - {gap}")

        assert not schema_gaps, (
            f"Schema validation found {len(schema_gaps)} gap(s):\n"
            + "\n".join(f"  - {g}" for g in schema_gaps)
        )
