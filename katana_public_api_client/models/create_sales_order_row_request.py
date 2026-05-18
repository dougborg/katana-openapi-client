from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_sales_order_row_request_attributes_item import (
        CreateSalesOrderRowRequestAttributesItem,
    )
    from ..models.create_sales_order_row_request_custom_fields_type_0 import (
        CreateSalesOrderRowRequestCustomFieldsType0,
    )


T = TypeVar("T", bound="CreateSalesOrderRowRequest")


@_attrs_define
class CreateSalesOrderRowRequest:
    """Request payload for creating a new sales order row (line item)

    Example:
        {'sales_order_id': 2001, 'variant_id': 2101, 'quantity': 2, 'price_per_unit': 599.99, 'tax_rate_id': 301,
            'location_id': 1}
    """

    sales_order_id: int
    variant_id: int
    quantity: float
    price_per_unit: float | Unset = UNSET
    tax_rate_id: int | Unset = UNSET
    location_id: int | Unset = UNSET
    attributes: list[CreateSalesOrderRowRequestAttributesItem] | Unset = UNSET
    total_discount: float | Unset = UNSET
    custom_fields: CreateSalesOrderRowRequestCustomFieldsType0 | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.create_sales_order_row_request_custom_fields_type_0 import (
            CreateSalesOrderRowRequestCustomFieldsType0,
        )

        sales_order_id = self.sales_order_id

        variant_id = self.variant_id

        quantity = self.quantity

        price_per_unit = self.price_per_unit

        tax_rate_id = self.tax_rate_id

        location_id = self.location_id

        attributes: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.attributes, Unset):
            attributes = []
            for attributes_item_data in self.attributes:
                attributes_item = attributes_item_data.to_dict()
                attributes.append(attributes_item)

        total_discount = self.total_discount

        custom_fields: dict[str, Any] | None | Unset
        if isinstance(self.custom_fields, Unset):
            custom_fields = UNSET
        elif isinstance(
            self.custom_fields, CreateSalesOrderRowRequestCustomFieldsType0
        ):
            custom_fields = self.custom_fields.to_dict()
        else:
            custom_fields = self.custom_fields

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "sales_order_id": sales_order_id,
                "variant_id": variant_id,
                "quantity": quantity,
            }
        )
        if price_per_unit is not UNSET:
            field_dict["price_per_unit"] = price_per_unit
        if tax_rate_id is not UNSET:
            field_dict["tax_rate_id"] = tax_rate_id
        if location_id is not UNSET:
            field_dict["location_id"] = location_id
        if attributes is not UNSET:
            field_dict["attributes"] = attributes
        if total_discount is not UNSET:
            field_dict["total_discount"] = total_discount
        if custom_fields is not UNSET:
            field_dict["custom_fields"] = custom_fields

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_sales_order_row_request_attributes_item import (
            CreateSalesOrderRowRequestAttributesItem,
        )
        from ..models.create_sales_order_row_request_custom_fields_type_0 import (
            CreateSalesOrderRowRequestCustomFieldsType0,
        )

        d = dict(src_dict)
        sales_order_id = d.pop("sales_order_id")

        variant_id = d.pop("variant_id")

        quantity = d.pop("quantity")

        price_per_unit = d.pop("price_per_unit", UNSET)

        tax_rate_id = d.pop("tax_rate_id", UNSET)

        location_id = d.pop("location_id", UNSET)

        _attributes = d.pop("attributes", UNSET)
        attributes: list[CreateSalesOrderRowRequestAttributesItem] | Unset = UNSET
        if _attributes is not UNSET:
            attributes = []
            for attributes_item_data in _attributes:
                attributes_item = CreateSalesOrderRowRequestAttributesItem.from_dict(
                    cast(Mapping[str, Any], attributes_item_data)
                )

                attributes.append(attributes_item)

        total_discount = d.pop("total_discount", UNSET)

        def _parse_custom_fields(
            data: object,
        ) -> CreateSalesOrderRowRequestCustomFieldsType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            # Empty dict -> None (Katana wire quirk; see #509).
            if isinstance(data, dict) and not data:
                return None
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                custom_fields_type_0 = (
                    CreateSalesOrderRowRequestCustomFieldsType0.from_dict(
                        cast(Mapping[str, Any], data)
                    )
                )

                return custom_fields_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                CreateSalesOrderRowRequestCustomFieldsType0 | None | Unset, data
            )

        custom_fields = _parse_custom_fields(d.pop("custom_fields", UNSET))

        create_sales_order_row_request = cls(
            sales_order_id=sales_order_id,
            variant_id=variant_id,
            quantity=quantity,
            price_per_unit=price_per_unit,
            tax_rate_id=tax_rate_id,
            location_id=location_id,
            attributes=attributes,
            total_discount=total_discount,
            custom_fields=custom_fields,
        )

        return create_sales_order_row_request
