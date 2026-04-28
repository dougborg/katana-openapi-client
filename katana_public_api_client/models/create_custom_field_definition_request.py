from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_custom_field_definition_request_options_type_0 import (
        CreateCustomFieldDefinitionRequestOptionsType0,
    )


T = TypeVar("T", bound="CreateCustomFieldDefinitionRequest")


@_attrs_define
class CreateCustomFieldDefinitionRequest:
    """Request payload for creating a new custom field definition.

    Example:
        {'label': 'Quality Grade', 'field_type': 'select', 'entity_type': 'product', 'source': 'user', 'description':
            'Customer-facing quality classification', 'options': {'values': ['A', 'B', 'C']}}
    """

    label: str
    field_type: str
    entity_type: str
    source: str
    description: None | str | Unset = UNSET
    options: CreateCustomFieldDefinitionRequestOptionsType0 | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.create_custom_field_definition_request_options_type_0 import (
            CreateCustomFieldDefinitionRequestOptionsType0,
        )

        label = self.label

        field_type = self.field_type

        entity_type = self.entity_type

        source = self.source

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        options: dict[str, Any] | None | Unset
        if isinstance(self.options, Unset):
            options = UNSET
        elif isinstance(self.options, CreateCustomFieldDefinitionRequestOptionsType0):
            options = self.options.to_dict()
        else:
            options = self.options

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "label": label,
                "field_type": field_type,
                "entity_type": entity_type,
                "source": source,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if options is not UNSET:
            field_dict["options"] = options

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_custom_field_definition_request_options_type_0 import (
            CreateCustomFieldDefinitionRequestOptionsType0,
        )

        d = dict(src_dict)
        label = d.pop("label")

        field_type = d.pop("field_type")

        entity_type = d.pop("entity_type")

        source = d.pop("source")

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_options(
            data: object,
        ) -> CreateCustomFieldDefinitionRequestOptionsType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                options_type_0 = (
                    CreateCustomFieldDefinitionRequestOptionsType0.from_dict(
                        cast(Mapping[str, Any], data)
                    )
                )

                return options_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                CreateCustomFieldDefinitionRequestOptionsType0 | None | Unset, data
            )

        options = _parse_options(d.pop("options", UNSET))

        create_custom_field_definition_request = cls(
            label=label,
            field_type=field_type,
            entity_type=entity_type,
            source=source,
            description=description,
            options=options,
        )

        return create_custom_field_definition_request
