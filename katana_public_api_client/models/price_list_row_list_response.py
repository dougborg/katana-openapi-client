from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.price_list_row import PriceListRow


T = TypeVar("T", bound="PriceListRowListResponse")


@_attrs_define
class PriceListRowListResponse:
    """Response containing a paginated list of price list rows showing variant-specific pricing within price lists

    Example:
        {'data': [{'id': 5001, 'price_list_id': 1001, 'variant_id': 201, 'price': 249.99, 'currency': 'USD',
            'created_at': '2024-01-15T10:00:00Z', 'updated_at': '2024-01-15T10:00:00Z'}, {'id': 5002, 'price_list_id': 1001,
            'variant_id': 202, 'price': 69.99, 'currency': 'USD', 'created_at': '2024-01-15T10:05:00Z', 'updated_at':
            '2024-01-15T10:05:00Z'}]}

    Attributes:
        data (Union[Unset, list['PriceListRow']]): Array of price list row objects containing variant pricing
    """

    data: Unset | list["PriceListRow"] = UNSET
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
        from ..models.price_list_row import PriceListRow

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = PriceListRow.from_dict(data_item_data)

            data.append(data_item)

        price_list_row_list_response = cls(
            data=data,
        )

        price_list_row_list_response.additional_properties = d
        return price_list_row_list_response

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
