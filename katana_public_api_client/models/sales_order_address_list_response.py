from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.sales_order_address import SalesOrderAddress


T = TypeVar("T", bound="SalesOrderAddressListResponse")


@_attrs_define
class SalesOrderAddressListResponse:
    """Response containing a list of billing and shipping addresses associated with sales orders

    Example:
        {'data': [{'id': 1201, 'sales_order_id': 2001, 'entity_type': 'billing', 'first_name': 'Sarah', 'last_name':
            'Johnson', 'company': "Johnson's Restaurant", 'phone': '+1-503-555-0123', 'line_1': '123 Main Street', 'line_2':
            'Suite 4B', 'city': 'Portland', 'state': 'OR', 'zip': '97201', 'country': 'US', 'created_at':
            '2024-01-15T10:00:00Z', 'updated_at': '2024-01-15T10:00:00Z'}]}

    Attributes:
        data (Union[Unset, list['SalesOrderAddress']]): Array of sales order addresses with complete contact and
            location information
    """

    data: Unset | list["SalesOrderAddress"] = UNSET
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
        from ..models.sales_order_address import SalesOrderAddress

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = SalesOrderAddress.from_dict(data_item_data)

            data.append(data_item)

        sales_order_address_list_response = cls(
            data=data,
        )

        sales_order_address_list_response.additional_properties = d
        return sales_order_address_list_response

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
