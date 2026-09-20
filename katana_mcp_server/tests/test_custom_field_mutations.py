"""Definition mutation previews, choice retention, and immediate cache writes."""

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
import time_machine
from katana_mcp.tools.foundation.custom_field_mutations import (
    CreateCustomFieldDefinitionRequest,
    DeleteCustomFieldDefinitionRequest,
    UpdateCustomFieldDefinitionRequest,
    _create_custom_field_definition_impl,
    _delete_custom_field_definition_impl,
    _merge_choices,
    _to_tool_result,
    _update_custom_field_definition_impl,
)
from pydantic import ValidationError

from katana_public_api_client.models import CustomFieldDefinition as AttrsDefinition
from katana_public_api_client.models_pydantic._generated import (
    CachedCustomFieldDefinition,
    CustomFieldDefinition,
)

FIELD_ID = UUID("00000000-0000-0000-0000-000000000001")


def current_definition():
    return CustomFieldDefinition.model_validate(
        {
            "id": FIELD_ID,
            "label": "Rep",
            "field_type": "singleSelect",
            "entity_type": "SalesOrder",
            "source": "test",
            "description": "Keep me",
            "options": {
                "choices": [
                    {"id": 1, "label": "A"},
                    {"id": 2, "label": "B"},
                    {"id": 3, "label": "C"},
                    {"id": 4, "label": "Old", "deleted": True},
                ]
            },
        }
    )


def response_for(definition):
    return MagicMock(
        status_code=200,
        parsed=AttrsDefinition.from_dict(
            definition.model_dump(mode="json", exclude_none=True)
        ),
    )


def test_desired_choices_keep_ids_and_retire_missing_labels():
    result = _merge_choices(
        current=current_definition(),
        request=UpdateCustomFieldDefinitionRequest(
            definition_id=FIELD_ID, choices=["A", "B", "D"]
        ),
    )
    assert result == [
        {"id": 1, "label": "A", "deleted": False},
        {"id": 2, "label": "B", "deleted": False},
        {"id": 3, "label": "C", "deleted": True},
        {"id": 4, "label": "Old", "deleted": True},
        {"label": "D"},
    ]


def test_delta_choices_preserve_untouched_choices():
    request = UpdateCustomFieldDefinitionRequest.model_validate(
        {"definition_id": FIELD_ID, "choice_changes": {"add": ["D"], "remove": [2]}}
    )
    result = _merge_choices(current=current_definition(), request=request)
    assert result[0] == {"id": 1, "label": "A"}
    assert result[1]["deleted"] is True
    assert result[2] == {"id": 3, "label": "C"}
    assert result[3]["deleted"] is True
    assert result[4] == {"label": "D"}


@pytest.mark.parametrize(
    "changes",
    [
        {"choice_changes": {"remove": [999]}},
        {"choice_changes": {"add": ["A"]}},
        {"choices": ["A", "A"]},
        {"choices": [""]},
    ],
)
def test_unsafe_choice_edits_fail(changes):
    request = UpdateCustomFieldDefinitionRequest.model_validate(
        {"definition_id": FIELD_ID, **changes}
    )
    with pytest.raises(ValueError):
        _merge_choices(current=current_definition(), request=request)


def test_unstructured_partial_choice_objects_are_rejected():
    with pytest.raises(ValidationError):
        UpdateCustomFieldDefinitionRequest.model_validate(
            {"definition_id": FIELD_ID, "choices": [{"id": 1, "label": "A"}]}
        )


@pytest.mark.asyncio
async def test_create_preview_never_writes_and_apply_updates_cache(
    context_with_typed_cache,
):
    context, _lifespan, cache = context_with_typed_cache
    request = CreateCustomFieldDefinitionRequest.model_validate(
        {
            "label": "Rep",
            "field_type": "singleSelect",
            "entity_type": "SalesOrder",
            "choices": ["A", "B", "C"],
        }
    )
    with patch(
        "katana_mcp.tools.foundation.custom_field_mutations.api_create.asyncio_detailed",
        AsyncMock(return_value=response_for(current_definition())),
    ) as endpoint:
        preview = await _create_custom_field_definition_impl(
            request=request, context=context
        )
        assert preview.is_preview
        endpoint.assert_not_awaited()
        applied = await _create_custom_field_definition_impl(
            request=request.model_copy(update={"preview": False}), context=context
        )
        assert not applied.is_preview
        assert endpoint.call_args.kwargs["body"].to_dict()["source"] == "katana-mcp"
    async with cache.session() as session:
        assert await session.get(CachedCustomFieldDefinition, FIELD_ID) is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("description", [None, "Revised"])
