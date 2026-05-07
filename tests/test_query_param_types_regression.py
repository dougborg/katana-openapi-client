"""Regression tests for #570 — six query parameter types now match Katana's wire contract.

Each test asserts the *outgoing* request URL matches what Katana actually accepts:
arrays for ``/inventory`` ``variant_id``, literal strings for the boolean-look-alike
flags, and strings for the ID filters that were previously typed as integers.
"""

from collections.abc import Callable

import httpx
import pytest

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.inventory import get_all_inventory_point
from katana_public_api_client.api.material import get_all_materials
from katana_public_api_client.api.product import get_all_products
from katana_public_api_client.api.recipe import get_all_recipes
from katana_public_api_client.api.stocktake import get_all_stocktakes
from katana_public_api_client.models.get_all_materials_batch_tracked import (
    GetAllMaterialsBatchTracked,
)
from katana_public_api_client.models.get_all_products_batch_tracked import (
    GetAllProductsBatchTracked,
)
from katana_public_api_client.models.get_all_products_serial_tracked import (
    GetAllProductsSerialTracked,
)


def _client_with_mock_transport(
    handler: Callable[[httpx.Request], httpx.Response],
) -> KatanaClient:
    """Build a KatanaClient backed by ``httpx.MockTransport`` (caller manages lifetime)."""
    return KatanaClient(
        api_key="test-api-key",
        base_url="https://api.katana.test",
        transport=httpx.MockTransport(handler),
    )


@pytest.mark.asyncio
async def test_inventory_variant_id_serializes_as_array() -> None:
    """``GET /inventory`` ``variant_id`` is an array — multi-valued filter."""
    captured: dict[str, list[tuple[str, str]]] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/inventory"
        captured["params"] = list(request.url.params.multi_items())
        return httpx.Response(200, json={"data": []})

    async with _client_with_mock_transport(handler) as client:
        await get_all_inventory_point.asyncio_detailed(
            client=client,
            variant_id=[101, 202, 303],
        )

    variant_params = [v for k, v in captured["params"] if k == "variant_id"]
    assert variant_params == ["101", "202", "303"]


@pytest.mark.asyncio
async def test_products_batch_tracked_serializes_as_literal_string() -> None:
    """``GET /products`` ``batch_tracked`` accepts the literal string ``"true"`` / ``"false"``."""
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["batch_tracked"] = request.url.params.get("batch_tracked", "")
        return httpx.Response(200, json={"data": []})

    async with _client_with_mock_transport(handler) as client:
        await get_all_products.asyncio_detailed(
            client=client,
            batch_tracked=GetAllProductsBatchTracked.TRUE,
        )

    assert captured["batch_tracked"] == "true"


@pytest.mark.asyncio
async def test_products_serial_tracked_serializes_as_literal_string() -> None:
    """``GET /products`` ``serial_tracked`` accepts the literal string ``"true"`` / ``"false"``."""
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["serial_tracked"] = request.url.params.get("serial_tracked", "")
        return httpx.Response(200, json={"data": []})

    async with _client_with_mock_transport(handler) as client:
        await get_all_products.asyncio_detailed(
            client=client,
            serial_tracked=GetAllProductsSerialTracked.FALSE,
        )

    assert captured["serial_tracked"] == "false"


@pytest.mark.asyncio
async def test_materials_batch_tracked_serializes_as_literal_string() -> None:
    """``GET /materials`` ``batch_tracked`` accepts the literal string ``"true"`` / ``"false"``."""
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["batch_tracked"] = request.url.params.get("batch_tracked", "")
        return httpx.Response(200, json={"data": []})

    async with _client_with_mock_transport(handler) as client:
        await get_all_materials.asyncio_detailed(
            client=client,
            batch_tracked=GetAllMaterialsBatchTracked.TRUE,
        )

    assert captured["batch_tracked"] == "true"


@pytest.mark.asyncio
async def test_recipes_recipe_row_id_serializes_as_string() -> None:
    """``GET /recipes`` ``recipe_row_id`` is a UUID string, not an int."""
    captured: dict[str, str] = {}
    recipe_uuid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

    def handler(request: httpx.Request) -> httpx.Response:
        captured["recipe_row_id"] = request.url.params.get("recipe_row_id", "")
        return httpx.Response(200, json={"data": []})

    async with _client_with_mock_transport(handler) as client:
        await get_all_recipes.asyncio_detailed(
            client=client,
            recipe_row_id=recipe_uuid,
        )

    assert captured["recipe_row_id"] == recipe_uuid


@pytest.mark.asyncio
async def test_stocktakes_stock_adjustment_id_serializes_as_string() -> None:
    """``GET /stocktakes`` ``stock_adjustment_id`` is a string per upstream wire contract."""
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["stock_adjustment_id"] = request.url.params.get(
            "stock_adjustment_id", ""
        )
        return httpx.Response(200, json={"data": []})

    async with _client_with_mock_transport(handler) as client:
        await get_all_stocktakes.asyncio_detailed(
            client=client,
            stock_adjustment_id="42",
        )

    assert captured["stock_adjustment_id"] == "42"
