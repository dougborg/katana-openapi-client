from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_sales_order_request_sales_order_rows_item_attributes_item import (
        CreateSalesOrderRequestSalesOrderRowsItemAttributesItem,
    )


T = TypeVar("T", bound="CreateSalesOrderRequestSalesOrderRowsItem")


@_attrs_define
class CreateSalesOrderRequestSalesOrderRowsItem:
    quantity: float
    variant_id: int
    tax_rate_id: None | Unset | int = UNSET
    location_id: None | Unset | int = UNSET
    price_per_unit: None | Unset | float = UNSET
    total_discount: None | Unset | float = UNSET
    attributes: (
        Unset | list["CreateSalesOrderRequestSalesOrderRowsItemAttributesItem"]
    ) = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        quantity = self.quantity

        variant_id = self.variant_id

        tax_rate_id: None | Unset | int
        if isinstance(self.tax_rate_id, Unset):
            tax_rate_id = UNSET
        else:
            tax_rate_id = self.tax_rate_id

        location_id: None | Unset | int
        if isinstance(self.location_id, Unset):
            location_id = UNSET
        else:
            location_id = self.location_id

        price_per_unit: None | Unset | float
        if isinstance(self.price_per_unit, Unset):
            price_per_unit = UNSET
        else:
            price_per_unit = self.price_per_unit

        total_discount: None | Unset | float
        if isinstance(self.total_discount, Unset):
            total_discount = UNSET
        else:
            total_discount = self.total_discount

        attributes: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.attributes, Unset):
            attributes = []
            for attributes_item_data in self.attributes:
                attributes_item = attributes_item_data.to_dict()
                attributes.append(attributes_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "quantity": quantity,
                "variant_id": variant_id,
            }
        )
        if tax_rate_id is not UNSET:
            field_dict["tax_rate_id"] = tax_rate_id
        if location_id is not UNSET:
            field_dict["location_id"] = location_id
        if price_per_unit is not UNSET:
            field_dict["price_per_unit"] = price_per_unit
        if total_discount is not UNSET:
            field_dict["total_discount"] = total_discount
        if attributes is not UNSET:
            field_dict["attributes"] = attributes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_sales_order_request_sales_order_rows_item_attributes_item import (
            CreateSalesOrderRequestSalesOrderRowsItemAttributesItem,
        )

        d = dict(src_dict)
        quantity = d.pop("quantity")

        variant_id = d.pop("variant_id")

        def _parse_tax_rate_id(data: object) -> None | Unset | int:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | int, data)

        tax_rate_id = _parse_tax_rate_id(d.pop("tax_rate_id", UNSET))

        def _parse_location_id(data: object) -> None | Unset | int:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | int, data)

        location_id = _parse_location_id(d.pop("location_id", UNSET))

        def _parse_price_per_unit(data: object) -> None | Unset | float:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | float, data)

        price_per_unit = _parse_price_per_unit(d.pop("price_per_unit", UNSET))

        def _parse_total_discount(data: object) -> None | Unset | float:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | float, data)

        total_discount = _parse_total_discount(d.pop("total_discount", UNSET))

        attributes = []
        _attributes = d.pop("attributes", UNSET)
        for attributes_item_data in _attributes or []:
            attributes_item = (
                CreateSalesOrderRequestSalesOrderRowsItemAttributesItem.from_dict(
                    attributes_item_data
                )
            )

            attributes.append(attributes_item)

        create_sales_order_request_sales_order_rows_item = cls(
            quantity=quantity,
            variant_id=variant_id,
            tax_rate_id=tax_rate_id,
            location_id=location_id,
            price_per_unit=price_per_unit,
            total_discount=total_discount,
            attributes=attributes,
        )

        create_sales_order_request_sales_order_rows_item.additional_properties = d
        return create_sales_order_request_sales_order_rows_item

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