async def test_update_preview_preserves_explicit_description_and_all_choices(
    context_with_typed_cache, description
):
    context, _lifespan, _cache = context_with_typed_cache
    request = UpdateCustomFieldDefinitionRequest(
        definition_id=FIELD_ID, choices=["A", "B", "D"], description=description
    )
    with (
        patch(
            "katana_mcp.tools.foundation.custom_fields.api_get.asyncio_detailed",
            AsyncMock(return_value=response_for(current_definition())),
        ),
        patch(
            "katana_mcp.tools.foundation.custom_field_mutations.api_update.asyncio_detailed",
            AsyncMock(),
        ) as endpoint,
    ):
        preview = await _update_custom_field_definition_impl(
            request=request, context=context
        )
        endpoint.assert_not_awaited()
    assert preview.payload["description"] == description
    assert preview.payload["options"]["choices"][2]["deleted"] is True
    card = _to_tool_result(
        response=preview, request=request, tool="update_custom_field_definition"
    )
    assert card.structured_content is not None
    assert card.structured_content["state"]["response"]["payload"] == preview.payload
    encoded = json.dumps(card.structured_content)
    assert "Confirm & Update" in encoded
    assert '"preview": false' in encoded
    roundtrip = UpdateCustomFieldDefinitionRequest.model_validate(
        request.model_dump(mode="json")
    )
    assert roundtrip.model_fields_set == request.model_fields_set | {"preview"}
    assert "label" not in roundtrip.model_fields_set


@pytest.mark.asyncio
async def test_update_apply_writes_through_response(context_with_typed_cache):
    context, _lifespan, cache = context_with_typed_cache
    request = UpdateCustomFieldDefinitionRequest(
        definition_id=FIELD_ID, label="New", preview=False
    )
    updated = current_definition().model_copy(update={"label": "New"})
    with (
        patch(
            "katana_mcp.tools.foundation.custom_fields.api_get.asyncio_detailed",
            AsyncMock(return_value=response_for(current_definition())),
        ),
        patch(
            "katana_mcp.tools.foundation.custom_field_mutations.api_update.asyncio_detailed",
            AsyncMock(return_value=response_for(updated)),
        ) as endpoint,
    ):
        await _update_custom_field_definition_impl(request=request, context=context)
        assert endpoint.call_args.kwargs["body"].to_dict() == {"label": "New"}
    async with cache.session() as session:
        row = await session.get(CachedCustomFieldDefinition, FIELD_ID)
        assert row.label == "New"


@pytest.mark.asyncio
async def test_delete_preview_and_apply_tombstone(context_with_typed_cache):
    context, _lifespan, cache = context_with_typed_cache
    request = DeleteCustomFieldDefinitionRequest(definition_id=FIELD_ID)
    with (
        patch(
            "katana_mcp.tools.foundation.custom_fields.api_get.asyncio_detailed",
            AsyncMock(return_value=response_for(current_definition())),
        ),
        patch(
            "katana_mcp.tools.foundation.custom_field_mutations.api_delete.asyncio_detailed",
            AsyncMock(return_value=MagicMock(status_code=204)),
        ) as endpoint,
    ):
        await _delete_custom_field_definition_impl(request=request, context=context)
        endpoint.assert_not_awaited()
        with time_machine.travel(datetime(2026, 9, 20, tzinfo=UTC), tick=False):
            applied = await _delete_custom_field_definition_impl(
                request=request.model_copy(update={"preview": False}), context=context
            )
        assert applied.definition is not None
        assert applied.definition.deleted_at == datetime(2026, 9, 20, tzinfo=UTC)
    async with cache.session() as session:
        row = await session.get(CachedCustomFieldDefinition, FIELD_ID)
        assert row.deleted_at == datetime(2026, 9, 20)
