from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="ItemConfig")


@_attrs_define
class ItemConfig:
    """Configuration option for products and materials that defines variant attributes

    Example:
        {'id': 201, 'name': 'Type', 'values': ['Standard', 'Double-bladed'], 'product_id': 1, 'material_id': None}

    Attributes:
        id (int): Unique identifier
        name (str): Configuration attribute name (e.g., Size, Color, Style, Grade)
        values (list[str]): Array of possible values for this configuration attribute
        product_id (Union[None, Unset, int]): ID of the product this configuration belongs to (null for materials)
        material_id (Union[None, Unset, int]): ID of the material this configuration belongs to (null for products)
    """

    id: int
    name: str
    values: list[str]
    product_id: None | Unset | int = UNSET
    material_id: None | Unset | int = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        values = self.values

        product_id: None | Unset | int
        if isinstance(self.product_id, Unset):
            product_id = UNSET
        else:
            product_id = self.product_id

        material_id: None | Unset | int
        if isinstance(self.material_id, Unset):
            material_id = UNSET
        else:
            material_id = self.material_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "values": values,
            }
        )
        if product_id is not UNSET:
            field_dict["product_id"] = product_id
        if material_id is not UNSET:
            field_dict["material_id"] = material_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        values = cast(list[str], d.pop("values"))

        def _parse_product_id(data: object) -> None | Unset | int:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | int, data)

        product_id = _parse_product_id(d.pop("product_id", UNSET))

        def _parse_material_id(data: object) -> None | Unset | int:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | int, data)

        material_id = _parse_material_id(d.pop("material_id", UNSET))

        item_config = cls(
            id=id,
            name=name,
            values=values,
            product_id=product_id,
            material_id=material_id,
        )

        item_config.additional_properties = d
        return item_config

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
