"""Custom-field value validation and omission-safe request shaping."""

import math
from collections.abc import Sequence
from datetime import date
from typing import Any
from uuid import UUID

from fastmcp import Context
from pydantic import BaseModel, Field, SerializerFunctionWrapHandler, model_serializer

from katana_mcp.tools.foundation.custom_fields import (
    ListCustomFieldDefinitionsRequest,
    _list_custom_field_definitions_impl,
)
from katana_mcp.tools.tool_result_utils import BLOCK_WARNING_PREFIX
from katana_public_api_client.client_types import UNSET
from katana_public_api_client.models_pydantic._generated import (
    CustomFieldDefinition,
    CustomFieldEntityType,
    CustomFieldType,
)


class CustomFieldValuesRequest(BaseModel):
    """Omit custom_fields to preserve, null to clear, or a UUID map to merge."""

    custom_fields: dict[str, Any] | None = Field(
        default=None,
        description="Custom-field values keyed by definition UUID. Omit to preserve; null clears all; an object merges its keys ({} changes none). Discover UUIDs with list_custom_field_definitions. Availability depends on account features.",
    )

    @model_serializer(mode="wrap")
    def preserve_custom_fields(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, Any]:
        """Retain explicit null, including through preview-to-apply arguments."""
        data = handler(self)
        if "custom_fields" not in self.model_fields_set:
            data.pop("custom_fields", None)
        elif self.custom_fields is None:
            data["custom_fields"] = None
        return data


def encode_custom_fields(*, request: CustomFieldValuesRequest, map_type: Any) -> Any:
    if "custom_fields" not in request.model_fields_set:
        return UNSET
    if request.custom_fields is None:
        return None
    return map_type.from_dict(request.custom_fields)


def _matches_type(*, definition: CustomFieldDefinition, value: Any) -> bool:
    if value is None:
        return True
    kind = definition.field_type
    if kind == CustomFieldType.boolean:
        return isinstance(value, bool)
    if kind == CustomFieldType.number:
        return type(value) is int or (type(value) is float and math.isfinite(value))
    if kind == CustomFieldType.single_select:
        return (
            type(value) is int
            and definition.options is not None
            and any(
                choice.id == value and not choice.deleted
                for choice in definition.options.choices
            )
        )
    if kind == CustomFieldType.date:
        if not isinstance(value, str) or len(value) != 10:
            return False
        try:
            date.fromisoformat(value)
        except ValueError:
            return False
        return True
    return isinstance(value, str)


async def validate_custom_field_values(
    *,
    values: list[tuple[CustomFieldEntityType, dict[str, Any] | None]],
    context: Context,
) -> list[str]:
    """Validate only supplied nonempty maps; clearing/omission needs no lookup."""
    if not any(fields for _, fields in values):
        return []
    response = await _list_custom_field_definitions_impl(
        request=ListCustomFieldDefinitionsRequest(), context=context
    )
    definitions = {definition.id: definition for definition in response.definitions}
    warnings = []
    for entity_type, fields in values:
        for key, value in (fields or {}).items():
            try:
                identifier = UUID(key)
            except ValueError:
                warnings.append(
                    f"{BLOCK_WARNING_PREFIX} Custom-field key {key!r} must be a definition UUID."
                )
                continue
            definition = definitions.get(identifier)
            if definition is None or definition.entity_type != entity_type:
                warnings.append(
                    f"{BLOCK_WARNING_PREFIX} Custom field {key} is not an active {entity_type} definition."
                )
            elif not _matches_type(definition=definition, value=value):
                warnings.append(
                    f"{BLOCK_WARNING_PREFIX} {definition.label} requires {definition.field_type} values"
                    + (
                        " using an active choice ID."
                        if definition.field_type == CustomFieldType.single_select
                        else "."
                    )
                )
    return warnings


