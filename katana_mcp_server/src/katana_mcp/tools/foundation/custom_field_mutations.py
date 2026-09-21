"""Preview and apply custom-field definition changes without losing choice IDs."""

from datetime import UTC, datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from mcp.types import ToolAnnotations
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    model_serializer,
    model_validator,
)

from katana_mcp.logging import observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools.foundation.custom_fields import (
    GetCustomFieldDefinitionRequest,
    _get_custom_field_definition_impl,
)
from katana_mcp.tools.tool_result_utils import UI_META, make_tool_result
from katana_mcp.typed_cache import ENTITY_SPECS, merge_filtered_fetch
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_public_api_client.api.custom_fields import (
    create_custom_field_definition as api_create,
    delete_custom_field_definition as api_delete,
    update_custom_field_definition as api_update,
)
from katana_public_api_client.models import (
    CreateCustomFieldDefinitionRequest as APICreateRequest,
    CustomFieldDefinition as AttrsDefinition,
    UpdateCustomFieldDefinitionRequest as APIUpdateRequest,
)
from katana_public_api_client.models_pydantic._generated import (
    CustomFieldDefinition,
    CustomFieldEntityType,
    CustomFieldType,
)
from katana_public_api_client.utils import unwrap, unwrap_as


class DefinitionMutationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    preview: bool = Field(
        default=True,
        description="Preview changes first; set false to apply the reviewed changes.",
    )

    @model_serializer(mode="wrap")
    def preserve_omitted_fields(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, Any]:
        """Keep explicit null distinct from omission through Confirm arguments."""
        data = handler(self)
        return {
            key: value
            for key, value in data.items()
            if key in self.model_fields_set or key == "preview"
        }


class CreateCustomFieldDefinitionRequest(DefinitionMutationRequest):
    label: str = Field(min_length=1, max_length=255)
    field_type: CustomFieldType
    entity_type: CustomFieldEntityType
    source: str = Field(default="katana-mcp", min_length=1, max_length=255)
    description: str | None = None
    choices: list[str] | None = Field(
        default=None,
        description="Choice labels, required for singleSelect. The server assigns IDs.",
    )

    @model_validator(mode="after")
    def validate_choices(self):
        if self.field_type == CustomFieldType.single_select:
            if not self.choices:
                raise ValueError("singleSelect requires at least one choice label")
            _validate_labels(labels=self.choices)
        elif self.choices is not None:
            raise ValueError("choices are only supported for singleSelect")
        return self


class ChoiceChanges(BaseModel):
    model_config = ConfigDict(extra="forbid")
    add: list[str] = Field(
        default_factory=list, description="New choice labels to append."
    )
    remove: list[int] = Field(
        default_factory=list, description="Existing choice IDs to soft-delete."
    )


class UpdateCustomFieldDefinitionRequest(DefinitionMutationRequest):
    definition_id: UUID
    label: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(
        default=None,
        description="Omit to preserve; explicit null clears the description.",
    )
    choices: list[str] | None = Field(
        default=None,
        description="Desired complete set of active labels. Omitted labels are soft-deleted. For partial changes use choice_changes.",
    )
    choice_changes: ChoiceChanges | None = Field(
        default=None,
        description="Explicit add/remove delta instead of a desired complete choices list.",
    )

    @model_validator(mode="after")
    def validate_update(self):
        if "label" in self.model_fields_set and self.label is None:
            raise ValueError("label cannot be null")
        if self.choices is not None and self.choice_changes is not None:
            raise ValueError(
                "Use either choices (complete desired state) or choice_changes (add/remove delta)"
            )
        if "choices" in self.model_fields_set and self.choices is None:
            raise ValueError(
                "Use choices=[] to retire all choices, or omit choices to preserve them"
            )
        if "choice_changes" in self.model_fields_set and self.choice_changes is None:
            raise ValueError(
                "Omit choice_changes to preserve choices; null is not a delta"
            )
        if self.choice_changes is not None and not (
            self.choice_changes.add or self.choice_changes.remove
        ):
            raise ValueError("choice_changes requires at least one addition or removal")
        if not self.model_fields_set.intersection(
            {"label", "description", "choices", "choice_changes"}
        ):
            raise ValueError("Supply at least one definition change")
        return self


class DeleteCustomFieldDefinitionRequest(DefinitionMutationRequest):
    definition_id: UUID


