from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="UpdateServiceRequest")


@_attrs_define
class UpdateServiceRequest:
    """Request payload for updating an existing service's properties and specifications

    Example:
        {'name': 'Updated Assembly Service', 'uom': 'hours', 'category_name': 'Professional Services', 'is_sellable':
            True, 'is_archived': False, 'sales_price': 85.0, 'default_cost': 55.0, 'sku': 'ASSM-001-UPD', 'additional_info':
            'Updated professional product assembly service', 'custom_field_collection_id': 1}
    """

    name: Unset | str = UNSET
    uom: Unset | str = UNSET
    category_name: Unset | str = UNSET
    additional_info: Unset | str = UNSET
    is_sellable: Unset | bool = UNSET
    is_archived: Unset | bool = UNSET
    sales_price: None | Unset | float = UNSET
    default_cost: None | Unset | float = UNSET
    sku: Unset | str = UNSET
    custom_field_collection_id: None | Unset | int = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        uom = self.uom

        category_name = self.category_name

        additional_info = self.additional_info

        is_sellable = self.is_sellable

        is_archived = self.is_archived

        sales_price: None | Unset | float
        if isinstance(self.sales_price, Unset):
            sales_price = UNSET
        else:
            sales_price = self.sales_price

        default_cost: None | Unset | float
        if isinstance(self.default_cost, Unset):
            default_cost = UNSET
        else:
            default_cost = self.default_cost

        sku = self.sku

        custom_field_collection_id: None | Unset | int
        if isinstance(self.custom_field_collection_id, Unset):
            custom_field_collection_id = UNSET
        else:
            custom_field_collection_id = self.custom_field_collection_id

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if uom is not UNSET:
            field_dict["uom"] = uom
        if category_name is not UNSET:
            field_dict["category_name"] = category_name
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info
        if is_sellable is not UNSET:
            field_dict["is_sellable"] = is_sellable
        if is_archived is not UNSET:
            field_dict["is_archived"] = is_archived
        if sales_price is not UNSET:
            field_dict["sales_price"] = sales_price
        if default_cost is not UNSET:
            field_dict["default_cost"] = default_cost
        if sku is not UNSET:
            field_dict["sku"] = sku
        if custom_field_collection_id is not UNSET:
            field_dict["custom_field_collection_id"] = custom_field_collection_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name", UNSET)

        uom = d.pop("uom", UNSET)

        category_name = d.pop("category_name", UNSET)

        additional_info = d.pop("additional_info", UNSET)

        is_sellable = d.pop("is_sellable", UNSET)

        is_archived = d.pop("is_archived", UNSET)

        def _parse_sales_price(data: object) -> None | Unset | float:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | float, data)

        sales_price = _parse_sales_price(d.pop("sales_price", UNSET))

        def _parse_default_cost(data: object) -> None | Unset | float:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | float, data)

        default_cost = _parse_default_cost(d.pop("default_cost", UNSET))

        sku = d.pop("sku", UNSET)

        def _parse_custom_field_collection_id(data: object) -> None | Unset | int:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | int, data)

        custom_field_collection_id = _parse_custom_field_collection_id(
            d.pop("custom_field_collection_id", UNSET)
        )

        update_service_request = cls(
            name=name,
            uom=uom,
            category_name=category_name,
            additional_info=additional_info,
            is_sellable=is_sellable,
            is_archived=is_archived,
            sales_price=sales_price,
            default_cost=default_cost,
            sku=sku,
            custom_field_collection_id=custom_field_collection_id,
        )

        return update_service_request
