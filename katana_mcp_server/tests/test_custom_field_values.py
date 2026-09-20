"""Sales-order custom values survive request serialization and validation."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from katana_mcp.tools._modification import FieldChange
from katana_mcp.tools._modification_dispatch import ActionSpec
from katana_mcp.tools.custom_field_values import (
    prepare_custom_field_plan,
    validate_custom_field_values,
)
from katana_mcp.tools.foundation.custom_fields import ListCustomFieldDefinitionsResponse
from katana_mcp.tools.foundation.sales_orders import (
    CreateSalesOrderRequest,
    ModifySalesOrderRequest,
    SOHeaderPatch,
    SORowAdd,
    SORowUpdate,
    _build_create_row_request,
    _build_update_header_request,
    _build_update_row_request,
    _create_sales_order_impl,
    _modify_sales_order_impl,
)
from katana_mcp_server.tests.conftest import create_mock_context

from katana_public_api_client.models_pydantic._generated import (
    CustomFieldDefinition,
    CustomFieldEntityType,
)

FIELD_ID = "00000000-0000-0000-0000-000000000001"


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"custom_fields": None},
        {"custom_fields": {}},
        {"custom_fields": {FIELD_ID: 4}},
    ],
)
@pytest.mark.parametrize("kind", ["header", "add", "update"])
def test_patch_roundtrip_and_wire_preserve_omitted_null_empty(payload, kind):
    if kind == "header":
        original = SOHeaderPatch(**payload)
        rebuilt = SOHeaderPatch.model_validate(original.model_dump(mode="json"))
        wire = _build_update_header_request(patch=rebuilt).to_dict()
    elif kind == "add":
        original = SORowAdd(variant_id=1, quantity=1, **payload)
        rebuilt = SORowAdd.model_validate(original.model_dump(mode="json"))
        wire = _build_create_row_request(so_id=1, row=rebuilt).to_dict()
    else:
        original = SORowUpdate(id=1, **payload)
        rebuilt = SORowUpdate.model_validate(original.model_dump(mode="json"))
        wire = _build_update_row_request(patch=rebuilt).to_dict()
    assert ("custom_fields" in wire) == ("custom_fields" in payload)
    if "custom_fields" in payload:
        assert wire["custom_fields"] == payload["custom_fields"]
    assert ("custom_fields" in rebuilt.model_fields_set) == ("custom_fields" in payload)


@pytest.mark.parametrize(
    "payload", [{}, {"custom_fields": None}, {"custom_fields": {}}]
)
def test_confirm_roundtrip_preserves_header_and_row_custom_field_presence(payload):
    request = ModifySalesOrderRequest.model_validate(
        {"id": 1, "update_header": payload, "update_rows": [{"id": 2, **payload}]}
    )
    rebuilt = ModifySalesOrderRequest.model_validate(request.model_dump(mode="json"))
    assert rebuilt.update_header is not None
    assert rebuilt.update_rows is not None
    assert ("custom_fields" in rebuilt.update_header.model_fields_set) == (
        "custom_fields" in payload
    )
    assert ("custom_fields" in rebuilt.update_rows[0].model_fields_set) == (
        "custom_fields" in payload
    )


def definition(kind="number", entity="SalesOrder", **extra):
    return CustomFieldDefinition.model_validate(
        {
            "id": FIELD_ID,
            "label": "Budget",
            "field_type": kind,
            "entity_type": entity,
            "source": "test",
            **extra,
        }
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("kind", "value", "valid"),
    [
        ("number", 5, True),
        ("number", False, False),
        ("number", "5", False),
        ("number", None, True),
        ("number", [], False),
        ("number", float("inf"), False),
        ("boolean", True, True),
        ("boolean", 1, False),
        ("shortText", "ok", True),
        ("shortText", 3, False),
        ("date", "2026-09-20", True),
        ("date", "2026-99-20", False),
    ],
)
async def test_validation_matches_definition_types(kind, value, valid):
    context, _lifespan = create_mock_context()
    definitions = ListCustomFieldDefinitionsResponse(
        definitions=[definition(kind=kind)], total_count=1
    )
    with patch(
        "katana_mcp.tools.custom_field_values._list_custom_field_definitions_impl",
        AsyncMock(return_value=definitions),
    ):
        warnings = await validate_custom_field_values(
            values=[(CustomFieldEntityType.sales_order, {FIELD_ID: value})],
            context=context,
        )
    assert bool(warnings) is not valid
    assert all(warning.startswith("BLOCK:") for warning in warnings)


@pytest.mark.asyncio
async def test_validation_rejects_deleted_choices_and_wrong_entity():
    context, _lifespan = create_mock_context()
    definitions = ListCustomFieldDefinitionsResponse(
        definitions=[
            definition(
                kind="singleSelect",
                options={
                    "choices": [
                        {"id": 1, "label": "Active"},
                        {"id": 2, "label": "Old", "deleted": True},
                    ]
                },
            )
        ],
        total_count=1,
    )
    with patch(
        "katana_mcp.tools.custom_field_values._list_custom_field_definitions_impl",
        AsyncMock(return_value=definitions),
    ):
        for entity, value in [
            (CustomFieldEntityType.sales_order, 2),
            (CustomFieldEntityType.sales_order_row, 1),
        ]:
            assert await validate_custom_field_values(
                values=[(entity, {FIELD_ID: value})], context=context
            )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "expected,actual,valid",
    [
        (None, None, True),
        (None, {FIELD_ID: 2}, False),
        ({FIELD_ID: 2}, {FIELD_ID: 2, "other": 3}, True),
        ({FIELD_ID: 2}, {FIELD_ID: 3}, False),
        ({}, None, True),
    ],
)
async def test_verifier_checks_merge_and_clear_semantics(expected, actual, valid):
    action = ActionSpec(
        operation="update_header",
        target_id=1,
        diff=[FieldChange(field="custom_fields", old={FIELD_ID: 3}, new=expected)],
    )
    prepare_custom_field_plan(plan=[action])
    assert action.verify is not None
    verified, _details = await action.verify(SimpleNamespace(custom_fields=actual))
    assert verified is valid


@pytest.mark.asyncio
@pytest.mark.parametrize("preview", [True, False])
async def test_invalid_values_block_create_and_modify_before_writes(preview):
    context, _lifespan = create_mock_context()
    with (
        patch(
            "katana_mcp.tools.foundation.sales_orders.validate_custom_field_values",
            AsyncMock(return_value=["BLOCK: Budget requires number values."]),
        ),
        patch(
            "katana_mcp.tools.foundation.sales_orders._fetch_sales_order_attrs",
            AsyncMock(),
        ) as fetch,
    ):
        created = await _create_sales_order_impl(
            request=CreateSalesOrderRequest.model_validate(
                {
                    "customer_id": 1,
                    "order_number": "SO-CF",
                    "items": [{"variant_id": 1, "quantity": 1}],
                    "custom_fields": {FIELD_ID: "bad"},
                    "preview": preview,
                }
            ),
            context=context,
        )
        modified = await _modify_sales_order_impl(
            request=ModifySalesOrderRequest(
                id=1,
                update_header=SOHeaderPatch(custom_fields={FIELD_ID: "bad"}),
                preview=preview,
            ),
            context=context,
        )
        fetch.assert_not_awaited()
    assert created.is_preview and modified.is_preview
    assert created.warnings[0].startswith("BLOCK:")
    assert modified.warnings[0].startswith("BLOCK:")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"custom_fields": None},
        {"custom_fields": {}},
        {"custom_fields": {FIELD_ID: 7}},
    ],
)
async def test_header_apply_and_cache_preserve_clear_merge_and_omission(
    context_with_typed_cache, payload
):
    from unittest.mock import MagicMock

    from katana_public_api_client.models import SalesOrder
    from katana_public_api_client.models_pydantic._generated import CachedSalesOrder

    context, _lifespan, cache = context_with_typed_cache
    old_fields = {FIELD_ID: 1, "00000000-0000-0000-0000-000000000002": 2}
    current_data = {
        "id": 1,
        "order_no": "SO-CF",
        "customer_id": 1,
        "location_id": 1,
        "status": "PENDING",
        "sales_order_rows": [],
        "custom_fields": old_fields,
    }
    current = SalesOrder.from_dict(current_data)
    expected = (
        old_fields
        if "custom_fields" not in payload
        else (
            None
            if payload["custom_fields"] is None
            else {**old_fields, **payload["custom_fields"]}
        )
    )
    updated = SalesOrder.from_dict(
        {**current_data, "order_no": "SO-CF-NEW", "custom_fields": expected}
    )
    with (
        patch(
            "katana_mcp.tools.foundation.sales_orders.validate_custom_field_values",
            AsyncMock(return_value=[]),
        ),
        patch(
            "katana_mcp.tools.foundation.sales_orders._fetch_sales_order_attrs",
            AsyncMock(return_value=current),
        ),
        patch(
            "katana_mcp.tools.foundation.sales_orders.api_update_sales_order.asyncio_detailed",
            AsyncMock(return_value=MagicMock(status_code=200, parsed=updated)),
        ) as endpoint,
    ):
        result = await _modify_sales_order_impl(
            request=ModifySalesOrderRequest(
                id=1,
                preview=False,
                update_header=SOHeaderPatch(order_no="SO-CF-NEW", **payload),
            ),
            context=context,
        )
    assert result.actions[0].succeeded is True
    assert result.actions[0].verified is True
    wire = endpoint.call_args.kwargs["body"].to_dict()
    assert ("custom_fields" in wire) == ("custom_fields" in payload)
    async with cache.session() as session:
        row = await session.get(CachedSalesOrder, 1)
        assert row is not None
        assert row.custom_fields == expected