class DefinitionMutationResponse(BaseModel):
    is_preview: bool
    operation: Literal["create", "update", "delete"]
    definition: CustomFieldDefinition | None = None
    payload: dict[str, Any]
    changes: list[str]


def _validate_labels(labels: list[str]) -> None:
    if any(not label.strip() for label in labels):
        raise ValueError("Choice labels cannot be blank")
    if len(set(labels)) != len(labels):
        raise ValueError("Choice labels must be unique")


def _merge_choices(
    *, current: CustomFieldDefinition, request: UpdateCustomFieldDefinitionRequest
) -> list[dict[str, Any]]:
    if current.field_type != CustomFieldType.single_select:
        raise ValueError("Choices can only be changed for singleSelect definitions")
    existing = (
        [
            choice.model_dump(mode="json", exclude_none=True)
            for choice in current.options.choices
        ]
        if current.options
        else []
    )
    labels = [choice["label"] for choice in existing]
    _validate_labels(labels=labels)
    if any("id" not in choice for choice in existing):
        raise ValueError(
            "Existing choices are missing IDs; cannot safely update the definition"
        )
    if request.choices is not None:
        _validate_labels(labels=request.choices)
        wanted = set(request.choices)
        merged = [
            {**choice, "deleted": choice["label"] not in wanted} for choice in existing
        ]
        merged.extend(
            {"label": label} for label in request.choices if label not in labels
        )
        return merged
    delta = request.choice_changes
    if delta is None:
        return existing
    _validate_labels(labels=delta.add)
    if set(delta.add).intersection(labels):
        raise ValueError(
            "Added labels already exist; use choices with the complete desired state to reactivate a retired label"
        )
    unknown = set(delta.remove) - {choice["id"] for choice in existing}
    if unknown:
        raise ValueError(f"Unknown choice IDs to remove: {sorted(unknown)}")
    merged = [
        {**choice, "deleted": True} if choice["id"] in delta.remove else choice
        for choice in existing
    ]
    merged.extend({"label": label} for label in delta.add)
    return merged


async def _cache_definition(
    *, definition: AttrsDefinition, context: Context
) -> CustomFieldDefinition:
    services = get_services(context)
    await merge_filtered_fetch(
        cache=services.typed_cache,
        spec=ENTITY_SPECS["custom_field_definition"],
        attrs_objs=[definition],
    )
    return CustomFieldDefinition.from_attrs(attrs_obj=definition)


async def _create_custom_field_definition_impl(
    request: CreateCustomFieldDefinitionRequest, context: Context
) -> DefinitionMutationResponse:
    payload: dict[str, Any] = {
        "label": request.label,
        "field_type": request.field_type.value,
        "entity_type": request.entity_type.value,
        "source": request.source,
    }
    if "description" in request.model_fields_set:
        payload["description"] = request.description
    if request.choices is not None:
        payload["options"] = {
            "choices": [{"label": label} for label in request.choices]
        }
    definition = None
    if not request.preview:
        response = await api_create.asyncio_detailed(
            client=get_services(context).client,
            body=APICreateRequest.from_dict(payload),
        )
        definition = await _cache_definition(
            definition=unwrap_as(response=response, expected_type=AttrsDefinition),
            context=context,
        )
    return DefinitionMutationResponse(
        is_preview=request.preview,
        operation="create",
        definition=definition,
        payload=payload,
        changes=[
            f"New custom field: {request.label} ({request.field_type}) for {request.entity_type}"
        ],
    )


async def _update_custom_field_definition_impl(
    request: UpdateCustomFieldDefinitionRequest, context: Context
) -> DefinitionMutationResponse:
    current = await _get_custom_field_definition_impl(
        request=GetCustomFieldDefinitionRequest(definition_id=request.definition_id),
        context=context,
    )
    if current.deleted_at is not None:
        raise ValueError("This definition has been deleted")
    payload: dict[str, Any] = {}
    changes = []
    for name in ("label", "description"):
        if name in request.model_fields_set:
            value = getattr(request, name)
            payload[name] = value
            changes.append(f"{name}: {getattr(current, name)} → {value}")
    if request.choices is not None or request.choice_changes is not None:
        choices = _merge_choices(current=current, request=request)
        payload["options"] = {"choices": choices}
        before = (
            {choice.id: choice for choice in current.options.choices}
            if current.options
            else {}
        )
        added = sum("id" not in choice for choice in choices)
        retired = sum(
            bool(choice.get("deleted")) and not bool(before[choice["id"]].deleted)
            for choice in choices
            if "id" in choice
        )
        changes.append(f"Add {added} choices; retire {retired} choices")
    definition = current
    if not request.preview:
        response = await api_update.asyncio_detailed(
            id=request.definition_id,
            client=get_services(context).client,
            body=APIUpdateRequest.from_dict(payload),
        )
        definition = await _cache_definition(
            definition=unwrap_as(response=response, expected_type=AttrsDefinition),
            context=context,
        )
    return DefinitionMutationResponse(
        is_preview=request.preview,
        operation="update",
        definition=definition,
        payload=payload,
        changes=changes,
    )


