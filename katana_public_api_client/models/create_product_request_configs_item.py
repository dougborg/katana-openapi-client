from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

T = TypeVar("T", bound="CreateProductRequestConfigsItem")


@_attrs_define
class CreateProductRequestConfigsItem:
    name: str
    values: list[str]

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        values = self.values

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
                "values": values,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        values = cast(list[str], d.pop("values"))

        create_product_request_configs_item = cls(
            name=name,
            values=values,
        )

        return create_product_request_configs_item
