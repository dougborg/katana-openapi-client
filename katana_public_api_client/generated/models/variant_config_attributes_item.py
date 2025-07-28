from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..types import UNSET, Unset

T = TypeVar("T", bound="VariantConfigAttributesItem")


@_attrs_define
class VariantConfigAttributesItem:
    config_name: Unset | str = UNSET
    config_value: Unset | str = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        config_name = self.config_name

        config_value = self.config_value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if config_name is not UNSET:
            field_dict["config_name"] = config_name
        if config_value is not UNSET:
            field_dict["config_value"] = config_value

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        config_name = d.pop("config_name", UNSET)

        config_value = d.pop("config_value", UNSET)

        variant_config_attributes_item = cls(
            config_name=config_name,
            config_value=config_value,
        )

        variant_config_attributes_item.additional_properties = d
        return variant_config_attributes_item

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
