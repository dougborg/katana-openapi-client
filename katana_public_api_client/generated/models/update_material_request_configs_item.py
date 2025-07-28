from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateMaterialRequestConfigsItem")


@_attrs_define
class UpdateMaterialRequestConfigsItem:
    name: str
    values: list[str]
    id: Unset | int = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        values = self.values

        id = self.id

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
                "values": values,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        values = cast(list[str], d.pop("values"))

        id = d.pop("id", UNSET)

        update_material_request_configs_item = cls(
            name=name,
            values=values,
            id=id,
        )

        return update_material_request_configs_item
