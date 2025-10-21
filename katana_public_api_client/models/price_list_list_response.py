from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.price_list import PriceList


T = TypeVar("T", bound="PriceListListResponse")


@_attrs_define
class PriceListListResponse:
    """Response containing a paginated list of price lists configured for customer-specific and market-specific pricing
    management

        Example:
            {'data': [{'id': 1001, 'name': 'Premium Customer Pricing', 'currency': 'USD', 'is_default': False,
                'markup_percentage': 25.0, 'start_date': '2024-01-01T00:00:00Z', 'end_date': '2024-12-31T23:59:59Z',
                'created_at': '2024-01-01T10:00:00Z', 'updated_at': '2024-01-15T14:30:00Z', 'deleted_at': None}, {'id': 1002,
                'name': 'Wholesale Rates', 'currency': 'USD', 'is_default': True, 'markup_percentage': 15.0, 'start_date': None,
                'end_date': None, 'created_at': '2024-01-01T10:05:00Z', 'updated_at': '2024-01-01T10:05:00Z', 'deleted_at':
                None}]}

        Attributes:
            data (Union[Unset, list['PriceList']]): Array of price list objects
    """

    data: Unset | list["PriceList"] = UNSET
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
        from ..models.price_list import PriceList

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = PriceList.from_dict(data_item_data)

            data.append(data_item)

        price_list_list_response = cls(
            data=data,
        )

        price_list_list_response.additional_properties = d
        return price_list_list_response

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
