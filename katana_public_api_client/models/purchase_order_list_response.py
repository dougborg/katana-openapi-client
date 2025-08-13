from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.purchase_order import PurchaseOrder


T = TypeVar("T", bound="PurchaseOrderListResponse")


@_attrs_define
class PurchaseOrderListResponse:
    """Response containing a list of purchase orders with pagination support for procurement management

    Example:
        {'data': [{'id': 156, 'status': 'OPEN', 'order_no': 'PO-2024-0156', 'entity_type': 'regular', 'supplier_id':
            4001, 'currency': 'USD', 'expected_arrival_date': '2024-02-15', 'order_created_date': '2024-01-28', 'total':
            1962.5, 'total_in_base_currency': 1962.5, 'billing_status': 'UNBILLED', 'created_at': '2024-01-28T09:15:00Z',
            'updated_at': '2024-01-28T09:15:00Z', 'deleted_at': None}, {'id': 157, 'status': 'RECEIVED', 'order_no':
            'PO-2024-0157', 'entity_type': 'regular', 'supplier_id': 4002, 'currency': 'USD', 'expected_arrival_date':
            '2024-02-10', 'order_created_date': '2024-01-25', 'total': 875.0, 'total_in_base_currency': 875.0,
            'billing_status': 'BILLED', 'created_at': '2024-01-25T14:30:00Z', 'updated_at': '2024-02-10T11:45:00Z',
            'deleted_at': None}]}
    """

    data: Unset | list["PurchaseOrder"] = UNSET
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
        from ..models.purchase_order import PurchaseOrder

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = PurchaseOrder.from_dict(data_item_data)

            data.append(data_item)

        purchase_order_list_response = cls(
            data=data,
        )

        purchase_order_list_response.additional_properties = d
        return purchase_order_list_response

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
