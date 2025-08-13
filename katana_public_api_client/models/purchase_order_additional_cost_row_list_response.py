from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.purchase_order_additional_cost_row import (
        PurchaseOrderAdditionalCostRow,
    )


T = TypeVar("T", bound="PurchaseOrderAdditionalCostRowListResponse")


@_attrs_define
class PurchaseOrderAdditionalCostRowListResponse:
    """Response containing a list of additional cost line items for purchase orders with pagination support

    Example:
        {'data': [{'id': 201, 'additional_cost_id': 1, 'group_id': 1, 'name': 'International Shipping',
            'distribution_method': 'BY_VALUE', 'tax_rate_id': 1, 'tax_rate': 8.5, 'price': 125.0, 'price_in_base': 125.0,
            'currency': 'USD', 'created_at': '2024-01-28T09:15:00Z', 'updated_at': '2024-01-28T09:15:00Z', 'deleted_at':
            None}, {'id': 202, 'additional_cost_id': 2, 'group_id': 1, 'name': 'Import Duty', 'distribution_method':
            'BY_VALUE', 'tax_rate_id': 1, 'tax_rate': 8.5, 'price': 85.0, 'price_in_base': 85.0, 'currency': 'USD',
            'created_at': '2024-01-28T09:15:00Z', 'updated_at': '2024-01-28T09:15:00Z', 'deleted_at': None}]}
    """

    data: Unset | list["PurchaseOrderAdditionalCostRow"] = UNSET
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
        from ..models.purchase_order_additional_cost_row import (
            PurchaseOrderAdditionalCostRow,
        )

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = PurchaseOrderAdditionalCostRow.from_dict(data_item_data)

            data.append(data_item)

        purchase_order_additional_cost_row_list_response = cls(
            data=data,
        )

        purchase_order_additional_cost_row_list_response.additional_properties = d
        return purchase_order_additional_cost_row_list_response

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
