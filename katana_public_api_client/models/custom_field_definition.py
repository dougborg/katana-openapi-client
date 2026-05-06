from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.custom_field_definition_options_type_0 import (
        CustomFieldDefinitionOptionsType0,
    )


T = TypeVar("T", bound="CustomFieldDefinition")


@_attrs_define
class CustomFieldDefinition:
    """A configured custom field definition that callers can attach to a
    resource (sales order, service, product, etc.) via the resource's
    ``custom_fields`` property. Definitions are scoped to a specific
    ``entity_type`` and shape what values consumers can store.

        Example:
            {'id': 42, 'label': 'Quality Grade', 'field_type': 'select', 'entity_type': 'product', 'source': 'user',
                'description': 'Customer-facing quality classification', 'options': {'values': ['A', 'B', 'C']}, 'created_at':
                '2024-01-08T10:00:00Z', 'updated_at': '2024-01-12T15:30:00Z'}
    """

    id: int
    label: str
    field_type: str
    entity_type: str
    source: str
    created_at: datetime.datetime | Unset = UNSET
    updated_at: datetime.datetime | Unset = UNSET
    description: None | str | Unset = UNSET
    options: CustomFieldDefinitionOptionsType0 | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.custom_field_definition_options_type_0 import (
            CustomFieldDefinitionOptionsType0,
        )

        id = self.id

        label = self.label

        field_type = self.field_type

        entity_type = self.entity_type

        source = self.source

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: str | Unset = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        options: dict[str, Any] | None | Unset
        if isinstance(self.options, Unset):
            options = UNSET
        elif isinstance(self.options, CustomFieldDefinitionOptionsType0):
            options = self.options.to_dict()
        else:
            options = self.options

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "label": label,
                "field_type": field_type,
                "entity_type": entity_type,
                "source": source,
            }
        )
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if description is not UNSET:
            field_dict["description"] = description
        if options is not UNSET:
            field_dict["options"] = options

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.custom_field_definition_options_type_0 import (
            CustomFieldDefinitionOptionsType0,
        )

        d = dict(src_dict)
        id = d.pop("id")

        label = d.pop("label")

        field_type = d.pop("field_type")

        entity_type = d.pop("entity_type")

        source = d.pop("source")

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        _updated_at = d.pop("updated_at", UNSET)
        updated_at: datetime.datetime | Unset
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_options(
            data: object,
        ) -> CustomFieldDefinitionOptionsType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            # Empty dict -> None (Katana wire quirk; see #509).
            if isinstance(data, dict) and not data:
                return None
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                options_type_0 = CustomFieldDefinitionOptionsType0.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return options_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(CustomFieldDefinitionOptionsType0 | None | Unset, data)

        options = _parse_options(d.pop("options", UNSET))

        custom_field_definition = cls(
            id=id,
            label=label,
            field_type=field_type,
            entity_type=entity_type,
            source=source,
            created_at=created_at,
            updated_at=updated_at,
            description=description,
            options=options,
        )

        custom_field_definition.additional_properties = d
        return custom_field_definition

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
