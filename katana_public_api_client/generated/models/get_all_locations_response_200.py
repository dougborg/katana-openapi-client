from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.location import Location


T = TypeVar("T", bound="GetAllLocationsResponse200")


@_attrs_define
class GetAllLocationsResponse200:
    """
    Example:
        {'data': [{'id': 101, 'name': 'Main Warehouse - Brooklyn', 'legal_name': 'Acme Manufacturing Co. - Brooklyn
            Facility', 'address_id': 1001, 'address': {'id': 1001, 'city': 'Brooklyn', 'country': 'United States', 'line_1':
            '500 Industrial Park Drive', 'line_2': 'Building A', 'state': 'New York', 'zip': '11201'}, 'is_primary': True,
            'sales_allowed': True, 'purchase_allowed': True, 'manufacturing_allowed': True, 'created_at':
            '2020-10-23T10:37:05.085Z', 'updated_at': '2024-01-15T09:30:00.000Z', 'deleted_at': None}, {'id': 102, 'name':
            'Distribution Center - Miami', 'legal_name': 'Acme Manufacturing Co. - Miami DC', 'address_id': 1002, 'address':
            {'id': 1002, 'city': 'Miami', 'country': 'United States', 'line_1': '750 Commerce Boulevard', 'line_2': 'Suite
            200', 'state': 'Florida', 'zip': '33126'}, 'is_primary': False, 'sales_allowed': True, 'purchase_allowed':
            False, 'manufacturing_allowed': False, 'created_at': '2020-11-15T14:22:15.000Z', 'updated_at':
            '2024-01-10T11:15:30.000Z', 'deleted_at': None}, {'id': 103, 'name': 'West Coast Production', 'legal_name':
            'Acme Manufacturing Co. - California Plant', 'address_id': 1003, 'address': {'id': 1003, 'city': 'Los Angeles',
            'country': 'United States', 'line_1': '1250 Manufacturing Way', 'line_2': 'Unit 5', 'state': 'California',
            'zip': '90021'}, 'is_primary': False, 'sales_allowed': False, 'purchase_allowed': True, 'manufacturing_allowed':
            True, 'created_at': '2021-03-01T08:00:00.000Z', 'updated_at': '2024-01-05T16:45:22.000Z', 'deleted_at': None}]}
    """

    data: Unset | list["Location"] = UNSET
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
        from ..models.location import Location

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = Location.from_dict(data_item_data)

            data.append(data_item)

        get_all_locations_response_200 = cls(
            data=data,
        )

        get_all_locations_response_200.additional_properties = d
        return get_all_locations_response_200

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
