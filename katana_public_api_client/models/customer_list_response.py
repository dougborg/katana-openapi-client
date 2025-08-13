from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.customer import Customer


T = TypeVar("T", bound="CustomerListResponse")


@_attrs_define
class CustomerListResponse:
    """Response containing a list of customers with pagination metadata

    Example:
        {'data': [{'id': 2001, 'name': 'Kitchen Pro Restaurants', 'first_name': 'Sarah', 'last_name': 'Johnson',
            'company': 'Kitchen Pro Restaurants Ltd', 'email': 'orders@kitchenpro.com', 'phone': '+1-555-0123', 'comment':
            'Preferred customer - high volume orders', 'currency': 'USD', 'reference_id': 'KPR-2024-001', 'category':
            'Restaurant Chain', 'discount_rate': 5.0, 'default_billing_id': 3001, 'default_shipping_id': 3002, 'created_at':
            '2024-01-10T09:00:00Z', 'updated_at': '2024-01-15T14:30:00Z', 'deleted_at': None}, {'id': 2002, 'name': "Baker's
            Choice Bakery", 'first_name': 'Michael', 'last_name': 'Chen', 'company': "Baker's Choice Bakery", 'email':
            'mike@bakerschoice.com', 'phone': '+1-555-0124', 'comment': 'Weekly wholesale orders', 'currency': 'USD',
            'reference_id': 'BC-2024-002', 'category': 'Bakery', 'discount_rate': 3.0, 'default_billing_id': 3003,
            'default_shipping_id': 3004, 'created_at': '2024-01-12T10:30:00Z', 'updated_at': '2024-01-18T16:45:00Z',
            'deleted_at': None}]}

    Attributes:
        data (Union[Unset, list['Customer']]): Array of customer entities
    """

    data: Unset | list["Customer"] = UNSET
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
        from ..models.customer import Customer

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = Customer.from_dict(data_item_data)

            data.append(data_item)

        customer_list_response = cls(
            data=data,
        )

        customer_list_response.additional_properties = d
        return customer_list_response

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
