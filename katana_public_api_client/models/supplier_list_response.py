from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.supplier import Supplier


T = TypeVar("T", bound="SupplierListResponse")


@_attrs_define
class SupplierListResponse:
    """Response containing a list of suppliers with pagination support for supplier management

    Example:
        {'data': [{'id': 4001, 'name': 'Premium Kitchen Supplies Ltd', 'email': 'orders@premiumkitchen.com', 'phone':
            '+1-555-0134', 'currency': 'USD', 'comment': 'Primary supplier for kitchen equipment and utensils',
            'default_address_id': 4001, 'created_at': '2023-06-15T08:30:00Z', 'updated_at': '2024-01-15T14:20:00Z',
            'deleted_at': None}, {'id': 4002, 'name': 'Industrial Food Systems', 'email': 'procurement@indufood.com',
            'phone': '+1-555-0276', 'currency': 'USD', 'comment': 'Specialized in commercial kitchen appliances',
            'default_address_id': 4002, 'created_at': '2023-08-22T10:15:00Z', 'updated_at': '2023-12-10T16:30:00Z',
            'deleted_at': None}]}
    """

    data: Unset | list["Supplier"] = UNSET
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
        from ..models.supplier import Supplier

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = Supplier.from_dict(data_item_data)

            data.append(data_item)

        supplier_list_response = cls(
            data=data,
        )

        supplier_list_response.additional_properties = d
        return supplier_list_response

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
