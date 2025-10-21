from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.customer_address import CustomerAddress


T = TypeVar("T", bound="CustomerAddressListResponse")


@_attrs_define
class CustomerAddressListResponse:
    """Response containing a list of customer addresses with complete contact information

    Example:
        {'data': [{'id': 3001, 'customer_id': 2001, 'entity_type': 'billing', 'default': True, 'first_name': 'Sarah',
            'last_name': 'Johnson', 'company': 'Kitchen Pro Restaurants Ltd', 'phone': '+1-555-0123', 'line_1': '123
            Restaurant Row', 'line_2': 'Suite 200', 'city': 'Chicago', 'state': 'IL', 'zip': '60601', 'country': 'US',
            'created_at': '2024-01-10T09:15:00Z', 'updated_at': '2024-01-10T09:15:00Z'}, {'id': 3002, 'customer_id': 2001,
            'entity_type': 'shipping', 'default': True, 'first_name': 'David', 'last_name': 'Kim', 'company': 'Kitchen Pro
            Restaurants Ltd', 'phone': '+1-555-0126', 'line_1': '456 Delivery Avenue', 'line_2': 'Loading Dock B', 'city':
            'Chicago', 'state': 'IL', 'zip': '60602', 'country': 'US', 'created_at': '2024-01-10T09:20:00Z', 'updated_at':
            '2024-01-10T09:20:00Z'}]}

    Attributes:
        data (Union[Unset, list['CustomerAddress']]): Array of customer address entities
    """

    data: Unset | list["CustomerAddress"] = UNSET
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
        from ..models.customer_address import CustomerAddress

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = CustomerAddress.from_dict(data_item_data)

            data.append(data_item)

        customer_address_list_response = cls(
            data=data,
        )

        customer_address_list_response.additional_properties = d
        return customer_address_list_response

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
