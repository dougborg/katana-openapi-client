"""Material prices use variant PATCH without repeating a successful creation."""

from unittest.mock import AsyncMock

import pytest
from katana_mcp.tools.foundation.catalog import (
    CreateMaterialRequest,
    _create_material_impl,
)
from katana_mcp.tools.foundation.items import (
    CreateItemRequest,
    ItemType,
    _create_item_impl,
)
from katana_mcp_server.tests.conftest import mock_item
from katana_mcp_server.tests.tools.test_catalog import create_mock_context
from pydantic import ValidationError

from katana_public_api_client.domain import KatanaVariant


def prepare():
    context, services = create_mock_context()
    services.client.materials.create = AsyncMock(
        return_value=mock_item(id=42, name="Steel")
    )
    variant = KatanaVariant(id=73, sku="STEEL", material_id=42, sales_price=0)
    services.client.variants.list = AsyncMock(return_value=[variant])
    services.client.variants.update = AsyncMock(return_value=variant)
    return context, services, variant


async def create(entry, context, price):
    if entry == "dedicated":
        return await _create_material_impl(
            CreateMaterialRequest(name="Steel", sku="STEEL", sales_price=price), context
        )
    return await _create_item_impl(
        CreateItemRequest(
            type=ItemType.MATERIAL, name="Steel", sku="STEEL", sales_price=price
        ),
        context,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("entry", ["dedicated", "generic"])
@pytest.mark.parametrize("price", [None, 0, 12.34])
async def test_material_price_uses_followup_patch(entry, price):
    context, services, variant = prepare()
    services.client.variants.update.return_value = variant.model_copy(
        update={"sales_price": price}
    )
    result = await create(entry, context, price)
    assert result.success
    services.client.materials.create.assert_awaited_once()
    body = services.client.materials.create.call_args.args[0].to_dict()
    assert "sales_price" not in body["variants"][0]
    if price is None:
        services.client.variants.list.assert_not_called()
        services.client.variants.update.assert_not_called()
    else:
        services.client.variants.list.assert_awaited_once_with(material_id=42)
        services.client.variants.update.assert_awaited_once()
        patch = services.client.variants.update.call_args.kwargs
        assert patch["variant_id"] == 73
        assert patch["variant_data"].to_dict() == {"sales_price": price}
        assert result.variant_id == 73
        assert result.variants[0].sales_price == price


@pytest.mark.asyncio
@pytest.mark.parametrize("entry", ["dedicated", "generic"])
@pytest.mark.parametrize("failure", ["lookup", "patch", "mismatch"])
async def test_material_partial_failure_retains_creation_and_recovery_ids(
    entry, failure
):
    context, services, _variant = prepare()
    if failure == "lookup":
        services.client.variants.list.side_effect = RuntimeError("Lookup failed")
    elif failure == "patch":
        services.client.variants.update.side_effect = RuntimeError("PATCH failed")
    result = await create(entry, context, 12.34)
    assert result.success is False
    assert result.id == 42
    assert "Do not repeat creation" in result.message
    assert "material 42" in result.warnings[0].lower()
    if failure != "lookup":
        assert result.variant_id == 73
        assert "variant 73" in result.warnings[0]
    else:
        services.client.variants.update.assert_not_called()
    services.client.materials.create.assert_awaited_once()
    assert '"success":false' in result.model_dump_json()


@pytest.mark.parametrize("price", [-1, float("inf"), float("nan")])
def test_invalid_price_rejected_before_creation(price):
    with pytest.raises(ValidationError):
        CreateMaterialRequest(name="Steel", sku="STEEL", sales_price=price)
    with pytest.raises(ValidationError):
        CreateItemRequest(
            type=ItemType.MATERIAL, name="Steel", sku="STEEL", sales_price=price
        )


@pytest.mark.asyncio
async def test_variant_discovery_never_updates_another_material():
    context, services, variant = prepare()
    services.client.variants.list.return_value = [
        variant.model_copy(update={"material_id": 999})
    ]
    result = await create("dedicated", context, 12.34)
    assert result.id == 42
    assert not result.success
    services.client.variants.update.assert_not_called()
