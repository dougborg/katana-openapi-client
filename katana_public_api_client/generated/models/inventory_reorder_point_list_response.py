from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.inventory_reorder_point import InventoryReorderPoint


T = TypeVar("T", bound="InventoryReorderPointListResponse")


@_attrs_define
class InventoryReorderPointListResponse:
    """List of inventory reorder point configurations showing threshold levels for automated purchase order generation

    Example:
        {'data': [{'variant_id': 3001, 'location_id': 1, 'value': 50.0, 'created_at': '2024-01-15T08:00:00.000Z',
            'updated_at': '2024-01-15T08:00:00.000Z', 'deleted_at': None}, {'variant_id': 3002, 'location_id': 1, 'value':
            30.0, 'created_at': '2024-01-16T09:00:00.000Z', 'updated_at': '2024-01-16T09:00:00.000Z', 'deleted_at': None}]}

    Attributes:
        data (Union[Unset, list['InventoryReorderPoint']]): Array of reorder point records with variant, location, and
            threshold information
    """

    data: Unset | list["InventoryReorderPoint"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data: Unset | list[dict[str, Any]] = UNSET
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
        from ..models.inventory_reorder_point import InventoryReorderPoint

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = InventoryReorderPoint.from_dict(data_item_data)

            data.append(data_item)

        inventory_reorder_point_list_response = cls(
            data=data,
        )

        inventory_reorder_point_list_response.additional_properties = d
        return inventory_reorder_point_list_response

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
