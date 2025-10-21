from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.product import Product


T = TypeVar("T", bound="ProductListResponse")


@_attrs_define
class ProductListResponse:
    """Response containing a paginated list of products with their variants and configurations

    Example:
        {'data': [{'id': 101, 'name': 'Professional Kitchen Knife Set', 'uom': 'set', 'category_name': 'Kitchenware',
            'is_sellable': True, 'is_producible': True, 'is_purchasable': False, 'type': 'product', 'variants': [{'id': 301,
            'sku': 'KNF-PRO-8PC', 'name': '8-Piece Professional Set', 'sales_price': 299.99}]}, {'id': 102, 'name':
            'Stainless Steel Mixing Bowls', 'uom': 'set', 'category_name': 'Kitchenware', 'is_sellable': True,
            'is_producible': False, 'is_purchasable': True, 'type': 'product', 'variants': [{'id': 302, 'sku': 'BOWL-
            SS-5PC', 'name': '5-Piece Mixing Bowl Set', 'sales_price': 79.99}]}]}

    Attributes:
        data (Union[Unset, list['Product']]): Array of product objects returned by the API
    """

    data: Unset | list["Product"] = UNSET
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
        from ..models.product import Product

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = Product.from_dict(data_item_data)

            data.append(data_item)

        product_list_response = cls(
            data=data,
        )

        product_list_response.additional_properties = d
        return product_list_response

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
