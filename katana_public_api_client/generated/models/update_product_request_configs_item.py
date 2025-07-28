from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateProductRequestConfigsItem")


@_attrs_define
class UpdateProductRequestConfigsItem:
    name: Unset | str = UNSET
    values: Unset | list[str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        values: Unset | list[str] = UNSET
        if not isinstance(self.values, Unset):
            values = self.values

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if values is not UNSET:
            field_dict["values"] = values

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name", UNSET)

        values = cast(list[str], d.pop("values", UNSET))

        update_product_request_configs_item = cls(
            name=name,
            values=values,
        )

        return update_product_request_configs_item
