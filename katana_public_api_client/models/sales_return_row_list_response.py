from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.sales_return_row import SalesReturnRow


T = TypeVar("T", bound="SalesReturnRowListResponse")


@_attrs_define
class SalesReturnRowListResponse:
    """Response containing a list of sales return row items with product return details and quantities

    Example:
        {'data': [{'id': 3501, 'sales_return_id': 3001, 'variant_id': 2002, 'quantity': 2, 'return_reason_id': 1,
            'notes': 'Packaging was damaged', 'unit_price': 25.0, 'total_price': 50.0}]}

    Attributes:
        data (Union[Unset, list['SalesReturnRow']]): List of sales return row items
    """

    data: Unset | list["SalesReturnRow"] = UNSET
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
        from ..models.sales_return_row import SalesReturnRow

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = SalesReturnRow.from_dict(data_item_data)

            data.append(data_item)

        sales_return_row_list_response = cls(
            data=data,
        )

        sales_return_row_list_response.additional_properties = d
        return sales_return_row_list_response

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
