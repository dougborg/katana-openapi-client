from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..types import UNSET, Unset

T = TypeVar("T", bound="MaterialConfigsItem")


@_attrs_define
class MaterialConfigsItem:
    id: Unset | int = UNSET
    name: Unset | str = UNSET
    values: Unset | list[str] = UNSET
    product_id: Unset | int = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        values: Unset | list[str] = UNSET
        if not isinstance(self.values, Unset):
            values = self.values

        product_id = self.product_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if values is not UNSET:
            field_dict["values"] = values
        if product_id is not UNSET:
            field_dict["product_id"] = product_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        name = d.pop("name", UNSET)

        values = cast(list[str], d.pop("values", UNSET))

        product_id = d.pop("product_id", UNSET)

        material_configs_item = cls(
            id=id,
            name=name,
            values=values,
            product_id=product_id,
        )

        material_configs_item.additional_properties = d
        return material_configs_item

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
