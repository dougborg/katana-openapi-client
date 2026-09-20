from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

T = TypeVar("T", bound="MaterialConfig")


@_attrs_define
class MaterialConfig:
    """Configuration option supplied while creating a material variant

    Example:
        {'name': 'Grade', 'values': ['Premium', 'Standard', 'Economy']}
    """

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

        material_config = cls(
            name=name,
            values=values,
        )

        return material_config
