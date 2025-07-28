from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..types import UNSET, Unset

T = TypeVar("T", bound="VariantResponseCustomFieldsItem")


@_attrs_define
class VariantResponseCustomFieldsItem:
    field_name: Unset | str = UNSET
    field_value: Unset | str = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        field_name = self.field_name

        field_value = self.field_value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if field_name is not UNSET:
            field_dict["field_name"] = field_name
        if field_value is not UNSET:
            field_dict["field_value"] = field_value

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        field_name = d.pop("field_name", UNSET)

        field_value = d.pop("field_value", UNSET)

        variant_response_custom_fields_item = cls(
            field_name=field_name,
            field_value=field_value,
        )

        variant_response_custom_fields_item.additional_properties = d
        return variant_response_custom_fields_item

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
