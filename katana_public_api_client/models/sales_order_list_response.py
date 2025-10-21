from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.sales_order import SalesOrder


T = TypeVar("T", bound="SalesOrderListResponse")


@_attrs_define
class SalesOrderListResponse:
    """Response containing a list of sales orders with pagination support for retrieving customer order data

    Example:
        {'data': [{'id': 2001, 'customer_id': 1501, 'order_no': 'SO-2024-001', 'source': 'Shopify',
            'order_created_date': '2024-01-15T10:00:00Z', 'delivery_date': '2024-01-22T14:00:00Z', 'picked_date': None,
            'location_id': 1, 'status': 'PACKED', 'currency': 'USD', 'conversion_rate': 1.0, 'conversion_date':
            '2024-01-15T10:00:00Z', 'invoicing_status': 'INVOICED', 'total': 1250.0, 'total_in_base_currency': 1250.0,
            'additional_info': 'Customer requested expedited delivery', 'customer_ref': 'CUST-REF-2024-001',
            'ecommerce_order_type': 'standard', 'ecommerce_store_name': 'Kitchen Pro Store', 'ecommerce_order_id':
            'SHOP-5678-2024', 'product_availability': 'IN_STOCK', 'ingredient_availability': 'IN_STOCK',
            'production_status': 'NOT_APPLICABLE', 'tracking_number': 'UPS1234567890', 'billing_address_id': 1201,
            'shipping_address_id': 1202, 'created_at': '2024-01-15T10:00:00Z', 'updated_at': '2024-01-20T16:30:00Z'}]}

    Attributes:
        data (Union[Unset, list['SalesOrder']]): Array of sales orders with complete order details and status
            information
    """

    data: Unset | list["SalesOrder"] = UNSET
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
        from ..models.sales_order import SalesOrder

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = SalesOrder.from_dict(data_item_data)

            data.append(data_item)

        sales_order_list_response = cls(
            data=data,
        )

        sales_order_list_response.additional_properties = d
        return sales_order_list_response

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
