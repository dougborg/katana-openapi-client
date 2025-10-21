from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.purchase_order_row import PurchaseOrderRow


T = TypeVar("T", bound="PurchaseOrderRowListResponse")


@_attrs_define
class PurchaseOrderRowListResponse:
    """Response containing a list of purchase order line items with pagination support for detailed order management

    Example:
        {'data': [{'id': 501, 'quantity': 250, 'variant_id': 501, 'tax_rate_id': 1, 'price_per_unit': 2.85,
            'price_per_unit_in_base_currency': 2.85, 'purchase_uom': 'kg', 'currency': 'USD', 'total': 712.5,
            'total_in_base_currency': 712.5, 'purchase_order_id': 156, 'created_at': '2024-01-28T09:15:00Z', 'updated_at':
            '2024-02-15T14:30:00Z', 'deleted_at': None}, {'id': 502, 'quantity': 100, 'variant_id': 502, 'tax_rate_id': 1,
            'price_per_unit': 12.5, 'price_per_unit_in_base_currency': 12.5, 'purchase_uom': 'pieces', 'currency': 'USD',
            'total': 1250.0, 'total_in_base_currency': 1250.0, 'purchase_order_id': 156, 'created_at':
            '2024-01-28T09:15:00Z', 'updated_at': '2024-02-15T14:30:00Z', 'deleted_at': None}]}

    Attributes:
        data (Union[Unset, list['PurchaseOrderRow']]): Array of purchase order line item objects
    """

    data: Unset | list["PurchaseOrderRow"] = UNSET
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
        from ..models.purchase_order_row import PurchaseOrderRow

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = PurchaseOrderRow.from_dict(data_item_data)

            data.append(data_item)

        purchase_order_row_list_response = cls(
            data=data,
        )

        purchase_order_row_list_response.additional_properties = d
        return purchase_order_row_list_response

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