async def _delete_custom_field_definition_impl(
    request: DeleteCustomFieldDefinitionRequest, context: Context
) -> DefinitionMutationResponse:
    current = await _get_custom_field_definition_impl(
        request=GetCustomFieldDefinitionRequest(definition_id=request.definition_id),
        context=context,
    )
    if not request.preview:
        response = await api_delete.asyncio_detailed(
            id=request.definition_id, client=get_services(context).client
        )
        if response.status_code != 204:
            unwrap(response=response)
            raise ValueError(f"Unexpected deletion response: {response.status_code}")
        tombstone = current.model_copy(update={"deleted_at": datetime.now(tz=UTC)})
        current = await _cache_definition(
            definition=tombstone.to_attrs(), context=context
        )
    return DefinitionMutationResponse(
        is_preview=request.preview,
        operation="delete",
        definition=current,
        payload={"id": str(request.definition_id)},
        changes=[
            f"Custom field {current.label} will be deleted; values will no longer appear on records"
        ],
    )


def _to_tool_result(
    *,
    response: DefinitionMutationResponse,
    request: DefinitionMutationRequest,
    tool: str,
) -> ToolResult:
    from katana_mcp.tools.custom_field_ui import build_definition_mutation_ui

    return make_tool_result(
        response=response,
        ui=build_definition_mutation_ui(
            response=response.model_dump(mode="json"), request=request, tool=tool
        ),
    )


@observe_tool
@unpack_pydantic_params
async def create_custom_field_definition(
    request: Annotated[CreateCustomFieldDefinitionRequest, Unpack()], context: Context
) -> ToolResult:
    """Create a custom-field definition after reviewing its preview. Availability depends on account features."""
    response = await _create_custom_field_definition_impl(
        request=request, context=context
    )
    return _to_tool_result(
        response=response, request=request, tool="create_custom_field_definition"
    )


@observe_tool
@unpack_pydantic_params
async def update_custom_field_definition(
    request: Annotated[UpdateCustomFieldDefinitionRequest, Unpack()], context: Context
) -> ToolResult:
    """Update a definition label, description, or choices after preview.

    choices is the complete desired active label list; missing labels are retired.
    Use choice_changes={"add": ["New"], "remove": [2]} for an explicit delta.
    Every existing choice ID is retained, including retired choices, so historical
    values remain resolvable. Field type, entity type, and source are immutable.
    """
    response = await _update_custom_field_definition_impl(
        request=request, context=context
    )
    return _to_tool_result(
        response=response, request=request, tool="update_custom_field_definition"
    )


@observe_tool
@unpack_pydantic_params
async def delete_custom_field_definition(
    request: Annotated[DeleteCustomFieldDefinitionRequest, Unpack()], context: Context
) -> ToolResult:
    """Preview then delete a custom-field definition. Its values disappear from record reads."""
    response = await _delete_custom_field_definition_impl(
        request=request, context=context
    )
    return _to_tool_result(
        response=response, request=request, tool="delete_custom_field_definition"
    )


def register_tools(mcp: FastMCP) -> None:
    """Register definition mutations with Confirm/Cancel previews."""
    from katana_mcp.tools.prefab_ui import register_preview_tool

    annotations = ToolAnnotations(
        read_only_hint=False, destructive_hint=True, open_world_hint=True
    )
    register_preview_tool(
        mcp=mcp,
        fn=create_custom_field_definition,
        tags={"custom-fields", "write"},
        annotations=annotations,
        meta=UI_META,
    )
    register_preview_tool(
        mcp=mcp,
        fn=update_custom_field_definition,
        tags={"custom-fields", "write"},
        annotations=annotations,
        meta=UI_META,
    )
    register_preview_tool(
        mcp=mcp,
        fn=delete_custom_field_definition,
        tags={"custom-fields", "write"},
        annotations=annotations,
        meta=UI_META,
    )
