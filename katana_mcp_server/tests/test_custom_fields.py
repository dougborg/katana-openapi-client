"""Custom-field discovery preserves UUID keys and historical choices."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from katana_mcp.resources.help import get_help_custom_fields
from katana_mcp.tools.foundation.custom_fields import (
    GetCustomFieldDefinitionRequest,
    ListCustomFieldDefinitionsRequest,
    _get_custom_field_definition_impl,
    _list_custom_field_definitions_impl,
)
from katana_mcp.typed_cache import force_resync
from katana_mcp.typed_cache.sync import ensure_custom_field_definitions_synced
from sqlmodel import select

from katana_public_api_client.models import CustomFieldDefinition
from katana_public_api_client.models_pydantic._generated import (
    CachedCustomFieldDefinition,
    CustomFieldEntityType,
)

FIELD_ID = UUID("00000000-0000-0000-0000-000000000001")
ROW_FIELD_ID = UUID("00000000-0000-0000-0000-000000000002")


def definition_payload(**overrides):
    return {
        "id": str(FIELD_ID),
        "label": "Sales Rep",
        "field_type": "singleSelect",
        "entity_type": "SalesOrder",
        "source": "test",
        "options": {
            "choices": [
                {"id": 1, "label": "Alex"},
                {"id": 2, "label": "Retired", "deleted": True},
            ]
        },
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
        **overrides,
    }


def list_response(*payloads):
    response = MagicMock(status_code=200)
    response.parsed.data = [CustomFieldDefinition.from_dict(p) for p in payloads]
    return response


@pytest.mark.asyncio
async def test_sync_uuid_definition_choices_and_incremental_update(typed_cache_engine):
    endpoint = AsyncMock(return_value=list_response(definition_payload()))
    with patch(
        "katana_mcp.typed_cache.sync.get_all_custom_field_definitions.asyncio_detailed",
        endpoint,
    ):
        await ensure_custom_field_definitions_synced(
            client=MagicMock(), cache=typed_cache_engine
        )
        assert "include_deleted" not in endpoint.call_args.kwargs
        async with typed_cache_engine.session() as session:
            row = await session.get(CachedCustomFieldDefinition, FIELD_ID)
            assert row is not None
            assert row.id == FIELD_ID
            assert row.options is not None
            assert row.options["choices"][1]["deleted"] is True
        endpoint.return_value = list_response(
            definition_payload(label="Account Manager")
        )
        await ensure_custom_field_definitions_synced(
            client=MagicMock(), cache=typed_cache_engine
        )
        assert "updated_at_min" in endpoint.call_args.kwargs
        async with typed_cache_engine.session() as session:
            rows = (await session.exec(select(CachedCustomFieldDefinition))).all()
            assert len(rows) == 1
            assert rows[0].label == "Account Manager"


@pytest.mark.asyncio
async def test_discovery_filters_deleted_and_groups_help(context_with_typed_cache):
    context, _lifespan, _cache = context_with_typed_cache
    deleted_id = "00000000-0000-0000-0000-000000000003"
    endpoint = AsyncMock(
        return_value=list_response(
            definition_payload(),
            definition_payload(
                id=str(ROW_FIELD_ID),
                entity_type="SalesOrderRow",
                label="Row | label",
                options=None,
                field_type="shortText",
            ),
            definition_payload(id=deleted_id, deleted_at="2026-01-02T00:00:00Z"),
        )
    )
    with patch(
        "katana_mcp.typed_cache.sync.get_all_custom_field_definitions.asyncio_detailed",
        endpoint,
    ):
        result = await _list_custom_field_definitions_impl(
            request=ListCustomFieldDefinitionsRequest(), context=context
        )
        assert result.total_count == 2
        options = result.definitions[0].options
        assert options is not None
        assert options.choices[1].label == "Retired"
        filtered = await _list_custom_field_definitions_impl(
            request=ListCustomFieldDefinitionsRequest(
                entity_type=CustomFieldEntityType.sales_order_row
            ),
            context=context,
        )
        assert [d.id for d in filtered.definitions] == [ROW_FIELD_ID]
        help_text = await get_help_custom_fields(context=context)
        assert "## SalesOrder\n" in help_text
        assert "## SalesOrderRow\n" in help_text
        assert "1: Alex" in help_text
        assert "Retired" not in help_text
        assert "1 deleted choices" in help_text
        assert "Row \\| label" in help_text
        assert "customFields.<uuid>" in help_text
        all_definitions = await _list_custom_field_definitions_impl(
            request=ListCustomFieldDefinitionsRequest(include_deleted=True),
            context=context,
        )
        assert all_definitions.total_count == 3


@pytest.mark.asyncio
async def test_get_definition_fetches_live_and_writes_through(context_with_typed_cache):
    context, _lifespan, cache = context_with_typed_cache
    response = MagicMock(
        status_code=200, parsed=CustomFieldDefinition.from_dict(definition_payload())
    )
    with patch(
        "katana_mcp.tools.foundation.custom_fields.api_get.asyncio_detailed",
        AsyncMock(return_value=response),
    ) as endpoint:
        result = await _get_custom_field_definition_impl(
            request=GetCustomFieldDefinitionRequest(definition_id=FIELD_ID),
            context=context,
        )
    assert result.id == FIELD_ID
    assert endpoint.call_args.kwargs["id"] == FIELD_ID
    async with cache.session() as session:
        cached = await session.get(CachedCustomFieldDefinition, FIELD_ID)
        assert cached is not None
        assert cached.label == "Sales Rep"


@pytest.mark.asyncio
async def test_rebuild_removes_absent_uuid_definitions(typed_cache_engine):
    endpoint = AsyncMock(return_value=list_response(definition_payload()))
    with patch(
        "katana_mcp.typed_cache.sync.get_all_custom_field_definitions.asyncio_detailed",
        endpoint,
    ):
        await ensure_custom_field_definitions_synced(
            client=MagicMock(), cache=typed_cache_engine
        )
        endpoint.return_value = list_response()
        await force_resync(
            client=MagicMock(),
            cache=typed_cache_engine,
            entity_key="custom_field_definition",
        )
        async with typed_cache_engine.session() as session:
            assert await session.get(CachedCustomFieldDefinition, FIELD_ID) is None
