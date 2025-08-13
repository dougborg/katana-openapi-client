from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.tax_rate import TaxRate


T = TypeVar("T", bound="TaxRateListResponse")


@_attrs_define
class TaxRateListResponse:
    """Response containing a paginated list of tax rates configured for the organization's sales and purchase tax
    compliance

        Example:
            {'data': [{'id': 301, 'name': 'VAT 20%', 'rate': 20.0, 'is_default_sales': True, 'is_default_purchases': False,
                'display_name': 'VAT (20.0%)', 'created_at': '2024-01-15T09:30:00Z', 'updated_at': '2024-01-15T09:30:00Z'},
                {'id': 302, 'name': 'VAT 5%', 'rate': 5.0, 'is_default_sales': False, 'is_default_purchases': True,
                'display_name': 'VAT (5.0%)', 'created_at': '2024-01-15T09:35:00Z', 'updated_at': '2024-01-15T09:35:00Z'}]}
    """

    data: Unset | list["TaxRate"] = UNSET
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
        from ..models.tax_rate import TaxRate

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = TaxRate.from_dict(data_item_data)

            data.append(data_item)

        tax_rate_list_response = cls(
            data=data,
        )

        tax_rate_list_response.additional_properties = d
        return tax_rate_list_response

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
