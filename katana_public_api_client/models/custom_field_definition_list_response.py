from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.custom_field_definition import CustomFieldDefinition


T = TypeVar("T", bound="CustomFieldDefinitionListResponse")


@_attrs_define
class CustomFieldDefinitionListResponse:
    """List of custom field definitions

    Example:
        {'data': [{'id': '0c8f1d6e-3c2a-4f5b-9d77-12ab34cd56ef', 'label': 'Channel', 'field_type': 'shortText',
            'entity_type': 'SalesOrder', 'source': 'your-integration', 'description': 'Customer-facing sales channel
            classification', 'options': None, 'created_at': '2026-05-14T10:00:00Z', 'updated_at': '2026-05-14T10:00:00Z',
            'deleted_at': None}]}
    """

    data: list[CustomFieldDefinition] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.data, Unset):
            data = []
            for data_item_data in self.data:
                data_item = data_item_data.to_dict()
                data.append(data_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if data is not UNSET:
            field_dict["data"] = data

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.custom_field_definition import CustomFieldDefinition

        d = dict(src_dict)
        _data = d.pop("data", UNSET)
        data: list[CustomFieldDefinition] | Unset = UNSET
        if _data is not UNSET:
            data = []
            for data_item_data in _data:
                data_item = CustomFieldDefinition.from_dict(
                    cast(Mapping[str, Any], data_item_data)
                )

                data.append(data_item)

        custom_field_definition_list_response = cls(
            data=data,
        )

        custom_field_definition_list_response.additional_properties = d
        return custom_field_definition_list_response

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
