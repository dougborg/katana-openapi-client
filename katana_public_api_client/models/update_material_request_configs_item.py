from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="UpdateMaterialRequestConfigsItem")


@_attrs_define
class UpdateMaterialRequestConfigsItem:
    values: list[str]
    id: int | Unset = UNSET
    name: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        values = self.values

        id = self.id

        name = self.name

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "values": values,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        values = cast(list[str], d.pop("values"))

        id = d.pop("id", UNSET)

        name = d.pop("name", UNSET)

        update_material_request_configs_item = cls(
            values=values,
            id=id,
            name=name,
        )

        return update_material_request_configs_item
