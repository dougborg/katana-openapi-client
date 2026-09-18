from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.manufacturing_order_production_ingredient_response import (
        ManufacturingOrderProductionIngredientResponse,
    )


T = TypeVar("T", bound="ManufacturingOrderProductionIngredientListResponse")


@_attrs_define
class ManufacturingOrderProductionIngredientListResponse:
    """Response containing a list of ingredient consumption records across manufacturing order productions, with
    pagination support.

        Example:
            {'data': [{'id': 252, 'location_id': 321, 'variant_id': 24764, 'manufacturing_order_id': 21400,
                'manufacturing_order_recipe_row_id': 20300, 'production_id': 21300, 'quantity': 4, 'production_date':
                '2023-02-10T10:06:13.047Z', 'cost': 1, 'created_at': '2023-02-10T10:06:14.435Z', 'updated_at':
                '2023-02-10T10:06:15.070Z', 'deleted_at': None}]}
    """

    data: list[ManufacturingOrderProductionIngredientResponse] | Unset = UNSET
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
        from ..models.manufacturing_order_production_ingredient_response import (
            ManufacturingOrderProductionIngredientResponse,
        )

        d = dict(src_dict)
        _data = d.pop("data", UNSET)
        data: list[ManufacturingOrderProductionIngredientResponse] | Unset = UNSET
        if _data is not UNSET:
            data = []
            for data_item_data in _data:
                data_item = ManufacturingOrderProductionIngredientResponse.from_dict(
                    cast(Mapping[str, Any], data_item_data)
                )

                data.append(data_item)

        manufacturing_order_production_ingredient_list_response = cls(
            data=data,
        )

        manufacturing_order_production_ingredient_list_response.additional_properties = d
        return manufacturing_order_production_ingredient_list_response

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
