from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.stocktake import Stocktake


T = TypeVar("T", bound="StocktakeListResponse")


@_attrs_define
class StocktakeListResponse:
    """List of stocktake records showing all physical inventory count sessions and their completion status

    Example:
        {'data': [{'id': 4001, 'reference_no': 'STK-2024-001', 'location_id': 1, 'status': 'COMPLETED', 'count_date':
            '2024-01-15T09:00:00.000Z', 'notes': 'Monthly physical inventory count', 'created_at':
            '2024-01-15T09:00:00.000Z', 'updated_at': '2024-01-15T17:30:00.000Z'}, {'id': 4002, 'reference_no':
            'STK-2024-002', 'location_id': 2, 'status': 'IN_PROGRESS', 'count_date': '2024-01-16T10:00:00.000Z', 'notes':
            'Spot check for high-value items', 'created_at': '2024-01-16T10:00:00.000Z', 'updated_at':
            '2024-01-16T12:00:00.000Z'}]}
    """

    data: Unset | list["Stocktake"] = UNSET
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
        from ..models.stocktake import Stocktake

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = Stocktake.from_dict(data_item_data)

            data.append(data_item)

        stocktake_list_response = cls(
            data=data,
        )

        stocktake_list_response.additional_properties = d
        return stocktake_list_response

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
