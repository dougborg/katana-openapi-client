from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.sales_order_fulfillment import SalesOrderFulfillment


T = TypeVar("T", bound="SalesOrderFulfillmentListResponse")


@_attrs_define
class SalesOrderFulfillmentListResponse:
    """Response containing a list of fulfillment records showing shipping and delivery status for sales orders

    Example:
        {'data': [{'id': 1, 'sales_order_id': 1, 'picked_date': '2020-10-23T10:37:05.085Z', 'status': 'DELIVERED',
            'invoice_status': 'NOT_INVOICED', 'conversion_rate': 2, 'conversion_date': '2020-10-23T10:37:05.085Z',
            'tracking_number': '12345678', 'tracking_url': 'https://tracking-number-url', 'tracking_carrier': 'UPS',
            'tracking_method': 'ground', 'packer_id': 1, 'sales_order_fulfillment_rows': [{'sales_order_row_id': 1,
            'quantity': 2, 'batch_transactions': [{'batch_id': 1, 'quantity': 2}], 'serial_numbers': [1]}], 'created_at':
            '2020-10-23T10:37:05.085Z', 'updated_at': '2020-10-23T10:37:05.085Z'}]}
    """

    data: list[SalesOrderFulfillment] | Unset = UNSET
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
        from ..models.sales_order_fulfillment import SalesOrderFulfillment

        d = dict(src_dict)
        _data = d.pop("data", UNSET)
        data: list[SalesOrderFulfillment] | Unset = UNSET
        if _data is not UNSET:
            data = []
            for data_item_data in _data:
                data_item = SalesOrderFulfillment.from_dict(data_item_data)

                data.append(data_item)

        sales_order_fulfillment_list_response = cls(
            data=data,
        )

        sales_order_fulfillment_list_response.additional_properties = d
        return sales_order_fulfillment_list_response

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
