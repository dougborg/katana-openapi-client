from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.outsourced_purchase_order import OutsourcedPurchaseOrder
    from ..models.regular_purchase_order import RegularPurchaseOrder


T = TypeVar("T", bound="PurchaseOrderListResponse")


@_attrs_define
class PurchaseOrderListResponse:
    """Response containing a list of purchase orders with pagination support for procurement management

    Example:
        {'data': [{'id': 156, 'status': 'OPEN', 'order_no': 'PO-2024-0156', 'entity_type': 'regular', 'supplier_id':
            4001, 'currency': 'USD', 'expected_arrival_date': '2024-02-15', 'order_created_date': '2024-01-28', 'total':
            1962.5, 'total_in_base_currency': 1962.5, 'billing_status': 'UNBILLED', 'tracking_location_id': None,
            'created_at': '2024-01-28T09:15:00Z', 'updated_at': '2024-01-28T09:15:00Z', 'deleted_at': None}, {'id': 158,
            'status': 'OPEN', 'order_no': 'PO-2024-0158', 'entity_type': 'outsourced', 'supplier_id': 4003, 'currency':
            'USD', 'expected_arrival_date': '2024-02-20', 'order_created_date': '2024-01-30', 'total': 2450.0,
            'total_in_base_currency': 2450.0, 'billing_status': 'UNBILLED', 'tracking_location_id': 2,
            'ingredient_availability': 'EXPECTED', 'ingredient_expected_date': '2024-02-18T10:00:00Z', 'created_at':
            '2024-01-30T11:20:00Z', 'updated_at': '2024-01-30T11:20:00Z', 'deleted_at': None}]}

    Attributes:
        data (Union[Unset, list[Union['OutsourcedPurchaseOrder', 'RegularPurchaseOrder']]]): Array of purchase order
            objects
    """

    data: Unset | list[Union["OutsourcedPurchaseOrder", "RegularPurchaseOrder"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.regular_purchase_order import RegularPurchaseOrder

        data: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.data, Unset):
            data = []
            for data_item_data in self.data:
                data_item: dict[str, Any]
                if isinstance(data_item_data, RegularPurchaseOrder):
                    data_item = data_item_data.to_dict()
                else:
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
        from ..models.outsourced_purchase_order import OutsourcedPurchaseOrder
        from ..models.regular_purchase_order import RegularPurchaseOrder

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:

            def _parse_data_item(
                data: object,
            ) -> Union["OutsourcedPurchaseOrder", "RegularPurchaseOrder"]:
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_purchase_order_type_0 = (
                        RegularPurchaseOrder.from_dict(data)
                    )

                    return componentsschemas_purchase_order_type_0
                except:  # noqa: E722
                    pass
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_purchase_order_type_1 = (
                    OutsourcedPurchaseOrder.from_dict(data)
                )

                return componentsschemas_purchase_order_type_1

            data_item = _parse_data_item(data_item_data)

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
