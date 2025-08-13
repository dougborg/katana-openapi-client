from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.sales_order_row import SalesOrderRow


T = TypeVar("T", bound="SalesOrderRowListResponse")


@_attrs_define
class SalesOrderRowListResponse:
    """Response containing a list of sales order rows with pagination support for retrieving order line items

    Example:
        {'data': [{'id': 2501, 'quantity': 2, 'variant_id': 2101, 'tax_rate_id': 301, 'location_id': 1,
            'product_availability': 'IN_STOCK', 'product_expected_date': None, 'price_per_unit': 599.99,
            'price_per_unit_in_base_currency': 599.99, 'total': 1199.98, 'total_in_base_currency': 1199.98, 'cogs_value':
            400.0, 'attributes': [{'key': 'engrave_text', 'value': "Johnson's Kitchen"}], 'batch_transactions':
            [{'batch_id': 1801, 'quantity': 2.0}], 'serial_numbers': [10001, 10002], 'linked_manufacturing_order_id': None,
            'conversion_rate': 1.0, 'conversion_date': '2024-01-15T10:00:00Z', 'created_at': '2024-01-15T10:00:00Z',
            'updated_at': '2024-01-15T10:00:00Z'}]}

    Attributes:
        data (Union[Unset, list['SalesOrderRow']]): Array of sales order row line items with pricing and product details
    """

    data: Unset | list["SalesOrderRow"] = UNSET
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
        from ..models.sales_order_row import SalesOrderRow

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = SalesOrderRow.from_dict(data_item_data)

            data.append(data_item)

        sales_order_row_list_response = cls(
            data=data,
        )

        sales_order_row_list_response.additional_properties = d
        return sales_order_row_list_response

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