def prepare_custom_field_plan(*, plan: list[Any]) -> None:
    """Verify map merges, explicit clears, and no-op empty-map patches."""
    from katana_mcp.tools._modification import make_response_verifier
    from katana_public_api_client.client_types import Unset

    def verifier_for(
        *,
        diff: list[Any],
        expected: dict[str, Any] | None,
        prior: dict[str, Any] | None,
    ):
        verify_other_fields = make_response_verifier(diff=diff)

        async def verify(outcome: Any):
            verified, actual_after = await verify_other_fields(outcome)
            raw: Any = getattr(outcome, "custom_fields", UNSET)
            actual = raw.to_dict() if hasattr(raw, "to_dict") else raw
            if isinstance(actual, Unset):
                matches = False
                actual = "not returned"
            elif expected is None:
                # Katana's cleared representation is nullable on the wire but
                # can be canonicalized to an empty object in a response.
                matches = actual is None or actual == {}
            elif expected == {}:
                # An explicit empty map is a merge no-op. It must preserve the
                # prior state, while treating null and {} as the same empty
                # custom-field state.
                matches = (
                    (actual is None or isinstance(actual, dict))
                    and (prior is None or isinstance(prior, dict))
                    and (actual or {}) == (prior or {})
                )
            else:
                matches = isinstance(actual, dict) and all(
                    key in actual and actual[key] == value
                    for key, value in expected.items()
                )
            if not matches:
                return False, {**(actual_after or {}), "custom_fields": actual}
            return verified, actual_after

        return verify

    for spec in plan:
        custom = next(
            (change for change in spec.diff if change.field == "custom_fields"), None
        )
        if custom is None:
            continue
        if hasattr(custom.old, "to_dict"):
            custom.old = custom.old.to_dict()
        spec.verify = verifier_for(
            diff=[change for change in spec.diff if change.field != "custom_fields"],
            expected=custom.new,
            prior=custom.old,
        )


def custom_fields_read_kwargs(*, record: Any) -> dict[str, Any]:
    """Retain omitted, null, and object values from an API or cached record."""
    from katana_public_api_client.client_types import Unset

    value = getattr(record, "custom_fields", UNSET)
    if isinstance(value, Unset):
        return {}
    if value is None:
        return (
            {"custom_fields": None}
            if getattr(record, "custom_fields_present", True)
            else {}
        )
    return {"custom_fields": value.to_dict() if hasattr(value, "to_dict") else value}


class ResolvedCustomField(BaseModel):
    definition_id: str
    label: str | None = None
    field_type: str | None = None
    value: Any
    value_label: str | None = None


class CustomFieldValuesResponse(CustomFieldValuesRequest):
    """Preserve read values without inventing empty fields when omitted."""

    custom_fields_resolved: list[ResolvedCustomField] = Field(default_factory=list)

    custom_fields: dict[str, Any] | None = Field(
        default=None,
        description="Custom-field UUID/value map, null when cleared, omitted when not returned by Katana.",
    )


async def resolve_custom_field_values(
    *, records: Sequence[CustomFieldValuesResponse], context: Context
) -> None:
    """Join labels once per result batch, retaining unknown and retired values."""
    populated = [record for record in records if record.custom_fields]
    if not populated:
        return
    response = await _list_custom_field_definitions_impl(
        request=ListCustomFieldDefinitionsRequest(include_deleted=True), context=context
    )
    definitions = {
        str(definition.id): definition for definition in response.definitions
    }
    for record in populated:
        resolved = []
        for identifier, value in (record.custom_fields or {}).items():
            definition = definitions.get(identifier)
            choices = (
                definition.options.choices if definition and definition.options else []
            )
            value_label = next(
                (choice.label for choice in choices if choice.id == value), None
            )
            resolved.append(
                ResolvedCustomField(
                    definition_id=identifier,
                    label=definition.label if definition else None,
                    field_type=definition.field_type.value if definition else None,
                    value=value,
                    value_label=value_label,
                )
            )
        record.custom_fields_resolved = resolved
