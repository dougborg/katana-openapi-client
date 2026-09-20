"""Discover custom-field definitions and their choice identifiers."""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from mcp.types import ToolAnnotations
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import select

from katana_mcp.logging import observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools.decorators import cache_read
from katana_mcp.tools.tool_result_utils import make_json_result
from katana_mcp.typed_cache import ENTITY_SPECS, merge_filtered_fetch
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_public_api_client.api.custom_fields import (
    get_custom_field_definition as api_get,
)
from katana_public_api_client.models.custom_field_definition import (
    CustomFieldDefinition as AttrsDefinition,
)
from katana_public_api_client.models_pydantic._generated import (
    CachedCustomFieldDefinition,
    CustomFieldDefinition,
    CustomFieldEntityType,
)
from katana_public_api_client.utils import unwrap_as


class ListCustomFieldDefinitionsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_type: CustomFieldEntityType | None = Field(
        default=None,
        description="Only definitions for this resource type; omit for all.",
    )
    include_deleted: bool = Field(
        default=False, description="Include cached deleted definitions."
    )


class ListCustomFieldDefinitionsResponse(BaseModel):
    definitions: list[CustomFieldDefinition]
    total_count: int


class GetCustomFieldDefinitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    definition_id: UUID = Field(description="Custom-field definition UUID.")


def _definition_from_cache(row: CachedCustomFieldDefinition) -> CustomFieldDefinition:
    """Restore SQLite UTC timestamps and validate nested JSON choice data."""
    data = {}
    for field in CustomFieldDefinition.model_fields:
        value = getattr(row, field)
        if isinstance(value, datetime) and value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        data[field] = value
    return CustomFieldDefinition.model_validate(obj=data)


@cache_read(CachedCustomFieldDefinition)
async def _list_custom_field_definitions_impl(
    request: ListCustomFieldDefinitionsRequest, context: Context
) -> ListCustomFieldDefinitionsResponse:
    services = get_services(context)
    async with services.typed_cache.session() as session:
        rows = (await session.exec(statement=select(CachedCustomFieldDefinition))).all()
    definitions = [
        _definition_from_cache(row=row)
        for row in rows
        if (request.include_deleted or row.deleted_at is None)
        and (request.entity_type is None or row.entity_type == request.entity_type)
    ]
    definitions.sort(
        key=lambda definition: (
            definition.entity_type,
            definition.label,
            str(definition.id),
        )
    )
    return ListCustomFieldDefinitionsResponse(
        definitions=definitions, total_count=len(definitions)
    )


async def _get_custom_field_definition_impl(
    request: GetCustomFieldDefinitionRequest, context: Context
) -> CustomFieldDefinition:
    """Fetch authoritative definition detail and write it through to the cache."""
    services = get_services(context)
    response = await api_get.asyncio_detailed(
        id=request.definition_id, client=services.client
    )
    definition = unwrap_as(response=response, expected_type=AttrsDefinition)
    await merge_filtered_fetch(
        cache=services.typed_cache,
        spec=ENTITY_SPECS["custom_field_definition"],
        attrs_objs=[definition],
    )
    return CustomFieldDefinition.from_attrs(attrs_obj=definition)


@observe_tool
@unpack_pydantic_params
async def list_custom_field_definitions(
    request: Annotated[ListCustomFieldDefinitionsRequest, Unpack()], context: Context
) -> ToolResult:
    """List custom-field UUIDs, labels, types, and choices from the synced cache.

    Discover definitions before reading or writing UUID-keyed custom_fields.
    Choice IDs are stored values; labels explain them. Deleted choices remain
    available for resolving historical values. Availability depends on the
    account's custom-field features. See katana://help/custom-fields.
    """
    response = await _list_custom_field_definitions_impl(
        request=request, context=context
    )
    return make_json_result(response=response)


@observe_tool
@unpack_pydantic_params
async def get_custom_field_definition(
    request: Annotated[GetCustomFieldDefinitionRequest, Unpack()], context: Context
) -> ToolResult:
    """Get a custom-field definition by UUID with a live API call.

    Returns its label, resource type, field type, and complete choice history.
    Refreshes the cached definition for subsequent discovery calls.
    """
    response = await _get_custom_field_definition_impl(request=request, context=context)
    return make_json_result(response=response)


def register_tools(mcp: FastMCP) -> None:
    """Register custom-field discovery tools."""
    annotations = ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )
    mcp.tool(tags={"custom-fields", "read"}, annotations=annotations)(
        list_custom_field_definitions
    )
    mcp.tool(tags={"custom-fields", "read"}, annotations=annotations)(
        get_custom_field_definition
    )
